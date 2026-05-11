# V1.34 Behavior Parity Packet 8 Pad 4 Lane Behavior Plan

## 1. Purpose

Define the next Packet 8 Pad 4 lane behavior planning slice.

This plan is documentation-only. It does not add implementation, tests, CLI
wiring, dispatch, command execution, MIDI, ports, package metadata, active
behavior, runtime behavior, or hardware behavior.

## 2. Current Clean Baseline

Current branch:

- `modularize-v1.34`

Current HEAD before this documentation slice:

- `fa7d976 Add next packet planning gate review after Packet 7`

Current phase:

- Passive/Mock Foundation Phase
- behavior-parity implementation phase
- Packet 1 complete
- Packet 2 accepted as meaningful read-only anchor/profile progress
- Packet 3 complete
- Packet 4 complete
- Packet 5 accepted as Pad 1 lane behavior progress
- Packet 6 Pad 2 command-helper scope covered
- Packet 7 complete
- next Packet 8 planning gate accepted
- Packet 8 Pad 4 lane behavior now being planned

Hardware status:

- Analog Rytm MKII off
- Analog Four MKII off
- hardware not required

## 3. Accepted Upstream Gate

Accepted upstream review:

- `Docs/V134_BEHAVIOR_PARITY_NEXT_PACKET_PLANNING_GATE_AFTER_PACKET_7_REVIEW.md`

The review accepts Packet 8 Pad 4 Lane Behavior planning as the next
behavior-parity branch after Packet 7.

Accepted future Packet 8 planning vocabulary:

- `P4A`: return Pad 4 to BD Acoustic body/accent anchor / home
- `P4R`: rotate Pad 4 through BD Acoustic behavior modes
- `P4X`: safely mutate the currently loaded Pad 4 mode

Preserved Packet 1 ownership:

- `P4M`: show Pad 4 BD Acoustic body / accent menu

The upstream gate does not authorize implementation, tests, runtime Pad 4
state, selected Pad 4 mode runtime state, anchor loading, rotation execution,
mutation execution, dispatch, MIDI, ports, package metadata, active behavior,
or hardware behavior.

## 4. Packet 8 Planning Choice

Packet 8 full planning surface:

- `P4A`
- `P4R`
- `P4X`

Recommended first implementation subset:

- Packet 8A: `P4A` only

Command meaning:

- `P4A`: return Pad 4 to BD Acoustic body/accent anchor / home

Reasons for choosing `P4A` first:

- It is an existing `PAD4_COMMANDS` command.
- It targets Pad 4 only.
- It is the smallest Pad 4 lane command because it can be modeled as anchor
  return/home intent.
- It establishes the future `behavior_pad4_lane` helper shape before rotation
  or mutation vocabulary.
- It can be represented as read-only intent without runtime Pad 4 state.
- It avoids jumping into current-mode mutation semantics too early.
- It keeps `P4R` and `P4X` deferred until the Pad 4 anchor/home vocabulary is
  stable.

## 5. Proposed Future Read-Only Behavior

A future Packet 8A implementation may model `P4A` as deterministic read-only
intent only.

Expected future result shape:

- command key: `P4A`
- label: return Pad 4 to BD Acoustic body/accent anchor / home
- source metadata: `PAD4_COMMANDS`
- target pad: `4`
- lane: Pad 4 BD Acoustic lane
- behavior family: `pad4-lane/bd-acoustic-body-accent-home-anchor`
- lane action: `return_pad4_bd_acoustic_body_accent_home_anchor`
- intent kind: `anchor_return`
- anchor concept: Pad 4 BD Acoustic body/accent home anchor
- accepted: true
- mock-only: true
- sends real MIDI: false
- opens ports: false
- hardware required: false
- active behavior: false

The helper may describe the intended Pad 4 BD Acoustic body/accent anchor
concept, but it must not mutate runtime state, select a runtime mode, load
anchors, rotate modes, mutate modes, dispatch commands, execute commands, open
ports, send MIDI, or touch hardware.

## 6. Expected Future Test Coverage

Future tests should verify:

- importing `rytm_randomizer.behavior_pad4_lane` prints nothing
- `P4A` returns deterministic accepted read-only intent data
- `P4A` copies existing `PAD4_COMMANDS` metadata
- `P4A` records target pad `4`
- `P4A` records lane `Pad 4 BD Acoustic lane`
- `P4A` records behavior family
  `pad4-lane/bd-acoustic-body-accent-home-anchor`
- `P4A` records lane action
  `return_pad4_bd_acoustic_body_accent_home_anchor`
- `P4A` records intent kind `anchor_return`
- `P4A` records anchor concept
  `Pad 4 BD Acoustic body/accent home anchor`
- displayed or formatted behavior says no MIDI, no ports, no hardware, and no
  execution
- returned metadata is copied and mutation-safe
- unknown keys fail safely
- existing known non-Pad-4 commands fail safely in this helper
- `P4R` remains unsupported/safe until separately planned
- `P4X` remains unsupported/safe until separately planned
- `P4M` remains Packet 1 menu/status behavior
- passive CLI behavior remains unchanged
- no real MIDI library is imported
- package metadata remains untouched
- V1.34 reference remains untouched

## 7. Existing And Deferred Packet 8 Scope

Planned first implementation candidate:

- `P4A`: Pad 4 BD Acoustic body/accent anchor return/home intent

Deferred/safe Packet 8 scope:

- `P4R`: rotate Pad 4 through BD Acoustic behavior modes
- `P4X`: safely mutate the currently loaded Pad 4 mode

Preserved Packet 1 ownership:

- `P4M`: show Pad 4 BD Acoustic body / accent menu

Packet 8 is not complete in this planning slice.

## 8. Relationship To Group Profile 4

This plan concerns existing Pad 4 command metadata from `PAD4_COMMANDS`.

It does not implement mock mapper support for group profile `"4"` / My BD
Acoustic.

Group profile `"4"` remains parked and unsupported/safe in the mock message
mapper unless separately approved.

## 9. Expected Future File Ownership

Future implementation files:

- `rytm_randomizer/behavior_pad4_lane.py`
- `tests/test_behavior_pad4_lane.py`

Future closeout update, if implementation is approved:

- add `=== Test: Behavior Pad 4 Lane ===`

No closeout script update happens in this documentation-only plan.

## 10. Non-Goals

No implementation in this slice.

No tests in this slice.

No CLI execution wiring.

No dispatch.

No command execution.

No scene execution.

No prompt/input loop.

No runtime Pad 4 state.

No selected Pad 4 mode runtime state.

No runtime Pad 4 anchor loading.

No runtime Pad 4 mode rotation.

No runtime Pad 4 mutation execution.

No real MIDI.

No `mido`.

No `rtmidi`.

No port opening.

No MIDI sending.

No package metadata changes.

No active CLI command.

No active behavior.

No hardware behavior.

No hardware validation.

No Analog Four support.

No Pads 5-12 support.

No SysEx.

No GUI/capture.

No group profile `"4"` mock mapper support.

## 11. Preconditions Before Implementation

Before any future Packet 8A implementation:

- this plan must be reviewed and accepted
- git status must be clean
- closeout must pass
- V1.34 reference diff must be empty
- package metadata diff must be empty
- implementation must use TDD
- implementation must remain read-only
- implementation must support `P4A` only
- implementation must keep `P4R` and `P4X` unsupported/safe
- implementation must keep `P4M` in Packet 1 menu/status ownership
- implementation must not implement group profile `"4"` mock mapper support
- implementation must not add runtime Pad 4 state
- implementation must not add selected Pad 4 mode runtime state
- implementation must not add Pad 4 anchor loading
- implementation must not add Pad 4 rotation execution
- implementation must not add Pad 4 mutation execution
- implementation must not add dispatch, MIDI, ports, package metadata, active
  behavior, or hardware behavior

## 12. Safe Next Options

Safe next options:

- review and accept this Packet 8 Pad 4 lane behavior plan
- pause at this clean planning checkpoint
- write a user-facing progress/timeline update before implementation

## 13. Recommendation

Review and accept this plan next.

After review, proceed with a tiny TDD Packet 8A implementation for read-only
`P4A` anchor/home intent only.

Do not widen beyond `P4A` in the same implementation slice.

## 14. Decision

Packet 8 Pad 4 lane behavior planning is documented.

Recommended future implementation scope:

- Packet 8A: `P4A` only

Hardware remains off.

No implementation in this slice.
