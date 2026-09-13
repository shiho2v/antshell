---
id: SPEC-CHART-001
title: "주가 차트와 기술지표 모듈 — 구현 계획"
version: "0.1.0"
status: in-progress
created: 2026-09-12
updated: 2026-09-13
tier: M
---

# SPEC-CHART-001 구현 계획 (Plan)

## A.1 현재 상태 (조사 결과)

| 항목 | 상태 |
|------|------|
| `backend/app/main.py` | 125줄, 라우트 3개 (`/health`, `/api/report/notion`, `/api/github/issues`) |
| `backend/requirements.txt` | `fastapi`, `uvicorn[standard]`, `python-jose[cryptography]`, `httpx`, `python-dotenv` |
| `backend/tests/` | **없음** — 테스트 디렉터리 자체가 부재 |
| `frontend/src/app/dashboard/page.tsx` | 224줄, `MOCK_STOCKS` 하드코딩 (16행), `API` 상수 (14행) |
| `frontend` 의존성 | `next@14.2.5`, `react@18`, `@supabase/*`, `zustand` — **차트 라이브러리 없음** |
| `data/*_ohlcv.json` | **없음** — 스냅샷(`*_market.json`)만 존재 |
| `scripts/` | `orchestrate_portfolio.py`, `orchestrate_stock_agents.py` — 수집 스크립트 없음 |

## A.2 기술 스택 결정

### 차트 라이브러리: `lightweight-charts`

| 후보 | 판단 |
|------|------|
| **`lightweight-charts`** (TradingView) | **채택.** 캔들스틱·거래량·라인 오버레이가 내장. 약 45KB로 경량. 명령형 API라 React 래퍼 없이 `useEffect`에서 직접 제어 가능 |
| `recharts` | 기각. React 친화적이지만 캔들스틱 네이티브 미지원 — 커스텀 셰이프로 직접 구현해야 함 |
| `chart.js` + 플러그인 | 기각. 금융 차트는 별도 플러그인 의존, 번들 크기 증가 |

프론트엔드 의존성 **1개 추가**(`lightweight-charts`)가 발생한다. 백엔드는 REQ-009에 따라 **0개 추가**다.

### 지표 계산: 표준 라이브러리 직접 구현

`pandas`/`numpy` 없이 순수 파이썬으로 구현한다 (REQ-009). 4개 지표 모두 단순 순회로 계산 가능하다.

| 지표 | 계산 방식 |
|------|-----------|
| SMA(n) | 길이 n 슬라이딩 윈도우 평균. 앞 n-1개는 `null` |
| EMA(n) | 초기값 = 앞 n개의 SMA, 이후 `EMA = 종가×k + 이전EMA×(1-k)`, `k = 2/(n+1)` |
| RSI(14) | Wilder 평활. `RS = 평균상승/평균하락`, `RSI = 100 - 100/(1+RS)`. 평균하락 0이면 RSI = 100 |
| MACD(12,26,9) | `MACD = EMA12 - EMA26`, `Signal = MACD의 EMA9`, `Histogram = MACD - Signal` |

### 수집 스크립트: pykrx + 샘플 폴백

`scripts/fetch_ohlcv.py`는 두 모드를 갖는다.

- 기본 모드: `pykrx.stock.get_market_ohlcv(시작일, 종료일, 종목코드)` 호출 → `data/{code}_ohlcv.json` 저장
- `--sample` 모드: 고정 시드 기반 결정론적 OHLCV 생성 → 동일 스키마로 저장, `source: "sample"` 표기

`pykrx`는 **개발 도구 의존성**이며 `backend/requirements.txt`가 아니라 `scripts/requirements.txt`(신설)에 둔다. 백엔드 런타임은 pykrx를 import하지 않는다 (REQ-007, REQ-009).

## A.3 마일스톤

### M1 — 수집 스크립트 + 데이터 생성
- `scripts/fetch_ohlcv.py` 신설 (pykrx 모드 + `--sample` 모드)
- `scripts/requirements.txt` 신설 (`pykrx`)
- 4개 종목 `data/{code}_ohlcv.json` 생성 후 커밋
- 커버: REQ-001, REQ-002, REQ-003 / AC-001, AC-002

### M2 — 지표 계산 모듈 + 단위 테스트
- `backend/app/indicators.py` 신설 — `sma`, `ema`, `rsi`, `macd` 순수 함수
- `backend/tests/__init__.py`, `backend/tests/test_indicators.py` 신설
- **TDD**: 손으로 검증 가능한 고정 입력에 대한 실패 테스트를 먼저 작성 (AC-016)
- 커버: REQ-008(수치), REQ-009, REQ-010 / AC-008, AC-009, AC-016

### M3 — 백엔드 엔드포인트
- `backend/app/main.py`에 `GET /api/stocks/{code}/ohlcv`, `GET /api/stocks/{code}/indicators` 추가
- 허용 목록 상수 + 경로 조작 방지 (허용 목록 검사를 파일 접근보다 먼저)
- `backend/tests/test_chart.py` 신설
- 커버: REQ-004, REQ-005, REQ-006, REQ-007, REQ-008(형태) / AC-003~AC-007

### M4 — 프론트엔드 차트 컴포넌트
- `npm install lightweight-charts`
- `frontend/src/components/StockChart.tsx` 신설 — 캔들스틱 + SMA 3선 + 거래량 서브차트
- 로딩·오류·데이터 기간 표시
- 커버: REQ-012, REQ-014, REQ-015 / AC-011, AC-013, AC-014

### M5 — 대시보드 연동
- `dashboard/page.tsx`에 종목 선택 상태 추가, 선택 시 `StockChart` 렌더링
- 기존 `MOCK_STOCKS` 테이블·GitHub 이슈·Notion 저장 버튼은 **건드리지 않음**
- 커버: REQ-011, REQ-013, REQ-016 / AC-010, AC-012, AC-015

### M6 — 품질 게이트
- 전체 테스트 통과 + 커버리지 측정
- AC-001~AC-016 PASS/FAIL 매트릭스 작성

## A.4 커버리지 리스크 (사전 식별)

`/moai run` → `/moai sync` 전환 조건은 **테스트 통과 + 커버리지 85% 이상**이다. 현재 `backend/tests/`가 존재하지 않으므로 기준선이 0%다.

완화책:
- M2를 **TDD로 먼저** 수행한다. `indicators.py`는 순수 함수라 100%에 가까운 커버리지를 얻기 쉽다.
- M3의 엔드포인트도 FastAPI `TestClient`로 전 분기(200/404×2)를 덮는다.
- 커버리지 측정 범위는 **신규 모듈 기준**으로 잡는다. 기존 `main.py`의 미테스트 라우트(`/api/report/notion` 등)까지 한 번에 85%를 요구하면 본 SPEC 범위를 넘는다. 측정 대상이 전체 `backend/`인지 신규 모듈인지는 M6에서 확인 후 조정한다.
- `pytest`, `pytest-cov`는 개발 의존성으로 `backend/requirements-dev.txt`(신설)에 둔다 — 런타임 의존성이 아니므로 REQ-009에 저촉되지 않는다.

## A.5 PRESERVE 목록 (수정 금지)

| 경로 | 사유 |
|------|------|
| `backend/app/main.py`의 기존 3개 라우트 | REQ-016 — 신규 라우트만 추가, 기존 함수 본문 수정 금지 |
| `backend/app/auth.py` | 본 SPEC 범위 밖 |
| `dashboard/page.tsx`의 `MOCK_STOCKS`·`MOCK_NEWS`·이슈 섹션·`saveToNotion` | REQ-016 — `SPEC-API-001` 소관. 본 SPEC은 차트 영역만 추가 |
| `data/*_market.json`, `data/*_fundamentals.json` | 읽지도 쓰지도 않음 |
| `.moai/specs/SPEC-API-001/` | 다른 SPEC의 산출물 |
| `.moai/state/`, `.moai/cache/`, `.moai/logs/` | 런타임 관리 파일 |

## A.6 신규 파일 목록

```
scripts/fetch_ohlcv.py            수집 스크립트
scripts/requirements.txt          pykrx, setuptools<82 (개발 도구)
scripts/tests/test_fetch_ohlcv.py 수집 스크립트 검증 (AC-001, AC-002)
data/005930_ohlcv.json            OHLCV 데이터 4종
data/000660_ohlcv.json
data/009150_ohlcv.json
data/008490_ohlcv.json
backend/app/indicators.py         지표 계산 순수 함수
backend/requirements-dev.txt      pytest, pytest-cov, httpx
backend/tests/__init__.py
backend/tests/test_indicators.py  지표 수치 검증
backend/tests/test_chart.py       엔드포인트 검증
frontend/src/components/StockChart.tsx   차트 컴포넌트
```

> M1 실측 반영: `scripts/tests/test_fetch_ohlcv.py`가 목록에 추가됐다. AC-002(실패 시
> 기존 파일 보존)는 자동 테스트로 검증되어야 하는데 최초 계획의 파일 목록에는
> 수집 스크립트용 테스트가 빠져 있었다. `backend/requirements-dev.txt`도 M2 예정이었으나
> M1 검증에 pytest가 필요해 앞당겨 신설했다.

수정 파일: `backend/app/main.py`(라우트 2개 추가), `frontend/src/app/dashboard/page.tsx`(선택 상태 + 차트 삽입), `frontend/package.json`(의존성 1개).

## A.7 미해결 사항

- **pykrx 실제 동작 여부 미확인.** 설치·네트워크·KRX 응답을 M1에서 처음 검증한다. 실패 시 `--sample` 모드로 진행하고 `source: "sample"`을 문서에 명시한다. 발표 시연은 샘플 데이터로도 동일하게 동작한다.
- **커버리지 측정 범위**(전체 backend vs 신규 모듈)는 M6에서 실측 후 결정한다 (A.4 참고).
