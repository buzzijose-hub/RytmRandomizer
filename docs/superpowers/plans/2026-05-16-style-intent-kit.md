# Style Intent Kit Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a passive style-intent doorway that turns genre/tag language into essence tags and a 12-pad kit plan.

**Architecture:** Create `rytm_randomizer.style_intent_profiles` for deterministic style profile metadata and report formatting. Wire a passive `style-intent-report` CLI command to the existing Essence Plan machinery. Keep Analog Four as future metadata only.

**Tech Stack:** Python dataclasses, existing essence tag/order helpers, existing machine catalog planner, pytest subprocess CLI tests.

---

### Task 1: Style Intent Profiles

**Files:**
- Create: `rytm_randomizer/style_intent_profiles.py`
- Test: `tests/test_style_intent_profiles.py`

- [x] Write failing tests for passive import safety, profile alias lookup, style tag derivation, Analog Four future-note visibility, and report formatting.
- [x] Run: `pytest tests\test_style_intent_profiles.py -q`
- [x] Implement style profiles, lookup, tag derivation, request building, and report formatting.
- [x] Run: `pytest tests\test_style_intent_profiles.py -q`

### Task 2: CLI Command

**Files:**
- Modify: `rytm_randomizer/cli.py`
- Modify: `rytm_randomizer/help_text.py`
- Modify: `tests/test_style_intent_profiles.py`
- Modify: `tests/test_cli.py`
- Modify: `tests/fixtures/cli_help_expected.txt`

- [x] Write failing CLI tests for `style-intent-report --style <text>` and optional `--discovery`.
- [x] Run: `pytest tests\test_style_intent_profiles.py tests\test_cli.py -q`
- [x] Add CLI dispatch and help text.
- [x] Run: `pytest tests\test_style_intent_profiles.py tests\test_cli.py -q`

### Task 3: Docs And Verification

**Files:**
- Modify: `docs/FUTURE_AUDIO_ANALYZER_REFERENCE_DISCOVERY.md`
- Modify: `docs/FUTURE_ANALOG_FOUR_EXPANSION.md`
- Modify: `docs/PASSIVE_CLI_OPERATOR_QUICKSTART.md`
- Modify: `docs/STATUS.md`

- [x] Update docs with style-intent kit design and Analog Four future target.
- [x] Run: `pytest tests\test_style_intent_profiles.py tests\test_essence_tag_adapter.py tests\test_essence_plan_report.py tests\test_machine_catalog.py tests\test_cli.py tests\architecture\test_no_side_effects.py -q`
- [x] Run: `python -m rytm_randomizer.cli style-intent-report --style "Birmingham dark techno"`
- [x] Run: `git diff --check`

### Task 4: Style Intent Readiness Gate

**Files:**
- Modify: `rytm_randomizer/essence_application.py`
- Modify: `rytm_randomizer/cli.py`
- Modify: `rytm_randomizer/help_text.py`
- Modify: `tests/test_essence_application.py`
- Modify: `docs/PASSIVE_CLI_OPERATOR_QUICKSTART.md`
- Modify: `docs/STATUS.md`

- [x] Write failing CLI tests for `essence-application-readiness-report --style <text>` using profile Discovery hints and explicit override.
- [x] Run: `pytest tests\test_essence_application.py -q`
- [x] Add passive style-intent source metadata to readiness reports.
- [x] Wire `--style` into the existing readiness command without adding MIDI, SysEx receive, or runtime mutation.
