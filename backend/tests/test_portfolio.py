# =============================================================
# File   : test_portfolio.py
# Week   : 10 | Ch.09 (2/2)
# =============================================================
"""포트폴리오 엔드포인트 검증 — SPEC-PORTFOLIO-001 AC-005 ~ AC-008.

실제 data/portfolio_analysis.json 에 의존하지 않는다. DATA_DIR 을 임시
디렉터리로 바꿔치기해 고정된 픽스처로만 검증하므로, 커밋된 분석 결과의
source 값(agent-team/sample)이 바뀌어도 테스트가 흔들리지 않는다
(acceptance.md 품질 게이트).
"""

import json
import shutil
import subprocess

import httpx
import pytest
from app import main
from fastapi.testclient import TestClient


def _build_valid_document(source="agent-team"):
    return {
        "schema_version": "1",
        "source": source,
        "generated_date": "2026-09-20",
        "portfolio_file": "data/portfolio.example.json",
        "portfolio_name": "샘플 포트폴리오",
        "as_of": "2026-07-25",
        "valuation": {
            "agent": "portfolio-valuation",
            "results": [
                {
                    "stock_code": "005930",
                    "name": "삼성전자",
                    "revenue_growth_pct": None,
                    "op_income_growth_pct": None,
                    "verdict": "적정",
                    "score": 60,
                    "basis": "실제 에이전트 판정이 아닙니다",
                },
                {
                    "stock_code": "000660",
                    "name": "SK하이닉스",
                    "revenue_growth_pct": None,
                    "op_income_growth_pct": None,
                    "verdict": "unknown",
                    "score": 0,
                    "basis": "데이터 부족으로 판정 불가",
                },
            ],
        },
        "risk": {
            "agent": "portfolio-risk",
            "total_market_value": 27770000.0,
            "results": [
                {
                    "stock_code": "005930",
                    "name": "삼성전자",
                    "market_value": 4290000.0,
                    "actual_weight_pct": 15.45,
                    "concentration": "중간",
                    "drawdown_from_52w": "0%",
                    "supply_flow": "중립",
                    "volume_state": "normal",
                    "risk_score": 60,
                    "overall": "medium",
                },
                {
                    "stock_code": "000660",
                    "name": "SK하이닉스",
                    "market_value": 13270000.0,
                    "actual_weight_pct": 47.8,
                    "concentration": "높음",
                    "drawdown_from_52w": "-5%",
                    "supply_flow": "매수",
                    "volume_state": "normal",
                    "risk_score": 40,
                    "overall": "unknown",
                },
            ],
        },
        "allocation": {
            "agent": "portfolio-allocation",
            "total_asset": 32770000.0,
            "cash": 5000000.0,
            "results": [
                {
                    "stock_code": "005930",
                    "name": "삼성전자",
                    "current_price": 71500.0,
                    "market_value": 4290000.0,
                    "actual_weight_pct": 13.09,
                    "target_weight_pct": 30.0,
                    "drift_pct": -16.91,
                    "action": "매수",
                    "rebalance_amount": 5541000,
                },
                {
                    "stock_code": "000660",
                    "name": "SK하이닉스",
                    "current_price": 132700.0,
                    "market_value": 13270000.0,
                    "actual_weight_pct": 40.49,
                    "target_weight_pct": 30.0,
                    "drift_pct": 10.49,
                    "action": "매도",
                    "rebalance_amount": -3437000,
                },
            ],
        },
    }


def _corrupt_missing_top_level_key(document):
    del document["allocation"]
    return document


def _corrupt_non_list_results(document):
    document["risk"]["results"] = "not-a-list"
    return document


def _corrupt_mismatched_lengths(document):
    document["valuation"]["results"] = document["valuation"]["results"][:1]
    return document


@pytest.fixture
def data_dir(tmp_path, monkeypatch):
    """DATA_DIR 을 임시 디렉터리로 교체하고 그 경로를 돌려준다."""
    monkeypatch.setattr(main, "DATA_DIR", tmp_path)
    return tmp_path


@pytest.fixture
def client():
    return TestClient(main.app)


def _write_portfolio_file(data_dir, document):
    target = data_dir / main.PORTFOLIO_ANALYSIS_FILE
    target.write_text(json.dumps(document, ensure_ascii=False), encoding="utf-8")
    return target


# --- AC-005: 성공 응답 계약 (source 무관) ------------------------------------


@pytest.mark.parametrize("source", ["agent-team", "sample"])
def test_portfolio_returns_200_with_meta_and_three_blocks(client, data_dir, source):
    document = _build_valid_document(source=source)
    _write_portfolio_file(data_dir, document)

    response = client.get("/api/portfolio")

    assert response.status_code == 200
    body = response.json()
    assert set(body.keys()) == {"meta", "valuation", "risk", "allocation"}

    meta = body["meta"]
    assert set(meta.keys()) == {
        "schema_version",
        "source",
        "portfolio_name",
        "as_of",
        "generated_date",
    }
    assert meta["source"] == source
    assert meta["as_of"] == document["as_of"]
    assert meta["generated_date"] == document["generated_date"]

    holdings_count = len(document["valuation"]["results"])
    assert len(body["valuation"]["results"]) == holdings_count
    assert len(body["risk"]["results"]) == holdings_count
    assert len(body["allocation"]["results"]) == holdings_count


# --- AC-006: 열화된 파일 처리 --------------------------------------------------


def test_portfolio_missing_file_returns_404(client, data_dir):
    response = client.get("/api/portfolio")

    assert response.status_code == 404


def test_portfolio_invalid_json_returns_500_without_leaking_details(client, data_dir):
    target = data_dir / main.PORTFOLIO_ANALYSIS_FILE
    target.write_text("{ not valid json", encoding="utf-8")

    response = client.get("/api/portfolio")

    assert response.status_code == 500
    body_text = response.text
    assert str(data_dir) not in body_text
    assert "/" not in body_text.replace("포트폴리오", "")  # 경로 조각(슬래시) 미노출
    assert "Traceback" not in body_text
    assert "JSONDecodeError" not in body_text


@pytest.mark.parametrize(
    "corrupt",
    [_corrupt_missing_top_level_key, _corrupt_non_list_results, _corrupt_mismatched_lengths],
)
def test_portfolio_schema_violation_returns_500(client, data_dir, corrupt):
    document = corrupt(_build_valid_document())
    _write_portfolio_file(data_dir, document)

    response = client.get("/api/portfolio")

    assert response.status_code == 500
    body_text = response.text
    assert str(data_dir) not in body_text
    assert "Traceback" not in body_text


# --- AC-007: 요청 경로가 claude/subprocess/외부 네트워크/data/ 쓰기를 하지 않는다 ---


def test_portfolio_endpoint_makes_no_subprocess_or_network_calls(client, data_dir, monkeypatch):
    document = _build_valid_document()
    _write_portfolio_file(data_dir, document)

    def fail_if_called(*args, **kwargs):
        raise AssertionError("포트폴리오 엔드포인트에서 금지된 호출이 발생했다")

    monkeypatch.setattr(main.urllib.request, "urlopen", fail_if_called)
    monkeypatch.setattr(subprocess, "run", fail_if_called)
    monkeypatch.setattr(subprocess, "Popen", fail_if_called)
    monkeypatch.setattr(shutil, "which", fail_if_called)
    monkeypatch.setattr(httpx, "AsyncClient", fail_if_called)
    monkeypatch.setattr(httpx, "Client", fail_if_called)

    response = client.get("/api/portfolio")

    assert response.status_code == 200


def test_portfolio_endpoint_does_not_write_to_data_dir(client, data_dir):
    document = _build_valid_document()
    _write_portfolio_file(data_dir, document)
    before = sorted(path.name for path in data_dir.iterdir())

    client.get("/api/portfolio")

    after = sorted(path.name for path in data_dir.iterdir())
    assert before == after


# --- AC-008: 비중은 allocation 하나만 응답에 실린다 ---------------------------


def test_portfolio_response_excludes_risk_weight_but_keeps_allocation_weight(client, data_dir):
    document = _build_valid_document()
    _write_portfolio_file(data_dir, document)

    response = client.get("/api/portfolio")
    body = response.json()

    for item in body["risk"]["results"]:
        assert "actual_weight_pct" not in item

    file_allocation_by_code = {
        item["stock_code"]: item["actual_weight_pct"] for item in document["allocation"]["results"]
    }
    for item in body["allocation"]["results"]:
        assert item["actual_weight_pct"] == file_allocation_by_code[item["stock_code"]]


# --- 회귀: 기존 라우트와 공존 -------------------------------------------------


def test_existing_routes_still_registered_alongside_portfolio(client):
    registered = {route.path for route in main.app.routes}

    assert "/api/portfolio" in registered
    assert "/health" in registered
