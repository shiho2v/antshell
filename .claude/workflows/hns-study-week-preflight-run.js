// =============================================================
// File   : hns-study-week-preflight-run.js
// Author : @jasonbaac
// Week   : 08 | Ch.08
// Created: 2026-09-06
// =============================================================
// hns-study-week-preflight-run.js — weekly study-cadence readiness + repo-health preflight
//
// SCOPE: user-owned Runner Workflow (the `hns-*` prefix) — NOT template-managed. `moai update`
//   never overwrites this file. It is the execution vehicle for /harness:study-week-preflight.
//
// Manifest: reads .claude/commands/harness/study-week-preflight/manifest.json as its single
//   source of truth (MANIFEST_PATH below). `moai harness doctor` checks that this constant
//   resolves to an existing file — do not rename or relocate without updating both.
//
// Pattern: Pipeline + Fan-out/Fan-in.
//   Context  — week-context (sub-agent) runs first; its output seeds every checker.
//   Checks   — branch-pr-audit / harness-health / quality-gate-probe / weekly-doc-audit run in
//              parallel (dynamic-workflow primitive — a fan-out group, not solo dispatch).
//   Report   — readiness-brief (sub-agent) fans in all 5 results into one Korean report.
//
// Dispatch: each specialist.primitive is consumed VERBATIM from the manifest, never re-derived.
//   The manifest's 6 specialists use only `sub-agent` and `dynamic-workflow` — both dispatch via
//   the same agent() call here; `dynamic-workflow` only means the specialist MAY run as part of a
//   parallel() fan-out group rather than solo (per dynamic-workflows.md primitive mapping).
//
// Determinism: no Date.now() / Math.random() in the script body. Any timestamp is stamped by the
//   orchestrator AFTER the run returns (dynamic-workflows.md § How a Workflow Runs).
//
// Isolation: every specialist in the manifest declares isolation: "none" — no specialist targets
//   overlapping write paths (this harness is read-only end to end), so NO worktree-cleanup
//   directive is emitted at end-of-run.
//
// Usage:
//   Workflow({ scriptPath: ".claude/workflows/hns-study-week-preflight-run.js" })

export const meta = {
  name: 'study-week-preflight',
  description: 'Weekly study-cadence readiness + repo-health preflight — presenter/branch/hook/quality-gate/doc checks fanned in to one Korean readiness brief',
  phases: [
    { title: 'Context', detail: 'week-context reads CLAUDE.md + the matching docs/weekly/WEEK_<NN>.md to establish the current week, presenter, and branch-prefix expectation' },
    { title: 'Checks', detail: 'branch-pr-audit / harness-health / quality-gate-probe / weekly-doc-audit run in parallel against the Context output' },
    { title: 'Report', detail: 'readiness-brief fans in all 5 results into one Korean readiness report with an exact fix per FAIL line' },
  ],
}

// Single config-read path — the manifest is the SSOT. `moai harness doctor` resolves this constant.
const MANIFEST_PATH = '.claude/commands/harness/study-week-preflight/manifest.json'

// determinism: read manifest content via the agent (file I/O happens inside the agent's tool use,
// not in the script body) — the script itself performs no filesystem access of its own.
// The Context specialist is instructed to read MANIFEST_PATH so the manifest stays the single
// source of truth the script points at, without the script body reading files directly.

// ---------------------------------------------------------------------------
phase('Context')

const WEEK_CONTEXT_PROMPT = `You are a read-only repo-context extractor for a 9-person Korean stock-analysis study team's weekly preflight harness. Do NOT modify any file.

This harness's manifest lives at ${MANIFEST_PATH} — read it first to confirm the specialist roster you are part of (informational only; you do not dispatch other specialists yourself).

Then:
1. Read /home/jsbaac/STUDY/antshell/CLAUDE.md and extract the current \`CURRENT_WEEK\`, \`CURRENT_PRESENTER\`, and \`CURRENT_CHAPTER\` values.
2. Zero-pad CURRENT_WEEK to two digits and read the matching docs/weekly/WEEK_<NN>.md (e.g. CURRENT_WEEK=08 -> docs/weekly/WEEK_08.md).
3. From WEEK_<NN>.md, extract the presenter name recorded there (if the document records one) and any stated branch-prefix expectation.
4. Compute the expected branch prefix for this week as \`feature/<week>-<presenter-name>-\` using the CLAUDE.md presenter (zero-padded week, e.g. \`feature/08-박재선-\`).
5. Compare the presenter named in CLAUDE.md against the presenter named in WEEK_<NN>.md. If they disagree (different name, or one is missing/placeholder), flag it explicitly as a presenter_metadata_consistency issue — name both values.

Return a structured markdown report with these exact headings, in this order:
## week_context
- current_week: <NN>
- current_presenter: <name from CLAUDE.md>
- current_chapter: <value>
- weekly_doc_path: docs/weekly/WEEK_<NN>.md
- weekly_doc_presenter: <name found in WEEK_<NN>.md, or "not found">
- expected_branch_prefix: feature/<NN>-<presenter>-
### presenter_consistency
(PASS if CLAUDE.md and WEEK_<NN>.md agree on the presenter; FAIL with both values named otherwise)
### gaps
(anything you could not determine, and why — never fabricate a value)`

const weekContext = await agent(WEEK_CONTEXT_PROMPT, { label: 'context:week', phase: 'Context', model: 'haiku', effort: 'low' })

// ---------------------------------------------------------------------------
phase('Checks')

const BRANCH_PR_AUDIT_PROMPT = `You are a read-only git-hygiene auditor. Do NOT modify any file, branch, or PR.

Week context from the prior phase:
${weekContext}

Steps:
1. Run \`git branch -a\` to list every local and remote branch.
2. Run \`which gh\`. If \`gh\` resolves, run \`gh pr list\` to also audit open pull requests; if it does not resolve, note that PR auditing was skipped (gh CLI unavailable) and proceed with branch names only — this is a graceful degradation, not a failure.
3. Validate every branch name (and, where available, every PR head branch) against the convention \`feature/<주차>-<이름>-<기능명>\`, expressed as the regex \`^feature/\\d{2}-[^-]+-.+$\`.
4. Separate findings into two buckets:
   - **graded violations**: branches belonging to the CURRENT week (matching the current week's number from week_context, e.g. branches starting \`feature/08-\` when current_week=08) that violate the regex, OR that do not match the expected_branch_prefix's presenter name from week_context.
   - **informational only**: branches from earlier weeks, already-merged branches, or branches unrelated to the \`feature/\` convention (e.g. \`main\`, \`develop\`) — list these but do NOT grade them as failures.

Return a structured markdown report with these exact headings:
## branch_pr_audit
### graded_violations
(one bullet per CURRENT-week branch that violates the convention, with the exact branch name and the exact fix — e.g. the corrected branch name to rename to)
### informational
(older/merged/unrelated branches — listed, not graded)
### gh_availability
(available | unavailable — and whether PR data was included)
### verdict
(PASS if graded_violations is empty, FAIL otherwise)`

const HARNESS_HEALTH_PROMPT = `You are a read-only Claude Code harness-health auditor. Do NOT modify any file.

Read .claude/settings.json. For every hook entry's \`command\` field:
1. Identify the named interpreter at the start of the command (e.g. \`python3\`, \`bash\`, \`node\`, \`sh\`).
2. Run \`which <interpreter>\` to confirm it resolves on this machine.
3. Extract the script file path referenced in the command and confirm the file exists on disk (Read or a file-existence check).

Return a structured markdown report with these exact headings:
## harness_health
### hooks_checked
(one row per hook: event, command, interpreter, interpreter_resolved yes/no, script_path, script_exists yes/no)
### failures
(one bullet per hook where the interpreter did not resolve OR the script file is missing, with the exact hook event and the exact remediation — e.g. "install python3" or "the referenced script path does not exist; create it or correct settings.json")
### verdict
(PASS if failures is empty, FAIL otherwise)`

const QUALITY_GATE_PROBE_PROMPT = `You are a read-only CI/quality-gate auditor. Do NOT modify any file.

1. Read .github/workflows/ci.yml and list every job step's referenced path or command target (working-directory values, test paths, script invocations).
2. Read frontend/package.json and list its \`scripts\` entries.
3. For every path referenced by ci.yml or by a package.json script (e.g. does \`backend/tests/\` exist if ci.yml references it; does a script's target file exist), verify the path actually exists on disk.
4. Flag any referenced path or command target that does NOT exist.

Return a structured markdown report with these exact headings:
## quality_gate_probe
### ci_yml_references
(one bullet per path/command target referenced in ci.yml, with exists yes/no)
### package_json_scripts
(one bullet per frontend/package.json script name + command, with any referenced path's exists yes/no)
### failures
(one bullet per missing reference, with the exact file and the exact fix — e.g. "create backend/tests/ or update ci.yml's working-directory")
### verdict
(PASS if failures is empty, FAIL otherwise)`

const WEEKLY_DOC_AUDIT_PROMPT = `You are a read-only documentation auditor for a weekly study rotation. Do NOT modify any file.

Week context from the prior phase:
${weekContext}

1. Read the CURRENT week's docs/weekly/WEEK_<NN>.md (current_week from week_context) and the NEXT week's docs/weekly/WEEK_<NN+1>.md (zero-padded, e.g. if current is 08 then next is 09).
2. For each of the two documents, check for:
   - a placeholder presenter (a single letter, "TBD", "미정", an empty field, or similar non-name placeholder)
   - any unfilled checklist item (an unchecked box or a placeholder line where content is expected)
   - any branch-name example written in the document that itself violates \`^feature/\\d{2}-[^-]+-.+$\`

Return a structured markdown report with these exact headings:
## weekly_doc_audit
### current_week_doc
(file path; PASS or FAIL with each issue named — placeholder presenter / unfilled checklist / bad branch example)
### next_week_doc
(file path; PASS or FAIL with each issue named)
### verdict
(PASS if both documents have zero issues, FAIL otherwise)`

const [branchPrAudit, harnessHealth, qualityGateProbe, weeklyDocAudit] = await parallel([
  () => agent(BRANCH_PR_AUDIT_PROMPT, { label: 'check:branch-pr-audit', phase: 'Checks', model: 'sonnet', effort: 'medium' }),
  () => agent(HARNESS_HEALTH_PROMPT, { label: 'check:harness-health', phase: 'Checks', model: 'sonnet', effort: 'medium' }),
  () => agent(QUALITY_GATE_PROBE_PROMPT, { label: 'check:quality-gate-probe', phase: 'Checks', model: 'sonnet', effort: 'medium' }),
  () => agent(WEEKLY_DOC_AUDIT_PROMPT, { label: 'check:weekly-doc-audit', phase: 'Checks', model: 'sonnet', effort: 'medium' }),
])

// ---------------------------------------------------------------------------
phase('Report')

const READINESS_BRIEF_PROMPT = `당신은 스터디 운영진을 위한 한국어 준비 상태 브리핑 작성자입니다. 파일을 수정하지 마세요.

다음 5개 점검 결과를 종합해 하나의 한국어 마크다운 보고서를 작성하세요.

## week_context
${weekContext}

## branch_pr_audit
${branchPrAudit}

## harness_health
${harnessHealth}

## quality_gate_probe
${qualityGateProbe}

## weekly_doc_audit
${weeklyDocAudit}

작성 규칙:
- 보고서 제목에 현재 주차(CURRENT_WEEK)와 발표자를 명시하세요.
- 각 점검 항목을 PASS/FAIL로 요약한 표를 맨 위에 두세요.
- FAIL로 판정된 모든 항목에는 반드시 "실행할 명령어" 또는 "수정할 정확한 문자열" 형태의 구체적 조치를 한 줄씩 붙이세요 — 모호한 조언("확인해 보세요")은 금지합니다.
- presenter_metadata_consistency 불일치가 있으면 최상단에 강조해서 표시하세요.
- gh CLI가 없어 PR 감사를 건너뛴 경우 그 사실을 보고서에 명시하세요 (실패로 취급하지 마세요).
- 전체 결론(발표 전 준비 완료 여부)을 마지막에 한 문장으로 명시하세요.

마크다운 문자열만 반환하세요. 파일을 쓰지 마세요 — 이 워크플로우를 호출한 커맨드가 결과를 사용자에게 보여줍니다.`

const readinessBrief = await agent(READINESS_BRIEF_PROMPT, { label: 'report:readiness-brief', phase: 'Report', model: 'sonnet', effort: 'high' })

// No worktree-cleanup directive: every specialist in the manifest declares isolation: "none".
return {
  week_context: weekContext,
  checks: {
    branch_pr_audit: branchPrAudit,
    harness_health: harnessHealth,
    quality_gate_probe: qualityGateProbe,
    weekly_doc_audit: weeklyDocAudit,
  },
  readiness_brief: readinessBrief,
}
