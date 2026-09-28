# =============================================================
# File   : test_orchestrate_portfolio.py
# Author : @정우준
# Week   : 10 | Ch.09 (2/2)
# Created: 2026-09-22
# =============================================================
"""scripts/orchestrate_portfolio.py 검증 — SPEC-PORTFOLIO-001 M1 (AC-001~AC-004).

REQ-001 (--save-json 저장) · REQ-002 (실패 시 비덮어쓰기) · REQ-003 (허용 목록 검사) ·
REQ-004 (--sample 결정론) 를 검증한다. 실제 claude 서브에이전트는 호출하지 않고
run_orchestrator 를 몽키패치하거나 --sample 모드로 대체한다.
"""

import json
import sys
from pathlib import Path
from unittest.mock import Mock

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parent.parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import orchestrate_portfolio

PROJECT_ROOT = SCRIPTS_DIR.parent
EXAMPLE_PORTFOLIO = PROJECT_ROOT / "data" / "portfolio.example.json"
EDGE_PORTFOLIO = PROJECT_ROOT / "data" / "portfolio.edge.json"

EXISTING_FILE_SENTINEL = '{"sentinel": true, "note": "기존 파일 — 실패 시 그대로 보존되어야 한다"}'


def _valid_merged_result(as_of="2026-07-25"):
    """spec.md §4 「필수 키 집합」다섯 조건을 만족하는 병합 결과 픽스처."""
    codes = ["005930", "000660", "009150", "008490"]
    valuation_results = [
        {"stock_code": c, "name": c, "verdict": "적정", "score": 50, "basis": "테스트 고정값"} for c in codes
    ]
    risk_results = [{"stock_code": c, "name": c, "overall": "medium"} for c in codes]
    allocation_results = [
        {
            "stock_code": c,
            "name": c,
            "actual_weight_pct": 25.0,
            "target_weight_pct": 25.0,
            "drift_pct": 0.0,
            "action": "유지",
            "rebalance_amount": 0,
        }
        for c in codes
    ]
    return {
        "portfolio_name": "테스트 포트폴리오",
        "as_of": as_of,
        "valuation": {"agent": "portfolio-valuation", "results": valuation_results},
        "risk": {"agent": "portfolio-risk", "total_market_value": 1_000_000, "results": risk_results},
        "allocation": {
            "agent": "portfolio-allocation",
            "total_asset": 1_200_000,
            "cash": 200_000,
            "results": allocation_results,
        },
    }


# --- AC-001: --save-json 저장 시 9개 최상위 키 + generated_date/as_of ----------


def test_save_json_writes_nine_top_level_keys_with_generated_date_and_as_of(tmp_path, monkeypatch):
    target = tmp_path / "portfolio_analysis.json"
    monkeypatch.setattr(orchestrate_portfolio, "run_orchestrator", Mock(return_value=_valid_merged_result()))

    exit_code = orchestrate_portfolio.main(
        ["--portfolio", str(EXAMPLE_PORTFOLIO), "--save-json", str(target)]
    )

    assert exit_code == 0
    assert target.exists()
    saved = json.loads(target.read_text(encoding="utf-8"))
    assert set(saved.keys()) == set(orchestrate_portfolio.REQUIRED_TOP_LEVEL_KEYS)
    import datetime as dt

    assert saved["generated_date"] == dt.date.today().isoformat()
    # data/portfolio.example.json 의 as_of 값과 동일해야 한다
    assert saved["as_of"] == "2026-07-25"
    assert saved["portfolio_file"] == str(EXAMPLE_PORTFOLIO)
    assert saved["schema_version"] == "1"
    assert saved["source"] == "agent-team"


# --- AC-002: 실패 시 비덮어쓰기 + 잔여 임시 파일 없음 --------------------------


def test_save_preserves_existing_file_on_subagent_failure(tmp_path, monkeypatch):
    target = tmp_path / "portfolio_analysis.json"
    target.write_text(EXISTING_FILE_SENTINEL, encoding="utf-8")

    monkeypatch.setattr(
        orchestrate_portfolio,
        "run_orchestrator",
        Mock(side_effect=RuntimeError("서브에이전트 실행 실패 (테스트 강제)")),
    )

    exit_code = orchestrate_portfolio.main(
        ["--portfolio", str(EXAMPLE_PORTFOLIO), "--save-json", str(target)]
    )

    assert exit_code != 0
    assert target.read_text(encoding="utf-8") == EXISTING_FILE_SENTINEL
    assert list(tmp_path.glob("*.tmp")) == []


def test_save_preserves_existing_file_when_replace_fails(tmp_path, monkeypatch):
    target = tmp_path / "portfolio_analysis.json"
    target.write_text(EXISTING_FILE_SENTINEL, encoding="utf-8")

    monkeypatch.setattr(orchestrate_portfolio, "run_orchestrator", Mock(return_value=_valid_merged_result()))

    def _raise_on_replace(*args, **kwargs):
        raise OSError("os.replace 직전 강제 실패 (테스트)")

    monkeypatch.setattr(orchestrate_portfolio.os, "replace", _raise_on_replace)

    exit_code = orchestrate_portfolio.main(
        ["--portfolio", str(EXAMPLE_PORTFOLIO), "--save-json", str(target)]
    )

    assert exit_code != 0
    assert target.read_text(encoding="utf-8") == EXISTING_FILE_SENTINEL
    assert list(tmp_path.glob("*.tmp")) == []


# --- AC-003: 허용 목록 밖 코드 거부 + 서브에이전트 미호출 -----------------------


def test_allowlist_rejects_out_of_range_codes_before_calling_subagent(tmp_path, monkeypatch, capsys):
    target = tmp_path / "portfolio_analysis.json"
    mock_run = Mock(side_effect=AssertionError("서브에이전트가 호출되면 안 된다"))
    monkeypatch.setattr(orchestrate_portfolio, "run_orchestrator", mock_run)

    exit_code = orchestrate_portfolio.main(["--portfolio", str(EDGE_PORTFOLIO), "--save-json", str(target)])

    assert exit_code != 0
    assert not target.exists()
    assert mock_run.call_count == 0
    captured = capsys.readouterr()
    assert "005380" in captured.err
    assert "999999" in captured.err


# --- AC-004: --sample 결정론 + 허용 목록 검사 동일 적용 -------------------------


def test_sample_mode_is_deterministic_and_never_touches_subprocess(tmp_path, monkeypatch):
    mock_run_subprocess = Mock(side_effect=AssertionError("subprocess 가 호출되면 안 된다"))
    mock_which = Mock(side_effect=AssertionError("shutil.which 가 호출되면 안 된다"))
    monkeypatch.setattr(orchestrate_portfolio.subprocess, "run", mock_run_subprocess)
    monkeypatch.setattr(orchestrate_portfolio.shutil, "which", mock_which)

    target_1 = tmp_path / "first" / "portfolio_analysis.json"
    target_2 = tmp_path / "second" / "portfolio_analysis.json"

    exit_code_1 = orchestrate_portfolio.main(
        ["--sample", "--portfolio", str(EXAMPLE_PORTFOLIO), "--save-json", str(target_1)]
    )
    exit_code_2 = orchestrate_portfolio.main(
        ["--sample", "--portfolio", str(EXAMPLE_PORTFOLIO), "--save-json", str(target_2)]
    )

    assert exit_code_1 == 0
    assert exit_code_2 == 0
    assert mock_run_subprocess.call_count == 0
    assert mock_which.call_count == 0
    assert target_1.read_bytes() == target_2.read_bytes()

    document = json.loads(target_1.read_text(encoding="utf-8"))
    assert document["source"] == "sample"
    assert orchestrate_portfolio.validate_schema(document) == []

    verdicts = [r["verdict"] for r in document["valuation"]["results"]]
    overalls = [r["overall"] for r in document["risk"]["results"]]
    actions = [r["action"] for r in document["allocation"]["results"]]
    assert any(v != "unknown" for v in verdicts)
    assert any(v == "unknown" for v in verdicts)
    assert any(o != "unknown" for o in overalls)
    assert any(o == "unknown" for o in overalls)
    assert any(a != "unknown" for a in actions)
    assert any(a == "unknown" for a in actions)


def test_sample_mode_still_rejects_out_of_allowlist_codes(tmp_path):
    target = tmp_path / "portfolio_analysis.json"

    exit_code = orchestrate_portfolio.main(
        ["--sample", "--portfolio", str(EDGE_PORTFOLIO), "--save-json", str(target)]
    )

    assert exit_code != 0
    assert not target.exists()


# --- validate_schema 단위 검증 (다섯 조건 개별) --------------------------------


@pytest.mark.parametrize(
    "mutate",
    [
        lambda d: d.pop("allocation"),
        lambda d: d.__setitem__("risk", {"agent": "x", "total_market_value": 1, "results": "not-a-list"}),
        lambda d: d["valuation"]["results"].pop(),
    ],
)
def test_validate_schema_detects_violations(mutate):
    document = orchestrate_portfolio.assemble_document(
        _valid_merged_result(), source="agent-team", generated_date="2026-09-22", portfolio_file="x"
    )
    mutate(document)

    errors = orchestrate_portfolio.validate_schema(document)

    assert errors != []


def test_validate_schema_passes_for_well_formed_document():
    document = orchestrate_portfolio.assemble_document(
        _valid_merged_result(), source="agent-team", generated_date="2026-09-22", portfolio_file="x"
    )

    assert orchestrate_portfolio.validate_schema(document) == []
