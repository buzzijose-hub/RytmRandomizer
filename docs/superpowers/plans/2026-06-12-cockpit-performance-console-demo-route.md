> Status: in-flight

# Cockpit Performance Console Demo Route

## Intent

Make the newly merged Cockpit performance console route directly usable in the
desktop/local frontend without requiring an external test harness to inject the
model. Visiting `#/performance-console` or `#/console` should render a bundled,
typed, passive demo packet that matches the backend
`LiveGuiPerformanceConsoleModelDict` contract.

This keeps the operator-facing product direction moving toward the cinematic
12-pad Rytm + A4 console while preserving the current safety posture: no MIDI
port opening, no hardware arm path, no outbound MIDI, no queue dispatch, and no
sidecar dependency for the demo surface.

## Scope

- Add a source-owned `performanceConsoleDemoModel` that uses the existing typed
  live GUI protocol.
- Keep test fixtures aligned by reusing the source-owned demo model instead of
  carrying a separate duplicate object in tests.
- Update the App hash router so the performance console route falls back to the
  bundled demo model when no live/injected model is supplied.
- Keep injected models taking priority so Storybook-style hosts/tests can still
  render custom packets.
- Update router tests and docs/status.

## Out Of Scope

- No WebSocket protocol changes.
- No sidecar packet subscription changes.
- No UI redesign beyond making the existing route render a real passive model.
- No Tauri installer changes.
- No MIDI, hardware port, Analog Rytm, Analog Four, OXI, SysEx, or outbound send
  behavior changes.

## TDD Plan

1. Update the router test that currently expects the performance-console route
   to fall back to the connecting placeholder without an injected model.
2. Make it expect the bundled demo model instead, including the passive safety
   state and absence of the connecting placeholder.
3. Run the focused router test and observe failure.
4. Implement the source-owned demo model and App fallback.
5. Re-run focused frontend tests, typecheck, lint, frontend build, architecture,
   and full pytest.

## Verification Plan

- `npm.cmd run test:run -- tests/router.test.tsx tests/cockpit/PerformanceConsole.test.tsx`
- `npm.cmd run typecheck`
- `npm.cmd run lint`
- `npm.cmd run test:run`
- `npm.cmd run build`
- `python -m pytest tests/architecture/ -q`
- `python -m pytest`
- `git diff --check`

## Safety Notes

The bundled model is static frontend data. It exists only to render passive UI
state. It cannot open ports, arm hardware, dispatch queued commands, load
snapshots, or send MIDI.
