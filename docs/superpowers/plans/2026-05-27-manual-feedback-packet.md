# Manual Feedback Packet Implementation Plan

Date: 2026-05-27

## Objective

Add one passive, reviewer-ready manual feedback packet surface:

```bash
python -m rytm_randomizer.cli manual-feedback-packet-report --scenario profile
python -m rytm_randomizer.cli manual-feedback-packet-report --scenario hardware --json
```

The command must help Jose capture current installer, cockpit, Profile Wizard,
analyzer, export, mock-control, pad-scope, and approved hardware-boundary
observations while preserving the project-wide passive default.

## Workstreams

1. Red tests:
   - Report builder defaults to `full` with ten steps.
   - `profile` scenario focuses analyzer, export, and pad-scope feedback.
   - Text and JSON outputs are deterministic.
   - CLI text, JSON, help, and unknown-scenario paths are covered.
   - Import safety proves no real MIDI modules load.
2. Data layer:
   - Add frozen `ManualFeedbackStep` and `ManualFeedbackScenario` tables under
     `rytm_randomizer/data/`.
   - Re-export through `rytm_randomizer.data`.
3. Report layer:
   - Add deterministic builder, text formatter, JSON formatter, parser,
     handler, and `CliCommand`.
   - Use existing passive report footer and safety lines.
4. CLI and docs:
   - Lazy-register `manual-feedback-packet-report`.
   - Add command help and top-level help entries.
   - Update CLI reference, README, manual hardware validation notes,
     architecture docs, diagrams, and status.
5. Verification:
   - Focused tests for the new report.
   - Passive CLI safety sweep.
   - CLI fixture tests.
   - Architecture, lint, fast/full tests, and coverage before push.

## Conformance Checklist

- [x] Gate 1 - touched report/data/CLI code has direct focused tests and will
  be covered by full coverage verification.
- [x] Gate 2 - V1.34 parity is untouched; no engine, group, or scene output
  changes.
- [x] Gate 3 - passive default preserved; command only builds in-memory data.
- [x] Gate 4 - no hardware-pinned dependency changes.
- [x] Gate 5 - docs updated with command, safety, and operator context.
- [x] Gate 6 - no `Any` escape hatches.
- [x] Gate 7 - N/A: no hot MIDI send path or state transition.
- [x] Gate 8 - no real MIDI import; passive CLI sweep covers `--help`.
- [x] Gate 9 - no new top-level modules; data/report modules live in existing
  subpackages.
- [x] Gate 10 - no new global command literals outside CLI/report docs.
- [x] Gate 11 - tests reuse existing subprocess CLI helpers.
- [x] Gate 12 - frozen dataclasses and mapping proxies follow existing data
  layer patterns.
- [x] Gate 13 - no fixture regeneration except the CLI help fixture refresh.
- [x] Gate 14 - bounded error handling: unknown scenario returns CLI exit 2.
- [x] Gate 15 - no hardware behavior, no network, no GUI launch.
- [x] Gate 16 - one clean-base PR, no stacked branch.
- [x] Gate 17 - reuses `data/`, `reports/formatter.py`, and `cli_registry`.
- [x] Gate 18 - architecture docs and diagrams refreshed.

## Rollback

Revert the single PR. It removes one data module, one report module, the lazy
CLI registration, the help/docs entries, and the focused tests. No hardware,
profile files, export files, or parity fixtures are produced by the feature.
