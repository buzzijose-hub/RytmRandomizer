# V1.34 Behavior Parity First Runtime Plan Expansion Design Review

## 1. Purpose

Review and accept
`Docs/V134_BEHAVIOR_PARITY_FIRST_RUNTIME_PLAN_EXPANSION_DESIGN.md`.

Accept it as the current planning design for the first possible runtime plan
expansion after the mock-only runtime plan scaffold.

This is a documentation-only review gate.

It adds no implementation, tests, fixture changes, closeout script changes,
CLI changes, CLI execution wiring, runtime execution, dispatch, command
execution, MIDI, ports, package metadata changes, active behavior, or hardware
behavior.

## 2. Current Clean Baseline

Current branch:

- `modularize-v1.34`

Current HEAD before this review slice:

- `44a3b02 Add first runtime plan expansion design`

Current phase:

- Passive/Mock Foundation Phase
- behavior-parity implementation phase
- mock-only runtime plan scaffold implemented and accepted
- first runtime plan expansion design created
- first runtime plan expansion design now being reviewed

Hardware status:

- Analog Rytm MKII off
- Analog Four MKII off
- hardware not required

## 3. Review Decision

Accepted design:

- `Docs/V134_BEHAVIOR_PARITY_FIRST_RUNTIME_PLAN_EXPANSION_DESIGN.md`

Accepted design milestone:

- `44a3b02 Add first runtime plan expansion design`

Accepted upstream selection:

- `Docs/V134_BEHAVIOR_PARITY_NEXT_BRANCH_SELECTION_AFTER_RUNTIME_PLAN_SCAFFOLD_REVIEW.md`

This review accepts the first runtime plan expansion design as the current
planning baseline.

This review does not implement that expansion by itself.

## 4. Accepted Design Direction

Accepted future direction:

- metadata-only blocked-preview visibility
- clearer safe-failure reason categories
- clearer fake-provider trace vocabulary
- richer source summary metadata
- explicit safety flags

The accepted design keeps blocked previews as the default.

It does not authorize execution.

It does not authorize CLI execution wiring.

It does not authorize real MIDI or port behavior.

## 5. Accepted Future Design Vocabulary

Accepted as planning vocabulary only:

- RuntimePlanReason
- RuntimePlanTrace
- RuntimePlanSafetyFlags
- RuntimePlanSourceSummary

These names are not implementation in this review.

They may be refined by a later implementation plan.

## 6. Accepted Future Test Expectations

If this design later becomes an implementation plan, future tests should prove:

- supported profiles `2` and `3` still return blocked previews only
- profile `4` remains parked
- unknown keys fail safely
- unsupported source kinds fail safely
- missing arming remains visible in metadata
- all previews record `would_execute: False`
- all previews record mock-only safety
- fake-provider records remain in memory only
- no real MIDI libraries are imported
- no ports are opened
- no CLI execution names are exposed
- V1.34 reference remains untouched
- package metadata remains untouched

## 7. Accepted Future Implementation Boundary

If later approved, likely future implementation scope remains limited to:

- `rytm_randomizer/runtime_plan.py`
- `tests/test_runtime_plan.py`

No closeout script update should be needed because `tests/test_runtime_plan.py`
is already covered by:

- `=== Test: Runtime Plan ===`

Any future implementation must require a separate implementation plan before
code changes.

## 8. Confirmed Absent Behavior

This review confirms the current baseline adds no:

- runtime plan expansion code
- new tests
- fixture changes
- closeout script changes
- real MIDI
- `mido`
- `rtmidi`
- port discovery
- port opening
- MIDI sending
- active CLI execution
- `execute-command`
- `send-command`
- `hardware-test`
- selected pad switching execution
- selected pad target state mutation
- selected pad anchor return execution
- current anchor return execution
- isolated pad mutation execution
- runtime mutation
- dispatch
- command execution
- scene execution
- profile `4` mock mapper support
- fourth runtime-adjacent candidate
- Analog Four support
- Pads 5-12 support
- SysEx
- GUI/capture
- package metadata changes
- active behavior
- hardware behavior

`rytm_hybrid_randomizer_v134.py` remains untouched.

Package metadata remains untouched.

## 9. Parked Scope

Still parked:

- profile `4` mock mapper support
- fourth runtime-adjacent candidate
- selected pad switching execution
- selected pad target state mutation
- selected pad anchor return execution
- current anchor return execution
- isolated pad mutation execution
- runtime mutation
- active CLI commands
- real MIDI
- hardware validation

## 10. Safe Next Options

Safe next options:

- create a tiny implementation plan for metadata-only runtime plan expansion
- pause at this accepted design checkpoint
- write a broader user-facing progress/timeline update
- return to behavior-parity packet implementation planning

## 11. Recommendation

Create a tiny docs-only implementation plan for metadata-only runtime plan
expansion.

Do not implement directly from this design review.

Do not add CLI execution wiring.

Do not add real MIDI.

Do not open ports.

Do not turn on hardware.

## 12. Decision

The first runtime plan expansion design is accepted.

The next recommended task is a docs-only implementation plan for metadata-only
blocked-preview visibility.

Hardware remains off.

No implementation in this slice.

## 13. Follow-Up Status

The recommended implementation plan is now documented by:

- `Docs/V134_BEHAVIOR_PARITY_METADATA_ONLY_RUNTIME_PLAN_EXPANSION_IMPLEMENTATION_PLAN.md`

The plan remains documentation-only and limits any future implementation to:

- `rytm_randomizer/runtime_plan.py`
- `tests/test_runtime_plan.py`

The next recommended task is:

- docs-only review/acceptance gate for the metadata-only runtime plan expansion
  implementation plan
