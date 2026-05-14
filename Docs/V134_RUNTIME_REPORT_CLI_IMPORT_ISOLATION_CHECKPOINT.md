# V1.34 Runtime Report CLI Import Isolation Checkpoint

## Purpose

Record the passive CLI import-isolation hardening for runtime and bridge report
formatters.

The CLI now lazy-loads runtime/bridge report formatters only when their
specific passive report commands are invoked.

## Current Clean Baseline

Current branch:

- `modularize-v1.34`

Current HEAD before this checkpoint:

- `aa198d8 Lazy-load runtime report CLI formatters`

Upstream checkpoint:

- `f2db03f Update checkpoint after behavior report import isolation`

## Milestone Summary

`rytm_randomizer.cli` no longer imports these modules during plain CLI import:

- `rytm_randomizer.runtime_plan_report`
- `rytm_randomizer.runtime_plan`
- `rytm_randomizer.mock_runtime_active_bridge_report`
- `rytm_randomizer.mock_runtime_active_bridge`

The formatters remain available through their existing passive commands:

- `python -m rytm_randomizer.cli runtime-plan-report`
- `python -m rytm_randomizer.cli mock-runtime-active-bridge-report`

## Files Changed By The Milestone

- `rytm_randomizer/cli.py`
- `tests/test_cli.py`

## Safety Boundaries

- no CLI output change
- no fixture change
- no command behavior change
- no runtime execution
- no bridge invocation from plain CLI import
- no dispatch
- no command execution
- no mutation execution
- no active CLI command
- no MIDI dependency
- no port discovery
- no port opening
- no MIDI sending
- no package metadata change
- no hardware behavior
- `rytm_hybrid_randomizer_v134.py` remains untouched

## Verification

Focused verification:

- `python -m pytest tests/test_cli.py::test_importing_cli_does_not_load_runtime_or_bridge_report_modules tests/test_cli.py::test_runtime_plan_report_command_exits_zero_and_matches_fixture tests/test_cli.py::test_mock_runtime_active_bridge_report_command_exits_zero_and_matches_fixture tests/test_cli.py::test_mock_runtime_active_bridge_report_command_does_not_load_bridge_or_mock_midi -q`
- `python -m pytest tests/test_cli.py -q`
- `python tests\test_cli.py`

Full closeout:

- `powershell -ExecutionPolicy Bypass -File .\Scripts\closeout_check.ps1`

Additional protection checks:

- `git diff -- rytm_hybrid_randomizer_v134.py`
- `git diff -- pyproject.toml requirements.txt setup.py setup.cfg`
- `git diff --check`

## Decision

Runtime/bridge report CLI formatter imports are now isolated behind their own
passive report commands. Plain CLI import stays lighter and avoids loading
runtime planning or bridge report modules unnecessarily.

## Next Recommended Task

Continue scanning for concrete passive import-boundary or report/helper drift.
Prefer test-backed hardening slices over automatic review gates.
