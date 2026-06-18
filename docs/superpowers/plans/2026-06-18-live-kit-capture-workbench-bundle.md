# Live Kit Capture Workbench Bundle Implementation Plan

> Status: in-flight

**Goal:** Extend the passive Cockpit performance console from a Live Kit
Capture explainer panel into a GUI-ready Live Kit Capture Workbench package
that shows capture slots, anchor verification, mutation readiness, recovery
gates, and future package metadata without touching hardware.

**Architecture:** Reuse the existing
`live-gui-performance-console-report` packet and Performance Console route.
Add one nested `live_kit_capture_workbench` object beside
`live_kit_capture_panel`, mirror it in the shared TypeScript protocol and demo
fixture, render it passively in React, and update README/CLI/status docs.

**Safety:** Passive/mock-safe only. No SysEx receive from Cockpit, no MIDI port
opening, no WebSocket command dispatch, no snapshot mutation, no hardware arm,
and no MIDI send.

## Workstreams

| Workstream | Owns | Depends on | Parallel with |
|---|---|---|---|
| WS1 Python contract | Python model, payload, text report, pytest | clean base | WS3 docs after shape is known |
| WS2 Frontend contract | TypeScript protocol, demo model, React section, Vitest | WS1 field names | WS3 docs |
| WS3 Docs and PR package | Spec, plan, README, CLI reference, status, PR body | WS1/WS2 terminology | WS1/WS2 |

## Implementation Tasks

- [x] Add the design spec and plan document.
- [x] Write failing Python tests for `live_kit_capture_workbench`.
- [x] Implement the Python workbench builder, payload wiring, blocked/safety
  aggregation, console id input, and text-report lines.
- [x] Write failing TypeScript/React assertions for the workbench section.
- [x] Add the shared TypeScript protocol interfaces and demo data.
- [x] Render the passive workbench UI with disabled active controls.
- [x] Update README, CLI reference, and status.
- [x] Run focused Python, frontend, lint, architecture, and full gates.
- [ ] Commit, push, and open one PR against `modularize-v1.34`.

## 18-Gate Expectations

- Gate 1: touched Python coverage stays at 100% via focused coverage check.
- Gate 2: V1.34 parity fixtures are not touched.
- Gate 3: ruff, black, isort, TypeScript typecheck, and frontend lint/build
  pass.
- Gate 4: no dead-code additions; all new fields are consumed by tests/UI.
- Gate 5: README, CLI reference, status, spec, and plan update together.
- Gate 6: no `Any`; Python shape remains dict/TypedDict-friendly and TS
  protocol mirrors it.
- Gate 7: report-only passive metadata; no new hot-path state transition.
- Gate 8: tests extend existing mirrored files.
- Gate 9: no new top-level Python modules.
- Gate 10: no mode string dispatch added.
- Gate 11: no duplicate shared fixtures.
- Gate 12: new module-level constants use `Final`.
- Gate 13: no new environment variables.
- Gate 14: maintainability handled by reusing the existing console packet
  instead of creating a parallel workbench surface.
- Gate 15: no new learned-skill extraction required for this narrow bundle.
- Gate 16: clean worktree/branch, one bundled PR, no stacked PRs.
- Gate 17: reuses the existing passive report and Performance Console
  abstractions.
- Gate 18: architecture docs do not need new diagrams because this is a nested
  console packet extension, not a new boundary.

## Verification Plan

```powershell
python -m pytest tests/test_live_gui_performance_console_model.py -n 0 -q
python -m pytest tests/test_live_gui_performance_console_model.py -n 0 --cov=rytm_randomizer.reports.live_gui_performance_console_model --cov=rytm_randomizer.reports.performance_console.live_kit_capture_workbench --cov-branch --cov-fail-under=100 --cov-report=term-missing
npm.cmd run test:run -- PerformanceConsole.test.tsx
npm.cmd run typecheck
npm.cmd run lint
npm.cmd run build
python -m pytest tests/architecture/ -q
python -m pytest
python -m ruff check .
python -m black --check --target-version=py311 .
python -m isort --profile black --check-only .
python scripts/code_review_gate.py --mode cli
```

## Rollback

Revert the single bundle commit. The workbench is additive passive metadata and
UI rendering, so rollback removes the nested packet and section without
changing the armed snapshot shell, V1.34 parity behavior, or hardware paths.
