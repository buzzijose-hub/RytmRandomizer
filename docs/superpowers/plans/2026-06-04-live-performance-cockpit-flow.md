# Live Performance Cockpit Flow Implementation Plan

> Status: in-flight on branch `codex/live-performance-cockpit-flow-bundle`

**Goal:** Add the first passive cockpit surface that ties the merged Rytm OXI
macro vocabulary and passive Analog Four runway into one visible live
performance flow.

**Architecture:** Keep the change in the existing frontend cockpit layer. Do
not change Python hardware behavior, MIDI send/render paths, A4 outbound paths,
V1.34 parity fixtures, or cross-language protocol models. Use a local typed
view model in `LiveReadinessPanel.tsx` until a backend report needs to emit the
same structure.

## Source Spec

Implement from
`docs/superpowers/specs/2026-06-04-live-performance-cockpit-flow-design.md`.

## Files

- Modify `desktop/web/src/cockpit/LiveReadinessPanel.tsx`
  - Add local `LivePerformanceFlowModel` and step model types.
  - Add deterministic default flow using the merged macro names.
  - Render `LivePerformanceFlow` inside the live readiness grid.
- Modify `desktop/web/src/cockpit/styles.css`
  - Add rail/card styling for the new performance-flow surface.
- Modify `desktop/web/tests/cockpit/LiveReadinessPanel.test.tsx`
  - Add test coverage for injected flow model, Rytm/A4 lanes, recovery, send
    policy, and blocked actions.
- Modify `docs/STATUS.md`
  - Record the cockpit-flow slice.

## Verification

- `npm.cmd run test:run -- tests/cockpit/LiveReadinessPanel.test.tsx`
- `npm.cmd run typecheck`
- `npm.cmd run lint`
- `npm.cmd run build`
- `python -m pytest tests/architecture/ -q`

## Follow-Ups

- Promote the local TS flow model into a Python passive report only when the
  cockpit needs backend-provided flow variants.
- Add A4 active macro behavior only after a separate operator-present hardware
  validation pass approves outbound A4 sends.
