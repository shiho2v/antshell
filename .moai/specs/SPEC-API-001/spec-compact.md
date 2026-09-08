---
id: SPEC-API-001
title: "백엔드 API와 대시보드 실데이터 연동 (Mock 종목 데이터 교체) — Compact"
version: "0.2.0"
status: draft
tier: M
---

# SPEC-API-001 Compact Extract

## 요구사항 (GEARS)

**REQ-001** [Ubiquitous] 백엔드는 사전에 정의된 4개 종목 코드(`005930`, `000660`, `009150`, `008490`)에 대해서만 종목 데이터를 제공한다.

**REQ-002** [Ubiquitous] 백엔드는 사전에 정의된 4개 종목 코드에 대한 종목명을 정적으로 보유하며, 범용 종목명 조회/검색 서비스를 두지 않는다.

**REQ-003** [Ubiquitous] `data/{code}_market.json`에 일별(전일 대비) 등락률 필드가 존재하지 않으므로, 백엔드는 `daily_change_pct` 값을 항상 `null`로 응답한다. 백엔드는 `pct_from_52w_high` 값을 등락률로 대체 제공하지 않는다.

**REQ-004** [Event-driven] **When** 클라이언트가 `GET /api/stocks` 요청을 보내면, 백엔드는 4개 종목 각각에 대해 `code`, `name`, `current_price`, `daily_change_pct`, `as_of`, `fetched_date`, `report_url` 필드를 포함하는 배열을 응답한다.

**REQ-005** [Event-driven] **When** 클라이언트가 `GET /api/stocks/{code}/report` 요청을 보내고 해당 코드가 4개 허용 목록에 포함되며 `outputs/{code}_report_*.html` 파일이 존재하면, 백엔드는 해당 HTML 파일을 `200` 응답으로 반환한다.

**REQ-006** [Event-driven] **When** 클라이언트가 `GET /api/stocks/{code}/report` 요청을 보내고 해당 코드의 리포트 파일이 존재하지 않으면, 백엔드는 `404` 상태 코드를 반환한다.

**REQ-007** [Event-driven] **When** 클라이언트가 4개 허용 코드 목록에 없는 `code`로 `GET /api/stocks/{code}/report`를 요청하면, 백엔드는 파일시스템의 임의 경로를 조회하지 않고 즉시 `404`를 반환한다. (경로 조작/디렉터리 탐색 방지)

**REQ-008** [Unwanted] 백엔드는 이 SPEC의 어떤 엔드포인트 호출로도 DART/pykrx 데이터 수집이나 `outputs/*.html` 리포트 재생성을 트리거하지 않는다.

**REQ-009** [Where] 프론트엔드는 기존 `NEXT_PUBLIC_API_URL` 환경 변수(설정 시) 또는 기본값 `http://localhost:8000`을 그대로 사용하여 신규 엔드포인트를 호출한다. (기존 `API` 상수 변경 없음)

**REQ-010** [Event-driven] **When** 대시보드 페이지가 마운트되면, 프론트엔드는 `GET /api/stocks`를 호출하여 응답 데이터로 보유 종목 테이블을 렌더링하고, `MOCK_STOCKS` 하드코딩 배열은 더 이상 사용하지 않는다.

**REQ-011** [Event-driven] **When** `GET /api/stocks` 요청이 실패(네트워크 오류, 5xx 등)하면, 프론트엔드는 빈 배열로 폴백하고 기존 GitHub 이슈 섹션과 동일한 방식으로 로딩/빈 상태 UI를 표시한다.

**REQ-012** [State-driven] **While** 특정 종목의 `daily_change_pct` 값이 `null`인 동안, 프론트엔드는 등락률 열에 고정 문자열 "준비중"을 표시하고 상승/하락 색상 로직(빨강/파랑)을 적용하지 않는다.

**REQ-013** [Ubiquitous] 프론트엔드는 각 종목 행에 데이터 기준일(`as_of` 또는 `fetched_date`)을 시각적으로 표시하여, 데이터가 실시간이 아니라 파이프라인이 생성한 스냅샷임을 사용자에게 알린다.

**REQ-014** [State-driven] **While** 특정 종목의 `report_url` 값이 `null`인 동안, 프론트엔드는 해당 종목의 "리포트 보기" 링크를 비활성화하거나 숨긴다.

**REQ-015** [Event-driven] **When** `report_url` 값이 존재하는 종목에 대해 사용자가 "리포트 보기"를 클릭하면, 프론트엔드는 새 탭에서 해당 리포트 HTML을 연다.

**REQ-016** [Ubiquitous] 기존 "Notion 저장" 버튼의 `POST /api/report/notion` 호출 방식은 변경되지 않으며, `daily_change_pct`가 `null`인 종목에 대해서는 `change` 필드에 문자열 "준비중"을 전달한다.

## 인수 기준 (Acceptance Criteria)

> 전체 인수 기준의 SSOT는 `.moai/specs/SPEC-API-001/acceptance.md` (Tier M). 아래는 요약 발췌.

**AC-001**: Given 백엔드 서버가 정상 기동 중일 때, When 클라이언트가 `GET /api/stocks`를 호출하면, Then 응답은 정확히 4개 항목(`005930`, `000660`, `009150`, `008490`)을 담은 JSON 배열이다.

**AC-002**: Given `/api/stocks` 응답의 각 항목을 검사할 때, When `daily_change_pct` 필드를 확인하면, Then 그 값은 예외 없이 `null`이다(숫자나 문자열이 아님).

**AC-003**: Given `outputs/005930_report_2026-07-10.html` 파일이 존재할 때, When 클라이언트가 `GET /api/stocks/005930/report`를 호출하면, Then 응답은 `200` 상태 코드와 해당 HTML 파일 본문이다.

**AC-004**: Given 코드 `005380`(허용 목록 외)이 주어졌을 때, When 클라이언트가 `GET /api/stocks/005380/report`를 호출하면, Then 응답은 `404`이다.

**AC-005**: Given 대시보드 페이지가 브라우저에 로드되었을 때, When `GET /api/stocks` 호출이 성공적으로 완료되면, Then "보유 종목" 테이블에는 4개 행이 렌더링되고 각 행의 종목명은 백엔드 정적 매핑과 일치하며, `MOCK_STOCKS` 배열은 코드에서 더 이상 참조되지 않는다.

**AC-006**: Given `GET /api/stocks` 호출이 실패하거나 타임아웃될 때, When 대시보드가 렌더링되면, Then 예외로 페이지가 중단되지 않고 로딩/빈 상태 UI가 표시된다.

**AC-007**: Given 특정 종목의 `daily_change_pct`가 `null`일 때, When 등락률 열이 렌더링되면, Then "준비중" 텍스트가 표시되고 빨강/파랑 색상 클래스가 적용되지 않는다.

**AC-008**: Given 특정 종목의 `report_url`이 존재할 때, When 사용자가 "리포트 보기"를 클릭하면, Then 새 브라우저 탭이 해당 백엔드 리포트 엔드포인트 URL로 열린다.

**AC-009**: Given `daily_change_pct`가 `null`인 종목에 대해 사용자가 "Notion 저장"을 클릭할 때, When `POST /api/report/notion` 요청이 전송되면, Then 요청 본문의 `change` 필드 값은 "준비중"이며 기존 백엔드 라우트가 정상 처리한다.

**AC-010**: Given 대시보드의 종목 행이 렌더링될 때, When 행 내용을 확인하면, Then 각 행에 `as_of` 또는 `fetched_date` 값이 텍스트로 렌더링되어 DOM에서 조회 가능하다.

**AC-011** *(신규)*: Given 4개 허용 코드 목록에 포함된 유효한 코드에 대해 리포트 파일이 존재하지 않을 때, When `GET /api/stocks/{code}/report`를 호출하면, Then 응답은 `404`이다. (REQ-006)

**AC-012** *(신규)*: Given 이 SPEC의 임의 엔드포인트가 호출될 때, When 요청 처리가 완료되면, Then DART/pykrx 네트워크 호출이나 `outputs/*.html` 재생성이 발생하지 않는다. (REQ-008)

**AC-013** *(신규)*: Given `NEXT_PUBLIC_API_URL`이 설정되어 있지 않을 때, When 프론트엔드가 신규 엔드포인트를 호출하면, Then 기본값 `http://localhost:8000`으로 호출된다. (REQ-009)

**AC-014** *(신규)*: Given 종목의 `report_url`이 `null`일 때, When 해당 행이 렌더링되면, Then "리포트 보기" 링크는 활성 하이퍼링크로 렌더링되지 않는다. (REQ-014)

## 파일 목록 (Files to Modify)

- `backend/app/main.py` — `GET /api/stocks`, `GET /api/stocks/{code}/report` 신규 엔드포인트, `StockSummary` 모델, `STOCK_NAMES`/`ALLOWED_CODES` 상수 추가
- `frontend/src/app/dashboard/page.tsx` — `MOCK_STOCKS` 제거, 실데이터 fetch 로직 및 표시 로직(준비중/기준일/리포트 링크) 추가
- `backend/tests/test_stocks.py` — 신규 테스트 파일

## 제외 범위 (Out of Scope)

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
