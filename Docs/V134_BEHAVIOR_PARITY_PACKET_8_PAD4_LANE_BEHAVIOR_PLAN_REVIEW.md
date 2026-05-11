# V1.34 Behavior Parity Packet 8 Pad 4 Lane Behavior Plan Review

## 1. Purpose

Review and accept the Packet 8 Pad 4 lane behavior plan.

This is a documentation-only review checkpoint. It confirms the next tiny
implementation scope without adding implementation, tests, CLI wiring,
dispatch, command execution, MIDI, ports, package metadata, active behavior,
runtime behavior, or hardware behavior.

## 2. Current Clean Baseline

Current branch:

- `modularize-v1.34`

Current HEAD before this documentation slice:

- `9b59a44 Add Packet 8 Pad 4 lane behavior plan`

Current phase:

- Passive/Mock Foundation Phase
- behavior-parity implementation phase
- Packet 7 complete
- next Packet 8 planning gate accepted
- Packet 8 Pad 4 lane behavior plan created and now being reviewed

Hardware status:

- Analog Rytm MKII off
- Analog Four MKII off
- hardware not required

## 3. Review Decision

The Packet 8 Pad 4 lane behavior plan is accepted:

- `Docs/V134_BEHAVIOR_PARITY_PACKET_8_PAD4_LANE_BEHAVIOR_PLAN.md`

Accepted plan milestone:

- `9b59a44 Add Packet 8 Pad 4 lane behavior plan`

Accepted future Packet 8A implementation scope:

- `P4A` only

No implementation is added by this review.

## 4. Accepted Future Packet 8A Behavior Vocabulary

Accepted future read-only `P4A` behavior vocabulary:

- existing `PAD4_COMMANDS` metadata
- target pad `4`
- lane `Pad 4 BD Acoustic lane`
- behavior family `pad4-lane/bd-acoustic-body-accent-home-anchor`
- lane action `return_pad4_bd_acoustic_body_accent_home_anchor`
- intent kind `anchor_return`
- anchor concept `Pad 4 BD Acoustic body/accent home anchor`
- read-only intent only

The future helper may describe the intended Pad 4 BD Acoustic body/accent
anchor concept, but it must not mutate runtime state, select a runtime mode,
load anchors, rotate modes, mutate modes, dispatch commands, execute commands,
open ports, send MIDI, or touch hardware.

## 5. Preserved And Deferred Scope

Accepted first implementation candidate:

- `P4A`: return Pad 4 to BD Acoustic body/accent anchor / home

Deferred/safe Packet 8 scope:

- `P4R`: rotate Pad 4 through BD Acoustic behavior modes
- `P4X`: safely mutate the currently loaded Pad 4 mode

Preserved Packet 1 ownership:

- `P4M`: show Pad 4 BD Acoustic body / accent menu

Group profile `"4"` / My BD Acoustic remains parked and unsupported/safe in
the mock message mapper. This review does not approve profile `"4"` mock
mapper support.

## 6. Future Implementation Requirements

The future Packet 8A implementation must:

- add `rytm_randomizer/behavior_pad4_lane.py`
- add `tests/test_behavior_pad4_lane.py`
- add closeout label `=== Test: Behavior Pad 4 Lane ===`
- support `P4A` only
- use existing `PAD4_COMMANDS` metadata
- copy metadata so returned data remains mutation-safe
- keep `P4R` and `P4X` unsupported/safe
- keep `P4M` in Packet 1 menu/status ownership
- keep group profile `"4"` mock mapper support parked
- follow red/green TDD
- keep passive CLI behavior unchanged
- avoid real MIDI imports
- avoid port opening
- avoid MIDI sending
- leave package metadata untouched
- leave V1.34 reference untouched

## 7. Confirmed Safety Boundaries

Confirmed absent:

- implementation
- tests
- CLI execution wiring
- command dispatch
- command execution
- scene execution
- prompt/input loop
- runtime Pad 4 state
- selected Pad 4 mode runtime state
- runtime Pad 4 anchor loading
- runtime Pad 4 mode rotation
- runtime Pad 4 mutation execution
- real MIDI
- `mido`
- `rtmidi`
- port opening
- MIDI sending
- package metadata changes
- active CLI command
- active behavior
- hardware behavior
- hardware validation
- Analog Four support
- Pads 5-12 support
- SysEx
- GUI/capture
- group profile `"4"` mock mapper support

`rytm_hybrid_randomizer_v134.py` remains untouched.

Package metadata remains untouched.

## 8. Preconditions Before Implementation

Before any future Packet 8A implementation:

- git status must be clean
- closeout must pass
- V1.34 reference diff must be empty
- package metadata diff must be empty
- this review must be committed
- implementation must remain read-only
- implementation must remain `P4A` only
- implementation must not add runtime Pad 4 state
- implementation must not add selected Pad 4 mode runtime state
- implementation must not add runtime anchor loading
- implementation must not add rotation execution
- implementation must not add mutation execution
- implementation must not add dispatch, MIDI, ports, package metadata, active
  behavior, or hardware behavior

## 9. Safe Next Options

Safe next options:

- proceed with a tiny TDD Packet 8A implementation for read-only `P4A`
  anchor/home intent only
- pause at this accepted plan review checkpoint
- write a short progress update before implementation

## 10. Recommendation

Proceed next with the tiny TDD Packet 8A implementation for read-only `P4A`
anchor/home intent only.

Do not widen beyond `P4A` in the same implementation slice.

## 11. Decision

The Packet 8 Pad 4 lane behavior plan is accepted.

The next implementation scope is:

- Packet 8A: `P4A` only

Hardware remains off.

No implementation in this slice.

## 12. Implementation Status

Packet 8A has now been implemented and checkpointed by:

- `05e0cf0 Add Packet 8A Pad 4 lane behavior`
- `Docs/V134_BEHAVIOR_PARITY_PACKET_8A_PAD4_LANE_BEHAVIOR_CHECKPOINT.md`

Implemented scope:

- `P4A` only

Deferred/safe scope remains:

- `P4R`
- `P4X`

`P4M` remains Packet 1 menu/status behavior.

Group profile `"4"` / My BD Acoustic remains parked in the mock message
mapper.
