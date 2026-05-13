# V1.34 Behavior Parity Runtime Plan Report CLI Preview Design Review

## 1. Purpose

Review and accept the runtime plan report CLI preview design.

This is a documentation-only review checkpoint.

It adds no implementation, tests, fixtures, closeout script changes, CLI
changes, CLI execution wiring, runtime execution, dispatch, command execution,
MIDI, ports, package metadata changes, active behavior, or hardware behavior.

## 2. Current Clean Baseline

Current branch:

- `modularize-v1.34`

Current HEAD before this review slice:

- `a6972fc Add runtime plan report CLI preview design`

Current phase:

- Passive/Mock Foundation Phase
- behavior-parity implementation phase
- read-only runtime plan report implemented and closeout-covered
- runtime plan report CLI preview design documented
- runtime plan report CLI preview design now being reviewed

Hardware status:

- Analog Rytm MKII off
- Analog Four MKII off
- hardware not required

## 3. Review Decision

Accepted design:

- `Docs/V134_BEHAVIOR_PARITY_RUNTIME_PLAN_REPORT_CLI_PREVIEW_DESIGN.md`

Accepted design milestone:

- `a6972fc Add runtime plan report CLI preview design`

The design is accepted as the current planning gate for a future passive
runtime plan report CLI preview.

The design remains documentation-only.

The design does not authorize implementation by itself.

The design does not authorize CLI changes, tests, fixtures, runtime execution,
dispatch, command execution, real MIDI, ports, active behavior, or hardware
validation.

## 4. Accepted Future CLI Shape

Accepted future command name:

- `runtime-plan-report`

Accepted future command shape:

- `python -m rytm_randomizer.cli runtime-plan-report`
- `python -m rytm_randomizer.cli runtime-plan-report --help`

Accepted future command behavior:

- print only existing `format_runtime_plan_report()` output
- exit `0`
- remain passive/read-only
- write no files
- require no hardware
- open no ports
- send no MIDI
- dispatch no commands
- execute no commands
- mutate no runtime state
- mutate no hardware state

## 5. Accepted Future Implementation Boundary

Any later implementation must stay limited to passive CLI visibility.

Allowed future implementation files, only after a separate approved
implementation plan:

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

## 6. Accepted Future Test Expectations

Future tests, only after a separate approved implementation plan, should prove:

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

## 7. Confirmed Absent Behavior

Still absent:

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

## 8. Confirmed Safety Invariants

This review confirms:

- V1.34 reference remains protected
- package metadata remains protected
- passive CLI remains read-only
- runtime plan report remains read-only
- runtime plan report remains blocked by default
- active/runtime report alignment remains closeout-covered
- no real MIDI libraries are required
- no ports are opened
- no hardware is required

## 9. Preconditions Before Future Implementation Plan

Before a future implementation plan:

- Git status must be clean
- closeout must pass
- V1.34 reference diff must be empty
- package metadata diff must be empty
- this design review must remain accepted
- passive CLI behavior must remain read-only
- runtime plan report behavior must remain read-only
- no real MIDI libraries may be added
- no ports may open
- no hardware may be required

## 10. Safe Next Options

Safe next options after this review:

- docs-only implementation plan for the runtime plan report CLI preview
- docs-only next-branch selection after this design review
- pause at this clean design review checkpoint
- select another tiny mock-only safety gap

## 11. Recommendation

Recommended next task:

- create a docs-only implementation plan for the runtime plan report CLI
  preview

The implementation plan should still add no code.

Do not implement the CLI preview yet.

Do not add tests yet.

Do not add real MIDI.

Do not open ports.

Do not add active CLI commands.

Do not turn on hardware.

## 12. Decision

`Docs/V134_BEHAVIOR_PARITY_RUNTIME_PLAN_REPORT_CLI_PREVIEW_DESIGN.md` is
accepted as the current planning gate for a future passive runtime plan report
CLI preview.

Hardware remains off.

No implementation in this slice.

## 13. Follow-Up Status

The implementation plan for this accepted design is now documented.

Implementation plan:

- `Docs/V134_BEHAVIOR_PARITY_RUNTIME_PLAN_REPORT_CLI_PREVIEW_IMPLEMENTATION_PLAN.md`

Planned future command:

- `python -m rytm_randomizer.cli runtime-plan-report`

Next recommended task:

- docs-only review/acceptance gate for the implementation plan

The implementation plan authorizes no implementation, tests, fixtures, CLI
changes, CLI execution wiring, runtime execution, dispatch, MIDI, ports,
active behavior, or hardware behavior.
