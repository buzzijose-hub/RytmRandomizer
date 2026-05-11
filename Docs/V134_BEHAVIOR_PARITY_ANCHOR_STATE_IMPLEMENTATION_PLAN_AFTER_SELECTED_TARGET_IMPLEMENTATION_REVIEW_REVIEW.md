# V1.34 Behavior Parity Anchor State Implementation Plan After Selected Target Implementation Review Review

## 1. Purpose

Review and accept the anchor state implementation plan after the accepted
selected target state implementation plan review.

This is a documentation-only review gate.

It accepts the anchor state implementation plan as the current planning
boundary only.

It adds no implementation, tests, CLI commands, runtime state, dispatch, MIDI,
ports, package metadata changes, active behavior, or hardware behavior.

## 2. Current Clean Baseline

Current branch:

- `modularize-v1.34`

Current HEAD before this review slice:

- `2f7f5f4 Add anchor state implementation plan`

Current phase:

- passive/mock foundation
- V1.34 behavior-parity implementation packets
- passive behavior reports and CLI visibility
- runtime-state vocabulary accepted for planning
- `PZ` behavior plan accepted for planning
- selected target state implementation plan accepted
- runtime-state implementation sequencing accepted
- anchor state implementation plan created
- anchor state implementation plan now being reviewed

Hardware status:

- Analog Rytm MKII off
- Analog Four MKII off
- hardware not required

## 3. Review Decision

Accepted implementation plan:

- `Docs/V134_BEHAVIOR_PARITY_ANCHOR_STATE_IMPLEMENTATION_PLAN_AFTER_SELECTED_TARGET_IMPLEMENTATION_REVIEW.md`

Accepted implementation plan milestone:

- `2f7f5f4 Add anchor state implementation plan`

Decision:

- accept anchor state implementation planning
- accept that anchor state answers only what known anchor belongs to the
  selected target
- keep anchor state non-hardware-facing
- keep anchor state unimplemented
- keep selected target state unimplemented
- keep selected isolated pad runtime state unimplemented
- keep runtime state unimplemented
- keep `PZ` parked
- require a separate approved implementation slice before any code or tests

This review accepts planning only.

It does not authorize implementation.

## 4. Accepted Future Ownership

The review accepts the likely future implementation/test surface:

- `rytm_randomizer/anchor_state.py`
- `tests/test_anchor_state.py`

The review also accepts that existing read-only behavior intent should remain
separate:

- `rytm_randomizer/behavior_anchor_profile.py`
- `tests/test_behavior_anchor_profile.py`
- `rytm_randomizer/behavior_selected_isolated_pad.py`
- `tests/test_behavior_selected_isolated_pad.py`

Any future closeout script change should be limited to adding a test label if
a new test file is created.

No closeout script change is authorized by this review.

## 5. Accepted Future Module Responsibility

The accepted anchor state module should answer one question only:

- what known anchor belongs to the selected target?

It should not answer:

- what target is selected
- whether selected target and anchor match
- whether selected isolated pad runtime context is valid
- whether `PZ` can execute
- whether hardware is connected
- what MIDI should be sent

This keeps anchor state smaller than selected isolated pad runtime state.

## 6. Accepted Anchor State Values

The review accepts these anchor state values for future implementation
planning:

- unknown
- static
- software-known
- soft-captured
- unsupported
- stale
- invalid

These remain planning values only.

No enum, dataclass, runtime object, storage, capture behavior, or anchor return
behavior is added by this review.

## 7. Accepted Future Object Shape

A future anchor state object may be dataclass-like and immutable-ish.

Accepted conceptual fields may include:

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

## 8. Accepted Smallest Future Behavior Surface

The review accepts that the first implementation, if separately approved,
should stay smaller than selected isolated pad runtime state.

Accepted future scope may include:

- construct an unknown anchor state
- construct a static anchor state from accepted passive planning context, if
  separately approved
- represent software-known anchors only if separately approved
- keep soft-captured anchors planned but unimplemented
- classify unsupported anchors deterministically
- classify stale/invalid anchor contexts deterministically
- return deterministic safe failure results
- expose data for tests only

The accepted plan must not:

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

## 9. Accepted First Scope Boundary

The review accepts the conservative first future scope:

- unknown anchor state
- unsupported anchor safe failures
- stale anchor safe failures
- invalid anchor safe failures

Optional future support remains separately reviewable:

- static anchor from accepted passive planning context
- software-known anchor from future approved in-memory state

Soft-capture and true hardware capture remain later.

Pads 5-12 remain unsupported.

Analog Four remains out of scope.

## 10. Accepted Safe Failure Requirements

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

Safe failure means:

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

## 11. Accepted Test-First Requirements

Before any future implementation, tests should be planned and then written
first.

Accepted future test categories include:

- import side-effect safety
- unknown anchor state safe behavior
- static anchor behavior, if approved
- software-known anchor behavior, if approved
- unsupported anchor safe failures
- Pads 5-12 safe failures
- stale anchor safe failures
- invalid anchor safe failures
- no selected target state exposure
- no selected isolated pad runtime state exposure
- no `PZ` execution exposure
- copied/immutable-ish result behavior
- deterministic repeated evaluations
- `PZ` remains parked
- passive CLI behavior remains unchanged
- no active command exposure
- no real MIDI library imports
- no port opening
- no MIDI sending
- V1.34 reference untouched
- package metadata untouched

No tests are added by this review.

## 12. Relationship To Later State Layers

Anchor state is not selected target state.

Anchor state is not selected isolated pad runtime state.

Anchor state does not make `PZ` ready.

Accepted relationship:

- selected target state answers what selected isolated pad is active
- anchor state answers what known anchor belongs to that selected target
- selected isolated pad runtime state composes target and anchor context later
- `PZ` depends on all of those and remains parked

## 13. Confirmed Absent Behavior

This review confirms no:

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

## 14. Preconditions Before Any Implementation

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

## 15. Safe Next Options

Safe next options:

- docs-only anchor state implementation planning gate
- docs-only selected isolated pad runtime-state implementation plan update
- docs-only progress/timeline update
- pause at this clean accepted checkpoint

## 16. Recommendation

Proceed with a docs-only selected isolated pad runtime-state implementation
plan update or planning gate.

Do not implement anchor state yet.

Do not implement selected target state yet.

Do not implement selected isolated pad runtime state yet.

Do not implement `PZ`.

Do not add MIDI, ports, active behavior, runtime execution, package metadata
changes, or hardware behavior.

## 17. Decision Summary

`Docs/V134_BEHAVIOR_PARITY_ANCHOR_STATE_IMPLEMENTATION_PLAN_AFTER_SELECTED_TARGET_IMPLEMENTATION_REVIEW.md`
is accepted for planning.

Anchor state remains unimplemented.

Selected target state remains unimplemented.

Selected isolated pad runtime state remains unimplemented.

`PZ` remains parked.

Hardware remains off.

No implementation in this review slice.
