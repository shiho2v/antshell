# valuation — 밸류에이션 모듈 지침

> 이 파일은 **valuation 모듈이 실행될 때만** 읽는다. 미리 읽지 않는다.

## 1. 목적

현재 주가가 이 기업의 이익·자산·현금흐름 대비 어느 수준인지 판단한다.
"싸다/비싸다"를 단정하는 것이 목적이 아니라, **현재 가격에 어떤 기대가 내재되어 있는지**를
근거와 함께 서술하는 것이 목적이다.

이 모듈의 6개 criterion(VAL-01~06)은 전부 `type: auto` 다.
→ **점수는 score_modules.py 가 metrics 값과 registry 밴드로 자동 계산한다.**
→ Claude 는 등급(level)을 제출하지 않는다. **해석 서술만** 작성한다.

## 2. 읽을 파일

| 파일 | 용도 |
|------|------|
| `data/normalized/{ticker}_metrics.json` | 지표 값 + formula + inputs + rcept_no + na_reason |
| `data/evidence/{ticker}_evidence.json` | `packs.valuation` 에 나열된 evidence item 만 |
| `data/{ticker}_analysis_contract.json` | peer_comparison, prohibited_inferences, unsupported_data, credentials_available |
| `modules/valuation/rubric.md` | 각 지표의 해석 기준 |

**원시 API 응답(`data/raw/*.json`)이나 전체 재무제표를 읽지 않는다.** evidence pack이 유일한 근거 단위다.

사용 지표 키: `per_trailing`, `pbr`, `ev_ebitda`, `earnings_yield`, `fcf_yield`, `psr`
해석 보조 키: `roe_ttm`(PBR 해석용), `operating_margin_ttm`(PSR 해석용),
`market_cap`, `ev`, `ebitda_ttm`, `close_price`, `net_debt`, `rev_cagr_3y`, `op_cagr_3y`

## 3. 분석 절차

1. metrics.json 에서 6개 지표의 `value` / `na_reason` / `formula` / `rcept_nos` 를 확인한다.
2. **N/A 지표를 먼저 분리한다.** 값이 없는 지표는 서술에서 "N/A + 사유"로만 다루고,
   낮은 값으로 취급하거나 다른 지표로 대체 추정하지 않는다.
3. 각 지표를 rubric.md 의 해석 기준에 따라 읽는다. 특히:
   - **PBR 은 반드시 ROE 와 함께 읽는다.** ROE 15% 기업의 PBR 1.5배와
     ROE 3% 기업의 PBR 1.5배는 전혀 다른 의미다.
   - **PSR 은 반드시 영업이익률과 함께 읽는다.** 이익률 2% 기업의 PSR 1배는 싸지 않다.
   - EV/EBITDA 는 `net_debt` 을 함께 인용해 자본구조 차이를 설명한다.
4. **성장률 대비 멀티플**: `rev_cagr_3y` / `op_cagr_3y` 를 인용해 "이 멀티플이
   과거 성장률에 비추어 어떤 의미인지" 정성적으로 서술한다.
   → **PEG 를 직접 계산하지 않는다.** Claude 는 어떤 산술도 하지 않는다.
     precomputed 값이 metrics.json 에 없으면 수치 대신 문장으로 서술한다.
5. **현재 가격에 내재된 기대**를 명시한다. 예: "Earnings Yield x%는 현재 이익 수준이
   유지된다는 가정을 가격이 이미 반영하고 있음을 뜻한다" 수준의, 지표에서 직접 따라 나오는 서술만.
6. **역사적 밴드**: `credentials_available` 에 KRX_ID/KRX_PW 가 있을 때만 다룬다.
   없으면 unknowns 에 "역사적 PER/PBR 밴드 — 지수·KRX 공표 데이터 미확보로 N/A" 로 남긴다.
7. **동종기업 비교**: `analysis_contract.peer_comparison.requested == true` 이고
   `explicit_peers` 에 비교기업이 명시된 경우에만 수행한다.
   계약에 없으면 **비교 섹션 자체를 생략한다.** 기억으로 동종기업을 고르지 않는다.
8. KRX 공표 PER/PBR 이 evidence 에 함께 존재하고 본문 Trailing PER 과 다르면,
   본문에는 **DART 기반 자체 계산값**을 쓰고 KRX 값은 `counter_evidence` 에 병기한다
   (KRX 공표치는 최근 확정 재무제표 기준이라 지연된다).

## 4. 판단 규칙 (결측 데이터 처리 / 추론 금지 항목)

- **N/A ≠ 0점.** 적자기업의 PER 은 `na_if_negative_earnings` 로 N/A 처리된다.
  "적자라서 PER 0점" 같은 서술은 금지다. EBITDA ≤ 0 이면 EV/EBITDA 도 동일하게 N/A.
- **시가총액 한계 명시:** market_cap = 종가(pykrx→Naver Finance 경유) × 발행주식수(DART stockTotqySttus).
  **두 값의 기준일이 다르다.** 시총·EV·PER·PBR·PSR 을 인용할 때 이 한계를 최소 1회 명시한다.
- pykrx 는 **비공식 래퍼(unofficial_wrapper)** 이며 기본 OHLCV 는 Naver Finance 를 경유한다.
  가격 기반 지표에는 이 출처 한계를 붙인다.
- 다음은 **데이터가 존재하지 않는다. 생성 시 즉시 위반이다:**
  컨센서스, Forward EPS, **Forward PER**, **목표주가**, 시장점유율, 적정주가, 업종 평균 멀티플.
- 어떤 산술도 하지 않는다. metrics.json 에 없는 수치는 보고서에 넣지 않는다.
- 외부 지식(사전 학습된 "이 회사는 원래 PER 10배 수준")으로 수치를 보완하지 않는다.

## 5. 출력

`data/module-results/{ticker}_valuation_judgment.json` 에 저장한다.
**auto 모듈이므로 `criteria` 배열은 비워 둔다(또는 생략). level 을 제출하지 않는다.**

```json
{
  "module": "valuation",
  "ticker": "009150",
  "criteria": [],
  "strengths":  [{"point": "…", "evidence_ids": ["V-PERTRAILIN-001"]}],
  "weaknesses": [{"point": "…", "evidence_ids": ["V-PBR-001", "Q-ROETTM-001"]}],
  "counter_evidence": [{"point": "KRX 공표 PER 은 x배로 자체 계산값과 다르다", "evidence_ids": ["…"]}],
  "unknowns": ["역사적 PER 밴드 — KRX 자격증명 없음", "동종기업 비교 — 계약에 비교기업 미지정"],
  "invalidating_conditions": ["…"],
  "verdict": "500단어 이내"
}
```

- strengths / weaknesses 는 **각 5개 이내**, 항목마다 `evidence_ids` **1개 이상 필수**.
- verdict 500단어 이내, **매수/매도 표현 금지**.
- 모든 수치에 (출처, 기준일) 병기.

## 6. 금지 사항

1. **Forward PER 계산 금지** — 검증된 Forward EPS 가 존재하지 않는다.
2. **목표주가·적정주가 생성 금지.**
3. **컨센서스·시장점유율 인용 금지** (unsupported_data).
4. **PEG 를 포함한 모든 직접 산술 금지.**
5. 계약에 명시되지 않은 동종기업과 비교 금지.
6. 적자기업에 PER 0점 부여 금지 — N/A + 사유.
7. level(등급) 제출 금지 — auto 모듈의 점수는 Python 이 계산한다.
8. 매수/매도/비중확대 등 투자 권유 표현 금지.
