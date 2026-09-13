"""4개 종목의 일별 OHLCV 시계열을 수집해 data/{code}_ohlcv.json 으로 저장하는 CLI 진입점.

사용법:
    python scripts/fetch_ohlcv.py                # pykrx 로 실제 시세 수집 (기본 365일)
    python scripts/fetch_ohlcv.py --days 180     # 수집 기간 지정
    python scripts/fetch_ohlcv.py --sample       # 결정론적 샘플 데이터 생성 (외부 의존 없음)

SPEC-CHART-001 REQ-001 ~ REQ-003 구현.

이 스크립트는 오프라인 수집 도구다. 백엔드 런타임은 이 스크립트를 호출하지 않으며
(REQ-007), 생성된 JSON 파일만 읽어 서빙한다. pykrx 는 scripts/requirements.txt 에만
선언되어 있고 backend/requirements.txt 에는 없다.

--sample 모드는 pykrx 미설치·네트워크 차단 환경에서도 동일한 스키마의 데이터를
재현 가능하게 생성한다. 고정 시드를 사용하므로 몇 번을 실행해도 결과가 같다.
생성된 파일의 source 필드가 "sample" 로 표기되어 실제 시세와 구분된다.
"""

import argparse
import json
import random
import sys
from datetime import date, timedelta
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"

# REQ-001: 사전에 정의된 4개 종목으로만 한정한다.
STOCK_CODES = ("005930", "000660", "009150", "008490")

# --sample 모드 랜덤 워크의 시작 가격.
# 실제 시세가 아니라 종목별로 그럴듯한 자릿수를 만들기 위한 기준값이다.
SAMPLE_BASE_PRICES = {
    "005930": 285000,
    "000660": 198000,
    "009150": 142000,
    "008490": 28350,
}

DEFAULT_DAYS = 365
SAMPLE_SEED = 20260913
SAMPLE_DAILY_VOLATILITY = 0.018
SAMPLE_BASE_VOLUME = 12_000_000


def build_trading_dates(end_date, calendar_days):
    """end_date 로부터 calendar_days 만큼 거슬러 올라가며 주말을 제외한 날짜를 반환한다.

    공휴일은 반영하지 않는다. 샘플 데이터용 근사이며, pykrx 모드에서는
    거래소가 실제 거래일만 돌려주므로 이 함수를 쓰지 않는다.
    """
    trading_dates = []
    for offset in range(calendar_days):
        candidate = end_date - timedelta(days=offset)
        if candidate.weekday() < 5:
            trading_dates.append(candidate)
    trading_dates.reverse()
    return trading_dates


def build_sample_records(stock_code, calendar_days, end_date):
    """고정 시드 기반 결정론적 OHLCV 레코드를 생성한다.

    같은 인자로 몇 번을 호출해도 동일한 결과가 나온다. 종목 코드를 시드에 섞어
    종목마다 다른 가격 흐름이 나오도록 한다.
    """
    generator = random.Random(SAMPLE_SEED + int(stock_code))
    close_price = float(SAMPLE_BASE_PRICES[stock_code])
    records = []
    for trading_date in build_trading_dates(end_date, calendar_days):
        drift = generator.uniform(-SAMPLE_DAILY_VOLATILITY, SAMPLE_DAILY_VOLATILITY)
        open_price = close_price
        close_price = max(close_price * (1.0 + drift), 100.0)
        session_high = max(open_price, close_price) * (1.0 + generator.uniform(0.0, 0.008))
        session_low = min(open_price, close_price) * (1.0 - generator.uniform(0.0, 0.008))
        volume = int(SAMPLE_BASE_VOLUME * generator.uniform(0.4, 1.9))
        records.append(
            {
                "date": trading_date.isoformat(),
                "open": int(round(open_price)),
                "high": int(round(session_high)),
                "low": int(round(session_low)),
                "close": int(round(close_price)),
                "volume": volume,
            }
        )
    return records


def fetch_pykrx_records(stock_code, start_date, end_date):
    """pykrx 로 실제 일별 OHLCV 를 조회해 레코드 목록으로 변환한다.

    조회 실패나 빈 응답은 RuntimeError 로 올려 호출자가 REQ-003 에 따라
    기존 파일을 보존한 채 중단하도록 한다.
    """
    try:
        from pykrx import stock as krx_stock
    except ImportError as import_error:
        # 원인을 그대로 노출한다. 미설치뿐 아니라 의존성 문제(예: Python 3.13 에서
        # pkg_resources 부재)로도 실패하므로, 메시지를 뭉뚱그리면 진단이 어려워진다.
        raise RuntimeError(
            f"pykrx 를 불러올 수 없습니다: {import_error}. "
            "'pip install -r scripts/requirements.txt' 로 설치하거나 "
            "--sample 모드를 사용하세요."
        ) from import_error

    start_text = start_date.strftime("%Y%m%d")
    end_text = end_date.strftime("%Y%m%d")
    try:
        price_frame = krx_stock.get_market_ohlcv(start_text, end_text, stock_code)
    except Exception as fetch_error:
        raise RuntimeError(f"{stock_code} 시세 조회 실패: {fetch_error}") from fetch_error

    if price_frame is None or price_frame.empty:
        raise RuntimeError(f"{stock_code} 시세 조회 결과가 비어 있습니다 ({start_text}~{end_text})")

    records = []
    for timestamp, row in price_frame.iterrows():
        records.append(
            {
                "date": timestamp.strftime("%Y-%m-%d"),
                "open": int(row["시가"]),
                "high": int(row["고가"]),
                "low": int(row["저가"]),
                "close": int(row["종가"]),
                "volume": int(row["거래량"]),
            }
        )
    # REQ-002: date 오름차순 정렬을 보장한다.
    records.sort(key=lambda record: record["date"])
    return records


def build_payload(stock_code, source, records, fetched_date):
    """spec.md §4 의 데이터 계약에 맞춘 최종 JSON 구조를 만든다."""
    return {
        "stock_code": stock_code,
        "source": source,
        "fetched_date": fetched_date.isoformat(),
        "records": records,
    }


def describe_path(target_path):
    """로그 출력용 경로 문자열. 프로젝트 루트 밖이면 절대 경로를 그대로 쓴다.

    --out-dir 로 임의 디렉터리(테스트의 tmp_path 등)를 지정할 수 있으므로
    relative_to 가 항상 성공한다고 가정하면 안 된다.
    """
    try:
        return str(target_path.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(target_path)


def write_ohlcv_file(payload, output_dir):
    output_path = output_dir / f"{payload['stock_code']}_ohlcv.json"
    with output_path.open("w", encoding="utf-8") as output_file:
        json.dump(payload, output_file, ensure_ascii=False, indent=2)
        output_file.write("\n")
    return output_path


def parse_arguments(argv):
    parser = argparse.ArgumentParser(
        description="4개 종목의 일별 OHLCV 를 수집해 data/{code}_ohlcv.json 으로 저장한다."
    )
    parser.add_argument(
        "--sample",
        action="store_true",
        help="pykrx 대신 결정론적 샘플 데이터를 생성한다 (외부 의존 없음).",
    )
    parser.add_argument(
        "--days",
        type=int,
        default=DEFAULT_DAYS,
        help=f"수집할 기간(달력 일수). 기본 {DEFAULT_DAYS}일.",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=DATA_DIR,
        help="출력 디렉터리. 기본 data/.",
    )
    return parser.parse_args(argv)


def main(argv=None):
    arguments = parse_arguments(argv)
    if arguments.days < 1:
        print("[fetch_ohlcv] --days 는 1 이상이어야 합니다.", file=sys.stderr)
        return 2

    end_date = date.today()
    start_date = end_date - timedelta(days=arguments.days)
    source = "sample" if arguments.sample else "pykrx"

    # REQ-003: 4개 종목을 모두 메모리에 모은 뒤에야 파일을 쓴다.
    # 중간에 하나라도 실패하면 어떤 파일도 건드리지 않고 종료한다.
    collected_payloads = []
    for stock_code in STOCK_CODES:
        try:
            if arguments.sample:
                records = build_sample_records(stock_code, arguments.days, end_date)
            else:
                records = fetch_pykrx_records(stock_code, start_date, end_date)
        except RuntimeError as collect_error:
            print(f"[fetch_ohlcv] 실패: {collect_error}", file=sys.stderr)
            print("[fetch_ohlcv] 기존 파일을 변경하지 않고 중단합니다.", file=sys.stderr)
            return 1
        print(f"[fetch_ohlcv] {stock_code}: {len(records)}개 레코드 수집 ({source})")
        collected_payloads.append(build_payload(stock_code, source, records, end_date))

    arguments.out_dir.mkdir(parents=True, exist_ok=True)
    for payload in collected_payloads:
        output_path = write_ohlcv_file(payload, arguments.out_dir)
        print(f"[fetch_ohlcv] 저장: {describe_path(output_path)}")

    print(f"[fetch_ohlcv] 완료 — {len(collected_payloads)}개 종목, source={source}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
