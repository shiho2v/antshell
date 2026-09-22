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
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
OUTPUTS_DIR = PROJECT_ROOT / "outputs"
DEFAULT_ANALYSIS_PATH = DATA_DIR / "portfolio_analysis.json"

# spec.md §1.3: 서브에이전트가 읽는 입력(data/{code}_market.json 등)이
# 존재하는 종목으로 한정한다. 이 목록 밖 코드가 섞이면 분석을 시작하지 않는다(REQ-003).
STOCK_CODES = ("005930", "000660", "009150", "008490")

SCHEMA_VERSION = "1"

# spec.md §4 「필수 키 집합」 — REQ-002(저장 전 검사)·REQ-004(--sample 검사)·
# REQ-007(백엔드 읽기 시 검사, M2)이 공통으로 참조하는 유일한 정의.
REQUIRED_TOP_LEVEL_KEYS = (
    "schema_version",
    "source",
    "generated_date",
    "portfolio_file",
    "portfolio_name",
    "as_of",
    "valuation",
    "risk",
    "allocation",
)
VALUATION_MIN_KEYS = ("stock_code", "verdict", "score")
RISK_MIN_KEYS = ("stock_code", "overall")
ALLOCATION_MIN_KEYS = ("stock_code", "actual_weight_pct", "action", "drift_pct", "rebalance_amount")

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

    # 서브에이전트가 스키마를 안 지키고 마크다운/설명을 섞어 돌려주는 경우가 있어
    # 어느 단계에서 깨졌는지 눈에 보이도록 감싼다.
    try:
        envelope = json.loads(result.stdout)
    except json.JSONDecodeError as e:
        raise RuntimeError(
            f"claude CLI 응답 봉투(JSON) 파싱 실패: {e}\n원 응답(앞 500자): {result.stdout[:500]!r}"
        ) from e

    raw_result = envelope.get("result", "")
    try:
        return json.loads(raw_result)
    except json.JSONDecodeError as e:
        raise RuntimeError(
            f"오케스트레이터 결과(JSON) 파싱 실패: {e}\n"
            "→ 서브에이전트가 스키마를 벗어난 텍스트를 반환했을 가능성이 큽니다.\n"
            f"원 result(앞 500자): {raw_result[:500]!r}"
        ) from e


def validate_allowlist(portfolio: dict) -> list:
    """§1.3 허용 목록 검사. 서브에이전트 호출 전에 먼저 실행해야 한다(REQ-003).

    허용 목록 밖 종목 코드 리스트를 돌려준다. 빈 리스트면 통과.
    """
    holdings = portfolio.get("holdings", [])
    return [h.get("stock_code") for h in holdings if h.get("stock_code") not in STOCK_CODES]


def validate_schema(document: dict) -> list:
    """spec.md §4 「필수 키 집합」 다섯 조건을 검사해 위반 사유 목록을 돌려준다.

    빈 리스트면 다섯 조건을 모두 만족한다. REQ-002(저장 전)·REQ-004(--sample)가
    이 함수를 공유하며, M2의 REQ-007(백엔드 읽기 시 검사)도 같은 정의를 구현해야 한다.
    """
    errors = []

    missing_top = [k for k in REQUIRED_TOP_LEVEL_KEYS if k not in document]
    if missing_top:
        errors.append(f"최상위 키 누락: {', '.join(missing_top)}")
        return errors

    blocks = {}
    for block_name in ("valuation", "risk", "allocation"):
        block = document.get(block_name)
        if not isinstance(block, dict):
            errors.append(f"'{block_name}'은 객체가 아닙니다")
            continue
        results = block.get("results")
        if not isinstance(results, list):
            errors.append(f"'{block_name}.results'는 리스트가 아닙니다")
            continue
        blocks[block_name] = results

    if len(blocks) < 3:
        return errors

    numeric_fields = {
        "risk.total_market_value": document["risk"].get("total_market_value"),
        "allocation.total_asset": document["allocation"].get("total_asset"),
        "allocation.cash": document["allocation"].get("cash"),
    }
    for field_name, value in numeric_fields.items():
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            errors.append(f"'{field_name}'은 숫자가 아닙니다: {value!r}")

    lengths = {name: len(results) for name, results in blocks.items()}
    if len(set(lengths.values())) > 1:
        errors.append(f"results 리스트 길이 불일치: {lengths}")

    min_keys_by_block = {
        "valuation": VALUATION_MIN_KEYS,
        "risk": RISK_MIN_KEYS,
        "allocation": ALLOCATION_MIN_KEYS,
    }
    for block_name, min_keys in min_keys_by_block.items():
        for idx, item in enumerate(blocks[block_name]):
            if not isinstance(item, dict):
                errors.append(f"'{block_name}.results[{idx}]'는 객체가 아닙니다")
                continue
            missing = [k for k in min_keys if k not in item]
            if missing:
                errors.append(f"'{block_name}.results[{idx}]' 필수 키 누락: {', '.join(missing)}")

    return errors


def assemble_document(merged: dict, source: str, generated_date: str, portfolio_file: str) -> dict:
    """저장 단계에서 4개 메타 필드를 병합 결과에 덧붙인다(REQ-001).

    나머지(portfolio_name·as_of·valuation·risk·allocation)는 merged 를 그대로 보존한다.
    """
    return {
        "schema_version": SCHEMA_VERSION,
        "source": source,
        "generated_date": generated_date,
        "portfolio_file": portfolio_file,
        **merged,
    }


def save_json_atomic(path: Path, document: dict) -> None:
    """같은 디렉터리의 임시 파일에 먼저 기록한 뒤 교체한다(REQ-001).

    교체(os.replace) 이전 단계에서 예외가 나면 대상 파일은 그대로 보존되고
    임시 파일도 정리된다(AC-002).
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(dir=str(path.parent), prefix=f".{path.name}.", suffix=".tmp")
    tmp_path = Path(tmp_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as tmp_file:
            json.dump(document, tmp_file, ensure_ascii=False, indent=2)
            tmp_file.write("\n")
        os.replace(tmp_name, path)
    except BaseException:
        if tmp_path.exists():
            tmp_path.unlink()
        raise


def generate_sample(portfolio: dict, generated_date: str) -> dict:
    """--sample 모드의 결정론적 분석 결과 생성(REQ-004).

    claude 서브에이전트를 호출하지 않고 입력 포트폴리오 파일만으로
    §4 「필수 키 집합」을 만족하는 병합 결과를 만든다. 같은 입력·같은 실행일이면
    항상 같은 바이트를 만든다(난수·시각 미사용). 보유 종목 순서 기준 짝수 인덱스는
    정상 판정, 홀수 인덱스는 unknown 판정으로 고정해 판정 값 분포 요구를 충족한다.
    """
    holdings = portfolio.get("holdings", [])
    if not holdings:
        raise ValueError("portfolio.holdings가 비어 있습니다.")

    cash = _num(portfolio.get("cash"), 0.0)

    enriched = []
    for holding in holdings:
        quantity = _num(holding.get("quantity"), 0.0)
        avg_price = _num(holding.get("avg_price"), 0.0)
        enriched.append(
            {
                "stock_code": holding.get("stock_code", ""),
                "name": holding.get("name", ""),
                "quantity": quantity,
                "avg_price": avg_price,
                "market_value": quantity * avg_price,
                "target_weight_pct": _num(holding.get("target_weight_pct"), 0.0),
            }
        )

    total_holdings_value = sum(item["market_value"] for item in enriched)
    total_asset = total_holdings_value + cash

    valuation_results, risk_results, allocation_results = [], [], []

    for idx, item in enumerate(enriched):
        known = idx % 2 == 0
        actual_weight_alloc = round(item["market_value"] / total_asset * 100, 2) if total_asset else 0.0
        actual_weight_risk = (
            round(item["market_value"] / total_holdings_value * 100, 2) if total_holdings_value else 0.0
        )
        drift = round(actual_weight_alloc - item["target_weight_pct"], 2)

        if known:
            verdict, score, overall = "적정", 60, "medium"
            action = "유지" if abs(drift) < 1 else ("매도" if drift > 0 else "매수")
            basis = "샘플 생성 — 실제 에이전트 판정이 아닙니다"
            rebalance_amount = round(item["target_weight_pct"] / 100 * total_asset - item["market_value"])
        else:
            verdict, score, overall, action = "unknown", 0, "unknown", "unknown"
            basis = "샘플 생성 — 데이터 부족으로 판정 불가"
            rebalance_amount = 0

        valuation_results.append(
            {
                "stock_code": item["stock_code"],
                "name": item["name"],
                "revenue_growth_pct": None,
                "op_income_growth_pct": None,
                "verdict": verdict,
                "score": score,
                "basis": basis,
            }
        )
        risk_results.append(
            {
                "stock_code": item["stock_code"],
                "name": item["name"],
                "market_value": item["market_value"],
                "actual_weight_pct": actual_weight_risk,
                "concentration": "중간" if known else "unknown",
                "drawdown_from_52w": "0%" if known else "unknown",
                "supply_flow": "중립" if known else "unknown",
                "volume_state": "normal" if known else "unknown",
                "risk_score": score,
                "overall": overall,
            }
        )
        allocation_results.append(
            {
                "stock_code": item["stock_code"],
                "name": item["name"],
                "current_price": item["avg_price"],
                "market_value": item["market_value"],
                "actual_weight_pct": actual_weight_alloc,
                "target_weight_pct": item["target_weight_pct"],
                "drift_pct": drift,
                "action": action,
                "rebalance_amount": rebalance_amount,
            }
        )

    return {
        "portfolio_name": portfolio.get("portfolio_name", "포트폴리오"),
        "as_of": portfolio.get("as_of", generated_date),
        "valuation": {"agent": "sample", "results": valuation_results},
        "risk": {
            "agent": "sample",
            "total_market_value": total_holdings_value,
            "results": risk_results,
        },
        "allocation": {
            "agent": "sample",
            "total_asset": total_asset,
            "cash": cash,
            "results": allocation_results,
        },
    }


def _num(value, default: float = 0.0) -> float:
    # None/문자열 등 숫자 포맷팅(:,.0f, %)에 못 넣는 값을 안전하게 흡수한다.
    if isinstance(value, (int, float)):
        return float(value)
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


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
        f"<td>{_num(r.get('actual_weight_pct'))}%</td>"
        f"<td>{html.escape(str(r.get('concentration', '')))}</td>"
        f"<td>{html.escape(str(r.get('drawdown_from_52w', '')))}</td>"
        f"<td>{html.escape(str(r.get('supply_flow', '')))}</td>"
        f"<td>{_num(r.get('risk_score'))}</td>"
        f"<td>{html.escape(str(r.get('overall', '')))}</td></tr>"
        for r in merged.get("risk", {}).get("results", [])
    )

    alloc_rows = "".join(
        f"<tr><td>{html.escape(r.get('stock_code', ''))}</td>"
        f"<td>{html.escape(r.get('name', ''))}</td>"
        f"<td>{_num(r.get('actual_weight_pct'))}%</td>"
        f"<td>{_num(r.get('target_weight_pct'))}%</td>"
        f"<td>{_num(r.get('drift_pct'))}%p</td>"
        f"<td>{html.escape(str(r.get('action', '')))}</td>"
        f"<td>{_num(r.get('rebalance_amount')):,.0f}</td></tr>"
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
<p>총 평가금액: {_num(merged.get('risk', {}).get('total_market_value')):,.0f} 원</p>
<table>
  <thead><tr><th>종목코드</th><th>종목명</th><th>실제비중</th><th>집중도</th><th>52주낙폭</th><th>수급</th><th>점수</th><th>종합</th></tr></thead>
  <tbody>{risk_rows}</tbody>
</table>

<h2>3. 리밸런싱 (portfolio-allocation)</h2>
<p>총자산: {_num(merged.get('allocation', {}).get('total_asset')):,.0f} 원 · 현금: {_num(merged.get('allocation', {}).get('cash')):,.0f} 원</p>
<table>
  <thead><tr><th>종목코드</th><th>종목명</th><th>실제비중</th><th>목표비중</th><th>드리프트</th><th>액션</th><th>리밸런싱 금액(원)</th></tr></thead>
  <tbody>{alloc_rows}</tbody>
</table>

</body>
</html>
"""


def parse_arguments(argv):
    parser = argparse.ArgumentParser(description="포트폴리오 분석 에이전트 팀 오케스트레이터 (Ch.04 실습)")
    parser.add_argument("--portfolio", required=True, help="포트폴리오 JSON 경로 (예: data/portfolio.example.json)")
    parser.add_argument("--save", action="store_true", help="outputs/portfolio_report_YYYY-MM-DD.html로 저장")
    parser.add_argument(
        "--save-json",
        type=Path,
        default=DEFAULT_ANALYSIS_PATH,
        help=f"분석 결과 JSON 저장 경로. 기본 {DEFAULT_ANALYSIS_PATH.relative_to(PROJECT_ROOT)}",
    )
    parser.add_argument(
        "--sample",
        action="store_true",
        help="claude 서브에이전트를 호출하지 않고 결정론적 샘플 데이터를 생성한다(REQ-004).",
    )
    return parser.parse_args(argv)


def main(argv=None) -> int:
    # Windows 콘솔이 cp1252 기본일 때 한글 print에서 UnicodeEncodeError가 나는 것을 방지한다.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")

    args = parse_arguments(argv)

    try:
        portfolio = load_portfolio(Path(args.portfolio))
    except FileNotFoundError as e:
        print(f"[orchestrate_portfolio] {e}", file=sys.stderr)
        return 1

    # REQ-003: 서브에이전트 호출/샘플 생성 이전에 허용 목록을 검사한다.
    offending_codes = validate_allowlist(portfolio)
    if offending_codes:
        print(
            f"[orchestrate_portfolio] 허용 목록 밖 종목 코드가 포함되어 있습니다: {', '.join(offending_codes)}",
            file=sys.stderr,
        )
        return 1

    generated_date = dt.date.today().isoformat()
    source = "sample" if args.sample else "agent-team"

    try:
        if args.sample:
            merged = generate_sample(portfolio, generated_date)
        else:
            prompt = build_prompt(portfolio)
            merged = run_orchestrator(prompt)
    except (RuntimeError, ValueError) as e:
        print(f"[orchestrate_portfolio] 분석 실패: {e}", file=sys.stderr)
        return 1

    print(json.dumps(merged, ensure_ascii=False, indent=2))

    document = assemble_document(merged, source, generated_date, str(args.portfolio))
    schema_errors = validate_schema(document)
    if schema_errors:
        print("[orchestrate_portfolio] 저장 전 스키마 검사 실패:", file=sys.stderr)
        for err in schema_errors:
            print(f"  - {err}", file=sys.stderr)
        return 1

    try:
        save_json_atomic(Path(args.save_json), document)
    except OSError as e:
        print(f"[orchestrate_portfolio] 저장 실패: {e}", file=sys.stderr)
        return 1
    print(f"[orchestrate_portfolio] 저장됨: {args.save_json} (source={source})", file=sys.stderr)

    if args.save:
        OUTPUTS_DIR.mkdir(exist_ok=True)
        today = dt.date.today().isoformat()
        out_path = OUTPUTS_DIR / f"portfolio_report_{today}.html"
        out_path.write_text(render_html(merged), encoding="utf-8")
        print(f"저장됨: {out_path}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    sys.exit(main())
