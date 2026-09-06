---
name: hns-study-week-preflight-verify
description: >
  Runnable build/launch/test recipe for the antshell repository, discovered
  once by direct inspection on 2026-09-06 and codified here so the
  study-week-preflight harness (and any human maintaining it) never has to
  re-derive how to build, lint, and test this project from scratch. Covers
  the frontend (Next.js) toolchain, the backend (FastAPI) toolchain, and the
  two analysis-pipeline pytest suites that .github/workflows/ci.yml currently
  never runs. Use when confirming the repository is in a working state, when
  the study-week-preflight harness's quality-gate-probe specialist needs a
  ground-truth recipe to compare CI configuration against, or when the
  toolchain changes and this recipe needs updating.
license: Apache-2.0
compatibility: Designed for Claude Code
allowed-tools: Read, Bash
metadata:
  version: "1.0.0"
  category: "domain"
  status: "active"
  updated: "2026-09-06"
  modularized: "false"
  tags: "verify, build-recipe, ci, pytest, ruff, next.js, antshell"
  author: "hns-study-week-preflight harness (GENERATE phase)"
  related-skills: "hns-study-week-preflight-conventions"

progressive_disclosure:
  enabled: true
  level1_tokens: 120
  level2_tokens: 1500

triggers:
  keywords: ["verify", "build recipe", "test suite", "ruff", "pytest", "ci drift", "state check", "is antshell working"]
  agents:
    - hns-study-week-preflight-quality-gate-probe-specialist
    - hns-study-week-preflight-readiness-brief-specialist
  phases: ["run"]
---

# Study-Week Preflight Verify

## Quick Reference

Recipe discovered ONCE this session (2026-09-06) via direct repo inspection — NOT assumed, NOT copied from documentation. If the toolchain changes (new lint tool, new test runner, restructured directories), re-discover and update this file rather than trusting it blindly.

| Stage | Command | Discovered from |
|---|---|---|
| 1. Frontend install+lint+build | `cd frontend && npm ci && npm run lint && npm run build` | `frontend/package.json` scripts block |
| 2. Backend install+lint | `pip install -r backend/requirements.txt && ruff check backend/` | `.github/workflows/ci.yml` |
| 3. Analysis-pipeline tests (CI never runs these) | `python3 -m pytest .claude/skills/generating-krx-report/tests/ .claude/skills/converting-investment-blog/tests/ -q` | Direct discovery — no CI reference exists |
| State check | See § State check below | — |

## Implementation Guide

### Stage 1 — Frontend (Next.js)

From a clean checkout, run from the repo root:

```bash
cd frontend && npm ci && npm run lint && npm run build
```

- `npm ci` — installs pinned dependencies from `frontend/package-lock.json`. Success: exits 0 with no `npm ERR!` lines. Failure: a missing/corrupt lockfile, or a registry error, exits non-zero.
- `npm run lint` — runs `next lint` (defined in `frontend/package.json` `scripts.lint`). Success: `✔ No ESLint warnings or errors` (or similar) and exit 0. Failure: ESLint reports violations and exits non-zero.
- `npm run build` — runs `next build`. Success: a `.next/` production build completes with a route summary table and exit 0. Failure: a TypeScript or build error, non-zero exit.

This exact 3-command sequence matches `.github/workflows/ci.yml`'s `Frontend 의존성 설치` → `Frontend 린트` → `Frontend 빌드 확인` steps (working-directory: `frontend`), so this stage should reproduce CI's frontend gate locally.

### Stage 2 — Backend (FastAPI)

From the repo root:

```bash
pip install -r backend/requirements.txt && ruff check backend/
```

- `pip install -r backend/requirements.txt` — installs `fastapi==0.111.0`, `uvicorn[standard]==0.30.1`, `python-jose[cryptography]==3.3.0`, `httpx==0.27.0`, `python-dotenv==1.0.1` (all pinned). Success: exits 0. Failure: a dependency-resolution conflict or network error, non-zero.
- `ruff check backend/` — lints the `backend/app/` source tree.

**Known gap in this recipe (flagged, not silently papered over)**: `ruff` itself has **no pinned version anywhere in this repository** — `backend/requirements.txt` does not list it, and `.github/workflows/ci.yml`'s `Python 의존성 설치` step installs it unpinned (`pip install -r backend/requirements.txt ruff pytest`). This means Stage 2's lint result can drift between runs as `ruff` releases new versions with new default rules — a CI run today and a CI run next month are not guaranteed to lint identically. The quality-gate-probe specialist should surface this as a finding (pin `ruff` to an exact version in `backend/requirements.txt` or a `requirements-dev.txt`) rather than assume lint stability.

**Second known gap, discovered directly (not from CI, since CI itself carries this drift)**: `.github/workflows/ci.yml`'s `Backend 테스트` step runs `pytest backend/tests/ -v`, but **`backend/tests/` does not exist on disk** — the `backend/` directory contains only `app/` and `requirements.txt`. This means the CI backend-test step, as configured today, fails or vacuously no-ops depending on the pytest/CI runner's handling of a missing test path. This recipe intentionally does NOT include a `pytest backend/tests/` command, because there is nothing to run — the gap belongs to CI configuration drift, which is exactly what `hns-study-week-preflight-quality-gate-probe-specialist` exists to catch. Do not add a `backend/tests/` invocation to this recipe until that directory is created and populated.

### Stage 3 — Analysis-pipeline tests (the gap this harness exists to close)

`.github/workflows/ci.yml` never runs the two test suites that actually cover the KRX-report-generation and blog-conversion pipelines. They live under `.claude/skills/`, outside any path CI touches:

```bash
python3 -m pytest .claude/skills/generating-krx-report/tests/ .claude/skills/converting-investment-blog/tests/ -q
```

Run this from the repository root. Both suites were verified this session to be pytest-collectible from a single invocation with no conflict:

- `.claude/skills/generating-krx-report/tests/test_units.py` and `test_fixtures.py` are written as stdlib `unittest.TestCase` subclasses. pytest natively collects and runs `unittest.TestCase` classes, so no `unittest`-vs-`pytest` runner mismatch exists. Both files insert `SKILL_ROOT/scripts` (the same directory, `.claude/skills/generating-krx-report/scripts/`) onto `sys.path` at import time before importing local modules (`_common`, `calculate_metrics`, `normalize_data`, `score_modules`, `validate_evidence`, `validate_report`, `build_evidence_packs`) — this is self-contained to the one directory and does not collide with the other suite.
- `.claude/skills/converting-investment-blog/tests/test_validate_blog_post.py` is written as native `pytest` (fixtures via `@pytest.fixture`, plain `def test_*` functions). It does NOT manipulate `sys.path` to import pipeline modules directly — it invokes `validate_blog_post.py` via `subprocess`, referencing `SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "validate_blog_post.py"`. Because it never imports a same-named module as the other suite, there is no `sys.path` collision between the two directories.

**Success**: pytest reports all collected tests passing (e.g. `N passed in X.XXs`), exit 0. **Failure**: any `F` (failed) or `E` (error) in the summary, non-zero exit — read the traceback for which module/fixture broke.

**Environment gap flagged**: at the time this recipe was discovered (2026-09-06), this session's own execution environment has no `pytest` installed (`ModuleNotFoundError: No module named 'pytest'` on `python3 -c "import pytest"`), so Stage 3 could not be executed end-to-end to confirm a passing run — only static inspection (imports, fixture usage, `sys.path` handling) was used to establish collectibility. The command above should be run in an environment with `pytest` installed (e.g. `pip install pytest` first, or whatever environment CI would use if this stage were added to `ci.yml`) before trusting a green result.

### State check

A single check (run from the repo root) that confirms the repository is in a working state right now:

```bash
git status --short && \
cd frontend && npm run lint --silent && cd .. && \
python3 -m pytest .claude/skills/generating-krx-report/tests/ .claude/skills/converting-investment-blog/tests/ -q
```

- `git status --short` — should print nothing (clean tree) or only expected in-flight changes; a large unexpected diff means something changed outside a tracked workflow.
- `npm run lint --silent` (frontend) — the fastest of the three stages; a quick canary for frontend regressions without paying the full `npm run build` cost.
- The analysis-pipeline pytest invocation (Stage 3) — the two suites CI does not cover, so this state check is the only mechanical confirmation that the KRX-report and blog-conversion pipelines still work.

This state check deliberately omits the full `npm run build` and the backend `ruff check` — both are still part of the full recipe (Stages 1-2 above) and should be run before a release or a presenter's demo, but are heavier than what a quick "is this repo OK right now" check needs.

## Advanced

- **Why this recipe is not a stub**: `.claude/skills/moai/workflows/harness-builder.md` § Artifact 6 permits a documented "no recipe found" stub only when the project genuinely has no discoverable build/launch/test recipe. antshell has three independent, already-configured toolchains (`frontend/package.json` scripts, `.github/workflows/ci.yml`, and two pytest suites under `.claude/skills/`) — the stub condition does not apply here, so this file carries the full discovered recipe instead.
- **When to re-discover**: if `frontend/package.json`'s `scripts` block changes, if `.github/workflows/ci.yml` is edited, if `backend/requirements.txt` gains or loses dependencies, or if either `.claude/skills/*/tests/` directory is restructured, re-run the discovery process (read the relevant config file, re-derive the commands) and update this file — do not assume the recipe above stays accurate indefinitely.
- **Relationship to `hns-study-week-preflight-quality-gate-probe-specialist`**: that specialist checks whether CI configuration (`ci.yml`, `package.json` scripts) references paths that exist on disk. This skill's two flagged gaps (unpinned `ruff`, non-existent `backend/tests/`) are exactly the class of finding that specialist is built to surface — this skill supplies the ground-truth recipe it probes against, not a duplicate of its logic.
