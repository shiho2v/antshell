---
id: SPEC-NEWS-001
title: "종목 뉴스 모듈 — 구현 계획"
version: "0.1.1"
status: draft
created: 2026-09-20
updated: 2026-09-20
tier: M
---

# SPEC-NEWS-001 구현 계획 (Plan)

## A.1 현재 상태 (조사 결과)

조사는 2026-09-20에 저장소 파일을 직접 읽어 수행했다. 스크립트·테스트·빌드는 실행하지 않았다(§A.9).

| 항목 | 확인된 상태 |
|------|-------------|
| `data/005930_agents.json` | 최상위 키 `ticker`·`news`·`financials` (**`name` 없음**). 뉴스 6건. 모든 항목이 `title`·`date`·`source`·`summary` 4키이고 `url`은 없다. `date`에 `"2026-07-06"`·`"2026-07-07"`이 각각 2건씩 있어 같은 날짜가 중복된다 |
| `data/000660_agents.json` | 최상위 키 `ticker`·`name`·`news`·`financials`. 뉴스 5건. 모든 항목이 4키 + **`url`**. 허용 목록 4종목 가운데 `url`이 있는 유일한 파일이다 |
| `data/009150_agents.json` | 최상위 키 4개. 뉴스 4건, 4키, `url` 없음 |
| `data/008490_agents.json` | **없다.** `008490`은 `_market.json`·`_fundamentals.json`·`_ohlcv.json`만 있고 `_agents.json`이 없다 |
| `data/005380_agents.json` | **있다. 그러나 허용 목록 밖 코드다.** 뉴스 4건 가운데 3건의 `date`가 `"2026-07 (중순)"`·`"2026-07 (중순)"`·`"2026-07 (초중순)"`로 파싱 불가하다. 허용 목록 4종목의 커밋된 파일에는 현재 파싱 불가 날짜가 없으므로, 이 파일이 그 형태가 실제로 발생한다는 유일한 증거다 |
| `.claude/agents/news-collector.md` | 출력 스키마를 `{ "ticker": string, "news": [{ "title", "date", "source", "summary" }] }`로 선언한다. **`url`이 선언에 없다** — 선언과 실물이 어긋난다. 도구는 `WebSearch, WebFetch`, 검색 최대 3회 |
| `scripts/orchestrate_stock_agents.py` | 인자 `ticker`(코드 또는 종목명) + `--save`. `shutil.which("claude")` → `subprocess.run([claude, "-p", "--output-format", "json", "--allowedTools", "WebSearch,WebFetch"], timeout=180)`. `--save`면 `DATA_DIR / f"{args.ticker}_agents.json"`에 `write_text`. **허용 목록 검사 없음**, 저장 전 스키마 검사 없음, 임시 파일 교체 없음 |
| `backend/app/main.py` | 라우트: `/health`, `/api/settings/notion`(GET·PUT·DELETE), `/api/report/notion`, `/api/github/issues`, `/api/stocks/{code}/ohlcv`, `/api/stocks/{code}/indicators`. **뉴스 라우트 없음.** 차트 구간에 `DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"`, `CHART_STOCK_CODES = frozenset({"005930","000660","009150","008490"})`, 단일 파일 접근 헬퍼 `_read_ohlcv_document`, 허용목록-선-검사 `_load_ohlcv_or_404`가 있다. import 블록은 `from app import auth, config, indicators` |
| `backend/tests/` | `__init__.py`, `conftest.py`, `test_chart.py`, `test_indicators.py`, `test_notion_settings.py`. 뉴스 테스트 없음 |
| `backend/requirements.txt` | `fastapi==0.141.1`, `uvicorn[standard]==0.52.4`, `httpx==0.27.0`, `python-dotenv==1.2.2`. **`pytest` 없음**(CI가 따로 설치한다). 파일 머리에 "ASCII only — cp949 한글 Windows에서 `pip install -r`가 깨진다"는 주의가 적혀 있다 |
| `backend/requirements-dev.txt` | 존재한다. CI 기능 단계 ①은 이 파일을 설치하지 않으므로, 여기 있는 개발 도구는 CI에서 쓰이지 않는다 |
| `backend/tests/conftest.py` | `backend/`를 `sys.path`에 넣어 `from app.xxx import ...`가 저장소 루트에서도 동작하게 한다 |
| `backend/tests/test_chart.py` | 픽스처가 `monkeypatch.setattr(main, "DATA_DIR", tmp_path)`로 **모듈 전역 `DATA_DIR`를 교체**하고, `TestClient(main.app)`로 호출한다. 신규 코드가 import 시점에 경로를 확정하면 이 교체가 무력화된다(§A.2 결정 3) |
| `.github/workflows/ci.yml` | 단일 job `lint-and-test`. `steps:` 배열은 11개이고 그중 기능 단계는 8개다: ① `pip install -r backend/requirements.txt ruff pytest` → ② `npm ci`(frontend) → ③ `ruff check backend/` → ④ `npm run lint`(frontend) → ⑤ `pytest backend/tests/ -v`(`env: DATABASE_URL: ${{ secrets.DATABASE_URL }}`) → ⑥ `npm run build`(frontend) → ⑦ `pip-audit`(`continue-on-error: true`) → ⑧ `npm audit --audit-level=high`(`continue-on-error: true`). 나머지 3개는 `actions/checkout@v4`·`setup-python@v5`·`setup-node@v4`다. **차단 게이트는 ③~⑥ 네 개**이고 ⑦·⑧은 경고다 |
| `ruff.toml` (저장소 루트) | `select` 미지정 → ruff 기본 규칙(E4·E7·E9·F)만 적용된다. **`E501`(줄 길이)은 비활성이다.** `[lint.flake8-bugbear] extend-immutable-calls`로 FastAPI `Depends` 계열만 예외 처리 |
| `scripts/tests/` | `test_fetch_ohlcv.py` 한 개. CI 테스트 단계가 `backend/tests/`만 지정하므로 이 디렉터리는 CI에서 실행되지 않는다. **본 SPEC은 `scripts/`를 수정하지 않으므로 이 제약이 걸리지 않는다**(§A.2 결정 4) |
| `frontend/src/app/dashboard/page.tsx` | `:16` `const API = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000'`. `:18-23` `MOCK_STOCKS`. `:25-29` `MOCK_NEWS`(`{title, time}` 3건). `:48` `selectedStock` 상태. `:117-122` `<Link href="/settings">`. `:205-217` 차트 구간(`StockChart` 사용). `:220-230` 뉴스 렌더 구간. `:50-56` Supabase 미인증 시 `/login` 리다이렉트 |
| `frontend/src/components/` | `StockChart.tsx` 하나. `StockChart.tsx:12`도 `NEXT_PUBLIC_API_URL ?? 'http://localhost:8000'` 관례를 따른다 |
| `frontend/package.json` | devDependencies는 `@types/*`·`autoprefixer`·`eslint`·`eslint-config-next`·`postcss`·`tailwindcss`·`typescript`. **jest·vitest·`@testing-library` 없음** — 컴포넌트 테스트 인프라가 존재하지 않는다. scripts는 `dev`·`build`·`start`·`lint` 네 개이며 `test` 스크립트가 없다 |
| `docs/weekly/WEEK_10.md` | 존재한다 |
| `.moai/config/sections/language.yaml` | `code_comments: ko` — 신규 코드 주석과 MX 태그 설명은 한국어로 쓴다 |

## A.2 기술 결정

되돌리기 비용이 큰 순서로 적는다. 앞의 결정이 바뀌면 뒤가 전부 따라 바뀐다.

### 결정 1 — 데이터 계약과 세 술어의 단일 정의 (되돌리기 비용 최상)

`spec.md` §4가 확정한 네 가지를 따른다.

- **「유효한 뉴스 문서」** — REQ-001(운영자 확인)과 REQ-002·REQ-006(백엔드 검사)이 **같은 네 조건**을 쓴다. 정의는 `spec.md` §4 한 곳에만 있다. 검사 코드를 어디에 두든 네 조건을 항목 단위로 옮겨 적고, 테스트 케이스도 같은 네 조건에서 뽑는다.
- **「뉴스 정렬 규칙」** — 백엔드가 정렬하고(REQ-002) 프론트엔드는 받은 순서를 바꾸지 않는다(REQ-008). 정렬 책임을 한쪽에만 두어야 "화면마다 순서가 다르다"가 생기지 않는다.
- **「안전한 링크」** — 프론트엔드가 판정한다. 근거는 `spec.md` §4에 적혀 있다.
- **응답 계약** — 최상위 키 `stock_code`·`news` 두 개. `financials`는 실리지 않는다(REQ-003).

이 결정이 바뀌면 백엔드·화면·테스트가 전부 따라 바뀐다. 구현 착수 전에 확정되어야 한다.

### 결정 2 — 뉴스 영역의 표시 상태 다섯 가지 (되돌리기 비용 상)

화면 구조를 먼저 정한다. 나중에 바꾸면 컴포넌트 구조와 수동 검증 절차를 함께 다시 써야 한다. 뉴스 영역은 항상 아래 다섯 상태 중 정확히 하나다.

| 상태 | 진입 조건 | 표시 | REQ |
|---|---|---|---|
| 미선택 | `selectedStock === null` | "종목을 선택하면 해당 종목의 뉴스가 표시됩니다" 류의 안내 | REQ-010 |
| 로딩 | 요청 진행 중 | 로딩 표시 | REQ-010 |
| 목록 | `200` + `news.length > 0` | 정렬된 뉴스 목록 + 스냅샷 문구 | REQ-008·REQ-009·REQ-012 |
| 빈 목록 | `200` + `news.length === 0` | "수집된 뉴스가 없습니다" 류의 안내 | REQ-010 |
| 오류 | 네트워크 오류 · `404` · `500` | 오류 안내(빈 목록과 다른 문구) | REQ-010 |

네 개의 비목록 상태가 **서로 구분되는 문구**를 갖는 것이 REQ-010의 핵심이다. "데이터 없음" 하나로 뭉치면 서흥 파일이 아직 없어서 `404`인 경우와 수집 결과가 0건인 경우를 사용자가 구분할 수 없다.

`008490` 파일이 없는 동안 서흥을 선택하면 오류 상태가 나오는 것이 정상 동작이며, REQ-001이 그 상태를 해소한다.

### 결정 3 — 신규 모듈 위치와 데이터 경로 바인딩 (되돌리기 비용 중)

**신규 코드는 `backend/app/news.py`에 둔다.** `main.py`에는 (a) import 한 줄과 (b) 라우트 등록 구간만 추가한다. `SPEC-PORTFOLIO-001`도 `main.py` 끝에 구간을 덧붙이므로(그 SPEC의 `plan.md` §A.4), `main.py`에 넣는 줄 수를 줄이면 병합 충돌 범위가 그만큼 줄어든다.

**데이터 경로는 요청 시점에 `main.DATA_DIR`로부터 해석한다.** 기존 테스트 전략이 `monkeypatch.setattr(main, "DATA_DIR", tmp_path)`로 모듈 전역을 교체하기 때문이다(§A.1). `news.py`가 자기 모듈 전역에 `NEWS_DIR = ...`를 두거나 import 시점에 `DATA_DIR / f"{code}_agents.json"`을 확정하면 그 교체가 무력화되고 임시 디렉터리 픽스처 전략이 깨진다.

구체적으로는 `news.py`가 **디렉터리를 인자로 받는 함수**를 노출하고 `main.py`가 호출 시점에 `DATA_DIR`를 넘긴다. 이렇게 하면 `news.py`가 `main`을 import할 필요가 없어 순환 import도 생기지 않는다. `SPEC-PORTFOLIO-001` 1차 감사의 D8(`PORTFOLIO_ANALYSIS_FILE` 모듈 전역 바인딩과 `monkeypatch` 전략의 충돌)이 지적한 것과 같은 함정이며, 여기서는 착수 전에 피한다.

### 결정 4 — 검증 파일의 위치 (되돌리기 비용 중)

**자동 테스트는 `backend/tests/test_news.py` 한 곳에만 둔다.** CI 기능 단계 ⑤가 `pytest backend/tests/ -v`이므로 이 파일은 **CI에서 실행된다**. `scripts/tests/`는 CI 테스트 단계 밖이지만(§A.1), 본 SPEC은 `scripts/`를 수정하지 않으므로 그쪽에 테스트를 둘 이유가 없다. 결과적으로 `.github/workflows/ci.yml`을 손댈 필요가 없다 — `SPEC-PORTFOLIO-001` M4가 같은 파일의 테스트 단계를 고치므로, 본 SPEC이 그 파일을 건드리지 않는 것 자체가 충돌 회피다.

화면 요구사항(REQ-008~REQ-014)은 자동 판정 수단이 없다. `frontend/package.json`에 테스트 프레임워크가 없고 도입은 범위 밖이므로(`spec.md` §5), `docs/weekly/WEEK_10.md`의 수동 검증 절차가 유일한 판정 근거다(M2 산출물, 요건은 `acceptance.md`).

### 결정 5 — 기각한 대안

| 후보 | 판단 |
|------|------|
| **기존 `data/{code}_agents.json`의 `news` 재사용** | **채택.** 파일이 이미 커밋되어 있고 형태도 그대로 쓸 수 있다. 백엔드는 읽기만 한다 |
| 새 `data/{code}_news.json` 형식 신설 | 기각. 같은 데이터가 두 파일에 중복되고, 수집 스크립트를 고쳐 두 파일을 함께 쓰게 만들어야 하며, 둘이 어긋날 때 어느 쪽이 맞는지 판단할 근거가 없다. 스크립트 변경은 §A.2 결정에서 피하려는 범위 확대 그 자체다 |
| 요청 시 뉴스 수집 | 기각. `scripts/orchestrate_stock_agents.py`의 `claude -p` 타임아웃이 180초다. 요청 하나가 최대 3분 걸리고, 방문 수만큼 Claude 사용량이 소모된다(팀원 전원 Pro 플랜). 발표 시연 중 한도에 걸리면 뉴스 영역이 비어 버린다 |
| `date` 값을 ISO로 정규화해 저장 | 기각. `"2026-07 (중순)"`을 특정 일자로 바꾸면 원본에 없던 정밀도를 만들어 낸다. 어느 날로 바꿀지에 정답이 없고, 한 번 덮어쓰면 원문을 되돌릴 수 없다. 표시는 원문 그대로 두고 순서만 정한다 |
| 뉴스 전용 페이지(`/news`) 신설 | 기각. 대시보드에 이미 종목 선택 상태(`selectedStock`)와 뉴스 영역 자리가 있다. 새 라우트를 만들면 종목 선택을 그 페이지에서 다시 구현해야 한다 |
| 백엔드에서 안전하지 않은 `url` 제거 | 기각. 근거는 `spec.md` §4 「안전한 링크」에 적어 두었다 — 응답을 저장 내용의 그대로 내보내는 계약으로 정의했고, 백엔드가 조용히 지우면 화면이 "링크 없음"과 "안전하지 않은 링크"를 구분할 수 없다 |

## A.3 마일스톤

세 마일스톤은 **순차 진행한다.** 병렬 진행을 주장하지 않는다 — M2의 산출물인 수동 검증 절차를 실행하려면 M1이 만든 엔드포인트와 `008490` 데이터가 있어야 하고, M3는 M1·M2의 결과를 기록한다. (M2의 컴포넌트 코드 자체는 `spec.md` §4 응답 계약만으로 작성할 수 있지만, 작성과 검증을 분리해 부분 진행을 주장하면 순서가 모호해지므로 그렇게 계획하지 않는다.)

### M1 — 데이터 확보 + 백엔드 엔드포인트

- **운영자 수동 단계**: `python scripts/orchestrate_stock_agents.py 008490 --save` 1회 실행 → `data/008490_agents.json` 생성 → `spec.md` §4 「유효한 뉴스 문서」 네 조건 충족 확인 → 커밋 (REQ-001)
- `backend/app/news.py` 신설 — 디렉터리를 인자로 받는 파일 읽기 헬퍼 1개 + 「유효한 뉴스 문서」 검사 + 「뉴스 정렬 규칙」 정렬
- `backend/app/main.py`에 import 한 줄과 `GET /api/stocks/{code}/news` 라우트 등록 구간 추가. 허용 목록 검사는 파일 접근보다 **먼저** 수행한다 (REQ-005, `_load_ohlcv_or_404`와 같은 모양)
- 허용 목록 상수는 `CHART_STOCK_CODES`를 그대로 쓰지 않고 뉴스용 상수를 따로 둘지 결정한다. 값은 같지만 `SPEC-CHART-001`의 상수에 결합하면 그쪽 종목 범위가 바뀔 때 뉴스 범위가 조용히 따라 움직인다 — 별도 상수를 권한다
- `backend/tests/test_news.py` 신설 — `monkeypatch.setattr(main, "DATA_DIR", tmp_path)` 픽스처 기반. 스키마 위반 케이스는 「유효한 뉴스 문서」 네 조건에서 각각 1건 이상 뽑는다
- 커버: REQ-001~REQ-007 / AC-001~AC-007

> **운영 주의.** `008490` 생성은 `claude -p` 호출이므로 Claude 사용량을 소모하며 자동화할 수 없다. **먼저 `python scripts/orchestrate_stock_agents.py 008490 --save`를 실제로 1회 실행한다** — 실행하지 않고 건너뛰면 아래 예외가 성립하지 않는다. 실행이 실패하면 M1은 나머지 항목(엔드포인트 + 테스트)까지 완료하고, `008490`에 대해서는 실행한 명령과 실패 출력, REQ-004의 `404` 경로가 그대로 동작한다는 사실, 미생성 사유를 `progress.md`에 기록한 뒤 AC-001을 `FAIL(차단됨)`으로 남긴다. 이 상태로 SPEC을 닫으려면 `acceptance.md` 「AC-001 예외 조항」의 세 조건 — ① 수집을 실제로 시도하고 명령과 실패 출력을 기록, ② AC-004와 AC-010 (c) 오류 상태가 모두 PASS, ③ 사유·후속 조치·파일 부재 사실을 기록 — 을 모두 충족해야 하며, 증거는 `progress.md`의 「AC-001 예외 기록」 표에 적는다. 예외는 AC-001에만 적용되고 REQ-004의 `404` 동작을 완화하지 않는다. 허위 PASS를 적지 않는다.

### M2 — 프론트엔드 뉴스 영역 + 수동 검증 절차

- `frontend/src/components/StockNews.tsx` 신설 — `stockCode`를 props로 받아 `GET /api/stocks/{code}/news`를 호출하고 §A.2 결정 2의 다섯 상태를 렌더링한다. `StockChart.tsx`의 구조(훅 순서, 타입 선언 위치, `API` 상수 관례)를 그대로 따른다 (REQ-008~REQ-012, REQ-014)
- `frontend/src/app/dashboard/page.tsx` — `MOCK_NEWS` 상수(`:25-29`) 삭제, 뉴스 렌더 구간(`:220-230`)을 `StockNews` 사용으로 교체, import 한 줄 추가 (REQ-013). **다른 구간은 건드리지 않는다**(§A.6)
- 직전 요청 무효화 처리 — 종목을 빠르게 바꿔도 이전 종목의 응답이 표시되지 않게 한다 (REQ-011)
- **`docs/weekly/WEEK_10.md`에 「대시보드 뉴스 영역 수동 검증 절차」 절 신설** — AC-008~AC-014와 AC-015의 대시보드 항목 각각에 대해 준비 / 실행 / 관찰 대상 / PASS 조건 네 줄. 응답 지연이 전제인 AC-010 (b)·AC-011은 브라우저 개발자도구 네트워크 탭의 **사용자 지정 스로틀링 프로파일**(이름 `news-delay`, 지연 5000ms, 대역폭 제한 없음)을 준비 수단으로 지목하고, 검증 후 `No throttling`으로 되돌리는 단계까지 적는다 — 저장소 파일도 신규 의존성도 건드리지 않는 수단이다. 스로틀링을 쓸 수 없는 환경이면 두 AC를 수행 불가로 기록한다. 요건은 `acceptance.md` 「수동 검증 절차 문서의 요건」과 「지연 상태를 만드는 방법」에 있다
- 자동 보조 게이트(`npm run lint`, `npm run build`)는 빌드·린트 측면만 보증하며 화면 동작의 PASS 근거가 아니다
- 커버: REQ-008~REQ-014 / AC-008~AC-014

### M3 — 문서 동기화 + 품질 게이트

- `docs/weekly/WEEK_10.md`에 모듈 요약과 실행 절차(스크립트 → 커밋 → 백엔드 → 화면) 기록 (M2가 쓴 수동 검증 절차 절과는 다른 절)
- 뉴스 재수집 절차(`python scripts/orchestrate_stock_agents.py <코드> --save`)를 주차 문서에 명시
- `ruff check backend/`, `npm run lint`, `npm run build`, `pytest backend/tests/ -v` 실행
- M2가 작성한 수동 검증 절차를 1회 실행하고 결과를 기록
- AC-001~AC-015 PASS/FAIL 매트릭스를 `progress.md`에 작성. 수동 판정 AC는 `docs/weekly/WEEK_10.md`의 해당 PASS 조건을 인용한다
- 커버: REQ-015 / AC-015 + 완료 정의 전체

## A.4 마일스톤별 파일 소유권

| 마일스톤 | 쓰기 허용 파일 | 선행 조건 |
|---|---|---|
| M1 | `data/008490_agents.json`(신규), `backend/app/news.py`(신규), `backend/app/main.py`(import 1줄 + 라우트 구간 추가), `backend/tests/test_news.py`(신규) | 없음 |
| M2 | `frontend/src/components/StockNews.tsx`(신규), `frontend/src/app/dashboard/page.tsx`(import 1줄 + `MOCK_NEWS` 삭제 + 뉴스 구간 교체), `docs/weekly/WEEK_10.md`의 「대시보드 뉴스 영역 수동 검증 절차」 절 | M1 완료 |
| M3 | `docs/weekly/WEEK_10.md`(수동 검증 절차 절을 제외한 나머지), `.moai/specs/SPEC-NEWS-001/progress.md` | M1·M2 완료 |

### `SPEC-PORTFOLIO-001`과 겹치는 파일

두 SPEC은 의존 관계가 없지만 세 파일을 함께 건드린다. 아래가 겹침의 전부이며, 어느 것도 같은 줄을 서로 고치지 않는다.

| 파일 | `SPEC-PORTFOLIO-001` | 본 SPEC | 겹침 판정 |
|---|---|---|---|
| `backend/app/main.py` | M2가 파일 **끝에** 구간 주석 + `PORTFOLIO_ANALYSIS_FILE` + `_read_portfolio_document()` + `GET /api/portfolio`를 추가 | M1이 import 블록에 한 줄, 파일 **끝에** 짧은 라우트 등록 구간을 추가 | 기존 함수 본문은 양쪽 다 고치지 않는다. 충돌 가능 지점은 파일 끝에 두 구간이 나란히 붙는 곳뿐이며, 양쪽 모두 **추가만** 하므로 병합 시 두 구간을 이어 붙이면 해소된다. 본 SPEC이 `main.py`에 넣는 양을 import 1줄 + 라우트 구간으로 줄인 이유가 이것이다(§A.2 결정 3) |
| `frontend/src/app/dashboard/page.tsx` | M3가 **헤더 구간**(`:117-122` 부근)에 `/portfolio` 링크 1개 추가. import는 추가하지 않는다(`Link`는 `:11`에 이미 있다) | M2가 **import 블록**에 한 줄, `:25-29` `MOCK_NEWS` 삭제, `:220-230` 뉴스 구간 교체 | 구간이 완전히 분리된다. 헤더(`:113-130`)와 뉴스(`:220-230`)는 서로 다른 영역이고, import 블록은 본 SPEC만 건드린다 |
| `docs/weekly/WEEK_10.md` | M3가 「`/portfolio` 화면 수동 검증 절차」, M4가 모듈 요약 | M2가 「대시보드 뉴스 영역 수동 검증 절차」, M3가 모듈 요약 | 서로 다른 절이다. 둘 다 절 추가 방식이므로 병합 시 순서만 정리하면 된다 |
| `.github/workflows/ci.yml` | M4가 "Backend 테스트" 단계 한 줄 수정 | **건드리지 않는다**(§A.2 결정 4) | 겹치지 않는다 |

## A.5 리스크

| 리스크 | 영향 | 완화 |
|---|---|---|
| 에이전트 출력이 「유효한 뉴스 문서」를 벗어남 | `008490` 수집 결과에 필수 4키 중 하나가 빠지거나 `news`가 리스트가 아니면 그 종목 뉴스가 `500`이 된다. `news-collector` 선언 스키마와 실물이 이미 `url`에서 어긋나 있으므로(§A.1) 재현이 보장되지 않는다 | 운영자가 커밋 전에 네 조건을 확인한다(REQ-001). 백엔드도 읽을 때 같은 술어로 다시 검사하고 위반 시 명시적으로 `500`을 낸다(REQ-006) — 반쯤 렌더링된 화면보다 명시적 실패가 낫다 |
| `008490` 생성 실패 | `claude` 미설치·사용량 한도·네트워크 차단이면 파일을 만들 수 없다. 이 SPEC에서 유일하게 외부 의존이 있는 단계다 | 파일이 없으면 REQ-004의 `404` 경로가 동작하고 화면은 오류 상태를 표시한다(§A.2 결정 2) — 기능이 깨지지 않는다. 실패 시 명령·출력·사유를 `progress.md`에 기록하고 AC-001을 `FAIL(차단됨)`으로 남긴다. SPEC 종결 조건은 `acceptance.md` 「AC-001 예외 조항」의 세 조건이다 |
| 허용 목록 밖 파일 노출 | `data/005380_agents.json`이 이미 존재한다. 허용 목록 검사가 파일 접근 뒤에 오면 이 파일이 서빙된다 | 허용 목록 검사를 파일 접근보다 **먼저** 수행하고(REQ-005), AC-005가 mock으로 "파일 시스템에 접근하지 않았음"을 검사한다. 기존 `_load_ohlcv_or_404`와 같은 패턴이다 |
| `url` 스킴 안전성 | 수집이 `javascript:` 같은 값을 넣으면 제목 링크가 스크립트 실행 경로가 된다 | `spec.md` §4 「안전한 링크」를 화면이 판정하고, 만족하지 않으면 앵커를 아예 만들지 않는다(REQ-009). AC-009가 `http`/`https`/비http/부재 네 경우를 검사한다 |
| `main.py` 병합 겹침 | `SPEC-PORTFOLIO-001` M2가 같은 파일 끝에 구간을 붙인다 | 신규 로직을 `backend/app/news.py`로 분리해 `main.py` 추가분을 import 1줄 + 라우트 구간으로 줄인다(§A.2 결정 3, §A.4) |
| `dashboard/page.tsx` 병합 겹침 | 두 SPEC이 같은 파일을 고친다 | 본 SPEC의 수정은 import 1줄 + `MOCK_NEWS` 삭제 + 뉴스 구간 교체로 한정한다. 헤더·테이블·차트·이슈·Notion 구간은 손대지 않는다(§A.6) |
| 테스트가 커밋된 데이터에 묶임 | `data/*_agents.json`의 내용이 바뀌면 기대값이 흔들린다 | `test_news.py`는 임시 디렉터리 픽스처로만 검증한다(`test_chart.py`와 동일). 커밋된 파일에 대해서는 「유효한 뉴스 문서」 적합성 테스트 하나만 둔다 |
| 경로 바인딩과 `monkeypatch` 충돌 | 신규 코드가 import 시점에 경로를 확정하면 기존 테스트 전략이 깨진다 | 요청 시점에 `main.DATA_DIR`로부터 해석한다(§A.2 결정 3) |
| `ruff check backend/` 게이트 | 신규 백엔드 코드의 ruff 기본 규칙 위반으로 CI가 멈춘다. 실제로 걸리는 것은 미사용 import(F401)·미정의 이름(F821) 계열이며, **줄 길이(E501)는 루트 `ruff.toml`에서 비활성이다**(§A.1) | 커밋 전 `ruff check backend/` 로컬 실행. `main.py` 기존 구간과 같은 스타일 유지 |
| `npm run lint` / `npm run build` 게이트 | 신규 컴포넌트의 미사용 변수·`any`·훅 의존성 경고. 차단 게이트 ④·⑥에 해당한다 | `StockChart.tsx`의 구조를 그대로 따른다. 커밋 전 `npm run lint` + `npm run build` |
| Windows/WSL 경로·인코딩 | 이 저장소에서 두 번 발생했다 — `requirements.txt` 한글 주석의 cp949 디코딩 실패, `.env` 상대 경로가 실행 디렉터리에 의존해 503 | 새 경로는 `DATA_DIR`(이미 `__file__` 기준)를 재사용한다. 파일 읽기에 `encoding="utf-8"`을 명시한다(`_read_ohlcv_document`와 동일) |
| 화면 AC의 자동 검증 수단 부재 | AC-008~AC-014가 "눈으로 봤다"로 흘러가 판정 근거가 남지 않는다 | 수동 검증 절차를 M2 산출물로 고정하고 AC별 PASS 조건을 이진 서술로 적는다. `progress.md` 매트릭스가 그 조건을 인용하지 않은 항목은 PASS로 보지 않는다(`acceptance.md` 품질 게이트) |

## A.6 PRESERVE 목록 (수정 금지)

| 경로 | 사유 |
|------|------|
| `backend/app/main.py`의 기존 라우트 전체와 차트 구간(`DATA_DIR`·`CHART_STOCK_CODES`·`_read_ohlcv_document`·`_load_ohlcv_or_404`) | REQ-015 — 신규 라우트 등록만 추가하고 기존 함수 본문은 고치지 않는다. `DATA_DIR`는 값을 읽어 쓸 뿐 재정의하지 않는다 |
| `backend/app/indicators.py`, `auth.py`, `config.py` | 본 SPEC 범위 밖 |
| `backend/requirements.txt` | 신규 런타임 의존성 없음. 표준 라이브러리와 기존 FastAPI만 쓴다 |
| `backend/tests/test_chart.py`·`test_indicators.py`·`test_notion_settings.py`·`conftest.py` | 기존 테스트. 신규 파일만 추가한다 |
| `dashboard/page.tsx`의 `MOCK_STOCKS`·헤더·포트폴리오 요약·보유 종목 테이블·`StockChart` 구간·GitHub 이슈 구간·`saveToNotion` | REQ-015 — 뉴스 구간 교체와 import 1줄 외 수정 금지. `MOCK_STOCKS` 제거는 `SPEC-API-001` 소관(`spec.md` §5) |
| `frontend/src/components/StockChart.tsx` | `SPEC-CHART-001`의 자산 |
| `frontend/package.json` | 프론트엔드 테스트 프레임워크 도입은 범위 밖(`spec.md` §5). 의존성 추가 금지 |
| `.github/workflows/ci.yml` | 본 SPEC은 CI를 바꾸지 않는다(§A.2 결정 4). `SPEC-PORTFOLIO-001` M4가 같은 파일을 고치므로 더욱 건드리지 않는다 |
| `scripts/` 전체(`orchestrate_stock_agents.py`·`fetch_ohlcv.py`·`orchestrate_portfolio.py`·`tests/`) | `spec.md` §5 — 수집 스크립트 변경은 범위 밖 |
| `.claude/agents/news-collector.md`, `financial-data.md` | 수집 로직·출력 스키마 변경은 범위 밖 |
| `data/`의 기존 파일 전체(`*_agents.json`·`*_market.json`·`*_fundamentals.json`·`*_ohlcv.json`·`portfolio*.json`) | 읽기 전용. 본 SPEC은 `008490_agents.json`만 새로 만든다 |
| `.moai/specs/SPEC-API-001/`, `SPEC-CHART-001/`, `SPEC-PORTFOLIO-001/` | 다른 SPEC의 산출물 |
| `.moai/state/`, `.moai/cache/`, `.moai/logs/` | 런타임 관리 파일 |

## A.7 신규 파일 목록

```
data/008490_agents.json                    서흥 뉴스·재무 (M1에서 운영자가 생성·커밋)
backend/app/news.py                        뉴스 문서 읽기 + 스키마 검사 + 정렬
backend/tests/test_news.py                 엔드포인트 검증 (AC-002~AC-007)
frontend/src/components/StockNews.tsx      대시보드 뉴스 영역 컴포넌트
```

수정 파일: `backend/app/main.py`(import 1줄 + 라우트 등록 구간), `frontend/src/app/dashboard/page.tsx`(import 1줄 + `MOCK_NEWS` 삭제 + 뉴스 구간 교체), `docs/weekly/WEEK_10.md`(M2의 수동 검증 절차 절 + M3의 모듈 요약·재수집 절차).

## A.8 MX 태그 계획

`code_comments: ko`이므로 태그 설명은 한국어로 쓴다.

| 대상 | 태그 | 내용 |
|---|---|---|
| `news.py`의 파일 읽기 헬퍼 | `@MX:ANCHOR` | 파일 시스템 접근 단일 지점. "요청 경로가 `data/`에 쓰지 않는다"(REQ-007)와 파싱·스키마 실패 처리(REQ-006)가 이 함수 하나에 걸려 있다. 우회 접근 경로가 생기면 두 요구사항이 동시에 무너진다 |
| `news.py`의 정렬 함수 | `@MX:NOTE` | 날짜를 두 갈래(파싱 가능/불가)로 나눠 정렬하고 원문 문자열은 고치지 않는 이유(`spec.md` §4·§1.2 결정 2). 주석이 없으면 "날짜를 정규화하면 간단해진다"는 방향으로 되돌아간다 |
| `main.py`의 허용 목록 선검사 지점 | `@MX:ANCHOR` | 허용 목록 검사가 파일 접근보다 먼저 와야 한다(REQ-005). `data/005380_agents.json`이 실제로 존재하므로 순서가 뒤집히면 허용 목록 밖 종목이 바로 노출된다. AC-005가 mock으로 이 순서를 검사한다 |
| `main.py`의 응답 조립부 | `@MX:NOTE` | `financials`·`ticker`·`name`을 싣지 않는 이유(REQ-003) — `financials` 스키마는 `financial-data` 에이전트가 독립적으로 정하므로 뉴스 계약이 거기에 묶이면 함께 깨진다 |
| `StockNews.tsx`의 링크 렌더 분기 | `@MX:NOTE` | 스킴 검사를 거치지 않은 `url`로 앵커를 만들지 않는 이유(`spec.md` §4 「안전한 링크」). `url`은 `news-collector` 선언 스키마에 없는 선택 필드라 값의 형태를 보장할 수 없다 |
| `StockNews.tsx`의 요청 무효화 처리 | `@MX:NOTE` | 종목을 빠르게 바꿀 때 이전 응답이 늦게 도착해 덮어쓰는 경로를 막는다(REQ-011). 제거하면 화면에는 아무 오류도 보이지 않고 잘못된 종목의 뉴스만 남는다 |

## A.9 미해결 사항

- **`008490` 수집 실행 가능 여부 미확인.** `claude -p` 호출이 이 환경에서 성공하는지 확인하지 못했다. M1에서 처음 검증한다. 실패 시 처리는 §A.3 M1의 운영 주의와 §A.5 리스크 표에 있다.
- **기존 테스트의 현재 통과 여부 미확인.** `pytest backend/tests/ -v`·`npm run lint`·`npm run build`를 실행하지 않았다(이 환경에 `pytest` 미설치). AC-015가 전제하는 "기존 테스트 통과"의 현재 상태는 조사 범위 밖이며, M1 착수 시 기준선으로 1회 실행해 확인한다.
- **`008490` 수집 결과의 `date` 형태 미확인.** 허용 목록 4종목의 커밋된 파일에는 파싱 불가 날짜가 없다. 파싱 불가 값이 실제로 발생한다는 증거는 허용 목록 밖 `data/005380_agents.json`뿐이다. 따라서 정렬 규칙의 "파싱 불가" 갈래는 **현재 커밋된 허용 목록 데이터만으로는 화면에서 실증할 수 없다.** AC-004(백엔드 정렬)는 픽스처로 검사하고, 화면 쪽 확인이 필요하면 수동 검증 절차에서 임시 픽스처 파일을 쓰도록 M2에서 절차를 적는다.
- **커버리지 측정 범위.** CI 기능 단계 ①은 `backend/requirements.txt` + `ruff` + `pytest`만 설치하고 `backend/requirements-dev.txt`를 설치하지 않으므로, 커버리지를 CI에서 강제할 수 없다. `requirements-dev.txt`의 내용은 이번 조사에서 읽지 않았다 — 커버리지 측정이 필요하면 M3에서 그 파일을 확인한 뒤 로컬 1회 측정해 `progress.md`에 기록한다. 본 SPEC은 커버리지 수치를 게이트로 삼지 않는다.
