# First-Candidate Mock-Only Active Test Design

## Purpose

This document defines the first mock-only active test candidate at design
level.

It is documentation-only. It does not implement tests, active behavior, MIDI,
port opening, CLI execution, or hardware validation.

## Current Clean Baseline

Current branch:

- modularize-v1.34

Current HEAD before this slice:

- 6938c58 Add passive mock foundation roadmap review

Current phase:

- Passive/Mock Foundation Phase
- passive/mock foundation complete enough for planning
- roadmap accepted
- first-candidate mock-only active test design now being documented

Hardware status:

- Analog Rytm MKII off
- Analog Four MKII off
- hardware not required

## Candidate Decision

The first mock-only active test candidate is:

- group profile `"2"` / My BD Hard

This candidate is mock-only and uses existing passive/mock metadata.

It is not a real hardware candidate yet.

## Why This Candidate

- It already exists in passive group profile metadata.
- It is already supported by the test-only mock message mapper.
- It targets validated Pad 1 scope.
- It is smaller than scenes, global mutation, wild/random discovery, or transport behavior.
- It can be represented through inert `MidiMessage` data.
- It can be recorded through `MockMidiSender` in memory only.
- It does not require profile `"4"` support.

## Candidate Boundary

The candidate may only prove:

- the mapper can produce deterministic inert mock messages for group profile `"2"`
- `MockMidiSender` can record those messages in order
- candidate metadata can be inspected in tests
- no real MIDI library is imported
- no ports are opened
- no MIDI is sent
- passive CLI remains read-only

The candidate must not prove or attempt:

- real MIDI sending
- port opening
- hardware behavior
- active CLI execution
- scene execution
- command dispatch
- SysEx
- GUI/capture
- Analog Four
- Pads 5-12
- profile `"4"` support

## Mock-Only Test Shape

Future mock-only tests may verify:

- importing any future candidate test helper prints nothing
- group profile `"2"` maps to deterministic inert mock messages
- mapped messages include expected metadata:
  - source kind: group_profile
  - source key: `"2"`
  - source name: My BD Hard
  - mock_only: True
  - sends_real_midi: False
- `MockMidiSender` records the candidate messages in order
- no messages are emitted for unknown keys
- no messages are emitted for unsupported keys
- no real MIDI library is imported
- no ports are opened
- no MIDI is sent
- passive CLI behavior remains unchanged
- V1.34 reference remains untouched

## Future Arming Concept

Arming remains conceptual only.

This candidate design does not add `--armed`, `execute-command`,
`send-command`, or `hardware-test`.

If future mock-only active tests introduce arming semantics, missing arming
must fail safely and emit no mock messages.

Arming must remain mock-only until a later reviewed active boundary exists.

## Preconditions Before Any Implementation

Before any mock-only implementation for this candidate:

- this design must be reviewed and accepted
- closeout must pass
- git status must be clean
- V1.34 reference diff must be empty
- passive commands must remain read-only
- mock MIDI must remain test-only/inert
- mock message mapper must remain test-only/inert
- no real MIDI libraries may be required
- no hardware may be required
- no ports may open
- no active CLI behavior may be added

## Forbidden Scope

- real MIDI
- mido
- MIDI port opening
- MIDI sending
- active execution
- CLI wiring to active behavior
- dispatch
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

## Profile 4 Position

Group profile `"4"` / My BD Acoustic remains parked.

Profile `"4"` is not part of this candidate.

Keeping profile `"4"` unsupported continues to prove unsupported/safe behavior
while the first candidate uses existing supported profile `"2"`.

## Hardware Stays Off

- Analog Rytm MKII remains off during this design phase.
- Analog Four MKII remains off during this design phase.
- Hardware is not required for this document.
- Hardware must not be turned on for this candidate design.

## Next Recommended Task

This first-candidate mock-only active test design is ready for review and
acceptance in:

- `Docs/FIRST_CANDIDATE_MOCK_ONLY_ACTIVE_TEST_DESIGN_REVIEW.md`

Then decide whether to:

- implement tiny mock-only tests for the accepted candidate
- add a more detailed mock-only implementation checklist
- pause at this planning checkpoint

Hardware remains off.

## Decision

- First mock-only active test candidate selected: group profile `"2"` / My BD Hard.
- Candidate remains mock-only.
- No implementation in this slice.
- Hardware remains off.
