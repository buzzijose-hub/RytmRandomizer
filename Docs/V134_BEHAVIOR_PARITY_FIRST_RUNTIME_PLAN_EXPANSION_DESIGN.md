# V1.34 Behavior Parity First Runtime Plan Expansion Design

## 1. Purpose

Design the first possible expansion after the accepted mock-only runtime plan
scaffold.

This is a documentation-only design.

It does not implement runtime plan expansion.

It does not add tests.

It does not change closeout.

It does not add CLI execution wiring, runtime execution, dispatch, command
execution, MIDI, ports, package metadata changes, active behavior, or hardware
behavior.

## 2. Current Clean Baseline

Current branch:

- `modularize-v1.34`

Current HEAD before this design slice:

- `9d86db2 Add next branch selection after runtime plan scaffold review`

Current phase:

- Passive/Mock Foundation Phase
- behavior-parity implementation phase
- mock-only runtime plan scaffold implemented and accepted
- next branch selected as first runtime plan expansion design
- first runtime plan expansion design now being documented

Hardware status:

- Analog Rytm MKII off
- Analog Four MKII off
- hardware not required

## 3. Accepted Current Runtime Plan Baseline

Accepted current files:

- `rytm_randomizer/runtime_plan.py`
- `tests/test_runtime_plan.py`
- `Scripts/closeout_check.ps1`

Accepted current concepts:

- `RuntimeIntent`
- `RuntimeSafetyEnvelope`
- `RuntimePlanPreview`
- `MockRuntimeProvider`
- `create_blocked_runtime_preview`
- `validate_runtime_intent_scope`

Accepted current closeout coverage:

- `=== Test: Runtime Plan ===`

Current behavior:

- group profiles `2` and `3` return blocked previews only
- unknown keys fail safely
- unsupported source kinds fail safely
- profile `4` remains parked
- `would_execute` remains `False`
- fake-provider records remain in memory only

## 4. Design Goal For The First Expansion

The first runtime plan expansion should improve visibility and safety metadata
without adding execution.

Recommended future expansion target:

- richer blocked-preview metadata
- clearer safe-failure reason categories
- clearer fake-provider recording trace

The expansion should help future tests answer:

- what source was requested
- why it remained blocked
- whether arming was missing
- whether scope was unsupported
- whether profile `4` stayed parked
- whether the preview would execute
- whether the preview remained mock-only

## 5. Proposed Future Concepts

Documented as design vocabulary only, not implementation:

- RuntimePlanReason
  - stable reason names for blocked previews
- RuntimePlanTrace
  - metadata describing how the preview was derived
- RuntimePlanSafetyFlags
  - explicit safety booleans preserved on every preview
- RuntimePlanSourceSummary
  - source kind, source key, source label, and target concept

These names are optional future design names. They are not implementation in
this slice.

## 6. Recommended Future Metadata

Future blocked previews may include metadata such as:

- source kind
- source key
- target
- source label
- request kind
- supported status
- parked status
- arming required
- armed status
- blocked reason
- mock-only status
- sends real MIDI status
- ports allowed status
- hardware required status
- would execute status

All metadata must remain inert and inspectable.

No metadata should imply that execution is available.

## 7. Safe-Failure Reason Categories

Future safe-failure categories may include:

- `execution_not_implemented`
- `unsupported_key`
- `unsupported_source_kind`
- `profile_4_parked`
- `missing_arming`
- `hardware_not_authorized`

These should remain planning vocabulary until a separate implementation plan is
reviewed and accepted.

## 8. Future Test Expectations

If this design later becomes implementation, future tests should prove:

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

## 9. Likely Future Implementation Scope

If later approved, the implementation should remain limited to:

- `rytm_randomizer/runtime_plan.py`
- `tests/test_runtime_plan.py`

No closeout script update should be needed because `tests/test_runtime_plan.py`
is already covered by:

- `=== Test: Runtime Plan ===`

The future implementation should be tiny and TDD-first.

## 10. Explicit Non-Goals

This design does not authorize:

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

## 11. Parked Scope

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

## 12. Safe Next Options

Safe next options after this design:

- docs-only review/acceptance gate for this design
- pause at this design checkpoint
- write a tiny implementation plan for metadata-only runtime plan expansion
  after review
- return to behavior-parity packet implementation planning

## 13. Recommendation

Review and accept this design next.

Then, if accepted, write a tiny implementation plan before any code changes.

Do not implement the expansion directly from this design.

Do not add CLI execution wiring.

Do not add real MIDI.

Do not open ports.

Do not turn on hardware.

## 14. Decision

The first runtime plan expansion design is documented.

The recommended future direction is metadata-only blocked-preview visibility.

Hardware remains off.

No implementation in this slice.

## 15. Review Status

This design is reviewed and accepted by:

- `Docs/V134_BEHAVIOR_PARITY_FIRST_RUNTIME_PLAN_EXPANSION_DESIGN_REVIEW.md`

The review accepts metadata-only blocked-preview visibility as the current
planning direction.

The next recommended task is:

- docs-only implementation plan for metadata-only runtime plan expansion
