# Snapshot Mock Runtime Report Design

Date: 2026-05-17

## Purpose

Add a passive bridge from saved Rytm snapshot mutation plans to inert mock MIDI
messages. This proves the future Live Snapshot send path can be expressed as
concrete CC messages while still opening no ports and touching no hardware.

## Operator Command

```powershell
python -m rytm_randomizer.cli sysex-snapshot-mock-runtime-report <path> --slot <1-128> --depth <micro|groove|strong>
```

The command reads an existing Rytm kit bank or whole-project SysEx file, decodes
one kit slot, builds the existing captured-value mutation plan, captures those
planned CC moves into `MockMidiSender`, and prints a deterministic report.

## Scope

In scope:

- Use saved snapshot values as the baseline.
- Reuse the existing snapshot decoder and mutation planner.
- Convert each planned change to one inert CC message.
- Preserve 1-based MIDI channel metadata and 0-based wire-channel message data.
- Report mock message count and message preview.
- Keep all safety text explicit.

Out of scope:

- Real MIDI output.
- Live SysEx receive.
- SysEx write or restore.
- Continuous knob tracking.
- Machine switching.
- Any change to the validated Safe Anchors runtime.

## Safety Boundary

The feature is passive/read-only. It imports only local snapshot planning and
mock MIDI helpers. It must not import `mido`, `rtmidi`, real MIDI providers,
or active hardware adapters.

## Success Criteria

- Importing the module is silent and does not load MIDI libraries.
- A saved kit snapshot plan captures deterministic mock CC messages.
- The CLI works against saved `.syx` files.
- The report says `mock sender only`, `captured-value relative`, and `no MIDI sending`.
