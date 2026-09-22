---
id: SPEC-PORTFOLIO-001
title: "포트폴리오 분석 모듈 — 진행 기록"
version: "0.1.1"
status: draft
created: 2026-09-20
updated: 2026-09-20
tier: M
---

# SPEC-PORTFOLIO-001 진행 기록

## 마일스톤 현황

| 마일스톤 | 상태 | 산출물 | 커버 |
|---|---|---|---|
| M1 스크립트 JSON 저장 + 샘플 모드 + 데이터 생성 | 대기 | `scripts/orchestrate_portfolio.py`, `scripts/tests/test_orchestrate_portfolio.py`, `data/portfolio_analysis.json` | REQ-001~REQ-004 / AC-001~AC-004 |
| M2 백엔드 엔드포인트 | 대기 | `backend/app/main.py`, `backend/tests/test_portfolio.py` | REQ-005~REQ-008 / AC-005~AC-008 |
| M3 프론트엔드 화면 + 대시보드 링크 + 수동 검증 절차 | 대기 | `frontend/src/app/portfolio/page.tsx`, `frontend/src/app/dashboard/page.tsx`(링크 1줄), `docs/weekly/WEEK_10.md` 「`/portfolio` 화면 수동 검증 절차」 | REQ-009~REQ-015 / AC-009~AC-015 |
| M4 문서 동기화 + CI 테스트 경로 확장 + 품질 게이트 | 대기 | `docs/weekly/WEEK_10.md`, `.github/workflows/ci.yml`("Backend 테스트" 단계), 본 문서 | REQ-016 / AC-016 |

## 인수 기준 판정 기록 (M4에서 작성)

AC-001~AC-016의 PASS/FAIL 매트릭스를 M4에서 여기에 채운다. 기록 규칙은 두 가지다.

- **자동 판정 AC**(AC-001~AC-008, AC-016의 백엔드 회귀분) — 실행한 명령과 그 출력을 그대로 적는다.
- **수동 판정 AC**(AC-009~AC-015, AC-016의 대시보드분) — `docs/weekly/WEEK_10.md` 「`/portfolio` 화면 수동 검증 절차」의 해당 PASS 조건을 인용하고, 관찰한 결과를 적는다. 절차 문서 인용 없이 "확인함"이라고만 적은 항목은 PASS로 보지 않는다(`acceptance.md` 품질 게이트).

`.github/workflows/ci.yml`의 테스트 단계를 `scripts/tests/`까지 확장하지 못한 경우, 그 사유와 AC-001~AC-004의 대체 검증 방법을 이 절에 함께 기록한다.

| AC | 판정 | 근거 |
|---|---|---|
| AC-001 ~ AC-016 | _<M4에서 기록>_ | _<M4에서 기록>_ |

## §E.1 Plan-phase Audit-Ready Signal

- plan_complete_at: 2026-09-22
- plan_status: audit-ready (plan-auditor iteration 2 verdict: PASS, aggregate 0.875 ≥ Tier M threshold 0.80, `.moai/reports/plan-audit/SPEC-PORTFOLIO-001-review-2.md`)

## §E.2 Run-phase Evidence

_<pending run-phase>_

## §E.3 Run-phase Audit-Ready Signal

_<pending run-phase>_

## §E.4 Sync-phase Audit-Ready Signal

_<pending sync-phase>_
