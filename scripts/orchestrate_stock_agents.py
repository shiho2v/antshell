"""news-collector, financial-data 서브에이전트를 병렬 호출해 결과를 병합하는 CLI 진입점.

사용법:
    python scripts/orchestrate_stock_agents.py 005930
    python scripts/orchestrate_stock_agents.py 삼성전자 --save

Claude Code 서브에이전트(.claude/agents/news-collector.md, financial-data.md)는
Claude Code 런타임(Task 도구)에서만 실행 가능하므로, 이 스크립트는 `claude -p`
헤드리스 모드를 통해 두 서브에이전트를 단일 메시지에서 병렬 호출하도록 지시한다.
"""

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"

ORCHESTRATOR_PROMPT_TEMPLATE = """\
아래 두 서브에이전트를 반드시 하나의 메시지 안에서 함께 호출해 병렬 실행하세요 (순차 호출 금지):
- news-collector: 종목 "{ticker}"의 최근 뉴스를 수집
- financial-data: 종목 "{ticker}"의 재무 데이터를 조회

두 서브에이전트의 결과를 받은 뒤, 아래 스키마 하나로만 병합해 응답하세요.
그 외 설명, 마크다운, 코드블록을 절대 덧붙이지 마세요:

{{
  "ticker": "{ticker}",
  "news": [...news-collector 결과의 news 배열...],
  "financials": {{...financial-data 결과 객체 전체(ticker 필드 제외)...}}
}}
"""


def run_orchestrator(ticker: str) -> dict:
    prompt = ORCHESTRATOR_PROMPT_TEMPLATE.format(ticker=ticker)

    claude_bin = shutil.which("claude")
    if claude_bin is None:
        raise RuntimeError("claude CLI를 PATH에서 찾을 수 없습니다. `npm install -g @anthropic-ai/claude-code` 설치 여부를 확인하세요.")

    # 프롬프트는 CLI 인자가 아니라 stdin으로 전달한다.
    # Windows에서 claude.CMD는 cmd.exe를 거쳐 실행되는데, 개행·중괄호가 섞인
    # 긴 인자를 넘기면 cmd.exe 파싱 단계에서 깨진다.
    # 헤드리스 모드는 대화형 권한 프롬프트가 없어 미승인 도구는 자동 거부된다.
    # news-collector/financial-data 서브에이전트가 선언한 도구만 명시적으로 허용한다.
    result = subprocess.run(
        [claude_bin, "-p", "--output-format", "json", "--allowedTools", "WebSearch,WebFetch"],
        input=prompt,
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=180,
    )

    if result.returncode != 0:
        raise RuntimeError(f"claude CLI 실행 실패: {result.stderr.strip()}")

    envelope = json.loads(result.stdout)
    return json.loads(envelope["result"])


def main() -> None:
    parser = argparse.ArgumentParser(description="뉴스/재무 서브에이전트 병렬 오케스트레이터")
    parser.add_argument("ticker", help="종목명 또는 6자리 티커 (예: 005930, 삼성전자)")
    parser.add_argument("--save", action="store_true", help="data/{ticker}_agents.json으로 저장")
    args = parser.parse_args()

    merged = run_orchestrator(args.ticker)
    print(json.dumps(merged, ensure_ascii=False, indent=2))

    if args.save:
        DATA_DIR.mkdir(exist_ok=True)
        output_path = DATA_DIR / f"{args.ticker}_agents.json"
        output_path.write_text(json.dumps(merged, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\n저장됨: {output_path}", file=sys.stderr)


if __name__ == "__main__":
    main()
