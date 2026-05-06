# Mock Message Mapping Design Spec Review

## Purpose

This document reviews and accepts `MOCK_MESSAGE_MAPPING_DESIGN_SPEC.md` as the
current planning spec.

It confirms that the project remains passive/mock-only and that no mapper
implementation, real MIDI, active execution, port opening, or hardware-facing
behavior has been implemented.

## Current Clean Baseline

Current branch:

- modularize-v1.34

Current HEAD before this slice:

- d1df975 Add mock message mapping design spec

Current phase:

- passive CLI / dry-run foundation complete
- test-only mock MIDI scaffold accepted
- mock message mapping design/spec created

Current hardware status:

- Analog Rytm MKII off
- Analog Four MKII off
- hardware not required

## Mock Message Mapping Design Acceptance Summary

`MOCK_MESSAGE_MAPPING_DESIGN_SPEC.md` is accepted as the current planning
document for future test-only message mapping.

- Future mapping must remain mock-only first.
- Future mapping must use mock MidiMessage objects only.
- Future mapping must not open ports.
- Future mapping must not send MIDI.
- Future mapping must not connect to CLI active execution.
- Real hardware validation remains a later explicit phase.

## Accepted Design Concepts

- passive metadata to mock MidiMessage mapping
- group profile metadata as the first likely source
- group profile 2 / My BD Hard as the first likely mock-only candidate
- deterministic mock message output
- MockMidiSender-only capture
- no real MIDI backend
- no port provider
- no hardware requirement
- no CLI active command

## Confirmed Safety Invariants

- no mido
- no real MIDI library
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
- no CLI wiring to active behavior
- no active command
- `rytm_hybrid_randomizer_v134.py` remains untouched

## Preconditions Before Any Future Mapper Scaffold

- clean Git status
- closeout passes
- V1.34 reference diff is empty
- mock MIDI scaffold accepted
- mock message mapping design accepted
- passive CLI remains read-only
- mapper work must remain test-only/mock-only first
- mapper work must not open ports
- mapper work must not send real MIDI
- mapper work must not connect to active CLI execution
- tests must prove no real MIDI libraries are imported

## What The First Mapper Scaffold May Include Later

This is future possibility only, not implementation:

- `rytm_randomizer/mock_message_mapper.py`
- `map_group_profile_to_mock_messages(key)`
- support only key `"2"` initially
- return deterministic mock MidiMessage objects
- include metadata:
  - source kind: group_profile
  - source key: 2
  - name: My BD Hard
  - group pad: 1
  - machine value: 0
- tests using MockMidiSender only
- no real MIDI backend
- no port opening
- no active CLI command

## Rejected/Forbidden Next Moves

- Do not add real MIDI backend.
- Do not add mido.
- Do not open ports.
- Do not turn on the Rytm.
- Do not add execute-command.
- Do not add send-command.
- Do not add hardware-test.
- Do not wire mock mapping into active CLI behavior.
- Do not add command execution.
- Do not add scene/global mutation execution.
- Do not add Pads 5-12.
- Do not add Analog Four.
- Do not add SysEx.
- Do not add GUI/capture.

## Decision

- Mock message mapping design/spec accepted for planning.
- Proceed next with a tiny test-only mock mapper scaffold if it remains mock-only and limited to group profile 2.
- Hardware remains off.

## Next Recommended Task

Implemented milestone:

- 4a590c8 Add test-only mock message mapper
- `rytm_randomizer/mock_message_mapper.py`
- `tests/test_mock_message_mapper.py`
- `Scripts/closeout_check.ps1`

The mapper supports only group profile key `"2"` / My BD Hard. It returns
deterministic inert mock MidiMessage objects using the existing mock_midi.py
scaffold, records cleanly through MockMidiSender, and fails safely for unknown
or unsupported keys.

The closeout suite now includes "Test: Mock Message Mapper".

Mock message mapper review:

- `Docs/MOCK_MESSAGE_MAPPER_REVIEW.md`

The review accepts the test-only mock message mapper, records that no real
MIDI behavior exists, keeps future mapper expansion mock-only unless
separately reviewed, and keeps hardware off.

No real MIDI.

No hardware.

No active CLI command.

No ports.

No execution.
