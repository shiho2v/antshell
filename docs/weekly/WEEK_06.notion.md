# 📚 6주차 | Ch.07 (1/2) | 양재호

> **날짜:** 2025-08-10 | **챕터:** Ch.07 비대화형 자동화 · 훅 시스템 | **PR:** https://github.com/shiho2v/antshell/pull/11

---

## 0. 기본 용어

| 용어 | 설명 |
| --- | --- |
| **훅(Hook)** | Claude Code가 특정 이벤트 발생 시 자동으로 실행하는 외부 스크립트 |
| **PreToolUse** | 도구 실행 **전** 에 트리거되는 훅. 검사·차단·경고에 활용 |
| **PostToolUse** | 도구 실행 **후** 에 트리거되는 훅. 기록·알림·후처리에 활용 |
| **matcher** | 훅이 반응할 도구 이름 (예: `Bash`, `Write`, `Edit`) |
| **비대화형 자동화** | 사람의 입력 없이 Claude Code가 훅·스크립트로 반복 작업을 수행하는 패턴 |

---

## 1. 핵심 개념

> 💡 **한 줄**: 훅은 Claude Code의 '행동 감시자' — 도구 호출 전후에 끼어들어 팀 규칙을 자동으로 강제한다.

| 구분 | 무엇 | 핵심 |
| --- | --- | --- |
| **훅 등록** | `settings.json` → `hooks` 블록 | matcher로 대상 도구 지정, command로 스크립트 실행 |
| **PreToolUse** | 실행 전 개입 | stdin으로 tool_input 수신 → 경고·차단 가능 |
| **PostToolUse** | 실행 후 개입 | 결과를 읽어 후속 작업(Notion 기록, 로그 등) 수행 |

> ⚙️ **훅과 에이전트의 차이** — 에이전트는 '무엇을 할지' 결정하는 주체, 훅은 결정된 행동에 **자동으로 붙는 규칙**. 코드 리뷰어가 PR마다 체크리스트를 확인하는 것과 같다.

---

## 2. 주식 웹 적용 — 훅 시스템 고도화

기존 1주차에서 기초를 잡은 훅 3종을 Ch.07 개념을 적용해 실질적으로 개선.

### commit_format.py 개선

| 항목 | 전 | 후 |
| --- | --- | --- |
| 패턴 | `feat: 설명` 만 허용 | `feat(scope): 설명` scope 포함 형식도 허용 |
| 경고 메시지 | 형식 안내만 출력 | 현재 메시지 분석해 **수정 예시 자동 제안** |
| Co-Authored-By | 미검사 | 누락 시 경고 + 올바른 형식 안내 |

```python
# scope 포함 패턴 강화
PATTERN = re.compile(r'^(' + '|'.join(TYPES) + r')(\([^)]+\))?: .+')
```

### notion_sync.py 고도화

| 항목 | 전 | 후 |
| --- | --- | --- |
| Notion 블록 | paragraph 1개 | **callout** (요약 + 커밋메시지 + 파일 목록) |
| 기록 정보 | 시간·작성자·메시지·파일 | + **브랜치명·커밋 SHA·주차** 추가 |
| 변경 파일 수 | 하드코딩 8개 | `NOTION_SYNC_MAX_FILES` 환경변수로 조정 가능 (기본 10) |
| 실패 처리 | 조용히 무시 | `.claude/hooks/notion_sync.log` fallback 로그 저장 |

**Notion에 기록되는 callout 예시**

```
📝  [Week 06] 2025-08-10 14:32  •  양재호  •  feature/06-양재호-hooks  •  61f0104
   feat(hooks): 커밋 자동 주석·Notion 동기화 훅 고도화
   • .claude/hooks/commit_format.py
   • .claude/hooks/notion_sync.py
```

---

## 3. 훅 설정 구조 (`settings.json`)

```json
{
  "hooks": {
    "PreToolUse": [
      { "matcher": "Bash", "hooks": [{ "type": "command", "command": "python commit_format.py" }] }
    ],
    "PostToolUse": [
      { "matcher": "Bash",  "hooks": [{ "type": "command", "command": "python notion_sync.py" }] },
      { "matcher": "Write", "hooks": [{ "type": "command", "command": "python auto_header.py" }] }
    ]
  }
}
```

> 📌 **포인트**: matcher를 `"*"`로 설정하면 모든 도구에 반응. 범위를 좁혀야 불필요한 훅 실행을 막을 수 있다.

---

## 4. 회고

- PreToolUse 훅은 경고만 출력하고 커밋을 막지 않는 게 맞다 — 강제 차단은 작업 흐름을 끊는다.
- Notion callout 블록으로 바꾸니 변경 로그 페이지 가독성이 크게 올라갔다.
- fallback 로그 덕분에 Notion API 장애 시에도 기록이 남아 안심하고 쓸 수 있다.
- 한계: 현재 훅은 Claude Code 내 커밋에만 반응 → 터미널 직접 커밋은 감지 못함.

> 📎 **다음 주 예고** — 발표자: **G** | 챕터: Ch.07 (2/2)
