# V1.34 Behavior Parity Next Branch Selection After Runtime Plan Report Review

## 1. Purpose

Select the next safe branch after accepting the read-only runtime plan report
checkpoint review.

Keep this as a documentation-only decision slice.

Do not implement code, tests, CLI commands, runtime execution, dispatch, MIDI,
ports, active behavior, or hardware behavior in this slice.

## 2. Current Clean Baseline

Current branch:

- `modularize-v1.34`

Current HEAD before this selection slice:

- `a2c6866 Add read-only runtime plan report checkpoint review`

Current phase:

- Passive/Mock Foundation Phase
- behavior-parity implementation phase
- mock-only runtime plan scaffold implemented and accepted
- metadata-only runtime plan preview metadata implemented and accepted
- read-only runtime plan report implemented and accepted
- next branch now being selected

Hardware status:

- Analog Rytm MKII off
- Analog Four MKII off
- hardware not required

## 3. Accepted Upstream Checkpoint

Accepted checkpoint review:

- `Docs/V134_BEHAVIOR_PARITY_READ_ONLY_RUNTIME_PLAN_REPORT_CHECKPOINT_REVIEW.md`

Accepted checkpoint:

- `Docs/V134_BEHAVIOR_PARITY_READ_ONLY_RUNTIME_PLAN_REPORT_CHECKPOINT.md`

Accepted checkpoint milestone:

- `e86200c Update checkpoint after read-only runtime plan report`

Accepted implementation milestone:

- `6e80cee Add read-only runtime plan report`

## 4. Current Safe Foundation

The project now has:

- passive CLI report/list/search/inspect/preview coverage
- mock MIDI scaffold
- mock message mapper and report
- active boundary reports
- real MIDI import/passive safety checks
- mock-only runtime plan scaffold
- metadata-only runtime plan preview metadata
- read-only runtime plan report
- closeout coverage for Runtime Plan
- closeout coverage for Runtime Plan Report

The runtime plan report can now summarize blocked future runtime intent without
executing anything.

## 5. Candidate Next Branches

Safe candidate branches:

- pause at the accepted runtime plan report checkpoint
- broader behavior-parity progress report
- docs-only runtime plan report CLI preview design
- docs-only first mock-only active candidate design

Rejected for the next branch:

- direct active implementation
- direct MIDI implementation
- direct port opening
- hardware validation
- runtime plan report CLI implementation without design/review

## 6. Selected Next Branch

Selected next branch:

- docs-only first mock-only active candidate design

This branch should define the first candidate for a future mock-only active
test path without implementing the candidate.

It should stay at design altitude.

It should not add code.

It should not add tests.

It should not add CLI wiring.

It should not add execution.

It should not add MIDI, ports, or hardware behavior.

## 7. Rationale

This is the best next branch because:

- the passive and mock foundations are now strong enough to discuss a first
  active-facing candidate safely
- the runtime plan report can summarize blocked runtime intent
- closeout already covers the Runtime Plan and Runtime Plan Report layers
- moving to candidate design gets closer to the fun work without crossing the
  execution boundary
- runtime plan report CLI preview can remain parked until visibility from
  PowerShell becomes necessary

## 8. Expected Design Scope For The Next Slice

The next docs-only design should define:

- candidate purpose
- candidate source metadata
- candidate target scope
- mock-only behavior
- expected blocked runtime plan status
- expected report visibility
- arming assumptions, as future concept only
- failure conditions
- stop conditions
- forbidden scope
- required tests before any implementation

Likely candidate direction:

- group profile `2` / My BD Hard
- Pad 1 only
- mock-only
- blocked by default
- no real MIDI
- no ports
- no hardware

The next design must not select any real hardware validation action.

## 9. Parked Scope

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

## 10. Confirmed Absent Behavior

This selection adds no:

- code changes
- tests
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
- Analog Four support
- Pads 5-12 support
- SysEx
- GUI/capture
- package metadata changes
- active behavior
- hardware behavior

`rytm_hybrid_randomizer_v134.py` remains untouched.

Hardware remains off.

## 11. Decision

The next branch is selected:

- docs-only first mock-only active candidate design

The next recommended task is to create that design document.

Hardware remains off.

No implementation in this slice.
