# V1.34 Behavior Parity Next Branch Selection After First Mock-Only Active Candidate Design Review

## 1. Purpose

Select the next safe branch after accepting the first mock-only active
candidate design alignment.

This is a documentation-only branch-selection checkpoint.

It adds no implementation, tests, fixtures, closeout script changes, CLI
changes, CLI execution wiring, runtime execution, dispatch, command execution,
MIDI, ports, package metadata changes, active behavior, or hardware behavior.

## 2. Current Clean Baseline

Current branch:

- `modularize-v1.34`

Current HEAD before this selection slice:

- `4c2fea7 Add first mock-only active candidate design review`

Current phase:

- Passive/Mock Foundation Phase
- behavior-parity implementation phase
- first mock-only active candidate design alignment accepted
- read-only runtime plan report exists
- read-only active-boundary report exists
- next active-facing mock-only safety gap is being selected

Hardware status:

- Analog Rytm MKII off
- Analog Four MKII off
- hardware not required

## 3. Accepted Upstream Review

Accepted review:

- `Docs/V134_BEHAVIOR_PARITY_FIRST_MOCK_ONLY_ACTIVE_CANDIDATE_DESIGN_REVIEW.md`

Accepted design:

- `Docs/V134_BEHAVIOR_PARITY_FIRST_MOCK_ONLY_ACTIVE_CANDIDATE_DESIGN.md`

Accepted review milestone:

- `4c2fea7 Add first mock-only active candidate design review`

Accepted candidate:

- group profile `2` / My BD Hard
- Pad 1 only
- mock-only
- runtime plan blocked by default
- visible in Runtime Plan Report
- no real MIDI
- no ports
- no hardware

## 4. Current Active-Facing Read-Only Surfaces

Runtime plan/report surface:

- `rytm_randomizer/runtime_plan.py`
- `tests/test_runtime_plan.py`
- `rytm_randomizer/runtime_plan_report.py`
- `tests/test_runtime_plan_report.py`
- closeout labels:
  - `=== Test: Runtime Plan ===`
  - `=== Test: Runtime Plan Report ===`

Active boundary/report surface:

- `rytm_randomizer/active_boundary.py`
- `tests/test_active_boundary.py`
- `rytm_randomizer/active_boundary_report.py`
- `tests/test_active_boundary_report.py`
- closeout labels:
  - `=== Test: Active Boundary ===`
  - `=== Test: Active Boundary Report ===`

Mock-only candidate proof:

- `tests/test_mock_only_active_candidate.py`
- closeout label:
  - `=== Test: Mock-Only Active Candidate ===`

## 5. Observed Gap

The runtime plan report and active-boundary report are both correct, but they
now describe adjacent parts of the same future active-facing story.

Runtime plan report currently shows:

- profile `2` as a supported planning input
- profile `3` as a supported planning input
- profile `4` as parked
- every input blocked by default
- no execution, MIDI, ports, or hardware

Active-boundary report currently shows:

- profile `2` as the accepted active-boundary candidate
- profile `3` as unsupported by active-boundary scope
- profile `4` as parked until separately approved
- no execution, MIDI, ports, or hardware

That difference is intentional.

The next useful safety step is to document a plan for proving these two
read-only surfaces stay aligned where they should align, and intentionally
different where they should remain different.

## 6. Candidate Branch Options

Safe branch options after the accepted design review:

- pause at the clean checkpoint
- write a broader behavior-parity progress report
- create a docs-only runtime plan report CLI preview design
- create a docs-only active-boundary/runtime-plan report alignment safety test
  plan
- create an implementation plan for one clearly named missing mock-only safety
  gap

## 7. Selected Next Branch

Selected next branch:

- docs-only active-boundary/runtime-plan report alignment safety test plan

This next branch should remain documentation-only.

It should not implement tests yet.

It should not modify code.

It should not add CLI behavior.

It should not add runtime execution, dispatch, MIDI, ports, active behavior,
or hardware behavior.

## 8. Rationale

This branch is the most useful next move because:

- the project now has more than one active-facing read-only safety surface
- the reports should agree on the accepted candidate profile `2`
- the reports should preserve the intentional difference for profile `3`
- profile `4` should remain parked/unsupported unless separately approved
- this closes a real documentation gap before further implementation
- this is smaller and safer than adding more CLI visibility
- it keeps the path toward future active behavior mock-only and test-gated

## 9. Expected Future Plan Scope

The selected future plan should define tests, still without implementing them,
that would prove:

- runtime plan report includes profile `2` as supported planning input
- active-boundary report accepts profile `2` as the only active-boundary
  candidate
- runtime plan report includes profile `3` as supported planning input
- active-boundary report keeps profile `3` unsupported for active-boundary
  scope
- runtime plan report keeps profile `4` parked
- active-boundary report keeps profile `4` parked until separately approved
- both reports show mock-only behavior
- both reports show no real MIDI
- both reports show no port opening
- both reports show no hardware requirement
- no CLI execution wiring is introduced
- no runtime execution is introduced

## 10. Parked Scope

Still parked:

- runtime plan report CLI preview
- runtime plan report CLI implementation
- profile `4` mock mapper support
- profile `4` active-boundary support
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

## 11. Confirmed Boundaries

This selection adds no:

- implementation
- tests
- fixtures
- closeout script changes
- CLI changes
- CLI execution wiring
- runtime execution
- dispatch
- command execution
- scene execution
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
- profile `4` active-boundary support
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

Hardware remains off.

## 12. Decision

The next branch is selected:

- docs-only active-boundary/runtime-plan report alignment safety test plan

The next recommended task is to create that docs-only safety test plan.

Hardware remains off.

No implementation in this slice.

## 13. Follow-Up Status

The selected docs-only alignment safety test plan is now documented by:

- `Docs/V134_BEHAVIOR_PARITY_ACTIVE_RUNTIME_REPORT_ALIGNMENT_SAFETY_TEST_PLAN.md`

The next recommended task is a docs-only review/acceptance gate for that plan.

The plan does not authorize implementation by itself.
