# Controller Brain Rehearsal Bundle Plan

> Status: in-flight (implemented and locally verified)
> Base: `origin/modularize-v1.34`
> Branch: `codex/controller-brain-rehearsal-bundle`
> Scope: one bundled PR, no stacked PRs

## Why

PR #183 added a passive 16-encoder controller-brain mapping catalog. The next
large slice should make that catalog useful for controller-template planning
and Cockpit handoff without crossing into live MIDI input. OXI E16-style
surfaces can provide knobs, pages, snapshots, and macros; RytmRandomizer should
provide the musical brain: reviewed intent, safety evidence, recovery targets,
and deterministic rehearsal packets.

## What Changes

This bundle adds a passive controller-brain rehearsal/export packet:

- A data-layer rehearsal scenario describing representative encoder gestures
  across the merged 16-encoder mapping profile.
- A report module that resolves those gestures against the mapping profile and
  emits deterministic template rows, gesture outcomes, queue/recovery notes,
  blocked actions, and replay commands.
- A passive CLI command, `controller-brain-rehearsal-report [--json]`.
- Tests covering data shape, report formatting, JSON determinism, CLI behavior,
  and passive/no-hardware guarantees.
- README, CLI reference, architecture, architecture diagrams, and STATUS
  updates.

The feature remains passive. It does not open controller input, run MIDI learn,
send controller feedback, dispatch Cockpit WebSocket commands, mutate
snapshots, open Rytm/A4 outputs, arm hardware, or send MIDI.

## Workstreams

| Workstream | Owns | Depends on | Parallel with |
|---|---|---|---|
| WS1 plan + tests | plan doc, `tests/test_controller_brain_rehearsal_report.py` | none | WS2 after red tests |
| WS2 passive model/report | `rytm_randomizer/data/controller_rehearsal_scenarios.py`, `rytm_randomizer/reports/controller_brain_rehearsal.py` | WS1 red tests | docs after green |
| WS3 CLI/help/docs | `cli.py`, `help_text.py`, README/docs/status | WS2 surface names | none |

## Parity Impact

No V1.34 parity output changes are expected. This is a new passive
report/data surface and does not touch engines, group runner, scene runner, or
parity fixtures.

## TDD Plan

1. Add a failing test asserting the default rehearsal report contains:
   - Version `controller-brain-rehearsal-v1`.
   - Exactly 112 template rows (7 pages * 16 slots).
   - Gesture outcomes that resolve real `intent_key` values from the mapping
     profile.
   - No raw MIDI controller fields.
   - Blocked active actions for controller input, MIDI learn, WebSocket
     dispatch, hardware arming, and hardware send.
2. Add failing CLI tests for `controller-brain-rehearsal-report` text and JSON.
3. Implement minimal data/report/CLI code to pass.
4. Add focused coverage for validation edges.

## Test Plan

- `python -m pytest tests/test_controller_brain_rehearsal_report.py -n 0 -q`
- `python -m pytest tests/test_cli.py -n 0 -q`
- `python -m pytest tests/test_controller_mapping_profiles.py tests/test_controller_mapping_profile_catalog_report.py tests/test_controller_brain_rehearsal_report.py tests/test_cli.py -n 0 -q`
- `python -m pytest tests/test_real_midi_passive_cli_safety.py -n 0 -q`
- `python -m pytest tests/architecture/ -q`
- `python -m ruff check .`
- `python -m black --check --target-version=py311 .`
- `python -m isort --profile black --check-only .`
- `python -m pytest`

## Rollback Plan

Revert the single PR. Because this bundle only adds passive data/report/CLI
surfaces and docs, rollback removes the new command and leaves all existing
hardware behavior unchanged.

## Done Criteria

- Passive report text and JSON are deterministic.
- The packet resolves against the real controller mapping profile instead of
  duplicating controls.
- The CLI command is discoverable in help and docs.
- Focused and full verification pass.
- One PR is opened against `modularize-v1.34` with the 18-gate checklist.

## Plan-Requirements Conformance

Per docs/PLAN_REQUIREMENTS.md:

- [x] Gate 1 - touched Python files receive focused branch coverage.
- [x] Gate 2 - V1.34 parity fixtures remain untouched.
- [x] Gate 3 - lint, format, and imports verified before PR.
- [x] Gate 4 - no dead production code intentionally introduced.
- [x] Gate 5 - docs updated in the same PR.
- [x] Gate 6 - frozen dataclasses / explicit types; no `Any` escape hatches.
- [x] Gate 7 - N/A: passive report/data surface, no hot-path state transition
  or send decision.
- [x] Gate 8 - tests mirror source behavior and use real code.
- [x] Gate 9 - new code stays in existing `data/` and `reports/` packages.
- [x] Gate 10 - no new mode/intensity/page dispatch strings.
- [x] Gate 11 - no duplicated cross-file fixtures.
- [x] Gate 12 - module constants use `Final` or frozen dataclasses.
- [x] Gate 13 - no new environment variables.
- [x] Gate 14 - maintainability bounded to the existing passive report pattern.
- [x] Gate 15 - no new reusable agent learning expected.
- [x] Gate 16 - isolated worktree, single bundled PR, no stacked PRs.
- [x] Gate 17 - reuses controller mapping facts, `CliCommand`, and passive
  report formatter helpers.
- [x] Gate 18 - architecture docs/diagrams updated for the new CLI/report
  surface.
