# Live Performance Set Plan Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a passive dual-machine performance set planner that turns ordered techno style targets into a time-boxed Rytm plus Analog Four audition roadmap for live preparation.

**Architecture:** Add one report module under `rytm_randomizer/reports/` that composes the existing dual-machine style selection mock preview path. The report never opens MIDI ports, never sends MIDI, and exposes text plus JSON contracts for future GUI/analyzer use.

**Tech Stack:** Python dataclasses, existing `CliCommand` registry, existing style discovery policy, existing dual-machine selection/mock-preview reports, pytest, ruff, black, isort.

---

## Why

Jose needs fewer approval cycles and a more complete feature slice. The current style pipeline can select saved kits and preview one or more style targets, but it does not yet organize those targets into a 5-hour performance arc with segment timing, discovery pressure, machine scope, and operator cues. This PR turns the previous live audition report into a higher-level show-planning surface while staying passive/mock-safe.

## File Structure

- Create `rytm_randomizer/reports/dual_machine_style_performance_set_plan.py`
  - Owns the performance set dataclasses, discovery ramp, segment timing, text formatter, JSON formatter, CLI parser, and registered command.
- Modify `rytm_randomizer/reports/dual_machine_style_selection_mock_preview.py`
  - Add a shared public event-row formatter so live audition and set-plan reports do not duplicate Rytm/A4 row formatting.
- Modify `rytm_randomizer/reports/dual_machine_style_live_audition.py`
  - Consume the shared event-row formatter and remove duplicate private row-format helpers.
- Modify `rytm_randomizer/cli.py`
  - Lazy-register `dual-machine-style-performance-set-plan-report`.
- Modify `rytm_randomizer/help_text.py`
  - Add top-level usage, dynamic help text, and command listing for the new report.
- Modify `tests/test_dual_machine_style_performance_set_plan_report.py`
  - New focused tests for plan building, discovery ramp, scopes, event previews, JSON, parser, and handler.
- Modify `tests/test_dual_machine_style_live_audition_report.py`
  - Remove the private A4 event-row test once the row formatter lives in the shared mock-preview report.
- Modify `tests/test_dual_machine_style_selection_mock_preview_report.py`
  - Add coverage for the shared event-row helper.
- Modify `tests/test_cli.py`, `tests/test_cli_coverage.py`, `tests/test_real_midi_passive_cli_safety.py`, `tests/fixtures/cli_help_expected.txt`
  - Cover help, lazy import, top-level help text, and passive safety.
- Modify `README.md` and `docs/STATUS.md`
  - Document the operator-facing command and the milestone.

## Task 1: Carry Forward Shared Event Rows

**Files:**
- Modify: `rytm_randomizer/reports/dual_machine_style_selection_mock_preview.py`
- Modify: `rytm_randomizer/reports/dual_machine_style_live_audition.py`
- Modify: `tests/test_dual_machine_style_selection_mock_preview_report.py`
- Modify: `tests/test_dual_machine_style_live_audition_report.py`

- [ ] **Step 1: Write/adjust tests first**

Add a test proving `format_dual_machine_style_selection_mock_preview_event_rows(plan)` returns both Rytm and A4 event rows from a selection mock preview plan. Remove the live-audition test that imports the private `_format_analog_four_event_row`.

- [ ] **Step 2: Run the focused test and verify RED**

Run:

```powershell
& "C:\Users\Jose Buzzi\AppData\Local\Programs\Python\Python313\python.exe" -m pytest tests\test_dual_machine_style_selection_mock_preview_report.py::test_selection_mock_preview_formats_shared_event_rows -n 0
```

Expected: FAIL because the shared formatter does not exist yet.

- [ ] **Step 3: Implement the shared formatter**

Move the existing private event-row logic into `dual_machine_style_selection_mock_preview.py` as a public helper and export it. Update live audition to call it.

- [ ] **Step 4: Run focused tests and verify GREEN**

Run:

```powershell
& "C:\Users\Jose Buzzi\AppData\Local\Programs\Python\Python313\python.exe" -m pytest tests\test_dual_machine_style_selection_mock_preview_report.py tests\test_dual_machine_style_live_audition_report.py -n 0
```

Expected: PASS.

## Task 2: Add Performance Set Plan Core

**Files:**
- Create: `rytm_randomizer/reports/dual_machine_style_performance_set_plan.py`
- Test: `tests/test_dual_machine_style_performance_set_plan_report.py`

- [ ] **Step 1: Write failing builder and formatter tests**

Test that a plan built from `("jose_core_techno", "birmingham_pressure", "warehouse_peak")`, saved Rytm/A4 kit banks, and `total_minutes=300` produces three segments with deterministic time windows, discovery values, selection readiness counts, event counts, and per-machine summaries.

- [ ] **Step 2: Run RED**

Run:

```powershell
& "C:\Users\Jose Buzzi\AppData\Local\Programs\Python\Python313\python.exe" -m pytest tests\test_dual_machine_style_performance_set_plan_report.py -n 0
```

Expected: FAIL because the module does not exist.

- [ ] **Step 3: Implement minimal report dataclasses and builder**

Use frozen dataclasses:

- `DualMachineStylePerformanceSetSegment`
- `DualMachineStylePerformanceSetPlan`

Compose `build_dual_machine_style_selection_mock_preview_report(...)` once per segment. Use a deterministic discovery ramp from `discovery_start` to `discovery_end`, inclusive, rounded to integer values. Infer equal segment windows from `total_minutes` when `segment_minutes` is omitted.

- [ ] **Step 4: Implement text and JSON formatters**

Use `passive_report_lines(...)`, `PassiveReportHeader`, and safety lines inherited from selection mock preview. Include set duration, segment count, scope, discovery ramp, readiness totals, segment windows, operator action, machine summary, optional event previews, and safety.

- [ ] **Step 5: Run focused tests and verify GREEN**

Run the same focused test file. Expected: PASS.

## Task 3: Wire CLI, Help, Passive Safety

**Files:**
- Modify: `rytm_randomizer/cli.py`
- Modify: `rytm_randomizer/help_text.py`
- Modify: `tests/test_cli.py`
- Modify: `tests/test_cli_coverage.py`
- Modify: `tests/test_real_midi_passive_cli_safety.py`
- Modify: `tests/fixtures/cli_help_expected.txt`

- [ ] **Step 1: Write CLI/help tests first**

Add tests for:

- `dual-machine-style-performance-set-plan-report --help`
- top-level `--help` listing
- lazy import when registry and module are unloaded
- passive sweep with no real MIDI or adapter modules

- [ ] **Step 2: Run RED**

Run:

```powershell
& "C:\Users\Jose Buzzi\AppData\Local\Programs\Python\Python313\python.exe" -m pytest tests\test_cli.py::test_dual_machine_style_performance_set_plan_report_help_exits_zero_and_safety_matches_source tests\test_cli_coverage.py::test_main_dual_machine_style_performance_set_plan_report_lazy_imports_when_unloaded tests\test_real_midi_passive_cli_safety.py -n 0
```

Expected: FAIL because the command is not wired yet.

- [ ] **Step 3: Implement CLI and help wiring**

Add the lazy command entry to `cli.py`, add dynamic help text to `help_text.py`, update top-level usage and command list, and update `cli_help_expected.txt`.

- [ ] **Step 4: Run focused CLI tests and verify GREEN**

Run:

```powershell
& "C:\Users\Jose Buzzi\AppData\Local\Programs\Python\Python313\python.exe" -m pytest tests\test_cli.py tests\test_cli_coverage.py tests\test_real_midi_passive_cli_safety.py -n 0
```

Expected: PASS.

## Task 4: Docs and Verification

**Files:**
- Modify: `README.md`
- Modify: `docs/STATUS.md`
- Modify: PR body file under local scratch path only

- [ ] **Step 1: Update docs**

Add the new command to the README examples near the existing dual-machine style reports. Add one dated `docs/STATUS.md` recent cleanup entry explaining that the live performance set plan is passive and mock-safe.

- [ ] **Step 2: Run focused related tests**

Run:

```powershell
& "C:\Users\Jose Buzzi\AppData\Local\Programs\Python\Python313\python.exe" -m pytest tests\test_dual_machine_style_performance_set_plan_report.py tests\test_dual_machine_style_live_audition_report.py tests\test_dual_machine_style_selection_mock_preview_report.py tests\test_cli.py tests\test_cli_coverage.py tests\test_real_midi_passive_cli_safety.py -n 0
```

Expected: PASS.

- [ ] **Step 3: Run architecture and lint gates**

Run:

```powershell
& "C:\Users\Jose Buzzi\AppData\Local\Programs\Python\Python313\python.exe" -m pytest tests\architecture\ -q
& "C:\Users\Jose Buzzi\AppData\Local\Programs\Python\Python313\python.exe" -m ruff check .
& "C:\Users\Jose Buzzi\AppData\Local\Programs\Python\Python313\python.exe" -m black --check --target-version=py311 .
& "C:\Users\Jose Buzzi\AppData\Local\Programs\Python\Python313\python.exe" -m isort --profile black --check-only .
```

Expected: PASS.

- [ ] **Step 4: Run full, fast, coverage, and review gates**

Run:

```powershell
& "C:\Users\Jose Buzzi\AppData\Local\Programs\Python\Python313\python.exe" -m pytest -m fast
& "C:\Users\Jose Buzzi\AppData\Local\Programs\Python\Python313\python.exe" -m pytest
& "C:\Users\Jose Buzzi\AppData\Local\Programs\Python\Python313\python.exe" -m pytest --cov=rytm_randomizer --cov-branch --cov-report=term-missing
& "C:\Users\Jose Buzzi\AppData\Local\Programs\Python\Python313\python.exe" scripts\code_review_gate.py --mode cli
```

Expected: PASS. Do not stage CRLF-only checkout noise or V1.34 parity fixture noise.

## Plan-Requirements Conformance

Per `docs/PLAN_REQUIREMENTS.md`, this PR is expected to satisfy:

- [x] Gate 1 (100% branch coverage on touched files) - new/touched report code gets focused tests and coverage run.
- [x] Gate 2 (V1.34 parity fixtures byte-identical) - no parity fixture changes are staged.
- [x] Gate 3 (lint/format/type clean) - ruff, black, and isort run before push.
- [x] Gate 4 (dead-code purge) - vulture/ruff unused checks run on touched files before push.
- [x] Gate 5 (docs updated before PR open) - README and STATUS updated.
- [x] Gate 6 (type-system hygiene) - frozen dataclasses, explicit public signatures, no `Any`.
- [x] Gate 7 (observability adoption) - N/A: passive report composition only, no hot-path state transition or CC send.
- [x] Gate 8 (test hygiene) - focused intent-named pytest tests.
- [x] Gate 9 (module organization hygiene) - new code lives under existing `reports/` subpackage.
- [x] Gate 10 (string-literal dispatch hygiene) - no new mode dispatch equality sites.
- [x] Gate 11 (shared fixtures) - tests reuse the existing Rytm fixture helper.
- [x] Gate 12 (module-level constants use `Final`) - new constants annotated.
- [x] Gate 13 (env vars require docs and safe default) - no new env vars.
- [x] Gate 14 (maintainability review) - plan asks the abstraction question and removes duplicate event-row formatting.
- [x] Gate 15 (learning phase) - N/A: no new reusable lesson expected unless review uncovers one.
- [x] Gate 16 (execution shape) - one clean-base bundled PR, no stacked PR.
- [x] Gate 17 (abstraction reuse and genericization) - consumes existing selection/mock-preview reports and shared event rows.
- [x] Gate 18 (architecture-doc and diagram freshness) - N/A: new passive CLI/report surface, no new subpackage/protocol/registry/device boundary.

## Rollback Plan

Revert the single PR. It removes the new passive report command and restores live audition to its pre-shared-helper event row formatting through the same diff.

## Done Criteria

- New command `dual-machine-style-performance-set-plan-report` works in text and JSON mode.
- Report supports dual, Rytm-only, and Analog-Four-only scopes without touching hardware.
- Existing live audition behavior remains green.
- Focused tests, architecture tests, lint trio, fast/full suite, coverage, and review gate pass.
- One PR is opened against `modularize-v1.34` with the full conformance checklist.
