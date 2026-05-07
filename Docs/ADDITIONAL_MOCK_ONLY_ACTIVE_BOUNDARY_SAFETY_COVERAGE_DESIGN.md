# Additional Mock-Only Active Boundary Safety Coverage Design

## 1. Purpose

Define a future test-only safety coverage slice for the current mock-first
active boundary.

This document is a design gate only.

No tests, implementation, real MIDI, port opening, active CLI behavior,
dispatch, execution, or hardware behavior is added by this document.

## 2. Current Clean Baseline

Current branch:

- modularize-v1.34

Current HEAD before this slice:

- 6d4ce4a Add session agenda handoff review

Current phase:

- Passive/Mock Foundation Phase
- session agenda handoff accepted
- mock-first active boundary exists for test-only evaluation
- read-only active boundary report and CLI preview exist
- no real MIDI or hardware validation started

Hardware status:

- Analog Rytm MKII off
- Analog Four MKII off
- hardware not required

## 3. Current Accepted Coverage

Current active boundary coverage already proves:

- importing `rytm_randomizer.active_boundary` prints nothing
- missing arming emits no messages
- missing dry-run confirmation emits no messages
- unknown keys emit no messages
- profile `"4"` remains parked and emits no messages
- profile `"3"` remains unsupported by the active boundary
- unsupported source kinds emit no messages
- profile `"2"` emits mock messages only when armed and dry-run confirmed
- repeated accepted evaluations are deterministic
- repeated failure evaluations are deterministic
- failure paths leave sender state empty
- invalid request or sender types fail before message emission
- passive CLI report remains read-only
- no real MIDI libraries are imported
- no active CLI command names are exposed by the boundary module

Current active boundary report coverage already proves:

- importing `rytm_randomizer.active_boundary_report` prints nothing
- report data is deterministic and copied
- accepted and unsupported profiles are summarized correctly
- active behavior, real MIDI, ports, dispatch, execution, and hardware behavior
  are recorded as absent
- profile `"3"` and profile `"4"` remain unsupported by the active boundary
- no active behavior names are exposed by the report module

## 4. Additional Coverage Goal

The next safety test slice should strengthen confidence around separation
between:

- passive CLI visibility
- read-only active boundary reporting
- mock-only active boundary evaluation
- unsupported scope
- real MIDI absence

It should not expand active-boundary scope.

It should not add profile `"3"` support.

It should not add profile `"4"` support.

It should not add real MIDI, ports, active CLI commands, or hardware behavior.

## 5. Proposed Future Test Ownership

Preferred future file ownership:

- update `tests/test_active_boundary.py`
- update `tests/test_active_boundary_report.py`
- update `tests/test_cli.py`

No new test file should be needed unless a future review finds the existing
files too broad.

No closeout script update should be needed because these files are already
covered by closeout.

## 6. Proposed Additional Active Boundary Tests

Future `tests/test_active_boundary.py` coverage may include:

- accepted result metadata includes target and remains immutable
- failure result metadata includes source kind, source key, mock-only status,
  and sends-real-MIDI false
- request source keys are normalized to strings before evaluation
- custom request metadata never leaks into emitted mock message metadata
- accepted evaluation does not mutate the original request metadata object
- accepted evaluation does not mutate the source mock mapper output
- sender receives exactly the emitted messages and no extras
- source kind matching remains exact and does not accept uppercase or plural
  variants
- target values remain metadata only and do not select ports or hardware

These tests must continue to use `MockMidiSender` only.

## 7. Proposed Additional Active Boundary Report Tests

Future `tests/test_active_boundary_report.py` coverage may include:

- formatted report remains newline-independent when joined for CLI output
- summarized report does not expose real MIDI, port provider, or hardware
  target fields
- unsupported source kinds remain limited to scene and command
- report closeout coverage lists only passive/mock labels
- mutating formatted report output does not mutate future report output
- report remains decoupled from `evaluate_mock_active_boundary`

These tests must not evaluate active boundary requests from the report layer.

## 8. Proposed Additional Passive CLI Tests

Future `tests/test_cli.py` coverage may include:

- `active-boundary-report` repeated runs are deterministic
- `active-boundary-report` output shows no real MIDI, ports, dispatch,
  execution, or hardware behavior
- `active-boundary-report` output shows profile `"3"` unsupported by the
  active boundary
- `active-boundary-report` output shows profile `"4"` parked/unsupported
- top-level help still lists only passive visibility commands, not active
  execution commands
- passive CLI exposes no `execute-command`, `send-command`, or
  `hardware-test` command
- passive CLI import does not import real MIDI libraries

The CLI tests must call only passive commands.

They must not call `evaluate_mock_active_boundary`.

They must not construct `MockMidiSender`.

## 9. Explicit Non-Goals

This design does not authorize:

- implementation in this slice
- new tests in this slice
- real MIDI
- mido
- MIDI port opening
- MIDI sending
- active CLI commands
- CLI wiring to active boundary evaluation
- dispatch
- command execution
- scene execution
- hardware behavior
- SysEx
- GUI/capture
- Analog Four support
- Pads 5-12 support
- machine/profile expansion
- profile `"4"` implementation
- profile `"3"` active-boundary support
- hardware validation

## 10. Future Implementation Constraints

If this design is accepted, the future implementation slice must:

- remain test-only
- modify only existing test files unless separately approved
- keep `rytm_randomizer/active_boundary.py` unchanged unless a failing test
  exposes an actual safety bug
- keep `rytm_randomizer/active_boundary_report.py` unchanged unless a failing
  test exposes an actual safety bug
- keep `rytm_randomizer/cli.py` unchanged unless a fixture-backed passive CLI
  safety assertion requires it
- avoid closeout script changes unless a new test file is explicitly approved
- keep V1.34 reference untouched
- run full closeout before commit

## 11. Stop Conditions

Stop immediately if:

- any real MIDI import appears
- any port opening appears
- any active CLI command appears
- any passive CLI command evaluates active boundary requests
- any passive CLI command constructs or uses `MockMidiSender`
- any dispatch or execution behavior appears
- any profile `"4"` implementation appears
- any profile `"3"` active-boundary support appears
- any V1.34 reference diff appears
- hardware state is uncertain

## 12. Recommended Future Slice

Next recommended task after this design:

- review and accept this additional mock-only active boundary safety coverage
  design

After review, a future implementation slice may add only the accepted
test-only coverage.

Hardware remains off.

## 13. Decision

Additional mock-only active boundary safety coverage is planned at design
altitude only.

No implementation is added in this slice.

Hardware remains off.
