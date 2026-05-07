# Real MIDI Boundary Planning Gate

## 1. Purpose

Define the gate before any real MIDI boundary planning document may be written.

This document does not design real MIDI implementation.

This document does not authorize real MIDI implementation.

This document does not authorize opening ports, sending MIDI, adding active CLI
commands, or turning hardware on.

## 2. Current Clean Baseline

Current branch:

- modularize-v1.34

Current HEAD before this slice:

- 3f67c9f Add project-level roadmap update review

Current phase:

- Passive/Mock Foundation Phase
- project-level roadmap update accepted
- mock-first active boundary safety baseline accepted
- real MIDI remains absent
- no hardware validation started

Hardware status:

- Analog Rytm MKII off
- Analog Four MKII off
- hardware not required

## 3. Current Accepted Baseline

The current accepted baseline includes:

- passive CLI visibility
- mock MIDI scaffold
- mock message mapper and report
- mock mapper report CLI preview
- mock-only active candidate tests
- mock-first active boundary for group profile `"2"` / My BD Hard
- active boundary safety tests
- read-only active boundary report
- `active-boundary-report` passive CLI preview
- active boundary safety progress report and review
- project-level roadmap update and review

## 4. Current Scope

Current mock mapper support:

- group profile `"2"` / My BD Hard
- group profile `"3"` / My BD Classic

Current active-boundary support:

- group profile `"2"` / My BD Hard only

Unsupported by the active boundary:

- group profile `"3"` / My BD Classic
- scenes
- commands

Parked or unsupported:

- group profile `"4"` / My BD Acoustic
- real hardware paths

## 5. Confirmed Absent Behavior

This planning gate confirms there is still no:

- real MIDI
- mido
- MIDI port opening
- MIDI sending
- hardware detection
- hardware send
- active CLI command
- active execution
- passive CLI active-boundary evaluation
- passive CLI construction of `MockMidiSender`
- dispatch
- command execution
- scene execution
- hardware behavior
- hardware mutation
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
- profile `"3"` active-boundary support

## 6. What A Future Real MIDI Boundary Plan May Cover

A future documentation-only real MIDI boundary plan may define:

- where a real MIDI adapter would live conceptually
- what high-level code must never import directly
- what interface would remain mockable
- how passive CLI commands stay read-only
- how active behavior would stay behind explicit arming
- how real MIDI imports would be isolated
- how port discovery would stay separate from passive imports
- how hardware validation would remain a later phase
- what tests must exist before implementation
- what operator checklist would be required before hardware is turned on

That future plan must remain documentation-only unless a separate
implementation gate is explicitly approved later.

## 7. What The Future Plan Must Not Authorize

The future real MIDI boundary plan must not authorize:

- implementation
- real MIDI imports
- mido dependency
- MIDI port opening
- MIDI sending
- hardware detection
- hardware send
- active CLI commands
- dispatch
- command execution
- scene execution
- hardware mutation
- SysEx
- GUI/capture
- Analog Four support
- Pads 5-12 support
- machine/profile expansion
- profile `"4"` implementation
- profile `"3"` active-boundary support
- hardware validation

## 8. Preconditions Before Future Real MIDI Boundary Planning

Before writing a future real MIDI boundary plan:

- Git status must be clean
- closeout must pass
- V1.34 reference diff must be empty
- project-level roadmap update review must remain accepted
- passive CLI must remain read-only
- mock-first active boundary safety baseline must remain accepted
- hardware must remain off
- the plan must stay documentation-only

## 9. Preconditions Before Any Later Real MIDI Implementation

This gate does not authorize implementation.

Before any later real MIDI implementation could be considered, the project
would need:

- accepted real MIDI boundary plan
- accepted implementation design/spec
- accepted test plan
- tests proving passive commands do not open ports
- tests proving passive commands do not send MIDI
- tests proving missing arming fails safely
- tests proving unknown and unsupported keys fail safely
- a mockable MIDI adapter boundary
- clean closeout
- clean Git status
- empty V1.34 reference diff
- explicit user approval

## 10. Preconditions Before Hardware Validation

This gate does not authorize hardware validation.

Before any hardware validation could be considered, the project would need:

- all real MIDI boundary tests passing
- real MIDI adapter implementation reviewed and accepted
- exact target device selected
- exact MIDI output port confirmed
- exact command/pad/channel scope confirmed
- current Analog Rytm kit/project saved
- monitoring volume lowered
- hardware validation checklist accepted
- explicit user confirmation that hardware validation is starting

Analog Rytm and Analog Four remain off during this gate.

## 11. Safe Next Options

Safe next options:

- review and accept this planning gate
- pause at this clean gate
- return to passive/project documentation
- create a documentation-only real MIDI boundary plan after this gate is
  accepted

Unsafe next moves:

- adding real MIDI
- importing mido
- opening ports
- sending MIDI
- adding active CLI commands
- wiring passive CLI to active boundary evaluation
- turning on hardware
- implementing profile `"4"` without separate approval
- adding profile `"3"` active-boundary support without separate approval

## 12. Recommendation

Review and accept this planning gate before writing any real MIDI boundary
plan.

Do not add real MIDI.

Do not open ports.

Do not add active CLI commands.

Do not turn on hardware.

## 13. Decision

Real MIDI boundary planning is gated.

Only a future documentation-only real MIDI boundary plan may follow from this
gate after review.

Hardware remains off.

No implementation is added in this slice.
