# Live Render Bundle Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a passive `style-performance-arc-live-render-bundle-report` command that packages the selected reference arc into segment-level mock-render previews for Rytm, Analog Four, or both.

**Architecture:** Reuse the existing reference arc live-session packet and its selected `DualMachineStylePerformanceSetPlan`. Each set-plan segment already owns a dual-machine mock preview; this PR projects that into a render-bundle dataclass, text report, JSON report, CLI command, and docs without adding active MIDI behavior.

**Tech Stack:** Python frozen dataclasses, existing passive report formatter, existing CLI registry, existing dual-machine mock preview JSON/event-row helpers, pytest, ruff, black, isort, vulture.

---

### Task 1: RED Tests For Live Render Bundle Report

**Files:**
- Modify: `tests/test_style_performance_arcs_report.py`

- [x] **Step 1: Write the failing report test**

Add `test_style_performance_arc_live_render_bundle_builds_segment_mock_packet` that imports:

```python
from rytm_randomizer.reports.style_performance_arcs import (
    build_style_performance_arc_live_render_bundle_report,
    format_style_performance_arc_live_render_bundle_report,
    to_style_performance_arc_live_render_bundle_json,
)
```

The test should:

- Use `_arc_bank_files(tmp_path)`.
- Build the bundle with both Rytm and Analog Four paths.
- Assert `bundle.live_session_packet.selected_set_plan is bundle.selected_set_plan`.
- Assert segment count and totals match the selected set plan.
- Assert the first render segment links the live-session segment and set-plan segment by position/style/time window.
- Assert the first segment exposes event preview rows, deferred rows, full preview JSON, Rytm summary, A4 summary, and counts.
- Format with `include_events=True, event_limit=1`.
- Assert title `RytmRandomizer passive style performance arc live render bundle`.
- Assert text contains `Render bundle summary:`, `Replayable passive commands:`, `Segment render bundles:`, `Mock render preview:`, `Deferred rows:`, `no real MIDI rendering`, and `no MIDI sending`.
- Assert JSON contains `render_bundle`, `segments`, `preview`, `event_preview_rows`, and `deferred_rows`.

- [x] **Step 2: Write the failing one-machine scope test**

Add `test_style_performance_arc_live_render_bundle_covers_single_machine_scope` that builds an `analog-four-only` bundle with only an A4 path. Assert:

- `bundle.selected_set_plan.scope == "analog-four-only"`.
- Rytm summary is `unchanged by scope`.
- Suggested command includes `--analog-four <analog-four-syx-path> --scope analog-four-only`.
- The JSON Rytm machine preview is `None`.
- Formatting with `event_limit=-1` raises `ValueError("event_limit must be >= 0")`.

- [x] **Step 3: Write parser and handler assertions**

Extend the existing parser/handler test to cover:

```python
_parse_arc_live_render_bundle_cli_args([...]) == {
    "arc_keys": ("jose_warehouse_five_hour",),
    "rytm_sysex_path": Path("rytm.syx"),
    "analog_four_sysex_path": Path("a4.syx"),
    "scope": "dual",
    "selection_rank": 2,
    "total_minutes": 240,
    "segment_minutes": 30,
    "discovery_start": 25,
    "discovery_end": 90,
    "include_events": True,
    "event_limit": 1,
    "json_output": True,
}
```

Also assert `_handle_style_performance_arc_live_render_bundle_report(...)` returns text and JSON successfully, and no-path invocation returns code `2` with the existing `requires --rytm` style error.

- [x] **Step 4: Run RED tests**

Run:

```bash
python -m pytest tests/test_style_performance_arcs_report.py::test_style_performance_arc_live_render_bundle_builds_segment_mock_packet tests/test_style_performance_arcs_report.py::test_style_performance_arc_live_render_bundle_covers_single_machine_scope -n 0
```

Expected: fail because the new functions do not exist.

### Task 2: Implement Report Data Model And Builders

**Files:**
- Modify: `rytm_randomizer/reports/style_performance_arcs.py`

- [x] **Step 1: Add constants**

Add `LIVE_RENDER_BUNDLE_TITLE`, `LIVE_RENDER_BUNDLE_SAFETY_LINES`, `_LIVE_RENDER_BUNDLE_HEADER`, `_LIVE_RENDER_BUNDLE_USAGE`, and `_LIVE_RENDER_BUNDLE_OPTIONS`.

- [x] **Step 2: Add dataclasses**

Add:

```python
@dataclass(frozen=True)
class StylePerformanceArcLiveRenderSegment:
    live_segment: StylePerformanceArcLiveSessionSegment
    set_plan_segment: DualMachineStylePerformanceSetSegment
    event_preview_rows: tuple[str, ...]
    deferred_rows: tuple[str, ...]


@dataclass(frozen=True)
class StylePerformanceArcLiveRenderBundleReport:
    live_session_packet: StylePerformanceArcLiveSessionPacketReport
    suggested_commands: tuple[str, ...]
    segments: tuple[StylePerformanceArcLiveRenderSegment, ...]
```

Add pass-through properties for selected entry, selected set plan, segment counts, and totals.

- [x] **Step 3: Add event/deferred row helpers**

Use `format_dual_machine_style_selection_mock_preview_event_rows(segment.preview_plan)` for event preview rows. Format deferred A4 rows locally from `segment.preview_plan.analog_four_preview.deferred_rows` without importing private helper functions.

- [x] **Step 4: Add builder**

Implement `build_style_performance_arc_live_render_bundle_report(...)` with the same options as the live-session packet builder. It should build the live-session packet, zip `packet.segments` with `packet.selected_set_plan.segments`, and produce render segments.

### Task 3: Implement Formatter, JSON, Parser, Handler, And CLI Registration

**Files:**
- Modify: `rytm_randomizer/reports/style_performance_arcs.py`
- Modify: `rytm_randomizer/cli.py`

- [x] **Step 1: Add text formatter**

Implement `format_style_performance_arc_live_render_bundle_report(report, include_events=False, event_limit=_DEFAULT_EVENT_LIMIT)`.

- [x] **Step 2: Add JSON formatter**

Implement `to_style_performance_arc_live_render_bundle_json(report)` with full selected packet and per-segment preview JSON.

- [x] **Step 3: Add parser and handler**

Add `_parse_arc_live_render_bundle_cli_args` and `_handle_style_performance_arc_live_render_bundle_report` mirroring the live-session packet parser/handler.

- [x] **Step 4: Register CLI command**

Add `STYLE_PERFORMANCE_ARC_LIVE_RENDER_BUNDLE_CLI_COMMAND`, register it, export it, and add the lazy CLI mapping in `rytm_randomizer/cli.py`.

### Task 4: CLI Help, Safety, And Fixture Coverage

**Files:**
- Modify: `rytm_randomizer/help_text.py`
- Modify: `tests/test_cli.py`
- Modify: `tests/test_real_midi_passive_cli_safety.py`
- Modify: `tests/fixtures/cli_help_expected.txt`

- [x] **Step 1: Add help text**

Add a command-specific help entry whose safety block imports `LIVE_RENDER_BUNDLE_SAFETY_LINES`.

- [x] **Step 2: Update top-level usage and command list**

Add the new command near the other style performance arc commands.

- [x] **Step 3: Update tests and fixture**

Assert top-level help includes the command and the command-specific help mentions `Builds a passive live render bundle from saved kit banks.`

### Task 5: Docs And Status

**Files:**
- Modify: `README.md`
- Modify: `docs/STYLE_ANALYSIS.md`
- Modify: `docs/STATUS.md`
- Modify: `docs/ARCHITECTURE.md`
- Modify: `docs/ARCHITECTURE_DIAGRAMS.md`

- [x] **Step 1: README**

Add a passive CLI example for the live render bundle after the live-session packet example.

- [x] **Step 2: Style docs**

Mention the bundle as the current mock-render bridge from reference arcs to future GUI/audio-analyzer routing.

- [x] **Step 3: Status and architecture docs**

Record the checkpoint and refresh the relevant report/CLI surfaces without changing architectural boundaries.

### Task 6: Verification And PR

**Files:**
- Create: PR body markdown under `docs/superpowers/plans/` or temp ignored path if needed.

- [x] **Step 1: Focused tests**

Run:

```bash
python -m pytest tests/test_style_performance_arcs_report.py -n 0
python -m pytest tests/test_cli.py tests/test_real_midi_passive_cli_safety.py -n 0
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

- [x] **Step 3: Commit, push, PR**

Stage only intended files, commit with:

```bash
git commit -m "feat: add live render bundle report"
```

Push `codex/live-render-bundle-pr27` and open a non-draft PR against `modularize-v1.34` with the 18-gate checklist.
