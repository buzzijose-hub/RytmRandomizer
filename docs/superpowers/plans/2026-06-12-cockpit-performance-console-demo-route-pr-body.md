# Summary

Adds a bundled passive demo model for the Cockpit performance console route so
the installed/local desktop UI can render `#/performance-console` or `#/console`
without waiting for an injected test harness packet or a sidecar
`session_status` frame.

## What changed

- Promoted the typed performance-console fixture into
  `desktop/web/src/cockpit/performanceConsoleDemoModel.ts`.
- Updated the App hash router so injected performance-console packets still win,
  but the route falls back to the bundled passive demo model when none is
  supplied.
- Kept the test fixture as a small re-export of the source-owned model so tests
  and the app share one contract.
- Updated router coverage and project status/docs.

## Why this matters

PR #163 made the route render an injected console packet. This follow-up makes
the route useful in the real app immediately: Jose can open the cockpit and jump
to the passive 12-pad Rytm + Analog Four performance-console preview while the
runtime sidecar bridge is still catching up.

The demo packet remains static frontend data. It cannot open a MIDI port, arm
hardware, dispatch queued commands, or send MIDI.

## Test plan

```bash
cd desktop/web && npm.cmd run test:run -- tests/router.test.tsx tests/cockpit/PerformanceConsole.test.tsx
cd desktop/web && npm.cmd run typecheck
cd desktop/web && npm.cmd run lint
cd desktop/web && npm.cmd run test:run
cd desktop/web && npm.cmd run build
python -m pytest tests/architecture/ -q
python -m pytest
python -m ruff check .
python -m black --check --target-version=py311 .
python -m isort --profile black --check-only .
git diff --check
```

- [x] Focused frontend route/console tests pass: 13 passed.
- [x] Full frontend Vitest suite passes: 390 passed.
- [x] Frontend typecheck and ESLint pass.
- [x] Frontend production build passes.
- [x] Architecture gate passes: 607 passed, 1 existing warn-only duplicate
  `main` warning.
- [x] Full Python suite passes: 5691 passed, 3 skipped.
- [x] Python lint trio passes: ruff, black, isort.
- [x] `git diff --check` passes.
- [ ] CI matrix green: pending after PR open.

## Plan-requirements conformance

Per `docs/PLAN_REQUIREMENTS.md`, every non-trivial PR must satisfy all 18 gates.
Mark each `[x]`, or `[ ] N/A - <reason>`.

- [ ] **Gate 1** - N/A: frontend/static demo model only; no touched Python
  branch-coverage target.
- [x] **Gate 2** - V1.34 parity remains byte-identical through the full suite;
  no fixture regeneration.
- [x] **Gate 3** - lint clean: frontend ESLint plus Python ruff, black, and
  isort.
- [ ] **Gate 4** - N/A: no new Python runtime symbols; no backend dead-code
  surface added.
- [x] **Gate 5** - docs updated: `docs/STATUS.md`, plan doc, and this PR body.
- [x] **Gate 6** - type-system hygiene: the demo model uses the existing
  `LiveGuiPerformanceConsoleModelDict` contract.
- [ ] **Gate 7** - N/A: no state transition, CC send, guardrail hot path, or
  hardware behavior added.
- [x] **Gate 8** - test hygiene: router tests cover injected-model priority and
  bundled-demo fallback.
- [x] **Gate 9** - module organization: frontend code stays inside the existing
  Cockpit package; no Python top-level module added.
- [x] **Gate 10** - no new mode/intensity string-dispatch arm.
- [x] **Gate 11** - shared fixture hygiene improved by replacing the duplicated
  test fixture body with a source re-export.
- [ ] **Gate 12** - N/A: no new Python module-level constants.
- [ ] **Gate 13** - N/A: no new environment variables.
- [x] **Gate 14** - maintainability reviewed in the plan doc; the fallback is
  route-scoped and keeps injected models authoritative.
- [ ] **Gate 15** - N/A: no new reusable skill or project rule discovered.
- [x] **Gate 16** - one clean-base branch/PR against `modularize-v1.34`; no
  stacked PR.
- [x] **Gate 17** - abstraction reuse: reuses the existing App router,
  Cockpit barrel export, typed protocol, and PerformanceConsole renderer.
- [ ] **Gate 18** - N/A: no architecture boundary or diagram count changed.

## Strict rules - non-negotiables

Per `CONTRIBUTING.md` strict rules, confirm each:

- [x] **No hardware in tests** - no test opens a real MIDI port; no test mutates
  a connected device.
- [x] **Lazy MIDI imports** - `mido` and `python-rtmidi` remain lazy and
  restricted.
- [x] **Hardware-pinned packages** - `mido==1.3.3` and `python-rtmidi==1.5.8`
  not bumped.
- [x] **Passive default** - `python -m rytm_randomizer.cli` does not open a real
  port.
- [x] **No stacked PRs** - this branch targets `modularize-v1.34`.
- [x] **No `--no-verify`** - hooks were not bypassed.

## Plan document

Plan doc:
`docs/superpowers/plans/2026-06-12-cockpit-performance-console-demo-route.md`

## Reviewer notes

- Full frontend Vitest exits 0 with the existing jsdom navigation/canvas/context
  console noise seen on prior runs.
- This is static frontend demo data only; runtime WebSocket delivery of a live
  console packet remains a follow-up.
