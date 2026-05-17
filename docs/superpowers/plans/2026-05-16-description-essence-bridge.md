# Description Essence Bridge Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let the passive essence-plan preview derive broad musical essence tags from a written reference description or existing style feature report.

**Architecture:** Add a small pure adapter module that maps description keywords and `FeatureReport` measurements into deterministic essence tags. Extend `essence-plan-report` with `--description <text>` while preserving the existing `--tags <csv>` path.

**Tech Stack:** Python standard library, existing `rytm_randomizer.style_analysis.FeatureReport`, pytest, passive CLI subprocess tests.

---

### Task 1: Passive Essence Tag Adapter

**Files:**
- Create: `rytm_randomizer/essence_tag_adapter.py`
- Test: `tests/test_essence_tag_adapter.py`

- [x] Write failing tests for description-to-tag mapping, track/artist-name hygiene, feature-report mapping, deterministic merge order, and import safety.
- [x] Run: `pytest tests\test_essence_tag_adapter.py -q`
- [x] Implement `derive_essence_tags_from_description()` and `derive_essence_tags_from_feature_report()`.
- [x] Run: `pytest tests\test_essence_tag_adapter.py -q`

### Task 2: CLI Description Input

**Files:**
- Modify: `rytm_randomizer/cli.py`
- Modify: `rytm_randomizer/help_text.py`
- Modify: `tests/test_essence_plan_report.py`
- Modify: `tests/test_cli.py`
- Modify: `tests/fixtures/cli_help_expected.txt`

- [x] Write failing CLI tests for `essence-plan-report --description <text> --discovery <0..1>`.
- [x] Run: `pytest tests\test_essence_plan_report.py tests\test_cli.py -q`
- [x] Extend CLI parsing and help text.
- [x] Run: `pytest tests\test_essence_plan_report.py tests\test_cli.py -q`

### Task 3: Checkpoint Docs And Verification

**Files:**
- Modify: `docs/MACHINE_CATALOG_ESSENCE_MATCHER_CHECKPOINT.md`
- Modify: `docs/FUTURE_AUDIO_ANALYZER_REFERENCE_DISCOVERY.md`
- Modify: `docs/PASSIVE_CLI_OPERATOR_QUICKSTART.md`
- Modify: `docs/STATUS.md`

- [x] Update docs to describe description-derived tags as a passive bridge toward later audio analysis.
- [x] Run: `pytest tests\test_essence_tag_adapter.py tests\test_essence_plan_report.py tests\test_machine_catalog.py tests\test_cli.py tests\architecture\test_no_side_effects.py tests\test_style_analysis.py -q`
- [x] Run: `python -m rytm_randomizer.cli essence-plan-report --description "metallic bell driving repetition Detroit techno" --discovery 1.0`
- [x] Run: `git diff --check`
