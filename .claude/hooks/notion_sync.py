#!/usr/bin/env python3
# =============================================================
# File   : notion_sync.py
# Author : @shiho2v
# Week   : 06 | Ch.07 (1/2)
# Created: 2025-07-05
# =============================================================
"""PostToolUse 훅: git commit 감지 시 Notion 변경 로그 페이지에 자동 기록."""
import json, os, sys, subprocess, urllib.request, urllib.error
from datetime import datetime
from pathlib import Path

MAX_FILES = int(os.environ.get("NOTION_SYNC_MAX_FILES", "10"))
LOG_PATH = Path(__file__).parent / "notion_sync.log"


def get_env(key: str) -> str:
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


def get_current_week() -> str:
    try:
        with open("CLAUDE.md", encoding="utf-8") as f:
            for line in f:
                if line.startswith("CURRENT_WEEK="):
                    return line.split("=", 1)[1].strip()
    except FileNotFoundError:
        pass
    return "??"


def get_current_branch() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"], encoding="utf-8"
        ).strip()
    except Exception:
        return "unknown"


def get_last_commit_info() -> tuple[str | None, str | None, str | None, list[str]]:
    try:
        msg = subprocess.check_output(
            ["git", "log", "-1", "--pretty=%s"], encoding="utf-8").strip()
        author = subprocess.check_output(
            ["git", "log", "-1", "--pretty=%an"], encoding="utf-8").strip()
        sha = subprocess.check_output(
            ["git", "log", "-1", "--pretty=%h"], encoding="utf-8").strip()
        files_raw = subprocess.check_output(
            ["git", "diff", "HEAD~1", "--name-only"], encoding="utf-8").strip()
        files = files_raw.split("\n") if files_raw else []
        return msg, author, sha, files
    except Exception:
        return None, None, None, []


def write_fallback_log(entry: str) -> None:
    try:
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(entry + "\n")
    except Exception:
        pass


def build_notion_blocks(msg: str, author: str, sha: str,
                        branch: str, week: str, files: list[str]) -> list[dict]:
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    truncated = files[:MAX_FILES]
    more = len(files) - MAX_FILES if len(files) > MAX_FILES else 0

    # 요약 한 줄
    summary = f"[Week {week}] {now}  •  {author}  •  {branch}  •  {sha}"

    file_items = [
        {
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {
                "rich_text": [{"type": "text", "text": {"content": f}}]
            }
        }
        for f in truncated
    ]
    if more:
        file_items.append({
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {
                "rich_text": [{"type": "text", "text": {"content": f"… 외 {more}개"}}]
            }
        })

    callout = {
        "object": "block",
        "type": "callout",
        "callout": {
            "icon": {"type": "emoji", "emoji": "📝"},
            "rich_text": [
                {"type": "text", "text": {"content": summary + "\n"}, "annotations": {"bold": True}},
                {"type": "text", "text": {"content": msg}}
            ],
            "children": file_items if file_items else []
        }
    }
    return [callout]


def append_to_notion(api_key: str, page_id: str, blocks: list[dict]) -> None:
    payload = json.dumps({"children": blocks}).encode()
    req = urllib.request.Request(
        f"https://api.notion.com/v1/blocks/{page_id}/children",
        data=payload,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28",
        },
        method="PATCH",
    )
    urllib.request.urlopen(req, timeout=5)


# ── 메인 ──────────────────────────────────────────────────────
hook_input = {}
try:
    hook_input = json.loads(sys.stdin.read() or "{}")
except Exception:
    pass

cmd = hook_input.get("tool_input", {}).get("command", "")
if "git commit" not in cmd:
    sys.exit(0)

api_key = get_env("NOTION_API_KEY")
page_id = get_env("NOTION_CHANGELOG_PAGE_ID")
if not api_key or not page_id:
    sys.exit(0)

msg, author, sha, files = get_last_commit_info()
if not msg:
    sys.exit(0)

branch = get_current_branch()
week = get_current_week()
blocks = build_notion_blocks(msg, author, sha, branch, week, files)

log_entry = f"[{datetime.now().strftime('%Y-%m-%d %H:%M')}] Week{week} | {branch} | {sha} | {author}: {msg}"

try:
    append_to_notion(api_key, page_id, blocks)
    print(f"[notion_sync] OK Notion 기록 완료 (Week {week} | {branch} | {sha})")
except Exception as e:
    print(f"[notion_sync] Notion 기록 실패 → 로컬 로그 저장: {e}", file=sys.stderr)
    write_fallback_log(log_entry)
