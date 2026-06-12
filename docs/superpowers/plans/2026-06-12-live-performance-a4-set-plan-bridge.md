# Live Performance A4 Set Plan Bridge Implementation Plan

> Status: in-flight

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Bridge the newly merged passive Analog Four OXI macro set planner into the existing live GUI performance flow so the main Cockpit readiness surface shows the A4 macro queue beside the Rytm/OXI flow.

**Architecture:** Extend `reports/live_gui_performance_flow_model.py` in place. Reuse `reports/analog_four_oxi_macro_set_planner.py` as the source of truth for the A4 set-plan summary. Mirror the new TypedDict in `desktop/web/src/types/live_gui_protocol.ts` and render it in `desktop/web/src/cockpit/LiveReadinessPanel.tsx`.

**Safety:** Passive metadata only. No GUI launch, no port opening, no MIDI send, no hardware mutation, no unattended A4 behavior, no A4 full macro SEND path.

---

## File Structure

- Modify `rytm_randomizer/reports/live_gui_performance_flow_model.py`
  - Add `LiveGuiAnalogFourSetPlan`.
  - Populate it from `build_analog_four_oxi_macro_set_planner_report()`.
  - Emit JSON/text beside existing A4 readiness.
- Modify `desktop/web/src/types/live_gui_protocol.ts`
  - Add the TypeScript mirror for the new Python TypedDict.
- Modify `desktop/web/src/cockpit/LiveReadinessPanel.tsx`
  - Add the default A4 set-plan model values.
  - Render an `A4 Set Plan` card in the passive performance flow.
- Modify tests:
  - `tests/test_live_gui_performance_flow_model.py`
  - `desktop/web/tests/cockpit/LiveReadinessPanel.test.tsx`
  - existing architecture guards for TS/Python mirror and frontend/Python value parity.

## Task 1: Red Tests For A4 Set Plan In Live Flow

- [x] Add backend expectations for `analog_four_set_plan` in model, payload, text, and CLI JSON.
- [x] Add frontend expectation that `LiveReadinessPanel` renders the A4 set plan and replay command.
- [x] Verify red on focused backend/UI tests.

## Task 2: Backend Contract

- [x] Add frozen `LiveGuiAnalogFourSetPlan` + sibling TypedDict.
- [x] Build the default summary from the passive A4 set-planner report rather than duplicating macro facts.
- [x] Include the A4 set-planner replay command in the live-flow replay list.
- [x] Emit deterministic JSON and operator-readable text.

## Task 3: Frontend Contract

- [x] Mirror the Python TypedDict in `live_gui_protocol.ts`.
- [x] Update the Cockpit default live performance flow model with the set-plan summary.
- [x] Render the passive A4 Set Plan card with blocked-action chips.

## Task 4: Verification

- [x] `python -m pytest tests\test_live_gui_performance_flow_model.py -n 0`
- [x] `python -m pytest tests\architecture\test_live_gui_protocol_ts_matches_python_typeddicts.py tests\architecture\test_live_gui_performance_flow_values_match_frontend.py -n 0`
- [x] `npm.cmd ci`
- [x] `npm.cmd run test:run -- tests/cockpit/LiveReadinessPanel.test.tsx`
- [x] `npm.cmd run typecheck`

## Self-Review

- Keeps A4 full macro SEND blocked.
- Reuses existing passive report data instead of creating a second A4 set-plan source.
- Extends an existing live-GUI contract, no new top-level package or command.
- The frontend default is pinned to Python values by the existing architecture guard.
