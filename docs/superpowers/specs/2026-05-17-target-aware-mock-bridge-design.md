# Target-Aware Mock Bridge Design

Date: 2026-05-17

## Purpose

The mock runtime bridge must obey the Live Snapshot target scope. If the
operator selects Rytm-only, the mock stream must contain only Rytm messages. If
the operator selects Analog-Four-only, the mock stream must contain only Analog
Four messages. If the operator selects both, existing combined behavior remains
unchanged.

## Command Shape

Existing command remains valid and defaults to `both`:

```powershell
python -m rytm_randomizer.cli dual-machine-mock-bridge-report <path> --slot <1-128> --depth <micro|groove|strong>
```

New target-aware form:

```powershell
python -m rytm_randomizer.cli dual-machine-mock-bridge-report <path> --slot <1-128> --depth <micro|groove|strong> --target <rytm|analog-four|both>
```

## Behavior

- `both`: include Rytm snapshot mock messages and Analog Four safe-starter mock
  messages.
- `rytm`: include only Rytm snapshot mock messages; mark Analog Four as
  untouched.
- `analog-four`: include only Analog Four safe-starter mock messages; mark
  Rytm as untouched.

For this slice, the command still accepts the saved Rytm path because the
current bridge command is Rytm-snapshot backed. The important behavior being
proved is target-aware message emission. A later Analog-Four snapshot-backed
command can remove the Rytm-file dependency for Analog-Four-only operation.

## Safety Contract

Target filtering happens before mock messages are captured. Untouched devices
must not contribute messages to `MockMidiSender`. The feature remains passive:
no MIDI imports, no port opening, no live SysEx receive, no SysEx writes, and no
hardware mutation.

## Success Criteria

- Default bridge behavior remains `both`.
- `--target rytm` emits only Analog Rytm mock messages.
- `--target analog-four` emits only Analog Four mock messages.
- Reports show active and untouched devices.
- Invalid targets are rejected through the existing passive error path.
