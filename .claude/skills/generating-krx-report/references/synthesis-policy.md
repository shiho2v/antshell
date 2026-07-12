# 합성 정책 (Synthesis Policy)

보고서를 **쓰는 단계**의 규칙이다. 이 단계에서 Claude 는 **원본 데이터를 다시 읽지 않는다.**
관련 문서: [evidence-policy.md](./evidence-policy.md) · [scoring-policy.md](./scoring-policy.md) · [report-style.md](./report-style.md)
검증 스크립트: `scripts/validate_report.py` (Gate 3 + Gate 4)

## 1. 합성 시점에 읽어도 되는 것 (화이트리스트)

| 읽는다 | 경로 |
|---|---|
| 최종 원장 | `data/{ticker}_manifest.json` |
| 종합점수 | `data/{ticker}_composite.json` |
| 모듈 결과 | `data/module-results/{ticker}_{module}.json` |
| 개별 근거 (**ID 로 지목해서만**) | `data/evidence/{ticker}_evidence.json` |

**읽지 않는다:** raw API JSON(`data/raw/*`), 재무제표 전문, DART 원문 XML 전체, `metrics.json` 통째로.

> 이유: 원본을 다시 읽으면 Claude 가 **숫자를 새로 계산하거나 근거 없는 사실을 끌어오게 된다.**
> 필요한 숫자는 이미 evidence item 으로 정제되어 있다. 없으면 **없는 것이다** — 원본을 뒤져서 만들지 않는다.

## 2. 주장 규율 (Claim Discipline)

보고서의 **모든 핵심 문장은 claim 객체 하나**로 등록된다.
등록되지 않은 주장, 근거 없는 주장은 **최종 보고서에서 삭제된다.** (Gate 4)

### claim_type 과 최소 근거 수

| claim_type | 뜻 | 최소 evidence |
|---|---|---|
| `fact` | 공시·시세로 직접 확인되는 사실 | **1개 이상** |
| `derived_interpretation` | 여러 근거를 엮은 해석 | **2개 이상** |
| `conditional_view` | 조건부 전망 ("~하면 ~할 수 있다") | **1개 이상** |
| `unknown` | 확인하지 못했음을 밝히는 문장 | 0개 (추정으로 대체 금지) |

추가 규칙:
- **경쟁우위 주장**은 evidence 2개 이상이되 **서로 다른 종류**여야 한다
  (예: `filing_text` + `metric`). 재무지표 2개는 2개로 세지 않는다. → [scoring-policy.md](./scoring-policy.md#5-na-처리-규칙-gate-3-검증-대상)
- **인과 주장**("~때문에", "~덕분에", "~영향으로", "따라서")에는 `causal_path` 를 반드시 채운다.
  **상관은 인과가 아니다.** 경로를 못 쓰면 인과 표현을 쓰지 않는다.
- **전망은 오직 조건부 문장으로만.** 단정적 미래 서술은 금지다.
  목표주가·컨센서스·Forward PER 은 **어떤 형태로도 생성하지 않는다** (데이터 출처가 없다).

### 상충 근거는 반드시 드러낸다
결론과 어긋나는 근거는 `counter_evidence_ids` 에 넣는다. **숨기면 안 된다.**
상충 근거가 하나도 없으면 Gate 4 가 경고를 낸다 — "정말 없는지 재확인 필요".

## 3. claims 파일 형식

`validate_report.py --claims` 가 소비하는 파일이다. 경로 예: `data/{ticker}_claims.json`

```json
{
  "ticker": "009150",
  "claims": [
    {
      "claim_id": "CLM-0001",
      "claim": "2026년 1분기 매출은 전년 동기 대비 18.4% 증가했다.",
      "claim_type": "fact",
      "module": "growth",
      "evidence_ids": ["G-REVYOYQ-001"],
      "counter_evidence_ids": [],
      "causal_path": null,
      "confidence": "high",
      "validation": "pending"
    },
    {
      "claim_id": "CLM-0002",
      "claim": "매출 성장과 함께 영업이익률이 확대되어 수익성을 동반한 성장이 나타났다.",
      "claim_type": "derived_interpretation",
      "module": "growth",
      "evidence_ids": ["G-REVYOYQ-001", "G-OPYOYQ-001", "Q-OPERATINGMA-001"],
      "counter_evidence_ids": ["Q-CASHCONV-001"],
      "causal_path": null,
      "confidence": "medium",
      "validation": "pending"
    },
    {
      "claim_id": "CLM-0003",
      "claim": "전방 수요가 회복되면 가동률 개선이 영업레버리지로 이어질 수 있다.",
      "claim_type": "conditional_view",
      "module": "catalyst",
      "evidence_ids": ["C-EVENT-002"],
      "counter_evidence_ids": [],
      "causal_path": "전방 수요 회복 → 출하량 증가 → 고정비 분산 → 영업이익률 개선. 각 단계는 미확인이며 조건부다.",
      "confidence": "low",
      "validation": "pending"
    },
    {
      "claim_id": "CLM-0004",
      "claim": "사업부문별 매출 구성비는 확인하지 못했다 (구조화 공시 데이터 부재).",
      "claim_type": "unknown",
      "module": "business",
      "evidence_ids": [],
      "counter_evidence_ids": [],
      "confidence": "low",
      "validation": "pending"
    }
  ]
}
```
`claim_id` 는 `CLM-0001` 형식(4자리)이다. `confidence` 는 `high` / `medium` / `low` 문자열이다.

## 4. Gate 4 가 자동으로 잡아내는 것

- 근거 없는 주장 (`unknown` 제외) → **실패**
- claim_type 별 최소 근거 수 미달 → **실패**
- 존재하지 않는 evidence ID 참조 (dangling) → **실패**
- 목표주가·적정주가·컨센서스가 부정문 없이 등장 → **실패**
- "매수"·"매도" 표현 (순매수/순매도 제외) → **실패**
- `data_completeness < 0.5` 인데 결론이 「판단 유보」가 아님 → **실패**
- 면책 문구 없음 → **실패**
- 인과 표현인데 `causal_path` 없음 → 경고
- `counter_evidence_ids` 가 전부 비어 있음 → 경고

**하나라도 실패하면 최종 보고서를 생성하지 않는다.** 검증 실패 보고서를 대신 만든다.

## 5. 값이 충돌할 때 — 조용히 하나를 고르지 않는다

가장 흔한 사례: **자체 계산 Trailing PER(DART 재무 기반) vs KRX 공표 PER(pykrx 경유)**

- 두 값은 **다를 수밖에 없다.** KRX 공표치는 **최근 확정 재무제표 기준**이라 분기 갱신이 지연된다.
- 처리: **둘 다 제시하고, 차이의 이유를 밝힌다.** 유리한 쪽을 고르지 않는다.
- 채점에 쓰는 것은 **자체 계산 Trailing PER**(VAL-01)이다. KRX 공표치는 교차검증·역사적 밴드 용도다.
- KRX 공표치를 못 받았다면(자격증명 없음) 그 사실을 쓰고, **없는 값을 추정하지 않는다.**

권장 문장:
> PER 은 12.4배다 (출처: 자체 계산 — DART 연결 재무 TTM 순이익 ÷ 시가총액, 기준일 2026-07-10, [rcept_no 20250514000123](https://dart.fss.or.kr/dsaf001/main.do?rcpNo=20250514000123)).
> KRX 공표 PER 은 14.1배로 다르다 (출처: pykrx(비공식 래퍼), 기준일 2026-07-10). 공표치는 최근 확정 재무제표를 쓰므로 최신 분기가 반영되지 않는다. 본 보고서의 채점은 자체 계산값을 사용한다.

같은 원칙이 **자체 지표 vs DART `fnlttSinglIndx.json` 지표**에도 적용된다 — 불일치는 `counter_evidence` 로 병기한다.

## 6. 합성 순서

1. `manifest.json` 을 읽어 종합점수·등급·게이트 상태·데이터 한계를 파악한다.
2. 모듈별 `module-result.json` 에서 `verdict`·`strengths`·`weaknesses`·`counter_evidence`·`unknowns` 를 가져온다.
3. 서술에 **인용할 숫자만** evidence ID 로 지목해 꺼낸다.
4. 각 핵심 문장을 claim 으로 등록하고 `{ticker}_claims.json` 을 쓴다.
5. 보고서 HTML 을 쓴다. 문체·구조는 [report-style.md](./report-style.md).
6. `python scripts/validate_report.py {ticker} --claims ... --html ...` 로 Gate 3·4 를 통과시킨다.
7. 실패하면 **보고서를 고치는 게 아니라 주장을 삭제하거나 근거를 N/A 로 되돌린다.**

> 검증을 통과시키려고 문구를 우회하지 않는다. Gate 는 방해물이 아니라 정직성의 최소선이다.
