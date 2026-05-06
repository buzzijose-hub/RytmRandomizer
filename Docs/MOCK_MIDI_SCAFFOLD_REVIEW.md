# Mock MIDI Scaffold Review

## Purpose

This document reviews and accepts the test-only mock MIDI scaffold.

It confirms that the project remains passive/mock-only and that no real MIDI,
active execution, port opening, or hardware-facing behavior exists.

## Current Clean Baseline

Current branch:

- modularize-v1.34

Current HEAD before this slice:

- c15296a Update checkpoint after mock MIDI scaffold

Current phase:

- passive CLI / dry-run foundation complete
- mock MIDI scaffold exists for test-only message representation

Current hardware status:

- Analog Rytm MKII off
- Analog Four MKII off
- hardware not required

## Mock MIDI Scaffold Acceptance Summary

- `rytm_randomizer/mock_midi.py` is accepted as the current test-only mock MIDI scaffold.
- `tests/test_mock_midi.py` is accepted as the current mock MIDI test coverage.
- Mock MIDI is in-memory only.
- Mock MIDI does not import real MIDI libraries.
- Mock MIDI does not open ports.
- Mock MIDI does not send MIDI.
- Mock MIDI is not wired to CLI or active execution.

## Accepted Mock MIDI Concepts

- MidiMessage representation
- MockMidiSender
- `send()`
- `send_many()`
- `clear()`
- recorded messages in memory only
- no real MIDI backend
- no hardware requirement
- no import-time side effects

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
- no CLI wiring to mock MIDI
- no active command
- `rytm_hybrid_randomizer_v134.py` remains untouched

## Preconditions Before Any Future Command-To-Mock-Message Mapping

- clean Git status
- closeout passes
- V1.34 reference diff is empty
- mock MIDI scaffold accepted
- passive CLI remains read-only
- mapping work must remain mock-only first
- mapping work must not open ports
- mapping work must not send real MIDI
- mapping work must not connect to CLI active execution
- tests must prove no real MIDI libraries are imported

## What Future Mapping May Include Later

This is future possibility only:

- map one passive command metadata entry to intended mock MIDI messages
- use MockMidiSender only
- use one tiny known-safe candidate
- assert expected message type/channel/control/value
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
- Do not wire mock MIDI into CLI active behavior.
- Do not add scene/global mutation execution.
- Do not add Pads 5-12.
- Do not add Analog Four.
- Do not add SysEx.
- Do not add GUI/capture.

## Decision

- Test-only mock MIDI scaffold accepted.
- Proceed next with either:
  - documentation-only mock message mapping plan
  - test-only command-to-mock-message mapper scaffold
- Hardware remains off.

## Next Recommended Task

Review and accept the mock message mapping design/spec:

- `Docs/MOCK_MESSAGE_MAPPING_DESIGN_SPEC.md`

The spec defines future mock-only mapping from passive metadata to mock
MidiMessage objects, keeps hardware off, keeps real MIDI absent, and sets the
next recommended task as review/acceptance before any mapper scaffold.

Mock message mapping design/spec review:

- `Docs/MOCK_MESSAGE_MAPPING_DESIGN_SPEC_REVIEW.md`

The review accepts the mock message mapping design/spec for planning, records
that no mapper implementation exists yet, sets the next recommended task as a
test-only mock mapper scaffold for group profile 2, and keeps hardware off.

No real MIDI.

No hardware.

No active CLI command.
