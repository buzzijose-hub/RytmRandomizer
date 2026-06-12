# Summary

Adds the passive Cockpit performance console packet after PR #161 so the desktop UI can review one composed, GUI-ready model for the cinematic RytmRandomizer console direction without launching a GUI, opening MIDI ports, or sending MIDI.

## What changed

- Added `live-gui-performance-console-report` as a lazy passive CLI report that composes device inventory, Rytm 12-pad surface, A4 set-plan review, Style Crates queue/journal, snapshot history, command queue, safety checklist, blocked actions, safety lines, and replay commands.
- Added Python tests proving deterministic JSON/text output, blocked active actions, malformed optional payload handling, blank session-label validation, and passive MIDI-import safety.
- Added the matching TypeScript protocol aliases plus an exported `PerformanceConsole` React component for passive render review of the packet.
- Updated README, CLI reference, STATUS, plan docs, CLI help fixture, and live GUI protocol architecture coverage.

## Why this matters

This turns the recent cinematic UI direction into a real contract the app can consume: one packet for the device rail, all 12 Rytm pads, style queue, snapshot/journal history, A4 runway, and safety state. The work keeps the current hardware rule intact: this is mock-safe review metadata only, with real send/queue/A4 actions still represented as blocked actions.

## Test plan

```bash
python -m pytest tests\test_live_gui_performance_console_model.py --cov=rytm_randomizer.reports.live_gui_performance_console_model --cov-branch --cov-fail-under=100 --cov-report=term-missing -n 0
python -m vulture rytm_randomizer\reports\live_gui_performance_console_model.py tests\test_live_gui_performance_console_model.py --min-confidence 80
python -m pytest tests\architecture\test_live_gui_protocol_ts_matches_python_typeddicts.py tests\architecture\test_no_new_top_level_modules.py tests\architecture\test_no_any_escape_hatches.py -q -n 0
python -m pytest tests\architecture\test_plan_doc_status_truth.py tests\architecture\test_plan_requirements_referenced.py -q -n 0
python -m pytest tests\test_live_gui_performance_console_model.py tests\test_cli.py tests\test_cli_coverage.py tests\test_real_midi_passive_cli_safety.py -q -n 0
python -m pytest tests\architecture\ -q
python -m pytest
python -m pytest --cov=rytm_randomizer --cov-branch --cov-report=term-missing
python -m ruff check .
python -m black --check --target-version=py311 .
python -m isort --profile black --check-only .
git diff --check
cd desktop/web && npm.cmd run test:run -- tests/cockpit/PerformanceConsole.test.tsx
cd desktop/web && npm.cmd run test:run
cd desktop/web && npm.cmd run typecheck
cd desktop/web && npm.cmd run lint
```

- [x] Local pytest passes: 5691 passed, 3 skipped.
- [x] `tests/architecture/` passes: 607 passed, 1 existing warn-only duplicate `main` warning.
- [x] Lint trio clean: ruff, black, isort.
- [x] Coverage stays >=95% pure-branch: full coverage total 98.80%; touched new report 100%.
- [x] V1.34 parity remains byte-identical via the full suite.
- [x] No new dead code: vulture clean at confidence 80 on the touched backend report/test.
- [ ] CI matrix green on all 3 OSes: pending after PR open.

## Plan-requirements conformance

Per [`docs/PLAN_REQUIREMENTS.md`](../docs/PLAN_REQUIREMENTS.md) - every non-trivial PR must satisfy all 18 gates. Mark each `[x]`, or `[ ] N/A - <reason>`.

- [x] **Gate 1** - 100% branch coverage on touched backend report; project coverage 98.80%.
- [x] **Gate 2** - V1.34 parity byte-identical through the full suite; no fixture regeneration.
- [x] **Gate 3** - lint clean: ruff, black `--target-version=py311`, and isort.
- [x] **Gate 4** - no new dead code: vulture clean on touched backend report/test.
- [x] **Gate 5** - docs updated: README, CLI reference, STATUS, plan docs, help fixture.
- [x] **Gate 6** - type-system hygiene: frozen dataclass, TypedDict sibling, `Final` constants, no `Any` escape hatch.
- [ ] **Gate 7** - N/A: passive report/render contract only; no state transition, CC send, or guardrail hot path added.
- [x] **Gate 8** - test hygiene: focused Python and Vitest coverage for the new surfaces.
- [x] **Gate 9** - module organization: backend code stays inside `rytm_randomizer/reports/`; no new top-level package module.
- [x] **Gate 10** - no new mode/intensity/page string-dispatch arm.
- [x] **Gate 11** - no duplicated shared fixture bodies.
- [x] **Gate 12** - module-level constants use `Final`.
- [ ] **Gate 13** - N/A: no new environment variables.
- [x] **Gate 14** - maintainability reviewed in the plan doc; the implementation aggregates existing report builders.
- [ ] **Gate 15** - N/A: no new reusable skill or project rule discovered.
- [x] **Gate 16** - one post-#161 branch/PR against `modularize-v1.34`; no stacked PR.
- [x] **Gate 17** - abstraction reuse: uses existing report builders, CLI registry, passive formatter, and TypeScript protocol architecture test.
- [ ] **Gate 18** - N/A: no architecture boundary or diagram count changed; README/CLI/STATUS docs and protocol architecture test were updated.

## Strict rules - non-negotiables

Per [`CONTRIBUTING.md` Section Strict rules](../CONTRIBUTING.md#strict-rules--non-negotiables) - confirm each:

- [x] **No hardware in tests** - no test opens a real MIDI port; no test mutates a connected device.
- [x] **Lazy MIDI imports** - `mido` and `python-rtmidi` remain lazy and restricted.
- [x] **Hardware-pinned packages** - `mido==1.3.3` and `python-rtmidi==1.5.8` not bumped.
- [x] **Passive default** - `python -m rytm_randomizer.cli` does not open a real port.
- [x] **No stacked PRs** - this branch targets `modularize-v1.34`.
- [x] **No `--no-verify`** - hooks were not bypassed.

## Plan document

Plan doc: `docs/superpowers/plans/2026-06-12-cockpit-performance-console-bundle.md`

## Reviewer notes

- `PerformanceConsole` is exported but not wired into `Cockpit.tsx` yet because no runtime state source currently supplies the composed console packet. This PR lands the passive contract and tested renderer only.
- `rytm_randomizer/reports/__init__.py` is intentionally unchanged to preserve the reports package lazy-import boundary; the new command is lazy-loaded through `rytm_randomizer/cli.py`.
- Full frontend Vitest exits 0 with existing jsdom console noise for navigation/canvas/provider-error tests.
