# Live Snapshot Mode Design Checkpoint

Date: 2026-05-16

## Purpose

Live Snapshot mode is the performance-centered path for RytmRandomizer. Instead
of loading the app's validated anchors first, it captures the kit that is
already loaded on the Analog Rytm, treats that captured kit as the temporary
anchor, mutates from that snapshot, and returns to that snapshot on command.

Safe Anchors mode remains first-class. It is still the known-good fallback,
test mode, sound-design mode, and release-validation base.

## Product Decision

Startup should ask the operator which mode to use:

```text
Select performance mode:

1 = Safe Anchors
    Load validated app anchors, then mutate from them.

2 = Live Snapshot
    Capture the currently loaded Rytm kit, then mutate from that snapshot.

Mode:
```

Safe Anchors stays option `1` because it is the validated V1.34 alpha path.
Live Snapshot is option `2` until its capture and return behavior pass real
hardware validation.

Live Snapshot also needs a target choice before any future hardware path opens
ports:

```text
Select Live Snapshot target:

1 = Analog Rytm only
2 = Analog Four only
3 = Both machines

Target:
```

The target choice is a safety boundary. A machine outside the selected target is
left alone: no capture request, no mutation CCs, no SysEx restore, and no
machine changes.

## Safe Anchors Mode

- Uses the existing validated app anchors.
- Scene/global commands may auto-load anchors when four-pad state is empty.
- `S5` and `Z` return to the validated app anchors.
- Current V1.34 alpha coverage is four pads:
  - Pad 1: BD Hard foundation
  - Pad 2: BD Classic / secondary percussion
  - Pad 3: SY Raw midrange bass / synth-percussion
  - Pad 4: BD Acoustic body/accent
- Current scene/global flow does not cycle Pad 3 through SY Chip, Dual VCO, or
  other machines. Pad 3 stays on the curated SY Raw lane unless a future
  validated machine expansion changes that behavior.

## Live Snapshot Mode

- Reads the currently loaded kit once.
- Captures all 12 pads as a snapshot baseline.
- Stores both machine identity and parameter values per pad.
- Mutates relative to that captured baseline.
- `S5`, `Z`, or their future 12-pad equivalents return to the captured
  snapshot, not the app's built-in anchors.
- Later manual knob/pad edits are not tracked continuously. The operator must
  explicitly capture again to create a new baseline.
- Live Snapshot mode must never surprise-replace the performer's kit.
- Live Snapshot mode must allow Rytm-only, Analog-Four-only, and both-machines
  target scopes.

## Snapshot State Model

The future snapshot model needs these concepts:

- `mode`: `safe_anchors` or `live_snapshot`
- `capture_status`: `not_requested`, `capturing`, `captured`, `failed`,
  `partial`
- `pad_count`: expected 12 for Live Snapshot
- per-pad machine identity
- per-pad parameter map
- per-pad baseline values
- per-pad current values written by the app
- per-pad previous app-written values for undo
- return target: app anchors for Safe Anchors, captured snapshot for Live
  Snapshot

Unknown or unsupported machines are allowed in the captured snapshot, but they
are not allowed to be mutated until the app has a validated parameter map and
safe-range policy for that machine. Return-to-snapshot may still be possible
only after the restore packet format is validated.

## Essence Application Readiness Gate

The passive `essence-application-readiness-report` command now models how an
Essence Plan would be gated under Safe Anchors or Live Snapshot.

Examples:

```powershell
python -m rytm_randomizer.cli essence-application-readiness-report --mode safe-anchors --tags metallic,bell,driving,repetition --discovery 0.35
python -m rytm_randomizer.cli essence-application-readiness-report --mode live-snapshot --description "metallic bell driving repetition Detroit techno" --discovery 1.0 --snapshot captured
python -m rytm_randomizer.cli essence-application-readiness-report --mode live-snapshot --description "metallic bell driving repetition Detroit techno" --discovery 0.35 --fixture am9-slot-01
```

Current behavior:

- Safe Anchors reports Pads 1-4 as ready when the selected candidates are
  mapped, and Pads 5-12 as blocked because current V1.34 runtime support is
  four-pad only.
- Live Snapshot reports all pads blocked until a complete 12-pad snapshot is
  available.
- With a captured snapshot, future inventory-only candidates such as SY Chip
  still report `future_only` until manual-backed machine maps and safe ranges
  exist.
- With `--fixture am9-slot-01`, readiness uses the AM9-inspired mock 12-pad
  captured machine inventory. This can block pads whose captured machine family
  is not yet mapped, even when the selected essence-plan candidate is mapped.

This is a passive planning gate only. It does not capture kits, parse live
SysEx, send MIDI, or enable Pads 5-12 mutation.

## Safety Rules

- If capture fails, no mutation commands may run.
- If capture is partial, no mutation commands may run unless the operator
  explicitly chooses a future pad-limited recovery path.
- Live Snapshot capture must be read-only until the operator arms mutation.
- Real MIDI capture must be behind an explicit armed hardware path.
- Passive reports and dry-run fixtures must never open ports or send MIDI.
- The first implementation slices should model snapshot semantics without
  touching hardware.
- The hardware receive path must be validated separately before any real kit
  mutation depends on it.

## Technical Boundary

Current V1.34 alpha primarily sends MIDI CC messages. It does not yet ask the
Rytm what kit is loaded. True Live Snapshot mode requires a new receive/capture
path, likely based on manual-backed kit or sound dump behavior.

That future receive path must answer:

- how to request the currently loaded kit/sound state
- how the Rytm identifies machine type per pad
- how kit data maps back to CC-style parameter names
- how to detect malformed, stale, partial, or wrong-device responses
- how to prove the parser does not mutate hardware
- how to verify restore-to-snapshot on real hardware

## Passive SysEx Bank Analyzer Checkpoint

The first offline SysEx analysis slice now exists. The passive
`sysex-kit-bank-report <path>` CLI command reads an already-saved `.syx` file,
splits complete kit-bank records, extracts visible slot names and offsets, and
identifies repeated unnamed records as blank/default candidates.

Jose's `AM9KITS.syx` file validates the usefulness of this path: it reports
128 fixed-length records, with slots 1-16 as nonblank and 17-128 as
blank/default candidates.

This is not live capture. It does not request a dump, decode editable
parameters, write SysEx, or restore hardware state. It gives Live Snapshot mode
a real offline fixture shape to build against before hardware receive work is
authorized.

The first mock 12-pad fixture now exists as `am9-slot-01`. It is hand-authored
metadata inspired by the AM9 bank observation, not decoded editable kit data.
It records mapped machines for nine pads and future-only machine families for
three pads, giving Live Snapshot readiness a realistic captured-machine support
mix to test against.

## Engine Coverage Direction

The current profile registry covers a useful but limited set of machines:

- BD Hard
- BD Sharp
- BD Classic
- BD Acoustic
- BD FM
- BD Plastic
- BD Silky
- SD Hard
- SD Classic
- SD FM
- SY Raw

Live Snapshot mode should preserve any loaded machine, including machines not
yet supported for mutation. Missing engine families such as SY Chip and Dual
VCO need a manual-backed inventory, parameter map, safe ranges, mock fixtures,
and hardware validation before mutation support is enabled.

## Implementation Sequence

1. Done: add passive performance-mode and snapshot-state data models.
2. Done: add tests proving Live Snapshot semantics block mutation without a
   complete snapshot.
3. Done: add passive saved-kit-bank analyzer for offline SysEx fixture
   visibility.
4. Done: add a passive Essence Application Readiness gate that explains
   whether a 12-pad plan is ready, blocked, or future-only by mode.
5. Done: add mock 12-pad snapshot fixtures and wire the AM9-inspired fixture
   into Live Snapshot readiness.
6. Done: add passive target-scope model for Rytm-only, Analog-Four-only, and
   both-machines Live Snapshot operation.
7. Add startup mode-selection design to the shell without changing the
   validated Safe Anchors flow.
8. Add a manual-backed parser plan for the Rytm kit/sound dump format.
9. Add read-only capture in a separately armed hardware-validation path.
10. Add restore-to-snapshot validation.
11. Add mutation support per machine family only after each parameter map and
   safe range is validated.

## Current Decision

Proceed with passive snapshot infrastructure only: mode metadata, snapshot-state
semantics, safety gates, and offline SysEx bank visibility. Do not implement
real hardware capture, SysEx writes, or new machine mutation support until the
receive/parser work is designed and tested.
