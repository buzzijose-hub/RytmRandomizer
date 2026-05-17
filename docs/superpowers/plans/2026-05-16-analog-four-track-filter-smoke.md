# Analog Four Track Filter Smoke Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add the first guarded Analog Four filter parameter smoke path.

**Architecture:** Extend the existing A4 smoke helper with a one-track Filter 1 Frequency CC18 step builder, runner, and report. Wire it into the active app as `--analog-four-track-filter-smoke <1-4>` behind `--dry-run` or `--arm`, sharing the existing A4 port prompt and mock sender boundary.

**Tech Stack:** Python dataclasses, argparse, existing `midi_io.send_cc`, pytest.

---

### Task 1: Filter Smoke Helper

**Files:**
- Modify: `rytm_randomizer/analog_four_smoke.py`
- Test: `tests/test_analog_four_smoke.py`

- [x] **Step 1: Write failing tests**

Tests require `build_analog_four_track_filter_smoke_steps(2)` to emit exactly three CC18 messages on wire channel 1 with values 48, 112, and 127; invalid tracks 0/5 to raise `ValueError`; and the filter report to include `Track tested: 1`, `Messages sent: 3`, and the safety lines.

- [x] **Step 2: Run tests to verify they fail**

Run:

```powershell
pytest tests\test_analog_four_smoke.py::test_build_analog_four_track_filter_smoke_steps_targets_one_track_filter_1 tests\test_analog_four_smoke.py::test_build_analog_four_track_filter_smoke_steps_rejects_invalid_track tests\test_analog_four_smoke.py::test_format_analog_four_track_filter_smoke_report_includes_single_track_summary -q
```

Expected red state: imports fail because the filter helper functions do not exist.

- [x] **Step 3: Implement helper**

Add `build_analog_four_track_filter_smoke_steps(track)`, `run_analog_four_track_filter_smoke_test(...)`, and `format_analog_four_track_filter_smoke_report(...)`.

- [x] **Step 4: Run helper tests**

Run:

```powershell
pytest tests\test_analog_four_smoke.py -q
```

Expected: all A4 smoke helper tests pass.

### Task 2: App Wiring

**Files:**
- Modify: `rytm_randomizer/app.py`
- Test: `tests/test_app_entry.py`

- [x] **Step 1: Write failing app tests**

Tests require `--dry-run --analog-four-track-filter-smoke 2`, `--arm --analog-four-track-filter-smoke 3`, bare filter smoke failure, out-of-range track failure, and mutual exclusion with other smoke flags.

- [x] **Step 2: Run tests to verify they fail**

Run:

```powershell
pytest tests\test_app_entry.py::test_app_main_dry_run_analog_four_track_filter_smoke_captures_mock_stream tests\test_app_entry.py::test_app_main_arm_analog_four_track_filter_smoke_sends_to_selected_fake_port -q
```

Expected red state: argparse rejects `--analog-four-track-filter-smoke`.

- [x] **Step 3: Implement app flag**

Add `--analog-four-track-filter-smoke TRACK`, validate tracks 1-4, keep smoke modifiers mutually exclusive, and route dry-run/arm through the filter helper.

- [x] **Step 4: Run focused app tests**

Run:

```powershell
pytest tests\test_app_entry.py::test_app_main_dry_run_analog_four_track_filter_smoke_captures_mock_stream tests\test_app_entry.py::test_app_main_arm_analog_four_track_filter_smoke_sends_to_selected_fake_port -q
```

Expected: focused app entry tests pass.

### Task 3: Docs And Verification

**Files:**
- Modify: `Docs/FUTURE_ANALOG_FOUR_EXPANSION.md`
- Modify: `Docs/MANUAL_HARDWARE_VALIDATION.md`
- Modify: `Docs/PASSIVE_CLI_OPERATOR_QUICKSTART.md`
- Modify: `Docs/STATUS.md`

- [x] **Step 1: Update docs**

Document `--analog-four-track-filter-smoke <1-4>` as Filter 1 Frequency CC18 validation, not Analog Four runtime mutation.

- [x] **Step 2: Verify**

Run:

```powershell
pytest tests\test_analog_four_smoke.py tests\test_app_entry.py tests\test_analog_four_reference.py tests\test_midi_io.py tests\architecture\test_no_side_effects.py -q
python -m rytm_randomizer.app --dry-run --analog-four-track-filter-smoke 1
git diff --check
git diff -- rytm_hybrid_randomizer_v134.py
```

Expected: selected tests pass, dry-run reports 3 mock messages, whitespace check has no errors, and the V1.34 monolith diff is empty.
