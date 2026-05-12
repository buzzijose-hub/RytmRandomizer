# V1.34 Behavior Parity Read-Only Runtime Plan Report Design

## 1. Purpose

Design a future read-only runtime plan report after the accepted metadata-only
runtime plan preview metadata baseline.

This is a documentation-only design.

It does not implement the report.

It does not add tests, fixture changes, closeout script changes, CLI changes,
CLI execution wiring, runtime execution, dispatch, command execution, MIDI,
ports, package metadata changes, active behavior, or hardware behavior.

## 2. Current Clean Baseline

Current branch:

- `modularize-v1.34`

Current HEAD before this design slice:

- `573ddf3 Add next branch selection after runtime preview metadata`

Current phase:

- Passive/Mock Foundation Phase
- behavior-parity implementation phase
- mock-only runtime plan scaffold implemented and accepted
- metadata-only runtime plan preview metadata implemented and accepted
- read-only runtime plan report design now being documented

Hardware status:

- Analog Rytm MKII off
- Analog Four MKII off
- hardware not required

## 3. Accepted Upstream Inputs

Accepted next-branch selection:

- `Docs/V134_BEHAVIOR_PARITY_NEXT_BRANCH_SELECTION_AFTER_RUNTIME_PLAN_PREVIEW_METADATA_REVIEW.md`

Accepted runtime preview metadata review:

- `Docs/V134_BEHAVIOR_PARITY_METADATA_ONLY_RUNTIME_PLAN_PREVIEW_METADATA_CHECKPOINT_REVIEW.md`

Accepted runtime preview metadata checkpoint:

- `Docs/V134_BEHAVIOR_PARITY_METADATA_ONLY_RUNTIME_PLAN_PREVIEW_METADATA_CHECKPOINT.md`

Accepted runtime preview metadata implementation:

- `0e902a8 Add metadata-only runtime plan preview metadata`

## 4. Current Runtime Plan Baseline

The accepted runtime plan baseline is:

- mock-only
- metadata-only
- blocked by default
- copied immutable preview metadata
- stable reason codes
- no runtime execution
- no CLI execution wiring
- no MIDI
- no ports
- no hardware requirement

Every preview still records:

- `would_execute: False`
- `mock_only: True`
- `sends_real_midi: False`
- `ports_allowed: False`
- `hardware_required: False`

## 5. Report Design Goal

The future report should summarize existing runtime plan metadata in a
read-only way.

It should make the current runtime planning boundary visible without expanding
runtime behavior.

It should answer:

- which planning inputs are supported but blocked
- which planning inputs are parked
- how unknown or unsupported inputs fail safely
- which reason codes are currently used
- whether any preview would execute
- whether any real MIDI or port behavior exists
- whether hardware is required

## 6. Proposed Future Report Content

A future read-only runtime plan report may include:

- report title
- current mode:
  - mock-only
  - metadata-only
  - blocked by default
- supported planning inputs:
  - group profile `2`
  - group profile `3`
- parked planning inputs:
  - group profile `4`
- unsupported planning inputs:
  - unknown keys
  - unsupported source kinds
- reason-code summary:
  - `execution_not_implemented`
  - `unsupported_key`
  - `unsupported_source_kind`
  - `profile_4_parked`
  - `missing_arming`
- safety summary:
  - `would_execute: False`
  - `mock_only: True`
  - `sends_real_midi: False`
  - `ports_allowed: False`
  - `hardware_required: False`
- closeout coverage:
  - `=== Test: Runtime Plan ===`

## 7. Proposed Future Module Shape

Possible future implementation module, only after a separate accepted
implementation plan:

- `rytm_randomizer/runtime_plan_report.py`

Possible future tests, only after a separate accepted implementation plan:

- `tests/test_runtime_plan_report.py`

Possible future function names, for design discussion only:

- `build_runtime_plan_report()`
- `format_runtime_plan_report(report=None)`
- `summarize_runtime_plan_report(report=None)`

These names are not implementation in this slice.

## 8. Report Data Source

The future report should derive from existing runtime plan concepts where
possible:

- `RuntimeIntent`
- `RuntimeSafetyEnvelope`
- `RuntimePlanPreview`
- `create_blocked_runtime_preview`
- `validate_runtime_intent_scope`

The report should not create a runtime execution path.

The report should not call any MIDI library.

The report should not open ports.

The report should not require hardware.

## 9. Determinism And Copy Safety

If implemented later, the report should be deterministic:

- stable ordering
- stable labels
- stable reason-code output
- stable formatter output

Returned data should be copied or immutable enough that callers cannot mutate
module-owned state.

The report should print nothing during import.

The report should have no import-time side effects.

## 10. Future Test Expectations

If a later implementation plan is approved, tests should prove:

- importing the report module prints nothing
- report contains supported profiles `2` and `3`
- report marks profile `4` as parked
- report includes unknown and unsupported safe-failure categories
- report includes stable reason codes
- report records `would_execute: False`
- report records `mock_only: True`
- report records `sends_real_midi: False`
- report records `ports_allowed: False`
- report records `hardware_required: False`
- formatter output is deterministic
- returned data is copied or immutable
- no real MIDI libraries are imported
- no ports are opened
- no CLI execution names are exposed
- V1.34 reference remains untouched
- package metadata remains untouched

## 11. CLI Position

Do not add a runtime plan report CLI command in the first report
implementation.

If CLI visibility is ever considered later, it must require a separate design,
review, implementation plan, tests, and closeout checkpoint.

The current design is report-layer only.

## 12. Required Future Implementation Boundary

Any future implementation must remain:

- read-only
- in-memory
- deterministic
- mock-only
- metadata-only
- side-effect free on import
- disconnected from CLI execution
- disconnected from MIDI
- disconnected from ports
- disconnected from hardware

Any future implementation must not add:

- runtime execution
- dispatch
- command execution
- scene execution
- MIDI
- ports
- active CLI commands
- hardware behavior

## 13. Parked Scope

Still parked:

- runtime plan report implementation
- runtime plan report CLI command
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

## 14. Confirmed Absent Behavior

This design adds no:

- implementation
- tests
- fixture changes
- closeout script changes
- CLI changes
- CLI execution wiring
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
- runtime mutation
- dispatch
- command execution
- scene execution
- Analog Four support
- Pads 5-12 support
- SysEx
- GUI/capture
- package metadata changes
- active behavior
- hardware behavior

`rytm_hybrid_randomizer_v134.py` remains untouched.

Package metadata remains untouched.

## 15. Safe Next Options

Safe next options:

- docs-only review/acceptance gate for this design
- pause at this clean design checkpoint
- broader behavior-parity progress report

Only after review and a separate implementation plan should a future report
implementation be considered.

## 16. Recommendation

Create a docs-only review/acceptance gate for this design next.

Do not implement the report yet.

Do not add CLI execution wiring.

Do not add real MIDI.

Do not open ports.

Do not turn on hardware.

## 17. Decision

The read-only runtime plan report design is documented.

The design does not authorize implementation by itself.

Hardware remains off.

## 18. Review Status

This design is reviewed and accepted by:

- `Docs/V134_BEHAVIOR_PARITY_READ_ONLY_RUNTIME_PLAN_REPORT_DESIGN_REVIEW.md`

The accepted future implementation scope remains limited to a report layer
only, and only after a separate accepted implementation plan:

- `rytm_randomizer/runtime_plan_report.py`
- `tests/test_runtime_plan_report.py`

The next recommended task is a docs-only implementation plan for the read-only
runtime plan report.

No implementation, tests, CLI changes, CLI execution wiring, dispatch, command
execution, runtime mutation, MIDI, ports, package metadata changes, active
behavior, or hardware behavior is authorized by this design review.
