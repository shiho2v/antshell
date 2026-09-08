# entry-points.md — 진입점 (트리거 유형별)

수집일: 2026-09-06 | 근거: `structure.md` §3(명령 목록 재사용) + `.claude/settings.json`, `.claude/hooks/*.py`, `.claude/skills/*/SKILL.md` 직접 확인

> `structure.md` §3이 진입점을 **디렉터리별**로 나열했다면, 이 문서는 같은 명령들을 **어떻게 실행이 시작되는가(트리거 유형)** 기준으로 재구성한다. 다섯 가지 트리거 유형: 수동 CLI 실행 / npm 스크립트 / 개발 서버 / Claude Code 스킬 호출 / 라이프사이클 훅 자동 트리거.

## 1. 수동 CLI 실행 — 사용자가 터미널에서 직접 실행

| 명령 | 소유 모듈 | 비고 |
|---|---|---|
| `python scripts/orchestrate_portfolio.py --portfolio data/portfolio.example.json [--save]` | `scripts/` | [B] 파이프라인. `--save` 시 `outputs/portfolio_report_{date}.html` 생성 |
| `python scripts/orchestrate_stock_agents.py <ticker> [--save]` | `scripts/` | [B] 파이프라인. `--save` 시 `data/{ticker}_agents.json` 생성 |
| `python .claude/skills/generating-krx-report/scripts/resolve_security.py {TICKER}` (외 12개 스크립트) | `generating-krx-report` | [A] 파이프라인 7단계 워크플로의 개별 스크립트. 전체 목록은 `modules.md` §6, 실행 순서는 `data-flow.md` §1 |
| `python .claude/skills/generating-krx-report/tests/test_units.py` | `generating-krx-report` | unittest, 네트워크 없음 |
| `pytest .claude/skills/converting-investment-blog/tests/ -q` | `converting-investment-blog` | pytest |

## 2. npm 스크립트 — `frontend/package.json`의 `scripts` 필드로 정의

| 명령 | 소유 모듈 | 비고 |
|---|---|---|
| `npm run build` | `frontend/` | Next.js 프로덕션 빌드 |
| `npm run start` | `frontend/` | 빌드된 앱 실행 |
| `npm run lint` | `frontend/` | `eslint-config-next` 기본값(커밋된 설정 파일 없음) |

## 3. 개발 서버 — 로컬 실행 커맨드 (빌드 산출물 없이 즉시 구동)

| 명령 | 포트 | 소유 모듈 |
|---|---|---|
| `cd backend && uvicorn app.main:app --reload` | 8000 | `backend/app/` |
| `cd frontend && npm run dev` | 3000 | `frontend/src/app/` |

## 4. Claude Code 스킬 호출 — 트리거 문구로 발동 (사용자가 슬래시 명령이 아닌 자연어로 시작)

| 스킬 | 발동 문구 예시 | 산출 |
|---|---|---|
| `generating-krx-report` | "삼성전기 종합 분석해줘", "009150 CANSLIM 채점" | `outputs/{TICKER}_report_{as_of}.html` |
| `company-blog-pipeline` | "블로그 글 써줘", "티스토리에 올릴 글" | `docs/blog/*.md` (오케스트레이터, 내부적으로 `converting-investment-blog` + 2개 에이전트 + `saving-tistory-draft`를 순차/병렬 호출) |
| `converting-investment-blog` | "보고서를 블로그 문체로 바꿔줘" (또는 `company-blog-pipeline`이 내부 위임) | 블로그 초안 Markdown (미저장 상태) |
| `saving-tistory-draft` | "초안 저장해줘" | `docs/blog/{YYYY-MM-DD}_{ticker}_{회사명}.md` 로컬 저장 |
| `add-comments` | "주석 달아줘", "@파일명 주석" | 대상 코드 파일에 주석 삽입(다른 4개 스킬과 데이터 비공유, 완전 독립) |

이 다섯 스킬은 슬래시 명령이 아니라 **자연어 의도 매칭**으로 진입한다는 점에서 §1~3의 명시적 명령 실행과 트리거 성격이 다르다 — 사용자가 정확한 명령어를 몰라도 자연어 요청만으로 진입 가능하다.

## 5. 라이프사이클 훅 자동 트리거 — Claude Code 이벤트에 반응해 자동 실행 (사용자가 직접 호출하지 않음)

`.claude/settings.json`의 `hooks` 블록에 등록된 4개 훅. **수동 실행 명령이 아니라, 특정 도구 사용/세션 이벤트가 발생하면 Claude Code 런타임이 자동으로 실행한다.**

| 훅 파일 | 이벤트 타입 | 매처(matcher) | 트리거 조건 |
|---|---|---|---|
| `auto_header.py` | PostToolUse | `Write` | `.py/.ts/.tsx/.js/.jsx` 확장자 파일이 새로 작성될 때 |
| `commit_format.py` | PreToolUse | `Bash` | `git commit -m "..."` 형태의 명령이 실행되기 **직전** |
| `notion_sync.py` | PostToolUse | `Bash` | `git commit` 명령이 실행된 **직후**(커밋 감지 시) |
| `log_session_end.py` | SessionEnd | (세션 종료 이벤트 전체) | Claude Code 세션이 종료될 때 |

이 4개는 사용자가 "실행"이라는 행위를 의식하지 않는 진입점이라는 점에서 §1~4와 근본적으로 다르다 — 다른 목적의 작업(파일 저장, 커밋)을 하는 동안 부수적으로 트리거된다. `commit_format.py`와 `notion_sync.py`는 **같은 Bash 명령(`git commit`)에 대해 Pre/Post 양쪽에서 각각 독립적으로 반응**하는 유일한 쌍이다 — 하나는 커밋 전 형식 검사(차단 가능), 하나는 커밋 후 부수 기록(Notion 동기화)이라는 서로 다른 역할을 진다.
