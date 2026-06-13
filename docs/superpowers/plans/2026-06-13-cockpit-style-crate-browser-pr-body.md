# Summary

Adds a passive Style Crates browser to the Cockpit Performance Console. The
console now renders existing crate cards before queued moves and the Mutation
Journal, showing crate summary, energy/risk, target pads, tags, primary move,
operator action, and disabled stage controls.

## What changed

- Rendered `model.style_queue.crate_cards` in `PerformanceConsole`.
- Added compact crate subsection headings for Style Crates, Queued Moves, and
  Mutation Journal.
- Kept crate staging passive with disabled buttons.
- Extended the component test to require the Dark Hypnotic crate card and
  disabled stage affordance.
- Updated status and plan docs.

## Why this matters

This moves the cinematic/OXI-style Cockpit closer to the intended live workflow:
browse a vibe crate, see its target pads and risk/energy, then review queued
moves. Real dispatch still stays outside the passive console.

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
- [x] Desktop coverage gate passes: 100% statements, branches, functions, and
  lines.
- [x] No WebSocket payload, report schema, sidecar command, MIDI, or hardware
  behavior changed.
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

`docs/superpowers/plans/2026-06-13-cockpit-style-crate-browser.md`

## Reviewer notes

This is a passive UI-only follow-up. Style crate staging remains disabled in
the console; no queue dispatch, WebSocket payload, sidecar command, MIDI port,
or hardware send behavior changes are included.
