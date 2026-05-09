# V1.34 Behavior Parity Packet 2C Anchor/Profile Plan

## Purpose

Define the next tiny anchor/profile behavior implementation packet after
Packet 2B.

Packet 2C is planning-only. It does not add implementation, tests, runtime
behavior, CLI wiring, command dispatch, command execution, scene execution,
real MIDI, port opening, package metadata, active CLI behavior, or hardware
behavior.

## Current Clean Baseline

Current branch:

- modularize-v1.34

Current HEAD before this slice:

- a254933 Add Packet 2B anchor profile review

Current phase:

- Passive/Mock Foundation Phase
- Packet 1 complete for the current intent-only behavior phase
- Packet 2A anchor/profile behavior implemented and accepted
- Packet 2B anchor/profile behavior implemented and accepted
- Packet 2C anchor/profile behavior planning now begins

Hardware status:

- Analog Rytm MKII off
- Analog Four MKII off
- hardware not required

## Accepted Planning Sources

This packet plan is grounded in:

- `Docs/V134_BEHAVIOR_PARITY_PACKET_2_ANCHOR_PROFILE_PLAN.md`
- `Docs/V134_BEHAVIOR_PARITY_PACKET_2_ANCHOR_PROFILE_PLAN_REVIEW.md`
- `Docs/V134_BEHAVIOR_PARITY_PACKET_2B_ANCHOR_PROFILE_REVIEW.md`
- accepted passive command metadata in `rytm_randomizer/commands.py`
- protected V1.34 reference as behavior reference only

The protected V1.34 reference remains read-only and untouched.

## Packet Identity

Packet name:

- Packet 2C: Anchor/Profile Behavior Parity

Packet intent:

- add one more deterministic read-only Pad 1 anchor-load intent
- keep profile `"4"` / My BD Acoustic parked for now
- prove the anchor/profile helper can add another non-profile-4 Pad 1 anchor
  without inventing group-profile metadata
- preserve the current no-MIDI, no-port, no-dispatch safety boundary

## Recommended Packet 2C Implementation Scope

Recommended Packet 2C scope:

- `BF`

Packet 2C should model only deterministic read-only Pad 1 anchor/profile load
intent for:

- `BF`: load Pad 1 BD FM profiled anchor

Reasons for this tiny scope:

- `BF` is an existing Pad 1 anchor-load command
- it does not require selected-profile state
- it does not require profile rotation
- it does not require multi-pad group behavior
- it avoids profile `"4"` / BD Acoustic for now
- it extends the same absent-profile-metadata pattern proven by `BS`
- it keeps the write set limited to one behavior module and one test file

## Existing Metadata Boundary

Existing passive command metadata for `BF` is captured in
`rytm_randomizer/commands.py:PAD1_COMMANDS`.

Existing group-profile metadata currently covers:

- `"2"` / My BD Hard
- `"3"` / My BD Classic
- `"4"` / My BD Acoustic
- `"5"` / Pad 3 SY Raw Mid Bass

There is no existing group-profile key for Pad 1 BD FM.

Packet 2C must not invent a new group-profile key, machine value, profile
name, group-profile entry, or machine/profile universe expansion for BD FM.

Future `BF` behavior should use deterministic safe absent values for
profile-specific fields, such as:

- `profile_key`: empty string
- `machine_value`: `None`

The result metadata should clearly record that group-profile metadata is
absent instead of invented.

## Profile 4 Position

Profile `"4"` / My BD Acoustic remains parked.

Packet 2C does not plan `BA`.

Reasons:

- profile `"4"` remains useful as an unsupported/safe boundary
- `BA` touches the parked BD Acoustic/profile-4 area
- existing group profile `"4"` is associated with group pad `4`, while `BA`
  is a Pad 1 command
- that mismatch deserves a separate decision/review before any behavior helper
  support is added

Any future `BA` support must be separately approved in its own tiny
documentation slice.

## Deferred Packet 2 Scope

Defer these areas until separately reviewed:

- `P` and `M` selected profile workflow
- `O` and `Z` full four-pad group anchor load/return
- rotations: `BR`, `P2R`, `P3R`, and `P4R`
- Pad 2 anchor/profile commands
- selected isolated pad anchor return
- Pad 3 mode and anchor commands
- Pad 4 anchor/profile commands
- Pad 1 profile `"4"` / BD Acoustic command `BA`
- BD FM return and discovery commands: `FZ`, `FT`, `FK`, and `FG`
- BD Plastic anchors, returns, and discovery commands: `BP`, `PBH`, `PT`,
  `PK`, and `PX`
- BD Silky anchors, returns, and discovery commands: `BI`, `SBH`, `ST`, `SK`,
  and `SC`

## Proposed Future File Ownership

If Packet 2C is implemented later, accepted ownership is:

- modify `rytm_randomizer/behavior_anchor_profile.py`
- modify `tests/test_behavior_anchor_profile.py`

No closeout script update is expected because `tests/test_behavior_anchor_profile.py`
is already covered by:

- `=== Test: Behavior Anchor Profile ===`

Do not edit:

- `rytm_hybrid_randomizer_v134.py`
- `rytm_randomizer/cli.py`
- `rytm_randomizer/mock_midi.py`
- `rytm_randomizer/mock_message_mapper.py`
- `rytm_randomizer/mock_mapper_report.py`
- real MIDI adapter files
- package metadata files
- runtime execution or dispatch logic

## Expected Future Packet 2C Semantics

For `BF`:

- behavior family should remain `anchor/profile`
- result should describe anchor/profile intent only
- target pad should be `1`
- anchor name should be `BD FM`
- profile key should be an empty string
- machine value should be `None`
- metadata should record `source: PAD1_COMMANDS`
- metadata should record that group-profile metadata is absent
- no prompt should run
- no state should change
- no command should dispatch
- no command should execute
- no scene should execute
- no MIDI should be sent
- no ports should open
- no hardware should be required
- no active behavior should exist

Existing `BH`, `BS`, and `BC` behavior must remain unchanged.

## Required Future Tests

Packet 2C tests should prove:

- `BH` behavior remains unchanged
- `BS` behavior remains unchanged
- `BC` behavior remains unchanged
- `BF` returns deterministic read-only Pad 1 BD FM anchor intent
- `BF` uses no invented profile key
- `BF` uses no invented machine value
- `BF` metadata records absent group-profile metadata safely
- accepted results expose no state mutation, prompts, ports, MIDI, hardware,
  dispatch, execution, or active behavior
- repeated evaluations are deterministic
- unknown keys still fail safely
- deferred keys still remain unsupported/safe
- `BA` and profile `"4"` remain parked
- passive CLI behavior remains unchanged
- no real MIDI library is imported
- no package metadata files are introduced
- V1.34 reference remains untouched
- no Pads 5-12 support is exposed
- no Analog Four support is exposed

## Parallelization Decision

Do not parallelize the immediate Packet 2C implementation.

Reason:

- the write set is one behavior module and one test file
- the change extends the same small result shape and absent-metadata pattern
- serial implementation is safer than splitting a tiny behavior change

Parallel work can be reconsidered after Packet 2C is implemented, reviewed,
and accepted.

## Work Not Authorized By This Plan

This plan does not authorize:

- implementation
- tests
- runtime behavior changes
- CLI wiring
- command dispatch
- command execution
- scene execution
- prompt/input loop execution
- selected profile state
- profile rotation
- full group anchor loading
- profile `"4"` implementation
- `BA` behavior support
- new group-profile metadata
- machine/profile universe expansion
- real MIDI dependency
- `mido`
- `rtmidi`
- package metadata changes
- MIDI port discovery
- MIDI port opening
- MIDI sending
- active CLI commands
- `execute-command`
- `send-command`
- `hardware-test`
- hardware behavior
- hardware validation
- Analog Four support
- Pads 5-12 support
- SysEx
- GUI/capture

## Stop Conditions For Future Implementation

Stop immediately if:

- implementation scope expands beyond `BF`
- `BA` or profile `"4"` implementation slips in
- any new profile metadata is introduced for BD FM
- any machine/profile universe expansion appears
- any real MIDI import appears
- any package metadata file appears
- any port-opening behavior appears
- any command dispatch or execution appears
- any passive CLI behavior changes unexpectedly
- any V1.34 reference diff appears
- any Analog Four or Pads 5-12 scope appears

## Next Safe Options

After this plan:

- review and accept this Packet 2C plan
- pause at this planning checkpoint
- if accepted, implement only Packet 2C for `BF`

## Recommendation

Review and accept this plan.

Then implement only Packet 2C:

- read-only anchor/profile intent for `BF`

Hardware remains off.

## Decision

Packet 2C anchor/profile behavior is planned.

No implementation is added in this slice.
