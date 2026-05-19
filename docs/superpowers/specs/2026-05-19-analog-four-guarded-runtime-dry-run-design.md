# Analog Four Guarded Runtime Dry-Run Design

Date: 2026-05-19

## Goal

Build the first A4-only guarded runtime dry-run path. It should take the
existing passive Analog Four Track 1-4 runtime plan and prove that the planned
mapped CC events can pass through a sender-shaped guard without opening a MIDI
port, sending real MIDI, touching the Rytm, or mutating hardware.

This is the bridge between `analog-four-runtime-report` and a later armed A4
runtime sender.

## Current State

The Analog Four path now has three relevant layers:

- `analog-four-reference-report` records the current A4 MKII OS1.51C manual
  reference and mapped starter CC/NRPN surface.
- `analog-four-runtime-report [--profile <profile>]` turns safe starter
  profiles into an inert 20-message Track 1-4 CC stream.
- The active app has narrow A4 smoke tests for Pan CC10 and one-track
  Filter 1 Frequency CC18, which Jose validated on hardware.

The runtime plan is still passive. It is not yet shaped like a guarded sender,
and the app has no A4 runtime dry-run flag beyond smoke tests.

## Recommended Approach

Add an A4-owned guarded dry-run module that mirrors the safety pattern used by
existing guarded senders, but keeps this slice independent from the
dual-machine bridge.

The module should:

1. Accept an `AnalogFourRuntimePlan`.
2. Classify only mapped CC runtime events as eligible.
3. Require explicit dry-run arming flags inside the API, even though it only
   accepts `MockMidiSender`.
4. Emit eligible events into `MockMidiSender` with guard metadata.
5. Block partial emission when the plan is malformed or not ready.
6. Format a deterministic report with track coverage, profile, emitted mock
   messages, and safety policy.

This keeps the A4 sender pathway testable and reviewable before any real
hardware port is involved.

## CLI Contract

Add a passive CLI report:

```powershell
python -m rytm_randomizer.cli analog-four-runtime-guarded-send-dry-run --profile birmingham-dark
```

Default profile should be `balanced` when `--profile` is omitted.

The report should include:

- device: `Elektron Analog Four MKII`
- starter profile label/key
- accepted flag and guard reason
- plan readiness
- eligible mapped CC message count
- emitted mock message count
- Track 1-4 coverage
- mock emission preview with MIDI channel, wire channel, CC, value, role, and
  parameter
- safety language:
  - passive/read-only
  - A4-only guarded dry-run
  - mock sender only
  - no Rytm MIDI sending
  - no MIDI sending
  - no MIDI receive
  - no port opening
  - no command execution
  - no hardware mutation
  - no live SysEx receive
  - no SysEx writes
  - no hardware required

Unknown profiles should fail safely with return code 1 and an error report
stating that no MIDI was sent.

## App Contract

After the passive CLI dry-run is green, add an app dry-run flag:

```powershell
rytm-randomizer --dry-run --analog-four-runtime --analog-four-profile birmingham-dark
```

The app flag should:

- run only in `--dry-run` for this slice
- reuse the same guarded dry-run module
- print a short operator intro explaining that no hardware or port is opened
- not prompt for Rytm pad/profile selection
- not touch the Rytm
- reject `--arm --analog-four-runtime` until a later approved hardware slice

## Testing

Add tests before implementation:

- importing the new guarded module is silent and does not import `mido` or
  `rtmidi`
- building the guarded result for `balanced` emits 20 mock CC messages
- `birmingham-dark` preserves Track 1 `Track Level CC95 -> 106`
- emitted metadata includes guard name, A4 device label, profile, track, MIDI
  channel, wire channel, role, parameter, `mock_only=True`, and
  `sends_real_midi=False`
- missing arming/dry-run confirmation blocks emission
- CLI report exits zero for a valid profile
- CLI report exits 1 for an unknown profile and says no MIDI was sent
- app `--dry-run --analog-four-runtime` captures 20 mock messages and does not
  enter the interactive Rytm shell
- app rejects `--arm --analog-four-runtime` for now

## Boundaries

Do not add:

- real MIDI sending for A4 runtime
- A4 port selection for this runtime path
- Rytm sends
- dual-machine coupling
- A4 SysEx snapshot receive/decode
- NRPN sending
- CV track mutation
- pitch mutation
- continuous knob tracking
- GUI behavior
- audio analysis

## Next Slice After This

After the A4-only guarded dry-run is green, the next best slice is an explicitly
reviewed armed A4 runtime sender that opens only the selected A4 port and sends
only the same eligible mapped CC events. Once that is proven, connect A4-only
runtime into the dual-machine layer.
