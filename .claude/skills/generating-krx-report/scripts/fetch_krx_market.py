#!/usr/bin/env python3
"""시세·수급·지수 수집 (pykrx) — **비공식 경로임을 명시한다**.

design-review.md 3장의 사실:
  - pykrx 는 KRX/Naver 와 무관한 third-party 스크레이퍼다 → source_type=unofficial_wrapper
  - 2026-07 기준 data.krx.co.kr 은 익명 호출에 400 LOGOUT 을 반환한다.
    → KRX 백엔드를 쓰는 함수는 **전부 KRX_ID/KRX_PW 가 필요**하다.
  - **유일한 예외**: get_market_ohlcv(adjusted=True, 기본값) 은 Naver Finance 를 긁으므로
    자격증명 없이 동작한다.

따라서 자격증명이 없으면:
  OHLCV                  ✅ (Naver 경유)
  수급 (CANSLIM I)       ❌ N/A   ← **0점으로 채점하지 않는다**
  지수 (CANSLIM M, L)    ❌ N/A   ← **0점으로 채점하지 않는다**
  KRX 공표 PER/PBR       ❌ N/A   (DART 기반 자체 계산으로 대체)

시가총액은 pykrx 에 의존하지 않는다 — `종가 × 발행주식수(DART)` 로 calculate_metrics.py 가 계산한다.

사용법:
    python fetch_krx_market.py 009150
    python fetch_krx_market.py 009150 --days 400

출력:
    data/raw/{ticker}_krx_market.json
"""
from __future__ import annotations

import argparse
from datetime import date, timedelta

from _common import (
    SkillError,
    die,
    has_krx_login,
    log,
    now_iso,
    raw_path,
    validate_ticker,
    write_json,
)

KOSPI_INDEX = "1001"
KOSDAQ_INDEX = "2001"


def _import_pykrx():
    try:
        from pykrx import stock
    except ImportError as e:
        raise SkillError("pykrx 가 설치되지 않았습니다: pip install pykrx") from e
    return stock


def fetch_ohlcv(stock_mod, ticker: str, fromdate: str, todate: str) -> dict:
    """수정주가 OHLCV. adjusted=True(기본) → Naver Finance 경유 (자격증명 불필요)."""
    try:
        df = stock_mod.get_market_ohlcv(fromdate, todate, ticker)
    except Exception as e:
        raise SkillError(f"OHLCV 조회 실패: {e}") from e

    if df is None or df.empty:
        raise SkillError(
            f"종목 {ticker} 의 OHLCV 가 비어 있습니다. 상장 여부/코드를 확인하세요."
        )

    df = df[df["종가"] > 0].dropna(subset=["종가"])
    if df.empty:
        raise SkillError(f"종목 {ticker} 의 유효한 종가가 없습니다.")

    closes = [
        {"date": idx.strftime("%Y-%m-%d"),
         "close": float(r["종가"]),
         "high": float(r["고가"]),
         "low": float(r["저가"]),
         "volume": float(r["거래량"])}
        for idx, r in df.iterrows()
    ]
    return {
        "as_of": closes[-1]["date"],
        "series": closes,
        "trading_days": len(closes),
        "source": {
            "provider": "pykrx",
            "source_type": "unofficial_wrapper",
            "underlying_source": "Naver Finance (pykrx adjusted=True 기본값)",
            "endpoint_or_function": "get_market_ohlcv",
            "retrieved_at": now_iso(),
        },
    }


def fetch_investor_flow(stock_mod, ticker: str, fromdate: str, todate: str) -> dict | None:
    """투자자별 순매수 (CANSLIM I). KRX 로그인 필요 — 없으면 None (**0 아님**)."""
    if not has_krx_login():
        log("KRX_ID/KRX_PW 없음 → 수급(CANSLIM I) = N/A. 0점으로 채점하지 않습니다.")
        return None
    try:
        df = stock_mod.get_market_trading_value_by_date(fromdate, todate, ticker)
    except Exception as e:
        log(f"수급 조회 실패 → N/A 처리: {e}")
        return None
    if df is None or df.empty:
        log("수급 응답이 비어 있음 → N/A")
        return None

    def pick(*names):
        for n in names:
            if n in df.columns:
                return n
        return None

    inst_c = pick("기관합계", "기관")
    for_c = pick("외국인합계", "외국인")
    tail = df.tail(60)

    return {
        "window_days": int(len(tail)),
        "inst_net": float(tail[inst_c].sum()) if inst_c else None,
        "foreign_net": float(tail[for_c].sum()) if for_c else None,
        "unit": "KRW (거래대금 순매수)",
        "source": {
            "provider": "pykrx",
            "source_type": "unofficial_wrapper",
            "underlying_source": "KRX (data.krx.co.kr, 로그인 필요)",
            "endpoint_or_function": "get_market_trading_value_by_date",
            "retrieved_at": now_iso(),
        },
    }


def fetch_index(stock_mod, market: str, fromdate: str, todate: str) -> dict | None:
    """지수 OHLCV (CANSLIM M, L). KRX 로그인 필요 — 없으면 None."""
    if not has_krx_login():
        log("KRX_ID/KRX_PW 없음 → 지수(CANSLIM M·L) = N/A. 0점으로 채점하지 않습니다.")
        return None

    idx = KOSDAQ_INDEX if market == "KOSDAQ" else KOSPI_INDEX
    try:
        df = stock_mod.get_index_ohlcv(fromdate, todate, idx)
    except Exception as e:
        log(f"지수 조회 실패 → N/A 처리: {e}")
        return None
    if df is None or df.empty:
        log("지수 응답이 비어 있음 → N/A")
        return None

    series = [
        {"date": i.strftime("%Y-%m-%d"), "close": float(r["종가"])}
        for i, r in df.iterrows() if float(r["종가"]) > 0
    ]
    if not series:
        return None

    return {
        "index_code": idx,
        "index_name": "KOSDAQ" if idx == KOSDAQ_INDEX else "KOSPI",
        "as_of": series[-1]["date"],
        "series": series,
        "source": {
            "provider": "pykrx",
            "source_type": "unofficial_wrapper",
            "underlying_source": "KRX (로그인 필요)",
            "endpoint_or_function": "get_index_ohlcv",
            "retrieved_at": now_iso(),
        },
    }


def fetch_krx_market_cap(stock_mod, ticker: str, fromdate: str, todate: str) -> dict | None:
    """KRX 공표 시가총액·상장주식수. **교차검증용** (자격증명 필요).

    본 스킬은 시가총액을 `종가 × 보통주 발행주식수(DART)` 로 자체 계산한다.
    KRX 공표값과 대조하면 주식 종류(보통주/우선주) 혼동 같은 오류를 자동으로 잡을 수 있다.
    """
    if not has_krx_login():
        return None
    try:
        df = stock_mod.get_market_cap(fromdate, todate, ticker)
    except Exception as e:
        log(f"KRX 시가총액 조회 실패 → 교차검증 생략: {e}")
        return None
    if df is None or df.empty:
        return None

    r = df.iloc[-1]
    try:
        return {
            "market_cap": float(r["시가총액"]),
            "listed_shares": float(r["상장주식수"]),
            "as_of": df.index[-1].strftime("%Y-%m-%d"),
            "purpose": "교차검증 전용 — 본문 시가총액은 DART 주식수 기반 자체 계산값을 쓴다",
            "source": {
                "provider": "pykrx",
                "source_type": "unofficial_wrapper",
                "underlying_source": "KRX (로그인 필요)",
                "endpoint_or_function": "get_market_cap",
                "retrieved_at": now_iso(),
            },
        }
    except (KeyError, TypeError, ValueError) as e:
        log(f"KRX 시가총액 파싱 실패 → 교차검증 생략: {e}")
        return None


def fetch_krx_fundamental(stock_mod, ticker: str, todate: str) -> dict | None:
    """KRX 공표 PER/PBR/EPS/BPS/DIV. 로그인 필요.

    **주의**: 최근 확정 재무제표 기준이라 분기 갱신이 지연된다.
    본문 Trailing PER 로 쓰지 않고 **교차검증·역사적 밴드**에만 쓴다.
    """
    if not has_krx_login():
        return None
    try:
        df = stock_mod.get_market_fundamental(todate, todate, ticker)
    except Exception as e:
        log(f"KRX 공표 밸류에이션 조회 실패 → N/A: {e}")
        return None
    if df is None or df.empty:
        return None

    r = df.iloc[-1]
    def g(c):
        try:
            v = float(r[c])
            return v if v > 0 else None
        except (KeyError, TypeError, ValueError):
            return None

    return {
        "per": g("PER"), "pbr": g("PBR"), "eps": g("EPS"),
        "bps": g("BPS"), "div": g("DIV"), "dps": g("DPS"),
        "caveat": (
            "KRX 가 공표한 값의 패스스루다. 최근 확정 재무제표 기준이므로 "
            "최신 분기를 반영하지 않을 수 있다. 본문 Trailing PER 은 DART 기반 자체 계산값을 쓰고, "
            "이 값과 차이가 나면 counter_evidence 로 병기한다."
        ),
        "source": {
            "provider": "pykrx",
            "source_type": "unofficial_wrapper",
            "underlying_source": "KRX 공표 지표 (로그인 필요)",
            "endpoint_or_function": "get_market_fundamental",
            "retrieved_at": now_iso(),
        },
    }


def main() -> None:
    ap = argparse.ArgumentParser(description="시세·수급·지수 수집 (pykrx, 비공식)")
    ap.add_argument("ticker")
    ap.add_argument("--days", type=int, default=420,
                    help="조회 기간(일). 52주 고가·200일선 계산에 여유가 필요하다.")
    args = ap.parse_args()

    try:
        ticker = validate_ticker(args.ticker)

        # 시장구분은 identity 가 있으면 쓰고, 없으면 KOSPI 지수를 기본으로 한다.
        market = "KOSPI"
        idp = raw_path(ticker, "identity")
        if idp.exists():
            from _common import read_json
            market = read_json(idp).get("market") or "KOSPI"

        stock_mod = _import_pykrx()

        today = date.today()
        todate = today.strftime("%Y%m%d")
        fromdate = (today - timedelta(days=args.days)).strftime("%Y%m%d")

        krx_login = has_krx_login()
        if not krx_login:
            log("KRX 자격증명 없음 → OHLCV 만 수집합니다 (pykrx→Naver, 비공식).")

        ohlcv = fetch_ohlcv(stock_mod, ticker, fromdate, todate)
        log(f"OHLCV {ohlcv['trading_days']}일 수집 (as_of={ohlcv['as_of']})")

        flow = fetch_investor_flow(stock_mod, ticker, fromdate, todate)
        index = fetch_index(stock_mod, market, fromdate, todate)
        krx_fund = fetch_krx_fundamental(stock_mod, ticker, todate)
        krx_cap = fetch_krx_market_cap(stock_mod, ticker, fromdate, todate)

        result = {
            "ticker": ticker,
            "market": market,
            "as_of": ohlcv["as_of"],
            "krx_login_available": krx_login,
            "ohlcv": ohlcv,
            "investor_flow": flow,
            "index": index,
            "krx_published_valuation": krx_fund,
            "krx_market_cap_crosscheck": krx_cap,
            "na_items": [
                item for item, val in [
                    ("investor_flow (CANSLIM I)", flow),
                    ("index (CANSLIM M, L)", index),
                    ("krx_published_valuation", krx_fund),
                    ("krx_market_cap_crosscheck", krx_cap),
                ] if val is None
            ],
            "na_reason": (
                None if krx_login else
                "KRX_ID/KRX_PW 미설정. data.krx.co.kr 이 익명 호출을 거부하므로 "
                "수급·지수·KRX 공표지표를 조회할 수 없다. **N/A 이며 0 이 아니다.**"
            ),
            "provenance_warning": (
                "pykrx 는 KRX/Naver 와 무관한 비공식 래퍼다. "
                "모든 evidence 는 source_type=unofficial_wrapper 로 기록된다."
            ),
        }

        out = write_json(raw_path(ticker, "krx_market"), result)
        print(f"저장: {out}")
        print(f"  as_of={result['as_of']} / 영업일 {ohlcv['trading_days']}일 / "
              f"KRX 로그인={'있음' if krx_login else '없음'}")
        if result["na_items"]:
            print(f"  N/A 항목: {', '.join(result['na_items'])}")

    except SkillError as e:
        die(str(e))


if __name__ == "__main__":
    main()
