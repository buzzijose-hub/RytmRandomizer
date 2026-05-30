# Reference Arc Rehearsal Manifest PR24 Plan

## Why

PR23 added a passive audition packet that chooses the best available reference arc from saved Rytm and Analog Four kit banks. The next operator-facing step is a rehearsal manifest: a deterministic runbook that turns the selected arc into preflight checks, segment timing, machine summaries, and rehearsal actions before any live hardware send exists.

This moves the project closer to Jose's live goal without opening MIDI ports, mutating hardware, or introducing a new architecture surface.

## Scope

Add one passive report command:

```text
style-performance-arc-rehearsal-manifest-report
```

The command will:

- Reuse the existing reference-arc audition packet builder.
- Select the best-ready arc from saved kit banks.
- Emit a segment-by-segment rehearsal runbook with time windows, discovery amount, readiness, operator action, and Rytm/A4 preview summaries.
- Support `--events`, `--limit`, and `--json` in the same shape as the audition packet command.
- Remain read-only: no MIDI sends, no port opening, no hardware mutation.

## Files

- `rytm_randomizer/reports/style_performance_arcs.py`
- `rytm_randomizer/cli.py`
- `rytm_randomizer/help_text.py`
- `tests/test_style_performance_arcs_report.py`
- `tests/test_cli.py`
- `tests/fixtures/cli_help_expected.txt`
- `README.md`
- `docs/STATUS.md`

## TDD Tasks

1. Add failing report tests for the rehearsal manifest builder, formatter, and JSON.
2. Add failing parser/handler and CLI/help coverage.
3. Implement dataclasses and builder by wrapping the existing audition packet and selected set plan.
4. Implement formatter and JSON output.
5. Register CLI command and help text.
6. Update README/status docs.

## Verification

Focused:

```bash
python -m pytest tests/test_style_performance_arcs_report.py -n 0
python -m pytest tests/test_cli.py tests/test_cli_coverage.py tests/test_real_midi_passive_cli_safety.py -n 0
```

Full:

```bash
python -m ruff check .
python -m black --check --target-version=py311 .
python -m isort --profile black --check-only .
python -m pytest tests/architecture/ -q
python -m pytest -m fast
python -m pytest
python -m pytest --cov=rytm_randomizer --cov-branch --cov-report=term-missing
python scripts\code_review_gate.py --mode cli
```

## Plan Gates

- Gate 1: touched Python files remain covered by focused and coverage runs.
- Gate 2: V1.34 parity is not intentionally changed; no fixture regeneration.
- Gate 3: passive CLI only; no real MIDI boundary touched.
- Gate 4: no hardware packages changed.
- Gate 5: no new top-level package or device-family package.
- Gate 6: no `Any` escape hatches.
- Gate 7: no top-level `mido` import.
- Gate 8: CLI help fixture updated.
- Gate 9: architecture suite run before PR.
- Gate 10: docs/status updated because operator-facing behavior changes.
- Gate 11: tests use existing fixtures/helpers.
- Gate 12: existing report/dataclass patterns reused.
- Gate 13: JSON output remains deterministic.
- Gate 14: error handling follows existing CLI report command pattern.
- Gate 15: no parity capture.
- Gate 16: one clean-base PR, not stacked.
- Gate 17: PR body includes checklist.
- Gate 18: review gate run before merge.

## Rollback

Revert the single PR commit. The feature is additive and passive, so rollback removes the command, tests, and docs without changing existing runtime behavior.
