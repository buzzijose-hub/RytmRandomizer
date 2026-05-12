# V1.34 Behavior Parity Active/Runtime Report Alignment Safety Test Plan

## 1. Purpose

Define a future test-only safety plan for aligning the read-only runtime plan
report and the read-only active-boundary report.

This plan exists to make sure both active-facing safety surfaces continue to
tell the same story where they should align, and intentionally different
stories where their scopes differ.

This is a documentation-only test plan.

It adds no implementation, tests, fixtures, closeout script changes, CLI
changes, CLI execution wiring, runtime execution, dispatch, command execution,
MIDI, ports, package metadata changes, active behavior, or hardware behavior.

## 2. Current Clean Baseline

Current branch:

- `modularize-v1.34`

Current HEAD before this planning slice:

- `629bce6 Add next branch selection after first mock-only candidate review`

Current phase:

- Passive/Mock Foundation Phase
- behavior-parity implementation phase
- first mock-only active candidate design alignment accepted
- read-only runtime plan report exists
- read-only active-boundary report exists
- next alignment safety tests are now being planned

Hardware status:

- Analog Rytm MKII off
- Analog Four MKII off
- hardware not required

## 3. Accepted Upstream Selection

Accepted upstream selection:

- `Docs/V134_BEHAVIOR_PARITY_NEXT_BRANCH_SELECTION_AFTER_FIRST_MOCK_ONLY_ACTIVE_CANDIDATE_DESIGN_REVIEW.md`

Accepted upstream milestone:

- `629bce6 Add next branch selection after first mock-only candidate review`

Selected branch:

- docs-only active-boundary/runtime-plan report alignment safety test plan

This document fulfills that selected branch.

## 4. Current Report Surfaces

Runtime plan report:

- module: `rytm_randomizer/runtime_plan_report.py`
- tests: `tests/test_runtime_plan_report.py`
- closeout label: `=== Test: Runtime Plan Report ===`

Active-boundary report:

- module: `rytm_randomizer/active_boundary_report.py`
- tests: `tests/test_active_boundary_report.py`
- closeout label: `=== Test: Active Boundary Report ===`

Mock-only candidate proof:

- tests: `tests/test_mock_only_active_candidate.py`
- closeout label: `=== Test: Mock-Only Active Candidate ===`

Active boundary:

- module: `rytm_randomizer/active_boundary.py`
- tests: `tests/test_active_boundary.py`
- closeout label: `=== Test: Active Boundary ===`

## 5. Alignment Intent

The reports should align on:

- profile `2` / My BD Hard as the first mock-only active candidate
- mock-only behavior
- no real MIDI
- no port opening
- no hardware requirement
- no runtime execution
- no CLI execution wiring

The reports should intentionally differ on:

- profile `3` / My BD Classic

Reason:

- runtime plan report may list profile `3` as a supported planning input
- active-boundary report must keep profile `3` unsupported for
  active-boundary scope

The reports should both keep parked/safe status for:

- profile `4` / My BD Acoustic

Reason:

- profile `4` remains parked until separately approved
- profile `4` must not become active-boundary supported by accident

## 6. Future Test File Ownership

Future implementation, only after review and approval of this plan, should use:

- create: `tests/test_active_runtime_report_alignment.py`
- update: `Scripts/closeout_check.ps1`

Expected future closeout label:

- `=== Test: Active/Runtime Report Alignment ===`

Do not edit these files in this planning slice.

## 7. Future Test Cases

Future tests should prove:

- importing the alignment test dependencies prints nothing
- runtime plan report includes profile `2` as supported planning input
- active-boundary report accepts only profile `2` as the active-boundary
  candidate
- runtime plan report includes profile `3` as supported planning input
- active-boundary report lists profile `3` as unsupported for active-boundary
  scope
- runtime plan report keeps profile `4` parked
- active-boundary report lists profile `4` as parked until separately approved
- both reports expose mock-only status
- both reports expose no real MIDI
- both reports expose no port opening
- both reports expose no hardware requirement
- both reports expose no runtime execution or active CLI execution wiring
- no real MIDI library is imported
- no ports are opened
- no MIDI is sent
- no active behavior is introduced

## 8. Future Deterministic Assertions

The future alignment tests should assert these stable values:

Runtime plan report:

- supported planning input keys: `("2", "3")`
- parked planning input keys: `("4",)`
- profile `2` reason code: `execution_not_implemented`
- profile `3` reason code: `execution_not_implemented`
- profile `4` reason code: `profile_4_parked`
- `would_execute`: `False`
- `mock_only`: `True`
- `sends_real_midi`: `False`
- `ports_allowed`: `False`
- `hardware_required`: `False`
- `runtime_execution`: `absent`
- `cli_execution_wiring`: `absent`

Active-boundary report:

- accepted key: `2`
- unsupported keys: `("3", "4")`
- profile `3` reason: mock mapper/report scope only; not active-boundary
  supported
- profile `4` reason: parked until separately approved
- `mock_only`: `True`
- `real_midi`: `absent`
- `port_opening`: `absent`
- `hardware_required`: `False`
- `active_cli_behavior`: `absent`
- `dispatch`: `absent`
- `command_execution`: `absent`
- `scene_execution`: `absent`
- `hardware_behavior`: `absent`

## 9. Future Test Sketch

The future test file may use helper functions like these, implemented in the
test file only:

```python
def _keys(items):
    return tuple(item["source_key"] for item in items)


def _profile_reason(profiles, key):
    return next(profile["reason"] for profile in profiles if profile["profile_key"] == key)
```

Likely future test names:

- `test_runtime_and_active_reports_align_on_profile_2_candidate`
- `test_profile_3_remains_runtime_supported_but_active_boundary_unsupported`
- `test_profile_4_remains_parked_in_both_report_surfaces`
- `test_report_safety_boundaries_match_no_midi_no_ports_no_hardware`
- `test_alignment_imports_no_real_midi_libraries`
- `test_alignment_report_tests_do_not_evaluate_active_boundary_requests`

The last test should inspect the alignment test/report modules and ensure the
alignment layer does not instantiate `MockMidiSender`, evaluate active-boundary
requests, or call execution-like functions.

## 10. Future Implementation Boundaries

Future alignment tests must not:

- change runtime report behavior
- change active-boundary report behavior
- change active-boundary evaluation behavior
- instantiate real MIDI objects
- instantiate a real port provider
- instantiate `MockMidiSender` unless a later approved plan explicitly needs it
- evaluate active-boundary requests
- call command execution
- call scene execution
- add CLI commands
- add CLI execution wiring
- add dispatch
- add runtime mutation
- add profile `4` support
- add active behavior
- require hardware

The future implementation should be test-only.

If any future alignment test fails, stop and review the report semantics before
changing implementation.

## 11. Parked Scope

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

## 12. Confirmed Absent Behavior

This plan confirms no:

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

## 13. Acceptance Criteria For This Plan

This plan is acceptable if it:

- preserves profile `2` as the first mock-only active candidate
- preserves profile `3` as runtime-plan supported but active-boundary
  unsupported
- preserves profile `4` as parked/unsupported
- keeps the future scope test-only
- requires no real MIDI
- requires no ports
- requires no hardware
- avoids implementation in this slice

## 14. Next Recommended Task

Create a docs-only review/acceptance gate for this alignment safety test plan.

After that review, a later separately approved implementation slice may add:

- `tests/test_active_runtime_report_alignment.py`
- `=== Test: Active/Runtime Report Alignment ===`

Hardware remains off.

No implementation in this slice.
