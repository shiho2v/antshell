---
id: SPEC-API-001
title: "백엔드 API와 대시보드 실데이터 연동 — 인수 기준"
version: "0.2.0"
status: draft
created: 2026-09-06
updated: 2026-09-06
tier: M
---

# SPEC-API-001 인수 기준 (Acceptance Criteria)

> Tier M 재분류에 따라 신설된 파일이다. spec.md §3의 인수 기준 인라인 절은 본 문서를 가리키는 포인터로 대체되었다 (plan-audit iteration 1 리뷰 D2 반영).

## 인수 기준 목록 (Given-When-Then)

**AC-001**: Given 백엔드 서버가 정상 기동 중일 때, When 클라이언트가 `GET /api/stocks`를 호출하면, Then 응답은 정확히 4개 항목(`005930`, `000660`, `009150`, `008490`)을 담은 JSON 배열이다. (REQ-001, REQ-004)

**AC-002**: Given `/api/stocks` 응답의 각 항목을 검사할 때, When `daily_change_pct` 필드를 확인하면, Then 그 값은 예외 없이 `null`이다(숫자나 문자열이 아님). (REQ-003)

**AC-003**: Given `outputs/005930_report_2026-07-10.html` 파일이 존재할 때, When 클라이언트가 `GET /api/stocks/005930/report`를 호출하면, Then 응답은 `200` 상태 코드와 해당 HTML 파일 본문이다. (REQ-005)

**AC-004**: Given 코드 `005380`(4개 허용 목록 외)이 주어졌을 때, When 클라이언트가 `GET /api/stocks/005380/report`를 호출하면, Then 응답은 `404`이다 (파일시스템 조회 없이 즉시 반환). (REQ-007)

**AC-005**: Given 대시보드 페이지가 브라우저에 로드되었을 때, When `GET /api/stocks` 호출이 성공적으로 완료되면, Then "보유 종목" 테이블에는 4개 행이 렌더링되고 각 행의 종목명은 백엔드의 정적 매핑과 일치하며, `MOCK_STOCKS` 배열은 코드에서 더 이상 참조되지 않는다. (REQ-002, REQ-010)

**AC-006**: Given `GET /api/stocks` 호출이 실패하거나 타임아웃될 때, When 대시보드가 렌더링되면, Then 예외로 페이지가 중단되지 않고 로딩/빈 상태 UI가 표시된다. (REQ-011)

**AC-007**: Given 특정 종목의 `daily_change_pct`가 `null`일 때, When 등락률 열이 렌더링되면, Then "준비중" 텍스트가 표시되고 빨강/파랑 색상 클래스가 적용되지 않는다. (REQ-012)

**AC-008**: Given 특정 종목의 `report_url`이 존재할 때, When 사용자가 "리포트 보기"를 클릭하면, Then 새 브라우저 탭이 해당 백엔드 리포트 엔드포인트 URL로 열린다. (REQ-015)

**AC-009**: Given `daily_change_pct`가 `null`인 종목에 대해 사용자가 "Notion 저장"을 클릭할 때, When `POST /api/report/notion` 요청이 전송되면, Then 요청 본문의 `change` 필드 값은 "준비중"이며 기존 백엔드 라우트가 정상 처리한다. (REQ-016)

**AC-010**: Given 대시보드의 종목 행이 렌더링될 때, When 행 내용을 확인하면, Then 각 행에 `as_of` 또는 `fetched_date` 값이 텍스트로 렌더링되어 DOM에서 조회 가능하다(구체적 어서션 대상 명시로 iteration 1 리뷰 D7 반영). (REQ-013)

**AC-011** *(신규 — REQ-006 트레이서빌리티 갭 해소)*: Given 4개 허용 코드 목록에 포함된 유효한 코드(예: `009150`)에 대해 `outputs/{code}_report_*.html` 파일이 디스크에 존재하지 않을 때, When 클라이언트가 `GET /api/stocks/{code}/report`를 호출하면, Then 응답은 `404`이다. (AC-004와 구분: AC-004는 허용 목록 밖의 코드, AC-011은 허용 목록 안이지만 리포트 파일이 없는 코드.) (REQ-006)

**AC-012** *(신규 — REQ-008 트레이서빌리티 갭 해소)*: Given 이 SPEC의 임의 엔드포인트가 호출될 때, When 요청 처리가 완료되면, Then DART/pykrx 엔드포인트로의 네트워크 호출(`subprocess`/`requests`/`urllib` 등)이나 `outputs/*.html` 재생성이 발생하지 않는다 — `backend/tests/test_stocks.py`에서 해당 호출이 발생하지 않았음을 mock/assert로 검증한다. (REQ-008)

**AC-013** *(신규 — REQ-009 트레이서빌리티 갭 해소)*: Given `NEXT_PUBLIC_API_URL` 환경 변수가 설정되어 있지 않을 때, When 프론트엔드가 신규 종목 엔드포인트를 호출하면, Then 기존 `API` 상수(`page.tsx:14`)와 동일하게 기본값 `http://localhost:8000`으로 호출된다. (REQ-009)

**AC-014** *(신규 — REQ-014 트레이서빌리티 갭 해소)*: Given 종목의 `report_url` 값이 `null`일 때, When 해당 종목 행이 렌더링되면, Then "리포트 보기" 링크는 활성 하이퍼링크로 렌더링되지 않는다(DOM에 없거나 비활성/클릭 불가 상태로 렌더링). (REQ-014)

## 엣지 케이스 (Edge Cases)

- 4개 허용 코드 중 하나의 데이터 파일(`data/{code}_market.json`)이 런타임에 갑자기 사라지는 경우 — plan.md M2에서 방어적 로그 처리만 하고 배열에서 제외하지 않음(정상 경로에서는 발생하지 않음이 SPEC §1에서 이미 검증됨).
- `outputs/{code}_report_*.html`이 여러 날짜로 누적된 경우 — plan.md M3에서 최신 1개만 선택.
- `daily_change_pct`가 `null`인 상태에서 "Notion 저장" 클릭 시 기존 `StockReportRequest` 계약을 깨지 않아야 함 (AC-009).

## 품질 게이트 기준 (Quality Gate Criteria)

- 모든 AC-001~AC-014는 자동화된 테스트(백엔드: `backend/tests/test_stocks.py`, 프론트엔드: 수동 또는 컴포넌트 테스트)로 검증 가능해야 한다.
- `GET /api/stocks`, `GET /api/stocks/{code}/report` 두 엔드포인트는 커버리지 대상에 포함되어야 한다.
- 기존 `POST /api/report/notion` 라우트의 회귀 테스트(AC-009)가 통과해야 한다.

## 완료 정의 (Definition of Done)

- [ ] REQ-001~REQ-016이 모두 구현되고 각 REQ에 매핑된 AC가 PASS
- [ ] `backend/tests/test_stocks.py` 신설 및 통과
- [ ] `MOCK_STOCKS` 배열이 `frontend/src/app/dashboard/page.tsx`에서 제거됨
- [ ] 기존 "Notion 저장" 기능 회귀 없음 (AC-009)
- [ ] Out of Scope 항목(spec.md §5) 중 어떤 것도 구현 범위에 포함되지 않음
