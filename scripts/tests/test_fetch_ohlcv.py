"""scripts/fetch_ohlcv.py 검증 — SPEC-CHART-001 AC-001, AC-002.

AC-002 는 "조회 실패 시 기존 파일을 덮어쓰지 않고 0 이 아닌 종료 코드로 종료한다"를
요구한다. 실제 네트워크를 쓰지 않고 검증하기 위해 수집 함수를 실패하도록 교체한다.
"""

import json
import sys
from pathlib import Path

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parent.parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import fetch_ohlcv  # noqa: E402  (sys.path 조정 후에 import 해야 한다)

REQUIRED_FIELDS = {"date", "open", "high", "low", "close", "volume"}


def read_payload(output_dir, stock_code):
    target = output_dir / f"{stock_code}_ohlcv.json"
    return json.loads(target.read_text(encoding="utf-8"))


# --- AC-001: 4개 파일, 6개 필드, date 오름차순 --------------------------------


def test_sample_mode_writes_one_file_per_stock(tmp_path):
    exit_code = fetch_ohlcv.main(["--sample", "--days", "40", "--out-dir", str(tmp_path)])

    assert exit_code == 0
    written = sorted(path.name for path in tmp_path.glob("*_ohlcv.json"))
    assert written == sorted(f"{code}_ohlcv.json" for code in fetch_ohlcv.STOCK_CODES)


@pytest.mark.parametrize("stock_code", fetch_ohlcv.STOCK_CODES)
def test_sample_records_have_required_fields_and_are_sorted(tmp_path, stock_code):
    fetch_ohlcv.main(["--sample", "--days", "40", "--out-dir", str(tmp_path)])
    payload = read_payload(tmp_path, stock_code)
    records = payload["records"]

    assert payload["stock_code"] == stock_code
    assert payload["source"] == "sample"
    assert records, "레코드가 비어 있으면 안 된다"
    for record in records:
        assert REQUIRED_FIELDS <= set(record)
    dates = [record["date"] for record in records]
    assert dates == sorted(dates)


@pytest.mark.parametrize("stock_code", fetch_ohlcv.STOCK_CODES)
def test_sample_records_are_ohlc_consistent(tmp_path, stock_code):
    fetch_ohlcv.main(["--sample", "--days", "40", "--out-dir", str(tmp_path)])
    records = read_payload(tmp_path, stock_code)["records"]

    for record in records:
        assert record["low"] <= record["open"] <= record["high"]
        assert record["low"] <= record["close"] <= record["high"]
        assert record["volume"] > 0


def test_sample_mode_is_deterministic(tmp_path):
    first_dir = tmp_path / "first"
    second_dir = tmp_path / "second"
    fetch_ohlcv.main(["--sample", "--days", "40", "--out-dir", str(first_dir)])
    fetch_ohlcv.main(["--sample", "--days", "40", "--out-dir", str(second_dir)])

    for stock_code in fetch_ohlcv.STOCK_CODES:
        assert read_payload(first_dir, stock_code) == read_payload(second_dir, stock_code)


# --- AC-002: 실패 시 기존 파일 보존 + 0 이 아닌 종료 코드 ----------------------


def test_fetch_failure_preserves_existing_file_and_exits_nonzero(tmp_path, monkeypatch):
    # 기존 파일을 만들어 둔다. 실패해도 이 바이트가 그대로여야 한다.
    existing_path = tmp_path / "005930_ohlcv.json"
    sentinel = '{"stock_code": "005930", "source": "pykrx", "records": []}\n'
    existing_path.write_text(sentinel, encoding="utf-8")

    def always_fail(stock_code, start_date, end_date):
        raise RuntimeError(f"{stock_code} 시세 조회 실패 (테스트 강제)")

    monkeypatch.setattr(fetch_ohlcv, "fetch_pykrx_records", always_fail)

    exit_code = fetch_ohlcv.main(["--days", "40", "--out-dir", str(tmp_path)])

    assert exit_code != 0
    assert existing_path.read_text(encoding="utf-8") == sentinel


def test_partial_failure_writes_no_file_at_all(tmp_path, monkeypatch):
    """첫 종목은 성공하고 두 번째에서 실패해도 어떤 파일도 쓰이면 안 된다."""
    call_log = []

    def fail_on_second(stock_code, start_date, end_date):
        call_log.append(stock_code)
        if len(call_log) >= 2:
            raise RuntimeError(f"{stock_code} 시세 조회 실패 (테스트 강제)")
        return [
            {
                "date": "2026-09-11",
                "open": 100,
                "high": 110,
                "low": 90,
                "close": 105,
                "volume": 1000,
            }
        ]

    monkeypatch.setattr(fetch_ohlcv, "fetch_pykrx_records", fail_on_second)

    exit_code = fetch_ohlcv.main(["--days", "40", "--out-dir", str(tmp_path)])

    assert exit_code != 0
    assert list(tmp_path.glob("*_ohlcv.json")) == []


def test_invalid_days_argument_is_rejected(tmp_path):
    exit_code = fetch_ohlcv.main(["--sample", "--days", "0", "--out-dir", str(tmp_path)])

    assert exit_code != 0
    assert list(tmp_path.glob("*_ohlcv.json")) == []
