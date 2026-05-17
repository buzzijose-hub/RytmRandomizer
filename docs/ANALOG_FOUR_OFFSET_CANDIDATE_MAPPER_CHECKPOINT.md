# Analog Four Offset Candidate Mapper Checkpoint

Date: 2026-05-17

## What This Milestone Proves

The project can now scan saved Analog Four MKII kit variations and identify saved-value offsets that vary across kits. This creates passive evidence for future parameter mapping without claiming parameter names.

## Current Scope

- Reads saved `.syx` files from disk
- Scans Analog Four kit records
- Selects one Track 1-4 block
- Can summarize all four track blocks in one passive report
- Reads CC-like 16-bit words in the `0-127` range
- Reports varying offsets across saved kits
- Marks every offset as `candidate_unverified`

## Safety Boundary

- passive/read-only
- candidate offsets only
- no parameter names claimed
- no MIDI sending
- no MIDI receive
- no port opening
- no hardware mutation
- no live SysEx receive
- no SysEx writes
- no hardware required

## Next Slice

Use the controlled diff report with baseline/variant exports to promote specific offsets from `candidate_unverified` to named saved-parameter mappings. Analog Four captured-value mutation should wait until those named mappings are proven.
