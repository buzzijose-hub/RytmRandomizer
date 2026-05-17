# Analog Four Kit Snapshot Decoder Checkpoint

Date: 2026-05-17

## What This Milestone Proves

The project can now inspect saved Analog Four MKII kit records without touching
hardware. This is the first step toward moving the A4 side from safe-starter
mock planning to captured-kit mutation planning.

## Current Scope

- Reads saved `.syx` files from disk
- Selects Analog Four kit slots `1-128`
- Unpacks Elektron 7-bit payloads
- Reports kit name and four Track 1-4 snapshot blocks
- Reports per-track block hashes
- Marks saved parameter offsets as `saved_parameter_offsets_unmapped`

## Safety Boundary

- passive/read-only
- no MIDI sending
- no MIDI receive
- no port opening
- no hardware mutation
- no live SysEx receive
- no SysEx writes
- no hardware required

## Snapshot Mutation Plan Checkpoint

The first passive Analog Four snapshot mutation planner now exists:

```powershell
python -m rytm_randomizer.cli analog-four-snapshot-mutation-plan-report "G:\ANALOG FOUR\WHOLE PROJECT DUMP\PROJECTANALOGFOUR01.syx" --slot 1 --depth micro
```

It reads a saved Analog Four kit slot, scans Tracks 1-4 for nonzero CC-like
saved words, and proposes bounded `captured -> planned` changes relative to the
saved values.

Important boundary: these are still `candidate_unverified` saved offsets. The
report does not claim parameter names, CC mapping, or direct sendability. That
keeps the future hardware path honest until controlled before/after mapping
proves each offset.

## Next Slice

The next slice is a saved parameter offset mapper using differential evidence
from known kit variations or controlled exports. Hardware-sendable A4 mutation
should wait until that mapper is proven.
