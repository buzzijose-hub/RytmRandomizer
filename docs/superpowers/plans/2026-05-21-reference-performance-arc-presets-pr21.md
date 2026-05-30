# Reference Performance Arc Presets Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add passive reference/performance arc presets that turn Jose's artist and movement references into reusable style-key sequences for the existing dual-machine performance set planner.

**Architecture:** Curated reference arc facts live once in `rytm_randomizer/data/style_performance_arcs.py`. A passive report in `rytm_randomizer/reports/style_performance_arcs.py` lists, inspects, searches, and expands those arcs into `dual-machine-style-performance-set-plan-report` plans without opening MIDI ports or sending messages.

**Tech Stack:** Python 3.11 dataclasses, immutable `MappingProxyType` data tables, existing passive CLI registry, existing dual-machine style performance planner, pytest fast/architecture/full/coverage gates.

---

## Design

This PR adds an operator-facing layer above the style catalog:

- `jose_warehouse_five_hour` is the default full-performance arc: Jeff Mills and Oscar Mulero as primary references, Birmingham/Stigmata/Regis/Surgeon pressure as the hard middle, and deep dark hypnosis as the release/reset path.
- `mills_mulero_tunnel` focuses the hypnotic/dark tunnel side for shorter sets.
- `stigmata_birmingham_assault` focuses Chris Liebing/Andre Walter Stigmata-era pressure, Glenn Wilson/Nightshift, Thomas Krome, Kay D Smith, Regis, Surgeon, and Birmingham/industrial intensity.
- `hardgroove_detroit_machine_funk` keeps the funkier Detroit/hardgroove side ready for live pacing.

The report can be used two ways:

1. Metadata only: list/inspect/search arcs.
2. Plan expansion: provide a Rytm and/or A4 SysEx bank path and get the existing timed performance set plan using the arc's default style sequence, duration, discovery ramp, rank, and scope.

No hardware behavior changes. No V1.34 engine, scene, group, or MIDI parity behavior changes.

## Files

- Create `rytm_randomizer/data/style_performance_arcs.py`
  - Owns `StylePerformanceArcSegment`, `StylePerformanceArc`, and immutable `STYLE_PERFORMANCE_ARCS`.
- Modify `rytm_randomizer/data/__init__.py`
  - Re-export `STYLE_PERFORMANCE_ARCS`.
- Create `rytm_randomizer/reports/style_performance_arcs.py`
  - Builds/prints arc catalog, list, inspect, search, and plan-expanded reports.
  - Registers CLI commands.
- Modify `rytm_randomizer/cli.py`
  - Lazy-register the new passive commands.
- Modify `rytm_randomizer/help_text.py`
  - Add usage/help for `style-performance-arc-report`, `list-style-performance-arcs`, `inspect-style-performance-arc`, `search-style-performance-arcs`, and `style-performance-arc-set-plan-report`.
- Create `tests/test_style_performance_arcs_report.py`
  - Covers data shape, formatting, JSON, CLI parser/handler, and passive behavior.
- Modify `tests/test_cli.py`, `tests/test_cli_coverage.py`, `tests/fixtures/cli_help_expected.txt`, and passive MIDI safety parametrizations.
- Modify `README.md` and `docs/STATUS.md`
  - Document the new arc commands and project milestone.

## Task 1: Data Layer

- [ ] **Step 1: Write failing data tests**

Add tests in `tests/test_style_performance_arcs_report.py` proving:

```python
from rytm_randomizer.data.style_performance_arcs import STYLE_PERFORMANCE_ARCS

def test_style_performance_arc_catalog_contains_jose_reference_arc():
    arc = STYLE_PERFORMANCE_ARCS["jose_warehouse_five_hour"]

    assert arc.name == "Jose Warehouse Five Hour"
    assert arc.default_total_minutes == 300
    assert arc.default_scope == "dual"
    assert arc.default_discovery_start == 30
    assert arc.default_discovery_end == 85
    assert arc.style_keys == (
        "jose_core_techno",
        "mills_hypnotic",
        "deep_dark_hypnosis",
        "birmingham_pressure",
        "industrial_dark",
        "warehouse_peak",
        "hood_stripped",
    )
    assert "Jeff Mills" in arc.references
    assert "Oscar Mulero" in arc.references
```

- [ ] **Step 2: Run failing test**

Run:

```powershell
python -m pytest tests/test_style_performance_arcs_report.py::test_style_performance_arc_catalog_contains_jose_reference_arc -n 0
```

Expected: fails with `ModuleNotFoundError` for `rytm_randomizer.data.style_performance_arcs`.

- [ ] **Step 3: Implement data module**

Create immutable dataclasses and four curated arcs. Validate at import time that every arc segment style key exists in `STYLE_PROFILES`.

- [ ] **Step 4: Re-export data**

Import and add `STYLE_PERFORMANCE_ARCS` to `rytm_randomizer/data/__init__.py`.

- [ ] **Step 5: Run data test**

Run:

```powershell
python -m pytest tests/test_style_performance_arcs_report.py::test_style_performance_arc_catalog_contains_jose_reference_arc -n 0
```

Expected: pass.

## Task 2: Passive Arc Report

- [ ] **Step 1: Write failing report tests**

Add tests for:

- `format_style_performance_arc_report()`
- `format_style_performance_arc_list()`
- `format_style_performance_arc_inspection("jose_warehouse_five_hour")`
- `format_style_performance_arc_search("stigmata")`
- `to_style_performance_arc_json(...)`

- [ ] **Step 2: Run failing report tests**

Run:

```powershell
python -m pytest tests/test_style_performance_arcs_report.py -n 0
```

Expected: fails because report module/functions do not exist.

- [ ] **Step 3: Implement report module**

Create `rytm_randomizer/reports/style_performance_arcs.py` with deterministic text and JSON output. Safety lines must include:

- `passive/read-only`
- `metadata and plan expansion only`
- `no MIDI sending`
- `no port opening`
- `no command execution`
- `no hardware mutation`
- `no hardware required`

- [ ] **Step 4: Run report tests**

Run:

```powershell
python -m pytest tests/test_style_performance_arcs_report.py -n 0
```

Expected: pass.

## Task 3: Set-Plan Expansion

- [ ] **Step 1: Write failing set-plan tests**

Add fixture-local Rytm/A4 test SysEx banks, then assert:

- `build_style_performance_arc_set_plan_report("jose_warehouse_five_hour", ...)` returns the existing performance set plan with arc style keys.
- Text output includes the arc header, reference list, arc defaults, and embedded performance segments.
- JSON output includes `arc`, `performance_plan`, and safety metadata.
- Rytm-only scope leaves A4 unchanged through the existing plan.

- [ ] **Step 2: Run failing set-plan tests**

Run:

```powershell
python -m pytest tests/test_style_performance_arcs_report.py -n 0
```

Expected: fails because set-plan expansion is not implemented.

- [ ] **Step 3: Implement set-plan expansion**

Reuse `build_dual_machine_style_performance_set_plan_report(...)` instead of duplicating planning logic. Allow CLI overrides for `--scope`, `--rank`, `--total-minutes`, `--segment-minutes`, `--discovery-start`, `--discovery-end`, `--events`, `--limit`, and `--json`.

- [ ] **Step 4: Run set-plan tests**

Run:

```powershell
python -m pytest tests/test_style_performance_arcs_report.py -n 0
```

Expected: pass.

## Task 4: CLI + Help + Safety

- [ ] **Step 1: Write failing CLI tests**

Add CLI tests that run:

- `style-performance-arc-report`
- `list-style-performance-arcs`
- `inspect-style-performance-arc jose_warehouse_five_hour`
- `search-style-performance-arcs stigmata`
- `style-performance-arc-set-plan-report jose_warehouse_five_hour --rytm <path> --analog-four <path> --events --limit 1`
- all matching `--help` commands

- [ ] **Step 2: Run failing CLI tests**

Run:

```powershell
python -m pytest tests/test_style_performance_arcs_report.py tests/test_cli.py::test_style_performance_arc_report_help -n 0
```

Expected: fails because commands/help are not wired.

- [ ] **Step 3: Wire lazy CLI commands and help text**

Update `cli.py`, `help_text.py`, `tests/fixtures/cli_help_expected.txt`, CLI coverage, and passive real-MIDI safety command lists.

- [ ] **Step 4: Run focused CLI tests**

Run:

```powershell
python -m pytest tests/test_style_performance_arcs_report.py tests/test_cli.py tests/test_cli_coverage.py tests/test_real_midi_passive_cli_safety.py -n 0
```

Expected: pass.

## Task 5: Docs + Verification

- [ ] **Step 1: Update docs**

Add README examples and a `docs/STATUS.md` line describing the passive reference-arc preset layer.

- [ ] **Step 2: Focused verification**

Run:

```powershell
python -m pytest tests/test_style_performance_arcs_report.py -n 0
python -m pytest tests/test_cli.py tests/test_cli_coverage.py tests/test_real_midi_passive_cli_safety.py -n 0
```

- [ ] **Step 3: Architecture and lint**

Run:

```powershell
python -m pytest tests/architecture/ -q
python -m ruff check .
python -m black --check --target-version=py311 .
python -m isort --profile black --check-only .
```

- [ ] **Step 4: Fast/full/coverage**

Run:

```powershell
python -m pytest -m fast
python -m pytest
python -m pytest --cov=rytm_randomizer --cov-branch --cov-report=term-missing
```

- [ ] **Step 5: Review gate**

Run:

```powershell
python scripts/code_review_gate.py --mode cli
```

- [ ] **Step 6: Commit/push/PR**

Commit all intentional changes and open one PR against `modularize-v1.34` with the required 18-gate checklist.

## Done Criteria

- Passive reference arcs are inspectable/searchable.
- `style-performance-arc-set-plan-report` expands a named arc into the existing dual-machine performance set plan.
- Text and JSON contracts are deterministic.
- No command opens a MIDI port or sends MIDI.
- No V1.34 parity fixture regeneration.
- Full verification and review gate pass before PR.
