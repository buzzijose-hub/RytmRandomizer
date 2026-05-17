# Snapshot Essence Hardware Send Design

## Context

The snapshot essence path can now read a saved Analog Rytm kit/project slot,
choose a 12-pad style/genre engine layout, turn that into an ordered CC send
plan, and prove the full plan through a mock-only guarded dry-run. The next
milestone is the first real-MIDI path for that plan, still guarded by app-level
`--arm` and an exact operator confirmation.

## Goal

Add a guarded Rytm-only hardware sender for `SnapshotEssenceSendPlan` and expose
it through `rytm_randomizer.app`. This lets a performer use a saved Rytm
snapshot plus a style prompt, select the Rytm MIDI output, type `SEND`, and
transmit the planned CC events to all 12 pads.

## Chosen Approach

Use the app entry point for active behavior and keep the passive CLI read-only.
The app already owns active smoke tests, real MIDI provider construction, port
selection, and confirmation prompts, so the new path should follow the existing
dual-machine hardware sender pattern.

The hardware sender module will not open ports or import a MIDI backend at
module import time. It accepts an already-open output port and a ready
`SnapshotEssenceSendPlan`, checks guard conditions, then emits eligible CC
events through `midi_io.send_cc`.

## Scope

In scope:

- `--snapshot-essence-send` app modifier.
- Required args: `--snapshot-path`, `--snapshot-slot`, `--snapshot-depth`, and
  `--snapshot-style`.
- Optional arg: `--snapshot-discovery`.
- `--dry-run` path using the existing snapshot essence guarded mock sender.
- `--arm` path using the new hardware sender, selected Rytm port, and exact
  `SEND` confirmation.
- Fake-port tests proving real MIDI message construction without hardware.

Out of scope:

- Analog Four snapshot essence hardware sending.
- Sending both machines in one snapshot essence command.
- Continuous live SysEx receive or hand-knob tracking.
- Writing SysEx back to hardware.
- GUI controls.

## App Shape

```text
python -m rytm_randomizer.app --dry-run --snapshot-essence-send --snapshot-path <path> --snapshot-slot <1-128> --snapshot-depth <micro|groove|strong> --snapshot-style <text> [--snapshot-discovery <0..1>]
python -m rytm_randomizer.app --arm --snapshot-essence-send --snapshot-path <path> --snapshot-slot <1-128> --snapshot-depth <micro|groove|strong> --snapshot-style <text> [--snapshot-discovery <0..1>]
```

## Safety Rules

- `--snapshot-essence-send` requires either `--dry-run` or `--arm`.
- It cannot be combined with smoke tests or `--dual-machine-snapshot-send`.
- `--arm` builds and validates the plan before listing/opening MIDI ports.
- `--arm` requires a selected Analog Rytm output port.
- `--arm` requires exact operator confirmation: `SEND`.
- Blocked or partially ineligible plans emit no MIDI messages.
- The passive CLI remains free of active sender construction and port opening.

## Acceptance

- Hardware sender import is silent and does not import `mido`, `rtmidi`, or
  `librosa`.
- Missing arming, missing confirmation, blocked plans, and ineligible events
  emit zero messages.
- A ready fake-port plan emits exactly `plan.eligible_event_count` CC messages.
- App `--dry-run --snapshot-essence-send` prints the guarded mock report and
  opens no port.
- App `--arm --snapshot-essence-send` sends only after port selection and exact
  `SEND` confirmation.
- Focused sender/app tests and the full suite pass.
