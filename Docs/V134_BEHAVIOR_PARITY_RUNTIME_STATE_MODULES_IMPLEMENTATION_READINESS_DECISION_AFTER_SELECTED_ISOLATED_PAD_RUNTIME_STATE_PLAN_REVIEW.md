# V1.34 Behavior Parity Runtime-State Modules Implementation Readiness Decision After Selected Isolated Pad Runtime-State Plan Review

## 1. Purpose

Decide whether the planned runtime-state modules are ready for a future
test-first implementation sequence after the selected isolated pad
runtime-state implementation plan has been reviewed and accepted.

This is a documentation-only readiness decision.

It does not implement selected target state, anchor state, selected isolated
pad runtime state, `PZ`, dispatch, MIDI, ports, active behavior, or hardware
behavior.

## 2. Current Clean Baseline

Current branch:

- `modularize-v1.34`

Current HEAD before this decision slice:

- `69f3178 Add selected isolated pad runtime state plan review`

Current phase:

- passive/mock foundation
- V1.34 behavior-parity implementation packets
- passive behavior reports and CLI visibility
- runtime-state vocabulary accepted for planning
- `PZ` behavior plan accepted for planning
- selected target state implementation plan accepted
- anchor state implementation plan accepted
- selected isolated pad runtime-state implementation plan accepted
- runtime-state module implementation readiness now being decided

Hardware status:

- Analog Rytm MKII off
- Analog Four MKII off
- hardware not required

## 3. Accepted Planning Inputs

Accepted planning inputs:

- selected target state implementation plan:
  - `Docs/V134_BEHAVIOR_PARITY_SELECTED_TARGET_STATE_IMPLEMENTATION_PLAN_AFTER_RUNTIME_STATE_SEQUENCING_REVIEW.md`
- selected target state implementation plan review:
  - `Docs/V134_BEHAVIOR_PARITY_SELECTED_TARGET_STATE_IMPLEMENTATION_PLAN_AFTER_RUNTIME_STATE_SEQUENCING_REVIEW_REVIEW.md`
- anchor state implementation plan:
  - `Docs/V134_BEHAVIOR_PARITY_ANCHOR_STATE_IMPLEMENTATION_PLAN_AFTER_SELECTED_TARGET_IMPLEMENTATION_REVIEW.md`
- anchor state implementation plan review:
  - `Docs/V134_BEHAVIOR_PARITY_ANCHOR_STATE_IMPLEMENTATION_PLAN_AFTER_SELECTED_TARGET_IMPLEMENTATION_REVIEW_REVIEW.md`
- selected isolated pad runtime-state implementation plan update:
  - `Docs/V134_BEHAVIOR_PARITY_SELECTED_ISOLATED_PAD_RUNTIME_STATE_IMPLEMENTATION_PLAN_AFTER_SELECTED_TARGET_AND_ANCHOR_STATE_REVIEWS.md`
- selected isolated pad runtime-state implementation plan update review:
  - `Docs/V134_BEHAVIOR_PARITY_SELECTED_ISOLATED_PAD_RUNTIME_STATE_IMPLEMENTATION_PLAN_AFTER_SELECTED_TARGET_AND_ANCHOR_STATE_REVIEWS_REVIEW.md`

These documents establish planning boundaries only.

They do not implement runtime behavior.

## 4. Readiness Decision

Decision:

- the runtime-state module implementation sequence is ready to be approached
  in future separate test-first implementation slices
- the first future implementation slice should be selected target state only
- anchor state should remain second
- selected isolated pad runtime state should remain third
- `PZ` must remain parked until all three state modules are implemented,
  reviewed, and accepted

This decision does not authorize implementation by itself.

It records readiness for a future implementation packet only.

## 5. Accepted Implementation Order

Accepted future implementation order:

1. selected target state
2. anchor state
3. selected isolated pad runtime state
4. `PZ` reconsideration only after separate review

Reason:

- selected target state is the smallest layer
- anchor state depends on target meaning
- selected isolated pad runtime state can validate target and anchor together
- `PZ` should not be reconsidered until those validations exist

## 6. First Future Implementation Candidate

The first future implementation candidate should be:

- `rytm_randomizer/selected_target_state.py`
- `tests/test_selected_target_state.py`

The first candidate should stay limited to:

- unset target state
- defaulted Pad 3 selected isolated pad target state
- unsupported target safe failures
- stale target safe failures
- invalid target safe failures
- deterministic explanatory results
- copied/immutable-ish result behavior
- import side-effect safety

The first candidate should not include:

- anchor state
- selected isolated pad runtime state
- `PZ`
- selected pad switching
- anchor return
- runtime mutation
- CLI wiring
- dispatch
- MIDI
- ports
- hardware behavior

## 7. Second Future Implementation Candidate

The second future implementation candidate should be:

- `rytm_randomizer/anchor_state.py`
- `tests/test_anchor_state.py`

It should start only after selected target state implementation is complete,
reviewed, and accepted.

It should stay limited to:

- unknown anchor state
- unsupported anchor safe failures
- stale anchor safe failures
- invalid anchor safe failures
- deterministic explanatory results
- copied/immutable-ish result behavior
- import side-effect safety

Optional static/software-known anchor behavior should remain separately
reviewable if there is uncertainty.

It should not include:

- selected target state ownership
- selected isolated pad runtime state
- `PZ`
- anchor return
- hardware capture
- dispatch
- MIDI
- ports
- hardware behavior

## 8. Third Future Implementation Candidate

The third future implementation candidate should be:

- `rytm_randomizer/selected_isolated_pad_runtime_state.py`
- `tests/test_selected_isolated_pad_runtime_state.py`

It should start only after selected target state and anchor state
implementations are complete, reviewed, and accepted.

It should stay limited to:

- uninitialized selected isolated pad runtime state
- passive-default Pad 3 selected isolated pad runtime state
- missing selected target state safe failure
- missing anchor state safe failure
- unsupported target safe failure
- unsupported anchor safe failure
- stale target safe failure
- stale anchor safe failure
- invalid target safe failure
- invalid anchor safe failure
- deterministic explanatory results
- copied/immutable-ish result behavior
- import side-effect safety

Optional target-anchor match or mismatch behavior should remain separately
reviewable if there is uncertainty.

It should not include:

- selected target state ownership
- anchor state ownership
- `PZ`
- selected pad switching
- anchor return
- runtime mutation unless separately approved
- CLI wiring
- dispatch
- MIDI
- ports
- hardware behavior

## 9. PZ Position

`PZ` remains parked.

`PZ` must not be implemented during selected target state, anchor state, or
selected isolated pad runtime-state implementation.

Future `PZ` reconsideration requires:

- selected target state implemented and reviewed
- anchor state implemented and reviewed
- selected isolated pad runtime state implemented and reviewed
- closeout passing
- V1.34 reference diff empty
- package metadata diff empty
- passive CLI still read-only
- no MIDI, ports, active behavior, runtime execution, or hardware behavior
  unless separately approved in a later slice

## 10. Required Test-First Discipline

Every future implementation slice must be test-first.

Before writing implementation code, each slice should add focused tests that
prove:

- import side-effect safety
- deterministic safe default behavior
- unsupported scope fails safely
- stale/invalid state fails safely
- copied/immutable-ish result behavior
- repeated evaluations are deterministic
- passive CLI behavior remains unchanged
- no active command names are exposed
- no real MIDI libraries are imported
- no ports are opened
- no MIDI is sent
- V1.34 reference remains untouched
- package metadata remains untouched

No tests are added by this document.

## 11. Closeout Expectations

For each future implementation slice:

- run full closeout
- confirm V1.34 reference diff is empty
- confirm package metadata diff is empty
- confirm git status is clean before and after commit
- update `Scripts/closeout_check.ps1` only if a new test file is added
- keep any closeout update limited to a new test label

No closeout script change is made by this document.

## 12. Confirmed Absent Behavior

This readiness decision confirms no:

- code changes
- test changes
- closeout script changes
- package metadata changes
- selected target state implementation
- anchor state implementation
- selected isolated pad runtime-state implementation
- runtime state implementation
- selected pad switching execution
- selected pad anchor return execution
- `PZ` implementation
- active CLI command
- `execute-command`
- `send-command`
- `hardware-test`
- dispatch
- command execution
- scene execution
- mutation execution
- direct behavior helper execution from CLI
- real MIDI dependency
- `mido`
- `rtmidi`
- port discovery
- port opening
- MIDI sending
- hardware behavior
- hardware validation
- true hardware capture
- SysEx
- GUI/capture
- Analog Four support
- Pads 5-12 support
- machine/profile universe expansion

`rytm_hybrid_randomizer_v134.py` remains untouched.

Package metadata remains untouched.

## 13. Preconditions Before First Implementation Slice

Before selected target state implementation begins:

- clean Git status
- full closeout passing
- V1.34 reference diff empty
- package metadata diff empty
- this readiness decision reviewed and accepted, or explicitly confirmed as
  the current implementation gate
- selected target state implementation plan reviewed and accepted
- passive CLI behavior remains read-only
- no active CLI behavior is added
- no MIDI libraries are imported
- no ports are opened
- no MIDI is sent
- no hardware is required

## 14. Safe Next Options

Safe next options:

- docs-only review/acceptance gate for this readiness decision
- first test-first selected target state implementation slice
- docs-only selected target state implementation packet plan
- docs-only progress/timeline update
- pause at this clean readiness checkpoint

## 15. Recommendation

Proceed with a docs-only review/acceptance gate for this readiness decision.

After that review, the next implementation-facing step can be a first
test-first selected target state implementation slice.

Do not implement selected target state in this slice.

Do not implement anchor state in this slice.

Do not implement selected isolated pad runtime state in this slice.

Do not implement `PZ`.

Do not add MIDI, ports, active behavior, runtime execution, package metadata
changes, or hardware behavior.

## 16. Decision Summary

Runtime-state module implementation readiness is documented.

Future implementation order is accepted for planning:

1. selected target state
2. anchor state
3. selected isolated pad runtime state
4. `PZ` reconsideration only after separate review

Selected target state remains unimplemented.

Anchor state remains unimplemented.

Selected isolated pad runtime state remains unimplemented.

`PZ` remains parked.

Hardware remains off.

No implementation in this decision slice.
