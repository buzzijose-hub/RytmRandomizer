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

## Next Slice

The next slice is a saved parameter offset mapper using differential evidence
from known kit variations or controlled exports. Captured-value A4 mutation
should wait until that mapper is proven.
