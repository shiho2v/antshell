# =============================================================
# File   : test_chart.py
# Author : @injeinnam
# Week   : 09 | Ch.09 (1/2)
# Created: 2026-09-13
# =============================================================
"""차트 엔드포인트 검증 — SPEC-CHART-001 AC-003 ~ AC-007, AC-015.

실제 data/ 디렉터리에 의존하지 않는다. DATA_DIR 을 임시 디렉터리로 바꿔치기해
고정된 픽스처로만 검증하므로, 시세 파일이 갱신돼도 기대값이 흔들리지 않는다.
"""

import json

import pytest
from app import main
from fastapi.testclient import TestClient

ALLOWED_CODE = "005930"
FORBIDDEN_CODE = "005380"
INDICATOR_KEYS = (
    "sma_5",
    "sma_20",
    "sma_60",
    "ema_12",
    "ema_26",
    "rsi_14",
    "macd",
    "macd_signal",
    "macd_histogram",
)


def build_fixture_records(count):
    """지표 최소 기간(60일)을 넘기는 결정론적 OHLCV 픽스처."""
    records = []
    close_price = 50_000
    for index in range(count):
        close_price += 100 if index % 3 else -70
        records.append(
            {
                "date": f"2026-01-{index + 1:02d}" if index < 31 else f"2026-02-{index - 30:02d}",
                "open": close_price - 50,
                "high": close_price + 120,
                "low": close_price - 130,
                "close": close_price,
                "volume": 1_000_000 + index,
            }
        )
    return records


@pytest.fixture
def data_dir(tmp_path, monkeypatch):
    """DATA_DIR 을 임시 디렉터리로 교체하고 그 경로를 돌려준다."""
    monkeypatch.setattr(main, "DATA_DIR", tmp_path)
    return tmp_path


@pytest.fixture
def client():
    return TestClient(main.app)


@pytest.fixture
def seeded_data_dir(data_dir):
    payload = {
        "stock_code": ALLOWED_CODE,
        "source": "pykrx",
        "fetched_date": "2026-09-13",
        "records": build_fixture_records(80),
    }
    target = data_dir / f"{ALLOWED_CODE}_ohlcv.json"
    target.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    return data_dir


# --- AC-003: OHLCV 정상 응답 -------------------------------------------------


def test_ohlcv_returns_records_for_allowed_code(client, seeded_data_dir):
    response = client.get(f"/api/stocks/{ALLOWED_CODE}/ohlcv")

    assert response.status_code == 200
    body = response.json()
    assert body["stock_code"] == ALLOWED_CODE
    assert body["source"] == "pykrx"
    assert body["fetched_date"] == "2026-09-13"
    assert len(body["records"]) >= 1
    first_record = body["records"][0]
    assert {"date", "open", "high", "low", "close", "volume"} <= set(first_record)


# --- AC-004: 허용 목록 밖 코드는 파일시스템 접근 없이 404 ---------------------


@pytest.mark.parametrize("endpoint", ["ohlcv", "indicators"])
def test_forbidden_code_returns_404(client, seeded_data_dir, endpoint):
    response = client.get(f"/api/stocks/{FORBIDDEN_CODE}/{endpoint}")

    assert response.status_code == 404


@pytest.mark.parametrize("endpoint", ["ohlcv", "indicators"])
def test_forbidden_code_never_touches_the_filesystem(client, data_dir, monkeypatch, endpoint):
    """REQ-005 — 허용 목록 검사가 파일 접근보다 먼저 일어나야 한다."""

    def fail_if_called(stock_code):
        raise AssertionError(f"허용 목록 밖 코드로 파일 접근이 발생했다: {stock_code}")

    monkeypatch.setattr(main, "_read_ohlcv_document", fail_if_called)

    response = client.get(f"/api/stocks/{FORBIDDEN_CODE}/{endpoint}")

    assert response.status_code == 404


@pytest.mark.parametrize(
    "traversal_code",
    ["../005930", "..%2F005930", "005930/../../etc/passwd", ".."],
)
def test_path_traversal_attempts_are_rejected(client, seeded_data_dir, traversal_code):
    response = client.get(f"/api/stocks/{traversal_code}/ohlcv")

    assert response.status_code == 404


# --- AC-005: 허용 목록 안이지만 파일이 없으면 404 -----------------------------


@pytest.mark.parametrize("endpoint", ["ohlcv", "indicators"])
def test_allowed_code_without_data_file_returns_404(client, data_dir, endpoint):
    response = client.get(f"/api/stocks/009150/{endpoint}")

    assert response.status_code == 404


# --- AC-006: 어떤 엔드포인트도 외부 수집을 트리거하지 않는다 ------------------


@pytest.mark.parametrize("endpoint", ["ohlcv", "indicators"])
def test_chart_endpoints_make_no_network_calls(client, seeded_data_dir, monkeypatch, endpoint):
    """REQ-007 — 요청 경로에서 pykrx/외부 API 호출이 없어야 한다."""

    def fail_if_called(*args, **kwargs):
        raise AssertionError("차트 엔드포인트에서 네트워크 호출이 발생했다")

    monkeypatch.setattr(main.urllib.request, "urlopen", fail_if_called)

    response = client.get(f"/api/stocks/{ALLOWED_CODE}/{endpoint}")

    assert response.status_code == 200


def test_chart_endpoints_do_not_write_data_files(client, seeded_data_dir):
    """REQ-007 — 응답 처리 중 data/ 에 새 파일이 생기면 안 된다."""
    before = sorted(path.name for path in seeded_data_dir.iterdir())

    client.get(f"/api/stocks/{ALLOWED_CODE}/ohlcv")
    client.get(f"/api/stocks/{ALLOWED_CODE}/indicators")

    after = sorted(path.name for path in seeded_data_dir.iterdir())
    assert before == after


# --- AC-007: 지표 응답 형태 --------------------------------------------------


def test_indicators_response_has_all_expected_keys(client, seeded_data_dir):
    response = client.get(f"/api/stocks/{ALLOWED_CODE}/indicators")

    assert response.status_code == 200
    body = response.json()
    for key in INDICATOR_KEYS:
        assert key in body, f"{key} 가 응답에 없다"


def test_indicator_series_match_record_count(client, seeded_data_dir):
    ohlcv_body = client.get(f"/api/stocks/{ALLOWED_CODE}/ohlcv").json()
    record_count = len(ohlcv_body["records"])

    body = client.get(f"/api/stocks/{ALLOWED_CODE}/indicators").json()

    assert len(body["dates"]) == record_count
    for key in INDICATOR_KEYS:
        assert len(body[key]) == record_count, f"{key} 길이가 레코드 수와 다르다"


def test_indicators_null_prefix_follows_minimum_period(client, seeded_data_dir):
    """REQ-010 — 최소 관측 기간을 못 채운 구간은 null 이다."""
    body = client.get(f"/api/stocks/{ALLOWED_CODE}/indicators").json()

    assert body["sma_5"][:4] == [None] * 4
    assert body["sma_5"][4] is not None
    assert body["sma_20"][:19] == [None] * 19
    assert body["sma_20"][19] is not None
    assert body["sma_60"][:59] == [None] * 59
    assert body["sma_60"][59] is not None
    assert body["rsi_14"][:14] == [None] * 14
    assert body["rsi_14"][14] is not None


def test_indicator_dates_align_with_ohlcv_dates(client, seeded_data_dir):
    ohlcv_body = client.get(f"/api/stocks/{ALLOWED_CODE}/ohlcv").json()
    expected_dates = [record["date"] for record in ohlcv_body["records"]]

    body = client.get(f"/api/stocks/{ALLOWED_CODE}/indicators").json()

    assert body["dates"] == expected_dates


# --- AC-015: 기존 라우트 회귀 없음 -------------------------------------------


def test_health_route_is_unchanged(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_existing_routes_are_still_registered(client):
    registered = {route.path for route in main.app.routes}

    assert "/health" in registered
    assert "/api/report/notion" in registered
    assert "/api/github/issues" in registered
