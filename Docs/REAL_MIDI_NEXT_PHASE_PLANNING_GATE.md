# Real MIDI Next Phase Planning Gate

## 1. Purpose

Define the safe next-phase decision gate after the completed and reviewed real
MIDI import and port safety tests.

This is a planning checkpoint only.

This document does not implement tests.

This document does not add runtime behavior.

This document does not authorize real MIDI, port opening, MIDI sending, active
CLI commands, hardware behavior, or hardware validation.

## 2. Current Clean Baseline

Current branch:

- modularize-v1.34

Current HEAD before this slice:

- 8f9fa46 Add real MIDI import safety tests review

Accepted safety baseline:

- 457b6be Add real MIDI import and port safety tests
- 3ad0939 Update checkpoint after real MIDI import safety tests
- 8f9fa46 Add real MIDI import safety tests review

Current phase:

- Passive/Mock Foundation Phase
- mock-first active boundary exists for test-only evaluation
- real MIDI import and port safety tests are in closeout
- real MIDI import and port safety tests are reviewed and accepted
- no real MIDI or hardware validation started

Hardware status:

- Analog Rytm MKII off
- Analog Four MKII off
- hardware not required

## 3. What Is Accepted Now

The project currently accepts:

- passive CLI report/list/search/inspect/preview behavior
- passive `mock-mapper-report`
- passive `active-boundary-report`
- test-only mock MIDI scaffold
- test-only mock message mapper
- mock-first active boundary for profile `"2"` only
- real MIDI import safety tests
- real MIDI passive CLI safety tests
- closeout coverage for those safety tests

The real MIDI import and passive CLI safety tests are now part of full
closeout.

## 4. What Has Been Proven

The current closeout-protected tests prove:

- passive/mock imports print nothing
- passive/mock imports do not import real MIDI libraries
- passive/mock source files expose no real MIDI affordances
- representative passive CLI commands do not import real MIDI libraries
- passive CLI source does not construct sender objects
- passive CLI source does not evaluate active boundary requests
- passive CLI help exposes no active or port commands
- passive report outputs expose no active or port commands
- active-boundary scope remains profile `"2"` only
- profile `"3"` remains unsupported by the active boundary
- profile `"4"` remains parked and unsupported
- V1.34 reference remains untouched

## 5. What Remains Blocked

Still blocked:

- real MIDI implementation
- mido dependency
- MIDI port opening
- MIDI sending
- hardware detection
- hardware send
- active CLI commands
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
- profile `"4"` implementation
- profile `"3"` active-boundary support
- hardware validation

## 6. Current Active-Boundary Scope

Accepted active-boundary scope:

- group profile `"2"` / My BD Hard

Unsupported active-boundary scope:

- group profile `"3"` / My BD Classic
- group profile `"4"` / My BD Acoustic
- scenes
- commands
- unknown keys
- unsupported source kinds

Profile `"4"` remains parked and unsupported.

Profile `"3"` remains mock-mapper/report scope only and is not
active-boundary supported.

## 7. Safe Next Branch Options

Safe next options:

- Option A: pause at this clean safety checkpoint
- Option B: return to passive/project documentation
- Option C: create a documentation-only real MIDI dependency decision note
- Option D: create a documentation-only real MIDI adapter boundary gate
- Option E: create a documentation-only hardware validation preconditions gate

Any implementation after this point must be separately planned, reviewed, and
approved.

## 8. Recommended Next Branch

Prefer Option C next:

- create a documentation-only real MIDI dependency decision note

That note should decide whether the future project should keep real MIDI
dependency choice deferred, evaluate `mido` later, or define an adapter shape
without installing or importing any real MIDI library yet.

Do not implement real MIDI in that note.

Do not install dependencies in that note.

Do not open ports in that note.

Do not turn on hardware in that note.

## 9. Preconditions Before Any Future Implementation Slice

Before any future implementation slice:

- clean Git status
- closeout passes
- V1.34 reference diff is empty
- implementation scope is separately documented
- implementation scope is separately reviewed
- passive CLI remains read-only
- profile `"3"` active-boundary support remains blocked unless separately
  approved
- profile `"4"` implementation remains blocked unless separately approved
- no hardware is required
- no hardware is turned on

## 10. Preconditions Before Any Real MIDI Dependency

Before adding any real MIDI dependency:

- dependency decision note must be written
- dependency decision note must be reviewed
- import safety tests must remain in closeout
- passive CLI safety tests must remain in closeout
- real MIDI imports must be isolated away from passive imports
- passive CLI must remain read-only
- no ports may open during import
- no ports may open during passive CLI commands
- no hardware may be required
- explicit user approval must be given

## 11. Preconditions Before Hardware Validation

This gate does not authorize hardware validation.

Before any future hardware validation:

- all mock-only tests must pass
- all import and port safety tests must pass
- all future real MIDI boundary tests must pass
- real MIDI adapter implementation must be reviewed and accepted
- exact target device must be selected
- exact MIDI output port must be confirmed
- exact command/pad/channel scope must be confirmed
- current Analog Rytm kit/project must be saved
- monitoring volume must be lowered
- hardware validation checklist must be accepted
- user must explicitly confirm hardware validation is starting

Analog Rytm and Analog Four remain off during this planning gate.

## 12. Stop Conditions

Stop immediately if any next slice would require:

- importing mido
- adding a real MIDI dependency
- opening a port
- sending MIDI
- adding active CLI commands
- wiring passive CLI to active boundary evaluation
- changing active-boundary candidate scope
- implementing profile `"4"`
- adding profile `"3"` active-boundary support
- editing `rytm_hybrid_randomizer_v134.py`
- turning on hardware

## 13. Decision

The next phase remains planning-only.

Real MIDI implementation remains blocked.

Hardware validation remains blocked.

The recommended next branch is a documentation-only real MIDI dependency
decision note.

Hardware remains off.

No implementation is added in this slice.
