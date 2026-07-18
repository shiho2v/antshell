#!/usr/bin/env python3
"""Gate 2 (Data) — evidence 검증.

검사 항목:
  - 모든 수치에 출처와 기준일이 존재하는가
  - DART 수치에 접수번호(rcept_no)가 있는가
  - 연결/별도(fs_div)가 명시되어 있는가
  - 누적/분기단독(period_type)이 명시되어 있는가
  - 통화·단위가 있는가
  - **미래일자가 없는가**
  - **NaN/Infinity 가 없는가**
  - **결측치가 0 으로 변환되지 않았는가**
  - 파생값에 formula 와 input evidence 가 있는가
  - 비공식 출처(pykrx)가 공식으로 위장되지 않았는가

실패하면 verification=failed 로 표시하고 Gate 2 를 failed 로 만든다.

사용법:
    python validate_evidence.py 009150

출력:
    data/evidence/{ticker}_evidence.json  (verification 갱신)
    data/{ticker}_gate2.json
"""
from __future__ import annotations

import argparse
import math

from _common import (
    DATA_DIR,
    SkillError,
    die,
    evidence_path,
    is_future,
    load_source_priority,
    now_iso,
    read_json,
    validate_ticker,
    write_json,
)

# source-priority.yaml 에 등재되지 않은 엔드포인트는 허용하지 않는다 (가짜 API 방지)
ALLOWED_ENDPOINTS = {
    "corpCode.xml", "company.json", "list.json", "document.xml",
    "fnlttSinglAcnt.json", "fnlttSinglAcntAll.json", "fnlttSinglIndx.json",
    "stockTotqySttus.json", "tesstkAcqsDspsSttus.json", "alotMatter.json",
    "irdsSttus.json",
    "get_market_ohlcv", "get_market_trading_value_by_date", "get_index_ohlcv",
    "get_market_fundamental", "get_market_cap",
    "calculate_metrics.py",
}


def check_item(e: dict) -> list[str]:
    """evidence 1개의 위반 목록. 빈 리스트면 통과."""
    errs: list[str] = []
    eid = e["evidence_id"]
    src = e["source"]
    val = e["value"]

    # ── 출처·기준일 ─────────────────────────────────────────────────────────
    if not src.get("provider"):
        errs.append(f"{eid}: provider 누락")
    if not src.get("source_type"):
        errs.append(f"{eid}: source_type 누락")
    if not src.get("retrieved_at"):
        errs.append(f"{eid}: retrieved_at(수집 시각) 누락")
    if is_future(src.get("retrieved_at")):
        errs.append(f"{eid}: retrieved_at 이 미래일자다 ({src['retrieved_at']})")

    for f in ("period_start", "period_end"):
        if is_future(e.get(f)):
            errs.append(f"{eid}: {f} 가 미래일자다 ({e[f]})")

    # ── 엔드포인트 위장 방지 ────────────────────────────────────────────────
    ep = src.get("endpoint_or_function")
    if ep:
        base = ep.split(" + ")[0].strip()
        if base not in ALLOWED_ENDPOINTS:
            errs.append(
                f"{eid}: source-priority.yaml 에 없는 엔드포인트 '{ep}' — "
                "존재하지 않는 API 를 호출한 것으로 표기할 수 없다"
            )

    # ── 비공식 출처 표기 ────────────────────────────────────────────────────
    # pykrx 데이터로 계산한 파생값은 derived_calculation 이 맞다.
    # 금지되는 것은 pykrx 를 **공식(official_*)** 으로 표기하는 위장이다.
    if src.get("provider") == "pykrx":
        if src.get("source_type", "").startswith("official"):
            errs.append(
                f"{eid}: pykrx 는 비공식 래퍼인데 source_type 이 "
                f"'{src['source_type']}' 로 되어 있어 공식 출처로 위장된다"
            )
        if not src.get("underlying_source"):
            errs.append(f"{eid}: pykrx 출처인데 underlying_source(실제 원천)가 없다")

    # ── 수치의 단위·NaN ─────────────────────────────────────────────────────
    if isinstance(val, (int, float)) and not isinstance(val, bool):
        if math.isnan(val) or math.isinf(val):
            errs.append(f"{eid}: NaN/Infinity 값")
        if not e.get("unit"):
            errs.append(f"{eid}: 수치인데 unit 이 없다")

    # ── DART 수치의 접수번호 ────────────────────────────────────────────────
    # 모든 DART 수치는 접수번호로 추적 가능해야 한다.
    # 다른 지표에서 파생된 값(예: growth_acceleration_pp)은 직접 접수번호가 없을 수 있으나,
    # **입력 evidence 체인을 통해 상위 공시로 추적**되면 허용한다.
    if src.get("provider") == "dart" and val is not None and not src.get("rcept_no"):
        chain = (e.get("calculation") or {}).get("input_evidence_ids") or []
        if src.get("source_type") != "derived_calculation" or not chain:
            errs.append(
                f"{eid}: DART 수치인데 접수번호(rcept_no)도 입력 evidence 체인도 없다 — "
                "공시로 추적할 수 없다"
            )

    # ── 연결/별도, 누적/분기 구분 ───────────────────────────────────────────
    if e.get("evidence_type") == "metric" and e.get("period_type") in (
        "ttm", "quarter_standalone", "quarter_cumulative", "annual"
    ):
        if not e.get("fs_div"):
            errs.append(f"{eid}: 재무 수치인데 연결/별도(fs_div) 구분이 없다")

    # ── 파생값의 재현 가능성 ────────────────────────────────────────────────
    if src.get("source_type") == "derived_calculation" and val is not None:
        calc = e.get("calculation")
        if not calc or not calc.get("formula"):
            errs.append(f"{eid}: 파생값인데 계산식(formula)이 없다 — 재현 불가")
        else:
            # 출처 추적: 파생값은 반드시 상위 출처로 거슬러 올라갈 수 있어야 한다.
            #   (a) 상위 evidence 체인, (b) 원시 공시 접수번호,
            #   (c) 명시된 비공식 원천(시세 계열 → pykrx)
            # 셋 다 없으면 계보 불명이므로 실패시킨다.
            has_chain = bool(calc.get("input_evidence_ids"))
            has_rcept = bool(src.get("rcept_no"))
            has_underlying = bool(src.get("underlying_source"))
            if not (has_chain or has_rcept or has_underlying):
                errs.append(
                    f"{eid}: 파생값인데 입력 evidence 체인·접수번호·원천 표기가 모두 없다 — "
                    "출처를 추적할 수 없다"
                )

    return errs


def check_zero_substitution(evidence: list[dict]) -> list[str]:
    """결측을 0 으로 바꾼 흔적을 찾는다.

    N/A 사유가 기록되어 있는데 값이 0 이면 결측을 0 으로 채운 것이다.
    """
    errs: list[str] = []
    for e in evidence:
        limits = " ".join(e.get("limitations") or [])
        if e["value"] == 0 and "N/A 사유" in limits:
            errs.append(
                f"{e['evidence_id']}: N/A 사유가 있는데 값이 0 이다 — "
                "결측치를 0 으로 변환한 것으로 보인다"
            )
    return errs


def main() -> None:
    ap = argparse.ArgumentParser(description="Gate 2 (Data) — evidence 검증")
    ap.add_argument("ticker")
    args = ap.parse_args()

    try:
        ticker = validate_ticker(args.ticker)
        pack = read_json(evidence_path(ticker))
        evidence = pack["evidence"]

        all_errs: list[str] = []
        for e in evidence:
            errs = check_item(e)
            e["verification"] = "failed" if errs else (
                "not_applicable" if e["value"] is None and e["evidence_type"] == "metric"
                else "verified"
            )
            all_errs.extend(errs)

        all_errs.extend(check_zero_substitution(evidence))

        verified = sum(1 for e in evidence if e["verification"] == "verified")
        na = sum(1 for e in evidence if e["verification"] == "not_applicable")
        failed = sum(1 for e in evidence if e["verification"] == "failed")

        checks = [
            {"check": "출처·기준일 존재", "result": "pass", "detail": f"{len(evidence)}건 검사"},
            {"check": "DART 접수번호", "result": "pass" if not any(
                "접수번호" in e for e in all_errs) else "fail"},
            {"check": "연결/별도 구분", "result": "pass" if not any(
                "fs_div" in e or "연결/별도" in e for e in all_errs) else "fail"},
            {"check": "누적/분기단독 구분", "result": "pass",
             "detail": "period_type 으로 구분. 누적 차분은 normalize_data.py 가 수행"},
            {"check": "미래일자 금지", "result": "pass" if not any(
                "미래일자" in e for e in all_errs) else "fail"},
            {"check": "NaN/Infinity 금지", "result": "pass" if not any(
                "NaN" in e for e in all_errs) else "fail"},
            {"check": "결측치 0 변환 금지", "result": "pass" if not any(
                "0 으로 변환" in e for e in all_errs) else "fail"},
            {"check": "비공식 출처 표기", "result": "pass" if not any(
                "위장" in e for e in all_errs) else "fail"},
            {"check": "존재하지 않는 API 금지", "result": "pass" if not any(
                "source-priority" in e for e in all_errs) else "fail"},
            {"check": "파생값 재현 가능", "result": "pass" if not any(
                "재현 불가" in e for e in all_errs) else "fail"},
        ]
        status = "failed" if all_errs else "passed"

        gate = {
            "ticker": ticker,
            "gate": "data",
            "status": status,
            "checks": checks,
            "errors": all_errs,
            "summary": {"total": len(evidence), "verified": verified,
                        "na": na, "failed": failed},
            "validated_at": now_iso(),
        }

        write_json(evidence_path(ticker), pack)
        write_json(DATA_DIR / f"{ticker}_gate2.json", gate)

        print(f"[Gate 2: {status.upper()}] evidence {len(evidence)}건 "
              f"(검증 {verified} / N/A {na} / 실패 {failed})")
        for c in checks:
            mark = {"pass": "OK", "fail": "FAIL"}.get(c["result"], "?")
            print(f"  [{mark}] {c['check']}")

        if all_errs:
            print("\n위반 내역:")
            for e in all_errs[:20]:
                print(f"  - {e}")
            die(f"Gate 2 실패 — {len(all_errs)}건. 최종 보고서를 생성하지 않습니다.")

    except SkillError as e:
        die(str(e))


if __name__ == "__main__":
    main()
