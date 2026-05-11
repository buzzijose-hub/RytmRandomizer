# V1.34 Behavior Parity Runtime-State Implementation Sequencing Note After Selected Isolated Pad Runtime-State Review

## 1. Purpose

Define the safe order for future runtime-state implementation planning after
the accepted selected isolated pad runtime-state implementation plan review.

This is a documentation-only sequencing note.

It decides what should be planned first, second, and later before any runtime
state code or tests are added.

It adds no implementation, tests, CLI commands, runtime state, dispatch, MIDI,
ports, package metadata changes, active behavior, or hardware behavior.

## 2. Current Clean Baseline

Current branch:

- `modularize-v1.34`

Current HEAD before this sequencing slice:

- `eb76007 Add selected isolated pad runtime-state implementation plan review`

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
- selected isolated pad runtime-state implementation plan accepted
- runtime-state implementation order now being sequenced at documentation
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
- runtime-state planning progress report review:
  - `Docs/V134_BEHAVIOR_PARITY_RUNTIME_STATE_PLANNING_PROGRESS_REPORT_AFTER_SELECTED_ISOLATED_PAD_REVIEW_REVIEW.md`
- `PZ` implementation readiness review:
  - `Docs/V134_BEHAVIOR_PARITY_PZ_IMPLEMENTATION_READINESS_DECISION_NOTE_AFTER_RUNTIME_STATE_PLANNING_REVIEW_REVIEW.md`
- selected isolated pad runtime-state implementation plan review:
  - `Docs/V134_BEHAVIOR_PARITY_SELECTED_ISOLATED_PAD_RUNTIME_STATE_IMPLEMENTATION_PLAN_AFTER_PZ_READINESS_REVIEW_REVIEW.md`

These documents establish planning vocabulary and readiness only.

They do not implement runtime behavior.

## 4. Sequencing Decision

Decision:

- do not implement selected isolated pad runtime state first
- do not implement `PZ` first
- plan and review smaller prerequisites before implementation
- keep all sequencing work documentation-only

Recommended order:

1. selected target state implementation plan
2. selected target state implementation plan review
3. anchor state implementation plan
4. anchor state implementation plan review
5. selected isolated pad runtime-state implementation plan update, if needed
6. selected isolated pad runtime-state test-only implementation slice, only
   after separate approval
7. `PZ` readiness review after runtime-state implementation
8. `PZ` implementation plan, only if readiness is accepted later

This document does not authorize any implementation step.

## 5. Why Selected Target Comes First

Selected target state should be planned first because it answers the smallest
required question:

- what selected isolated pad is active?

Future selected target state should be able to represent:

- unset
- defaulted
- explicit
- unsupported
- stale
- invalid

Without this layer, selected isolated pad runtime state cannot safely know
which pad it is describing.

Without this layer, `PZ` cannot safely know what pad would be returned to an
anchor.

## 6. Why Anchor State Comes Second

Anchor state should be planned after selected target state because it answers
the second required question:

- what known anchor belongs to the selected target?

Future anchor state should be able to represent:

- unknown
- static
- software-known
- soft-captured
- unsupported
- stale
- invalid

Without this layer, selected isolated pad runtime state cannot safely pair a
target with an anchor.

Without this layer, `PZ` cannot safely know what anchor would be used.

## 7. Why Selected Isolated Pad Runtime State Comes Third

Selected isolated pad runtime state should come after target and anchor
planning because it composes both concepts.

It should eventually answer:

- what selected isolated pad workflow context exists?
- what target is selected?
- what anchor belongs to that target?
- do target and anchor match?
- is the context stale, invalid, unsupported, or safe?

Future selected isolated pad runtime-state values remain:

- uninitialized
- passive-default
- explicit-target
- target-anchor-matched
- target-anchor-mismatched
- unsupported
- stale
- invalid

Planning this third keeps the state object from quietly inventing target or
anchor rules before those rules are separately accepted.

## 8. Why PZ Remains Later

`PZ` means:

- return selected isolated pad to anchor only

`PZ` depends on:

- selected target state
- anchor state
- selected isolated pad runtime state
- safe failure behavior
- another readiness review

`PZ` remains parked until those prerequisites exist and are accepted.

This sequencing note does not make `PZ` ready.

## 9. Future Implementation Packet Boundaries

If implementation is approved later, packet boundaries should stay small:

- Packet A:
  - selected target state tests and minimal non-hardware implementation
- Packet B:
  - anchor state tests and minimal non-hardware implementation
- Packet C:
  - selected isolated pad runtime-state tests and minimal non-hardware
    implementation
- Packet D:
  - readiness review after runtime-state implementation
- Packet E:
  - `PZ` implementation plan only if readiness is accepted

Each packet should:

- have one commit
- run full closeout
- leave V1.34 reference diff empty
- leave package metadata diff empty
- avoid MIDI, ports, active behavior, and hardware behavior

No packet is implemented by this document.

## 10. Future File Responsibility Map

Possible future files, subject to separate approval:

- `rytm_randomizer/selected_target_state.py`
  - represents selected isolated pad target state only
- `tests/test_selected_target_state.py`
  - tests selected target state safe defaults and safe failures
- `rytm_randomizer/anchor_state.py`
  - represents selected isolated pad anchor knowledge only
- `tests/test_anchor_state.py`
  - tests anchor state safe defaults and safe failures
- `rytm_randomizer/selected_isolated_pad_runtime_state.py`
  - composes selected target and anchor state for selected isolated pad context
- `tests/test_selected_isolated_pad_runtime_state.py`
  - tests composition and safe failure behavior

Existing read-only behavior helpers should remain separate:

- `rytm_randomizer/behavior_selected_isolated_pad.py`
- `rytm_randomizer/behavior_selected_profile.py`
- `rytm_randomizer/behavior_anchor_profile.py`

The CLI should remain passive/read-only.

## 11. Future Test-First Sequence

Before any implementation packet, write tests first.

Selected target state test plan should come first:

- import prints nothing
- unset target fails safely
- default Pad 3 target is deterministic
- explicit supported target behavior is deterministic, if approved
- unsupported targets fail safely
- Pads 5-12 fail safely
- no MIDI libraries are imported
- no ports are opened
- passive CLI remains unchanged

Anchor state test plan should come second:

- import prints nothing
- unknown anchor fails safely
- static/software-known anchor behavior is deterministic, if approved
- unsupported anchors fail safely
- stale anchors fail safely
- invalid anchors fail safely
- no MIDI libraries are imported
- no ports are opened
- passive CLI remains unchanged

Selected isolated pad runtime-state test plan should come third:

- uninitialized context fails safely
- passive-default Pad 3 context is deterministic
- target-anchor matched context is deterministic, if approved
- target-anchor mismatch fails safely
- stale context fails safely
- invalid context fails safely
- `PZ` remains parked
- no MIDI libraries are imported
- no ports are opened
- passive CLI remains unchanged

No tests are added by this document.

## 12. Confirmed Current Non-Implementation State

Current implementation state:

- selected target state is unimplemented
- anchor state is unimplemented
- selected isolated pad runtime state is unimplemented
- runtime state is unimplemented
- `PZ` is unimplemented
- selected pad switching execution is unimplemented
- selected pad anchor return execution is unimplemented

Current safety state:

- passive CLI remains read-only
- V1.34 reference remains untouched
- package metadata remains untouched
- hardware remains off
- no real MIDI libraries are required
- no ports are opened
- no MIDI is sent

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

## 14. Preconditions Before Any Implementation

Before any implementation:

- clean Git status
- full closeout passing
- V1.34 reference diff empty
- package metadata diff empty
- this sequencing note reviewed and accepted
- selected target state implementation plan reviewed and accepted
- anchor state implementation plan reviewed and accepted
- future tests specified in test-first form
- passive CLI behavior remains read-only
- no active CLI behavior is added
- no MIDI libraries are imported
- no ports are opened
- no MIDI is sent
- no hardware is required

## 15. Safe Next Options

Safe next options:

- docs-only review/acceptance gate for this sequencing note:
  - `Docs/V134_BEHAVIOR_PARITY_RUNTIME_STATE_IMPLEMENTATION_SEQUENCING_NOTE_AFTER_SELECTED_ISOLATED_PAD_RUNTIME_STATE_REVIEW_REVIEW.md`
- docs-only selected target state implementation plan
- docs-only anchor state implementation plan
- user-facing progress/timeline update
- pause at this clean sequencing checkpoint

## 16. Follow-On Review

The follow-on docs-only review gate is:

- `Docs/V134_BEHAVIOR_PARITY_RUNTIME_STATE_IMPLEMENTATION_SEQUENCING_NOTE_AFTER_SELECTED_ISOLATED_PAD_RUNTIME_STATE_REVIEW_REVIEW.md`

It accepts this sequencing note as the current planning boundary.

It keeps selected target state unimplemented.

It keeps anchor state unimplemented.

It keeps selected isolated pad runtime state unimplemented.

It keeps `PZ` parked.

It authorizes no implementation, tests, CLI commands, runtime state, dispatch,
MIDI, ports, package metadata changes, active behavior, or hardware behavior.

## 17. Recommendation

Proceed with a docs-only selected target state implementation plan.

Then plan selected target state implementation first.

Do not implement selected target state yet.

Do not implement anchor state yet.

Do not implement selected isolated pad runtime state yet.

Do not implement `PZ`.

Do not add MIDI, ports, active behavior, runtime execution, package metadata
changes, or hardware behavior.

## 18. Decision Summary

Runtime-state implementation sequencing is documented.

Selected target state should be planned first.

Anchor state should be planned second.

Selected isolated pad runtime state should be planned third.

`PZ` remains later and parked.

Hardware remains off.

No implementation in this slice.
