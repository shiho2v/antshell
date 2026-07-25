---
title: "{{TITLE}}"
ticker: "{{TICKER}}"
company: "{{COMPANY_NAME}}"
market: "{{MARKET}}"
as_of: "{{DATA_CUTOFF}}"
analysis_mode: "{{ANALYSIS_MODE}}"
composite_score: {{COMPOSITE_SCORE}}
verdict: "{{VERDICT}}"
confidence: {{CONFIDENCE}}
data_completeness: {{DATA_COMPLETENESS}}
source_manifest: "{{MANIFEST_PATH}}"
claim_count: {{CLAIM_COUNT}}
tags: [{{TAGS}}]
status: "draft"
---

# {{TITLE}}

## 1. 한 줄 요약

{{ONE_LINE_SUMMARY}}<!-- {{CLAIM_ID}} -->

종합점수는 {{COMPOSITE_SCORE}}점, 결론은 **{{VERDICT}}**이다.<!-- MANIFEST -->
판단 신뢰도 {{CONFIDENCE_PCT}}%, 데이터 완전성 {{DATA_COMPLETENESS_PCT}}% 기준이며,<!-- MANIFEST -->
분석 관점은 {{ANALYSIS_MODE_LABEL}}이다.
{{RENORMALIZED_NOTE}}

## 2. 이 회사는 무엇으로 돈을 버는가

{{BUSINESS_PARAGRAPHS}}

## 3. 숫자로 보는 현재

| 지표 | 값 | 기준 | 근거 |
|---|---|---|---|
| {{METRIC_NAME}} | {{METRIC_VALUE}} | {{METRIC_BASIS}} | [공시]({{DART_URL}})<!-- {{CLAIM_ID}} --> |

> 표의 수치는 전부 공시·시세에서 가져오거나 그 값으로 직접 계산한 것이다.
> 산출하지 못한 항목은 아래처럼 사유와 함께 남긴다.

- {{NA_ITEM}} — 산출하지 못했다. {{NA_REASON}}<!-- {{CLAIM_ID}} -->

## 4. 투자 포인트 3

### 4-1. {{POINT_TITLE}}

{{POINT_BODY}}<!-- {{CLAIM_ID}} -->

### 4-2. {{POINT_TITLE}}

{{POINT_BODY}}<!-- {{CLAIM_ID}} -->

### 4-3. {{POINT_TITLE}}

{{POINT_BODY}}<!-- {{CLAIM_ID}} -->

## 5. 리스크 3

### 5-1. {{RISK_TITLE}}

{{RISK_BODY}}<!-- {{CLAIM_ID}} -->

### 5-2. {{RISK_TITLE}}

{{RISK_BODY}}<!-- {{CLAIM_ID}} -->

### 5-3. {{RISK_TITLE}}

{{RISK_BODY}}<!-- {{CLAIM_ID}} -->

#### CANSLIM 체크리스트 (trend 모듈을 실행했다면 필수)

| 항목 | 무엇을 보는가 | 지표 | 값 | 등급 |
|---|---|---|---|---|
| **C** | 최근 분기 실적 | {{METRIC}} | {{VALUE}} | {{LEVEL}}<!-- MOD:trend/TRD-C --> |
| **A** | 연간 이익 성장 | {{METRIC}} | {{VALUE_OR_NA}} | {{LEVEL_OR_NA}}<!-- MOD:trend/TRD-A --> |
| **N** | 신고가 근접도 | {{METRIC}} | {{VALUE}} | {{LEVEL}}<!-- MOD:trend/TRD-N --> |
| **S** | 수급(거래량 급증) | {{METRIC}} | {{VALUE}} | {{LEVEL}}<!-- MOD:trend/TRD-S --> |
| **L** | 주도주 여부 | {{METRIC}} | {{VALUE}} | {{LEVEL}}<!-- MOD:trend/TRD-L --> |
| **I** | 기관·외국인 순매수 | {{METRIC}} | {{VALUE}} | {{LEVEL}}<!-- MOD:trend/TRD-I --> |
| **M** | 시장 방향 | {{METRIC}} | {{VALUE}} | {{LEVEL}}<!-- MOD:trend/TRD-M --> |

{{HOW_TO_READ}}

N/A 항목은 **0점이 아니라 미채점**으로 쓰고 사유를 함께 적는다.

## 6. 이 분석에 대한 반론

위 결론과 어긋나는 근거를 숨기지 않고 남긴다.

- **{{OBJECTION_TARGET}}에 대하여** — {{OBJECTION_BODY}}<!-- {{CLAIM_ID}} -->

{{NO_OBJECTION_NOTE}}

## 7. 확인하지 못한 것

공식 데이터 출처가 없어 이 글에서 다루지 않은 항목이다. 추정으로 대체하지 않았다.

- {{UNKNOWN_ITEM}}<!-- {{CLAIM_ID}} -->
- {{UNSUPPORTED_ITEM}}

## 8. 출처·기준일·면책

### 출처

| 제공처 | 종류 | 엔드포인트 | 기준일 |
|---|---|---|---|
| {{PROVIDER}} | {{SOURCE_TYPE}} | {{ENDPOINT}} | {{RETRIEVED_AT}} |

### 데이터 한계

- {{DATA_LIMITATION}}

### 검증

이 글의 바탕이 된 보고서는 종목 식별·데이터·분석·보고서 4개 검증 게이트를 통과했다.
본문의 문장은 {{CLAIM_COUNT}}개의 근거 항목에 각각 연결되어 있다.

### 면책

> 본 글은 공개된 공시·시세 데이터를 기계적으로 집계·채점한 **교육용 기록**이며, **투자 자문이 아닙니다.**
> 특정 종목의 매매를 권유하지 않으며, 목표주가·투자의견을 제시하지 않습니다.
> 데이터는 기준일 시점의 것이며 이후 변경될 수 있습니다. 투자 판단과 그 결과의 책임은 투자자 본인에게 있습니다.
