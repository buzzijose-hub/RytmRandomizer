# Essence Application Readiness Design

Date: 2026-05-16

## Purpose

The Essence Plan Preview can now choose candidate machines for a 12-pad Rytm
layout, but planning is not the same as safe runtime application. This design
adds a passive readiness layer that answers one question:

> Given a reference-derived 12-pad plan and a performance mode, what can be
> applied today, what is blocked, and why?

## Design

Add `rytm_randomizer.essence_application`, a metadata-only module that consumes
the existing machine catalog plan and the existing `SnapshotState` model. It
does not send MIDI, open ports, request SysEx, parse live kits, or mutate
hardware.

The module reports per-pad status:

- `ready`: the selected candidate is mapped and the current mode has a usable
  baseline for that pad.
- `blocked`: the pad is outside current runtime support or Live Snapshot has no
  complete snapshot yet.
- `future_only`: the selected candidate still needs manual-backed mapping.

Overall readiness is intentionally strict: a full 12-pad application is not
ready unless all 12 pads are ready. That means Safe Anchors currently reports a
partial runtime boundary because the validated V1.34 active surface covers Pads
1-4 only. Live Snapshot reports blocked until a complete 12-pad snapshot exists.

## CLI

Add a passive command:

```powershell
python -m rytm_randomizer.cli essence-application-readiness-report --mode safe-anchors --description "metallic bell driving repetition" --discovery 0.35
python -m rytm_randomizer.cli essence-application-readiness-report --mode live-snapshot --description "metallic bell driving repetition" --discovery 1.0 --snapshot captured
```

This command prints global readiness, per-pad selected candidate, status, and
reason. It is a planning gate only.

## Safety Boundary

This design adds no active runtime behavior:

- no MIDI sending
- no port discovery
- no port opening
- no command execution
- no hardware mutation
- no live SysEx receive/write behavior
- no Pads 5-12 runtime mutation
