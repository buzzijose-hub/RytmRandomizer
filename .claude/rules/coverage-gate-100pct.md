# 100% branch coverage on touched files (Gate 1)

**Authority:** `docs/PLAN_REQUIREMENTS.md` Gate 1.
**Scope:** Every workstream that touches `rytm_randomizer/*.py`.

## The rule

New or modified production code reaches 100% **branch** coverage (not line coverage) on the set of files the WS actually touched. The ratcheted whole-package floor in `.coveragerc` (currently `fail_under = 98`) is a separate, weaker gate; this gate is stricter and per-WS.

## How to compute and run

Use the same script CI runs — `scripts/check_touched_coverage.py`, invoked
from `.github/workflows/test.yml`:

```bash
just gate1
# == python -m pytest --cov=rytm_randomizer --cov-branch --cov-report=xml -q
#    python scripts/check_touched_coverage.py coverage.xml
```

It computes the touched set from the diff, reads `coverage.xml`, and fails
listing every touched file with a missed line or partial branch. A touched
production file **absent** from the report fails too — an untested new
module is exactly what this gate exists to catch.

### Do not hand-roll a `--cov` command

The recipe this rule used to document did not work, and failed *silently*:

```bash
# BROKEN — kept here so nobody reinvents it.
cov_args=$(… --cov=<dotted.module> …)
python -m pytest $cov_args --cov-branch --cov-fail-under=100
```

`.coveragerc` declares `source = rytm_randomizer`, which overrides per-run
`--cov` arguments; the two combine to measure nothing. pytest-cov reports
"No data was collected" as a **warning**, so the command exits 0 and the
gate reads as satisfied. **A gate that cannot fail is not a gate** — and
this is the gate every contributor's work is judged against. Verified
broken on 2026-09-08.

Two related traps if you measure a single file ad hoc: pass
`--rcfile=/dev/null` so the repo config does not override the scope, and
keep the test files out of the measured set or `--fail-under` scores the
tests instead of the code.

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
