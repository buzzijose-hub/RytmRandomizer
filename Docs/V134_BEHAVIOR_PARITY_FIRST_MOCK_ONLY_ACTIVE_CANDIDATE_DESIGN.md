# V1.34 Behavior Parity First Mock-Only Active Candidate Design

## 1. Purpose

Restate and align the first mock-only active candidate design with the current
V1.34 behavior-parity runtime plan/report layer.

This document connects the existing accepted candidate to the newer
metadata-only runtime plan preview and read-only runtime plan report work.

This is a documentation-only design slice.

It adds no code, tests, closeout script changes, CLI changes, CLI execution
wiring, runtime execution, dispatch, command execution, MIDI, ports, package
metadata changes, active behavior, or hardware behavior.

## 2. Current Clean Baseline

Current branch:

- `modularize-v1.34`

Current HEAD before this design slice:

- `64be89f Add next branch selection after runtime plan report review`

Current phase:

- Passive/Mock Foundation Phase
- behavior-parity implementation phase
- mock-only active candidate proof exists
- mock-first active boundary exists
- metadata-only runtime plan preview metadata exists
- read-only runtime plan report exists and is accepted
- first mock-only active candidate design is now being aligned to the current
  runtime plan/report layer

Hardware status:

- Analog Rytm MKII off
- Analog Four MKII off
- hardware not required

## 3. Existing Accepted Candidate

The accepted first mock-only active candidate remains:

- source kind: `group_profile`
- source key: `2`
- source name: `My BD Hard`
- target scope: Pad 1 only
- target concept: Pad 1 / My BD Hard
- behavior mode: mock-only
- runtime plan status: blocked by default
- real MIDI: absent
- ports: absent
- hardware required: false

This candidate was already selected by:

- `Docs/FIRST_CANDIDATE_MOCK_ONLY_ACTIVE_TEST_DESIGN.md`
- `Docs/FIRST_CANDIDATE_MOCK_ONLY_ACTIVE_TEST_DESIGN_REVIEW.md`

The test-only proof is already accepted by:

- `Docs/MOCK_ONLY_ACTIVE_CANDIDATE_TESTS_REVIEW.md`

This design does not replace those documents.

It aligns them with the current runtime plan/report checkpoint.

## 4. Current Candidate Implementation Reality

Current mock-only candidate proof:

- `tests/test_mock_only_active_candidate.py`
- closeout label: `=== Test: Mock-Only Active Candidate ===`

Current mock-first active boundary:

- `rytm_randomizer/active_boundary.py`
- `tests/test_active_boundary.py`
- closeout label: `=== Test: Active Boundary ===`

Current active-boundary report:

- `rytm_randomizer/active_boundary_report.py`
- `tests/test_active_boundary_report.py`
- closeout label: `=== Test: Active Boundary Report ===`

This document does not modify those modules or tests.

## 5. Runtime Plan Relationship

Current runtime plan layer:

- `rytm_randomizer/runtime_plan.py`
- `tests/test_runtime_plan.py`
- closeout label: `=== Test: Runtime Plan ===`

For group profile `2`, the runtime plan preview must remain:

- status: blocked
- reason: execution not implemented
- reason code: `execution_not_implemented`
- supported: true
- parked: false
- would_execute: false
- mock_only: true
- sends_real_midi: false
- ports_allowed: false
- hardware_required: false

This means the candidate can be recognized as supported planning input while
still refusing to execute.

## 6. Runtime Plan Report Relationship

Current runtime plan report layer:

- `rytm_randomizer/runtime_plan_report.py`
- `tests/test_runtime_plan_report.py`
- closeout label: `=== Test: Runtime Plan Report ===`

For group profile `2`, the report should continue to show:

- source label: `group_profile:2`
- target: Pad 1 / My BD Hard
- status: blocked
- reason code: `execution_not_implemented`
- supported: true
- parked: false
- would_execute: false
- mock_only: true
- sends_real_midi: false
- ports_allowed: false
- hardware_required: false

This report visibility is the bridge between passive/mock planning and future
active-facing test design.

It is not execution.

## 7. Candidate Boundary

The first candidate may prove, in mock-only contexts:

- profile `2` can map to deterministic inert mock messages
- `MockMidiSender` can record those messages in memory only
- active-boundary requests can fail safely before emission
- active-boundary requests can emit mock messages only when mock conditions are
  satisfied
- runtime plan preview keeps the candidate blocked by default
- runtime plan report can summarize candidate status

The first candidate must not prove or attempt:

- real MIDI sending
- port opening
- hardware behavior
- active CLI execution
- scene execution
- command dispatch
- runtime mutation
- SysEx
- GUI/capture
- Analog Four
- Pads 5-12
- profile `4` support

## 8. Future Arming Semantics

Arming remains mock-only in the current active-boundary layer.

For the accepted candidate, any active-boundary request must continue to fail
safely unless all mock-only conditions are satisfied:

- source kind is `group_profile`
- source key is `2`
- request is armed
- dry-run confirmation is present
- sender is a `MockMidiSender`

This does not authorize real arming.

This does not authorize a CLI `--armed` path.

This does not authorize hardware validation.

## 9. Failure Conditions

The candidate must fail safely for:

- missing arming
- missing dry-run confirmation
- unsupported source kind
- unsupported or unknown key
- invalid request type
- invalid sender type
- profile `3` in active-boundary scope
- profile `4` in active-boundary scope
- any real MIDI dependency
- any port opening attempt

Failure must emit no real MIDI.

Failure must require no hardware.

## 10. Stop Conditions

Stop immediately if any future slice proposes:

- real MIDI import
- `mido`
- `rtmidi`
- port discovery
- port opening
- MIDI sending
- active CLI command
- runtime execution
- dispatch
- scene execution
- command execution
- runtime mutation
- hardware behavior
- hardware validation
- profile `4` active-boundary support without separate approval
- Pads 5-12
- Analog Four
- SysEx
- GUI/capture
- package metadata changes

## 11. Required Tests Before Any New Implementation

Before any new implementation beyond this design, a separate implementation
plan must define tests that prove:

- passive CLI remains read-only
- runtime plan report still includes profile `2`
- runtime plan preview remains blocked by default
- active-boundary failure paths emit no messages
- accepted mock-only path emits only inert mock messages
- `MockMidiSender` is the only sender used in tests
- no real MIDI libraries are imported
- no ports are opened
- V1.34 reference remains untouched
- package metadata remains untouched

Existing tests already cover much of this surface.

Any new implementation plan must name the exact gap it is closing.

## 12. Parked Scope

Still parked:

- runtime plan report CLI preview
- runtime plan report CLI implementation
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

## 13. Recommendation

Review and accept this alignment design next.

Then choose one of:

- docs-only implementation plan for one missing mock-only safety gap
- docs-only runtime plan report CLI preview design
- broader behavior-parity progress report
- pause at this clean checkpoint

Do not add real MIDI.

Do not open ports.

Do not turn on hardware.

## 14. Decision

The first mock-only active candidate remains group profile `2` / My BD Hard.

This design aligns that candidate with the current runtime plan/report layer.

Hardware remains off.

No implementation in this slice.
