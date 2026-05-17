# Mock 12-Pad Snapshot Fixtures Design

Date: 2026-05-16

## Purpose

Live Snapshot readiness currently knows whether a complete 12-pad snapshot was
captured, but it does not know which machines were captured on those pads. The
next passive slice adds deterministic mock snapshot fixtures so readiness can
reason about realistic pad/machine inventories before live SysEx capture exists.

## Design

Add `rytm_randomizer.snapshot_fixtures`, a passive module containing immutable
12-pad snapshot fixture metadata. The first fixture is an AM9-inspired mock
snapshot, not a decoded kit dump. It records:

- fixture key, label, source note, and capture status
- exactly 12 pad entries
- captured machine key/label/value per pad when known
- support status: currently mutable versus needs manual mapping
- a small baseline parameter count so reports can prove the fixture carries
  baseline-shape metadata without decoding packed SysEx bytes

The fixture is intentionally explicit about future-only machines such as hat
and rim families. Those pads may be captured, preserved, and restored later,
but they are not mutation-ready until manual-backed parameter maps and safe
ranges exist.

## Readiness Integration

Extend `evaluate_essence_application_readiness()` with an optional
`snapshot_fixture`. In Live Snapshot mode:

- the fixture supplies captured snapshot state
- if the captured machine on a pad is unmapped, that pad reports
  `snapshot_machine_needs_manual_mapping`
- if the selected Essence Plan candidate is unmapped, that pad still reports
  `machine_needs_manual_mapping`
- mapped captured machine plus mapped selected candidate can be marked ready

This is still a passive gate. It does not decide to switch engines, send CCs,
decode SysEx, or restore snapshots.

## CLI

Extend the existing readiness report with:

```powershell
python -m rytm_randomizer.cli essence-application-readiness-report --mode live-snapshot --description "metallic bell driving repetition" --discovery 0.35 --fixture am9-slot-01
```

The report includes the fixture label and per-pad reasons.

## Safety Boundary

This design adds no active behavior:

- no MIDI sending
- no MIDI receive
- no port opening
- no command execution
- no hardware mutation
- no live SysEx parsing
- no SysEx writes
- no Pads 5-12 runtime mutation
