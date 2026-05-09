# V1.34 Behavior Parity Packet 2 Anchor/Profile Plan Review

## Purpose

Review and accept
`Docs/V134_BEHAVIOR_PARITY_PACKET_2_ANCHOR_PROFILE_PLAN.md` as the current
planning gate for the next tiny behavior-parity implementation packet.

This review is documentation-only. It adds no implementation, tests, runtime
behavior, command dispatch, scene execution, MIDI, port opening, active CLI
command, package metadata change, or hardware behavior.

## Current Clean Baseline

Current branch:

- modularize-v1.34

Current HEAD before this slice:

- 7b3fe8c Add Packet 1 completion checkpoint review

Current phase:

- Passive/Mock Foundation Phase
- Packet 1 accepted as complete for the current intent-only behavior phase
- Packet 2 anchor/profile behavior plan created
- Packet 2 anchor/profile behavior plan now being reviewed

Hardware status:

- Analog Rytm MKII off
- Analog Four MKII off
- hardware not required

## Review Decision

`Docs/V134_BEHAVIOR_PARITY_PACKET_2_ANCHOR_PROFILE_PLAN.md` is accepted as the
current Packet 2 planning gate.

The plan remains planning-only.

The plan does not authorize broad behavior parity implementation by itself.

The plan does not authorize turning hardware on by itself.

## Accepted Packet Identity

Accepted packet:

- Packet 2: Anchor/Profile Behavior Parity

Accepted packet intent:

- model anchor/profile load, return, and selection intent as deterministic
  read-only behavior before any real execution exists
- preserve the current no-MIDI, no-port, no-dispatch safety boundary
- keep future active behavior separate from this intent-only layer

## Accepted Full Planning Scope

The review accepts that the full Packet 2 planning universe comes from the
accepted anchor/profile matrix and includes:

- profile workflow commands
- full group anchor load/return commands
- Pad 1 anchor load, return, and rotation commands
- Pad 2 profile load, return, and rotation commands
- selected isolated pad anchor return
- Pad 3 mode load, anchor return, and rotation commands
- Pad 4 anchor return and rotation commands

The review accepts that this full planning scope is not the first
implementation scope.

## Accepted Packet 2A Implementation Scope

The review accepts only this tiny future implementation scope:

- `BH`
- `BC`

Accepted future Packet 2A behavior:

- `BH`: read-only Pad 1 BD Hard anchor/profile load intent
- `BC`: read-only Pad 1 BD Classic anchor/profile load intent

Accepted Packet 2A safety semantics:

- no prompt
- no state mutation
- no command dispatch
- no command execution
- no scene execution
- no real MIDI
- no ports
- no active CLI behavior
- no hardware behavior

## Accepted Deferred Scope

The review accepts deferring:

- `P` and `M` selected profile workflow
- `O` and `Z` full group anchor load/return
- rotations: `BR`, `P2R`, `P3R`, and `P4R`
- Pad 2 anchor/profile commands
- selected isolated pad anchor return
- Pad 3 mode and anchor commands
- Pad 4 anchor/profile commands
- Pad 1 non-initial anchors and returns
- profile `"4"` / BD Acoustic-related expansion

Profile `"4"` / My BD Acoustic remains parked unless separately approved.

## Accepted Future File Ownership

If Packet 2A is implemented later, accepted ownership is:

- create `rytm_randomizer/behavior_anchor_profile.py`
- create `tests/test_behavior_anchor_profile.py`
- update `Scripts/closeout_check.ps1` only to add the new test label

No other runtime, CLI, mock MIDI, real MIDI, package metadata, or dispatch
files are accepted as part of Packet 2A.

## Accepted Future Tests

The review accepts that future Packet 2A tests must prove:

- import silence
- deterministic `BH` and `BC` accepted behavior
- read-only safety flags
- metadata copy/immutability
- repeated evaluation determinism
- unknown-key safe failure
- deferred-key safe failure
- profile `"4"` remains parked
- passive CLI remains unchanged
- no real MIDI libraries are imported
- no package metadata files are introduced
- V1.34 reference remains untouched
- no Pads 5-12 or Analog Four support is exposed

## Parallelization Decision

The review accepts that the immediate Packet 2A implementation should not be
parallelized.

Reason:

- the first anchor/profile result shape and test vocabulary should stabilize
  serially in a small write set

## Confirmed Absent Behavior

This review confirms there is still no:

- implementation
- tests
- runtime code change
- CLI wiring
- command dispatch
- command execution
- scene execution
- prompt/input loop execution
- selected profile state
- profile rotation
- full group anchor loading
- real MIDI dependency
- `mido`
- `rtmidi`
- package metadata change
- MIDI port discovery
- MIDI port opening
- MIDI sending
- active CLI command
- `execute-command`
- `send-command`
- `hardware-test`
- hardware behavior
- hardware mutation
- hardware validation
- profile `"4"` implementation
- Analog Four support
- Pads 5-12 support
- machine/profile expansion
- SysEx
- GUI/capture

## Safe Next Options

Safe next options:

- implement Packet 2A for `BH` and `BC` only
- pause at this accepted planning checkpoint
- create a short progress checkpoint before implementation

Unsafe next moves:

- adding real MIDI
- opening ports
- adding active CLI commands
- implementing selected-profile state
- implementing full group anchor behavior
- implementing rotations
- implementing profile `"4"` without separate approval
- adding package metadata
- turning on hardware

## Recommendation

Proceed next with the tiny Packet 2A implementation:

- `rytm_randomizer/behavior_anchor_profile.py`
- `tests/test_behavior_anchor_profile.py`
- closeout label `=== Test: Behavior Anchor Profile ===`

The implementation must stay read-only, deterministic, and limited to `BH`
and `BC`.

## Decision

The Packet 2 anchor/profile behavior plan is accepted.

The next recommended task is the tiny Packet 2A implementation for `BH` and
`BC`.

Hardware remains off.

No implementation is added in this slice.
