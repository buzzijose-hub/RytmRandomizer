# V1.34 Behavior Parity Next Branch Selection After Passive/Runtime Visibility Phase Review

## 1. Purpose

Select the next safe branch after accepting the passive/runtime visibility
phase review.

This is a documentation-only branch-selection checkpoint.

It adds no implementation, tests, fixtures, closeout script changes, CLI
changes, CLI execution wiring, runtime execution, dispatch, command execution,
MIDI, ports, package metadata changes, active behavior, or hardware behavior.

## 2. Current Clean Baseline

Current branch:

- `modularize-v1.34`

Current HEAD before this selection slice:

- `61d20cb Add passive runtime visibility phase review`

Current phase:

- Behavior-Parity Passive/Mock Visibility Phase
- passive/runtime visibility phase accepted
- operator-facing read-only visibility surfaces accepted
- next branch after the accepted phase review is being selected

Hardware status:

- Analog Rytm MKII off
- Analog Four MKII off
- hardware not required

## 3. Accepted Upstream Phase Review

Accepted phase review:

- `Docs/V134_BEHAVIOR_PARITY_PASSIVE_RUNTIME_VISIBILITY_PHASE_REVIEW.md`

Accepted phase-review milestone:

- `61d20cb Add passive runtime visibility phase review`

The accepted phase review confirms:

- passive CLI visibility is accepted
- runtime plan report CLI visibility is accepted
- active-boundary report visibility is accepted
- behavior-parity report visibility is accepted
- mock mapper report visibility is accepted
- profile `2` / My BD Hard is supported and active-boundary accepted
- profile `3` / My BD Classic is runtime-plan supported and
  active-boundary unsupported
- profile `4` / My BD Acoustic remains parked
- runtime execution remains absent
- real MIDI, ports, active behavior, and hardware behavior remain absent

## 4. Candidate Branch Options

Safe branch options after the accepted phase review:

- pause at the clean phase checkpoint
- create a user-facing progress/timeline summary for handoff
- choose another tiny mock-only safety gap
- create a docs-only first narrow runtime/active-facing implementation plan
- return to passive/project documentation

Rejected for the next branch:

- direct active implementation
- direct MIDI implementation
- direct port opening
- hardware validation
- runtime execution
- CLI execution wiring
- command execution
- scene execution
- mutation execution
- profile `4` active-boundary support without a separate plan
- fourth runtime-adjacent candidate without a separate plan

## 5. Selected Next Branch

Selected next branch:

- docs-only first narrow runtime/active-facing implementation plan

This next branch should remain documentation-only.

It should create a plan for the first narrow implementation packet that could
move beyond reporting while staying mock-only, passive-safe, and
hardware-off.

It should not implement that packet.

## 6. Expected Future Plan Scope

The future implementation plan should cover:

- exact goal and non-goals
- exact candidate scope
- likely first candidate:
  - profile `2` / My BD Hard
  - mock-only
  - active-boundary accepted
  - blocked by default
  - no real MIDI
  - no hardware
- files that may be touched later
- tests that must be written first
- closeout expectations
- protected files and package metadata checks
- explicit arming/failure behavior if relevant
- exact ways passive CLI commands must remain read-only

The future plan should preserve:

- profile `3` as runtime-plan supported but active-boundary unsupported
- profile `4` as parked
- unknown/unsupported inputs as safe failures
- no active CLI execution
- no MIDI
- no ports
- no hardware

## 7. Expected Future Plan Non-Goals

The future plan should explicitly reject:

- implementation in the planning slice
- tests in the planning slice
- fixtures in the planning slice
- closeout script changes in the planning slice
- CLI execution wiring
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
- profile `4` implementation
- Analog Four support
- Pads 5-12 support
- SysEx
- GUI/capture
- active behavior
- hardware behavior
- hardware validation

## 8. Rationale

This branch is the best next move because:

- the passive/runtime visibility phase is accepted
- the project now has enough read-only visibility to plan the first narrow
  implementation packet responsibly
- a plan creates the bridge from reporting to a small future mock-only packet
  without crossing into execution
- profile `2` already has the safest accepted active-boundary status
- profile `3` and profile `4` preserve useful unsupported/parked coverage
- the project can move closer to active-facing work without adding active
  behavior yet

## 9. Parked Scope

Still parked:

- active CLI commands
- selected pad switching execution
- selected pad target state mutation
- selected pad anchor return execution
- current anchor return execution
- isolated pad mutation execution
- runtime mutation
- profile `4` mock mapper support
- profile `4` runtime expansion
- profile `4` active-boundary support
- fourth runtime-adjacent candidate
- real MIDI boundary implementation
- hardware validation

## 10. Confirmed Boundaries

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
- mutation execution
- real MIDI
- `mido`
- `rtmidi`
- port discovery
- port opening
- MIDI sending
- package metadata changes
- active CLI execution
- `execute-command`
- `send-command`
- `hardware-test`
- profile `4` active-boundary support
- fourth runtime-adjacent candidate
- Analog Four support
- Pads 5-12 support
- SysEx
- GUI/capture
- active behavior
- hardware behavior

`rytm_hybrid_randomizer_v134.py` remains untouched.

Package metadata remains untouched.

Hardware remains off.

## 11. Decision

The next branch is selected:

- docs-only first narrow runtime/active-facing implementation plan

The next recommended task is to create that documentation-only plan.

Hardware remains off.

No implementation in this slice.

## Follow-Up Implementation Plan

The selected next branch is now represented by:

- `Docs/V134_BEHAVIOR_PARITY_FIRST_NARROW_RUNTIME_ACTIVE_IMPLEMENTATION_PLAN.md`

That plan defines a future mock-only runtime/active bridge packet for profile
`2` / My BD Hard.

It requires a documentation-only review/acceptance gate before implementation.

It adds no implementation, tests, fixtures, closeout script changes, CLI
changes, CLI execution wiring, runtime execution, dispatch, command execution,
mutation execution, MIDI, ports, package metadata changes, active behavior, or
hardware behavior.
