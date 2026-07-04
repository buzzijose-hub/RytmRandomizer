# Summary

Adds a frontend-only, Synplant-inspired Patch Genome surface to the cockpit UI
and saves the five Synplant 2 reference screenshots under
`docs/assets/synplant-2-reference/`.

## What changed

- Added a typed `patchGenomeModel` with grouped design-preview genes for
  oscillator, envelope/LFO, filter/FX, and performance families.
- Added `PatchGenomePanel` with family selection, local gene locks,
  grow/reset variant controls, trait meters, and explicit preview/no-send
  status.
- Mounted the panel in the existing cockpit side stack without adding a
  WebSocket command, sidecar call, audio-analysis path, hardware arm path, or
  MIDI send path.
- Added focused Vitest coverage for the model, component interactions, and
  cockpit composition.
- Updated README/status docs and captured the design/spec plan for future UI
  work.

## Why this matters

This gives the cockpit the simple inspired randomizer surface from the design
discussion while keeping the DNA mapping/intelligence thread separate. It is a
reviewable UI cockpit, not an audio-to-patch engine.

## Test plan

```powershell
Set-Location 'C:\Users\Jose Buzzi\Documents\RytmRandomizer\.worktrees\synplant-cockpit-ui-design\desktop\web'
npm.cmd ci
npm.cmd run test:run
npm.cmd run test:coverage
npm.cmd run build
npm.cmd run lint
npm.cmd run e2e:ci

Set-Location 'C:\Users\Jose Buzzi\Documents\RytmRandomizer\.worktrees\synplant-cockpit-ui-design'
& 'C:\Users\Jose Buzzi\Documents\RytmRandomizer\.venv\Scripts\python.exe' -m pytest tests/architecture/test_readme_freshness.py tests/architecture/test_readme_is_product_facing.py tests/architecture/test_plan_doc_status_truth.py -q -n 0
& 'C:\Users\Jose Buzzi\Documents\RytmRandomizer\.venv\Scripts\python.exe' -m pytest tests/architecture/ -q -n 0
& 'C:\Users\Jose Buzzi\Documents\RytmRandomizer\.venv\Scripts\python.exe' -m ruff check .
& 'C:\Users\Jose Buzzi\Documents\RytmRandomizer\.venv\Scripts\python.exe' -m black --check --target-version=py311 .
& 'C:\Users\Jose Buzzi\Documents\RytmRandomizer\.venv\Scripts\python.exe' -m isort --profile black --check-only .
git diff --cached --check
git push -u origin codex/synplant-cockpit-ui-design
```

- [x] Full frontend Vitest coverage suite passed: 41 files, 476 tests, 100% statements/branches/functions/lines.
- [x] Frontend build passed.
- [x] Frontend ESLint passed.
- [x] Full Playwright e2e passed: 12 passed, 1 skipped.
- [x] README/plan status targeted architecture checks passed: 17 tests.
- [x] Full architecture suite passed locally with `-n 0`: 622 passed, 1 existing warn-only abstraction warning.
- [x] Python lint trio passed.
- [x] Pre-push mechanical gate passed: ruff, black, isort, architecture, and V1.34 parity 685/685.
- [x] No hardware test was run; this is frontend-only and passive.

## Plan-requirements conformance

Per [`docs/PLAN_REQUIREMENTS.md`](../PLAN_REQUIREMENTS.md), every non-trivial
PR must satisfy all 18 gates. Mark each `[x]`, or `[ ] N/A - <reason>`.

- [x] **Gate 1** - N/A: no Python package source file is touched in this design-only branch; frontend behavior is covered by Vitest.
- [x] **Gate 2** - V1.34 parity passed in the pre-push gate: 685 passed.
- [x] **Gate 3** - frontend lint/build, Python lint trio, architecture gate, and pre-push gate completed.
- [x] **Gate 4** - N/A: no Python source touched for vulture/dead-code purge.
- [x] **Gate 5** - docs updated: README, STATUS, design spec, implementation plan, and saved screenshot references.
- [x] **Gate 6** - TypeScript model uses explicit readonly types; no Python `Any` escape hatch introduced.
- [x] **Gate 7** - N/A: no Python state transition, MIDI send, or guardrail decision added.
- [x] **Gate 8** - tests are focused, behavior-named, and live under existing cockpit test structure.
- [x] **Gate 9** - no new top-level Python module or package.
- [x] **Gate 10** - N/A: no Python string-dispatch site touched.
- [x] **Gate 11** - no duplicated Python fixtures introduced.
- [x] **Gate 12** - N/A: no Python module-level constants added.
- [x] **Gate 13** - N/A: no environment variable added.
- [x] **Gate 14** - maintainability is scoped to one cockpit component, one model file, and existing CSS/test surfaces.
- [x] **Gate 15** - N/A: no reusable learned skill or rule needed.
- [x] **Gate 16** - execution shape is one bundled PR against `modularize-v1.34`, not stacked on another open PR.
- [x] **Gate 17** - abstraction reuse: uses the existing cockpit side stack, test harness, export surface, and CSS token system.
- [x] **Gate 18** - architecture docs/diagrams are N/A: no Python architecture boundary, protocol, registry, CLI, or dependency rule changed.

## Strict rules - non-negotiables

Per [`CONTRIBUTING.md` section Strict rules](../../CONTRIBUTING.md#strict-rules--non-negotiables):

- [x] **No hardware in tests** - no test opens a real MIDI port or mutates a connected device.
- [x] **Lazy MIDI imports** - no Python MIDI import path touched.
- [x] **Hardware-pinned packages** - `mido==1.3.3` and `python-rtmidi==1.5.8` not bumped.
- [x] **Passive default** - no passive CLI, sidecar command, arm path, or runtime MIDI behavior changed.
- [x] **No stacked PRs** - this PR's base is `modularize-v1.34`, not another open PR's head.
- [x] **No `--no-verify`** - hooks were not bypassed.

## Plan document

Plan doc: `docs/superpowers/plans/2026-07-03-synplant-inspired-cockpit-ui.md`

## Reviewer notes

This is intentionally UI-only. The Patch Genome panel does not dispatch
WebSocket commands, call the Python sidecar, analyze audio, synthesize patches,
open MIDI ports, arm hardware, or send MIDI.
