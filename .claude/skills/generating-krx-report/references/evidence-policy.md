# 근거 정책 (Evidence Policy)

이 스킬의 **데이터 정직성 계약**이다. 채점·서술·보고서보다 이 문서가 우선한다.
관련 문서: [data-honesty.md](./data-honesty.md) · [scoring-policy.md](./scoring-policy.md) · [synthesis-policy.md](./synthesis-policy.md) · [report-style.md](./report-style.md)
기계 판독 규격: [`schemas/evidence-item.schema.json`](../schemas/evidence-item.schema.json) · 수집 경로: [`config/source-priority.yaml`](../config/source-priority.yaml)

## 1. 근거 없이는 아무것도 존재하지 않는다

수치든 서술이든 **모든 근거는 evidence item 하나**로 표현된다.
출처·기준일·단위·수집경로가 없는 근거는 만들 수 없다. 보고서에 넣을 수도 없다.

| 필드 | 의미 | 필수 조건 |
|---|---|---|
| `evidence_id` | `Q-PROFIT-001` 형식의 고유 ID | 모든 주장은 이 ID로만 근거를 가리킨다 |
| `module` | business / quality / growth / moat / valuation / trend / risk / catalyst / shared | |
| `evidence_type` | `metric`(수치) / `statement`(공시 서술) / `filing_text`(원문 발췌) / `event`(공시 사건) / `timeseries`(시계열) | |
| `metric` | registry 의 metric 키와 **철자까지 일치** | `evidence_type=metric` 일 때 |
| `value` | 값. **`null` = 데이터 없음(N/A)이며 0 과 다르다** | NaN/Infinity 금지 |
| `unit` | `%`, `x`, `KRW`, `%p`, `주` | `value` 가 숫자면 필수 |
| `period_start` / `period_end` | 대상 기간 | |
| `period_type` | `quarter_standalone` / `quarter_cumulative` / `annual` / `ttm` / `point_in_time` / `range` | 누적·분기단독 혼용을 막는 핵심 필드 |
| `fs_div` | `CFS`(연결) / `OFS`(별도) | DART 재무 수치이면 필수 |
| `comparison` | YoY·QoQ·CAGR 등 비교의 상대 기간 | 동일 `period_type` 끼리만 |
| `source` | provider·source_type·retrieved_at (+ rcept_no, endpoint_or_function) | 항상 필수 |
| `calculation` | formula + input_evidence_ids | `derived_calculation` 이면 필수 |
| `text` | 인용문. **원문을 변형하지 않는다** | statement/filing_text/event |
| `verification` | pending / verified / failed / not_applicable | |
| `limitations` | 예: "종가 기준일과 발행주식수 기준일이 다름" | 알면서 넘어가지 않는다 |

## 2. source_type — 언제 무엇을 쓰는가

| source_type | 정확히 이럴 때만 | 예 |
|---|---|---|
| `official_api` | OpenDART / KRX Open API 를 **직접 호출**해 받은 값 | `fnlttSinglAcntAll.json`, `stockTotqySttus.json`, `list.json` |
| `official_filing` | DART 공시 **원문**(`document.xml`)에서 발췌한 텍스트 | 사업보고서 「II. 사업의 내용」 문단 |
| `official_download` | 공식 파일 다운로드 | `corpCode.xml` (ZIP) |
| `unofficial_wrapper` | **pykrx** 로 얻은 모든 값 | OHLCV, 수급, 지수, KRX 공표 PER/PBR |
| `derived_calculation` | 위 값들로 계산한 파생값 | 시가총액, TTM, YoY, CAGR, PER |

`config/source-priority.yaml` 에 **없는 엔드포인트·함수는 존재하지 않는다.** 이름을 지어내지 않는다.

### pykrx 를 정직하게 인용하는 법
pykrx 는 KRX·Naver 와 무관한 **third-party 스크레이퍼**다. 공식 데이터인 것처럼 적지 않는다.
`get_market_ohlcv` 는 기본값(`adjusted=True`)에서 **Naver Finance** 를 경유한다.

```json
"source": {
  "provider": "pykrx",
  "source_type": "unofficial_wrapper",
  "underlying_source": "Naver Finance",
  "endpoint_or_function": "get_market_ohlcv(fromdate, todate, ticker)",
  "retrieved_at": "2026-07-12T09:31:00+09:00"
}
```
보고서 본문 표기: `(출처: pykrx(비공식 래퍼, 원천 Naver Finance), 기준일: 2026-07-10)`

### DART 수치는 rcept_no 가 없으면 근거가 아니다
모든 DART 수치는 14자리 접수번호를 갖는다. 없으면 그 수치는 **쓰지 않는다**.
뷰어 링크: `https://dart.fss.or.kr/dsaf001/main.do?rcpNo={rcept_no}`

```json
"source": {
  "provider": "dart", "source_type": "official_api",
  "endpoint_or_function": "fnlttSinglAcntAll.json",
  "rcept_no": "20250514000123",
  "url_or_identifier": "https://dart.fss.or.kr/dsaf001/main.do?rcpNo=20250514000123",
  "retrieved_at": "2026-07-12T09:30:00+09:00"
}
```

## 3. N/A ≠ 0 (가장 자주 어기는 규칙)

- **데이터가 없다 → `value: null` + `na_reason`.** 절대 `0` 으로 바꾸지 않는다.
- **데이터 조회 실패 → N/A.** 실패는 "나쁜 실적"이 아니다. 0점으로 채점하지 않는다.
- DART 응답 status `013`/`014`(데이터 없음)는 **오류가 아니며 0도 아니다.** N/A 다.
- 자격증명(`KRX_ID`/`KRX_PW`) 부재로 못 받은 항목 — 수급(CANSLIM I), 지수(M·L), KRX 공표 PER/PBR — 은 전부 **N/A**다.
- 불확실하지만 존재는 하는 사실은 `확인 필요`로 표기하고, 추정값으로 채우지 않는다.

> "대략 ~수준", "통상 ~정도", "업계 평균은 ~" 같은 표현은 근거가 아니라 환각이다.

## 4. 외부 지식 금지

- **사전 학습 지식·기억·유명한 사실로 빠진 숫자를 보완하지 않는다.**
  - 금지: "삼성전기는 MLCC 점유율 상위권이다" → 시장점유율은 공시에 없다. 생성 금지.
- 다음은 **공식 경로가 없으므로 어떤 형태로도 생성하지 않는다**:
  애널리스트 컨센서스 / Forward EPS / Forward PER / 목표주가 / 시장점유율 / 자동 경쟁사 선정 /
  사업부문별 매출·생산능력·가동률·원재료·수주잔고의 **구조화 수치**.
- 위 서술 항목들은 **사업보고서 원문(document.xml) 텍스트에만** 존재한다.
  쓰려면 `evidence_type: filing_text`, `source_type: official_filing` 으로 **원문을 인용**하고,
  거기서 수치를 자동 추출해 지표로 만들지 않는다.

## 5. 파생값은 재현 가능해야 한다

`source_type: derived_calculation` 이면 `calculation` 이 필수다. 공식과 입력 근거 ID가 있어야 Gate 3 를 통과한다.

```json
{
  "evidence_id": "V-PER-001",
  "evidence_type": "metric", "metric": "per_trailing", "value": 12.4, "unit": "x",
  "period_type": "ttm", "fs_div": "CFS",
  "source": {"provider": "internal", "source_type": "derived_calculation",
             "retrieved_at": "2026-07-12T09:35:00+09:00"},
  "calculation": {
    "formula": "market_cap / net_income_ttm",
    "inputs": {"market_cap": 9876543210000, "net_income_ttm": 796495420000},
    "input_evidence_ids": ["SH-MKTCAP-001", "Q-NETINCOME-001"]
  },
  "limitations": ["종가 기준일(2026-07-10)과 발행주식수 기준일(2026-03-31)이 다르다"]
}
```

## 6. 섞지 말아야 할 것들 (Gate 2 실패 사유)

- **연결(CFS) ↔ 별도(OFS) 혼용 금지.** 한 계산식의 모든 입력은 같은 `fs_div` 여야 한다.
  CFS 가 없어 OFS 로 폴백했다면 `limitations` 에 "OFS 폴백 적용"을 남긴다.
- **누적 ↔ 분기단독 혼용 금지.** DART 분기 수치는 **누적값**이다.
  분기 단독값은 인접 누적 보고서의 **차분으로만** 파생한다:
  `Q1 = 1Q` / `Q2 = 반기 − 1Q` / `Q3 = 3Q누적 − 반기` / `Q4 = FY − 3Q누적`.
  `thstrm_add_amount` 를 신뢰하지 않는다. 인접 보고서가 결측이면 그 분기는 **N/A**(0 아님).
- **YoY 는 동일 분기끼리만.** 3Q 를 2Q 와 비교하지 않는다.
- **적자기업 PER·EV/EBITDA 금지.** 순이익 ≤ 0 이면 N/A 다. 음수 배수를 만들지 않는다.
- **음수 기준연도 CAGR 금지.** 기준연도 값이 0 이하면 CAGR 은 N/A 다.

## 7. 수정공시와 값 충돌

- 동일 항목에 여러 보고서가 있으면 **가장 최신 rcept_no 를 우선**한다(정정공시 우선).
- 자체 계산 지표와 DART `fnlttSinglIndx.json` 지표가 다르면 **둘 다 적는다.**
  자체 계산값을 1차로 쓰고, 불일치는 `counter_evidence` 로 병기한다. 조용히 하나만 고르지 않는다.
- 자체 계산 PER 과 KRX 공표 PER 이 다르면 **양쪽을 모두 제시**한다 —
  KRX 공표치는 최근 **확정** 재무제표 기준이라 분기 갱신이 지연된다. 처리 원칙은 [synthesis-policy.md](./synthesis-policy.md) 참조.

## 8. 위반 시

근거를 이 계약대로 만들 수 없으면 → 그 항목을 **N/A 로 두고 사유를 기록**한다.
데이터 수집 자체가 실패하면 → **보고서를 만들지 않고** 실패 사실을 사용자에게 알린다.
빈칸·0·추정치로 메우는 것은 어떤 경우에도 허용되지 않는다.
