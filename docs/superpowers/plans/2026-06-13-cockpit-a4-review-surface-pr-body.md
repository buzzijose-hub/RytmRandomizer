# Summary

Adds a passive Analog Four Review Surface to the Cockpit Performance Console.
The console now composes the existing A4 OXI macro set planner and readiness
reports into one GUI-ready panel showing the `warehouse-arc` sequence, next
macro readiness rows, soft-capture preflight, validation workflow, recovery
notes, promotion gates, blocked actions, and safety lines.

## What changed

- Added `analog_four_review_surface` to
  `live-gui-performance-console-report --json`.
- Reused the existing passive A4 set planner and A4 readiness reports instead
  of duplicating macro data.
- Rendered a dedicated Cockpit A4 Review Surface with disabled Review/Promote
  controls.
- Mirrored the new contract into the shared TypeScript live-GUI protocol and
  demo model.
- Updated README, status, and plan docs.

## Why this matters

This is the next clean step toward the Analog Four side of the OXI-style
randomizer: Jose can rehearse the synth macro arc visually beside the Rytm
12-pad/OXI surface, while full A4 macro SEND stays blocked until separate
hardware validation promotes it.

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
git push -u origin codex/cockpit-a4-review-surface
```

- [x] Touched Python report has 100% branch coverage.
- [x] Full Python test suite passes: 5696 passed, 3 skipped.
- [x] Full web Vitest suite passes: 39 files / 394 tests.
- [x] TypeScript protocol mirrors Python TypedDict fields.
- [x] Pre-push mechanical gates pass: ruff, black, isort, architecture, V1.34 parity.
- [ ] CI matrix green on all required jobs.

## Plan-requirements conformance

Per `docs/PLAN_REQUIREMENTS.md`:

- [x] **Gate 1** - Touched Python report verified at 100% branch coverage.
- [x] **Gate 2** - V1.34 parity passed in pre-push; no parity fixtures touched.
- [x] **Gate 3** - Python lint/format and web lint/typecheck verified locally.
- [x] **Gate 4** - Ruff/vulture-style dead-code checks satisfied by ruff and architecture gates; no unused code introduced.
- [x] **Gate 5** - Docs updated: README, `docs/STATUS.md`, plan doc, and PR body file.
- [x] **Gate 6** - No `Any` escape hatches; TS/Python contracts stay typed.
- [ ] Gate 7 - N/A: passive report/UI metadata only; no state transition, send path, or guardrail decision changed.
- [x] **Gate 8** - Focused Python and React tests cover the new review surface.
- [x] **Gate 9** - No new package modules or top-level source files.
- [x] **Gate 10** - No new mode/intensity/page string-dispatch path.
- [x] **Gate 11** - No duplicate fixtures introduced.
- [x] **Gate 12** - New module constants are annotated with `Final`.
- [x] **Gate 13** - No new environment variables.
- [x] **Gate 14** - Maintains the existing passive report composition pattern and avoids duplicating A4 macro data.
- [ ] Gate 15 - N/A: no new reusable agent skill needed for this UI/report follow-up.
- [x] **Gate 16** - One clean branch/PR based on `modularize-v1.34`; no stacked PR.
- [x] **Gate 17** - Reuses existing A4 planner/readiness abstractions and the existing Performance Console render pattern.
- [ ] Gate 18 - N/A: no new architecture boundary or diagram surface; README/status explain the user-facing surface.

## Strict rules - non-negotiables

- [x] **No hardware in tests** - no test opens a real MIDI port or mutates a device.
- [x] **Lazy MIDI imports** - unchanged; passive report path imports no real MIDI adapter.
- [x] **Hardware-pinned packages** - unchanged.
- [x] **Passive default** - unchanged; A4 Review/Promote controls are disabled.
- [x] **No stacked PRs** - base is `modularize-v1.34`.
- [x] **No `--no-verify`** - pre-push hook ran and passed.

## Plan document

`docs/superpowers/plans/2026-06-13-cockpit-a4-review-surface.md`

## Reviewer notes

This is a passive GUI/report bundle only. It does not add A4 macro SEND,
unattended playback, WebSocket command dispatch, port opening, hardware arm
behavior, command execution, or MIDI sending.
