# V1.34 Behavior Parity Anchor/Profile Report CLI Visibility Decision Note

## 1. Purpose

Decide whether the read-only anchor/profile behavior report should be exposed
through a future passive CLI command.

This is a decision note only.

It does not implement CLI behavior.

## 2. Current Clean Baseline

Current branch:

- `modularize-v1.34`

Current HEAD before this slice:

- `db90dfb Add anchor profile report checkpoint review`

Current phase:

- passive/mock foundation
- V1.34 behavior-parity implementation packets
- read-only anchor/profile behavior report implemented
- anchor/profile behavior report checkpoint reviewed and accepted
- CLI visibility decision now being documented

Hardware status:

- Analog Rytm MKII off
- Analog Four MKII off
- hardware not required

## 3. Current Report Status

The read-only anchor/profile behavior report exists:

- `rytm_randomizer/behavior_anchor_profile_report.py`

Focused test coverage exists:

- `tests/test_behavior_anchor_profile_report.py`

Closeout includes:

- `=== Test: Behavior Anchor Profile Report ===`

The report remains deterministic, in-memory, copied/mutation-safe, and
side-effect free on import.

## 4. Decision

Approve a future passive CLI visibility slice for the anchor/profile behavior
report.

The future CLI command should be read-only and formatter-only.

Likely command name:

- `python -m rytm_randomizer.cli anchor-profile-report`

Likely help command:

- `python -m rytm_randomizer.cli anchor-profile-report --help`

This decision note does not implement those commands.

## 5. Accepted Future CLI Behavior

A future CLI visibility slice may:

- import the report formatter only
- print the existing formatted anchor/profile behavior report
- update top-level passive CLI help
- add deterministic fixture-backed CLI tests
- keep existing passive commands unchanged
- exit successfully for the report command and help command

The future CLI command must remain passive and read-only.

## 6. Forbidden Future CLI Behavior

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

## 7. Report Scope To Expose

The future CLI command may expose the existing formatted report covering:

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
- parked/safe scope:
  - `PZ`
  - group profile `4` mock mapper support

## 8. Confirmed Absent Behavior In This Slice

This decision note adds no:

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

## 9. Preconditions Before Future CLI Implementation

Before implementing the passive CLI visibility slice:

- clean Git status
- full closeout passing
- V1.34 reference diff empty
- package metadata diff empty
- this decision note committed
- existing report checkpoint review accepted
- CLI command remains formatter-only
- no runtime state introduced
- no direct helper execution introduced
- no mock message mapping invoked
- no MIDI, ports, active behavior, or hardware behavior introduced

## 10. Future Test Expectations

Future CLI tests should prove:

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

## 11. Safe Next Options

Safe next options:

- implement passive CLI visibility for the anchor/profile behavior report with
  focused tests
- create a review/acceptance gate for this decision note first
- follow-up review gate:
  - `Docs/V134_BEHAVIOR_PARITY_ANCHOR_PROFILE_REPORT_CLI_VISIBILITY_DECISION_NOTE_REVIEW.md`
- broader progress/timeline update
- pause at this clean checkpoint

## 12. Recommendation

Create a short review/acceptance gate for this decision note next.

Then, if accepted, implement the passive CLI visibility command in a tiny
formatter-only slice.

Do not implement `PZ`.

Do not add profile `4` mock mapper support.

Do not add MIDI, ports, active behavior, runtime execution, package metadata
changes, or hardware behavior.

## 13. Decision Summary

Future passive CLI visibility is approved for planning.

No CLI behavior is implemented in this slice.

The next recommended task is a docs-only review/acceptance gate for this
decision note.

Hardware remains off.
