# Cockpit Rytm Lane Policy Matrix

> Status: in-flight

## Goal

Expose the existing OXI live macro lane policy inside the passive Cockpit
Performance Console so Jose and reviewers can see how each macro treats pads
5-12 before any future GUI apply/send path exists.

## Product Rules Captured

- Pads 5, 9, 10, and 11 stay SRC-first. They avoid filter/LFO movement and only
  allow the AMP-side overdrive/delay/reverb families.
- Pads 6-8 are tom/source movement pads. They can receive useful SRC movement,
  light filter movement, AMP-side overdrive/delay/reverb, and no LFO craziness.
- Pad 12 remains product-supported even if Jose does not usually use it live.
- Macro policy stays derived from `oxi-live-macro-catalog-report`; the console
  must not introduce a parallel policy source.

## Scope

- Add `rytm_lane_policy_matrix` to
  `live-gui-performance-console-report --json`.
- Render the matrix in the Cockpit Performance Console near the 12-pad surface.
- Show pad groups, macro rows, per-pad lane policy cards, blocked actions,
  safety lines, replay metadata, and disabled Apply/Send controls.
- Keep the work passive and mock-safe: no sidecar command dispatch, no command
  execution, no MIDI port opening, no hardware arm path, no MIDI send, and no
  snapshot mutation.

## Verification

- `python -m pytest tests\test_live_gui_performance_console_model.py --cov=rytm_randomizer.reports.live_gui_performance_console_model --cov-branch --cov-report=term-missing --cov-fail-under=100 -n 0`
- `python -m pytest tests\test_live_gui_performance_console_model.py tests\architecture\test_live_gui_protocol_ts_matches_python_typeddicts.py -q -n 0`
- `npm.cmd run test:run -- tests/cockpit/PerformanceConsole.test.tsx`
- `npm.cmd run typecheck`
- Targeted Python and web lint/format checks for touched files.
