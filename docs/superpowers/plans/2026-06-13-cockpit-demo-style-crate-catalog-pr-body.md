# Summary

Updates the bundled Cockpit Performance Console demo/fallback packet so the
installed/mock console shows the full default Style Crates rehearsal catalog
instead of a one-card placeholder.

## What changed

- Reused `DEFAULT_STYLE_CRATE_REHEARSAL_DECK` in
  `performanceConsoleDemoModel`.
- Added normalized crate and queued-move UI test ids in `PerformanceConsole`.
- Extended the component test to assert the full nine-card crate catalog,
  staged queue labels, journal labels, disabled stage controls, and
  dry-run-only boundaries.
- Updated status and plan docs.

## Why this matters

This keeps the installed/mock Cockpit experience aligned with the real
Style Crates direction: operators can browse the full crate vocabulary and
staged queue preview even before a live WebSocket packet arrives. Real staging
and hardware sends remain blocked outside the explicitly armed shell.

## Test plan

```bash
cd desktop/web
npm.cmd ci
npm.cmd run test:run -- tests/cockpit/PerformanceConsole.test.tsx
npm.cmd run test:coverage
npm.cmd run typecheck
npm.cmd run lint
npm.cmd run build
cd ..\..
python -m pytest tests\architecture\test_plan_doc_status_truth.py tests\architecture\test_plan_requirements_referenced.py -q -n 0
git diff --check
```

- [x] Focused component test passes.
- [x] Desktop coverage gate passes.
- [x] Desktop typecheck passes.
- [x] Desktop lint passes.
- [x] Desktop build passes.
- [x] Plan/status architecture checks pass.
- [x] Diff hygiene passes.
- [ ] CI matrix green on all required jobs.

## Plan-requirements conformance

Per `docs/PLAN_REQUIREMENTS.md`:

- [ ] **Gate 1** - N/A: frontend-only TypeScript/docs change; no Python
  touched-file branch coverage.
- [x] **Gate 2** - V1.34 parity unaffected; no parity fixtures touched.
- [x] **Gate 3** - frontend lint/typecheck/build verified locally.
- [ ] **Gate 4** - N/A: no Python symbol or dead-code surface changed.
- [x] **Gate 5** - docs updated: `docs/STATUS.md` and plan doc.
- [x] **Gate 6** - no `Any` escape hatches or Python type loosening.
- [ ] **Gate 7** - N/A: no state-transition/send/guardrail decision path.
- [x] **Gate 8** - focused component tests cover passive UI behavior.
- [x] **Gate 9** - no new package modules or top-level source files.
- [x] **Gate 10** - no Python dispatch strings changed.
- [x] **Gate 11** - no fixture duplication.
- [x] **Gate 12** - no new Python constants.
- [x] **Gate 13** - no new environment variables.
- [x] **Gate 14** - improves maintainability by reusing the shared default
  crate deck instead of duplicating demo metadata.
- [ ] **Gate 15** - N/A: focused UI/demo-data follow-up, no reusable skill.
- [x] **Gate 16** - one clean branch/PR; no stacked PR.
- [x] **Gate 17** - reuses existing TypeScript contracts, constants, and
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

`docs/superpowers/plans/2026-06-13-cockpit-demo-style-crate-catalog.md`

## Reviewer notes

This is a passive demo-data/UI follow-up. It does not change WebSocket payloads,
report schemas, sidecar commands, queue dispatch, MIDI ports, hardware arm
paths, or MIDI sends.
