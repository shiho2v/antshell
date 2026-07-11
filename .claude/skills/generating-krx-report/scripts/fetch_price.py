#!/usr/bin/env python3
# =============================================================
# File   : fetch_price.py
# Role   : pykrx로 최근 1년 OHLCV + 60일 평균 대비 거래량 비율 +
#          최근 60일 기관/외국인 순매수 합계를 조회해
#          data/{code}_market.json 생성
# Note   : 스터디 예제. 조용한 실패 금지 — 실패 시 명확한 에러로 종료.
# =============================================================
"""사용법:
    python fetch_price.py 009150

환경변수(선택):
    KRX_ID, KRX_PW  — 기관/외국인 순매수(수급, I 항목) 조회에 필요.
    미설정 시 시세(OHLCV·거래량)는 정상 수집되나 수급은 N/A로 남고
    supply_note에 사유가 기록된다(조용한 실패 금지). 사용하는 pykrx 빌드가
    import 시점에 이 환경변수를 읽으므로, 실행 전 셸에 export 되어 있어야 한다.

출력:
    data/{code}_market.json  (조회일 as_of 포함)
"""
import argparse
import json
import os
import sys
from datetime import date, timedelta


def die(msg: str, code: int = 1):
    print(f"[fetch_price] ERROR: {msg}", file=sys.stderr)
    sys.exit(code)


def main():
    parser = argparse.ArgumentParser(
        description="pykrx 시세/수급 수집 → data/{code}_market.json")
    parser.add_argument("code", help="6자리 종목코드 (예: 009150)")
    args = parser.parse_args()

    code = args.code.strip()
    if not (code.isdigit() and len(code) == 6):
        die(f"종목코드는 6자리 숫자여야 합니다: '{code}'")

    try:
        from pykrx import stock
    except ImportError:
        die("pykrx가 설치되지 않았습니다. `pip install pykrx` 후 다시 실행하세요.")

    today = date.today()
    start = today - timedelta(days=400)  # 영업일 보정 위해 넉넉히 1년+
    fromdate = start.strftime("%Y%m%d")
    todate = today.strftime("%Y%m%d")

    # --- OHLCV (최근 약 1년) ---
    try:
        ohlcv = stock.get_market_ohlcv(fromdate, todate, code)
    except Exception as e:  # pykrx 내부 예외 다양 → 명확히 종료
        die(f"OHLCV 조회 실패: {e}")
    if ohlcv is None or ohlcv.empty:
        die(f"종목 {code}의 OHLCV 데이터가 비어 있습니다. 코드/상장 여부 확인.")

    ohlcv = ohlcv.dropna()
    close_col = "종가"
    high_col = "고가"
    vol_col = "거래량"

    last_row = ohlcv.iloc[-1]
    as_of = ohlcv.index[-1].strftime("%Y-%m-%d")
    current_price = int(last_row[close_col])

    # 52주(약 1년) 고가
    year_window = ohlcv.tail(250)
    high_52w = int(year_window[high_col].max())
    pct_from_52w_high = round((current_price / high_52w - 1) * 100, 2) \
        if high_52w else None

    # 60일 평균 대비 최근 거래량 비율
    vol60 = ohlcv[vol_col].tail(60)
    avg_vol_60 = float(vol60.mean()) if len(vol60) else None
    last_vol = int(last_row[vol_col])
    volume_ratio_vs_60d = round(last_vol / avg_vol_60, 3) \
        if avg_vol_60 else None

    # --- 최근 60일 기관/외국인 순매수 합계 ---
    inst_sum = None
    foreign_sum = None
    supply_note = None
    try:
        sd = (today - timedelta(days=120)).strftime("%Y%m%d")
        flow = stock.get_market_trading_value_by_date(sd, todate, code)
        if flow is not None and not flow.empty:
            flow = flow.tail(60)
            # 컬럼명은 pykrx 버전에 따라 '기관합계'/'외국인'/'외국인합계' 등
            def col(df, *names):
                for n in names:
                    if n in df.columns:
                        return n
                return None
            inst_c = col(flow, "기관합계", "기관")
            for_c = col(flow, "외국인합계", "외국인")
            if inst_c:
                inst_sum = int(flow[inst_c].sum())
            if for_c:
                foreign_sum = int(flow[for_c].sum())
        else:
            supply_note = "수급 데이터 없음(빈 응답)"
    except Exception as e:
        supply_note = f"수급 조회 실패: {e}"  # 시세는 유지, 수급만 N/A 처리

    inst_foreign_net_60d = None
    if inst_sum is not None or foreign_sum is not None:
        inst_foreign_net_60d = (inst_sum or 0) + (foreign_sum or 0)

    result = {
        "stock_code": code,
        "as_of": as_of,                 # 조회 기준일(최근 영업일)
        "fetched_date": today.strftime("%Y-%m-%d"),
        "source": "pykrx",
        "current_price": current_price,
        "high_52w": high_52w,
        "pct_from_52w_high": pct_from_52w_high,   # (현재가/52주고가 - 1)*100 %
        "last_volume": last_vol,
        "avg_volume_60d": round(avg_vol_60) if avg_vol_60 else None,
        "volume_ratio_vs_60d": volume_ratio_vs_60d,  # 최근/60일평균
        "inst_net_60d": inst_sum,        # 기관 순매수(거래대금, 원)
        "foreign_net_60d": foreign_sum,  # 외국인 순매수(거래대금, 원)
        "inst_foreign_net_60d": inst_foreign_net_60d,  # 합계
        "supply_note": supply_note,
        "trading_days_used": int(len(ohlcv)),
    }

    out_dir = os.path.join("data")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f"{code}_market.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"[fetch_price] 저장 완료: {out_path} (as_of={as_of})")


if __name__ == "__main__":
    main()
