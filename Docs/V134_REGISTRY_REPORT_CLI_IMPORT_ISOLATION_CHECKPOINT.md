# V1.34 Registry Report CLI Import Isolation Checkpoint

## Purpose

Record the passive CLI import-isolation hardening for the registry report
formatter.

The CLI now lazy-loads the registry report formatter only when the passive
`report` command is invoked.

## Current Clean Baseline

Current branch:

- `modularize-v1.34`

Current HEAD before this checkpoint:

- `a0ffe67 Lazy-load registry report CLI formatter`

Upstream checkpoint:

- `4901cf5 Update checkpoint after runtime report import isolation`

## Milestone Summary

`rytm_randomizer.cli` no longer imports this module during plain CLI import:

- `rytm_randomizer.registry_report`

The formatter remains available through the existing passive command:

- `python -m rytm_randomizer.cli report`

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

- `python -m pytest tests/test_cli.py::test_importing_cli_does_not_load_registry_report_module tests/test_cli.py::test_report_command_exits_zero_and_matches_fixture -q`
- `python -m pytest tests/test_cli.py -q`
- `python tests\test_cli.py`

Full closeout:

- `powershell -ExecutionPolicy Bypass -File .\Scripts\closeout_check.ps1`

Additional protection checks:

- `git diff -- rytm_hybrid_randomizer_v134.py`
- `git diff -- pyproject.toml requirements.txt setup.py setup.cfg`
- `git diff --check`

## Decision

All current report-only CLI formatters are now loaded by their specific command
branches rather than plain CLI import. This keeps the passive CLI import
surface smaller and easier to audit.

## Next Recommended Task

Pause the import-isolation thread unless a new concrete drift appears. The next
useful branch should be either a short import-boundary progress summary or a
different test-backed behavior-parity alignment slice.
