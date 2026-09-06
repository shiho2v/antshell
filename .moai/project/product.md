# product.md — 돌아온 불타는 개미지옥

수집일: 2026-09-06 | 근거: `.moai/project/interview.md`, 코드베이스 정찰(Explore 에이전트 분석 결과)

## 1. 한 줄 소개

"클로드 코드로 시작하는 실전 에이전틱 코딩" 책을 학습하는 9명 스터디팀이, 12주(2025.07.05 ~ 10.18, 현재 8주차 · Ch.08 MoAI-ADK)에 걸쳐 국내 주식 분석 웹앱과 KRX 종목 분석 리포트 파이프라인을 함께 만드는 스터디 겸 실전 프로젝트다.

## 2. 대상 사용자

- **1차 사용자 — 스터디팀 9명**: 매주 챕터를 학습하며 직접 코드를 작성·리뷰하는 주체. `feature/<주차>-<이름>-<기능명>` 브랜치 규칙(`_claude_core/GIT_RULES.md`)으로 각자의 기여를 구분한다. Git 초보자가 섞여 있어 자동화로 진입 장벽을 낮추는 것이 팀 운영의 전제다.
- **2차 사용자 — 분석 리포트의 최종 소비자**: KRX 종목 분석 HTML 보고서와 투자 블로그 초안을 읽는 사람. 현재는 팀 내부용이며, `SKILL.md`가 선언한 인터페이스상으로는 임의 종목명/티커에 적용 가능하나 실제 검증된 것은 `data/`의 샘플 5종목 이내다.

## 3. 두 개의 핵심 구성요소 — 왜 동등하게 다루는가

이 저장소는 서로 다른 완성도를 가진 두 개의 핵심 구성요소를 동시에 담고 있으며, 인터뷰에서 사용자가 두 구성요소를 동등한 주역으로 다루기로 확정했다.

| 구성요소 | 내용 | 현재 완성도 |
|---|---|---|
| **웹앱** | Next.js 14 대시보드 + FastAPI 백엔드 + Supabase 인증 | 뼈대 수준 — 대시보드는 목(mock) 데이터로 동작 |
| **분석 파이프라인** | DART/KRX 데이터를 8개 모듈로 채점해 HTML 리포트를 생성하고, 이를 블로그 초안까지 변환하는 Claude Code 스킬·에이전트 체계 | 실제로 동작하는 본체 — 약 7,000줄, 실제 자동 테스트 보유 |

`PRD.md`/`README.md`는 웹앱만 공식적으로 선언하지만, 실제 코드량과 실행 가능성 기준으로는 분석 파이프라인이 이 저장소의 실질적 본체다. 두 구성요소는 현재 **데이터를 전혀 공유하지 않는 별개의 시스템**으로 존재한다(이유와 구조는 `structure.md`의 3-파이프라인 절 참고).

## 4. 현재 상태 (2026-09-06 기준, 정찰 근거)

### 웹앱 — 뼈대(scaffold) 단계
- `frontend/src/app/dashboard/page.tsx`에 `MOCK_STOCKS`(005930/000660/009150/008490 4종, 문자열 가격) · `MOCK_NEWS`(3건)가 하드코딩되어 있고, 이것이 대시보드가 보여주는 전부다.
- 프런트엔드가 실제로 호출하는 백엔드 API는 `/api/github/issues` 조회와 `/api/report/notion` 전송 2개뿐이며, 둘 다 주식 데이터와 무관하다.
- 백엔드(`backend/app/main.py`)는 `/health`, `/api/report/notion`, `/api/github/issues` 3개 라우트만 노출하고, `data/`나 `outputs/`를 전혀 읽지 않는다(grep으로 확인됨).
- Supabase 인증은 프런트엔드 브라우저에서 직접 호출되어 백엔드를 우회하며, 백엔드의 `auth.py` 의존성은 어떤 라우트에서도 사용되지 않는다 — 결과적으로 3개 백엔드 엔드포인트 모두 인증 없이 열려 있다.

### 분석 파이프라인 — 실질적으로 동작하는 본체
- `.claude/skills/generating-krx-report/`가 DART 공시·재무와 pykrx 시세를 실제로 조회해 8개 모듈(사업/품질/성장/해자/밸류에이션/추세-CANSLIM/위험/촉매) 채점과 4단계 검증 게이트를 거쳐 HTML 리포트(`outputs/{TICKER}_report_{as_of}.html`)를 생성한다.
- 이 파이프라인은 `.claude/skills/generating-krx-report/tests/`(unittest, 725+549줄)와 `.claude/skills/converting-investment-blog/tests/`(pytest, 304줄)라는 **실제 자동 테스트를 보유**하고 있다 — 이는 초기 인터뷰의 "자동 테스트 없음" 인상을 정정하는 사실이다(웹앱에는 여전히 테스트가 없다).
- 이 외에 `company-blog-pipeline`(review 에이전트 병렬 실행 + 검증 루프)이 리포트를 투자 블로그 초안(`docs/blog/*.md`)으로 변환하고, `saving-tistory-draft`가 로컬 저장까지 담당한다(외부 발행 자동화는 의도적으로 하지 않음).

### 그 외 별도 데모 — 에이전트 팀 CLI
- `scripts/orchestrate_stock_agents.py` · `orchestrate_portfolio.py`는 `claude -p` 서브프로세스로 7종 금융 에이전트를 오케스트레이션하는 CLI 데모이며, 위 두 축과도 데이터를 공유하지 않는 세 번째 독립 파이프라인이다.

## 5. 알려진 결함 (건설적 로드맵 항목으로 처리 — 비난이 아님)

| 항목 | 내용 |
|---|---|
| CI 깨짐 | `.github/workflows/ci.yml`이 존재하지 않는 `backend/tests/`를 대상으로 `pytest`를 실행해 매번 실패하며, 실제로 존재하는 3개 스킬 테스트 스위트는 CI에서 전혀 실행되지 않는다 |
| 선언-미설치 스택 | TradingView Lightweight Charts, Celery+Redis, KIS 실시간 시세, BigKinds 뉴스 API, FinanceDataReader — 문서(README/PROJECT.md/PRD.md)에는 있으나 코드에는 없음. 아래 §로드맵의 후보로만 관리 |
| 죽은 코드 | 미사용 Supabase 인증 의존성(`backend/app/auth.py`), 미사용 패키지(`python-jose`, `python-dotenv`, `zustand`) |
| 문서 링크 깨짐 | `CLAUDE.md`가 가리키는 `docs/architecture/ARCH.md`, `DEV_PRINCIPLES.md`가 가리키는 `WEB_DEV_GUIDELINES.md` 둘 다 파일 없음 |
| 자격증명 문서 누락 | `generating-krx-report` 스킬이 요구하는 `KRX_ID`/`KRX_PW`가 `.env.example`에 없음(자세한 내용은 `tech.md`) |
| 주차 문서 미완성 | `docs/weekly/WEEK_02/03/05/09~12.md` 등 일부가 보일러플레이트 상태로 남아 있음 |

## 6. 12주 스터디 로드맵 맥락

- 스터디 기간: 2025.07.05 ~ 10.18, 총 12주
- 현재: 8주차, Ch.08 MoAI-ADK 진행 중 (`CLAUDE.md` `CURRENT_WEEK=08`)
- 남은 4주 동안 웹앱과 분석 파이프라인을 함께 완성하는 것이 목표(인터뷰 확정 사항)
- 매주 담당 발표자와 진행 계획은 `docs/weekly/WEEK_XX.md`에 개별 기록됨

## 7. 로드맵 (후보 항목 — SPEC 작성은 `/moai plan`에서 진행)

이 절은 향후 SPEC 후보를 나열할 뿐이며, 이 문서 자체는 SPEC을 생성하지 않는다.

1. **[최우선 후보] 백엔드-분석 파이프라인 연결** — `data/*.json` / `outputs/*.html`을 서빙하는 백엔드 엔드포인트를 신설해 대시보드의 `MOCK_STOCKS`를 실데이터로 대체. 이것이 웹앱과 분석 파이프라인을 잇는, 현재 가장 가치 있는 연결 지점이다. SPEC 작성은 `/moai plan`에서 진행.
2. CI 수정 — `backend/tests/` 부재 문제 해결 및 기존 3개 스킬 테스트 스위트를 CI 파이프라인에 편입.
3. `KRX_ID`/`KRX_PW`를 `.env.example`에 추가하고 관련 문서 정정.
4. 미사용 의존성(`python-jose`, `python-dotenv`, `zustand`) 정리 또는 실제 사용처 확정.
5. 깨진 문서 링크(`ARCH.md`, `WEB_DEV_GUIDELINES.md`) 복구.
6. 미완성 주차 문서(`docs/weekly/WEEK_02/03/05/09~12.md`) 채우기.
7. 백엔드 인증 적용 여부 결정 — 현재 3개 엔드포인트 모두 무인증 상태.

## 8. 미확정 사항

- `ANTHROPIC_API_KEY`를 사용한 haiku 기반 요약 경로가 `_claude_core/ENV_GUIDE.md`에 언급되어 있으나 코드에서 발견되지 않음 — 실제로 구현할 것인지, 문서만 정정할 것인지 미확정. 확인 방법: 웹 서비스 요약 기능의 실제 필요 여부를 팀에 재확인.
- 웹앱 실사용자(2차 사용자)의 구체적 범위(팀 내부 전용인지, 외부 공개 예정인지) — 확인 방법: 스터디 종료 시점의 배포 계획을 팀과 재확인.
