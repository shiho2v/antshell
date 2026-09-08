# overview.md — 아키텍처 개요

수집일: 2026-09-06 | 근거: `structure.md`·`product.md`·`tech.md` + 소스 직접 확인(backend/app, frontend/src/app, scripts/, .claude/agents, .claude/skills/generating-krx-report)

> 이 문서는 `structure.md`가 이미 확정한 사실과 절대 모순되지 않는다. `structure.md`가 "무엇이 분리되어 있는가"를 다뤘다면, 이 문서는 "그 분리된 각 조각이 내부적으로 어떤 설계 원칙으로 짜여 있는가"를 다룬다.

## 1. 가장 먼저 이해해야 할 것 — 세 파이프라인의 완전한 분리

이 저장소를 하나의 시스템으로 읽으면 반드시 오독한다. 실제로는 **데이터를 전혀 공유하지 않는 세 개의 독립 시스템**이 한 저장소에 공존한다.

- **[A] 분석 파이프라인** — `generating-krx-report` → `company-blog-pipeline` → `converting-investment-blog`/`saving-tistory-draft`. DART·KRX 실데이터를 조회하고, 실제 자동 테스트를 갖춘, 이 저장소의 실질적 본체.
- **[B] 에이전트 팀 CLI 데모** — `scripts/orchestrate_portfolio.py`, `orchestrate_stock_agents.py`. `claude -p` 서브프로세스로 7종 금융 에이전트를 병렬 호출하는 교육용 데모.
- **[C] "웹앱"** — Next.js 대시보드 + FastAPI 백엔드. 대시보드는 100% 목(mock) 데이터로 렌더링되며, 백엔드는 `data/`나 `outputs/`를 한 줄도 읽지 않는다.

세 파이프라인 사이에는 **런타임 데이터 흐름이 없다.** A와 B가 각각 생산하는 HTML 리포트·JSON 산출물은 C의 어떤 라우트에서도 소비되지 않는다. 이 사실은 아래의 모든 설계 패턴·의존성·데이터 흐름 서술의 전제이며, `modules.md`·`dependencies.md`·`data-flow.md` 어디에서도 뒤집히지 않는다.

## 2. 실제로 존재하는 설계 패턴

### 2.1 "계산은 Python, 판단은 Claude" (분석 파이프라인의 핵심 원칙)

`generating-krx-report/SKILL.md`의 절대 규칙 1번이 명시하는 이 패턴은 스킬 문서의 선언에 그치지 않고, 파이프라인의 스크립트-모듈 경계 설계 자체에 반영되어 있다.

- 성장률·CAGR·멀티플·모듈 점수·총점은 전부 `calculate_metrics.py`, `score_modules.py` 등 Python 스크립트가 계산한다.
- Claude(모듈 분석 단계)는 `metrics.json`/evidence pack을 **그대로 인용**할 뿐, 산술을 수행하지 않는다.
- 정량 모듈(quality/growth/valuation/trend)은 `criteria: []`로 등급 자체를 제출하지 않고 해석 서술(verdict/strengths/weaknesses)만 작성한다.
- 정성 모듈(business/moat/risk/catalyst)은 서수 등급(0~3)만 제출하고 점수 계산은 하지 않는다.

이 분리는 "LLM이 산술에서 실수한다"는 가정 위에 설계되어 있으며, 이 패턴이 이 저장소에서 가장 방어적으로(4단계 검증 게이트로) 지켜지는 규칙이다.

### 2.2 단일 파일 소유 + JSON 전용 출력 (7종 프로젝트 에이전트)

`.claude/agents/`의 7개 프로젝트 전용 에이전트(`financial-data`, `news-collector`, `portfolio-valuation`, `portfolio-risk`, `portfolio-allocation`, `financial-fact-checker`, `investment-devils-advocate`)는 예외 없이 동일한 세 가지 규율을 코드 수준에서 공유한다.

1. **읽기 파일 화이트리스트 고정** — 각 에이전트는 자신의 역할에 필요한 파일 패턴 하나(예: `portfolio-valuation`은 `data/{code}_fundamentals.json`만)만 읽도록 프롬프트에 명시되어 있고, 다른 파일 접근은 "절대 금지" 섹션으로 차단된다.
2. **JSON 전용 출력** — 모든 에이전트가 "그 외 설명·마크다운·코드블록 금지"를 명시하며, 응답 스키마를 프롬프트 안에 인라인으로 고정한다.
3. **호출 횟수 상한** — 웹 조회 에이전트(`financial-data`, `news-collector`)는 각각 최대 3회로 호출 수를 제한한다.

이 패턴은 `portfolio-team.yaml`의 `ownership_rules`(파일 소유권 선언)와 대응 관계에 있다 — 팀 전체가 "누가 무엇을 읽고 쓸 수 있는가"를 선언적으로 통제하는 하나의 설계 철학을 공유한다.

### 2.3 읽기 화이트리스트 패턴 (converting-investment-blog / 검증 에이전트)

블로그 변환 계열(`converting-investment-blog`, `financial-fact-checker`, `investment-devils-advocate`)은 원본 데이터(`data/raw/`, `data/normalized/`, 재무제표 원문, 리포트 HTML 원문)를 읽지 않고, **manifest·claims·module-results·evidence(지목된 ID만)** 로만 작업 범위를 제한한다. 이는 "이미 검증된 근거 밖으로 나가 새로운 사실을 추론하지 못하게" 만드는 구조적 장치이며, 웹 검색 도구 자체를 부여하지 않는 것(`tools: Read`만)으로 이중 강제된다.

### 2.4 검증 게이트 체인

분석 파이프라인은 4개의 순차 게이트(Gate 1 종목 식별 → Gate 2 evidence 검증 → Gate 3·4 합성·보고서 검증)를 통과하지 못하면 최종 보고서 대신 검증 실패 보고서를 생성한다. 블로그 파이프라인은 이 위에 별도의 회귀 루프(최대 2회, `validate_blog_post.py`)를 얹는다. 두 파이프라인 모두 "실패 시 조용히 진행하지 않고 중단한다"는 동일한 원칙을 따른다.

## 3. 시스템 경계 — 저장소 내부 vs. 로컬 세션 vs. 외부 API

| 경계 | 내용 |
|---|---|
| **저장소 내부에서 완결** | `backend/app/*`의 라우트 핸들러 로직, `frontend/src/app/*`의 렌더링 로직, `generating-krx-report`의 13개 Python 스크립트(계산 전담) |
| **사용자의 로컬 `claude` CLI 세션에 의존** | `scripts/orchestrate_*.py`가 `subprocess.run([claude_bin, "-p", ...])`로 호출하는 7종 에이전트 실행 전체 — `ANTHROPIC_API_KEY` 환경변수가 아니라 사용자의 Claude Pro/Max 로그인 세션을 소비한다. `company-blog-pipeline`이 `financial-fact-checker`/`investment-devils-advocate`를 병렬 실행하는 것도 Claude Code 런타임(Task 도구) 안에서만 가능하며, `scripts/` CLI에서는 재현되지 않는다. |
| **외부 API에 의존** | DART Open API(공시·재무), pykrx/Naver 경유 KRX 시세, Notion API(리포트 저장), GitHub REST API(이슈 조회), Supabase Auth(로그인/회원가입) — 각 의존 관계는 `dependencies.md` §4 참고 |

핵심 구분: **[A] 분석 파이프라인의 계산 단계는 순수 저장소 내부 로직**(외부 LLM 세션 없이 재현 가능)이지만, **[A]의 모듈 판단 단계와 [B] 전체**는 Claude Code 런타임 또는 로컬 `claude` CLI 세션의 존재를 전제로 한다. 이 구분이 없으면 "이 저장소만으로 완전히 재현 가능한가"라는 질문에 답할 수 없다.

## 4. 다음 문서 안내

- 각 모듈의 책임과 공개 인터페이스 → `modules.md`
- 내부/외부 의존성 그래프 → `dependencies.md`
- 트리거 유형별 진입점 → `entry-points.md`
- 세 파이프라인 각각의 종단 데이터 흐름 → `data-flow.md`
