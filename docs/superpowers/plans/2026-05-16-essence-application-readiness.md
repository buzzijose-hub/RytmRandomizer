# Essence Application Readiness Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a passive report that explains whether a 12-pad essence plan can be applied under Safe Anchors or Live Snapshot, and why not when blocked.

**Architecture:** Create `rytm_randomizer.essence_application` as a pure metadata layer over `machine_catalog`, `essence_tag_adapter`, and `performance_modes.SnapshotState`. Add a passive CLI command that formats the readiness gate without touching MIDI or hardware.

**Tech Stack:** Python standard library dataclasses, existing passive modules, pytest subprocess CLI tests.

---

### Task 1: Readiness Model

**Files:**
- Create: `rytm_randomizer/essence_application.py`
- Test: `tests/test_essence_application.py`

- [x] Write failing tests for import safety, Safe Anchors partial readiness, Live Snapshot blocked-without-capture, Live Snapshot complete snapshot readiness, and future-only machine blocking.
- [x] Run: `pytest tests\test_essence_application.py -q`
- [x] Implement the dataclasses and `evaluate_essence_application_readiness()`.
- [x] Run: `pytest tests\test_essence_application.py -q`

### Task 2: CLI Report

**Files:**
- Modify: `rytm_randomizer/cli.py`
- Modify: `rytm_randomizer/help_text.py`
- Modify: `tests/test_essence_application.py`
- Modify: `tests/test_cli.py`
- Modify: `tests/fixtures/cli_help_expected.txt`

- [x] Write failing CLI tests for `essence-application-readiness-report`.
- [x] Run: `pytest tests\test_essence_application.py tests\test_cli.py -q`
- [x] Add help text and CLI dispatch.
- [x] Run: `pytest tests\test_essence_application.py tests\test_cli.py -q`

### Task 3: Docs And Verification

**Files:**
- Modify: `docs/LIVE_SNAPSHOT_MODE_DESIGN_CHECKPOINT.md`
- Modify: `docs/MACHINE_CATALOG_ESSENCE_MATCHER_CHECKPOINT.md`
- Modify: `docs/PASSIVE_CLI_OPERATOR_QUICKSTART.md`
- Modify: `docs/STATUS.md`

- [x] Update docs with the passive readiness gate and current blocked reasons.
- [x] Run: `pytest tests\test_essence_application.py tests\test_essence_tag_adapter.py tests\test_essence_plan_report.py tests\test_machine_catalog.py tests\test_performance_modes.py tests\test_cli.py tests\architecture\test_no_side_effects.py -q`
- [x] Run: `python -m rytm_randomizer.cli essence-application-readiness-report --mode live-snapshot --description "metallic bell driving repetition Detroit techno" --discovery 1.0 --snapshot captured`
- [x] Run: `git diff --check`
