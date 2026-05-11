# V1.34 Behavior Parity Packet 9D Undo Commit State Behavior Plan

## 1. Purpose

Define the next tiny Packet 9D undo/commit/state behavior planning slice for
`U` only.

This plan is documentation-only. It does not add implementation, tests, CLI
wiring, dispatch, command execution, MIDI, ports, package metadata changes,
active behavior, runtime behavior, undo-stack behavior, or hardware behavior.

## 2. Current Clean Baseline

Current branch:

- `modularize-v1.34`

Current HEAD before this documentation slice:

- `916f550 Add behavior parity progress report review after Packet 9C`

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
- Packet 9C undo/commit/state `W` accepted
- Packet 9D undo/commit/state `U` now being planned

Hardware status:

- Analog Rytm MKII off
- Analog Four MKII off
- hardware not required

## 3. Accepted Upstream Gate

Accepted upstream progress report review:

- `Docs/V134_BEHAVIOR_PARITY_IMPLEMENTATION_PROGRESS_REPORT_AFTER_PACKET_9C_REVIEW.md`

The review accepts the current Packet 9 boundary:

- `B` accepted
- `E` accepted
- `W` accepted
- `U` deferred/safe
- `H` and `R` remain Packet 1 menu/status behavior

The upstream review recommends a docs-only Packet 9D plan for `U` only if
continuing behavior-parity work.

## 4. Packet 9D Planning Choice

Packet 9D planning scope:

- `U` only

Command meaning:

- `U`: undo previous script-generated state

Reasons for choosing `U` next:

- It is the only remaining deferred/safe Packet 9 command.
- It is an existing `STATE_UTILITY_COMMANDS` command.
- It can be modeled as read-only state-history intent without performing an
  undo.
- It completes the Packet 9 behavior-helper planning sequence if later
  implemented and reviewed.
- It preserves `H` and `R` in Packet 1 menu/status ownership.

## 5. Proposed Future Read-Only Behavior

A future Packet 9D implementation may model `U` as deterministic read-only
intent only.

Expected future result shape:

- command key: `U`
- label: undo previous script-generated state
- source metadata: `STATE_UTILITY_COMMANDS`
- source scope: `script_generated_state`
- target scope: `script_generated_state_history`
- behavior family: `undo-commit-state/script-generated-state-undo`
- state action: `describe_previous_script_generated_state_undo_intent`
- intent kind: `state_history_undo`
- history concept: previous script-generated state
- lifecycle effect: `described_only`
- accepted: true
- mock-only: true
- sends real MIDI: false
- opens ports: false
- hardware required: false
- active behavior: false

The helper may describe intended undo behavior, but it must not inspect,
construct, mutate, pop, restore, or persist an undo stack. It must not mutate
runtime state, mutate anchor state, update files, dispatch commands, execute
commands, open ports, send MIDI, or touch hardware.

## 6. Expected Future Test Coverage

Future Packet 9D tests should verify:

- existing `B` behavior remains unchanged
- existing `E` behavior remains unchanged
- existing `W` behavior remains unchanged
- `U` returns deterministic accepted read-only state-history undo intent data
- `U` copies existing `STATE_UTILITY_COMMANDS` metadata
- `U` records source scope `script_generated_state`
- `U` records target scope `script_generated_state_history`
- `U` records behavior family
  `undo-commit-state/script-generated-state-undo`
- `U` records state action
  `describe_previous_script_generated_state_undo_intent`
- `U` records intent kind `state_history_undo`
- `U` records history concept `previous script-generated state`
- `U` records lifecycle effect `described_only`
- displayed or formatted behavior says no MIDI, no ports, no hardware, no
  execution, no undo-stack mutation, and no state mutation
- returned metadata is copied and mutation-safe
- unknown keys fail safely
- Packet 1 `H` and `R` menu/status behavior remains unchanged
- passive CLI behavior remains unchanged
- no real MIDI library is imported
- package metadata remains untouched
- V1.34 reference remains untouched

## 7. Existing Packet 9 Scope

Already implemented and accepted:

- `B`: back to current anchor
- `E`: commit current state as new anchor
- `W`: waveform exploration only

Planned future Packet 9D implementation candidate:

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

No undo stack inspection.

No undo stack mutation.

No undo execution.

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

Before any future Packet 9D implementation:

- clean Git status
- closeout passes
- V1.34 reference diff is empty
- package metadata diff is empty
- Packet 9D plan accepted in a separate docs-only review
- `B` behavior remains unchanged
- `E` behavior remains unchanged
- `W` behavior remains unchanged
- Packet 1 `H` and `R` behavior remains unchanged
- implementation remains read-only and intent-only
- implementation follows TDD
- no undo-stack behavior is introduced
- no runtime state mutation is introduced

## 11. Parallelization Position

Do not parallelize immediate Packet 9D implementation.

Packet 9D touches the same helper and test file as Packet 9A, Packet 9B, and
Packet 9C. The undo-intent vocabulary should be added in one narrow path and
reviewed before any broader Packet 9 completion checkpoint.

Parallel implementation can be reconsidered later only if future work splits
into independent files, independent tests, and a clear closeout synchronization
point.

## 12. Safe Next Options

After this plan:

- docs-only Packet 9D plan review
- user-facing progress/timeline update
- pause at this clean planning checkpoint

After a separate plan review:

- tiny TDD Packet 9D implementation for read-only `U` intent only

## 13. Recommendation

Proceed next with a docs-only Packet 9D plan review.

Do not implement `U`, dispatch, MIDI, ports, package metadata changes, active
behavior, runtime execution, undo execution, or hardware behavior without the
separate Packet 9D plan review.

## 14. Decision

Packet 9D is planned as a tiny future read-only `U` behavior slice.

Hardware remains off.

No implementation in this slice.
