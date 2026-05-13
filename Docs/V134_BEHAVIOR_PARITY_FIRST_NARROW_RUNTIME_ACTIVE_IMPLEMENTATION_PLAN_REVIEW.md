# V1.34 First Narrow Runtime/Active-Facing Implementation Plan Review

## 1. Purpose

Review and accept the first narrow runtime/active-facing implementation plan.

This is a documentation-only review gate.

It confirms the future implementation packet is narrow enough to execute next
if it remains mock-only, test-only, and hardware-off.

This review adds no implementation, tests, fixtures, closeout script changes,
CLI changes, CLI execution wiring, runtime execution, dispatch, command
execution, MIDI, ports, package metadata changes, active behavior, or hardware
behavior.

## 2. Current Clean Baseline

Current branch:

- `modularize-v1.34`

Current HEAD before this review slice:

- `29d1cc0 Add first narrow runtime active implementation plan`

Current phase:

- Behavior-Parity Passive/Mock Visibility Phase
- passive/runtime visibility phase accepted
- first narrow runtime/active-facing implementation plan created
- first narrow implementation plan now being reviewed

Hardware status:

- Analog Rytm MKII off
- Analog Four MKII off
- hardware not required

## 3. Review Decision

Accepted plan:

- `Docs/V134_BEHAVIOR_PARITY_FIRST_NARROW_RUNTIME_ACTIVE_IMPLEMENTATION_PLAN.md`

Accepted plan milestone:

- `29d1cc0 Add first narrow runtime active implementation plan`

The plan is accepted as the current gate for the first narrow
runtime/active-facing implementation packet.

The plan remains constrained to a mock-only, test-only bridge.

The plan does not authorize real MIDI, ports, active CLI commands, runtime
execution, dispatch, command execution, hardware behavior, or hardware
validation.

## 4. Accepted Candidate Scope

Accepted future candidate:

- source kind: `group_profile`
- source key: `2`
- source name: My BD Hard
- target concept: Pad 1 / BD Hard
- current runtime-plan status: supported planning input, blocked by default
- current active-boundary status: accepted first mock-only active candidate
- sender boundary: `MockMidiSender` only

Accepted success path:

- profile `2` succeeds only when:
  - request is mock-only
  - request is armed in test-only code
  - dry-run is confirmed in test-only code
  - runtime scope validates
  - active boundary accepts
  - messages are recorded through `MockMidiSender`

Accepted failure paths:

- missing arming emits no messages
- missing dry-run confirmation emits no messages
- profile `3` remains runtime-plan supported but active-boundary rejected
- profile `4` remains parked
- unknown keys fail safely
- unsupported source kinds fail safely
- invalid request/sender types fail before message emission

## 5. Accepted Future File Scope

Accepted future implementation files:

- `rytm_randomizer/mock_runtime_active_bridge.py`
- `tests/test_mock_runtime_active_bridge.py`

Accepted future closeout update:

- `Scripts/closeout_check.ps1`
- closeout label:
  - `=== Test: Mock Runtime Active Bridge ===`

Files that must remain untouched by the future implementation packet:

- `rytm_hybrid_randomizer_v134.py`
- `rytm_randomizer/cli.py`
- `pyproject.toml`
- `requirements.txt`
- `setup.py`
- `setup.cfg`
- existing metadata source files
- runtime dispatch/execution modules
- active CLI command modules

## 6. Accepted Future Module Boundary

Accepted future module:

- `rytm_randomizer.mock_runtime_active_bridge`

Accepted public names:

- `RuntimeActiveBridgeRequest`
- `RuntimeActiveBridgeResult`
- `evaluate_mock_runtime_active_bridge`

Accepted module constraints:

- imports existing inert modules only
- uses `RuntimeIntent` / `validate_runtime_intent_scope`
- uses `ActiveBoundaryRequest` / `evaluate_mock_active_boundary`
- uses `MockMidiSender`
- returns copied/immutable metadata
- emits no messages on failure
- exposes no CLI command names
- opens no ports
- sends no real MIDI
- mutates no runtime state
- touches no hardware

## 7. Required Future Test Coverage

The future implementation packet must prove:

- importing `rytm_randomizer.mock_runtime_active_bridge` prints nothing
- importing the bridge imports no `mido`
- importing the bridge imports no `rtmidi`
- profile `2` records mock messages only when armed and dry-run confirmed
- missing arming emits no messages
- missing dry-run confirmation emits no messages
- profile `3` remains runtime-plan supported but bridge rejected
- profile `4` remains parked and emits no messages
- unknown keys emit no messages
- unsupported source kinds emit no messages
- passive CLI `report` remains read-only
- V1.34 reference remains untouched
- package metadata remains untouched

## 8. Confirmed Preserved Semantics

Profile `2` / My BD Hard:

- remains the only accepted bridge success candidate
- remains mock-only
- remains test-only
- remains no real MIDI / no ports / no hardware

Profile `3` / My BD Classic:

- remains runtime-plan supported
- remains active-boundary unsupported
- must not become a bridge success path in this packet

Profile `4` / My BD Acoustic:

- remains parked
- must not receive mock mapper, runtime, active-boundary, or bridge support in
  this packet

Unknown and unsupported inputs:

- remain safe failures
- must emit no messages

## 9. Confirmed Absent Behavior

Still absent:

- `execute-command`
- `send-command`
- `hardware-test`
- CLI execution wiring
- runtime execution
- dispatch
- command execution
- scene execution
- mutation execution
- real MIDI dependency
- `mido`
- `rtmidi`
- port discovery
- port opening
- MIDI sending
- hardware mutation
- hardware validation
- SysEx
- GUI/capture
- Analog Four support
- Pads 5-12 support
- package metadata changes
- machine/profile universe expansion

## 10. Preconditions Before Executing The Future Packet

Before implementation begins:

- git status must be clean
- closeout must pass
- V1.34 reference diff must be empty
- package metadata diff must be empty
- this review must be accepted
- implementation must follow the plan document
- implementation must use tests first
- implementation must remain mock-only
- implementation must not touch CLI execution wiring
- hardware must remain off

## 11. Safe Next Task

Safe next task after this review:

- execute the accepted first narrow runtime/active-facing implementation plan

Execution constraints for that next task:

- create only the mock runtime/active bridge module
- create only the bridge test file
- update closeout only for the bridge test
- do not edit CLI
- do not add active CLI commands
- do not add real MIDI
- do not open ports
- do not require hardware
- keep profile `3` rejected at the bridge
- keep profile `4` parked

## 12. Rejected Next Moves

Do not jump to:

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
- profile `4` support
- Analog Four support
- Pads 5-12 support
- SysEx
- GUI/capture

## 13. Decision

The first narrow runtime/active-facing implementation plan is accepted.

The next approved implementation packet is:

- mock runtime/active bridge for profile `2` only

Hardware remains off.

No implementation in this slice.
