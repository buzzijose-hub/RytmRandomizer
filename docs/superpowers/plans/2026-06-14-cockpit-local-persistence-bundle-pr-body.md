# Summary

Adds passive local rehearsal persistence to the Cockpit Performance Console. Operators can now keep the local set-plan/journal/rehearsal state across reloads, export it as copy-ready JSON, import a passive local rehearsal JSON payload, and clear the saved browser-local rehearsal state.

## What changed

- Added a versioned `LocalRehearsalSnapshot` schema inside `desktop/web/src/cockpit/PerformanceConsole.tsx`.
- Added safe `unknown` parsers for local journal entries, local set-plan entries, operator events, and the full local rehearsal snapshot.
- Initialized component-local selected crate, queued move, snapshot, preview depth, dry-run summary, journal entries, set-plan state, current step, operator log, and next local step index from browser-local storage.
- Added local auto-save via `localStorage` using `rytmrandomizer.performanceConsole.localRehearsal.v1`.
- Added component-local controls for local auto-save, export local rehearsal JSON, import local rehearsal JSON, and clear saved local rehearsal.
- Added compact persistence panel styling for the auto-save toggle, JSON import textarea, and exported JSON preview.
- Extended cockpit Vitest coverage for restore, export/import, clear-storage behavior, and unchanged no-hardware safety.
- Updated `README.md`, `docs/STATUS.md`, and the implementation plan.

## Why this matters

The cinematic Cockpit is becoming useful as a live operator planning surface before it can fire hardware. This gives Jose a way to recover a local rehearsal plan after reload, carry a plan between sessions as JSON, and validate the shape of future snapshot/journal import flows while preserving the current safety boundary.

## Safety notes

This is frontend/component-local only. The new controls write to browser `localStorage` and render/copy JSON in the React UI. They do not call a cockpit client, WebSocket, Tauri invoke, sidecar command, MIDI adapter, send planner, queue executor, hardware arm path, project file writer, snapshot mutator, or MIDI send.

## Test plan

```bash
npm.cmd run test:run -- tests/cockpit/PerformanceConsole.test.tsx
npm.cmd run typecheck
npm.cmd run build
npm.cmd run lint -- --ext .ts,.tsx --max-warnings 0 src/cockpit/PerformanceConsole.tsx tests/cockpit/PerformanceConsole.test.tsx
npm.cmd run test:coverage
python -m pytest tests\architecture\test_plan_doc_status_truth.py::test_every_plan_declares_its_lifecycle_status -q
python -m pytest tests\architecture\ -q
python -m pytest
python -m ruff check .
python -m black --check --target-version=py311 .
python -m isort --profile black --check-only .
git diff --check
```

- [x] TDD red: focused cockpit test failed because the local storage key was `null` and the persistence summary did not exist.
- [x] TDD red: focused cockpit test failed because `performance-console-local-import-input` did not exist.
- [x] Focused cockpit test passes: 14 passed.
- [x] Frontend typecheck passes.
- [x] Frontend production build passes.
- [x] Targeted ESLint passes.
- [x] Frontend coverage passes: 408 passed, 100% statements / branches / functions / lines.
- [x] Plan lifecycle status guard passes: 1 passed.
- [x] Architecture suite passes: 608 passed, 1 warning.
- [x] Full Python suite passes: 5698 passed, 3 skipped, 7 warnings.
- [x] Python ruff, black, and isort pass.
- [x] `git diff --check` passes.
- [x] No hardware validation required; this is frontend/component-local only and does not open MIDI ports or send MIDI.

## Plan-requirements conformance

Per [`docs/PLAN_REQUIREMENTS.md`](../../PLAN_REQUIREMENTS.md) - every non-trivial PR must satisfy all 18 gates. Mark each `[x]`, or `[ ] N/A - <reason>`.

- [x] **Gate 1** - 100% branch coverage on touched frontend files via `npm.cmd run test:coverage`.
- [x] **Gate 2** - V1.34 parity byte-identical through `python -m pytest`; no parity fixtures changed.
- [x] **Gate 3** - frontend build/typecheck/targeted ESLint clean; Python ruff, black, and isort clean.
- [x] **Gate 4** - no new dead code: new local persistence helpers/state are covered by focused Vitest tests.
- [x] **Gate 5** - docs updated: `README.md`, `docs/STATUS.md`, implementation plan, and this PR body.
- [x] **Gate 6** - type-system hygiene: no `Any` escape hatches; imported JSON is parsed from `unknown` through typed guards.
- [ ] Gate 7 - N/A: no backend state-transition, send path, guardrail decision, or MIDI hot path was added.
- [x] **Gate 8** - test hygiene: new coverage lives in the existing cockpit component test file and exercises behavior through rendered UI.
- [x] **Gate 9** - module organization hygiene: no new runtime modules or package roots.
- [x] **Gate 10** - string-literal dispatch hygiene: no new backend mode/intensity dispatch.
- [x] **Gate 11** - shared fixtures: no duplicated Python fixtures; local TS model variants stay scoped to one component test file.
- [x] **Gate 12** - constants: new frontend storage constants are component-local and versioned.
- [x] **Gate 13** - env var docs: no new environment variables.
- [x] **Gate 14** - maintainability review: local persistence stays bounded to the existing cockpit component and existing local rehearsal state.
- [ ] Gate 15 - N/A: no reusable new agent workflow or project rule was discovered.
- [x] **Gate 16** - execution shape: one clean-base bundled PR against `modularize-v1.34`; no stacked PRs.
- [x] **Gate 17** - abstraction reuse: reuses `PerformanceConsole`, existing local rehearsal state, existing style queue/snapshot packet types, and existing cockpit CSS surfaces.
- [ ] Gate 18 - N/A: no new architecture boundary, protocol, registry, CLI/report command, or diagram count changed.

## Strict rules - non-negotiables

Per [`CONTRIBUTING.md` Section Strict rules](../../../CONTRIBUTING.md#strict-rules--non-negotiables) - confirm each:

- [x] **No hardware in tests** - tests render React only; no real MIDI port is opened and no connected device is mutated.
- [x] **Lazy MIDI imports** - no MIDI imports touched.
- [x] **Hardware-pinned packages** - `mido==1.3.3` and `python-rtmidi==1.5.8` not changed.
- [x] **Passive default** - passive CLI behavior untouched.
- [x] **No stacked PRs** - branch is based on `origin/modularize-v1.34`.
- [x] **No `--no-verify`** - hooks were not bypassed.

## Plan document

Plan doc: `docs/superpowers/plans/2026-06-14-cockpit-local-persistence-bundle.md`

## Reviewer notes

The import/export controls intentionally operate on copy-ready JSON text in the browser. They are rehearsal-state controls, not file-system import/export, sidecar import/export, command dispatch, queue dispatch, or hardware send behavior.
