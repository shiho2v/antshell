#!/usr/bin/env python3
"""DART 기업 프로필 수집 — 기업개황 + 주식총수(발행주식수).

발행주식수는 **시가총액 계산의 공식 출처**다 (stockTotqySttus).
KRX 자격증명이 없어도 `종가 × 발행주식수` 로 시가총액을 얻을 수 있게 해주는 핵심 데이터다.

사업부문·생산능력·원재료·수주잔고는 **구조화 API 가 존재하지 않는다**
(design-review.md 2.7). 유일한 공식 경로는 사업보고서 원문(document.xml)이며,
`--with-document` 로 옵트인할 때만 「II. 사업의 내용」 텍스트를 추출해 저장한다.
**자동으로 수치를 뽑아내지 않는다.** Claude 가 정성 근거로만 인용한다.

사용법:
    python fetch_dart_profile.py 009150
    python fetch_dart_profile.py 009150 --with-document

출력:
    data/raw/{ticker}_dart_profile.json
    data/raw/{ticker}_business_section.txt   (--with-document 일 때만)
"""
from __future__ import annotations

import argparse
import re
import sys
from datetime import date

from _common import (
    DartNoData,
    REPRT_ANNUAL,
    SkillError,
    clean_number,
    dart_get_json,
    dart_get_zip,
    die,
    log,
    now_iso,
    RAW_DIR,
    raw_path,
    read_json,
    validate_ticker,
    write_json,
)

MAX_SECTION_CHARS = 60_000   # 원문 섹션 저장 상한 (토큰 폭주 방지)


def fetch_company(corp_code: str) -> dict:
    try:
        d = dart_get_json("company.json", {"corp_code": corp_code})
    except DartNoData as e:
        raise SkillError(f"기업개황 없음: {e}") from e
    return {k: v for k, v in d.items() if k not in ("status", "message")}


def _parse_shares_row(rows: list[dict], year: int) -> dict | None:
    """주식 종류별(se) 행을 분해한다. **보통주와 우선주를 반드시 구분한다.**

    실제 공시(삼성전기 2025 사업보고서)에서 확인:
        의결권이 있는주식(보통주)  istc_totqy = 74,693,696   ← KRX 상장주식수와 일치
        의결권이 없는주식(우선주)  istc_totqy =  2,906,984
        합계                      istc_totqy = 77,600,680

    **'합계' 를 시가총액 계산에 쓰면 안 된다.** 우리가 가진 주가는 *보통주* 종가이므로,
    합계(보통주+우선주)를 곱하면 시가총액이 과대계상된다(이 사례에서 약 +3.9%).
    보통주 주식수를 쓰면 KRX 공표 시가총액과 정확히 일치한다:
        1,584,000 × 74,693,696 = 118,314,814,464,000  (= KRX get_market_cap)

    따라서 issued_shares(시가총액용) = **보통주** 주식수로 고정한다.
    우선주 존재 사실은 별도로 보존해 limitation 으로 노출한다.
    """
    def find(*keys):
        for r in rows:
            se = (r.get("se") or "")
            if any(k in se for k in keys) and clean_number(r.get("istc_totqy")) is not None:
                return r
        return None

    common = find("보통주")
    preferred = find("우선주")
    total = find("합계")

    # 보통주 행이 없으면(단일 종류 발행) 합계를 보통주로 간주한다.
    base = common or total
    if base is None:
        return None

    common_shares = clean_number(base.get("istc_totqy"))
    if common_shares is None:
        return None

    preferred_shares = clean_number(preferred.get("istc_totqy")) if preferred else None
    total_shares = clean_number(total.get("istc_totqy")) if total else common_shares

    return {
        "bsns_year": year,
        "reprt_code": REPRT_ANNUAL,
        "se": base.get("se"),
        # 시가총액 계산에 쓰는 값 = 보통주 주식수 (KRX 상장주식수 정의와 일치)
        "issued_shares": common_shares,
        "common_shares": common_shares,
        "preferred_shares": preferred_shares,
        "total_shares_all_classes": total_shares,
        "has_preferred": bool(preferred_shares),
        "treasury_shares": clean_number(base.get("tesstk_co")),
        "distributed_shares": clean_number(base.get("distb_stock_co")),
        "rcept_no": base.get("rcept_no"),
    }


def fetch_shares(corp_code: str, years_back: int = 3) -> dict:
    """주식총수(stockTotqySttus) — 최근 사업보고서부터 역순으로 여러 해를 수집한다.

    최신 스냅샷 하나만으로는 **주식 희석(share_change_1y)을 계산할 수 없다.**
    연도별 스냅샷을 모아 두어야 발행주식수 증가율을 구할 수 있다.
    당해 사업보고서는 미공시일 수 있으므로 과거로 내려가며 수집한다.
    """
    this_year = date.today().year
    history: list[dict] = []

    for year in range(this_year, this_year - years_back - 2, -1):
        try:
            d = dart_get_json("stockTotqySttus.json", {
                "corp_code": corp_code,
                "bsns_year": str(year),
                "reprt_code": REPRT_ANNUAL,
            })
        except DartNoData:
            continue  # 013 = 데이터 없음. 오류 아님. 다음 해로.

        parsed = _parse_shares_row(d.get("list", []), year)
        if parsed:
            history.append(parsed)
        if len(history) >= years_back:
            break

    if not history:
        raise SkillError(
            "주식총수(stockTotqySttus)를 최근 사업보고서에서 찾지 못했습니다. "
            "시가총액·PER·PBR 계산이 불가하며 밸류에이션 모듈이 N/A 가 됩니다."
        )

    history.sort(key=lambda h: h["bsns_year"], reverse=True)
    latest = dict(history[0])
    latest["history"] = history       # 희석 계산용 (연도별 발행주식수)
    return latest


def fetch_business_section(corp_code: str) -> dict | None:
    """사업보고서 원문에서 「II. 사업의 내용」 텍스트를 추출한다 (옵트인).

    구조화 API 가 없는 항목(사업부문별 매출·생산능력·가동률·원재료·수주잔고)의
    **유일한 공식 경로**다. source_type = official_filing.
    수치를 자동 추출하지 않는다 — 텍스트를 그대로 저장하고 Claude 가 읽는다.
    """
    # 1) 최근 사업보고서의 접수번호를 찾는다
    try:
        lst = dart_get_json("list.json", {
            "corp_code": corp_code,
            "bgn_de": f"{date.today().year - 2}0101",
            "end_de": date.today().strftime("%Y%m%d"),
            "pblntf_ty": "A",        # 정기공시
            "page_count": "100",
        })
    except DartNoData:
        log("정기공시 목록이 없어 원문 추출을 건너뜁니다.")
        return None

    reports = [
        r for r in lst.get("list", [])
        if "사업보고서" in (r.get("report_nm") or "")
    ]
    if not reports:
        log("사업보고서를 찾지 못해 원문 추출을 건너뜁니다.")
        return None

    reports.sort(key=lambda r: r.get("rcept_dt", ""), reverse=True)
    rcept_no = reports[0]["rcept_no"]
    report_nm = reports[0]["report_nm"]

    # 2) 원문 ZIP 내려받기
    try:
        zf = dart_get_zip("document.xml", {"rcept_no": rcept_no})
    except DartNoData:
        log(f"원문 문서 없음 (rcept_no={rcept_no}).")
        return None

    names = zf.namelist()
    if not names:
        return None
    raw = zf.read(names[0])

    # DART 원문은 EUC-KR 또는 UTF-8
    text = None
    for enc in ("utf-8", "euc-kr", "cp949"):
        try:
            text = raw.decode(enc)
            break
        except UnicodeDecodeError:
            continue
    if text is None:
        log("원문 인코딩을 해독하지 못했습니다.")
        return None

    # 3) 태그 제거 → 「II. 사업의 내용」 섹션 슬라이스
    plain = re.sub(r"<[^>]+>", " ", text)
    plain = re.sub(r"&[a-zA-Z#0-9]+;", " ", plain)
    plain = re.sub(r"[ \t]+", " ", plain)
    plain = re.sub(r"\n\s*\n+", "\n", plain)

    start = re.search(r"(II\.|Ⅱ\.)\s*사업의\s*내용", plain)
    end = re.search(r"(III\.|Ⅲ\.)\s*재무에\s*관한\s*사항", plain)
    if start:
        section = plain[start.start(): end.start() if end and end.start() > start.start() else None]
    else:
        log("「II. 사업의 내용」 섹션 경계를 찾지 못해 원문 앞부분을 저장합니다.")
        section = plain

    truncated = len(section) > MAX_SECTION_CHARS
    section = section[:MAX_SECTION_CHARS]

    return {
        "rcept_no": rcept_no,
        "report_nm": report_nm,
        "rcept_dt": reports[0].get("rcept_dt"),
        "section_text": section,
        "truncated": truncated,
        "chars": len(section),
    }


def main() -> None:
    ap = argparse.ArgumentParser(description="DART 기업개황 + 주식총수 수집")
    ap.add_argument("ticker")
    ap.add_argument("--with-document", action="store_true",
                    help="사업보고서 원문의 「II. 사업의 내용」 텍스트를 추출한다 "
                         "(구조화 API 가 없는 사업부문·가동률·원재료·수주잔고의 유일한 공식 경로)")
    args = ap.parse_args()

    try:
        ticker = validate_ticker(args.ticker)
        ident = read_json(raw_path(ticker, "identity"))
        corp_code = ident["corp_code"]

        company = fetch_company(corp_code)
        log(f"기업개황 수집 완료: {company.get('corp_name')}")

        shares = fetch_shares(corp_code)
        log(f"주식총수: 발행 {shares['issued_shares']:,.0f}주 "
            f"(기준 {shares['bsns_year']} 사업보고서, rcept_no={shares['rcept_no']})")

        result = {
            "ticker": ticker,
            "corp_code": corp_code,
            "company": company,
            "shares": shares,
            "business_section": None,
            "source": {
                "provider": "dart",
                "source_type": "official_api",
                "endpoint_or_function": "company.json + stockTotqySttus.json",
                "retrieved_at": now_iso(),
            },
        }

        if args.with_document:
            log("사업보고서 원문 추출 중 (official_filing)...")
            sec = fetch_business_section(corp_code)
            if sec:
                txt_path = RAW_DIR / f"{ticker}_business_section.txt"
                txt_path.parent.mkdir(parents=True, exist_ok=True)
                txt_path.write_text(sec.pop("section_text"), encoding="utf-8")
                sec["text_path"] = str(txt_path)
                sec["source_type"] = "official_filing"
                result["business_section"] = sec
                log(f"원문 섹션 저장: {txt_path} ({sec['chars']:,}자"
                    f"{', 절단됨' if sec['truncated'] else ''})")
            else:
                log("원문 섹션을 추출하지 못했습니다. 사업부문 정보는 N/A 로 남습니다.")
        else:
            log("--with-document 미지정 → 사업부문·가동률·원재료·수주잔고는 N/A 로 남습니다.")

        out = write_json(raw_path(ticker, "dart_profile"), result)
        print(f"저장: {out}")

    except SkillError as e:
        die(str(e))


if __name__ == "__main__":
    main()
