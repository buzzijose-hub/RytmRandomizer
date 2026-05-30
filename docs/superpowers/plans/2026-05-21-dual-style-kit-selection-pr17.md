# Dual Style Kit Selection Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a passive report that turns Rytm/A4 style kit-readiness sweeps into a ranked live operator selection for dual-machine, Rytm-only, or Analog Four-only snapshot use.

**Architecture:** Build on the existing report layer introduced by the style readiness work. The new module composes `rytm_style_kit_readiness`, `analog_four_style_kit_readiness`, and `dual_machine_style_kit_readiness`; it never decodes MIDI ports, renders real MIDI, or mutates hardware.

**Tech Stack:** Python dataclasses, passive CLI registry, existing style discovery policy, existing SysEx/readiness report modules, pytest fast tests, architecture gates, coverage.

---

## File Structure

- Create `rytm_randomizer/reports/dual_machine_style_kit_selection.py`
  - Defines selection dataclasses, passive builders, text formatter, JSON formatter, parser, CLI handler, safety lines, and command registration.
  - Accepts `--scope dual`, `--scope rytm-only`, `--scope analog-four-only`, and alias `--scope a4-only`.
  - Supports automatic scope selection: both paths means `dual`; only Rytm means `rytm-only`; only A4 means `analog-four-only`.
- Create `tests/test_dual_machine_style_kit_selection.py`
  - Covers dual, Rytm-only, A4-only, parser validation, JSON, text formatting, and CLI handlers.
- Modify `rytm_randomizer/cli.py`
  - Adds lazy registration for `dual-machine-style-kit-selection-report`.
- Modify `rytm_randomizer/help_text.py`
  - Adds top-level usage, command summary, dynamic help entry, and safety block.
- Modify `tests/test_cli.py`
  - Updates usage fixture expectations and checks command help is available.
- Modify `tests/test_cli_coverage.py`
  - Adds command-specific dynamic help coverage and registry fallback coverage.
- Modify `tests/test_real_midi_passive_cli_safety.py`
  - Confirms the new command help path remains passive and does not import real MIDI modules.
- Modify `tests/fixtures/cli_help_expected.txt`
  - Updates byte-stable passive CLI help fixture.
- Modify `README.md`
  - Adds an operator example for dual-machine and single-machine style kit selection.
- Modify `docs/STATUS.md`
  - Notes the new passive selection layer and its current hardware boundary.

## Task 1: Selection Report Behavior

**Files:**
- Create: `tests/test_dual_machine_style_kit_selection.py`
- Create: `rytm_randomizer/reports/dual_machine_style_kit_selection.py`

- [ ] **Step 1: Write failing tests for dual and single-machine selection**

```python
def test_dual_machine_style_kit_selection_defaults_to_dual_when_both_paths(tmp_path):
    report = build_dual_machine_style_kit_selection_report(
        "jose_core_techno",
        rytm_sysex_path=rytm_path,
        analog_four_sysex_path=a4_path,
    )
    assert report.scope == "dual"
    assert report.candidate_count == 4
    assert report.entries[0].selection_readiness == "partial"
    assert report.entries[0].rytm_choice is not None
    assert report.entries[0].analog_four_choice is not None
```

```python
def test_dual_machine_style_kit_selection_supports_rytm_only_scope(tmp_path):
    report = build_dual_machine_style_kit_selection_report(
        "jose_core_techno",
        rytm_sysex_path=rytm_path,
        scope="rytm-only",
    )
    assert report.scope == "rytm-only"
    assert report.entries[0].analog_four_choice is None
    assert "leave Analog Four unchanged" in report.entries[0].operator_action
```

- [ ] **Step 2: Run tests to verify RED**

Run: `python -m pytest tests\test_dual_machine_style_kit_selection.py -n 0`

Expected: FAIL because `rytm_randomizer.reports.dual_machine_style_kit_selection` does not exist.

- [ ] **Step 3: Implement report dataclasses and builder**

Create:
- `StyleKitSelectionMachineChoice`
- `DualMachineStyleKitSelectionEntry`
- `DualMachineStyleKitSelectionReport`
- `normalize_selection_scope`
- `build_dual_machine_style_kit_selection_report`

The builder reuses existing readiness builders and ranks entries by readiness, score, and slot order. It validates that required paths exist for the requested scope.

- [ ] **Step 4: Run tests to verify GREEN**

Run: `python -m pytest tests\test_dual_machine_style_kit_selection.py -n 0`

Expected: PASS for report behavior tests.

## Task 2: Formatting, JSON, and CLI Parser

**Files:**
- Modify: `tests/test_dual_machine_style_kit_selection.py`
- Modify: `rytm_randomizer/reports/dual_machine_style_kit_selection.py`

- [ ] **Step 1: Write failing tests for formatter, JSON, parser, and handler**

Tests assert:
- Text output includes scope, selection readiness counts, selected kit slots, fingerprints, and safety boundaries.
- JSON output includes `scope`, `candidate_count`, `entries`, `rytm`, `analog_four`, and safety.
- Parser supports `--rytm`, `--analog-four`, `--scope`, `--discovery`, `--limit`, and `--json`.
- Parser rejects missing required machine paths for the selected scope.

- [ ] **Step 2: Run tests to verify RED**

Run: `python -m pytest tests\test_dual_machine_style_kit_selection.py -n 0`

Expected: FAIL because formatter/parser/handler functions are missing.

- [ ] **Step 3: Implement formatters, JSON, parser, and command registration**

Add:
- `format_dual_machine_style_kit_selection_report`
- `to_dual_machine_style_kit_selection_json`
- `_parse_cli_args`
- `_handle_cli_report`
- `DUAL_MACHINE_STYLE_KIT_SELECTION_CLI_COMMAND`

- [ ] **Step 4: Run tests to verify GREEN**

Run: `python -m pytest tests\test_dual_machine_style_kit_selection.py -n 0`

Expected: PASS.

## Task 3: CLI, Help, Docs, and Safety Wiring

**Files:**
- Modify: `rytm_randomizer/cli.py`
- Modify: `rytm_randomizer/help_text.py`
- Modify: `tests/test_cli.py`
- Modify: `tests/test_cli_coverage.py`
- Modify: `tests/test_real_midi_passive_cli_safety.py`
- Modify: `tests/fixtures/cli_help_expected.txt`
- Modify: `README.md`
- Modify: `docs/STATUS.md`

- [ ] **Step 1: Write failing CLI/help/safety tests**

Tests assert:
- `python -m rytm_randomizer.cli dual-machine-style-kit-selection-report --help` prints command help.
- Top-level help includes the new command and usage.
- The passive safety sweep includes the command help path.
- CLI lazy registration includes the new report module.

- [ ] **Step 2: Run tests to verify RED**

Run:

```powershell
python -m pytest tests\test_dual_machine_style_kit_selection.py tests\test_cli.py tests\test_cli_coverage.py tests\test_real_midi_passive_cli_safety.py -n 0
```

Expected: FAIL because CLI/help wiring is missing.

- [ ] **Step 3: Implement CLI/help/docs wiring**

Add the command to lazy registration, help text, help fixture, passive safety tuples, README examples, and status notes.

- [ ] **Step 4: Run focused tests to verify GREEN**

Run:

```powershell
python -m pytest tests\test_dual_machine_style_kit_selection.py tests\test_cli.py tests\test_cli_coverage.py tests\test_real_midi_passive_cli_safety.py -n 0
```

Expected: PASS.

## Task 4: Verification and PR

**Files:**
- All changed files in this plan.

- [ ] **Step 1: Run required focused verification**

Run:

```powershell
python -m pytest tests\test_dual_machine_style_kit_selection.py tests\test_dual_machine_style_kit_readiness.py tests\test_rytm_style_kit_readiness.py tests\test_analog_four_style_kit_readiness.py tests\test_cli.py tests\test_cli_coverage.py tests\test_real_midi_passive_cli_safety.py -n 0
```

- [ ] **Step 2: Run architecture, lint, fast, full, coverage, and review gates**

Run:

```powershell
python -m ruff check .
python -m black --check --target-version=py311 .
python -m isort --profile black --check-only .
python -m pytest tests/architecture/ -q
python -m pytest -m fast
python -m pytest
python -m pytest --cov=rytm_randomizer --cov-branch --cov-report=term-missing
python scripts\code_review_gate.py --mode cli
```

- [ ] **Step 3: Stage only intended files**

Run `git status --short`, then stage only files listed in this plan. Preserve unrelated checkout/CRLF/parity noise.

- [ ] **Step 4: Commit, push, and open PR**

Commit message: `feat: add dual-machine style kit selection`

Open a PR against `modularize-v1.34` with the 18-gate checklist and a link to this plan.
