#!/usr/bin/env python3
# =============================================================
# File   : notion_sync.py
# Author : @shiho2v
# Week   : 01 | Ch.01~02
# Created: 2025-07-05
# =============================================================
"""PostToolUse 훅: git commit 감지 시 Notion 변경 로그 페이지에 자동 기록."""
import json, os, sys, subprocess, urllib.request
from datetime import datetime


def get_env(key: str) -> str:
    """환경변수 또는 .env 파일에서 설정값을 읽는다.

    [Week 01 | @shiho2v]
    Ch.02 설정관리 — settings.json의 env 블록 대신 .env 파일로 민감정보 분리.
    IAM 보안 유의사항: 자격증명은 코드에 하드코딩하지 않고 환경변수로 관리.

    Args:
        key: 읽을 환경변수 이름 (예: 'NOTION_API_KEY')

    Returns:
        환경변수 값. 없으면 빈 문자열.
    """
    val = os.environ.get(key, "")
    if not val:
        try:
            with open(".env", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith(key + "=") and not line.startswith("#"):
                        val = line.split("=", 1)[1].strip().strip('"').strip("'")
                        break
        except FileNotFoundError:
            pass
    return val


def get_last_commit_info() -> tuple[str | None, str | None, list[str]]:
    """가장 최근 커밋의 메시지·작성자·변경 파일 목록을 가져온다.

    [Week 01 | @shiho2v]
    Ch.01 깃 통합 — git log/diff 명령으로 변경 내역을 요약하는 역할.
    에이전틱 루프의 '컨텍스트 수집' 단계와 동일한 구조:
    필요한 정보(커밋 내역)를 수집해 다음 작업(Notion 기록)에 전달.

    Returns:
        (커밋메시지, 작성자, 변경파일리스트) 튜플.
        실패 시 (None, None, []).
    """
    try:
        msg = subprocess.check_output(
            ["git", "log", "-1", "--pretty=%s"], encoding="utf-8").strip()
        author = subprocess.check_output(
            ["git", "log", "-1", "--pretty=%an"], encoding="utf-8").strip()
        files = subprocess.check_output(
            ["git", "diff", "HEAD~1", "--name-only"], encoding="utf-8").strip()
        return msg, author, files.split("\n") if files else []
    except Exception:
        return None, None, []


def append_to_notion(api_key: str, page_id: str, msg: str,
                     author: str, files: list[str]) -> None:
    """Notion 변경 로그 페이지에 커밋 내역을 append한다.

    [Week 01 | @shiho2v]
    Ch.01 MCP 서버 / Ch.02 확장 도구 — urllib만 사용해 외부 라이브러리 없이
    Notion REST API를 직접 호출. 컨텍스트 윈도우 토큰 절약 원칙 적용.
    PostToolUse 훅으로 git commit 이후 자동 실행.

    Args:
        api_key: Notion Integration API 키
        page_id: 변경 로그 페이지 ID (NOTION_CHANGELOG_PAGE_ID)
        msg: 커밋 메시지
        author: 커밋 작성자명
        files: 변경된 파일 경로 목록

    Raises:
        urllib.error.URLError: API 호출 실패 시 (오류는 캐치 후 무시)
    """
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    file_list = "\n".join(f"  • {f}" for f in files[:8])
    text = f"[{now}] {author}: {msg}"
    if file_list:
        text += f"\n{file_list}"

    payload = json.dumps({
        "children": [{
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [{"type": "text", "text": {"content": text}}]
            }
        }]
    }).encode()

    req = urllib.request.Request(
        f"https://api.notion.com/v1/blocks/{page_id}/children",
        data=payload,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28"
        },
        method="PATCH"
    )
    try:
        urllib.request.urlopen(req, timeout=5)
        print("[notion_sync] ✓ Notion 기록 완료")
    except Exception as e:
        print(f"[notion_sync] 오류 (무시됨): {e}", file=sys.stderr)


# ── 메인 ──────────────────────────────────────────────────────
hook_input = {}
try:
    hook_input = json.loads(sys.stdin.read() or "{}")
except Exception:
    pass

tool_name = hook_input.get("tool_name", "")
tool_input = hook_input.get("tool_input", {})
cmd = tool_input.get("command", "")

if "git commit" in cmd:
    api_key = get_env("NOTION_API_KEY")
    page_id = get_env("NOTION_CHANGELOG_PAGE_ID")
    if api_key and page_id:
        msg, author, files = get_last_commit_info()
        if msg:
            append_to_notion(api_key, page_id, msg, author, files)
