# Rytm Controlled Diff Report Design

Date: 2026-05-17

## Goal

Add a passive controlled-diff report for Analog Rytm mapping sessions. The report compares a baseline saved kit export against a second saved export after one known pad parameter change.

## Design

The command reads two existing `.syx` files, selects the same Rytm kit slot and pad from each file, decodes both with the existing saved-kit snapshot decoder, and reports changed decoded saved parameters.

The command shape is:

```powershell
python -m rytm_randomizer.cli rytm-controlled-diff-report "G:\ANALOG RYTM\MAPPING\RYTM_BASELINE.syx" "G:\ANALOG RYTM\MAPPING\RYTM_PAD1_FILTER_UP.syx" --slot 1 --pad 1 --limit 16
```

## Mapping Workflow

1. Export the baseline kit.
2. Change exactly one known Rytm pad parameter by hand.
3. Export the same kit again.
4. Run the controlled diff report for the target pad.
5. Use the changed decoded parameter as evidence for 12-pad snapshot mapping.

## Boundaries

- Passive/read-only
- Controlled comparison only
- Mapped saved parameters only
- No MIDI sending
- No MIDI receive
- No port opening
- No hardware mutation
- No live SysEx receive
- No SysEx writes

## Success Criteria

- Synthetic tests prove changed mapped parameters are reported.
- Unchanged mapped parameters are not reported.
- CLI can compare two saved files without hardware.
- Real Rytm project dump can be parsed in a same-file no-change comparison.
