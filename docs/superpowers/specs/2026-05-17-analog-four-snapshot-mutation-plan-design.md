# Analog Four Snapshot Mutation Plan Design

Date: 2026-05-17

## Purpose

Add the Analog Four counterpart to Rytm snapshot mutation planning. The planner
starts from saved Analog Four kit values and proposes bounded changes relative
to those captured values.

## Honesty Boundary

The current Analog Four snapshot decoder identifies kit and track blocks, but
the saved parameter offsets are still unmapped. Therefore this first planner
must treat planned changes as `candidate_unverified` saved offsets. It must not
claim parameter names, CC numbers, or direct sendability.

## Command Shape

```powershell
python -m rytm_randomizer.cli analog-four-snapshot-mutation-plan-report <path> --slot <1-128> --depth <micro|groove|strong>
```

The command scans Tracks 1-4 for CC-like saved words in the selected kit slot,
selects a small deterministic set per track, and reports `captured -> planned`
values.

## Behavior

- Decode one saved Analog Four kit slot from an existing `.syx` file.
- Build per-track plans for Tracks 1-4.
- Use saved values as the baseline.
- Apply deterministic bounded deltas for `micro`, `groove`, and `strong`.
- Clamp planned values to MIDI-safe `0..127` value range.
- Report saved offset and word index instead of parameter names.

## Safety Contract

This feature is passive/read-only. It does not import MIDI libraries, open
ports, send MIDI, request dumps, receive live SysEx, write SysEx, mutate
hardware, or claim a parameter map.

## Success Criteria

- Importing the planner is silent and does not load MIDI libraries.
- A synthetic A4 kit produces captured-value-relative plans for all four tracks.
- Unknown depth is rejected.
- The CLI reports `candidate_unverified`, `no parameter names claimed`, and
  `no MIDI sending`.
