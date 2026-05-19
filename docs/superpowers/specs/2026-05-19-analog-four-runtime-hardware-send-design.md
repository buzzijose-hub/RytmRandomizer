# Analog Four Runtime Hardware Send Design

Date: 2026-05-19

## Goal

Add the first A4-only armed runtime sender in software. The sender should take
the already validated A4 Track 1-4 runtime plan, require an explicit `--arm`
mode and exact `SEND` confirmation, open only the selected Analog Four MIDI
output, and send only the mapped CC events that already pass through the
guarded mock dry-run.

This is a software readiness slice. It can be verified with fake MIDI ports in
tests. Real hardware testing remains a separate operator step.

## Current State

The A4 path now has these layers:

- `analog-four-reference-report` records manual-backed A4 reference metadata.
- `analog-four-runtime-report [--profile <profile>]` previews Track 1-4 mapped
  CC runtime events.
- `analog-four-runtime-guarded-send-dry-run [--profile <profile>]` executes the
  same events into `MockMidiSender` only.
- `rytm-randomizer --dry-run --analog-four-runtime --analog-four-profile <profile>`
  exposes the A4-only guarded dry-run from the app.
- `--arm --analog-four-runtime` is currently blocked before port listing.

## Recommended Approach

Add `rytm_randomizer/analog_four/hardware_runtime_sender.py` as the active
counterpart to `analog_four/guarded_runtime_sender.py`.

The module should:

1. Accept an `AnalogFourRuntimePlan` and an already-open output port.
2. Refuse unless `armed=True` and `operator_confirmed=True`.
3. Send the plan's mapped CC events in deterministic Track 1-4 order.
4. Use `midi_io.send_cc` so real `mido` access stays lazy and centralized.
5. Return a deterministic result object and report.
6. Import no real MIDI backend at module import time.

The app should then allow:

```powershell
rytm-randomizer --arm --analog-four-runtime --analog-four-profile birmingham-dark
```

The operator flow should be:

1. Build the A4 runtime plan from the selected profile.
2. List MIDI outputs.
3. Ask the user to choose the Analog Four output.
4. Ask for exact `SEND` confirmation with the profile and message count shown.
5. Open the selected port only after confirmation.
6. Send the A4 runtime CC messages.
7. Close the port best-effort.

## Safety Contract

The armed path must:

- touch only Analog Four runtime events
- send only mapped CC messages from `AnalogFourRuntimePlan`
- require `--arm`
- require exact `SEND`
- open one selected A4 output only
- not open a Rytm output
- not send Rytm MIDI
- not do SysEx receive/write
- not do NRPN or CV mutation
- not run dual-machine sends
- not start the interactive Rytm shell
- emit no partial messages when confirmation is missing or the plan is invalid

## Testing

Add tests before implementation:

- importing `analog_four.hardware_runtime_sender` is silent and does not import
  `mido` or `rtmidi`
- missing arming refuses without sending
- missing operator confirmation refuses without sending
- accepted hardware send emits 20 fake port messages for `balanced`
- `birmingham-dark` sends Track 1 `Track Level CC95 -> 106`
- report includes active safety language and A4-only policy
- app `--arm --analog-four-runtime --analog-four-profile birmingham-dark`
  lists fake ports, chooses the A4 fake port, requires `SEND`, emits 20
  messages, and closes the fake port
- app cancellation before `SEND` does not open the port

## Boundaries

Do not add:

- dual-machine runtime integration
- Rytm sends
- audio analysis
- GUI behavior
- A4 SysEx snapshot receive/decode
- continuous knob tracking
- NRPN sends
- CV track mutation
- style-to-profile auto-selection beyond the existing explicit profile flag

## Next Slice After This

After this software path is green and pushed, the next useful step is a real
hardware checklist for Jose to run with the A4 on. If that validates, connect
the A4-only runtime path into the dual-machine coordination layer.
