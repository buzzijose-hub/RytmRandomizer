# Rytm 12-Pad Engine Matrix Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: use
> superpowers:test-driven-development and superpowers:verification-before-completion.

**Goal:** Add a passive Rytm 12-pad engine matrix report that makes the legal
pad/engine table and runtime support levels explicit.

## Tasks

- [ ] Add failing tests for a new `rytm_12_pad_engine_matrix` module:
  import safety, matrix counts, Pad 10 OH guard, Pads 6-8 XT guard, report
  content, and CLI output.
- [ ] Implement `rytm_randomizer/essence/rytm_12_pad_engine_matrix.py` using
  `machine_catalog` and `ENGINE_SOURCE_STARTERS`.
- [ ] Wire `rytm-12-pad-engine-matrix-report` into `cli.py`, `help_text.py`,
  `tests/test_cli.py`, and `tests/fixtures/cli_help_expected.txt`.
- [ ] Update `docs/STATUS.md` with the milestone.
- [ ] Run focused tests, architecture tests, fast tests, formatting/lint, and
  `git diff --check`.
- [ ] Commit and push the branch.

## Verification Commands

```powershell
python -m pytest tests/test_rytm_12_pad_engine_matrix.py tests/test_cli.py::test_rytm_12_pad_engine_matrix_report_help_exits_zero tests/test_cli.py::test_top_level_help_exits_zero_and_matches_fixture -q -n 0
python -m pytest tests/test_machine_catalog.py tests/test_rytm_engine_cycle_plan.py tests/test_twelve_pad_rytm_runtime.py tests/test_rytm_12_pad_engine_matrix.py -q -n 0
python -m pytest tests/architecture -q -n 0
python -m pytest -m fast -q -n 0
python -m ruff check .
python -m isort --check-only --profile black rytm_randomizer tests
git diff --check
```
