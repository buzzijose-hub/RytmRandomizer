# Live Performance Cockpit Flow Design - 2026-06-04

## Purpose

Turn the merged OXI-style Rytm macro bundle and passive Analog Four macro
runway into one cockpit-facing performance flow. The operator should be able to
see the live story as a sequence: capture the Rytm anchor, stage a named Rytm
macro, review the Analog Four candidate lane, and recover to the captured kit.

This slice is passive GUI work. It does not open MIDI ports, send MIDI, arm
hardware, add an Analog Four outbound path, write SysEx, change V1.34 parity, or
alter the hardware-tested snapshot shell behavior.

## Current Truth

- PR #150 merged the all-12-pad OXI live macro bundle.
- PR #151 added a passive Analog Four OXI macro report.
- PR #152 added the Analog Four cockpit OXI macro strip.
- The cockpit already has 12-pad Rytm readiness, A4 track cards, scene queue,
  snapshot history, safety checklist, command queue, analyzer panel, hardware
  rail, and snapshot compatibility panels.
- What is missing is a single operator-facing flow that shows how Rytm and A4
  are meant to work together during a set.

## Operator Model

The live rig remains:

```text
OXI: notes, triggers, mutes, pattern motion
RytmRandomizer: Rytm sound-design movement over the captured kit
Analog Four: candidate synth/macro direction, review-only for now
```

The cockpit flow should show these phases:

1. `kit/resnapshot` captures the current Rytm kit anchor.
2. `kit-core` stages the baseline all-12-pad safe macro.
3. `hard-groove` stages dry pressure.
4. `industrial` stages metallic texture and grit.
5. `dub-pressure` stages darker space.
6. `transition` stages section movement.
7. `Z + send` / `home` recovers the captured anchor.

Each row should show the Rytm command, the matching A4 review lane, the send
policy, and the recovery action.

## Safety Boundaries

- Rytm rows may describe existing staged/sendable shell commands.
- Analog Four rows remain review-only/candidate-only.
- Hardware actions stay blocked unless an existing armed path is used outside
  this GUI slice.
- The panel must surface blocked actions such as A4 outbound macro send and
  unattended hardware behavior.
- The panel must be deterministic and testable without a running sidecar.

## UI Shape

The first implementation lives inside the existing live readiness panel. It
adds a wide `Performance Flow` surface between the scene queue and the lower
status/safety surfaces. Cards use the existing cockpit compact card language:

- short step number and phase,
- step label,
- Rytm command,
- A4 review action,
- send policy plus recovery action,
- current-step highlight,
- blocked-action chips,
- replay command chips for the passive report producers.

## Done Criteria

- The default cockpit live readiness panel renders the performance-flow surface.
- Tests can inject a smaller flow model and verify Rytm/A4 lane text, recovery,
  send policy, and blocked actions.
- The new UI remains passive: no port, send, arm, or hardware mutation behavior.
- Existing cockpit tests and type checks continue to pass.
