# Cockpit Performance Console Source Badge

> Status: in-flight

## Why

The Cockpit performance console can render from three passive sources: an
injected preview packet, the live WebSocket/store packet, or the bundled demo
fallback. All three are useful, but installed-app testing can look confusing
when the UI renders a convincing mock-safe console before the live sidecar
packet arrives. Operators need to know which packet they are looking at without
opening developer tools or guessing from the session label.

## Scope

- Add a passive source badge to the performance-console header.
- Keep `PerformanceConsole` usable with a default source label when rendered
  directly in tests or story-style preview code.
- Have `App` derive the label from its existing route precedence:
  injected preview packet first, live WebSocket/store packet second, bundled
  demo fallback last.
- Do not change the report schema, WebSocket protocol, sidecar, MIDI boundary,
  or any armed hardware behavior.

## Test Plan

- RED: extend the focused `PerformanceConsole` test to require the default
  `passive packet` badge.
- RED: extend router tests to require `injected packet`, `live websocket`, and
  `demo fallback` on the relevant route paths.
- GREEN: implement the badge and route-derived label.
- Verify focused Vitest, TypeScript, lint, build, architecture tests, Python
  tests, and diff hygiene before opening a PR.

## Plan-Requirements Conformance

- Gate 1 - N/A: frontend-only TypeScript/CSS/docs change; no Python touched-file
  branch coverage.
- Gate 2 - V1.34 parity remains byte-identical; no parity fixtures touched.
- Gate 3 - frontend lint/typecheck plus Python lint trio will run before PR.
- Gate 4 - dead-code sweep via vulture will run before PR.
- Gate 5 - docs/status updated in this branch.
- Gate 6 - no `Any` escape hatches or new Python module boundaries.
- Gate 7 - no state-transition, send, or guardrail decision path changed.
- Gate 8 - tests are intent-named and mirror the touched route/component paths.
- Gate 9 - no new package modules or top-level files under `rytm_randomizer/`.
- Gate 10 - no new Python dispatch strings.
- Gate 11 - no shared fixture duplication.
- Gate 12 - no new Python constants.
- Gate 13 - no new environment variables.
- Gate 14 - maintainability impact is positive: the console explains its packet
  source directly in the UI.
- Gate 15 - N/A: this is a small feature PR, not a multi-plan run.
- Gate 16 - one clean worktree/branch, no stacked PR.
- Gate 17 - reuses the existing `PerformanceConsole` prop seam and App route
  precedence; no new data model or protocol.
- Gate 18 - N/A: no architecture surface, subpackage, protocol, registry, CLI
  command, or dependency-direction rule changed.
