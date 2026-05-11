# V1.34 Behavior Parity Anchor State Implementation Plan After Selected Target Implementation Review

## 1. Purpose

Define the future anchor state implementation plan after the accepted selected
target state implementation plan review.

This is a documentation-only implementation plan.

It describes the smallest safe future implementation surface for selected
isolated pad anchor state.

It adds no implementation, tests, CLI commands, runtime state, dispatch, MIDI,
ports, package metadata changes, active behavior, or hardware behavior.

## 2. Current Clean Baseline

Current branch:

- `modularize-v1.34`

Current HEAD before this planning slice:

- `ad5980e Add selected target state implementation plan review`

Current phase:

- passive/mock foundation
- V1.34 behavior-parity implementation packets
- passive behavior reports and CLI visibility
- runtime-state vocabulary accepted for planning
- `PZ` behavior plan accepted for planning
- selected target state implementation plan accepted
- runtime-state implementation sequencing accepted
- anchor state implementation now being planned at documentation level

Hardware status:

- Analog Rytm MKII off
- Analog Four MKII off
- hardware not required

## 3. Accepted Upstream Context

Accepted upstream context:

- anchor state plan review:
  - `Docs/V134_BEHAVIOR_PARITY_ANCHOR_STATE_PLAN_AFTER_SELECTED_TARGET_REVIEW_REVIEW.md`
- selected isolated pad runtime-state plan review:
  - `Docs/V134_BEHAVIOR_PARITY_SELECTED_ISOLATED_PAD_RUNTIME_STATE_PLAN_AFTER_ANCHOR_STATE_REVIEW_REVIEW.md`
- runtime-state implementation sequencing review:
  - `Docs/V134_BEHAVIOR_PARITY_RUNTIME_STATE_IMPLEMENTATION_SEQUENCING_NOTE_AFTER_SELECTED_ISOLATED_PAD_RUNTIME_STATE_REVIEW_REVIEW.md`
- selected target state implementation plan review:
  - `Docs/V134_BEHAVIOR_PARITY_SELECTED_TARGET_STATE_IMPLEMENTATION_PLAN_AFTER_RUNTIME_STATE_SEQUENCING_REVIEW_REVIEW.md`

These documents establish planning vocabulary, implementation order, and
safety boundaries only.

They do not implement runtime behavior.

## 4. Current Decision

Decision:

- plan anchor state implementation after selected target state implementation
  planning
- keep anchor state non-hardware-facing
- keep the plan test-first
- keep anchor state unimplemented in this slice
- keep selected target state unimplemented
- keep selected isolated pad runtime state unimplemented
- keep runtime state unimplemented
- keep `PZ` parked

This document does not authorize implementation by itself.

Implementation would require a separate approved slice.

## 5. Future Ownership

Future implementation, if approved later, should be isolated in a new module.

Possible future files:

- `rytm_randomizer/anchor_state.py`
- `tests/test_anchor_state.py`

Existing read-only behavior files should remain intent/reporting surfaces:

- `rytm_randomizer/behavior_anchor_profile.py`
- `tests/test_behavior_anchor_profile.py`
- `rytm_randomizer/behavior_selected_isolated_pad.py`
- `tests/test_behavior_selected_isolated_pad.py`

Future closeout script changes should be limited to adding a test label if a
new test file is created.

No closeout script changes are made by this document.

## 6. Future Module Responsibility

The future anchor state module should answer one question only:

- what known anchor belongs to the selected target?

It should not answer:

- what target is selected
- whether the selected target and anchor match
- whether selected isolated pad runtime context is valid
- whether `PZ` can execute
- whether hardware is connected
- what MIDI should be sent

The module should remain a small, deterministic, in-memory state helper for
tests and future runtime planning.

## 7. Future Anchor State Values

Accepted anchor state values remain:

- unknown:
  - no anchor is known
- static:
  - anchor comes from accepted static/passive planning context
- software-known:
  - anchor comes from a future approved software-known state
- soft-captured:
  - anchor comes from a future approved non-hardware capture-like source
- unsupported:
  - anchor is outside the supported selected isolated pad scope
- stale:
  - anchor may no longer reflect current session assumptions
- invalid:
  - anchor is malformed or impossible

These are future implementation values only.

No enum, dataclass, runtime object, storage, capture behavior, or anchor return
behavior is added by this document.

## 8. Proposed Future Object Shape

A future anchor state object may be dataclass-like and immutable-ish.

Conceptual fields may include:

- anchor pad
- anchor state
- anchor source
- anchor identity
- command key
- source scope
- source profile key
- source profile name
- source machine value
- static status
- software-known status
- soft-captured status
- supported status
- stale status
- valid status
- explanatory reason
- safe failure code

The object should contain no MIDI object, port object, hardware handle,
dispatch callback, execution callback, selected target state object, selected
isolated pad runtime state object, or `PZ` executor.

## 9. Smallest Future Behavior Surface

The first implementation, if approved later, should stay smaller than selected
isolated pad runtime state.

It may include:

- construct an unknown anchor state
- construct a static anchor state from accepted passive planning context, if
  separately approved
- represent software-known anchors only if separately approved
- keep soft-captured anchors planned but unimplemented
- classify unsupported anchors deterministically
- classify stale/invalid anchor contexts deterministically
- return deterministic safe failure results
- expose data for tests only

It must not:

- execute `PZ`
- execute anchor return
- switch selected pad
- create selected target state
- create selected isolated pad runtime state
- capture real hardware
- mutate runtime or hardware state
- dispatch commands
- open ports
- send MIDI
- wire into active CLI behavior

## 10. Supported Scope For The First Implementation Plan

The first implementation should be conservative.

Required future support:

- unknown anchor state
- unsupported anchor safe failures
- stale anchor safe failures
- invalid anchor safe failures

Optional future support, only if separately reviewed:

- static anchor from accepted passive planning context
- software-known anchor from future approved in-memory state

Soft-capture and true hardware capture remain later.

Pads 5-12 must remain unsupported.

Analog Four must remain out of scope.

## 11. Safe Failure Requirements

Any future implementation must fail safely for:

- unknown anchor
- unsupported anchor
- anchor outside selected isolated pad scope
- anchor outside currently supported pad scope
- Pads 5-12
- Analog Four anchor scope
- stale anchor
- invalid anchor
- attempt to use anchor state as selected target state
- attempt to use anchor state as selected isolated pad runtime state
- attempt to use anchor state for `PZ` before selected target/runtime state is
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
- unknown anchor state is deterministic and safe
- static anchor state is deterministic, if approved
- software-known anchor state is deterministic, if approved
- unsupported anchors fail safely
- Pads 5-12 fail safely
- stale anchor state fails safely
- invalid anchor state fails safely
- anchor state exposes no selected target state
- anchor state exposes no selected isolated pad runtime state
- anchor state exposes no `PZ` execution
- anchor state objects are copied/immutable-ish
- repeated evaluations are deterministic
- `PZ` remains parked
- passive CLI behavior remains unchanged
- no active command names are exposed
- no real MIDI libraries are imported
- no ports are opened
- no MIDI is sent
- V1.34 reference remains untouched
- package metadata remains untouched

These tests are not added by this document.

## 13. Relationship To Selected Target State

Anchor state is not selected target state.

Selected target state answers:

- what selected isolated pad is active?

Anchor state answers:

- what known anchor belongs to that selected target?

This plan does not implement selected target state.

Selected target state remains separately planned and unimplemented.

## 14. Relationship To Selected Isolated Pad Runtime State

Selected isolated pad runtime state is not anchor state.

Selected isolated pad runtime state should eventually compose:

- selected target state
- anchor state
- selected isolated pad workflow context
- validation state

This plan does not implement selected isolated pad runtime state.

Selected isolated pad runtime state remains later.

## 15. Relationship To PZ

`PZ` remains parked.

This plan does not make `PZ` ready for implementation.

The future anchor state implementation would only be one prerequisite toward
eventually reconsidering `PZ`.

Before `PZ` can be reconsidered, the project still needs:

- accepted selected target state implementation
- accepted anchor state implementation plan
- accepted anchor state implementation
- accepted selected isolated pad runtime-state implementation plan
- selected isolated pad runtime-state implementation
- safe failure coverage for `PZ` prerequisites
- another readiness review

## 16. Confirmed Absent Behavior

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

## 17. Preconditions Before Implementation

Before any future anchor state implementation:

- clean Git status
- full closeout passing
- V1.34 reference diff empty
- package metadata diff empty
- this implementation plan reviewed and accepted
- selected target state implementation plan reviewed and accepted
- future tests specified in test-first form
- passive CLI behavior remains read-only
- no active CLI behavior is added
- no MIDI libraries are imported
- no ports are opened
- no MIDI is sent
- no hardware is required

## 18. Safe Next Options

Safe next options:

- docs-only review/acceptance gate for this implementation plan
- docs-only anchor state implementation planning gate
- docs-only progress/timeline update
- pause at this clean planning checkpoint

## 19. Recommendation

Proceed with a docs-only review/acceptance gate for this anchor state
implementation plan.

Do not implement anchor state yet.

Do not implement selected target state yet.

Do not implement selected isolated pad runtime state yet.

Do not implement `PZ`.

Do not add MIDI, ports, active behavior, runtime execution, package metadata
changes, or hardware behavior.

## 20. Decision Summary

Anchor state implementation planning is documented.

Anchor state remains unimplemented.

Selected target state remains unimplemented.

Selected isolated pad runtime state remains unimplemented.

`PZ` remains parked.

Hardware remains off.

No implementation in this slice.
