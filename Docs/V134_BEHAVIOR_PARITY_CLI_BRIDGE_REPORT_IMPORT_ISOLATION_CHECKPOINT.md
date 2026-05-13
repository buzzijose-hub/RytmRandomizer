# V1.34 Behavior Parity CLI Bridge Report Import Isolation Checkpoint

## 1. Purpose

Record the tiny CLI bridge report import-isolation refinement selected after
the accepted bridge safety coverage audit review.

This checkpoint records a safety-test refinement and a minimal
behavior-preserving CLI import isolation change.

It adds no active behavior, runtime execution, dispatch, command execution,
mutation execution, MIDI, ports, package metadata changes, or hardware
behavior.

## 2. Current Clean Baseline

Current branch:

- `modularize-v1.34`

Current HEAD before this checkpoint slice:

- `d2444fe Add CLI bridge report import isolation`

Private GitHub repository:

- `https://github.com/buzzijose-hub/RytmRandomizer`

Current phase:

- bridge safety coverage audit reviewed and accepted
- next branch selected as tiny test-only CLI bridge report import-isolation
  refinement
- import-isolation refinement implemented and verified

Hardware status:

- Analog Rytm MKII off
- Analog Four MKII off
- hardware not required

## 3. Implementation Milestone

Implementation milestone:

- `d2444fe Add CLI bridge report import isolation`

Files changed by the milestone:

- `rytm_randomizer/cli.py`
- `tests/test_cli.py`

No closeout script update was needed because `tests/test_cli.py` is already
covered by:

- `=== Test: Passive CLI ===`

## 4. What Changed

The passive CLI now lazy-loads these report formatters only when their commands
run:

- `format_mock_mapper_report`
- `format_active_boundary_report`

This keeps unrelated report imports from loading mock MIDI while running:

- `python -m rytm_randomizer.cli mock-runtime-active-bridge-report`

The visible CLI behavior remains unchanged.

The command still prints the existing formatted mock runtime/active bridge
report only.

## 5. New Safety Test

`tests/test_cli.py` now includes a subprocess-level import-isolation test for:

- `main(["mock-runtime-active-bridge-report"])`

The test confirms:

- command exits zero
- `rytm_randomizer.mock_runtime_active_bridge` is not loaded
- `rytm_randomizer.mock_midi` is not loaded
- `mido` is not loaded
- `rtmidi` is not loaded
- stdout is captured during the subprocess check
- stderr is empty

## 6. Red/Green Evidence

The first version of the new test failed because importing `rytm_randomizer.cli`
loaded `rytm_randomizer.mock_midi` through unrelated top-level report imports.

Root cause:

- `rytm_randomizer.cli` imported `mock_mapper_report` at module import time
- `mock_mapper_report` imported `mock_message_mapper`
- `mock_message_mapper` imported `mock_midi`
- `rytm_randomizer.cli` also imported `active_boundary_report` at module import
  time, which can reach the active boundary chain

Fix:

- lazy-load `mock_mapper_report` only inside the `mock-mapper-report` command
- lazy-load `active_boundary_report` only inside the `active-boundary-report`
  command

Focused green evidence:

- `python -m pytest tests/test_cli.py::test_mock_runtime_active_bridge_report_command_does_not_load_bridge_or_mock_midi -q`
- `python -m pytest tests/test_cli.py -q`
- `python tests\test_cli.py`

Full closeout also passed after the implementation.

## 7. Confirmed Preserved Behavior

Preserved behavior:

- `mock-runtime-active-bridge-report` output remains formatter-only
- `mock-runtime-active-bridge-report` does not invoke the bridge
- `mock-runtime-active-bridge-report` does not construct a sender
- `mock-runtime-active-bridge-report` emits no messages
- `mock-mapper-report` remains available
- `active-boundary-report` remains available
- passive CLI behavior remains read-only
- no fixtures changed
- no closeout script changed

## 8. Confirmed Still Absent

Still absent:

- real MIDI
- `mido`
- `rtmidi`
- MIDI port discovery
- MIDI port opening
- MIDI sending
- active CLI execution wiring
- bridge invocation from CLI
- sender construction from CLI
- message emission from CLI
- runtime execution
- dispatch
- command execution
- scene execution
- mutation execution
- `execute-command`
- `send-command`
- `hardware-test`
- hardware validation
- Analog Four support
- Pads 5-12 support
- SysEx
- GUI/capture
- package metadata changes
- hardware behavior

## 9. Verification

Verification completed:

- focused CLI import-isolation test passed
- full `tests/test_cli.py` pytest run passed
- direct `python tests\test_cli.py` run passed
- full closeout passed
- V1.34 reference diff was empty
- package metadata diff was empty
- `git diff --check` was clean except normal line-ending warnings before
  commit

## 10. Next Recommended Task

Create a docs-only review/acceptance gate for this checkpoint.

Do not add more CLI import-isolation changes unless a separate review selects
them.

Do not add real MIDI, ports, active behavior, or hardware behavior.

## 11. Decision

CLI bridge report import isolation checkpoint complete.

The selected tiny refinement is implemented and verified.

Hardware remains off.
