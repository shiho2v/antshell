---
id: SPEC-API-001
title: "백엔드 API와 대시보드 실데이터 연동 — 구현 계획"
version: "0.2.0"
status: draft
created: 2026-09-06
updated: 2026-09-06
---

# SPEC-API-001 구현 계획

## 기술 접근 (Technical Approach)

- 신규 외부 의존성 없음. `pathlib`, `glob`, `fastapi.responses.FileResponse`는 표준 라이브러리/기존 FastAPI 의존성 범위 내.
- `backend/app/main.py`는 `backend/` 디렉터리를 cwd로 기동된다(`docs/setup/ONBOARDING.md`의 인접한 두 줄 — `:156` `cd backend`, `:157` `uvicorn app.main:app --reload` — 이 두 단계로 구성된 개발 실행 명령이며, 원본 파일에 `&&`로 연결된 한 줄이 아니다). 레포 루트의 `data/`, `outputs/`에 접근하려면 `main.py` 파일 위치 기준 상대 경로를 사용한다:
  `Path(__file__).resolve().parents[2]` → `backend/app/main.py`에서 `parents[0]=app/`, `parents[1]=backend/`, `parents[2]=레포 루트`.
- CORS(`ALLOWED_ORIGINS`) 설정은 변경하지 않는다. 기존 `.env` 기반 `_get_env()` 헬퍼도 이 SPEC에서는 사용하지 않는다(신규 엔드포인트는 환경 변수 의존이 없음).

## 마일스톤 (우선순위 기반, 변경 가능성 높은 결정부터)

### M1 (Priority: High) — 응답 데이터 계약 확정

가장 되돌리기 어려운 결정: 이 스키마가 확정되면 프론트엔드 전체가 이를 기준으로 작성된다.

- `StockSummary` 응답 모델 정의 (Pydantic, `backend/app/main.py:49-53`의 `StockReportRequest` 스타일을 따름): `code: str`, `name: str`, `current_price: int`, `daily_change_pct: float | None`, `as_of: str`, `fetched_date: str`, `report_url: str | None`
- `STOCK_NAMES: dict[str, str]` 정적 매핑 정의: `{"005930": "삼성전자", "000660": "SK하이닉스", "009150": "삼성전기", "008490": "서흥"}`
- `ALLOWED_CODES = list(STOCK_NAMES.keys())` 상수로 4개 허용 코드 목록을 단일 출처화
- `report_url` 값의 형태를 상대 경로 `/api/stocks/{code}/report`로 확정 (원본 파일 경로를 클라이언트에 직접 노출하지 않음)

### M2 (Priority: High) — 백엔드: `GET /api/stocks` 엔드포인트

- `backend/app/main.py:56-92`(`save_report_to_notion` 라우트)의 스타일을 그대로 따른다: 데코레이터 기반 함수, `HTTPException`으로 에러 처리, 인증 없음
- `ALLOWED_CODES`를 순회하며 각 코드의 `data/{code}_market.json`을 읽어 `current_price`, `as_of`, `fetched_date` 추출
- `STOCK_NAMES[code]`로 `name` 채움, `daily_change_pct`는 항상 `None`
- `report_url`은 M3에서 정의할 리포트 존재 여부 판단 로직을 재사용해 계산 (파일 없으면 `None`)
- 데이터 파일이 예기치 않게 없을 경우(운영 중 삭제 등) 해당 종목을 배열에서 건너뛰지 않고 로그만 남기며, 이 케이스는 4개 종목 모두 파일이 존재함이 이미 검증되었으므로(SPEC §1 근거) 정상 경로에서는 발생하지 않음 — 방어적 처리로만 추가

### M3 (Priority: High) — 백엔드: `GET /api/stocks/{code}/report` 엔드포인트

- 요청 즉시 `code in ALLOWED_CODES` 검사 → 실패 시 파일시스템 조회 없이 즉시 `404` (경로 조작 방지, REQ-007)
- `outputs/{code}_report_*.html` 글롭 탐색. 여러 날짜 리포트가 누적될 경우를 대비해 파일명 정렬(날짜가 `YYYY-MM-DD`로 앞자리 정렬 가능) 또는 `mtime` 기준으로 최신 1개만 선택
- 파일이 없으면 `404` (REQ-006), 있으면 `FileResponse(path, media_type="text/html")`로 응답

### M4 (Priority: Medium) — 프론트엔드: `MOCK_STOCKS`를 실데이터 페칭으로 교체

- `frontend/src/app/dashboard/page.tsx:54-60`의 GitHub 이슈 `useEffect` 패턴을 그대로 따른다: `fetch(`${API}/...`)` + `.then(r => r.json())` + `.catch(() => setX([]))` + `.finally(() => setLoading(false))`
- `stocks` state + `stocksLoading` state 추가, `useEffect`로 `GET /api/stocks` 호출
- 테이블 렌더링을 `MOCK_STOCKS.map(...)` → `stocks.map(...)`로 교체 (`page.tsx:143`)
- `MOCK_STOCKS` 상수 자체는 삭제 (더 이상 참조되지 않음 — REQ-010)

### M5 (Priority: Medium) — 프론트엔드: 표시 로직 (준비중 / 기준일 / 리포트 링크)

- 등락률 셀: `daily_change_pct === null`이면 회색 "준비중" 텍스트, 아니면 기존 `up` 판정 로직을 `daily_change_pct >= 0`으로 대체하여 빨강/파랑 스타일 유지
- 각 행에 `as_of` 또는 `fetched_date`를 작은 보조 텍스트로 노출 (예: 종목 코드 옆 또는 현재가 아래에 "7/10 기준" 형태) — REQ-013
- `report_url`이 있으면 "리포트 보기" 링크(새 탭, `target="_blank" rel="noreferrer"`) 추가, 없으면 비활성/숨김 — REQ-014, REQ-015
- `saveToNotion()` 호출 시 전달하는 객체의 `price`를 `current_price.toLocaleString()`(문자열)로, `change`를 `daily_change_pct === null ? '준비중' : ...`로 매핑 — 기존 `StockReportRequest` 계약(REQ-016)을 깨지 않도록 프론트엔드에서 변환

### M6 (Priority: Low, 기계적) — 백엔드 테스트 추가

- `backend/tests/test_stocks.py` 신설: `TestClient`로 `GET /api/stocks`(4개 항목, `daily_change_pct` null 검증), `GET /api/stocks/005380/report`(404), `GET /api/stocks/005930/report`(200) 케이스 작성
- `backend/requirements.txt`에 `pytest`가 없으므로 로컬 실행 시 별도 설치 필요함을 README 또는 커밋 메시지에 명시 (CI는 `pip install ... pytest`로 별도 설치 중 — `.github/workflows/ci.yml:28`)

**시너지 메모 (요구사항 아님)**: `.github/workflows/ci.yml:42`가 `pytest backend/tests/ -v`를 실행하지만 현재 `backend/tests/` 디렉터리 자체가 존재하지 않아 CI가 이 스텝에서 실패하거나 스킵되는 상태다. M6에서 `backend/tests/test_stocks.py`를 생성하면 이 CI 갭이 부수적으로 해소된다. 다만 CI 수정 자체는 본 SPEC의 범위가 아니며 `.moai/project/product.md` §7에 별도 로드맵 항목으로 이미 추적 중이다.

## 제약사항 (Constraints)

- 유료 클라우드 서비스 추가 없음 (신규 엔드포인트는 로컬 파일 읽기만 수행)
- Git 초보자도 이해 가능한 단순한 구현 유지 — 신규 추상화 계층(리포지토리 패턴, 서비스 레이어 등) 도입하지 않고 기존 `main.py`의 flat 함수 스타일 유지
- Claude Code 토큰 절약 — 본 SPEC은 Tier M으로 spec.md + plan.md + acceptance.md 3개 파일만 생성 (plan-audit iteration 1 리뷰 D2 반영, Tier S → M 재분류)

## 리스크

| 리스크 | 완화 방안 |
|--------|-----------|
| `outputs/{code}_report_*.html`가 향후 여러 날짜로 누적되면 글롭이 다중 결과를 반환 | M3에서 최신 파일(정렬 또는 mtime) 1개만 선택하도록 명시적으로 구현 |
| `data/*.json` 파일 인코딩 불일치 시 파싱 오류 | 기존 `generating-krx-report` 스킬과 동일하게 UTF-8 가정, `json.load(f, encoding="utf-8")` 명시 |
| 배포 환경에서 `ALLOWED_ORIGINS`가 로컬 기본값(`http://localhost:3000`)에 의존 | 본 SPEC 범위 밖의 기존 이슈이므로 언급만 하고 별도 조치하지 않음 |
| 프론트엔드가 `current_price`(숫자)와 기존 `MOCK_STOCKS.price`(문자열, 콤마 포함)의 타입 차이를 놓칠 경우 렌더링 오류 | M4/M5에서 `.toLocaleString()` 변환을 명시적 구현 항목으로 기재 |

## @MX 태그 계획 (Phase 14)

Full scan 적용(기존 코드 수정 + 신규 공개 API 생성 모두 해당). 이 프로젝트의 `development_mode: ddd`(테스트 커버리지 10% 미만 기준, 이번 세션에서 확정)이므로 manager-develop은 ANALYZE-PRESERVE-IMPROVE 사이클로 구현한다.

- **fan_in 측정 결과**: `backend/app/main.py`의 기존 3개 라우트 함수 모두 fan_in 0~1(다른 코드에서 참조되지 않음, HTTP로만 호출됨) — `@MX:ANCHOR`의 fan_in≥3 기준 미충족. 신규 라우트(`get_stocks`, `get_stock_report`)도 동일하게 낮은 fan_in이 예상된다.
- **`@MX:ANCHOR` 후보**(fan_in 기준이 아닌 "공개 API 경계" 기준으로): `GET /api/stocks`, `GET /api/stocks/{code}/report` — 프론트엔드가 소비하는 신규 공개 계약이므로 각각 1개씩 부여를 권장. `@MX:REASON`: "대시보드가 소비하는 공개 API 계약 — 응답 스키마 변경 시 프론트엔드 영향 확인 필요."
- **`@MX:NOTE` 후보**: `STOCK_NAMES` 정적 매핑(4개 종목 한정인 이유 — REQ-002/제외범위 참조), `daily_change_pct: None` 반환 로직(원본 데이터에 필드 자체가 없다는 사실 — REQ-003 참조).
- **`@MX:TODO`**: M6(테스트 추가) 이전 커밋에서는 신규 라우트 2개에 `@MX:TODO`(미검증) 부여, M6 완료 후 제거.
- 기존 코드(`main.py`, `page.tsx`)에는 `@MX:` 태그가 전혀 없음(확인됨) — 이번 SPEC이 이 파일들의 첫 MX 태깅이 된다.

## 참조

- `backend/app/main.py:56-92` — 신규 라우트 스타일의 기준 패턴 (`save_report_to_notion`)
- `frontend/src/app/dashboard/page.tsx:54-60` — 신규 fetch 로직의 기준 패턴 (GitHub 이슈 `useEffect`)
- `.moai/specs/SPEC-API-001/spec.md` — 본 계획이 구현하는 요구사항 원본
