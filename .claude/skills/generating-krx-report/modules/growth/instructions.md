# growth — 성장성 분석 (auto 채점 / Claude 는 해석만)

## 1. 목적
이 모듈은 **"얼마나 빠르게 커지고 있으며, 그 성장이 가속되고 있는가, 그리고 수익성을 동반하는가"**
에 답한다. 성장의 **원인**(해자·기술우위)은 moat 모듈, 성장의 **가격**은 valuation 모듈의 몫이다.

> **중요 — 이 모듈은 `auto` 다.**
> GRO-01~07 의 등급은 `score_modules.py` 가 `metrics.json` + registry bands 로 자동 채점한다.
> **Claude 는 level 을 제출하지 않는다.** judgment 의 `criteria` 는 **빈 배열**(`[]`)로 둔다.
> Claude 는 `verdict`/`strengths`/`weaknesses`/`counter_evidence`/`unknowns`/
> `invalidating_conditions` 만 쓰며, 이는 **서술에만** 쓰인다.

> **재사용 계약 (반드시 준수)**
> `GRO-03`(`eps_yoy_q`) 와 `GRO-05`(`op_cagr_3y`) 는 **trend 모듈의 CANSLIM C·A 로 그대로
> 재사용된다.** trend 에서 다시 계산하지 않으며, evidence_id 도 동일한 것을 재참조한다.
> 따라서 이 두 지표의 해석은 여기서 확정하고, 이후 모듈은 이를 뒤집지 않는다.

## 2. 읽을 파일
| 파일 | 용도 |
|------|------|
| `data/evidence/{ticker}_evidence.json` | `packs.growth` 의 evidence item **만** |
| `data/normalized/{ticker}_metrics.json` | 아래 키의 `value`/`period`/`formula`/`na_reason`/`limitations` |
| `modules/growth/rubric.md` | 밴드 정의 |

**채점되는 지표 (7개):**
`rev_yoy_q`, `op_yoy_q`, `eps_yoy_q`, `rev_cagr_3y`, `op_cagr_3y`,
`growth_acceleration_pp`, `profitable_growth_gap_pp`

**해석 보조 (채점 안 됨):** `eps_cagr_3y`, `capex_to_ocf`, `operating_margin_ttm`, `revenue_ttm`

원시 DART JSON·전체 재무제표는 읽지 않는다. 값은 **이미 계산되어 있다.**

## 3. 분석 절차
1. **기간 메타 확인** — 각 지표의 `period` 를 본다. 분기 YoY 는 **분기 단독값(누적 아님)** 이며
   **같은 분기끼리만** 비교된다 (예: 2025Q2 vs 2024Q2). 이 사실을 verdict 에 명시한다.
2. **분기 YoY 3종** — `rev_yoy_q`(매출), `op_yoy_q`(영업이익), `eps_yoy_q`(EPS)를 함께 읽는다.
   - 세 값의 **순서**가 정보다. EPS YoY > 영업이익 YoY > 매출 YoY 이면 마진 개선 + 주식수 안정
     또는 영업외 이익 기여를 시사한다. 역순이면 그 반대다.
   - EPS YoY 가 영업이익 YoY 를 크게 웃돌면 **일회성 영업외 이익 또는 세금 효과** 가능성을
     제기하되, 근거 없이 단정하지 않는다 → `unknowns` 또는 `counter_evidence` 로 보낸다.
3. **3년 CAGR** — `rev_cagr_3y`, `op_cagr_3y`. 4개 연말값이 필요하다. 부족하면 N/A 다.
   기준연도 값이 0 이하이면 CAGR 은 **정의되지 않는다**(N/A). 이를 "성장 0%" 로 쓰지 않는다.
4. **단기 vs 장기 대조** — 분기 YoY 와 3년 CAGR 의 방향이 어긋나면 그것이 이 모듈의 핵심 서술이다.
   (예: CAGR 은 높은데 최근 분기 YoY 가 음수 → 사이클 하강 진입 가설.)
5. **가속/둔화** — `growth_acceleration_pp` = 이번 분기 매출 YoY − 직전 분기 매출 YoY (%p).
   양수면 가속, 음수면 둔화다. **단 2개 분기만의 비교**이므로 추세로 과잉 일반화하지 않는다.
6. **수익성 동반 성장** — `profitable_growth_gap_pp` = 영업이익 YoY − 매출 YoY (%p).
   양수면 매출보다 이익이 빨리 늘어 **영업 레버리지가 작동**한 것이고, 음수면 매출은 늘어도
   마진이 훼손된 것이다. `operating_margin_ttm` 과 묶어 서술한다.
7. **성장의 재원과 지속 가능성** — `capex_to_ocf` 로 성장 투자 강도를 본다.
   R&D 지출·수주잔고는 **구조화 API 가 없다** → 아래 4번 규칙 참조.
8. `verdict` 로 종합한다. **C·A 재사용 지표(`eps_yoy_q`, `op_cagr_3y`)의 해석을 명시적으로 남긴다.**

## 4. 판단 규칙
- **사업부별 성장률은 N/A 다.** 부문별 매출은 구조화 DART API 가 없다.
  evidence pack 에 `B-FILING-001`(사업보고서 원문)이 있으면 **원문 서술로만** 정성 언급이 가능하며,
  이때도 **성장률을 직접 계산하지 않는다.** 원문에 부문별 수치가 표로 있어도 계산은 금지다
  (모든 산술은 Python 에서만 일어난다). 원문이 없으면 부문별 성장은 언급 자체를 하지 않는다.
- **R&D 지출·수주잔고·생산능력 증설 계획은 구조화 API 가 없다.** `--with-document` 로 확보된
  원문이 있을 때만 정성 인용, 없으면 **N/A** 이며 `unknowns` 에 적는다.
- **컨센서스·가이던스·목표주가·경쟁사 성장률은 UNSUPPORTED** — 생성 금지.
- **적자 → 적자 변화를 성장률로 표기하지 않는다.** 기준값이 0 이하인 YoY/CAGR 은 N/A 다.
- 값이 null 인 지표는 **N/A 이며 0 이 아니다.** verdict 에서 `na_reason` 을 그대로 인용한다.
- 지표를 **다시 계산하지 않는다.** 뺄셈·나눗셈·연율화 전부 금지.

## 5. 출력
`data/module-results/{ticker}_growth_judgment.json`

```json
{
  "module": "growth",
  "criteria": [],
  "strengths": [{"point": "최근 분기 영업이익 YoY 가 매출 YoY 를 상회해 영업 레버리지가 확인된다",
                 "evidence_ids": ["G-OPYOYQ-001", "G-PROFITABL-001"]}],
  "weaknesses": [{"point": "성장 가속도가 음수로 전환됐다", "evidence_ids": ["G-GROWTHACC-001"]}],
  "counter_evidence": [{"point": "EPS YoY 가 영업이익 YoY 를 크게 웃돈다 — 영업외 요인 가능성",
                        "evidence_ids": ["G-EPSYOYQ-001"]}],
  "unknowns": ["사업부별 성장률 — 구조화 API 없음", "수주잔고 / R&D 지출 — 원문 미확보", "컨센서스 — UNSUPPORTED"],
  "invalidating_conditions": ["다음 분기 매출 YoY 가 음수로 전환되면 가속 서술은 무효다"],
  "verdict": "500단어 이내. 분기 단독 기준·비교 분기를 명시. 매수/매도 표현 금지."
}
```

- `criteria` 는 **반드시 빈 배열**이다.
- strengths/weaknesses 각 **최대 5개**, 항목마다 `evidence_ids` **1개 이상 필수**.
- evidence_id 는 pack 에서 `metric` 필드로 매칭해 확인한 실제 ID 만 쓴다. **지어내지 않는다.**

## 6. 금지 사항
- 등급(level) 제출 — Python 이 채점한다.
- 성장률·CAGR·가속도 재계산 (원문 표의 부문별 수치 계산 포함).
- **trend 모듈에서 `eps_yoy_q`·`op_cagr_3y` 를 재계산하는 것** — 반드시 재사용한다.
- 누적(YTD) 값과 분기 단독값을 섞어 비교하는 것.
- 적자 기준 성장률 표기, 컨센서스·가이던스·목표주가 생성.
- 매수/매도/비중확대 표현.
