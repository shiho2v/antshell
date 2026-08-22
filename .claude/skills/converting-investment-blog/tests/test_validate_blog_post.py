# =============================================================
# File   : test_validate_blog_post.py
# Author : @suhdongphill
# Week   : 04 | Ch.04 (2/2)
# Created: 2026-07-25
# =============================================================
"""validate_blog_post.py 회귀 테스트.

generating-krx-report 의 실제 산출물(gitignore 대상)에 의존하지 않도록
최소 manifest 를 임시 디렉터리에 만들어 --data-dir 로 주입한다.

실행: pytest .claude/skills/converting-investment-blog/tests/ -q
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "validate_blog_post.py"
TICKER = "009240"

MINIMAL_MANIFEST = {
    "ticker": TICKER,
    "company_name": "테스트기업",
    "composite": {
        "score": 55.7,
        "confidence": 0.743,
        "data_completeness": 0.915,
        "verdict": "중립적 관찰",
    },
    "modules": [{"module": "quality", "score": 64.7, "confidence": 0.9}],
    "claims": [
        {"claim_id": "CLM-0004", "claim": "영업이익률은 TTM 기준 1.3%로 매우 낮다."},
        {"claim_id": "CLM-0009", "claim": "2026년 1분기 매출은 전년 동기 대비 9.9% 감소했다."},
    ],
}

FRONT_MATTER = """---
title: "{title}"
ticker: "009240"
company: "테스트기업"
as_of: "2026-07-25"
composite_score: 55.7
verdict: "{verdict}"
confidence: 0.743
data_completeness: 0.915
claim_count: 2
status: "draft"
---
"""

DISCLAIMER = "\n> 본 글은 교육용 기록이며, **투자 자문이 아닙니다.**\n"


def write_draft(tmp_path: Path, body: str, title: str = "테스트기업(009240) 숫자로 본 현재",
                verdict: str = "중립적 관찰", with_disclaimer: bool = True) -> Path:
    draft_path = tmp_path / "draft.md"
    content = FRONT_MATTER.format(title=title, verdict=verdict) + body
    if with_disclaimer:
        content += DISCLAIMER
    draft_path.write_text(content, encoding="utf-8")
    return draft_path


MINIMAL_TREND_MODULE = {
    "module": "trend",
    "criteria_scores": [
        {"criterion_id": "TRD-C", "name": "C — 최근 분기 실적", "type": "auto",
         "level": 0, "weight": 15, "metric": "eps_yoy_q", "metric_value": -72.68},
        {"criterion_id": "TRD-A", "name": "A — 연간 이익 성장", "type": "auto",
         "level": None, "weight": 15, "metric": "op_cagr_3y", "metric_value": None,
         "na_reason": "기준연도 영업적자로 정의 불가"},
    ],
}


@pytest.fixture
def data_dir(tmp_path: Path) -> Path:
    directory = tmp_path / "data"
    directory.mkdir()
    manifest_path = directory / f"{TICKER}_manifest.json"
    manifest_path.write_text(
        json.dumps(MINIMAL_MANIFEST, ensure_ascii=False), encoding="utf-8"
    )
    module_dir = directory / "module-results"
    module_dir.mkdir()
    (module_dir / f"{TICKER}_trend.json").write_text(
        json.dumps(MINIMAL_TREND_MODULE, ensure_ascii=False), encoding="utf-8"
    )
    return directory


def run_validator(draft_path: Path, data_dir: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT_PATH), str(draft_path),
         "--ticker", TICKER, "--data-dir", str(data_dir)],
        capture_output=True, text=True, encoding="utf-8",
    )


def test_valid_draft_passes(tmp_path: Path, data_dir: Path) -> None:
    body = "\n## 1. 한 줄 요약\n\n종합점수는 55.7점이다.<!-- MANIFEST -->\n" \
           "영업이익률은 1.3%다.<!-- CLM-0004 -->\n"
    result = run_validator(write_draft(tmp_path, body), data_dir)
    assert result.returncode == 0, result.stdout


def test_number_without_annotation_fails(tmp_path: Path, data_dir: Path) -> None:
    body = "\n## 1. 한 줄 요약\n\n영업이익률은 7.7%로 업계 평균을 웃돈다.\n"
    result = run_validator(write_draft(tmp_path, body), data_dir)
    assert result.returncode == 1
    assert "근거 주석" in result.stdout


def test_manifest_annotation_rejects_unknown_number(tmp_path: Path, data_dir: Path) -> None:
    body = "\n## 1. 한 줄 요약\n\n종합점수는 99.9점이다.<!-- MANIFEST -->\n"
    result = run_validator(write_draft(tmp_path, body), data_dir)
    assert result.returncode == 1
    assert "99.9" in result.stdout


def test_claim_annotation_only_warns_on_unknown_number(tmp_path: Path, data_dir: Path) -> None:
    body = "\n## 1. 한 줄 요약\n\n영업이익률은 7.7%다.<!-- CLM-0004 -->\n"
    result = run_validator(write_draft(tmp_path, body), data_dir)
    assert result.returncode == 0
    assert "[WARN]" in result.stdout


def test_dangling_claim_id_fails(tmp_path: Path, data_dir: Path) -> None:
    body = "\n## 1. 한 줄 요약\n\n영업이익률은 1.3%다.<!-- CLM-9999 -->\n"
    result = run_validator(write_draft(tmp_path, body), data_dir)
    assert result.returncode == 1
    assert "CLM-9999" in result.stdout


def test_buy_sell_in_title_fails(tmp_path: Path, data_dir: Path) -> None:
    body = "\n## 1. 한 줄 요약\n\n영업이익률은 1.3%다.<!-- CLM-0004 -->\n"
    draft_path = write_draft(tmp_path, body, title="지금이 매수 기회인 테스트기업(009240)")
    result = run_validator(draft_path, data_dir)
    assert result.returncode == 1
    assert "매수" in result.stdout


def test_net_buy_term_is_allowed(tmp_path: Path, data_dir: Path) -> None:
    body = "\n## 1. 한 줄 요약\n\n기관 순매수가 이어졌고 영업이익률은 1.3%다.<!-- CLM-0004 -->\n"
    result = run_validator(write_draft(tmp_path, body), data_dir)
    assert result.returncode == 0, result.stdout


def test_missing_disclaimer_fails(tmp_path: Path, data_dir: Path) -> None:
    body = "\n## 1. 한 줄 요약\n\n영업이익률은 1.3%다.<!-- CLM-0004 -->\n"
    draft_path = write_draft(tmp_path, body, with_disclaimer=False)
    result = run_validator(draft_path, data_dir)
    assert result.returncode == 1
    assert "면책" in result.stdout


def test_verdict_mismatch_fails(tmp_path: Path, data_dir: Path) -> None:
    body = "\n## 1. 한 줄 요약\n\n영업이익률은 1.3%다.<!-- CLM-0004 -->\n"
    draft_path = write_draft(tmp_path, body, verdict="긍정적 관찰")
    result = run_validator(draft_path, data_dir)
    assert result.returncode == 1
    assert "manifest 결론" in result.stdout


def test_sources_section_is_exempt(tmp_path: Path, data_dir: Path) -> None:
    body = ("\n## 1. 한 줄 요약\n\n영업이익률은 1.3%다.<!-- CLM-0004 -->\n"
            "\n## 8. 출처·기준일·면책\n\n| dart | official_api | 8건 | 2026-07-25 |\n")
    result = run_validator(write_draft(tmp_path, body), data_dir)
    assert result.returncode == 0, result.stdout


def test_wrapped_sentence_shares_annotation(tmp_path: Path, data_dir: Path) -> None:
    """Markdown 소프트랩 — 주석이 다음 줄에 붙어도 같은 문단이면 인정한다."""
    body = ("\n## 1. 한 줄 요약\n\n재무구조도 뒷받침한다. 영업이익률은 1.3%이며,\n"
            "매출은 9.9% 줄었다.<!-- CLM-0004 --><!-- CLM-0009 -->\n")
    result = run_validator(write_draft(tmp_path, body), data_dir)
    assert result.returncode == 0, result.stdout


def test_table_rows_need_their_own_annotation(tmp_path: Path, data_dir: Path) -> None:
    """표의 각 행은 독립된 근거 단위다 — 윗 행의 주석이 아랫 행을 덮지 않는다."""
    body = ("\n## 3. 지표\n\n| 지표 | 값 |\n|---|---|\n"
            "| 영업이익률 | 1.3%<!-- CLM-0004 --> |\n| 매출 성장률 | -9.9% |\n")
    result = run_validator(write_draft(tmp_path, body), data_dir)
    assert result.returncode == 1
    assert "근거 주석" in result.stdout


def test_list_items_are_separate_units(tmp_path: Path, data_dir: Path) -> None:
    body = ("\n## 5. 리스크\n\n- 영업이익률은 1.3%다.<!-- CLM-0004 -->\n"
            "- 매출은 9.9% 줄었다.\n")
    result = run_validator(write_draft(tmp_path, body), data_dir)
    assert result.returncode == 1
    assert "근거 주석" in result.stdout


def test_criterion_annotation_passes(tmp_path: Path, data_dir: Path) -> None:
    """MOD 주석은 module-results 의 criteria_scores 값을 인용할 수 있게 한다."""
    body = ("\n## 5. CANSLIM\n\n| 항목 | 값 | 등급 |\n|---|---|---|\n"
            "| C | -72.7% | 0 |<!-- MOD:trend/TRD-C -->\n")
    result = run_validator(write_draft(tmp_path, body), data_dir)
    assert result.returncode == 0, result.stdout
    assert "채점 항목 1" in result.stdout


def test_dangling_criterion_fails(tmp_path: Path, data_dir: Path) -> None:
    body = ("\n## 5. CANSLIM\n\n| C | -72.7% | 0 |<!-- MOD:trend/TRD-Z -->\n")
    result = run_validator(write_draft(tmp_path, body), data_dir)
    assert result.returncode == 1
    assert "존재하지 않는 채점 항목" in result.stdout


def test_criterion_annotation_rejects_unknown_number(tmp_path: Path, data_dir: Path) -> None:
    """MOD 는 '채점표를 그대로 옮겼다'는 선언이므로 원장 밖 숫자를 막는다."""
    body = ("\n## 5. CANSLIM\n\n| C | -88.8% | 0 |<!-- MOD:trend/TRD-C -->\n")
    result = run_validator(write_draft(tmp_path, body), data_dir)
    assert result.returncode == 1
    assert "-88.8" in result.stdout


def test_na_criterion_needs_no_number(tmp_path: Path, data_dir: Path) -> None:
    body = ("\n## 5. CANSLIM\n\n| A | N/A | — | 기준연도 영업적자로 정의 불가 |"
            "<!-- MOD:trend/TRD-A -->\n")
    result = run_validator(write_draft(tmp_path, body), data_dir)
    assert result.returncode == 0, result.stdout


def make_chart_ledger(tmp_path: Path, with_image_file: bool = True) -> None:
    """초안 옆에 render_charts.py 가 남기는 차트 원장을 흉내낸다."""
    asset_dir = tmp_path / "assets" / TICKER
    asset_dir.mkdir(parents=True)
    ledger = {
        "ticker": TICKER,
        "charts": [{"name": "canslim_grades", "file": "canslim_grades.png",
                    "title": "CANSLIM 7항목 채점"}],
    }
    (asset_dir / "charts.json").write_text(
        json.dumps(ledger, ensure_ascii=False), encoding="utf-8"
    )
    if with_image_file:
        (asset_dir / "canslim_grades.png").write_bytes(b"fake-png")


def test_figure_annotation_passes(tmp_path: Path, data_dir: Path) -> None:
    make_chart_ledger(tmp_path)
    body = ("\n## 5. 추세\n\n![CANSLIM](assets/009240/canslim_grades.png)"
            "<!-- FIG:canslim_grades -->\n\n영업이익률은 1.3%다.<!-- CLM-0004 -->\n")
    result = run_validator(write_draft(tmp_path, body), data_dir)
    assert result.returncode == 0, result.stdout
    assert "차트 1 / 1" in result.stdout


def test_image_without_figure_annotation_fails(tmp_path: Path, data_dir: Path) -> None:
    make_chart_ledger(tmp_path)
    body = ("\n## 5. 추세\n\n![CANSLIM](assets/009240/canslim_grades.png)\n"
            "\n영업이익률은 1.3%다.<!-- CLM-0004 -->\n")
    result = run_validator(write_draft(tmp_path, body), data_dir)
    assert result.returncode == 1
    assert "차트 주석" in result.stdout


def test_unknown_figure_fails(tmp_path: Path, data_dir: Path) -> None:
    make_chart_ledger(tmp_path)
    body = ("\n## 5. 추세\n\n![없는 차트](assets/009240/nope.png)<!-- FIG:nope -->\n"
            "\n영업이익률은 1.3%다.<!-- CLM-0004 -->\n")
    result = run_validator(write_draft(tmp_path, body), data_dir)
    assert result.returncode == 1
    assert "차트 원장에 없는" in result.stdout


def test_missing_image_file_fails(tmp_path: Path, data_dir: Path) -> None:
    make_chart_ledger(tmp_path, with_image_file=False)
    body = ("\n## 5. 추세\n\n![CANSLIM](assets/009240/canslim_grades.png)"
            "<!-- FIG:canslim_grades -->\n\n영업이익률은 1.3%다.<!-- CLM-0004 -->\n")
    result = run_validator(write_draft(tmp_path, body), data_dir)
    assert result.returncode == 1
    assert "그림 파일이 없다" in result.stdout


def test_image_hidden_in_sources_section_fails(tmp_path: Path, data_dir: Path) -> None:
    """출처절은 수치 검사 제외 구역이라 이미지를 숨기는 통로가 될 수 있다."""
    make_chart_ledger(tmp_path)
    body = ("\n## 1. 요약\n\n영업이익률은 1.3%다.<!-- CLM-0004 -->\n"
            "\n## 8. 출처\n\n![숨긴 차트](assets/009240/canslim_grades.png)\n")
    result = run_validator(write_draft(tmp_path, body), data_dir)
    assert result.returncode == 1
    assert "검증 제외 구역" in result.stdout


def test_ticker_mismatch_is_execution_error(tmp_path: Path, data_dir: Path) -> None:
    body = "\n## 1. 한 줄 요약\n\n영업이익률은 1.3%다.<!-- CLM-0004 -->\n"
    draft_path = write_draft(tmp_path, body)
    result = subprocess.run(
        [sys.executable, str(SCRIPT_PATH), str(draft_path),
         "--ticker", "005930", "--data-dir", str(data_dir)],
        capture_output=True, text=True, encoding="utf-8",
    )
    assert result.returncode == 2
