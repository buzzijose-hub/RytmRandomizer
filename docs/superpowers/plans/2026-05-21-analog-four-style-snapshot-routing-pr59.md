# Analog Four Style Snapshot Routing Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a passive Analog Four style snapshot routing strategy that maps a decoded A4 kit snapshot and style target into four track-role previews without sending MIDI or claiming promoted offset safety.

**Architecture:** Keep the work inside the existing Device Strategy boundary by adding `rytm_randomizer/devices/strategies/analog_four_style_snapshot_routing.py`. The strategy consumes the shared style target/profile data and the existing `AnalogFourKitSnapshot`, returning frozen plan records that report favored zones and readiness while preserving the candidate-only offset block.

**Tech Stack:** Python dataclasses, `MappingProxyType`, existing style data tables, pytest, architecture tests, and passive/mock-safe verification.

---

## Scope

This slice is intentionally not an Analog Four sender, CLI command, or parameter mutator. It is the A4 counterpart to the Rytm style-routing planner: a deterministic planning object the later report/mutation slices can consume.

## File Structure

- Create `rytm_randomizer/devices/strategies/analog_four_style_snapshot_routing.py`: pure strategy helper and frozen plan records.
- Modify `rytm_randomizer/devices/strategies/__init__.py`: re-export the new A4 routing records/helper.
- Create `tests/test_analog_four_style_snapshot_routing.py`: TDD coverage for candidate-only blocking, promoted readiness, unknown style errors, wrong snapshot errors, and read-only determinism.
- Modify `docs/STATUS.md`: note the passive A4 style routing checkpoint.
- Modify `docs/ARCHITECTURE_DIAGRAMS.md`: bump module count and list the new A4 strategy surface.
- Modify `docs/superpowers/plans/2026-05-21-style-target-routing-pr-body.md`: include A4 routing in the prepared PR body.

## Tasks

### Task 1: Strategy Tests

**Files:**
- Create: `tests/test_analog_four_style_snapshot_routing.py`

- [x] **Step 1: Write failing tests**

Cover:
- Candidate-only snapshots return four blocked track plans.
- Promoted snapshots return four ready track plans.
- Unknown style keys fail safely.
- Wrong snapshot types fail safely.
- Returned plan is deterministic and read-only.

- [x] **Step 2: Verify red**

Run:

```bash
python -m pytest tests/test_analog_four_style_snapshot_routing.py -n 0
```

Expected before implementation: import failures for `plan_analog_four_style_snapshot_routes`.

### Task 2: Passive Strategy

**Files:**
- Create: `rytm_randomizer/devices/strategies/analog_four_style_snapshot_routing.py`
- Modify: `rytm_randomizer/devices/strategies/__init__.py`

- [x] **Step 1: Implement frozen records and planner**

Add:
- `AnalogFourStyleTrackPlan`
- `AnalogFourStyleSnapshotRoutingPlan`
- `plan_analog_four_style_snapshot_routes(snapshot, style_key)`

The planner:
- Rejects non-`AnalogFourKitSnapshot` inputs.
- Normalizes the style key and rejects unknown targets.
- Scores style zones using shared `StyleTargetVector` axes.
- Produces four stable A4 track roles: bass foundation, stab pulse, texture motion, and space accent.
- Keeps `route_ready=False` while `snapshot.offsets_promoted` is false.

- [x] **Step 2: Verify green**

Run:

```bash
python -m pytest tests/test_analog_four_style_snapshot_routing.py -n 0
```

Expected: 5 passed.

### Task 3: Verification and Docs

**Files:**
- Modify: `docs/STATUS.md`
- Modify: `docs/ARCHITECTURE_DIAGRAMS.md`
- Modify: `docs/superpowers/plans/2026-05-21-style-target-routing-pr-body.md`

- [x] **Step 1: Focused coverage and style checks**

Run:

```bash
python -m pytest tests/test_analog_four_style_snapshot_routing.py --cov=rytm_randomizer.devices.strategies.analog_four_style_snapshot_routing --cov-branch --cov-report=term-missing -n 0
python -m ruff check rytm_randomizer\devices\strategies\analog_four_style_snapshot_routing.py tests\test_analog_four_style_snapshot_routing.py rytm_randomizer\devices\strategies\__init__.py
python -m black --check --target-version=py311 rytm_randomizer\devices\strategies\analog_four_style_snapshot_routing.py tests\test_analog_four_style_snapshot_routing.py rytm_randomizer\devices\strategies\__init__.py
python -m isort --profile black --check-only rytm_randomizer\devices\strategies\analog_four_style_snapshot_routing.py tests\test_analog_four_style_snapshot_routing.py rytm_randomizer\devices\strategies\__init__.py
```

Expected: tests pass, focused branch coverage reaches 100%, lint/format/import checks pass.

- [x] **Step 2: Architecture checks**

Run:

```bash
python -m pytest tests/architecture/test_no_side_effects.py tests/architecture/test_device_protocol_enforcement.py tests/architecture/test_no_new_top_level_modules.py -q
```

Expected: architecture checks pass with no MIDI import/port side effects.

## Plan-Requirements Conformance

Per docs/PLAN_REQUIREMENTS.md, this plan commits to:

- [x] Gate 1 - 100% branch coverage on touched files.
- [x] Gate 2 - V1.34 parity remains untouched; final closeout will run parity through `scripts/code_review_gate.py --mode cli`.
- [x] Gate 3 - lint/format/import checks pass for touched files; final closeout will run full lint.
- [x] Gate 4 - no new dead code; final closeout will include vulture on touched style/A4 files.
- [x] Gate 5 - docs updated in the same local checkpoint.
- [x] Gate 6 - frozen dataclasses and explicit types, no `Any`.
- [ ] Gate 7 - N/A: passive planner only, no send/state-transition hot path.
- [x] Gate 8 - focused intent-named tests.
- [x] Gate 9 - no new top-level modules; new strategy lives under `devices/strategies/`.
- [x] Gate 10 - no new legacy mode/intensity/page dispatch.
- [x] Gate 11 - no duplicate shared fixtures.
- [x] Gate 12 - module constants use `Final`.
- [ ] Gate 13 - N/A: no environment variables.
- [x] Gate 14 - bounded scope: A4 routing only, real mutation remains blocked.
- [ ] Gate 15 - N/A: no reusable learned skill/rule needed.
- [x] Gate 16 - isolated local worktree; no push/PR while PR #56 is open.
- [x] Gate 17 - reuses style data, A4 snapshot types, and Device Strategy boundaries.
- [x] Gate 18 - architecture diagrams refreshed for the new strategy module/count.
