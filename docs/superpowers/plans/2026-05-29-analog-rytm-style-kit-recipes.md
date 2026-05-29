# Analog Rytm Style Kit Recipes Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add curated full-12-pad Analog Rytm style-kit recipes with dry-run rendering and explicit-confirmation armed CC sending.

**Architecture:** Recipe facts live in `rytm_randomizer/data/analog_rytm_style_recipes.py` and resolve through the existing manual-backed Rytm MIDI catalog. `rytm_randomizer/app.py` owns the dry-run/armed command boundary and reuses the existing mido provider plus `midi_io.send_cc`.

**Tech Stack:** Python 3.11 stdlib, frozen dataclasses, `MappingProxyType`, existing app CLI, existing `send_cc`, pytest with fake mido seams.

---

## File Structure

- Create: `rytm_randomizer/data/analog_rytm_style_recipes.py`
  - Curated recipe dataclasses, recipe constants, validation, and render helper.
- Modify: `rytm_randomizer/data/__init__.py`
  - Re-export only the uppercase recipe registry constant.
- Modify: `rytm_randomizer/app.py`
  - Add `--rytm-kit-style` and `--confirm-rytm-kit-send`; add dry-run and armed send handlers.
- Create: `tests/test_analog_rytm_style_recipes.py`
  - Recipe coverage, safety exclusions, legal machine validation, and deterministic render tests.
- Modify: `tests/test_app_validate_one_cc.py`
  - App-level dry-run, confirmation refusal, and armed fake-mido send tests.
- Modify: `README.md`, `docs/MANUAL_HARDWARE_VALIDATION.md`, `docs/STATUS.md`
  - Document the style-kit sender and hardware boundary.

## Tasks

### Task 1: Recipe Data Tests

- [ ] Add `tests/test_analog_rytm_style_recipes.py`.
- [ ] Assert recipe names are exactly `detroit-deep`, `deeper-rolling`, `hard-groove`, `banging-warehouse`, `hypnotic-pressure`, and `mills-drive`.
- [ ] Assert every recipe covers pads 1 through 12.
- [ ] Assert every pad uses a legal machine from `RYTM_PAD_CAPABILITIES`.
- [ ] Assert rendering emits one machine-select event per pad and at least one tone event per pad.
- [ ] Assert rendered events avoid samples, performance macros, track/source/amp volume, mute, solo, and LFO destination.
- [ ] Run the new test file and confirm it fails because the module does not exist yet.

### Task 2: Recipe Data Implementation

- [ ] Create `rytm_randomizer/data/analog_rytm_style_recipes.py`.
- [ ] Add frozen dataclasses:
  - `AnalogRytmStyleParameter`
  - `AnalogRytmStylePad`
  - `AnalogRytmStyleRecipe`
  - `AnalogRytmRenderedStyleEvent`
- [ ] Add `ANALOG_RYTM_STYLE_RECIPES` with the six curated styles.
- [ ] Add `render_analog_rytm_style_recipe(recipe)` returning deterministic rendered events.
- [ ] Re-export `ANALOG_RYTM_STYLE_RECIPES` from `data/__init__.py`.
- [ ] Run the recipe data tests and confirm they pass.

### Task 3: App Command Tests

- [ ] Extend `tests/test_app_validate_one_cc.py`.
- [ ] Assert `--dry-run --rytm-kit-style detroit-deep` prints mock-only/full-kit output and imports no real MIDI.
- [ ] Assert `--arm --rytm-kit-style detroit-deep` refuses before listing ports when `--confirm-rytm-kit-send` is missing.
- [ ] Assert `--arm --rytm-kit-style detroit-deep --confirm-rytm-kit-send` sends fake mido control-change messages and closes the port.
- [ ] Assert style-kit flags conflict with A4 and one-CC helper flags.
- [ ] Run the added app tests and confirm they fail because app wiring does not exist yet.

### Task 4: App Command Implementation

- [ ] Add parser arguments in `app.py`.
- [ ] Add `_resolve_rytm_style_recipe`.
- [ ] Add `_send_rytm_style_events`.
- [ ] Add `_run_dry_run_rytm_kit_style`.
- [ ] Add `_run_armed_rytm_kit_style`.
- [ ] Add conflict checks in `main`.
- [ ] Run the app tests and recipe tests.

### Task 5: Docs And Verification

- [ ] Update README with dry-run and armed command examples.
- [ ] Update manual hardware validation with disposable-kit guidance.
- [ ] Update status with the new active Rytm style-kit boundary.
- [ ] Run targeted tests.
- [ ] Run `python -m pytest tests/architecture/ -q`.
- [ ] Run `python -m pytest -m fast`.
- [ ] Run `python -m pytest`.
- [ ] Run `python -m ruff check .`, `python -m black --check --target-version=py311 .`, and `python -m isort --profile black --check-only .`.

## Safety Boundary

This plan intentionally avoids source level, track level, amp volume, samples,
performance macros, transport, pattern changes, kit saves, project writes, and
SysEx. The armed path requires both `--arm` and `--confirm-rytm-kit-send`.
