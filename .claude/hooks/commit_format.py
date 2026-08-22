#!/usr/bin/env python3
# =============================================================
# File   : commit_format.py
# Author : @shiho2v
# Week   : 06 | Ch.07 (1/2)
# Created: 2025-07-05
# =============================================================
"""PreToolUse 훅: git commit 메시지 형식 검사 및 자동 경고."""
import json, sys, re

TYPES = ["feat", "fix", "docs", "refactor", "test", "chore", "style"]

# feat: 설명  또는  feat(scope): 설명 모두 허용
PATTERN = re.compile(
    r'^(' + '|'.join(TYPES) + r')(\([^)]+\))?: .+'
)


def parse_commit_message(cmd: str) -> str | None:
    """커밋 명령에서 -m 플래그의 메시지를 추출한다."""
    m = re.search(r'-m\s+["\']?([^"\']+)["\']?', cmd)
    return m.group(1).strip() if m else None


def validate_format(msg: str) -> bool:
    """Conventional Commits 형식(scope 포함) 여부를 검사한다."""
    first_line = msg.split("\n")[0]
    return bool(PATTERN.match(first_line))


def suggest_fix(msg: str) -> str:
    """메시지를 분석해 올바른 형식 예시를 제안한다."""
    first_line = msg.split("\n")[0].strip()
    # 타입이 이미 있지만 콜론이 빠진 경우
    for t in TYPES:
        if first_line.lower().startswith(t):
            rest = first_line[len(t):].lstrip(" :(")
            return f'{t}: {rest}' if rest else f'{t}: 변경 내용 설명'
    return f'feat: {first_line}'


def check_co_authored(cmd: str) -> bool:
    """Co-Authored-By 줄이 커밋 메시지에 포함되어 있는지 확인한다."""
    return "Co-Authored-By" in cmd


# ── 메인 ──────────────────────────────────────────────────────
hook_input = {}
try:
    hook_input = json.loads(sys.stdin.read() or "{}")
except Exception:
    pass

cmd = hook_input.get("tool_input", {}).get("command", "")

if "git commit" not in cmd:
    sys.exit(0)

commit_msg = parse_commit_message(cmd)
if not commit_msg:
    sys.exit(0)

warnings = []

if not validate_format(commit_msg):
    suggestion = suggest_fix(commit_msg)
    warnings.append(
        f'  현재 : "{commit_msg.split(chr(10))[0]}"\n'
        f'  제안 : "{suggestion}"\n'
        f'  형식 : <type>(<scope>): 설명  (scope는 선택)\n'
        f'  타입 : {", ".join(TYPES)}'
    )

if not check_co_authored(cmd):
    warnings.append(
        '  Co-Authored-By 누락 — Claude Code 사용 시 아래 줄을 추가하세요:\n'
        '  Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>'
    )

if warnings:
    print("\n[commit_format] ⚠️  커밋 메시지 확인:", file=sys.stderr)
    for w in warnings:
        print(w, file=sys.stderr)
    print("  (경고만 표시되며 커밋은 진행됩니다)\n", file=sys.stderr)

sys.exit(0)
