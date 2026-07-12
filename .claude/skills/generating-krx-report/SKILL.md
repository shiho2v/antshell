---
name: generating-krx-report
description: 한국 상장기업(KRX)을 8개 모듈(사업·품질·성장·해자·밸류에이션·추세/CANSLIM·위험·촉매)로 종합 평가해 근거 검증된 HTML 투자분석 보고서를 만든다. 종목명 또는 6자리 티커와 함께 "종합 기업분석", "투자 보고서", "종목 분석", "CANSLIM 채점", "밸류에이션", "업데이트 보고서" 같은 분석·리포트·채점 의도가 있을 때 발동한다 (예: "삼성전기 종합 분석해줘", "009150 CANSLIM 채점", "SK하이닉스 밸류에이션"). DART 공시·재무 + KRX 시세를 실제 조회하고, 계산은 Python이, 해석만 Claude가 하며, 4개 검증 게이트를 통과해야 보고서를 생성한다. 다음은 발동하지 않는다: 회사 소개만 묻는 질문, 지수 조회, DART·pykrx API 사용법 문의, 종목과 무관한 프로그래밍 질문. 기본 예시 종목은 삼성전기(009150).
allowed-tools: Read, Write, Bash
---

# KRX 기업 종합평가 보고서

**교육·연구용.** 산출물은 투자 자문이 아니다. 매수·매도 의견을 내지 않는다.

> `allowed-tools` 는 권한 프롬프트를 줄이는 **사전승인**일 뿐 도구를 제한하지 않는다 (공식 사양).

## 절대 규칙 (위반 시 중단)

1. **Claude 는 산술하지 않는다.** 성장률·CAGR·멀티플·점수·총점은 전부 Python 이 계산한다.
   보고서의 모든 수치는 `metrics.json` / `module-result.json` 에서 **그대로 인용**한다.
2. **N/A ≠ 0.** 데이터 조회 실패·자격증명 부재를 0점으로 채점하지 않는다.
   데이터가 부족하면 점수를 깎지 말고 **confidence 와 evidence_coverage 를 낮춘다**.
3. **없는 데이터를 만들지 않는다.** 목표주가·컨센서스·Forward EPS·시장점유율·경쟁사 임의 선정은
   **공식 데이터 출처가 존재하지 않으므로 금지**다 (`config/source-priority.yaml` 의 `unsupported`).
4. **외부 지식으로 수치를 보완하지 않는다.** 기억·뉴스로 공시 데이터를 메우지 않는다.
5. 스크립트가 에러로 종료하면 **보고서를 만들지 말고** 에러를 사용자에게 그대로 전달한다.

## 실행 전제

```bash
pip install requests pykrx jsonschema PyYAML     # Python 3.10+
```

- `DART_API_KEY` — **필수** (재무·공시 일체)
- `KRX_ID`, `KRX_PW` — 선택. **없으면** 수급(CANSLIM I)·지수(M)·상대강도(L)·역사적 밴드가 **N/A** 가 된다.
  (시세 OHLCV 는 pykrx→Naver 경유로 자격증명 없이 동작하나 **비공식 경로**다.)

아래 `SKILL` 은 이 스킬 디렉터리다. Bash 에서 `${CLAUDE_SKILL_DIR}` 로 참조한다.

## 워크플로 (7단계)

### 1. 종목 식별 (Gate 1)

- 6자리 티커를 받으면 그대로 사용. 종목명만 받으면 **추측하지 말고** 후보를 제시한 뒤 확인받는다.
- 아무 종목도 없으면 예시 `009150`(삼성전기)로 진행하되 **예시임을 명시**한다.

```bash
python "${CLAUDE_SKILL_DIR}/scripts/resolve_security.py" {TICKER}
# 이름 검색:  --name 삼성전기   (후보만 제시. 자동 확정하지 않는다)
```

**Gate 1 실패 시 분석을 중단한다.**

### 2. 분석 계약 생성

요청 유형을 분류한다 → `comprehensive` | `canslim` | `valuation` | `update`
분석 관점을 정한다 → `balanced`(기본) | `growth` | `value` | `long-term` | `momentum`

```bash
python "${CLAUDE_SKILL_DIR}/scripts/build_analysis_contract.py" {TICKER} \
    --mode balanced --request-type comprehensive
```

사용자가 명시하지 않은 것은 **임의로 채우지 않는다**. 기본값 적용은 `assumptions` 에,
결과에 중대한 영향을 주는데 기본값이 없으면 `unresolved_items` 에 기록된다.
투자기간을 지정하지 않으면 **장기/단기로 임의 해석하지 않는다**.

계약의 `unresolved_items` 가 중대하면 사용자에게 먼저 묻는다.

### 3. 모듈 선택

계약이 `required_modules`(정식 채점) 와 `optional_modules`(요약 인용)를 결정한다.

| 요청 | 정식 채점 | 요약 인용 |
|---|---|---|
| 종합 기업분석 | business, quality, growth, moat, valuation, trend, risk, catalyst | — |
| CANSLIM 분석 | growth, trend | business, risk |
| 밸류에이션 | quality, valuation | business, growth, risk |
| 업데이트 | 변경 감지된 모듈만 | 나머지 |

CANSLIM 의 C·A 는 growth 지표를 재사용하므로 **growth 는 의존성으로 항상 실행**된다.

### 4. 데이터 수집 → 정규화 → 계산

```bash
S="${CLAUDE_SKILL_DIR}/scripts"
python "$S/fetch_dart_profile.py"    {TICKER}   # + --with-document 로 사업보고서 원문 추출
python "$S/fetch_dart_financials.py" {TICKER}
python "$S/fetch_dart_events.py"     {TICKER}
python "$S/fetch_krx_market.py"      {TICKER}
python "$S/normalize_data.py"        {TICKER}   # 누적 → 분기단독 차분
python "$S/calculate_metrics.py"     {TICKER}   # 모든 산술의 단일 지점
```

- **사업부문별 매출·생산능력·가동률·원재료·수주잔고는 구조화 API 가 없다.**
  `--with-document` 를 써야 사업보고서 원문 텍스트로만 확인 가능하며, 쓰지 않으면 **N/A** 다.
  business/moat 를 정식 채점한다면 `--with-document` 를 권장한다.

### 5. Evidence Pack 생성 및 검증 (Gate 2)

```bash
python "$S/build_evidence_packs.py" {TICKER}
python "$S/validate_evidence.py"    {TICKER}
```

**Gate 2 실패 시 보고서를 만들지 않는다.**

### 6. 모듈 분석 — 실행하는 모듈의 문서만 읽는다

**실행하지 않는 모듈의 instructions/rubric 을 읽지 않는다** (토큰 낭비).
원시 API JSON 과 전체 재무제표는 **읽지 않는다**. evidence pack 과 metrics 만 읽는다.

각 모듈마다:
1. `modules/{module}/instructions.md` 와 `rubric.md` 를 읽는다
2. `data/evidence/{TICKER}_evidence.json` 의 `packs.{module}` 에 해당하는 evidence 만 본다
3. `data/module-results/{TICKER}_{module}_judgment.json` 을 작성한다

- **정성 모듈**(business, moat, risk, catalyst): 기준별 **서수 등급(0~3) + evidence_ids** 만 제출.
  **점수를 계산하지 않는다.** 근거가 없으면 등급 대신 `level: null` + `na_reason`.
- **정량 모듈**(quality, growth, valuation, trend): 등급을 제출하지 **않는다**(`criteria: []`).
  Python 이 채점한다. Claude 는 해석 서술(verdict/strengths/weaknesses/counter_evidence)만 쓴다.

```bash
python "$S/score_modules.py" {TICKER}     # 모듈 점수 + 종합점수 (Python 전담)
```

### 7. 합성 → 검증 (Gate 3·4) → 저장

`references/synthesis-policy.md` 를 읽고 핵심 주장을 claim 으로 구조화한다
(`data/{TICKER}_claims.json`). 근거 없는 주장은 **보고서에서 제거**한다.

합성 단계에서 읽는 것은 **manifest·composite·module-result·필요한 evidence item 뿐**이다.

템플릿을 채워 저장한다:
- 종합 → `templates/full-report.html`
- CANSLIM·밸류에이션 → `templates/compact-report.html`
- 업데이트 → `templates/update-report.html`
- 저장 위치: `outputs/{TICKER}_report_{as_of}.html`

```bash
python "$S/validate_report.py" {TICKER} \
    --claims "data/{TICKER}_claims.json" \
    --html   "outputs/{TICKER}_report_{as_of}.html"
```

**한 게이트라도 실패하면 최종 보고서 대신 검증 실패 보고서를 생성한다.**

## 업데이트 보고서

이전 `data/{TICKER}_manifest.json` 이 있으면, 변경된 데이터만 다시 수집하고
**변경된 모듈만 재실행**한다. 나머지는 이전 `module-result.json` 을 재사용한다.

## 종합 의견 (매수·매도 표현 금지)

`긍정적 관찰` · `중립적 관찰` · `보수적 관찰` · `판단 유보` 중 하나만 쓴다.
데이터 완전성 50% 미만 또는 신뢰도 40% 미만이면 **점수와 무관하게 `판단 유보`** 로 강등된다.

## 참고 문서 (필요할 때만 읽기)

| 파일 | 언제 읽나 |
|---|---|
| `references/evidence-policy.md` | 근거·출처·N/A 처리 규칙 (데이터 다룰 때) |
| `references/scoring-policy.md` | 채점 방식·judgment 형식 (모듈 분석 전) |
| `references/synthesis-policy.md` | claim 구조화·상충 근거 (합성 전) |
| `references/report-style.md` | 보고서 20개 절 구조·문체 (작성 전) |
| `design-review.md` | 무엇이 왜 불가능한지 (데이터 한계를 설명할 때) |
| `config/source-priority.yaml` | 어떤 데이터가 어디서 오는지 / `unsupported` 목록 |

## 알려진 한계 (보고서에 반드시 노출)

- 컨센서스·Forward EPS·목표주가: **무료 공식 API 가 존재하지 않는다.**
- 사업부문별 매출·가동률·원재료·수주잔고: 구조화 API 없음. 원문 텍스트로만.
- pykrx 는 **비공식** 래퍼다. 기본 OHLCV 는 Naver 경유.
- 시가총액 = 종가 × 발행주식수(DART) — **두 입력의 기준일이 다르다.**
- KRX 자격증명이 없으면 CANSLIM 의 L·I·M 이 N/A 가 된다.
