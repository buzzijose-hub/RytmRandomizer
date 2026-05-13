# V1.34 Behavior Parity Runtime Plan Report CLI Preview Design

## 1. Purpose

Design a future passive CLI preview for the existing read-only runtime plan
report.

This is a documentation-only design.

It does not implement the CLI command.

It does not add tests, fixtures, closeout script changes, CLI changes, CLI
execution wiring, runtime execution, dispatch, command execution, MIDI, ports,
package metadata changes, active behavior, or hardware behavior.

## 2. Current Clean Baseline

Current branch:

- `modularize-v1.34`

Current HEAD before this design slice:

- `ebcedca Add next branch selection after progress report review`

Current phase:

- Passive/Mock Foundation Phase
- behavior-parity implementation phase
- read-only runtime plan report implemented and closeout-covered
- active/runtime report alignment tests closeout-covered
- behavior-parity progress report accepted
- runtime plan report CLI preview design now being documented

Hardware status:

- Analog Rytm MKII off
- Analog Four MKII off
- hardware not required

## 3. Accepted Upstream Selection

Accepted next-branch selection:

- `Docs/V134_BEHAVIOR_PARITY_NEXT_BRANCH_SELECTION_AFTER_ACTIVE_RUNTIME_ALIGNMENT_PROGRESS_REPORT_REVIEW.md`

Accepted upstream progress report review:

- `Docs/V134_BEHAVIOR_PARITY_PROGRESS_REPORT_AFTER_ACTIVE_RUNTIME_REPORT_ALIGNMENT_TESTS_REVIEW.md`

Accepted upstream milestone:

- `ebcedca Add next branch selection after progress report review`

Selected branch:

- docs-only runtime plan report CLI preview design

## 4. Existing Runtime Plan Report Baseline

Existing module:

- `rytm_randomizer/runtime_plan_report.py`

Existing helpers:

- `build_runtime_plan_report()`
- `summarize_runtime_plan_report()`
- `format_runtime_plan_report(report=None)`

Existing closeout label:

- `=== Test: Runtime Plan Report ===`

The runtime plan report is already:

- read-only
- in-memory
- deterministic
- mock-only
- metadata-only
- blocked by default
- side-effect free on import
- disconnected from CLI execution
- disconnected from MIDI
- disconnected from ports
- disconnected from hardware

## 5. Future CLI Preview Goal

The future CLI preview should expose the existing formatted runtime plan report
from PowerShell without expanding behavior.

It should make the current runtime planning boundary visible to the operator.

It should not add an execution path.

It should not create or validate runtime actions.

It should not open ports.

It should not send MIDI.

It should not require hardware.

## 6. Proposed Future Command Shape

Possible future command:

- `python -m rytm_randomizer.cli runtime-plan-report`

Possible future help command:

- `python -m rytm_randomizer.cli runtime-plan-report --help`

The command name should be:

- `runtime-plan-report`

Reason:

- matches existing report command naming
- clearly says this is runtime-plan visibility, not execution
- avoids active words like `execute`, `send`, or `hardware-test`

## 7. Proposed Future Behavior

If implemented later, `runtime-plan-report` should:

- call `format_runtime_plan_report()` only
- print the existing formatted runtime plan report
- exit `0`
- write no files
- require no hardware
- open no MIDI ports
- send no MIDI
- dispatch no commands
- execute no commands
- mutate no runtime state
- mutate no hardware state
- add no options beyond `--help`

It must not call runtime execution code because no runtime execution exists.

It must not call real MIDI adapters because no real MIDI path is authorized.

## 8. Proposed Future Help Text

The future command help should state:

- passive/read-only
- prints the read-only runtime plan report
- no MIDI sending
- no port opening
- no runtime execution
- no command execution
- no dispatch
- no hardware mutation
- no hardware required

The future top-level CLI help should list:

- `runtime-plan-report`

The future top-level usage string should include:

- `runtime-plan-report`

## 9. Expected Future Output

The future command output should be deterministic and fixture-backed.

It should show the existing runtime plan report content, including:

- title
- mock-only mode
- metadata-only mode
- blocked-by-default mode
- supported planning inputs:
  - group profile `2`
  - group profile `3`
- parked planning inputs:
  - group profile `4`
- unsupported planning inputs:
  - unknown group profile key
  - unsupported scene source kind
- safety status:
  - `would_execute: False`
  - `mock_only: True`
  - `sends_real_midi: False`
  - `ports_allowed: False`
  - `hardware_required: False`
  - `runtime_execution: absent`
  - `cli_execution_wiring: absent`
  - `dispatch: absent`

## 10. Proposed Future Test Scope

Future tests, only after a separate accepted implementation plan, should verify:

- importing `rytm_randomizer.cli` prints nothing
- top-level help lists `runtime-plan-report`
- `runtime-plan-report --help` exits `0`
- `runtime-plan-report --help` matches a fixture
- `runtime-plan-report` exits `0`
- `runtime-plan-report` output matches a fixture
- output is deterministic across repeated runs
- output shows supported profiles `2` and `3`
- output shows profile `4` parked
- output shows unknown/unsupported safe-failure categories
- output shows mock-only/read-only safety boundaries
- no real MIDI library is imported
- no ports are opened
- no MIDI is sent
- no CLI active behavior is introduced
- V1.34 reference remains untouched
- package metadata remains untouched

Possible future fixtures:

- `tests/fixtures/cli_runtime_plan_report_help_expected.txt`
- `tests/fixtures/cli_runtime_plan_report_expected.txt`

If `tests/test_cli.py` remains the right home for CLI tests, no new closeout
label should be needed.

## 11. Future Implementation Boundary

Any future implementation must be limited to passive CLI visibility.

Allowed future files, only after separate approval:

- `rytm_randomizer/cli.py`
- `tests/test_cli.py`
- `tests/fixtures/cli_help_expected.txt`
- `tests/fixtures/cli_runtime_plan_report_help_expected.txt`
- `tests/fixtures/cli_runtime_plan_report_expected.txt`

Do not update `Scripts/closeout_check.ps1` unless a new test file is created.

Do not edit:

- `rytm_hybrid_randomizer_v134.py`
- runtime execution/dispatch logic
- active CLI commands
- package metadata files
- MIDI adapter code
- hardware-facing code

## 12. Relationship To Existing CLI Reports

The future command should follow the passive CLI report pattern already used
for:

- `report`
- `mock-mapper-report`
- `active-boundary-report`
- `anchor-profile-report`
- `behavior-parity-report`

It should be a visibility command only.

It should not make runtime planning more capable.

It should not wire the CLI to execution.

It should not create active behavior.

## 13. Explicit Non-Goals

This design does not authorize:

- implementation
- tests
- fixtures
- closeout script changes
- CLI changes
- active CLI commands
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
- runtime mutation
- profile `4` active-boundary support
- fourth runtime-adjacent candidate
- Analog Four support
- Pads 5-12 support
- SysEx
- GUI/capture
- package metadata changes
- hardware behavior

## 14. Parked Scope

Still parked:

- runtime plan report CLI preview implementation
- runtime plan report CLI fixtures/tests
- active CLI commands
- selected pad switching execution
- selected pad target state mutation
- selected pad anchor return execution
- current anchor return execution
- isolated pad mutation execution
- runtime mutation
- profile `4` mock mapper support
- profile `4` active-boundary support
- fourth runtime-adjacent candidate
- real MIDI
- hardware validation

## 15. Required Future Review Before Implementation

Before implementing this CLI preview:

- this design must be reviewed and accepted
- Git status must be clean
- closeout must pass
- V1.34 reference diff must be empty
- package metadata diff must be empty
- passive CLI must remain read-only
- runtime plan report must remain read-only
- no real MIDI libraries may be added
- no ports may open
- no hardware may be required

## 16. Safe Next Options

Safe next options:

- docs-only review/acceptance gate for this design
- pause at this clean design checkpoint
- create a docs-only implementation plan for the CLI preview after review
- select another tiny mock-only safety gap

## 17. Recommendation

Recommended next task:

- docs-only review/acceptance gate for this design

Do not implement the CLI preview yet.

Do not add tests yet.

Do not add real MIDI.

Do not open ports.

Do not add active CLI commands.

Do not turn on hardware.

## 18. Decision

The runtime plan report CLI preview design is documented.

The design does not authorize implementation by itself.

Hardware remains off.

No implementation in this slice.

## 19. Review Status

This design has been reviewed and accepted as the current planning gate for a
future passive runtime plan report CLI preview.

Review document:

- `Docs/V134_BEHAVIOR_PARITY_RUNTIME_PLAN_REPORT_CLI_PREVIEW_DESIGN_REVIEW.md`

Accepted design milestone:

- `a6972fc Add runtime plan report CLI preview design`

Next recommended task:

- docs-only implementation plan for the runtime plan report CLI preview

The review authorizes no implementation, tests, fixtures, CLI changes, CLI
execution wiring, runtime execution, dispatch, MIDI, ports, active behavior, or
hardware behavior.
