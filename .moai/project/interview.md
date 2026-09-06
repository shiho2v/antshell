# 프로젝트 인터뷰

수집일: 2026-09-06
대상: `/home/jsbaac/STUDY/antshell` (돌아온 불타는 개미지옥)
프로젝트 타입: 기존 프로젝트 (Phase 1 탐지 → 사용자 확정)

---

## Stage A Round 1: 소유·목적·목표

Question: 이 프로젝트를 지금 어떤 상태로 보고 계시나요? / PRD 에 없는 종목 분석 파이프라인을 문서에서 어떻게 다룰까요?
Answer: 진행 중인 스터디 프로젝트 / 웹앱과 분석 파이프라인 둘 다 주역 취급

Domain: stock-analysis-study (코드베이스 분석에서 자동 추론 후 사용자 확정)
Goal: "클로드 코드로 시작하는 실전 에이전틱 코딩" 12주 스터디(현재 8주차, Ch.08 MoAI-ADK)를 진행하면서, 국내 주식 분석 웹앱과 KRX 종목 분석 리포트 파이프라인을 9명이 함께 완성한다.

보충 맥락:
- `PRD.md` / `README.md` 가 선언한 웹앱(Next.js 14 + FastAPI + Supabase)과, 선언에 없던 로컬 분석 파이프라인(`scripts/`, `data/`, `outputs/`, 도메인 스킬 5종 + 금융 에이전트 7종)이 **동등한 구성요소**로 문서화된다.
- 문서는 현재 구현 상태와 남은 주차 로드맵을 함께 담는다.

---

## Stage A Round 2: 제약과 비목표

Question: 지금 이 프로젝트가 지켜야 하는 제약 중 가장 무거운 건 무엇인가요?
Answer: PRD 의 세 제약 그대로

Constraints:
1. **유료 클라우드 서비스 최소화** — 무료/저비용 티어 안에서 해결한다.
2. **Git 초보자 포함** — 자동화로 진입 장벽을 낮춘다. 브랜치·커밋 규칙은 `_claude_core/GIT_RULES.md` 로 고정.
3. **Claude Code 토큰 절약** — 파일 분리·선택적 로드 설계. `CLAUDE.md` 상단의 토큰 절약 규칙과 `_claude_core/` 분리 구조가 이 제약의 구현체.

전제: 팀원 전원 Claude Pro 요금제 (사용량 한도 고려 필수).

---

## Stage A Round 3: 범위·경계·문서 우선순위

Question: 문서가 가장 정확하게 담아야 할 측면은? / 범위 경계를 어디까지로 잡을까요?
Answer: 아키텍처와 모듈 경계 / 저장소 전체 — 생성 산출물 제외

문서 우선순위: **아키텍처와 모듈 경계**. `backend` / `frontend` / `scripts` / `data` / `outputs` / `.claude` 가 서로 어떻게 맞물리는지를 가장 정확하게 기술한다. 9명이 같은 저장소를 건드리므로 경계가 가장 자주 부딪힌다.

Scope:
- **IN**: `backend/`, `frontend/`, `scripts/`, `.claude/` 하네스(스킬·에이전트·훅·룰), `docs/` (주차 운영 문서 포함), 루트 설정 파일(`.env.example`, `.mcp.json`, `portfolio-team.yaml`, `CLAUDE.md`, `DEV_PRINCIPLES.md`, `PRD.md`)
- **OUT**: `data/*.json` 과 `outputs/*.html` 의 **개별 내용** (스키마와 생성 규칙만 기술), `docs/blog/` 의 개별 게시글, 외부 API 자체 명세

근거: 생성 산출물은 계속 늘어나므로 개별 기술 시 문서가 금방 상하게 된다.

---

## Stage B Round 4: 검증·표면·연동·공유

Verification: **수동 확인 위주**. 자동 테스트 스위트 없음.
- 근거: `frontend/package.json` 의 scripts 에 `test` 없음 (`dev` / `build` / `start` / `lint` 만 존재), `backend/requirements.txt` 에 pytest 계열 없음 (fastapi, uvicorn, python-jose, httpx, python-dotenv 5종).
- 사용 가능한 유일한 정적 검사: `npm run lint` (eslint-config-next 14.2.5).

UI surface: **has-ui (웹)**
- 근거: `frontend/` 에 Next.js 14.2.5 + React 18 + TailwindCSS 3.4, `next.config.js` / `tailwind.config.js` / `tsconfig.json` / `src/` 구성. 추가로 `outputs/*.html` 리포트가 브라우저로 열리는 두 번째 표면.

External systems: **DART · KRX/시세 · Anthropic (LLM)**
- 사용자가 실제 호출 경로로 확정한 3종.
- `.env.example` 에는 이 외에 Supabase, KIS, BigKinds, Notion, GitHub, Redis 자격증명이 선언돼 있으나 **선언과 실제 호출은 별개** — 문서에서는 "선언됨 / 사용 확인됨"을 구분해 기술한다.

Team sharing: **team-shared (9명)**
- 근거: `PRD.md` §1 팀 구성 9명(스터디장 포함), `README.md` 헤더, 최근 커밋의 `shiho2v/antshell` 저장소 PR 머지 이력(#12, #13).
- 문서에 브랜치 규칙(`feature/<주차>-<이름>-<기능명>`)과 온보딩 경로를 강조해 넣는다.

---

## 인터뷰 진행 기록

| 단계 | 라운드 | 종료 사유 |
|---|---|---|
| Stage A | 3 / 3 | `project.max_rounds` 도달 (네 기본 필드 모두 수집 완료) |
| Stage B | 1 (필수) | 네 축 모두 수집 완료 |

미수집 필드: 없음.
