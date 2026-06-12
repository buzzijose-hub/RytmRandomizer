> Status: in-flight

# Cockpit Performance Console WS Store Bridge

## Goal

Carry the passive Cockpit performance console packet through the existing
WebSocket/store path so `#/performance-console` can render a real sidecar event
when one is available, while keeping the bundled demo packet as the offline
fallback.

## Architecture

The Python cockpit WebSocket protocol gains a passive
`performance_console_changed` event whose payload is the existing
`live_gui_performance_console_model_payload()` dict. Initial WebSocket
bootstrap emits this event after the already-established session/snapshot/profile
/history events. The TypeScript protocol, Cockpit store, and App route then
store and render this live packet before falling back to the static demo model.

## Safety

This is a passive metadata bridge. It does not open MIDI ports, arm hardware,
send MIDI, dispatch command queues, run the profile analyzer, or alter the
Rytm/A4/OXI behavior paths. The underlying performance-console report already
marks active actions as blocked.

## Files

- Modify `rytm_randomizer/cockpit/ws/protocol.py`: add event constant,
  TypedDict, event set, and export.
- Modify `rytm_randomizer/cockpit/ws/handlers.py`: build and emit the passive
  console event during initial WS bootstrap.
- Modify `tests/cockpit/test_ws_protocol.py`: assert protocol constant, event
  count, and payload shape.
- Modify `tests/cockpit/test_ws_handlers.py`: assert initial events include the
  console packet and passive blocked actions.
- Modify `desktop/web/src/ws/protocol.ts`: add event type and type guard entry.
- Modify `desktop/web/src/state/store.ts`: add `performanceConsole` slice and
  setter.
- Modify `desktop/web/src/state/index.ts`: bind
  `performance_console_changed` into the store.
- Modify `desktop/web/src/App.tsx`: prefer injected model, then store event,
  then demo fallback.
- Modify `desktop/web/tests/store.test.ts`, `desktop/web/tests/ws-client.test.ts`,
  and `desktop/web/tests/router.test.tsx`: TDD coverage.
- Update `docs/STATUS.md`.

## TDD Steps

1. Write failing Python protocol tests for `performance_console_changed`.
2. Run those tests and verify they fail because the event is unknown.
3. Add the Python protocol constant/TypedDict/export.
4. Run protocol tests and verify they pass.
5. Write failing WS handler test proving initial bootstrap emits the passive
   console packet.
6. Implement the handler event builder and bootstrap emission.
7. Write failing TypeScript protocol/store/router tests for event recognition,
   store binding, and route preference.
8. Implement the TypeScript protocol/store/App changes.
9. Run focused frontend and Python tests, then full verification.

## Verification

- `python -m pytest tests/cockpit/test_ws_protocol.py tests/cockpit/test_ws_handlers.py -q -n 0`
- `npm.cmd run test:run -- tests/ws-client.test.ts tests/store.test.ts tests/router.test.tsx tests/cockpit/PerformanceConsole.test.tsx`
- `npm.cmd run typecheck`
- `npm.cmd run lint`
- `npm.cmd run test:run`
- `npm.cmd run build`
- `python -m pytest tests/architecture/ -q`
- `python -m pytest`
- `python -m ruff check .`
- `python -m black --check --target-version=py311 .`
- `python -m isort --profile black --check-only .`
- `git diff --check`
