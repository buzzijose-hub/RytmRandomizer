# Summary

Adds passive local set planning to the Cockpit Performance Console. Operators can stage the current local crate / queued move / snapshot / depth selection as a future set-plan step, promote the next staged move, skip it, or clear the plan without dispatching any command or touching MIDI.

## What changed

- Added component-local set-plan state to `desktop/web/src/cockpit/PerformanceConsole.tsx`.
- Added local-only controls for staging, promoting, skipping, and clearing set-plan steps.
- Added a deterministic local set-plan queue panel with action summaries and local-only safety copy.
- Added CSS for compact staged set-plan entries inside the existing cockpit HUD.
- Added Vitest coverage for multi-step staging, promote/skip/clear behavior, empty-plan fallbacks, and hardware-send safety.
- Updated `README.md`, `docs/STATUS.md`, and the implementation plan.

## Why this matters

This turns the passive cinematic HUD into a more realistic live set scratchpad: Jose can prepare a sequence of intended moves before anything is wired to real hardware. The safety boundary stays unchanged: this PR does not add WebSocket dispatch, Tauri commands, sidecar commands, MIDI port opening, hardware arming, queued command execution, snapshot mutation, or MIDI sends.

## Test plan

```bash
npm.cmd run test:run -- tests/cockpit/PerformanceConsole.test.tsx
npm.cmd run test:coverage
npm.cmd run build
npm.cmd run typecheck
npm.cmd run lint -- --ext .ts,.tsx --max-warnings 0 src/cockpit/PerformanceConsole.tsx tests/cockpit/PerformanceConsole.test.tsx
python -m pytest tests\architecture\ -q
python -m pytest
python -m ruff check .
python -m black --check --target-version=py311 .
python -m isort --profile black --check-only .
git diff --check
```

- [x] Local pytest passes: 5697 passed, 3 skipped.
- [x] `tests/architecture/` passes: 607 passed.
- [x] Frontend coverage passes at 100% statements / branches / functions / lines.
- [x] Cockpit Performance Console focused test passes: 12 passed.
- [x] Cockpit web build, typecheck, and targeted ESLint pass.
- [x] Python ruff, black, and isort pass.
- [x] V1.34 parity remains byte-identical through the full pytest suite.
- [x] No hardware validation required; this is frontend/local-only and does not open MIDI ports or send MIDI.

## Plan-requirements conformance

Per [`docs/PLAN_REQUIREMENTS.md`](../docs/PLAN_REQUIREMENTS.md) - every non-trivial PR must satisfy all 18 gates. Mark each `[x]`, or `[ ] N/A - <reason>`.

- [x] **Gate 1** - 100% branch coverage on touched frontend files via `npm.cmd run test:coverage`.
- [x] **Gate 2** - V1.34 parity byte-identical through `python -m pytest`; no parity fixtures changed.
- [x] **Gate 3** - frontend build/typecheck/targeted ESLint clean; Python ruff, black, and isort clean.
- [x] **Gate 4** - no new dead code: new local helpers are all covered by focused Vitest and 100% branch coverage.
- [x] **Gate 5** - docs updated: `README.md`, `docs/STATUS.md`, implementation plan, and this PR body.
- [x] **Gate 6** - type-system hygiene: no `Any` escape hatches; new TS state and helpers are explicitly typed.
- [ ] Gate 7 - N/A: no backend state-transition, send path, guardrail decision, or MIDI hot path was added.
- [x] **Gate 8** - test hygiene: new tests live in the existing cockpit component test file and exercise behavior through rendered UI.
- [x] **Gate 9** - module organization hygiene: no new runtime modules or package roots.
- [x] **Gate 10** - string-literal dispatch hygiene: no new backend mode/intensity dispatch.
- [x] **Gate 11** - shared fixtures: no duplicated Python fixtures; local TS model variants stay scoped to one component test file.
- [x] **Gate 12** - constants: new frontend helpers are local component helpers; no Python module constants added.
- [x] **Gate 13** - env var docs: no new environment variables.
- [x] **Gate 14** - maintainability review: state is component-local, derived from existing packet types, and bounded to passive UI set planning.
- [ ] Gate 15 - N/A: no reusable new agent workflow or project rule was discovered.
- [x] **Gate 16** - execution shape: one clean-base bundled PR against `modularize-v1.34`; no stacked PRs.
- [x] **Gate 17** - abstraction reuse: reuses `LiveGuiPerformanceConsoleModelDict`, existing style queue packet types, and existing cockpit component/CSS surface.
- [ ] Gate 18 - N/A: no new architecture boundary, protocol, registry, CLI/report command, or diagram count changed.

## Strict rules - non-negotiables

Per [`CONTRIBUTING.md` Section Strict rules](../CONTRIBUTING.md#strict-rules--non-negotiables) - confirm each:

- [x] **No hardware in tests** - tests render React only; no real MIDI port is opened and no connected device is mutated.
- [x] **Lazy MIDI imports** - no MIDI imports touched.
- [x] **Hardware-pinned packages** - `mido==1.3.3` and `python-rtmidi==1.5.8` not changed.
- [x] **Passive default** - passive CLI behavior untouched.
- [x] **No stacked PRs** - branch is based on `origin/modularize-v1.34`.
- [x] **No `--no-verify`** - hooks were not bypassed.

## Plan document

Plan doc: `docs/superpowers/plans/2026-06-14-cockpit-local-set-planning-bundle.md`

## Reviewer notes

The active controls added here are intentionally local-only. They update React state and visible set-plan evidence only; they do not call a cockpit client, WebSocket, Tauri invoke, sidecar command, MIDI adapter, send planner, or queue executor.
