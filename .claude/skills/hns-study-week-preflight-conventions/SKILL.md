---
name: hns-study-week-preflight-conventions
description: >
  Single source of truth for antshell's study-cadence conventions — branch
  naming, weekly-doc completeness, and presenter-metadata consistency between
  CLAUDE.md and docs/weekly/WEEK_XX.md. Consumed by the study-week-preflight
  harness's branch-pr-audit, weekly-doc-audit, week-context, and
  readiness-brief specialists so the convention definitions live in exactly
  one place instead of being copy-pasted across four agent files. Use when
  auditing a branch name, a weekly doc, or CLAUDE.md's CURRENT_PRESENTER
  field for compliance, or when deriving a compliant branch name from a
  violating one.
license: Apache-2.0
compatibility: Designed for Claude Code
allowed-tools: Read, Grep
metadata:
  version: "1.0.0"
  category: "domain"
  status: "active"
  updated: "2026-09-06"
  modularized: "false"
  tags: "study-week, branch-naming, weekly-doc, presenter-metadata, antshell"
  author: "hns-study-week-preflight harness (GENERATE phase)"
  related-skills: "hns-study-week-preflight-verify"

progressive_disclosure:
  enabled: true
  level1_tokens: 110
  level2_tokens: 1400

triggers:
  keywords: ["branch naming", "feature branch", "weekly doc", "WEEK_XX", "CURRENT_PRESENTER", "presenter mismatch", "study week convention"]
  agents:
    - hns-study-week-preflight-branch-pr-audit-specialist
    - hns-study-week-preflight-weekly-doc-audit-specialist
    - hns-study-week-preflight-week-context-specialist
    - hns-study-week-preflight-readiness-brief-specialist
  phases: ["run"]
---

# Study-Week Preflight Conventions

## Quick Reference

| Convention | Rule |
|---|---|
| Branch naming | `feature/<주차>-<이름>-<기능명>` — two-digit zero-padded week, presenter's real name, short feature slug |
| Branch regex | `^feature/\d{2}-[^-]+-.+$` |
| Weekly-doc completeness | Real presenter name (not a single letter or "TBD") + at least one checked-off or concretely-scoped deliverable + no embedded example that itself violates the branch regex |
| Presenter-metadata consistency | `CLAUDE.md`'s `CURRENT_PRESENTER` MUST equal the current week's `docs/weekly/WEEK_XX.md` presenter field |

## Implementation Guide

### 1. Branch naming convention

Source: `_claude_core/GIT_RULES.md` § 브랜치 전략 (GitHub Flow), which states verbatim:

> ```
> main                                  ← 항상 배포 가능. 직접 push 금지.
>   └── feature/<주차>-<이름>-<기능명>   ← 기능 개발
>   └── fix/<주차>-<이름>-<버그내용>     ← 버그 수정
>   └── hotfix/<이름>-<내용>             ← 긴급 수정
> ```
>
> 예시:
> - `feature/01-alice-project-init`
> - `feature/03-bob-dart-api`

The canonical form is `feature/<주차>-<이름>-<기능명>`:

- `<주차>` — two-digit zero-padded week number (`01`, not `1`)
- `<이름>` — the presenter's real name (or the team's agreed short handle), never a placeholder letter
- `<기능명>` — a short, hyphen-or-word feature slug

Validation regex (feature branches): `^feature/\d{2}-[^-]+-.+$`

- `\d{2}` enforces the two-digit zero-padded week
- `[^-]+` captures the name segment up to the next hyphen (the name itself MUST NOT contain a hyphen, or the segments become ambiguous)
- `.+` captures the remainder as the feature slug (may itself contain hyphens)

The `fix/<주차>-<이름>-<버그내용>` and `hotfix/<이름>-<내용>` variants follow the same discipline; `hotfix/` omits the week number by design (GIT_RULES.md treats hotfixes as out-of-cadence).

### 2. Weekly-doc completeness bar

A `docs/weekly/WEEK_XX.md` is **filled** when ALL of the following hold:

1. **Real presenter name** in the header line (`**발표자:** <name>`) — not a single letter (`H`, `I`, `A`, `B`, ...) and not `TBD`/`미정`.
2. **At least one concretely-scoped deliverable** in `## 발표자 작업 목록` — a checked-off item (`- [x]`), or an unchecked item whose text names a specific artifact/file/SPEC rather than a generic placeholder phrase.
3. **No embedded convention-violating example** in the doc's own body text (see § Negative example below) — a doc that instructs its presenter to create a branch that itself fails the § 1 regex is propagating the violation forward.

**Negative example found this session (2026-09-06)**: `WEEK_02.md`, `WEEK_03.md`, `WEEK_05.md`, `WEEK_09.md`, `WEEK_10.md`, `WEEK_11.md`, and `WEEK_12.md` all share one boilerplate template whose `**발표자:**` field is a bare single letter (`B`, `C`, `E`, `I`, `A`, `B`, `전원` respectively) rather than a real name. Two of these docs go further and embed a branch-name instruction that itself violates the § 1 regex:

- `WEEK_08.md` § 발표자 작업 목록: `- [ ] feat/H-week08 브랜치 생성 후 PR 오픈` — wrong prefix (`feat/` not `feature/`), wrong shape (no zero-padded week segment, no separate feature slug), and the placeholder letter `H` in the name position.
- `WEEK_09.md` § 발표자 작업 목록: `- [ ] feat/I-week09 브랜치 생성 후 PR 오픈` — same defect shape with placeholder letter `I`.

A weekly doc audit MUST flag both defects independently: the placeholder presenter name (§ 2 item 1) and the embedded non-compliant branch example (§ 2 item 3), because the second one actively instructs the presenter toward a rule violation rather than merely omitting information.

### 3. Presenter-metadata-consistency rule

`CLAUDE.md`'s `CURRENT_PRESENTER` field and the current week's `docs/weekly/WEEK_XX.md` `**발표자:**` field describe the same fact (who presents this week) from two different files, and MUST agree. Disagreement means one of the two was updated and the other was not — a stale-doc signal, not a stylistic difference.

**Worked example found this session (2026-09-06)**: with `CURRENT_WEEK=08` in `CLAUDE.md`:

- `CLAUDE.md` line 28: `CURRENT_PRESENTER=박재선`
- `docs/weekly/WEEK_08.md` header: `**발표자:** H`

These disagree (`박재선` ≠ `H`). This is exactly the disagreement this convention exists to catch: `WEEK_08.md` was never filled in past its boilerplate stage (see § 2), so it still carries the template's placeholder letter while `CLAUDE.md` was updated with the real presenter's name for the week. The audit's job is to surface this pairing — WHICH file is authoritative is a judgment for the readiness-brief specialist / the human presenter to make, not something this convention decides on its own.

### 4. Corrected-name recipe

Given a violating branch name (or a violating embedded example in a weekly doc), derive the compliant replacement in three steps:

1. **Extract the week number** from context (the doc's own filename `WEEK_<NN>.md`, or `CLAUDE.md`'s `CURRENT_WEEK`) and zero-pad it to two digits.
2. **Extract or resolve the presenter's real name** — prefer `CLAUDE.md`'s `CURRENT_PRESENTER` when the week matches `CURRENT_WEEK`; otherwise use the weekly doc's own `**발표자:**` field IF it is a real name (not a single-letter placeholder — see § 2). If both sources currently show only a placeholder, the corrected name cannot be derived mechanically and MUST be flagged as a blocker (missing input), not guessed.
3. **Reuse the existing feature-slug segment** (the part after the placeholder name, e.g. `week09`) as `<기능명>`, or replace it with a more descriptive slug when one is available.

**Worked derivations from this session's findings**:

| Violating form | Week | Real presenter (from CLAUDE.md when week matches) | Corrected form |
|---|---|---|---|
| `feat/H-week08` (WEEK_08.md) | 08 | 박재선 (CURRENT_WEEK=08 → CURRENT_PRESENTER=박재선) | `feature/08-박재선-week08` |
| `feat/I-week09` (WEEK_09.md) | 09 | I (placeholder only — WEEK_09.md's own field is also unfilled; not yet CURRENT_WEEK, so CLAUDE.md carries no presenter for week 09) | Cannot be mechanically derived — flag as blocker until WEEK_09.md's `**발표자:**` field is filled with a real name |

The first row shows the recipe succeeding because `CLAUDE.md` supplies a real name for the currently-active week. The second row shows the recipe correctly refusing to guess when no source yet carries a real name — this is the intended behavior, not a gap in the recipe.

## Advanced

- **Why the branch regex requires `[^-]+` for the name segment**: a hyphenated real name (e.g. a romanized name with a hyphen) would make `feature/09-a-b-week09` ambiguous between name=`a-b` and name=`a` with slug=`b-week09`. Teams whose members have hyphenated names should agree on a hyphen-free handle for the branch-name position specifically; this is a documentation convention, not a tooling limitation.
- **Scope of this skill**: this skill defines and evidences the conventions; it does not itself run the git/grep commands that apply them (that is each consuming specialist's job — `hns-study-week-preflight-branch-pr-audit-specialist` for branches, `hns-study-week-preflight-weekly-doc-audit-specialist` for doc completeness, `hns-study-week-preflight-week-context-specialist` for the presenter cross-check, `hns-study-week-preflight-readiness-brief-specialist` for surfacing the corrected-name recipe in its next-actions section).
- **Re-verify before citing**: the worked examples above are dated 2026-09-06. A consuming specialist MUST re-read `CLAUDE.md` and the relevant `WEEK_XX.md` at run time rather than assuming these examples still hold — `CURRENT_WEEK`/`CURRENT_PRESENTER` change weekly by design.
