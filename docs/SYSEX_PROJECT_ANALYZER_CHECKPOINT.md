# SysEx Project Analyzer Checkpoint

Date: 2026-05-17

## Purpose

`sysex-project-report <path>` is the passive whole-project companion to the
existing kit-bank analyzer. It reads a saved `.syx` project dump from disk and
groups complete Elektron SysEx records by device family, object type, byte
length, and slot range.

This is the first durable bridge between Jose's real project dumps and the
future Live Snapshot mode. It does not decode editable parameters yet; it
proves the software can recognize the project inventory safely before any
runtime mutation is attempted.

## Current Dumps

Analog Rytm MKII:

```powershell
python -m rytm_randomizer.cli sysex-project-report "G:\ANALOG RYTM\WHOLE PROJECT DUMP\PROJECTRYTM01.syx"
```

- 405 complete SysEx records
- 128 kits, 2998 bytes each
- 128 sounds, 201 bytes each
- 128 patterns, 14988 bytes each
- 16 song/project slots, 1506 bytes each
- 4 global slots, 107 bytes each
- 1 project/settings record, 2401 bytes

Analog Four MKII:

```powershell
python -m rytm_randomizer.cli sysex-project-report "G:\ANALOG FOUR\WHOLE PROJECT DUMP\PROJECTANALOGFOUR01.syx"
```

- 405 complete SysEx records
- 128 kits, 2770 bytes each
- 128 sounds, 415 bytes each
- 128 patterns, 14802 bytes each
- 16 song/project slots, 1506 bytes each
- 4 global slots, 2618 bytes each
- 1 project/settings record, 86 bytes

## Boundary

The analyzer is passive/read-only. It does not request dumps, open MIDI ports,
receive live SysEx, send MIDI, decode editable parameters, mutate hardware, or
write SysEx. The next Live Snapshot slice can now focus on decoding the Rytm
kit record shape from saved bytes and mapping that into a 12-pad snapshot
model.
