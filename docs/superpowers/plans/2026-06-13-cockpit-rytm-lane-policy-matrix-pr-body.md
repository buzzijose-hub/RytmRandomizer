# Summary

Adds a passive Rytm Lane Policy Matrix to the Cockpit Performance Console. The
console now exposes the OXI-style macro rules that matter for full-kit live
performance: pads 5/9/10/11 stay SRC-first with filter/LFO off, pads 6-8 get
tom/source movement with light filter and no LFO craziness, and Pad 12 remains
product-supported.

## What changed

- Added `rytm_lane_policy_matrix` to
  `live-gui-performance-console-report --json`.
- Reused the existing `oxi-live-macro-catalog-report` data instead of creating
  a duplicate macro policy source.
- Rendered a Cockpit Rytm Lane Policy Matrix with pad groups, macro policy
  rows, per-pad lane cards, blocked actions, safety lines, and disabled
  Apply/Send controls.
- Mirrored the new contract into the shared TypeScript live-GUI protocol and
  bundled demo model.
- Updated README, status, and plan docs.

## Why this matters

This moves the OXI-style randomizer toward a usable live Cockpit: before Jose
applies anything, he can see whether the selected macro respects the pad
discipline that worked in hardware testing.

## Test plan

```powershell
python -m pytest tests\test_live_gui_performance_console_model.py --cov=rytm_randomizer.reports.live_gui_performance_console_model --cov-branch --cov-report=term-missing --cov-fail-under=100 -n 0
python -m pytest tests\test_live_gui_performance_console_model.py tests\architecture\test_live_gui_protocol_ts_matches_python_typeddicts.py -q -n 0
python -m pytest
cd desktop\web
npm.cmd run test:run
npm.cmd run test:run -- tests/cockpit/PerformanceConsole.test.tsx
npm.cmd run typecheck
npm.cmd run lint -- --ext .ts,.tsx --max-warnings 0 src/cockpit/PerformanceConsole.tsx src/cockpit/performanceConsoleDemoModel.ts src/types/live_gui_protocol.ts tests/cockpit/PerformanceConsole.test.tsx
cd ..\..
python -m ruff check .
python -m black --check --target-version=py311 .
python -m isort --profile black --check-only .
git diff --check
```

- [x] Touched Python report has 100% branch coverage.
- [x] TypeScript protocol mirrors Python TypedDict fields.
- [x] Focused React coverage verifies the lane matrix renders with disabled
  Apply/Send controls.
- [x] Full Python test suite passes: 5697 passed, 3 skipped.
- [x] Full web Vitest suite passes: 39 files / 394 tests.
- [x] Lint/format checks pass.
- [ ] CI matrix green on all required jobs.

## Plan-requirements conformance

Per `docs/PLAN_REQUIREMENTS.md`:

- [x] **Gate 1** - Touched Python report verified at 100% branch coverage.
- [x] **Gate 2** - V1.34 parity not touched; no parity fixtures changed.
- [x] **Gate 3** - Python lint/format and web lint/typecheck verified locally.
- [x] **Gate 4** - No dead code introduced; helpers are covered by focused
  tests.
- [x] **Gate 5** - Docs updated: README, `docs/STATUS.md`, plan doc, and PR
  body file.
- [x] **Gate 6** - No `Any` escape hatches; TS/Python contracts stay typed.
- [ ] Gate 7 - N/A: passive report/UI metadata only; no state transition, send
  path, or guardrail decision changed.
- [x] **Gate 8** - Focused Python and React tests cover the new lane-policy
  matrix.
- [x] **Gate 9** - No new package modules or top-level source files.
- [x] **Gate 10** - No new mode/intensity/page string-dispatch path.
- [x] **Gate 11** - No duplicate fixtures introduced.
- [x] **Gate 12** - New module constants are annotated with `Final`.
- [x] **Gate 13** - No new environment variables.
- [x] **Gate 14** - Maintains the existing passive report composition pattern
  and avoids duplicating OXI macro data.
- [ ] Gate 15 - N/A: no new reusable agent skill needed for this UI/report
  follow-up.
- [x] **Gate 16** - One clean branch/PR based on `modularize-v1.34`; no stacked
  PR.
- [x] **Gate 17** - Reuses existing OXI live macro catalog abstractions and the
  existing Performance Console render pattern.
- [ ] Gate 18 - N/A: no new architecture boundary or diagram surface; README
  and status explain the user-facing surface.

## Strict rules - non-negotiables

- [x] **No hardware in tests** - no test opens a real MIDI port or mutates a
  device.
- [x] **Lazy MIDI imports** - unchanged; passive report path imports no real
  MIDI adapter.
- [x] **Hardware-pinned packages** - unchanged.
- [x] **Passive default** - unchanged; Apply/Send controls are disabled.
- [x] **No stacked PRs** - base is `modularize-v1.34`.
- [x] **No `--no-verify`** - normal push path used; hooks are not bypassed.

## Plan document

`docs/superpowers/plans/2026-06-13-cockpit-rytm-lane-policy-matrix.md`

## Reviewer notes

This is a passive GUI/report bundle only. It does not add macro dispatch,
unattended playback, WebSocket command dispatch, port opening, hardware arm
behavior, command execution, MIDI sending, or snapshot mutation.
