#!/usr/bin/env python3
"""Gate 1 (Identity) — 종목 식별을 확정한다.

종목명↔6자리 코드 일치, 시장구분, DART corp_code, 보통주/우선주,
상장 상태를 확인한다. **실패하면 분석을 중단한다.**

사용법:
    python resolve_security.py 009150
    python resolve_security.py --name 삼성전기      # 이름으로 후보 검색 (확정하지 않음)

출력:
    data/raw/{ticker}_identity.json
"""
from __future__ import annotations

import argparse
import sys

from _common import (
    DartNoData,
    SkillError,
    credentials,
    die,
    load_corpcode_map,
    log,
    now_iso,
    raw_path,
    dart_get_json,
    validate_ticker,
    write_json,
)

# 우선주 판별: 6자리 코드의 마지막 자리가 0 이 아니면 우선주/신형우선주일 가능성이 높다.
# 이는 **경험칙**이며 확정 근거가 아니다. company.json 의 종목명으로 교차확인한다.
PREFERRED_MARKERS = ("우", "우B", "1우", "2우", "우선주")


def guess_share_class(corp_name: str, ticker: str) -> tuple[str, str]:
    """(share_class, basis). 확정 불가하면 '확인 필요'."""
    if any(m in corp_name for m in ("우B", "1우", "2우")) or corp_name.rstrip().endswith("우"):
        return "preferred", "종목명에 우선주 표기"
    if ticker.endswith("0"):
        return "common", "6자리 코드 말미 0 (경험칙) + 종목명에 우선주 표기 없음"
    return "확인 필요", "코드 말미가 0 이 아니며 종목명으로 확정 불가"


def resolve(ticker: str) -> dict:
    mapping = load_corpcode_map()
    entry = mapping.get(ticker)
    if not entry:
        raise SkillError(
            f"종목코드 {ticker} 를 DART 상장사 매핑에서 찾지 못했습니다.\n"
            "  - 6자리 코드가 정확한지 확인하세요.\n"
            "  - 상장폐지·코드변경 종목일 수 있습니다.\n"
            "  Gate 1(Identity) 실패 — 분석을 중단합니다."
        )

    corp_code = entry["corp_code"]
    corp_name = entry["corp_name"]

    # 기업개황으로 시장구분·상장상태 교차확인
    try:
        profile = dart_get_json("company.json", {"corp_code": corp_code})
    except DartNoData as e:
        raise SkillError(f"기업개황 조회 결과가 없습니다 ({ticker}). Gate 1 실패: {e}") from e

    corp_cls = profile.get("corp_cls", "")   # Y=유가(KOSPI), K=코스닥, N=코넥스, E=기타
    market = {"Y": "KOSPI", "K": "KOSDAQ", "N": "KONEX"}.get(corp_cls)
    if market is None:
        raise SkillError(
            f"시장구분을 확정할 수 없습니다 (corp_cls={corp_cls!r}). "
            "비상장/기타 법인일 수 있습니다. Gate 1 실패."
        )

    # DART 가 돌려준 종목코드가 요청과 같은지 (코드변경·합병 감지)
    dart_stock_code = (profile.get("stock_code") or "").strip()
    code_mismatch = bool(dart_stock_code) and dart_stock_code != ticker

    share_class, class_basis = guess_share_class(corp_name, ticker)

    checks = [
        {"check": "corp_code 매핑", "result": "pass", "detail": f"{ticker} → {corp_code}"},
        {"check": "시장구분", "result": "pass", "detail": f"{market} (corp_cls={corp_cls})"},
        {
            "check": "종목코드 일치",
            "result": "fail" if code_mismatch else "pass",
            "detail": f"DART stock_code={dart_stock_code or '(없음)'}",
        },
        {
            "check": "보통주/우선주",
            "result": "warn" if share_class == "확인 필요" else "pass",
            "detail": f"{share_class} — {class_basis}",
        },
        {
            "check": "상장상태",
            "result": "pass",
            "detail": "DART 상장사 매핑에 존재 (corpCode.xml)",
        },
    ]
    status = "failed" if any(c["result"] == "fail" for c in checks) else "passed"

    return {
        "ticker": ticker,
        "corp_code": corp_code,
        "company_name": profile.get("corp_name") or corp_name,
        "company_name_eng": profile.get("corp_name_eng"),
        "market": market,
        "corp_cls": corp_cls,
        "share_class": share_class,
        "share_class_basis": class_basis,
        "industry_code": profile.get("induty_code"),
        "established": profile.get("est_dt"),
        "fiscal_month": profile.get("acc_mt"),
        "ceo": profile.get("ceo_nm"),
        "homepage": profile.get("hm_url"),
        "code_mismatch": code_mismatch,
        "gate1": {"status": status, "checks": checks},
        "credentials_available": credentials(),
        "source": {
            "provider": "dart",
            "source_type": "official_api",
            "endpoint_or_function": "corpCode.xml + company.json",
            "retrieved_at": now_iso(),
        },
        "resolved_at": now_iso(),
    }


def search_by_name(name: str) -> list[dict]:
    """이름으로 후보를 **제시만** 한다. 자동 확정하지 않는다 (Gate 1: 종목명·코드 일치)."""
    mapping = load_corpcode_map()
    hits = [
        {"ticker": sc, "corp_name": v["corp_name"], "corp_code": v["corp_code"]}
        for sc, v in mapping.items()
        if name in v["corp_name"]
    ]
    return sorted(hits, key=lambda h: (len(h["corp_name"]), h["corp_name"]))[:10]


def main() -> None:
    ap = argparse.ArgumentParser(description="Gate 1 종목 식별 확정")
    ap.add_argument("ticker", nargs="?", help="6자리 종목코드 (예: 009150)")
    ap.add_argument("--name", help="종목명으로 후보 검색 (확정하지 않음)")
    args = ap.parse_args()

    try:
        if args.name:
            cands = search_by_name(args.name)
            if not cands:
                die(f"'{args.name}' 에 해당하는 상장사를 찾지 못했습니다.")
            print(f"'{args.name}' 후보 (자동 확정하지 않습니다 — 사용자 확인 필요):")
            for c in cands:
                print(f"  {c['ticker']}  {c['corp_name']}  (corp_code={c['corp_code']})")
            return

        if not args.ticker:
            die("종목코드 또는 --name 이 필요합니다.")

        ticker = validate_ticker(args.ticker)
        result = resolve(ticker)
        out = write_json(raw_path(ticker, "identity"), result)

        g = result["gate1"]
        print(f"[Gate 1: {g['status'].upper()}] {result['company_name']} ({ticker}) "
              f"/ {result['market']} / corp_code={result['corp_code']}")
        for c in g["checks"]:
            mark = {"pass": "OK", "fail": "FAIL", "warn": "WARN"}[c["result"]]
            print(f"  [{mark}] {c['check']}: {c['detail']}")
        print(f"저장: {out}")

        if g["status"] == "failed":
            die("Gate 1 실패 — 분석을 중단합니다.")

    except SkillError as e:
        die(str(e))


if __name__ == "__main__":
    main()
