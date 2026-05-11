# V1.34 Behavior Parity Packet 10B Selected Profile Workflow Plan

## 1. Purpose

Define the next tiny behavior-parity planning branch for selected-profile
anchor-load workflow behavior.

This plan is documentation-only. It does not add implementation, tests, CLI
wiring, dispatch, command execution, MIDI, ports, package metadata changes,
active behavior, runtime behavior, selected-profile runtime state, machine
changes, anchor loading execution, or hardware behavior.

## 2. Current Clean Baseline

Current branch:

- `modularize-v1.34`

Current HEAD before this documentation slice:

- `35cbd72 Add Packet 10 progress checkpoint review`

Current phase:

- Passive/Mock Foundation Phase
- behavior-parity implementation phase
- Packet 10A `P` accepted
- Packet 10 progress checkpoint accepted
- Packet 10B `M` behavior now being planned

Hardware status:

- Analog Rytm MKII off
- Analog Four MKII off
- hardware not required

## 3. Accepted Upstream Gate

Accepted upstream checkpoint review:

- `Docs/V134_BEHAVIOR_PARITY_PACKET_10_PROGRESS_CHECKPOINT_REVIEW.md`

The review accepts current Packet 10 progress:

- `P`: implemented and accepted as read-only selected-profile workflow intent
- `M`: deferred/safe

The review recommends:

- docs-only Packet 10B plan for `M`

This plan follows that recommendation.

## 4. Packet 10B Scope

Packet 10B planning scope:

- `M`: load selected profile anchor

Passive metadata source:

- `PROFILE_WORKFLOW_COMMANDS`

Future Packet 10B implementation should remain in the existing selected
profile helper surface:

- `rytm_randomizer/behavior_selected_profile.py`
- `tests/test_behavior_selected_profile.py`

No new runtime owner is authorized by this plan.

## 5. Recommended Future Implementation Target

Recommended future Packet 10B implementation target:

- `M` only

Command meaning:

- `M`: load selected profile anchor

Reasons for choosing `M` now:

- It is the only deferred Packet 10 command after accepted Packet 10A.
- `P` has already established selected-profile workflow result shape.
- `M` can be represented as read-only selected-profile anchor-load intent
  without loading an anchor.
- Planning `M` closes the current Packet 10 selected-profile workflow surface
  without adding runtime selected-profile state.

## 6. Proposed Future Read-Only Behavior For Packet 10B

A future Packet 10B implementation may model `M` as deterministic read-only
intent only.

Expected future result shape:

- command key: `M`
- label: load selected profile anchor
- source metadata: `PROFILE_WORKFLOW_COMMANDS`
- source scope: `selected_profile`
- behavior family: `selected-profile-workflow/selected-profile-anchor-load`
- workflow action: `describe_selected_profile_anchor_load_intent`
- intent kind: `selected_profile_anchor_load`
- uses selected profile: true
- selected profile dependency: `current_selected_profile_state`
- anchor load intent: true
- selected-profile runtime state exists: false
- anchor load executed: false
- machine change executed: false
- accepted: true
- mock-only: true
- sends real MIDI: false
- opens ports: false
- hardware required: false
- active behavior: false

The helper may describe selected-profile anchor-load intent, but it must not
read a selected-profile runtime state, create a selected-profile runtime state,
load an anchor, change machines, mutate runtime state, dispatch commands,
execute commands, open ports, send MIDI, or touch hardware.

## 7. Expected Future Test Coverage

Future Packet 10B tests should verify:

- importing the helper still prints nothing
- `M` returns deterministic accepted read-only selected-profile anchor-load
  intent data
- `M` copies existing `PROFILE_WORKFLOW_COMMANDS` metadata
- `M` records source scope `selected_profile`
- `M` records behavior family
  `selected-profile-workflow/selected-profile-anchor-load`
- `M` records workflow action
  `describe_selected_profile_anchor_load_intent`
- `M` records intent kind `selected_profile_anchor_load`
- `M` records `uses_selected_profile` as true
- `M` records `anchor_load_intent` as true
- `M` records selected-profile dependency as `current_selected_profile_state`
- `M` records that selected-profile runtime state does not exist in the helper
- `M` records that anchor loading execution does not occur
- `M` records that machine change execution does not occur
- displayed or formatted behavior says no MIDI, no ports, no hardware, and no
  execution
- returned metadata is copied and mutation-safe
- `P` behavior remains unchanged
- unknown keys fail safely
- Packet 2 direct anchor/profile behavior remains unchanged
- Packet 3 legacy single-profile mutation behavior remains unchanged
- Packet 9 undo/commit/state behavior remains unchanged
- passive CLI behavior remains unchanged
- no real MIDI library is imported
- package metadata remains untouched
- V1.34 reference remains untouched

## 8. Preserved Packet 10A Scope

Packet 10A remains responsible for:

- `P`: select/switch profile and change Rytm machine

Packet 10B must preserve `P` behavior exactly:

- profile selection described only
- machine change described only
- no selected-profile runtime state
- no machine change execution
- no anchor loading execution

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

Packet 10B must not re-own or alter earlier packet behavior.

## 10. Expected Future File Ownership

Future implementation files:

- `rytm_randomizer/behavior_selected_profile.py`
- `tests/test_behavior_selected_profile.py`

Future closeout script update:

- none expected, because `tests/test_behavior_selected_profile.py` is already
  covered by `=== Test: Behavior Selected Profile ===`

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

Before any future Packet 10B implementation:

- clean Git status
- closeout passes
- V1.34 reference diff is empty
- package metadata diff is empty
- Packet 10B plan accepted in a separate docs-only review
- implementation remains read-only and intent-only
- implementation follows TDD
- Packet 10A `P` behavior remains unchanged
- Packet 2 direct anchor/profile behavior remains unchanged
- Packet 3 legacy single-profile mutation behavior remains unchanged
- Packet 9 undo/commit/state behavior remains unchanged
- no selected-profile runtime state is introduced
- no anchor loading execution is introduced

## 13. Parallelization Position

Do not parallelize immediate Packet 10B implementation.

Packet 10B should be a single narrow TDD slice in the existing selected profile
helper and test file. Parallel work can be reconsidered after Packet 10 is
complete if a broader progress report identifies independent follow-up
branches.

## 14. Safe Next Options

After this plan:

- docs-only Packet 10B plan review
- pause at this clean planning checkpoint
- user-facing progress/timeline update before implementation

## 15. Recommendation

Recommended next task:

- review and accept this Packet 10B selected-profile workflow plan

Then, if accepted:

- implement a tiny TDD Packet 10B read-only behavior helper for `M` only

## 16. Decision

Packet 10B selected-profile workflow behavior is planned.

Future implementation target should be `M` only, read-only and intent-only.

Hardware remains off.

No implementation in this slice.
