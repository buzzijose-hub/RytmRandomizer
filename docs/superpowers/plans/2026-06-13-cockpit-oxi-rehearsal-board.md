# Cockpit OXI Rehearsal Board

> Status: in-flight

## Goal

Surface the existing OXI live set strategy and Rytm live macro hardware rehearsal
reports inside the passive Cockpit Performance Console as one GUI-ready
Rehearsal Board. The board should help Jose rehearse the next live-performance
session by showing chapters, operator cues, SRC-first pad-lane checks, hardware
validation runway items, A4 promotion gates, recovery checks, and replay
commands.

## Scope

- Compose existing passive report payloads rather than duplicating OXI strategy
  or Rytm rehearsal data.
- Add the Rehearsal Board to `live-gui-performance-console-report --json`.
- Render the board in the Cockpit demo/preview route with disabled launch/fire
  controls.
- Keep all behavior mock-safe: no sidecar command dispatch, no MIDI port
  opening, no hardware arm path, no MIDI send, no A4 outbound macro promotion.

## Verification

- `python -m pytest tests\test_live_gui_performance_console_model.py -n 0`
- `python -m pytest tests\architecture\test_live_gui_protocol_ts_matches_python_typeddicts.py -q -n 0`
- `npm.cmd run test:run -- tests/cockpit/PerformanceConsole.test.tsx`
- `npm.cmd run typecheck`
- Targeted Python and web lint/format checks for touched files.
