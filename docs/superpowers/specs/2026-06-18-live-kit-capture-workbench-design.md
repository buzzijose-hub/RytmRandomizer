# Live Kit Capture Workbench Design

## Purpose

The Live Kit Capture panel now explains the core workflow: receive the kit that
is actually loaded on the Analog Rytm, mutate from that exact anchor, and
recover back to it. The next Cockpit step is a passive workbench that makes the
workflow reviewable as an operator package before any GUI-side hardware bridge
exists.

This is the differentiator against fixed controller products. A controller can
turn knobs, but RytmRandomizer can understand the current kit, preserve a
captured anchor, stage a variation from that anchor, and show the recovery path
before the performer sends anything.

## Scope

This slice adds a passive `live_kit_capture_workbench` object to the existing
`live-gui-performance-console-report` packet and renders it in the Performance
Console. It remains mock-safe and review-only.

In scope:

- Capture slots for current live kit, candidate variation, recovery anchor, and
  resnapshot target.
- Anchor verification evidence for kit identity, fingerprint, pad context,
  lane policy, and recovery command availability.
- Mutation readiness gates that show what is ready, what remains operator-only,
  and what Cockpit must not execute.
- Recovery gates for `home`/`send`, `Z`/`send`, reload saved kit, and
  resnapshot-before-next-run.
- A package manifest shape for future export/import review, including replay
  commands and disabled active controls.
- A passive UI section with disabled action buttons.

Out of scope:

- Receiving SysEx in Cockpit.
- Opening MIDI input or output ports.
- Dispatching WebSocket commands from the workbench.
- Mutating or sending a captured kit from the GUI.
- Changing the armed snapshot shell.
- Changing V1.34 parity fixtures.

## Data Shape

`live_kit_capture_workbench` carries:

- Version, id, status, title, summary, and `source_panel_id`.
- `capture_slots`: ordered cards for current anchor, staged candidate,
  recovery anchor, and resnapshot target.
- `anchor_verification`: fingerprint/source evidence plus deterministic checks.
- `mutation_readiness`: readiness status plus gates for capture, review,
  mutation staging, manual fire, recovery, and resnapshot.
- `recovery_gates`: explicit operator sequences and expected results.
- `package_manifest`: a future-portable bundle summary with includes,
  replay commands, disabled controls, and blocked active actions.
- `blocked_actions`, `safety_lines`, and `replay_commands`.

## UI Shape

The Performance Console renders a `Live Kit Capture Workbench` section near the
existing Live Kit Capture panel. It shows:

- Capture slot cards.
- Anchor verification checks.
- Mutation readiness gates.
- Recovery gates.
- Package manifest metadata.
- Disabled controls for Receive Kit, Stage Mutation, Apply Package, Export
  Package, and Send Captured Plan.

## Safety

The workbench is declarative metadata. The only active path remains the
operator-present armed shell:

`python -m rytm_randomizer.app --arm --rytm-live-snapshot-shell --confirm-rytm-snapshot-shell-send`

All GUI actions that imply SysEx receive, mutation execution, package apply,
hardware arming, port opening, or MIDI send remain blocked.
