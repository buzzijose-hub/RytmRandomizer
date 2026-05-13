# V1.34 Mock Runtime/Active Bridge Report Design Spec

## 1. Purpose

Design a future read-only report for the mock runtime/active bridge.

The future report should summarize current bridge behavior without invoking the
bridge, constructing a sender, emitting messages, wiring CLI execution, or
widening scope.

This is a documentation-only design/spec.

It adds no implementation, tests, fixtures, closeout script changes, CLI
changes, CLI execution wiring, runtime execution, dispatch, command execution,
MIDI, ports, package metadata changes, active behavior, or hardware behavior.

## 2. Current Clean Baseline

Current branch:

- `modularize-v1.34`

Current HEAD before this design/spec slice:

- `e291852 Add next branch selection after bridge review`

Current phase:

- Behavior-Parity Passive/Mock Visibility Phase
- mock runtime/active bridge implemented and accepted
- next branch selected as read-only bridge report design/spec
- bridge report design/spec now being documented

Hardware status:

- Analog Rytm MKII off
- Analog Four MKII off
- hardware not required

## 3. Current Accepted Bridge Scope

Current accepted bridge:

- module: `rytm_randomizer.mock_runtime_active_bridge`
- request type: `RuntimeActiveBridgeRequest`
- result type: `RuntimeActiveBridgeResult`
- evaluator: `evaluate_mock_runtime_active_bridge`
- sender boundary: `MockMidiSender` only

Current success candidate:

- source kind: `group_profile`
- source key: `2`
- source name: My BD Hard
- target concept: Pad 1 / BD Hard

Accepted success requirements:

- request is armed
- dry-run is confirmed
- runtime scope validates
- active boundary accepts
- supplied sender is a `MockMidiSender`

## 4. Current Accepted Rejection And Parked Scope

Current bridge-rejected scope:

- profile `3` / My BD Classic
- unknown group profile keys
- unsupported source kinds
- missing arming
- missing dry-run confirmation
- invalid request type
- invalid sender type

Current parked scope:

- profile `4` / My BD Acoustic

Accepted behavior for all rejection/parked cases:

- accepted flag is false
- no emitted messages
- `MockMidiSender` remains empty
- metadata remains inert and copied/immutable

## 5. Report Concept

The future report should be passive and read-only.

It should summarize the current bridge contract from static report data and
known accepted constants, not by executing the bridge.

The report should answer:

- what bridge module exists
- which source is the only accepted success candidate
- which profiles are rejected or parked
- what arming/dry-run conditions are required
- what sender boundary is allowed
- what remains absent
- what tests/closeout currently protect the bridge

The report should not:

- invoke `evaluate_mock_runtime_active_bridge`
- construct `RuntimeActiveBridgeRequest`
- construct `MockMidiSender`
- call `sender.send`
- call `sender.send_many`
- emit messages
- open ports
- import real MIDI libraries
- wire CLI execution

## 6. Proposed Future Module Shape

Future module:

- `rytm_randomizer.mock_runtime_active_bridge_report`

Suggested future public functions:

- `build_mock_runtime_active_bridge_report()`
- `summarize_mock_runtime_active_bridge_report(report=None)`
- `format_mock_runtime_active_bridge_report(report=None)`

Design intent:

- `build_...` returns deterministic copied data
- `summarize_...` returns compact copied summary data
- `format_...` returns deterministic human-readable lines

The future module should remain read-only and in-memory.

## 7. Proposed Report Data Shape

The future report may include:

- `title`
- `mode`
  - `read_only: True`
  - `mock_only: True`
  - `metadata_only: True`
  - `invokes_bridge: False`
  - `constructs_sender: False`
  - `emits_messages: False`
- `bridge`
  - `module: rytm_randomizer.mock_runtime_active_bridge`
  - `request_type: RuntimeActiveBridgeRequest`
  - `result_type: RuntimeActiveBridgeResult`
  - `evaluator: evaluate_mock_runtime_active_bridge`
- `accepted_candidate`
  - `source_kind: group_profile`
  - `source_key: "2"`
  - `source_name: My BD Hard`
  - `target: Pad 1 / BD Hard`
  - `requires_armed: True`
  - `requires_dry_run_confirmed: True`
  - `sender: MockMidiSender`
- `rejected_cases`
  - missing arming
  - missing dry-run confirmation
  - profile `3` / My BD Classic
  - unknown key
  - unsupported source kind
  - invalid request
  - invalid sender
- `parked_cases`
  - profile `4` / My BD Acoustic
- `safety`
  - `real_midi: absent`
  - `port_opening: absent`
  - `hardware_required: False`
  - `cli_execution_wiring: absent`
  - `runtime_execution: absent`
  - `dispatch: absent`

## 8. Proposed Formatter Behavior

The future formatter should produce deterministic lines with sections such as:

- `RytmRandomizer Mock Runtime Active Bridge Report`
- `Bridge Mode`
- `Accepted Candidate`
- `Rejected Cases`
- `Parked Cases`
- `Safety`
- `Source`

The formatted report should make clear:

- profile `2` is the only accepted bridge candidate
- profile `3` is rejected at the bridge
- profile `4` is parked
- arming and dry-run confirmation are required
- no real MIDI is sent
- no ports are opened
- no hardware is required
- no CLI execution wiring exists

## 9. Proposed Future Tests

Future tests should verify:

- importing `rytm_randomizer.mock_runtime_active_bridge_report` prints nothing
- report includes profile `2` as accepted candidate
- report marks profile `3` as rejected
- report marks profile `4` as parked
- report says `read_only` is true
- report says `mock_only` is true
- report says `invokes_bridge` is false
- report says `constructs_sender` is false
- report says `emits_messages` is false
- report says real MIDI is absent
- report says port opening is absent
- report says hardware is not required
- report says CLI execution wiring is absent
- report data is copied/mutation-safe
- formatted report is deterministic
- report implementation imports no `mido`
- report implementation imports no `rtmidi`
- report implementation does not instantiate `MockMidiSender`
- report implementation does not call `evaluate_mock_runtime_active_bridge`
- passive CLI behavior remains unchanged
- V1.34 reference remains untouched
- package metadata remains untouched

## 10. Future Closeout Expectations

If implemented later, closeout should add one label:

- `=== Test: Mock Runtime Active Bridge Report ===`

The future closeout entry should run:

- `tests/test_mock_runtime_active_bridge_report.py`

Existing closeout entries must remain:

- `Mock Runtime Active Bridge`
- `Active/Runtime Report Alignment`
- `Runtime Plan Report`
- `Active Boundary Report`
- `Mock MIDI`

## 11. Future CLI Position

No CLI command should be added in the first report implementation packet.

If a CLI preview is desired later, it should be separately planned and
reviewed.

Possible future CLI name, for later discussion only:

- `mock-runtime-active-bridge-report`

This design/spec does not authorize that command.

## 12. What Must Remain Absent

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

## 13. Non-Goals

This design/spec does not add:

- implementation
- tests
- fixtures
- closeout script changes
- CLI changes
- bridge report CLI preview
- bridge invocation
- `MockMidiSender` construction
- message emission
- profile `3` bridge success
- profile `4` support
- real MIDI
- ports
- hardware

## 14. Safe Next Options

Safe next options after this design/spec:

- create a docs-only review/acceptance gate for this design/spec
- create the read-only bridge report implementation packet after review
- create a broader progress/timeline update
- pause at this clean checkpoint

Rejected immediate next moves:

- bridge report implementation without review
- bridge report CLI preview
- real MIDI
- port opening
- hardware validation
- active CLI commands
- runtime execution
- bridge scope expansion

## 15. Recommendation

Recommended next task:

- create a documentation-only review/acceptance gate for this design/spec

Reason:

- the bridge report should be reviewed before implementation
- the report must remain passive and must not invoke bridge behavior
- profile `2`, profile `3`, and profile `4` semantics should remain explicit

## 16. Decision

The read-only mock runtime/active bridge report design/spec is documented.

Hardware remains off.

No implementation in this slice.

## 17. Follow-Up Review

The design/spec is now reviewed and accepted by:

- `Docs/V134_BEHAVIOR_PARITY_MOCK_RUNTIME_ACTIVE_BRIDGE_REPORT_DESIGN_SPEC_REVIEW.md`

That review accepts this document as the current planning gate for a future
read-only bridge report implementation packet.

The review preserves these boundaries:

- no bridge invocation from report code
- no `MockMidiSender` construction from report code
- no message emission from report code
- no CLI command in the first implementation packet
- no real MIDI
- no ports
- no runtime execution
- no active behavior
- no hardware behavior

Recommended follow-up:

- create the read-only mock runtime/active bridge report implementation packet

The follow-up implementation packet must remain report-only and must not widen
the accepted bridge scope.

## 18. Follow-Up Implementation Checkpoint

The read-only mock runtime/active bridge report was implemented by:

- `75f731c Add mock runtime active bridge report`

Implementation checkpoint:

- `Docs/V134_BEHAVIOR_PARITY_MOCK_RUNTIME_ACTIVE_BRIDGE_REPORT_CHECKPOINT.md`

The implementation follows this design/spec by remaining read-only,
mock-only, metadata-only, deterministic, and in-memory.

It adds no CLI command, bridge invocation, `MockMidiSender` construction,
message emission, real MIDI, ports, runtime execution, active behavior, or
hardware behavior.

Recommended follow-up:

- create a documentation-only review/acceptance gate for the implementation
