# risk — 위험 모듈 지침

> 이 파일은 **risk 모듈이 실행될 때만** 읽는다. 미리 읽지 않는다.

## 1. 목적

이 기업의 투자 논리를 훼손할 수 있는 위험을 7개 축(RSK-01~07)으로 구조화하고,
각 위험이 **어떤 조건에서 현실화되는지**와 **무엇을 보면 미리 알 수 있는지**를 서술한다.

7개 criterion 전부 `type: judged` 다.
→ **Claude 가 등급(level 0~3)과 evidence_ids 를 제출한다. 산술은 하지 않는다.**

**`inverse_scale: true` — 이 모듈은 점수가 높을수록 위험이 낮다.**
즉 등급 3 = "이 위험이 낮다/잘 통제되고 있다", 등급 0 = "이 위험이 크다".
방향을 반대로 매기면 종합점수 전체가 뒤집힌다. 매 항목마다 확인한다.

## 2. 읽을 파일

| 파일 | 용도 |
|------|------|
| `data/evidence/{ticker}_evidence.json` | `packs.risk` 에 나열된 evidence item 만 |
| `data/normalized/{ticker}_metrics.json` | hint_metrics 값 조회 |
| `data/raw/{ticker}_dart_events.json` | 공시 사건 (자본변동, 설비투자, 손익 등) |
| `data/{ticker}_analysis_contract.json` | prohibited_inferences, unsupported_data, unresolved_items |
| `modules/risk/rubric.md` | 7개 항목 등급 정의 |

hint_metrics: RSK-03 → `net_debt_to_equity`, `interest_coverage`, `current_ratio`
RSK-05 → `capex_to_ocf`, `share_change_1y`

사업보고서 원문 근거(`B-FILING-001`)는 risk 팩에 공유된다 — 집중도·원재료·규제 서술의 근거로 쓴다.
**원시 API 응답이나 전체 재무제표는 읽지 않는다.**

## 3. 분석 절차

1. evidence pack 을 먼저 훑고, 각 위험 축에 **실제로 붙일 수 있는 근거가 있는지** 확인한다.
2. 각 항목(RSK-01~07)마다 아래 6요소를 **모두** 채운 서술을 만든다. 하나라도 비면 그 위험은
   "확인 필요(unknowns)"로 내리고, 지어내지 않는다.

   | 요소 | 설명 |
   |------|------|
   | 위험 내용 | 무엇이 잘못될 수 있는가 (한 문장) |
   | 근거 | evidence_id + (출처, 기준일). 근거 없는 위험은 등재 금지 |
   | 발생 가능성 | 높음/중간/낮음 — 근거에서 따라 나오는 수준으로만 |
   | 영향도 | 매출·이익·현금흐름 중 어디를 얼마나 타격하는가 |
   | 선행지표 | 무엇을 관측하면 먼저 알 수 있는가 (분기 실적 항목, 공시 유형 등) |
   | **투자 논리 훼손 조건** | 이 위험이 어디까지 가면 판단이 뒤집히는가 (수치·사건으로) |

3. `hint_metrics` 가 있는 항목(RSK-03, RSK-05)은 지표 값을 반드시 인용한다.
   지표가 N/A 면 등급을 낮게 주지 말고 **N/A + na_reason** 으로 처리한다.
4. **데이터 불확실성 그 자체를 하나의 위험으로 서술한다.**
   - 예: KRX 자격증명 미설정 → 수급·시장 국면 미확인 → 밸류에이션·수급 위험(RSK-06) 판단 신뢰도 저하.
   - 예: 사업부문별 매출 구조가 구조화 API 로 제공되지 않음 → 집중도 위험(RSK-02) 정량 확인 불가.
   - 이런 항목은 `unknowns` 에 반드시 남기고, verdict 에서 신뢰도 한계로 언급한다.
5. 마지막으로 `invalidating_conditions` 에 **모듈 전체의 판단을 뒤집을 조건**을 정리한다
   (개별 위험의 "투자 논리 훼손 조건"을 종합).

## 4. 판단 규칙

- **근거 없는 위험은 등재하지 않는다.** 모든 judged 항목은 `requires_evidence: 1` — evidence_id 없으면
  score_modules.py 가 자동으로 N/A 처리한다.
- **N/A ≠ 0점.** 위험을 확인할 데이터가 없는 것과 위험이 큰 것은 다르다.
  전자는 `level: null` + `na_reason`, 후자는 `level: 0`.
- **inverse_scale 재확인:** "위험이 크다" → **낮은 등급(0~1)**. "위험이 통제된다" → 높은 등급(2~3).
- 뉴스·기억으로 위험을 만들지 않는다. 공시·재무·사업보고서 원문에 없는 사건은 쓰지 않는다.
- 컨센서스·목표주가·시장점유율·업황 전망치: 데이터가 없다. 생성 금지.
- 확률을 수치로 만들지 않는다("30% 확률"). 높음/중간/낮음의 정성 등급만 쓴다.
- 모든 산술 금지. metrics.json 에 없는 수치를 만들지 않는다.

## 5. 출력

`data/module-results/{ticker}_risk_judgment.json`

```json
{
  "module": "risk",
  "ticker": "009150",
  "criteria": [
    {"criterion_id": "RSK-01", "level": 2,
     "evidence_ids": ["Q-OPERATINGMA-001", "B-FILING-001"],
     "rationale": "위험 내용/근거/발생가능성/영향도/선행지표/훼손조건을 담은 서술",
     "na_reason": null},
    {"criterion_id": "RSK-04", "level": null, "evidence_ids": [],
     "rationale": null, "na_reason": "회계 이슈를 확인할 감사의견·주석 근거 없음 — 추정하지 않는다"}
  ],
  "strengths": [{"point": "…", "evidence_ids": ["…"]}],
  "weaknesses": [{"point": "…", "evidence_ids": ["…"]}],
  "counter_evidence": [{"point": "…", "evidence_ids": ["…"]}],
  "unknowns": ["사업부문별 매출 비중 — 구조화 데이터 없음"],
  "invalidating_conditions": ["순차입금/자기자본이 1.0배를 넘고 이자보상배율이 2배 미만으로 하락"],
  "verdict": "500단어 이내"
}
```

- RSK-01~07 **7개 항목 모두** `criteria` 에 등장해야 한다 (N/A 라도 na_reason 과 함께).
- strengths/weaknesses 각 5개 이내, 항목마다 evidence_ids 1개 이상.
- verdict 500단어 이내, 매수/매도 표현 금지.

## 6. 금지 사항

1. 근거(evidence_id) 없는 위험 등재.
2. inverse_scale 반대로 채점 (위험이 큰데 높은 등급).
3. 데이터 부족을 낮은 등급으로 처리 (→ N/A + na_reason 이어야 한다).
4. 뉴스·기억 기반 위험 서술, 확률의 수치화.
5. 컨센서스·목표주가·시장점유율·업황 전망 인용.
6. 모든 직접 산술.
