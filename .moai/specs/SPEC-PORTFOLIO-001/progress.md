---
id: SPEC-PORTFOLIO-001
title: "포트폴리오 분석 모듈 — 진행 기록"
version: "0.1.1"
status: in-progress
created: 2026-09-20
updated: 2026-09-22
tier: M
---

# SPEC-PORTFOLIO-001 진행 기록

## 마일스톤 현황

| 마일스톤 | 상태 | 산출물 | 커버 |
|---|---|---|---|
| M1 스크립트 JSON 저장 + 샘플 모드 + 데이터 생성 | 완료 | `scripts/orchestrate_portfolio.py`, `scripts/tests/test_orchestrate_portfolio.py`, `data/portfolio_analysis.json`(`source: "sample"`) | REQ-001~REQ-004 / AC-001~AC-004 |
| M2 백엔드 엔드포인트 | 완료 | `backend/app/main.py`(`GET /api/portfolio`), `backend/tests/test_portfolio.py` | REQ-005~REQ-008 / AC-005~AC-008 |
| M3 프론트엔드 화면 + 대시보드 링크 + 수동 검증 절차 | 완료(코드) / 수동 절차 미실행 | `frontend/src/app/portfolio/page.tsx`, `frontend/src/app/dashboard/page.tsx`(링크 1줄), `docs/weekly/WEEK_10.md` 「`/portfolio` 화면 수동 검증 절차」 | REQ-009~REQ-015 / AC-009~AC-015 |
| M4 문서 동기화 + CI 테스트 경로 확장 + 품질 게이트 | 완료 | `docs/weekly/WEEK_10.md`, `.github/workflows/ci.yml`("Backend 테스트" 단계 확장), 본 문서 | REQ-016 / AC-016 |

## 인수 기준 판정 기록 (M4에서 작성)

AC-001~AC-016의 PASS/FAIL 매트릭스를 M4에서 여기에 채운다. 기록 규칙은 두 가지다.

- **자동 판정 AC**(AC-001~AC-008, AC-016의 백엔드 회귀분) — 실행한 명령과 그 출력을 그대로 적는다.
- **수동 판정 AC**(AC-009~AC-015, AC-016의 대시보드분) — `docs/weekly/WEEK_10.md` 「`/portfolio` 화면 수동 검증 절차」의 해당 PASS 조건을 인용하고, 관찰한 결과를 적는다. 절차 문서 인용 없이 "확인함"이라고만 적은 항목은 PASS로 보지 않는다(`acceptance.md` 품질 게이트).

`.github/workflows/ci.yml`의 테스트 단계를 `scripts/tests/`까지 확장하지 못한 경우, 그 사유와 AC-001~AC-004의 대체 검증 방법을 이 절에 함께 기록한다.

| AC | 판정 | 근거 |
|---|---|---|
| AC-001 | PASS | `test_save_json_writes_nine_top_level_keys_with_generated_date_and_as_of` — `pytest scripts/tests/test_orchestrate_portfolio.py -v` |
| AC-002 | PASS | `test_save_preserves_existing_file_on_subagent_failure`, `test_save_preserves_existing_file_when_replace_fails` |
| AC-003 | PASS | `test_allowlist_rejects_out_of_range_codes_before_calling_subagent` — 직접 재현: `data/portfolio.edge.json` 입력 시 exit 1, 파일 미생성 |
| AC-004 | PASS | `test_sample_mode_is_deterministic_and_never_touches_subprocess`, `test_sample_mode_still_rejects_out_of_allowlist_codes` — 직접 재현: `--sample` 2회 실행 바이트 동일(diff 없음) |
| AC-005 | PASS | `test_portfolio_returns_200_with_meta_and_three_blocks[agent-team/sample]` — `pytest backend/tests/test_portfolio.py -v`; 직접 재현: `GET /api/portfolio` 라이브 호출로 4블록 응답 확인 |
| AC-006 | PASS | `test_portfolio_missing_file_returns_404`, `test_portfolio_invalid_json_returns_500_without_leaking_details`, `test_portfolio_schema_violation_returns_500[...]` (3종) |
| AC-007 | PASS | `test_portfolio_endpoint_makes_no_subprocess_or_network_calls`, `test_portfolio_endpoint_does_not_write_to_data_dir` |
| AC-008 | PASS | `test_portfolio_response_excludes_risk_weight_but_keeps_allocation_weight` — 직접 재현: 라이브 응답에서 `risk.results[]`에 `actual_weight_pct` 없음, `allocation.results[]`에는 있음 확인 |
| AC-009 ~ AC-015 | **미실행** | 코드 구현은 완료되고 정적 점검(코드 스팟체크: `unknown`→"판정 불가" 처리, `/login` 리다이렉트, 영역 한정 오류, `NEXT_PUBLIC_API_URL` 관례, `source==='sample'` 표기 — 전부 소스에 존재 확인)했으나, 이 환경에 브라우저/개발자도구가 없어 `docs/weekly/WEEK_10.md` 「`/portfolio` 화면 수동 검증 절차」의 실제 실행은 하지 못했다. 발표 전 사람이 절차대로 1회 실행 필요. |
| AC-016 | PASS(백엔드) / **미실행**(대시보드) | 백엔드: 기존 `test_chart.py`·`test_indicators.py`·`test_notion_settings.py` 전부 PASS(`pytest backend/tests/ -v` → 91+ passed, 회귀 없음). 대시보드 5개 영역 수동 확인은 위와 같은 사유로 미실행. |

## §E.1 Plan-phase Audit-Ready Signal

- plan_complete_at: 2026-09-22
- plan_status: audit-ready (plan-auditor iteration 2 verdict: PASS, aggregate 0.875 ≥ Tier M threshold 0.80, `.moai/reports/plan-audit/SPEC-PORTFOLIO-001-review-2.md`)

## §E.2 Run-phase Evidence

M1~M4 전체 커밋: `2021f11`(M1 RED) → `6dda15a`(M1 GREEN) → `4af23e7`(M2) → `8fc5b1e`(M3) → CI 확장·문서(M4, 본 커밋). 워크트리 `.claude/worktrees/portfolio-news` / `portfolio-m3`(M3만 별도 워크트리, 병합됨), 최종 브랜치 `feature/10-정우준-portfolio-news`.

**통합 후 전체 검증(2026-09-22, HEAD `e9cd48e` 기준)**:
```
$ python3 -m pytest backend/tests/ scripts/tests/ -v
114 passed, 1 skipped, 1 warning in 0.55s
$ ruff check backend/
All checks passed!
$ npm run lint && npx tsc --noEmit && npm run build
✔ No ESLint warnings or errors / tsc 무출력(clean) / ✓ Compiled successfully — /portfolio 라우트 2.1 kB 생성
```
1-skip 사유: `test_committed_agents_json_files_satisfy_valid_news_document[008490]` — `008490_agents.json` 미생성(SPEC-NEWS-001 소관, 아래 재수집 절차 참고).

## §E.3 Run-phase Audit-Ready Signal

- run_status: 코드 구현 및 자동 게이트 전체 완료. AC-009~AC-015 및 AC-016 대시보드분은 브라우저 수동 검증이 필요하나 이 실행 환경에 브라우저가 없어 **미실행** — PASS로 기록하지 않음(정직성 원칙).
- ac_pass_count: 9 (AC-001~AC-008, AC-016 백엔드분)
- ac_pending_count: 8 (AC-009~AC-015, AC-016 대시보드분 — 사람이 `docs/weekly/WEEK_10.md` 절차대로 1회 실행 필요)
- preserve_list_post_run_count: 위반 0건
- new_warnings_or_lints_introduced: 0

## §E.4 Sync-phase Audit-Ready Signal

_<pending sync-phase — PR 생성 시 manager-git 또는 사용자가 기록>_
