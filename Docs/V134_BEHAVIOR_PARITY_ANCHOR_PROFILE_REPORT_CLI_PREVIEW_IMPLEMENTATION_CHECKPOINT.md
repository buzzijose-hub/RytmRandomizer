# V1.34 Behavior Parity Anchor/Profile Report CLI Preview Implementation Checkpoint

## 1. Purpose

Record the passive anchor/profile behavior report CLI preview implementation
milestone.

This checkpoint documents what changed, what is now visible from the CLI, what
tests were added, and what remains intentionally absent.

This checkpoint is documentation-only.

## 2. Current Clean Baseline

Current branch:

- `modularize-v1.34`

Current HEAD before this slice:

- `0e3de07 Add passive anchor profile report CLI preview`

Current phase:

- passive/mock foundation
- V1.34 behavior-parity implementation packets
- read-only anchor/profile behavior report implemented
- CLI visibility decision note reviewed and accepted
- passive anchor/profile report CLI preview implemented

Hardware status:

- Analog Rytm MKII off
- Analog Four MKII off
- hardware not required

## 3. Milestone

New milestone:

- passive anchor/profile report CLI preview

New commit:

- `0e3de07 Add passive anchor profile report CLI preview`

Files changed by the milestone:

- `rytm_randomizer/cli.py`
- `rytm_randomizer/behavior_anchor_profile_report.py`
- `tests/test_cli.py`
- `tests/test_behavior_anchor_profile_report.py`
- `tests/fixtures/cli_help_expected.txt`
- `tests/fixtures/cli_anchor_profile_report_expected.txt`
- `tests/fixtures/cli_anchor_profile_report_help_expected.txt`

No closeout script update was needed because `tests/test_cli.py` and
`tests/test_behavior_anchor_profile_report.py` are already included in
closeout.

## 4. New Passive CLI Command

New command:

- `python -m rytm_randomizer.cli anchor-profile-report`

New help command:

- `python -m rytm_randomizer.cli anchor-profile-report --help`

Top-level help now lists:

- `anchor-profile-report`

The command prints the existing formatted read-only anchor/profile behavior
report only.

## 5. Behavior Added

The CLI preview:

- imports the anchor/profile report formatter
- prints deterministic report output
- exits successfully for the report command
- exits successfully for the help command
- keeps existing passive CLI commands unchanged
- remains formatter-only
- remains passive/read-only

The report safety wording now distinguishes:

- `passive_cli_visibility: present`
- `active_cli_wiring: absent`

This makes the milestone explicit: passive visibility exists, but active CLI
wiring does not.

## 6. Current Report Visibility

The CLI report shows existing read-only coverage for:

- direct Packet 2 anchor/profile behavior:
  - `BH`
  - `BC`
  - `BS`
  - `BF`
- Pad 1 lane anchor/profile intent:
  - `FZ`
  - `BP`
  - `PBH`
  - `BI`
  - `SBH`
  - `BA`
- Pad 2 lane anchor/profile intent:
  - `P2B`
  - `P2H`
  - `P2C`
  - `P2F`
  - `P2Z`
- Pad 3 anchor intent:
  - `P3A`
  - `SA`
- Pad 4 anchor intent:
  - `P4A`
- group anchor intent:
  - `O`
  - `Z`
- current-anchor state intent:
  - `B`
  - `E`
- selected-profile workflow intent:
  - `P`
  - `M`
- selected isolated pad target intent:
  - `L`

## 7. Parked Scope Preserved

Parked/safe scope remains:

- `PZ`
- group profile `4` mock mapper support

`PZ` remains selected isolated pad anchor-return scope that requires a separate
decision before implementation.

Profile `4` remains mock mapper support that requires separate approval before
implementation.

## 8. Tests Updated

CLI tests now verify:

- top-level help lists `anchor-profile-report`
- `anchor-profile-report --help` matches a deterministic fixture
- `anchor-profile-report` matches a deterministic fixture
- the command is deterministic across repeated runs
- unknown `anchor-profile-report` arguments fail safely
- the command imports no real MIDI libraries
- the command exposes parked `PZ`
- the command exposes parked group profile `4`
- the command exposes no active behavior or support expansion

Anchor/profile report tests now verify:

- passive CLI visibility is present
- active CLI wiring remains absent
- existing passive registry report behavior remains unchanged
- no active command names appear in the report output

## 9. TDD Note

The CLI tests and fixtures were added before the CLI implementation.

Initial RED result:

- `tests/test_cli.py` failed because the CLI did not yet expose
  `anchor-profile-report`.

GREEN result:

- after adding the formatter-only CLI command, focused CLI tests passed

Integration fix:

- full closeout first surfaced stale report tests that still asserted no CLI
  visibility
- those tests were updated to distinguish passive CLI visibility from active
  CLI wiring
- full closeout passed after that correction

## 10. Confirmed Absent Behavior

This milestone adds no:

- active CLI command
- `execute-command`
- `send-command`
- `hardware-test`
- dispatch
- command execution
- scene execution
- mutation execution
- runtime state
- direct behavior helper execution from CLI
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

## 11. Closeout Result

Closeout passed after the milestone.

Protected checks:

- V1.34 reference diff was empty
- package metadata diff was empty
- git status was clean

## 12. Safe Next Options

Safe next options:

- docs-only review/acceptance gate for this CLI preview implementation
  checkpoint
- broader behavior-parity progress/timeline update
- pause at this clean checkpoint

## 13. Recommendation

Review and accept this implementation checkpoint next.

Do not implement `PZ`.

Do not add profile `4` mock mapper support.

Do not add MIDI, ports, active behavior, runtime execution, package metadata
changes, or hardware behavior.

## 14. Decision

The passive anchor/profile report CLI preview implementation milestone is
documented.

The next recommended task is a docs-only review/acceptance gate for this
implementation checkpoint.

Hardware remains off.
