# Summary

Turns the passive Cockpit Performance Console into a cinematic live-operator HUD
that matches Jose's current product direction: top safety/port/arm bar, left
device rail, central all-12-pad Rytm snapshot deck, right Style Crates/queue
mutation panel, blocked hardware actions, command queue, safety checklist, and
bottom session strip.

## What changed

- Reshaped `PerformanceConsole.tsx` around explicit HUD regions while reusing
  the existing `LiveGuiPerformanceConsoleModelDict` packet.
- Kept all existing passive section/test IDs alive for lane policy, A4 review,
  rehearsal board, macro actions, Style Crates, analyzer, snapshot history,
  command queue, safety, and blocked actions.
- Added a dense dark cockpit layout in `styles.css` for the topbar, device rail,
  12-pad deck, mutation panel, snapshot history strip, and bottom session bar.
- Extended React tests to cover the new HUD shell, disabled hardware controls,
  all-12-pad deck, mutation panel, and fallback rendering.
- Updated README, status, and plan docs.

## Why this matters

This bridges the recent backend/passive-console work into the interface Jose
actually wants to perform with. It is still mock-safe, but it now looks and
behaves like the future cockpit rather than a long passive report.

## Test plan

```powershell
cd desktop\web
npm.cmd run test:run -- tests/cockpit/PerformanceConsole.test.tsx
npm.cmd run test:run
npm.cmd run test:coverage
npm.cmd run typecheck
npm.cmd run lint -- --ext .ts,.tsx --max-warnings 0 src/cockpit/PerformanceConsole.tsx tests/cockpit/PerformanceConsole.test.tsx
npm.cmd run build
cd ..\..
python -m pytest tests\architecture\ -q
git diff --check
```

- [x] Focused React tests cover the new HUD regions and disabled controls.
- [x] Full web Vitest suite passes.
- [x] Web coverage is 100% statements/branches/functions/lines.
- [x] Web typecheck and targeted ESLint pass.
- [x] Web production build passes.
- [x] Playwright render sanity checked the route at 1672x944 and 390x844;
  both render all 12 pads, and the narrow viewport has no horizontal overflow.
- [x] Architecture gate passes: 607 passed, 1 existing Gate 17 warn-only note.
- [x] Diff whitespace check passes.
- [ ] CI matrix green on all required jobs.

## Plan-requirements conformance

Per `docs/PLAN_REQUIREMENTS.md`:

- [ ] Gate 1 - N/A: no Python package file touched.
- [x] **Gate 2** - V1.34 parity not touched; no parity fixtures changed.
- [x] **Gate 3** - Web lint/typecheck verified locally; Python lint not
  required for this frontend-only change.
- [x] **Gate 4** - No dead code introduced; fallback branches are covered.
- [x] **Gate 5** - Docs updated: README, `docs/STATUS.md`, plan doc, and PR
  body file.
- [x] **Gate 6** - No `Any` escape hatches; the existing typed console model is
  reused.
- [ ] Gate 7 - N/A: passive frontend rendering only; no state transition, send
  path, or guardrail decision changed.
- [x] **Gate 8** - Intent-named React tests cover main and fallback behavior.
- [x] **Gate 9** - No new package modules or top-level source files.
- [x] **Gate 10** - No new mode/intensity/page string-dispatch path.
- [x] **Gate 11** - No duplicate fixtures introduced.
- [ ] Gate 12 - N/A: no new module-level constants added outside existing
  frontend helper constants.
- [x] **Gate 13** - No new environment variables.
- [x] **Gate 14** - Maintains the existing passive console abstraction instead
  of introducing another cockpit model.
- [ ] Gate 15 - N/A: no new reusable agent skill needed for this UI follow-up.
- [x] **Gate 16** - One clean branch/PR based on `modularize-v1.34`; no stacked
  PR.
- [x] **Gate 17** - Reuses the existing Performance Console packet, Style
  Crates deck, lane policy matrix, A4 review surface, and safety/queue models.
- [ ] Gate 18 - N/A: no new architecture boundary or diagram surface; README
  and status explain the user-facing UI surface.

## Strict rules - non-negotiables

- [x] **No hardware in tests** - no test opens a real MIDI port or mutates a
  device.
- [x] **Lazy MIDI imports** - unchanged; frontend route imports no real MIDI
  adapter.
- [x] **Hardware-pinned packages** - unchanged.
- [x] **Passive default** - unchanged; all hardware actions remain disabled.
- [x] **No stacked PRs** - base is `modularize-v1.34`.
- [x] **No `--no-verify`** - normal push path used; hooks are not bypassed.

## Plan document

`docs/superpowers/plans/2026-06-13-cockpit-performance-console-cinematic-hud.md`

## Reviewer notes

This is a passive GUI rendering bundle only. It does not add command dispatch,
unattended playback, WebSocket command dispatch, MIDI port opening, hardware
arm behavior, command execution, MIDI sending, or snapshot mutation.
