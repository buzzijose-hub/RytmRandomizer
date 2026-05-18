# Snapshot Mutation Plan Checkpoint

Date: 2026-05-17

Requirements reference: `docs/PLAN_REQUIREMENTS.md`

## Purpose

`sysex-snapshot-mutation-plan-report <path> --slot <1-128> --depth <micro|groove|strong>`
is the first passive bridge from decoded Live Snapshot baselines to mutation
behavior. It does not load safe anchors. It starts from the values captured in
the saved kit snapshot and proposes bounded CC changes around those values.

## What It Proves

- A saved Rytm kit snapshot can be decoded and used as the mutation baseline.
- Planned changes are captured-value relative, not anchor relative.
- Known machine maps keep their musical parameter names.
- Generic mapped machines use saved CC-slot labels so all identified pads can
  still participate in planning.
- Depth values are constrained to `micro`, `groove`, and `strong`.
- The report remains passive/read-only and sends no MIDI.

## Current Commands

Whole-project dump:

```powershell
python -m rytm_randomizer.cli sysex-snapshot-mutation-plan-report "G:\ANALOG RYTM\WHOLE PROJECT DUMP\PROJECTRYTM01.syx" --slot 1 --depth micro
```

Mock runtime bridge:

```powershell
python -m rytm_randomizer.cli sysex-snapshot-mock-runtime-report "G:\ANALOG RYTM\WHOLE PROJECT DUMP\PROJECTRYTM01.syx" --slot 1 --depth micro
```

Performance kit bank:

```powershell
python -m rytm_randomizer.cli sysex-snapshot-mutation-plan-report "G:\ANALOG RYTM\KITS\ANALOGRYTMKITS2.syx" --slot 16 --depth micro
```

Both report:

- source kit slot and kit name
- source snapshot parameter-map status
- planned pads and planned change count
- per-pad baseline status
- planned CC changes in the form `captured -> planned`
- mutation policy: captured-value relative, no anchor loading, no machine
  switching

The mock runtime report additionally proves that the planned changes can be
captured as inert CC messages in `MockMidiSender`, with 0-based wire channels
and 1-based operator-facing MIDI channel metadata.

## Boundary

This is passive/read-only. It does not request dumps, receive live SysEx, open
ports, send MIDI, mutate hardware, restore a kit, switch machines, load anchors,
or write SysEx.

Use `rytm-controlled-diff-report` with baseline/variant Rytm exports to prove
which decoded saved parameter moved after one controlled hand tweak. This is the
passive calibration path for expanding Live Snapshot behavior across all 12
pads.

The current runtime slice connects this planner to mock MIDI message capture,
still without opening a port. Next, the armed Live Snapshot flow can be designed
around the same plan object.
