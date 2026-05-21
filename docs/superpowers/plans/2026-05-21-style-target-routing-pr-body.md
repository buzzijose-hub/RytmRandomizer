# Summary

Adds the passive style-target-to-snapshot bridge: style profile data now has normalized target vectors, operators can inspect those targets from the passive CLI, a mock-safe Rytm style snapshot routing report explains which pads in a captured kit are ready to mutate toward a style goal, Analog Four gains the matching passive track-role routing foundation plus an operator-facing report command, and the Rytm/A4/dual-machine reports can emit deterministic JSON for future GUI/audio-analyzer consumers. No MIDI is sent and no hardware is touched.

## What Changed

- Added style target vectors and passive style-target report/inspection CLI surfaces.
- Added a pure Rytm style snapshot routing strategy under `devices/strategies/` that combines snapshot machine facts, pad-machine compatibility, and style target emphasis.
- Added a passive `rytm-style-snapshot-routing-report <syx-path> <style-key> [--slot N] [--json]` CLI command for operator-facing and machine-readable snapshot readiness.
- Added a pure Analog Four style snapshot routing strategy that maps a candidate kit snapshot and style target into four A4 track roles, favored zones, and explicit candidate-offset readiness.
- Added a passive `analog-four-style-snapshot-routing-report <syx-path> <style-key> [--slot N] [--json]` CLI command for operator-facing and machine-readable A4 track readiness.
- Added a passive `dual-machine-style-snapshot-routing-report <rytm-syx-path> <a4-syx-path> <style-key> [--rytm-slot N] [--a4-slot N] [--json]` CLI command for rig-level style readiness.
- Updated README, status notes, architecture diagrams, CLI help fixtures, and plan docs for the new passive surface.
- Covered the new report and routing branches, including CLI parsing/error behavior and empty-plan formatting.

## Why This Matters

This is the first concrete bridge between the artist/style intelligence layer and live-kit snapshot mode. It does not mutate parameters yet; it tells the next mutation slice which pads, machines, and zones are legal and musically relevant for a chosen style.

## Test Plan

```bash
python -m pytest tests/test_rytm_style_snapshot_routing.py -n 0
python -m pytest tests/test_analog_four_style_snapshot_routing.py -n 0
python -m pytest tests/test_rytm_style_snapshot_routing.py tests/test_cli.py -n 0 -k "style_snapshot_routing or rytm_style_snapshot_routing or cli_help"
python -m pytest tests/test_analog_four_style_snapshot_routing.py tests/test_cli.py -n 0 -k "analog_four_style_snapshot_routing or cli_help"
python -m pytest tests/test_dual_machine_style_snapshot_routing_report.py tests/test_cli.py -n 0 -k "dual_machine_style_snapshot_routing or cli_help"
python -m pytest tests/test_rytm_style_snapshot_routing.py --cov=rytm_randomizer.reports.rytm_style_snapshot_routing --cov-branch --cov-report=term-missing -n 0
python -m pytest tests/test_analog_four_style_snapshot_routing.py --cov=rytm_randomizer.devices.strategies.analog_four_style_snapshot_routing --cov-branch --cov-report=term-missing -n 0
python -m pytest tests/test_analog_four_style_snapshot_routing.py --cov=rytm_randomizer.reports.analog_four_style_snapshot_routing --cov-branch --cov-report=term-missing -n 0
python -m pytest tests/test_dual_machine_style_snapshot_routing_report.py --cov=rytm_randomizer.reports.dual_machine_style_snapshot_routing --cov-branch --cov-report=term-missing -n 0
python -m vulture rytm_randomizer\data\style_profiles.py rytm_randomizer\data\style_targets.py rytm_randomizer\reports\style_profiles.py rytm_randomizer\reports\style_targets.py rytm_randomizer\reports\rytm_style_snapshot_routing.py rytm_randomizer\reports\analog_four_style_snapshot_routing.py rytm_randomizer\reports\dual_machine_style_snapshot_routing.py rytm_randomizer\devices\strategies\analog_rytm_style_snapshot_routing.py rytm_randomizer\devices\strategies\analog_four_style_snapshot_routing.py tests\test_style_profiles_report.py tests\test_style_targets_report.py tests\test_rytm_style_snapshot_routing.py tests\test_analog_four_style_snapshot_routing.py tests\test_dual_machine_style_snapshot_routing_report.py --min-confidence 80
python -m pytest tests/architecture/ -q
python -m ruff check .
python -m black --check --target-version=py311 .
python -m isort --profile black --check-only .
python -m pytest -m fast
python -m pytest
python -m pytest --cov=rytm_randomizer --cov-branch --cov-report=term-missing
python scripts/code_review_gate.py --mode cli
```

- [x] Local pytest passes: 2713 passed, 4 skipped.
- [x] `tests/architecture/` passes: 255 passed, 1 skipped.
- [x] Lint trio clean: ruff, black, isort.
- [x] Coverage stays >=95% pure-branch: whole package 98.20%; new Rytm/A4/dual-machine routing reports have focused coverage.
- [x] 685/685 V1.34 parity items byte-identical via `scripts/code_review_gate.py --mode cli`.
- [x] No new dead code: vulture clean on touched style/Rytm/A4 routing modules and tests.
- [ ] CI matrix green on all 3 OSes - N/A until this local branch is pushed after PR #56 lands.

## Plan-Requirements Conformance

Per `docs/PLAN_REQUIREMENTS.md`:

- [x] Gate 1 - 100% branch coverage on touched files; project >=95% pure-branch.
- [x] Gate 2 - V1.34 parity byte-identical: 685 parity items passed.
- [x] Gate 3 - lint clean: ruff + black + isort passed locally.
- [x] Gate 4 - no new dead code: vulture clean on touched style/Rytm/A4 routing files.
- [x] Gate 5 - docs updated: README, docs/STATUS.md, architecture diagrams, and plan docs updated.
- [x] Gate 6 - type-system hygiene: frozen dataclasses, explicit mappings, no `Any` escape hatch.
- [ ] Gate 7 - N/A: passive report/planning path only; no hot MIDI send/state-transition path added.
- [x] Gate 8 - test hygiene: focused tests mirror passive report/strategy behavior and reuse shared fixtures.
- [x] Gate 9 - module-organization hygiene: new implementation lives under existing `devices/strategies/` and `reports/`.
- [x] Gate 10 - string-literal dispatch hygiene: no new legacy mode/intensity/page dispatch.
- [x] Gate 11 - shared fixtures: snapshot fixture payload comes from `tests/conftest.py`.
- [x] Gate 12 - module-level constants use `Final`.
- [ ] Gate 13 - N/A: no new environment variables.
- [x] Gate 14 - maintainability review: plan docs define the small passive bridge and keep mutation sending deferred.
- [ ] Gate 15 - N/A: no new reusable learned skill or project rule required for this narrow bridge.
- [x] Gate 16 - execution shape: work isolated in a local worktree; not pushed/opened while PR #56 is open.
- [x] Gate 17 - abstraction reuse: uses `data/`, `snapshot/sysex_file`, `Device` strategy package, `reports/formatter`, and CLI registry patterns.
- [x] Gate 18 - architecture-doc + diagram freshness: architecture diagrams updated for new Rytm/A4/dual-machine strategy, report, and CLI surfaces.

## Strict Rules

- [x] No hardware in tests - no test opens a real MIDI port or mutates a connected device.
- [x] Lazy MIDI imports - no top-level `mido` or `python-rtmidi` import added.
- [x] Hardware-pinned packages - `mido==1.3.3` and `python-rtmidi==1.5.8` unchanged.
- [x] Passive default - new CLI command is passive/read-only and does not open a real port.
- [x] No stacked PRs - this work remains local until PR #56 lands; publish from `modularize-v1.34`.
- [x] No `--no-verify` - hooks were not bypassed.

## Plan Document

- `docs/superpowers/specs/2026-05-21-style-profile-snapshot-routing-design.md`
- `docs/superpowers/plans/2026-05-21-style-target-vector-pr57.md`
- `docs/superpowers/plans/2026-05-21-rytm-style-snapshot-routing-pr58.md`
- `docs/superpowers/plans/2026-05-21-analog-four-style-snapshot-routing-pr59.md`
- `docs/superpowers/plans/2026-05-21-analog-four-style-routing-report-pr60.md`
- `docs/superpowers/plans/2026-05-21-dual-machine-style-routing-report-pr61.md`
- `docs/superpowers/plans/2026-05-21-style-routing-json-payloads-pr62.md`

## Reviewer Notes

- This remains passive/mock-safe. It plans and reports readiness only; parameter mutation and MIDI rendering remain future slices.
- Analog Four style routing intentionally stays blocked for real mutation while A4 offsets are candidate-only; the report exposes that state clearly for operators.
- The single-machine reports now expose detailed per-pad/per-track JSON; the dual-machine report remains the compact rig-level summary with optional JSON.
- Local `python -m pyright ...` could not run because `pyright` is not installed in this environment.
- PR #56 is still blocking publish at the time this body was drafted, so CI status is intentionally left N/A until this branch can be pushed from a clean base.
