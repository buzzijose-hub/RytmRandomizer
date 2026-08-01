# 100% branch coverage on touched files (Gate 1)

**Authority:** `docs/PLAN_REQUIREMENTS.md` Gate 1.
**Scope:** Every workstream that touches `rytm_randomizer/*.py`.

## The rule

New or modified production code reaches 100% **branch** coverage (not line coverage) on the set of files the WS actually touched. The ratcheted whole-package floor in `.coveragerc` (currently `fail_under = 98`) is a separate, weaker gate; this gate is stricter and per-WS.

## How to compute and run

```bash
# 1. Compute the touched-file set against the base branch.
touched=$(git diff --name-only origin/modularize-v1.34...HEAD -- 'rytm_randomizer/*.py')

# 2. Turn each path into a coverage source argument (path -> dotted module).
cov_args=$(for f in $touched; do
  printf -- '--cov=%s ' "$(echo "$f" | sed -e 's#/#.#g' -e 's#\.py$##')"
done)

# 3. Run with branch coverage AND fail-under set to 100.
.venv/bin/python -m pytest $cov_args --cov-branch --cov-fail-under=100 --cov-report=term-missing
```

If `--cov-fail-under=100` fails, the orchestrator re-dispatches `tdd-guide` with the missing-branch output. Max 2 retries before escalating to `architect`.

## Why branch coverage, not line coverage

Branch coverage catches the corner cases the duck-typed boundaries currently let slip:

- `if resolved_bounds is None` — a line-coverage tool sees the function executed and reports green even if the `is None` branch never fires.
- `if depth == 0` — same; line coverage misses the boundary.
- `try: ... except X: ...` — line coverage misses the `except` arm if no test triggers the exception.

Branch coverage forces every conditional to be exercised in **both** directions.

## `# pragma: no cover` policy

Any `# pragma: no cover` requires a one-line justification comment immediately above it, pointing at either:

- `docs/ARCHITECTURE.md` §8 (the parity API surface — some symbols exist for V1.34 compatibility and have no live caller), OR
- A specific incident in `docs/SIMPLIFICATION_RUN_LOG.md`.

Without the justification, the architecture test `tests/architecture/test_no_unjustified_pragma_no_cover.py` (when WS-S8 lands) fails the build.

## Cross-references

- `docs/PLAN_REQUIREMENTS.md` Gate 1 — canonical rule definition.
- `docs/COVERAGE_POLICY.md` — whole-package ratchet policy.
- `.coveragerc` — the ratcheted package-wide floor (currently 98%; `scripts/coverage_ratchet.py` only ever moves it up).
- `.claude/skills/learned/coverage-py-blended-vs-pure-branch/` — why pure-branch and blended numbers disagree.
