# Live Performance Runbook Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add one passive live-performance runbook command that turns a chosen performance arc or reference match into a show-facing checklist, cue timeline, machine focus map, stage packet summary, and JSON payload.

**Architecture:** The feature composes the existing `style_performance_arcs` chain from a new report module instead of growing the already-large arc module. Direct `--arc` selection uses the live cue-sheet builder; reference sources use the reference-match builder and its embedded cue sheet/stage packet. The new report remains passive, read-only, and CLI-only: no MIDI imports, no ports, no hardware sends.

**Tech Stack:** Python 3.11, frozen dataclasses, `CliCommand`, passive report formatter, pytest fast tests, existing SysEx fixture builders.

Per docs/PLAN_REQUIREMENTS.md, this plan keeps the work bundled as one logical PR and avoids V1.34 parity fixture changes.

---

### Task 1: RED Tests For Runbook Model, Formatting, JSON, And CLI

**Files:**
- Modify: `tests/test_style_performance_arcs_report.py`
- Modify: `tests/test_cli.py`
- Modify: `tests/test_cli_coverage.py`
- Modify: `tests/test_real_midi_passive_cli_safety.py`

- [ ] **Step 1: Add model/format/JSON tests**

Append tests that import:

```python
build_style_performance_arc_live_runbook_report
format_style_performance_arc_live_runbook_report
to_style_performance_arc_live_runbook_json
```

Assert:

```python
runbook = build_style_performance_arc_live_runbook_report(
    arc_key="jose_warehouse_five_hour",
    rytm_sysex_path=rytm_path,
    analog_four_sysex_path=a4_path,
)
assert runbook.selection_source == "arc"
assert runbook.selected_arc_key == "jose_warehouse_five_hour"
assert runbook.live_cue_sheet is not None
assert runbook.stage_packet is runbook.live_cue_sheet.stage_packet
assert runbook.show_mode == "dual-machine"
assert runbook.launch_brief
assert runbook.timeline_cards
```

Also test a reference-description path:

```python
runbook = build_style_performance_arc_live_runbook_report(
    description="Jeff Mills Oscar Mulero tunnel bells",
    rytm_sysex_path=rytm_path,
    analog_four_sysex_path=a4_path,
)
assert runbook.selection_source == "description"
assert runbook.reference_match is not None
assert runbook.selected_arc_key == "mills_mulero_tunnel"
```

- [ ] **Step 2: Add CLI dispatch tests**

Extend `test_style_performance_arc_cli_dispatch_and_help` to call:

```python
main([
    "style-performance-arc-live-runbook-report",
    "--description",
    "Jeff Mills Oscar Mulero tunnel",
    "--rytm",
    str(rytm_path),
    "--analog-four",
    str(a4_path),
    "--events",
    "--limit",
    "1",
])
```

Assert stdout contains the runbook title, "Launch brief:", "Timeline cards:", "Stage packet:", and the matched arc.

- [ ] **Step 3: Add passive safety coverage**

Add `("style-performance-arc-live-runbook-report", "--help")` to both passive CLI safety command lists.

- [ ] **Step 4: Run RED**

Run:

```powershell
python -m pytest tests/test_style_performance_arcs_report.py::test_style_performance_arc_live_runbook_builds_direct_arc_packet -n 0
```

Expected: FAIL because the runbook functions do not exist yet.

### Task 2: Implement Passive Runbook Builder And Formatter

**Files:**
- Add: `rytm_randomizer/reports/live_performance_runbook.py`

- [ ] **Step 1: Add constants and frozen dataclasses**

Add:

```python
REPORT_TITLE: Final[str] = "RytmRandomizer passive style performance arc live runbook"
SAFETY_LINES: Final[tuple[str, ...]] = (...)
```

Add frozen dataclasses for:

```python
StylePerformanceArcLiveRunbookTimelineCard
StylePerformanceArcLiveRunbookReport
```

- [ ] **Step 2: Build from direct arc or reference**

Add `build_style_performance_arc_live_runbook_report(...)` with mutually exclusive selection:

- `arc_key` builds `build_style_performance_arc_live_cue_sheet_report((arc_key,), ...)`.
- `description` / `audio_path` / `library_path` builds `build_style_performance_arc_reference_match_report(..., include_live_cue_sheet=True)`.
- Exactly one selection source is required.

- [ ] **Step 3: Format and JSON**

Add:

```python
format_style_performance_arc_live_runbook_report(report, include_events=False, event_limit=24)
to_style_performance_arc_live_runbook_json(report)
```

Formatted output includes:

- runbook summary
- launch brief
- replayable passive commands
- stage packet
- timeline cards
- recovery cues
- safety

JSON includes the same model plus embedded cue sheet and optional reference match.

### Task 3: Wire CLI And Help

**Files:**
- Modify: `rytm_randomizer/reports/live_performance_runbook.py`
- Modify: `rytm_randomizer/cli.py`
- Modify: `rytm_randomizer/help_text.py`

- [ ] **Step 1: Add parser and handler**

Add parser support for:

```text
style-performance-arc-live-runbook-report (--arc <arc-key>|--description <text>|--audio <path>|--library <dir>) [--rytm <syx-path>] [--analog-four <syx-path>] [--scope dual|rytm-only|analog-four-only|a4-only] [--rank N] [--total-minutes N] [--segment-minutes N] [--discovery-start N] [--discovery-end N] [--events] [--limit N] [--json]
```

- [ ] **Step 2: Register command**

Add `STYLE_PERFORMANCE_ARC_LIVE_RUNBOOK_CLI_COMMAND`, register it, and add it to `__all__`.

- [ ] **Step 3: Add lazy CLI mapping and help text**

Map the command in `cli.py`, add top-level usage in `help_text.py`, and create `_style_performance_arc_live_runbook_help()`.

### Task 4: Docs And Verification

**Files:**
- Modify: `README.md`
- Modify: `docs/STATUS.md`
- Modify: `tests/fixtures/cli_help_expected.txt` if the top-level help fixture changes.

- [ ] **Step 1: Update README passive command examples**

Add one example after reference-match:

```powershell
python -m rytm_randomizer.cli style-performance-arc-live-runbook-report --description "Jeff Mills Oscar Mulero Birmingham pressure" --rytm "<RYTM_KITS.syx>" --analog-four "<ANALOG_FOUR_KITS.syx>" --events --limit 8
```

- [ ] **Step 2: Update status**

Add a 2026-05-22 status entry describing the passive live runbook and confirming no hardware send path.

- [ ] **Step 3: Verify**

Run:

```powershell
python -m pytest tests/test_style_performance_arcs_report.py tests/test_cli.py tests/test_cli_coverage.py tests/test_real_midi_passive_cli_safety.py -n 0
python -m pytest tests/architecture/ -q
python -m pytest -m fast
python -m pytest
python -m pytest --cov=rytm_randomizer --cov-branch --cov-report=term-missing
python -m ruff check .
python -m black --check --target-version=py311 .
python -m isort --profile black --check-only .
python scripts/code_review_gate.py --mode cli
```

Expected: all pass, with no V1.34 parity fixture diffs staged.
