# Mock Message Mapper Review

## Purpose

This document reviews and accepts the test-only mock message mapper.

It confirms that the project remains passive/mock-only and that no real MIDI,
active execution, port opening, CLI wiring, or hardware-facing behavior exists.

## Current Clean Baseline

Current branch:

- modularize-v1.34

Current HEAD before this slice:

- 5ee0e01 Update checkpoint after mock message mapper

Current phase:

- passive CLI / dry-run foundation complete
- test-only mock MIDI scaffold complete
- test-only mock message mapper complete

Current hardware status:

- Analog Rytm MKII off
- Analog Four MKII off
- hardware not required

## Mock Message Mapper Acceptance Summary

- `rytm_randomizer/mock_message_mapper.py` is accepted as the current test-only mapper scaffold.
- `tests/test_mock_message_mapper.py` is accepted as current test coverage.
- The mapper supports group profile key `"2"` / My BD Hard.
- The mapper supports group profile key `"3"` / My BD Classic.
- Existing group profile key `"4"` remains unsupported and fails safely.
- The mapper returns deterministic inert MidiMessage data.
- The mapper records through MockMidiSender.
- The mapper fails safely for unknown/unsupported keys.
- The mapper is not wired into CLI.
- The mapper is not wired into runtime execution.
- The mapper imports no real MIDI library.
- The mapper opens no ports.
- The mapper sends no MIDI.
- The mapper adds no hardware behavior.

## Accepted Mock Mapping Scope

- source kind: group_profile
- source key: `"2"`
- source name: My BD Hard
- group pad: 1
- machine value: 0
- target concept: Pad 1 / BD Hard
- mock_only: True
- sends_real_midi: False
- source key: `"3"`
- source name: My BD Classic
- group pad: 2
- machine value: 1
- target concept: Pad 2 / BD Classic
- mock_only: True
- sends_real_midi: False

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

## Preconditions Before Any Future Mapper Expansion

- clean Git status
- closeout passes
- V1.34 reference diff is empty
- mock message mapper accepted
- passive CLI remains read-only
- any expansion must remain test-only/mock-only first
- no real MIDI library imports
- no port opening
- no real MIDI sending
- no active CLI execution
- no hardware required

## What Future Work May Include Later

This is future possibility only:

- add mock mapping for another existing group profile
- add mock mapping for one passive command only after review
- keep all mapper work test-only
- keep all messages inert and metadata-rich
- keep hardware off
- keep real MIDI absent

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

- Test-only mock message mapper accepted.
- Proceed next with either:
  - documentation-only next-phase checkpoint
  - another tiny test-only mapper expansion only if it remains mock-only and limited to existing passive metadata
- Hardware remains off.

## Next Recommended Task

Latest mock-only mapper expansion:

- 4507647 Add mock mapping for group profile 3
- `rytm_randomizer/mock_message_mapper.py`
- `tests/test_mock_message_mapper.py`

The mapper now also supports existing group profile key `"3"` / My BD Classic.
Group profile key `"2"` / My BD Hard behavior remains unchanged. Group profile
key `"4"` remains unsupported and fails safely. The mapping remains test-only,
mock-only, deterministic, and unwired from CLI or runtime execution.

Update `Docs/NEXT_ACTION.md` to recommend either:

- a progress checkpoint / milestone report
- a small mock-only mapper expansion plan

No real MIDI.

No hardware.

No active CLI command.

No ports.

No execution.
