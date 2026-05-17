# Analog Four Snapshot Mock Runtime Design

## Goal

Add a passive Analog Four snapshot mock-runtime report that converts saved-kit
snapshot mutation plans into inert mock events. This proves the live-snapshot
shape for the Analog Four without claiming the saved offsets are sendable CCs.

## Approach

Create `rytm_randomizer/analog_four_snapshot_mock_runtime.py` beside the
existing Analog Four snapshot planner. It will reuse
`analog_four_snapshot_mutation_planner` as its only data source, then capture
each planned saved-offset change into `MockMidiSender` with a non-CC message
type.

The mock event will store the track, wire channel, saved offset, word index,
baseline value, planned value, delta, mapping status, and source. Reports must
say `candidate_unverified`, `saved-offset candidate`, `no CC mapping claimed`,
`mock sender only`, and `no MIDI sending`.

## CLI

Add:

```powershell
python -m rytm_randomizer.cli analog-four-snapshot-mock-runtime-report <path> --slot <1-128> --depth <micro|groove|strong>
```

This command reads an existing saved Analog Four SysEx kit/project dump, selects
one kit slot, builds the passive snapshot mutation plan, and prints the mock
event stream. It does not open MIDI ports, receive live SysEx, write SysEx, or
touch hardware.

## Boundaries

- This slice is passive/read-only.
- It does not add real Analog Four MIDI sending.
- It does not claim any candidate saved offset is a MIDI CC.
- It keeps the current dual-machine bridge unchanged; bridge integration is the
  next slice after this report is verified.

## Success Criteria

- Importing the new module is silent and does not import `mido` or `rtmidi`.
- Synthetic A4 saved values produce deterministic inert mock events.
- The CLI report works against saved SysEx without hardware.
- Existing passive architecture checks remain green.
