# Snapshot Essence Send Plan Design

## Purpose

Build the next passive bridge between saved-kit snapshot mode and future 12-pad hardware mutation. The feature turns a `SnapshotEssenceOverlayPlan` into an ordered CC event plan that can be inspected and tested without opening MIDI ports or sending hardware MIDI.

## Design

The send plan is Rytm-only for this slice. It accepts a saved Rytm SysEx file, slot, mutation depth, style prompt, and optional discovery amount. It first builds the existing snapshot essence overlay, then converts each pad decision into eligible mock-send events:

- If the selected essence machine differs from the captured snapshot machine, emit `CC15` first as a `machine_switch` event.
- For switched-machine pads, emit the selected mapped profile's known anchor parameters as `selected_profile_anchor` events. This keeps engine cycling musical and avoids applying captured old-engine values to a new engine where those values may mean something else.
- For same-engine pads, emit captured-value relative changes as `snapshot_mutation` events.
- Blocked overlay pads emit no events and mark the plan not ready.

The plan remains passive. It may capture events into `MockMidiSender` for reports/tests, but it must not import `mido`, open ports, receive live SysEx, write SysEx, or mutate hardware.

## Interfaces

- New module: `rytm_randomizer/snapshot_essence_send_plan.py`
- New CLI report:

```text
snapshot-essence-send-plan-report <path> --slot <1-128> --depth <micro|groove|strong> --style <text> [--discovery <0..1>]
```

The formatter reports source kit metadata, style matching, readiness, event counts, per-pad policy counts, a mock MIDI stream preview, and passive safety lines.

## Error Handling

The CLI returns deterministic passive errors for missing files, invalid slot/depth/discovery/style values, and blocked plans. Errors state that no MIDI was sent and no command was executed.

## Testing

Add focused tests for import safety, mixed same-engine/engine-switch behavior, mock capture ordering, and CLI output. Run the focused new test file first red, then green, then run nearby snapshot/style/send-plan regressions and the full suite.
