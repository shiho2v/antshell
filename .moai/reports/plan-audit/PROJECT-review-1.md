# Plan Audit Report — /moai project (iteration 1)

Document type: project
Files audited: `.moai/project/product.md`, `.moai/project/structure.md`, `.moai/project/tech.md`
Harness level: minimal (auto-detected: file_count<=3, spec_type=docs)
Gate mode: `plan_audit_global.always_enabled: true` (forced regardless of level); `require_must_pass: false` at minimal (advisory, non-blocking)
Auditor: plan-auditor (context-isolated — no interview/analysis reasoning passed in)

## Verification method

~40 factual claims independently re-derived from the live repository (not trusted from the documents' own citations): FastAPI route count/paths, frontend mock-data claim, 3 declared-but-unused dependencies, CI failure mode, line/file counts, external-system credential names, scope-boundary compliance (`.moai/specs/` emptiness).

Result: every spot-checked claim held up, several down to the exact line number.

## Defects found (all advisory — fixed same session)

| ID | Severity | File | Issue | Status |
|---|---|---|---|---|
| D1 | Major | product.md | "두 축(pillar)" calque — matches the prohibited pattern in `native-idiom-and-register.md` hazard list | Fixed |
| D2 | Minor | product.md | "이음매(seam)" — same calque family | Fixed |
| D3 | Minor | tech.md | Line-range citation off by ~3 lines (`log_session_end.py:33-43` → `:30-43`) | Fixed |
| D4 | Minor | structure.md | `portfolio-team.yaml` referenced but not listed in the directory table | Fixed |
| D5 | Minor | tech.md | Quotation marks implied a verbatim quote from ENV_GUIDE.md that was actually a paraphrase | Fixed |
| D6 | Minor | product.md | Pipeline-generality claim stated more confidently than evidence supports | Fixed |

## Verdicts

| File | Verdict |
|---|---|
| product.md | PASS (defects D1, D2, D6 — fixed) |
| structure.md | PASS (defect D4 — fixed) |
| tech.md | PASS (defects D3, D5 — fixed) |

Verdict: PASS

No factual, fabricated, or scope-violating claim found across ~40 independently re-derived checks. `.moai/specs/` confirmed empty (scope boundary respected). All six advisory defects fixed post-audit; no re-audit iteration required (non-blocking level).
