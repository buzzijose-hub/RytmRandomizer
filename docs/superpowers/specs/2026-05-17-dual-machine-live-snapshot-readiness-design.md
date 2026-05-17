# Dual-Machine Live Snapshot Readiness Design

## Goal

Add a passive readiness gate over the dual-machine mock bridge. The report must
answer whether the current bridge preview is mapping-ready for a future live
send path, and it must clearly block Analog Four saved-offset candidates until
their CC/parameter mapping is proven.

## Selected Approach

Create `rytm_randomizer/dual_machine_live_snapshot_readiness.py`. It consumes an
already-built `DualMachineMockBridge`, captures its inert mock stream, and
classifies each machine:

- `ready_mapped_cc`: active device has only mapped CC mock messages.
- `ready_safe_starter_cc`: Analog Four safe-starter fallback uses validated
  smoke-test CCs.
- `blocked_candidate_unverified`: active device has saved-offset candidate
  events that do not claim a CC mapping.
- `blocked_no_mapped_messages`: active device has nothing usable to send.
- `untouched`: target scope leaves the device alone.

The report is not an active sender. It is a gate that prevents unverified saved
offsets from being treated as sendable hardware messages.

## CLI

Add:

```powershell
python -m rytm_randomizer.cli dual-machine-live-snapshot-readiness-report <rytm-path> --slot <1-128> --depth <micro|groove|strong>
python -m rytm_randomizer.cli dual-machine-live-snapshot-readiness-report <rytm-path> --slot <1-128> --depth <micro|groove|strong> --analog-four-path <a4-path> --analog-four-slot <1-128>
```

`--target <rytm|analog-four|both>` may be appended to either form.

## Boundary

This remains passive/read-only. It does not send MIDI, open ports, receive live
SysEx, write SysEx, or mutate hardware. A readiness result of `True` means the
mock bridge contains only mapped/safe CC events for active devices; it does not
itself arm or send anything.

## Success Criteria

- Existing safe-starter bridge previews report mapping readiness.
- A4 snapshot-backed bridge previews report blocked readiness because the A4
  side is `candidate_unverified`.
- Target scoping reports untouched devices as untouched.
- The command is import-safe and covered by focused and full tests.
