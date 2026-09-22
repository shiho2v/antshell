---
id: SPEC-NEWS-001
title: "종목 뉴스 모듈 — 진행 기록"
version: "0.1.1"
status: draft
created: 2026-09-20
updated: 2026-09-20
tier: M
---

# SPEC-NEWS-001 진행 기록

## 마일스톤 현황

| 마일스톤 | 상태 | 산출물 | 커버 REQ | 커버 AC |
|---|---|---|---|---|
| M1 데이터 확보 + 백엔드 엔드포인트 | 대기 | `data/008490_agents.json`, `backend/app/news.py`, `backend/app/main.py`(import 1줄 + 라우트 구간), `backend/tests/test_news.py` | REQ-001~REQ-007 | AC-001~AC-007 |
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
| 조건 1 — 수집 시도 | 실행한 명령(`python scripts/orchestrate_stock_agents.py 008490 --save`)과 그 실패 출력을 그대로 | _<M1에서 기록>_ |
| 조건 2 — 파일 부재 동작 | AC-004(`404`)와 AC-010 (c) 오류 상태의 판정 — 둘 다 PASS여야 한다 | _<AC-004는 M1, AC-010은 M3에서 기록>_ |
| 조건 3 — 사유와 후속 | 실패 사유 / AC-001을 PASS로 바꾸기 위한 후속 조치 / `data/008490_agents.json`이 여전히 없다는 사실 | _<M3에서 기록>_ |
| 종합 | 세 조건이 모두 충족되었는가(예 / 아니오). "아니오"면 SPEC을 닫지 않는다 | _<M3에서 기록>_ |

## §E.1 Plan-phase Audit-Ready Signal

- plan_complete_at: 2026-09-22
- plan_status: audit-ready (plan-auditor iteration 2 verdict: PASS, `.moai/reports/plan-audit/SPEC-NEWS-001-review-2.md`)

## §E.2 Run-phase Evidence

_<pending run-phase>_

## §E.3 Run-phase Audit-Ready Signal

_<pending run-phase>_

## §E.4 Sync-phase Audit-Ready Signal

_<pending sync-phase>_
