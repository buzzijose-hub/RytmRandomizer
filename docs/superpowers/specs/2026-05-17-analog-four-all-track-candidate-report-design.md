# Analog Four All-Track Candidate Report Design

Date: 2026-05-17

## Goal

Add a passive all-track mode to the Analog Four offset-candidate report so one command can summarize Tracks 1-4 from a saved kit bank or whole-project dump.

## Design

The all-track report reuses the existing single-track candidate scanner. It reads the saved `.syx` file once, builds one candidate report per Analog Four track, and formats those reports under one safety boundary.

The command shape is:

```powershell
python -m rytm_randomizer.cli analog-four-offset-candidate-report "G:\ANALOG FOUR\WHOLE PROJECT DUMP\PROJECTANALOGFOUR01.syx" --all-tracks --limit 8
```

## Boundaries

- Passive/read-only
- Candidate offsets only
- No parameter names claimed
- No MIDI sending
- No MIDI receive
- No port opening
- No hardware mutation
- No live SysEx receive
- No SysEx writes

## Success Criteria

- Synthetic tests prove all four track reports are produced.
- CLI tests prove `--all-tracks --limit <n>` reads saved kits without hardware.
- Help and operator docs show both single-track and all-track forms.
- Real Analog Four project dump produces a four-track passive report.
