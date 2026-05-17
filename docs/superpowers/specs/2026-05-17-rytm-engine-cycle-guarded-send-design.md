# Rytm Engine Cycle Guarded Send Design

## Goal

Make the 12-pad Rytm engine-cycle planner executable through the same safety ladder as the rest of the app: passive plan first, guarded mock dry-run second, and armed hardware send only after explicit confirmation.

## Scope

This slice sends only Analog Rytm machine-select CC15 messages chosen by `rytm_engine_cycle_plan`. It does not send anchors, mutate parameters, read live SysEx, write SysEx, or touch the Analog Four. Existing snapshot essence and dual-machine send paths remain unchanged.

## Approach

Add a mock-only guarded sender that accepts a `RytmEngineCyclePlan`, requires arming plus dry-run confirmation, then emits one CC15 mock message per planned pad. Add an active hardware sender with the same readiness checks, but it sends through an injected already-open MIDI output only after `--arm`, selected port, and exact `SEND` confirmation.

The app gains `--rytm-engine-cycle` as a mutually exclusive active-mode modifier. It uses `--engine-cycle-style <text>` and optional `--engine-cycle-discovery <0..1>`. `--dry-run` prints a guarded dry-run report. `--arm` selects the Analog Rytm port, asks for `SEND`, then transmits the 12 CC15 engine selections.

## Safety Rules

- No module import may import `mido`, `rtmidi`, or open ports.
- `--rytm-engine-cycle` requires `--dry-run` or `--arm`.
- Armed mode must build and validate the plan before opening a port.
- Armed mode must require exact `SEND` before sending any CC15 message.
- Plans with unresolved pads emit no partial messages.
- Reports must state whether MIDI was mock-only or real hardware.

## Testing

Tests cover import safety, missing arming, missing confirmation, unresolved-pad refusal, mock message capture, fake-mido hardware emission, app dry-run routing, app arm routing, argument validation, and active-mode conflict handling.
