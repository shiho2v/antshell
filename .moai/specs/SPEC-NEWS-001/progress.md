---
id: SPEC-NEWS-001
title: "종목 뉴스 모듈 — 진행 기록"
version: "0.1.1"
status: in-progress
created: 2026-09-20
updated: 2026-09-22
tier: M
---

# SPEC-NEWS-001 진행 기록

## 마일스톤 현황

| 마일스톤 | 상태 | 산출물 | 커버 REQ | 커버 AC |
|---|---|---|---|---|
| M1 데이터 확보 + 백엔드 엔드포인트 | 완료(AC-001만 차단) | `backend/app/news.py`, `backend/app/main.py`(import 1줄 + 라우트 구간), `backend/tests/test_news.py`. `data/008490_agents.json`은 수집 실패로 미생성 — 「AC-001 예외 기록」 참고 | REQ-001~REQ-007 | AC-002~AC-007 PASS, AC-001 FAIL(차단됨) |
| M2 프론트엔드 뉴스 영역 + 수동 검증 절차 | 대기 | `frontend/src/components/StockNews.tsx`, `frontend/src/app/dashboard/page.tsx`(import 1줄 + `MOCK_NEWS` 삭제 + 뉴스 구간 교체), `docs/weekly/WEEK_10.md` 「대시보드 뉴스 영역 수동 검증 절차」 | REQ-008~REQ-014 | AC-008~AC-014 |
| M3 문서 동기화 + 품질 게이트 | 대기 | `docs/weekly/WEEK_10.md`(모듈 요약·재수집 절차), 본 문서 | REQ-015 | AC-015 |

세 마일스톤은 순차 진행한다(`plan.md` §A.3).

## 인수 기준 판정 기록 (M3에서 작성)

AC-001~AC-015의 PASS/FAIL 매트릭스를 M3에서 여기에 채운다. 기록 규칙은 두 가지다.

- **자동 판정 AC**(AC-002~AC-007, AC-013·AC-014의 자동분, AC-015의 백엔드 회귀분) — 실행한 명령과 그 출력을 그대로 적는다.
- **수동 판정 AC**(AC-001, AC-008~AC-012, AC-013·AC-014의 화면분, AC-015의 대시보드분) — `docs/weekly/WEEK_10.md` 「대시보드 뉴스 영역 수동 검증 절차」의 해당 PASS 조건을 인용하고 관찰한 결과를 적는다. 절차 문서 인용 없이 "확인함"이라고만 적은 항목은 PASS로 보지 않는다(`acceptance.md` 품질 게이트).

`data/008490_agents.json` 생성에 실패한 경우, AC-001은 `acceptance.md` 「AC-001 예외 조항」의 **세 조건을 모두 충족한 때에만** `FAIL(차단됨)`으로 기록하고 SPEC을 닫을 수 있다(`plan.md` §A.3 M1 운영 주의). 세 조건의 증거는 아래 「AC-001 예외 기록」 표에 적으며, 한 줄이라도 비어 있으면 예외가 성립하지 않으므로 SPEC을 닫지 않는다.

| AC | 판정 | 근거 |
|---|---|---|
| AC-001 ~ AC-015 | _<M3에서 기록>_ | _<M3에서 기록>_ |

### AC-001 예외 기록 (수집 실패 시에만 작성)

`data/008490_agents.json` 수집에 성공했다면 이 표는 비워 두고 AC-001을 PASS로 기록한다. 실패한 경우에만 아래 네 줄을 모두 채운다 — 세 조건 가운데 하나라도 비면 `FAIL(차단됨)`으로 닫을 수 없다(`acceptance.md` 「AC-001 예외 조항」).

| 조건 | 적을 내용 | 기록 |
|---|---|---|
| 조건 1 — 수집 시도 | 실행한 명령(`python scripts/orchestrate_stock_agents.py 008490 --save`)과 그 실패 출력을 그대로 | 실행: `python3 scripts/orchestrate_stock_agents.py 008490 --save` (2026-09-22, 워크트리 `news-001`). 종료 코드 1. 출력: `json.decoder.JSONDecodeError: Expecting value: line 1 column 1 (char 0)` — `run_orchestrator()`가 `envelope["result"]`를 다시 JSON으로 파싱하는 단계에서 실패했다(스크립트 64행). `claude -p --output-format json --allowedTools WebSearch,WebFetch` 서브프로세스 자체의 종료 코드는 확인했으나(0으로 반환되어 `subprocess.run`의 `returncode != 0` 분기는 타지 않았다), 그 결과 봉투(envelope)의 `result` 필드가 재파싱 가능한 JSON 문자열이 아니었다. `data/008490_agents.json`은 생성되지 않았다(`git status --short data/` 결과 없음). 재시도는 하지 않았다 — 외부 부작용 호출(REQ-001 자체가 유일한 부작용 호출)이라 근거 없는 반복 실행을 피했다. |
| 조건 2 — 파일 부재 동작 | AC-004(`404`)와 AC-010 (c) 오류 상태의 판정 — 둘 다 PASS여야 한다 | AC-004 PASS(M1) — `backend/tests/test_news.py::test_missing_file_for_allowed_code_returns_404`가 `008490`(허용 목록 안, 파일 없음)에 대해 `404`를 확인했다(아래 §E.2 E1 참고). AC-010 (c)는 M2/M3의 화면 수동 검증 절차 범위이며 여기서는 기록하지 않는다. |
| 조건 3 — 사유와 후속 | 실패 사유 / AC-001을 PASS로 바꾸기 위한 후속 조치 / `data/008490_agents.json`이 여전히 없다는 사실 | _<M3에서 기록>_ |
| 종합 | 세 조건이 모두 충족되었는가(예 / 아니오). "아니오"면 SPEC을 닫지 않는다 | _<M3에서 기록>_ |

## §E.1 Plan-phase Audit-Ready Signal

- plan_complete_at: 2026-09-22
- plan_status: audit-ready (plan-auditor iteration 2 verdict: PASS, `.moai/reports/plan-audit/SPEC-NEWS-001-review-2.md`)

## §E.2 Run-phase Evidence

M1 — 데이터 확보 + 백엔드 엔드포인트. 워크트리 `.claude/worktrees/news-001`, 브랜치 `feat/SPEC-NEWS-001`, 베이스 커밋 `f1ecff9`.

### E1 — AC-001~AC-007 PASS/FAIL 매트릭스

**명령**: `python3 -m pytest backend/tests/test_news.py -v`

**출력(발췌, 전체 21건 — 20 passed, 1 skipped)**:
```
test_news_response_sorting_url_and_passthrough_keys PASSED   # AC-002
test_news_response_empty_list_is_ok PASSED                   # AC-002 (빈 배열)
test_news_response_excludes_financials_ticker_name PASSED    # AC-003
test_missing_file_for_allowed_code_returns_404 PASSED        # AC-004
test_forbidden_code_returns_404_without_touching_filesystem PASSED  # AC-005
test_path_traversal_codes_are_rejected[...] PASSED (4건)     # AC-005
test_malformed_json_bytes_returns_500 PASSED                 # AC-006 (a)
test_missing_news_key_returns_500 PASSED                     # AC-006 (b)
test_news_not_a_list_returns_500 PASSED                      # AC-006 (c)
test_news_item_not_an_object_returns_500 PASSED              # AC-006 (d)
test_news_item_missing_summary_returns_500 PASSED            # AC-006 (e)
test_news_item_title_not_a_string_returns_500 PASSED         # AC-006 (f)
test_news_endpoint_makes_no_subprocess_or_network_calls PASSED  # AC-007
test_news_endpoint_does_not_write_to_data_dir PASSED          # AC-007
test_committed_agents_json_files_satisfy_valid_news_document[000660] PASSED
test_committed_agents_json_files_satisfy_valid_news_document[005930] PASSED
test_committed_agents_json_files_satisfy_valid_news_document[008490] SKIPPED  # 파일 미생성
test_committed_agents_json_files_satisfy_valid_news_document[009150] PASSED
20 passed, 1 skipped, 1 warning in 0.32s
```

| AC | 판정 | 근거 |
|---|---|---|
| AC-001 | **FAIL(차단됨)** | 「AC-001 예외 기록」참고 — 수집 실패, 예외 조항 조건 1·2 M1분 충족 |
| AC-002 | PASS | 정렬(B,A,C,D,E) · `url` B에만 · `extra` 통과 · 빈 배열 200 — 위 발췌 2건 |
| AC-003 | PASS | 최상위 2키, `financials`/`ticker`/`name` 직렬화 결과에 부재 |
| AC-004 | PASS | `008490`(허용+파일없음) → 404 |
| AC-005 | PASS | `005380`(허용목록 밖, 파일 실재) → 404 + `_read_news_document` 미호출(mock) + 경로조작 4종 |
| AC-006 | PASS | 「유효한 뉴스 문서」 네 조건 각각 1건 이상 — (a)~(f) 6건 전부 500, 절대경로·파일명·Traceback·예외클래스명 미노출 |
| AC-007 | PASS | subprocess.run·shutil.which·httpx.AsyncClient·urllib.request.urlopen 미호출 + `data/` 파일 목록 불변 |

### E2 — RED 증거 (TDD)

라우트 등록 전(`backend/app/news.py`만 존재, `main.py` 미수정) `python3 -m pytest backend/tests/test_news.py -v` 실행 결과, 10건 실패(발췌):

```
FAILED backend/tests/test_news.py::test_news_response_sorting_url_and_passthrough_keys
FAILED backend/tests/test_news.py::test_news_response_empty_list_is_ok
FAILED backend/tests/test_news.py::test_news_response_excludes_financials_ticker_name
FAILED backend/tests/test_news.py::test_malformed_json_bytes_returns_500
FAILED backend/tests/test_news.py::test_missing_news_key_returns_500
FAILED backend/tests/test_news.py::test_news_not_a_list_returns_500
FAILED backend/tests/test_news.py::test_news_item_not_an_object_returns_500
FAILED backend/tests/test_news.py::test_news_item_missing_summary_returns_500
FAILED backend/tests/test_news.py::test_news_item_title_not_a_string_returns_500
FAILED backend/tests/test_news.py::test_news_endpoint_makes_no_subprocess_or_network_calls
10 failed, 10 passed, 1 skipped, 1 warning in 0.43s
```
(라우트 미등록으로 전부 404를 받아 500/200 기대값과 불일치했다. `test_missing_file_for_allowed_code_returns_404` 등 애초에 404를 기대하는 테스트는 우연히 통과했으나 근거가 "미등록"이라 GREEN 이후 재확인함.)

### E3 — 범위 확인

**명령**: `git diff --stat f1ecff9` + `git status --short`

**출력**:
```
 backend/app/main.py | 25 ++++++++++++++++++++++++-
 1 file changed, 24 insertions(+), 1 deletion(-)

 M backend/app/main.py
?? backend/app/news.py
?? backend/tests/test_news.py
```
허용 파일(`backend/app/news.py`(신규) · `backend/app/main.py`(import 1줄 + 라우트 구간) · `backend/tests/test_news.py`(신규)) 외 변경 없음. `data/008490_agents.json`은 수집 실패로 생성되지 않았다(위 「AC-001 예외 기록」).

### E4 — 회귀 확인

**명령**: `python3 -m pytest backend/tests/ -v`

**출력(요약)**: `80 passed, 1 skipped, 1 warning in 0.49s` — 기존 `test_chart.py`(11건)·`test_indicators.py`(19건)·`test_notion_settings.py`(15건) 전부 PASS, 신규 `test_news.py` 20 PASS + 1 SKIPPED(008490 미생성). `ruff check backend/` → `All checks passed!`.

### E5 — 요청 경로 경계 grep

**명령**: `grep -n "subprocess\|httpx\|urllib.request" backend/app/news.py`

**출력**: (없음 — 매치 0건). `news.py`는 `json`·`datetime.date`·`pathlib.Path`·`fastapi.HTTPException`만 import한다.

### E6 — 블로커

없음. REQ-001 운영자 수동 단계(008490 수집)는 시도했으나 실패했고, 「AC-001 예외 기록」 표에 조건 1·2(M1분)를 기록했다. 엔드포인트·테스트는 예외 조항과 무관하게 완료했다.

## §E.3 Run-phase Audit-Ready Signal

- run_status: M1 complete (AC-002~AC-007 PASS, AC-001 FAIL(차단됨) — 예외 조항 진행 중, 조건 3·종합은 M3에서 기록)
- ac_pass_count: 6 (AC-002~AC-007)
- ac_fail_count: 1 (AC-001, 차단됨 — 예외 조항 미완결)
- preserve_list_post_run_count: 위반 0건 — `plan.md` §A.6 PRESERVE 목록 중 `backend/app/main.py` 기존 라우트 본문·차트 구간 미수정(추가만), `backend/requirements.txt`·`test_chart.py`·`test_indicators.py`·`test_notion_settings.py`·`conftest.py`·`.github/workflows/ci.yml`·`scripts/`·`data/` 기존 파일 전체 미변경
- new_warnings_or_lints_introduced: 0 (`ruff check backend/` → All checks passed)
- total_run_phase_files: 3 (`backend/app/news.py` 신규, `backend/app/main.py` 수정, `backend/tests/test_news.py` 신규)
- m1_commit_sha: pending-backfill-M1 (이 섹션을 쓰는 커밋이 자신의 SHA를 알 수 없으므로 다음 커밋에서 backfill)

## §E.4 Sync-phase Audit-Ready Signal

_<pending sync-phase>_
