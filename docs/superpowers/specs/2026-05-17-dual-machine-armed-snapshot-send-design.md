# Dual-Machine Armed Snapshot Send Design

## Context

The project now has a passive active send plan and a guarded mock-only dry-run.
Those layers prove which events are eligible and prove that blocked plans emit
nothing. The next step is the first real hardware send path, still guarded by
the same plan.

## Goal

Add an app-level `--arm` / `--dry-run` snapshot send path that can send one
selected target scope from a saved project/kit snapshot. The first active slice
is single-target only: Rytm or Analog Four, not both at once.

## Chosen Approach

Use the app entry point, not the passive CLI, because the CLI must remain a
read-only report surface. The app already owns `--arm`, port selection, and
active smoke tests, so it is the right boundary for real sending.

The active path will:

- Build the dual-machine bridge from saved dumps.
- Build the active send plan.
- Refuse blocked plans.
- Refuse `target=both` for real hardware sending in this slice.
- Prompt for one MIDI output port based on the selected target.
- Ask the operator to type `SEND` before any MIDI message leaves.
- Send only eligible mapped CC events.

Dry-run uses the existing mock-only guarded sender and opens no port.

## Scope

In scope:

- `--dual-machine-snapshot-send` app modifier.
- Snapshot args: path, slot, depth, target, optional Analog Four path/slot.
- Dry-run report using the mock sender.
- Armed report using a selected real output port.
- Single-target active sending only.
- Fake-port tests proving message emission without hardware.

Out of scope:

- Sending both devices in one active command.
- Continuous live SysEx snapshot receive.
- Writing SysEx back to hardware.
- Mapping Analog Four saved-offset candidates.
- GUI controls.

## CLI Shape

```text
python -m rytm_randomizer.app --dry-run --dual-machine-snapshot-send --snapshot-path <path> --snapshot-slot <1-128> --snapshot-depth <micro|groove|strong> --snapshot-target <rytm|analog-four|both>
python -m rytm_randomizer.app --arm --dual-machine-snapshot-send --snapshot-path <path> --snapshot-slot <1-128> --snapshot-depth <micro|groove|strong> --snapshot-target <rytm|analog-four>
```

Optional Analog Four saved snapshot arguments:

```text
--analog-four-path <path> --analog-four-slot <1-128>
```

## Safety Rules

- `--dual-machine-snapshot-send` requires either `--dry-run` or `--arm`.
- Active hardware send requires `--arm`.
- Active hardware send requires a single target, not `both`.
- Active hardware send requires plan readiness.
- Active hardware send requires exact operator confirmation: `SEND`.
- The passive CLI remains free of active sender construction and port opening.

## Acceptance

- Dry-run Rytm-only real project dump emits 60 mock messages.
- Armed Rytm-only fake-port test sends the eligible mapped CC messages.
- Armed combined Rytm+A4 with A4 candidates refuses before opening a port.
- Armed `target=both` refuses before opening a port.
- Full suite remains green.
