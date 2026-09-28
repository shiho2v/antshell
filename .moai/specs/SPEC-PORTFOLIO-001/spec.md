---
id: SPEC-PORTFOLIO-001
title: "포트폴리오 분석 모듈 (밸류에이션·리스크·리밸런싱 API + 화면)"
version: "0.1.1"
status: draft
created: 2026-09-20
updated: 2026-09-20
author: 정우준
priority: P1
phase: "v1.0.0"
module: "scripts, backend/app, frontend/src/app/portfolio"
lifecycle: spec-anchored
tags: "backend, frontend, portfolio, agent-team, fastapi, nextjs"
tier: M
---

## HISTORY

| 버전 | 날짜 | 작성자 | 변경 내용 |
|------|------|--------|-----------|
| 0.1.0 | 2026-09-20 | 정우준 | 최초 작성 — 포트폴리오 분석 모듈 SPEC 초안 (Tier M). 기존 `scripts/orchestrate_portfolio.py`가 병합 결과를 JSON으로 저장하지 않는다는 점을 실행으로 확인하고, 오프라인 생성 + 파일 서빙 구조를 채택. `SPEC-API-001`이 미구현(`status: draft`)이므로 `depends_on`을 선언하지 않고 독립 실행 가능하도록 범위를 조정. 실행 결과에서 risk와 allocation의 비중 계산 분모가 어긋나는 것을 확인하고 표시 기준을 allocation 하나로 확정 |
| 0.1.1 | 2026-09-20 | 정우준 | plan-auditor 1차 감사(FAIL, 0.69)의 blocking 6건 반영. **D1** — `--sample` 모드를 REQ-004·AC-004로 명문화(결정론성·허용 목록 검사·비덮어쓰기·에이전트 미호출). **D2** — §4에 「필수 키 집합」 술어를 한 곳에 정의하고, 스크립트 저장 전 검사(REQ-002·REQ-004)와 백엔드 읽기 시 검사(REQ-007)가 같은 정의를 참조하도록 통일. **D3** — REQ-012를 로그인 리다이렉트(Event-driven)와 대시보드 링크(REQ-013, Ubiquitous)로 분리해 GEARS 패턴 1:1 대응 복구. **D4** — `plan.md` CI 기술을 실제 8단계로 정정하고 `scripts/tests/`를 CI 테스트 단계에 포함하는 작업을 M4 산출물로 추가. **D5** — 화면 AC의 수동 검증 절차를 M3 산출물로 승격하고 AC별 검증 수단을 명시, 프론트엔드 테스트 프레임워크 도입은 §5 제외 범위로 명시. **D6** — REQ-001의 임시 파일 교체 저장을 AC-002가 실제로 행사하도록 보강. Tier M 예산(REQ 16·AC 16)을 지키기 위해 성공 응답 계약(구 REQ-004 + 구 REQ-008)을 REQ-005로, 구 AC-004 + 구 AC-016을 AC-005로, 구 AC-005 + 구 AC-006을 AC-006으로 병합 |

---

## 1. 개요 (Overview)

본 SPEC은 4주차 실습으로 만들어 둔 **포트폴리오 분석 에이전트 팀**의 결과를 웹에서 볼 수 있게 만든다. 밸류에이션·리스크·리밸런싱 세 축의 분석 결과를 백엔드가 서빙하고, 전용 화면 `/portfolio`가 이를 표시한다.

### 1.0 선행 SPEC과의 관계

8주차 `SPEC-API-001`(백엔드 API ↔ 대시보드 실데이터 연동)은 현재 `status: draft`이며 **구현되지 않았다** — `backend/app/main.py`에 `/api/stocks` 목록 라우트가 없고, `frontend/src/app/dashboard/page.tsx`는 여전히 `MOCK_STOCKS` 하드코딩 배열을 사용한다.

따라서 본 SPEC은 `depends_on`을 선언하지 않고 **독립적으로 실행 가능**하도록 범위를 잡는다. 신규 라우트 `GET /api/portfolio`는 `SPEC-API-001`의 `/api/stocks/...` 및 `SPEC-CHART-001`이 추가한 `/api/stocks/{code}/ohlcv`·`/api/stocks/{code}/indicators`와 경로가 겹치지 않는다. 대시보드의 `MOCK_STOCKS`를 실데이터로 교체하는 작업은 `SPEC-API-001`의 몫이며 본 SPEC에서 대신 수행하지 않는다(§5).

9주차 `SPEC-CHART-001`이 확립한 **"요청 경로에서 데이터 수집을 트리거하지 않는다"** 원칙과 **허용 목록 검사를 파일 접근보다 먼저 수행한다**는 구현 패턴을 그대로 계승한다.

### 1.1 확인된 현재 상태와 데이터 공백

작업 착수 전 저장소를 조사하고 스크립트를 실제로 1회 실행한 결과, **분석 결과를 담은 영속 파일이 존재하지 않는다.**

- `scripts/orchestrate_portfolio.py`는 병합 JSON을 **표준 출력에 출력만** 한다. `--save` 옵션은 `outputs/portfolio_report_YYYY-MM-DD.html` 한 개만 기록하며, **JSON을 저장하지 않는다.**
- 따라서 백엔드가 읽을 수 있는 분석 결과 파일이 없다. 웹에서 표시하려면 JSON 저장 경로가 먼저 필요하다.
- 스크립트는 `claude -p`를 `subprocess`로 호출하고 240초 타임아웃을 둔다. 이 호출을 요청 경로에 두면 응답 지연과 Claude 사용량 소모가 요청 수에 비례한다(§1.2).

### 1.2 설계 결정 — 생성·서빙·표시의 책임 분리

| 계층 | 책임 |
|------|------|
| 생성 (오프라인) | `scripts/orchestrate_portfolio.py`를 사람이 직접 실행한다. `claude -p`로 3개 서브에이전트(`portfolio-valuation`·`portfolio-risk`·`portfolio-allocation`)를 병렬 호출하고, 병합 결과를 `data/portfolio_analysis.json`에 저장한다. 저장소에 커밋한다. 실행할 수 없는 환경에서는 에이전트를 호출하지 않는 결정론적 `--sample` 모드로 같은 스키마의 파일을 만든다(REQ-004) |
| 서빙 | 백엔드는 커밋된 파일만 읽어 응답한다. `claude` 실행·`subprocess`·외부 네트워크 호출·`data/` 쓰기를 하지 않는다 |
| 표시 | 프론트엔드 `/portfolio`가 종목별 밸류에이션 판정·리스크 등급·리밸런싱 액션을 표시하고, 데이터가 스냅샷임을 함께 알린다 |

생성이 오프라인인 이유는 §1.1의 두 번째·세 번째 항목이다. 대안 비교와 기각 근거는 `plan.md` §A.2에 있다.

### 1.3 종목 범위

`SPEC-CHART-001`과 동일하게 4개 종목(`005930` 삼성전자, `000660` SK하이닉스, `009150` 삼성전기, `008490` 서흥)으로 한정한다. 이 4개는 `data/{code}_market.json`·`data/{code}_fundamentals.json`이 이미 존재하는 종목과 일치하며, 서브에이전트가 읽는 입력이 바로 그 파일들이다. 보유 종목 입력 파일에 이 목록 밖의 코드가 섞이면 분석을 시작하지 않고 거부한다(REQ-003). 이 거부 규칙은 `--sample` 모드에도 똑같이 적용된다(REQ-004).

보유 종목 입력은 저장소에 고정된 `data/portfolio.example.json` 한 개다. 사용자별 보유 종목 입력은 범위 밖이다(§5).

### 1.4 비중 정의 불일치와 해소

2026-09-20 실행 결과에서 **같은 종목의 비중이 두 값으로 나왔다.**

| 종목 | `risk`의 `actual_weight_pct` | `allocation`의 `actual_weight_pct` |
|------|------|------|
| SK하이닉스 (`000660`) | 47.8 | 44.54 |

원인은 분모가 다르기 때문이다. `risk`는 보유 종목 평가금액 합계를 분모로 쓰고, `allocation`은 현금 5,000,000원을 포함한 총자산을 분모로 쓴다. 둘 다 틀린 값은 아니지만, 한 화면에 함께 두면 사용자는 어느 쪽이 맞는지 알 수 없다.

**결정: 화면에는 `allocation`의 비중 하나만 표시한다.** 목표 비중(`target_weight_pct`)과 드리프트(`drift_pct`)가 모두 총자산 기준으로 계산되므로, 같은 분모를 쓰는 `allocation` 쪽이 리밸런싱 판단과 일관된다. `risk`의 비중 필드는 API 응답 계약에서 제외한다(REQ-005, §4).

## 2. 요구사항 (GEARS)

### 오프라인 생성 — 스크립트

**REQ-001** [Ubiquitous] 오케스트레이터 스크립트는 `--save-json <경로>` 옵션(기본 대상 `data/portfolio_analysis.json`)을 제공하며, 병합된 분석 결과에 `schema_version`·`source`·`generated_date`(스크립트 실행일)·`portfolio_file`(입력 보유 종목 파일 경로) 4개 메타 필드와 병합 결과가 이미 갖고 있는 `as_of`(보유 종목 파일의 기준일)를 함께 담아 저장한다. 저장은 대상과 같은 디렉터리의 임시 파일에 먼저 기록한 뒤 교체하는 방식으로 수행하며, 교체 이전 단계에서 중단되면 대상 파일의 바이트가 그대로 보존되고 임시 파일도 남지 않는다.

**REQ-002** [Event-driven] **When** 저장 전 검증 실패가 감지되면 — 서브에이전트 실행 실패, 응답을 스키마대로 파싱하지 못함, 병합 결과가 §4 「필수 키 집합」을 만족하지 못함 가운데 하나 — 스크립트는 `--save-json` 대상 파일을 덮어쓰지 않고 0이 아닌 종료 코드로 종료한다.

**REQ-003** [Event-driven] **When** 입력 보유 종목 파일의 `holdings`에 §1.3의 4개 허용 목록 밖 종목 코드가 하나라도 포함되어 있으면, 스크립트는 서브에이전트를 호출하기 전에 해당 코드를 명시한 오류 메시지와 함께 0이 아닌 종료 코드로 종료하며, 부분 결과 파일을 생성하지 않는다.

**REQ-004** [Event-driven] **When** `--sample` 옵션으로 실행하면, 스크립트는 `claude` 실행과 서브에이전트 호출을 한 번도 하지 않고 입력 보유 종목 파일만을 읽어 고정된 결정론적 규칙으로 §4 「필수 키 집합」을 만족하는 분석 결과를 만들고 `source`를 `"sample"`로 기록해 저장한다. 같은 입력 파일과 같은 실행일로 두 번 실행하면 저장된 바이트가 동일하다. 생성 규칙은 보유 종목 가운데 최소 한 종목에 대해 `verdict`·`overall`·`action`이 모두 `unknown`이 아닌 값을, 최소 한 종목에 대해 `unknown`을 만든다. 이 모드에도 REQ-003의 허용 목록 검사, REQ-001의 임시 파일 교체 저장, REQ-002의 비덮어쓰기 규칙이 그대로 적용된다.

### 백엔드 — 분석 결과 서빙

**REQ-005** [Event-driven] **When** 클라이언트가 `GET /api/portfolio`를 요청하고 `data/portfolio_analysis.json`이 존재하며 §4 「필수 키 집합」을 만족하면, 백엔드는 `200`과 함께 메타데이터(`meta`)·밸류에이션(`valuation`)·리스크(`risk`)·리밸런싱(`allocation`) 네 블록을 응답하되, 응답에 실리는 실제 비중 필드는 현금을 포함한 총자산을 분모로 하는 `allocation.results[].actual_weight_pct` 하나뿐이며 `risk.results[]`의 `actual_weight_pct`는 응답 계약에서 제외한다(§1.4).

**REQ-006** [Event-driven] **When** `data/portfolio_analysis.json`이 존재하지 않으면, 백엔드는 `404`를 반환한다.

**REQ-007** [Event-driven] **When** 분석 결과 파일이 JSON으로 파싱되지 않거나 §4 「필수 키 집합」을 만족하지 못하면, 백엔드는 `500`과 함께 일반화된 메시지만 반환하며 파일 시스템 경로·예외 문자열·스택 트레이스를 응답 본문에 포함하지 않는다.

**REQ-008** [Unwanted] 백엔드는 이 SPEC의 어떤 엔드포인트 호출로도 `claude` 실행·`subprocess` 생성·외부 네트워크 호출을 하지 않으며 `data/` 아래에 파일을 쓰지 않는다.

### 프론트엔드 — 포트폴리오 화면

**REQ-009** [Event-driven] **When** 사용자가 `/portfolio`에 진입하면, 프론트엔드는 보유 종목별로 밸류에이션 판정(`verdict`)과 점수(`score`), 리스크 종합 등급(`overall`), 리밸런싱 액션(`action`)·드리프트(`drift_pct`)·리밸런싱 금액(`rebalance_amount`)을 표시한다.

**REQ-010** [State-driven] **While** 화면이 분석 결과를 표시하는 동안, 프론트엔드는 보유 종목 기준일(`as_of`)과 분석 생성일(`generated_date`)을 함께 표시하고 이 데이터가 실시간 시세가 아닌 스냅샷임을 문구로 알리며, `source`가 `"sample"`인 경우 실제 에이전트 분석 결과가 아님을 구분해 표기한다.

**REQ-011** [Event-driven] **When** 분석 결과 요청이 실패(네트워크 오류, 4xx, 5xx)하면, 프론트엔드는 해당 영역에만 오류 상태를 표시하고 화면의 나머지 영역 렌더링을 중단하지 않는다.

**REQ-012** [Event-driven] **When** 인증되지 않은 사용자가 `/portfolio`에 접근하면, 프론트엔드는 대시보드와 동일하게 `/login`으로 이동시킨다.

**REQ-013** [Ubiquitous] 대시보드는 `/portfolio`로 이동하는 링크를 제공한다.

**REQ-014** [Where] 프론트엔드는 기존 대시보드와 동일하게 `NEXT_PUBLIC_API_URL` 환경 변수(설정 시) 또는 기본값 `http://localhost:8000`을 사용하여 신규 엔드포인트를 호출한다.

**REQ-015** [Unwanted] 프론트엔드는 판정·액션·등급 값이 `unknown`이거나 비어 있는 종목을 목록에서 숨기거나 정상 판정과 같은 모양으로 표시하지 않는다. 해당 항목은 "판정 불가"로 명시된 별도 상태로 렌더링한다.

### 기존 기능 호환성

**REQ-016** [Ubiquitous] 기존 라우트(`GET /health`, `GET·PUT·DELETE /api/settings/notion`, `POST /api/report/notion`, `GET /api/github/issues`, `GET /api/stocks/{code}/ohlcv`, `GET /api/stocks/{code}/indicators`)의 동작과 대시보드의 기존 영역(보유 종목 테이블, 주가 차트, 최신 뉴스, GitHub 이슈, Notion 저장 버튼)은 변경되지 않는다.

## 3. 인수 기준 (Acceptance Criteria)

인수 기준은 `.moai/specs/SPEC-PORTFOLIO-001/acceptance.md` 참고 (Tier M). REQ-001~REQ-016 전체가 AC-001~AC-016으로 커버된다. AC별 검증 수단(자동 테스트 / 문서화된 수동 절차)은 같은 문서의 「검증 수단」 표에 있다.

## 4. 데이터 계약 (구현 아님)

### `data/portfolio_analysis.json`

```
{
  "schema_version": "1",
  "source": "agent-team" | "sample",
  "generated_date": "YYYY-MM-DD",      // 스크립트 실행일
  "portfolio_file": "data/portfolio.example.json",
  "portfolio_name": str,
  "as_of": "YYYY-MM-DD",               // 보유 종목 파일의 기준일 (실행일과 다를 수 있음)
  "valuation": {
    "agent": str,
    "results": [
      { "stock_code": str, "name": str,
        "revenue_growth_pct": number | null, "op_income_growth_pct": number | null,
        "verdict": "저평가" | "적정" | "주의" | "고평가" | "unknown",
        "score": int, "basis": str }
    ]
  },
  "risk": {
    "agent": str,
    "total_market_value": number,
    "results": [
      { "stock_code": str, "name": str, "market_value": number,
        "actual_weight_pct": number,            // 분모 = 보유 종목 합계. 응답에서는 제외
        "concentration": str, "drawdown_from_52w": str,
        "supply_flow": str, "volume_state": str,
        "risk_score": number,
        "overall": "low" | "medium" | "high" | "unknown" }
    ]
  },
  "allocation": {
    "agent": str,
    "total_asset": number,
    "cash": number,
    "results": [
      { "stock_code": str, "name": str, "current_price": number, "market_value": number,
        "actual_weight_pct": number,            // 분모 = 현금 포함 총자산. 화면 표시 기준
        "target_weight_pct": number, "drift_pct": number,
        "action": "매수" | "매도" | "유지" | "unknown",
        "rebalance_amount": number }
    ]
  }
}
```

- `schema_version`·`source`·`generated_date`·`portfolio_file` 4개는 `--save-json` 저장 단계에서 덧붙인다. 나머지는 서브에이전트 병합 결과를 그대로 보존한다.
- `as_of`와 `generated_date`는 **다른 값이다.** 2026-09-20 실행에서 `as_of`는 `"2026-07-25"`였다. 두 값을 모두 저장하고 화면에 함께 표시하는 이유가 이것이다(REQ-010).
- `verdict`·`overall`·`action`은 `unknown`을 가질 수 있다. 실행 결과에서 서흥(`008490`)의 `volume_state`가 `"stale"`로 나온 사례가 있으므로 판정 불가 상태는 예외가 아니라 정상 경로로 취급한다(REQ-015).

### 필수 키 집합 (REQ-002 · REQ-004 · REQ-007 공통 술어)

분석 결과 파일이 "스키마를 만족한다"는 말의 뜻을 여기 한 곳에서만 정의한다. 스크립트의 저장 전 검사(REQ-002, REQ-004)와 백엔드의 읽기 시 검사(REQ-007)는 이 정의를 그대로 쓴다. 두 계층이 서로 다른 집합을 구현하면 저장은 통과하는데 서빙이 500을 내는(또는 그 반대의) 비대칭이 생기고, M1과 M2가 병렬로 진행되므로 구현 중에 그 어긋남을 맞출 기회가 없다.

아래 다섯 조건을 모두 만족할 때에만 필수 키 집합을 만족한다.

1. **최상위 키 9개가 모두 존재한다** — `schema_version`, `source`, `generated_date`, `portfolio_file`, `portfolio_name`, `as_of`, `valuation`, `risk`, `allocation`.
2. **`valuation`·`risk`·`allocation`은 각각 객체이고, 그 안의 `results`는 리스트다.**
3. **숫자여야 하는 값** — `risk.total_market_value`, `allocation.total_asset`, `allocation.cash`.
4. **세 `results` 리스트의 길이가 서로 같다.**
5. **각 `results` 원소의 최소 키** — `valuation.results[]`는 `stock_code`·`verdict`·`score`, `risk.results[]`는 `stock_code`·`overall`, `allocation.results[]`는 `stock_code`·`actual_weight_pct`·`action`·`drift_pct`·`rebalance_amount`.

다섯 조건 가운데 하나라도 어긋나면 스키마 위반이다. 이 집합에 열거되지 않은 키가 더 있거나 없는 것은 위반이 아니며, 값의 범위나 enum 적합성(예: `verdict`가 다섯 값 중 하나인지)도 이 술어의 판정 대상이 아니다 — 판정 불가 값은 정상 경로이기 때문이다(REQ-015).

응답 스키마의 `meta` 5개 필드는 위 최상위 키에서 파생한다. 파일에는 `meta`라는 키가 없으므로 그 부재는 위반이 아니다.

### `GET /api/portfolio` 응답

```
{
  "meta": {
    "schema_version": str, "source": str,
    "portfolio_name": str, "as_of": "YYYY-MM-DD", "generated_date": "YYYY-MM-DD"
  },
  "valuation":  { "results": [ ...파일과 동일... ] },
  "risk":       { "total_market_value": number,
                  "results": [ ...파일과 동일, 단 actual_weight_pct 제외... ] },
  "allocation": { "total_asset": number, "cash": number,
                  "results": [ ...파일과 동일... ] }
}
```

**비중 정의 (REQ-005).** 응답에 실리는 실제 비중은 `allocation.results[].actual_weight_pct` 하나다. 분모는 현금을 포함한 총자산(`allocation.total_asset`)이다. `risk.results[]`의 동명 필드는 분모가 달라 같은 종목에서 다른 값이 나오므로(§1.4) 응답에서 제거한다. 화면은 응답에 있는 값만 표시하므로 두 값이 한 화면에 공존할 수 없다.

### 기존 파일과의 관계

- `data/portfolio.example.json`: 보유 종목 입력. 스크립트가 읽고, 백엔드는 읽지 않는다.
- `data/{code}_market.json`·`data/{code}_fundamentals.json`: 서브에이전트의 입력. 백엔드는 읽지 않는다.
- `data/{code}_ohlcv.json`: `SPEC-CHART-001`의 자산. 본 SPEC은 읽지도 쓰지도 않는다.
- `outputs/portfolio_report_*.html`: 기존 `--save` 산출물. 본 SPEC은 이 동작을 변경하지 않는다.

## 5. 제외 범위 (Out of Scope)

### Out of Scope — 사용자별 보유 종목 입력
- 로그인 사용자별 보유 종목 등록·수정 화면, Supabase 보유 종목 테이블, 보유 종목 업로드. 입력은 저장소에 고정된 `data/portfolio.example.json` 한 개다.

### Out of Scope — 뉴스 모듈
- 뉴스 수집·요약·감성 분석 및 대시보드의 `MOCK_NEWS` 교체. 별도 SPEC(`SPEC-NEWS-001`)의 범위다.

### Out of Scope — `SPEC-API-001` 범위 구현
- `GET /api/stocks` 목록 엔드포인트 신설, 대시보드 `MOCK_STOCKS` 제거, 보유 종목 테이블 실데이터 연동. `SPEC-API-001`이 담당하며 본 SPEC이 대신 구현하지 않는다.

### Out of Scope — 실시간 데이터
- 실시간/스트리밍 시세, WebSocket 갱신, 폴링 기반 자동 새로고침. 본 SPEC은 사전 생성된 스냅샷만 표시한다.

### Out of Scope — 자동 재분석 스케줄링
- cron·GitHub Actions·백그라운드 잡을 통한 분석 자동 재실행, 분석 결과 만료 감지 후 자동 갱신. 재실행은 사람이 스크립트를 직접 실행하는 수동 절차다.

### Out of Scope — 요청 경로의 LLM 호출
- 요청 처리 중 `claude` 실행, 서브에이전트 호출, 임의 LLM API 호출, 결과 캐시 워밍. 생성은 오프라인 스크립트의 책임이다(REQ-008).

### Out of Scope — 분석 로직 변경
- 서브에이전트(`portfolio-valuation`·`portfolio-risk`·`portfolio-allocation`)의 프롬프트·판정 기준·점수 산식 수정. 본 SPEC은 기존 에이전트의 출력을 저장·서빙·표시만 한다. `--sample`의 고정 규칙(REQ-004)은 에이전트 판정을 흉내 내는 대체 분석이 아니라 스키마를 채우는 자리끼움이며, 실제 판정 품질을 주장하지 않는다.

### Out of Scope — 프론트엔드 테스트 프레임워크 도입
- jest·vitest·`@testing-library` 등 컴포넌트 테스트 인프라 신설과 그에 따른 `frontend/package.json` 의존성 추가. 현재 저장소에는 프론트엔드 테스트 프레임워크가 없으며, 화면 요구사항(REQ-009~REQ-015)은 `docs/weekly/WEEK_10.md`에 기록하는 **문서화된 수동 검증 절차**와 기존 자동 게이트(`npm run lint`, `npm run build`, `npx tsc --noEmit`)로 판정한다. 대응 관계는 `acceptance.md` 「검증 수단」 표에 있다.

### Out of Scope — 신규 엔드포인트 인증
- `GET /api/portfolio`에 대한 인증·인가 적용. 기존 무인증 라우트(`/api/github/issues`, `/api/stocks/...`)와 동일하게 유지한다. 화면 접근 제어(REQ-012)는 프론트엔드 라우팅 수준의 기존 동작을 따르는 것이며 API 인증과는 별개다.
