---
id: SPEC-CHART-001
title: "주가 차트와 기술지표 모듈 — 인수 기준"
version: "0.1.0"
status: in-progress
created: 2026-09-12
updated: 2026-09-13
tier: M
---

# SPEC-CHART-001 인수 기준 (Acceptance Criteria)

> Tier M 산출물. `spec.md` §3은 본 문서를 가리키는 포인터다.
> REQ-001~REQ-016 전체가 아래 AC로 커버된다 (트레이서빌리티 갭 없음).

## 인수 기준 목록 (Given-When-Then)

**AC-001**: Given 수집 스크립트를 4개 허용 코드에 대해 실행했을 때, When 생성된 `data/{code}_ohlcv.json`을 검사하면, Then 파일이 정확히 4개 생성되고 각 파일의 `records` 배열의 모든 원소가 `date`·`open`·`high`·`low`·`close`·`volume` 6개 필드를 가지며 `date` 오름차순으로 정렬되어 있다. (REQ-001, REQ-002)

**AC-002**: Given `data/005930_ohlcv.json`이 이미 존재하는 상태에서 데이터 조회가 실패하도록 강제했을 때, When 수집 스크립트를 실행하면, Then 종료 코드가 0이 아니고 기존 파일의 내용(바이트)이 실행 전과 동일하다. (REQ-003)

**AC-003**: Given `data/005930_ohlcv.json`이 존재할 때, When 클라이언트가 `GET /api/stocks/005930/ohlcv`를 호출하면, Then 응답은 `200`이며 본문은 `stock_code`·`source`·`fetched_date`·`records` 키를 가진 객체이고, `records`는 길이 1 이상의 일별 OHLCV 레코드 배열이다. (REQ-004)

> *AC-003 문구 조정 (M3 구현 중)*: 최초 문구는 "본문은 배열"이었으나, 그 형태로는 `spec.md` §4가
> 요구하는 `source`(`pykrx` / `sample` 구분)와 `fetched_date`를 응답에 실을 수 없다. 파일 데이터
> 계약과 동일한 객체 형태로 맞추고 문구를 수정했다. 검증 강도는 동일하다.

**AC-004**: Given 코드 `005380`(4개 허용 목록 외)이 주어졌을 때, When 클라이언트가 `GET /api/stocks/005380/ohlcv` 및 `GET /api/stocks/005380/indicators`를 호출하면, Then 두 응답 모두 `404`이며, 파일시스템 접근 함수가 호출되지 않았음을 mock으로 검증할 수 있다. (REQ-005)

**AC-005**: Given 허용 목록에 포함된 코드(예: `009150`)에 대해 `data/009150_ohlcv.json`이 디스크에 없을 때, When 클라이언트가 `GET /api/stocks/009150/ohlcv`를 호출하면, Then 응답은 `404`이다. (AC-004와 구분: AC-004는 허용 목록 밖의 코드, AC-005는 허용 목록 안이지만 파일이 없는 코드.) (REQ-006)

**AC-006**: Given 이 SPEC의 임의 엔드포인트가 호출될 때, When 요청 처리가 완료되면, Then pykrx/외부 네트워크 호출(`pykrx`·`requests`·`urllib`·`httpx`)이 발생하지 않고 `data/*_ohlcv.json`에 쓰기가 발생하지 않는다 — `backend/tests/test_chart.py`에서 mock/assert로 검증한다. (REQ-007)

**AC-007**: Given 유효한 OHLCV 데이터가 있을 때, When 클라이언트가 `GET /api/stocks/005930/indicators`를 호출하면, Then 응답 본문에 `sma_5`·`sma_20`·`sma_60`·`ema_12`·`ema_26`·`rsi_14`·`macd`·`macd_signal`·`macd_histogram` 키가 모두 존재하고 각 값은 OHLCV 레코드 수와 동일한 길이의 배열이다. (REQ-008)

**AC-008**: Given 백엔드 소스를 검사할 때, When 지표 계산 모듈의 import 구문과 `backend/requirements.txt`를 확인하면, Then `pandas`·`numpy`·`talib` 등 신규 서드파티 런타임 의존성이 추가되지 않았다. (REQ-009)

**AC-009**: Given OHLCV 레코드가 N개일 때, When 지표 응답을 검사하면, Then `sma_60` 배열의 앞 59개 원소는 `null`이고 60번째 원소부터 숫자이며, 동일 규칙이 `sma_5`(앞 4개)·`sma_20`(앞 19개)·`rsi_14`(앞 14개)에 적용된다. (REQ-010)

**AC-010**: Given 대시보드가 로드되고 보유 종목 테이블이 렌더링되었을 때, When 사용자가 특정 종목 행을 선택하면, Then 해당 종목 코드의 캔들스틱 차트가 화면에 렌더링되고 차트가 표시하는 종목 코드가 선택한 코드와 일치한다. (REQ-011)

**AC-011**: Given 캔들스틱 차트가 렌더링되었을 때, When 차트 구성 요소를 검사하면, Then SMA(5, 20, 60) 3개 라인 시리즈와 거래량 서브차트가 함께 존재한다. (REQ-012)

**AC-012**: Given `NEXT_PUBLIC_API_URL` 환경 변수가 설정되어 있지 않을 때, When 프론트엔드가 OHLCV·지표 엔드포인트를 호출하면, Then 기존 `API` 상수(`page.tsx:14`)와 동일하게 기본값 `http://localhost:8000`으로 호출된다. (REQ-013)

**AC-013**: Given OHLCV 요청이 실패(네트워크 오류 또는 404)하도록 강제했을 때, When 대시보드가 렌더링되면, Then 차트 영역에 오류 상태가 표시되고 보유 종목 테이블·GitHub 이슈 섹션은 정상 렌더링되며 페이지가 예외로 중단되지 않는다. (REQ-014)

**AC-014**: Given 차트가 정상 렌더링되었을 때, When 차트 주변 DOM을 조회하면, Then 데이터 기간(최초 거래일과 최종 거래일)이 텍스트로 조회 가능하다. (REQ-015)

**AC-015**: Given 본 SPEC의 변경이 모두 적용된 상태에서, When 기존 라우트(`GET /health`, `POST /api/report/notion`, `GET /api/github/issues`)를 호출하고 대시보드를 렌더링하면, Then 세 라우트의 응답이 변경 전과 동일하고 보유 종목 테이블·GitHub 이슈 섹션·Notion 저장 버튼이 정상 동작한다. (REQ-016)

**AC-016** *(지표 수치 정확성)*: Given 종가가 `[1, 2, 3, 4, 5, 6]`인 알려진 입력이 주어졌을 때, When SMA(5)를 계산하면, Then 결과는 `[null, null, null, null, 3.0, 4.0]`이다. 동일하게 EMA·RSI·MACD도 손으로 검증 가능한 고정 입력에 대해 기대값과 일치한다. (REQ-008 수치 검증 — AC-007은 응답 형태만 검증하므로 별도 필요)

## 엣지 케이스 (Edge Cases)

- **데이터가 지표 최소 기간보다 짧은 경우** — 예: 레코드 30개인데 SMA-60 요청. 전 구간 `null` 배열을 반환하며 오류가 아니다 (AC-009의 일반화).
- **RSI 계산 중 하락분 합계가 0인 구간** — 0 나눗셈이 발생하지 않아야 하며, 관례에 따라 RSI = 100으로 처리한다.
- **`source: "sample"` 파일로 동작하는 경우** — 엔드포인트 동작은 `"pykrx"` 파일과 동일해야 한다. 테스트는 샘플 데이터로 수행되므로 이 동등성이 전제된다.
- **거래 정지 등으로 특정 날짜가 누락된 경우** — 날짜 연속성을 가정하지 않고 레코드 인덱스 기준으로 지표를 계산한다.

## 품질 게이트 기준 (Quality Gate Criteria)

- AC-001~AC-016 전체가 자동화된 테스트로 검증 가능해야 한다.
  - 백엔드: `backend/tests/test_chart.py` (신설)
  - 지표 수치: `backend/tests/test_indicators.py` (신설)
  - 프론트엔드: 컴포넌트 테스트 또는 문서화된 수동 검증 절차
- 신규 백엔드 모듈(엔드포인트 + 지표 계산)은 커버리지 측정 대상에 포함되어야 한다.
- 기존 3개 라우트(`/health`, `/api/report/notion`, `/api/github/issues`)에 회귀가 없어야 한다 (AC-015).

## 완료 정의 (Definition of Done)

- [ ] REQ-001~REQ-016이 모두 구현되고 각 REQ에 매핑된 AC가 PASS
- [ ] `scripts/fetch_ohlcv.py` 신설 및 4개 종목 `data/{code}_ohlcv.json` 생성·커밋
- [ ] `backend/tests/test_chart.py`, `backend/tests/test_indicators.py` 신설 및 통과
- [ ] `backend/requirements.txt`에 신규 런타임 의존성 추가 없음 (AC-008)
- [ ] 대시보드에서 종목 선택 → 캔들스틱 + SMA 오버레이 + 거래량 표시 동작
- [ ] 기존 3개 라우트 및 대시보드 기존 영역 회귀 없음 (AC-015)
- [ ] Out of Scope 항목(`spec.md` §5) 중 어떤 것도 구현 범위에 포함되지 않음
