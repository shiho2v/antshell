# quality — 기업 품질 분석 (auto 채점 / Claude 는 해석만)

## 1. 목적
이 모듈은 **"버는 이익이 진짜 현금인가, 그리고 그 이익을 지탱하는 재무 체력은 어떤가"** 에 답한다.
성장 속도(growth)·경쟁우위의 원인(moat)·가격(valuation)은 다루지 않는다.

> **중요 — 이 모듈은 `auto` 다.**
> QUA-01~06 의 등급은 `score_modules.py` 가 `metrics.json` 값과 registry 의 bands 로 **자동 채점**한다.
> **Claude 는 level 을 제출하지 않는다.** judgment 파일의 `criteria` 배열은 **비워 둔다**(`[]`).
> Claude 가 쓰는 것은 `verdict` / `strengths` / `weaknesses` / `counter_evidence` /
> `unknowns` / `invalidating_conditions` 뿐이며, 이는 **서술(narrative)에만** 쓰인다.

## 2. 읽을 파일
| 파일 | 용도 |
|------|------|
| `data/evidence/{ticker}_evidence.json` | `packs.quality` 의 evidence item **만** |
| `data/normalized/{ticker}_metrics.json` | 아래 나열한 키의 `value`/`unit`/`formula`/`na_reason`/`limitations` |
| `modules/quality/rubric.md` | 밴드 정의 (해석 기준) |

**채점되는 지표 (6개):**
`operating_margin_ttm`, `roe_ttm`, `cash_conversion_ttm`, `fcf_margin_ttm`,
`net_debt_to_equity`, `share_change_1y`

**해석에만 쓰는 보조 지표 (채점 안 됨):**
`net_margin_ttm`, `roic_ttm`, `interest_coverage`, `current_ratio`, `capex_to_ocf`,
`fcf_ttm`, `ebitda_ttm`

원시 DART JSON·전체 재무제표는 읽지 않는다. 값은 **이미 계산되어 있다.**

## 3. 분석 절차
1. **메타 확인** — `metrics.json` 의 `fs_div`(연결/별도), `ttm_period`, `ttm_fallback` 을 먼저 본다.
   `ttm_fallback: true` 면 TTM 이 아니라 **최근 연간값으로 폴백**한 것이다. 이 사실을 verdict 에
   반드시 명시하고 `limitations` 를 인용한다.
2. **마진 구조** — `operating_margin_ttm` 과 `net_margin_ttm` 의 **격차**를 본다.
   순이익률이 영업이익률을 크게 웃돌면 영업외수익/일회성 이익 의심, 크게 밑돌면 금융비용·손상·세금
   부담 의심이다. **원인을 단정하지 말고** 관측된 격차와 그로부터 나오는 가설을 구분해 쓴다.
3. **자본수익성** — `roe_ttm` 과 `roic_ttm` 을 함께 본다.
   - ROE 는 **평균자본이 아닌 기말자본** 분모다 (limitations 에 명시됨). 그대로 인용한다.
   - ROIC 는 **유효세율 = 법인세비용/세전이익**, **투하자본 = 자본총계 + 순차입금** 이라는
     **가정 위에서만** 성립한다. 인용할 때 이 가정을 반드시 함께 적는다. 값이 null 이면 N/A.
   - ROE ≫ ROIC 이면 레버리지가 ROE 를 밀어올린 것이다 → `net_debt_to_equity` 로 교차 확인한다.
4. **이익의 현금성** — `cash_conversion_ttm`(영업현금흐름/당기순이익)이 이 모듈의 핵심이다.
   1.0 을 크게 밑돌면 이익이 현금으로 회수되지 않는다는 뜻이며, 운전자본(매출채권·재고) 증가 또는
   이익의 질 저하 가능성을 시사한다. `capex_to_ocf` 와 묶어 **영업현금 → 재투자 → 잉여현금**
   경로를 서술한다.
5. **잉여현금흐름** — `fcf_ttm`(= OCF − |CAPEX|), `fcf_margin_ttm`. FCF 마진이 음수면
   성장 투자 국면인지 현금 소진인지 `capex_to_ocf` 로 구분해 서술한다 (단정하지 않는다).
6. **재무 안정성** — `net_debt_to_equity`(음수 = 순현금), `interest_coverage`, `current_ratio`.
   `net_debt` 이 null 이면 **"무차입"이 아니라 "미확인"** 이다. 절대 무차입으로 쓰지 않는다.
7. **회계상 일회성 항목** — 마진 격차·현금전환율 이상치로 **의심 신호만** 제기한다.
   구체적 일회성 항목의 존재를 주장하려면 근거(공시 evidence)가 있어야 한다.
   근거가 없으면 `unknowns` 로 보낸다.
8. **주식 희석** — `share_change_1y`. 사업보고서 연 1회 스냅샷 기준이라 **기중 증자 반영이
   지연될 수 있다**(limitations). 이 한계를 함께 적는다.
9. 위 관측을 `verdict` 로 종합하고, strengths/weaknesses 를 evidence_ids 와 함께 정리한다.

## 4. 판단 규칙
- **값이 null 인 지표는 N/A 다. 0 이 아니다.** Python 이 해당 criterion 을 분자·분모에서 제외한다.
  Claude 는 verdict 에서 "N/A" 로 부르고 그 사유(`na_reason`)를 그대로 인용한다.
- `cash_conversion_ttm` 은 **순이익이 0 이하이면 N/A** 다 (적자 기업의 현금전환율은 무의미).
  이를 "현금창출력 0" 으로 서술하지 않는다.
- 지표를 **다시 계산하지 않는다.** 곱셈·나눗셈·증감률 계산 금지. 값은 인용만 한다.
- 산업 평균·경쟁사 대비 비교는 **UNSUPPORTED** 다. 비교 대상 데이터가 없다. 하지 않는다.
- 사전 학습 지식으로 수치를 보완하거나 정당화하지 않는다.

## 5. 출력
`data/module-results/{ticker}_quality_judgment.json`

```json
{
  "module": "quality",
  "criteria": [],
  "strengths": [{"point": "영업이익률 TTM 기준 ...", "evidence_ids": ["Q-OPERATINGM-001"]}],
  "weaknesses": [{"point": "현금전환율이 순이익을 크게 밑돈다 ...", "evidence_ids": ["Q-CASHCONVER-001"]}],
  "counter_evidence": [{"point": "다만 ROIC 는 유효세율 가정에 민감하다", "evidence_ids": ["Q-ROICTTM-001"]}],
  "unknowns": ["일회성 항목의 구체 내역 — 공시 근거 없음", "산업 평균 마진 — UNSUPPORTED"],
  "invalidating_conditions": ["운전자본 증가가 2개 분기 더 이어져 현금전환율이 0.5x 아래로 내려가면 이 판단은 무효다"],
  "verdict": "500단어 이내. 모든 수치에 (출처, 기준일) 병기. 매수/매도 표현 금지."
}
```

- `criteria` 는 **반드시 빈 배열**이다. level 을 넣지 않는다 (넣어도 auto 채점이 덮어쓴다).
- strengths/weaknesses 는 각 **최대 5개**, 항목마다 `evidence_ids` **1개 이상 필수**.
- evidence_id 는 pack 에서 `metric` 필드로 매칭해 확인한 실제 ID 만 쓴다. **지어내지 않는다.**

## 6. 금지 사항
- 등급(level) 제출 — 이 모듈은 Python 이 채점한다.
- 지표 재계산·암산·반올림 변경.
- `net_debt = null` 을 "무차입"으로 해석하는 것.
- 적자 기업의 현금전환율·ROE 를 "0" 으로 서술하는 것.
- 산업 평균/경쟁사 비교, 컨센서스 인용, 목표주가.
- 매수/매도/비중확대 표현.
