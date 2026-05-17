# Dual-Machine A4 Snapshot Bridge Design

## Goal

Upgrade the passive dual-machine mock bridge so the Analog Four side can use a
saved Analog Four snapshot instead of the conservative safe-starter plan.

## Approaches Considered

1. Add a new bridge command for snapshot-backed dual-machine previews.
   This would keep old behavior isolated, but it would split the operator
   workflow too early.

2. Replace the existing A4 safe-starter plan entirely.
   This is cleaner eventually, but too abrupt while A4 saved offsets are still
   `candidate_unverified`.

3. Keep the existing command and add optional A4 snapshot inputs.
   This is the best next step. Existing calls still work, and adding
   `--analog-four-path` plus `--analog-four-slot` switches the A4 side to
   saved-snapshot mock events.

## Selected Design

The existing command remains valid:

```powershell
python -m rytm_randomizer.cli dual-machine-mock-bridge-report <rytm-path> --slot <1-128> --depth <micro|groove|strong>
```

New optional form:

```powershell
python -m rytm_randomizer.cli dual-machine-mock-bridge-report <rytm-path> --slot <1-128> --depth <micro|groove|strong> --analog-four-path <a4-path> --analog-four-slot <1-128>
```

`--target <rytm|analog-four|both>` can still be appended to either form.

## Behavior

- The Rytm side continues to use saved-kit snapshot mutation plans.
- Without A4 snapshot inputs, the A4 side keeps using the safe-starter CC plan.
- With A4 snapshot inputs, the A4 side uses the new A4 snapshot mock runtime.
- A4 snapshot-backed events use message type `saved_offset_candidate`, not `cc`.
- Reports must show the A4 source path, slot, kit name, `candidate_unverified`,
  and `no CC mapping claimed`.
- Target scoping still controls which devices emit mock events.

## Boundary

This remains passive/read-only. The bridge still does not open ports, send MIDI,
receive live SysEx, write SysEx, or mutate hardware. A4 saved offsets remain
unverified candidates until controlled mapping proves sendable parameters.
