# modules.md — 모듈별 책임과 공개 인터페이스

수집일: 2026-09-06 | 근거: 소스 직접 확인(각 절에 파일 경로 명시)

> `structure.md` §2의 디렉터리 표를 전제로, 각 모듈의 **책임**과 **공개 인터페이스**(함수 시그니처 / CLI 인자 / JSON 스키마 / 라우트 시그니처)를 기술한다.

## 1. `backend/app/` — FastAPI 서비스

**책임**: [C] 웹앱 경계의 유일한 백엔드. `data/`·`outputs/`를 읽지 않으며 주식 데이터와 무관한 두 개의 프록시 기능만 제공한다.

| 파일 | 책임 |
|---|---|
| `main.py` (125줄) | FastAPI 앱 정의, CORS 미들웨어, 3개 라우트 |
| `auth.py` (31줄) | Supabase JWT 검증 의존성 — **어떤 라우트에서도 `Depends()`로 연결되지 않음(죽은 코드)** |

**공개 인터페이스 — 라우트**:

| 메서드/경로 | 요청 | 응답 | 비고 |
|---|---|---|---|
| `GET /health` | 없음 | `{"status": "ok"}` | 헬스체크 |
| `POST /api/report/notion` | `StockReportRequest{code, name, price, change}` (Pydantic `BaseModel`, 전부 `str`) | `{"ok": true, "message": str}` \| `HTTPException(503, "Notion 환경변수 미설정")` \| `HTTPException(502, "Notion API 오류: {code}")` | Notion 블록 API(`PATCH /v1/blocks/{page_id}/children`)로 프록시 |
| `GET /api/github/issues` | 없음 | `{"issues": [{number, title, user, url, created_at, labels}]}` | GitHub REST API(`/repos/shiho2v/antshell/issues`)로 프록시, PR 항목은 필터링 |

**공개 인터페이스 — 함수**: `_get_env(key: str) -> str` — 환경변수 우선, 없으면 `.env` 파일을 직접 파싱(3중 손수 구현 중 하나, `dependencies.md` §1 참고).

**인증 상태**: `auth.py`의 `get_current_user(credentials) -> dict`는 Supabase `/auth/v1/user` 엔드포인트로 토큰을 검증하는 완결된 함수이지만, `main.py`의 어떤 라우트도 `Depends(get_current_user)`를 사용하지 않는다. 결과적으로 3개 라우트 모두 무인증으로 열려 있다.

## 2. `frontend/src/app/` — Next.js 14 App Router 페이지

**책임**: [C] 웹앱의 UI. 대시보드는 목 데이터로 렌더링되며, 로그인/회원가입만 Supabase Auth와 실제로 통신한다.

| 페이지 | 파일 | 책임 | 상태 관리 |
|---|---|---|---|
| `layout.tsx` | 21줄 | 루트 레이아웃, `<html lang="ko">`, 다크 배경 전역 스타일, 메타데이터(`title`, `description`) | 없음(정적) |
| `dashboard/page.tsx` | 224줄 | 로그인 가드 + 목 데이터 렌더링 + GitHub 이슈 실조회 + Notion 저장 트리거 | `useState`(`user`, `savingCode`, `saveMsg`, `issues`, `issuesLoading`) — 전역 상태 라이브러리(zustand) 미사용, 컴포넌트 로컬 상태만 |
| `login/page.tsx` | 76줄 | Supabase `signInWithPassword` 로그인 폼 | `useState`(`email`, `password`, `error`, `loading`) |
| `signup/page.tsx` | 92줄 | Supabase `signUp` 회원가입 폼 + 이메일 인증 안내 화면 | `useState`(`email`, `password`, `error`, `done`, `loading`) |

**목-데이터 경계 (공개 인터페이스로서의 형태)**: `dashboard/page.tsx` 최상단에 하드코딩된 두 상수가 대시보드가 렌더링하는 주식 데이터의 전부다.

- `MOCK_STOCKS: {code, name, price, change, up}[]` — 4종목(005930/000660/009150/008490), 가격·등락률이 문자열 리터럴
- `MOCK_NEWS: {title, time}[]` — 3건 고정 문자열

**대시보드가 실제로 호출하는 것**:
- `GET {API}/api/github/issues` (컴포넌트 마운트 시 1회, `useEffect`) → `GithubIssue[]` 타입으로 파싱
- `POST {API}/api/report/notion` (사용자가 "Notion 저장" 버튼 클릭 시, `MOCK_STOCKS`의 한 종목 객체를 그대로 body로 전송)
- `supabase.auth.getUser()` / `supabase.auth.signOut()` — 브라우저에서 Supabase에 직접 호출, 백엔드 미경유

`API` 상수는 `process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000'`으로 정의된다.

## 3. `frontend/src/lib/` — Supabase 브라우저 클라이언트

**책임**: 로그인/회원가입/대시보드 페이지가 공유하는 Supabase 클라이언트 팩토리 1개 함수.

**공개 인터페이스**: `createClient(): SupabaseClient` (`supabase.ts`, `@supabase/ssr`의 `createBrowserClient` 래퍼) — `NEXT_PUBLIC_SUPABASE_URL`, `NEXT_PUBLIC_SUPABASE_ANON_KEY` 두 환경변수를 소비한다. 백엔드를 거치지 않는 직접 호출이므로, `backend/app/auth.py`가 검증하는 JWT와 이 클라이언트가 발급받는 세션은 같은 Supabase 프로젝트를 가리키지만 두 코드 경로가 실제로 연결되어 있지는 않다.

## 4. `scripts/` — 에이전트 팀 CLI 오케스트레이터 2종

**책임**: [B] 파이프라인. `claude -p` 헤드리스 서브프로세스를 통해 Claude Code 서브에이전트를 병렬 호출하고 결과를 병합해 JSON/HTML로 저장한다.

| 스크립트 | 줄수 | 공개 인터페이스(CLI) | 호출 대상 에이전트 |
|---|---|---|---|
| `orchestrate_stock_agents.py` | 84줄 | `python scripts/orchestrate_stock_agents.py <ticker> [--save]` | `news-collector`, `financial-data` (2종, 병렬) |
| `orchestrate_portfolio.py` | 240줄 | `python scripts/orchestrate_portfolio.py --portfolio <path> [--save]` | `portfolio-valuation`, `portfolio-risk`, `portfolio-allocation` (3종, 병렬) |

**공개 함수 시그니처** (두 스크립트 공통 패턴):
- `load_portfolio(path: Path) -> dict` (포트폴리오 스크립트 전용)
- `build_prompt(portfolio: dict) -> str` — 병렬 호출 지시문 + 서브에이전트별 입력 JSON을 하나의 프롬프트 문자열로 조립
- `run_orchestrator(prompt: str) -> dict` — `subprocess.run([claude_bin, "-p", "--output-format", "json", "--allowedTools", ...], input=prompt, ...)`로 호출하고, 응답 봉투(`envelope["result"]`)를 다시 JSON으로 파싱
- `render_html(merged: dict) -> str` (포트폴리오 스크립트 전용) — 병합된 JSON을 3개 표(밸류에이션/리스크/리밸런싱)를 가진 정적 HTML 문자열로 렌더링

두 스크립트 모두 `--allowedTools`로 서브에이전트가 실제로 선언한 도구만 명시적으로 허용해, 헤드리스 모드에서 미승인 도구가 자동 거부되게 한다(`orchestrate_stock_agents.py`: `WebSearch,WebFetch`; `orchestrate_portfolio.py`: `Read,Bash`).

## 5. `.claude/agents/` — 프로젝트 전용 에이전트 7종

**책임**: 각 에이전트가 정확히 하나의 데이터 조회/계산 역할을 맡고, JSON 스키마로만 응답한다(`overview.md` §2.2 패턴).

| 에이전트 | `tools:` | 읽기 범위 | 호출 상한 | 출력 스키마 핵심 필드 |
|---|---|---|---|---|
| `financial-data` | WebSearch, WebFetch, Bash | 웹 조회만 | 3회 | `{ticker, price, quarter, revenue, operatingIncome, per, pbr}` |
| `news-collector` | WebSearch, WebFetch | 웹 조회만 | 3회 | `{ticker, news: [{title, date, source, summary}]}` |
| `portfolio-valuation` | Read, Bash | `data/{code}_fundamentals.json`만 | — | `{results: [{stock_code, name, revenue_growth_pct, op_income_growth_pct, verdict, score, basis}]}` |
| `portfolio-risk` | Read, Bash | `data/{code}_market.json`만 | — | `{total_market_value, results: [{stock_code, ..., concentration, drawdown_from_52w, supply_flow, volume_state, risk_score, overall}]}` |
| `portfolio-allocation` | Read, Bash | `data/{code}_market.json`(시세만) | — | `{total_asset, cash, results: [{stock_code, ..., actual_weight_pct, target_weight_pct, drift_pct, action, rebalance_amount}]}` |
| `financial-fact-checker` | Read | manifest·claims·evidence·module-results(읽기 전용, 지목된 ID만) | — | `{agent, ticker, draft_path, findings: [{line, sentence, claim_id, verdict, expected, found, evidence_id, reason, severity}], summary}` |
| `investment-devils-advocate` | Read | manifest·module-results·evidence(읽기 전용, 지목된 ID만) | — | `{agent, ticker, draft_path, objections: [{line, target_claim_id, target_sentence, type, objection, evidence_ids, required_action}]}` |

**판정 값 도메인** (열거형 필드, `portfolio-team.yaml`의 `produces.values`와 일치):
- `portfolio-valuation.verdict`: `저평가 | 적정 | 주의 | 고평가 | unknown`
- `portfolio-risk.overall`: `low | medium | high | unknown`
- `portfolio-allocation.action`: `매수 | 매도 | 유지 | unknown`
- `financial-fact-checker.findings[].verdict`: `match | mismatch | unsourced | period_mismatch | unit_mismatch`
- `investment-devils-advocate.objections[].type`: `overreach | counterpoint | missing_context`

## 6. `.claude/skills/generating-krx-report/` — 8개 분석 모듈 + 4단계 검증 게이트

**책임**: [A] 파이프라인의 핵심. 13개 Python 스크립트로 DART/pykrx 데이터를 조회·정규화·계산하고, 8개 모듈로 채점해 HTML 리포트를 생성한다. 전체 워크플로는 `entry-points.md` §"Claude Code 스킬 호출"과 `data-flow.md` §1에서 상세히 다룬다.

**8개 분석 모듈**과 그 판정 방식(정성/정량):

| 모듈 | 판정 방식 | 산출 |
|---|---|---|
| business | 정성 — 서수 등급(0~3) + evidence_ids | `level`/`na_reason` |
| quality | 정량 — Python 채점, Claude는 해석 서술만 | `criteria: []` + verdict/strengths/weaknesses |
| growth | 정량 (CANSLIM C·A의 의존 대상, 항상 실행) | 위와 동일 |
| moat | 정성 | 위와 동일 |
| valuation | 정량 | 위와 동일 |
| trend(CANSLIM) | 정량 | 위와 동일 |
| risk | 정성 | 위와 동일 |
| catalyst | 정성 | 위와 동일 |

**4단계 검증 게이트**: Gate 1(종목 식별, `resolve_security.py`) → Gate 2(evidence 검증, `validate_evidence.py`) → Gate 3·4(합성·보고서 검증, `validate_report.py`). 한 게이트라도 실패하면 최종 보고서 대신 검증 실패 보고서를 생성한다.

**공개 인터페이스(CLI, 대표 스크립트)**: 각 스크립트는 `python <script>.py {TICKER} [옵션]` 형태의 argparse CLI. 전체 13종 목록은 SKILL.md에 있으며, 여기서는 데이터 흐름상 핵심인 스크립트만 표기한다(`data-flow.md` §1 참고).

## 7. `.claude/skills/converting-investment-blog/` — 리포트→블로그 변환

**책임**: 이미 생성된 리포트의 manifest·claims·module-results만 읽어 블로그 8절 구조 Markdown 초안을 생성한다. `allowed-tools: Read, Write, Bash`.

**읽기 화이트리스트**: manifest, claims, evidence(지목된 ID만), module-results. **금지**: `data/raw/`, `data/normalized/`, 리포트 HTML 원문.

**공개 인터페이스**: 스킬 자체는 CLI 인자를 받지 않고, 트리거 문구("보고서를 블로그 문체로 바꿔줘")로 발동하며 출력은 `docs/blog/{YYYY-MM-DD}_{ticker}_{회사명}.md` 형식의 8절 구조 Markdown 파일이다.

## 8. `.claude/skills/company-blog-pipeline/` — 블로그 파이프라인 오케스트레이터

**책임**: `converting-investment-blog` 실행 → `financial-fact-checker`/`investment-devils-advocate` 병렬 실행 → `validate_blog_post.py` 검증 → 최대 2회 회귀 루프를 조율한다. `allowed-tools: Read, Write, Bash, Agent` — 7종 중 유일하게 `Agent` 도구를 가진 스킬(다른 에이전트를 호출할 수 있는 유일한 지점).

**공개 인터페이스**: 종목명/티커 + 게시용 글쓰기 의도("블로그 글 써줘" 등)로 트리거. manifest의 4개 검증 게이트를 모두 통과한 리포트만 변환 대상으로 받아들인다. 외부 발행은 수행하지 않는다(로컬 Markdown 초안까지만).

## 9. `.claude/skills/saving-tistory-draft/` — 로컬 저장 전용

**책임**: 완성된 블로그 초안을 `docs/blog/` 아래 로컬 Markdown 파일로 저장하고, 티스토리 수동 붙여넣기 안내를 제공한다. **네트워크 호출 0건** — 검증기가 비정상 종료하면 저장을 거부한다.

**공개 인터페이스**: 트리거 문구("초안 저장해줘")로 발동. 발행 자동화는 의도적으로 구현하지 않는다(발행은 되돌리기 어렵고 캐시·색인이 남기 때문).

## 10. `.claude/skills/add-comments/` — 독립 유틸리티 스킬

**책임**: 코드 파일에 현재 스터디 주차 학습 개념을 반영한 주석/docstring을 삽입한다. 위 분석·블로그 파이프라인과 데이터를 공유하지 않는 완전히 독립된 스킬.

**공개 인터페이스**: 트리거 문구("주석 달아줘", "@파일명 주석")로 발동, 대상 파일 경로를 인자로 받는다.

## 11. `.claude/hooks/` — 라이프사이클 훅 4종

**책임**: Claude Code 세션 이벤트에 반응해 부수 작업(주석 삽입, 커밋 형식 검사, Notion 기록, 세션 로그 저장)을 자동 수행한다. 트리거 조건과 실행 시점은 `entry-points.md` §"라이프사이클 훅"에서 상세히 다룬다.

| 훅 파일 | 줄수 | 책임 |
|---|---|---|
| `auto_header.py` | 139줄 | 새 코드 파일(`.py/.ts/.tsx/.js/.jsx`) Write 시 주차별 헤더 주석 자동 삽입, `git config user.name`으로 작성자 식별 |
| `commit_format.py` | 86줄 | `git commit` 명령의 `-m` 메시지가 Conventional Commits 패턴(`feat|fix|docs|refactor|test|chore|style`)을 따르는지 검사 |
| `notion_sync.py` | 165줄 | `git commit` 감지 시 변경 파일 목록(최대 `NOTION_SYNC_MAX_FILES`개)을 Notion 변경 로그 페이지에 자동 기록 |
| `log_session_end.py` | 186줄 | 세션 종료 시 `session_id`·작업 제목·종료 사유를 `sessions/` 아래 JSON에 최신 10개까지 누적 저장, GitHub 이슈 등록 연동 |

## 12. `portfolio-team.yaml` (루트) — [B] 파이프라인 소유권 선언

**책임**: 코드가 아니라 선언적 설정 파일이지만, `.claude/agents/portfolio-*.md` 3종의 읽기 범위와 `orchestrate_portfolio.py`의 쓰기 범위를 명문화하는 유일한 지점이다.

**공개 인터페이스(스키마)**: `team`, `leader.runtime`, `members[].{name, definition, owns_read, produces.{schema_key, values}}`, `ownership_rules.{writable_by_leader_only, read_only_all}`, `execution.{mode, timeout_sec, output_dir}`. 내부 모듈 관계로서의 상세 해석은 `dependencies.md` §3 참고.
