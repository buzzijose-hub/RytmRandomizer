# V1.34 Behavior Parity Packet 9B Undo Commit State Behavior Plan

## 1. Purpose

Define the next tiny Packet 9B undo/commit/state behavior planning slice for
`E` only.

This plan is documentation-only. It does not add implementation, tests, CLI
wiring, dispatch, command execution, MIDI, ports, package metadata changes,
active behavior, runtime behavior, or hardware behavior.

## 2. Current Clean Baseline

Current branch:

- `modularize-v1.34`

Current HEAD before this documentation slice:

- `c024b5a Add behavior parity progress report review after Packet 9A`

Current phase:

- Passive/Mock Foundation Phase
- behavior-parity implementation phase
- Packet 1 complete and accepted
- Packet 2 accepted as meaningful read-only anchor/profile progress
- Packet 3 complete and accepted
- Packet 4 complete and accepted
- Packet 5 accepted as Pad 1 lane behavior progress
- Packet 6 Pad 2 command-helper scope covered
- Packet 7 complete and accepted
- Packet 8 Pad 4 command-helper scope covered
- Packet 9A undo/commit/state `B` accepted
- Packet 9B undo/commit/state `E` now being planned

Hardware status:

- Analog Rytm MKII off
- Analog Four MKII off
- hardware not required

## 3. Accepted Upstream Gate

Accepted upstream progress report review:

- `Docs/V134_BEHAVIOR_PARITY_IMPLEMENTATION_PROGRESS_REPORT_AFTER_PACKET_9A_REVIEW.md`

The review accepts the current Packet 9 boundary:

- `B` accepted
- `E` deferred/safe
- `W` deferred/safe
- `U` deferred/safe
- `H` and `R` remain Packet 1 menu/status behavior

The upstream review recommends a docs-only Packet 9B plan for `E` only if
continuing behavior-parity work.

## 4. Packet 9B Planning Choice

Packet 9B planning scope:

- `E` only

Command meaning:

- `E`: commit current state as new anchor

Reasons for choosing `E` next:

- It is an existing `STATE_UTILITY_COMMANDS` command.
- It is the next smallest Packet 9 command after accepted `B` behavior.
- It can be modeled as read-only anchor-commit intent without committing an
  anchor.
- It lets the project define anchor lifecycle vocabulary without runtime state
  mutation.
- It preserves `W` and `U` as explicit deferred/safe cases.
- It keeps `H` and `R` in Packet 1 menu/status ownership.

## 5. Proposed Future Read-Only Behavior

A future Packet 9B implementation may model `E` as deterministic read-only
intent only.

Expected future result shape:

- command key: `E`
- label: commit current state as new anchor
- source metadata: `STATE_UTILITY_COMMANDS`
- target scope: current anchor state
- behavior family: `undo-commit-state/current-state-anchor-commit`
- state action: `describe_current_state_anchor_commit_intent`
- intent kind: `anchor_commit`
- anchor concept: current state as new anchor
- lifecycle effect: described only
- accepted: true
- mock-only: true
- sends real MIDI: false
- opens ports: false
- hardware required: false
- active behavior: false

The helper may describe the intended anchor-commit concept, but it must not
commit anchors, mutate runtime state, mutate anchor state, update files,
dispatch commands, execute commands, open ports, send MIDI, or touch hardware.

## 6. Expected Future Test Coverage

Future Packet 9B tests should verify:

- existing `B` behavior remains unchanged
- `E` returns deterministic accepted read-only intent data
- `E` copies existing `STATE_UTILITY_COMMANDS` metadata
- `E` records target scope `current_anchor_state`
- `E` records behavior family
  `undo-commit-state/current-state-anchor-commit`
- `E` records state action
  `describe_current_state_anchor_commit_intent`
- `E` records intent kind `anchor_commit`
- `E` records anchor concept `current state as new anchor`
- `E` records lifecycle effect `described_only`
- displayed or formatted behavior says no MIDI, no ports, no hardware, no
  execution, and no state mutation
- returned metadata is copied and mutation-safe
- `W` and `U` remain unsupported/safe until separately planned
- unknown keys fail safely
- Packet 1 `H` and `R` menu/status behavior remains unchanged
- passive CLI behavior remains unchanged
- no real MIDI library is imported
- package metadata remains untouched
- V1.34 reference remains untouched

## 7. Existing And Deferred Packet 9 Scope

Already implemented and accepted:

- `B`: back to current anchor

Planned future Packet 9B implementation candidate:

- `E`: commit current state as new anchor

Deferred/safe Packet 9 scope:

- `W`: waveform exploration only
- `U`: undo previous script-generated state

Preserved Packet 1 ownership:

- `H`: show current anchor
- `R`: print current script state

Packet 9 is not complete in this planning slice.

## 8. Expected Future File Ownership

Future implementation files:

- `rytm_randomizer/behavior_undo_commit_state.py`
- `tests/test_behavior_undo_commit_state.py`

No closeout script update is expected because `tests/test_behavior_undo_commit_state.py`
is already covered by:

- `=== Test: Behavior Undo Commit State ===`

## 9. Non-Goals

No implementation in this slice.

No tests in this slice.

No CLI execution wiring.

No dispatch.

No command execution.

No prompt/input loop.

No runtime state mutation.

No undo stack mutation.

No anchor commit execution.

No anchor restore execution.

No waveform exploration execution.

No file persistence.

No real MIDI.

No `mido`.

No `rtmidi`.

No port opening.

No MIDI sending.

No package metadata changes.

No active behavior.

No hardware behavior.

No hardware validation.

## 10. Preconditions Before Future Implementation

Before any future Packet 9B implementation:

- clean Git status
- closeout passes
- V1.34 reference diff is empty
- package metadata diff is empty
- Packet 9B plan accepted in a separate docs-only review
- `B` behavior remains unchanged
- `W` and `U` remain deferred/safe
- Packet 1 `H` and `R` behavior remains unchanged
- implementation remains read-only and intent-only
- implementation follows TDD
- no runtime anchor state mutation is introduced

## 11. Parallelization Position

Do not parallelize immediate Packet 9B implementation.

Packet 9B touches the same helper and test file as Packet 9A. The anchor-commit
vocabulary should be added in one narrow path before later `W` or `U`
planning.

Parallel implementation can be reconsidered later only if future Packet 9
sub-slices split into independent files, independent tests, and a clear
closeout synchronization point.

## 12. Safe Next Options

After this plan:

- docs-only Packet 9B plan review
- user-facing progress/timeline update
- pause at this clean planning checkpoint

After a separate plan review:

- tiny TDD Packet 9B implementation for read-only `E` intent only

## 13. Recommendation

Proceed next with a docs-only Packet 9B plan review.

Do not implement `E`, `W`, `U`, dispatch, MIDI, ports, package metadata
changes, active behavior, runtime execution, or hardware behavior without the
separate Packet 9B plan review.

## 14. Decision

Packet 9B is planned as a tiny future read-only `E` behavior slice.

Hardware remains off.

No implementation in this slice.

## 15. Review Status

This plan is reviewed by:

- `Docs/V134_BEHAVIOR_PARITY_PACKET_9B_UNDO_COMMIT_STATE_BEHAVIOR_PLAN_REVIEW.md`

The review accepts the future tiny Packet 9B implementation scope for `E`
only.

The review keeps `B` unchanged, keeps `W` and `U` deferred/safe, keeps `H` and
`R` in Packet 1 menu/status ownership, and adds no implementation, tests, CLI
wiring, dispatch, command execution, runtime anchor state mutation, MIDI,
ports, package metadata changes, active behavior, or hardware behavior.
