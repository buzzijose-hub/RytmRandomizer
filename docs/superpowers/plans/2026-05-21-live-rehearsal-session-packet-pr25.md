# Live Rehearsal Session Packet Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a passive `style-performance-arc-live-session-packet-report` command that packages the selected rehearsal manifest into an operator-facing live-session checklist.

**Architecture:** Reuse `build_style_performance_arc_rehearsal_manifest_report` and project its result into packet dataclasses in `rytm_randomizer/reports/style_performance_arcs.py`. Register the command through the existing lazy CLI registry and update help/fixtures/docs.

**Tech Stack:** Python dataclasses, existing passive report formatter, existing CLI registry, pytest, ruff, black, isort.

---

### Task 1: RED Tests For Packet Builder, Formatter, And JSON

**Files:**
- Modify: `tests/test_style_performance_arcs_report.py`

- [ ] **Step 1: Add failing report behavior test**

Add a test named `test_style_performance_arc_live_session_packet_builds_operator_packet` that imports:

```python
from rytm_randomizer.reports.style_performance_arcs import (
    build_style_performance_arc_live_session_packet_report,
    format_style_performance_arc_live_session_packet_report,
    to_style_performance_arc_live_session_packet_json,
)
```

The test should:

- Use `_arc_bank_files(tmp_path)`.
- Build the packet with both Rytm and Analog Four paths.
- Assert the selected rehearsal manifest is reused.
- Assert `packet.segment_count`, `packet.launch_checklist`, `packet.suggested_commands`, and `packet.segments` are populated.
- Assert the first segment includes `listen_for`, `go_no_go_cue`, and `reset_cue`.
- Format with `include_events=True, event_limit=1`.
- Assert the title is `RytmRandomizer passive style performance arc live session packet`.
- Assert text contains `Launch checklist:`, `Suggested passive commands:`, `Segment cards:`, `Listen for:`, `Go/no-go cue:`, `Reset cue:`, and `Event preview for segment`.
- Assert JSON includes `session_packet`, `launch_checklist`, `suggested_commands`, `segments`, and safety.

- [ ] **Step 2: Add failing one-machine edge test**

Add a test named `test_style_performance_arc_live_session_packet_covers_single_machine_edges` that builds with `scope="analog-four-only"` and only an A4 path. Assert the packet says Rytm is unchanged by scope and the segment Rytm preview is `unchanged by scope`. Also assert formatting with `event_limit=-1` raises `ValueError("event_limit must be >= 0")`.

- [ ] **Step 3: Run RED tests**

Run:

```bash
python -m pytest tests/test_style_performance_arcs_report.py::test_style_performance_arc_live_session_packet_builds_operator_packet tests/test_style_performance_arcs_report.py::test_style_performance_arc_live_session_packet_covers_single_machine_edges -n 0
```

Expected: FAIL because the new functions do not exist.

### Task 2: Implement Packet Dataclasses And Formatter

**Files:**
- Modify: `rytm_randomizer/reports/style_performance_arcs.py`

- [ ] **Step 1: Add constants**

Add:

```python
LIVE_SESSION_PACKET_TITLE: Final[str] = (
    "RytmRandomizer passive style performance arc live session packet"
)
LIVE_SESSION_PACKET_SAFETY_LINES: Final[tuple[str, ...]] = (
    "passive/read-only",
    "live rehearsal session packet",
    "operator checklist only",
    "metadata and plan expansion only",
    "no MIDI sending",
    "no port opening",
    "no command execution",
    "no hardware mutation",
    "no hardware required",
)
```

Add `_LIVE_SESSION_PACKET_HEADER` and `_LIVE_SESSION_PACKET_USAGE` beside the existing rehearsal manifest constants.

- [ ] **Step 2: Add dataclasses**

Add frozen dataclasses:

```python
@dataclass(frozen=True)
class StylePerformanceArcLiveSessionSegment:
    position: int
    style_key: str
    time_window: str
    discovery_amount: int
    discovery_band: str
    mutation_depth: str
    readiness: str
    listen_for: str
    go_no_go_cue: str
    reset_cue: str
    rytm_preview_summary: str
    analog_four_preview_summary: str
    event_row_count: int
    mock_message_count: int
    deferred_row_count: int


@dataclass(frozen=True)
class StylePerformanceArcLiveSessionPacketReport:
    rehearsal_manifest: StylePerformanceArcRehearsalManifestReport
    launch_checklist: tuple[str, ...]
    suggested_commands: tuple[str, ...]
    segments: tuple[StylePerformanceArcLiveSessionSegment, ...]
```

Add pass-through properties for `selected_entry`, `selected_set_plan`, `segment_count`, `ready_segment_count`, `partial_segment_count`, and `blocked_segment_count`.

- [ ] **Step 3: Add deterministic guidance helpers**

Implement helpers with this behavior:

```python
def _live_session_listen_for(segment: StylePerformanceArcRehearsalSegment) -> str:
    if segment.discovery_amount <= 35:
        return "Subtle variation while the loaded kit identity stays recognizable."
    if segment.discovery_amount >= 75:
        return "Surprise, edge, and whether the machine still supports the live set."
    return "Useful groove movement and tonal pressure without losing the segment role."

def _live_session_go_no_go_cue(segment: StylePerformanceArcRehearsalSegment) -> str:
    if segment.readiness == "ready":
        return "Auditionable: move forward if the segment supports the room."
    if segment.readiness == "partial":
        return "Rehearse carefully: continue only if the weak machine is not exposed."
    return "Planning-only: skip live use until better saved kit material exists."

def _live_session_reset_cue(segment: StylePerformanceArcRehearsalSegment) -> str:
    if segment.readiness == "blocked":
        return "Reset to the previous known-good kit before live use."
    if segment.discovery_amount >= 75:
        return "Reset after audition if the edge overwhelms the groove."
    return "Reset only if the segment pulls focus away from the live arc."
```

Use only `discovery_amount`, `discovery_band`, `mutation_depth`, and `readiness`.

- [ ] **Step 4: Add builder**

Implement `build_style_performance_arc_live_session_packet_report` with the same keyword options as the rehearsal manifest builder. It should call `build_style_performance_arc_rehearsal_manifest_report`, then create launch checklist, suggested command strings, and segment cards.

- [ ] **Step 5: Add formatter and JSON**

Implement:

```python
def format_style_performance_arc_live_session_packet_report(
    report: StylePerformanceArcLiveSessionPacketReport,
    *,
    include_events: bool = False,
    event_limit: int = _DEFAULT_EVENT_LIMIT,
) -> list[str]:
    if event_limit < 0:
        raise ValueError("event_limit must be >= 0")
    body_lines = [
        "Summary:",
        f"- Scope: {report.selected_set_plan.scope}",
        "Selected arc:",
        f"- Key: {report.selected_entry.arc.key}",
        "Launch checklist:",
        *[f"- {step}" for step in report.launch_checklist],
        "Suggested passive commands:",
        *[f"- {command}" for command in report.suggested_commands],
        "Segment cards:",
    ]
    for segment in report.segments:
        body_lines.extend(
            [
                f"- {segment.position}. {segment.time_window} | {segment.style_key}",
                f"  Listen for: {segment.listen_for}",
                f"  Go/no-go cue: {segment.go_no_go_cue}",
                f"  Reset cue: {segment.reset_cue}",
            ]
        )
    return passive_report_lines(_LIVE_SESSION_PACKET_HEADER, body_lines)

def to_style_performance_arc_live_session_packet_json(
    report: StylePerformanceArcLiveSessionPacketReport,
) -> dict[str, object]:
    return {
        "selected": _readiness_entry_json(report.selected_entry),
        "rehearsal_manifest": to_style_performance_arc_rehearsal_manifest_json(
            report.rehearsal_manifest
        ),
        "session_packet": {
            "scope": report.selected_set_plan.scope,
            "launch_checklist": list(report.launch_checklist),
            "suggested_commands": list(report.suggested_commands),
            "segments": [
                {
                    "position": segment.position,
                    "style_key": segment.style_key,
                    "listen_for": segment.listen_for,
                    "go_no_go_cue": segment.go_no_go_cue,
                    "reset_cue": segment.reset_cue,
                }
                for segment in report.segments
            ],
        },
        "safety": list(LIVE_SESSION_PACKET_SAFETY_LINES),
    }
```

The formatter should include `Summary:`, `Selected arc:`, `Launch checklist:`, `Suggested passive commands:`, `Segment cards:`, optional `Event previews:`, and the safety block.

- [ ] **Step 6: Run GREEN report tests**

Run:

```bash
python -m pytest tests/test_style_performance_arcs_report.py::test_style_performance_arc_live_session_packet_builds_operator_packet tests/test_style_performance_arcs_report.py::test_style_performance_arc_live_session_packet_covers_single_machine_edges -n 0
```

Expected: PASS.

### Task 3: CLI Parser, Handler, Help, And Dispatch

**Files:**
- Modify: `rytm_randomizer/reports/style_performance_arcs.py`
- Modify: `rytm_randomizer/cli.py`
- Modify: `rytm_randomizer/help_text.py`
- Modify: `tests/test_style_performance_arcs_report.py`
- Modify: `tests/test_cli.py`
- Modify: `tests/fixtures/cli_help_expected.txt`

- [ ] **Step 1: Add parser/handler tests**

Extend the existing parser/handler test to cover `_parse_arc_live_session_packet_cli_args` and `_handle_style_performance_arc_live_session_packet_report`, mirroring rehearsal manifest options.

- [ ] **Step 2: Add CLI dispatch/help tests**

Extend `test_style_performance_arc_cli_dispatch_and_help` to call:

```python
main([
    "style-performance-arc-live-session-packet-report",
    "--rytm",
    str(rytm_path),
    "--analog-four",
    str(a4_path),
    "--events",
    "--limit",
    "1",
])
```

Assert the output title and `Segment cards:`. Also assert `resolve_help_text("--help")` and command-specific help mention the new command.

- [ ] **Step 3: Verify RED**

Run:

```bash
python -m pytest tests/test_style_performance_arcs_report.py -n 0
```

Expected: FAIL on missing parser/handler/command/help.

- [ ] **Step 4: Implement CLI command**

Add parser/handler/command registration in `style_performance_arcs.py`; lazy command mapping in `cli.py`; help text and usage in `help_text.py`; expected CLI fixture and `tests/test_cli.py` usage string updates.

- [ ] **Step 5: Verify GREEN**

Run:

```bash
python -m pytest tests/test_style_performance_arcs_report.py -n 0
python -m pytest tests/test_cli.py tests/test_cli_coverage.py tests/test_real_midi_passive_cli_safety.py -n 0
```

Expected: PASS.

### Task 4: Docs And Closeout

**Files:**
- Modify: `README.md`
- Modify: `docs/STATUS.md`

- [ ] **Step 1: Add README command example**

Add one passive command example beside the rehearsal manifest report:

```text
python -m rytm_randomizer.cli style-performance-arc-live-session-packet-report --rytm "<RYTM_KITS.syx>" --analog-four "<ANALOG_FOUR_KITS.syx>" --events --limit 8
```

- [ ] **Step 2: Add STATUS entry**

Add a 2026-05-21 entry explaining that the passive CLI can now generate a live rehearsal session packet with launch checklist, suggested passive commands, segment cards, listen/go/reset cues, and JSON for future GUI/audio-analyzer workflows.

- [ ] **Step 3: Run full verification**

Run:

```bash
python -m vulture rytm_randomizer\cli.py rytm_randomizer\help_text.py rytm_randomizer\reports\style_performance_arcs.py tests\test_cli.py tests\test_style_performance_arcs_report.py --min-confidence 80
python -m ruff check .
python -m black --check --target-version=py311 .
python -m isort --profile black --check-only .
python -m pytest tests/architecture/ -q
python -m pytest -m fast
python -m pytest
python -m pytest --cov=rytm_randomizer --cov-branch --cov-report=term-missing
python scripts\code_review_gate.py --mode cli
```

Expected: all pass.

- [ ] **Step 4: Commit, push, and open PR**

Stage only intentional files:

```bash
git add README.md docs/STATUS.md docs/superpowers/specs/2026-05-21-live-rehearsal-session-packet-design.md docs/superpowers/plans/2026-05-21-live-rehearsal-session-packet-pr25.md rytm_randomizer/cli.py rytm_randomizer/help_text.py rytm_randomizer/reports/style_performance_arcs.py tests/fixtures/cli_help_expected.txt tests/test_cli.py tests/test_style_performance_arcs_report.py
git commit -m "feat: add live rehearsal session packet"
git push -u origin codex/live-rehearsal-session-packet-pr25
```

Open a ready PR against `modularize-v1.34` with the 18-gate checklist and strict-rules confirmation.
