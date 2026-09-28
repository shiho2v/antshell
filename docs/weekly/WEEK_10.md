# WEEK_10 — 10주차 작업 계획

**날짜:** 2026-09-20 | **발표자:** 정우준 | **챕터:** Ch.09 (2/2) | **난이도:** 고급

## 이번 주 목표
에이전트 팀 병렬 개발·스킬 생태계·빌더 에이전트

## 발표자 작업 목록
- [x] 담당 챕터 정독 및 핵심 개념 3가지 정리
- [x] 주식 웹 적용 기능 개발 (아래 참고) — 코드·자동 게이트 완료, 화면 수동 검증은 발표 전 실행 필요
- [ ] `feature/10-정우준-portfolio-news` 브랜치 생성 후 PR 오픈
- [ ] Notion 발표 페이지 초안 작성 (D-1까지)

## 주식 웹 적용
포트폴리오·뉴스 모듈 팀 병렬 빌드 + /moai sync 문서화

## 발표 구성 (70분)
| 시간 | 내용 |
|------|------|
| 0~5분 | 지난 주 이어서 + 이번 챕터 위치 설명 |
| 5~25분 | 챕터 핵심 개념 설명 (자신의 말로) |
| 25~55분 | 주식 웹 적용 실시연 |
| 55~70분 | Q&A + 막힌 점 공유 + 다음 주 예고 |

## 팀원 사전 준비
없음

## 다음 주 예고
발표자: **주경희** | 챕터: Ch.10

## `/portfolio` 화면 수동 검증 절차

SPEC-PORTFOLIO-001 M3 산출물. 이 저장소에는 프론트엔드 테스트 프레임워크가 없으므로(`spec.md` §5, 도입은 범위 밖), 아래 절차가 AC-009~AC-015 및 AC-016 대시보드 항목의 유일한 PASS 판정 근거다. 자동 보조 게이트(`npm run lint`, `npm run build`, `npx tsc --noEmit`)는 빌드·타입·린트만 보증하며 화면 동작의 근거가 아니다.

### AC-009 — 종목별 밸류에이션·리스크·리밸런싱 표시
1. **준비**: `python scripts/orchestrate_portfolio.py --sample --save-json data/portfolio_analysis.json`로 샘플 데이터를 생성한다 (최소 한 종목은 정상 판정, 최소 한 종목은 `unknown`을 포함 — REQ-004).
2. **실행**: `uvicorn app.main:app --reload` (backend/) → `npm run dev` (frontend/) → `http://localhost:3000/portfolio` 접속.
3. **관찰 대상**: 「종목별 분석」 표의 각 행.
4. **PASS 조건**: 보유 종목 각각에 대해 밸류에이션 배지(+점수), 리스크 배지, 리밸런싱 액션 배지, 드리프트(%), 리밸런싱 금액(원)이 모두 표시되면 PASS.

### AC-010 — 기준일·생성일·스냅샷·샘플 표기
1. **준비**: AC-009와 동일한 샘플 데이터 상태.
2. **실행**: `/portfolio` 접속.
3. **관찰 대상**: 상단 메타 정보 영역.
4. **PASS 조건**: "보유 종목 기준일"과 "분석 생성일" 레이블이 각각 다른 날짜와 함께 표시되고, "실시간 시세가 아닌 스냅샷" 문구가 보이며, `source`가 `"sample"`이므로 "샘플 데이터" 배지가 보이면 PASS.

### AC-011 — 요청 실패 시 영역 한정 오류 표시
1. **준비**: 백엔드 서버를 중지한다 (또는 `data/portfolio_analysis.json`을 임시로 이동해 404를 유발).
2. **실행**: `npm run dev` (frontend만 실행) → `/portfolio` 접속.
3. **관찰 대상**: 분석 결과 영역과 헤더 영역.
4. **PASS 조건**: 헤더(제목·이메일·대시보드 링크)는 정상 렌더링되고, 분석 결과 영역에만 오류 문구가 표시되며, 콘솔에 처리되지 않은 예외가 없고 화면이 하얗게 깨지지 않으면 PASS.

### AC-012 — 미인증 접근 시 로그인 리다이렉트
1. **준비**: 로그아웃 상태 (Supabase 세션 없음).
2. **실행**: 주소창에 `http://localhost:3000/portfolio` 직접 입력.
3. **관찰 대상**: 브라우저 주소창.
4. **PASS 조건**: `/login`으로 이동하면 PASS.

### AC-013 — 대시보드 → 포트폴리오 링크
1. **준비**: 로그인 상태.
2. **실행**: `/dashboard` 접속 후 헤더의 "포트폴리오 분석" 링크 클릭.
3. **관찰 대상**: 대시보드 헤더, 클릭 후 주소창.
4. **PASS 조건**: 헤더에 링크가 보이고, 클릭 시 `/portfolio`로 이동하면 PASS.

### AC-014 — API 주소 기본값 규칙
1. **준비**: `frontend/.env.local`에 `NEXT_PUBLIC_API_URL`을 설정하지 않은 상태.
2. **실행**: `/portfolio` 접속 후 브라우저 개발자 도구 Network 탭 확인.
3. **관찰 대상**: `/api/portfolio` 요청의 대상 origin.
4. **PASS 조건**: 요청이 `http://localhost:8000/api/portfolio`로 나가면 PASS (환경 변수 설정 시에는 그 값으로 나가는지 추가 확인).

### AC-015 — `unknown` 판정의 "판정 불가" 표시
1. **준비**: AC-009와 동일한 샘플 데이터 (verdict/overall/action 중 최소 하나씩 `unknown` 포함).
2. **실행**: `/portfolio` 접속.
3. **관찰 대상**: `unknown` 값을 가진 종목의 배지.
4. **PASS 조건**: 해당 항목이 목록에서 숨겨지지 않고 "판정 불가"로 표시되며, 점선 테두리로 정상 판정(채워진 색 배지)과 시각적으로 구분되면 PASS.

### AC-016 (대시보드 영역) — 기존 기능 회귀 없음
1. **준비**: 로그인 상태, 정상 실행 중인 backend.
2. **실행**: `/dashboard` 접속.
3. **관찰 대상**: 보유 종목 테이블, 주가 차트, 최신 뉴스, GitHub 이슈, Notion 저장 버튼.
4. **PASS 조건**: 다섯 영역 모두 이전과 동일하게 정상 동작하면 PASS (백엔드 회귀는 `pytest backend/tests/ -v`로 별도 확인).

## 포트폴리오 모듈 요약 및 재생성 절차 (SPEC-PORTFOLIO-001 M4)

### 모듈 요약

`scripts/orchestrate_portfolio.py`가 보유 종목(`data/portfolio.example.json`)을 3개 서브에이전트(밸류에이션·리스크·리밸런싱)로 분석해 `data/portfolio_analysis.json`에 저장하고, 백엔드 `GET /api/portfolio`가 이 파일을 읽어 서빙하며, `/portfolio` 화면이 종목별 판정을 표시한다. 현재 커밋된 `data/portfolio_analysis.json`은 `--sample` 모드로 생성됐다(`source: "sample"`) — 실제 에이전트 팀 분석(`source: "agent-team"`)은 아직 실행되지 않았다.

### 재생성 절차

1. 실제 분석: `python scripts/orchestrate_portfolio.py --portfolio data/portfolio.example.json --save-json data/portfolio_analysis.json` (3개 서브에이전트를 `claude -p`로 순차/병렬 호출, Claude 사용량 소모, 서브에이전트당 최대 240초).
   샘플(결정론적, 에이전트 미호출): `python scripts/orchestrate_portfolio.py --portfolio data/portfolio.example.json --sample --save-json data/portfolio_analysis.json`
2. 저장된 파일이 spec.md §4 「필수 키 집합」 다섯 조건을 만족하는지 확인한다(스크립트가 저장 전에 자체 검사하므로, 종료 코드가 0이면 이미 만족된 것이다).
3. 저장소에 커밋한다.
4. 실행일(`generated_date`)과 보유 종목 기준일(`as_of`)은 서로 다를 수 있다 — 화면에 둘 다 표시된다(REQ-010).

### CI 확장

`.github/workflows/ci.yml`의 "Backend 테스트" 단계를 `pytest backend/tests/ -v`에서 `pytest backend/tests/ scripts/tests/ -v`로 확장했다(2026-09-22). 로컬에서 두 스위트가 함께 통과함을 사전 확인했다(114 passed, 1 skipped — skip은 `008490_agents.json` 미생성에 따른 예상된 스킵).

## 대시보드 뉴스 영역 수동 검증 절차 (SPEC-NEWS-001 M2)

`frontend/package.json`에 jest·vitest·`@testing-library`가 없어 컴포넌트 테스트 자동화가 불가능하므로(`spec.md` §5), AC-008~AC-014와 AC-015의 대시보드 항목은 아래 절차로 판정한다. `acceptance.md` 「검증 수단」 표가 지정한 유일한 수동 판정 근거다.

**공통 준비**: 백엔드 `uvicorn app.main:app --reload`(포트 8000) → 프론트엔드 `npm run dev` → 브라우저에서 `http://localhost:3000/dashboard` 접속 → Supabase 로그인.

### 지연 상태를 만드는 방법 (AC-010 (b) · AC-011 공통 — 스로틀링 프로파일)

- **준비**: 개발자도구 → Network 패널 → Throttling 드롭다운 → *Add…* → 이름 `news-delay`, latency **5000ms**, 대역폭 제한 없음으로 사용자 지정 프로파일을 만든다. 저장소 파일·의존성은 변경하지 않는다.
- **적용**: 검증 대상 항목을 시작하기 전 Throttling 드롭다운에서 `news-delay`를 선택한다 — 선택 시점부터 **모든 요청이 동일하게** 5초 지연된다.
- **되돌리기**: 해당 항목 검증이 끝나면 즉시 Throttling을 `No throttling`으로 되돌린다. 되돌리지 않으면 이후 항목의 관찰 결과가 흔들린다.
- **환경에 스로틀링을 쓸 수 없으면**: AC-010 (b)와 AC-011을 "수행 불가"로 기록하고, 사유와 환경을 `progress.md`에 남긴다. "확인함"으로 적지 않는다.

### AC-008 — 종목 선택 시 뉴스 표시

- **준비**: 백엔드·프론트엔드 정상 기동, 스로틀링 없음.
- **실행**: 대시보드에서 보유 종목 테이블의 삼성전자(005930) 행을 클릭한다.
- **관찰 대상**: 뉴스 영역의 항목 순서·`title`/`source`/`date`/`summary` 표시 여부. 추가로 `data/005930_agents.json`의 뉴스 항목 하나를 임시로 `title: "<b>태그</b>"`, `summary: "<img src=x onerror=alert(1)>"`로 바꾼 임시 픽스처(§ 임시 픽스처 사용 원칙)로 교체 후 다시 클릭한다.
- **PASS 조건**: 응답 순서 그대로 항목이 나열되고 네 값이 모두 보이며, `date`가 API 응답 문자열과 동일하고, 임시 픽스처 재검증에서 `<b>태그</b>`·`<img src=x onerror=alert(1)>`가 글자 그대로 보이고(굵게 표시되거나 이미지가 삽입되지 않고) 경고창이 뜨지 않는다.

### AC-009 — 링크 조건부 렌더링

- **준비**: 임시 픽스처(§ 임시 픽스처 사용 원칙)로 `news` 배열에 ①`"url": "https://example.com/a"`, ②`"url": "HTTP://example.com/b"`, ③`"url": "javascript:alert(1)"`, ④`url` 키 없음 네 항목을 놓는다.
- **실행**: 해당 종목을 선택해 뉴스 영역을 렌더링하고, ①~④ 각 제목을 클릭해 본다.
- **관찰 대상**: 각 제목이 앵커 요소인지, 클릭 시 새 탭이 열리는지.
- **PASS 조건**: ①·②는 새 탭(`target=_blank`, `rel=noopener noreferrer`)으로 해당 주소가 열리고, ③·④는 앵커가 아닌 텍스트로 표시되어 클릭해도 아무 이동이 없다.

### AC-010 — 표시할 뉴스가 없는 네 상태

- **준비**: (a) 페이지 진입 직후, (b) `news-delay` 스로틀링 적용 후 종목 선택, (c) 백엔드를 잠시 멈추거나 임시로 `404`/`500`을 반환하게 함, (d) 임시 픽스처로 `news: []` 응답을 만듦.
- **실행**: 네 상황 각각에서 대시보드를 렌더링(또는 관찰)한다.
- **관찰 대상**: 뉴스 영역의 안내 문구, 그리고 헤더·포트폴리오 요약·보유 종목 테이블·주가 차트·GitHub 이슈 영역의 정상 렌더링 여부.
- **PASS 조건**: 네 상황 모두 뉴스 영역에 안내가 뜨고 **네 문구가 서로 다르며**, 네 상황 모두 다른 대시보드 영역이 정상 렌더링되고 페이지가 예외로 중단되지 않는다.

### AC-011 — 직전 응답 무효화

- **준비**: `news-delay` 스로틀링 적용. 검증 전 `GET /api/stocks/005930/news`·`GET /api/stocks/000660/news`를 각각 1회 호출해 첫 기사 제목(`T5930`·`T0660`)을 적어 둔다.
- **실행**: 삼성전자 선택 → 약 3초 뒤 SK하이닉스 선택 → 개발자도구 Network 탭에서 두 요청이 모두 완료될 때까지(약 8초) 뉴스 영역을 계속 관찰한다.
- **관찰 대상**: 관찰 구간 전체의 뉴스 영역 표시 내용.
- **PASS 조건**: 구간 전체에서 `T5930`이 한 번도 나타나지 않고(그동안 로딩 상태 유지), 두 요청 완료 후 `T0660`으로 시작하는 SK하이닉스 응답만 표시되며, 이후 3초를 더 기다려도 바뀌지 않는다.

### AC-012 — 스냅샷 표기

- **준비**: 뉴스 목록이 정상 표시된 상태(AC-008 실행 결과 재사용 가능).
- **실행**: 뉴스 영역을 관찰한다.
- **관찰 대상**: 스냅샷 안내 문구의 존재, 수집 시각·주기·방법의 구체적 값 표기 여부.
- **PASS 조건**: "실시간 뉴스가 아닌 사전 수집된 스냅샷" 취지의 문구가 있고, 수집 시각·주기·방법을 구체적 값으로 제시하는 표기는 없다.

### AC-013 — 하드코딩 뉴스 제거

- **준비**: 본 SPEC의 프론트엔드 변경 적용 상태.
- **실행**: `grep -c 'MOCK_NEWS' frontend/src/app/dashboard/page.tsx` 실행 후, 대시보드에서 4개 종목을 각각 선택해 본다.
- **관찰 대상**: grep 결과, 뉴스 영역에 `'삼성전자, 3분기 영업이익 10조 돌파 전망'`·`'SK하이닉스 HBM4 양산 일정 앞당겨'`·`'코스피, 외국인 순매수에 2,650선 회복'` 세 문구의 출현 여부.
- **PASS 조건**: grep 결과가 `0`이고, 4개 종목 중 어느 것을 선택해도 세 문구가 나타나지 않는다.

### AC-014 — API 주소 관례

- **준비**: 환경 변수 `NEXT_PUBLIC_API_URL` 미설정 상태와, 다른 주소(예: `http://localhost:9000`)로 설정한 상태 두 가지.
- **실행**: `frontend/src/components/StockNews.tsx` 코드를 확인하고, 두 환경 각각에서 종목을 선택해 개발자도구 Network 탭을 연다.
- **관찰 대상**: 코드의 `NEXT_PUBLIC_API_URL` + 기본값 `'http://localhost:8000'` 관례 존재 여부, 요청 대상 주소.
- **PASS 조건**: 코드에 해당 관례가 있고, 미설정 시 요청이 `http://localhost:8000/api/stocks/{code}/news`로 가며, 설정 시 그 주소로 바뀐다.

### AC-015 (대시보드 항목) — 기존 기능 회귀 없음

- **준비**: 본 SPEC의 변경이 모두 적용된 상태.
- **실행**: 대시보드에서 헤더(설정·로그아웃)·포트폴리오 요약·보유 종목 테이블·주가 차트·GitHub 이슈·Notion 저장 버튼을 각각 조작해 본다.
- **관찰 대상**: 각 영역의 기존 동작.
- **PASS 조건**: 여섯 영역 모두 SPEC-NEWS-001 적용 이전과 동일하게 동작한다(뉴스 영역 이외 회귀 없음).

### 임시 픽스처 사용 원칙 (AC-008 ④ · AC-009 · AC-010 (d) 공통)

AC-008 ④·AC-009·AC-010 (d)는 커밋된 `data/*_agents.json`만으로 재현할 수 없는 값(HTML 태그 문자열, `javascript:` 스킴, 빈 배열)을 요구한다. 검증 대상 종목의 `data/{code}_agents.json`을 검증 직전에 임시로 백업(`cp data/005930_agents.json /tmp/005930_agents.json.bak`)한 뒤 필요한 값으로 잠시 고쳐 쓰고, 검증이 끝나면 백업으로 복원한다(`cp /tmp/005930_agents.json.bak data/005930_agents.json`). 커밋된 파일을 그대로 고쳐 커밋하지 않는다.

### 실행 결과 기록

수동 절차 실행 1회의 AC별 PASS/FAIL 결과는 `.moai/specs/SPEC-NEWS-001/progress.md`의 매트릭스에 위 PASS 조건을 인용해 기록한다. 절차 인용 없이 "확인함"만 적은 항목은 PASS로 보지 않는다(`acceptance.md` 품질 게이트).

## 뉴스 모듈 요약 및 재수집 절차 (SPEC-NEWS-001 M3)

### 모듈 요약

`GET /api/stocks/{code}/news`가 `data/{code}_agents.json`의 `news` 배열을 읽어 정렬·전달하고, 대시보드의 `StockNews` 컴포넌트가 보유 종목 선택에 맞춰 이를 표시한다. 4개 허용 종목(`005930`·`000660`·`009150`·`008490`) 중 `008490`은 아직 뉴스 파일이 없어 `404`를 반환한다(아래 재수집 절차 참고). 데이터는 사전 수집된 스냅샷이며 요청 경로에서 실시간으로 수집하지 않는다.

### 재수집 절차 (`008490` 또는 다른 종목 갱신 시)

1. `python scripts/orchestrate_stock_agents.py <티커> --save` 를 1회 실행한다 (`claude -p` 서브에이전트 호출, Claude 사용량 소모, 최대 180초).
2. 생성된 `data/<티커>_agents.json`이 spec.md §4 「유효한 뉴스 문서」 네 조건(JSON 객체 파싱 가능 / `news` 키가 리스트 / 모든 원소가 객체 / 모든 원소가 `title`·`date`·`source`·`summary` 네 문자열 키 보유)을 만족하는지 확인한다.
3. `git diff --stat scripts/` 로 수집 스크립트 자체가 변경되지 않았는지 확인한다(REQ-001 — 스크립트는 이 SPEC에서 수정하지 않는다).
4. 저장소에 커밋한다.

**2026-09-22 실행 기록**: `008490`에 대해 위 1단계를 1회 실행했으나 실패했다 — `claude -p` 서브프로세스 자체는 종료 코드 0으로 끝났지만, 반환된 봉투(envelope)의 `result` 필드가 JSON으로 재파싱되지 않았다(`json.decoder.JSONDecodeError: Expecting value: line 1 column 1 (char 0)`). 재시도는 하지 않았다(외부 부작용 호출의 근거 없는 반복 실행을 피함). `data/008490_agents.json`은 여전히 존재하지 않으며, `GET /api/stocks/008490/news`는 `404`를 반환한다(AC-004 확인됨) — 이 상태는 정상 경로로 설계되어 있다(§4 엣지 케이스). 재시도는 이 SPEC 범위 밖의 후속 작업으로 남긴다.
