# Reference Performance Arc Readiness Matrix Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a passive CLI report that ranks curated style performance arcs against saved Rytm and Analog Four kit banks so an operator can choose which long-form reference arc is most ready before a live set.

**Architecture:** Reuse the merged `style_performance_arcs` catalog and `build_style_performance_arc_set_plan_report()` for each arc. The new report stays in `rytm_randomizer/reports/style_performance_arcs.py`, adds no hardware boundary, and summarizes readiness from each arc's existing timed dual-machine set plan.

**Tech Stack:** Python 3.13, frozen dataclasses, existing passive CLI registry, existing dual-machine saved-kit SysEx decoders, pytest, ruff, black, isort.

---

### Task 1: Add Readiness Matrix Tests

**Files:**
- Modify: `tests/test_style_performance_arcs_report.py`

- [x] **Step 1: Write the failing build/format/JSON test**

Add a test named `test_style_performance_arc_readiness_matrix_ranks_all_arcs_against_saved_banks` that imports:

```python
from rytm_randomizer.reports.style_performance_arcs import (
    build_style_performance_arc_readiness_report,
    format_style_performance_arc_readiness_report,
    to_style_performance_arc_readiness_json,
)
```

The test should:
- create the existing `_arc_bank_files(tmp_path)` Rytm/A4 fixtures
- build the report with both paths
- assert all four curated arcs are represented
- assert the scope is `dual`
- assert at least one entry is `partial` with segment counts derived from the embedded set plan
- assert formatter output includes the title, matrix summary, `jose_warehouse_five_hour`, `Average selection score:`, and passive safety lines
- assert JSON contains `entries[0]["arc"]["key"]`, `entries[0]["readiness"]`, and `entries[0]["performance_plan"]["totals"]`

- [x] **Step 2: Run the test to verify RED**

Run:

```bash
python -m pytest tests/test_style_performance_arcs_report.py::test_style_performance_arc_readiness_matrix_ranks_all_arcs_against_saved_banks -n 0
```

Expected: fail with `ImportError` because the readiness matrix functions do not exist yet.

### Task 2: Implement Readiness Matrix Core

**Files:**
- Modify: `rytm_randomizer/reports/style_performance_arcs.py`

- [x] **Step 1: Add report dataclasses**

Add frozen dataclasses:

```python
@dataclass(frozen=True)
class StylePerformanceArcReadinessEntry:
    position: int
    arc: StylePerformanceArc
    readiness: str
    average_selection_score: int
    operator_action: str
    plan: DualMachineStylePerformanceSetPlan


@dataclass(frozen=True)
class StylePerformanceArcReadinessReport:
    scope: str
    arc_count: int
    ready_arc_count: int
    partial_arc_count: int
    blocked_arc_count: int
    total_segment_count: int
    total_event_row_count: int
    total_mock_message_count: int
    total_deferred_row_count: int
    entries: tuple[StylePerformanceArcReadinessEntry, ...]
```

- [x] **Step 2: Add builder helpers**

Add helpers to normalize optional arc keys, compute entry readiness from segment counts, average segment scores, and produce a concise operator action. `blocked_segment_count > 0` means blocked, otherwise `partial_segment_count > 0` means partial, otherwise ready.

- [x] **Step 3: Add `build_style_performance_arc_readiness_report()`**

The builder accepts:

```python
arc_keys: Sequence[str] | None = None
rytm_sysex_path: Path | None = None
analog_four_sysex_path: Path | None = None
scope: str | None = None
selection_rank: int | None = None
total_minutes: int | None = None
segment_minutes: int | None = None
discovery_start: int | None = None
discovery_end: int | None = None
```

For each selected arc, call `build_style_performance_arc_set_plan_report()` and derive an entry from its plan. Sort entries by readiness rank (`ready`, `partial`, `blocked`), descending average score, then arc key.

- [x] **Step 4: Add formatter and JSON helpers**

Add:

```python
format_style_performance_arc_readiness_report(report: StylePerformanceArcReadinessReport) -> list[str]
to_style_performance_arc_readiness_json(report: StylePerformanceArcReadinessReport) -> dict[str, object]
```

Formatter output must be compact and operator-facing; JSON should include full nested `performance_plan` via `to_dual_machine_style_performance_set_plan_json()`.

- [x] **Step 5: Run the focused test to verify GREEN**

Run:

```bash
python -m pytest tests/test_style_performance_arcs_report.py::test_style_performance_arc_readiness_matrix_ranks_all_arcs_against_saved_banks -n 0
```

Expected: pass.

### Task 3: Add CLI Command

**Files:**
- Modify: `rytm_randomizer/reports/style_performance_arcs.py`
- Modify: `rytm_randomizer/cli.py`
- Modify: `rytm_randomizer/help_text.py`
- Modify: `tests/test_style_performance_arcs_report.py`
- Modify: `tests/test_cli.py`
- Modify: `tests/fixtures/cli_help_expected.txt`

- [x] **Step 1: Add parser/handler tests**

Add tests for `_parse_arc_readiness_cli_args()`, `_handle_style_performance_arc_readiness_report()`, and `main(["style-performance-arc-readiness-report", "--rytm", str(path)])`.

- [x] **Step 2: Run tests to verify RED**

Run:

```bash
python -m pytest tests/test_style_performance_arcs_report.py -n 0
```

Expected: fail because parser/handler/CLI command do not exist.

- [x] **Step 3: Wire command**

Add `STYLE_PERFORMANCE_ARC_READINESS_CLI_COMMAND`, register it, add lazy import mapping in `cli.py`, and add help text. Syntax:

```bash
python -m rytm_randomizer.cli style-performance-arc-readiness-report [<arc-key> ...] --rytm <syx-path> [--analog-four <syx-path>] [--scope dual|rytm-only|analog-four-only|a4-only] [--rank N] [--total-minutes N] [--segment-minutes N] [--discovery-start N] [--discovery-end N] [--limit N] [--json]
```

- [x] **Step 4: Run tests to verify GREEN**

Run:

```bash
python -m pytest tests/test_style_performance_arcs_report.py tests/test_cli.py tests/test_cli_coverage.py tests/test_real_midi_passive_cli_safety.py -n 0
```

Expected: pass.

### Task 4: Docs And Verification

**Files:**
- Modify: `README.md`
- Modify: `docs/STATUS.md`

- [x] **Step 1: Update operator docs**

Add README command examples for `style-performance-arc-readiness-report`, and add a `docs/STATUS.md` entry explaining that the report ranks reference arcs against saved kit banks without opening ports or sending MIDI.

- [x] **Step 2: Run format and gates**

Run:

```bash
python -m ruff check .
python -m black --check --target-version=py311 .
python -m isort --profile black --check-only .
python -m pytest tests/test_style_performance_arcs_report.py tests/test_cli.py tests/test_cli_coverage.py tests/test_real_midi_passive_cli_safety.py -n 0
python -m pytest tests/architecture/ -q
python -m pytest -m fast
python -m pytest
python -m pytest --cov=rytm_randomizer --cov-branch --cov-report=term-missing
python scripts/code_review_gate.py --mode cli
```

Expected: all pass. If `python -m vulture . --min-confidence 80` still reports pre-existing untouched baseline variables, run scoped vulture on touched files and document the repo-wide baseline note in the PR body.

### Task 5: Publish PR

**Files:**
- Stage only the files listed in this plan.

- [ ] **Step 1: Commit**

```bash
git add README.md docs/STATUS.md docs/superpowers/plans/2026-05-21-reference-performance-arc-readiness-matrix-pr22.md rytm_randomizer/cli.py rytm_randomizer/help_text.py rytm_randomizer/reports/style_performance_arcs.py tests/fixtures/cli_help_expected.txt tests/test_cli.py tests/test_style_performance_arcs_report.py
git commit -m "feat: add reference arc readiness matrix"
```

- [ ] **Step 2: Push and open PR**

Push `codex/reference-arc-audition-matrix-pr22` and open a ready PR against `modularize-v1.34` with the mandatory 18-gate checklist.

- [ ] **Step 3: Watch CI and post review comment**

Watch `gh pr checks --watch`, fix any failures, and post a Codex self-review comment with Findings, Abstraction, Docs, and Verification sections.
