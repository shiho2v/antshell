#!/usr/bin/env python3
# =============================================================
# File   : commit_format.py
# Author : @shiho2v
# Week   : 01 | Ch.01~02
# Created: 2025-07-05
# =============================================================
"""PreToolUse 훅: git commit 메시지 형식 검사 및 자동 경고."""
import json, sys, re

TYPES = ["feat", "fix", "docs", "refactor", "test", "chore", "style"]
PATTERN = re.compile(r'^(' + '|'.join(TYPES) + r'): .+')


def parse_commit_message(cmd: str) -> str | None:
    """커밋 명령에서 -m 플래그의 메시지를 추출한다.

    [Week 01 | @shiho2v]
    Ch.02 깃 통합 워크플로 4단계 중 '커밋' 단계에서 동작.
    에이전틱 루프의 '결과 확인' — 규칙 기반 피드백으로 메시지 형식 검증.

    Args:
        cmd: 실행된 전체 git 명령 문자열

    Returns:
        -m 플래그 이후의 커밋 메시지. 없으면 None.
    """
    m = re.search(r'-m\s+["\']?([^"\']+)["\']?', cmd)
    return m.group(1).strip() if m else None


def validate_message(msg: str) -> bool:
    """커밋 메시지가 Conventional Commits 형식을 따르는지 검사한다.

    [Week 01 | @shiho2v]
    GIT_RULES.md §11.2 준수 — feat/fix/docs 등 타입 접두사 필수.
    PreToolUse 훅 특성상 검사 실패해도 커밋은 차단하지 않고 경고만 출력.

    Args:
        msg: 검사할 커밋 메시지 문자열

    Returns:
        형식이 올바르면 True, 아니면 False.
    """
    return bool(PATTERN.match(msg))


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

if not validate_message(commit_msg):
    print(f"""
[commit_format] ⚠️  커밋 메시지 형식 확인:
  현재: "{commit_msg}"
  권장: "feat: 기능 설명" 또는 "fix: 버그 수정"
  타입: {', '.join(TYPES)}
  (형식이 틀려도 커밋은 진행됩니다)
""", file=sys.stderr)

sys.exit(0)
