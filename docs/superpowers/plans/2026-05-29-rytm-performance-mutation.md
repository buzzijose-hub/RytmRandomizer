# Rytm Performance Mutation Implementation Plan

> Status: in-flight (branch codex/rytm-snapshot-pad-compatibility-pr1)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add an explicit performance mutation path that decodes a captured Analog Rytm kit SysEx file and renders either a seeded, depth-bounded live-safe current-machine mutation or an explicit flow-shift machine-switching mutation.

**Architecture:** Keep raw SysEx parsing passive and reuse the existing snapshot decoder plus curated style renderer. Add a Rytm strategy helper that filters rendered style events into `live-safe` or `flow-shift` modes. `live-safe` applies seeded bounded variation without machine switching, with extra Pad 1 kick guardrails; `flow-shift` keeps the full style including machine switches. Expose both through `app.py` behind `--dry-run` or `--arm` plus a dedicated confirmation flag for armed sends.

**Tech Stack:** Python 3.13 in this workspace, frozen dataclasses, existing Elektron SysEx helpers, existing Rytm style recipes, pytest, ruff.

---

## Task 1: Performance Planner

**Files:**
- Create: `rytm_randomizer/devices/strategies/analog_rytm_performance_mutation.py`
- Modify: `rytm_randomizer/devices/strategies/__init__.py`
- Test: `tests/test_analog_rytm_performance_mutation.py`

- [x] Write tests proving `live-safe` excludes `Track Machine Type` events, preserves manual FILTER/AMP events, and only keeps SRC events compatible with the decoded current machine.
- [x] Write tests proving `live-safe` varies values by seed without changing event shape, covers pads 1-12, and keeps Pad 1 BD Hard tune in a punch-safe range at `safe` depth.
- [x] Write tests proving `flow-shift` keeps the full rendered style including 12 machine-switch events.
- [x] Implement `build_rytm_performance_mutation_plan(snapshot, recipe, mode, depth, seed)`.
- [x] Re-export the public plan dataclass and builder.
- [x] Run `python -m pytest tests/test_analog_rytm_performance_mutation.py -n 0`.

## Task 2: App Surface

**Files:**
- Modify: `rytm_randomizer/app.py`
- Test: `tests/test_app_validate_one_cc.py`

- [x] Add app flags: `--rytm-performance-snapshot`, `--rytm-performance-mode`, `--rytm-performance-style`, `--rytm-performance-depth`, `--rytm-performance-seed`, and `--confirm-rytm-performance-send`.
- [x] Add dry-run tests proving the snapshot file is decoded, the mock sender captures messages, and no real MIDI module is imported.
- [x] Add app tests proving depth/seed are reported, seed is non-negative, and depth/seed do not silently run without a snapshot.
- [x] Add armed tests proving confirmation is required before port discovery.
- [x] Add armed fake-mido tests proving the selected output port receives exactly the planned events and closes.
- [x] Run `python -m pytest tests/test_app_validate_one_cc.py -k rytm_performance -n 0`.

## Task 3: Verification

**Files:**
- No additional files.

- [x] Run the performance planner tests, app performance tests, snapshot file tests, and style recipe tests together.
- [x] Run ruff on touched files.
- [x] Run `python -m rytm_randomizer.app --dry-run --rytm-performance-snapshot <local-current-kit.syx> --rytm-performance-mode live-safe --rytm-performance-style flow-shift`.
- [x] Run `python -m rytm_randomizer.app --dry-run --rytm-performance-snapshot <local-current-kit.syx> --rytm-performance-mode live-safe --rytm-performance-style flow-shift --rytm-performance-depth safe`.
- [x] Hardware-send the verified `live-safe` / `safe` plan only after explicit user approval.
- [x] Document the first hardware lesson: seed `890002068` initially pushed Pad 1 filter frequency to `62`, which killed kick punch.
- [x] Add a regression test for seed `890002068` proving Pad 1 kick filter frequency stays in `21..29` at `safe` depth.
- [x] Correct the same-seed plan to Pad 1 `SRC Tune=61`, `SRC Decay=71`, `Filter Frequency=24`, then send the corrected CC-only plan.
- [x] Save the handoff in `docs/hardware-validation/2026-05-29-rytm-live-safe-performance-session.md`.
