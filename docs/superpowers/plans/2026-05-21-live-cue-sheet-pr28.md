# Live Cue Sheet Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a passive `style-performance-arc-live-cue-sheet-report` command that consumes the selected live render bundle and produces operator-facing live-performance cues for Rytm, Analog Four, or both.

**Architecture:** Reuse the existing reference arc live render bundle and its selected `DualMachineStylePerformanceSetPlan`. The cue sheet is a report projection only: it adds risk labels, machine focus, hands-on moves, recovery cues, text, JSON, CLI help, and docs without adding active MIDI behavior.

**Tech Stack:** Python frozen dataclasses, existing passive report formatter, existing CLI registry, existing live render bundle data, pytest, ruff, black, isort, vulture.

---

### Task 1: RED Tests For Live Cue Sheet Report

**Files:**
- Modify: `tests/test_style_performance_arcs_report.py`

- [x] **Step 1: Write the failing report test**

Add `test_style_performance_arc_live_cue_sheet_builds_operator_cues` that imports:

```python
from rytm_randomizer.reports.style_performance_arcs import (
    build_style_performance_arc_live_cue_sheet_report,
    format_style_performance_arc_live_cue_sheet_report,
    to_style_performance_arc_live_cue_sheet_json,
)
```

The test should:

- Use `_arc_bank_files(tmp_path)`.
- Build the cue sheet with both Rytm and Analog Four paths.
- Assert the selected render bundle, set plan, segment count, cue count, and totals line up.
- Assert the first cue links to the first render segment and exposes position, time window, style key, risk, operator move, recovery action, and render row summary.
- Format with `include_events=True, event_limit=1`.
- Assert title, cue summary, preflight cues, performance cues, hands-on move, risk, recovery, mock preview, and passive safety lines.
- Assert JSON contains selected arc, embedded live render bundle, cue sheet totals, cues, risk level, and safety lines.

- [x] **Step 2: Write one-machine and branch-edge tests**

Add tests for `analog-four-only`, `rytm-only`, dual-machine fallback focus, green/amber/red risk levels, empty mock preview rows, and event-limit all-rows behavior.

- [x] **Step 3: Write parser and handler assertions**

Extend the existing parser/handler test to cover `_parse_arc_live_cue_sheet_cli_args(...)`, `_handle_style_performance_arc_live_cue_sheet_report(...)`, text output, JSON output, and missing-path errors.

- [x] **Step 4: Run RED tests**

Run the focused cue-sheet tests and confirm they fail before implementation because the new functions do not exist.

### Task 2: Implement Report Data Model And Builders

**Files:**
- Modify: `rytm_randomizer/reports/style_performance_arcs.py`

- [x] **Step 1: Add constants**

Add `LIVE_CUE_SHEET_TITLE`, `LIVE_CUE_SHEET_SAFETY_LINES`, `_LIVE_CUE_SHEET_HEADER`, `_LIVE_CUE_SHEET_USAGE`, and `_LIVE_CUE_SHEET_OPTIONS`.

- [x] **Step 2: Add dataclasses**

Add:

```python
@dataclass(frozen=True)
class StylePerformanceArcLiveCue:
    render_segment: StylePerformanceArcLiveRenderSegment
    machine_focus: str
    operator_move: str
    risk_level: str
    recovery_action: str


@dataclass(frozen=True)
class StylePerformanceArcLiveCueSheetReport:
    live_render_bundle: StylePerformanceArcLiveRenderBundleReport
    suggested_commands: tuple[str, ...]
    preflight_cues: tuple[str, ...]
    recovery_cues: tuple[str, ...]
    cues: tuple[StylePerformanceArcLiveCue, ...]
```

Add pass-through properties for selected entry, selected set plan, segment counts, cue count, and totals.

- [x] **Step 3: Add cue helpers**

Add helpers that derive suggested commands, machine focus, operator move, risk level, recovery action, preflight cues, and deduplicated recovery cues from the live render bundle.

- [x] **Step 4: Add builder**

Implement `build_style_performance_arc_live_cue_sheet_report(...)` with the same options as the live render bundle builder.

### Task 3: Formatter, JSON, Parser, Handler, And CLI Registration

**Files:**
- Modify: `rytm_randomizer/reports/style_performance_arcs.py`
- Modify: `rytm_randomizer/cli.py`

- [x] **Step 1: Add text formatter**

Implement `format_style_performance_arc_live_cue_sheet_report(report, include_events=False, event_limit=_DEFAULT_EVENT_LIMIT)`.

- [x] **Step 2: Add JSON formatter**

Implement `to_style_performance_arc_live_cue_sheet_json(report)` with the embedded live render bundle JSON and cue-sheet-specific rows.

- [x] **Step 3: Add parser and handler**

Add `_parse_arc_live_cue_sheet_cli_args` and `_handle_style_performance_arc_live_cue_sheet_report`.

- [x] **Step 4: Register CLI command**

Add `STYLE_PERFORMANCE_ARC_LIVE_CUE_SHEET_CLI_COMMAND`, register it, export it, and add the lazy CLI mapping in `rytm_randomizer/cli.py`.

### Task 4: CLI Help, Safety, And Fixture Coverage

**Files:**
- Modify: `rytm_randomizer/help_text.py`
- Modify: `tests/test_cli.py`
- Modify: `tests/test_real_midi_passive_cli_safety.py`
- Modify: `tests/fixtures/cli_help_expected.txt`

- [x] **Step 1: Add help text**

Add a command-specific help entry whose safety block imports `LIVE_CUE_SHEET_SAFETY_LINES`.

- [x] **Step 2: Update top-level usage and command list**

Add the new command near the other style performance arc commands.

- [x] **Step 3: Update tests and fixture**

Assert top-level help includes the command and command-specific help says `Builds a passive live performance cue sheet from saved kit banks.`

### Task 5: Docs And Status

**Files:**
- Modify: `README.md`
- Modify: `docs/STYLE_ANALYSIS.md`
- Modify: `docs/STATUS.md`
- Modify: `docs/ARCHITECTURE.md`
- Modify: `docs/ARCHITECTURE_DIAGRAMS.md`
- Create: `docs/superpowers/specs/2026-05-21-live-cue-sheet-design.md`
- Create: `docs/superpowers/plans/2026-05-21-live-cue-sheet-pr28.md`

- [x] **Step 1: README**

Add a passive CLI example for the live cue sheet after the live render bundle example.

- [x] **Step 2: Style docs**

Mention the cue sheet as the current operator-facing bridge after live render bundles.

- [x] **Step 3: Status and architecture docs**

Record the checkpoint and refresh the relevant report/CLI surfaces without changing architectural boundaries.

### Task 6: Verification And PR

- [x] **Step 1: Focused tests**

Run:

```bash
python -m pytest tests/test_style_performance_arcs_report.py -n 0
python -m pytest tests/test_cli.py tests/test_real_midi_passive_cli_safety.py -n 0
python -m pytest tests/test_style_performance_arcs_report.py -n 0 --cov=rytm_randomizer.reports.style_performance_arcs --cov-branch --cov-report=term-missing --cov-fail-under=100
```

- [x] **Step 2: Mechanical checks**

Run:

```bash
python -m ruff check .
python -m black --check --target-version=py311 .
python -m isort --profile black --check-only .
python -m vulture rytm_randomizer tests --min-confidence 80
python -m pytest tests/architecture/ -q
python -m pytest -m fast
python -m pytest
python -m pytest --cov=rytm_randomizer --cov-branch --cov-report=term-missing
python scripts/code_review_gate.py --mode cli
```

- [ ] **Step 3: Commit, push, PR**

Stage only intended files, commit with:

```text
feat: add live performance cue sheet
```

Open a PR against `modularize-v1.34` with the required 18-gate checklist and link to this plan.

### Task 7: Reference-Selected Stage Packet Extension

**Files:**
- Modify: `rytm_randomizer/reports/style_performance_arcs.py`
- Modify: `tests/test_style_performance_arcs_report.py`
- Modify: `rytm_randomizer/help_text.py`
- Modify: `tests/fixtures/cli_help_expected.txt`
- Modify: `README.md`
- Modify: `docs/STYLE_ANALYSIS.md`
- Modify: `docs/STATUS.md`
- Modify: `docs/ARCHITECTURE.md`
- Modify: `docs/ARCHITECTURE_DIAGRAMS.md`

- [x] **Step 1: RED tests**

Extend the live cue sheet and reference-match tests to require a passive
stage packet with selected arc, scope, readiness, cue count, planned Rytm
pads, planned Analog Four tracks, compact stage cards, JSON output, and
formatted text output.

- [x] **Step 2: Implement stage packet data model**

Add frozen stage-card and stage-packet dataclasses derived from the existing
live cue sheet. Keep the packet passive and reuse saved-kit mock/deferred rows
without adding any MIDI send path.

- [x] **Step 3: Wire formatter and JSON**

Expose the stage packet under the live cue sheet JSON, the reference-match
JSON, the live cue sheet text output, and the reference-match summary.

- [x] **Step 4: Refresh operator-facing docs**

Update CLI help summaries, README, STYLE_ANALYSIS, STATUS, architecture docs,
and the top-level help fixture to describe the stage-packet handoff.

- [x] **Step 5: Re-run verification and push**

Run focused tests, touched-module coverage, CLI/help safety tests,
architecture, fast/full suites, coverage, and review gate before staging only
the intended files and pushing the PR update.
