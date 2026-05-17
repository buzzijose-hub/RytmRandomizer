# Analog Four Hardware Smoke Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add the first guarded Analog Four MKII hardware smoke path.

**Architecture:** Create a tiny A4 smoke helper that sends only Amp Pan CC10 across synth Tracks 1-4 and returns each track to center. Wire it into `rytm-randomizer --dry-run --analog-four-smoke` and `rytm-randomizer --arm --analog-four-smoke`, with an Analog Four-specific port prompt.

**Tech Stack:** Python dataclasses, existing `midi_io.send_cc`, argparse, pytest.

---

### Task 1: Analog Four Smoke Helper

**Files:**
- Create: `rytm_randomizer/analog_four_smoke.py`
- Test: `tests/test_analog_four_smoke.py`

- [x] **Step 1: Write failing tests**

Tests require passive import, deterministic Track 1-4 Pan CC10 steps, mock capture on wire channels 0-3, and report safety lines.

- [x] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_analog_four_smoke.py -q`

Expected: fails because `rytm_randomizer.analog_four_smoke` does not exist yet.

- [x] **Step 3: Implement helper**

Implement `build_analog_four_smoke_steps()`, `run_analog_four_smoke_test()`, and `format_analog_four_smoke_report()`.

- [x] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_analog_four_smoke.py -q`

Expected: all helper tests pass.

### Task 2: App Wiring

**Files:**
- Modify: `rytm_randomizer/app.py`
- Test: `tests/test_app_entry.py`

- [x] **Step 1: Write failing app tests**

Tests require `--dry-run --analog-four-smoke`, `--arm --analog-four-smoke`, bare `--analog-four-smoke` failure, and mutual exclusion with `--twelve-pad-smoke`.

- [x] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_app_entry.py::test_app_main_dry_run_analog_four_smoke_captures_mock_stream tests/test_app_entry.py::test_app_main_arm_analog_four_smoke_sends_to_selected_fake_port -q`

Expected: fails because the parser has no A4 smoke flag.

- [x] **Step 3: Implement app flag**

Add `--analog-four-smoke`; use the A4 prompt when armed; route dry-run through `MockMidiSender`.

- [x] **Step 4: Run app tests**

Run: `pytest tests/test_app_entry.py -q`

Expected: all app entry tests pass.

### Task 3: Docs And Verification

**Files:**
- Modify: `Docs/FUTURE_ANALOG_FOUR_EXPANSION.md`
- Modify: `Docs/PASSIVE_CLI_OPERATOR_QUICKSTART.md`
- Modify: `Docs/STATUS.md`

- [x] **Step 1: Update docs**

Document the A4 smoke path as pan-only channel validation, not full runtime support.

- [x] **Step 2: Verify**

Run: `pytest tests/test_analog_four_smoke.py tests/test_app_entry.py tests/test_analog_four_reference.py tests/test_midi_io.py tests/architecture/test_no_side_effects.py -q`

Expected: all selected tests pass.

- [x] **Step 3: Whitespace check**

Run: `git diff --check`

Expected: no whitespace errors.
