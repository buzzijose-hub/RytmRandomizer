# Summary

Adds a passive Live Kit Operator Package lane to the Cockpit performance
console. The new lane binds the captured-kit audition slots from the Live Kit
Package Audition payload into browser-local operator steps, recovery
requirements, journal/export preview metadata, and local rehearsal package
evidence.

## What changed

- Added `live_kit_operator_package` to
  `live-gui-performance-console-report [--json]`, derived from the existing
  live-kit capture workbench and live-kit package audition payload.
- Added a typed passive backend payload with operator steps, slot bindings,
  recovery requirements, journal commit preview, local export preview, blocked
  actions, safety lines, replay commands, and text report output.
- Rendered the Live Kit Operator Package panel in the desktop Performance
  Console with browser-local stage buttons and disabled hardware package
  controls.
- Extended local rehearsal package export/import so packages can carry optional
  `auditionSource` and `operatorPackage` evidence while older exports still
  import.
- Added frontend compatibility handling for older console packets without
  operator-package metadata and marked stale imported operator slots as
  review-required.
- Added nested Python/TypeScript field-parity coverage for the operator-package
  payload contract.
- Updated the TypeScript protocol, demo packet, focused backend/frontend tests,
  README, CLI reference, STATUS, architecture docs/diagrams, and implementation
  plan.

## Why this matters

The previous packet could review captured-kit audition slots, but the operator
still had to mentally connect them to the local set-plan and package export
flow. This PR turns those audition slots into a concrete local rehearsal lane:
Jose can stage a captured-kit move locally, see the recovery requirement, and
export a package that records which captured-kit operator package slot inspired
the rehearsal.

This remains passive metadata and browser-local UI only. It opens no MIDI
ports, sends no MIDI, does not dispatch sidecar commands, does not receive
SysEx from Cockpit, and does not mutate snapshots or hardware.

## Test plan

```bash
python -m pytest tests/test_live_gui_performance_console_model.py -n 0
python -m pytest tests/architecture/ -q
python -m ruff check .
python -m black --check --target-version=py311 .
python -m isort --profile black --check-only .
cd desktop/web && npm.cmd ci
cd desktop/web && npm.cmd run test:run -- PerformanceConsole.test.tsx
cd desktop/web && npm.cmd run typecheck
cd desktop/web && npm.cmd run lint
cd desktop/web && npm.cmd run test:coverage
python -m pytest
cd desktop/web && npm.cmd run test:run
cd desktop/web && npm.cmd run build
git diff --check
```

- [x] Focused Python contract tests pass: 17 passed.
- [x] Architecture gate passes: 622 passed, with the existing warn-only
  duplicate `main` warning.
- [x] Python lint trio clean: ruff, black, isort.
- [x] Focused PerformanceConsole Vitest passes: 27 passed.
- [x] Frontend typecheck and ESLint pass.
- [x] Full Python suite passes: 5737 passed, 3 skipped.
- [x] Frontend coverage suite passes: 39 files / 419 tests passed with
  100% statements, branches, functions, and lines.
- [x] Frontend production build passes.
- [x] `git diff --check` passes.
- [ ] CI matrix green: pending after PR open.

## Plan-requirements conformance

Per `docs/PLAN_REQUIREMENTS.md`, every non-trivial PR must satisfy all 18
gates. Mark each `[x]`, or `[ ] N/A - <reason>`.

- [x] **Gate 1** - focused backend report tests and frontend component tests
  cover the new operator package payload, panel, local staging, and export
  evidence.
- [x] **Gate 2** - V1.34 parity remains byte-identical; no fixture
  regeneration.
- [x] **Gate 3** - lint clean: ruff, black, isort, and frontend ESLint.
- [x] **Gate 4** - full Python suite, architecture tests, and frontend suite
  pass; no new dead-code surface detected.
- [x] **Gate 5** - docs updated: README, CLI reference, STATUS, and plan doc.
- [x] **Gate 6** - type-system hygiene: Python TypedDict payloads and
  TypeScript protocol updated; no `Any` escape hatch.
- [ ] **Gate 7** - N/A: passive report/UI metadata only; no state transition,
  CC send, guardrail hot path, or hardware behavior added.
- [x] **Gate 8** - test hygiene: TDD was used for backend and frontend focused
  coverage.
- [x] **Gate 9** - module organization: backend work stays under
  `rytm_randomizer/reports/performance_console`; frontend work stays in the
  existing Cockpit package; no new top-level Python module.
- [x] **Gate 10** - no new mode/intensity/page string-dispatch arm.
- [x] **Gate 11** - no duplicated shared fixture body.
- [x] **Gate 12** - new Python module-level constants use `Final`.
- [ ] **Gate 13** - N/A: no new environment variables.
- [x] **Gate 14** - maintainability audit is recorded in the plan doc;
  implementation composes existing capture workbench/audition payloads and
  keeps legacy frontend packets fallback-safe.
- [ ] **Gate 15** - N/A: no new reusable skill or project rule discovered.
- [x] **Gate 16** - one clean-base branch/PR against `modularize-v1.34`; no
  stacked PRs.
- [x] **Gate 17** - abstraction reuse: Gate 17 architecture test passes after
  keeping helper names package-specific and reusing payload helpers.
- [x] **Gate 18** - architecture docs refreshed for the added
  `reports/performance_console/live_kit_operator_package.py` helper and current
  `rytm_randomizer/` module count; README/CLI/STATUS and protocol contract were
  also updated.

## Strict rules - non-negotiables

Per `CONTRIBUTING.md` strict rules, confirm each:

- [x] **No hardware in tests** - no test opens a real MIDI port; no test mutates
  a connected device.
- [x] **Lazy MIDI imports** - `mido` and `python-rtmidi` remain lazy and
  restricted.
- [x] **Hardware-pinned packages** - `mido==1.3.3` and `python-rtmidi==1.5.8`
  not bumped.
- [x] **Passive default** - `python -m rytm_randomizer.cli` does not open a real
  port.
- [x] **No stacked PRs** - this branch targets `modularize-v1.34`.
- [x] **No `--no-verify`** - hooks were not bypassed.

## Plan document

Plan doc:
`docs/superpowers/plans/2026-06-19-live-kit-operator-package-bundle.md`

## Reviewer notes

- The active-looking operator package controls remain disabled; only
  browser-local staging buttons are enabled.
- Exported packages now optionally carry `auditionSource` and
  `operatorPackage` metadata, but older local package exports still import.
- Real captured-kit mutation and send remain in the explicitly armed snapshot
  shell, not the passive Cockpit report.
