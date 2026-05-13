# V1.34 Behavior Parity Next Branch Selection After Mock Runtime Active Bridge Report Review

## 1. Purpose

Select the next safe branch after accepting the read-only mock runtime/active
bridge report implementation.

This is a documentation-only branch-selection checkpoint.

It adds no implementation, tests, fixtures, closeout script changes, CLI
changes, CLI execution wiring, runtime execution, dispatch, command execution,
MIDI, ports, package metadata changes, active behavior, or hardware behavior.

## 2. Current Clean Baseline

Current branch:

- `modularize-v1.34`

Current HEAD before this selection slice:

- `7bd532c Add mock runtime active bridge report review`

Current phase:

- Behavior-Parity Passive/Mock Visibility Phase
- mock runtime/active bridge implemented and accepted
- mock runtime/active bridge report implemented
- mock runtime/active bridge report implementation accepted
- next branch after the accepted bridge report review is being selected

Hardware status:

- Analog Rytm MKII off
- Analog Four MKII off
- hardware not required

## 3. Accepted Upstream Review

Accepted review:

- `Docs/V134_BEHAVIOR_PARITY_MOCK_RUNTIME_ACTIVE_BRIDGE_REPORT_REVIEW.md`

Accepted review milestone:

- `7bd532c Add mock runtime active bridge report review`

Accepted implementation checkpoint:

- `Docs/V134_BEHAVIOR_PARITY_MOCK_RUNTIME_ACTIVE_BRIDGE_REPORT_CHECKPOINT.md`

Accepted implementation milestone:

- `75f731c Add mock runtime active bridge report`

The accepted review confirms:

- the read-only bridge report implementation is accepted
- the report is the current passive bridge visibility layer
- the report remains read-only, mock-only, metadata-only, and in-memory
- profile `2` / My BD Hard is the only accepted bridge candidate in the report
- profile `3` / My BD Classic remains bridge rejected in the report
- profile `4` / My BD Acoustic remains parked in the report
- the report does not invoke the bridge
- the report does not construct `MockMidiSender`
- the report emits no messages
- closeout includes `Mock Runtime Active Bridge Report`
- real MIDI, ports, CLI execution wiring, runtime execution, active behavior,
  and hardware behavior remain absent

## 4. Candidate Branch Options

Safe branch options after the accepted bridge report review:

- pause at the clean bridge report checkpoint
- create a docs-only next-branch selection after the report review
- create a docs-only bridge report CLI preview design/spec
- create a broader progress/timeline update
- return to passive/project documentation

Rejected for the next branch:

- bridge report CLI preview implementation
- bridge invocation from report code
- `MockMidiSender` construction from report code
- message emission from report code
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

- docs-only mock runtime/active bridge report CLI preview design/spec

This next branch should remain documentation-only.

It should design a future passive CLI preview command that prints the existing
formatted bridge report only.

It should not implement the CLI command.

## 6. Expected Future Design/Spec Scope

The future design/spec should cover:

- purpose of a passive CLI preview for the bridge report
- proposed command name:
  - `mock-runtime-active-bridge-report`
- expected behavior:
  - print `format_mock_runtime_active_bridge_report()` output only
  - exit 0
  - require no arguments beyond `--help`
  - remain deterministic and fixture-backed if implemented later
- existing bridge report source:
  - `rytm_randomizer.mock_runtime_active_bridge_report`
- expected help output
- expected report output
- required passive CLI tests before implementation
- fixture expectations before implementation
- closeout expectations if implemented later
- explicit non-goals

The future design/spec should preserve:

- profile `2` as the only accepted bridge candidate
- profile `3` as bridge rejected
- profile `4` as parked
- no bridge invocation from CLI preview code
- no `MockMidiSender` construction from CLI preview code
- no message emission
- no CLI execution wiring
- no runtime execution
- no dispatch
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
- bridge invocation
- `MockMidiSender` construction
- message emission
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

- the report implementation is accepted
- the next useful step is passive visibility from the CLI
- the CLI preview should be designed before implementation
- the command can expose report output without invoking bridge behavior
- this preserves the project pattern of design, review, implementation,
  checkpoint, review

## 9. Parked Scope

Still parked:

- bridge report CLI preview implementation
- bridge invocation from CLI preview code
- `MockMidiSender` construction from CLI preview code
- message emission from CLI preview code
- active CLI commands
- CLI execution wiring
- runtime execution
- dispatch
- command execution
- scene execution
- mutation execution
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

- docs-only mock runtime/active bridge report CLI preview design/spec

The next recommended task is to create that documentation-only design/spec.

Hardware remains off.

No implementation in this slice.

## 12. Follow-Up Design Spec

The selected next branch is now represented by:

- `Docs/V134_BEHAVIOR_PARITY_MOCK_RUNTIME_ACTIVE_BRIDGE_REPORT_CLI_PREVIEW_DESIGN_SPEC.md`

That design/spec defines a future passive CLI preview command:

- `python -m rytm_randomizer.cli mock-runtime-active-bridge-report`

The design/spec requires the future command to print existing
`format_mock_runtime_active_bridge_report()` output only.

The design/spec preserves these boundaries:

- no bridge invocation from CLI preview code
- no `MockMidiSender` construction from CLI preview code
- no message emission from CLI preview code
- no active flags
- no CLI execution wiring
- no runtime execution
- no real MIDI
- no ports
- no hardware behavior

Recommended follow-up:

- create a documentation-only review/acceptance gate for the CLI preview
  design/spec

This follow-up adds no implementation, tests, fixtures, closeout script changes,
CLI changes, CLI execution wiring, runtime execution, dispatch, command
execution, mutation execution, MIDI, ports, package metadata changes, active
behavior, or hardware behavior.
