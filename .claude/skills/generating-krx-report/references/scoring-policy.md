# 채점 정책 (Scoring Policy)

관련 문서: [evidence-policy.md](./evidence-policy.md) · [synthesis-policy.md](./synthesis-policy.md) · [report-style.md](./report-style.md) · [canslim-rubric.md](./canslim-rubric.md)
기준 파일: [`config/module-registry.yaml`](../config/module-registry.yaml) · [`config/analysis-modes.yaml`](../config/analysis-modes.yaml) · [`schemas/module-result.schema.json`](../schemas/module-result.schema.json)

## 0. 단 하나의 규칙: Claude 는 산술하지 않는다

**점수 계산은 `scripts/score_modules.py` 만 한다.**
Claude 는 성장률·CAGR·배수·합계·가중평균을 **직접 계산하지 않는다.** 암산도, 검산도 하지 않는다.
Claude 가 하는 일은 두 가지뿐이다.

1. 정성 criterion 에 대해 **서수 등급(level 0~3) + evidence_ids** 를 제출한다.
2. 산출된 점수를 **읽어서 서술**한다.

## 1. module-registry.yaml 이 단일 진실 원천이다

- `score_modules.py` 는 **이 파일만** 읽어 채점한다.
- `references/*.md`(이 문서, rubric 문서 포함)는 사람과 Claude 가 읽는 **산문 설명일 뿐 채점을 구동하지 않는다.**
- 문서와 registry 가 어긋나면 **registry 가 이긴다.** 문서를 근거로 점수를 바꾸지 않는다.
- `validate_report.py` 가 registry 로 점수를 **독립 재계산**해 보고서와 대조한다(Gate 3).

## 2. criterion 의 두 종류

### `type: auto` — Python 이 채점한다
`metrics.json` 의 값을 registry 의 `bands` 에 넣어 level 을 정한다. **Claude 개입 없음.**

```yaml
- id: QUA-02
  name: ROE (TTM)
  type: auto
  weight: 18
  metric: roe_ttm
  direction: higher_better
  bands: [[null, 5, 0], [5, 10, 1], [10, 15, 2], [15, null, 3]]
```
각 밴드는 `[min, max, level]` 이며 `[min, max)` 구간이다. `null` = 무한대.
지표가 없으면 level = `null`(N/A) — **0 이 아니다.**

### `type: judged` — Claude 가 등급만 제출한다
Claude 는 rubric 과 evidence 를 읽고 **0~3 정수 하나**와 **evidence_ids** 만 낸다.
파일: `data/module-results/{ticker}_{module}_judgment.json`

```json
{
  "module": "moat",
  "criteria": [
    {"criterion_id": "MOA-01", "level": 2,
     "evidence_ids": ["B-FILING-001", "Q-OPERATINGMA-001"],
     "rationale": "사업보고서 원문에 인증·품질 요건 서술이 있고, 영업이익률이 8분기 연속 두 자릿수를 유지했다."},
    {"criterion_id": "MOA-02", "level": null,
     "evidence_ids": [],
     "na_reason": "원가구조를 뒷받침할 공시 근거가 없다 — 추정하지 않는다."}
  ],
  "strengths":   [{"point": "...", "evidence_ids": ["Q-OPERATINGMA-001"]}],
  "weaknesses":  [{"point": "...", "evidence_ids": ["G-REVYOY-001"]}],
  "counter_evidence": [{"point": "...", "evidence_ids": ["V-PER-002"]}],
  "unknowns": ["사업부문별 원가 배분은 공시되지 않는다"],
  "invalidating_conditions": ["영업이익률이 2개 분기 연속 5%p 이상 하락"],
  "verdict": "500단어 이내 서술. 매수/매도 표현 금지."
}
```
`level` 은 **정수 0~3 또는 null** 이어야 한다. 소수점·백분율·점수를 넣으면 스크립트가 즉시 실패한다.

## 3. level 의 의미 (0~3)

| level | 의미 |
|---|---|
| **3** | 탁월 — 근거가 여러 갈래로 일관되게 강함 |
| **2** | 양호 — 근거가 명확하나 결정적이지는 않음 |
| **1** | 제한적 — 근거가 약하거나 부분적 |
| **0** | **근거상 명백히 취약** — "데이터가 없다"가 아니라 **"있는 근거가 나쁘다"** |
| `null` | **N/A** — 판단할 근거 자체가 없다. `na_reason` 필수 |

> 0 과 null 의 구분이 이 스킬의 핵심이다. 모르면 **0 이 아니라 null** 이다.

`inverse: true`(BUS-03 집중도 위험, CAT-04 선반영)는 **높은 level = 위험이 낮음/선반영이 적음**을 뜻한다.
`risk` 모듈은 `inverse_scale: true` — 모듈 점수가 높을수록 위험이 낮다.

## 4. 점수 공식 (참고용 — Claude 는 실행하지 않는다)

```
모듈점수 = Σ(weight_i × level_i / 3) / Σ(weight_i, 채점된 i만) × 100
```
- **N/A criterion 은 분자와 분모 양쪽에서 제외**된다. 0점을 주지 않는다.
- 채점 가능한 criterion 이 하나도 없으면 `score = null`, `status = insufficient_data`.

## 5. N/A 처리 규칙 (Gate 3 검증 대상)

| 상황 | 결과 |
|---|---|
| 지표가 계산되지 않음 | `level: null` + `na_reason` |
| `requires_credentials` 미충족 (KRX_ID/KRX_PW 없음 → TRD-I, TRD-L, TRD-M) | `level: null` + "자격증명 없음" |
| 적자기업 PER·EV/EBITDA (`na_if_negative_earnings`) | `level: null` |
| `requires_evidence` 미달 | `level: null` + "근거 부족" |
| 인접 분기 보고서 결측으로 분기단독값 불가 | `level: null` |

**`na_reason` 이 없는 N/A 는 Gate 3 실패다.** 사유를 반드시 남긴다.

### requires_evidence
criterion 이 요구하는 **최소 근거 수**를 못 채우면, level 을 제출했더라도 **N/A 로 강등**된다.
근거 없는 판단은 채점하지 않는다.

### distinct_evidence_types: true
`moat` 의 MOA-01·MOA-02·MOA-03 은 `requires_evidence: 2` + `distinct_evidence_types: true` 다.
→ **서로 다른 종류의 근거 2개 이상**이 필요하다. "다른 종류"란 `evidence_type` 이 다르거나
(`filing_text` + `metric`) `source_type` 이 다른 경우(`official_filing` + `derived_calculation`)를 말한다.
**같은 재무지표 2개는 2개로 세지 않는다.** 경쟁우위는 재무 하나로 증명되지 않는다.

## 6. score ≠ confidence ≠ evidence_coverage

세 값은 서로 다른 질문에 답한다. 혼동하면 보고서가 거짓말을 하게 된다.

| 값 | 질문 | 낮다는 뜻 |
|---|---|---|
| **score** (0~100) | "이 **기업**이 좋은가?" | 기업이 이 축에서 약하다 |
| **confidence** (0~1) | "이 **판단**을 믿을 수 있는가?" | 근거가 적거나 상충 근거가 많다 |
| **evidence_coverage** (0~1) | "필요한 **데이터**를 얼마나 확보했는가?" = 채점된 criterion 수 / 전체 criterion 수 | 데이터를 못 구했다 |

> **데이터 부족은 낮은 점수가 아니라 낮은 confidence / coverage 로 표현한다.**
> KRX 자격증명이 없어 CANSLIM I·M·L 이 N/A 라면 → trend 점수를 깎는 게 아니라 coverage 가 4/7 로 떨어진다.

## 7. 종합점수와 재정규화

- 종합점수는 `analysis-modes.yaml` 의 모드별 가중치(합 100)로 계산한다. 기본 모드는 `balanced`.
- **일부 모듈만 실행하면**(예: `canslim` 프로필 = growth + trend) 실행·채점된 모듈의 가중치만 남기고
  **합이 100 이 되도록 재정규화**한다. `score = null` 인 모듈은 종합에서 제외된다.
- 재정규화가 일어나면 `composite.renormalized: true` 가 되고, **보고서에 그 사실을 명시**해야 한다.
- 등급은 점수만으로 정하지 않는다. `data_completeness < 0.5` 또는 `confidence < 0.4` 또는 게이트 실패이면
  **점수와 무관하게 「판단 유보」로 강등**된다.
- 등급은 4개뿐이다: **긍정적 관찰(≥70) / 중립적 관찰(≥50) / 보수적 관찰 / 판단 유보.**
  **매수·매도·목표주가 표현은 금지**된다.

## 8. Claude 의 체크리스트

- [ ] judgment 파일에 **정수 level 과 evidence_ids** 만 넣었는가? (계산식·점수·백분율 없음)
- [ ] 근거가 없는 criterion 을 0 이 아니라 **null + na_reason** 으로 두었는가?
- [ ] moat 의 근거 2개가 **서로 다른 종류**인가?
- [ ] `counter_evidence` 를 숨기지 않았는가? (숨기면 confidence 가 거짓으로 높아진다)
- [ ] 점수를 **직접 계산하지 않고** `score_modules.py` 출력만 인용했는가?
