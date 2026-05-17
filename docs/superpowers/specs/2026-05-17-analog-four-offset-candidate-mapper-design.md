# Analog Four Offset Candidate Mapper Design

Date: 2026-05-17

## Goal

Build a passive Analog Four MKII saved-kit offset candidate mapper. This is the
next step after the A4 kit snapshot decoder: scan saved kit variations and
identify byte offsets inside a track block that look like editable numeric
values.

The mapper must not name parameters yet. It should produce evidence only.
Every reported offset uses the status:

```text
candidate_unverified
```

## Approach

The command scans existing Analog Four kit records from a saved `.syx` file.
For one selected track, it:

- finds all Analog Four kit records in the file
- unpacks each Elektron 7-bit payload
- extracts the chosen Track 1-4 block
- reads even-aligned 16-bit big-endian words after the visible name area
- keeps values in the CC-like `0-127` range
- reports offsets that vary across kits

This gives us a passive differential view of where values live without
pretending we already know what each value controls.

## CLI Contract

```powershell
python -m rytm_randomizer.cli analog-four-offset-candidate-report "G:\ANALOG FOUR\WHOLE PROJECT DUMP\PROJECTANALOGFOUR01.syx" --track 1 --limit 12
```

The report includes:

- source path
- selected track
- kit records scanned
- candidate count
- top candidate offsets
- sample count
- unique value count
- min/max values
- preview values
- `candidate_unverified`
- safety section

## Boundaries

Do not add:

- parameter names
- captured-value mutation planning
- MIDI sending
- NRPN sending
- port selection
- live SysEx receive
- SysEx writes
- hardware mutation

## Success Criteria

- Synthetic tests prove varying saved words become candidates.
- Constant saved words are not reported as candidates.
- Real A4 project dump produces a passive candidate report.
- All side-effect and observability architecture tests remain green.
