# V1.34 Behavior Parity Next Branch Selection After Active/Runtime Alignment Progress Report Review

## 1. Purpose

Select the next safe branch after accepting the behavior-parity progress report
after the active/runtime report alignment tests.

This is a documentation-only branch-selection checkpoint.

It adds no implementation, tests, fixtures, closeout script changes, CLI
changes, CLI execution wiring, runtime execution, dispatch, command execution,
MIDI, ports, package metadata changes, active behavior, or hardware behavior.

## 2. Current Clean Baseline

Current branch:

- `modularize-v1.34`

Current HEAD before this selection slice:

- `2a950db Add progress report review after active runtime alignment tests`

Current phase:

- Passive/Mock Foundation Phase
- behavior-parity implementation phase
- active/runtime report alignment tests closeout-covered
- behavior-parity progress report accepted
- next branch after the accepted progress report is being selected

Hardware status:

- Analog Rytm MKII off
- Analog Four MKII off
- hardware not required

## 3. Accepted Upstream Review

Accepted review:

- `Docs/V134_BEHAVIOR_PARITY_PROGRESS_REPORT_AFTER_ACTIVE_RUNTIME_REPORT_ALIGNMENT_TESTS_REVIEW.md`

Accepted progress report:

- `Docs/V134_BEHAVIOR_PARITY_PROGRESS_REPORT_AFTER_ACTIVE_RUNTIME_REPORT_ALIGNMENT_TESTS.md`

Accepted review milestone:

- `2a950db Add progress report review after active runtime alignment tests`

Accepted report milestone:

- `f6e4f06 Add progress report after active runtime alignment tests`

## 4. Current Accepted Safety State

The accepted progress report review confirms:

- profile `2` remains the aligned/accepted mock-only active candidate
- profile `3` remains runtime-plan supported but active-boundary unsupported
- profile `4` remains parked/unsupported
- runtime plan report remains read-only
- active-boundary report remains read-only
- active/runtime report alignment remains closeout-covered
- V1.34 reference remains protected
- package metadata remains protected
- hardware remains off

## 5. Candidate Branch Options

Safe branch options after this accepted progress report review:

- pause at the clean checkpoint
- create a docs-only runtime plan report CLI preview design
- select another tiny mock-only safety gap
- create a roadmap/timeline update for the next behavior-parity phase
- return to passive/project documentation

## 6. Selected Next Branch

Selected next branch:

- docs-only runtime plan report CLI preview design

This next branch should remain documentation-only.

It should design how a future passive CLI command could display the existing
read-only runtime plan report.

It should not add the command yet.

It should not change `rytm_randomizer/cli.py`.

It should not add tests yet.

It should not add CLI execution wiring, runtime execution, dispatch, MIDI,
ports, active behavior, or hardware behavior.

## 7. Rationale

This branch is the best next move because:

- the runtime plan report already exists
- the report is read-only and blocked by default
- the mock mapper report already has a passive CLI visibility pattern
- a design step can define the future CLI preview without implementing it
- CLI visibility is useful, but the project should preserve the design/review
  gate before touching CLI code
- this keeps the project moving toward useful operator visibility without
  crossing into execution

## 8. Expected Future Design Scope

The future design document should cover:

- possible future command name, likely `runtime-plan-report`
- expected command shape:
  - `python -m rytm_randomizer.cli runtime-plan-report`
  - `python -m rytm_randomizer.cli runtime-plan-report --help`
- future behavior:
  - print the existing formatted runtime plan report only
  - exit `0`
  - require no hardware
  - open no ports
  - send no MIDI
  - dispatch no commands
  - execute no commands
  - mutate no runtime state
- fixture-backed deterministic output expectations
- passive CLI safety regression expectations
- protected V1.34 and package metadata checks

## 9. Expected Future Non-Goals

The future design should explicitly reject:

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

## 10. Parked Scope

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

- docs-only runtime plan report CLI preview design

The next recommended task is to create that design document.

Hardware remains off.

No implementation in this slice.

## 13. Follow-Up Status

The selected next branch has been carried out as a documentation-only design.

Design document:

- `Docs/V134_BEHAVIOR_PARITY_RUNTIME_PLAN_REPORT_CLI_PREVIEW_DESIGN.md`

Designed future command:

- `python -m rytm_randomizer.cli runtime-plan-report`

Next recommended task:

- docs-only review/acceptance gate for the design

The follow-up design authorizes no implementation, tests, fixtures, CLI
changes, CLI execution wiring, runtime execution, dispatch, MIDI, ports,
active behavior, or hardware behavior.
