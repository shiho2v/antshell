# design-review.md — 사실검증 및 설계 정제

작성일: 2026-07-12
대상: `.claude/skills/generating-krx-report/`
목적: 구현 전에 원 요구사항을 공식 사양과 대조하여, **사실과 다르거나 실행 불가능한 항목을 식별하고 설계를 정제**한다.

> 원칙: **공식 사양이 프롬프트 요구사항과 충돌하면 공식 사양을 우선**하고, 변경 사유를 여기에 기록한다.
> 여기 기록되지 않은 임의 구현은 하지 않는다.

---

## 0. 요약 — 원 요구사항에서 정정한 항목

| # | 원 요구사항 | 검증 결과 | 조치 |
|---|---|---|---|
| C1 | Python 3.11 이상 | 이 환경은 **Python 3.10.5** | 3.10 호환으로 구현. 3.11 전용 기능 미사용 |
| C2 | `allowed-tools`로 도구 제한 | `allowed-tools`는 **제한이 아니라 사전승인(pre-approve)** | 보안 경계로 의존하지 않음. 문서화만 |
| C3 | 스크립트 경로를 상대경로로 호출 | 공식 변수 **`${CLAUDE_SKILL_DIR}`** 존재 | 모든 호출을 `${CLAUDE_SKILL_DIR}` 기준으로 작성 |
| C4 | DART 분기 수치를 그대로 사용 | 분기보고서 금액은 **누적(YTD)이 기본**, `thstrm_add_amount`는 **누락 빈번** | 분기 단독값은 **연속 누적 보고서 차분**으로 파생 |
| C5 | 사업부문별 매출·가동률·생산능력·원재료·수주잔고 | **구조화된 DART API 없음** | `unsupported`. 원문 공시(`document.xml`) 텍스트 추출로만 제한적 제공 |
| C6 | Forward PER / 컨센서스 / 목표주가 | **무료 공식 API 존재하지 않음** | `unsupported`. 계약 기본값 `false`. 생성 금지 |
| C7 | pykrx는 수급(I)만 로그인 필요 | 현재 **KRX 백엔드 전체가 로그인 필요** (익명 호출 → `400 LOGOUT`) | `KRX_ID`/`KRX_PW` 없으면 OHLCV만 가능(Naver 경유), 나머지 N/A |
| C8 | KRX Open API 사용 | 존재하지만 **AUTH_KEY 발급 + 서비스별 이용신청 필요**, 수급·PER 미제공 | 선택 경로로만 지원. 키 없으면 `unsupported` |
| C9 | ROIC "계산 가능한 경우" | 계산 가능하나 **가정(세율·투하자본 정의) 필요** | 가정을 evidence에 명시하고 계산 |
| C10 | CANSLIM M(시장방향), I(기관수급), L(주도주) | 모두 **KRX 로그인 의존** | 자격증명 없으면 N/A. 0점 처리 금지 |
| C11 | EPS를 계정명으로 추출 | 과거 보고서는 account_id가 전부 미사용 → **우선주 EPS를 집을 위험** | 보통주 전용 추출기. §5.5(1) |
| C12 | 시가총액 = 종가 × 발행주식수(합계) | 합계는 보통주+우선주 → **약 4% 과대계상** | 보통주 주식수 사용 + KRX 교차검증. §5.5(2) |
| C13 | EV/EBITDA 항상 계산 | 감가상각비가 본문에 없는 기업 존재 | N/A 처리. 추정 금지. §5.5(3) |

---

## 1. Claude Code 스킬 공식 사양 확인

출처: <https://code.claude.com/docs/en/skills.md>

### 1.1 프론트매터

공식 지원 필드: `name`, `description`, `when_to_use`, `argument-hint`, `arguments`,
`disable-model-invocation`, `user-invocable`, `allowed-tools`, `disallowed-tools`,
`model`, `effort`, `context`, `agent`, `hooks`, `paths`, `shell`.

- 모든 필드가 **선택(optional)**. `description`이 사실상 발동을 결정하므로 필수에 준함.
- `description` + `when_to_use` 합계 **1,536자에서 절단**됨.
- **`name`은 표시용 라벨일 뿐이며, 슬래시 커맨드 이름은 디렉터리명에서 나온다.** (`.claude/skills/generating-krx-report/` → `/generating-krx-report`)
- **정정 (C2)**: `allowed-tools`는 **"사전승인"**이다. 공식 문서: *"every tool remains callable, and your permission settings still govern tools that are not listed."*
  → **도구 제한 수단이 아니다.** 본 스킬은 `allowed-tools`를 권한 프롬프트 절감 용도로만 쓰고,
  "이 스킬은 X만 할 수 있다"는 식의 보안 주장을 하지 않는다.
  - 도구를 실제로 **빼려면** `disallowed-tools`를 써야 한다.
- 문법: 공백 또는 쉼표 구분 문자열, 또는 YAML 리스트. `Bash(git add *)` 형태의 스코프 지정 지원.
- **미확인**: 알 수 없는 프론트매터 필드가 거부/무시/경고 중 무엇인지 **문서화되어 있지 않음**.
  → 안전하게 **문서화된 필드만** 사용한다.

### 1.2 컨텍스트 로딩 (Progressive disclosure)

| 시점 | 로드되는 것 |
|---|---|
| 세션 시작 | **description만** |
| 스킬 발동 | `SKILL.md` **본문 전체**가 메시지로 들어가 **세션 내내 유지** |
| supporting files (`references/`, `modules/`, `scripts/`) | **자동 로드되지 않음.** Claude가 Read를 호출할 때만 |

- 공식 권장: `SKILL.md` **500줄 미만**. 프롬프트 요구(200줄)가 더 엄격 → **200줄 준수**.
- SKILL.md는 세션 내내 상주하므로, 여기에 rubric을 복사하는 것은 **영구적 토큰 낭비**다.
  → Phase 12 토큰 규칙의 근거가 공식 사양으로 확인됨.

### 1.3 경로 해석 — **설계에 직접 영향 (C3)**

- 공식 변수 **`${CLAUDE_SKILL_DIR}`** = SKILL.md가 있는 디렉터리. *"regardless of the current working directory."*
- `${CLAUDE_PROJECT_DIR}` = 프로젝트 루트 (Claude Code v2.1.196+ 필요).
- **조치**: SKILL.md의 모든 스크립트 호출을 `${CLAUDE_SKILL_DIR}/scripts/...` 로 작성한다.
  추가로 모든 스크립트는 `__file__` 기준으로 스킬 루트를 자체 계산하여 **CWD와 무관하게** `data/`·`outputs/`에 쓴다.
  (기존 스킬의 `fetch_dart.py`는 CWD의 `data/`에 저장 → 실행 위치에 따라 파일이 흩어짐. 정정함.)

### 1.4 스크립트 실행

- Claude가 **Bash 도구로 직접 실행**한다. 자동 실행 메커니즘은 없다.
- 예외: `` !`cmd` `` 동적 주입은 **스킬 렌더링 시점에 전처리**로 실행된다(Claude가 실행하는 게 아님).
  → 본 스킬은 동적 주입을 **쓰지 않는다**. 네트워크·API 키가 필요한 명령을 발동 시점에 자동 실행하면
  사용자가 의도하지 않은 API 호출이 발생하고, 실패 시 스킬 본문이 오염된다.

---

## 2. OpenDART 사실확인

출처: OpenDART 개발가이드 DS001/DS002/DS003/DS004.

### 2.1 실재하는 엔드포인트 (본 스킬이 사용하는 것만)

| 엔드포인트 | 용도 | 필수 파라미터 | 비고 |
|---|---|---|---|
| `corpCode.xml` | corp_code ↔ 6자리 종목코드 매핑 | `crtfc_key` | **ZIP 바이너리** 응답 |
| `company.json` | 기업개황 | `corp_code` | 업종·대표자·설립일·결산월 |
| `list.json` | 공시검색 | `crtfc_key` | `rcept_no`, `report_nm`, `rcept_dt` |
| `fnlttSinglAcnt.json` | 단일회사 주요계정 | `corp_code`,`bsns_year`,`reprt_code` | **`fs_div` 파라미터 없음**. CFS·OFS **둘 다 반환**, 행마다 `fs_div` 보유 |
| `fnlttSinglAcntAll.json` | 단일회사 **전체** 재무제표 | + **`fs_div` 필수** | BS/IS/CIS/CF/SCE |
| `fnlttSinglIndx.json` | 재무지표 | + `idx_cl_code` (M210000 수익성 / M220000 안정성 / M230000 성장성 / M240000 활동성) | |
| `stockTotqySttus.json` | 주식총수 | `corp_code`,`bsns_year`,`reprt_code` | **시가총액 계산의 공식 주식수 출처** |
| `tesstkAcqsDspsSttus.json` | 자기주식 취득·처분 | 〃 | 자사주 촉매 |
| `alotMatter.json` | 배당 | 〃 | |
| `irdsSttus.json` | 증자·감자 | 〃 | **희석 판단 근거** |
| `document.xml` | 공시서류 **원본** | `rcept_no` | **ZIP 바이너리**. 서술 섹션의 유일한 공식 경로 |

- **오류는 HTTP 200으로 온다.** 본문 `status`로 판정해야 한다. → `raise_for_status()`만으로는 실패를 못 잡는다.

### 2.2 `reprt_code` — 함정 확인

`11011` 사업보고서(FY) · `11012` **반기(H1)** · `11013` **1분기** · `11014` **3분기**

- **11012는 2분기가 아니라 반기다.** 순서가 직관과 다르다(11013 → 11012 → 11014).

### 2.3 누적 vs 분기 단독 — **가장 중요한 정정 (C4)**

- 공식 가이드는 `thstrm_amount`(당기금액), `thstrm_add_amount`(당기**누적**금액)만 정의하며,
  **분기보고서에서 어느 XBRL 컨텍스트가 `thstrm_amount`에 담기는지 명시하지 않는다** → **사양상 미확인**.
- 실무: `thstrm_add_amount`가 YTD여야 하지만 **제출인·XBRL 태깅에 따라 비어 있는 경우가 잦고**,
  그때는 `thstrm_amount`가 누적을 담는다.
- **조치**: 분기 단독값을 **API 필드 하나로 믿지 않는다.**
  손익·현금흐름 항목은 **연속 누적 보고서의 차분**으로 파생한다.
  ```
  Q1 = 1Q누적
  Q2 = 반기누적 − 1Q누적
  Q3 = 3Q누적 − 반기누적
  Q4 = FY − 3Q누적
  ```
  차분에 필요한 인접 보고서가 없으면 해당 분기는 **N/A** (0 아님).
  재무상태표(BS)는 시점값이므로 차분하지 않는다.
- 파생값은 `source_type: derived_calculation`, `formula`, `input_evidence_ids`를 반드시 남긴다.

### 2.4 연결/별도 (`fs_div`)

- `CFS` = 연결, `OFS` = 별도/개별.
- `fnlttSinglAcntAll`은 `fs_div` **필수** → 무엇을 받았는지 요청 시점에 확정된다.
- `fnlttSinglAcnt`는 CFS·OFS를 **섞어서 반환** → 행의 `fs_div`로 **반드시 필터링**해야 한다.
  (기존 `fetch_dart.py`는 필터링 없이 `account_nm` 첫 매치를 취함 → **연결·별도 혼입 버그**. 정정함.)
- 연결 대상이 없는 회사는 `fs_div=CFS` 요청 시 `status=013`.
- **조치**: 기본 `CFS`, 없으면 `OFS`로 폴백하되 **폴백 사실을 evidence와 보고서에 명시**하고,
  하나의 계산식 안에서 CFS와 OFS를 **절대 섞지 않는다** (Gate 2에서 차단).

### 2.5 `rcept_no`

- **확인: `fnlttSinglAcnt` / `fnlttSinglAcntAll` 및 DS002 엔드포인트 응답에 행 단위로 `rcept_no`가 포함된다.**
  → Phase 6의 "DART 수치에 접수번호 저장" 요구는 **실현 가능**하다.
- 뷰어 링크: `https://dart.fss.or.kr/dsaf001/main.do?rcpNo={rcept_no}`

### 2.6 status 코드

| 코드 | 의미 | 분류 |
|---|---|---|
| 000 | 정상 | OK |
| 010 / 011 / 012 | 미등록 키 / 사용불가 키 / 접근불가 IP | **hard error** (재시도 무의미) |
| **013** | **조회된 데이터 없음** | **정상적 빈 결과 — 오류 아님. 0으로 해석 금지** |
| 014 | 파일 없음 | 빈 결과 (바이너리 엔드포인트) |
| **020** | **요청 제한 초과** | **rate limit — 백오프** |
| 021 | 회사 개수 초과(최대 100) | 호출자 버그 |
| 100 / 101 | 부적절한 값 / 부적절한 접근 | 호출자 버그 / hard error |
| 800 / 900 | 점검 중 / 미정의 오류 | 일시적 — 재시도 |
| 901 | 개인정보 보유기간 만료 | hard error |

- **일일 호출 한도 수치는 공식 페이지에서 확인되지 않음.** 흔히 인용되는 "20,000회/일"은 **미확인**.
  → **숫자를 하드코딩하지 않고 `status == "020"`으로 분기**한다.

### 2.7 DART에서 **얻을 수 없는** 것 (C5, C6)

구조화된 API가 **없다**:

- **사업부문별 매출(segment revenue)** — 엔드포인트 없음
- **생산능력·가동률** — 엔드포인트 없음
- **원재료** — 엔드포인트 없음
- **수주잔고** — 엔드포인트 없음
- **연구개발비** — 전용 엔드포인트 없음 (일부 기업에서 `fnlttSinglAcntAll`에 "경상연구개발비" 계정으로 나타날 수 있으나 **보장되지 않음**)
- **애널리스트 컨센서스 / Forward EPS / 목표주가** — **DART 영역이 아님. 존재하지 않음.**

**조치**:
- 위 항목은 모두 `unsupported`로 레지스트리에 명시한다. **함수 이름을 지어내지 않는다.**
- 서술 항목(사업부문·가동률·원재료·수주잔고·R&D)의 유일한 공식 경로는 **`document.xml` 원문 파싱**이다.
  → `fetch_dart_profile.py --with-document` **옵트인 플래그**로 사업보고서 원문의
  「II. 사업의 내용」 섹션 텍스트를 추출해 `data/raw/`에 저장한다.
  - `source_type: official_filing`, `rcept_no` 부착.
  - **자동으로 숫자를 뽑아내지 않는다.** Claude가 텍스트를 읽고 정성 근거로 인용하며, 수치를 인용할 경우 반드시 원문 문구에 근거해야 한다.
  - 플래그를 쓰지 않으면 해당 항목은 **N/A**이며, Business/Moat 모듈의 `evidence_coverage`가 낮아진다.
    → **점수를 깎지 않고 confidence를 낮춘다** (Phase 7 규칙).

---

## 3. KRX 사실확인 — 세 가지를 구분한다 (C7, C8)

| 구분 | 정체 | 인증 | 본 스킬에서의 지위 |
|---|---|---|---|
| **KRX Open API** (`openapi.krx.co.kr`, 호출 base `data-dbg.krx.co.kr/svc/apis/...`) | KRX **공식** API | **AUTH_KEY 헤더 필수** + 데이터셋별 이용신청(승인 대기) | `official_api`. **선택 경로.** 키 없으면 `unsupported` |
| **KRX 정보데이터시스템** (`data.krx.co.kr`) | **웹 포털** (API 아님) | 로그인 | 내부 JSON 엔드포인트는 **공개 계약이 아님**. 직접 호출하지 않음 |
| **pykrx** | **비공식** 3rd-party 스크레이퍼 | `KRX_ID`/`KRX_PW` | `unofficial_wrapper`. **반드시 그렇게 표기** |

### 3.1 pykrx 자격증명 — 기존 코드의 주석이 틀렸다 (C7)

- pykrx는 **import 시점**에 `KRX_ID`/`KRX_PW`를 읽어 `data.krx.co.kr`에 로그인한다(`comm/auth.py`).
- **2026-07-12 실측**: 익명 상태로 `data.krx.co.kr` 내부 엔드포인트 호출 시 **HTTP 400, body `LOGOUT`**.
  → **수급뿐 아니라 KRX 백엔드를 쓰는 모든 pykrx 함수가 사실상 로그인 필요.**
- **유일한 예외**: `get_market_ohlcv(..., adjusted=True)` — **기본값** — 은 **Naver Finance**를 긁는다.
  자격증명 없이 동작한다.
- 기존 `fetch_price.py`는 *"미설정 시 시세는 정상 수집되나 수급만 N/A"*라고 적었는데,
  **시세가 수집되는 이유는 KRX가 허용해서가 아니라 Naver로 우회하기 때문**이다.
  → **정정**: 자격증명 없을 때 조회 가능한 것은 **수정주가 OHLCV뿐**이며, 그 출처는 **Naver(비공식)**임을 명시한다.

### 3.2 자격증명 유무에 따른 가용성

| 항목 | pykrx 함수 | `KRX_ID`/`KRX_PW` 없을 때 |
|---|---|---|
| 수정주가 OHLCV | `get_market_ohlcv` (adjusted=True → Naver) | ✅ 가능 (`unofficial_wrapper`, underlying=Naver) |
| 시가총액·상장주식수 | `get_market_cap` | ❌ N/A → **DART `stockTotqySttus` + 종가로 대체 계산** |
| PER/PBR/EPS/BPS/DIV | `get_market_fundamental` | ❌ N/A → **DART 기반 자체 계산으로 대체** |
| 투자자별 순매수 (CANSLIM **I**) | `get_market_trading_value_by_date` | ❌ **N/A** (대체 불가) |
| 지수 OHLCV (CANSLIM **M**) | `get_index_ohlcv` | ❌ **N/A** (대체 불가) |
| 업종 분류 (CANSLIM **L**) | `get_market_sector_classifications` | ❌ N/A |

- **핵심 설계 결과**: **시가총액을 pykrx에 의존하지 않는다.**
  `시가총액 = 종가(Naver/pykrx) × 발행주식수(DART stockTotqySttus)` 로 계산하면
  **자격증명 없이도 밸류에이션 모듈(PER·PBR·EV/EBITDA·FCF Yield)이 동작**한다.
  이 파생값은 `derived_calculation`으로 기록하고 두 입력의 **기준일 불일치**를 `limitations`에 남긴다.

### 3.3 `get_market_fundamental`의 PER/PBR을 인용해도 되는가?

- 이 값은 pykrx 계산이 아니라 **KRX가 공표한 값의 패스스루**다.
- 그러나 KRX는 **최근 확정 재무제표 기준(trailing)**으로 산출하며 **분기 갱신이 지연**된다.
- **조치**: KRX 공표 PER/PBR은 **참고(historical band용)**로만 쓰고,
  분석 본문의 Trailing PER은 **DART 재무 + 현재가로 자체 계산**한 값을 사용한다.
  둘이 다르면 **차이를 숨기지 않고 counter_evidence로 병기**한다.

---

## 4. 구현 불가 / 비공식 의존 항목 확정

### 4.1 `unsupported` (공식 경로 없음 — 생성 금지)

| 항목 | 사유 |
|---|---|
| 애널리스트 컨센서스 | 무료 공식 API 없음 |
| Forward EPS / Forward PER | 위와 동일. **검증된 Forward EPS가 없으므로 Forward PER은 계산하지 않는다** |
| 목표주가 | 위와 동일. 계약에서 요청되어도 **근거 없이 생성하지 않는다** |
| 시장점유율 | 공시에 없음. **추정 금지** |
| 경쟁사 자동 선정 | 선정 규칙 없이는 임의 선택 금지 |
| 생산능력·가동률·원재료·수주잔고·사업부문별 매출 | 구조화 API 없음 (원문 파싱만) |

### 4.2 `credential_required` (자격증명 있으면 가능)

| 항목 | 필요 자격증명 |
|---|---|
| 재무 데이터 일체 | `DART_API_KEY` |
| CANSLIM **I** (기관수급) | `KRX_ID` + `KRX_PW` |
| CANSLIM **M** (시장방향) | `KRX_ID` + `KRX_PW` |
| CANSLIM **L** (주도주/업종) | `KRX_ID` + `KRX_PW` |
| 역사적 PER/PBR 밴드 | `KRX_ID` + `KRX_PW` |
| KRX 공식 경로 OHLCV | `KRX_OPEN_API_KEY` (선택) |

**이들은 없을 때 `N/A` + 낮은 confidence로 처리하며, 절대 0점으로 채점하지 않는다.**

---

## 5. 설계 정제 결정

### 5.1 계산과 해석의 경계 — 정성 모듈의 채점 문제

**충돌**: Phase 3은 *"LLM이 총점을 계산하지 않게 한다"*고 하지만,
Business·Moat·Risk·Catalyst는 본질적으로 **정성 판단**이라 Python이 점수를 만들 수 없다.

**해결 (2단계 분리)**:

1. Claude는 rubric의 각 기준에 대해 **서수 등급(0/1/2/3)과 evidence_id만** 산출하여
   `data/module-results/{ticker}_{module}_judgment.json`에 기록한다. **산술을 하지 않는다.**
2. `score_modules.py`가 등급 → 가중 점수 → 모듈 점수 → 종합점수를 **전부 Python으로 계산**한다.

→ LLM은 **판단**만, 산술은 **전부 Python**. Phase 3 원칙을 위배하지 않으면서 정성 모듈이 동작한다.
정량 모듈(quality/growth/valuation/trend)은 임계값 기반으로 **Python이 자동 채점**하며 Claude 등급이 필요 없다.

기준의 **단일 진실 원천은 `config/module-registry.yaml`**이다.
`rubric.md`는 그 기준을 사람이/Claude가 읽도록 서술한 것이며, **점수 산정에 사용되지 않는다**
(불일치 시 registry가 이긴다 — `validate_report.py`가 재계산으로 검증).

### 5.2 CANSLIM 재배치

CANSLIM은 최상위 프레임에서 **`trend` 모듈의 하위 rubric**으로 내려간다.
- C·A는 **`growth` 모듈이 계산한 지표를 evidence_id로 재참조**한다. **재계산하지 않는다** (Phase 4 요구).
- 사용자가 "CANSLIM 분석"만 요청해도 `growth`는 **의존성으로 실행**된다(C·A 없이는 CANSLIM이 성립 불가).
  단, 보고서에는 `growth-summary`로 축약 출력한다.

### 5.3 `analysis_contract.json` 저장 위치

프롬프트는 `data/analysis_contract.json`(종목 무관)이라 했으나, 종목별로 덮어쓰면 동시 분석이 깨진다.
→ **`data/{ticker}_analysis_contract.json`으로 저장하고, `data/analysis_contract.json`은 최신 계약의 별칭으로 함께 쓴다.**
사유: 다종목 분석 시 계약 유실 방지. 프롬프트가 요구한 경로도 그대로 존재하므로 하위호환.

### 5.4 미래일자·NaN 차단

`validate_evidence.py`가 다음을 **하드 실패**로 처리한다: 미래 기준일, NaN/Infinity,
결측치의 0 변환, `status != "000"` 응답의 데이터화, 단위 누락, 기간 불일치 비교.

---

## 5.5 실측으로 발견한 사항 (2026-07-12, 삼성전기 009150 통합 테스트)

문서만으로는 드러나지 않았고 **실제 응답을 돌려보고서야 발견한** 것들이다.
모두 회귀 테스트로 고정했다.

### (1) EPS 보통주/우선주 혼동 — **정합성 위험 최상**

2022~2023 사업보고서에서는 EPS 행의 `account_id` 가 **전부 `-표준계정코드 미사용-`** 이다.
→ ID 매칭이 실패하고 **이름 매칭으로 넘어간다.** 그런데 행이 이렇게 생겼다:

```
보통주 기본 및 희석주당이익      5,597
우선주 기본 및 희석주당이익      5,647     ← 단순 부분일치는 이걸 집을 수 있다
```

2025년에도 `우선주기본주당이익 9,395` 과 `보통주기본주당이익 9,345` 가 나란히 있다.
우선주를 집으면 **PER·EPS 성장률·CANSLIM C 가 전부 오염된다.**

**조치**: `_pick_eps()` 전용 추출기를 만들어 (a) 우선주 행을 무조건 배제, (b) IFRS 표준 ID 우선,
(c) 이름 매칭 시 `보통주` 요구 + 기본(basic) > 희석, 총이익 > 계속영업이익 순위를 적용했다.
보통주 EPS 가 없으면 **N/A** 이며 우선주로 대체하지 않는다.

### (2) 시가총액 — `합계` 주식수를 쓰면 과대계상된다

`stockTotqySttus` 의 주식 종류별 행 (삼성전기 2025):

| se | istc_totqy |
|---|---|
| 의결권이 있는주식(보통주) | **74,693,696** ← KRX 상장주식수와 정확히 일치 |
| 의결권이 없는주식(우선주) | 2,906,984 |
| 합계 | 77,600,680 ← **이걸 쓰면 안 된다** |

우리가 가진 주가는 **보통주 종가**다. 합계를 곱하면 시가총액이 **약 +3.9% 과대계상**된다.
보통주 주식수를 쓰면 KRX 공표 시가총액과 **정확히 일치**한다:

```
1,584,000 × 74,693,696 = 118,314,814,464,000  = KRX get_market_cap
```

**조치**: 보통주 행을 사용하도록 고정하고, 우선주 제외 사실과
"분자(시총)는 우선주 제외 / 분모(순이익·자본)는 우선주 포함" 이라는 비대칭을 limitation 으로 노출한다.
또한 `get_market_cap` 으로 **자동 교차검증**해 괴리 0.5% 초과 시 경고를 남긴다.

### (3) 감가상각비가 재무제표 본문에 없다 → EV/EBITDA 는 N/A

삼성전기는 `fnlttSinglAcntAll` 의 BS/IS/CIS/CF **어디에도 감가상각비 행이 없다**(주석에만 존재).
→ EBITDA 를 구성할 수 없다. **추정하지 않는다.** `ebitda_ttm`·`ev_ebitda` 는 N/A 이며
VAL-03(w20)은 채점에서 제외된다(0점 아님). 기업에 따라 감가상각비를 본문에 표시하면 정상 계산된다.

### (4) 이자비용 대신 `금융원가`

`ifrs-full_InterestExpense` 가 없고 **`ifrs-full_FinanceCosts`(금융원가)** 만 있는 기업이 많다.
대용하되, 금융원가는 외환·파생 손실을 포함할 수 있어 이자보상배율이 과소평가될 수 있다
→ 대용 사실을 limitation 으로 기록한다.

### (5) `get_market_fundamental` 이 현재 깨져 있다

pykrx 1.2.8 에서 KRX 로그인이 성공해도
`Error: "None of [Index(['TRD_DD','BPS','PER','PBR','EPS','DVD_YLD','DPS'])] are in the [columns]"`
가 발생한다(KRX 응답 스키마 변경 추정).
→ **조용히 실패하지 않고 N/A 로 강등**되도록 처리했다. 본문 PER 은 어차피 DART 기반 자체 계산값을 쓰므로
분석은 계속 진행된다.

### (6) 데이터 완전성이 부풀려지는 버그

`data_completeness` 를 **채점된 모듈만** 평균내면, 8개 중 4개가 데이터 부재여도 **95%** 로 표시됐다.
이러면 Gate 4 의 "데이터 완전성 ↔ 결론 강도 일치" 검사가 무력화된다.
**조치**: 완전성·신뢰도는 **요청된 모든 모듈**에 대해 가중평균한다(미채점 = coverage 0).
같은 상황에서 95% → **52%** 로 정정되었고, 미채점 모듈 목록이 결론 문장에 명시된다.
(점수 자체는 N/A 에 0점을 줄 수 없으므로 채점된 모듈만으로 재정규화하는 것이 맞다.)

---

## 6. 남은 미확인 사항 (정직하게 기록)

1. OpenDART **일일 호출 한도의 정확한 수치** — 공식 페이지에서 확인 불가. 코드에서 숫자 가정 안 함.
2. DART 분기보고서에서 `thstrm_amount`의 **XBRL 컨텍스트(3개월 vs YTD)** — 사양에 명시 없음.
   → 차분 방식으로 우회하므로 분석 결과는 이 미확인에 의존하지 않는다.
3. `alotMatter.json`의 `se` 항목 **열거값** — 미확인. 런타임에 읽어서 처리한다.
4. Claude Code가 **알 수 없는 프론트매터 필드**를 어떻게 처리하는지 — 미문서화. 문서화된 필드만 사용.
5. KRX Open API 일일 한도(≈10,000) — **2차 출처 기반, 공식 미확인**. 하드코딩 안 함.

---

## 7. 이 스킬이 하지 않는 것 (명시적 비목표)

- 매수/매도 의견 제시 (→ 관찰 등급 4단계로 제한)
- 목표주가 산출
- 컨센서스·전망치 생성
- 뉴스로 공시 데이터 보완 (계약에서 `news_allowed: false`가 기본)
- 근거 없는 경쟁사·시장점유율·해자 추정
- 데이터 부족을 낮은 점수로 환산

---

## 8. 필요 패키지

```bash
pip install requests pykrx jsonschema PyYAML
```

- Python **3.10+** (이 환경 3.10.5에서 검증)
- `DART_API_KEY` — 필수 (재무 일체)
- `KRX_ID`, `KRX_PW` — 선택 (수급·지수·업종·밸류에이션 밴드)
- `KRX_OPEN_API_KEY` — 선택 (KRX 공식 API 경로)
