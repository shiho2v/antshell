# moat — 경쟁우위 분석 (judged)

## 1. 목적
이 모듈은 **"이 회사의 초과수익을 경쟁으로부터 지켜주는 구조가 실제로 존재하는가, 그리고 그것이
재무로 발현되고 있는가"** 에 답한다. 성장 속도(growth)나 이익의 질(quality) 자체가 아니라,
**그 이익이 왜 지속될 수 있는가**를 묻는다.

> **이 모듈은 환각 위험이 가장 높다.** 해자 서술은 사전 학습 지식으로 그럴듯하게 지어내기 쉽다.
> **근거가 없으면 해자는 없는 것이 아니라 "확인되지 않은 것"(N/A)이다.**

## 2. 읽을 파일
| 파일 | 용도 |
|------|------|
| `data/evidence/{ticker}_evidence.json` | `packs.moat` 의 evidence item **만** |
| `data/raw/{ticker}_business_section.txt` | `B-FILING-001` 이 pack 에 있을 때**만** |
| `data/normalized/{ticker}_metrics.json` | `operating_margin_ttm`, `roe_ttm` (MOA-05 의 hint_metrics) |
| `modules/moat/rubric.md` | 등급 정의 |

원시 API JSON·전체 재무제표는 읽지 않는다.

## 3. 분석 절차
1. **근거 가용성부터 확인한다.** `packs.moat` 에 `B-FILING-001` 이 있는가?
   - **없으면** — 기술·원가·전환비용·특허에 대한 서술 근거가 **전혀 없다.**
     MOA-01~04 는 전부 **N/A** 다. MOA-05 만 재무 지표로 판단 가능하다.
     이 경우를 억지로 메우지 말고 그대로 제출한다.
   - **있으면** — 원문(`data/raw/{ticker}_business_section.txt`)을 정독한다.
2. **원문에서 해자의 흔적을 찾는다** (원문 문구를 그대로 인용할 수 있는 것만):
   - **기술·품질 우위**: 공정 난이도, 수율, 품질 인증, 규격 승인, 신뢰성 시험 통과 서술
   - **인증 장벽**: 자동차·의료·항공 등 고객 승인 절차, 인증 취득 기간 서술
   - **원가우위·규모의 경제**: 생산능력 규모, 수직계열화, 내재화, 원재료 조달 구조
   - **전환비용**: 고객 설계 단계 참여(design-in), 장기공급계약, 인증된 부품 교체 난이도
   - **공급망 지위**: 소수 공급사 체제, 대체 불가 소재, 장기 계약
   - **특허·R&D**: 특허 보유 서술, 연구개발 조직·성과 (지출 **금액**은 구조화 API 없음 — 원문에만)
   - **브랜드·네트워크 효과**: 대개 제조업 사업보고서에는 없다. 없으면 **없다고 쓴다.**
3. **MOA-05(수익성 지속성)** — 해자의 **재무적 발현**을 본다.
   `operating_margin_ttm`, `roe_ttm` 을 인용한다. 마진과 ROE 가 높다는 것은 해자의 **결과**일 수
   있으나 **증거는 아니다.** 반드시 MOA-01~04 중 하나 이상의 정성 근거와 **함께** 제시한다
   (requires_evidence=2). 정성 근거 없이 마진만으로 해자를 주장하지 않는다.
   - **연도별 마진 추이(operating_margin_history)는 현재 계산되지 않는다.** 지속성을 시계열로
     입증할 수 없으면 그 한계를 rationale 에 명시하고 등급을 보수적으로 잡는다.
4. **distinct_evidence_types 확인** — MOA-01·02·03 은 근거 **2개 이상**이며 **서로 다른 종류**여야
   한다. evidence item 의 `evidence_type` (`filing_text` / `metric` / `statement` / `event`) 이
   달라야 한다. 같은 `B-FILING-001` 을 두 번 쓰는 것으로는 요건을 채울 수 없다.
   서로 다른 타입의 근거를 2개 모을 수 없으면 **그 criterion 은 N/A** 다.
5. rubric.md 에 맞춰 MOA-01~05 의 level 을 정하고 judgment 파일을 쓴다.

## 4. 판단 규칙 (여기가 이 모듈의 핵심이다)
- **시장점유율·경쟁사 자동선정·경쟁사 대비 마진 비교는 UNSUPPORTED.**
  어떤 경로로도 조회되지 않으며 **절대 추정·생성하지 않는다.** "업계 1위", "과점 구조",
  "점유율 ○○%" 같은 문장은 근거가 없으면 **쓰지 않는다.**
- **고객사명은 원문에 명시된 경우에만** 인용한다. 추정 금지.
- **근거가 없으면 해자는 N/A 다. level 0 이 아니다.**
  level 0 은 "근거는 확보했으나 그 근거가 해자의 부재를 보여준다"는 뜻이다.
  "모르겠다"는 반드시 `level: null` + `na_reason` 이다.
- 사전 학습 지식("이 회사는 MLCC 세계 2위다" 등)으로 해자를 주장하지 않는다.
  아무리 유명한 사실이어도 evidence pack 에 없으면 **쓰지 않는다.**
- 높은 마진·ROE 만으로 MOA-01~04 를 채우지 않는다. 그건 MOA-05 의 재료다.
- 근거 요건(2개, 서로 다른 타입) 미충족 시 Python 이 자동으로 N/A 처리한다.
  요건을 채우려고 관련 없는 evidence 를 끼워 넣지 않는다.

## 5. 출력
`data/module-results/{ticker}_moat_judgment.json`

```json
{
  "module": "moat",
  "criteria": [
    {"criterion_id": "MOA-01", "level": 2,
     "evidence_ids": ["B-FILING-001", "Q-OPERATINGM-001"],
     "rationale": "원문의 인증·품질 서술 + 마진 발현. 서로 다른 evidence_type 2개."},
    {"criterion_id": "MOA-02", "level": null, "evidence_ids": [],
     "na_reason": "원가우위·규모의 경제를 뒷받침할 서로 다른 종류의 근거 2개를 확보하지 못했다. 추정하지 않는다."},
    {"criterion_id": "MOA-03", "level": null, "evidence_ids": ["B-FILING-001"],
     "na_reason": "전환비용 관련 근거가 1개뿐 — distinct 근거 2개 요건 미충족"},
    {"criterion_id": "MOA-04", "level": 1, "evidence_ids": ["B-FILING-001"], "rationale": "..."},
    {"criterion_id": "MOA-05", "level": 2,
     "evidence_ids": ["Q-OPERATINGM-001", "Q-ROETTM-001"], "rationale": "..."}
  ],
  "strengths": [{"point": "...", "evidence_ids": ["B-FILING-001"]}],
  "weaknesses": [{"point": "...", "evidence_ids": ["Q-OPERATINGM-001"]}],
  "counter_evidence": [{"point": "고마진이 사이클 호황의 결과일 수 있다", "evidence_ids": ["Q-OPERATINGM-001"]}],
  "unknowns": ["시장점유율 — UNSUPPORTED", "경쟁사 대비 마진 — 비교 데이터 없음",
               "연도별 마진 추이 — 미계산으로 지속성 시계열 입증 불가"],
  "invalidating_conditions": ["경쟁사 신규 증설로 영업이익률이 2개 분기 연속 하락하면 해자 판단은 무효다"],
  "verdict": "500단어 이내. 매수/매도 표현 금지."
}
```

- `criteria` 는 MOA-01~05 **5개 전부** 포함한다 (N/A 도 항목은 남긴다).
- MOA-01·02·03: `evidence_ids` **2개 이상 + 서로 다른 evidence_type**.
  MOA-04: 1개 이상. MOA-05: 2개 이상.
- strengths/weaknesses 각 **최대 5개**, 항목마다 `evidence_ids` **1개 이상 필수**.
- evidence_id 는 pack 에 실재하는 것만. **지어내면 채점에서 탈락한다.**

## 6. 금지 사항
- 시장점유율·순위·경쟁사 목록·경쟁사 마진 생성 (**UNSUPPORTED**).
- 사전 학습 지식으로 해자 주장.
- 근거 없는 항목에 level 0 부여 (반드시 level=null + na_reason).
- 마진·ROE 만으로 기술우위·전환비용을 주장하는 것.
- 같은 evidence 를 중복 나열해 distinct 요건을 형식적으로 채우는 것.
- 점수·가중합 직접 계산, 매수/매도 표현.
