# 12-Pad Mock Runtime Contract Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the first mock-only 12-pad runtime contract from style intent to planned MIDI CC messages.

**Architecture:** Add a passive `twelve_pad_mock_runtime` module that resolves a style prompt through the existing Style Intent and Machine Catalog layers, selects only mapped V1.34-safe machine profiles, and builds inert `MockMidiSender` messages. Expose it through a passive CLI report so Jose can inspect a complete 12-pad message stream before any armed hardware work exists.

**Tech Stack:** Python dataclasses, existing `style_intent_profiles`, `machine_catalog`, `data.PROFILES`, `mock_midi`, pytest subprocess CLI tests.

---

### Task 1: Mock Runtime Contract

**Files:**
- Create: `rytm_randomizer/twelve_pad_mock_runtime.py`
- Test: `tests/test_twelve_pad_mock_runtime.py`

- [x] Write failing tests for passive import safety, 12 pad/channel coverage, safe mapped engine selection, future-engine fallback, and mock message metadata.
- [x] Run: `pytest tests\test_twelve_pad_mock_runtime.py -q`
- [x] Implement the mock runtime plan dataclasses, safe profile mapping, message builder, and report formatter.
- [x] Run: `pytest tests\test_twelve_pad_mock_runtime.py -q`

### Task 2: Passive CLI Report

**Files:**
- Modify: `rytm_randomizer/cli.py`
- Modify: `rytm_randomizer/help_text.py`
- Modify: `tests/test_cli.py`
- Modify: `tests/fixtures/cli_help_expected.txt`
- Test: `tests/test_twelve_pad_mock_runtime.py`

- [x] Add failing CLI tests for `twelve-pad-mock-runtime-report --style <text>` and optional `--discovery`.
- [x] Run: `pytest tests\test_twelve_pad_mock_runtime.py tests\test_cli.py -q`
- [x] Wire the passive CLI command and help text.
- [x] Run: `pytest tests\test_twelve_pad_mock_runtime.py tests\test_cli.py -q`

### Task 3: Verification

**Files:**
- Modify: `docs/PASSIVE_CLI_OPERATOR_QUICKSTART.md`
- Modify: `docs/STATUS.md`

- [x] Document the mock-only 12-pad contract and safety boundary.
- [x] Run: `python -m rytm_randomizer.cli twelve-pad-mock-runtime-report --style "Birmingham dark techno"`
- [x] Run: `pytest tests\test_twelve_pad_mock_runtime.py tests\test_style_intent_profiles.py tests\test_machine_catalog.py tests\test_cli.py tests\architecture\test_no_side_effects.py -q`
- [x] Run: `git diff --check`
