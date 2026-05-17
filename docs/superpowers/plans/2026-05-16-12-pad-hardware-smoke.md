# 12-Pad Hardware Smoke Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn the confirmed manual Pads 5-12 MIDI smoke test into an official guarded app path.

**Architecture:** Add a small smoke-stream helper that builds/sends deterministic Pad 5-12 pan/filter CC movements. Wire it into `rytm-randomizer --dry-run --twelve-pad-smoke` and `rytm-randomizer --arm --twelve-pad-smoke`, reusing the existing mock sender and mido-backed port provider.

**Tech Stack:** Python dataclasses, existing `midi_io.send_cc`, argparse, pytest.

---

### Task 1: Smoke Stream Helper

**Files:**
- Create: `rytm_randomizer/twelve_pad_smoke.py`
- Test: `tests/test_twelve_pad_smoke.py`

- [x] **Step 1: Write failing tests**

Tests require a passive import, deterministic Pad 5-12 CC10/CC74 stream, mock capture on wire channels 4-11, and report text with safety boundaries.

- [x] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_twelve_pad_smoke.py -q`

Expected: fails because `rytm_randomizer.twelve_pad_smoke` does not exist yet.

- [x] **Step 3: Implement helper**

Implement `build_twelve_pad_smoke_steps()`, `run_twelve_pad_smoke_test()`, and `format_twelve_pad_smoke_report()`.

- [x] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_twelve_pad_smoke.py -q`

Expected: all helper tests pass.

### Task 2: App Wiring

**Files:**
- Modify: `rytm_randomizer/app.py`
- Test: `tests/test_app_entry.py`

- [x] **Step 1: Write failing app tests**

Tests require `--dry-run --twelve-pad-smoke` to capture mock messages, `--arm --twelve-pad-smoke` to use the fake provider/port, and bare `--twelve-pad-smoke` to fail safely.

- [x] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_app_entry.py::test_app_main_dry_run_twelve_pad_smoke_captures_mock_stream tests/test_app_entry.py::test_app_main_twelve_pad_smoke_requires_active_mode -q`

Expected: fails because the parser has no flag.

- [x] **Step 3: Implement app flag**

Add `--twelve-pad-smoke`; in dry-run, run helper against `MockMidiSender`; in arm, select/open the real port then run helper and close port.

- [x] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_app_entry.py -q`

Expected: app tests pass.

### Task 3: Docs And Verification

**Files:**
- Modify: `Docs/PASSIVE_CLI_OPERATOR_QUICKSTART.md`
- Modify: `Docs/MANUAL_HARDWARE_VALIDATION.md`
- Modify: `Docs/STATUS.md`

- [x] **Step 1: Update docs**

Document the new dry-run and armed smoke commands, and keep Analog Four blocked until its own mock path exists.

- [x] **Step 2: Verify**

Run: `pytest tests/test_twelve_pad_smoke.py tests/test_app_entry.py tests/test_midi_io.py tests/architecture/test_no_side_effects.py -q`

Expected: all selected tests pass.

- [x] **Step 3: Whitespace check**

Run: `git diff --check`

Expected: no whitespace errors.
