# V1.34 Behavior Parity Packet 9C Undo Commit State Behavior Plan

## 1. Purpose

Define the next tiny Packet 9C undo/commit/state behavior planning slice for
`W` only.

This plan is documentation-only. It does not add implementation, tests, CLI
wiring, dispatch, command execution, MIDI, ports, package metadata changes,
active behavior, runtime behavior, or hardware behavior.

## 2. Current Clean Baseline

Current branch:

- `modularize-v1.34`

Current HEAD before this documentation slice:

- `c3a3e14 Add behavior parity progress report review after Packet 9B`

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
- Packet 9B undo/commit/state `E` accepted
- Packet 9C undo/commit/state `W` now being planned

Hardware status:

- Analog Rytm MKII off
- Analog Four MKII off
- hardware not required

## 3. Accepted Upstream Gate

Accepted upstream progress report review:

- `Docs/V134_BEHAVIOR_PARITY_IMPLEMENTATION_PROGRESS_REPORT_AFTER_PACKET_9B_REVIEW.md`

The review accepts the current Packet 9 boundary:

- `B` accepted
- `E` accepted
- `W` deferred/safe
- `U` deferred/safe
- `H` and `R` remain Packet 1 menu/status behavior

The upstream review recommends a docs-only Packet 9C plan for `W` only if
continuing behavior-parity work.

## 4. Packet 9C Planning Choice

Packet 9C planning scope:

- `W` only

Command meaning:

- `W`: waveform exploration only

Reasons for choosing `W` next:

- It is an existing `STATE_UTILITY_COMMANDS` command.
- It is narrower than undo-stack behavior.
- It can be modeled as read-only waveform-exploration intent without selecting
  waveforms or mutating sound state.
- It lets the project define waveform-exploration vocabulary without runtime
  exploration behavior.
- It preserves `U` as the remaining deferred/safe Packet 9 case.
- It keeps `H` and `R` in Packet 1 menu/status ownership.

## 5. Proposed Future Read-Only Behavior

A future Packet 9C implementation may model `W` as deterministic read-only
intent only.

Expected future result shape:

- command key: `W`
- label: waveform exploration only
- source metadata: `STATE_UTILITY_COMMANDS`
- target scope: waveform exploration
- behavior family: `undo-commit-state/waveform-exploration`
- state action: `describe_waveform_exploration_intent`
- intent kind: `waveform_exploration`
- exploration concept: waveform exploration only
- lifecycle effect: `described_only`
- accepted: true
- mock-only: true
- sends real MIDI: false
- opens ports: false
- hardware required: false
- active behavior: false

The helper may describe the intended waveform-exploration concept, but it must
not select waveforms, randomize waveforms, mutate runtime state, mutate anchor
state, update files, dispatch commands, execute commands, open ports, send
MIDI, or touch hardware.

## 6. Expected Future Test Coverage

Future Packet 9C tests should verify:

- existing `B` behavior remains unchanged
- existing `E` behavior remains unchanged
- `W` returns deterministic accepted read-only intent data
- `W` copies existing `STATE_UTILITY_COMMANDS` metadata
- `W` records target scope `waveform_exploration`
- `W` records behavior family `undo-commit-state/waveform-exploration`
- `W` records state action `describe_waveform_exploration_intent`
- `W` records intent kind `waveform_exploration`
- `W` records exploration concept `waveform exploration only`
- `W` records lifecycle effect `described_only`
- displayed or formatted behavior says no MIDI, no ports, no hardware, no
  execution, no waveform mutation, and no state mutation
- returned metadata is copied and mutation-safe
- `U` remains unsupported/safe until separately planned
- unknown keys fail safely
- Packet 1 `H` and `R` menu/status behavior remains unchanged
- passive CLI behavior remains unchanged
- no real MIDI library is imported
- package metadata remains untouched
- V1.34 reference remains untouched

## 7. Existing And Deferred Packet 9 Scope

Already implemented and accepted:

- `B`: back to current anchor
- `E`: commit current state as new anchor

Planned future Packet 9C implementation candidate:

- `W`: waveform exploration only

Deferred/safe Packet 9 scope:

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

No waveform selection.

No waveform randomization.

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

Before any future Packet 9C implementation:

- clean Git status
- closeout passes
- V1.34 reference diff is empty
- package metadata diff is empty
- Packet 9C plan accepted in a separate docs-only review
- `B` behavior remains unchanged
- `E` behavior remains unchanged
- `U` remains deferred/safe
- Packet 1 `H` and `R` behavior remains unchanged
- implementation remains read-only and intent-only
- implementation follows TDD
- no waveform exploration execution is introduced
- no runtime state mutation is introduced

## 11. Parallelization Position

Do not parallelize immediate Packet 9C implementation.

Packet 9C touches the same helper and test file as Packet 9A and Packet 9B.
The waveform-exploration vocabulary should be added in one narrow path before
the remaining `U` planning.

Parallel implementation can be reconsidered later only if future work splits
into independent files, independent tests, and a clear closeout synchronization
point.

## 12. Safe Next Options

After this plan:

- docs-only Packet 9C plan review
- user-facing progress/timeline update
- pause at this clean planning checkpoint

After a separate plan review:

- tiny TDD Packet 9C implementation for read-only `W` intent only

## 13. Recommendation

Proceed next with a docs-only Packet 9C plan review.

Do not implement `W`, `U`, dispatch, MIDI, ports, package metadata changes,
active behavior, runtime execution, or hardware behavior without the separate
Packet 9C plan review.

## 14. Decision

Packet 9C is planned as a tiny future read-only `W` behavior slice.

Hardware remains off.

No implementation in this slice.
