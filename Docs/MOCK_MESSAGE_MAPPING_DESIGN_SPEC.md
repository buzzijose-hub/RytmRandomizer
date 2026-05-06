# Mock Message Mapping Design Spec

## Purpose

This document defines the future test-only mapping layer between passive
metadata and mock `MidiMessage` objects.

It is design/spec only. No mapper implementation is added by this document. No
real MIDI behavior is added by this document.

## Current Clean Baseline

Current branch:

- modularize-v1.34

Current HEAD before this slice:

- 82d4898 Add mock MIDI scaffold review

Current phase:

- passive CLI / dry-run foundation complete
- mock MIDI scaffold accepted

Hardware status:

- Analog Rytm MKII off
- Analog Four MKII off
- hardware not required

## Current Available Passive/Mock Pieces

- Passive registry metadata
- Passive command/profile/scene lookup
- Passive CLI report/list/search/inspect/preview
- Test-only `mock_midi.py` scaffold
- MockMidiSender
- MidiMessage representation
- Mock MIDI tests in closeout

## Mapping Concept

- A future mapper may translate selected passive metadata into intended mock MidiMessage objects.
- The mapper must be mock-only at first.
- The mapper must not open ports.
- The mapper must not send MIDI.
- The mapper must not connect to real hardware.
- The mapper must not be wired to active CLI execution yet.
- The mapper must produce inspectable message objects for tests only.

## Candidate Mapping Source

Start with group profile metadata, not scenes or global mutations.

Prefer group profile key 2: My BD Hard.

Reason:

- already exists in passive group_profiles
- targets validated Pad 1
- machine value 0 is already documented for BD Hard
- smaller scope than scenes/global mutation

This is a future mock-only candidate, not a real hardware test.

## Conceptual Output

A future mock mapper for group profile 2 may emit a mock MidiMessage
representing intended machine selection or anchor-related intent.

It should include enough metadata to inspect:

- source kind: group_profile
- source key: 2
- name: My BD Hard
- group pad: 1
- machine value: 0
- target concept: Pad 1 / BD Hard

If represented as a CC-like message later, it must remain mock-only until
active-layer review accepts a real MIDI candidate.

## Required Safeguards

- Mapping unknown profile keys must fail safely.
- Mapping unsupported metadata must fail safely.
- No messages emitted when validation fails.
- No messages emitted for unsupported scope.
- No real MIDI libraries imported.
- No ports opened.
- No CLI active command added.
- No hardware required.

## What Not To Map Yet

- scenes
- global mutations
- wild/random discovery
- full command execution
- Pads 5-12
- Analog Four
- SysEx
- pattern/project/kit save/clear
- transport/clock
- GUI/capture
- reference-analysis features

## Proposed Future Module Shape

This is design only, not implementation.

Future module:

- `rytm_randomizer/mock_message_mapper.py`

Possible future functions:

- `map_group_profile_to_mock_messages(key)`
- `map_command_to_mock_messages(key)`

For the first implementation, prefer only:

- `map_group_profile_to_mock_messages("2")`

Do not implement in this slice.

## Proposed Future Tests

Future tests should verify:

- importing mapper prints nothing
- unknown keys fail safely
- group profile 2 maps to deterministic mock messages
- emitted message metadata matches expected group profile metadata
- MockMidiSender records mapped messages in order
- no real MIDI library is imported
- no ports are opened
- passive CLI behavior remains unchanged
- V1.34 reference remains untouched
- no Pads 5-12 support exposed
- no Analog Four support exposed

## Relationship To Active Layer

- Mock mapping is not active execution.
- Mock mapping is not hardware validation.
- Mock mapping is only a test design step before any real send path.
- Active layer remains unimplemented.
- Hardware remains off.

## Stop Conditions

- Any real MIDI import
- Any port opening
- Any CLI active command
- Any dispatch/execution behavior
- Any V1.34 reference diff
- Any Pads 5-12 or Analog Four scope added
- Any uncertainty about mapping meaning

## Next Recommended Task After This Spec

Review status:

- `Docs/MOCK_MESSAGE_MAPPING_DESIGN_SPEC_REVIEW.md`

The mock message mapping design/spec is accepted for planning.

Implemented milestone:

- 4a590c8 Add test-only mock message mapper
- `rytm_randomizer/mock_message_mapper.py`
- `tests/test_mock_message_mapper.py`
- `Scripts/closeout_check.ps1`

The mapper supports only group profile key `"2"` / My BD Hard, returns
deterministic inert mock MidiMessage objects using the existing mock_midi.py
scaffold, records cleanly through MockMidiSender, and fails safely for unknown
or unsupported keys.

The closeout suite now includes "Test: Mock Message Mapper".

No real MIDI backend, mido dependency, port provider, hardware detection,
hardware send, active CLI command, execute-command, send-command,
hardware-test command, runtime execution, dispatch, SysEx, GUI/capture, Analog
Four support, Pads 5-12 support, or machine/profile expansion was added.

Hardware remains off.
