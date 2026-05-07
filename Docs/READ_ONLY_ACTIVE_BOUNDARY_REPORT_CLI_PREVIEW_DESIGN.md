# Read-Only Active Boundary Report CLI Preview Design

## 1. Purpose

Define a future passive CLI preview command for the read-only active boundary
report.

This is a documentation-only design.

It does not implement a CLI command, modify CLI behavior, evaluate active
requests, send MIDI, open ports, dispatch commands, or touch hardware.

## 2. Current Clean Baseline

Current branch:

- modularize-v1.34

Current HEAD before this slice:

- 7029d9f Add read-only active boundary report review

Current phase:

- Passive/Mock Foundation Phase
- first mock-first active boundary implemented
- read-only active boundary report implemented and reviewed
- active boundary report CLI preview now being designed
- no real MIDI or hardware validation started

Hardware status:

- Analog Rytm MKII off
- Analog Four MKII off
- hardware not required

## 3. Current Report Module

The accepted read-only report module is:

- `rytm_randomizer.active_boundary_report`

Accepted functions:

- `build_active_boundary_report()`
- `format_active_boundary_report(report=None)`
- `summarize_active_boundary_report(report=None)`

The report is:

- read-only
- in-memory
- deterministic
- mutation-safe through copied data
- not wired to CLI
- not wired to MIDI
- not hardware-facing

## 4. Proposed Future CLI Command

Documented as design only:

```powershell
python -m rytm_randomizer.cli active-boundary-report
python -m rytm_randomizer.cli active-boundary-report --help
```

The command should print formatted report output only.

The command should call:

- `format_active_boundary_report()`

The command should exit `0` when printing the report.

The command should add no options beyond `--help` in the first slice.

## 5. Required CLI Behavior

The future command must:

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

## 6. Existing CLI Commands Must Remain Passive

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

## 7. Proposed Future File Ownership

Documented as design only:

- `rytm_randomizer/cli.py`
- `tests/test_cli.py`

Possible future fixtures:

- `tests/fixtures/cli_active_boundary_report_help_expected.txt`
- `tests/fixtures/cli_active_boundary_report_expected.txt`
- `tests/fixtures/cli_help_expected.txt`

No file is changed by this design except documentation.

## 8. Future Test Requirements

Future CLI tests should verify:

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

## 9. Relationship To Active Boundary Report

The CLI preview should display the existing report only.

It should not duplicate report construction logic inside `cli.py`.

It should reuse:

- `format_active_boundary_report()`

The active boundary report module remains the source of report formatting.

## 10. Forbidden Scope

This design does not authorize:

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

## 11. Preconditions Before Future CLI Implementation

Before any future implementation:

- Git status must be clean
- closeout must pass
- V1.34 reference diff must be empty
- this design must be reviewed and accepted
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

## 12. Safe Next Options

Safe next options:

- review and accept this CLI preview design
- pause at this clean design checkpoint
- implement the read-only CLI preview only after review
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

## 13. Recommendation

Review and accept this design before any CLI implementation.

This design is accepted by:

- `Docs/READ_ONLY_ACTIVE_BOUNDARY_REPORT_CLI_PREVIEW_DESIGN_REVIEW.md`

If accepted, the future implementation should be tiny, fixture-backed, and
limited to displaying `format_active_boundary_report()` output.

Do not add real MIDI.

Do not open ports.

Do not add active CLI commands.

Do not turn on hardware.

## 14. Decision

The active boundary report CLI preview is designed as a future passive
visibility command.

Hardware remains off.

No implementation is added in this slice.
