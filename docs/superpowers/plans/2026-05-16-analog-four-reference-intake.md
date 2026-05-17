# Analog Four Reference Intake Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a passive Analog Four MKII reference-intake report so A4 planning can start without opening ports or sending MIDI.

**Architecture:** Create one small metadata module that stores source attribution, four A4 track roles, and the first safe parameter groups distilled from the public midi.guide reference. Expose it through the existing passive CLI/help pattern and docs.

**Tech Stack:** Python dataclasses, existing passive CLI dispatcher, pytest, no mido/rtmidi imports.

---

### Task 1: Passive A4 Reference Model

**Files:**
- Create: `rytm_randomizer/analog_four_reference.py`
- Test: `tests/test_analog_four_reference.py`

- [x] **Step 1: Write the failing tests**

Test import safety, source metadata, track roles, safe parameter groups, and report safety text.

- [x] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_analog_four_reference.py -q`

Expected: fails because `rytm_randomizer.analog_four_reference` does not exist yet.

- [x] **Step 3: Implement minimal passive module**

Implement frozen dataclasses and deterministic list/format helpers only. Do not import MIDI libraries.

- [x] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_analog_four_reference.py -q`

Expected: all tests pass.

### Task 2: Passive CLI Command

**Files:**
- Modify: `rytm_randomizer/cli.py`
- Modify: `rytm_randomizer/help_text.py`
- Modify: `tests/test_cli.py`
- Modify: `tests/fixtures/cli_help_expected.txt`

- [x] **Step 1: Write the failing CLI tests**

Add substring tests for `analog-four-reference-report` and its help text. Update the top-level help fixture to include the new command.

- [x] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_cli.py::test_analog_four_reference_report_cli_exits_zero tests/test_cli.py::test_analog_four_reference_report_help_exits_zero -q`

Expected: fails because the CLI has no command yet.

- [x] **Step 3: Implement minimal CLI dispatch/help**

Add the new command behind the passive dispatcher. It should only import the metadata module inside the command branch.

- [x] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_cli.py::test_analog_four_reference_report_cli_exits_zero tests/test_cli.py::test_analog_four_reference_report_help_exits_zero tests/test_cli.py::test_top_level_help_exits_zero_and_matches_fixture -q`

Expected: all selected tests pass.

### Task 3: Docs And Verification

**Files:**
- Modify: `Docs/FUTURE_ANALOG_FOUR_EXPANSION.md`
- Modify: `Docs/PASSIVE_CLI_OPERATOR_QUICKSTART.md`
- Modify: `Docs/STATUS.md`

- [x] **Step 1: Update docs**

Document the new passive command and make clear that this is reference intake only, not A4 runtime support.

- [x] **Step 2: Run focused verification**

Run: `pytest tests/test_analog_four_reference.py tests/test_cli.py tests/architecture/test_no_side_effects.py -q`

Expected: all selected tests pass.

- [x] **Step 3: Check whitespace**

Run: `git diff --check`

Expected: no whitespace errors.
