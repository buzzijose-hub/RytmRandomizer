# Summary

Adds passive operator-readiness details to the Cockpit Performance Console so
macro cards and style-queue moves show their recovery path, dry-run-only state,
target pads, and blocked hardware boundary directly in the card body.

## What changed

- Macro action cards now render compact passive labels for:
  - `recover <action>`
  - `hardware <state>`
  - `dry-run only`
- Style queue cards now render target pads, operator action, recovery action,
  and dry-run-only status.
- Focused component coverage requires those labels while confirming prepare/send
  controls remain disabled.
- Status and plan docs record the follow-up.

## Why this matters

This moves the cinematic/OXI-style Cockpit closer to live usability without
changing any active behavior. An operator can see what a staged macro or queued
move would affect, how to recover, and why Cockpit still cannot send hardware
from those passive cards.

## Test plan

```bash
cd desktop/web
npm.cmd ci
npm.cmd run test:run -- tests/cockpit/PerformanceConsole.test.tsx
npm.cmd run test:run
npm.cmd run typecheck
npm.cmd run lint
npm.cmd run build
cd ..\..
python -m pytest tests\architecture\test_plan_doc_status_truth.py tests\architecture\test_plan_requirements_referenced.py -q -n 0
python -m pytest tests\architecture\ -q
python -m pytest
python -m ruff check .
python -m black --check --target-version=py311 .
python -m isort --profile black --check-only .
python -m vulture rytm_randomizer tests --min-confidence 80
git diff --check
```

- [x] Focused component test passes.
- [x] Full desktop Vitest passes: 39 files, 393 tests.
- [x] Desktop typecheck, lint, and build pass.
- [x] Architecture suite passes: 607 passed, 1 existing warn-only duplicate
  `main` warning.
- [x] Full Python suite passes: 5694 passed, 3 skipped, 7 warnings.
- [x] Lint trio clean.
- [x] Vulture clean.
- [x] Diff hygiene clean.
- [ ] CI matrix green on all required jobs.

## Plan-requirements conformance

Per `docs/PLAN_REQUIREMENTS.md`:

- [ ] **Gate 1** - N/A: frontend-only TypeScript/docs change; no Python
  touched-file branch coverage.
- [x] **Gate 2** - V1.34 parity unaffected; no parity fixtures touched.
- [x] **Gate 3** - lint/typecheck/format checks pass locally.
- [x] **Gate 4** - dead-code sweep clean.
- [x] **Gate 5** - docs updated: `docs/STATUS.md` and plan doc.
- [x] **Gate 6** - no `Any` escape hatches or Python type loosening.
- [ ] **Gate 7** - N/A: no state-transition/send/guardrail decision path.
- [x] **Gate 8** - focused component test covers the passive UI behavior.
- [x] **Gate 9** - no new package modules or top-level source files.
- [x] **Gate 10** - no Python dispatch strings changed.
- [x] **Gate 11** - no fixture duplication.
- [x] **Gate 12** - no new Python constants.
- [x] **Gate 13** - no new environment variables.
- [x] **Gate 14** - improves maintainability by rendering existing packet
  fields where operators need them.
- [ ] **Gate 15** - N/A: focused UI rendering follow-up, no reusable skill.
- [x] **Gate 16** - one clean branch/PR; no stacked PR.
- [x] **Gate 17** - reuses existing TypeScript contract fields and component
  render paths; no new abstraction.
- [ ] **Gate 18** - N/A: no architecture surface or diagram count changed.

## Strict rules - non-negotiables

- [x] **No hardware in tests** - no test opens a real MIDI port or mutates a
  device.
- [x] **Lazy MIDI imports** - unchanged.
- [x] **Hardware-pinned packages** - unchanged.
- [x] **Passive default** - unchanged.
- [x] **No stacked PRs** - base is `modularize-v1.34`.
- [x] **No `--no-verify`** - pre-push hook will run on push.

## Plan document

`docs/superpowers/plans/2026-06-13-cockpit-performance-action-readiness.md`

## Reviewer notes

Vitest still prints the repo's existing jsdom navigation/canvas/provider noise
while exiting successfully. No WebSocket payload, sidecar command, report schema,
MIDI, or armed hardware path changes are included.
