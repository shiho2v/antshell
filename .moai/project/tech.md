# tech.md — 기술 스택

수집일: 2026-09-06 | 근거: 코드베이스 정찰(Explore 에이전트 분석 결과)

## 1. 제약 (기술 선택에 영향을 준 배경)

인터뷰(`interview.md` Stage A Round 2)에서 확정된 3가지 제약이 아래 기술 선택 다수의 배경이다.

1. **유료 클라우드 서비스 최소화** — Supabase, Notion, GitHub, DART, KRX 모두 무료/저비용 티어 사용을 전제로 함.
2. **Git 초보자 포함 팀 운영** — 브랜치 규칙 고정(`_claude_core/GIT_RULES.md`), 자동화 훅(`.claude/hooks/`)으로 커밋 포맷·세션 종료 처리 등을 자동화.
3. **Claude Code 토큰 절약** — `_claude_core/`로 참조 문서를 분리하고 `CLAUDE.md`에서 "필요한 것만 읽으라"는 규칙을 명시. 이는 파일 분리 설계 자체가 제약을 구현체로 삼은 사례다.

## 2. 사용 중 (코드에서 실제 호출 확인)

### 백엔드
| 패키지 | 버전 | 근거 |
|---|---|---|
| fastapi | 0.111.0 | `backend/requirements.txt:1`, `backend/app/main.py:7,16` |
| uvicorn[standard] | 0.30.1 | `backend/requirements.txt`, 실행 명령에서 사용 |
| httpx | 0.27.0 | `backend/app/auth.py`에서 사용 |

### 프런트엔드
| 패키지 | 버전 | 근거 |
|---|---|---|
| next | 14.2.5 | `frontend/package.json:12`, App Router 구조(`src/app/`) |
| react / react-dom | ^18 | `frontend/package.json:13-14` |
| typescript | 5 | `frontend/package.json:20`, `tsconfig.json:15-16` |
| tailwindcss | 3.4 | PostCSS 경유, `tailwind.config.js:10` — 테마 미설정 상태 |
| @supabase/ssr | ^0.5.1 | `frontend/src/lib/supabase.ts:9-14`에서 사용 |
| @supabase/supabase-js | ^2.45.0 | 타입 전용 사용(실제 호출은 `@supabase/ssr` 경유) |

### 분석 파이프라인
- Python (버전 미확정 — pyproject.toml/requirements 파일이 스킬별로 분산되어 루트 통합 버전 고정 없음)
- DART Open API 호출: `.claude/skills/generating-krx-report/scripts/_common.py`, `fetch_dart_*.py`
- KRX 시세 조회: `pykrx` (`fetch_krx_market.py`)

## 3. 선언됐지만 미사용 (의존성 목록에는 있으나 import 없음)

| 패키지 | 위치 | 비고 |
|---|---|---|
| python-jose[cryptography] 3.3.0 | `backend/requirements.txt` | 어떤 파일에서도 import되지 않음 |
| python-dotenv 1.0.1 | `backend/requirements.txt` | 대신 손으로 작성한 `.env` 파서가 3곳에 중복 존재: `backend/app/main.py:29-41`, `.claude/hooks/notion_sync.py:17-29`, `.claude/hooks/log_session_end.py:30-43` |
| zustand ^4.5.4 | `frontend/package.json` | `PROJECT.md`는 상태 관리 레이어로 명시하지만 실제 import는 0건 |

→ `product.md` §7 로드맵 후보: 이 3개 패키지를 실제로 채택할지, 의존성에서 제거할지 결정 필요.

## 4. 문서에는 있지만 코드 없음 (아스피레이셔널 — 현재 미구현)

| 항목 | 언급된 위치 | 상태 |
|---|---|---|
| TradingView Lightweight Charts | `README.md`, `PROJECT.md` | 미설치, 미사용 |
| Celery + Redis | `PROJECT.md`, `.env.example`(`REDIS_URL`), `README.md` brew 안내 | 미설치, 미사용 |
| KIS 실시간 시세 | `PRD.md`, `.env.example` 환경변수 4개 | 코드 0건 |
| BigKinds 뉴스 API | `PROJECT.md`, `.env.example` | 코드 0건 — `news-collector` 에이전트는 대신 일반 WebSearch 사용 |
| FinanceDataReader | `PROJECT.md` | 코드 0건 — 대신 `pykrx` 사용 |

이 항목들은 현재 스택이 아니라 로드맵 후보다. 문서 정정 또는 실제 도입 여부는 `product.md` §7 참고.

## 5. 외부 시스템 및 자격증명

| 시스템 | 용도 | 필요 환경변수 | 비고 |
|---|---|---|---|
| DART Open API | 공시·재무 데이터 조회 | `DART_API_KEY` | 사용 확인됨 |
| KRX / pykrx | 시세 조회 | `KRX_ID`, `KRX_PW` | **`.env.example`에 문서화되어 있지 않음** — 이 자격증명이 없으면 CANSLIM 채점의 L/I/M 항목이 N/A로 저하됨. `product.md` §7 로드맵 3번 항목 |
| Notion API | 보고서 저장, 주간 요약 | `NOTION_API_KEY` + 페이지 ID 2개 | `backend/app/main.py:78-86`, `.claude/hooks/notion_sync.py`, `notion_weekly.yml`에서 사용 |
| GitHub REST API | 이슈 조회/생성 | `GITHUB_TOKEN` | `backend/app/main.py:105`, `log_session_end.py`에서 사용 |
| Supabase Auth | 로그인/회원가입 | Supabase 프로젝트 키 | 프런트엔드에서 직접 호출, 백엔드 미경유 — 결과적으로 백엔드 3개 엔드포인트는 무인증 |
| Anthropic / Claude | 에이전트 오케스트레이션 | 없음(사용자 Claude Pro CLI 세션 사용) | `scripts/orchestrate_*.py`가 `claude -p` 서브프로세스로 호출 — `ANTHROPIC_API_KEY` 환경변수 자체는 사용하지 않음. `_claude_core/ENV_GUIDE.md`는 이 키를 haiku 모델 전용이며 웹 서비스의 요약 기능에만 쓰인다고 설명하지만 해당 경로는 코드에서 발견되지 않음(미확정, `product.md` §8 참고) |

## 6. 빌드 · 테스트 · 검증

- **린터/포매터 설정 파일 없음**: `pyproject.toml`, `ruff.toml`, `pytest.ini`, `.eslintrc` 등 어떤 것도 저장소에 존재하지 않음(전수 검색 결과 0건).
- `npm run lint`는 `eslint-config-next` 기본값에만 의존하며 커밋된 설정 파일이 없음.
- **실제 자동 테스트는 분석 파이프라인에만 존재**:
  - `.claude/skills/generating-krx-report/tests/test_units.py` (725줄, unittest, 네트워크 없음)
  - `.claude/skills/generating-krx-report/tests/test_fixtures.py` (549줄)
  - `.claude/skills/converting-investment-blog/tests/test_validate_blog_post.py` (304줄, pytest)
  - `backend/`, `frontend/`, `scripts/`에는 테스트가 전혀 없음.
- **CI 깨짐**: `.github/workflows/ci.yml`이 존재하지 않는 `backend/tests/`를 대상으로 `pytest backend/tests/ -v`를 실행해 매 실행마다 실패한다. 위 3개의 실제 테스트 스위트는 CI에서 전혀 실행되지 않는다. `ruff`와 `pytest`는 설치되지만 버전 고정이 없다. → `product.md` §7 로드맵 2번 항목.
- 그 외 CI: `notion_weekly.yml`(토요일 크론, git log를 Notion에 요약), `label-sync.yml`.

## 7. 미확정 사항

- Python 버전 고정 여부 — 스킬별 요구사항 파일이 분산되어 루트 통합 버전 명시가 없음. 확인 방법: 각 스킬 디렉터리의 `requirements.txt`(있다면) 취합 및 CI 수정 시 버전 고정.
- `ANTHROPIC_API_KEY`의 실제 용도(§외부 시스템 표 Anthropic 행 참고) — `product.md` §8과 동일한 미확정 사항.
