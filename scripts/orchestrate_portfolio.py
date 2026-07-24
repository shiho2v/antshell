# =============================================================
# File   : orchestrate_portfolio.py
# Author : @ZeuroSurgeoZ
# Week   : 04 | Ch.04 (2/2)
# Created: 2026-07-25
# =============================================================
"""포트폴리오 분석 에이전트 팀(valuation/risk/allocation)을 병렬 호출해 종합 HTML 리포트를 생성하는 CLI 진입점.

사용법:
    python scripts/orchestrate_portfolio.py --portfolio data/portfolio.example.json
    python scripts/orchestrate_portfolio.py --portfolio data/portfolio.example.json --save

Ch.04 (2/2) 실습: 3주차 orchestrate_stock_agents.py 확장판.
- 리더(이 스크립트)가 헤드리스 `claude -p` 모드로 3 서브에이전트를 단일 메시지에서 동시에 Task 호출한다.
- 각 서브에이전트는 자기 소유의 data/*.json만 읽고 JSON 스키마로만 응답한다.
- 병합 결과는 outputs/portfolio_report_YYYY-MM-DD.html 로 저장한다.
"""

import argparse
import datetime as dt
import html
import json
import shutil
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
OUTPUTS_DIR = PROJECT_ROOT / "outputs"

ORCHESTRATOR_PROMPT_TEMPLATE = """\
아래 세 서브에이전트를 반드시 하나의 메시지 안에서 함께 호출해 병렬 실행하세요 (순차 호출 금지):
- portfolio-valuation: 아래 종목 리스트로 밸류에이션 판정
- portfolio-risk: 아래 포트폴리오 요약으로 리스크 지표 계산
- portfolio-allocation: 아래 포트폴리오 전체로 리밸런싱 액션 결정

각 서브에이전트에 전달할 입력은 아래와 같습니다.

[종목 리스트 (valuation용)]
{tickers_json}

[포트폴리오 요약 (risk용)]
{holdings_json}

[포트폴리오 전체 (allocation용)]
{portfolio_json}

세 서브에이전트의 결과를 받은 뒤, 아래 스키마 하나로만 병합해 응답하세요.
그 외 설명, 마크다운, 코드블록을 절대 덧붙이지 마세요:

{{
  "portfolio_name": "{portfolio_name}",
  "as_of": "{as_of}",
  "valuation": {{...portfolio-valuation 결과 객체 전체...}},
  "risk": {{...portfolio-risk 결과 객체 전체...}},
  "allocation": {{...portfolio-allocation 결과 객체 전체...}}
}}
"""


def load_portfolio(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(f"포트폴리오 파일을 찾을 수 없습니다: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def build_prompt(portfolio: dict) -> str:
    holdings = portfolio.get("holdings", [])
    if not holdings:
        raise ValueError("portfolio.holdings가 비어 있습니다.")

    tickers = [{"stock_code": h["stock_code"], "name": h.get("name", "")} for h in holdings]
    return ORCHESTRATOR_PROMPT_TEMPLATE.format(
        tickers_json=json.dumps(tickers, ensure_ascii=False),
        holdings_json=json.dumps(holdings, ensure_ascii=False),
        portfolio_json=json.dumps(portfolio, ensure_ascii=False),
        portfolio_name=portfolio.get("portfolio_name", "포트폴리오"),
        as_of=portfolio.get("as_of", dt.date.today().isoformat()),
    )


def run_orchestrator(prompt: str) -> dict:
    claude_bin = shutil.which("claude")
    if claude_bin is None:
        raise RuntimeError(
            "claude CLI를 PATH에서 찾을 수 없습니다. `npm install -g @anthropic-ai/claude-code` 설치 여부를 확인하세요."
        )

    # 3주차 스크립트와 동일한 이유로 프롬프트는 stdin으로 전달한다.
    # 서브에이전트가 선언한 도구(Read, Bash)만 명시적으로 허용해 미승인 도구 실행을 차단한다.
    result = subprocess.run(
        [claude_bin, "-p", "--output-format", "json", "--allowedTools", "Read,Bash"],
        input=prompt,
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=240,
    )

    if result.returncode != 0:
        raise RuntimeError(f"claude CLI 실행 실패: {result.stderr.strip()}")

    envelope = json.loads(result.stdout)
    return json.loads(envelope["result"])


def render_html(merged: dict) -> str:
    val_rows = "".join(
        f"<tr><td>{html.escape(r.get('stock_code', ''))}</td>"
        f"<td>{html.escape(r.get('name', ''))}</td>"
        f"<td>{r.get('revenue_growth_pct', 'N/A')}</td>"
        f"<td>{r.get('op_income_growth_pct', 'N/A')}</td>"
        f"<td>{html.escape(str(r.get('verdict', '')))}</td>"
        f"<td>{r.get('score', 0)}</td></tr>"
        for r in merged.get("valuation", {}).get("results", [])
    )

    risk_rows = "".join(
        f"<tr><td>{html.escape(r.get('stock_code', ''))}</td>"
        f"<td>{html.escape(r.get('name', ''))}</td>"
        f"<td>{r.get('actual_weight_pct', 0)}%</td>"
        f"<td>{html.escape(str(r.get('concentration', '')))}</td>"
        f"<td>{html.escape(str(r.get('drawdown_from_52w', '')))}</td>"
        f"<td>{html.escape(str(r.get('supply_flow', '')))}</td>"
        f"<td>{r.get('risk_score', 0)}</td>"
        f"<td>{html.escape(str(r.get('overall', '')))}</td></tr>"
        for r in merged.get("risk", {}).get("results", [])
    )

    alloc_rows = "".join(
        f"<tr><td>{html.escape(r.get('stock_code', ''))}</td>"
        f"<td>{html.escape(r.get('name', ''))}</td>"
        f"<td>{r.get('actual_weight_pct', 0)}%</td>"
        f"<td>{r.get('target_weight_pct', 0)}%</td>"
        f"<td>{r.get('drift_pct', 0)}%p</td>"
        f"<td>{html.escape(str(r.get('action', '')))}</td>"
        f"<td>{r.get('rebalance_amount', 0):,.0f}</td></tr>"
        for r in merged.get("allocation", {}).get("results", [])
    )

    return f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>포트폴리오 분석 리포트 — {html.escape(merged.get('portfolio_name', ''))}</title>
<style>
  body {{ font-family: -apple-system, "Segoe UI", sans-serif; margin: 32px; color: #222; }}
  h1 {{ margin-bottom: 4px; }}
  .meta {{ color: #666; margin-bottom: 24px; }}
  h2 {{ border-bottom: 2px solid #333; padding-bottom: 4px; margin-top: 32px; }}
  table {{ border-collapse: collapse; width: 100%; margin-top: 12px; }}
  th, td {{ border: 1px solid #ddd; padding: 8px 12px; text-align: right; }}
  th {{ background: #f5f5f5; text-align: center; }}
  td:nth-child(1), td:nth-child(2) {{ text-align: left; }}
</style>
</head>
<body>
<h1>{html.escape(merged.get('portfolio_name', '포트폴리오'))} — 종합 분석</h1>
<div class="meta">기준일: {html.escape(merged.get('as_of', ''))} · 팀: portfolio-analysis (valuation + risk + allocation)</div>

<h2>1. 밸류에이션 (portfolio-valuation)</h2>
<table>
  <thead><tr><th>종목코드</th><th>종목명</th><th>매출성장</th><th>영업이익성장</th><th>판정</th><th>점수</th></tr></thead>
  <tbody>{val_rows}</tbody>
</table>

<h2>2. 리스크 (portfolio-risk)</h2>
<p>총 평가금액: {merged.get('risk', {}).get('total_market_value', 0):,.0f} 원</p>
<table>
  <thead><tr><th>종목코드</th><th>종목명</th><th>실제비중</th><th>집중도</th><th>52주낙폭</th><th>수급</th><th>점수</th><th>종합</th></tr></thead>
  <tbody>{risk_rows}</tbody>
</table>

<h2>3. 리밸런싱 (portfolio-allocation)</h2>
<p>총자산: {merged.get('allocation', {}).get('total_asset', 0):,.0f} 원 · 현금: {merged.get('allocation', {}).get('cash', 0):,.0f} 원</p>
<table>
  <thead><tr><th>종목코드</th><th>종목명</th><th>실제비중</th><th>목표비중</th><th>드리프트</th><th>액션</th><th>리밸런싱 금액(원)</th></tr></thead>
  <tbody>{alloc_rows}</tbody>
</table>

</body>
</html>
"""


def main() -> None:
    # Windows 콘솔이 cp1252 기본일 때 한글 print에서 UnicodeEncodeError가 나는 것을 방지한다.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description="포트폴리오 분석 에이전트 팀 오케스트레이터 (Ch.04 실습)")
    parser.add_argument("--portfolio", required=True, help="포트폴리오 JSON 경로 (예: data/portfolio.example.json)")
    parser.add_argument("--save", action="store_true", help="outputs/portfolio_report_YYYY-MM-DD.html로 저장")
    args = parser.parse_args()

    portfolio = load_portfolio(Path(args.portfolio))
    prompt = build_prompt(portfolio)
    merged = run_orchestrator(prompt)

    print(json.dumps(merged, ensure_ascii=False, indent=2))

    if args.save:
        OUTPUTS_DIR.mkdir(exist_ok=True)
        today = dt.date.today().isoformat()
        out_path = OUTPUTS_DIR / f"portfolio_report_{today}.html"
        out_path.write_text(render_html(merged), encoding="utf-8")
        print(f"\n저장됨: {out_path}", file=sys.stderr)


if __name__ == "__main__":
    main()
