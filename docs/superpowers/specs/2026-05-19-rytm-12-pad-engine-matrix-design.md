# Rytm 12-Pad Engine Matrix Runtime-Brain Design

## Context

Jose validated that all 12 Analog Rytm pads respond to MIDI CC movement, and
the current code now enforces the Analog Rytm MKII OS 1.72 pad/machine table.
The next risk is operator trust: before expanding live engine cycling and
12-pad mutation, the software needs a single passive report that explains what
each pad can legally become and what level of runtime support exists for those
engines.

This directly addresses the Pad 10 confusion from live testing. Pad 10 is the
OH open hihat lane. XT Classic belongs only on Pads 6-8. The code already
models this; the product now needs to surface it plainly.

## Goal

Add a passive Rytm 12-pad engine matrix report that shows, for every pad:

- track code and musical lane label;
- MIDI channel and zero-based wire channel;
- every allowed machine from the OS 1.72 compatibility table;
- CC15 machine-select readiness;
- engine source-starter coverage;
- existing V1.34 tuned-mutation support versus engine-select-only support.

The report should become the reference layer for later active runtime work:
style kits, snapshot kits, audio-analyzer kits, and genre/tag-driven kits should
all be able to ask the same question: "is this machine legal and supported on
this pad?"

## Non-Goals

This slice does not add:

- new live MIDI sends;
- new armed app flags;
- live SysEx receive;
- SysEx writes;
- audio analysis;
- continuous knob tracking;
- Analog Four changes;
- deeper per-engine source parameter maps.

## Behavior

The new CLI command should be:

```powershell
python -m rytm_randomizer.cli rytm-12-pad-engine-matrix-report
```

It is passive/read-only. It imports no real MIDI backend, opens no ports, sends
no MIDI, receives no SysEx, and mutates no hardware.

## Success Criteria

- The matrix covers exactly 12 pads and the complete OS 1.72 allowed-machine
  table currently modeled in `machine_catalog`.
- Pad 10 reports `OH / Open Hihat` and never lists `XT Classic`.
- Pads 6-8 report `XT Classic` as the tom-lane engine.
- Every listed machine has a CC15 value.
- Source-starter coverage and pending gaps are counted explicitly.
- The CLI help and top-level help fixture include the new report.
- Focused tests, CLI tests, architecture tests, and fast tests pass.
