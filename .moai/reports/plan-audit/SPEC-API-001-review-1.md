# SPEC Review Report: SPEC-API-001
Iteration: 1/3
Verdict: FAIL
Overall Score: 0.75 (aggregate score is moot — MP-2 must-pass firewall failure forces FAIL regardless of aggregate per M5)

Reasoning context ignored per M1 Context Isolation. This audit is based solely on `.moai/specs/SPEC-API-001/{spec.md, plan.md, progress.md, spec-compact.md}` and live cross-checks against the repository (`backend/app/main.py`, `frontend/src/app/dashboard/page.tsx`, `data/*.json`, `outputs/*.html`, `docs/setup/ONBOARDING.md`, `.github/workflows/ci.yml`).

Tier: S (per frontmatter `tier: S`). Input contract used: spec.md + plan.md (Tier S; AC inline in spec.md §3). Confirmed no acceptance.md/design.md/research.md exist in the SPEC directory — only spec.md, plan.md, progress.md, and the auto-generated spec-compact.md are present (`ls .moai/specs/SPEC-API-001/`).

## Must-Pass Results

- **[FAIL] MP-1 REQ number consistency**: REQ-001 through REQ-016 are sequential, zero-padded consistently (3 digits), with no gaps or duplicates (spec.md:L40-78, mirrored in spec-compact.md:L13-43). This criterion itself PASSES. *(Listed here for completeness; see Overall Score note — this one criterion is fine.)*
  → Corrected: **[PASS] MP-1** REQ-001..016 sequential, no gaps/dupes, consistent `REQ-0NN` zero-padding. Evidence: spec.md:L40 (`REQ-001`) through spec.md:L78 (`REQ-016`).

- **[FAIL] MP-2 EARS/GEARS format compliance** (requirement layer — spec.md `REQ-XXX` entries only; no AC-XXX was graded against this criterion, per M3 § Scope): Three requirements carry a bracketed tag, `[Event-detected]`, that is **not one of the five canonical GEARS/EARS pattern names** (Ubiquitous / Event-driven / State-driven / Where / Unwanted) enumerated in M3:
  - spec.md:L52 — REQ-006 tagged `[Event-detected]`
  - spec.md:L54 — REQ-007 tagged `[Event-detected]`
  - spec.md:L64 — REQ-011 tagged `[Event-detected]`
  All three requirements are otherwise grammatically shaped as valid `When [trigger], the <subject> shall [response]` sentences (Event-driven grammar), but the bracketed label itself is an invented sixth category not present in the canonical taxonomy. Per M5 MP-2: "Every REQ-XXX requirement entry in spec.md must match one of the five GEARS patterns (or their legacy EARS equivalents)." A non-canonical tag name is a literal mismatch against this criterion — 3 of 16 REQs (18.75%) are affected. This is a must-pass firewall failure and forces `Verdict: FAIL` regardless of aggregate score (M5).

- **[PASS] MP-3 YAML frontmatter validity**: spec.md:L1-15 carries all 12 canonical fields with correct types, no rejected snake_case aliases (`created:`/`updated:`/`tags:` used correctly, not `created_at:`/`updated_at:`/`labels:`). `id: SPEC-API-001` matches `^SPEC-[A-Z][A-Z0-9]+-[0-9]{3}$`; `version: "0.1.0"` quoted semver; `status: draft` valid enum; `priority: P1` valid enum; `lifecycle: spec-anchored` valid enum; `phase: "v1.0.0"` is a release-target label, not a prohibited stage name. Evidence: spec.md:L1-15.

- **[N/A] MP-4 Section 22 language neutrality**: This SPEC is scoped to a two-language application stack (Python/FastAPI backend + TypeScript/Next.js frontend) rather than the 16-supported-language template-bound tooling surface the criterion targets. N/A auto-passes per MP-4 precedent.

- **[N/A / no BLOCKING] MP-5 D7 cross-SPEC reconciliation**: `grep -Eo 'SPEC-([A-Z][A-Z0-9]+-)+[0-9]+' spec.md plan.md spec-compact.md` returns only self-references to `SPEC-API-001` (its own ID inside frontmatter/body); no other SPEC-ID is referenced anywhere in the document. D7 verification verb executed; no external SPEC-ID target exists to check status on, so no BLOCKING finding is possible. Marked N/A per the "verb not executable against a real target" precedent (MP-4 style).

- **[PASS] MP-6 D8 cross-platform discipline**: `grep -n 'syscall' spec.md plan.md spec-compact.md` returns zero matches. D8 auto-PASS per D8-4 (no `syscall` mention → no cross-platform discipline concern).

- **[PASS] MP-7 clarification gate**: `grep -rn '\[NEEDS CLARIFICATION' .moai/specs/SPEC-API-001/plan.md` returns zero matches. `research.md` does not exist for this Tier S SPEC (expected — Tier S input contract is spec.md + plan.md only), so only plan.md was checked; it carries no unresolved markers.

**Must-pass firewall verdict**: MP-2 FAILS → overall `Verdict: FAIL` per M5 (a single must-pass failure cannot be compensated by other scores, no matter how the aggregate computes).

## Category Scores (0.0-1.0, rubric-anchored)

| Dimension | Score | Rubric Band | Evidence |
|-----------|-------|-------------|----------|
| Clarity | 0.75 | 0.75 — minor ambiguity in one or two requirements a reasonable engineer resolves consistently | spec.md:L44 (REQ-003 blends a Ubiquitous "always respond null" clause with an embedded Unwanted "shall not substitute pct_from_52w_high" clause inside one REQ-ID — grammatically readable but structurally mixed); spec.md:L60 (REQ-009 tagged `[Where]` but the sentence is not bolded/marked as a `**Where**`-triggered conditional the way `**When**`/`**While**` REQs are — the capability-gate semantics are present in substance but the formatting is inconsistent with the rest of §2) |
| Completeness | 1.0 | 1.0 — all required sections present, frontmatter complete, Out-of-Scope with H3 sub-headings + bullets | spec.md:L17-22 (HISTORY), L25-34 (Overview/WHY+WHAT), L36-78 (REQUIREMENTS), L80-102 (ACCEPTANCE CRITERIA, Tier S inline), L110-131 (six `### Out of Scope — <topic>` H3 sub-headings, each with `-` bullets) |
| Testability | 0.75 | 0.75 — one AC not precisely binary-testable but measurable with minor interpretation | spec.md:L102 — AC-010's Then-clause "각 행에 데이터 기준일이 사용자에게 보이는 형태로 표시된다" ("displayed in a visible form") lacks a precise assertion target (no specific selector/format named), unlike AC-001/AC-002/AC-004 which name exact values/status codes. The other 9 ACs are binary-testable with a specific HTTP call + assertion or a specific DOM/state check. |
| Traceability | 0.50 | 0.50 — multiple REQs lack ACs | Four of sixteen REQs have no dedicated AC: **REQ-006** (spec.md:L52, 404 for an allow-listed code whose report file is missing — distinct from AC-004, which only covers a code outside the allow-list / REQ-007) has no AC; **REQ-008** (spec.md:L56, Unwanted — no DART/pykrx trigger) has no AC; **REQ-009** (spec.md:L60, frontend uses existing `NEXT_PUBLIC_API_URL`/default) has no AC; **REQ-014** (spec.md:L72, report_url null → hide/disable link) has no AC — AC-008 only covers the report_url-exists case, not the null case. AC list is spec.md:L84-102. |

## Independent Fact-Verification (adversarial spot-checks, not self-reported)

1. **plan.md line-number citations — VERIFIED ACCURATE.**
   - `backend/app/main.py:56-92` — actual lines 56 (`@app.post("/api/report/notion")`) through 92 (`return {"ok": True, ...}`) span exactly the `save_report_to_notion` route plan.md names as the style reference (plan.md:L32, L82). Confirmed by direct read of `backend/app/main.py`.
   - `backend/app/main.py:49-53` — actual lines 49-53 are the `StockReportRequest` Pydantic model body (`class StockReportRequest(BaseModel): code / name / price / change`), matching plan.md:L25's claim.
   - `frontend/src/app/dashboard/page.tsx:54-60` — actual lines 54-60 are exactly the GitHub-issues `useEffect` (`fetch(...).then(r => r.json()).then(...).catch(...).finally(...)`), matching plan.md:L46, L83's claim verbatim.
   - `frontend/src/app/dashboard/page.tsx:143` (plan.md:L48, "`MOCK_STOCKS.map(...) → stocks.map(...)`") — actual line 143 is `{MOCK_STOCKS.map(s => (`, confirming the citation.
   - Minor inaccuracy (not a line-number error): plan.md:L15 quotes `docs/setup/ONBOARDING.md:156-157` as `cd backend && uvicorn app.main:app --reload` (implying one joined command). The actual file has these as two separate lines (`ONBOARDING.md:156` = `cd backend`, `:157` = `uvicorn app.main:app --reload`, no `&&`). The underlying technical claim (backend runs with cwd=`backend/`) is correct; only the backtick-quoted rendering falsely implies a verbatim single-line quote. See D6 below.
   - `.github/workflows/ci.yml:28` (`pip install -r backend/requirements.txt ruff pytest`) and `:42` (`pytest backend/tests/ -v`) — both verified exact-match via `grep -n` against the live workflow file. plan.md's "synergy note" (M6, plan.md:L63) claim that `backend/tests/` does not currently exist and `pytest` is not in `backend/requirements.txt` was independently confirmed (`ls backend/tests` → not found; `grep -i pytest backend/requirements.txt` → no match).

2. **Data-shape claims in spec.md §4 — VERIFIED for all 4 in-scope tickers (task asked for ≥2; all 4 checked).**
   - `data/{code}_fundamentals.json` keys for `005930` and `000660`: `['stock_code', 'corp_code', 'fetched_at', 'source', 'unit', 'annual', 'quarterly']` — exact match to spec.md:L106's claimed shape.
   - `data/{code}_market.json` for `005930`, `000660`, `009150`, `008490`: all four carry `stock_code, as_of, fetched_date, source, current_price, high_52w, pct_from_52w_high, ...` exactly as spec.md:L107 claims (plus additional volume/flow fields the spec's `...` correctly elides).

3. **"All 4 tickers have fundamentals + market + ≥1 report" claim — VERIFIED TRUE.**
   - `data/`: `005930_fundamentals.json` + `005930_market.json`, `000660_fundamentals.json` + `000660_market.json`, `009150_fundamentals.json` + `009150_market.json`, `008490_fundamentals.json` + `008490_market.json` — all 8 files present.
   - `outputs/`: `005930_report_2026-07-10.html`, `000660_report_2026-07-10.html`, `009150_report_2026-07-10.html`, `008490_report_2026-07-10.html` — all 4 present. AC-003's cited filename (`outputs/005930_report_2026-07-10.html`) matches the real file exactly.

4. **GEARS pattern correctness — see MP-2 above** (the primary defect) plus the REQ-009 formatting inconsistency noted under Clarity.

5. **Internal consistency (spec.md requirements/exclusions vs. plan.md milestones) — VERIFIED CONSISTENT.** plan.md's M1-M6 implement REQ-001 through REQ-016 without introducing anything spec.md excludes (no new DART/pykrx collection, no report regeneration, no ticker-scope expansion, no auth, no schema changes). REQ-004's field list (`code, name, current_price, daily_change_pct, as_of, fetched_date, report_url`) matches plan.md M1's `StockSummary` model field-for-field.

6. **Acceptance criteria testability — 9/10 clean, 1 borderline** (see Testability score above; AC-010 is the borderline case).

## Defects Found (structured defect-list)

D1. **MP-2-EVENT-DETECTED** — spec.md:L52,L54,L64 — REQ-006, REQ-007, REQ-011 use the bracketed tag `[Event-detected]`, which is not one of the five canonical GEARS/EARS pattern names (Ubiquitous/Event-driven/State-driven/Where/Unwanted). — Severity: **critical** — Class: **blocking** — Required fix: Re-tag REQ-006, REQ-007, and REQ-011 as `[Event-driven]` (their grammar already matches "When [trigger], the system shall [response]" and error-path responses are a normal Event-driven case — GEARS does not have a separate "detected" sub-category).

D2. **TIER-BUDGET-EXCEEDED** — spec.md:L1-131 — The SPEC is frontmatter-tagged `tier: S`, whose REQ ceiling is 8 and AC ceiling is 8 (`.claude/rules/moai/workflow/spec-workflow.md` § SPEC Complexity Tier). This SPEC carries 16 REQs (REQ-001..016) and 10 ACs (AC-001..010) — double the REQ ceiling and 125% of the AC ceiling. This is an over-formalization signal the Tier taxonomy exists to catch; the actual REQ/AC volume fits Tier M's ceiling (16/16), not Tier S's (8/8). — Severity: **major** — Class: **blocking** — Required fix: Re-tier the SPEC to `tier: M` (which also mandates a separate `acceptance.md` per the Tier M 3-file artifact set) OR split the SPEC into two Tier-S-sized SPECs (e.g., backend-endpoint SPEC + frontend-integration SPEC), each within the 8/8 ceiling.

D3. **TRACEABILITY-GAP** — spec.md:L52 (REQ-006), L56 (REQ-008), L60 (REQ-009), L72 (REQ-014) — Four REQs have no dedicated AC (see Traceability score evidence above for the per-REQ detail; AC-004 and AC-008 are each mistakenly reusable-looking but do not actually cover REQ-006 or REQ-014's specific scenario). — Severity: major — Class: blocking — Required fix: Add AC-011 (REQ-006: allow-listed code + missing report file → 404), AC-012 (REQ-014: report_url null → link hidden/disabled), and either add explicit ACs for REQ-008/REQ-009 or explicitly note in §3 that they are non-HTTP-observable constraints validated by code review rather than AC (and state that rationale in the SPEC, not silently).

D4. **RQ-4-IMPL-DETAIL** — spec.md:L42 (REQ-002) — REQ-002 names the exact Python variable and type-hint (`STOCK_NAMES: dict[str, str]`) inside the requirement text — this is a HOW-level implementation detail (variable name + language-specific type annotation), not a WHAT/WHY requirement statement. — Severity: minor — Class: blocking (this is a rubric criterion the checklist explicitly names, RQ-3/RQ-4) — Required fix: Rephrase as "백엔드는 종목명 조회를 위해 4개 코드에 한정된 정적 매핑을 사용하며, 범용 종목명 조회/검색 서비스를 두지 않는다." — leave the concrete Python type to plan.md M1 (which already restates it correctly at plan.md:L26).

D5. **CLARITY-REQ003-COMPOUND** — spec.md:L44 (REQ-003) — REQ-003 mixes a Ubiquitous clause ("daily_change_pct는 항상 null") with an embedded Unwanted clause ("pct_from_52w_high 값을 등락률로 대체 제공하지 않는다") inside a single REQ-ID. — Severity: minor — Class: optional — Required fix (optional): Split into REQ-003a (Ubiquitous: always null) and REQ-003b (Unwanted: shall not substitute pct_from_52w_high) if stricter one-pattern-per-REQ discipline is desired; not required for correctness since both halves are independently unambiguous.

D6. **CITATION-PARAPHRASE** — plan.md:L15 — The citation `docs/setup/ONBOARDING.md:156-157`: `cd backend && uvicorn app.main:app --reload` renders as if it were a verbatim two-line quote joined by `&&`; the actual file has these as two independent lines with no `&&`. The underlying technical claim is correct. — Severity: minor — Class: optional — Required fix (optional): Either quote the two lines separately or drop the `&&` to avoid implying a verbatim single-command quote.

D7. **TESTABILITY-AC010-VAGUE** — spec.md:L102 (AC-010) — "각 행에 데이터 기준일(...)이 사용자에게 보이는 형태로 표시된다" does not name a specific selector, format, or assertion target, unlike the other 9 ACs. — Severity: minor — Class: optional — Required fix (optional): Tighten to "Then 각 행에 `as_of` 또는 `fetched_date` 값이 텍스트로 렌더링되어 DOM에서 조회 가능하다" or equivalent.

## Regression Check (Iteration 2+ only)

N/A — this is iteration 1.

## Recommendation

Verdict is FAIL due to a must-pass firewall violation (MP-2). Fix instructions for manager-spec, in priority order:

1. **(Must-pass, blocking)** Re-tag REQ-006, REQ-007, REQ-011 from `[Event-detected]` to `[Event-driven]` (spec.md:L52, L54, L64, mirrored in spec-compact.md:L23, L25, L33). No grammar change needed — only the bracketed label.
2. **(Blocking)** Resolve the Tier-S REQ/AC budget overrun (D2): either re-tier to Tier M and add `acceptance.md`, or split the SPEC into two Tier-S SPECs.
3. **(Blocking)** Close the four traceability gaps (D3) by adding AC-011/AC-012 (or equivalent) for REQ-006 and REQ-014, and explicitly address REQ-008/REQ-009's AC status.
4. **(Blocking per rubric)** Rephrase REQ-002 to remove the Python type-hint/variable-name implementation detail (D4).
5. **(Optional)** Consider splitting REQ-003 (D5), tightening AC-010's assertion target (D7), and correcting the ONBOARDING.md citation format in plan.md (D6) — these do not block a PASS on their own but improve overall quality.

Re-audit scope for iteration 2 (per the Retry Loop Contract): verify D1-D4 are resolved (blocking) and check whether D5-D7 (optional) were addressed at manager-spec's discretion; this is a defect-delta re-audit, not a from-scratch review.
