# Analog Four Controlled Diff Report Design

Date: 2026-05-17

## Goal

Add a passive controlled-diff report for Analog Four mapping sessions. The report compares a baseline saved kit export against a second saved export after one known parameter change.

## Design

The command reads two existing `.syx` files, selects the same Analog Four kit slot and Track 1-4 block from each file, and reports changed CC-like 16-bit words in the `0-127` range.

The command shape is:

```powershell
python -m rytm_randomizer.cli analog-four-controlled-diff-report "G:\ANALOG FOUR\MAPPING\A4_BASELINE.syx" "G:\ANALOG FOUR\MAPPING\A4_FILTER_FREQ_UP.syx" --slot 1 --track 1 --limit 16
```

## Mapping Workflow

1. Export the baseline kit.
2. Change exactly one known A4 parameter by hand.
3. Export the same kit again.
4. Run the controlled diff report.
5. Treat changed offsets as `candidate_unverified` until repeated exports prove the mapping.

## Boundaries

- Passive/read-only
- Controlled comparison only
- Candidate offsets only
- No parameter names claimed
- No MIDI sending
- No MIDI receive
- No port opening
- No hardware mutation
- No live SysEx receive
- No SysEx writes

## Success Criteria

- Synthetic tests prove changed CC-like words are reported.
- Non-CC-like words and unchanged words are ignored.
- CLI can compare two saved files without hardware.
- Real Analog Four project dump can be parsed in a same-file no-change comparison.
