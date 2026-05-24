# Cockpit SEND Plan Readiness

## Goal

Add a passive, deterministic preflight object between a previewed cockpit mutation candidate and the SEND action. SEND must only apply an already-prepared ready plan, so the GUI and sidecar share the same readiness state before any live hardware path is allowed to fire.

## Scope

- Add inert `CockpitSendPlan` / `SendPlanPacket` data models with JSON-safe round-trips and MIDI bounds validation.
- Add a pure `prepare_send_plan(...)` builder that converts candidate deltas into deterministic packet rows, excludes locked pads, and reports readiness blockers.
- Extend the WebSocket protocol with `prepare_send_plan` and `send_plan_changed`.
- Store the active plan in `CockpitSession`, clear stale plans after candidate/lock changes, and require a ready plan for SEND.
- Add `apply_send_plan(...)` to mock and real cockpit device adapters; the real adapter consumes packet CC/channel/value values from the plan instead of recomputing them.
- Extend the desktop protocol, Zustand store, and ActionBar so the operator prepares a plan first and SEND stays disabled until the sidecar confirms readiness.
- Keep all tests passive/mock-safe: no MIDI ports opened, no hardware sends.

## Verification

- Focused backend cockpit tests cover data, engine, mock/real adapters, protocol, handlers, and SEND integration.
- Focused frontend tests cover the protocol guard, state binding/selectors, and ActionBar PREPARE/SEND gating.
- Full closeout should run Python focused/full gates, architecture checks, frontend typecheck/lint/test/build, and coverage before PR.
