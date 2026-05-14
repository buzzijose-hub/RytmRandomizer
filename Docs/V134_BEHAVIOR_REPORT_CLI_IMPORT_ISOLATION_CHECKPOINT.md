# V1.34 Behavior Report CLI Import Isolation Checkpoint

## Purpose

Record the passive CLI import-isolation hardening for behavior report
formatters.

The CLI now lazy-loads the heavier behavior report formatters only when their
specific report commands are invoked.

## Current Clean Baseline

Current branch:

- `modularize-v1.34`

Current HEAD before this checkpoint:

- `ab492ad Lazy-load behavior report CLI formatters`

Upstream checkpoint:

- `11a7022 Update checkpoint after structured Packet 11 summary count`

## Milestone Summary

`rytm_randomizer.cli` no longer imports these modules during plain CLI import:

- `rytm_randomizer.behavior_anchor_profile_report`
- `rytm_randomizer.behavior_parity_coverage_report`
- `rytm_randomizer.behavior_selected_isolated_pad`
- `rytm_randomizer.selected_isolated_pad_runtime_state`

The formatters remain available through their existing passive commands:

- `python -m rytm_randomizer.cli anchor-profile-report`
- `python -m rytm_randomizer.cli behavior-parity-report`

## Files Changed By The Milestone

- `rytm_randomizer/cli.py`
- `tests/test_cli.py`

## Safety Boundaries

- no CLI output change
- no fixture change
- no command behavior change
- no runtime execution
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

- `python -m pytest tests/test_cli.py::test_importing_cli_does_not_load_behavior_report_modules tests/test_cli.py::test_anchor_profile_report_command_imports_no_real_midi_libraries tests/test_cli.py::test_behavior_parity_report_command_imports_no_real_midi_libraries tests/test_cli.py::test_behavior_parity_report_command_exits_zero_and_matches_fixture -q`
- `python -m pytest tests/test_cli.py -q`
- `python tests\test_cli.py`

Full closeout:

- `powershell -ExecutionPolicy Bypass -File .\Scripts\closeout_check.ps1`

Additional protection checks:

- `git diff -- rytm_hybrid_randomizer_v134.py`
- `git diff -- pyproject.toml requirements.txt setup.py setup.cfg`
- `git diff --check`

## Decision

Behavior report CLI formatter imports are now isolated behind their own passive
report commands. This keeps plain CLI import lighter and makes accidental
report-helper loading easier to catch.

## Next Recommended Task

Continue scanning for concrete passive import-boundary or report/helper drift.
Prefer test-backed hardening slices over automatic review gates.
