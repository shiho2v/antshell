#!/usr/bin/env python3
"""
Claude Code SessionEnd 훅 스크립트

세션이 종료될 때마다 session_id, 작업 제목(첫 user 메시지), 종료 사유 등을
프로젝트 루트의 sessions/ 폴더 아래 JSON 파일 하나에 최신 N개까지만 누적 저장한다.

파일명은 "마지막 갱신 날짜" 기준으로 갱신되며, 날짜가 바뀌면 새 파일로 교체되고
이전 날짜 파일은 삭제된다.
"""

import json
import os
import sys
import urllib.request
import urllib.error
from datetime import datetime
from pathlib import Path

# ===== 설정 =====
SAVE_SUBDIR = "sessions"       # 프로젝트 루트 기준 하위 폴더명
MAX_ENTRIES = 10               # 최대 보관 세션 개수
FILE_PREFIX = "sessions_"      # 파일명 접두사
TITLE_MAX_LEN = 50             # 제목 최대 길이
GITHUB_REPO = "shiho2v/antshell"
GITHUB_ISSUE_LABEL = "session-log"
# =================


def get_env(key: str) -> str:
    val = os.environ.get(key, "")
    if not val:
        try:
            env_path = get_project_dir() / ".env"
            with open(env_path, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith(key + "=") and not line.startswith("#"):
                        val = line.split("=", 1)[1].strip().strip('"').strip("'")
                        break
        except (FileNotFoundError, OSError):
            pass
    return val


def create_github_issue(record: dict) -> None:
    token = get_env("GITHUB_TOKEN")
    if not token or token.startswith("ghp_xxx"):
        return

    title = f"[세션 완료] {record['title']}"
    body = (
        f"**session_id:** `{record['session_id']}`\n"
        f"**종료 사유:** {record['reason']}\n"
        f"**작업 디렉토리:** `{record['cwd']}`\n"
        f"**종료 시각:** {record['ended_at']}\n"
    )
    payload = json.dumps({
        "title": title,
        "body": body,
        "labels": [GITHUB_ISSUE_LABEL],
    }).encode()
    req = urllib.request.Request(
        f"https://api.github.com/repos/{GITHUB_REPO}/issues",
        data=payload,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        urllib.request.urlopen(req, timeout=5)
    except urllib.error.HTTPError:
        pass


def get_project_dir() -> Path:
    """CLAUDE_PROJECT_DIR 환경변수를 기준으로 프로젝트 루트 경로를 반환한다."""
    return Path(os.environ.get("CLAUDE_PROJECT_DIR", "."))


def read_hook_input() -> dict:
    """stdin으로 전달된 훅 JSON 페이로드를 읽는다."""
    if hasattr(sys.stdin, "reconfigure"):
        sys.stdin.reconfigure(encoding="utf-8")
    raw = sys.stdin.read()
    return json.loads(raw) if raw.strip() else {}


def extract_title(transcript_path: str, max_len: int = TITLE_MAX_LEN) -> str:
    """transcript(jsonl) 파일에서 첫 번째 user 메시지를 뽑아 작업 제목으로 사용한다."""
    if not transcript_path:
        return "(제목 없음)"

    try:
        with open(transcript_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                entry = json.loads(line)
                if entry.get("type") != "user":
                    continue

                content = entry.get("message", {}).get("content", "")
                if isinstance(content, list):
                    content = next(
                        (c.get("text", "") for c in content if c.get("type") == "text"),
                        "",
                    )
                title = content.strip().replace("\n", " ")
                return title[:max_len] if title else "(제목 없음)"
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        pass

    return "(제목 추출 실패)"


def build_record(hook_input: dict) -> dict:
    """훅 입력값으로부터 저장할 레코드를 구성한다."""
    return {
        "session_id": hook_input.get("session_id", "unknown"),
        "title": extract_title(hook_input.get("transcript_path", "")),
        "cwd": hook_input.get("cwd", ""),
        "reason": hook_input.get("reason", "unknown"),
        "ended_at": datetime.now().isoformat(),
    }


def find_latest_session_file(save_dir: Path) -> Path | None:
    """save_dir 안에서 가장 최근 sessions_*.json 파일을 찾는다."""
    files = sorted(save_dir.glob(f"{FILE_PREFIX}*.json"))
    return files[-1] if files else None


def load_existing_records(file_path: Path | None) -> list[dict]:
    """기존 세션 로그 파일을 읽어온다. 없거나 손상됐으면 빈 리스트를 반환한다."""
    if file_path is None:
        return []
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return []


def save_records(save_dir: Path, records: list[dict], today: datetime) -> Path:
    """레코드 리스트를 오늘 날짜 파일명으로 저장하고 저장된 경로를 반환한다."""
    save_dir.mkdir(parents=True, exist_ok=True)
    new_file = save_dir / f"{FILE_PREFIX}{today.strftime('%Y%m%d')}.json"
    with open(new_file, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)
    return new_file


def cleanup_old_file(old_file: Path | None, new_file: Path) -> None:
    """날짜가 바뀌어 새 파일이 만들어졌다면 이전 파일을 삭제한다."""
    if old_file and old_file != new_file and old_file.exists():
        old_file.unlink()


def main() -> None:
    hook_input = read_hook_input()
    record = build_record(hook_input)

    save_dir = get_project_dir() / SAVE_SUBDIR
    old_file = find_latest_session_file(save_dir)
    records = load_existing_records(old_file)

    records.append(record)
    records = records[-MAX_ENTRIES:]

    new_file = save_records(save_dir, records, datetime.now())
    cleanup_old_file(old_file, new_file)

    create_github_issue(record)

    sys.exit(0)


if __name__ == "__main__":
    main()
