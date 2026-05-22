# Live Performance State Packet Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a passive GUI-ready live performance state packet that composes the live command deck into current-screen state for future live UI and audio-analyzer routing.

**Architecture:** Keep the feature in `rytm_randomizer/reports/` as a passive report layer above `live_command_deck.py`. The new report must consume existing command-deck data, expose deterministic text and JSON, register through the passive CLI registry, and avoid active MIDI imports or hardware behavior.

**Tech Stack:** Python dataclasses, existing `CliCommand` registry, pytest fast tests, existing passive formatter helpers.

---

## Feature Shape

Jose approved the next live-performance step after PR #83: turn the operator command deck into a stable state object a future GUI can render. The packet answers "what should the screen show right now?" rather than "what report should the operator read?"

The report is intentionally passive:

- It reads only in-memory report objects and optional saved `.syx` paths already supported by upstream reports.
- It never opens a MIDI port, imports real MIDI modules, sends MIDI, mutates hardware, or writes files.
- It preserves the upstream command deck, transition timeline, show export, cockpit, stage routing, cue sheet, and reference-match JSON chain for traceability.

## Files

- Create `rytm_randomizer/reports/live_performance_state.py`
- Modify `rytm_randomizer/cli.py`
- Modify `rytm_randomizer/help_text.py`
- Modify `tests/test_style_performance_arcs_report.py`
- Modify `tests/test_cli.py`
- Modify `tests/test_cli_coverage.py`
- Modify `tests/test_real_midi_passive_cli_safety.py`
- Modify `tests/test_manual_hardware_validation_doc.py`
- Modify `tests/fixtures/cli_help_expected.txt`
- Modify `README.md`
- Modify `docs/STYLE_ANALYSIS.md`
- Modify `docs/MANUAL_HARDWARE_VALIDATION.md`
- Modify `docs/ARCHITECTURE.md`
- Modify `docs/ARCHITECTURE_DIAGRAMS.md`
- Modify `docs/STATUS.md`

## Tasks

### Task 1: Red Tests

- [x] Add tests proving a new `live_performance_state` module builds a state packet from a live command deck.
- [x] Assert the packet exposes current cue, next cues, machine panels, action bar, warning stack, recovery stack, replay commands, text output, and JSON.
- [x] Add parser/CLI edge tests for source selection, cue/lookahead/limit validation, text output, JSON output, and safe errors.
- [x] Run the focused tests and verify they fail because the module is missing.

Command:

```powershell
python -m pytest tests/test_style_performance_arcs_report.py::test_style_performance_arc_live_state_packet_builds_gui_ready_state tests/test_style_performance_arcs_report.py::test_style_performance_arc_live_state_packet_parser_cli_and_edges -n 0 -q
```

Expected red result:

```text
ModuleNotFoundError: No module named 'rytm_randomizer.reports.live_performance_state'
```

### Task 2: Report Module

- [x] Add frozen dataclasses for cue state, machine state, and the aggregate state packet.
- [x] Compose from `StylePerformanceArcLiveCommandDeckReport`.
- [x] Preserve deterministic identifiers using a SHA-256 digest prefix.
- [x] Render deterministic text sections: summary, current GUI state, next cue strip, machine state panels, action bar, warning stack, recovery stack, replay commands, and safety.
- [x] Render deterministic JSON with the full upstream report chain.
- [x] Verify the focused report tests pass.

Command:

```powershell
python -m pytest tests/test_style_performance_arcs_report.py::test_style_performance_arc_live_state_packet_builds_gui_ready_state tests/test_style_performance_arcs_report.py::test_style_performance_arc_live_state_packet_parser_cli_and_edges -n 0 -q
```

Expected green result:

```text
2 passed
```

### Task 3: Public CLI Surface

- [x] Register `style-performance-arc-live-state-report` as a lazy passive CLI command.
- [x] Add command help and top-level usage.
- [x] Add passive MIDI safety coverage for `--help`.
- [x] Add README and manual validation doc assertions.
- [x] Regenerate the top-level CLI help fixture from the actual CLI output after help text is wired.

### Task 4: Docs And Closeout

- [x] Update README, STYLE_ANALYSIS, manual hardware validation, architecture, architecture diagrams, and status.
- [x] Run focused report, CLI coverage, passive safety, manual hardware docs, architecture, fast, full, coverage, lint, and review gates.
- [x] Exact-stage only intended files, commit, push, open PR to `modularize-v1.34`, and request `edward-rosado`.
