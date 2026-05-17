# Performance Snapshot Target Scope Design

Date: 2026-05-17

## Purpose

Live Snapshot mode must let the operator choose which machine is in scope:
Analog Rytm only, Analog Four only, or both machines. A target choice must also
make the inverse rule explicit: devices outside the selected target are left
alone.

## Operator Intent

Supported targets:

- `rytm`: capture, mutate, and restore only the Analog Rytm.
- `analog-four`: capture, mutate, and restore only the Analog Four.
- `both`: capture, mutate, and restore both machines as one performance scope.

Aliases such as `a4`, `analog4`, `analog_four`, and `all` may normalize to the
canonical targets, but reports should always print the canonical target.

## Passive Command

```powershell
python -m rytm_randomizer.cli performance-snapshot-target-report --target <rytm|analog-four|both>
```

This command does not inspect SysEx files or hardware. It only reports the
selected target scope, the devices that are armed for future capture/mutation,
and the devices that must remain untouched.

## Safety Contract

Any future hardware path must consult this target scope before opening ports or
building outgoing messages. If a device is outside the selected target, it must
receive no capture request, no CC messages, no SysEx restore, and no machine
changes.

## Success Criteria

- `rytm` reports Analog Rytm as active and Analog Four as untouched.
- `analog-four` reports Analog Four as active and Analog Rytm as untouched.
- `both` reports both devices as active and no untouched devices.
- Invalid targets produce a passive error.
- Importing the target-scope module is silent and does not import MIDI libraries.
