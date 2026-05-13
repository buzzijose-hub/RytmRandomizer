# V1.34 Behavior Parity Next Branch Selection After Runtime Plan CLI Roadmap Review

## 1. Purpose

Select the next safe branch after accepting the behavior-parity
roadmap/timeline update after the passive runtime plan report CLI preview.

This is a documentation-only branch-selection checkpoint.

It adds no implementation, tests, fixtures, closeout script changes, CLI
changes, CLI execution wiring, runtime execution, dispatch, command execution,
MIDI, ports, package metadata changes, active behavior, or hardware behavior.

## 2. Current Clean Baseline

Current branch:

- `modularize-v1.34`

Current HEAD before this selection slice:

- `37626ec Add roadmap timeline review after runtime plan CLI preview`

Current phase:

- Behavior-Parity Passive/Mock Visibility Phase
- runtime plan report CLI preview implemented and accepted
- roadmap/timeline update after the runtime plan report CLI preview accepted
- next branch after the accepted roadmap/timeline update is being selected

Hardware status:

- Analog Rytm MKII off
- Analog Four MKII off
- hardware not required

## 3. Accepted Upstream Review

Accepted review:

- `Docs/V134_BEHAVIOR_PARITY_ROADMAP_TIMELINE_UPDATE_AFTER_RUNTIME_PLAN_REPORT_CLI_PREVIEW_REVIEW.md`

Accepted roadmap/timeline update:

- `Docs/V134_BEHAVIOR_PARITY_ROADMAP_TIMELINE_UPDATE_AFTER_RUNTIME_PLAN_REPORT_CLI_PREVIEW.md`

Accepted review milestone:

- `37626ec Add roadmap timeline review after runtime plan CLI preview`

Accepted roadmap/timeline milestone:

- `ecb7331 Add roadmap timeline after runtime plan CLI preview`

## 4. Current Accepted Safety State

The accepted roadmap/timeline review confirms:

- current phase is Behavior-Parity Passive/Mock Visibility Phase
- runtime plan report CLI preview is implemented and accepted
- passive CLI visibility remains read-only
- group profiles `2` and `3` remain supported runtime planning inputs
- group profile `4` remains parked
- real MIDI / hardware validation remains `0%`
- V1.34 reference remains protected
- package metadata remains protected
- hardware remains off

## 5. Candidate Branch Options

Safe branch options after this accepted roadmap/timeline review:

- pause at the clean checkpoint
- create a passive/runtime visibility phase review
- select another tiny mock-only safety gap
- create a user-facing progress/timeline summary for session handoff
- return to passive/project documentation

Rejected for the next branch:

- direct active implementation
- direct MIDI implementation
- direct port opening
- hardware validation
- runtime execution
- CLI execution wiring
- profile `4` active-boundary support
- fourth runtime-adjacent candidate without a separate plan

## 6. Selected Next Branch

Selected next branch:

- docs-only passive/runtime visibility phase review

This next branch should remain documentation-only.

It should summarize and accept the current visibility phase as a coherent
project surface before choosing another implementation slice.

It should cover:

- passive CLI visibility
- runtime plan report CLI visibility
- active-boundary report visibility
- behavior-parity report visibility
- mock mapper report visibility
- accepted profile semantics
- parked scope
- remaining absent execution/hardware behavior
- safe next branch options after the phase review

It should not add code.

It should not add tests.

It should not change CLI behavior.

It should not add runtime execution, dispatch, MIDI, ports, active behavior,
or hardware behavior.

## 7. Rationale

This branch is the best next move because:

- the roadmap/timeline update is now accepted
- the project has several read-only CLI visibility surfaces
- the current visibility phase should be accepted as a coherent phase before
  the next implementation slice
- a phase review helps prevent the project from drifting into execution by
  accident
- it gives us a cleaner launch point for either another tiny mock-only safety
  gap or a future active-facing implementation plan

## 8. Expected Future Phase Review Scope

The future passive/runtime visibility phase review should cover:

- current clean baseline
- current phase name
- accepted passive CLI visibility commands
- accepted runtime plan CLI visibility
- accepted active-boundary/report visibility
- accepted behavior-parity report visibility
- accepted mock/report visibility
- current closeout coverage at a high level
- accepted profile semantics:
  - profile `2` supported and active-boundary accepted
  - profile `3` runtime-plan supported and active-boundary unsupported
  - profile `4` parked
- remaining parked scope
- remaining absent behavior
- safe next options after the phase review

## 9. Expected Future Non-Goals

The future phase review should explicitly reject:

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

## 10. Parked Scope

Still parked:

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

- docs-only passive/runtime visibility phase review

The next recommended task is to create that documentation-only phase review.

Hardware remains off.

No implementation in this slice.
