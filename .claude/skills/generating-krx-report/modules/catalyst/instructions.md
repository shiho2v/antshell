# catalyst — 촉매 모듈 지침

> 이 파일은 **catalyst 모듈이 실행될 때만** 읽는다. 미리 읽지 않는다.

## 1. 목적

향후 실적·주가에 영향을 줄 수 있는 **구체적인 사건(촉매)** 을, 그것이 실제로 존재한다는
**공시 근거(rcept_no)** 와 함께 등재하고, 각 촉매가 어떤 경로로 재무제표에 나타나는지를 서술한다.

4개 criterion(CAT-01~04)은 전부 `type: judged` 다.
→ **Claude 가 등급(0~3)과 evidence_ids 를 제출한다. 산술은 하지 않는다.**

**핵심 원칙: 공시 근거 없는 촉매는 등재 자체가 금지된다.** 촉매가 없으면 "촉매 없음"이 정답이다.
없는 촉매를 만들어내는 것이 이 모듈에서 가장 흔하고 가장 치명적인 실패다.

## 2. 읽을 파일

| 파일 | 용도 |
|------|------|
| `data/raw/{ticker}_dart_events.json` → `catalyst_candidates` | **유일한 촉매 원천** |
| `data/evidence/{ticker}_evidence.json` | `packs.catalyst` — `C-EVENT-001…` 이벤트 evidence |
| `data/normalized/{ticker}_metrics.json` | 재무적 연결 경로 서술용 (매출·이익·capex 규모 비교) |
| `data/{ticker}_analysis_contract.json` | `news_allowed`(기본 false), prohibited_inferences |
| `modules/catalyst/rubric.md` | 4개 항목 등급 정의 |

`catalyst_candidates` 는 공시 **제목 키워드**로 태깅된 목록이다:
신규수주 / 설비투자 / 자사주 / 지배구조 / 자본변동 / 손익 / 배당.
**이 태그는 후보(candidate)일 뿐 확정된 촉매가 아니다.** 제목만으로 규모·시점을 단정하지 않는다.

## 3. 분석 절차

1. `catalyst_candidates` 를 훑고, 각 후보가 **실제로 실적에 영향을 줄 사건인지** 판별한다.
   정기보고서 제출, 단순 정정공시 등은 촉매가 아니다.
2. 촉매로 채택한 사건마다 아래 6요소를 **모두** 채운다. 하나라도 못 채우면 등재하지 않는다.

   | 요소 | 설명 |
   |------|------|
   | 사건 | 무슨 일이 일어났는가 / 일어날 것인가 (공시 제목에 근거) |
   | 예상 시점 | 언제 실적에 반영되는가. **공시에 없으면 "시점 미공시"** — 추정 금지 |
   | 재무적 연결 경로 | 매출 → 영업이익 → 현금흐름 중 어디에, 어떤 순서로 나타나는가 |
   | 확인 지표 | 무엇을 보면 촉매가 작동했는지 알 수 있는가 (분기 매출, 가동률 공시 등) |
   | **공시 근거(rcept_no)** | **필수.** evidence_id(`C-EVENT-00N`) + rcept_no + 접수일 |
   | 주가 선반영 가능성 | 이미 가격에 반영되었을 여지 (`pct_from_52w_high`, 거래량과 함께) |

3. 규모를 인용할 때는 공시 제목·본문에 명시된 값만 쓴다. **수주금액을 추정하지 않는다.**
   금액이 확인되지 않으면 "규모 미확인"으로 적고, 재무적 연결 경로는 방향만 서술한다.
4. 선반영 판단(CAT-04)은 **inverse** 다. 이미 크게 반영되었을수록 **낮은 등급**이다.
5. 촉매가 하나도 없으면: CAT-01 을 낮은 등급(0)으로 두거나, 판단 근거조차 없으면 N/A 로 두고,
   CAT-02~04 는 N/A + na_reason("등재된 촉매 없음")으로 처리한다. **없는 촉매를 만들지 않는다.**

## 4. 판단 규칙

- **뉴스로 촉매를 만들지 않는다.** 계약의 `news_allowed` 는 기본 `false` 다.
  뉴스가 허용된 경우에도 뉴스는 보조 맥락일 뿐이며, **CAT-01 의 등급 근거가 될 수 없다**
  (CAT-01 은 "공시로 확인된" 촉매의 존재를 묻는다).
- **기억·사전 학습 지식으로 촉매를 만들지 않는다.** ("이 회사는 곧 신제품을 낸다" 등)
- **N/A ≠ 0점.** 촉매를 확인할 데이터가 없는 것과 촉매가 없는 것은 다르다.
  전자는 `level: null` + na_reason, 후자(공시를 다 봤는데 촉매성 사건이 없음)는 `level: 0`.
- 컨센서스·Forward EPS·목표주가·시장점유율: 존재하지 않는 데이터다. 촉매의 효과를
  **주가 상승폭이나 EPS 증가폭으로 수치화하지 않는다.**
- 모든 산술 금지. 촉매의 매출 기여도를 계산하지 않는다 — 경로와 방향만 서술한다.
- 공시 제목 태그는 후보 분류일 뿐이다 — "신규수주 태그가 있으므로 수주 증가"로 비약하지 않는다.

## 5. 출력

`data/module-results/{ticker}_catalyst_judgment.json`

```json
{
  "module": "catalyst",
  "ticker": "009150",
  "criteria": [
    {"criterion_id": "CAT-01", "level": 2, "evidence_ids": ["C-EVENT-001", "C-EVENT-003"],
     "rationale": "사건/예상시점/재무적 연결 경로/확인 지표/rcept_no/선반영 가능성을 담은 서술",
     "na_reason": null},
    {"criterion_id": "CAT-03", "level": null, "evidence_ids": [],
     "rationale": null, "na_reason": "공시에 시점이 명시되지 않았다 — 추정하지 않는다"}
  ],
  "strengths": [{"point": "…", "evidence_ids": ["C-EVENT-001"]}],
  "weaknesses": [{"point": "…", "evidence_ids": ["…"]}],
  "counter_evidence": [{"point": "촉매 공시 이후 주가가 이미 52주 고점 근접", "evidence_ids": ["…"]}],
  "unknowns": ["수주 금액 미공시 — 매출 기여 규모 확인 불가"],
  "invalidating_conditions": ["설비투자 공시가 철회되거나 가동 시점이 1년 이상 지연"],
  "verdict": "500단어 이내"
}
```

- CAT-01~04 **4개 항목 모두** `criteria` 에 등장해야 한다 (N/A 라도 na_reason 과 함께).
- strengths/weaknesses 각 5개 이내, 항목마다 evidence_ids 1개 이상.
- verdict 500단어 이내, 매수/매도 표현 금지.

## 6. 금지 사항

1. **공시 근거(rcept_no) 없는 촉매 등재** — 가장 심각한 위반.
2. 뉴스·기억·업계 상식 기반 촉매 생성.
3. 공시에 없는 시점·금액 추정 ("하반기 양산 예상", "약 500억 규모로 추정").
4. 촉매 효과의 수치화 (EPS 증가율, 목표주가, 상승 여력).
5. 데이터 부족을 0점으로 처리 (→ N/A + na_reason).
6. CAT-04 를 정방향으로 채점 (선반영이 클수록 높은 등급) — **inverse 다**.
7. 모든 직접 산술.
