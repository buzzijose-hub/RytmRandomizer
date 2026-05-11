# V1.34 Behavior Parity Packet 10 Selected Profile Workflow Plan

## 1. Purpose

Define the next behavior-parity planning branch for selected-profile workflow
behavior.

This plan is documentation-only. It does not add implementation, tests, CLI
wiring, dispatch, command execution, MIDI, ports, package metadata changes,
active behavior, runtime behavior, selected-profile runtime state, machine
changes, anchor loading execution, or hardware behavior.

## 2. Current Clean Baseline

Current branch:

- `modularize-v1.34`

Current HEAD before this documentation slice:

- `68a0c21 Add next packet planning gate review after Packet 9`

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
- Packet 10 selected-profile workflow behavior now being planned

Hardware status:

- Analog Rytm MKII off
- Analog Four MKII off
- hardware not required

## 3. Accepted Upstream Gate

Accepted upstream planning gate review:

- `Docs/V134_BEHAVIOR_PARITY_NEXT_PACKET_PLANNING_GATE_AFTER_PACKET_9_REVIEW.md`

The review accepts the next branch:

- Packet 10 selected-profile workflow planning

The review accepts these command keys as Packet 10 planning vocabulary:

- `P`: select/switch profile and change Rytm machine
- `M`: load selected profile anchor

The review does not authorize implementation by itself.

## 4. Packet 10 Full Planning Surface

Packet 10 planning surface:

- `P`: select/switch profile and change Rytm machine
- `M`: load selected profile anchor

Passive metadata source:

- `PROFILE_WORKFLOW_COMMANDS`

The full Packet 10 surface is not safe to implement all at once because these
commands imply future selected-profile state, machine switching, and selected
profile anchor loading vocabulary.

## 5. Recommended First Implementation Subset

Recommended future Packet 10A implementation scope:

- `P` only

Command meaning:

- `P`: select/switch profile and change Rytm machine

Reasons for choosing `P` first:

- It is an existing `PROFILE_WORKFLOW_COMMANDS` command.
- It establishes selected-profile workflow vocabulary before anchor loading.
- It can be represented as read-only profile selection and machine-change
  intent without creating runtime selected-profile state.
- It is narrower than `M`, which depends on an already selected profile and
  implies future anchor loading.
- It preserves `M` as an explicit deferred/safe case until selected-profile
  intent is reviewed.

## 6. Proposed Future Read-Only Behavior For Packet 10A

A future Packet 10A implementation may model `P` as deterministic read-only
intent only.

Expected future result shape:

- command key: `P`
- label: select/switch profile and change Rytm machine
- source metadata: `PROFILE_WORKFLOW_COMMANDS`
- source scope: `profile_machine`
- behavior family: `selected-profile-workflow/profile-selection`
- workflow action: `describe_profile_selection_machine_change_intent`
- intent kind: `profile_machine_selection`
- selects profile: true
- machine change intent: true
- selected-profile runtime state exists: false
- machine change executed: false
- accepted: true
- mock-only: true
- sends real MIDI: false
- opens ports: false
- hardware required: false
- active behavior: false

The helper may describe the intended profile-selection and machine-change
concept, but it must not select a profile, change machines, load anchors,
mutate runtime state, dispatch commands, execute commands, open ports, send
MIDI, or touch hardware.

## 7. Expected Future Test Coverage

Future Packet 10A tests should verify:

- importing the helper prints nothing
- `P` returns deterministic accepted read-only intent data
- `P` copies existing `PROFILE_WORKFLOW_COMMANDS` metadata
- `P` records source scope `profile_machine`
- `P` records behavior family
  `selected-profile-workflow/profile-selection`
- `P` records workflow action
  `describe_profile_selection_machine_change_intent`
- `P` records intent kind `profile_machine_selection`
- `P` records `selects_profile` as true
- `P` records `machine_change_intent` as true
- `P` records that selected-profile runtime state does not exist in the helper
- `P` records that machine change execution does not occur
- displayed or formatted behavior says no MIDI, no ports, no hardware, and no
  execution
- returned metadata is copied and mutation-safe
- `M` remains unsupported/safe until separately planned
- unknown keys fail safely
- Packet 2 direct anchor/profile behavior remains unchanged
- Packet 3 legacy single-profile mutation behavior remains unchanged
- Packet 9 undo/commit/state behavior remains unchanged
- passive CLI behavior remains unchanged
- no real MIDI library is imported
- package metadata remains untouched
- V1.34 reference remains untouched

## 8. Deferred Packet 10 Scope

Deferred/safe Packet 10 scope:

- `M`: load selected profile anchor

Reasons to defer:

- `M` depends on a selected-profile concept.
- `M` implies future selected-profile anchor loading vocabulary.
- `M` is safer after `P` establishes the selected-profile workflow result
  shape and safe-failure language.
- `M` should receive a separate docs-only plan and review before any
  implementation.

## 9. Preserved Earlier Packet Ownership

Packet 2 remains responsible for direct anchor/profile intent progress.

Packet 3 remains responsible for mutation-depth and guarded-input behavior,
including legacy single-profile mutation intent for:

- `M1`
- `M2`
- `M3`

Packet 9 remains responsible for undo/commit/state utility intent:

- `B`
- `E`
- `W`
- `U`

Packet 10 must not re-own or alter earlier packet behavior.

## 10. Expected Future File Ownership

Future implementation files:

- `rytm_randomizer/behavior_selected_profile.py`
- `tests/test_behavior_selected_profile.py`

Future closeout script update:

- `Scripts/closeout_check.ps1`, only to add the new test file with a label such
  as `=== Test: Behavior Selected Profile ===`

No file is changed by this planning slice beyond documentation.

## 11. Non-Goals

No implementation in this slice.

No tests in this slice.

No CLI execution wiring.

No dispatch.

No command execution.

No prompt/input loop.

No runtime selected-profile state.

No runtime current-profile state.

No profile switching execution.

No machine change execution.

No anchor loading execution.

No active selected-profile mutation.

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

Before any future Packet 10A implementation:

- clean Git status
- closeout passes
- V1.34 reference diff is empty
- package metadata diff is empty
- Packet 10 plan accepted in a separate docs-only review
- implementation remains read-only and intent-only
- implementation follows TDD
- Packet 2 direct anchor/profile behavior remains unchanged
- Packet 3 legacy single-profile mutation behavior remains unchanged
- Packet 9 undo/commit/state behavior remains unchanged
- `M` remains deferred/safe

## 13. Parallelization Position

Do not parallelize immediate Packet 10A implementation.

The first Packet 10 slice should establish the selected-profile workflow
result shape, safe-failure vocabulary, and closeout coverage in one narrow
path before any parallel work.

Parallel implementation can be reconsidered later only if future Packet 10
sub-slices split into independent files, independent tests, and a clear
closeout synchronization point.

## 14. Safe Next Options

After this plan:

- docs-only Packet 10 plan review
- pause at this clean planning checkpoint
- user-facing progress/timeline update before implementation

## 15. Recommendation

Recommended next task:

- review and accept this Packet 10 selected-profile workflow plan

Then, if accepted:

- implement a tiny TDD Packet 10A read-only behavior helper for `P` only

Do not implement `M` until after a separate docs-only plan and review.

## 16. Decision

Packet 10 selected-profile workflow behavior is planned.

Future first implementation target should be `P` only, read-only and
intent-only.

Hardware remains off.

No implementation in this slice.

## 17. Review Status

Review document:

- `Docs/V134_BEHAVIOR_PARITY_PACKET_10_SELECTED_PROFILE_WORKFLOW_PLAN_REVIEW.md`

Review decision:

- accepted as the current Packet 10 selected-profile workflow behavior plan

Accepted future first implementation target:

- Packet 10A `P` only

Deferred/safe Packet 10 scope:

- `M`

This review does not authorize selected-profile runtime state, profile
switching execution, machine changes, anchor loading execution, dispatch,
MIDI, ports, package metadata changes, active behavior, or hardware behavior.
