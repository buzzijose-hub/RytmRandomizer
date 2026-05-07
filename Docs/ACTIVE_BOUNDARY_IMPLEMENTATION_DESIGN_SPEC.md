# Active Boundary Implementation Design Spec

## 1. Purpose

Define the future implementation shape for the first active boundary while
remaining at design/spec altitude.

This spec uses the accepted mock-only proof for group profile `"2"` / My BD
Hard to define the smallest future active boundary that can still be tested
without real MIDI, ports, CLI execution, or hardware.

This document does not implement code, tests, active behavior, MIDI behavior,
port opening, dispatch, CLI commands, or hardware validation.

## 2. Current Clean Baseline

Current branch:

- modularize-v1.34

Current HEAD before this slice:

- bb48555 Add active boundary implementation planning gate

Current phase:

- Passive/Mock Foundation Phase
- mock-only active candidate tests accepted
- active boundary implementation planning gate established
- active boundary implementation design/spec now being documented

Hardware status:

- Analog Rytm MKII off
- Analog Four MKII off
- hardware not required

## 3. Accepted Proof Input

Accepted mock-only proof:

- group profile `"2"` / My BD Hard

Existing proof components:

- `tests/test_mock_only_active_candidate.py`
- `rytm_randomizer/mock_message_mapper.py`
- `rytm_randomizer/mock_midi.py`
- `MockMidiSender`
- `MidiMessage`
- `map_group_profile_to_mock_messages("2")`

The proof remains mock-only and does not authorize hardware validation.

## 4. Design Decision

The first future active boundary should be:

- mock-first
- test-only at first
- candidate-specific
- isolated from passive CLI
- isolated from real MIDI
- unable to open ports
- unable to reach hardware

The boundary should not be a CLI feature yet.

The boundary should not introduce real MIDI yet.

The boundary should not implement profile `"4"` support.

## 5. Proposed Future Module Shape

Future implementation may create:

- `rytm_randomizer/active_boundary.py`
- `tests/test_active_boundary.py`

Only after separate approval, closeout may add:

- `=== Test: Active Boundary ===`

This slice does not create those files.

## 6. Conceptual Data Shapes

Future design names only, not implementation:

- `ActiveBoundaryRequest`
- `ActiveBoundaryResult`
- `ActiveBoundaryError`
- `evaluate_mock_active_boundary(request, sender)`

Conceptual request fields:

- `source_kind`
- `source_key`
- `armed`
- `dry_run_confirmed`
- `target`
- `metadata`

Conceptual result fields:

- `accepted`
- `emitted_messages`
- `reason`
- `mock_only`
- `sends_real_midi`

## 7. First Candidate Behavior

For group profile `"2"` / My BD Hard:

- missing arming should fail safely
- missing dry-run confirmation should fail safely
- unknown key should fail safely
- unsupported key should fail safely
- profile `"4"` should fail safely
- no mock messages should emit on failure
- armed and dry-run-confirmed mock request may record inert messages through `MockMidiSender`
- result metadata must state `mock_only: True`
- result metadata must state `sends_real_midi: False`

This is still mock-only behavior.

## 8. Passive CLI Separation

The passive CLI must not import or construct the active boundary in this phase.

These commands must remain read-only:

- report
- list-commands
- list-scenes
- list-group-profiles
- search-commands
- search-scenes
- search-group-profiles
- inspect-command
- inspect-scene
- inspect-group-profile
- preview-command
- preview-scene
- preview-group-profile
- mock-mapper-report

No active CLI command should be added yet.

## 9. Real MIDI Separation

The future active boundary must not:

- import `mido`
- import real MIDI libraries
- open MIDI ports
- send MIDI
- detect hardware
- require hardware

It may use only:

- `MockMidiSender`
- `MidiMessage`
- existing mock message mapper outputs

until a separate real MIDI boundary design is written and accepted.

## 10. Arming Semantics

Arming remains mock-only in the first implementation.

Future arming rules:

- `armed=False` fails safely
- missing arming fails safely
- `dry_run_confirmed=False` fails safely
- missing dry-run confirmation fails safely
- failure emits no messages
- failure does not mutate sender state
- success requires exact source kind and source key
- success requires supported candidate `"2"`

This arming model must not be exposed through CLI yet.

## 11. Expected Future Tests

Future tests should prove:

- importing active boundary prints nothing
- passive CLI commands remain unchanged
- missing arming emits no messages
- missing dry-run confirmation emits no messages
- unknown keys emit no messages
- profile `"4"` emits no messages
- profile `"2"` emits expected mock messages only when armed and dry-run confirmed
- `MockMidiSender` records expected messages in order
- no real MIDI libraries are imported
- no ports are opened
- no active CLI command names are exposed
- V1.34 reference remains untouched

## 12. File Ownership For Future Implementation

Allowed future implementation files, after separate approval:

- `rytm_randomizer/active_boundary.py`
- `tests/test_active_boundary.py`
- `Scripts/closeout_check.ps1`

Forbidden future implementation files unless separately approved:

- `rytm_randomizer/cli.py`
- `rytm_hybrid_randomizer_v134.py`
- `rytm_randomizer/mock_midi.py`
- `rytm_randomizer/mock_message_mapper.py`
- `rytm_randomizer/mock_mapper_report.py`
- runtime execution/dispatch modules
- metadata source files

## 13. Forbidden Scope

This design/spec does not add and does not authorize:

- implementation
- tests
- real MIDI
- mido
- MIDI port opening
- MIDI sending
- hardware detection
- hardware send
- active CLI commands
- CLI wiring to active behavior
- dispatch
- command execution
- scene execution
- hardware behavior
- SysEx
- GUI/capture
- Analog Four support
- Pads 5-12 support
- machine/profile expansion
- execute-command
- send-command
- hardware-test
- hardware validation
- profile `"4"` implementation

## 14. Required Review Before Implementation

Before implementation:

- this design/spec must be reviewed and accepted
- implementation plan must be written
- closeout must pass
- git status must be clean
- V1.34 reference diff must be empty
- hardware must remain off

## 15. Next Recommended Task

Create a documentation-only review/acceptance checkpoint for this design/spec.

Then, if accepted, create a mock-first active boundary implementation plan.

Do not implement active boundary code yet.

## 16. Decision

The future active boundary shape is defined at design/spec level.

The boundary remains mock-first and candidate-specific.

Hardware remains off.

No implementation in this slice.
