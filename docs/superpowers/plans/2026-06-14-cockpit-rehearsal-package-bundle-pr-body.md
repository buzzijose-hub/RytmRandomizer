# Summary

Adds a passive Cockpit rehearsal-package bundle on top of the existing
browser-local rehearsal persistence. The Performance Console can now wrap its
local rehearsal snapshot in a portable package with manifest metadata,
compatibility checks, device/safety evidence, blocked-action evidence, recovery
notes, and backwards-compatible raw snapshot import.

## What changed

- Added typed local rehearsal package parsing/building in
  `desktop/web/src/cockpit/PerformanceConsole.tsx`.
- Added `Export local rehearsal package` and `Import local rehearsal package`
  controls beside the existing raw JSON import/export controls.
- Added visible package evidence: manifest, compatibility status/checks,
  device list, safety checklist, blocked actions, recovery notes, and exported
  package JSON.
- Recompute imported package compatibility against the current passive packet
  so missing crate/queue/snapshot references stay visible as `needs review`.
- Preserved old raw local rehearsal JSON import compatibility.
- Added focused Vitest coverage and compact CSS for the package evidence panel.
- Updated `README.md`, `docs/STATUS.md`, and the implementation plan.

## Why this matters

The operator can now hand off or archive a local performance rehearsal as one
reviewable package instead of a raw state blob, while preserving the project's
passive/mock-first safety boundary. This is still browser-local rehearsal
evidence only; it does not create a SEND path.

## Test plan

```powershell
Set-Location 'C:\Users\Jose Buzzi\Documents\RytmRandomizer\desktop\web'
npm.cmd run test:run -- tests/cockpit/PerformanceConsole.test.tsx
npm.cmd run test:coverage
npm.cmd run typecheck
npm.cmd run build
npm.cmd run lint -- --ext .ts,.tsx --max-warnings 0 src/cockpit/PerformanceConsole.tsx tests/cockpit/PerformanceConsole.test.tsx

Set-Location 'C:\Users\Jose Buzzi\Documents\RytmRandomizer'
python -m pytest tests\architecture\ -q -n 0
python -m ruff check .
python -m black --check --target-version=py311 .
python -m isort --profile black --check-only .
git diff --check
```

- [x] Focused Performance Console Vitest coverage passes.
- [x] Full frontend coverage completed at 100% statements/branches/functions/lines.
- [x] Local frontend type/build/lint verification completed.
- [x] Python architecture gate completed with `-n 0` on local Windows/Python 3.13: 608 passed, 1 existing warn-only abstraction warning.
- [x] Python lint trio completed.
- [x] Full Python suite was attempted in local xdist mode and hit a local worker crash in `test_no_unreferenced_top_level_symbols.py`; that file and the full architecture gate pass with `-n 0`, and this PR does not touch Python runtime code.
- [x] No hardware test was run; this change is passive frontend/local state only.

## Plan-requirements conformance

Per [`docs/PLAN_REQUIREMENTS.md`](../PLAN_REQUIREMENTS.md) - every
non-trivial PR must satisfy all 18 gates. Mark each `[x]`, or `[ ] N/A -
<reason>`.

- [x] **Gate 1** - frontend touched file coverage is 100% statements/branches/functions/lines under `npm.cmd run test:coverage`; no touched Python package file.
- [x] **Gate 2** - V1.34 parity byte-identical by scope; no V1.34 engine, group runner, scene runner, parity fixture, or armed CLI path touched.
- [x] **Gate 3** - local lint/type/build verification completed.
- [x] **Gate 4** - N/A: no touched Python source for vulture/dead-code purge.
- [x] **Gate 5** - docs updated: `README.md`, `docs/STATUS.md`, and the linked plan/PR body reflect the change.
- [x] **Gate 6** - type-system hygiene preserved with explicit TypeScript interfaces and `unknown` parsers; no `Any` escape hatch introduced.
- [x] **Gate 7** - N/A: no Python hot path, state transition, MIDI send, or guardrail decision added.
- [x] **Gate 8** - tests are behavior-focused and stay in the existing cockpit test file.
- [x] **Gate 9** - module organization unchanged; no new top-level module or package.
- [x] **Gate 10** - N/A: no Python mode/intensity/page string-dispatch site added.
- [x] **Gate 11** - no duplicated shared Python fixtures introduced.
- [x] **Gate 12** - N/A: no Python module-level constants added.
- [x] **Gate 13** - N/A: no environment variable added or read.
- [x] **Gate 14** - maintainability bounded to the existing Performance Console local persistence surface; no new architecture layer.
- [x] **Gate 15** - N/A: no new reusable agent-learning rule or skill required for this frontend package wrapper.
- [x] **Gate 16** - execution shape is one bundled branch/PR against `modularize-v1.34`, not a stacked PR cascade.
- [x] **Gate 17** - abstraction reuse: builds on the existing local rehearsal snapshot, passive Performance Console packet, and current CSS/test surfaces instead of introducing a parallel persistence system.
- [x] **Gate 18** - N/A: no new architecture surface, subpackage, protocol, registry, architecture test, CLI surface, or dependency-direction rule.

## Strict rules - non-negotiables

Per [`CONTRIBUTING.md` section Strict rules](../../CONTRIBUTING.md#strict-rules--non-negotiables) - confirm each:

- [x] **No hardware in tests** - no test opens a real MIDI port; no test mutates a connected device.
- [x] **Lazy MIDI imports** - no Python MIDI import path touched.
- [x] **Hardware-pinned packages** - `mido==1.3.3` and `python-rtmidi==1.5.8` not bumped.
- [x] **Passive default** - no passive CLI or armed runtime behavior changed.
- [x] **No stacked PRs** - this PR's base is `modularize-v1.34`, not another open PR's head.
- [x] **No `--no-verify`** - pre-commit hooks were not bypassed.

## Plan document

Plan doc: `docs/superpowers/plans/2026-06-14-cockpit-rehearsal-package-bundle.md`

## Reviewer notes

This is intentionally frontend-local only. The package import/export buttons do
not dispatch WebSocket commands, do not call Tauri/sidecar APIs, do not write
project files, do not open MIDI ports, do not arm hardware, do not execute a
queued command, do not mutate snapshots on hardware, and do not send MIDI.
