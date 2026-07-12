#!/usr/bin/env python3
"""DART 공시 사건 수집 — catalyst / risk 모듈의 **유일한 근거원**.

공시에 없는 촉매는 등재할 수 없다 (config/module-registry.yaml: CAT-01).
뉴스·추측으로 촉매를 만들지 않는다.

수집 대상:
  - list.json               정기·주요사항·발행 공시 목록 (rcept_no + 제목 + 접수일)
  - tesstkAcqsDspsSttus     자기주식 취득·처분 (자사주 촉매)
  - irdsSttus               증자·감자 (희석 위험)
  - alotMatter              배당

사용법:
    python fetch_dart_events.py 009150
    python fetch_dart_events.py 009150 --months 18

출력:
    data/raw/{ticker}_dart_events.json
"""
from __future__ import annotations

import argparse
from datetime import date, timedelta

from _common import (
    DartNoData,
    REPRT_ANNUAL,
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

# 촉매 후보를 식별하기 위한 공시 제목 키워드.
# **분류 힌트일 뿐 촉매를 확정하지 않는다.** 판단은 Claude 가 rubric 으로 한다.
CATALYST_KEYWORDS = {
    "신규수주": ["공급계약", "수주", "계약체결"],
    "설비투자": ["신규시설투자", "시설투자", "증설"],
    "자사주": ["자기주식", "자사주"],
    "지배구조": ["합병", "분할", "영업양수", "영업양도", "주식양수", "주식양도"],
    "자본변동": ["유상증자", "무상증자", "전환사채", "신주인수권", "교환사채", "감자"],
    "손익": ["영업(잠정)실적", "잠정실적", "매출액또는손익구조"],
    "배당": ["현금·현물배당", "배당"],
}

# 공시유형 (pblntf_ty): A=정기, B=주요사항, C=발행, D=지분, E=기타, F=외부감사, ...
EVENT_TYPES = ["A", "B", "C"]


def classify(report_nm: str) -> list[str]:
    """제목 키워드로 태그를 붙인다. 촉매 확정이 아니라 **후보 분류**다."""
    return [
        tag for tag, kws in CATALYST_KEYWORDS.items()
        if any(k in report_nm for k in kws)
    ]


def fetch_disclosures(corp_code: str, months: int) -> list[dict]:
    bgn = (date.today() - timedelta(days=months * 31)).strftime("%Y%m%d")
    end = date.today().strftime("%Y%m%d")

    events: list[dict] = []
    for ty in EVENT_TYPES:
        page = 1
        while page <= 3:  # 페이지 상한 — 무한 루프 방지
            try:
                d = dart_get_json("list.json", {
                    "corp_code": corp_code,
                    "bgn_de": bgn,
                    "end_de": end,
                    "pblntf_ty": ty,
                    "page_no": str(page),
                    "page_count": "100",
                })
            except DartNoData:
                break  # 이 유형에 공시가 없다. 정상.

            for r in d.get("list", []):
                nm = r.get("report_nm", "")
                events.append({
                    "rcept_no": r.get("rcept_no"),
                    "report_nm": nm,
                    "rcept_dt": r.get("rcept_dt"),
                    "flr_nm": r.get("flr_nm"),
                    "pblntf_ty": ty,
                    "tags": classify(nm),
                    "url": f"https://dart.fss.or.kr/dsaf001/main.do?rcpNo={r.get('rcept_no')}",
                })

            total_page = int(d.get("total_page", 1) or 1)
            if page >= total_page:
                break
            page += 1

    events.sort(key=lambda e: e.get("rcept_dt") or "", reverse=True)
    return events


def fetch_periodic(corp_code: str, endpoint: str, label: str) -> dict | None:
    """DS002 정기보고서 주요정보 — 최근 사업보고서 기준. 없으면 None."""
    this_year = date.today().year
    for year in range(this_year, this_year - 3, -1):
        try:
            d = dart_get_json(endpoint, {
                "corp_code": corp_code,
                "bsns_year": str(year),
                "reprt_code": REPRT_ANNUAL,
            })
        except DartNoData:
            continue
        rows = d.get("list", [])
        if rows:
            log(f"{label}: {len(rows)}행 ({year} 사업보고서)")
            return {"bsns_year": year, "rows": rows}
    log(f"{label}: 데이터 없음 (N/A)")
    return None


def main() -> None:
    ap = argparse.ArgumentParser(description="DART 공시 사건 수집")
    ap.add_argument("ticker")
    ap.add_argument("--months", type=int, default=12, help="공시 조회 기간(개월)")
    args = ap.parse_args()

    try:
        ticker = validate_ticker(args.ticker)
        ident = read_json(raw_path(ticker, "identity"))
        corp_code = ident["corp_code"]

        disclosures = fetch_disclosures(corp_code, args.months)
        log(f"공시 {len(disclosures)}건 수집 (최근 {args.months}개월)")

        tagged = [e for e in disclosures if e["tags"]]
        log(f"촉매 후보 태그가 붙은 공시: {len(tagged)}건 "
            "(**후보일 뿐 촉매로 확정된 것이 아니다**)")

        result = {
            "ticker": ticker,
            "corp_code": corp_code,
            "period_months": args.months,
            "disclosures": disclosures,
            "catalyst_candidates": tagged,
            "treasury_stock": fetch_periodic(
                corp_code, "tesstkAcqsDspsSttus.json", "자기주식 취득·처분"),
            "capital_changes": fetch_periodic(
                corp_code, "irdsSttus.json", "증자·감자"),
            "dividends": fetch_periodic(
                corp_code, "alotMatter.json", "배당"),
            "note": (
                "공시에 없는 촉매는 등재할 수 없다. 태그는 제목 키워드 기반 후보 분류이며 "
                "촉매 확정이 아니다. 각 촉매는 rcept_no 로 공시 근거를 제시해야 한다."
            ),
            "source": {
                "provider": "dart",
                "source_type": "official_api",
                "endpoint_or_function": (
                    "list.json + tesstkAcqsDspsSttus.json + irdsSttus.json + alotMatter.json"
                ),
                "retrieved_at": now_iso(),
            },
        }

        out = write_json(raw_path(ticker, "dart_events"), result)
        print(f"저장: {out}")
        print(f"  공시 {len(disclosures)}건 / 촉매 후보 {len(tagged)}건")

    except SkillError as e:
        die(str(e))


if __name__ == "__main__":
    main()
