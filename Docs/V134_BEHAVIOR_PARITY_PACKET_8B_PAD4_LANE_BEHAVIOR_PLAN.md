# V1.34 Behavior Parity Packet 8B Pad 4 Lane Behavior Plan

## 1. Purpose

Define the next tiny Packet 8B Pad 4 lane behavior planning slice for `P4R`
only.

This is documentation-only. It does not add implementation, tests, CLI wiring,
dispatch, command execution, MIDI, ports, package metadata, active behavior,
runtime behavior, or hardware behavior.

## 2. Current Clean Baseline

Current branch:

- `modularize-v1.34`

Current HEAD before this documentation slice:

- `2ca46ab Add behavior parity progress report review after Packet 8A`

Current phase:

- Passive/Mock Foundation Phase
- behavior-parity implementation phase
- Packet 8A accepted
- progress report after Packet 8A accepted
- Packet 8B Pad 4 lane behavior now being planned

Hardware status:

- Analog Rytm MKII off
- Analog Four MKII off
- hardware not required

## 3. Accepted Upstream Gate

Accepted upstream progress report review:

- `Docs/V134_BEHAVIOR_PARITY_IMPLEMENTATION_PROGRESS_REPORT_AFTER_PACKET_8A_REVIEW.md`

The review accepts the current Packet 8 boundary:

- `P4A` accepted
- `P4R` deferred/safe
- `P4X` deferred/safe
- `P4M` remains Packet 1 menu/status behavior
- group profile `"4"` / My BD Acoustic remains parked in the mock message
  mapper

The upstream review recommends a docs-only Packet 8B plan for `P4R` if
continuing.

## 4. Packet 8B Planning Choice

Packet 8B planning scope:

- `P4R` only

Command meaning:

- `P4R`: rotate Pad 4 through BD Acoustic behavior modes

Reasons for choosing `P4R` next:

- It is an existing `PAD4_COMMANDS` command.
- It targets Pad 4 only.
- Packet 8A already established Pad 4 lane helper shape with `P4A`.
- Rotation intent can be modeled read-only without runtime Pad 4 mode state.
- It follows the accepted `P2R` and `P3R` read-only rotation intent pattern.
- It keeps current-mode mutation behavior `P4X` deferred until rotation
  vocabulary is stable.

## 5. Proposed Future Read-Only Behavior

A future Packet 8B implementation may model `P4R` as deterministic read-only
intent only.

Expected future result shape:

- command key: `P4R`
- label: rotate Pad 4 through BD Acoustic behavior modes
- source metadata: `PAD4_COMMANDS`
- target pad: `4`
- lane: Pad 4 BD Acoustic lane
- behavior family: `pad4-lane/bd-acoustic-mode-rotation`
- lane action: `describe_pad4_bd_acoustic_mode_rotation_intent`
- intent kind: `rotation`
- rotation concept: Pad 4 BD Acoustic behavior mode rotation
- accepted: true
- mock-only: true
- sends real MIDI: false
- opens ports: false
- hardware required: false
- active behavior: false

The helper may describe the intended Pad 4 BD Acoustic mode rotation concept,
but it must not mutate runtime state, select a runtime mode, load anchors,
rotate modes, mutate modes, dispatch commands, execute commands, open ports,
send MIDI, or touch hardware.

## 6. Expected Future Test Coverage

Future tests should verify:

- existing `P4A` behavior remains unchanged
- `P4R` returns deterministic accepted read-only intent data
- `P4R` copies existing `PAD4_COMMANDS` metadata
- `P4R` records target pad `4`
- `P4R` records lane `Pad 4 BD Acoustic lane`
- `P4R` records behavior family `pad4-lane/bd-acoustic-mode-rotation`
- `P4R` records lane action `describe_pad4_bd_acoustic_mode_rotation_intent`
- `P4R` records intent kind `rotation`
- `P4R` records rotation concept `Pad 4 BD Acoustic behavior mode rotation`
- displayed or formatted behavior says no MIDI, no ports, no hardware, and no
  execution
- returned metadata is copied and mutation-safe
- unknown keys still fail safely
- `P4X` remains unsupported/safe until separately planned
- `P4M` remains Packet 1 menu/status behavior
- passive CLI behavior remains unchanged
- no real MIDI library is imported
- package metadata remains untouched
- V1.34 reference remains untouched

## 7. Existing And Deferred Packet 8 Scope

Already implemented and accepted:

- `P4A`: Pad 4 BD Acoustic body/accent anchor return/home intent

Planned future Packet 8B implementation candidate:

- `P4R`: Pad 4 BD Acoustic behavior mode rotation intent

Deferred/safe Packet 8 scope:

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

Before any future Packet 8B implementation:

- this plan must be reviewed and accepted
- git status must be clean
- closeout must pass
- V1.34 reference diff must be empty
- package metadata diff must be empty
- implementation must use TDD
- implementation must remain read-only
- implementation must support `P4R` only
- implementation must preserve `P4A`
- implementation must keep `P4X` unsupported/safe
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

- review and accept this Packet 8B Pad 4 lane behavior plan
- pause at this clean planning checkpoint
- write a user-facing progress/timeline update before implementation

## 13. Recommendation

Review and accept this plan next.

After review, proceed with a tiny TDD Packet 8B implementation for read-only
`P4R` rotation intent only.

Do not widen beyond `P4R` in the same implementation slice.

## 14. Decision

Packet 8B Pad 4 lane behavior planning is documented.

Recommended future implementation scope:

- Packet 8B: `P4R` only

Hardware remains off.

No implementation in this slice.
