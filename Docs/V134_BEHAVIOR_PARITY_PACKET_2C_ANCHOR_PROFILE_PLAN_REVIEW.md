# V1.34 Behavior Parity Packet 2C Anchor/Profile Plan Review

## Purpose

Review and accept
`Docs/V134_BEHAVIOR_PARITY_PACKET_2C_ANCHOR_PROFILE_PLAN.md` as the current
planning gate for the next tiny anchor/profile implementation packet.

This review is documentation-only. It adds no implementation, tests, runtime
behavior, command dispatch, scene execution, MIDI, port opening, active CLI
command, package metadata change, machine/profile expansion, or hardware
behavior.

## Current Clean Baseline

Current branch:

- modularize-v1.34

Current HEAD before this slice:

- b79cf17 Add Packet 2C anchor profile plan

Current phase:

- Passive/Mock Foundation Phase
- Packet 2A anchor/profile behavior implemented and accepted
- Packet 2B anchor/profile behavior implemented and accepted
- Packet 2C anchor/profile behavior plan created
- Packet 2C anchor/profile behavior plan now being reviewed

Hardware status:

- Analog Rytm MKII off
- Analog Four MKII off
- hardware not required

## Review Decision

`Docs/V134_BEHAVIOR_PARITY_PACKET_2C_ANCHOR_PROFILE_PLAN.md` is accepted as
the current Packet 2C planning gate.

The plan remains planning-only.

The plan does not authorize broad behavior parity implementation by itself.

The plan does not authorize turning hardware on by itself.

## Accepted Packet Identity

Accepted packet:

- Packet 2C: Anchor/Profile Behavior Parity

Accepted packet intent:

- add one more deterministic read-only Pad 1 anchor-load intent
- keep profile `"4"` / My BD Acoustic parked for now
- prove the anchor/profile helper can add another non-profile-4 Pad 1 anchor
  without inventing group-profile metadata
- preserve the current no-MIDI, no-port, no-dispatch safety boundary

## Accepted Packet 2C Implementation Scope

The review accepts only this tiny future implementation scope:

- `BF`

Accepted future Packet 2C behavior:

- `BF`: read-only Pad 1 BD FM profiled anchor intent

Accepted `BF` profile metadata semantics:

- no invented profile key
- no invented machine value
- no invented group-profile entry
- profile key should be an empty string
- machine value should be `None`
- metadata should record that group-profile metadata is absent

Accepted Packet 2C safety semantics:

- no prompt
- no state mutation
- no command dispatch
- no command execution
- no scene execution
- no real MIDI
- no ports
- no active CLI behavior
- no package metadata
- no machine/profile expansion
- no hardware behavior

## Accepted Profile 4 Position

The review accepts keeping `BA` and profile `"4"` / My BD Acoustic parked.

Reasons:

- profile `"4"` remains useful as an unsupported/safe boundary
- `BA` touches the parked BD Acoustic/profile-4 area
- existing group profile `"4"` is associated with group pad `4`, while `BA`
  is a Pad 1 command
- that mismatch deserves a separate decision/review before any behavior helper
  support is added

Any future `BA` support must be separately approved in its own tiny
documentation slice.

## Accepted Deferred Scope

The review accepts deferring:

- `P` and `M` selected profile workflow
- `O` and `Z` full group anchor load/return
- rotations: `BR`, `P2R`, `P3R`, and `P4R`
- Pad 2 anchor/profile commands
- selected isolated pad anchor return
- Pad 3 mode and anchor commands
- Pad 4 anchor/profile commands
- profile `"4"` / BD Acoustic command `BA`
- BD FM return and discovery commands
- BD Plastic anchors, returns, and discovery commands
- BD Silky anchors, returns, and discovery commands

## Accepted Future File Ownership

If Packet 2C is implemented later, accepted ownership is:

- modify `rytm_randomizer/behavior_anchor_profile.py`
- modify `tests/test_behavior_anchor_profile.py`

No closeout script update is expected because `tests/test_behavior_anchor_profile.py`
is already covered by:

- `=== Test: Behavior Anchor Profile ===`

No other runtime, CLI, mock MIDI, real MIDI, package metadata, metadata
source, or dispatch files are accepted as part of Packet 2C.

## Accepted Future Tests

The review accepts that future Packet 2C tests must prove:

- `BH` behavior remains unchanged
- `BS` behavior remains unchanged
- `BC` behavior remains unchanged
- deterministic `BF` accepted behavior
- `BF` uses no invented profile key
- `BF` uses no invented machine value
- `BF` metadata records absent group-profile metadata safely
- read-only safety flags
- repeated evaluation determinism
- unknown-key safe failure
- deferred-key safe failure
- `BA` and profile `"4"` remain parked
- passive CLI remains unchanged
- no real MIDI libraries are imported
- no package metadata files are introduced
- V1.34 reference remains untouched
- no Pads 5-12 or Analog Four support is exposed

## Parallelization Decision

The review accepts that the immediate Packet 2C implementation should not be
parallelized.

Reason:

- the write set is one module and one test file
- preserving Packet 2A and Packet 2B behavior while adding one absent-metadata
  Pad 1 anchor is safer as a serial change

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
- profile `"4"` implementation
- `BA` behavior support
- new group-profile metadata
- machine/profile universe expansion
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
- Analog Four support
- Pads 5-12 support
- SysEx
- GUI/capture

## Safe Next Options

Safe next options:

- implement Packet 2C for `BF` only
- pause at this accepted planning checkpoint
- create a short Packet 2 progress checkpoint before implementation

Unsafe next moves:

- adding real MIDI
- opening ports
- adding active CLI commands
- inventing BD FM group-profile metadata
- implementing `BA` or profile `"4"` without separate approval
- implementing selected-profile state
- implementing full group anchor behavior
- implementing rotations
- adding package metadata
- turning on hardware

## Recommendation

Proceed next with the tiny Packet 2C implementation:

- modify `rytm_randomizer/behavior_anchor_profile.py`
- modify `tests/test_behavior_anchor_profile.py`

The implementation must stay read-only, deterministic, and limited to `BF`.

## Decision

The Packet 2C anchor/profile behavior plan is accepted.

The next recommended task is the tiny Packet 2C implementation for `BF`.

Hardware remains off.

No implementation is added in this slice.
