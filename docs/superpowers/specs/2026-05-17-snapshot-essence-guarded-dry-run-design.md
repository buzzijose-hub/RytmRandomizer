# Snapshot Essence Guarded Dry-Run Design

## Purpose

Prove that the new 12-pad Rytm snapshot essence send plan can pass through an explicit guard before any hardware sender exists. This is the safety layer between the passive 298-event plan and a future armed real-MIDI sender.

## Design

Add a mock-only guarded sender for `SnapshotEssenceSendPlan`. The guard accepts an already-built plan plus an injected `MockMidiSender`. It emits no messages unless all conditions are true:

- `armed=True`
- `dry_run_confirmed=True`
- the send plan is ready
- every planned event is eligible

Accepted plans emit one inert mock CC message per eligible event. Refused plans emit no partial messages and report the refusal reason. The module must remain passive: no `mido`, no port opening, no live SysEx receive, no SysEx writes, and no hardware mutation.

## CLI

Add:

```text
snapshot-essence-guarded-send-dry-run-report <path> --slot <1-128> --depth <micro|groove|strong> --style <text> [--discovery <0..1>]
```

The CLI builds the snapshot essence send plan from a saved Rytm SysEx file, executes the guard into a fresh `MockMidiSender`, and prints a deterministic report. It is a dry-run report only; it does not open a MIDI port or send hardware MIDI.

## Testing

Use TDD. Add tests for import safety, missing arming refusal, missing confirmation refusal, blocked/ineligible plan refusal, accepted ready-plan emission, report formatting, and CLI output. Verify focused tests, nearby snapshot/send-plan regressions, architecture import/observability guards, and the full suite.
