# V1.34 Behavior Parity Packet 2B Anchor/Profile Plan Review

## Purpose

Review and accept
`Docs/V134_BEHAVIOR_PARITY_PACKET_2B_ANCHOR_PROFILE_PLAN.md` as the current
planning gate for the next tiny anchor/profile implementation packet.

This review is documentation-only. It adds no implementation, tests, runtime
behavior, command dispatch, scene execution, MIDI, port opening, active CLI
command, package metadata change, machine/profile expansion, or hardware
behavior.

## Current Clean Baseline

Current branch:

- modularize-v1.34

Current HEAD before this slice:

- 5cad62b Add Packet 2A anchor profile checkpoint review

Current phase:

- Passive/Mock Foundation Phase
- Packet 2A anchor/profile behavior implemented and accepted
- Packet 2B anchor/profile behavior plan created
- Packet 2B anchor/profile behavior plan now being reviewed

Hardware status:

- Analog Rytm MKII off
- Analog Four MKII off
- hardware not required

## Review Decision

`Docs/V134_BEHAVIOR_PARITY_PACKET_2B_ANCHOR_PROFILE_PLAN.md` is accepted as
the current Packet 2B planning gate.

The plan remains planning-only.

The plan does not authorize broad behavior parity implementation by itself.

The plan does not authorize turning hardware on by itself.

## Accepted Packet Identity

Accepted packet:

- Packet 2B: Anchor/Profile Behavior Parity

Accepted packet intent:

- add one more deterministic read-only Pad 1 anchor-load intent
- prove the anchor/profile helper can represent an anchor command that has
  passive command metadata but no existing group-profile metadata
- preserve the current no-MIDI, no-port, no-dispatch safety boundary

## Accepted Packet 2B Implementation Scope

The review accepts only this tiny future implementation scope:

- `BS`

Accepted future Packet 2B behavior:

- `BS`: read-only Pad 1 BD Sharp anchor/profile load intent

Accepted `BS` profile metadata semantics:

- no invented profile key
- no invented machine value
- profile key should be an empty string
- machine value should be `None`
- metadata should record that group-profile metadata is absent

Accepted Packet 2B safety semantics:

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
- BD FM, BD Plastic, and BD Silky anchors and returns

Profile `"4"` / My BD Acoustic remains parked unless separately approved.

## Accepted Future File Ownership

If Packet 2B is implemented later, accepted ownership is:

- modify `rytm_randomizer/behavior_anchor_profile.py`
- modify `tests/test_behavior_anchor_profile.py`

No closeout script update is expected because `tests/test_behavior_anchor_profile.py`
is already covered by:

- `=== Test: Behavior Anchor Profile ===`

No other runtime, CLI, mock MIDI, real MIDI, package metadata, metadata
source, or dispatch files are accepted as part of Packet 2B.

## Accepted Future Tests

The review accepts that future Packet 2B tests must prove:

- `BH` behavior remains unchanged
- `BC` behavior remains unchanged
- deterministic `BS` accepted behavior
- `BS` uses no invented profile key
- `BS` uses no invented machine value
- `BS` metadata records absent group-profile metadata safely
- read-only safety flags
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

The review accepts that the immediate Packet 2B implementation should not be
parallelized.

Reason:

- the write set is one module and one test file
- preserving Packet 2A behavior while adding one edge-case anchor is safer as
  a serial change

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

- implement Packet 2B for `BS` only
- pause at this accepted planning checkpoint
- create a short progress checkpoint before implementation

Unsafe next moves:

- adding real MIDI
- opening ports
- adding active CLI commands
- inventing BD Sharp group-profile metadata
- implementing selected-profile state
- implementing full group anchor behavior
- implementing rotations
- implementing profile `"4"` without separate approval
- adding package metadata
- turning on hardware

## Recommendation

Proceed next with the tiny Packet 2B implementation:

- modify `rytm_randomizer/behavior_anchor_profile.py`
- modify `tests/test_behavior_anchor_profile.py`

The implementation must stay read-only, deterministic, and limited to `BS`.

## Decision

The Packet 2B anchor/profile behavior plan is accepted.

The next recommended task is the tiny Packet 2B implementation for `BS`.

Hardware remains off.

No implementation is added in this slice.
