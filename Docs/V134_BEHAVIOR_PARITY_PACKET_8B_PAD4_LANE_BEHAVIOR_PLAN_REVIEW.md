# V1.34 Behavior Parity Packet 8B Pad 4 Lane Behavior Plan Review

## 1. Purpose

Review and accept the Packet 8B Pad 4 lane behavior plan for `P4R`.

This is a documentation-only review checkpoint. It confirms the next tiny
implementation scope without adding implementation, tests, CLI wiring,
dispatch, command execution, MIDI, ports, package metadata, active behavior,
runtime behavior, or hardware behavior.

## 2. Current Clean Baseline

Current branch:

- `modularize-v1.34`

Current HEAD before this documentation slice:

- `b95cd81 Add Packet 8B Pad 4 lane behavior plan`

Current phase:

- Passive/Mock Foundation Phase
- behavior-parity implementation phase
- Packet 8A accepted
- progress report after Packet 8A accepted
- Packet 8B Pad 4 lane behavior plan created and now being reviewed

Hardware status:

- Analog Rytm MKII off
- Analog Four MKII off
- hardware not required

## 3. Review Decision

The Packet 8B Pad 4 lane behavior plan is accepted:

- `Docs/V134_BEHAVIOR_PARITY_PACKET_8B_PAD4_LANE_BEHAVIOR_PLAN.md`

Accepted plan milestone:

- `b95cd81 Add Packet 8B Pad 4 lane behavior plan`

Accepted future Packet 8B implementation scope:

- `P4R` only

No implementation is added by this review.

## 4. Accepted Future Packet 8B Behavior Vocabulary

Accepted future read-only `P4R` behavior vocabulary:

- existing `PAD4_COMMANDS` metadata
- target pad `4`
- lane `Pad 4 BD Acoustic lane`
- behavior family `pad4-lane/bd-acoustic-mode-rotation`
- lane action `describe_pad4_bd_acoustic_mode_rotation_intent`
- intent kind `rotation`
- rotation concept `Pad 4 BD Acoustic behavior mode rotation`
- read-only intent only

The future helper may describe the intended Pad 4 BD Acoustic mode rotation
concept, but it must not mutate runtime state, select a runtime mode, load
anchors, rotate modes, mutate modes, dispatch commands, execute commands,
open ports, send MIDI, or touch hardware.

## 5. Preserved And Deferred Scope

Existing accepted Packet 8 behavior must remain unchanged:

- `P4A`: Pad 4 BD Acoustic body/accent anchor return/home intent

Accepted next implementation candidate:

- `P4R`: rotate Pad 4 through BD Acoustic behavior modes

Deferred/safe Packet 8 scope:

- `P4X`: safely mutate the currently loaded Pad 4 mode

Preserved Packet 1 ownership:

- `P4M`: show Pad 4 BD Acoustic body / accent menu

Group profile `"4"` / My BD Acoustic remains parked and unsupported/safe in
the mock message mapper.

## 6. Future Implementation Requirements

The future Packet 8B implementation must:

- update `rytm_randomizer/behavior_pad4_lane.py`
- update `tests/test_behavior_pad4_lane.py`
- support `P4R` only as the new behavior
- preserve existing `P4A` behavior unchanged
- use existing `PAD4_COMMANDS` metadata
- copy metadata so returned data remains mutation-safe
- keep `P4X` unsupported/safe
- keep `P4M` in Packet 1 menu/status ownership
- keep group profile `"4"` mock mapper support parked
- follow red/green TDD
- keep passive CLI behavior unchanged
- avoid real MIDI imports
- avoid port opening
- avoid MIDI sending
- leave package metadata untouched
- leave V1.34 reference untouched

No closeout script update is expected because `tests/test_behavior_pad4_lane.py`
is already covered by:

- `=== Test: Behavior Pad 4 Lane ===`

## 7. Confirmed Safety Boundaries

Confirmed absent:

- implementation
- tests
- CLI execution wiring
- command dispatch
- command execution
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

Before any future Packet 8B implementation:

- git status must be clean
- closeout must pass
- V1.34 reference diff must be empty
- package metadata diff must be empty
- this review must be committed
- implementation must remain read-only
- implementation must remain `P4R` only
- implementation must preserve `P4A`
- implementation must not add runtime Pad 4 state
- implementation must not add selected Pad 4 mode runtime state
- implementation must not add runtime rotation execution
- implementation must not add mutation execution
- implementation must not add dispatch, MIDI, ports, package metadata, active
  behavior, or hardware behavior

## 9. Safe Next Options

Safe next options:

- proceed with a tiny TDD Packet 8B implementation for read-only `P4R`
  rotation intent only
- pause at this accepted plan review checkpoint
- write a short progress update before implementation

## 10. Recommendation

Proceed next with the tiny TDD Packet 8B implementation for read-only `P4R`
rotation intent only.

Do not widen beyond `P4R` in the same implementation slice.

## 11. Decision

The Packet 8B Pad 4 lane behavior plan is accepted.

The next implementation scope is:

- Packet 8B: `P4R` only

Hardware remains off.

No implementation in this slice.
