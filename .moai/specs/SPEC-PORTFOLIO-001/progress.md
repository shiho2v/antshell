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
| M3 프론트엔드 화면 + 대시보드 링크 + 수동 검증 절차 | 거의 완료 (AC-011만 미실행) | `frontend/src/app/portfolio/page.tsx`, `frontend/src/app/dashboard/page.tsx`(링크 1줄), `docs/weekly/WEEK_10.md` 「`/portfolio` 화면 수동 검증 절차」 | REQ-009~REQ-015 / AC-009~AC-015 |
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
| AC-009 | PASS | 2026-09-22 사용자 수동 검증(스크린샷). 4개 종목 모두 밸류에이션 배지+점수, 리스크 배지, 리밸런싱 액션 배지, 드리프트%, 리밸런싱 금액이 표시됨. 값이 커밋된 `data/portfolio_analysis.json`과 정확히 일치(예: 삼성전자 드리프트 -16.9%/리밸런싱 5,541,000원, 삼성전기 9.7%/-3,167,500원). |
| AC-010 | PASS | 2026-09-22 사용자 수동 검증(스크린샷). "보유 종목 기준일: 2026-07-25"·"분석 생성일: 2026-09-22" 별도 레이블로 표시, "실시간 시세가 아닌 스냅샷" 문구 존재, "샘플 데이터(실제 에이전트 분석 아님)" 배지 존재. |
| AC-011 | **미실행** | `/api/portfolio` 요청 실패(네트워크 오류/404/500) 시나리오는 아직 강제로 재현해보지 않음 — 백엔드 중지 또는 파일 임시 이동 필요. |
| AC-012 | PASS | 2026-09-22 사용자 수동 검증. 로그아웃 후 `/portfolio` 직접 접근 시 `/login`으로 리다이렉트됨을 확인(3단계). |
| AC-013 | PASS | 2026-09-22 사용자 수동 검증(스크린샷). 대시보드 헤더에 "포트폴리오 분석" 링크 존재, 클릭 시 `/portfolio`로 정상 이동. |
| AC-014 | PASS | 위 AC-009/010 데이터가 실제로 로드됐다는 것 자체가 `NEXT_PUBLIC_API_URL` 관례가 동작함을 의미 (검증 중 CORS 설정 오류를 발견해 수정한 뒤 확인됨 — 아래 §E.2 부록 참고). |
| AC-015 | PASS | 2026-09-22 사용자 수동 검증(스크린샷). SK하이닉스·서흥의 밸류에이션/리스크/리밸런싱이 모두 "판정 불가"로 점선 테두리 배지로 표시되어 목록에서 숨겨지지 않고 정상 판정(채워진 색 배지)과 시각적으로 구분됨. |
| AC-016 | PASS(백엔드) / 부분 PASS(대시보드) | 백엔드: 기존 `test_chart.py`·`test_indicators.py`·`test_notion_settings.py` 전부 PASS(`pytest backend/tests/ -v` → 91+ passed, 회귀 없음). 대시보드: 2026-09-22 CORS 수정 후 재접속 사용자 확인("잘 됩니다") — 보유 종목 테이블·주가 차트가 정상 로드됨. **주의**: 최초 「1단계 완료」 보고는 잘못된 포트(3000, main 브랜치)를 보고 있었던 것으로 판명되어 이 브랜치의 증거로 사용하지 않음. Notion 저장 버튼 실제 클릭 동작은 아직 테스트 안 됨. |

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

### 브라우저 수동 검증 (2026-09-22, 사용자 직접 실행)

이 브랜치를 8003(백엔드)·3001(프론트엔드) 포트로 별도 기동해 사용자가 직접 로그인 후 AC-009·010·012·013·014·015·016을 확인(스크린샷 2건). AC-011(요청 실패 시 영역 한정 오류)은 아직 미실행.

**검증 중 발견한 환경 이슈(코드 결함 아님)**: 검증용 백엔드를 3001 프론트엔드와 CORS 없이 기동해 최초 시도에서 전체 fetch 실패가 발생했다. 원인은 `backend/app/main.py`의 `ALLOWED_ORIGINS` 기본값이 `http://localhost:3000`만 포함하기 때문이며, 실제 배포/평소 개발 환경(프론트엔드 3000, 백엔드 8000)에서는 발생하지 않는다 — 오케스트레이터가 검증 편의상 3001 포트를 선택하면서 생긴 문제였다. `ALLOWED_ORIGINS=http://localhost:3001,http://localhost:3000` 환경변수로 재기동해 해소했다. SPEC 코드 변경 없음.

## §E.3 Run-phase Audit-Ready Signal

- run_status: 코드 구현 및 자동 게이트 전체 완료. 사용자가 2026-09-22 직접 브라우저로 AC-009·010·012·013·014·015·016을 확인(PASS). AC-011만 아직 미실행.
- ac_pass_count: 15 (AC-001~AC-010, AC-012~AC-016)
- ac_pending_count: 1 (AC-011 — 요청 실패 시나리오 재현 필요)
- preserve_list_post_run_count: 위반 0건
- new_warnings_or_lints_introduced: 0

## §E.4 Sync-phase Audit-Ready Signal

_<pending sync-phase — PR 생성 시 manager-git 또는 사용자가 기록>_
