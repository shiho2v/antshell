#!/usr/bin/env python3
"""DART 재무제표 수집 (fnlttSinglAcntAll) — 원시 데이터만 저장한다.

**여기서는 계산하지 않는다.** 누적→분기단독 차분과 지표 계산은
normalize_data.py / calculate_metrics.py 의 책임이다 (계산과 수집의 분리).

핵심 사실 (design-review.md 2.3, 2.4):
  - reprt_code 11012 는 2분기가 아니라 **반기**다.
  - 분기보고서 금액은 **누적(YTD)이 기본**이며 thstrm_add_amount 는 누락이 잦다.
    → 분기 단독값은 normalize 단계에서 **연속 누적 보고서 차분**으로 파생한다.
  - fnlttSinglAcntAll 은 fs_div 가 **필수**다. CFS 우선, 없으면 OFS 폴백하며
    **폴백 사실을 기록**한다. 하나의 계산식에서 CFS/OFS 를 섞지 않는다.
  - 모든 행에 rcept_no 가 있다 → 모든 수치에 접수번호를 붙일 수 있다.

사용법:
    python fetch_dart_financials.py 009150
    python fetch_dart_financials.py 009150 --years 4

출력:
    data/raw/{ticker}_dart_financials.json
"""
from __future__ import annotations

import argparse
from datetime import date

from _common import (
    DartNoData,
    REPRT_ANNUAL,
    REPRT_HALF,
    REPRT_LABELS,
    REPRT_Q1,
    REPRT_Q3,
    SkillError,
    dart_get_json,
    die,
    log,
    now_iso,
    raw_path,
    read_json,
    validate_ticker,
    write_json,
)

# 저장할 재무제표 구분. SCE(자본변동표)는 본 스킬의 지표에 쓰이지 않아 제외한다.
KEEP_SJ = {"BS", "IS", "CIS", "CF"}

# 분기 보고서 코드를 회계연도 내 순서대로 (누적 차분의 전제)
QUARTER_SEQUENCE = [REPRT_Q1, REPRT_HALF, REPRT_Q3, REPRT_ANNUAL]


def fetch_one(corp_code: str, year: int, reprt_code: str, fs_div: str) -> dict | None:
    """단일 (연도, 보고서, 연결구분) 재무제표. 데이터 없으면 None (0 아님)."""
    try:
        d = dart_get_json("fnlttSinglAcntAll.json", {
            "corp_code": corp_code,
            "bsns_year": str(year),
            "reprt_code": reprt_code,
            "fs_div": fs_div,
        })
    except DartNoData:
        return None

    rows = [r for r in d.get("list", []) if (r.get("sj_div") or "") in KEEP_SJ]
    if not rows:
        return None

    # 이 보고서의 접수번호 (행마다 동일하지만 방어적으로 첫 행에서 취한다)
    rcept_no = next((r.get("rcept_no") for r in rows if r.get("rcept_no")), None)

    return {
        "bsns_year": year,
        "reprt_code": reprt_code,
        "reprt_label": REPRT_LABELS[reprt_code],
        "fs_div": fs_div,
        "rcept_no": rcept_no,
        "currency": next((r.get("currency") for r in rows if r.get("currency")), None),
        "row_count": len(rows),
        # 원시 행을 그대로 보존한다. 여기서 값을 해석하거나 변환하지 않는다.
        "rows": [
            {
                "sj_div": r.get("sj_div"),
                "sj_nm": r.get("sj_nm"),
                "account_id": r.get("account_id"),
                "account_nm": r.get("account_nm"),
                "thstrm_nm": r.get("thstrm_nm"),
                "thstrm_amount": r.get("thstrm_amount"),
                "thstrm_add_amount": r.get("thstrm_add_amount"),
                "frmtrm_nm": r.get("frmtrm_nm"),
                "frmtrm_amount": r.get("frmtrm_amount"),
                "frmtrm_q_nm": r.get("frmtrm_q_nm"),
                "frmtrm_q_amount": r.get("frmtrm_q_amount"),
                "frmtrm_add_amount": r.get("frmtrm_add_amount"),
                "bfefrmtrm_nm": r.get("bfefrmtrm_nm"),
                "bfefrmtrm_amount": r.get("bfefrmtrm_amount"),
                "ord": r.get("ord"),
                "currency": r.get("currency"),
                "rcept_no": r.get("rcept_no"),
            }
            for r in rows
        ],
    }


def resolve_fs_div(corp_code: str, year: int) -> tuple[str, bool]:
    """연결(CFS) 우선, 없으면 별도(OFS) 폴백. (fs_div, fallback_used) 반환."""
    probe = fetch_one(corp_code, year, REPRT_ANNUAL, "CFS")
    if probe:
        return "CFS", False
    probe = fetch_one(corp_code, year, REPRT_ANNUAL, "OFS")
    if probe:
        return "OFS", True
    raise SkillError(
        f"{year} 사업보고서를 CFS·OFS 어느 쪽으로도 조회하지 못했습니다. "
        "종목코드/공시 여부를 확인하세요."
    )


def main() -> None:
    ap = argparse.ArgumentParser(description="DART 재무제표 수집 (원시)")
    ap.add_argument("ticker")
    ap.add_argument("--years", type=int, default=4,
                    help="수집할 회계연도 수 (3년 CAGR 에 최소 4개 연말값이 필요하므로 기본 4)")
    args = ap.parse_args()

    try:
        ticker = validate_ticker(args.ticker)
        ident = read_json(raw_path(ticker, "identity"))
        corp_code = ident["corp_code"]

        this_year = date.today().year
        # 당해 사업보고서는 아직 미공시일 수 있으므로 직전 연도를 기준으로 fs_div 를 정한다.
        fs_div, fallback = resolve_fs_div(corp_code, this_year - 1)
        if fallback:
            log("연결재무제표(CFS)가 없어 별도(OFS)로 폴백합니다. "
                "**보고서에 별도 기준임을 명시해야 합니다.**")
        else:
            log("연결재무제표(CFS) 기준으로 수집합니다.")

        annual: list[dict] = []
        quarterly: list[dict] = []

        # ── 연간 (CAGR·TTM 기준) ────────────────────────────────────────────
        for year in range(this_year, this_year - args.years - 2, -1):
            rec = fetch_one(corp_code, year, REPRT_ANNUAL, fs_div)
            if rec:
                annual.append(rec)
                log(f"연간 {year} 사업보고서 수집 ({rec['row_count']}행, "
                    f"rcept_no={rec['rcept_no']})")
            if len(annual) >= args.years:
                break

        # ── 분기 (누적) — 차분의 재료. 최근 2개 회계연도를 모두 채운다 ────────
        # YoY 분기 비교를 하려면 당해와 전년의 같은 분기 누적이 모두 필요하다.
        for year in range(this_year, this_year - 3, -1):
            for rc in QUARTER_SEQUENCE:
                if rc == REPRT_ANNUAL:
                    continue  # 연간은 위에서 이미 수집 (Q4 차분에 재사용)
                rec = fetch_one(corp_code, year, rc, fs_div)
                if rec:
                    quarterly.append(rec)
                    log(f"분기 {year} {rec['reprt_label']} 수집 (누적 기준, "
                        f"rcept_no={rec['rcept_no']})")

        if not annual:
            raise SkillError(
                "사업보고서를 하나도 조회하지 못했습니다. "
                "성장성·품질·밸류에이션 모듈을 실행할 수 없습니다."
            )

        result = {
            "ticker": ticker,
            "corp_code": corp_code,
            "fs_div": fs_div,
            "fs_div_fallback": fallback,
            "fs_div_note": (
                "연결(CFS) 기준" if not fallback else
                "**별도(OFS) 기준** — 연결재무제표가 존재하지 않아 폴백했다. "
                "연결 기준 수치와 혼용해서는 안 된다."
            ),
            "cumulative_warning": (
                "분기보고서 금액은 누적(YTD)이다. 분기 단독값은 normalize_data.py 가 "
                "연속 누적 보고서를 차분해 파생한다. thstrm_add_amount 를 신뢰하지 않는다."
            ),
            "annual": annual,
            "quarterly": quarterly,
            "source": {
                "provider": "dart",
                "source_type": "official_api",
                "endpoint_or_function": "fnlttSinglAcntAll.json",
                "retrieved_at": now_iso(),
            },
        }

        out = write_json(raw_path(ticker, "dart_financials"), result)
        print(f"저장: {out}")
        print(f"  기준: {fs_div}{' (폴백)' if fallback else ''} / "
              f"연간 {len(annual)}개 / 분기(누적) {len(quarterly)}개")

    except SkillError as e:
        die(str(e))


if __name__ == "__main__":
    main()
