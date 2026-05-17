# SysEx Kit Bank Analyzer Checkpoint

Date: 2026-05-16

## Purpose

The passive SysEx kit bank analyzer is the first bridge between saved Analog
Rytm kit dumps and the future Live Snapshot mode. It lets the project inspect a
saved `.syx` kit bank offline, split it into complete SysEx records, identify
kit slots, and distinguish the repeated blank/default tail of a bank without
opening MIDI ports or touching hardware.

## Current Capability

The analyzer can:

- read an existing SysEx file from disk
- split complete `F0` ... `F7` messages
- detect fixed-length kit records
- extract the Elektron manufacturer ID bytes
- read the visible kit name field used by the current Rytm kit-bank fixture
- report each slot's header index, file offset, and byte length
- identify the largest duplicate normalized record group
- mark that duplicate unnamed group as blank/default candidates
- expose the report through the passive CLI:

```powershell
python -m rytm_randomizer.cli sysex-kit-bank-report "G:\ANALOG RYTM\KITS\AM9KITS.syx"
```

## AM9KITS.syx Observation

Jose's local `AM9KITS.syx` bank was analyzed read-only. The report shows:

- record count: 128
- record length: 2998 bytes
- fixed-length records: true
- valid SysEx boundaries: true
- manufacturer ID: `00 20 3C`
- nonblank kit slots: 1-16
- blank/default candidate slots: 17-128

This matches the operator memory that kits 1-16 contain the useful material and
the rest of the bank is blank/default.

## Safety Boundary

This feature is passive only:

- no MIDI sending
- no port discovery
- no port opening
- no command execution
- no hardware mutation
- no SysEx writes
- no hardware required

It reads a file that already exists. It does not request a dump from the Rytm,
decode editable parameter maps, send restore packets, or mutate kit state.

## Live Snapshot Relevance

The analyzer gives the project real kit-bank material to test future snapshot
models against before any live hardware capture is attempted. The next snapshot
work can use this capability to prove that saved kit records can be carried as
raw snapshot baselines, while deeper parameter decoding remains a separate,
manual-backed phase.

The first passive mock snapshot fixture now exists as `am9-slot-01`. It is
AM9-inspired metadata rather than decoded SysEx parameter data. It records a
12-pad captured-machine support mix: nine pads on currently mapped machine
families and three pads on future-only families that still need manual mapping.
`essence-application-readiness-report --fixture am9-slot-01` uses this fixture
to show how Live Snapshot readiness will block unmapped captured machines
before any live capture path exists.

## Still Not Implemented

- live MIDI receive/capture
- current-kit dump request from hardware
- parameter decoding from packed kit bytes
- machine-family mutation support beyond the existing V1.34 anchors
- restore-to-snapshot SysEx writes
- 12-pad runtime mutation behavior
