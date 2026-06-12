# Summary

Adds a passive Live Macro Actions deck to the Cockpit performance console so
the UI can show the OXI-style Rytm live macro moves as operator cards without
firing anything from the browser.

## What changed

- Added `macro_action_deck` to `live-gui-performance-console-report`, derived
  from the existing OXI live macro catalog and performance-flow metadata.
- Added deterministic cards for `kit-core`, `hard-groove`, `industrial`,
  `dub-pressure`, `transition`, and `home` with shell command, send policy,
  recovery action, affected pads, risk/status labels, safety lines, replay
  commands, and blocked active actions.
- Rendered the deck in the desktop `PerformanceConsole` route as Live Macro
  Actions with visible but disabled Prepare/Send controls.
- Updated the TypeScript protocol, demo packet, component test coverage, README,
  CLI reference, STATUS, and implementation plan.

## Why this matters

The current console packet is already reaching the desktop app through the
mock-safe route/WebSocket bridge. This makes it feel like a live performance
surface: Jose can see the next macro directions and the exact shell commands
that correspond to them, while real macro firing remains in the explicitly
armed snapshot shell.

This PR is passive metadata and UI only. It opens no MIDI ports, sends no MIDI,
does not dispatch sidecar commands, and does not mutate snapshots or hardware.

## Test plan

```bash
python -m pytest tests\test_live_gui_performance_console_model.py --cov=rytm_randomizer.reports.live_gui_performance_console_model --cov-branch --cov-report=term-missing --cov-fail-under=100 -n 0
python -m pytest tests\test_live_gui_performance_console_model.py tests\architecture\test_live_gui_protocol_ts_matches_python_typeddicts.py -n 0
python -m pytest tests\architecture\test_plan_doc_status_truth.py -n 0
python -m pytest tests\architecture\ -q
python -m pytest
python -m vulture rytm_randomizer tests --min-confidence 80
python -m ruff check .
python -m black --check --target-version=py311 .
python -m isort --profile black --check-only .
git diff --check
cd desktop/web && npm.cmd ci
cd desktop/web && npm.cmd run test:run -- tests/cockpit/PerformanceConsole.test.tsx
cd desktop/web && npm.cmd run test:run
cd desktop/web && npm.cmd run typecheck
cd desktop/web && npm.cmd run lint
cd desktop/web && npm.cmd run build
```

- [x] Touched backend coverage: 100% statement/branch for
  `live_gui_performance_console_model.py`.
- [x] Focused Python contract tests pass: 10 passed.
- [x] Plan lifecycle gate passes: 6 passed.
- [x] Architecture gate passes: 607 passed, with the existing warn-only
  duplicate `main` warning.
- [x] Full Python suite passes: 5694 passed, 3 skipped, 7 warnings.
- [x] Vulture clean at confidence 80.
- [x] Python lint trio clean: ruff, black, isort.
- [x] `git diff --check` passes.
- [x] Focused PerformanceConsole Vitest passes: 1 test passed.
- [x] Full frontend Vitest exits 0: 39 files passed / 393 tests passed, with
  existing jsdom navigation/canvas/provider-error console noise.
- [x] Frontend typecheck, ESLint, and production build pass.
- [ ] CI matrix green: pending after PR open.

## Plan-requirements conformance

Per `docs/PLAN_REQUIREMENTS.md`, every non-trivial PR must satisfy all 18
gates. Mark each `[x]`, or `[ ] N/A - <reason>`.

- [x] **Gate 1** - 100% branch coverage on the touched backend report; focused
  frontend tests cover the rendered macro deck.
- [x] **Gate 2** - V1.34 parity remains byte-identical through the full suite;
  no fixture regeneration.
- [x] **Gate 3** - lint clean: ruff, black, isort, and frontend ESLint.
- [x] **Gate 4** - no new dead code: vulture clean at confidence 80.
- [x] **Gate 5** - docs updated: README, CLI reference, STATUS, and plan doc.
- [x] **Gate 6** - type-system hygiene: frozen dataclass/TypedDict field order
  preserved, TypeScript protocol updated, no `Any` escape hatch.
- [ ] **Gate 7** - N/A: passive report/UI metadata only; no state transition,
  CC send, guardrail hot path, or hardware behavior added.
- [x] **Gate 8** - test hygiene: Python report tests and React component tests
  cover the new deck.
- [x] **Gate 9** - module organization: backend work stays in
  `rytm_randomizer/reports/`; frontend work stays in the existing Cockpit
  package; no new top-level Python module.
- [x] **Gate 10** - no new mode/intensity/page string-dispatch arm.
- [x] **Gate 11** - no duplicated shared fixture body.
- [x] **Gate 12** - new Python module-level constants use `Final`.
- [ ] **Gate 13** - N/A: no new environment variables.
- [x] **Gate 14** - maintainability reviewed in the plan doc; implementation
  reuses existing report builders and the existing console route.
- [ ] **Gate 15** - N/A: no new reusable skill or project rule discovered.
- [x] **Gate 16** - one clean-base branch/PR against `modularize-v1.34`; no
  stacked PRs.
- [x] **Gate 17** - abstraction reuse: derives cards from the OXI live macro
  catalog and performance-flow model instead of duplicating macro facts.
- [ ] **Gate 18** - N/A: no architecture boundary or diagram count changed;
  README/CLI/STATUS and protocol architecture coverage were updated.

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
`docs/superpowers/plans/2026-06-12-cockpit-performance-console-macro-actions.md`

## Reviewer notes

- The deck intentionally exposes disabled Prepare/Send controls so the UI shows
  the eventual performance intent without adding a browser-side hardware path.
- The armed snapshot shell remains the only place for real Rytm macro sends.
- Full frontend Vitest exits 0 with the existing jsdom navigation/canvas/context
  console noise seen on prior frontend runs.
