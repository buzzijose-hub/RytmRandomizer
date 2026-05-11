# V1.34 Behavior Parity Selected Target State Implementation Plan After Runtime-State Sequencing Review

## 1. Purpose

Define the future selected target state implementation plan after the accepted
runtime-state implementation sequencing review.

This is a documentation-only implementation plan.

It describes the smallest safe future implementation surface for selected
isolated pad target state.

It adds no implementation, tests, CLI commands, runtime state, dispatch, MIDI,
ports, package metadata changes, active behavior, or hardware behavior.

## 2. Current Clean Baseline

Current branch:

- `modularize-v1.34`

Current HEAD before this planning slice:

- `be9e91a Add runtime-state implementation sequencing review`

Current phase:

- passive/mock foundation
- V1.34 behavior-parity implementation packets
- passive behavior reports and CLI visibility
- runtime-state vocabulary accepted for planning
- `PZ` behavior plan accepted for planning
- selected target state plan accepted for planning
- anchor state plan accepted for planning
- selected isolated pad runtime-state plan accepted for planning
- selected isolated pad runtime-state implementation plan accepted
- runtime-state implementation sequencing accepted
- selected target state implementation now being planned at documentation
  level

Hardware status:

- Analog Rytm MKII off
- Analog Four MKII off
- hardware not required

## 3. Accepted Upstream Context

Accepted upstream context:

- selected target state plan review:
  - `Docs/V134_BEHAVIOR_PARITY_SELECTED_TARGET_STATE_PLAN_AFTER_PZ_REVIEW_REVIEW.md`
- anchor state plan review:
  - `Docs/V134_BEHAVIOR_PARITY_ANCHOR_STATE_PLAN_AFTER_SELECTED_TARGET_REVIEW_REVIEW.md`
- selected isolated pad runtime-state plan review:
  - `Docs/V134_BEHAVIOR_PARITY_SELECTED_ISOLATED_PAD_RUNTIME_STATE_PLAN_AFTER_ANCHOR_STATE_REVIEW_REVIEW.md`
- selected isolated pad runtime-state implementation plan review:
  - `Docs/V134_BEHAVIOR_PARITY_SELECTED_ISOLATED_PAD_RUNTIME_STATE_IMPLEMENTATION_PLAN_AFTER_PZ_READINESS_REVIEW_REVIEW.md`
- runtime-state implementation sequencing review:
  - `Docs/V134_BEHAVIOR_PARITY_RUNTIME_STATE_IMPLEMENTATION_SEQUENCING_NOTE_AFTER_SELECTED_ISOLATED_PAD_RUNTIME_STATE_REVIEW_REVIEW.md`

These documents establish planning vocabulary, implementation order, and
safety boundaries only.

They do not implement runtime behavior.

## 4. Current Decision

Decision:

- plan selected target state implementation first
- keep selected target state non-hardware-facing
- keep the plan test-first
- keep selected target state unimplemented in this slice
- keep anchor state unimplemented
- keep selected isolated pad runtime state unimplemented
- keep runtime state unimplemented
- keep `PZ` parked

This document does not authorize implementation by itself.

Implementation would require a separate approved slice.

## 5. Future Ownership

Future implementation, if approved later, should be isolated in a new module.

Possible future files:

- `rytm_randomizer/selected_target_state.py`
- `tests/test_selected_target_state.py`

Existing read-only behavior files should remain intent/reporting surfaces:

- `rytm_randomizer/behavior_selected_isolated_pad.py`
- `tests/test_behavior_selected_isolated_pad.py`

Future closeout script changes should be limited to adding a test label if a
new test file is created.

No closeout script changes are made by this document.

## 6. Future Module Responsibility

The future selected target state module should answer one question only:

- what selected isolated pad is active?

It should not answer:

- what anchor belongs to that target
- whether target and anchor match
- whether `PZ` can execute
- whether hardware is connected
- what MIDI should be sent

The module should remain a small, deterministic, in-memory state helper for
tests and future runtime planning.

## 7. Future Selected Target State Values

Accepted selected target state values remain:

- unset:
  - no selected target is known
- defaulted:
  - target comes from accepted passive default behavior such as Pad 3
- explicit:
  - target was explicitly selected by a future approved runtime path
- unsupported:
  - target is outside the supported selected isolated pad scope
- stale:
  - target may no longer reflect current session assumptions
- invalid:
  - target is malformed or impossible

These are future implementation values only.

No enum, dataclass, runtime object, storage, or behavior is added by this
document.

## 8. Proposed Future Object Shape

A future selected target state object may be dataclass-like and immutable-ish.

Conceptual fields may include:

- target pad
- target state
- target source
- command key
- source scope
- default status
- explicit status
- supported status
- stale status
- valid status
- explanatory reason
- safe failure code

The object should contain no MIDI object, port object, hardware handle,
dispatch callback, execution callback, anchor state, or `PZ` executor.

## 9. Smallest Future Behavior Surface

The first implementation, if approved later, should stay smaller than anchor
state and selected isolated pad runtime state.

It may include:

- construct an unset selected target state
- construct a defaulted selected target state from accepted `L` / Pad 3
  passive planning context
- represent an explicit target only if separately approved
- classify unsupported targets deterministically
- classify stale/invalid target contexts deterministically
- return deterministic safe failure results
- expose data for tests only

It must not:

- execute `L`
- execute `PZ`
- switch selected pad
- create anchor state
- create selected isolated pad runtime state
- return any pad to anchor
- mutate runtime or hardware state
- dispatch commands
- open ports
- send MIDI
- wire into active CLI behavior

## 10. Supported Scope For The First Implementation Plan

The first implementation should be conservative.

Required future support:

- unset target state
- defaulted Pad 3 selected isolated pad target state
- unsupported target safe failures
- stale target safe failures
- invalid target safe failures

Explicit target support may be planned but should remain separately reviewed
if there is any uncertainty.

Pads 5-12 must remain unsupported.

Analog Four must remain out of scope.

## 11. Safe Failure Requirements

Any future implementation must fail safely for:

- unset target
- unsupported target
- target outside selected isolated pad scope
- target outside currently supported pad scope
- Pads 5-12
- Analog Four target scope
- stale target
- invalid target
- attempt to use selected target state as anchor state
- attempt to use selected target state as selected isolated pad runtime state
- attempt to use selected target state for `PZ` before anchor/runtime state is
  approved
- accidental active path
- accidental hardware-facing path

Safe failure must mean:

- no dispatch
- no command execution
- no scene execution
- no selected pad switch
- no anchor return
- no runtime mutation unless explicitly allowed by a later implementation
- no MIDI
- no ports
- no hardware mutation
- deterministic explanatory result

## 12. Future Test-First Plan

Before any implementation, tests should be planned and then written first.

Future tests should verify:

- importing the module prints nothing
- unset selected target state is deterministic and safe
- defaulted Pad 3 selected target state is deterministic
- defaulted state records its source as passive/default planning context
- unsupported targets fail safely
- Pads 5-12 fail safely
- stale target state fails safely
- invalid target state fails safely
- selected target state exposes no anchor state
- selected target state exposes no selected isolated pad runtime state
- selected target state exposes no `PZ` execution
- selected target state objects are copied/immutable-ish
- repeated evaluations are deterministic
- `L` behavior remains read-only
- `PZ` remains parked
- passive CLI behavior remains unchanged
- no active command names are exposed
- no real MIDI libraries are imported
- no ports are opened
- no MIDI is sent
- V1.34 reference remains untouched
- package metadata remains untouched

These tests are not added by this document.

## 13. Relationship To Current Passive L Behavior

`L` currently means:

- select isolated single-pad mutation target, default Pad 3

Current behavior remains read-only.

`L` does not create selected target state today.

`L` does not execute selected pad switching today.

`L` does not mutate runtime state today.

Future selected target state implementation may use the accepted default Pad 3
planning context, but it must not turn `L` into execution without a separate
approved implementation slice.

## 14. Relationship To Anchor State

Selected target state is not anchor state.

Selected target state answers:

- what selected isolated pad is active?

Anchor state answers:

- what known anchor belongs to that selected target?

This plan does not implement anchor state.

Anchor state remains the next planned prerequisite after selected target state.

## 15. Relationship To Selected Isolated Pad Runtime State

Selected isolated pad runtime state is not selected target state.

Selected isolated pad runtime state should eventually compose:

- selected target state
- anchor state
- selected isolated pad workflow context
- validation state

This plan does not implement selected isolated pad runtime state.

Selected isolated pad runtime state remains later.

## 16. Relationship To PZ

`PZ` remains parked.

This plan does not make `PZ` ready for implementation.

The future selected target state implementation would only be one prerequisite
toward eventually reconsidering `PZ`.

Before `PZ` can be reconsidered, the project still needs:

- accepted selected target state implementation plan
- accepted selected target state implementation
- accepted anchor state implementation plan
- accepted anchor state implementation
- accepted selected isolated pad runtime-state implementation plan
- selected isolated pad runtime-state implementation
- safe failure coverage for `PZ` prerequisites
- another readiness review

## 17. Confirmed Absent Behavior

This document adds no:

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

## 18. Preconditions Before Implementation

Before any future selected target state implementation:

- clean Git status
- full closeout passing
- V1.34 reference diff empty
- package metadata diff empty
- this implementation plan reviewed and accepted
- future tests specified in test-first form
- passive CLI behavior remains read-only
- no active CLI behavior is added
- no MIDI libraries are imported
- no ports are opened
- no MIDI is sent
- no hardware is required

## 19. Safe Next Options

Safe next options:

- docs-only review/acceptance gate for this implementation plan
- docs-only selected target state implementation planning gate
- docs-only progress/timeline update
- pause at this clean planning checkpoint

## 20. Recommendation

Proceed with a docs-only review/acceptance gate for this selected target state
implementation plan.

Do not implement selected target state yet.

Do not implement anchor state yet.

Do not implement selected isolated pad runtime state yet.

Do not implement `PZ`.

Do not add MIDI, ports, active behavior, runtime execution, package metadata
changes, or hardware behavior.

## 21. Decision Summary

Selected target state implementation planning is documented.

Selected target state remains unimplemented.

Anchor state remains unimplemented.

Selected isolated pad runtime state remains unimplemented.

`PZ` remains parked.

Hardware remains off.

No implementation in this slice.
