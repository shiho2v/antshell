# .claude/settings.json 설정 가이드

## 훅 (Hooks)

훅은 Claude Code 생애주기 이벤트에 바인딩되어 자동 실행되는 명령어다.

### PreToolUse — Bash

```json
"matcher": "Bash" → "command": "python3 .claude/hooks/commit_format.py"
```

- **실행 시점**: Claude Code가 `git commit` 명령을 실행하기 **직전**
- **하는 일**: 커밋 메시지가 Conventional Commits 형식(`feat:`, `fix:` 등)에 맞는지 검사
- **결과**: 형식이 틀리면 경고 출력. 커밋은 차단하지 않음

### PostToolUse — Bash

```json
"matcher": "Bash" → "command": "python3 .claude/hooks/notion_sync.py"
```

- **실행 시점**: Claude Code가 `git commit` 명령을 실행한 **직후**
- **하는 일**: 커밋 작성자·메시지·변경 파일 목록을 Notion 변경 로그 페이지에 자동 기록

### PostToolUse — Write

```json
"matcher": "Write" → "command": "python3 .claude/hooks/auto_header.py"
```

- **실행 시점**: Claude Code가 새 파일을 **Write(생성)한 직후**
- **하는 일**: `.py` `.ts` `.js` 파일에 `[Week XX | @author]` 헤더 주석 자동 삽입
- **스킵 조건**: 파일 상단에 헤더가 이미 있으면 삽입하지 않음

---

## ⚠️ 훅 실행 주의사항 — git commit 방법에 따라 동작이 달라진다

훅은 **Claude Code 세션 안에서 Bash 도구로 실행한 명령에만** 반응한다.

| git commit 방법 | 훅 실행 여부 | 이유 |
|----------------|-------------|------|
| Claude Code 세션에서 커밋 | ✅ 실행됨 | PostToolUse Bash 훅이 감지 |
| 터미널에서 직접 `git commit` | ❌ 실행 안 됨 | Claude Code 외부 명령이라 감지 불가 |
| VS Code Source Control GUI | ❌ 실행 안 됨 | Claude Code 외부 |
| GitHub Actions 자동 커밋 | ❌ 실행 안 됨 | 별도 서버 환경 |
| `git commit --amend` | ✅/❌ | Claude Code 세션 여부에 따라 다름 |

> **결론**: Notion 변경 로그 자동 기록을 원하면 반드시 **Claude Code 세션 안에서** 커밋할 것.
> 외부에서 커밋한 경우엔 `notion_sync.py`를 수동 실행하거나 백필 스크립트를 사용한다.

---

## MCP 서버

MCP(Model Context Protocol) 서버는 Claude가 외부 도구에 직접 접근할 수 있게 연결하는 설정이다.

### notion

```json
"command": "npx", "args": ["-y", "@notionhq/notion-mcp-server"]
```

- **역할**: Claude가 Notion 페이지를 직접 읽고 쓸 수 있게 연결
- **인증**: `.env`의 `NOTION_API_KEY` 사용
- **활용 예**: "Notion 1주차 페이지에 내용 정리해줘"

### github

```json
"command": "npx", "args": ["-y", "@modelcontextprotocol/server-github"]
```

- **역할**: Claude가 GitHub 이슈·PR·코드를 직접 조회할 수 있게 연결
- **인증**: `.env`의 `GITHUB_TOKEN` 사용
- **활용 예**: "PR #1 리뷰 코멘트 확인해줘"

> **주의**: MCP 서버는 `npx`로 실행되므로 Node.js가 설치되어 있어야 한다.
> `GITHUB_TOKEN`이 플레이스홀더(`ghp_xxxx`)면 github MCP 서버가 인증 실패한다.

---

## 환경변수 (env)

| 키 | 값 | 의미 |
|----|-----|------|
| `CLAUDE_COMPACT_THRESHOLD` | `0.7` | 컨텍스트 윈도우 70% 도달 시 자동 컴팩션. 기본값(98%)보다 일찍 압축해 토큰 낭비 방지 |
| `CLAUDE_SKIP_PERMISSIONS` | `false` | 도구 실행 전 권한 확인 프롬프트 유지. `true`로 바꾸면 모든 도구 자동 승인됨 (주의) |
