# V1.34 Mock Runtime/Active Bridge Report CLI Preview Design Spec

## 1. Purpose

Design a future passive CLI preview command for the read-only mock
runtime/active bridge report.

The future command should print the existing formatted bridge report only.

This is a documentation-only design/spec.

It adds no implementation, tests, fixtures, closeout script changes, CLI
changes, CLI execution wiring, runtime execution, dispatch, command execution,
MIDI, ports, package metadata changes, active behavior, or hardware behavior.

## 2. Current Clean Baseline

Current branch:

- `modularize-v1.34`

Current HEAD before this design/spec slice:

- `901808c Add next branch selection after bridge report review`

Current phase:

- Behavior-Parity Passive/Mock Visibility Phase
- mock runtime/active bridge implemented and accepted
- mock runtime/active bridge report implemented and accepted
- next branch selected as bridge report CLI preview design/spec
- bridge report CLI preview design/spec now being documented

Hardware status:

- Analog Rytm MKII off
- Analog Four MKII off
- hardware not required

## 3. Accepted Upstream Scope

Accepted upstream review:

- `Docs/V134_BEHAVIOR_PARITY_MOCK_RUNTIME_ACTIVE_BRIDGE_REPORT_REVIEW.md`

Accepted upstream milestone:

- `7bd532c Add mock runtime active bridge report review`

Accepted branch selection:

- `Docs/V134_BEHAVIOR_PARITY_NEXT_BRANCH_SELECTION_AFTER_MOCK_RUNTIME_ACTIVE_BRIDGE_REPORT_REVIEW.md`

Accepted bridge report implementation:

- `75f731c Add mock runtime active bridge report`

The accepted report implementation provides:

- `build_mock_runtime_active_bridge_report()`
- `summarize_mock_runtime_active_bridge_report(report=None)`
- `format_mock_runtime_active_bridge_report(report=None)`

The report remains read-only, mock-only, metadata-only, deterministic, and
in-memory.

## 4. Proposed Future CLI Command

Proposed passive CLI command:

- `python -m rytm_randomizer.cli mock-runtime-active-bridge-report`

Proposed help command:

- `python -m rytm_randomizer.cli mock-runtime-active-bridge-report --help`

The command name is intentionally long and explicit.

It should communicate that the command is:

- mock-runtime scoped
- active-bridge report scoped
- report-only
- passive

## 5. Proposed Future Behavior

The future command should:

- call `format_mock_runtime_active_bridge_report()`
- print the returned formatted report lines to stdout
- exit 0
- accept no options beyond `--help`
- write no files
- require no hardware
- open no ports
- send no MIDI
- execute no commands
- dispatch no runtime behavior
- mutate no runtime state
- mutate no hardware state

The future command should not:

- invoke `evaluate_mock_runtime_active_bridge`
- construct `RuntimeActiveBridgeRequest`
- construct `MockMidiSender`
- call `sender.send`
- call `sender.send_many`
- emit messages
- import real MIDI libraries
- widen bridge scope
- add active CLI behavior

## 6. Proposed Help Behavior

Top-level CLI help should list:

- `mock-runtime-active-bridge-report`

The command help should make clear:

- this is a passive report preview
- it prints the mock runtime/active bridge report
- it does not invoke the bridge
- it does not construct a sender
- it does not send MIDI
- it does not open ports
- it does not require hardware

The command should not add operational flags such as:

- `--armed`
- `--port`
- `--device`
- `--send`
- `--execute`
- `--hardware`

## 7. Expected Report Output Contract

The future CLI output should be the exact output from:

- `format_mock_runtime_active_bridge_report()`

The formatted output should show:

- `RytmRandomizer Mock Runtime Active Bridge Report`
- bridge mode
- accepted candidate:
  - profile `2` / My BD Hard
- rejected cases:
  - missing arming
  - missing dry-run confirmation
  - profile `3` / My BD Classic
  - unknown key
  - unsupported source kind
  - invalid request
  - invalid sender
- parked case:
  - profile `4` / My BD Acoustic
- safety boundaries:
  - real MIDI absent
  - port opening absent
  - hardware required false
  - CLI execution wiring absent
  - runtime execution absent
  - dispatch absent
  - active behavior absent
  - hardware behavior absent

The CLI command should not hand-format separate bridge semantics. It should use
the existing formatter as the source of truth.

## 8. Proposed Future Test Scope

Future tests should verify:

- importing `rytm_randomizer.cli` prints nothing
- top-level CLI help lists `mock-runtime-active-bridge-report`
- command help exits 0
- command help is deterministic and fixture-backed
- command output exits 0
- command output is deterministic and fixture-backed
- command output matches `format_mock_runtime_active_bridge_report()`
- repeated command runs produce identical output
- output shows profile `2` accepted
- output shows profile `3` bridge rejected
- output shows profile `4` parked
- output shows no real MIDI
- output shows no ports
- output shows no hardware required
- output shows no CLI execution wiring
- output shows no runtime execution
- output shows no active behavior
- no `mido` import is introduced
- no `rtmidi` import is introduced
- passive CLI behavior remains unchanged
- V1.34 reference remains untouched
- package metadata remains untouched

## 9. Proposed Future Files

If implemented later, expected files to update:

- `rytm_randomizer/cli.py`
- `tests/test_cli.py`
- `tests/fixtures/cli_help_expected.txt`

Expected future fixture files:

- `tests/fixtures/cli_mock_runtime_active_bridge_report_help_expected.txt`
- `tests/fixtures/cli_mock_runtime_active_bridge_report_expected.txt`

The closeout script should not need a new entry if `tests/test_cli.py` remains
the test owner.

## 10. Preconditions Before Future Implementation

Before any future CLI preview implementation:

- git status must be clean
- closeout must pass
- V1.34 reference diff must be empty
- package metadata diff must be empty
- this design/spec must be reviewed and accepted
- the report implementation must remain accepted
- the CLI preview must call report formatting only
- the CLI preview must not invoke bridge behavior
- the CLI preview must not construct `MockMidiSender`
- the CLI preview must not emit messages
- the CLI preview must not add active behavior
- hardware must remain off

## 11. Non-Goals

This design/spec does not add:

- implementation
- tests
- fixtures
- closeout script changes
- CLI changes
- CLI preview command
- bridge invocation
- `RuntimeActiveBridgeRequest` construction
- `MockMidiSender` construction
- message emission
- profile `3` bridge success
- profile `4` support
- bridge scope expansion
- runtime execution
- dispatch
- command execution
- scene execution
- mutation execution
- real MIDI
- `mido`
- `rtmidi`
- port discovery
- port opening
- MIDI sending
- package metadata changes
- active behavior
- hardware behavior
- hardware validation

## 12. Safe Next Options

Safe next options after this design/spec:

- create a docs-only review/acceptance gate for this design/spec
- create the passive CLI preview implementation packet after review
- create a broader progress/timeline update
- pause at this clean checkpoint

Rejected immediate next moves:

- CLI preview implementation without review
- active CLI commands
- bridge invocation from CLI
- sender construction from CLI
- message emission from CLI
- real MIDI
- port opening
- hardware validation
- runtime execution
- bridge scope expansion

## 13. Recommendation

Recommended next task:

- create a documentation-only review/acceptance gate for this design/spec

Reason:

- CLI visibility should be reviewed before implementation
- the command must remain passive and report-only
- the report formatter should remain the single source of output truth
- the project should preserve the design, review, implementation, checkpoint,
  review sequence

## 14. Decision

The passive mock runtime/active bridge report CLI preview design/spec is
documented.

Hardware remains off.

No implementation in this slice.
