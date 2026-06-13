# Cockpit Performance Action Readiness Details

> Status: in-flight

## Why

The Cockpit performance console now carries passive OXI-style macro cards,
style queue moves, journal entries, 12-pad Rytm state, and Analog Four runway
state. The next operator problem is readability during live prep: the console
shows commands and disabled controls, but macro and queue cards should also make
their recovery path, hardware boundary, and dry-run-only state visible without
requiring the operator to infer those details from longer hints.

## Scope

- Keep the existing passive performance-console packet contract.
- Add visible macro-card details for recovery action, hardware action state, and
  dry-run-only status.
- Add visible style-queue details for target pads, operator action, recovery
  action, and dry-run-only status.
- Keep all prepare/send controls disabled.
- Do not change WebSocket events, report payload fields, sidecar commands, MIDI
  behavior, or any armed hardware path.

## Test Plan

- RED: extend `PerformanceConsole.test.tsx` to require macro-card recovery,
  hardware boundary, and dry-run-only labels.
- RED: extend the same test to require style-queue target pads, operator action,
  recovery action, and dry-run-only labels.
- GREEN: render the existing packet fields in compact passive UI rows.
- Verify focused Vitest, full desktop web tests, typecheck, lint, build,
  Python tests, architecture tests, and lint trio before PR.

## Plan-Requirements Conformance

- Gate 1 - N/A: frontend-only TypeScript/docs change; no Python touched-file
  branch coverage.
- Gate 2 - V1.34 parity remains byte-identical; no parity fixtures touched.
- Gate 3 - frontend lint/typecheck plus Python lint trio run before PR.
- Gate 4 - dead-code sweep runs before PR.
- Gate 5 - docs/status updated in this branch.
- Gate 6 - no `Any` escape hatches or Python type loosening.
- Gate 7 - no state-transition, send, or guardrail decision path changed.
- Gate 8 - component test names the passive no-hardware behavior under review.
- Gate 9 - no new top-level package modules.
- Gate 10 - no Python dispatch strings changed.
- Gate 11 - no fixture duplication.
- Gate 12 - no new Python constants.
- Gate 13 - no new environment variables.
- Gate 14 - maintainability improves because existing packet fields are visible
  where operators need them.
- Gate 15 - N/A: focused UI rendering follow-up; no new reusable skill.
- Gate 16 - one clean worktree/branch, no stacked PR.
- Gate 17 - reuses existing TypeScript props and passive packet fields; no new
  model or protocol.
- Gate 18 - N/A: no architecture surface, subpackage, protocol, registry, CLI
  command, or dependency-direction rule changed.
