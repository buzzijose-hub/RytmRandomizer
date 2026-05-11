# V1.34 Behavior Parity PZ Implementation Readiness Decision Note After Runtime-State Planning Review

## 1. Purpose

Decide whether `PZ` is ready for implementation planning after the accepted
runtime-state planning progress report review.

This is a documentation-only decision note.

It records readiness status and remaining prerequisites before any future `PZ`
implementation plan.

It adds no implementation, tests, CLI commands, runtime state, dispatch, MIDI,
ports, package metadata changes, active behavior, or hardware behavior.

## 2. Current Clean Baseline

Current branch:

- `modularize-v1.34`

Current HEAD before this decision note:

- `84313e3 Add runtime-state planning progress report review`

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
- `PZ` implementation readiness now being evaluated

Hardware status:

- Analog Rytm MKII off
- Analog Four MKII off
- hardware not required

## 3. Accepted Upstream Planning Context

Accepted upstream planning includes:

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

These documents provide planning vocabulary and guardrails only.

They do not implement runtime behavior.

## 4. Current PZ Readiness Decision

Decision:

- `PZ` is not ready for implementation yet.
- `PZ` is not ready for test-only implementation yet.
- `PZ` is ready for one more planning step: a selected isolated pad
  runtime-state implementation plan or a narrower `PZ` prerequisites plan.

Reason:

- selected target state is accepted for planning but unimplemented
- anchor state is accepted for planning but unimplemented
- selected isolated pad runtime state is accepted for planning but
  unimplemented
- no runtime state object exists
- no selected target state tests exist
- no anchor state tests exist
- no selected isolated pad runtime-state tests exist
- no `PZ` safe-failure tests exist
- `PZ` still cannot safely answer selected target, known anchor, target-anchor
  match, or stale/invalid runtime context

## 5. What Is Ready

The following are ready as planning foundations:

- shared runtime-state vocabulary
- `PZ` behavior meaning
- selected target state vocabulary
- anchor state vocabulary
- selected isolated pad runtime-state vocabulary
- safe failure expectations
- passive command read-only boundary
- no-MIDI/no-port/no-hardware boundary
- closeout discipline

These foundations make the next planning step possible.

They do not make `PZ` implementation safe yet.

## 6. What Is Not Ready

The following are not ready:

- `PZ` implementation
- `PZ` test-only implementation
- selected pad anchor return behavior
- selected pad switching behavior
- runtime state mutation
- CLI execution wiring
- dispatch
- MIDI
- ports
- hardware behavior

`PZ` should remain parked until the runtime prerequisites have their own
accepted implementation plan and tests.

## 7. Required Prerequisites Before Any PZ Implementation Plan

Before any future `PZ` implementation plan:

- clean Git status
- full closeout passing
- V1.34 reference diff empty
- package metadata diff empty
- this readiness decision reviewed and accepted
- selected target state implementation plan exists
- anchor state implementation plan exists
- selected isolated pad runtime-state implementation plan exists
- safe failure cases are specified in test-first form
- passive CLI behavior remains read-only
- no MIDI libraries are imported
- no ports are opened
- no MIDI is sent
- explicit statement that `PZ` remains non-hardware-facing

## 8. Minimum Future Test Categories Before PZ

Before any future `PZ` implementation, tests should exist or be planned for:

- unset selected target safe failure
- default selected target behavior
- explicit selected target behavior
- unknown anchor safe failure
- unsupported anchor safe failure
- target-anchor mismatch safe failure
- stale selected isolated pad runtime context safe failure
- invalid selected isolated pad runtime context safe failure
- `PZ` remains parked until explicitly approved
- passive CLI commands remain unchanged
- no real MIDI imports
- no port opening
- no MIDI sending
- V1.34 reference remains untouched
- package metadata remains untouched

## 9. Recommended Next Planning Branch

Recommended next branch:

- docs-only selected isolated pad runtime-state implementation plan

Reason:

- `PZ` depends on selected isolated pad runtime state.
- selected isolated pad runtime state depends on selected target state and
  anchor state.
- planning the small runtime-state implementation surface first is safer than
  planning `PZ` behavior directly.

Alternative safe branches:

- docs-only selected target state implementation plan
- docs-only anchor state implementation plan
- user-facing progress/timeline update
- pause at this clean checkpoint

## 10. Confirmed Absent Behavior

This decision note confirms no:

- code changes
- test changes
- closeout script changes
- package metadata changes
- active CLI command
- `execute-command`
- `send-command`
- `hardware-test`
- dispatch
- command execution
- scene execution
- mutation execution
- runtime state implementation
- selected target state implementation
- anchor state implementation
- selected isolated pad runtime state implementation
- selected pad switching execution
- selected pad anchor return execution
- `PZ` implementation
- profile `4` mock mapper support
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

## 11. Decision Summary

`PZ` is not ready for implementation yet.

`PZ` remains parked.

Runtime state remains unimplemented.

Selected target state remains unimplemented.

Anchor state remains unimplemented.

Selected isolated pad runtime state remains unimplemented.

The next recommended task is a docs-only review/acceptance gate for this
readiness decision note.

Hardware remains off.

No implementation in this decision note.

## 12. Follow-Up Status

This decision note is now followed by:

- `Docs/V134_BEHAVIOR_PARITY_PZ_IMPLEMENTATION_READINESS_DECISION_NOTE_AFTER_RUNTIME_STATE_PLANNING_REVIEW_REVIEW.md`

That review accepts the readiness decision that `PZ` is not ready for
implementation yet and recommends a docs-only selected isolated pad
runtime-state implementation plan as the next safe planning branch.
