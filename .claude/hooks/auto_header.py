#!/usr/bin/env python3
# =============================================================
# File   : auto_header.py
# Author : @shiho2v
# Week   : 01 | Ch.01~02
# Created: 2025-07-05
# =============================================================
"""PostToolUse 훅: 새 코드 파일 Write 시 주차별 헤더 주석 자동 삽입."""
import json, sys, os, subprocess
from datetime import datetime
from pathlib import Path

SUPPORTED = {'.py', '.ts', '.tsx', '.js', '.jsx'}
PY_MARKER = '# ============'
JS_MARKER = '// ============'


def get_git_user() -> str:
    """Git 설정에서 현재 사용자명을 가져온다.

    [Week 01 | @shiho2v]
    Ch.01 깃 통합 — git config user.name 으로 작성자를 자동 식별.
    IAM 개념의 '누가' 에 해당하는 정보를 코드 수준에서 추적.

    Returns:
        Git user.name 값. 실패 시 'unknown'.
    """
    try:
        return subprocess.check_output(
            ['git', 'config', 'user.name'], text=True
        ).strip()
    except Exception:
        return 'unknown'


def get_week_info() -> tuple[str, str]:
    """CLAUDE.md에서 현재 주차와 챕터 정보를 읽는다.

    [Week 01 | @shiho2v]
    Ch.02 설정관리 — CLAUDE.md는 세션 시작 시 로드되는 팀 공유 메모리.
    CURRENT_WEEK 값으로 주차별 컨텍스트를 자동 연결.

    Returns:
        (week, chapter) 튜플. 예: ('01', 'Ch.01~02')
    """
    week, chapter = '01', 'Ch.01~02'
    try:
        with open('CLAUDE.md', encoding='utf-8') as f:
            for line in f:
                if line.startswith('CURRENT_WEEK='):
                    week = line.split('=', 1)[1].strip()
                elif line.startswith('CURRENT_CHAPTER='):
                    chapter = line.split('=', 1)[1].strip()
    except FileNotFoundError:
        pass
    return week, chapter


def make_header(filename: str, author: str, week: str, chapter: str,
                date: str, is_python: bool) -> str:
    """파일 상단에 삽입할 헤더 주석 블록을 생성한다.

    [Week 01 | @shiho2v]
    팀 표준 주석 양식 (WEEK_01.md 실습 포인트 기반).
    Python은 # 스타일, JS/TS는 // 스타일로 분기.

    Args:
        filename: 파일명 (경로 제외)
        author: Git user.name
        week: 현재 주차 번호 문자열
        chapter: 현재 챕터 문자열
        date: 생성일 (YYYY-MM-DD)
        is_python: True면 Python 헤더, False면 JS/TS 헤더

    Returns:
        헤더 주석 문자열 (개행 포함)
    """
    sep = '#' if is_python else '//'
    return (
        f"{sep} =============================================================\n"
        f"{sep} File   : {filename}\n"
        f"{sep} Author : @{author}\n"
        f"{sep} Week   : {week} | {chapter}\n"
        f"{sep} Created: {date}\n"
        f"{sep} =============================================================\n"
    )


# ── 메인 ──────────────────────────────────────────────────────
hook_input = {}
try:
    hook_input = json.loads(sys.stdin.read() or '{}')
except Exception:
    sys.exit(0)

if hook_input.get('tool_name') != 'Write':
    sys.exit(0)

file_path = hook_input.get('tool_input', {}).get('file_path', '')
if not file_path:
    sys.exit(0)

ext = Path(file_path).suffix.lower()
if ext not in SUPPORTED:
    sys.exit(0)

try:
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
except Exception:
    sys.exit(0)

# 헤더가 이미 있으면 스킵
if PY_MARKER in content[:300] or JS_MARKER in content[:300]:
    sys.exit(0)

author = get_git_user()
week, chapter = get_week_info()
date = datetime.now().strftime('%Y-%m-%d')
filename = os.path.basename(file_path)
is_python = ext == '.py'

header = make_header(filename, author, week, chapter, date, is_python)

# shebang(#!) 다음 줄에 삽입
if content.startswith('#!'):
    first, rest = content.split('\n', 1)
    new_content = first + '\n' + header + rest
else:
    new_content = header + content

try:
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print(f'[auto_header] ✓ 헤더 추가: {filename} (Week {week} | @{author})')
except Exception as e:
    print(f'[auto_header] 오류: {e}', file=sys.stderr)

sys.exit(0)
