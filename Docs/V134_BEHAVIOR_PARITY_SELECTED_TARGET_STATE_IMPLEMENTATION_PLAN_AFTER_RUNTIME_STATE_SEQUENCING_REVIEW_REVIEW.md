# V1.34 Behavior Parity Selected Target State Implementation Plan After Runtime-State Sequencing Review Review

## 1. Purpose

Review and accept the selected target state implementation plan after the
accepted runtime-state implementation sequencing review.

This is a documentation-only review gate.

It accepts the selected target state implementation plan as the current
planning boundary only.

It adds no implementation, tests, CLI commands, runtime state, dispatch, MIDI,
ports, package metadata changes, active behavior, or hardware behavior.

## 2. Current Clean Baseline

Current branch:

- `modularize-v1.34`

Current HEAD before this review slice:

- `e7bc6ab Add selected target state implementation plan`

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
- selected target state implementation plan created
- selected target state implementation plan now being reviewed

Hardware status:

- Analog Rytm MKII off
- Analog Four MKII off
- hardware not required

## 3. Review Decision

Accepted implementation plan:

- `Docs/V134_BEHAVIOR_PARITY_SELECTED_TARGET_STATE_IMPLEMENTATION_PLAN_AFTER_RUNTIME_STATE_SEQUENCING_REVIEW.md`

Accepted implementation plan milestone:

- `e7bc6ab Add selected target state implementation plan`

Decision:

- accept selected target state implementation planning
- accept that selected target state answers only what selected isolated pad is
  active
- keep selected target state non-hardware-facing
- keep selected target state unimplemented
- keep anchor state unimplemented
- keep selected isolated pad runtime state unimplemented
- keep runtime state unimplemented
- keep `PZ` parked
- require a separate approved implementation slice before any code or tests

This review accepts planning only.

It does not authorize implementation.

## 4. Accepted Future Ownership

The review accepts the likely future implementation/test surface:

- `rytm_randomizer/selected_target_state.py`
- `tests/test_selected_target_state.py`

The review also accepts that existing read-only behavior intent should remain
separate:

- `rytm_randomizer/behavior_selected_isolated_pad.py`
- `tests/test_behavior_selected_isolated_pad.py`

Any future closeout script change should be limited to adding a test label if
a new test file is created.

No closeout script change is authorized by this review.

## 5. Accepted Future Module Responsibility

The accepted selected target state module should answer one question only:

- what selected isolated pad is active?

It should not answer:

- what anchor belongs to that target
- whether target and anchor match
- whether `PZ` can execute
- whether hardware is connected
- what MIDI should be sent

This keeps selected target state smaller than anchor state and selected
isolated pad runtime state.

## 6. Accepted Selected Target State Values

The review accepts these selected target state values for future
implementation planning:

- unset
- defaulted
- explicit
- unsupported
- stale
- invalid

These remain planning values only.

No enum, dataclass, runtime object, storage, or behavior is added by this
review.

## 7. Accepted Future Object Shape

A future selected target state object may be dataclass-like and immutable-ish.

Accepted conceptual fields may include:

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

## 8. Accepted Smallest Future Behavior Surface

The review accepts that the first implementation, if separately approved,
should stay smaller than anchor state and selected isolated pad runtime state.

Accepted future scope may include:

- construct an unset selected target state
- construct a defaulted selected target state from accepted `L` / Pad 3
  passive planning context
- represent an explicit target only if separately approved
- classify unsupported targets deterministically
- classify stale/invalid target contexts deterministically
- return deterministic safe failure results
- expose data for tests only

The accepted plan must not:

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

## 9. Accepted First Scope Boundary

The review accepts the conservative first future scope:

- unset target state
- defaulted Pad 3 selected isolated pad target state
- unsupported target safe failures
- stale target safe failures
- invalid target safe failures

Explicit target support remains separately reviewable if there is uncertainty.

Pads 5-12 remain unsupported.

Analog Four remains out of scope.

## 10. Accepted Safe Failure Requirements

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
- unset selected target state safe behavior
- defaulted Pad 3 selected target behavior
- passive/default source metadata
- unsupported target safe failures
- Pads 5-12 safe failures
- stale target safe failures
- invalid target safe failures
- no anchor state exposure
- no selected isolated pad runtime state exposure
- no `PZ` execution exposure
- copied/immutable-ish result behavior
- deterministic repeated evaluations
- `L` remains read-only
- `PZ` remains parked
- passive CLI behavior remains unchanged
- no active command exposure
- no real MIDI library imports
- no port opening
- no MIDI sending
- V1.34 reference untouched
- package metadata untouched

No tests are added by this review.

## 12. Relationship To Current Passive L Behavior

`L` remains read-only selected isolated pad target intent.

The review accepts that current `L` behavior:

- describes default Pad 3 intent
- does not create selected target state today
- does not execute selected pad switching today
- does not mutate runtime state today

Future selected target state may use the accepted default Pad 3 planning
context, but this review does not turn `L` into execution.

## 13. Relationship To Later State Layers

Selected target state is not anchor state.

Selected target state is not selected isolated pad runtime state.

Selected target state does not make `PZ` ready.

Accepted relationship:

- selected target state answers what selected isolated pad is active
- anchor state answers what known anchor belongs to that selected target
- selected isolated pad runtime state composes target and anchor context later
- `PZ` depends on all of those and remains parked

## 14. Confirmed Absent Behavior

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

## 15. Preconditions Before Any Implementation

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

## 16. Safe Next Options

Safe next options:

- docs-only selected target state implementation planning gate
- docs-only anchor state implementation plan
- docs-only progress/timeline update
- pause at this clean accepted checkpoint

## 17. Recommendation

Proceed with a docs-only selected target state implementation planning gate or
docs-only anchor state implementation plan.

Prefer a planning gate if one more safety checkpoint is desired before code.

Do not implement selected target state yet.

Do not implement anchor state yet.

Do not implement selected isolated pad runtime state yet.

Do not implement `PZ`.

Do not add MIDI, ports, active behavior, runtime execution, package metadata
changes, or hardware behavior.

## 18. Decision Summary

`Docs/V134_BEHAVIOR_PARITY_SELECTED_TARGET_STATE_IMPLEMENTATION_PLAN_AFTER_RUNTIME_STATE_SEQUENCING_REVIEW.md`
is accepted for planning.

Selected target state remains unimplemented.

Anchor state remains unimplemented.

Selected isolated pad runtime state remains unimplemented.

`PZ` remains parked.

Hardware remains off.

No implementation in this review slice.
