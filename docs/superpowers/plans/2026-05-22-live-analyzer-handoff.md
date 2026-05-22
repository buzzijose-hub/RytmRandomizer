# Live Analyzer Handoff Report Plan

## Intent

Add one passive, mock-safe report that joins the reference-match evidence layer with the live control surface so future GUI/audio-analyzer work can consume a single rehearsal handoff packet.

## Scope

- Add `style-performance-arc-live-analyzer-handoff-report` as a passive CLI command.
- Accept exactly one reference input: `--description`, `--audio`, or `--library`.
- Require at least one saved-kit bank path (`--rytm` or `--analog-four`) so the live control surface can be built.
- Reuse the existing reference-match and live-control-surface reports instead of duplicating performance-arc planning.
- Emit text and deterministic JSON with FeatureReport meters, top influence matches, control-surface sync cards, next-cue sync cards, capture prompts, replayable passive commands, and safety lines.
- Do not open ports, import real MIDI eagerly, send MIDI, mutate hardware, or write files.

## Architecture

- Put the implementation in `rytm_randomizer/reports/live_analyzer_handoff.py`.
- Register through `CliCommand` and the lazy CLI module map.
- Keep all payloads immutable dataclasses with explicit types.
- Preserve the Device/Strategy boundary by only consuming passive reports and saved-kit paths.

## TDD Checks

- RED: focused tests for text output, JSON output, injected FeatureReport construction, and CLI argument validation.
- GREEN: build the report from existing passive reports.
- Regression coverage: CLI help, README command listing, and passive MIDI safety matrix.

## Verification Plan

- `python -m pytest tests\test_live_analyzer_handoff_report.py -n 0`
- `python -m pytest tests\test_live_analyzer_handoff_report.py tests\test_live_control_surface_report.py tests\test_cli.py tests\test_cli_coverage.py tests\test_real_midi_passive_cli_safety.py -q`
- `python -m pytest tests\architecture\ -q`
- `python -m pytest -m fast`
- `python -m pytest`
- `python -m pytest --cov=rytm_randomizer --cov-branch --cov-report=term-missing`
- `python -m ruff check .`
- `python -m black --check --target-version=py311 .`
- `python -m isort --profile black --check-only .`
- `python scripts\code_review_gate.py --mode cli`
- `python scripts\closeout_check.py`
- `git diff --check`

## Gate Notes

- Gate 1: touched implementation has branch coverage through focused report tests.
- Gate 2: no new top-level modules.
- Gate 3: no V1.34 parity output changed.
- Gate 4: no hardware or real MIDI boundary changes.
- Gate 5: docs and README updated with the new command.
- Gate 6: PR remains one logical change, not a stacked cascade.
