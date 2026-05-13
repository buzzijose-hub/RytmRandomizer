# V1.34 Behavior Parity Next Branch Selection After Mock Runtime Active Bridge Review

## 1. Purpose

Select the next safe branch after accepting the mock runtime/active bridge
implementation.

This is a documentation-only branch-selection checkpoint.

It adds no implementation, tests, fixtures, closeout script changes, CLI
changes, CLI execution wiring, runtime execution, dispatch, command execution,
MIDI, ports, package metadata changes, active behavior, or hardware behavior.

## 2. Current Clean Baseline

Current branch:

- `modularize-v1.34`

Current HEAD before this selection slice:

- `670b0dd Add mock runtime active bridge review`

Current phase:

- Behavior-Parity Passive/Mock Visibility Phase
- mock runtime/active bridge implemented
- mock runtime/active bridge implementation accepted
- next branch after the accepted bridge review is being selected

Hardware status:

- Analog Rytm MKII off
- Analog Four MKII off
- hardware not required

## 3. Accepted Upstream Review

Accepted review:

- `Docs/V134_BEHAVIOR_PARITY_MOCK_RUNTIME_ACTIVE_BRIDGE_REVIEW.md`

Accepted review milestone:

- `670b0dd Add mock runtime active bridge review`

Accepted implementation checkpoint:

- `Docs/V134_BEHAVIOR_PARITY_MOCK_RUNTIME_ACTIVE_BRIDGE_CHECKPOINT.md`

Accepted implementation milestone:

- `b35cf9e Add mock runtime active bridge`

The accepted review confirms:

- the mock runtime/active bridge is accepted
- profile `2` / My BD Hard is the only bridge success path
- profile `3` / My BD Classic remains bridge rejected
- profile `4` / My BD Acoustic remains parked
- bridge behavior remains mock-only and test-only
- `MockMidiSender` remains the only sender boundary
- closeout includes `Mock Runtime Active Bridge`
- real MIDI, ports, CLI execution wiring, runtime execution, active behavior,
  and hardware behavior remain absent

## 4. Candidate Branch Options

Safe branch options after the accepted bridge review:

- pause at the clean bridge checkpoint
- create a docs-only next-branch selection after the bridge review
- create a read-only bridge report design/spec
- create a read-only bridge report implementation packet after a separate plan
- create a broader progress/timeline update
- return to passive/project documentation

Rejected for the next branch:

- real MIDI
- port opening
- hardware validation
- active CLI commands
- CLI execution wiring
- runtime execution
- dispatch
- command execution
- scene execution
- mutation execution
- profile `3` bridge success
- profile `4` support
- Analog Four support
- Pads 5-12 support
- SysEx
- GUI/capture

## 5. Selected Next Branch

Selected next branch:

- docs-only read-only mock runtime/active bridge report design/spec

This next branch should remain documentation-only.

It should design a future passive report that summarizes current bridge
behavior without invoking the bridge, sending messages, wiring CLI execution,
or widening scope.

It should not implement that report.

## 6. Expected Future Design/Spec Scope

The future design/spec should cover:

- purpose of a read-only bridge report
- current bridge scope
- current bridge success case:
  - profile `2` / My BD Hard
  - armed and dry-run confirmed required
  - `MockMidiSender` only
  - no real MIDI
  - no hardware
- current bridge rejection cases:
  - missing arming
  - missing dry-run confirmation
  - profile `3`
  - profile `4`
  - unknown key
  - unsupported source kind
  - invalid request/sender
- planned report data shape
- planned formatter behavior
- planned tests before implementation
- closeout expectations if implemented later
- explicit non-goals

The future design/spec should preserve:

- profile `2` as the only bridge success path
- profile `3` as bridge rejected
- profile `4` as parked
- no bridge invocation from a report
- no `MockMidiSender` construction from report code unless explicitly justified
  and separately reviewed
- no CLI execution wiring
- no runtime execution
- no MIDI
- no ports
- no hardware

## 7. Expected Future Design/Spec Non-Goals

The future design/spec should explicitly reject:

- implementation in the design/spec slice
- tests in the design/spec slice
- fixtures in the design/spec slice
- closeout script changes in the design/spec slice
- CLI changes in the design/spec slice
- bridge report CLI command in the design/spec slice
- bridge scope expansion
- profile `3` bridge success
- profile `4` support
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

## 8. Rationale

This branch is the best next move because:

- the bridge is now implemented and accepted
- the next useful step is visibility, not broader behavior
- a read-only report can summarize what the bridge accepts, rejects, and parks
- a report design/spec keeps the project deliberate before adding another
  report module
- this avoids drifting from mock-only bridge behavior into execution

## 9. Parked Scope

Still parked:

- active CLI commands
- CLI execution wiring
- runtime execution
- dispatch
- command execution
- scene execution
- mutation execution
- bridge report implementation
- bridge report CLI preview
- profile `3` bridge success
- profile `4` support
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
- profile `3` bridge success
- profile `4` support
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

- docs-only read-only mock runtime/active bridge report design/spec

The next recommended task is to create that documentation-only design/spec.

Hardware remains off.

No implementation in this slice.

## 12. Follow-Up Design Spec

The selected next branch is now represented by:

- `Docs/V134_BEHAVIOR_PARITY_MOCK_RUNTIME_ACTIVE_BRIDGE_REPORT_DESIGN_SPEC.md`

That design/spec defines a future read-only mock runtime/active bridge report.

The design/spec preserves the accepted bridge boundary:

- profile `2` / My BD Hard is the only accepted bridge candidate
- profile `3` / My BD Classic remains bridge rejected
- profile `4` / My BD Acoustic remains parked
- arming and dry-run confirmation remain required
- `MockMidiSender` remains the mock-only sender boundary

The design/spec requires the future report to remain static, read-only, and
metadata-only. It must not invoke the bridge, construct a `MockMidiSender`,
emit messages, open ports, import real MIDI libraries, wire CLI execution, or
widen bridge scope.

Recommended follow-up:

- create a documentation-only review/acceptance gate for the report design/spec

This follow-up adds no implementation, tests, fixtures, closeout script changes,
CLI changes, CLI execution wiring, runtime execution, dispatch, command
execution, mutation execution, MIDI, ports, package metadata changes, active
behavior, or hardware behavior.
