#!/usr/bin/env python3
"""
PostToolUse 훅: git commit 감지 시 Notion 변경 로그 페이지에 자동 기록
토큰 절약: urllib만 사용 (외부 라이브러리 없음)
"""
import json, os, sys, subprocess, urllib.request
from datetime import datetime


def get_env(key):
    # .env 파일에서 직접 읽기 (python-dotenv 없이)
    val = os.environ.get(key, "")
    if not val:
        try:
            with open(".env") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith(key + "=") and not line.startswith("#"):
                        val = line.split("=", 1)[1].strip().strip('"').strip("'")
                        break
        except FileNotFoundError:
            pass
    return val


def get_last_commit_info():
    try:
        msg = subprocess.check_output(
            ["git", "log", "-1", "--pretty=%s"], text=True).strip()
        author = subprocess.check_output(
            ["git", "log", "-1", "--pretty=%an"], text=True).strip()
        files = subprocess.check_output(
            ["git", "diff", "HEAD~1", "--name-only"], text=True).strip()
        return msg, author, files.split("\n") if files else []
    except Exception:
        return None, None, []


def append_to_notion(api_key, page_id, msg, author, files):
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


# 메인
hook_input = {}
try:
    hook_input = json.loads(sys.stdin.read() or "{}")
except Exception:
    pass

tool_name = hook_input.get("tool_name", "")
tool_input = hook_input.get("tool_input", {})
cmd = tool_input.get("command", "")

# git commit 명령이 실행된 경우에만 동작
if "git commit" in cmd:
    api_key = get_env("NOTION_API_KEY")
    page_id = get_env("NOTION_CHANGELOG_PAGE_ID")
    if api_key and page_id:
        msg, author, files = get_last_commit_info()
        if msg:
            append_to_notion(api_key, page_id, msg, author, files)
