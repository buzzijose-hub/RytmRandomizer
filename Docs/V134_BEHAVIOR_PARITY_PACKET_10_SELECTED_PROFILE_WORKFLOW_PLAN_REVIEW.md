# V1.34 Behavior Parity Packet 10 Selected Profile Workflow Plan Review

## 1. Purpose

Review and accept the Packet 10 selected-profile workflow behavior plan.

This is a documentation-only review gate. It adds no implementation, tests,
CLI wiring, dispatch, command execution, MIDI, ports, package metadata
changes, active behavior, runtime behavior, selected-profile runtime state,
machine changes, anchor loading execution, or hardware behavior.

## 2. Current Clean Baseline

Current branch:

- `modularize-v1.34`

Current HEAD before this review slice:

- `1ea99fb Add Packet 10 selected profile workflow plan`

Current phase:

- Passive/Mock Foundation Phase
- behavior-parity implementation phase
- Packet 9 covered and accepted for the current read-only intent-only behavior
  phase
- Packet 10 selected-profile workflow behavior plan created
- Packet 10 selected-profile workflow behavior plan now being reviewed

Hardware status:

- Analog Rytm MKII off
- Analog Four MKII off
- hardware not required

## 3. Review Decision

Accepted plan:

- `Docs/V134_BEHAVIOR_PARITY_PACKET_10_SELECTED_PROFILE_WORKFLOW_PLAN.md`

Accepted plan milestone:

- `1ea99fb Add Packet 10 selected profile workflow plan`

The plan is accepted as the current behavior-parity planning document for
selected-profile workflow behavior.

## 4. Accepted Packet 10 Planning Surface

Accepted Packet 10 planning surface:

- `P`: select/switch profile and change Rytm machine
- `M`: load selected profile anchor

Accepted passive metadata source:

- `PROFILE_WORKFLOW_COMMANDS`

The full Packet 10 surface is not accepted for immediate implementation all at
once.

## 5. Accepted First Implementation Target

Accepted future first implementation target:

- Packet 10A `P` only

Accepted future command meaning:

- `P`: select/switch profile and change Rytm machine

Accepted future behavior:

- read-only profile selection and machine-change intent
- existing `PROFILE_WORKFLOW_COMMANDS` metadata
- source scope `profile_machine`
- behavior family `selected-profile-workflow/profile-selection`
- workflow action `describe_profile_selection_machine_change_intent`
- intent kind `profile_machine_selection`
- selected-profile runtime state remains absent
- machine change execution remains absent

This review does not implement Packet 10A. It only accepts `P` as the first
future implementation target.

## 6. Deferred Packet 10 Scope

Deferred/safe Packet 10 scope:

- `M`: load selected profile anchor

Accepted reason for deferral:

- `M` depends on selected-profile workflow vocabulary.
- `M` implies future selected-profile anchor loading language.
- `M` should remain unsupported/safe until `P` establishes the read-only
  selected-profile workflow result shape.
- `M` must receive a separate docs-only plan and review before any
  implementation.

## 7. Expected Future File Ownership

Accepted future implementation files:

- `rytm_randomizer/behavior_selected_profile.py`
- `tests/test_behavior_selected_profile.py`

Accepted future closeout update:

- `Scripts/closeout_check.ps1`, only to add the future test file with a label
  such as `=== Test: Behavior Selected Profile ===`

No files are changed by this review beyond documentation.

## 8. Confirmed Absent Behavior

This review confirms the accepted Packet 10 plan adds no:

- implementation
- tests
- CLI execution wiring
- command dispatch
- command execution
- scene execution
- prompt/input loop
- selected-profile runtime state
- current-profile runtime state
- profile switching execution
- machine change execution
- anchor loading execution
- active selected-profile mutation
- MIDI dependency
- `mido`
- `rtmidi`
- package metadata changes
- MIDI port discovery
- MIDI port opening
- MIDI sending
- active CLI command
- `execute-command`
- `send-command`
- `hardware-test`
- hardware behavior
- hardware validation
- machine/profile universe expansion
- Analog Four support
- Pads 5-12 support
- SysEx
- GUI/capture

`rytm_hybrid_randomizer_v134.py` remains untouched.

Package metadata remains untouched.

## 9. Preconditions Before Any Packet 10A Implementation

Before any Packet 10A implementation begins:

- Git status must be clean.
- Full closeout must pass.
- V1.34 reference diff must be empty.
- Package metadata diff must be empty.
- This Packet 10 plan review must be accepted.
- The first implementation subset must be `P` only.
- The implementation must remain read-only and intent-only.
- Implementation must follow TDD.
- Packet 2 direct anchor/profile behavior must remain unchanged.
- Packet 3 legacy single-profile mutation behavior must remain unchanged.
- Packet 9 undo/commit/state behavior must remain unchanged.
- `M` must remain deferred/safe.
- Runtime selected-profile state, profile switching execution, machine changes,
  anchor loading execution, dispatch, command execution, MIDI, ports, package
  metadata, active behavior, and hardware behavior must remain out of scope.

## 10. Safe Next Options

Safe next options:

- tiny TDD Packet 10A implementation for read-only `P` intent only
- user-facing progress/timeline update before implementation
- pause at this clean accepted Packet 10 planning checkpoint

## 11. Recommendation

Prefer:

- tiny TDD Packet 10A implementation for read-only `P` intent only

Do not implement `M` yet.

Do not add selected-profile runtime state, profile switching execution, machine
changes, anchor loading execution, dispatch, MIDI, ports, package metadata
changes, active behavior, or hardware behavior from this review.

## 12. Decision

The Packet 10 selected-profile workflow plan is accepted.

Packet 10A `P` is the recommended next tiny behavior-parity implementation
target.

Hardware remains off.

No implementation in this review slice.

## 13. Follow-Up Status

Follow-up checkpoint:

- `Docs/V134_BEHAVIOR_PARITY_PACKET_10A_SELECTED_PROFILE_WORKFLOW_CHECKPOINT.md`

Follow-up implementation milestone:

- `c8763ce Add Packet 10A selected profile behavior`

Implemented read-only scope:

- Packet 10A `P`: select/switch profile and change Rytm machine

Deferred/safe scope:

- `M`

The follow-up implementation adds no selected-profile runtime state, profile
switching execution, machine changes, anchor loading execution, dispatch,
MIDI, ports, package metadata changes, active behavior, or hardware behavior.
