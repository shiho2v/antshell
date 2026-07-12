# business — 사업구조 분석 (judged)

## 1. 목적
이 모듈은 **"이 회사는 무엇을 팔아 어떻게 돈을 버는가, 그리고 그 구조가 얼마나 취약한가"**
하나만 답한다. 성장률·수익성·밸류에이션은 다른 모듈의 몫이다. 여기서는 다루지 않는다.

산출물은 5개 criterion(BUS-01~05)의 **서수 등급(0~3)과 근거 ID**다.
점수 계산은 `score_modules.py` 가 한다. **Claude 는 산술하지 않는다.**

## 2. 읽을 파일 (이 목록 밖은 읽지 않는다)
| 파일 | 용도 |
|------|------|
| `data/evidence/{ticker}_evidence.json` | `packs.business` 에 나열된 evidence item **만** 본다 |
| `data/raw/{ticker}_business_section.txt` | `B-FILING-001` 이 evidence pack 에 있을 때**만** 읽는다 |
| `modules/business/rubric.md` | 등급 정의 |

- **원시 API 응답(`data/raw/*_dart_*.json`)과 전체 재무제표는 읽지 않는다.** (progressive disclosure)
- evidence_id 는 **evidence pack 에 실재하는 것만** 인용한다. ID를 지어내면 채점에서 탈락한다.
- 참고 지표가 필요하면 `data/normalized/{ticker}_metrics.json` 의 값을 **읽기만** 한다.
  이 모듈에서 유용한 키: `capex_to_ocf`, `net_debt_to_equity`, `operating_margin_ttm`
  (자본집약도·고정비 구조의 방증. 단, 근거로 인용할 때는 evidence pack 의 해당 metric item ID 를 쓴다.)

## 3. 분석 절차
1. **evidence pack 로드** — `packs.business` 의 ID 목록을 확보한다. 여기에 `B-FILING-001` 이
   있는지 먼저 확인한다. 있으면 사업보고서 원문이 확보된 것이고, 없으면 아래 4번의 N/A 규칙이
   광범위하게 적용된다.
2. **기업 개요** — `B-PROFILE-001` 에서 법인명·업종코드·설립일·결산월·대표자를 확인한다.
   업종코드는 표준산업분류일 뿐 **사업부문 구성을 설명하지 않는다.** 업종코드로 사업을 추론하지 않는다.
3. **사업의 내용 정독** (`B-FILING-001` 이 있을 때만) — `data/raw/{ticker}_business_section.txt` 를
   읽고 다음을 **원문 문구 그대로** 뽑는다. 표 구조가 손실됐을 수 있으니 애매하면 인용하지 않는다.
   - 사업부문 구분과 각 부문의 사업 내용
   - 주요 제품·서비스와 그 용도·전방 산업
   - 부문별·제품별 매출 비중 (원문에 표로 있는 경우)
   - 지역별 매출 비중, 주요 고객 관련 서술 (있는 경우)
   - 원재료 종류·주요 매입처·가격 변동 서술
   - 생산능력·생산실적·가동률
   - 주요 종속회사와 연결 대상 범위
4. **매출구조 해석** — 무엇이 얼마를 벌고, 어떤 요인(단가/물량/환율/전방수요)에 반응하는지
   원문 서술로 설명 가능한지 판단한다. 설명 가능하면 BUS-02 등급이 올라간다.
5. **집중도 위험(BUS-03) 평가** — 제품·고객·지역 중 하나라도 편중이 **원문으로 확인되면**
   위험이 크다는 뜻이고, 이 criterion 은 **inverse** 이므로 **등급이 낮아진다**
   (등급이 높을수록 집중도 위험이 낮다). 편중 여부를 확인할 수 없으면 N/A 다.
6. **자본집약도(BUS-04)** — 생산능력·설비·가동률 서술 + `capex_to_ocf`, `net_debt_to_equity`
   지표를 함께 본다. 가동률이 실적에 미치는 레버리지(고정비 구조)를 서술한다.
7. **실적 변동성의 원천(BUS-05)** — 이 회사의 실적을 흔드는 것이 무엇인지(전방 사이클, 원재료가,
   환율, 고객사 재고조정, 단일 대형 프로젝트 등) 원문 근거로 특정한다. **일반론을 쓰지 않는다.**
8. rubric.md 의 등급 정의에 맞춰 5개 criterion 의 level 을 정하고 judgment 파일을 쓴다.

## 4. 판단 규칙 (데이터가 없을 때)
- **`--with-document` 없이 수집된 경우** (= evidence pack 에 `B-FILING-001` 이 없음):
  사업부문별 매출, 생산능력·가동률, 원재료, 수주잔고, R&D 지출은 **구조화된 DART API 가 존재하지
  않는다.** 이 항목들은 전부 **N/A** 다. 추론하지 않는다.
  이 경우 BUS-02·BUS-03·BUS-04 는 대개 N/A 가 되고, BUS-01 만 `B-PROFILE-001` 로 최소 판단이 가능하다.
- **시장점유율, 경쟁사 목록, 컨센서스, 목표주가는 UNSUPPORTED** 다. 어떤 경로로도 추정하거나
  생성하지 않는다. 필요하면 `unknowns` 에 적는다.
- **N/A ≠ 0점.** 데이터가 없어서 판단 못 하는 것을 "나쁘다"로 바꾸지 않는다.
  level=null + na_reason 으로 남기면 Python 이 분자·분모에서 제외한다.
- 사전 학습 지식("이 회사는 MLCC 강자다" 같은 것)으로 근거를 보충하지 않는다.
- 근거가 1개 미만이면 그 criterion 은 채점되지 않는다 (BUS 전 항목 requires_evidence=1).

## 5. 출력
`data/module-results/{ticker}_business_judgment.json` 에 **정확히** 아래 형태로 쓴다.

```json
{
  "module": "business",
  "criteria": [
    {"criterion_id": "BUS-01", "level": 2,
     "evidence_ids": ["B-PROFILE-001", "B-FILING-001"],
     "rationale": "원문 근거에 기반한 1~3문장. 수치를 새로 계산하지 않는다."},
    {"criterion_id": "BUS-02", "level": 1, "evidence_ids": ["B-FILING-001"], "rationale": "..."},
    {"criterion_id": "BUS-03", "level": null, "evidence_ids": [],
     "na_reason": "사업보고서 원문 미확보 — 제품·고객·지역 편중을 확인할 근거가 없다. 추정하지 않는다."},
    {"criterion_id": "BUS-04", "level": 2, "evidence_ids": ["B-FILING-001", "Q-CAPEXTOOC-001"], "rationale": "..."},
    {"criterion_id": "BUS-05", "level": 2, "evidence_ids": ["B-FILING-001"], "rationale": "..."}
  ],
  "strengths": [{"point": "...", "evidence_ids": ["B-FILING-001"]}],
  "weaknesses": [{"point": "...", "evidence_ids": ["B-FILING-001"]}],
  "counter_evidence": [{"point": "결론과 상충하는 근거", "evidence_ids": ["..."]}],
  "unknowns": ["부문별 매출 비중 — 구조화 API 없음", "시장점유율 — UNSUPPORTED"],
  "invalidating_conditions": ["주력 부문의 전방 수요가 2개 분기 연속 역성장하면 이 판단은 무효다"],
  "verdict": "500단어 이내 서술. 매수/매도 표현 금지."
}
```

- `criteria` 는 BUS-01~05 **5개 전부** 포함한다 (N/A 도 항목은 남긴다).
- `strengths`/`weaknesses` 는 각각 **최대 5개**, 항목마다 `evidence_ids` **1개 이상 필수**.
- `evidence_ids` 는 실제 pack 에 있는 ID 만. 위 예시의 `Q-CAPEXTOOC-001` 같은 ID도
  **pack 에서 확인한 뒤** 쓴다 (metric 필드로 매칭한다).

## 6. 금지 사항
- 점수·백분율·가중합을 직접 계산하는 것 (Python 의 일이다).
- 사업부문별 매출·가동률·수주잔고를 원문 없이 "추정"하거나 업계 통념으로 채우는 것.
- 시장점유율·경쟁사·컨센서스·목표주가 생성.
- 근거 없는 항목에 level 0 부여 (반드시 level=null + na_reason).
- 매수/매도/비중확대 같은 투자 권유 표현.
