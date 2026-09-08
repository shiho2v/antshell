---
description: 스터디 주차 문서와 저장소 상태(브랜치 규칙·훅·품질 게이트)가 발표 전에 준비됐는지 점검한다
argument-hint: ""
allowed-tools: Skill
---

Run the Runner Workflow `hns-study-week-preflight-run.js` (`.claude/workflows/hns-study-week-preflight-run.js`), which reads `.claude/commands/harness/study-week-preflight/manifest.json` as its single source of truth and dispatches the manifest's 6 specialists. Return its aggregated result as the readiness report.
