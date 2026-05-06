# Mock MIDI Boundary Test Plan Review

## Purpose

This document reviews and accepts `MOCK_MIDI_BOUNDARY_TEST_PLAN.md` as the
current mock MIDI testing plan.

It confirms that the project is still passive/read-only and that no mock MIDI
code, real MIDI code, active execution, or hardware-facing behavior has been
implemented.

## Current Clean Baseline

Current branch:

- modularize-v1.34

Current HEAD before this slice:

- 16fff78 Add mock MIDI boundary test plan

Current phase:

- passive CLI / dry-run foundation complete
- passive-to-active boundary accepted
- active-layer design/spec accepted
- mock MIDI boundary test plan created

Current hardware status:

- Analog Rytm MKII off
- Analog Four MKII off
- hardware not required

## Mock MIDI Plan Acceptance Summary

`MOCK_MIDI_BOUNDARY_TEST_PLAN.md` is accepted as the current planning document
for test-only MIDI behavior.

- Future MIDI behavior must be mockable before any real port opening exists.
- Unit tests must never open real MIDI ports.
- Passive CLI commands must remain read-only and must not construct or use any MIDI sender.
- Real hardware validation remains a later explicit phase.

## Accepted Mock MIDI Concepts

- MidiMessage concept
- MidiSender concept
- MockMidiSender concept
- MidiPortProvider concept
- HardwareExecutionContext concept
- ActiveCommandExecutor concept
- Mock-only unit tests before real MIDI
- No real port opening in tests
- Passive CLI remains separate from active execution

## Confirmed Safety Invariants

- no MIDI sending
- no MIDI port opening
- no dispatch
- no command execution
- no scene execution
- no hardware mutation
- no SysEx
- no GUI
- no capture
- no Analog Four support
- no Pads 5-12 support
- no machine/profile expansion
- `rytm_hybrid_randomizer_v134.py` remains untouched

## Preconditions Before Any Future Mock MIDI Scaffold

- clean Git status
- closeout passes
- V1.34 reference diff is empty
- mock MIDI boundary test plan accepted
- active-layer design/spec accepted
- passive-to-active boundary accepted
- mock MIDI code must be test-only/passive-safe
- no real MIDI libraries should be required by tests
- no hardware required
- no real ports opened

## What The First Mock Scaffold May Include Later

This is future possibility only, not implementation.

- small dataclass-like MIDI message representation
- MockMidiSender that records messages in memory
- tests proving messages are recorded only when explicitly invoked in mock tests
- tests proving passive CLI commands do not create or use sender objects
- no real MIDI backend
- no port provider implementation
- no active CLI command yet

## Rejected/Forbidden Next Moves

- Do not add real MIDI backend.
- Do not open ports.
- Do not turn on the Rytm.
- Do not add execute-command.
- Do not add send-command.
- Do not add hardware-test active behavior.
- Do not add scene/global mutation execution.
- Do not add Pads 5-12.
- Do not add Analog Four.
- Do not add SysEx.
- Do not add GUI/capture.

## Decision

- Mock MIDI boundary test plan accepted for planning.
- Proceed next with test-only mock MIDI scaffold design or implementation only if it remains mock-only and no real MIDI/ports/hardware are introduced.
- Hardware remains off.

## Next Recommended Task

Review the test-only mock MIDI scaffold milestone and decide the next mock-only
test slice.

Implemented milestone:

- 58f4a44 Add test-only mock MIDI scaffold
- `rytm_randomizer/mock_midi.py`
- `tests/test_mock_midi.py`
- `Scripts/closeout_check.ps1`

The scaffold records intended messages in memory only. It adds no real MIDI
backend, no port provider, no hardware detection, no hardware send, no active
CLI command, and no execution.

Mock MIDI scaffold review:

- `Docs/MOCK_MIDI_SCAFFOLD_REVIEW.md`

The review accepts the test-only mock MIDI scaffold, records that no real MIDI
behavior exists, sets the next recommended task as mock message mapping
design/spec or a test-only mapper scaffold, and keeps hardware off.

Mock message mapping design/spec:

- `Docs/MOCK_MESSAGE_MAPPING_DESIGN_SPEC.md`

The spec defines future mock-only mapping from passive metadata to mock
MidiMessage objects, keeps hardware off, keeps real MIDI absent, and sets the
next recommended task as review/acceptance before any mapper scaffold.

Mock message mapping design/spec review:

- `Docs/MOCK_MESSAGE_MAPPING_DESIGN_SPEC_REVIEW.md`

The review accepts the mock message mapping design/spec for planning, records
that no mapper implementation exists yet, sets the next recommended task as a
test-only mock mapper scaffold for group profile 2, and keeps hardware off.

Keep hardware off.
