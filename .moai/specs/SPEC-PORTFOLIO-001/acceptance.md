---
id: SPEC-PORTFOLIO-001
title: "포트폴리오 분석 모듈 — 인수 기준"
version: "0.1.1"
status: draft
created: 2026-09-20
updated: 2026-09-20
tier: M
---

# SPEC-PORTFOLIO-001 인수 기준 (Acceptance Criteria)

> Tier M 산출물. `spec.md` §3은 본 문서를 가리키는 포인터다.
> **트레이서빌리티**: REQ-001~REQ-016 전체가 아래 AC-001~AC-016으로 커버된다. 모든 AC는 최소 1개의 REQ를 참조하며, 참조되지 않은 REQ는 없다(갭 없음). 대응 관계는 문서 끝의 매핑 표에 정리했다.
> **검증 수단**: 16개 AC 가운데 자동 테스트로 판정하는 것과 문서화된 수동 절차로 판정하는 것이 나뉜다. 어느 쪽인지는 「검증 수단」 표에 명시했다.

## 인수 기준 목록 (Given-When-Then)

**AC-001**: Given 허용 목록 4개 종목만 담긴 보유 종목 파일이 주어지고 서브에이전트 응답이 정상일 때, When `--save-json <대상>` 옵션으로 스크립트를 실행하면, Then 대상 경로에 파일이 생성되고 그 내용은 `schema_version`·`source`·`generated_date`·`portfolio_file`·`portfolio_name`·`as_of`·`valuation`·`risk`·`allocation` 9개 최상위 키를 가지며, `generated_date`는 실행일(ISO `YYYY-MM-DD`)이고 `as_of`는 입력 보유 종목 파일의 `as_of` 값과 같다. (REQ-001)

**AC-002**: Given 대상 경로에 기존 분석 파일이 이미 존재하는 상태에서 아래 두 실패를 각각 강제했을 때 — (a) 서브에이전트 실행 또는 응답 파싱이 실패하도록 한 경우, (b) 저장 함수가 임시 파일을 만든 **뒤** 교체(`os.replace`) 직전에 예외를 던지도록 패치한 경우 — When `--save-json` 옵션으로 스크립트를 실행하면, Then 두 경우 모두 종료 코드가 0이 아니고, 대상 파일의 내용(바이트)이 실행 전과 동일하며, 대상 파일이 있는 디렉터리에 잔여 임시 파일이 남지 않는다. (REQ-001, REQ-002)

**AC-003**: Given 허용 목록 밖 코드(`005380`, `999999`)를 포함한 `data/portfolio.edge.json`이 입력으로 주어졌을 때, When `--save-json` 옵션으로 스크립트를 실행하면, Then 종료 코드가 0이 아니고, 오류 메시지에 허용 목록 밖 코드가 명시되며, 대상 경로에 파일이 생성되지 않고(기존 파일이 있었다면 그대로이며), 서브에이전트 호출이 한 번도 일어나지 않았음을 mock으로 검증할 수 있다. (REQ-003)

**AC-004** *(샘플 생성 모드)*: Given `data/portfolio.example.json`을 입력으로 하고 `subprocess` 호출이 일어나면 테스트가 실패하도록 감시를 걸어 둔 상태에서, When `--sample --save-json <대상>`으로 같은 날 두 번 실행하면, Then 두 번 모두 종료 코드가 0이고, `subprocess`·`shutil.which` 호출이 한 번도 발생하지 않으며, 두 번의 저장 결과가 바이트 단위로 동일하고, 저장된 내용은 `spec.md` §4 「필수 키 집합」 다섯 조건을 모두 만족하며 `source`가 `"sample"`이고, 보유 종목 가운데 최소 한 종목은 `verdict`·`overall`·`action`이 모두 `unknown`이 아니며 최소 한 종목은 `unknown`이다. 또한 Given 같은 옵션에 입력만 `data/portfolio.edge.json`으로 바꾸면, Then 종료 코드가 0이 아니고 대상 경로에 파일이 생성되지 않는다. (REQ-004)

**AC-005** *(성공 응답 계약 — `source` 무관)*: Given `data/portfolio_analysis.json`이 `spec.md` §4 「필수 키 집합」을 만족하는 상태로 존재할 때, When 클라이언트가 `GET /api/portfolio`를 호출하면, Then 응답은 `200`이고 본문은 `meta`·`valuation`·`risk`·`allocation` 4개 키를 가지며, `meta`에 `schema_version`·`source`·`portfolio_name`·`as_of`·`generated_date`가 모두 존재하고, 세 분석 블록의 `results` 배열 길이가 모두 보유 종목 수와 같다. 이 단언은 `source`가 `"agent-team"`인 파일과 `"sample"`인 파일 각각에 대해 동일하게 성립하며, 두 응답은 상태 코드와 키 구조가 같고 `meta.source` 값만 다르다. (REQ-004, REQ-005)

**AC-006** *(열화된 파일 처리)*: Given 분석 결과 파일이 (a) 존재하지 않는 경우, (b) JSON으로 파싱되지 않는 경우, (c) 최상위 키 `allocation`이 없는 경우, (d) `risk.results`가 리스트가 아닌 경우, (e) `valuation.results`의 길이가 나머지 두 `results`와 다른 경우 각각에 대해, When 클라이언트가 `GET /api/portfolio`를 호출하면, Then (a)는 응답이 `404`이고 (b)~(e)는 모두 `500`이며, (b)~(e)의 응답 본문 문자열에 파일 시스템 경로(`/`·`\`를 포함한 절대 경로 조각), 예외 클래스명, `Traceback` 문자열이 포함되지 않는다. (REQ-006, REQ-007)

**AC-007**: Given `GET /api/portfolio`가 호출될 때, When 요청 처리가 완료되면, Then `subprocess`·`shutil.which`·외부 HTTP 클라이언트(`httpx`·`urllib`·`requests`) 호출이 한 번도 발생하지 않고, `data/` 아래에 어떤 파일도 생성·수정되지 않는다 — `backend/tests/test_portfolio.py`에서 mock/assert와 디렉터리 스냅샷 비교로 검증한다. (REQ-008)

**AC-008**: Given 파일의 `risk.results[]`와 `allocation.results[]`가 같은 종목에 대해 서로 다른 `actual_weight_pct`(예: 47.8 대 44.54)를 담고 있을 때, When `GET /api/portfolio` 응답을 검사하면, Then `risk.results[]`의 각 원소에 `actual_weight_pct` 키가 존재하지 않고, `allocation.results[]`의 `actual_weight_pct`는 파일의 값과 동일하다. (REQ-005)

**AC-009**: Given 인증된 사용자가 정상 분석 결과를 받는 상태일 때, When `/portfolio` 화면을 렌더링하면, Then 보유 종목 각각에 대해 밸류에이션 `verdict`와 `score`, 리스크 `overall`, 리밸런싱 `action`·`drift_pct`·`rebalance_amount`가 화면에서 조회 가능하다. (REQ-009)

**AC-010**: Given `as_of`가 `"2026-07-25"`, `generated_date`가 `"2026-09-20"`, `source`가 `"sample"`인 응답이 주어졌을 때, When `/portfolio` 화면을 렌더링하면, Then 두 날짜가 각각 어떤 날짜인지 구분되는 레이블과 함께 모두 표시되고, 실시간 시세가 아닌 스냅샷임을 알리는 문구가 존재하며, 샘플 데이터임을 구분하는 표기가 존재한다. (REQ-010)

**AC-011**: Given `GET /api/portfolio` 요청이 실패(네트워크 오류 또는 404 또는 500)하도록 강제했을 때, When `/portfolio` 화면을 렌더링하면, Then 분석 결과 영역에 오류 상태가 표시되고, 헤더·네비게이션 등 나머지 영역은 정상 렌더링되며 페이지가 예외로 중단되지 않는다. (REQ-011)

**AC-012**: Given 로그인하지 않은 사용자가 있을 때, When `/portfolio`에 접근하면, Then 대시보드와 동일하게 `/login`으로 이동한다. (REQ-012)

**AC-013**: Given 로그인한 사용자가 있을 때, When 대시보드를 렌더링하면, Then `/portfolio`로 이동하는 링크가 화면에 존재하고, 그 링크를 눌렀을 때 `/portfolio`로 이동한다. (REQ-013)

**AC-014**: Given `NEXT_PUBLIC_API_URL` 환경 변수가 설정되어 있지 않을 때, When `/portfolio`가 분석 결과를 요청하면, Then 대시보드의 `API` 상수(`dashboard/page.tsx:16`)와 동일한 기본값 `http://localhost:8000`으로 호출한다. 환경 변수가 설정된 경우에는 그 값을 사용한다. (REQ-014)

**AC-015**: Given `verdict`가 `"unknown"`인 종목, `overall`이 `"unknown"`인 종목, `action`이 `"unknown"`인 종목을 포함한 응답이 주어졌을 때, When `/portfolio` 화면을 렌더링하면, Then 세 종목 모두 목록에 남아 있고 해당 항목이 "판정 불가"로 명시된 상태로 표시되며, 정상 판정값(예: `"저평가"`·`"low"`·`"매수"`)과 시각적으로 구분된다. (REQ-015)

**AC-016**: Given 본 SPEC의 변경이 모두 적용된 상태에서, When 기존 라우트(`GET /health`, `GET·PUT·DELETE /api/settings/notion`, `POST /api/report/notion`, `GET /api/github/issues`, `GET /api/stocks/{code}/ohlcv`, `GET /api/stocks/{code}/indicators`)를 호출하고 대시보드를 렌더링하면, Then 모든 라우트의 응답이 변경 전과 동일하고, 기존 백엔드 테스트(`test_chart.py`·`test_indicators.py`·`test_notion_settings.py`)가 전부 통과하며, 대시보드의 보유 종목 테이블·주가 차트·최신 뉴스·GitHub 이슈·Notion 저장 버튼이 정상 동작한다. (REQ-016)

## 검증 수단 (Verification Means)

저장소에는 프론트엔드 테스트 프레임워크가 없다(`frontend/package.json` devDependencies에 jest·vitest·`@testing-library` 없음). 도입은 본 SPEC의 범위 밖이므로(`spec.md` §5), 화면 AC는 **문서화된 수동 절차**로 판정한다. 아래 표가 AC별 판정 수단의 단일 목록이다.

| AC | 판정 수단 | 실행 위치 |
|---|---|---|
| AC-001 ~ AC-004 | 자동 — `scripts/tests/test_orchestrate_portfolio.py` | M4에서 CI 테스트 단계를 `pytest backend/tests/ scripts/tests/ -v`로 확장한다(`plan.md` M4). 확장 전까지는 로컬 실행 |
| AC-005 ~ AC-008 | 자동 — `backend/tests/test_portfolio.py` | CI `pytest backend/tests/ -v` |
| AC-009 ~ AC-015 | **수동** — `docs/weekly/WEEK_10.md`의 「`/portfolio` 화면 수동 검증 절차」 + 자동 보조 게이트(`npm run lint`, `npm run build`, `npx tsc --noEmit`) | 수동 절차는 M3 산출물, 1회 실행 결과는 `progress.md` 매트릭스에 기록 |
| AC-016 | 자동(백엔드 회귀 — 기존 3개 테스트 파일) + **수동**(대시보드 기존 5개 영역) | CI `pytest backend/tests/ -v` + 수동 절차 문서의 회귀 절 |

자동 보조 게이트는 화면이 **빌드·타입·린트 측면에서 성립하는지**만 말해 준다. 표시 내용과 동작(AC-009~AC-015)은 증명하지 못하므로, 자동 게이트 통과를 해당 AC의 PASS 근거로 삼지 않는다.

### 수동 검증 절차 문서의 요건 (M3 산출물)

`docs/weekly/WEEK_10.md`의 「`/portfolio` 화면 수동 검증 절차」 절은 AC-009~AC-015와 AC-016의 대시보드 항목 각각에 대해 다음 네 가지를 한 줄씩 적는다.

1. **준비** — 어떤 데이터 상태에서 시작하는가(예: `--sample`로 생성한 `data/portfolio_analysis.json`, 백엔드를 멈춘 상태, 로그아웃 상태).
2. **실행** — 실제로 치는 명령과 여는 경로(예: `uvicorn app.main:app --reload` → `npm run dev` → `http://localhost:3000/portfolio`).
3. **관찰 대상** — 화면의 어느 요소를 보는가.
4. **PASS 조건** — 무엇이 보이면 통과인가(이진 판정이 되도록 쓴다).

`--sample` 생성 규칙이 최소 한 종목의 정상 판정과 최소 한 종목의 `unknown`을 동시에 만들도록 요구하는 이유가 이것이다(REQ-004). 샘플 데이터만으로 AC-009와 AC-015를 한 화면에서 함께 확인할 수 있어야 한다.

## 엣지 케이스 (Edge Cases)

아래 항목 가운데 AC로 승격되지 않은 것은 구현 시 참고 사항이며 게이트가 아니다.

- **분석 파일 부재** — `GET /api/portfolio`는 `404`. 예외로 500이 나면 안 된다(AC-006 (a)). 화면은 이 경우를 "분석 결과가 아직 생성되지 않았습니다"로 안내하며, 일반 오류와 구분해 표시하는 편이 낫다.
- **분석 파일이 깨진 JSON** — `500` + 일반화 메시지. 내부 경로나 예외 문자열이 새면 안 된다(AC-006 (b)).
- **필수 키 누락(스키마 위반)** — 파싱은 되지만 `spec.md` §4 「필수 키 집합」을 어기는 경우. 깨진 JSON과 동일하게 `500`으로 처리한다(AC-006 (c)~(e)). 반쯤 렌더링된 화면보다 명시적 실패가 낫다.
- **입력에 허용 목록 밖 코드** — `data/portfolio.edge.json`(`005380`, `999999`)이 고정 입력이다. 에이전트 호출 전에 거부하며 부분 결과를 남기지 않는다(AC-003). `--sample` 모드도 같은 검사를 먼저 통과해야 한다(AC-004 후반절). 서브에이전트가 읽을 `data/005380_market.json`이 없어 판정이 `unknown`으로 채워지는 상황 자체를 만들지 않는 것이 목적이다.
- **`unknown` 판정** — 실행 실측에서 서흥(`008490`)의 `volume_state`가 `"stale"`로 나온 전례가 있다. `verdict`·`overall`·`action`의 `unknown`은 오류가 아니라 정상 경로이며 "판정 불가"로 표시한다(AC-015).
- **현금이 0인 포트폴리오** — `allocation.total_asset`이 보유 종목 평가금액 합계와 같아지고, 이때만 `risk`와 `allocation`의 비중이 우연히 일치한다. 그래도 응답 계약은 바뀌지 않으며 `risk`의 비중 필드는 여전히 제외한다(AC-008). 0으로 나누는 계산이 발생하지 않아야 한다.
- **보유 종목이 빈 배열** — 스크립트는 기존 `build_prompt`의 `ValueError`("portfolio.holdings가 비어 있습니다") 경로로 0이 아닌 종료 코드를 내며 파일을 쓰지 않는다. 백엔드는 이 상황을 파일 부재(`404`) 또는 스키마 위반(`500`)으로 만나며, 어느 쪽이든 빈 화면을 예외 없이 렌더링한다.
- **`as_of`가 실행일보다 훨씬 과거** — 실측에서 두 달 가까이 차이가 났다. 오류가 아니며, 두 날짜를 모두 표시하는 것으로 해소한다(AC-010).

## 품질 게이트 기준 (Quality Gate Criteria)

- AC-001~AC-016 전체가 「검증 수단」 표에 지정된 방법으로 판정 가능해야 한다. 자동 테스트로 판정하는 것은 AC-001~AC-008과 AC-016의 백엔드 회귀분이고, 나머지(AC-009~AC-015, AC-016의 대시보드분)는 문서화된 수동 절차로 판정한다.
- 수동 판정 AC는 절차 문서의 PASS 조건을 인용해 `progress.md` 매트릭스에 기록한다. 절차 문서 없이 "확인함"이라고만 적은 항목은 PASS로 보지 않는다.
- 백엔드 테스트는 커밋된 `data/portfolio_analysis.json`의 `source` 값에 의존하지 않는다. 임시 디렉터리 픽스처로 검증하고, 커밋된 파일에 대해서는 `spec.md` §4 「필수 키 집합」 적합성 테스트 하나만 둔다.
- 신규 백엔드 코드(엔드포인트 + 파일 읽기 헬퍼)는 커버리지 측정 대상에 포함되어야 한다.
- 기존 라우트와 대시보드 기존 영역에 회귀가 없어야 한다(AC-016).
- `scripts/tests/`는 현재 CI 테스트 단계(`pytest backend/tests/ -v`)에 포함되지 않는다. M4에서 이 단계를 `scripts/tests/`까지 확장하며, 확장하지 못한 경우 그 사유와 대안(M4 수동 1회 실행)을 `progress.md`에 기록한다.

## 완료 정의 (Definition of Done)

- [ ] REQ-001~REQ-016이 모두 구현되고 각 REQ에 매핑된 AC가 PASS
- [ ] `scripts/orchestrate_portfolio.py`에 `--save-json`(REQ-001)·`--sample`(REQ-004) 추가, `data/portfolio_analysis.json` 생성·커밋
- [ ] `scripts/tests/test_orchestrate_portfolio.py`, `backend/tests/test_portfolio.py` 신설 및 통과
- [ ] `frontend/src/app/portfolio/page.tsx` 신설, 대시보드에 `/portfolio` 링크 추가
- [ ] `docs/weekly/WEEK_10.md`에 「`/portfolio` 화면 수동 검증 절차」 기록 (AC-009~AC-015, AC-016의 대시보드 항목)
- [ ] 수동 검증 절차를 1회 실행하고 AC별 PASS/FAIL을 절차 문서 인용과 함께 `progress.md` 매트릭스에 기록
- [ ] `.github/workflows/ci.yml`의 테스트 단계가 `scripts/tests/`를 포함 (포함하지 못했다면 사유를 `progress.md`에 기록)
- [ ] `ruff check backend/` 무결 (신규 위반 0건)
- [ ] `npm run lint` 무결, `npm run build` 성공, `npx tsc --noEmit` 종료 코드 0
- [ ] 백엔드 테스트 전체 통과, 기존 `test_chart.py`·`test_indicators.py`·`test_notion_settings.py`에 영향 없음 (AC-016)
- [ ] `backend/requirements.txt`에 신규 런타임 의존성 추가 없음, `frontend/package.json`에 신규 의존성 추가 없음
- [ ] 분석 결과 재생성 절차가 `docs/weekly/WEEK_10.md`에 기록됨
- [ ] Out of Scope 항목(`spec.md` §5) 중 어떤 것도 구현 범위에 포함되지 않음

## REQ → AC 매핑

| REQ | AC |
|---|---|
| REQ-001 | AC-001, AC-002 |
| REQ-002 | AC-002 |
| REQ-003 | AC-003 |
| REQ-004 | AC-004, AC-005 |
| REQ-005 | AC-005, AC-008 |
| REQ-006 | AC-006 |
| REQ-007 | AC-006 |
| REQ-008 | AC-007 |
| REQ-009 | AC-009 |
| REQ-010 | AC-010 |
| REQ-011 | AC-011 |
| REQ-012 | AC-012 |
| REQ-013 | AC-013 |
| REQ-014 | AC-014 |
| REQ-015 | AC-015 |
| REQ-016 | AC-016 |

| AC | 참조 REQ |
|---|---|
| AC-001 | REQ-001 |
| AC-002 | REQ-001, REQ-002 |
| AC-003 | REQ-003 |
| AC-004 | REQ-004 |
| AC-005 | REQ-004, REQ-005 |
| AC-006 | REQ-006, REQ-007 |
| AC-007 | REQ-008 |
| AC-008 | REQ-005 |
| AC-009 | REQ-009 |
| AC-010 | REQ-010 |
| AC-011 | REQ-011 |
| AC-012 | REQ-012 |
| AC-013 | REQ-013 |
| AC-014 | REQ-014 |
| AC-015 | REQ-015 |
| AC-016 | REQ-016 |
