---
id: SPEC-PORTFOLIO-001
title: "포트폴리오 분석 모듈 — 구현 계획"
version: "0.1.1"
status: draft
created: 2026-09-20
updated: 2026-09-20
tier: M
---

# SPEC-PORTFOLIO-001 구현 계획 (Plan)

## A.1 현재 상태 (조사 결과)

조사는 파일 읽기와 스크립트 1회 실행(2026-09-20)으로 수행했다.

| 항목 | 확인된 상태 |
|------|-------------|
| `scripts/orchestrate_portfolio.py` | 병합 JSON을 **표준 출력에만** 출력한다. `--save`는 `outputs/portfolio_report_YYYY-MM-DD.html` 한 개만 기록하며 **JSON을 저장하지 않는다**. `claude -p --output-format json --allowedTools Read,Bash`를 `subprocess`로 호출하고 타임아웃 240초 |
| 병합 결과 최상위 키 | `portfolio_name`, `as_of`, `valuation`, `risk`, `allocation` |
| `as_of` 실측값 | `"2026-07-25"` — 보유 종목 파일의 기준일이며 **실행일(2026-09-20)이 아니다** |
| `valuation.results[]` | `stock_code`, `name`, `revenue_growth_pct`, `op_income_growth_pct`, `verdict`(저평가\|적정\|주의\|고평가\|unknown), `score`(int), `basis`(텍스트) |
| `risk.results[]` | `stock_code`, `name`, `market_value`, `actual_weight_pct`, `concentration`, `drawdown_from_52w`, `supply_flow`, `volume_state`, `risk_score`, `overall`(low\|medium\|high\|unknown) |
| `allocation` | `agent`, `total_asset`, `cash`, `results[]`: `stock_code`, `name`, `current_price`, `market_value`, `actual_weight_pct`, `target_weight_pct`, `drift_pct`, `action`(매수\|매도\|유지\|unknown), `rebalance_amount` |
| 비중 불일치 | SK하이닉스 `actual_weight_pct`가 risk 47.8 / allocation 44.54. 분모가 보유 종목 합계 대 현금 포함 총자산으로 다름 (`spec.md` §1.4) |
| `volume_state` 이상값 | 서흥(`008490`)이 `"stale"`. 판정 불가 상태가 실제로 발생한다 |
| `backend/app/main.py` | 라우트: `/health`, `/api/settings/notion`(GET·PUT·DELETE), `/api/report/notion`, `/api/github/issues`, `/api/stocks/{code}/ohlcv`, `/api/stocks/{code}/indicators`. 차트 구간은 허용 목록 상수 `CHART_STOCK_CODES`, `DATA_DIR`(`__file__` 기준), 단일 파일 접근 헬퍼 `_read_ohlcv_document`를 쓴다 |
| `backend/tests/` | `conftest.py`, `test_chart.py`, `test_indicators.py`, `test_notion_settings.py`. 포트폴리오 테스트 없음 |
| `backend/requirements.txt` | `fastapi`, `uvicorn[standard]`, `httpx`, `python-dotenv`. **pytest 없음** (CI가 별도로 설치) |
| CI (`.github/workflows/ci.yml`, 단일 job `lint-and-test`) | 순서대로 8단계: ① `pip install -r backend/requirements.txt ruff pytest` → ② `npm ci`(frontend) → ③ `ruff check backend/`(루트 `ruff.toml`) → ④ `npm run lint`(frontend) → ⑤ **`pytest backend/tests/ -v`** → ⑥ **`npm run build`**(frontend) → ⑦ `pip-audit`(`continue-on-error: true`) → ⑧ `npm audit --audit-level=high`(`continue-on-error: true`). 차단 게이트는 ③~⑥ 네 개이고 ⑦·⑧은 경고다 |
| `scripts/tests/` | `test_fetch_ohlcv.py` 한 개(`SPEC-CHART-001` 산출물). **CI 테스트 단계가 `backend/tests/`만 지정하므로 이 디렉터리는 CI에서 실행되지 않는다.** 이 파일과 대상 스크립트(`scripts/fetch_ohlcv.py`, `scripts/orchestrate_portfolio.py`)의 import는 표준 라이브러리 + `pytest`뿐이라, CI가 이미 설치하는 의존성만으로 실행 가능하다 |
| `frontend/src/app/` | `dashboard`, `login`, `signup`, `settings`. **`portfolio` 라우트 없음** |
| `frontend/package.json` | devDependencies는 `@types/*`·`autoprefixer`·`eslint`·`eslint-config-next`·`postcss`·`tailwindcss`·`typescript`. **jest·vitest·`@testing-library` 없음 — 컴포넌트 테스트 인프라가 존재하지 않는다.** 화면 요구사항은 수동 검증 절차로 판정한다(`acceptance.md` 「검증 수단」, `spec.md` §5) |
| `dashboard/page.tsx` | `const API = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000'`(16행), `Link` from `next/link` 이미 import, Supabase `createClient`로 미인증 시 `/login` 리다이렉트, `/settings` 링크 존재 |
| `data/` | `portfolio.example.json`, `portfolio.edge.json`, 4개 종목의 `_market.json`·`_fundamentals.json`·`_ohlcv.json`. **`portfolio_analysis.json` 없음** |
| `data/portfolio.edge.json` | `005380`·`999999` 등 허용 목록 밖 코드를 포함 — REQ-003 검증에 그대로 쓸 수 있는 고정 입력 |
| `portfolio-team.yaml` | 저장소 루트에 존재. 세 서브에이전트(`portfolio-valuation`·`portfolio-risk`·`portfolio-allocation`) 정의는 `.claude/agents/` 아래에 있음 |

## A.2 기술 결정

아래 세 결정이 이후 구현 전체의 모양을 정한다. 되돌리기 비용이 가장 큰 순서로 적는다.

### 결정 1 — 데이터 계약과 비중 정의 (되돌리기 비용 최상)

`spec.md` §4가 확정한 파일 스키마와 응답 스키마를 따른다. 핵심은 두 가지다.

- **메타 4필드 추가**: `schema_version`·`source`·`generated_date`·`portfolio_file`. 병합 결과에는 실행일 정보가 없으므로 저장 단계에서 넣어야 한다. `as_of`만으로는 두 달 지난 데이터인지 알 수 없다.
- **비중은 allocation 하나만 노출**: 응답에서 `risk.results[].actual_weight_pct`를 제거한다(REQ-005). 화면이 두 값 중 하나를 고르게 두면 표시 로직에 정책 판단이 스며들고, 나중에 어느 쪽이 기준이었는지 추적할 수 없다. 제거 위치를 백엔드에 두는 이유가 이것이다.
- **「필수 키 집합」은 한 곳에만 정의**: `spec.md` §4의 다섯 조건이 유일한 정의다. M1의 저장 전 검사(REQ-002·REQ-004)와 M2의 읽기 시 검사(REQ-007)는 같은 술어를 구현한다. 두 마일스톤이 병렬로 진행되므로 구현 중에 서로 맞출 기회가 없고, 집합이 어긋나면 "저장은 되는데 서빙이 500"이라는 비대칭이 남는다. 검사 함수를 각자 작성하더라도 §4의 다섯 조건을 항목 단위로 옮겨 적고, 테스트 케이스를 같은 다섯 조건으로 구성한다.

이 결정이 바뀌면 파일·백엔드·화면·테스트가 전부 따라 바뀐다. 구현 착수 전에 확정되어야 한다.

### 결정 2 — 생성 시점: 오프라인 실행 (되돌리기 비용 중)

| 후보 | 판단 |
|------|------|
| **오프라인 생성 → 파일 서빙** | **채택.** 요청 경로가 파일 읽기뿐이라 응답이 즉시 나오고, Claude 사용량이 요청 수와 무관하다. `SPEC-CHART-001`이 이미 같은 구조를 쓰고 있어 패턴이 일관된다 |
| 요청 시 에이전트 실행 | 기각. 스크립트 타임아웃이 240초다. 요청 하나가 최대 4분 걸리고, Pro 플랜 사용량 한도 아래에서 방문자 수만큼 Claude 호출이 발생한다. 발표 시연 중 한도에 걸리면 화면이 비어버린다 |
| 순수 파이썬으로 재구현 | 기각. 판정 근거 텍스트(`basis`)와 수급·집중도 해석은 에이전트의 언어 판단 결과다. 수식으로 바꾸면 그 문장이 사라지고, 무엇보다 4주차 에이전트 팀 실습이라는 이 모듈의 존재 이유가 없어진다 |
| 사용자가 보유 종목 직접 입력 | 기각. 입력 화면·검증·저장소(Supabase 테이블)·사용자별 분석 실행이 모두 따라붙어 Tier M 범위를 넘는다. 고정 파일 한 개로 시작하고, 필요해지면 별도 SPEC으로 분리한다 |

### 결정 3 — 실제 분석 데이터가 없을 때의 폴백 (되돌리기 비용 하)

`data/portfolio_analysis.json` 생성은 Claude 사용량을 소모하는 **사람의 수동 단계**다. 네트워크·사용량 한도·`claude` 미설치 등으로 실행할 수 없는 환경이 있다.

`SPEC-CHART-001`의 `--sample` 선례를 따라, 스크립트에 결정론적 샘플 생성 모드를 둔다. 이 모드는 **REQ-004로 명문화된 요구사항**이며 AC-004로 판정한다 — 구현자 재량으로 남겨 두면 모든 종목을 `unknown`으로 채운 샘플도 적법해지고, 그 파일로는 M3의 수동 검증(AC-009·AC-015)을 한 화면에서 실증할 수 없다.

- `--sample`: `claude`를 실행하지 않고(서브에이전트 호출 0회) `data/portfolio.example.json`만 읽어 고정 규칙으로 §4 「필수 키 집합」을 만족하는 결과를 만들어 저장한다. `source: "sample"`을 기록한다.
- **결정론**: 같은 입력 파일과 같은 실행일로 두 번 실행하면 저장된 바이트가 같다. 난수·시각·해시 순서에 의존하지 않는다.
- **판정 값 분포**: 최소 한 종목은 `verdict`·`overall`·`action`이 모두 `unknown`이 아니고, 최소 한 종목은 `unknown`이다.
- **동일하게 적용되는 규칙**: 허용 목록 검사(REQ-003)를 에이전트 호출 경로와 똑같이 먼저 수행하고, 저장은 임시 파일 교체 방식(REQ-001), 실패 시 기존 파일 비덮어쓰기(REQ-002)를 지킨다.
- 에이전트 실행 성공 시에는 `source: "agent-team"`.
- 화면은 `source`를 읽어 샘플임을 구분 표기한다(REQ-010).

**테스트는 커밋된 파일의 `source` 값에 의존하지 않는다.** `backend/tests/test_portfolio.py`는 임시 디렉터리에 픽스처 파일을 만들고 데이터 경로를 그쪽으로 바꿔 검증한다. 커밋된 `data/portfolio_analysis.json`에 대해서는 §4 「필수 키 집합」을 만족하는지 확인하는 테스트 하나만 둔다. 이렇게 하면 실제 분석본으로 교체해도 테스트가 깨지지 않는다.

### 구현 패턴 — `SPEC-CHART-001` 계승

- 단일 파일 접근 헬퍼 `_read_portfolio_document()` 하나만 파일 시스템에 접근한다. `_read_ohlcv_document`와 같은 모양이다. 헬퍼를 하나로 모아야 "요청이 파일을 쓰지 않는다"와 "허용되지 않은 경로를 읽지 않는다"를 테스트로 증명할 수 있다(AC-007. 기존 `backend/tests/test_chart.py`가 쓰는 mock/assert 방식과 같다).
- 경로는 `DATA_DIR`(이미 `main.py`에 있는 `__file__` 기준 상수)를 재사용한다. 실행 디렉터리에 의존하는 상대 경로를 새로 만들지 않는다.
- 신규 라우트는 `main.py` **끝에 구획 주석과 함께 추가**하고 기존 함수 본문은 건드리지 않는다.

## A.3 마일스톤

### M1 — 스크립트 JSON 저장 + 데이터 파일 생성

- `scripts/orchestrate_portfolio.py`에 `--save-json <경로>`(기본 `data/portfolio_analysis.json`)와 `--sample` 추가
- 저장은 같은 디렉터리 임시 파일 기록 후 교체(REQ-001). 실패 시 기존 파일 보존 + 0이 아닌 종료 코드(REQ-002)
- 저장 전 `spec.md` §4 「필수 키 집합」 다섯 조건 검사(REQ-002). M2의 읽기 시 검사와 같은 술어여야 한다
- 입력 허용 목록 검사를 에이전트 호출 **이전에** 수행(REQ-003)
- `--sample` 결정론적 생성 규칙(REQ-004) — 에이전트 미호출, 같은 입력·같은 실행일이면 바이트 동일, 최소 1종목 정상 판정 + 최소 1종목 `unknown`
- `scripts/tests/test_orchestrate_portfolio.py` 신설 — 저장 내용, 실패 시 보존(파싱 실패 경로 + `os.replace` 직전 예외 주입 경로 양쪽), 허용 목록 거부, `--sample` 결정론 검증
- `data/portfolio_analysis.json` 생성 후 커밋
- 커버: REQ-001~REQ-004 / AC-001~AC-004

> **운영 주의.** 실제 분석 생성은 `claude -p` 호출이므로 Claude 사용량을 소모하며, 자동화할 수 없는 사람의 수동 단계다. 실행이 불가능하면 `--sample`로 생성해 커밋하고 `source: "sample"`을 문서에 명시한다. 어느 쪽이든 M2·M3는 동일하게 진행된다.

### M2 — 백엔드 엔드포인트

- `backend/app/main.py`에 구획 주석 + `PORTFOLIO_ANALYSIS_FILE` 상수 + `_read_portfolio_document()` + `GET /api/portfolio` 추가
- 응답 조립 시 `risk.results[]`의 `actual_weight_pct` 제거(REQ-005)
- 파일 부재 404(REQ-006), 파싱 실패 또는 §4 「필수 키 집합」 위반 시 500 + 일반화 메시지(REQ-007)
- `backend/tests/test_portfolio.py` 신설 — 임시 데이터 디렉터리 픽스처 기반. 스키마 위반 케이스는 §4 다섯 조건에서 뽑은 3종(최상위 키 누락 / `results` 비-list / `results` 길이 불일치)으로 구성한다
- 커버: REQ-005~REQ-008 / AC-005~AC-008

### M3 — 프론트엔드 화면 + 대시보드 링크

- `frontend/src/app/portfolio/page.tsx` 신설 — 대시보드와 동일한 Supabase 인증 처리(REQ-012), `API` 상수 관례 동일(REQ-014)
- 종목별 밸류에이션·리스크·리밸런싱 표시(REQ-009), `as_of`/`generated_date`/스냅샷 문구/샘플 표기(REQ-010), `unknown` → "판정 불가" 상태(REQ-015)
- 요청 실패 시 해당 영역만 오류 표시(REQ-011)
- `dashboard/page.tsx` 헤더에 `/portfolio` 링크 1개 추가(REQ-013, `/settings` 링크와 같은 모양)
- **`docs/weekly/WEEK_10.md`에 「`/portfolio` 화면 수동 검증 절차」 절 신설** — AC-009~AC-015와 AC-016의 대시보드 항목 각각에 대해 준비 / 실행 / 관찰 대상 / PASS 조건 네 줄. 저장소에 프론트엔드 테스트 프레임워크가 없고 도입은 범위 밖이므로(`spec.md` §5), 이 문서가 해당 AC의 유일한 판정 근거다. 요건은 `acceptance.md` 「수동 검증 절차 문서의 요건」에 있다
- 자동 보조 게이트(`npm run lint`, `npm run build`, `npx tsc --noEmit`)는 빌드·타입·린트만 보증하며 화면 동작의 PASS 근거가 아니다
- 커버: REQ-009~REQ-015 / AC-009~AC-015

### M4 — 문서 동기화 + 품질 게이트

- `docs/weekly/WEEK_10.md`에 모듈 요약과 실행 절차(스크립트 → 커밋 → 백엔드 → 화면) 기록 (M3가 쓴 수동 검증 절차 절과는 다른 절)
- 분석 결과 재생성 절차를 README 또는 주차 문서에 명시
- **`.github/workflows/ci.yml`의 "Backend 테스트" 단계를 `pytest backend/tests/ scripts/tests/ -v`로 확장.** 현재 이 단계는 `backend/tests/`만 지정하므로 `scripts/tests/`(AC-001~AC-004의 검증 파일)가 CI에서 한 번도 실행되지 않는다. 확장 전에 로컬에서 두 스위트를 1회 실행해 초록임을 확인한다. `scripts/tests/test_fetch_ohlcv.py`가 이미 실패 상태라면 확장을 보류하고 그 사실·원인·대안(M4 수동 1회 실행)을 `progress.md`에 기록한다. 이 단계 외의 CI 단계는 건드리지 않는다
- `ruff check backend/`, `npm run lint`, `npm run build`, `npx tsc --noEmit`, 백엔드·스크립트 테스트 전체 실행
- M3가 작성한 수동 검증 절차를 1회 실행하고 결과를 기록
- AC-001~AC-016 PASS/FAIL 매트릭스를 `progress.md`에 작성. 수동 판정 AC는 `docs/weekly/WEEK_10.md`의 해당 PASS 조건을 인용한다
- 커버: REQ-016 / AC-016 + 완료 정의 전체

## A.4 마일스톤별 파일 소유권

M2와 M3는 서로 다른 파일만 건드리므로 병렬로 진행할 수 있다. M1은 두 마일스톤의 입력(데이터 파일)을 만들므로 선행되어야 한다.

| 마일스톤 | 쓰기 허용 파일 | 선행 조건 |
|---|---|---|
| M1 | `scripts/orchestrate_portfolio.py`, `scripts/tests/test_orchestrate_portfolio.py`, `data/portfolio_analysis.json` | 없음 |
| M2 | `backend/app/main.py`(끝에 추가), `backend/tests/test_portfolio.py` | M1의 데이터 계약 확정 (파일 실물은 픽스처로 대체 가능) |
| M3 | `frontend/src/app/portfolio/page.tsx`(신설), `frontend/src/app/dashboard/page.tsx`(링크 1개), `docs/weekly/WEEK_10.md`의 「`/portfolio` 화면 수동 검증 절차」 절 | M2의 응답 계약 확정 |
| M4 | `docs/weekly/WEEK_10.md`(수동 검증 절차 절을 제외한 나머지), `.github/workflows/ci.yml`("Backend 테스트" 단계 한 줄), `.moai/specs/SPEC-PORTFOLIO-001/progress.md` | M1~M3 완료 |

M3와 M4가 `docs/weekly/WEEK_10.md`를 함께 쓰지만 서로 다른 절이고 M4가 M3보다 뒤이므로 충돌하지 않는다.

M2와 M3가 동시에 진행되는 경우, M3는 `spec.md` §4의 응답 스키마를 계약으로 삼고 목 응답으로 작업한다. M2 완료 후 실제 응답으로 한 번 맞춰본다.

## A.5 리스크

| 리스크 | 영향 | 완화 |
|---|---|---|
| 에이전트 출력이 §4 스키마를 벗어남 | 저장 실패 또는 화면에 빈 값. 2026-09-20 실행에서는 스키마를 지켰으나 LLM 출력이라 재현이 보장되지 않는다 | 저장 전에 §4 「필수 키 집합」을 검사하고 어긋나면 저장하지 않고 종료(REQ-002). 백엔드도 읽을 때 같은 술어로 한 번 더 검사(REQ-007). 화면은 `unknown`·결측을 정상 경로로 처리(REQ-015) |
| `scripts/tests/`가 CI 테스트 단계 밖 | AC-001~AC-004의 검증 파일이 회귀 감시에서 조용히 빠진다. M4에서 1회 실행하고 끝나면 이후 스크립트 변경이 무방비다 | M4에서 CI "Backend 테스트" 단계를 `pytest backend/tests/ scripts/tests/ -v`로 확장한다. 대상 스크립트가 표준 라이브러리만 쓰므로 CI 의존성 추가는 필요 없다. 확장이 불가능하면 그 사유와 수동 게이트 한계를 `progress.md`에 명시한다 |
| 화면 AC의 자동 검증 수단 부재 | AC-009~AC-015가 "눈으로 봤다"로 흘러가 판정 근거가 남지 않는다 | 수동 검증 절차를 M3 산출물로 고정하고(`docs/weekly/WEEK_10.md`), AC별 PASS 조건을 이진 서술로 적는다. `progress.md` 매트릭스가 그 조건을 인용하지 않은 항목은 PASS로 보지 않는다(`acceptance.md` 품질 게이트) |
| `--sample`이 실질적인 주 데이터 경로가 됨 | `claude -p` 실행이 불가능하면 커밋되는 데이터가 전부 샘플이다. 생성 규칙이 느슨하면 모든 종목이 `unknown`으로 채워져 AC-009와 AC-015를 한 화면에서 실증할 수 없다 | REQ-004가 결정론과 판정 값 분포(최소 1종목 정상 판정 + 최소 1종목 `unknown`)를 요구사항으로 고정하고 AC-004가 이를 검사한다 |
| `as_of`가 실행일보다 한참 과거 | 사용자가 두 달 전 보유 기준 데이터를 최신으로 오해 | `generated_date`를 별도 저장하고 두 날짜를 함께 표시 + 스냅샷 문구(REQ-010) |
| Windows/WSL 경로·인코딩 문제 | 이 저장소에서 이미 두 번 발생했다 — `requirements.txt` 한글 주석의 cp949 디코딩 실패, `.env` 상대 경로가 실행 디렉터리에 의존해 503 | 새 경로는 전부 `__file__` 기준(`DATA_DIR` 재사용). 파일 입출력에 `encoding="utf-8"` 명시. 스크립트는 기존 `sys.stdout.reconfigure` 처리를 유지 |
| `ruff check backend/` 게이트 | CI가 루트 `ruff.toml`로 검사한다. 신규 코드의 줄 길이·미사용 import로 파이프라인이 멈춘다 | 커밋 전 `ruff check backend/ scripts/` 로컬 실행. `main.py` 기존 구간과 같은 스타일 유지 |
| `npm run lint` / 타입 검사 게이트 | 신규 페이지의 미사용 변수·`any`·훅 의존성 경고 | 대시보드 페이지의 구조(훅 순서, 타입 선언 위치)를 그대로 따른다. 커밋 전 `npm run lint` + `npx tsc --noEmit` |
| 분석 재생성이 수동 단계 | 데이터가 오래되어도 아무도 모른다 | `generated_date`를 화면에 항상 노출. 자동 스케줄링은 의도적으로 범위 밖(`spec.md` §5) |
| 대시보드 파일 동시 수정 | M3가 `dashboard/page.tsx`를 건드리므로 다른 SPEC 작업과 충돌 가능 | 변경을 헤더 링크 1줄로 한정. 차트·테이블·Notion 버튼 구간은 손대지 않는다(A.6 PRESERVE) |

## A.6 PRESERVE 목록 (수정 금지)

| 경로 | 사유 |
|------|------|
| `backend/app/main.py`의 기존 라우트 전체 | REQ-016 — 신규 라우트만 끝에 추가, 기존 함수 본문 수정 금지 |
| `backend/app/indicators.py`, `backend/app/auth.py`, `backend/app/config.py` | 본 SPEC 범위 밖 |
| `dashboard/page.tsx`의 `MOCK_STOCKS`·`MOCK_NEWS`·`StockChart` 구간·이슈 섹션·`saveToNotion` | REQ-016 — 헤더 링크 1개 추가(REQ-013) 외 수정 금지. `MOCK_STOCKS` 제거는 `SPEC-API-001` 소관 |
| `.github/workflows/ci.yml`의 "Backend 테스트" 단계를 제외한 모든 단계 | M4가 고치는 것은 테스트 경로 한 줄뿐이다. 린트·빌드·취약점 스캔 단계와 `continue-on-error` 설정은 손대지 않는다 |
| `frontend/package.json` | 프론트엔드 테스트 프레임워크 도입은 범위 밖(`spec.md` §5). 의존성 추가 금지 |
| `scripts/orchestrate_portfolio.py`의 `render_html`·`--save` 동작 | 기존 HTML 리포트 기능은 그대로 둔다. JSON 저장은 별도 옵션으로 추가 |
| `.claude/agents/portfolio-*.md`, `portfolio-team.yaml` | 분석 로직 변경은 범위 밖(`spec.md` §5) |
| `data/*_market.json`, `data/*_fundamentals.json`, `data/*_ohlcv.json`, `data/portfolio.example.json` | 읽기 전용. 본 SPEC은 `portfolio_analysis.json`만 새로 만든다 |
| `.moai/specs/SPEC-API-001/`, `.moai/specs/SPEC-CHART-001/` | 다른 SPEC의 산출물 |
| `.moai/state/`, `.moai/cache/`, `.moai/logs/` | 런타임 관리 파일 |

## A.7 신규 파일 목록

```
data/portfolio_analysis.json                    분석 결과 (M1에서 생성·커밋)
scripts/tests/test_orchestrate_portfolio.py     스크립트 검증 (AC-001~AC-004)
backend/tests/test_portfolio.py                 엔드포인트 검증 (AC-005~AC-008)
frontend/src/app/portfolio/page.tsx             포트폴리오 화면
```

수정 파일: `scripts/orchestrate_portfolio.py`(옵션 2개 + 저장 함수 + 허용 목록 검사 + 샘플 생성 규칙), `backend/app/main.py`(구획 하나 추가), `frontend/src/app/dashboard/page.tsx`(헤더 링크 1줄), `docs/weekly/WEEK_10.md`(M3의 수동 검증 절차 절 + M4의 모듈 요약·재생성 절차), `.github/workflows/ci.yml`("Backend 테스트" 단계 한 줄).

## A.8 MX 태그 계획

| 대상 | 태그 | 내용 |
|---|---|---|
| `_read_portfolio_document()` (`main.py`) | `@MX:ANCHOR` | 파일 시스템 접근 단일 지점. "요청 경로가 `data/`에 쓰지 않는다"(REQ-008)와 파싱·스키마 실패 처리(REQ-007)가 이 함수 하나에 걸려 있으므로, 우회 접근 경로가 생기면 두 요구사항이 동시에 무너진다 |
| 응답 조립부의 비중 처리 (`main.py`) | `@MX:NOTE` | `risk.results[].actual_weight_pct`를 제거하는 이유 — 분모가 allocation과 달라 같은 종목에서 다른 값이 나온다(`spec.md` §1.4). 주석이 없으면 "필드가 빠졌다"는 결함으로 오인되어 되살아난다 |
| `--save-json` 저장 함수 (`orchestrate_portfolio.py`) | `@MX:NOTE` | 임시 파일 기록 후 교체하는 이유 — 실패 시 기존 파일 보존(REQ-001·REQ-002). AC-002가 `os.replace` 직전 예외 주입으로 이 경로를 실제로 검사한다 |
| `--sample` 생성 규칙 (`orchestrate_portfolio.py`) | `@MX:NOTE` | 결정론과 판정 값 분포가 요구사항이라는 사실(REQ-004) — 난수나 실행 시각을 끼워 넣으면 AC-004가 깨지고, 모든 종목을 `unknown`으로 채우면 화면 수동 검증이 성립하지 않는다 |
| `generated_date` / `as_of` 병기 지점 (`portfolio/page.tsx`) | `@MX:NOTE` | 두 날짜가 다른 값이라는 사실과 그래서 둘 다 표시한다는 의도 |

태그 설명 언어는 `.moai/config/sections/language.yaml`의 `code_comments` 설정을 따른다.

## A.9 미해결 사항

- **실제 분석 실행 가능 여부 미확인.** `claude -p` 호출 성공 여부는 M1에서 처음 검증한다. 실패 시 `--sample`로 진행하고 `source: "sample"`을 문서에 명시한다(A.2 결정 3). `--sample`의 동작은 REQ-004·AC-004로 고정되어 있으므로, 이 경로로 빠지더라도 데이터 형태와 화면 검증 가능성은 보장된다.
- **`scripts/tests/`의 현재 통과 여부 미확인.** `scripts/tests/test_fetch_ohlcv.py`가 지금 초록인지는 실행으로 확인하지 못했다(이 환경에 `pytest` 미설치). 확인된 사실은 대상 스크립트와 테스트의 import가 표준 라이브러리 + `pytest`뿐이라는 것까지다. M4의 CI 확장은 로컬 실행으로 초록을 확인한 뒤에 적용한다.
- **커버리지 측정 범위.** `SPEC-CHART-001` M6에서 "신규 코드 기준"으로 판정한 선례가 있다. 본 SPEC도 신규 코드 기준을 적용하되, 실측 후 M4에서 확정한다.
