# Cockpit Demo Style Crate Catalog

> Status: in-flight

## Why

The passive Performance Console can now render Style Crates, but the bundled
demo/fallback packet still carried a small one-card style queue that drifted
from the real default rehearsal deck. Installed or mock-only Cockpit sessions
should show the same crate catalog operators will rehearse against: Dark
Hypnotic, Peak Time, Hard Groove, Dub Pressure, Industrial/Broken, Deep
Minimal, Chaos Fills, Transitions, Saved Accidents, staged queue moves, and
journal seeds.

## Scope

- Replace the hand-authored one-card demo style queue with
  `DEFAULT_STYLE_CRATE_REHEARSAL_DECK`.
- Keep the demo model passive and read-only.
- Normalize crate and queued-move `data-testid` values in the renderer so
  underscore-based packet keys remain stable in UI tests.
- Update focused Cockpit component coverage to assert the full nine-card crate
  catalog, staged move labels, journal labels, disabled stage controls, and
  dry-run-only boundaries.
- Do not change WebSocket payloads, report schemas, sidecar commands, queue
  dispatch, MIDI ports, hardware arming, or MIDI sends.

## Test Plan

- RED: update `PerformanceConsole.test.tsx` to require nine crate cards from
  the default deck and stable ids such as `style-crate-dark-hypnotic`.
- GREEN: reuse `DEFAULT_STYLE_CRATE_REHEARSAL_DECK` in the demo model and add
  renderer-local id normalization for crates and queued moves.
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
- Gate 8 - component tests cover the passive no-hardware UI behavior.
- Gate 9 - no new package modules or top-level source files.
- Gate 10 - no Python dispatch strings changed.
- Gate 11 - no fixture duplication.
- Gate 12 - no new Python constants.
- Gate 13 - no new environment variables.
- Gate 14 - maintainability improves by reusing the shared default crate deck
  instead of duplicating stale demo metadata.
- Gate 15 - N/A: focused UI/demo-data follow-up; no new reusable skill.
- Gate 16 - one clean worktree/branch, no stacked PR.
- Gate 17 - reuses existing TypeScript contracts, Style Crates deck constants,
  and component render paths; no new abstraction.
- Gate 18 - N/A: no architecture surface, subpackage, protocol, registry, CLI
  command, or dependency-direction rule changed.
