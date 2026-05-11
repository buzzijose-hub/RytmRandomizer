# V1.34 Behavior Parity Selected Isolated Pad Runtime-State Implementation Plan After PZ Readiness Review Review

## 1. Purpose

Review and accept the selected isolated pad runtime-state implementation plan
after the accepted `PZ` implementation readiness review.

This is a documentation-only review gate.

It accepts the implementation plan as the current planning boundary only.

It adds no implementation, tests, CLI commands, runtime state, dispatch, MIDI,
ports, package metadata changes, active behavior, or hardware behavior.

## 2. Current Clean Baseline

Current branch:

- `modularize-v1.34`

Current HEAD before this review slice:

- `861b7d7 Add selected isolated pad runtime-state implementation plan`

Current phase:

- passive/mock foundation
- V1.34 behavior-parity implementation packets
- passive behavior reports and CLI visibility
- runtime-state vocabulary accepted for planning
- `PZ` behavior plan accepted for planning
- selected target state plan accepted for planning
- anchor state plan accepted for planning
- selected isolated pad runtime-state plan accepted for planning
- runtime-state planning progress report accepted
- `PZ` implementation readiness review accepted
- selected isolated pad runtime-state implementation plan created
- selected isolated pad runtime-state implementation plan now being reviewed

Hardware status:

- Analog Rytm MKII off
- Analog Four MKII off
- hardware not required

## 3. Review Decision

Accepted implementation plan:

- `Docs/V134_BEHAVIOR_PARITY_SELECTED_ISOLATED_PAD_RUNTIME_STATE_IMPLEMENTATION_PLAN_AFTER_PZ_READINESS_REVIEW.md`

Accepted implementation plan milestone:

- `861b7d7 Add selected isolated pad runtime-state implementation plan`

Decision:

- accept selected isolated pad runtime-state implementation planning
- keep the accepted plan non-hardware-facing
- keep the accepted plan test-first
- keep selected isolated pad runtime state unimplemented
- keep selected target state unimplemented
- keep anchor state unimplemented
- keep runtime state unimplemented
- keep `PZ` parked
- require a separate approved implementation slice before any code or tests

This review accepts planning only.

It does not authorize implementation.

## 4. Accepted Future Ownership

The review accepts the likely future implementation/test surface:

- `rytm_randomizer/selected_isolated_pad_runtime_state.py`
- `tests/test_selected_isolated_pad_runtime_state.py`

The review also accepts that existing read-only behavior intent should remain
separate:

- `rytm_randomizer/behavior_selected_isolated_pad.py`
- `tests/test_behavior_selected_isolated_pad.py`

Any future closeout script change should be limited to adding a test label if
a new test file is created.

No closeout script change is authorized by this review.

## 5. Accepted Runtime-State Planning Values

The review accepts these selected isolated pad runtime-state planning values
for future implementation design:

- uninitialized
- passive-default
- explicit-target
- target-anchor-matched
- target-anchor-mismatched
- unsupported
- stale
- invalid

These remain planning values only.

No enum, dataclass, runtime state object, storage, or behavior is added by
this review.

## 6. Accepted Smallest Future Behavior Surface

The review accepts that the first future implementation, if separately
approved, should stay smaller than `PZ`.

Accepted future scope may include:

- construct an uninitialized selected isolated pad runtime state
- construct a passive-default selected isolated pad runtime state from the
  accepted default Pad 3 planning context
- represent an explicit selected target only if separately approved
- attach a known static/software-known anchor only if separately approved
- validate target-anchor match or mismatch
- return deterministic safe failure results
- expose data for tests only

The accepted plan must not:

- execute `PZ`
- switch selected pad
- return any pad to anchor
- mutate hardware
- dispatch commands
- open ports
- send MIDI
- wire into active CLI behavior

## 7. Accepted Safe Failure Requirements

Any future implementation must fail safely for:

- uninitialized selected isolated pad runtime context
- unsupported selected target
- target outside selected isolated pad scope
- target outside currently supported pad scope
- missing anchor
- unknown anchor
- unsupported anchor
- target-anchor mismatch
- stale context
- invalid context
- attempt to use runtime state for `PZ` before `PZ` is approved
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

## 8. Accepted Test-First Requirements

Before any future implementation, tests should be planned and then written
first.

Accepted future test categories include:

- import side-effect safety
- uninitialized state safe behavior
- passive-default Pad 3 behavior
- unsupported target safe failures
- Pads 5-12 safe failures
- unknown anchor safe failures
- unsupported anchor safe failures
- target-anchor mismatch safe failures
- stale context safe failures
- invalid context safe failures
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

## 9. Relationship To PZ

`PZ` remains parked.

This review does not make `PZ` ready for implementation.

The accepted implementation plan is one prerequisite toward eventually
reconsidering `PZ`, not a direct `PZ` implementation plan.

Before `PZ` can be reconsidered, the project still needs:

- accepted selected target state implementation plan
- accepted anchor state implementation plan
- accepted selected isolated pad runtime-state implementation plan
- test-first implementation of the needed runtime-state foundation
- safe failure coverage for `PZ` prerequisites
- another readiness review

## 10. Confirmed Absent Behavior

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

## 11. Preconditions Before Any Implementation Slice

Before any future selected isolated pad runtime-state implementation slice:

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

## 12. Safe Next Options

Safe next options:

- docs-only selected target state implementation plan
- docs-only anchor state implementation plan
- docs-only runtime-state implementation sequencing note:
  - `Docs/V134_BEHAVIOR_PARITY_RUNTIME_STATE_IMPLEMENTATION_SEQUENCING_NOTE_AFTER_SELECTED_ISOLATED_PAD_RUNTIME_STATE_REVIEW.md`
- docs-only progress/timeline update
- pause at this clean accepted checkpoint

## 13. Follow-On Sequencing Note

The follow-on docs-only runtime-state implementation sequencing note is:

- `Docs/V134_BEHAVIOR_PARITY_RUNTIME_STATE_IMPLEMENTATION_SEQUENCING_NOTE_AFTER_SELECTED_ISOLATED_PAD_RUNTIME_STATE_REVIEW.md`

It documents this future order:

- selected target state should be planned first
- anchor state should be planned second
- selected isolated pad runtime state should be planned third
- `PZ` remains later and parked

The follow-on note adds no implementation, tests, CLI commands, runtime state,
dispatch, MIDI, ports, package metadata changes, active behavior, or hardware
behavior.

## 14. Recommendation

Proceed with a docs-only review/acceptance gate for the runtime-state
implementation sequencing note.

Reason:

- selected isolated pad runtime state depends on selected target and anchor
  state
- selected target and anchor state still have implementation plans pending
- sequencing the small runtime-state prerequisites first will keep the first
  implementation slice narrow

Do not implement selected isolated pad runtime state yet.

Do not implement selected target state yet.

Do not implement anchor state yet.

Do not implement `PZ`.

Do not add MIDI, ports, active behavior, runtime execution, package metadata
changes, or hardware behavior.

## 15. Decision Summary

`Docs/V134_BEHAVIOR_PARITY_SELECTED_ISOLATED_PAD_RUNTIME_STATE_IMPLEMENTATION_PLAN_AFTER_PZ_READINESS_REVIEW.md`
is accepted for planning.

Selected isolated pad runtime state remains unimplemented.

Selected target state remains unimplemented.

Anchor state remains unimplemented.

`PZ` remains parked.

Hardware remains off.

No implementation in this review slice.
