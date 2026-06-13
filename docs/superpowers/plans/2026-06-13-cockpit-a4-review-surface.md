# Cockpit A4 Review Surface

> Status: in-flight

## Goal

Surface the existing passive Analog Four OXI macro set planner and readiness
reports inside the Cockpit Performance Console as one review-only A4 panel. The
panel should let an operator see the warehouse-arc macro sequence, inspect the
next A4 macro's readiness rows, review validation commands, and understand the
promotion gates before any outbound A4 macro path exists.

## Scope

- Compose existing passive `analog-four-oxi-macro-set-planner-report` and
  `analog-four-oxi-macro-readiness-report` payloads.
- Add a GUI-ready `analog_four_review_surface` packet to
  `live-gui-performance-console-report --json`.
- Render the A4 review surface in the Cockpit Performance Console with disabled
  review/promote controls, blocked action chips, safety lines, validation steps,
  recovery notes, and promotion gates.
- Keep the feature passive and mock-safe: no sidecar command dispatch, no MIDI
  port opening, no hardware arm path, no MIDI send, no command execution, and no
  full A4 macro SEND.

## Verification

- `python -m pytest tests\test_live_gui_performance_console_model.py -n 0`
- `python -m pytest tests\architecture\test_live_gui_protocol_ts_matches_python_typeddicts.py -q -n 0`
- `npm.cmd run test:run -- tests/cockpit/PerformanceConsole.test.tsx`
- `npm.cmd run typecheck`
- Targeted Python and web lint/format checks for touched files.
