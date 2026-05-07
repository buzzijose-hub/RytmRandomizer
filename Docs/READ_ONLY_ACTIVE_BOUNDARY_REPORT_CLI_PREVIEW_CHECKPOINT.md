# Read-Only Active Boundary Report CLI Preview Checkpoint

## 1. Purpose

Record completion of the tiny read-only active boundary report CLI preview
slice.

This checkpoint documents the new passive CLI visibility command, its
fixture-backed tests, and the closeout result.

This document is documentation-only.

## 2. Current Clean Baseline

Current branch:

- modularize-v1.34

Current HEAD before this documentation slice:

- 1f14769 Add read-only active boundary report CLI preview

Current phase:

- Passive/Mock Foundation Phase
- first mock-first active boundary implemented
- read-only active boundary report implemented and reviewed
- read-only active boundary report CLI preview implemented
- no real MIDI or hardware validation started

Hardware status:

- Analog Rytm MKII off
- Analog Four MKII off
- hardware not required

## 3. Milestone

New milestone:

- read-only active boundary report CLI preview

Commit:

- 1f14769 Add read-only active boundary report CLI preview

Files changed by the milestone:

- `rytm_randomizer/cli.py`
- `tests/test_cli.py`
- `tests/fixtures/cli_help_expected.txt`
- `tests/fixtures/cli_active_boundary_report_help_expected.txt`
- `tests/fixtures/cli_active_boundary_report_expected.txt`

No closeout script update was needed because `tests/test_cli.py` is already
part of closeout.

## 4. CLI Paths Added

New passive CLI paths:

```powershell
python -m rytm_randomizer.cli active-boundary-report
python -m rytm_randomizer.cli active-boundary-report --help
```

The command prints the existing formatted read-only active boundary report.

It calls:

- `format_active_boundary_report()`

## 5. Behavior Added

The command prints deterministic report output showing:

- group profile `"2"` / My BD Hard as the accepted active-boundary candidate
- group profile `"3"` / My BD Classic as unsupported by the active boundary
- group profile `"4"` / My BD Acoustic as parked and unsupported
- explicit arming required
- dry-run confirmation required
- injected `MockMidiSender` required for the mock boundary
- mock-only status
- hardware not required
- real MIDI absent
- port opening absent
- active CLI behavior absent
- dispatch absent
- command execution absent
- scene execution absent
- hardware behavior absent
- closeout coverage

The command exits `0` for the report and help output.

## 6. Tests Added

The milestone updates:

- `tests/test_cli.py`

The tests verify:

- top-level CLI help lists `active-boundary-report`
- `active-boundary-report --help` exits `0` and matches a fixture
- `active-boundary-report` exits `0` and matches a fixture
- repeated report runs are deterministic
- the command imports no real MIDI libraries
- unknown `active-boundary-report` arguments fail safely with usage
- the output exposes no active behavior or support expansion
- profile `"2"` is reported as the accepted active-boundary candidate
- profile `"3"` remains unsupported by the active boundary
- profile `"4"` remains parked and unsupported
- real MIDI, ports, active CLI behavior, dispatch, execution, and hardware
  behavior remain absent

## 7. TDD Verification

Red step:

```powershell
python .\tests\test_cli.py
```

Result before implementation:

- failed because top-level CLI help did not yet match the new
  `active-boundary-report` fixture contract

Green step:

```powershell
python .\tests\test_cli.py
```

Result after implementation:

- passed

## 8. Manual Verification

Manual CLI checks were run:

```powershell
python -m rytm_randomizer.cli --help
python -m rytm_randomizer.cli active-boundary-report --help
python -m rytm_randomizer.cli active-boundary-report
```

Manual output confirmed:

- top-level help lists `active-boundary-report`
- command help prints passive/read-only usage
- report output shows profile `"2"` as the accepted active-boundary candidate
- report output shows profiles `"3"` and `"4"` unsupported by the active
  boundary
- report output shows real MIDI absent
- report output shows port opening absent
- report output shows active CLI behavior absent
- report output shows hardware not required

## 9. Behavior Not Added

This milestone does not add:

- active request evaluation from CLI
- mock message emission from CLI
- real MIDI
- mido
- MIDI port opening
- MIDI sending
- hardware detection
- hardware send
- active CLI command
- active execution
- dispatch
- command execution
- scene execution
- hardware behavior
- SysEx
- GUI/capture
- Analog Four support
- Pads 5-12 support
- machine/profile expansion
- execute-command
- send-command
- hardware-test
- hardware validation
- profile `"4"` implementation
- profile `"3"` active-boundary support

## 10. Verification

Full closeout:

```powershell
powershell -ExecutionPolicy Bypass -File .\Scripts\closeout_check.ps1
```

Result:

- passed

V1.34 reference diff:

- empty

Git status after commit:

- clean

## 11. What This Means

The project can now view the read-only active boundary report from PowerShell
through the passive CLI.

This improves operator visibility without evaluating active requests, emitting
mock messages, opening ports, sending MIDI, dispatching commands, executing
commands, or touching hardware.

## 12. Review Status

The design accepted before implementation is:

- `Docs/READ_ONLY_ACTIVE_BOUNDARY_REPORT_CLI_PREVIEW_DESIGN_REVIEW.md`

The completed CLI preview is accepted in:

- `Docs/READ_ONLY_ACTIVE_BOUNDARY_REPORT_CLI_PREVIEW_REVIEW.md`

The next recommended task is either a pause at this clean review checkpoint or
a broader documentation-only read-only active boundary visibility progress
report.

Hardware remains off.

## 13. Decision

The read-only active boundary report CLI preview is complete and
closeout-protected.

Hardware remains off.

No real MIDI, ports, active execution, dispatch, command execution, scene
execution, or hardware behavior exists.
