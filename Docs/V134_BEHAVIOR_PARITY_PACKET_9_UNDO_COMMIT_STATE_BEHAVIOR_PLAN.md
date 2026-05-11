# V1.34 Behavior Parity Packet 9 Undo Commit State Behavior Plan

## 1. Purpose

Define the next behavior-parity planning branch for undo, commit, anchor-state,
and waveform-exploration utility behavior.

This plan is documentation-only. It does not add implementation, tests, CLI
wiring, dispatch, command execution, MIDI, ports, package metadata changes,
active behavior, runtime behavior, or hardware behavior.

## 2. Current Clean Baseline

Current branch:

- `modularize-v1.34`

Current HEAD before this documentation slice:

- `5f4dc64 Add next packet planning gate review after Packet 8C`

Current phase:

- Passive/Mock Foundation Phase
- behavior-parity implementation phase
- Packet 1 complete
- Packet 2 accepted as meaningful read-only anchor/profile progress
- Packet 3 complete
- Packet 4 complete
- Packet 5 accepted as Pad 1 lane behavior progress
- Packet 6 Pad 2 command-helper scope covered
- Packet 7 complete
- Packet 8 Pad 4 command-helper scope covered
- Packet 9 undo/commit/state behavior now being planned

Hardware status:

- Analog Rytm MKII off
- Analog Four MKII off
- hardware not required

## 3. Accepted Upstream Gate

Accepted upstream planning gate review:

- `Docs/V134_BEHAVIOR_PARITY_NEXT_PACKET_PLANNING_GATE_AFTER_PACKET_8C_REVIEW.md`

The review accepts the next branch:

- Packet 9 undo/commit/state behavior planning

The review accepts these command keys as Packet 9 planning vocabulary:

- `B`: back to current anchor
- `E`: commit current state as new anchor
- `W`: waveform exploration only
- `U`: undo previous script-generated state

The review keeps Packet 1 ownership for:

- `H`: show current anchor
- `R`: print current script state

## 4. Packet 9 Full Planning Surface

Packet 9 planning surface:

- `B`: back to current anchor
- `E`: commit current state as new anchor
- `W`: waveform exploration only
- `U`: undo previous script-generated state

Passive metadata source:

- `STATE_UTILITY_COMMANDS`

The full Packet 9 surface is not safe to implement all at once because these
commands imply future runtime state vocabulary.

## 5. Recommended First Implementation Subset

Recommended future Packet 9A implementation scope:

- `B` only

Command meaning:

- `B`: back to current anchor

Reasons for choosing `B` first:

- It is an existing `STATE_UTILITY_COMMANDS` command.
- It is narrower than commit, waveform exploration, or undo-stack behavior.
- It can be represented as read-only current-anchor return intent without
  restoring hardware state.
- It allows the project to establish the Packet 9 result shape before touching
  higher-risk state vocabulary.
- It preserves `E`, `W`, and `U` as explicit deferred/safe cases.

## 6. Proposed Future Read-Only Behavior For Packet 9A

A future Packet 9A implementation may model `B` as deterministic read-only
intent only.

Expected future result shape:

- command key: `B`
- label: back to current anchor
- source metadata: `STATE_UTILITY_COMMANDS`
- target scope: current anchor
- behavior family: `undo-commit-state/current-anchor-return`
- state action: `describe_current_anchor_return_intent`
- intent kind: `anchor_return`
- anchor concept: current anchor
- accepted: true
- mock-only: true
- sends real MIDI: false
- opens ports: false
- hardware required: false
- active behavior: false

The helper may describe the intended current-anchor return concept, but it
must not restore runtime state, load anchors, mutate anchors, dispatch
commands, execute commands, open ports, send MIDI, or touch hardware.

## 7. Expected Future Test Coverage

Future Packet 9A tests should verify:

- importing the helper prints nothing
- `B` returns deterministic accepted read-only intent data
- `B` copies existing `STATE_UTILITY_COMMANDS` metadata
- `B` records target scope `current_anchor`
- `B` records behavior family `undo-commit-state/current-anchor-return`
- `B` records state action `describe_current_anchor_return_intent`
- `B` records intent kind `anchor_return`
- `B` records anchor concept `current anchor`
- displayed or formatted behavior says no MIDI, no ports, no hardware, and no
  execution
- returned metadata is copied and mutation-safe
- `E`, `W`, and `U` remain unsupported/safe until separately planned
- unknown keys fail safely
- Packet 1 `H` and `R` menu/status behavior remains unchanged
- passive CLI behavior remains unchanged
- no real MIDI library is imported
- package metadata remains untouched
- V1.34 reference remains untouched

## 8. Deferred Packet 9 Scope

Deferred/safe Packet 9 scope:

- `E`: commit current state as new anchor
- `W`: waveform exploration only
- `U`: undo previous script-generated state

Reasons to defer:

- `E` implies future anchor commit/lifecycle semantics.
- `W` implies future waveform exploration workflow semantics.
- `U` implies future state-history or undo-stack semantics.
- Each should receive a separate docs-only plan and review before any
  implementation.

## 9. Preserved Packet 1 Ownership

Packet 1 remains responsible for read-only menu/status behavior:

- `H`: show current anchor
- `R`: print current script state

Packet 9 must not re-own or alter `H` or `R`.

## 10. Expected Future File Ownership

Future implementation files:

- `rytm_randomizer/behavior_undo_commit_state.py`
- `tests/test_behavior_undo_commit_state.py`

Future closeout script update:

- `Scripts/closeout_check.ps1`, only to add the new test file with a label such
  as `=== Test: Behavior Undo Commit State ===`

No file is changed by this planning slice beyond documentation.

## 11. Non-Goals

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

Before any future Packet 9A implementation:

- clean Git status
- closeout passes
- V1.34 reference diff is empty
- package metadata diff is empty
- Packet 9 plan accepted in a separate docs-only review
- implementation remains read-only and intent-only
- implementation follows TDD
- Packet 1 `H` and `R` behavior remains unchanged
- `E`, `W`, and `U` remain deferred/safe

## 13. Parallelization Position

Do not parallelize immediate Packet 9A implementation.

The first Packet 9 slice should establish the undo/commit/state result shape,
safe-failure vocabulary, and closeout coverage in one narrow path before any
parallel work.

Parallel implementation can be reconsidered later only if future Packet 9
sub-slices split into independent files, independent tests, and a clear
closeout synchronization point.

## 14. Safe Next Options

After this plan:

- docs-only Packet 9 plan review
- pause at this clean planning checkpoint

After a separate plan review:

- tiny TDD Packet 9A implementation for read-only `B` intent only

## 15. Recommendation

Proceed next with a docs-only Packet 9 plan review.

Do not implement `B`, `E`, `W`, `U`, dispatch, MIDI, ports, package metadata
changes, active behavior, runtime execution, or hardware behavior without the
separate Packet 9 plan review.

## 16. Decision

Packet 9 is planned as undo/commit/state behavior parity.

The recommended first implementation slice is Packet 9A for read-only `B`
intent only.

Hardware remains off.

No implementation in this slice.

## 17. Review Status

This plan is reviewed by:

- `Docs/V134_BEHAVIOR_PARITY_PACKET_9_UNDO_COMMIT_STATE_BEHAVIOR_PLAN_REVIEW.md`

The review accepts Packet 9 as undo/commit/state behavior parity and accepts a
future tiny Packet 9A implementation scope for read-only `B` intent only.

The review keeps `E`, `W`, and `U` deferred/safe, keeps `H` and `R` in Packet 1
ownership, and adds no implementation, tests, CLI wiring, dispatch, command
execution, MIDI, ports, package metadata changes, active behavior, runtime
behavior, or hardware behavior.
