# dependencies.md — 의존성 그래프

수집일: 2026-09-06 | 근거: `tech.md`(패키지 사용/미사용 판정 재사용), `portfolio-team.yaml`, 소스 직접 확인

> 패키지의 사용/미사용 여부 자체는 `tech.md`가 이미 확정했으므로 여기서는 재검증하지 않고, 그 결과를 **의존성 그래프의 간선(edge)** 형태로 재구성한다. 이 문서의 새 기여는 §3(내부 모듈 관계)과 §4(외부 API 소유 매핑)이다.

## 1. 백엔드 의존성 그래프 (`backend/requirements.txt`)

| 패키지 | 버전 | 사용처(간선) | 상태 |
|---|---|---|---|
| fastapi | 0.111.0 | `backend/app/main.py` → 앱 정의·라우트 데코레이터 | 사용 |
| uvicorn[standard] | 0.30.1 | 실행 명령(`uvicorn app.main:app`) | 사용 |
| httpx | 0.27.0 | `backend/app/auth.py` → Supabase `/auth/v1/user` 호출 | 사용(단, `auth.py` 자체가 미배선 — §3 참고) |
| python-jose[cryptography] | 3.3.0 | 없음 | **미사용** |
| python-dotenv | 1.0.1 | 없음(대신 `main.py`가 `.env`를 손으로 파싱) | **미사용** |

## 2. 프런트엔드 의존성 그래프 (`frontend/package.json`)

| 패키지 | 버전 | 사용처(간선) | 상태 |
|---|---|---|---|
| next | 14.2.5 | `frontend/src/app/**` App Router 전체 | 사용 |
| react / react-dom | ^18 | 모든 페이지 컴포넌트 | 사용 |
| typescript | ^5 | 전체 `.tsx`/`.ts` | 사용 |
| tailwindcss | ^3.4.1 | 전 페이지의 유틸리티 클래스(`className="..."`) | 사용(테마 미설정) |
| @supabase/ssr | ^0.5.1 | `frontend/src/lib/supabase.ts` → `createBrowserClient` | 사용 |
| @supabase/supabase-js | ^2.45.0 | `dashboard/page.tsx`의 `User` 타입 임포트만 | 사용(타입 전용) |
| zustand | ^4.5.4 | 없음 — 모든 페이지가 `useState`로 로컬 상태만 관리 | **미사용** |

## 3. 내부 모듈 관계 (누가 누구를 호출하는가)

```
backend/app/main.py
    ├─(HTTP 프록시)→ Notion API
    └─(HTTP 프록시)→ GitHub REST API
    ✕ data/ 를 호출하지 않음
    ✕ outputs/ 를 호출하지 않음
    ✕ scripts/ 를 호출하지 않음
    ✕ .claude/skills/ 를 호출하지 않음

frontend/src/app/dashboard/page.tsx
    ├─(fetch)→ backend/app/main.py  GET /api/github/issues
    ├─(fetch)→ backend/app/main.py  POST /api/report/notion
    └─(직접 호출, 백엔드 미경유)→ Supabase Auth (getUser/signOut)

frontend/src/app/{login,signup}/page.tsx
    └─(직접 호출, 백엔드 미경유)→ Supabase Auth (signInWithPassword/signUp)

scripts/orchestrate_stock_agents.py
    └─(subprocess: claude -p)→ .claude/agents/{news-collector, financial-data}.md
        읽기: 웹 조회만 (data/ 미참조)
        쓰기(옵션): data/{ticker}_agents.json

scripts/orchestrate_portfolio.py
    └─(subprocess: claude -p)→ .claude/agents/{portfolio-valuation, portfolio-risk, portfolio-allocation}.md
        읽기: data/{code}_fundamentals.json, data/{code}_market.json (에이전트별 화이트리스트 분리)
        쓰기(옵션): outputs/portfolio_report_*.html (리더만 — portfolio-team.yaml ownership_rules)

.claude/skills/generating-krx-report (13개 스크립트)
    ├─(HTTP)→ DART Open API
    ├─(HTTP, pykrx 경유)→ KRX/Naver 시세
    └─(내부 파이프)→ data/*.json → outputs/{TICKER}_report_{as_of}.html

.claude/skills/company-blog-pipeline (오케스트레이터, Agent 도구 보유)
    ├─(호출)→ .claude/skills/converting-investment-blog
    ├─(Agent 병렬 호출)→ .claude/agents/financial-fact-checker.md
    ├─(Agent 병렬 호출)→ .claude/agents/investment-devils-advocate.md
    └─(호출)→ .claude/skills/saving-tistory-draft

.claude/skills/converting-investment-blog
    └─(읽기 전용, 화이트리스트)→ generating-krx-report의 manifest/claims/module-results/evidence(지목 ID)
    ✕ data/raw/, data/normalized/, 리포트 HTML 원문은 읽지 않음

.claude/hooks/notion_sync.py
    └─(git commit 감지 시, HTTP)→ Notion API

.claude/hooks/log_session_end.py
    └─(세션 종료 시, HTTP)→ GitHub REST API (이슈 등록)
```

**교차 파이프라인 호출은 존재하지 않는다.** `backend/app/main.py`는 [A]/[B]의 어떤 산출물도 참조하지 않고, `scripts/orchestrate_*.py`는 `backend/`나 `frontend/`를 호출하지 않으며, `generating-krx-report`는 `scripts/`나 `backend/`를 호출하지 않는다. 이는 `overview.md` §1의 "세 파이프라인 분리" 주장을 의존성 그래프 수준에서 뒷받침한다.

## 4. 외부 API 의존성 — 소유 모듈 매핑

| 외부 시스템 | 호출 지점(소유 모듈) | 용도 | 필요 환경변수 |
|---|---|---|---|
| DART Open API | `.claude/skills/generating-krx-report/scripts/fetch_dart_*.py` | 공시·재무 데이터 조회 | `DART_API_KEY` |
| KRX / pykrx (Naver 경유) | `.claude/skills/generating-krx-report/scripts/fetch_krx_market.py` | 시세 조회 | `KRX_ID`, `KRX_PW`(선택 — 없으면 CANSLIM L/I/M이 N/A) |
| Notion API | `backend/app/main.py`(`POST /api/report/notion`), `.claude/hooks/notion_sync.py` | 리포트 저장, 커밋 변경 로그 | `NOTION_API_KEY` + 페이지 ID 2개 |
| GitHub REST API | `backend/app/main.py`(`GET /api/github/issues`), `.claude/hooks/log_session_end.py` | 이슈 조회/생성 | `GITHUB_TOKEN` |
| Supabase Auth | `frontend/src/lib/supabase.ts`(브라우저 직접 호출), `backend/app/auth.py`(미배선) | 로그인/회원가입 | Supabase 프로젝트 키(`NEXT_PUBLIC_SUPABASE_URL`, `NEXT_PUBLIC_SUPABASE_ANON_KEY`) |
| Anthropic / Claude (CLI 세션) | `scripts/orchestrate_portfolio.py`, `scripts/orchestrate_stock_agents.py` (둘 다 `subprocess.run([shutil.which("claude"), "-p", ...])`) | 에이전트 오케스트레이션 | 없음 — 사용자의 로컬 `claude` CLI/Pro 세션 사용, `ANTHROPIC_API_KEY` 미사용 |

**소유 규칙**: 하나의 외부 API를 두 개 이상의 모듈이 호출하는 경우(Notion·GitHub)는 각각 서로 다른 트리거(HTTP 요청 vs. 훅 이벤트)에서 독립적으로 호출하며, 호출 로직을 공유하지 않는다(`backend/app/main.py`의 `_get_env`와 `.claude/hooks/notion_sync.py`의 `get_env`는 각각 별도로 `.env`를 파싱하는 중복 구현이다 — `tech.md` §3의 "손으로 작성한 `.env` 파서 3곳 중복" 서술과 일치).
