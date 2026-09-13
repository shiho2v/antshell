---
id: SPEC-CHART-001
title: "주가 차트와 기술지표 모듈 (캔들스틱 + SMA/EMA/RSI/MACD)"
version: "0.1.0"
status: in-progress
created: 2026-09-12
updated: 2026-09-13
author: 어지수
priority: P1
phase: "v1.0.0"
module: "backend/app, frontend/src/app/dashboard, scripts"
lifecycle: spec-anchored
tags: "backend, frontend, chart, indicator, fastapi, nextjs, pykrx"
tier: M
---

## HISTORY

| 버전 | 날짜 | 작성자 | 변경 내용 |
|------|------|--------|-----------|
| 0.1.0 | 2026-09-12 | 어지수 | 최초 작성 — 주가 차트·기술지표 모듈 SPEC 초안 (Tier M). 저장소에 일별 OHLCV 시계열이 부재함을 확인하고, 오프라인 수집 스크립트 + 파일 서빙 구조를 채택. `SPEC-API-001`이 미구현(`status: draft`, `/api/stocks` 부재) 상태임을 확인하여 `depends_on`을 선언하지 않고 독립 실행 가능하도록 범위를 조정 |

---

## 1. 개요 (Overview)

본 SPEC은 대시보드에 **캔들스틱 차트와 기술지표**를 추가한다.

### 1.0 선행 SPEC과의 관계

8주차 `SPEC-API-001`(백엔드 API ↔ 대시보드 실데이터 연동)은 현재 `status: draft`이며 **구현되지 않았다** — `backend/app/main.py`에 `/api/stocks` 라우트가 없고, `frontend/src/app/dashboard/page.tsx`는 여전히 `MOCK_STOCKS` 하드코딩 배열을 사용한다.

따라서 본 SPEC은 `depends_on`을 선언하지 않고 **독립적으로 실행 가능**하도록 범위를 잡는다. 차트 엔드포인트(`/api/stocks/{code}/ohlcv`, `/api/stocks/{code}/indicators`)는 `SPEC-API-001`의 `/api/stocks`와 경로가 겹치지 않으며, 종목 허용 목록과 `API` 상수는 각각 독립적으로 정의·재사용한다. `SPEC-API-001`이 나중에 구현되더라도 충돌하지 않는다.

### 1.1 확인된 데이터 공백

작업 착수 전 저장소를 조사한 결과, **일별 OHLCV 시계열 데이터가 존재하지 않는다.**

```json
// data/005930_market.json — 시계열이 아니라 특정 시점 스냅샷 1건
{ "stock_code": "005930", "as_of": "2026-07-10", "current_price": 285000,
  "high_52w": 374500, "last_volume": 19919725, "avg_volume_60d": 30627975, ... }
```

캔들스틱, SMA/EMA, RSI, MACD는 **모두 일별 시계열을 입력으로 요구**하므로, 위 스냅샷만으로는 어느 것도 계산할 수 없다. `source` 필드는 `pykrx`를 가리키지만 수집 코드는 저장소에 없고, `backend/requirements.txt`에도 `pykrx`·`pandas`가 없다.

### 1.2 설계 결정

`SPEC-API-001` REQ-008이 문서로 확립한 **"요청 경로에서 데이터 수집을 트리거하지 않는다"** 원칙을 그대로 계승한다 (해당 SPEC은 미구현이지만 설계 원칙 자체는 유효하다). 따라서:

| 계층 | 책임 |
|------|------|
| 수집 (오프라인) | `scripts/fetch_ohlcv.py` 가 pykrx로 일별 OHLCV를 받아 `data/{code}_ohlcv.json` 으로 저장. 저장소에 커밋 |
| 서빙 | 백엔드는 커밋된 파일만 읽어 응답. 네트워크 호출 없음 |
| 계산 | 지표는 백엔드가 표준 라이브러리로 계산. 신규 런타임 의존성 없음 |
| 표시 | 프론트엔드는 캔들스틱 + 지표 오버레이 렌더링 |

수집 스크립트는 pykrx를 사용할 수 없는 환경(네트워크 차단, 미설치)을 위해 결정론적 샘플 데이터 생성 모드를 함께 제공한다. 이는 개발·테스트·발표 시연을 외부 의존성 없이 재현 가능하게 만들기 위한 것이며, 생성된 파일에는 샘플 여부를 나타내는 메타데이터가 포함된다 (상세: `plan.md`).

### 1.3 종목 범위

대시보드가 현재 표시하는 4개 종목(`005930` 삼성전자, `000660` SK하이닉스, `009150` 삼성전기, `008490` 서흥)으로 한정한다. 이 4개는 `data/{code}_market.json`·`{code}_fundamentals.json`이 이미 존재하는 종목과 일치한다. 종목 범위 확장은 본 SPEC의 대상이 아니다.

## 2. 요구사항 (GEARS)

### 데이터 수집 — 오프라인 스크립트

**REQ-001** [Ubiquitous] 수집 스크립트는 사전에 정의된 4개 종목 코드(`005930`, `000660`, `009150`, `008490`)에 대해서만 OHLCV를 수집한다.

**REQ-002** [Ubiquitous] 수집 스크립트는 결과를 `data/{code}_ohlcv.json`에 저장하며, 각 일별 레코드는 `date`, `open`, `high`, `low`, `close`, `volume` 필드를 갖는다.

**REQ-003** [Event-driven] **When** 수집 스크립트가 데이터 조회에 실패하면, 기존 `data/{code}_ohlcv.json` 파일을 덮어쓰지 않고 0이 아닌 종료 코드로 종료한다.

### 백엔드 — OHLCV 서빙

**REQ-004** [Event-driven] **When** 클라이언트가 `GET /api/stocks/{code}/ohlcv`를 요청하고 해당 코드가 4개 허용 목록에 포함되며 `data/{code}_ohlcv.json`이 존재하면, 백엔드는 `200`과 함께 일별 OHLCV 레코드 배열을 응답한다.

**REQ-005** [Event-driven] **When** 클라이언트가 4개 허용 코드 목록에 없는 `code`로 OHLCV 또는 지표 엔드포인트를 요청하면, 백엔드는 파일시스템의 임의 경로를 조회하지 않고 즉시 `404`를 반환한다. (경로 조작/디렉터리 탐색 방지)

**REQ-006** [Event-driven] **When** 허용 목록에 포함된 코드이지만 `data/{code}_ohlcv.json`이 존재하지 않으면, 백엔드는 `404`를 반환한다.

**REQ-007** [Unwanted] 백엔드는 이 SPEC의 어떤 엔드포인트 호출로도 pykrx/외부 API 데이터 수집이나 `data/*_ohlcv.json` 파일 생성을 트리거하지 않는다.

### 백엔드 — 지표 계산

**REQ-008** [Event-driven] **When** 클라이언트가 `GET /api/stocks/{code}/indicators`를 요청하면, 백엔드는 해당 종목의 OHLCV로부터 SMA(5, 20, 60), EMA(12, 26), RSI(14), MACD(12, 26, 9)를 계산하여 응답한다.

**REQ-009** [Ubiquitous] 지표 계산은 파이썬 표준 라이브러리만으로 수행하며, `backend/requirements.txt`에 `pandas`·`numpy` 등 신규 런타임 의존성을 추가하지 않는다.

**REQ-010** [State-driven] **While** 특정 지표가 요구하는 최소 관측 기간(예: SMA-60은 60거래일)을 데이터가 충족하지 못하는 구간 동안, 백엔드는 해당 구간의 지표 값을 `null`로 응답한다.

### 프론트엔드 — 차트 표시

**REQ-011** [Event-driven] **When** 사용자가 대시보드 보유 종목 테이블에서 특정 종목을 선택하면, 프론트엔드는 해당 종목의 일별 캔들스틱 차트를 표시한다.

**REQ-012** [Event-driven] **When** 캔들스틱 차트가 렌더링되면, 프론트엔드는 SMA(5, 20, 60) 이동평균선 오버레이와 거래량 서브차트를 함께 표시한다.

**REQ-013** [Where] 프론트엔드는 기존 `NEXT_PUBLIC_API_URL` 환경 변수(설정 시) 또는 기본값 `http://localhost:8000`을 그대로 사용하여 신규 엔드포인트를 호출한다.

**REQ-014** [Event-driven] **When** OHLCV 또는 지표 요청이 실패(네트워크 오류, 4xx, 5xx)하면, 프론트엔드는 차트 영역에만 오류 상태를 표시하고 대시보드의 나머지 영역 렌더링을 중단하지 않는다.

**REQ-015** [Ubiquitous] 프론트엔드는 차트에 데이터 기간(최초 거래일 ~ 최종 거래일)을 표시하여, 실시간 시세가 아니라 사전 수집된 스냅샷임을 사용자에게 알린다.

### 기존 기능 호환성

**REQ-016** [Ubiquitous] 기존 라우트 `GET /health`, `POST /api/report/notion`, `GET /api/github/issues`의 동작과 대시보드의 기존 영역(보유 종목 테이블, GitHub 이슈 섹션, Notion 저장 버튼)은 변경되지 않는다.

## 3. 인수 기준 (Acceptance Criteria)

인수 기준은 `.moai/specs/SPEC-CHART-001/acceptance.md` 참고 (Tier M).

## 4. 데이터 계약 (구현 아님)

### `data/{code}_ohlcv.json`

```
{
  "stock_code": "005930",
  "source": "pykrx" | "sample",
  "fetched_date": "YYYY-MM-DD",
  "records": [
    { "date": "YYYY-MM-DD", "open": int, "high": int,
      "low": int, "close": int, "volume": int }
  ]
}
```

- `records`는 `date` 오름차순으로 정렬된다.
- `source`가 `"sample"`인 파일은 실제 시세가 아니며, 프론트엔드·문서에서 이를 구분해 표기할 수 있어야 한다.

### 기존 파일과의 관계

- `data/{code}_market.json`: 본 SPEC은 이 파일을 **읽지 않는다**. 스냅샷 지표(52주 최고가 대비, 수급)는 `SPEC-API-001`의 영역이다.
- `data/{code}_fundamentals.json`: 본 SPEC의 범위 밖(재무 데이터).

## 5. 제외 범위 (Out of Scope)

### Out of Scope — 실시간 시세
- 실시간/스트리밍 시세, WebSocket 갱신, 폴링 기반 자동 새로고침. 본 SPEC은 사전 수집된 일별 스냅샷만 표시한다.

### Out of Scope — 종목 범위 확장
- 4개 허용 종목을 넘어서는 종목 지원, 사용자 임의 종목 검색·추가.

### Out of Scope — 요청 시 데이터 수집
- 백엔드 요청 경로에서의 pykrx 호출, 캐시 워밍, 백그라운드 수집 잡. 수집은 오프라인 스크립트의 책임이다 (REQ-007).

### Out of Scope — 추가 기술지표
- 볼린저 밴드, 스토캐스틱, 일목균형표, 거래량 지표(OBV 등). 본 SPEC은 SMA/EMA/RSI/MACD 4종으로 한정한다.

### Out of Scope — 차트 상호작용 고급 기능
- 드로잉 툴, 추세선, 피보나치, 차트 이미지 내보내기, 기간 비교(다종목 오버레이).

### Out of Scope — 인증
- 신규 엔드포인트에 대한 인증/인가 적용 (기존 라우트와 동일하게 무인증 유지).

### Out of Scope — `SPEC-API-001` 범위 구현
- `GET /api/stocks` 엔드포인트 신설, `MOCK_STOCKS` 제거, 실데이터 연동 등 `SPEC-API-001`이 담당하는 작업. 해당 SPEC은 미구현 상태이며 본 SPEC이 대신 구현하지 않는다.
