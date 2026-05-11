# V1.34 Behavior Parity Packet 11 Selected Isolated Pad Utility Behavior Plan

## 1. Purpose

Define the next behavior-parity planning branch for selected isolated pad
utility behavior.

This plan is documentation-only. It does not add implementation, tests, CLI
wiring, dispatch, command execution, MIDI, ports, package metadata changes,
active behavior, runtime behavior, selected isolated pad runtime state,
selected-pad switching execution, selected-pad anchor return execution,
mutation execution, or hardware behavior.

## 2. Current Clean Baseline

Current branch:

- `modularize-v1.34`

Current HEAD before this documentation slice:

- `740e9a0 Add next packet planning gate review after Packet 10`

Current phase:

- Passive/Mock Foundation Phase
- behavior-parity implementation phase
- Packet 1 complete
- Packet 2 accepted as meaningful read-only anchor/profile progress
- Packet 3 complete
- Packet 4 complete
- Packet 5 accepted as meaningful Pad 1 lane behavior progress
- Packet 6 Pad 2 command-helper scope covered
- Packet 7 complete
- Packet 8 Pad 4 command-helper scope covered
- Packet 9 covered and accepted for the current read-only intent-only behavior
  phase
- Packet 10 covered and accepted for the current read-only intent-only behavior
  phase
- Packet 11 selected isolated pad utility behavior now being planned

Hardware status:

- Analog Rytm MKII off
- Analog Four MKII off
- hardware not required

## 3. Accepted Upstream Gate

Accepted upstream planning gate review:

- `Docs/V134_BEHAVIOR_PARITY_NEXT_PACKET_PLANNING_GATE_AFTER_PACKET_10_REVIEW.md`

The review accepts the next branch:

- Packet 11 selected isolated pad utility behavior planning

The review accepts these command keys as Packet 11 planning vocabulary:

- `L`: select isolated single-pad mutation target, default Pad 3
- `PZ`: return selected isolated pad to anchor only

The review accepts the first future implementation target:

- Packet 11A `L` only

The review does not authorize implementation by itself.

## 4. Packet 11 Full Planning Surface

Packet 11 planning surface:

- `L`: select isolated single-pad mutation target, default Pad 3
- `PZ`: return selected isolated pad to anchor only

Passive metadata source:

- `ISOLATED_PAD_UTILITY_COMMANDS`

The full Packet 11 surface is not safe to implement all at once because these
commands imply future selected isolated pad target state and selected isolated
pad anchor-return vocabulary.

## 5. Recommended First Implementation Subset

Recommended future Packet 11A implementation scope:

- `L` only

Command meaning:

- `L`: select isolated single-pad mutation target, default Pad 3

Reasons for choosing `L` first:

- It is an existing `ISOLATED_PAD_UTILITY_COMMANDS` command.
- It establishes selected isolated pad target vocabulary before anchor return.
- It has a deterministic default target pad: Pad 3.
- It can be represented as read-only selected isolated pad target-selection
  intent without creating runtime selected-pad state.
- It is narrower than `PZ`, which depends on an already selected isolated pad
  and implies future anchor-return behavior.
- It preserves `PZ` as an explicit deferred/safe case until selected isolated
  pad target intent is reviewed.

## 6. Proposed Future Read-Only Behavior For Packet 11A

A future Packet 11A implementation may model `L` as deterministic read-only
intent only.

Expected future result shape:

- command key: `L`
- label: select isolated single-pad mutation target, default Pad 3
- source metadata: `ISOLATED_PAD_UTILITY_COMMANDS`
- source scope: `isolated_pad_target`
- behavior family: `selected-isolated-pad/target-selection`
- utility action: `describe_selected_isolated_pad_target_selection_intent`
- intent kind: `selected_isolated_pad_target_selection`
- default target pad: `3`
- selects isolated pad: true
- selected isolated pad runtime state exists: false
- selected pad switched: false
- anchor return executed: false
- mutation executed: false
- accepted: true
- mock-only: true
- sends real MIDI: false
- opens ports: false
- hardware required: false
- active behavior: false

The helper may describe the intended selected isolated pad target concept, but
it must not select a pad, create selected-pad runtime state, return anchors,
mutate pads, dispatch commands, execute commands, open ports, send MIDI, or
touch hardware.

## 7. Expected Future Test Coverage

Future Packet 11A tests should verify:

- importing the helper prints nothing
- `L` returns deterministic accepted read-only intent data
- `L` copies existing `ISOLATED_PAD_UTILITY_COMMANDS` metadata
- `L` records source scope `isolated_pad_target`
- `L` records behavior family
  `selected-isolated-pad/target-selection`
- `L` records utility action
  `describe_selected_isolated_pad_target_selection_intent`
- `L` records intent kind `selected_isolated_pad_target_selection`
- `L` records default target pad `3`
- `L` records that selected isolated pad runtime state does not exist in the
  helper
- `L` records that selected-pad switching execution does not occur
- displayed or formatted behavior says no MIDI, no ports, no hardware, and no
  execution
- returned metadata is copied and mutation-safe
- `PZ` remains unsupported/safe until separately planned
- unknown keys fail safely
- Packet 1 selected-pad menu/status behavior remains unchanged
- Packet 3 selected isolated pad mutation-depth behavior remains unchanged
- Packet 9 undo/commit/state behavior remains unchanged
- Packet 10 selected-profile workflow behavior remains unchanged
- passive CLI behavior remains unchanged
- no real MIDI library is imported
- package metadata remains untouched
- V1.34 reference remains untouched

## 8. Deferred Packet 11 Scope

Deferred/safe Packet 11 scope:

- `PZ`: return selected isolated pad to anchor only

Reasons to defer:

- `PZ` depends on a selected isolated pad concept.
- `PZ` implies future selected isolated pad anchor-return vocabulary.
- `PZ` is safer after `L` establishes the selected isolated pad target result
  shape and safe-failure language.
- `PZ` should receive a separate docs-only plan and review before any
  implementation.

## 9. Preserved Earlier Packet Ownership

Packet 1 remains responsible for selected-pad menu/status behavior:

- `PR`: show selected isolated pad

Packet 3 remains responsible for selected isolated pad mutation-depth behavior:

- `PM`
- `PS`
- `PF`
- `PA`
- `PL`
- `PO`
- `PB`
- `PG`

Packet 5 through Packet 8 remain responsible for pad lane behavior surfaces.

Packet 9 remains responsible for undo/commit/state utility intent:

- `B`
- `E`
- `W`
- `U`

Packet 10 remains responsible for selected-profile workflow intent:

- `P`
- `M`

Packet 11 must not re-own or alter earlier packet behavior.

## 10. Expected Future File Ownership

Future implementation files:

- `rytm_randomizer/behavior_selected_isolated_pad.py`
- `tests/test_behavior_selected_isolated_pad.py`

Future closeout script update:

- `Scripts/closeout_check.ps1`, only to add the new test file with a label such
  as `=== Test: Behavior Selected Isolated Pad ===`

No file is changed by this planning slice beyond documentation.

## 11. Non-Goals

No implementation in this slice.

No tests in this slice.

No CLI execution wiring.

No dispatch.

No command execution.

No prompt/input loop.

No active depth prompt.

No runtime selected isolated pad state.

No selected-pad switching execution.

No selected-pad anchor return execution.

No isolated pad mutation execution.

No selected-profile runtime state.

No current-profile runtime state.

No real MIDI.

No `mido`.

No `rtmidi`.

No port opening.

No MIDI sending.

No package metadata changes.

No active behavior.

No hardware behavior.

No hardware validation.

## 12. Preconditions Before Future Implementation

Before any future Packet 11A implementation:

- clean Git status
- closeout passes
- V1.34 reference diff is empty
- package metadata diff is empty
- Packet 11 plan accepted in a separate docs-only review
- implementation remains read-only and intent-only
- implementation follows TDD
- first implementation subset is `L` only
- `PZ` remains deferred/safe
- Packet 1 selected-pad menu/status behavior remains unchanged
- Packet 3 selected isolated pad mutation-depth behavior remains unchanged
- Packet 9 undo/commit/state behavior remains unchanged
- Packet 10 selected-profile workflow behavior remains unchanged
- runtime selected isolated pad state remains absent
- selected-pad switching execution remains absent
- selected-pad anchor return execution remains absent
- mutation execution remains absent
- dispatch, command execution, MIDI, ports, package metadata changes, active
  behavior, and hardware behavior remain out of scope

## 13. Safe Next Options

Safe next options:

- docs-only review/acceptance gate for this Packet 11 plan
- tiny TDD Packet 11A implementation for read-only `L` intent only, after plan
  review
- user-facing progress/timeline update before implementation
- pause at this clean Packet 11 planning checkpoint

## 14. Recommendation

Proceed next with a docs-only Packet 11 plan review.

If accepted, the next implementation should be a tiny TDD Packet 11A
implementation for read-only `L` intent only.

Do not implement `PZ` yet.

## 15. Decision

The Packet 11 selected isolated pad utility behavior plan is documented.

Packet 11A `L` is the recommended next tiny behavior-parity implementation
target after review.

Hardware remains off.

No implementation in this slice.
