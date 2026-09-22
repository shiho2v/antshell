# =============================================================
# File   : test_news.py
# Week   : 10 | Ch.09 (2/2)
# =============================================================
"""종목 뉴스 엔드포인트 검증 — SPEC-NEWS-001 AC-002 ~ AC-007.

실제 data/ 디렉터리에 의존하지 않는다. DATA_DIR 을 임시 디렉터리로 바꿔치기해
고정된 픽스처로만 검증하므로, 뉴스 파일이 재수집으로 갱신돼도 기대값이
흔들리지 않는다(test_chart.py 와 동일한 전략).
"""

import json
import shutil
import subprocess
from pathlib import Path

import pytest
from app import main, news
from fastapi.testclient import TestClient

ALLOWED_CODE = "005930"
MISSING_FILE_CODE = "008490"
FORBIDDEN_CODE = "005380"

REAL_DATA_DIR = Path(main.__file__).resolve().parent.parent.parent / "data"


@pytest.fixture
def data_dir(tmp_path, monkeypatch):
    """DATA_DIR 을 임시 디렉터리로 교체하고 그 경로를 돌려준다."""
    monkeypatch.setattr(main, "DATA_DIR", tmp_path)
    return tmp_path


@pytest.fixture
def client():
    return TestClient(main.app)


def _write_agents_json(data_dir, stock_code, payload):
    target = data_dir / f"{stock_code}_agents.json"
    target.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    return target


def _news_item(**overrides):
    item = {
        "title": "제목",
        "date": "2026-07-06",
        "source": "언론사",
        "summary": "요약",
    }
    item.update(overrides)
    return item


def _assert_no_leaked_details(response, data_dir):
    body_text = response.text
    assert str(data_dir) not in body_text
    assert "_agents.json" not in body_text
    assert "Traceback" not in body_text
    for exception_name in ("JSONDecodeError", "KeyError", "TypeError", "AttributeError"):
        assert exception_name not in body_text


# --- AC-002: 성공 응답 계약 (정렬 · url · extra 키 통과 · 빈 배열) -------------


def test_news_response_sorting_url_and_passthrough_keys(client, data_dir):
    item_a = _news_item(title="A", date="2026-07-06", extra="x")
    item_b = _news_item(title="B", date="2026-07-10", url="https://example.com/b")
    item_c = _news_item(title="C", date="2026-07-06")
    item_d = _news_item(title="D", date="2026-07 (중순)")
    item_e = _news_item(title="E", date="2026-08 (하순)")
    _write_agents_json(
        data_dir,
        ALLOWED_CODE,
        {"ticker": ALLOWED_CODE, "news": [item_a, item_b, item_c, item_d, item_e]},
    )

    response = client.get(f"/api/stocks/{ALLOWED_CODE}/news")

    assert response.status_code == 200
    body = response.json()
    assert set(body.keys()) == {"stock_code", "news"}
    assert body["stock_code"] == ALLOWED_CODE
    assert len(body["news"]) == 5
    titles = [item["title"] for item in body["news"]]
    assert titles == ["B", "A", "C", "D", "E"]
    assert body["news"][0]["url"] == "https://example.com/b"
    for item in (body["news"][1], body["news"][2], body["news"][3], body["news"][4]):
        assert "url" not in item
    assert body["news"][1]["extra"] == "x"
    assert body["news"][1]["date"] == "2026-07-06"
    assert body["news"][3]["date"] == "2026-07 (중순)"
    assert body["news"][4]["date"] == "2026-08 (하순)"


def test_news_response_empty_list_is_ok(client, data_dir):
    _write_agents_json(data_dir, ALLOWED_CODE, {"ticker": ALLOWED_CODE, "news": []})

    response = client.get(f"/api/stocks/{ALLOWED_CODE}/news")

    assert response.status_code == 200
    body = response.json()
    assert set(body.keys()) == {"stock_code", "news"}
    assert body["news"] == []


# --- AC-003: news 밖 내용 비노출 ---------------------------------------------


def test_news_response_excludes_financials_ticker_name(client, data_dir):
    _write_agents_json(
        data_dir,
        ALLOWED_CODE,
        {
            "ticker": ALLOWED_CODE,
            "name": "삼성전자",
            "news": [_news_item()],
            "financials": {"per": 12.3},
        },
    )

    response = client.get(f"/api/stocks/{ALLOWED_CODE}/news")

    assert response.status_code == 200
    body = response.json()
    assert set(body.keys()) == {"stock_code", "news"}
    serialized = json.dumps(body)
    assert "financials" not in serialized
    assert "ticker" not in serialized
    assert "name" not in serialized


# --- AC-004: 허용 종목이지만 파일 부재 ---------------------------------------


def test_missing_file_for_allowed_code_returns_404(client, data_dir):
    response = client.get(f"/api/stocks/{MISSING_FILE_CODE}/news")

    assert response.status_code == 404


# --- AC-005: 허용 목록 밖 — 파일 접근 이전 거부 -------------------------------


def test_forbidden_code_returns_404_without_touching_filesystem(client, data_dir, monkeypatch):
    _write_agents_json(data_dir, FORBIDDEN_CODE, {"ticker": FORBIDDEN_CODE, "news": [_news_item()]})

    def fail_if_called(*args, **kwargs):
        raise AssertionError("허용 목록 밖 코드로 파일 접근이 발생했다")

    monkeypatch.setattr(news, "_read_news_document", fail_if_called)

    response = client.get(f"/api/stocks/{FORBIDDEN_CODE}/news")

    assert response.status_code == 404
    assert "제목" not in response.text


@pytest.mark.parametrize(
    "traversal_code",
    ["../005930", "..%2F005930", "005930/../../etc/passwd", ".."],
)
def test_path_traversal_codes_are_rejected(client, data_dir, traversal_code):
    response = client.get(f"/api/stocks/{traversal_code}/news")

    assert response.status_code == 404


# --- AC-006: 열화된 파일 처리 (「유효한 뉴스 문서」 네 조건 각각 최소 1건) ------


def test_malformed_json_bytes_returns_500(client, data_dir):
    target = data_dir / f"{ALLOWED_CODE}_agents.json"
    target.write_bytes(b"{not valid json")

    response = client.get(f"/api/stocks/{ALLOWED_CODE}/news")

    assert response.status_code == 500
    _assert_no_leaked_details(response, data_dir)


def test_missing_news_key_returns_500(client, data_dir):
    """조건 2 위반 — 최상위에 news 키가 없다."""
    _write_agents_json(data_dir, ALLOWED_CODE, {"ticker": ALLOWED_CODE})

    response = client.get(f"/api/stocks/{ALLOWED_CODE}/news")

    assert response.status_code == 500
    _assert_no_leaked_details(response, data_dir)


def test_news_not_a_list_returns_500(client, data_dir):
    """조건 2 위반 — news 값이 리스트가 아니다."""
    _write_agents_json(data_dir, ALLOWED_CODE, {"ticker": ALLOWED_CODE, "news": "오류"})

    response = client.get(f"/api/stocks/{ALLOWED_CODE}/news")

    assert response.status_code == 500
    _assert_no_leaked_details(response, data_dir)


def test_news_item_not_an_object_returns_500(client, data_dir):
    """조건 3 위반 — news 원소가 객체가 아니다."""
    _write_agents_json(data_dir, ALLOWED_CODE, {"ticker": ALLOWED_CODE, "news": ["문자열 항목"]})

    response = client.get(f"/api/stocks/{ALLOWED_CODE}/news")

    assert response.status_code == 500
    _assert_no_leaked_details(response, data_dir)


def test_news_item_missing_summary_returns_500(client, data_dir):
    """조건 4 위반 — 필수 키(summary)가 빠졌다."""
    item = _news_item()
    del item["summary"]
    _write_agents_json(data_dir, ALLOWED_CODE, {"ticker": ALLOWED_CODE, "news": [item]})

    response = client.get(f"/api/stocks/{ALLOWED_CODE}/news")

    assert response.status_code == 500
    _assert_no_leaked_details(response, data_dir)


def test_news_item_title_not_a_string_returns_500(client, data_dir):
    """조건 4 위반 — title 값이 문자열이 아니다."""
    item = _news_item(title=12345)
    _write_agents_json(data_dir, ALLOWED_CODE, {"ticker": ALLOWED_CODE, "news": [item]})

    response = client.get(f"/api/stocks/{ALLOWED_CODE}/news")

    assert response.status_code == 500
    _assert_no_leaked_details(response, data_dir)


# --- AC-007: 요청 경로 부작용 금지 -------------------------------------------


def test_news_endpoint_makes_no_subprocess_or_network_calls(client, data_dir, monkeypatch):
    _write_agents_json(data_dir, ALLOWED_CODE, {"ticker": ALLOWED_CODE, "news": [_news_item()]})

    def fail_if_called(*args, **kwargs):
        raise AssertionError("뉴스 엔드포인트에서 금지된 호출이 발생했다")

    monkeypatch.setattr(subprocess, "run", fail_if_called)
    monkeypatch.setattr(shutil, "which", fail_if_called)
    monkeypatch.setattr(main.httpx, "AsyncClient", fail_if_called)
    monkeypatch.setattr(main.urllib.request, "urlopen", fail_if_called)

    response = client.get(f"/api/stocks/{ALLOWED_CODE}/news")

    assert response.status_code == 200


def test_news_endpoint_does_not_write_to_data_dir(client, data_dir):
    _write_agents_json(data_dir, ALLOWED_CODE, {"ticker": ALLOWED_CODE, "news": [_news_item()]})
    before = sorted(path.name for path in data_dir.iterdir())

    client.get(f"/api/stocks/{ALLOWED_CODE}/news")

    after = sorted(path.name for path in data_dir.iterdir())
    assert before == after


# --- 커밋된 파일의 「유효한 뉴스 문서」 적합성 (자동, 검증 수단 표) -------------


@pytest.mark.parametrize("stock_code", sorted(news.NEWS_STOCK_CODES))
def test_committed_agents_json_files_satisfy_valid_news_document(stock_code):
    """spec.md §4 「유효한 뉴스 문서」 적합성 — 실제 커밋된 파일 대상.

    008490 은 REQ-001 운영자 수동 단계가 아직 실행되지 않았으면 없을 수 있다.
    """
    target = REAL_DATA_DIR / f"{stock_code}_agents.json"
    if not target.exists():
        pytest.skip(f"{stock_code}_agents.json 이 아직 생성되지 않았다 (REQ-001 운영자 수동 단계 미완료)")
    with target.open(encoding="utf-8") as data_file:
        document = json.load(data_file)
    assert news._is_valid_news_document(document)
