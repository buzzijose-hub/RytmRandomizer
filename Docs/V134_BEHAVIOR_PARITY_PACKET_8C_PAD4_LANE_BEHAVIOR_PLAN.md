# V1.34 Behavior Parity Packet 8C Pad 4 Lane Behavior Plan

## 1. Purpose

Define the next tiny Packet 8C Pad 4 lane behavior planning slice for `P4X`
only.

This is documentation-only. It does not add implementation, tests, CLI wiring,
dispatch, command execution, MIDI, ports, package metadata, active behavior,
runtime behavior, or hardware behavior.

## 2. Current Clean Baseline

Current branch:

- `modularize-v1.34`

Current HEAD before this documentation slice:

- `6f8b60f Add behavior parity progress report review after Packet 8B`

Current phase:

- Passive/Mock Foundation Phase
- behavior-parity implementation phase
- Packet 8A accepted
- Packet 8B accepted
- progress report after Packet 8B accepted
- Packet 8C Pad 4 lane behavior now being planned

Hardware status:

- Analog Rytm MKII off
- Analog Four MKII off
- hardware not required

## 3. Accepted Upstream Gate

Accepted upstream progress report review:

- `Docs/V134_BEHAVIOR_PARITY_IMPLEMENTATION_PROGRESS_REPORT_AFTER_PACKET_8B_REVIEW.md`

The review accepts the current Packet 8 boundary:

- `P4A` accepted
- `P4R` accepted
- `P4X` deferred/safe
- `P4M` remains Packet 1 menu/status behavior
- group profile `"4"` / My BD Acoustic remains parked in the mock message
  mapper

The upstream review recommends a docs-only Packet 8C plan for `P4X` if
continuing.

## 4. Packet 8C Planning Choice

Packet 8C planning scope:

- `P4X` only

Command meaning:

- `P4X`: safely mutate the currently loaded Pad 4 mode

Reasons for choosing `P4X` next:

- It is an existing `PAD4_COMMANDS` command.
- It targets Pad 4 only.
- It follows the accepted `P3X` current-mode safe mutation intent pattern.
- Packet 8A and Packet 8B already established the Pad 4 helper shape and
  rotation vocabulary.
- Current-mode safe mutation intent can be modeled read-only without runtime
  Pad 4 mode state.
- It completes the current Pad 4 command-helper surface after a future
  implementation, checkpoint, and review.

## 5. Proposed Future Read-Only Behavior

A future Packet 8C implementation may model `P4X` as deterministic read-only
intent only.

Expected future result shape:

- command key: `P4X`
- label: safely mutate the currently loaded Pad 4 mode
- source metadata: `PAD4_COMMANDS`
- target pad: `4`
- lane: Pad 4 BD Acoustic lane
- behavior family: `pad4-lane/bd-acoustic-current-mode-safe-mutation`
- lane action: `describe_pad4_bd_acoustic_current_mode_safe_mutation_intent`
- intent kind: `mutation`
- mutation concept: Pad 4 BD Acoustic current mode safe mutation
- accepted: true
- mock-only: true
- sends real MIDI: false
- opens ports: false
- hardware required: false
- active behavior: false

The helper may describe the intended Pad 4 BD Acoustic current-mode safe
mutation concept, but it must not mutate runtime state, select a runtime mode,
load anchors, rotate modes, mutate modes, dispatch commands, execute commands,
open ports, send MIDI, or touch hardware.

## 6. Expected Future Test Coverage

Future tests should verify:

- existing `P4A` behavior remains unchanged
- existing `P4R` behavior remains unchanged
- `P4X` returns deterministic accepted read-only intent data
- `P4X` copies existing `PAD4_COMMANDS` metadata
- `P4X` records target pad `4`
- `P4X` records lane `Pad 4 BD Acoustic lane`
- `P4X` records behavior family
  `pad4-lane/bd-acoustic-current-mode-safe-mutation`
- `P4X` records lane action
  `describe_pad4_bd_acoustic_current_mode_safe_mutation_intent`
- `P4X` records intent kind `mutation`
- `P4X` records mutation concept
  `Pad 4 BD Acoustic current mode safe mutation`
- displayed or formatted behavior says no MIDI, no ports, no hardware, and no
  execution
- returned metadata is copied and mutation-safe
- unknown keys still fail safely
- `P4M` remains Packet 1 menu/status behavior
- passive CLI behavior remains unchanged
- no real MIDI library is imported
- package metadata remains untouched
- V1.34 reference remains untouched

## 7. Existing And Deferred Packet 8 Scope

Already implemented and accepted:

- `P4A`: Pad 4 BD Acoustic body/accent anchor return/home intent
- `P4R`: Pad 4 BD Acoustic behavior mode rotation intent

Planned future Packet 8C implementation candidate:

- `P4X`: Pad 4 BD Acoustic current-mode safe mutation intent

Preserved Packet 1 ownership:

- `P4M`: show Pad 4 BD Acoustic body / accent menu

If `P4X` is later implemented, checkpointed, and reviewed, there will be no
remaining deferred command-helper scope for the current `PAD4_COMMANDS`
surface. Runtime Pad 4 state and hardware-facing behavior remain separate
future work.

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

No closeout script update is expected because `tests/test_behavior_pad4_lane.py`
is already covered by:

- `=== Test: Behavior Pad 4 Lane ===`

## 10. Non-Goals

No implementation in this slice.

No tests in this slice.

No CLI execution wiring.

No dispatch.

No command execution.

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

No active behavior.

No hardware behavior.

No hardware validation.

## 11. Preconditions Before Future Implementation

Before any future Packet 8C implementation:

- clean Git status
- closeout passes
- V1.34 reference diff is empty
- package metadata diff is empty
- Packet 8C plan accepted in a separate docs-only review
- `P4A` behavior remains unchanged
- `P4R` behavior remains unchanged
- `P4M` remains Packet 1 menu/status behavior
- group profile `"4"` remains parked unless separately approved
- implementation remains read-only and intent-only

## 12. Safe Next Options

After this plan:

- docs-only Packet 8C plan review
- pause at this clean planning checkpoint

After a separate plan review:

- tiny TDD Packet 8C implementation for read-only `P4X` intent only

## 13. Recommendation

Proceed next with a docs-only Packet 8C plan review.

Do not implement `P4X`, dispatch, MIDI, ports, package metadata changes,
active behavior, runtime execution, or hardware behavior without the separate
Packet 8C plan review.

## 14. Decision

Packet 8C is planned as a tiny future read-only `P4X` behavior slice.

Hardware remains off.

No implementation in this slice.

## 15. Review Status

This plan is reviewed by:

- `Docs/V134_BEHAVIOR_PARITY_PACKET_8C_PAD4_LANE_BEHAVIOR_PLAN_REVIEW.md`

The review accepts the future tiny Packet 8C implementation scope for `P4X`
only.

The review keeps `P4A` unchanged, keeps `P4R` unchanged, keeps `P4M` in Packet
1 menu/status ownership, and keeps group profile `"4"` / My BD Acoustic parked
in the mock message mapper.

No implementation, tests, CLI wiring, dispatch, command execution, runtime Pad
4 state, MIDI, ports, package metadata changes, active behavior, or hardware
behavior is added by the review.
