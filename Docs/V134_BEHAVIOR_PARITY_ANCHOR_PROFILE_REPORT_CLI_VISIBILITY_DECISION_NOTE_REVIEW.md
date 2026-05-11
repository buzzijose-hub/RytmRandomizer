# V1.34 Behavior Parity Anchor/Profile Report CLI Visibility Decision Note Review

## 1. Purpose

Review and accept the anchor/profile behavior report CLI visibility decision
note.

This is a review checkpoint only.

It does not implement CLI behavior.

## 2. Current Clean Baseline

Current branch:

- `modularize-v1.34`

Current HEAD before this slice:

- `2538190 Add anchor profile report CLI visibility decision`

Current phase:

- passive/mock foundation
- V1.34 behavior-parity implementation packets
- read-only anchor/profile behavior report implemented
- anchor/profile behavior report checkpoint reviewed and accepted
- CLI visibility decision note created
- CLI visibility decision note now being reviewed

Hardware status:

- Analog Rytm MKII off
- Analog Four MKII off
- hardware not required

## 3. Review Decision

Accepted decision note:

- `Docs/V134_BEHAVIOR_PARITY_ANCHOR_PROFILE_REPORT_CLI_VISIBILITY_DECISION_NOTE.md`

Accepted decision note milestone:

- `2538190 Add anchor profile report CLI visibility decision`

The CLI visibility decision note is accepted as the current planning baseline.

This review does not authorize implementation by itself.

## 4. Accepted Future CLI Visibility

Accepted future command:

- `python -m rytm_randomizer.cli anchor-profile-report`

Accepted future help command:

- `python -m rytm_randomizer.cli anchor-profile-report --help`

The future command may print only the existing formatted read-only
anchor/profile behavior report.

The future command must be formatter-only, passive, and read-only.

## 5. Accepted Future Implementation Scope

A future implementation slice may update:

- `rytm_randomizer/cli.py`
- `tests/test_cli.py`
- deterministic CLI fixtures as needed

The closeout script should not need changes if `tests/test_cli.py` already
covers the new command.

Any future implementation must keep existing passive CLI behavior unchanged.

## 6. Accepted Future Test Expectations

Future tests should prove:

- importing `rytm_randomizer.cli` prints nothing
- top-level help lists `anchor-profile-report`
- `anchor-profile-report --help` prints deterministic passive help
- `anchor-profile-report` prints deterministic report output
- output includes the supported report scope
- output shows `PZ` parked
- output shows group profile `4` parked
- existing passive CLI behavior remains unchanged
- no real MIDI library is imported
- no ports are opened
- no MIDI is sent
- no active behavior is introduced
- V1.34 reference remains untouched
- package metadata remains untouched

## 7. Confirmed Forbidden Behavior

The future CLI command must not:

- call behavior helpers directly
- create runtime state
- switch selected pads
- return selected pads to anchors
- execute anchors
- execute profiles
- mutate anything
- call mock message mapping
- open ports
- send MIDI
- add active behavior
- require hardware

## 8. Confirmed Absent Behavior In This Slice

This review adds no:

- CLI command
- CLI fixture
- CLI test
- active CLI command
- `execute-command`
- `send-command`
- `hardware-test`
- dispatch
- command execution
- scene execution
- mutation execution
- runtime state
- selected pad switching execution
- selected pad anchor return execution
- `PZ` implementation
- profile `4` mock mapper support
- real MIDI dependency
- `mido`
- `rtmidi`
- port discovery
- port opening
- MIDI sending
- hardware behavior
- hardware validation
- SysEx
- GUI/capture
- Analog Four support
- Pads 5-12 support
- package metadata changes
- machine/profile universe expansion

`rytm_hybrid_randomizer_v134.py` remains untouched.

Package metadata remains untouched.

## 9. Parked Scope

Parked scope remains:

- `PZ`
- group profile `4` mock mapper support

`PZ` remains selected isolated pad anchor-return scope that requires a separate
decision before implementation.

Profile `4` remains mock mapper support that requires separate approval before
implementation.

## 10. Preconditions Before Future CLI Implementation

Before implementing passive CLI visibility:

- clean Git status
- full closeout passing
- V1.34 reference diff empty
- package metadata diff empty
- this review accepted
- CLI command remains formatter-only
- CLI command prints only the formatted report
- no runtime state introduced
- no direct helper execution introduced
- no mock message mapping invoked
- no MIDI, ports, active behavior, or hardware behavior introduced

## 11. Safe Next Options

Safe next options:

- implement passive CLI visibility for the anchor/profile behavior report with
  focused tests
- broader progress/timeline update
- pause at this clean checkpoint

## 12. Recommendation

Implement the passive CLI visibility command in a tiny formatter-only slice.

Do not implement `PZ`.

Do not add profile `4` mock mapper support.

Do not add MIDI, ports, active behavior, runtime execution, package metadata
changes, or hardware behavior.

## 13. Decision Summary

The anchor/profile behavior report CLI visibility decision note is accepted.

The next recommended task is a tiny passive CLI visibility implementation.

Hardware remains off.

No implementation in this slice.
