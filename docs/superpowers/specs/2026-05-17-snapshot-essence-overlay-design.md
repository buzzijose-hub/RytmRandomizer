# Snapshot Essence Overlay Design

## Context

The current app can mutate a saved Rytm snapshot and send the mapped CC changes
through a guarded armed path. Separately, the project has a 12-pad style/essence
planner that can choose mapped machine profiles for genres such as Birmingham
techno, dark techno, schranz, and Detroit techno.

The missing bridge is a passive decision layer that compares the currently
loaded kit snapshot against a style/essence machine plan. This is needed before
we safely let software cycle engines across all 12 pads.

## Goal

Add a passive `snapshot-essence-overlay-report` that reads one saved Rytm kit
snapshot, resolves a style prompt into a 12-pad machine plan, and reports which
pads can stay on their captured engine versus which pads would need a mapped
machine switch.

## Approach

Create a focused module, `snapshot_essence_overlay.py`, with no MIDI imports and
no port access. It will:

- Decode the saved Rytm snapshot through the existing snapshot planner.
- Resolve the style prompt through the existing style-intent profiles.
- Rank mapped candidates per 12-pad role.
- Compare each selected mapped machine against the captured machine on that pad.
- Mark pads as snapshot-mutation ready, engine-switch ready, or blocked.

The first slice stays passive/read-only. It does not generate an active sender
stream and does not write SysEx. The report is the checkpoint that tells us what
the future armed engine-cycling path may safely attempt.

## CLI Shape

```text
python -m rytm_randomizer.cli snapshot-essence-overlay-report <path> --slot <1-128> --depth <micro|groove|strong> --style <text>
python -m rytm_randomizer.cli snapshot-essence-overlay-report <path> --slot <1-128> --depth <micro|groove|strong> --style <text> --discovery <0..1>
```

## Statuses

- `same_engine_snapshot_ready`: selected style engine matches the captured pad
  engine and the snapshot planner has captured-value changes.
- `engine_switch_ready`: selected style engine is mapped but differs from the
  captured pad engine, so a future active path would need CC15 before parameter
  shaping.
- `blocked_no_mapped_candidate`: no mapped machine candidate exists for that
  pad role.
- `blocked_no_snapshot_parameters`: selected style engine matches the captured
  pad engine, but no captured-value mutation parameters are available.

## Safety

- Passive/read-only only.
- No MIDI sending.
- No port opening.
- No live SysEx receive.
- No SysEx writes.
- No hardware mutation.
- No command execution.

## Acceptance

- The module imports silently without importing `mido`, `rtmidi`, or audio
  dependencies.
- A fixture Rytm kit plus `Birmingham dark techno` produces all 12 pad overlay
  rows.
- Same-engine pads are identified separately from engine-switch pads.
- CLI report reads the real project dump path and prints a deterministic
  overlay summary.
