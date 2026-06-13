# Cockpit Style Crate Browser

> Status: in-flight

## Why

The passive performance console already receives a Style Crates rehearsal deck,
but the desktop UI only showed the staged queue and journal. The cinematic
Cockpit direction needs the operator to browse crates first, then stage or
inspect queued moves. Rendering the existing crate cards closes that visibility
gap without introducing queue dispatch or hardware behavior.

## Scope

- Render `model.style_queue.crate_cards` inside the Performance Console.
- Show each crate's name, summary, energy/risk, risk status, target pads, tags,
  primary move, and operator action.
- Add disabled stage controls so the UI communicates future intent while
  remaining passive.
- Keep the existing queue and journal display.
- Do not change WebSocket payloads, report schemas, sidecar commands, queue
  dispatch, MIDI ports, or armed hardware paths.

## Test Plan

- RED: extend `PerformanceConsole.test.tsx` to require a visible Dark Hypnotic
  crate card and a disabled stage button.
- GREEN: render crate cards from the existing packet fields.
- Verify focused Vitest, desktop coverage, typecheck, lint, build,
  plan-doc architecture checks, and diff hygiene before PR.

## Plan-Requirements Conformance

- Gate 1 - N/A: frontend-only TypeScript/docs change; no Python touched-file
  branch coverage.
- Gate 2 - V1.34 parity remains byte-identical; no parity fixtures touched.
- Gate 3 - frontend lint/typecheck/format checks run before PR.
- Gate 4 - N/A: no Python symbol surface or dead-code path changed.
- Gate 5 - docs/status updated in this branch.
- Gate 6 - no `Any` escape hatches or Python type loosening.
- Gate 7 - no state-transition, send, or guardrail decision path changed.
- Gate 8 - component test covers the passive no-hardware UI behavior.
- Gate 9 - no new top-level package modules.
- Gate 10 - no Python dispatch strings changed.
- Gate 11 - no fixture duplication.
- Gate 12 - no new Python constants.
- Gate 13 - no new environment variables.
- Gate 14 - maintainability improves by using existing packet fields instead
  of duplicating crate metadata.
- Gate 15 - N/A: focused UI rendering follow-up; no new reusable skill.
- Gate 16 - one clean worktree/branch, no stacked PR.
- Gate 17 - reuses existing TypeScript props, Style Crates deck fields, and
  component render paths; no new abstraction.
- Gate 18 - N/A: no architecture surface, subpackage, protocol, registry, CLI
  command, or dependency-direction rule changed.
