---
id: SPEC-CHART-001
title: "주가 차트와 기술지표 모듈 — 진행 기록"
version: "0.1.0"
status: in-progress
created: 2026-09-12
updated: 2026-09-13
tier: M
---

# SPEC-CHART-001 진행 기록

## 마일스톤 현황

| 마일스톤 | 상태 | 산출물 |
|---|---|---|
| M1 수집 스크립트 + 데이터 | 완료 | `scripts/fetch_ohlcv.py`, `data/{4}_ohlcv.json` |
| M2 지표 계산 모듈 (TDD) | 완료 | `backend/app/indicators.py` |
| M3 백엔드 엔드포인트 | 완료 | `main.py` 131~216행 |
| M4 차트 컴포넌트 | 완료 | `frontend/src/components/StockChart.tsx` |
| M5 대시보드 연동 | 완료 | `dashboard/page.tsx` 4개소 |
| M6 품질 게이트 | 완료 | 본 문서 |

## 품질 게이트

### 테스트

```
$ python -m pytest backend/tests scripts/tests -q
52 passed in 0.79s

  20 - backend/tests/test_chart.py
  19 - backend/tests/test_indicators.py
  13 - scripts/tests/test_fetch_ohlcv.py
```

### 커버리지 — 측정 범위 결정

`plan.md` A.4에서 M6로 미뤄둔 결정이다. 측정 결과 기준에 따라 판정이 갈린다.

| 범위 | stmts | miss | 커버리지 | 85% 게이트 |
|---|---:|---:|---:|---|
| **SPEC-CHART-001 신규 코드** | 122 | 0 | **100.0%** | **PASS** |
| 기존 코드 (`main.py` 1~130행) | 65 | 39 | 40.0% | — |
| 전체 `backend/app` | 187 | 39 | 79.0% | FAIL |

**결정: 신규 코드 기준으로 판정한다 (100%, PASS).**

근거 — 미커버 39줄이 전부 본 SPEC 범위 밖 코드임을 줄 단위로 확인했다.

```
미커버 구간   33-44    _get_env               (8주차 이전)
             61-95    save_report_to_notion  (8주차 이전)
            100-128   get_github_issues      (8주차 이전)

신규 섹션    131-216   SPEC-CHART-001         미커버 0줄
```

전체 기준을 적용하면 8주차 이전 라우트에 테스트를 붙여야 하는데, 이는 `spec.md` §5 "Out of Scope — `SPEC-API-001` 범위 구현"에 해당한다. 해당 라우트의 테스트는 `SPEC-API-001` 구현 시 함께 작성되어야 한다.

### 프론트엔드

```
$ npx tsc --noEmit     exit 0
$ npx next build       ✓ Compiled successfully   /dashboard 4 kB / First Load 159 kB
```

## 인수 기준 판정 (AC-001 ~ AC-016)

| AC | 판정 | 근거 |
|---|---|---|
| AC-001 | PASS | `test_sample_mode_writes_one_file_per_stock`, `test_sample_records_have_required_fields_and_are_sorted[4종목]` + 실데이터 242건×4 검증 |
| AC-002 | PASS | `test_fetch_failure_preserves_existing_file_and_exits_nonzero`, `test_partial_failure_writes_no_file_at_all` |
| AC-003 | PASS | `test_ohlcv_returns_records_for_allowed_code` + 실데이터 스모크 200/242건 |
| AC-004 | PASS | `test_forbidden_code_returns_404[2]`, `test_forbidden_code_never_touches_the_filesystem[2]`, `test_path_traversal_attempts_are_rejected[4]` |
| AC-005 | PASS | `test_allowed_code_without_data_file_returns_404[2]` |
| AC-006 | PASS | `test_chart_endpoints_make_no_network_calls[2]`, `test_chart_endpoints_do_not_write_data_files` |
| AC-007 | PASS | `test_indicators_response_has_all_expected_keys`, `test_indicator_series_match_record_count` |
| AC-008 | PASS | `test_indicators_module_imports_standard_library_only` (AST 검사), `test_requirements_txt_has_no_new_runtime_dependency` |
| AC-009 | PASS | `test_simple_moving_average_null_prefix_length[5/20/60]`, `test_relative_strength_index_null_prefix_length`, `test_indicators_null_prefix_follows_minimum_period` |
| AC-010 | PASS | 브라우저 실측 — 로그인 후 보유 종목 행 클릭 시 해당 종목 차트 표시 확인 (2026-09-13, 작성자 직접 확인) |
| AC-011 | PASS | 브라우저 실측 — SMA 5/20/60 3선 + 거래량 별도 pane 확인 (`.moai/reports/SPEC-CHART-001/chart-005930.jpg`) |
| AC-012 | PASS | `StockChart.tsx:11` 기본값 확인 + 런타임에서 `localhost:8000` 호출 성공 |
| AC-013 | PASS | 브라우저 실측 — 허용목록 밖 종목 선택 시 `요청 실패 (404)` 표시, 페이지 정상 동작 |
| AC-014 | PASS | 브라우저 실측 — `2025-09-15 ~ 2026-09-11 · 242거래일` 렌더링 확인 |
| AC-015 | PASS | 백엔드 3개 라우트는 `test_health_route_is_unchanged`, `test_existing_routes_are_still_registered`. 대시보드 UI(테이블·뉴스·이슈·Notion 버튼)는 브라우저 실측 — 아래 § Notion 버튼 원인 분리 참고 |
| AC-016 | PASS | `test_simple_moving_average_matches_hand_computed_values`, `test_exponential_moving_average_matches_hand_computed_values`, `test_relative_strength_index_matches_hand_computed_values` |

**집계: 16 PASS / 0 부분 / 0 미검증**

## AC-010 / AC-015 검증 기록 (2026-09-13)

초안 작성 시점에는 `/dashboard` 진입이 불가해 두 항목을 미검증으로 남겼으나, 환경 설정을 해소한 뒤 실측으로 판정했다.

### 환경 설정 해소 절차

Next.js는 `next`가 실행되는 디렉터리(`frontend/`)에서만 `.env*`를 찾고 상위로 올라가지 않는다. `docs/setup/ONBOARDING.md:63`은 루트 `.env`만 안내하므로, 문서대로 따라하면 Supabase 클라이언트 생성이 실패한다.

1. `frontend/.env.local` 생성 — 루트 `.env`의 `NEXT_PUBLIC_SUPABASE_URL`, `NEXT_PUBLIC_SUPABASE_ANON_KEY` 복사 (`.gitignore:5` 대상)
2. anon key 유효성 확인 — `GET {URL}/auth/v1/user` → `HTTP 403 invalid claim: missing sub claim` (키 유효, 세션만 없음. 키가 잘못되면 `Invalid API key`가 온다)
3. `backend/.env` 생성 — 아래 § Notion 버튼 원인 분리 참고
4. 백엔드 `uvicorn app.main:app --port 8000`, 프론트 `npm run dev`
5. `/signup` 계정 생성 후 로그인

`next.config.js`에서 `@next/env`의 `loadEnvConfig`로 루트 `.env`를 읽는 방법을 3회 시도했으나 모두 실패했다. `process.env`에는 로드되지만(`URL len=40`, `KEY len=46` 확인) `NEXT_PUBLIC_*`의 클라이언트 번들 인라인에는 반영되지 않았다. 팀원 파일이므로 원상복구했다.

### 판정

- **AC-010 PASS** — 보유 종목 행 클릭 시 해당 종목 캔들스틱 차트 표시, 선택 행 하이라이트 확인
- **AC-015 PASS** — 보유 종목 테이블 4행 · 최신 뉴스 3건 · GitHub 이슈 목록 정상. "Notion 저장" 버튼은 아래 참고

## Notion 버튼 원인 분리 (AC-015)

브라우저 실측에서 "Notion 저장" 버튼만 동작하지 않았다. 본 SPEC이 해당 버튼에 `e.stopPropagation()`을 추가했으므로 회귀 여부를 먼저 가렸다.

**결론: 본 SPEC의 변경과 무관한 기존 결함이다.**

근거 3가지:

1. 프론트엔드를 거치지 않은 직접 호출도 실패
   ```
   curl -X POST http://localhost:8000/api/report/notion
   → HTTP 503 {"detail":"Notion 환경변수 미설정"}
   ```
2. `git diff backend/app/main.py` 의 변경 범위는 `@@ -14,0 +15,3 @@`(import)와 `@@ -125,0 +129,88 @@`(신규 차트 섹션)뿐 — `_get_env`(32~45행)와 `save_report_to_notion`(59~96행)은 미수정
3. 버튼 핸들러는 `stopPropagation()` 후 `saveToNotion(s)`를 정상 호출 — 차트 선택만 차단하고 저장 경로는 그대로

### 원인과 임시 조치

`main.py:35`의 `open(".env")`가 **실행 디렉터리 기준 상대경로**다. 백엔드는 `backend/`에서 실행되므로(`ONBOARDING.md:157`) 루트 `.env`가 아니라 없는 `backend/.env`를 찾아 빈 문자열을 반환했다.

`backend/.env`를 생성해 해소했고(`.gitignore:4` 대상), 재확인 결과 `HTTP 200 {"ok":true}`. `_get_env`가 요청 시마다 파일을 읽으므로 서버 재시작은 불필요했다.

## 발견한 기존 결함 — 환경변수 경로 해석 (본 SPEC 범위 밖)

`backend/.env` 생성은 임시 조치이며 근본 원인은 남아 있다. 4가지 이유:

1. **CWD 의존** — 실측 결과: `backend/`에서 실행 → 찾음, 저장소 루트에서 실행 → 찾음, 그 외 디렉터리 → 빈 문자열(503). IDE·프로세스 매니저·Docker·CI 등 실행 위치가 달라지면 다시 깨진다.
2. **`os.getenv` 호출은 미해결** — `main.py:23`(`ALLOWED_ORIGINS`), `auth.py:13`(`NEXT_PUBLIC_SUPABASE_URL`)은 `.env` 폴백이 없어 `backend/.env`로도 해결되지 않는다. 후자는 JWT 검증용이라 보호 엔드포인트 추가 시 드러난다.
3. **비밀값 3중화** — 루트 `.env` / `frontend/.env.local` / `backend/.env`. 이미 드리프트 발생 (anon key: `.env.local` 208자 정상 vs 루트 `.env` 46자 플레이스홀더).
4. **`python-dotenv==1.0.1`이 설치돼 있으나 미사용** — `_get_env`는 dotenv 기능을 14줄로 재구현한 것이다.

권장 수정 (본 SPEC에서는 미적용 — `plan.md` A.5 PRESERVE 대상):

```python
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent.parent / ".env")
```

`__file__` 기준이라 CWD와 무관하고, `os.environ`을 채우므로 위 2번도 함께 해결되며 `_get_env` 14줄을 삭제할 수 있다. 본 SPEC이 추가한 `DATA_DIR`(`main.py:139`)도 같은 `__file__` 기준 방식을 쓴다.

## 구현 중 발견·수정한 결함

| # | 내용 | 발견 경로 |
|---|---|---|
| 1 | `requirements.txt` 한글 주석이 pip cp949 디코딩 실패 유발 | `pip install` 실행 |
| 2 | Python 3.13 + `setuptools>=82` 조합에서 `pkg_resources` 부재로 pykrx import 실패 | 수집 스크립트 실행 |
| 3 | `--out-dir`이 프로젝트 루트 밖이면 `relative_to()` ValueError | 테스트 10개 실패 |
| 4 | RSI 주 계산식 경로가 테스트에서 한 번도 실행되지 않음 (상승만/평평 케이스가 조기 반환 분기만 탐) | 커버리지 97% 잔여 3줄 추적 |
| 5 | 차트 컨테이너가 `display:none` 상태에서 생성되어 `clientWidth=0` → 242개 캔들이 우측 5%에 압축 | 브라우저 실측 |

5번은 타입 검사·빌드로는 잡히지 않는 결함이었다. 브라우저 실측이 없었다면 발표 자료에 깨진 차트가 실렸을 것이다.

## 발표 시 언급할 사항

**RSI 평평 구간 관례** — `acceptance.md` 엣지 케이스에 따라 "평균 하락 = 0 → RSI 100"으로 구현했다. 이 규칙이 가격 변동이 전혀 없는 구간에도 적용되어, 평평한 시세에서 RSI가 과매수(100)로 표시된다. 중립인 50이 더 자연스럽지만 실제 시세에서는 거의 발생하지 않아 승인된 스펙을 유지했다. 테스트는 값을 고정하지 않고 `0 ≤ RSI ≤ 100` 범위만 검증한다.

**MOCK 데이터 병존** — 보유 종목 테이블은 `SPEC-API-001`이 미구현(`status: draft`)이라 여전히 하드코딩된 Mock 가격(삼성전자 74,500원)을 표시한다. 차트는 실제 시세(259,500원)를 그리므로 한 화면에서 두 값이 어긋난다. `spec.md` §5에서 의도적으로 Out of Scope 처리했다.

**환경변수 경로 결함** — 프론트엔드(`frontend/.env.local` 부재)와 백엔드(`_get_env`의 CWD 상대경로) 양쪽에서 같은 유형의 문제가 나왔다. 둘 다 "루트에 `.env` 하나만 두면 된다"는 가정이 깨진 사례다. SPEC 범위를 지키면서 기존 결함을 발견·기록한 예로 쓸 수 있다.

## 다음 단계

- `/moai sync` — 문서 동기화 + PR 생성 (미실행)
- 브랜치: `feature/09-어지수-chart-indicator`
