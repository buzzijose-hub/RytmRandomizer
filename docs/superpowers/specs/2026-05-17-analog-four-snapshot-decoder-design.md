# Analog Four Kit Snapshot Decoder Design

Date: 2026-05-17

## Goal

Build the first passive Analog Four MKII saved-kit snapshot decoder. This
closes the gap between the current Analog Four safe-starter mock plan and the
future captured-kit mutation flow.

The decoder reads an already-saved Analog Four `.syx` kit bank or whole-project
dump, selects one kit slot, unpacks the Elektron 7-bit payload, and reports a
safe inventory of the kit and four synth-track blocks. It does not send MIDI,
open ports, receive live SysEx, write SysEx, or mutate hardware.

## Current Evidence

The existing passive project analyzer reports Jose's Analog Four whole-project
dump as:

- device family byte `0x06`, Analog Four MKII
- 405 complete SysEx records
- 128 kit records
- kit record length: 2770 bytes
- complete stream with valid SysEx boundaries

Manual passive inspection of the first kit records shows:

- decoded kit payload length: 2414 bytes
- kit name at decoded payload offset `4`
- four visible track-like name blocks around offsets `44`, `394`, `744`, and
  `1094`
- later printable performance macro labels around offset `1944`

Those offsets are enough for a first inventory decoder. They are not enough to
claim saved parameter offset mappings yet.

## Recommended Slice

Implement a new passive module:

```text
rytm_randomizer/analog_four_snapshot_decoder.py
```

It should expose:

- `decode_analog_four_kit_snapshot_file(path, *, slot)`
- `decode_analog_four_kit_snapshot_bytes(data, *, slot)`
- `format_analog_four_kit_snapshot_report(snapshot)`
- `format_analog_four_kit_snapshot_error(path, message)`

Primary data structures:

- `AnalogFourKitSnapshot`
- `AnalogFourTrackSnapshot`

The kit snapshot should include:

- source path when available
- slot number
- kit name
- raw SysEx record length
- decoded payload length
- manufacturer ID
- device family byte
- object type
- kit record hash
- four track snapshots

Each track snapshot should include:

- track number
- MIDI channel
- wire channel
- decoded block offset
- decoded block length
- visible track/sound name
- block hash
- mapping status

For this first slice, mapping status should be explicit:

```text
saved_parameter_offsets_unmapped
```

That text matters. It prevents the report from implying that Analog Four saved
parameter values are mutation-ready before we prove the saved kit layout.

## CLI Contract

Add a passive CLI command:

```powershell
python -m rytm_randomizer.cli analog-four-kit-snapshot-report "G:\ANALOG FOUR\WHOLE PROJECT DUMP\PROJECTANALOGFOUR01.syx" --slot 1
```

The report should include:

- `RytmRandomizer passive Analog Four kit snapshot report`
- kit slot and kit name
- decoded payload length
- four track entries
- per-track block hashes
- mapping status
- safety section

The command exits with:

- `0` for a valid decoded A4 kit snapshot
- `1` for file/decode/slot errors with deterministic stderr
- `2` for usage errors

## Error Handling

Introduce `AnalogFourSnapshotDecodeError` under the project error taxonomy:

```python
class AnalogFourSnapshotDecodeError(DataError, ValueError):
    ...
```

This preserves existing validation-style handling while satisfying the
observability architecture rule that package raises live under
`RytmRandomizerError`.

Expected errors:

- no complete SysEx messages
- slot outside `1-128`
- requested slot not found
- selected record is not an Analog Four kit record
- decoded payload too short for the four observed track blocks

## Testing

Use TDD with synthetic A4 kit SysEx records before implementation.

Focused tests:

- importing the module is silent and does not import `mido` or `rtmidi`
- a synthetic packed A4 kit record decodes kit name and four track names
- invalid slot raises `AnalogFourSnapshotDecodeError`
- non-A4 kit record raises `AnalogFourSnapshotDecodeError`
- CLI report reads a synthetic saved kit without hardware
- CLI help exposes the command and passive safety boundary
- architecture tests accept `AnalogFourSnapshotDecodeError`

Manual verification after implementation:

```powershell
python -m rytm_randomizer.cli analog-four-kit-snapshot-report "G:\ANALOG FOUR\WHOLE PROJECT DUMP\PROJECTANALOGFOUR01.syx" --slot 1
```

## Boundaries

Do not add in this slice:

- Analog Four parameter mutation planning
- Analog Four saved parameter baseline claims
- NRPN sending
- CC sending
- port selection
- live SysEx receive
- SysEx writes
- Analog Four engine cycling
- cross-device armed mode
- GUI behavior

## Next Slice After This

After this decoder is green, the next useful slice is an Analog Four saved
parameter offset mapper. That mapper should use differential evidence from
known kit variations or controlled exports before any A4 captured-value
mutation planner is allowed.
