# V1.34 Behavior Parity Packet 7G Pad 3 Lane Behavior Plan

## 1. Purpose

Define the next tiny Packet 7G Pad 3 lane behavior planning slice for `P3R`
only.

This is documentation-only. It does not add implementation, tests, CLI wiring,
dispatch, command execution, MIDI, ports, package metadata, active behavior,
runtime behavior, or hardware behavior.

## 2. Current Clean Baseline

Current branch:

- `modularize-v1.34`

Current HEAD before this documentation slice:

- `a67e2ed Add next Packet 7 command selection review after Packet 7F`

Current phase:

- Passive/Mock Foundation Phase
- behavior-parity implementation phase
- Packet 7F accepted
- progress report after Packet 7F accepted
- next Packet 7 command selection after Packet 7F accepted
- Packet 7G Pad 3 lane behavior now being planned

Hardware status:

- Analog Rytm MKII off
- Analog Four MKII off
- hardware not required

## 3. Accepted Upstream Gate

Accepted upstream selection review:

- `Docs/V134_BEHAVIOR_PARITY_NEXT_PACKET_7_COMMAND_SELECTION_CHECKPOINT_AFTER_PACKET_7F_REVIEW.md`

The selection review accepts docs-only Packet 7G Pad 3 lane behavior planning
for `P3R` only.

Accepted future Packet 7G planning vocabulary:

- Pad 3 SY Raw behavior mode rotation intent
- existing `PAD3_COMMANDS` metadata
- target pad `3`
- lane `Pad 3 SY Raw lane`
- behavior family `pad3-lane/sy-raw-mode-rotation`
- lane action `describe_pad3_sy_raw_mode_rotation_intent`
- intent kind `rotation`
- read-only intent only

The upstream gate does not authorize implementation, tests, runtime Pad 3
state, mode loading, mutation, discovery execution, rotation execution,
dispatch, MIDI, ports, package metadata, active behavior, or hardware behavior.

## 4. Packet 7G Planning Choice

Packet 7G planning scope:

- `P3R` only

Command meaning:

- `P3R`: rotate Pad 3 through SY Raw behavior modes

Reasons for choosing `P3R` next:

- It is an existing `PAD3_COMMANDS` command.
- It targets Pad 3 only.
- It follows the accepted Pad 3 lane helper shape.
- It is narrower than current-mode mutation behavior.
- It can be modeled as read-only rotation intent without runtime Pad 3 state.
- It can describe mode-rotation vocabulary without actually selecting or
  loading a mode.
- It should precede `P3X` so mutation intent does not arrive before the
  current-mode vocabulary is documented.

## 5. Proposed Future Read-Only Behavior

A future Packet 7G implementation may model `P3R` as deterministic read-only
intent only.

Expected future result shape:

- command key: `P3R`
- label: rotate Pad 3 through SY Raw behavior modes
- source metadata: `PAD3_COMMANDS`
- target pad: `3`
- lane: Pad 3 SY Raw lane
- behavior family: `pad3-lane/sy-raw-mode-rotation`
- lane action: `describe_pad3_sy_raw_mode_rotation_intent`
- intent kind: `rotation`
- rotation concept: Pad 3 SY Raw behavior mode rotation
- accepted: true
- mock-only: true
- sends real MIDI: false
- opens ports: false
- hardware required: false
- active behavior: false

The helper may describe the intended rotation concept, but it must not rotate
runtime state, select a runtime mode, load modes, dispatch commands, execute
commands, open ports, send MIDI, or touch hardware.

## 6. Expected Future Test Coverage

Future tests should verify:

- existing `P3A` behavior remains unchanged
- existing `SA` behavior remains unchanged
- existing `SL` behavior remains unchanged
- existing `SB` behavior remains unchanged
- existing `SX` behavior remains unchanged
- existing `SW` behavior remains unchanged
- `P3R` returns deterministic accepted read-only intent data
- `P3R` copies existing `PAD3_COMMANDS` metadata
- `P3R` records target pad `3`
- `P3R` records lane `Pad 3 SY Raw lane`
- `P3R` records behavior family `pad3-lane/sy-raw-mode-rotation`
- `P3R` records lane action
  `describe_pad3_sy_raw_mode_rotation_intent`
- `P3R` records intent kind `rotation`
- `P3R` records rotation concept `Pad 3 SY Raw behavior mode rotation`
- displayed or formatted behavior says no MIDI, no ports, no hardware, and no
  execution
- returned metadata is copied and mutation-safe
- unknown keys still fail safely
- unsupported deferred keys still fail safely
- `P3M` remains Packet 1 menu/status behavior
- passive CLI behavior remains unchanged
- no real MIDI library is imported
- package metadata remains untouched
- V1.34 reference remains untouched

## 7. Existing And Deferred Packet 7 Scope

Already implemented and accepted:

- `P3A`: Pad 3 SY Raw Mid Bass home anchor intent
- `SA`: Pad 3 SY Raw anchor return intent
- `SL`: Pad 3 SY Raw LP1 bassline mode-load intent
- `SB`: Pad 3 SY Raw Bandpass mid-bass mode-load intent
- `SX`: Pad 3 SY Raw sci-fi motion accent mode-load intent
- `SW`: Pad 3 SY Raw Wave + Balance discovery intent

Preserved Packet 1 ownership:

- `P3M`: show Pad 3 SY Raw bass / synth-percussion menu

Deferred/safe Packet 7 scope:

- `P3X`: safely mutate the currently loaded Pad 3 mode

The deferred command remains unsupported/safe until separately planned and
reviewed.

## 8. Expected Future File Ownership

Future implementation files:

- `rytm_randomizer/behavior_pad3_lane.py`
- `tests/test_behavior_pad3_lane.py`

No closeout script update is expected because `tests/test_behavior_pad3_lane.py`
is already covered by:

- `=== Test: Behavior Pad 3 Lane ===`

## 9. Non-Goals

No implementation in this slice.

No tests in this slice.

No CLI execution wiring.

No dispatch.

No command execution.

No scene execution.

No prompt/input loop.

No runtime Pad 3 state.

No selected Pad 3 mode runtime state.

No runtime discovery execution.

No runtime mode loading.

No mutation execution.

No profile rotation execution.

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

## 10. Preconditions Before Implementation

Before any future Packet 7G implementation:

- this plan must be reviewed and accepted
- git status must be clean
- closeout must pass
- V1.34 reference diff must be empty
- package metadata diff must be empty
- implementation must use TDD
- implementation must remain read-only
- implementation must support `P3R` only
- implementation must preserve `P3A`, `SA`, `SL`, `SB`, `SX`, and `SW`
- implementation must keep `P3M` in Packet 1 menu/status ownership
- implementation must keep `P3X` unsupported/safe
- implementation must not add runtime Pad 3 state
- implementation must not add rotation execution
- implementation must not add mode loading
- implementation must not add dispatch, MIDI, ports, active behavior, or
  hardware behavior

## 11. Safe Next Options

Safe next options:

- create a docs-only review/acceptance gate for this Packet 7G plan
- pause at this planning checkpoint
- write a short progress update before implementation

## 12. Recommendation

Create a docs-only Packet 7G plan review next.

If accepted, proceed with a tiny TDD implementation for read-only `P3R`
rotation intent only.

## 13. Decision

Packet 7G planning selects:

- `P3R` only

Hardware remains off.

No implementation in this slice.
