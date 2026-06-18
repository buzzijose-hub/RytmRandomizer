# Live Kit Capture Cockpit Design

## Purpose

RytmRandomizer's central advantage over a generic encoder controller is live
SysEx kit capture. The operator can receive the kit that is loaded on the
Analog Rytm in the moment, understand its current pad engines and values, stage
musical mutations from that exact anchor, and recover back to the captured kit.
The Cockpit should make that advantage visible before any hardware bridge is
promoted into the GUI.

## Product Position

The phrase to surface is: "Mutate the kit you are actually playing." The
Cockpit should show this as a workflow, not as a marketing hero. The operator
needs to see the capture command, the kit-aware mutation path, the recovery
commands, the safety boundary, and how this differs from a controller that only
maps knobs to fixed CCs.

## Scope

This slice is passive only. It adds a GUI-ready `live_kit_capture_panel` to the
existing `live-gui-performance-console-report` packet and renders it in the
desktop Performance Console. It does not receive SysEx, open MIDI ports, arm
hardware, send MIDI, dispatch WebSocket commands, launch a sidecar command, or
change the armed snapshot shell.

## Data Shape

The panel carries:

- Version, id, status, title, tagline, and source report.
- Armed snapshot shell launch command for operator review.
- Workflow steps: receive kit, review compatibility, randomize, send/go,
  recover, and resnapshot.
- Differentiators against fixed controller mapping: live kit capture,
  engine-aware mutation, captured-anchor recovery, 12-pad Rytm context, and
  OXI/controller complement.
- Active controls represented as blocked actions.
- Safety lines and replay commands.

## UI Shape

The Performance Console renders a dedicated `Live Kit Capture` panel near the
Rytm lane policy and rehearsal/controller sections. The panel shows the tagline,
launch command, workflow cards, differentiator cards, blocked-action chips, and
disabled controls for Receive Kit, Mutate Captured Kit, and Send Captured Plan.

## Safety

All controls remain disabled. The panel is a declarative review surface only.
Actual operator-present hardware use remains in:

`python -m rytm_randomizer.app --arm --rytm-live-snapshot-shell --confirm-rytm-snapshot-shell-send`

Recovery stays anchored to `home`/`send` and `Z`/`send`.
