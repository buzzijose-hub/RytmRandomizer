# Summary

Adds a passive source badge to the Cockpit Performance Console so operators can
see whether the screen is rendering an injected preview packet, a live
WebSocket/store packet, or the bundled demo fallback.

## What changed

- Added an optional `packetSource` prop to `PerformanceConsole`, with a default
  `passive packet` label for direct component renders.
- Updated the App performance-console route to derive `injected packet`,
  `live websocket`, or `demo fallback` from the existing route precedence.
- Rendered the source as a third read-only status chip in the console header.
- Added focused component/router coverage and a short plan/status note.

## Why this matters

The installed/local Cockpit can show a valid mock-safe console even before a
live sidecar packet arrives. This badge makes that state obvious during testing
without changing any report schema, WebSocket protocol, sidecar command, MIDI
boundary, or armed hardware path.

## Test plan

```bash
cd desktop/web
npm.cmd ci
npm.cmd run test:run -- tests/router.test.tsx tests/cockpit/PerformanceConsole.test.tsx
npm.cmd run test:run
npm.cmd run typecheck
npm.cmd run lint
npm.cmd run build
cd ..\..
python -m pytest
python -m pytest tests\architecture\ -q
python -m pytest tests\architecture\test_plan_doc_status_truth.py::test_every_plan_declares_its_lifecycle_status -q
python -m ruff check .
python -m black --check --target-version=py311 .
python -m isort --profile black --check-only .
python -m vulture rytm_randomizer tests --min-confidence 80
git diff --check
git diff --cached --check
git push -u origin codex/cockpit-macro-deck-ws-contract
```

- [x] Local pytest passes: 5694 passed, 3 skipped, 7 warnings.
- [x] `tests/architecture/` passes: 607 passed, 1 existing warn-only duplicate
  `main` warning.
- [x] Lint trio clean.
- [x] Coverage stays >=95% pure-branch; no Python source touched.
- [x] 685/685 V1.34 parity items byte-identical via pre-push hook.
- [x] No new dead code: vulture clean at min confidence 80.
- [ ] CI matrix green on all required jobs.

## Plan-requirements conformance

Per `docs/PLAN_REQUIREMENTS.md`:

- [ ] **Gate 1** - N/A: frontend-only TypeScript/CSS/docs change; no Python
  touched-file branch coverage.
- [x] **Gate 2** - V1.34 parity byte-identical; pre-push parity passed.
- [x] **Gate 3** - lint clean.
- [x] **Gate 4** - no new dead code.
- [x] **Gate 5** - docs updated: `docs/STATUS.md` and plan doc.
- [x] **Gate 6** - type-system hygiene; no `Any` escape hatches.
- [ ] **Gate 7** - N/A: no hot-path state transition/send/guardrail decision.
- [x] **Gate 8** - focused component/router tests updated.
- [x] **Gate 9** - no new package modules or top-level source files.
- [x] **Gate 10** - no Python dispatch strings changed.
- [x] **Gate 11** - no fixture duplication.
- [x] **Gate 12** - no new Python constants.
- [x] **Gate 13** - no new environment variables.
- [x] **Gate 14** - maintainability improved by making packet provenance visible.
- [ ] **Gate 15** - N/A: small feature PR, no reusable skill/rule extraction.
- [x] **Gate 16** - one clean branch/PR; no stacked PR.
- [x] **Gate 17** - reuses existing App route precedence and component prop seam.
- [ ] **Gate 18** - N/A: no architecture surface or diagram count changed.

## Strict rules - non-negotiables

- [x] **No hardware in tests** - no test opens a real MIDI port or mutates a
  device.
- [x] **Lazy MIDI imports** - unchanged.
- [x] **Hardware-pinned packages** - unchanged.
- [x] **Passive default** - unchanged.
- [x] **No stacked PRs** - base is `modularize-v1.34`.
- [x] **No `--no-verify`** - pre-push hook ran and passed.

## Plan document

`docs/superpowers/plans/2026-06-12-cockpit-performance-console-source-badge.md`

## Reviewer notes

Vitest still prints the repo's existing jsdom navigation/canvas/context noise,
but exits successfully with 39 files and 393 tests passed.
