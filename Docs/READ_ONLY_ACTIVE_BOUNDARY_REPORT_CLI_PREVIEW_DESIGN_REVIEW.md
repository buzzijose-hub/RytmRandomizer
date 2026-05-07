# Read-Only Active Boundary Report CLI Preview Design Review

## 1. Purpose

Review and accept
`Docs/READ_ONLY_ACTIVE_BOUNDARY_REPORT_CLI_PREVIEW_DESIGN.md` as the current
planning gate for future passive CLI visibility of the read-only active
boundary report.

This is a documentation-only review gate.

No CLI command, implementation, real MIDI, port opening, active CLI behavior,
dispatch, or hardware behavior is added by this document.

## 2. Current Clean Baseline

Current branch:

- modularize-v1.34

Current HEAD before this slice:

- 8289003 Add read-only active boundary report CLI preview design

Current phase:

- Passive/Mock Foundation Phase
- first mock-first active boundary implemented
- read-only active boundary report implemented and reviewed
- active boundary report CLI preview design created
- active boundary report CLI preview design now being reviewed
- no real MIDI or hardware validation started

Hardware status:

- Analog Rytm MKII off
- Analog Four MKII off
- hardware not required

## 3. Review Decision

`Docs/READ_ONLY_ACTIVE_BOUNDARY_REPORT_CLI_PREVIEW_DESIGN.md` is accepted as
the current planning document for future passive CLI visibility of the
read-only active boundary report.

The review accepts the design as a planning gate only.

The design does not authorize active execution by itself.

The design does not authorize real MIDI, ports, dispatch, or hardware
validation.

## 4. Accepted Future CLI Command

Accepted future passive command shape:

```powershell
python -m rytm_randomizer.cli active-boundary-report
python -m rytm_randomizer.cli active-boundary-report --help
```

The future command must print:

- `format_active_boundary_report()` output only

The future command must exit `0` when printing the report.

The future command should add no options beyond `--help` in the first
implementation slice.

## 5. Accepted Future File Ownership

Accepted future file ownership:

- `rytm_randomizer/cli.py`
- `tests/test_cli.py`

Accepted future fixtures:

- `tests/fixtures/cli_active_boundary_report_help_expected.txt`
- `tests/fixtures/cli_active_boundary_report_expected.txt`
- `tests/fixtures/cli_help_expected.txt`

No `Scripts/closeout_check.ps1` update should be needed because
`tests/test_cli.py` is already part of closeout.

## 6. Accepted Future Test Scope

Accepted future CLI tests should verify:

- importing `rytm_randomizer.cli` prints nothing
- top-level CLI help lists `active-boundary-report`
- `active-boundary-report --help` exits `0`
- `active-boundary-report --help` matches a deterministic fixture
- `active-boundary-report` exits `0`
- `active-boundary-report` matches a deterministic fixture
- repeated report runs are deterministic
- report output shows profile `"2"` as the accepted active-boundary candidate
- report output shows profile `"3"` unsupported by the active boundary
- report output shows profile `"4"` parked and unsupported
- report output shows arming and dry-run confirmation are required
- report output shows real MIDI absent
- report output shows ports absent
- report output shows active CLI behavior absent
- report output shows hardware not required
- no real MIDI library is imported
- no ports are opened
- no MIDI is sent
- no active boundary requests are evaluated
- no mock messages are emitted
- passive CLI behavior remains unchanged
- V1.34 reference remains untouched
- no profile `"4"` support is added
- no profile `"3"` active-boundary support is added

## 7. Existing Passive CLI Commands Must Remain Passive

Existing passive CLI commands must keep working unchanged:

- `python -m rytm_randomizer.cli --help`
- `python -m rytm_randomizer.cli report`
- `python -m rytm_randomizer.cli list-commands`
- `python -m rytm_randomizer.cli list-scenes`
- `python -m rytm_randomizer.cli list-group-profiles`
- `python -m rytm_randomizer.cli search-commands <query>`
- `python -m rytm_randomizer.cli search-scenes <query>`
- `python -m rytm_randomizer.cli search-group-profiles <query>`
- `python -m rytm_randomizer.cli inspect-command <key>`
- `python -m rytm_randomizer.cli inspect-scene <key>`
- `python -m rytm_randomizer.cli inspect-group-profile <key>`
- `python -m rytm_randomizer.cli preview-command <key>`
- `python -m rytm_randomizer.cli preview-scene <key>`
- `python -m rytm_randomizer.cli preview-group-profile <key>`
- `python -m rytm_randomizer.cli mock-mapper-report`

None of these may reach active execution or hardware behavior.

## 8. Required Boundary For Future Implementation

The future CLI preview must:

- remain passive/read-only
- print deterministic human-readable report text
- print nothing during import
- write no files
- require no hardware
- open no MIDI ports
- send no MIDI
- dispatch no commands
- execute no commands
- evaluate no active boundary requests
- emit no mock messages
- mutate no runtime or hardware state
- add no active behavior

## 9. Confirmed Absent Behavior

This review confirms there is still no:

- real MIDI
- mido
- MIDI port opening
- MIDI sending
- hardware detection
- hardware send
- active CLI command
- active execution
- CLI wiring to active behavior
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

## 10. Preconditions Before Future CLI Implementation

Before any future CLI implementation:

- Git status must be clean
- closeout must pass
- V1.34 reference diff must be empty
- this design review must remain accepted
- `READ_ONLY_ACTIVE_BOUNDARY_REPORT_REVIEW.md` must remain accepted
- passive CLI must remain read-only
- the command must print formatted report output only
- no active boundary request evaluation may occur
- no mock messages may be emitted
- real MIDI must remain absent
- ports must remain closed
- hardware must remain off
- profile `"4"` must remain parked unless separately approved
- profile `"3"` must remain unsupported by the active boundary unless separately approved

## 11. Safe Next Options

Safe next options:

- pause at this clean design review checkpoint
- implement the read-only active boundary report CLI preview
- write a broader project-level progress checkpoint
- keep active planning frozen and return to passive/project documentation

Unsafe next moves:

- adding real MIDI
- opening ports
- adding active CLI commands
- wiring passive CLI to active execution
- turning on hardware
- implementing profile `"4"` without separate approval
- adding profile `"3"` active-boundary support without separate approval

## 12. Recommendation

Proceed next only with the tiny fixture-backed CLI preview if more operator
visibility is useful.

The future implementation should display `format_active_boundary_report()`
output only.

Do not add real MIDI.

Do not open ports.

Do not add active CLI commands.

Do not turn on hardware.

## 13. Decision

The read-only active boundary report CLI preview design is accepted as the
current planning gate.

Hardware remains off.

No implementation is added in this slice.
