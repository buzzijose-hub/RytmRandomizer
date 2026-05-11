# V1.34 Behavior Parity Selected Isolated Pad Runtime-State Implementation Plan After PZ Readiness Review

## 1. Purpose

Define a future implementation plan for selected isolated pad runtime state
after the accepted `PZ` implementation readiness review.

This is a documentation-only implementation plan.

It describes the smallest safe future implementation surface needed before
`PZ` can be reconsidered.

It adds no implementation, tests, CLI commands, runtime state, dispatch, MIDI,
ports, package metadata changes, active behavior, or hardware behavior.

## 2. Current Clean Baseline

Current branch:

- `modularize-v1.34`

Current HEAD before this planning slice:

- `570513d Add PZ implementation readiness review`

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
- selected isolated pad runtime-state implementation now being planned at
  documentation level

Hardware status:

- Analog Rytm MKII off
- Analog Four MKII off
- hardware not required

## 3. Accepted Upstream Context

Accepted upstream planning and review context:

- runtime-state vocabulary:
  - `Docs/V134_BEHAVIOR_PARITY_RUNTIME_STATE_VOCABULARY_DECISION_NOTE_REVIEW.md`
- `PZ` behavior boundary:
  - `Docs/V134_BEHAVIOR_PARITY_PZ_BEHAVIOR_PLAN_AFTER_RUNTIME_STATE_VOCABULARY_REVIEW.md`
- selected target state boundary:
  - `Docs/V134_BEHAVIOR_PARITY_SELECTED_TARGET_STATE_PLAN_AFTER_PZ_REVIEW_REVIEW.md`
- anchor state boundary:
  - `Docs/V134_BEHAVIOR_PARITY_ANCHOR_STATE_PLAN_AFTER_SELECTED_TARGET_REVIEW_REVIEW.md`
- selected isolated pad runtime-state boundary:
  - `Docs/V134_BEHAVIOR_PARITY_SELECTED_ISOLATED_PAD_RUNTIME_STATE_PLAN_AFTER_ANCHOR_STATE_REVIEW_REVIEW.md`
- runtime-state planning progress report:
  - `Docs/V134_BEHAVIOR_PARITY_RUNTIME_STATE_PLANNING_PROGRESS_REPORT_AFTER_SELECTED_ISOLATED_PAD_REVIEW_REVIEW.md`
- `PZ` implementation readiness review:
  - `Docs/V134_BEHAVIOR_PARITY_PZ_IMPLEMENTATION_READINESS_DECISION_NOTE_AFTER_RUNTIME_STATE_PLANNING_REVIEW_REVIEW.md`

These documents establish planning vocabulary and safety guardrails only.

They do not implement runtime behavior.

## 4. Current Decision

Decision:

- plan a tiny future selected isolated pad runtime-state implementation surface
- keep the plan non-hardware-facing
- keep the plan test-first
- keep `PZ` parked
- keep selected target state implementation unstarted
- keep anchor state implementation unstarted
- keep selected isolated pad runtime state unimplemented in this slice

This document does not authorize implementation by itself.

Implementation would require a separate approved slice.

## 5. Proposed Future Ownership

Future implementation, if approved later, should likely be isolated in a new
module rather than expanding the existing read-only behavior helper.

Possible future files:

- `rytm_randomizer/selected_isolated_pad_runtime_state.py`
- `tests/test_selected_isolated_pad_runtime_state.py`

Existing read-only files should remain behavior-intent surfaces:

- `rytm_randomizer/behavior_selected_isolated_pad.py`
- `tests/test_behavior_selected_isolated_pad.py`

Future closeout script changes should be limited to adding the new test label
if a new test file is created.

No closeout script changes are made by this document.

## 6. Proposed Future Runtime-State Object

A future selected isolated pad runtime-state object may be dataclass-like and
immutable-ish.

Conceptual fields may include:

- target pad
- target source
- target state
- anchor source
- anchor state
- anchor identity
- operation kind
- selected isolated pad command key
- validation status
- stale status
- explanatory reason
- safe failure code

These are planning fields only.

No enum, dataclass, runtime state object, storage, or behavior is added by
this document.

## 7. Accepted Planning Values

The implementation plan should preserve the accepted selected isolated pad
runtime-state values:

- uninitialized:
  - no selected isolated pad runtime context exists
- passive-default:
  - context is inferred from read-only behavior intent such as default Pad 3
- explicit-target:
  - context was explicitly selected by a future approved runtime path
- target-anchor-matched:
  - selected target and known anchor agree
- target-anchor-mismatched:
  - selected target and known anchor do not agree
- unsupported:
  - selected isolated pad context is outside current supported scope
- stale:
  - runtime context may no longer reflect current session assumptions
- invalid:
  - runtime context is malformed or impossible

Future implementation should return deterministic state/result objects that
make these values inspectable in tests.

## 8. Smallest Future Behavior Surface

The first implementation, if approved later, should stay smaller than `PZ`.

It may include:

- construct an uninitialized selected isolated pad runtime state
- construct a passive-default selected isolated pad runtime state from the
  accepted default Pad 3 planning context
- represent an explicit selected target only if separately approved
- attach a known static/software-known anchor only if separately approved
- validate target-anchor match or mismatch
- return deterministic safe failure results
- expose data for tests only

It must not:

- execute `PZ`
- switch selected pad
- return any pad to anchor
- mutate hardware
- dispatch commands
- open ports
- send MIDI
- wire into active CLI behavior

## 9. Safe Failure Requirements

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

## 10. Future Test-First Plan

Before any implementation, tests should be planned and then written first.

Future tests should verify:

- importing the module prints nothing
- uninitialized state is deterministic and safe
- passive-default Pad 3 context is deterministic
- explicit target behavior is absent unless separately approved
- unsupported targets fail safely
- Pads 5-12 fail safely
- unknown anchors fail safely
- unsupported anchors fail safely
- target-anchor mismatches fail safely
- stale context fails safely
- invalid context fails safely
- runtime-state objects are copied/immutable-ish
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

## 11. Relationship To Current Behavior Helpers

`rytm_randomizer/behavior_selected_isolated_pad.py` currently models passive
intent for:

- `L`:
  - read-only selected isolated pad target intent
- `PZ`:
  - deferred selected isolated pad anchor return intent

The future runtime-state module should not turn this helper into execution.

The helper should continue to report intent and safe deferral.

The future runtime-state module, if approved, should provide inspectable state
objects for tests and later planning.

## 12. Relationship To PZ

`PZ` remains parked.

This plan does not make `PZ` ready for implementation.

The future runtime-state implementation would only be one prerequisite toward
eventually reconsidering `PZ`.

Before `PZ` can be reconsidered, the project still needs:

- accepted selected target state implementation plan
- accepted anchor state implementation plan
- accepted selected isolated pad runtime-state implementation plan
- test-first implementation of the needed runtime-state foundation
- safe failure coverage for `PZ` prerequisites
- another readiness review

## 13. Confirmed Absent Behavior

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

## 14. Preconditions Before Implementation

Before any future selected isolated pad runtime-state implementation:

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

## 15. Safe Next Options

Safe next options:

- docs-only review/acceptance gate for this implementation plan
- docs-only selected target state implementation plan
- docs-only anchor state implementation plan
- user-facing progress/timeline update
- pause at this clean planning checkpoint

## 16. Recommendation

Proceed with a docs-only review/acceptance gate for this selected isolated pad
runtime-state implementation plan.

Do not implement selected isolated pad runtime state yet.

Do not implement selected target state yet.

Do not implement anchor state yet.

Do not implement `PZ`.

Do not add MIDI, ports, active behavior, runtime execution, package metadata
changes, or hardware behavior.

## 17. Decision Summary

Selected isolated pad runtime-state implementation planning is documented.

Selected isolated pad runtime state remains unimplemented.

Selected target state remains unimplemented.

Anchor state remains unimplemented.

`PZ` remains parked.

Hardware remains off.

No implementation in this slice.
