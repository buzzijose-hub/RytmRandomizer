# Mock 12-Pad Snapshot Fixtures Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add passive 12-pad snapshot fixtures and use them in Live Snapshot readiness.

**Architecture:** Create `rytm_randomizer.snapshot_fixtures` for immutable fixture metadata, then extend `rytm_randomizer.essence_application` so Live Snapshot readiness can consider captured machine support per pad. Add CLI support for `--fixture <key>` on the existing readiness command.

**Tech Stack:** Python dataclasses, existing machine catalog support status, existing passive CLI and pytest subprocess tests.

---

### Task 1: Snapshot Fixture Module

**Files:**
- Create: `rytm_randomizer/snapshot_fixtures.py`
- Test: `tests/test_snapshot_fixtures.py`

- [x] Write failing tests for passive import safety, 12-pad AM9 fixture shape, fixture lookup, snapshot-state conversion, and report formatting.
- [x] Run: `pytest tests\test_snapshot_fixtures.py -q`
- [x] Implement immutable fixture dataclasses, `get_snapshot_fixture()`, `list_snapshot_fixtures()`, `snapshot_state_from_fixture()`, and `format_snapshot_fixture_report()`.
- [x] Run: `pytest tests\test_snapshot_fixtures.py -q`

### Task 2: Readiness Integration

**Files:**
- Modify: `rytm_randomizer/essence_application.py`
- Modify: `tests/test_essence_application.py`

- [x] Write failing tests showing a fixture with unmapped captured machines blocks those pads in Live Snapshot readiness.
- [x] Run: `pytest tests\test_essence_application.py tests\test_snapshot_fixtures.py -q`
- [x] Add optional `snapshot_fixture` support to readiness evaluation and report formatting.
- [x] Run: `pytest tests\test_essence_application.py tests\test_snapshot_fixtures.py -q`

### Task 3: CLI Fixture Option And Docs

**Files:**
- Modify: `rytm_randomizer/cli.py`
- Modify: `rytm_randomizer/help_text.py`
- Modify: `tests/test_essence_application.py`
- Modify: `tests/test_cli.py`
- Modify: `tests/fixtures/cli_help_expected.txt`
- Modify: `docs/LIVE_SNAPSHOT_MODE_DESIGN_CHECKPOINT.md`
- Modify: `docs/SYSEX_KIT_BANK_ANALYZER_CHECKPOINT.md`
- Modify: `docs/PASSIVE_CLI_OPERATOR_QUICKSTART.md`
- Modify: `docs/STATUS.md`

- [x] Write failing CLI tests for `--fixture am9-slot-01`.
- [x] Run: `pytest tests\test_essence_application.py tests\test_cli.py -q`
- [x] Add help text, CLI parsing, and docs.
- [x] Run: `pytest tests\test_snapshot_fixtures.py tests\test_essence_application.py tests\test_essence_tag_adapter.py tests\test_essence_plan_report.py tests\test_machine_catalog.py tests\test_performance_modes.py tests\test_cli.py tests\architecture\test_no_side_effects.py -q`
- [x] Run: `python -m rytm_randomizer.cli essence-application-readiness-report --mode live-snapshot --description "metallic bell driving repetition Detroit techno" --discovery 0.35 --fixture am9-slot-01`
- [x] Run: `git diff --check`
