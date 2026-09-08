---
id: SPEC-API-001
title: "백엔드 API와 대시보드 실데이터 연동 (Mock 종목 데이터 교체)"
version: "0.2.0"
status: draft
created: 2026-09-06
updated: 2026-09-06
author: jasonbaac
priority: P1
phase: "v1.0.0"
module: "backend/app, frontend/src/app/dashboard"
lifecycle: spec-anchored
tags: "backend, frontend, api, dashboard, fastapi, nextjs"
tier: M
---

## HISTORY

| 버전 | 날짜 | 작성자 | 변경 내용 |
|------|------|--------|-----------|
| 0.1.0 | 2026-09-06 | jasonbaac | 최초 작성 — 백엔드 API와 대시보드 실데이터 연동 SPEC 초안 (Tier S) |
| 0.2.0 | 2026-09-06 | jasonbaac | plan-audit iteration 1 리뷰(MP-2 FAIL) 반영 — Tier S → M 재분류(acceptance.md 신설), REQ-006/007/011 `[Event-detected]` → `[Event-driven]` 재태깅(MP-2 수정), REQ-006/008/009/014 트레이서빌리티 갭 해소(AC-011~014 신설), REQ-002 구현 세부사항(타입 힌트) 제거. REQ-003은 문장 2개로 나눠 가독성만 개선했으며, Ubiquitous+Unwanted 복합 태그 자체는 REQ 16개 상한(Tier M)을 지키기 위해 의도적으로 미해결로 남김(plan-audit iteration 2 review D8 지적, 논블로킹) |

---

## 1. 개요 (Overview)

`frontend/src/app/dashboard/page.tsx`의 보유 종목 테이블은 현재 하드코딩된 `MOCK_STOCKS` 배열(4개 종목: `005930` 삼성전자, `000660` SK하이닉스, `009150` 삼성전기, `008490` 서흥)을 표시하고 있다. 이 4개 종목에 대해서는 이미 `generating-krx-report` 스킬 파이프라인이 생성한 실제 데이터 파일(`data/{code}_fundamentals.json`, `data/{code}_market.json`, `outputs/{code}_report_{date}.html`)이 레포지토리에 존재한다.

본 SPEC은 `backend/app/main.py`에 신규 엔드포인트를 추가해 이 기존 파일들을 그대로 서빙하고, 대시보드가 Mock 데이터 대신 이 엔드포인트를 호출하도록 교체하는 것을 목표로 한다. 신규 데이터 수집, 리포트 재생성, 종목 범위 확장은 포함하지 않는다.

두 가지 실제 데이터 공백이 존재하며, 각각에 대한 설계 결정은 다음과 같다:

1. **종목명 부재**: `data/{code}_fundamentals.json`, `data/{code}_market.json` 어디에도 한글 종목명 필드가 없다 → 백엔드가 4개 코드 한정 정적 매핑(`STOCK_NAMES`)을 보유한다.
2. **전일 대비 등락률 부재**: `data/{code}_market.json`에는 `pct_from_52w_high`(52주 최고가 대비율)만 있고 전일 대비 등락률 필드가 없다 → 응답의 `daily_change_pct`는 항상 `null`이며, 프론트엔드는 이를 "준비중"으로 표시한다. `pct_from_52w_high`를 등락률로 오용하지 않는다.

## 2. 요구사항 (GEARS)

### 백엔드 — 응답 범위 및 데이터 계약

**REQ-001** [Ubiquitous] 백엔드는 사전에 정의된 4개 종목 코드(`005930`, `000660`, `009150`, `008490`)에 대해서만 종목 데이터를 제공한다.

**REQ-002** [Ubiquitous] 백엔드는 사전에 정의된 4개 종목 코드에 대한 종목명을 정적으로 보유하며, 범용 종목명 조회/검색 서비스를 두지 않는다.

**REQ-003** [Ubiquitous] `data/{code}_market.json`에 일별(전일 대비) 등락률 필드가 존재하지 않으므로, 백엔드는 `daily_change_pct` 값을 항상 `null`로 응답한다. 백엔드는 `pct_from_52w_high` 값을 등락률로 대체 제공하지 않는다.

### 백엔드 — 엔드포인트 동작

**REQ-004** [Event-driven] **When** 클라이언트가 `GET /api/stocks` 요청을 보내면, 백엔드는 4개 종목 각각에 대해 `code`, `name`, `current_price`, `daily_change_pct`, `as_of`, `fetched_date`, `report_url` 필드를 포함하는 배열을 응답한다.

**REQ-005** [Event-driven] **When** 클라이언트가 `GET /api/stocks/{code}/report` 요청을 보내고 해당 코드가 4개 허용 목록에 포함되며 `outputs/{code}_report_*.html` 파일이 존재하면, 백엔드는 해당 HTML 파일을 `200` 응답으로 반환한다.

**REQ-006** [Event-driven] **When** 클라이언트가 `GET /api/stocks/{code}/report` 요청을 보내고 해당 코드의 리포트 파일이 존재하지 않으면, 백엔드는 `404` 상태 코드를 반환한다.

**REQ-007** [Event-driven] **When** 클라이언트가 4개 허용 코드 목록에 없는 `code`로 `GET /api/stocks/{code}/report`를 요청하면, 백엔드는 파일시스템의 임의 경로를 조회하지 않고 즉시 `404`를 반환한다. (경로 조작/디렉터리 탐색 방지)

**REQ-008** [Unwanted] 백엔드는 이 SPEC의 어떤 엔드포인트 호출로도 DART/pykrx 데이터 수집이나 `outputs/*.html` 리포트 재생성을 트리거하지 않는다.

### 프론트엔드 — 데이터 연동

**REQ-009** [Where] 프론트엔드는 기존 `NEXT_PUBLIC_API_URL` 환경 변수(설정 시) 또는 기본값 `http://localhost:8000`을 그대로 사용하여 신규 엔드포인트를 호출한다. (기존 `API` 상수 변경 없음)

**REQ-010** [Event-driven] **When** 대시보드 페이지가 마운트되면, 프론트엔드는 `GET /api/stocks`를 호출하여 응답 데이터로 보유 종목 테이블을 렌더링하고, `MOCK_STOCKS` 하드코딩 배열은 더 이상 사용하지 않는다.

**REQ-011** [Event-driven] **When** `GET /api/stocks` 요청이 실패(네트워크 오류, 5xx 등)하면, 프론트엔드는 빈 배열로 폴백하고 기존 GitHub 이슈 섹션과 동일한 방식으로 로딩/빈 상태 UI를 표시한다.

### 프론트엔드 — 표시 로직

**REQ-012** [State-driven] **While** 특정 종목의 `daily_change_pct` 값이 `null`인 동안, 프론트엔드는 등락률 열에 고정 문자열 "준비중"을 표시하고 상승/하락 색상 로직(빨강/파랑)을 적용하지 않는다.

**REQ-013** [Ubiquitous] 프론트엔드는 각 종목 행에 데이터 기준일(`as_of` 또는 `fetched_date`)을 시각적으로 표시하여, 데이터가 실시간이 아니라 파이프라인이 생성한 스냅샷임을 사용자에게 알린다.

**REQ-014** [State-driven] **While** 특정 종목의 `report_url` 값이 `null`인 동안, 프론트엔드는 해당 종목의 "리포트 보기" 링크를 비활성화하거나 숨긴다.

**REQ-015** [Event-driven] **When** `report_url` 값이 존재하는 종목에 대해 사용자가 "리포트 보기"를 클릭하면, 프론트엔드는 새 탭에서 해당 리포트 HTML을 연다.

### 기존 기능 호환성

**REQ-016** [Ubiquitous] 기존 "Notion 저장" 버튼의 `POST /api/report/notion` 호출 방식은 변경되지 않으며, `daily_change_pct`가 `null`인 종목에 대해서는 `change` 필드에 문자열 "준비중"을 전달한다.

## 3. 인수 기준 (Acceptance Criteria)

인수 기준은 `.moai/specs/SPEC-API-001/acceptance.md` 참고 (Tier M).

## 4. 데이터 소스 참조 (계약, 구현 아님)

- `data/{code}_fundamentals.json`: `{stock_code, corp_code, fetched_at, source, unit, annual: [...], quarterly: [...]}` — 본 SPEC의 `/api/stocks` 응답은 이 파일에서 값을 직접 인용하지 않는다(가격/등락률만 필요). 향후 재무 지표 확장 시 참조 대상.
- `data/{code}_market.json`: `{stock_code, as_of, fetched_date, source, current_price, high_52w, pct_from_52w_high, ...}` — `current_price`, `as_of`, `fetched_date`가 응답의 핵심 소스.
- `outputs/{code}_report_{YYYY-MM-DD}.html`: 날짜가 파일명에 포함되므로 요청 시점에 글롭(glob)으로 탐색한다. 날짜를 하드코딩하지 않는다.

## 5. 제외 범위 (Out of Scope)

### Out of Scope — 신규 데이터 수집
- DART/pykrx API를 통한 신규 공시·시세 수집 또는 트리거 (기존 배치/스킬 파이프라인의 책임)
- `outputs/*.html` 리포트의 재생성 (읽기 전용으로 기존 파일만 서빙)

### Out of Scope — 종목 범위 확장
- `MOCK_STOCKS`에 없는 종목(예: `005380`) 지원 — 필수 데이터 파일(`fundamentals`/`market`)이 없음
- 사용자가 임의 종목 코드를 검색하거나 추가하는 기능

### Out of Scope — 인증
- 신규 엔드포인트에 대한 인증/인가 적용 (기존 3개 라우트와 동일하게 무인증 유지; 프로젝트 전체 인증 도입은 별도 SPEC 대상)

### Out of Scope — 종목명 해석 서비스
- 4개 코드를 넘어서는 범용 종목명 조회/검색 서비스 구축

### Out of Scope — 실시간 시세
- 실시간/라이브 시세 스트리밍 (기존 파이프라인이 생성한 스냅샷 데이터만 제공하며, `as_of`/`fetched_date` 노출로 비실시간임을 명시)

### Out of Scope — 데이터 스키마 변경
- `data/*.json` 스키마 변경 또는 `generating-krx-report` 스킬 파이프라인 자체 수정
