# Rytm Style Render Mock Preview PR11 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add the next passive Rytm style bridge: encode Jose Core Techno as a first-class style target, then turn Rytm style render-plan target values into mock-safe CC preview rows.

**Architecture:** Keep all device-specific behavior inside `rytm_randomizer/devices/strategies/`. The new mock-preview strategy consumes the PR10 render-plan dataclasses, reuses the Rytm message renderer for mock CC resolution, and exposes a report/CLI command that stays passive: no MIDI ports, no hardware sends, no real runtime dispatch.

**Tech Stack:** Python 3.11, frozen dataclasses, `MappingProxyType`, existing Rytm `Device`/Strategy boundary, existing passive CLI registry, pytest fast/focused tests.

---

### Task 1: Jose Core Techno Style Data

**Files:**
- Modify: `rytm_randomizer/data/style_profiles.py`
- Modify: `rytm_randomizer/data/style_targets.py`
- Modify: `tests/test_data_layer.py`
- Modify: `tests/test_style_targets_report.py`

- [ ] **Step 1: Write failing style-data tests**

Add assertions that `jose_core_techno` exists, references Jeff Mills/Oscar Mulero/Stigmata/Birmingham-style pressure through tags/focus text, and has high drive, hypnosis, darkness, metallicity, industrial edge, and warehouse intensity target values.

- [ ] **Step 2: Verify RED**

Run: `python -m pytest tests/test_data_layer.py::test_style_profiles_cover_core_techno_aesthetic_targets tests/test_style_targets_report.py::test_style_target_vectors_encode_expected_musical_intent -n 0`

Expected: fails because `jose_core_techno` is not in the style catalog yet.

- [ ] **Step 3: Implement style profile and target vector**

Add one `StyleProfile` and one `_target("jose_core_techno", ...)` entry. Keep the target vector bounded 0-100 and the profile passive design data only.

- [ ] **Step 4: Verify GREEN**

Run the same focused command and confirm it passes.

### Task 2: Rytm Style Render Mock Strategy

**Files:**
- Create: `rytm_randomizer/devices/strategies/analog_rytm_style_mutation_mock_preview.py`
- Modify: `rytm_randomizer/devices/strategies/__init__.py`
- Create: `tests/test_rytm_style_mutation_mock_preview.py`

- [ ] **Step 1: Write failing mock-preview tests**

Tests should prove a promoted Rytm snapshot plus `jose_core_techno` builds deterministic mock rows with CC/channel/value metadata, preserves render-plan window context, refuses blocked/selectable-only pads, and raises for unknown styles.

- [ ] **Step 2: Verify RED**

Run: `python -m pytest tests/test_rytm_style_mutation_mock_preview.py -n 0`

Expected: import failure because the new strategy/report module does not exist yet.

- [ ] **Step 3: Implement the strategy**

Create frozen dataclasses for `RytmStyleMutationMockPreviewEvent` and `RytmStyleMutationMockPreview`. Build `RytmPlanEvent` rows from render-ready PR10 events, pass a `RytmMutationPlan` through the Rytm message renderer's mock conversion path, and combine returned `MidiMessage` rows with render-window metadata.

- [ ] **Step 4: Verify GREEN**

Run: `python -m pytest tests/test_rytm_style_mutation_mock_preview.py -n 0`

Expected: all new mock-preview strategy tests pass.

### Task 3: Passive Report + CLI

**Files:**
- Create: `rytm_randomizer/reports/rytm_style_mutation_mock_preview.py`
- Modify: `rytm_randomizer/cli.py`
- Modify: `rytm_randomizer/help_text.py`
- Modify: `tests/test_cli.py`
- Modify: `tests/test_cli_coverage.py`
- Modify: `tests/test_real_midi_passive_cli_safety.py`
- Modify: `tests/fixtures/cli_help_expected.txt`

- [ ] **Step 1: Write failing report/CLI tests**

Add tests for text output, JSON output, `--events`/`--limit`, bad-argument handling, help resolution, top-level help visibility, and passive safety.

- [ ] **Step 2: Verify RED**

Run: `python -m pytest tests/test_rytm_style_mutation_mock_preview.py tests/test_cli.py tests/test_cli_coverage.py tests/test_real_midi_passive_cli_safety.py -n 0 -k "style_mutation_mock_preview or top_level_help or passive_cli"`

Expected: fails until the command/report exists.

- [ ] **Step 3: Implement report and lazy CLI registration**

Register `rytm-style-mutation-mock-preview-report <syx-path> <style-key> [--slot N] [--discovery N] [--events] [--limit N] [--json]`. Safety lines must say mock-only preview, no MIDI sending, no port opening, no hardware mutation, no hardware required.

- [ ] **Step 4: Verify GREEN**

Run the same focused command and update `tests/fixtures/cli_help_expected.txt` from actual `--help` output only after the focused assertions pass.

### Task 4: Docs, Review, and PR

**Files:**
- Modify: `README.md`
- Modify: `docs/STATUS.md`
- Modify: `docs/ARCHITECTURE_DIAGRAMS.md`

- [ ] **Step 1: Update operator docs**

Document the Jose Core style key and the new mock-preview command. Clarify this still does not open MIDI ports or send hardware.

- [ ] **Step 2: Run required verification**

Run:

```powershell
python -m pytest tests/test_rytm_style_mutation_mock_preview.py -n 0
python -m pytest tests/architecture/ -q
python -m pytest -m fast
python -m pytest
python -m pytest --cov=rytm_randomizer --cov-branch --cov-report=term-missing
python -m ruff check .
python -m black --check --target-version=py311 .
python -m isort --profile black --check-only .
python scripts/code_review_gate.py --mode cli
```

- [ ] **Step 3: Commit, push, open PR**

Stage only intentional PR11 files; preserve unrelated CRLF/parity checkout noise. Open one PR against `modularize-v1.34` with the required 18-gate checklist and this plan linked.
