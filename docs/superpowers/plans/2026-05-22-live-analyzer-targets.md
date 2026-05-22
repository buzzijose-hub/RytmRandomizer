# Live Analyzer Targets

## Goal

Add one passive, mock-safe report that composes the live analyzer handoff into rehearsal targets for future GUI/audio-analyzer comparison.

## Scope

- Add `style-performance-arc-live-analyzer-targets-report` as a passive CLI command.
- Consume the existing live analyzer handoff rather than bypassing the report stack.
- Emit target bands, cue checkpoints, calibration steps, warning thresholds, replayable passive commands, and deterministic JSON.
- Preserve the existing safety boundary: no MIDI imports, no port opening, no sends, no file writes.

## Files

- `rytm_randomizer/reports/live_analyzer_targets.py`
- `rytm_randomizer/cli.py`
- `rytm_randomizer/help_text.py`
- `tests/test_live_analyzer_targets_report.py`
- CLI/help/safety/docs fixtures and docs touched by the new command.

## Verification

- `python -m pytest tests\test_live_analyzer_targets_report.py -n 0`
- `python -m pytest tests\test_live_analyzer_targets_report.py tests\test_live_analyzer_handoff_report.py tests\test_live_control_surface_report.py tests\test_cli_coverage.py tests\test_real_midi_passive_cli_safety.py -q`
- `python -m pytest tests\test_cli.py -q`
- `python -m pytest tests\architecture\ -q`
- `python -m pytest -m fast`
- `python -m pytest`
- `python -m pytest --cov=rytm_randomizer --cov-branch --cov-report=term-missing`
- `python -m ruff check .`
- `python -m black --check --target-version=py311 .`
- `python -m isort --profile black --check-only .`

## Gate Notes

- Gate 1 coverage: new report covered by direct unit/CLI tests.
- Gate 2 integration: composes the existing analyzer handoff and CLI registry.
- Gate 3 passive safety: safety tests assert no real MIDI imports/ports.
- Gate 4 docs: README, status, manual validation, style analysis, and diagrams mention the new report.
- Gate 5 parity: V1.34 engine/group/scene behavior untouched.
- Gate 16 PR shape: single clean-base feature branch from `origin/modularize-v1.34`.
