# structure.md — 아키텍처와 모듈 경계

수집일: 2026-09-06 | 근거: 코드베이스 정찰(Explore 에이전트 분석 결과)

> 이 문서는 인터뷰에서 확정된 **최우선 문서화 대상**이다(9명이 같은 저장소를 공유하므로 경계가 가장 자주 마찰을 일으킨다). 새로 합류하는 팀원은 이 문서, 특히 §1을 가장 먼저 읽어야 한다.

## 1. 가장 먼저 이해해야 할 것 — 세 개의 분리된 파이프라인

이 저장소에는 실제 HTTP 경계(프런트엔드 → FastAPI)가 존재하지만, **그 경계로 주식 데이터가 전혀 흐르지 않는다.** 대신 서로 데이터를 공유하지 않는 세 개의 독립 파이프라인이 공존한다.

```
[A] 분석 파이프라인 (실질적 본체)
    .claude/skills/generating-krx-report/scripts/*.py (DART + pykrx)
        → data/*.json
        → outputs/{TICKER}_report_{as_of}.html
    → company-blog-pipeline
        → .claude/skills/converting-investment-blog/ (+ financial-fact-checker, investment-devils-advocate 병렬 검증)
        → docs/blog/*.md

[B] 에이전트 팀 CLI 데모
    scripts/orchestrate_stock_agents.py, orchestrate_portfolio.py
        --(subprocess `claude -p`)--> 7종 금융 에이전트
        읽기: data/{ticker}_fundamentals.json, data/{ticker}_market.json
        쓰기: data/{ticker}_agents.json, outputs/portfolio_report_*.html
        (portfolio-team.yaml:41-48 이 outputs/portfolio_report_*.html 을
         writable_by_leader_only, data/*.json 을 read_only_all 로 공식 선언)

[C] "웹앱" — 대시보드는 목(mock) 데이터
    frontend/src/app/dashboard/page.tsx (MOCK_STOCKS 4종, MOCK_NEWS 3건 하드코딩)
        --HTTP--> backend/app/main.py (FastAPI, 3개 라우트만 존재)
                     GET  /health
                     POST /api/report/notion  --> Notion API
                     GET  /api/github/issues  --> GitHub API
        (Supabase Auth는 브라우저에서 backend를 거치지 않고 직접 호출됨)
```

**핵심**: `backend/app/main.py`는 `data/`나 `outputs/`를 한 줄도 읽지 않는다(grep으로 확인됨). 즉 A·B가 생산하는 모든 분석 결과는 C(웹앱)에 전혀 반영되지 않는다. 대시보드에 보이는 종목 가격과 뉴스는 100% 하드코딩된 문자열이며, 백엔드가 실제로 프록시하는 것은 Notion 저장과 GitHub 이슈 조회뿐이다.

이 분리는 결함이 아니라 현재 개발 단계의 사실이다 — 다만 `product.md` §7의 로드맵 1번 항목(백엔드-분석 파이프라인 연결)이 이 세 파이프라인 중 A와 C를 잇는 유일하게 계획된 다리다.

## 2. 디렉터리 구조

| 경로 | 역할 | 비고 |
|---|---|---|
| `backend/app/` | FastAPI 서비스. `main.py`(125줄): health · Notion 프록시 · GitHub 이슈 조회. `auth.py`(31줄): Supabase JWT 의존성이지만 어떤 라우트에서도 미사용 | 위 [C] 참고 |
| `frontend/src/app/` | Next.js 14 App Router 페이지 — `dashboard`, `login`, `signup`, 공통 `layout` | 대시보드는 목 데이터로 렌더링 |
| `frontend/src/lib/` | Supabase 브라우저 클라이언트 팩토리(`supabase.ts`) | 백엔드를 거치지 않고 브라우저에서 직접 호출 |
| `scripts/` | `claude -p` 서브프로세스로 금융 에이전트를 오케스트레이션하는 CLI (`orchestrate_portfolio.py` 240줄, `orchestrate_stock_agents.py` 84줄) | 위 [B] 파이프라인 |
| `data/` | 분석 입력 샘플 JSON(종목별 fundamentals/market/agents, `portfolio.example.json`, `portfolio.edge.json`) | **범위 제외**: 개별 파일 내용은 문서화하지 않고 스키마·생성 규칙만 기술 |
| `outputs/` | 생성된 HTML 리포트 + `AB_TEST.md` | **범위 제외**: 개별 산출물 내용이 아니라 생성 규칙만 기술 |
| `.claude/agents/` | 프로젝트 전용 에이전트 7종(§4) + vendored `moai/` 에이전트 | |
| `.claude/skills/generating-krx-report/` | 가장 규모가 큰 실질 서브시스템 — 13개 Python 스크립트, 8개 분석 모듈, 4단계 검증 게이트, "Claude는 산술을 직접 하지 않는다" 원칙 | §5 참고 |
| `.claude/skills/converting-investment-blog/` | 리포트 → 블로그 변환. 읽기 화이트리스트 엄격 적용(manifest/claims/module-results/evidence-by-ID만 — `data/raw`, `data/normalized`, 리포트 HTML 원문은 읽지 않음) | |
| `.claude/hooks/` | 라이프사이클 훅 — `notion_sync.py`, `auto_header.py`, `commit_format.py`, `log_session_end.py` | |
| `_claude_core/` | 토큰 예산을 고려해 분리한 참조 문서(`PROJECT.md`, `ENV_GUIDE.md`, `GIT_RULES.md`, `NOTION_SETUP.md`) | CLAUDE.md 토큰 절약 규칙의 구현체 |
| `docs/weekly/` | 12주차 주간 계획 문서 | 일부(WEEK_02/03/05/09~12) 아직 보일러플레이트 |
| `docs/blog/` | 블로그 파이프라인의 최종 산출물(마크다운) | **범위 제외**: 개별 게시글 내용은 문서화하지 않음 |
| `portfolio-team.yaml` (루트) | [B] 파이프라인의 파일 소유권 선언(§4, §6 참고) | `data/*.json`은 전원 읽기 전용, `outputs/portfolio_report_*.html`은 리더만 쓰기 가능 |

## 3. 진입점(Entry Points)

| 대상 | 명령 |
|---|---|
| 백엔드 실행 | `cd backend && uvicorn app.main:app --reload` (포트 8000) |
| 프런트엔드 실행 | `cd frontend && npm run dev` (포트 3000; `build`/`start`/`lint`도 존재) |
| 포트폴리오 에이전트 데모 | `python scripts/orchestrate_portfolio.py --portfolio data/portfolio.example.json --save` |
| 종목 에이전트 데모 | `python scripts/orchestrate_stock_agents.py 005930 --save` |
| KRX 분석 스크립트 13종 | 각각 argparse 기반 — 목록은 `generating-krx-report/SKILL.md` 참고 |
| 분석 스킬 테스트 | `python .claude/skills/generating-krx-report/tests/test_units.py` (unittest) |
| 블로그 검증 테스트 | `pytest .claude/skills/converting-investment-blog/tests/ -q` |

## 4. Claude Code 하네스 구성 — 프로젝트 에이전트 7종

모두 "단일 파일 소유 + JSON 전용 출력"을 원칙으로 설계되어 있다.

| 에이전트 | 역할 | 제약 |
|---|---|---|
| `financial-data` | 재무 데이터 웹 조회 | 최대 3회 호출 |
| `news-collector` | 뉴스 웹 조회 | 최대 3회 검색 |
| `portfolio-valuation` | 밸류에이션 계산 | `data/{code}_fundamentals.json`만 읽음 |
| `portfolio-risk` | 리스크 계산 | `data/{code}_market.json`만 읽음 |
| `portfolio-allocation` | 자산 배분 계산 | `data/{code}_market.json`에서 가격만 읽음 |
| `financial-fact-checker` | 블로그 초안의 수치를 manifest/claims/evidence와 대조 검증 | 읽기 전용, 웹 조회 없음 |
| `investment-devils-advocate` | 기존 근거만으로 반론 제기 | 읽기 전용, 웹 조회 없음 |

## 5. Claude Code 하네스 구성 — 도메인 스킬 5종의 조합 흐름

```
generating-krx-report        (8모듈 채점 · 4게이트 · "계산은 Python이 담당" 원칙)
    → company-blog-pipeline   (오케스트레이터: converting-investment-blog +
                                두 리뷰 에이전트를 병렬 실행 + validate_blog_post.py,
                                최대 2회 회귀 루프)
        → converting-investment-blog  (리포트 → 블로그 8절 구조 변환, 읽기 화이트리스트 엄격)
        → saving-tistory-draft         (로컬 저장 전용, 검증기 비정상 종료 시 거부,
                                          네트워크 호출 0건 — 발행 자동화는 의도적으로 하지 않음)

add-comments  (독립 스킬 — 현재 스터디 주차 태그가 붙은 파일 헤더/docstring 삽입)
```

## 6. 팀 협업 경계

- 브랜치 규칙: `feature/<주차>-<이름>-<기능명>` (`_claude_core/GIT_RULES.md`)
- 팀 규모: 9명, 저장소 `shiho2v/antshell` 공유(PR #12, #13 등 머지 이력으로 확인)
- 파일 소유 경계가 명시적으로 선언된 유일한 지점: `portfolio-team.yaml:41-48`(`data/*.json`은 전원 읽기 전용, `outputs/portfolio_report_*.html`은 리더만 쓰기 가능)
- 그 외 디렉터리(특히 `.claude/`, `docs/`)의 소유권은 문서화되어 있지 않음 — 충돌이 발생하기 쉬운 지점으로 §미확정 참고

## 7. 미확정 사항

- `data/*.json`, `outputs/*.html`의 정확한 스키마 정의 문서가 별도로 존재하지 않음 — 확인 방법: `generating-krx-report/SKILL.md` 및 각 스크립트의 출력부를 근거로 별도 스키마 문서를 `/moai plan`에서 작성할지 결정 필요.
- `.claude/`, `docs/` 디렉터리에 대한 팀 차원의 파일 소유 규칙(누가 어떤 하위 디렉터리를 주로 다루는지)이 `portfolio-team.yaml` 수준으로 명문화되어 있지 않음 — 확인 방법: 팀 내 실제 작업 분담 현황 재확인.
