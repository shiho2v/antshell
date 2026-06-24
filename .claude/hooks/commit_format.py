#!/usr/bin/env python3
"""
PreToolUse 훅: git commit 시 메시지 형식 검사 및 자동 제안
형식: 타입: 한글 요약 (50자 이내)
"""
import json, sys, re

TYPES = ["feat", "fix", "docs", "refactor", "test", "chore", "style"]
PATTERN = re.compile(r'^(' + '|'.join(TYPES) + r'): .+')

hook_input = {}
try:
    hook_input = json.loads(sys.stdin.read() or "{}")
except Exception:
    pass

cmd = hook_input.get("tool_input", {}).get("command", "")

if "git commit" not in cmd:
    sys.exit(0)

# -m 플래그로 메시지가 있는 경우만 검사
m = re.search(r'-m\s+["\']?([^"\']+)["\']?', cmd)
if not m:
    sys.exit(0)

commit_msg = m.group(1).strip()

if not PATTERN.match(commit_msg):
    print(f"""
[commit_format] ⚠️  커밋 메시지 형식 확인:
  현재: "{commit_msg}"
  권장: "feat: 기능 설명" 또는 "fix: 버그 수정"
  타입: {', '.join(TYPES)}
  (형식이 틀려도 커밋은 진행됩니다)
""", file=sys.stderr)

# exit 0 = 커밋 허용 (경고만 표시)
sys.exit(0)
