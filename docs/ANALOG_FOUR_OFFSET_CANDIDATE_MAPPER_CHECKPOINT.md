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

## Promotion Path

The codebase now has a verified saved-offset mapping registry and lookup path.
The registry is empty by default, so no saved Analog Four offset is guessed or
sent as a CC until controlled evidence promotes it. When a future controlled
diff proves a track/offset pair maps to a named CC parameter, that exact entry
can be supplied to the snapshot planner. The planner then emits a mapped CC
mock event for that saved offset while all other offsets remain
`candidate_unverified`.

The passive guide command:

```powershell
python -m rytm_randomizer.cli analog-four-saved-offset-mapping-guide --track 1 --parameter filter-1-frequency
```

prints the controlled before/after export workflow, the matching
`analog-four-controlled-diff-report` command, and the exact verified mapping
entry shape to add only after the offset is proven.

After exporting before/after files, the passive promotion command:

```powershell
python -m rytm_randomizer.cli analog-four-saved-offset-mapping-promotion-report "<before.syx>" "<after.syx>" --slot 1 --track 1 --parameter filter-1-frequency --limit 8
```

runs the controlled diff and prints an `AnalogFourVerifiedSavedOffsetMapping`
entry only when exactly one saved offset changed. If no offsets or multiple
offsets changed, it stays blocked and asks for a cleaner controlled retest.

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

Use the guide and promotion report with controlled baseline/variant exports to
prove the first real A4 saved offset mappings, starting with one low-risk
Track 1 parameter such as Filter 1 Frequency CC18 or Amp Pan CC10. Add only
the proven track/offset/CC entry, then let the existing guarded send plan
decide whether the selected snapshot has no remaining unverified offsets.
