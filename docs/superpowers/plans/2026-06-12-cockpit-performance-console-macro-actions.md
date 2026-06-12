# Cockpit Performance Console Macro Actions

> Status: in-flight

## Why

PR #165 made the passive Cockpit performance-console packet arrive through the
WebSocket store. The next useful OXI-style step is to make that packet feel like
an operator surface instead of a static report: the console should show which
Rytm live macro can be staged, what shell command it maps to, what recovery
command is attached, which pads it affects, and why active firing remains
blocked in this passive Cockpit model.

## Scope

- Add a deterministic passive `macro_action_deck` to the existing
  `live-gui-performance-console-report` payload.
- Derive the cards from the existing OXI live macro catalog and performance-flow
  reports instead of duplicating macro facts.
- Render the deck in the desktop Performance Console route with disabled
  prepare/send controls.
- Keep the change passive/mock-safe: no sidecar command dispatch, no MIDI port
  opening, no hardware send, no new environment variables, and no parity fixture
  updates.

## Workstream

| Workstream | Files | Notes |
|---|---|---|
| Backend packet | `rytm_randomizer/reports/live_gui_performance_console_model.py`, tests | Compose macro action cards from existing reports. |
| Frontend render | `desktop/web/src/cockpit/PerformanceConsole.tsx`, `desktop/web/src/types/live_gui_protocol.ts`, demo/tests/CSS | Surface cards and disabled operator controls. |
| Docs | `README.md`, `docs/STATUS.md`, this plan | Document passive Cockpit macro action handoff. |

## TDD

1. Add failing Python tests for `macro_action_deck` in the report payload.
2. Add failing React tests for the visible macro action deck and disabled SEND.
3. Implement the smallest backend/frontend changes to satisfy the tests.
4. Run focused Python and frontend suites, then full verification before PR.

## Safety

This bundle only creates and renders passive metadata. It does not call the
armed snapshot shell, does not open MIDI input/output ports, and does not send
MIDI. Hardware action buttons remain disabled with explicit blocked-action
labels.

## Plan-Requirements Conformance

- [x] Gate 1 -- focused tests cover touched branches; full coverage run before PR.
- [x] Gate 2 -- no V1.34 parity fixture regeneration.
- [x] Gate 3 -- ruff, black, isort, TypeScript checks before PR.
- [x] Gate 4 -- vulture run before PR.
- [x] Gate 5 -- README and STATUS updated.
- [x] Gate 6 -- TypedDict/dataclass/TypeScript contracts, no `Any`.
- [x] Gate 7 -- N/A: passive report/UI metadata only; no hot path or state transition.
- [x] Gate 8 -- tests mirror existing source structure.
- [x] Gate 9 -- existing reports and cockpit subpackages only.
- [x] Gate 10 -- no new mode dispatch.
- [x] Gate 11 -- no duplicated shared fixtures.
- [x] Gate 12 -- new module-level constants use `Final`.
- [x] Gate 13 -- no new env vars.
- [x] Gate 14 -- scoped to one existing packet/surface, no new architecture layer.
- [x] Gate 15 -- no new durable learning pattern required.
- [x] Gate 16 -- one clean-base PR, no stacked PRs.
- [x] Gate 17 -- reuses OXI macro catalog, performance-flow model, and passive report formatter.
- [x] Gate 18 -- N/A: no new subpackage, registry, dependency rule, or architecture surface.

## Done Criteria

- `live-gui-performance-console-report --json` includes deterministic macro
  action deck cards for `kit-core`, `hard-groove`, `industrial`, `dub-pressure`,
  `transition`, and `home`.
- The Performance Console renders those cards and shows active macro send as
  blocked.
- Focused Python and frontend tests pass before full closeout.
