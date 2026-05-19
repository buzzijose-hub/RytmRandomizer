# Summary

Redo the dual-machine foundation as one bundled PR on top of the PR #45 agent-governance baseline. The branch adds a registered `AnalogFourDevice`, generic guarded/hardware sender surfaces, and passive `rytm` / `a4` / `both` target reporting through the PR #43 Device Strategy architecture.

## What changed

- Added registered `AnalogFourDevice` through `rytm_randomizer.devices`.
- Added Analog Four snapshot decoder, mutation planner, and message renderer strategies under `rytm_randomizer/devices/strategies/`.
- Added generic `senders.guarded` and `senders.hardware` surfaces that consume registered `Device` instances.
- Added `dual_machine.targets` and `dual_machine.reports` for human-friendly `rytm`, `a4`, and `both` target selection.
- Added passive CLI support for `dual-machine-target-report <rytm|a4|both>`.
- Added focused tests for A4 readiness gating, sender refusal/sending paths, target reports, CLI behavior, and manual hardware-validation docs.
- Updated status/manual-validation docs and captured the design/plan under `docs/superpowers/`.

## Why this matters

This is the clean redo of the earlier dual-machine line of work: it keeps Rytm and Analog Four support behind the new Device Strategy seam, avoids the old stacked-PR cascade, and keeps A4 hardware sends readiness-gated until snapshot offsets are promoted.

## Test plan

```bash
python -m pytest tests/test_analog_four_device.py tests/test_devices_strategies_analog_four_snapshot_decoder.py tests/test_devices_strategies_analog_four_mutation_planner.py tests/test_devices_strategies_analog_four_message_renderer.py tests/test_dual_machine_targets.py tests/test_dual_machine_reports.py tests/test_senders_guarded.py tests/test_senders_hardware.py tests/test_manual_hardware_validation_doc.py -q
python -m pytest tests/architecture/ -q
python -m ruff check .
python -m black --check --target-version=py311 .
python -m isort --profile black --check-only .
python -m pytest --cov=rytm_randomizer --cov-branch --cov-report=term-missing --cov-report=xml -q
python scripts/coverage_ratchet.py coverage.xml
python -m vulture <touched python files> --min-confidence 80
```

- [x] Local focused changed-area tests pass: 37 passed.
- [x] `tests/architecture/` passes: 229 passed, 1 skipped.
- [x] Lint trio clean: ruff, black, and isort.
- [x] Coverage stays at or above 95 percent pure-branch: 2419 passed, 4 skipped; total coverage 97.92 percent; pure-branch coverage 95.50 percent.
- [x] 685/685 V1.34 parity items byte-identical: full coverage suite passed without fixture changes.
- [x] No new dead code in touched files: touched-file vulture scan clean at `--min-confidence 80`.
- [ ] CI matrix green on all 3 OSes: pending after rebase onto merged PR #45.

## Plan-requirements conformance

Per [`docs/PLAN_REQUIREMENTS.md`](../docs/PLAN_REQUIREMENTS.md) - every non-trivial PR must satisfy all 16 gates.

- [x] **Gate 1** - 100 percent branch coverage on touched files; project at or above 95 percent pure-branch. Focused coverage tests added for defensive branches; ratchet reports 95.50 percent pure-branch.
- [x] **Gate 2** - V1.34 parity byte-identical (505 goldens / 685 pytest items). No parity fixtures changed.
- [x] **Gate 3** - lint clean (ruff + black `--target-version=py311` + isort `--profile black`).
- [x] **Gate 4** - no new dead code. Touched-file vulture scan is clean; full-repo vulture reports two pre-existing warnings outside this diff.
- [x] **Gate 5** - docs updated: `docs/STATUS.md`, `docs/MANUAL_HARDWARE_VALIDATION.md`, migration map, design doc, and implementation plan.
- [x] **Gate 6** - type-system hygiene: Device Strategy Protocol shape used; `Final` constants used; no bare `Any` added.
- [ ] **Gate 7** - N/A: this PR adds passive strategy/report/sender boundaries, not hot-path observability instrumentation.
- [x] **Gate 8** - test hygiene: focused behavior tests added around public surfaces and defensive branches.
- [x] **Gate 9** - module-organization hygiene: new code lives in `devices/strategies/`, `senders/`, and `dual_machine/`; no parallel device-family subpackage.
- [x] **Gate 10** - string-literal dispatch hygiene: no mode-dispatch allowlist expansion; architecture tests pass.
- [x] **Gate 11** - shared fixtures: no duplicate shared fixture surfaces introduced.
- [x] **Gate 12** - `Final` constants on module-level constants where applicable.
- [x] **Gate 13** - env var docs: no env vars introduced.
- [x] **Gate 14** - maintainability review: sender duplication collapsed into generic sender surfaces; A4 remains readiness-gated until offsets are promoted.
- [x] **Gate 15** - learning capture: design and implementation plan captured under `docs/superpowers/`; PR #45 Codex guidance has been read and applied during rebase.
- [x] **Gate 16** - execution shape: one bundled PR against `modularize-v1.34`, no stacked PRs.

## Strict rules - non-negotiables

Per [`CONTRIBUTING.md` Strict rules](../CONTRIBUTING.md#strict-rules--non-negotiables) - confirm each:

- [x] **No hardware in tests** - no test opens a real MIDI port; no test mutates a connected device.
- [x] **Lazy MIDI imports** - `mido` and `python-rtmidi` imports remain lazy inside the existing real-MIDI boundary.
- [x] **Hardware-pinned packages** - `mido==1.3.3` and `python-rtmidi==1.5.8` not bumped.
- [x] **Passive default** - passive CLI/report additions do not open a real port.
- [x] **No stacked PRs** - this PR's base is `modularize-v1.34`, not another open PR head.
- [x] **No `--no-verify`** - pre-commit hooks were not bypassed.

## Plan document

Plan doc: `docs/superpowers/plans/2026-05-19-dual-machine-strategy-redo.md`

Design checkpoint: `docs/superpowers/specs/2026-05-19-dual-machine-strategy-redo-design.md`

Migration map: `docs/DUAL_MACHINE_STRATEGY_REDO_MIGRATION_MAP.md`

## Reviewer notes

- A4 outbound sends intentionally remain readiness-gated. The planner returns `ready=False` for candidate-only offset snapshots, and generic senders refuse not-ready plans.
- Rytm remains the mature reference path. This PR adds the A4 shape and safe orchestration surface without claiming final A4 snapshot-offset promotion.
- Full-repo vulture currently reports two pre-existing warnings outside this diff: `tests/test_engines_pad1.py:428` and `tests/test_guardrails_store.py:634`. The touched-file vulture scan is clean.
