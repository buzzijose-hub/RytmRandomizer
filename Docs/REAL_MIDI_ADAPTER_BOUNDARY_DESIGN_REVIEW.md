# Real MIDI Adapter Boundary Design Review

## 1. Purpose

Review and accept `Docs/REAL_MIDI_ADAPTER_BOUNDARY_DESIGN.md` as the current
planning design for a future real MIDI adapter boundary.

This is a review checkpoint only.

This document does not implement an adapter.

This document does not install dependencies.

This document does not import real MIDI libraries, open ports, send MIDI, add
active CLI commands, add hardware behavior, or start hardware validation.

## 2. Current Clean Baseline

Current branch:

- modularize-v1.34

Current HEAD before this slice:

- de313fe Add real MIDI adapter boundary design

Current phase:

- Passive/Mock Foundation Phase
- mock-first active boundary exists for test-only evaluation
- real MIDI dependency decision is reviewed and accepted
- real MIDI adapter boundary gate is reviewed and accepted
- real MIDI adapter boundary design has been documented
- real MIDI adapter boundary design is now being reviewed

Accepted safety baseline:

- real MIDI import safety tests are in closeout
- real MIDI passive CLI safety tests are in closeout
- real MIDI dependency selection remains deferred
- `mido` remains absent
- no real MIDI backend exists
- no real MIDI adapter module exists
- no hardware validation has started

Hardware status:

- Analog Rytm MKII off
- Analog Four MKII off
- hardware not required

## 3. Review Decision

`Docs/REAL_MIDI_ADAPTER_BOUNDARY_DESIGN.md` is accepted as the current
planning design for the future real MIDI adapter boundary.

The design remains documentation-only.

The design does not authorize implementation by itself.

The design does not authorize adding a real MIDI dependency by itself.

The design does not authorize turning hardware on by itself.

## 4. Accepted Design Concepts

The review accepts these design concepts:

- future real MIDI behavior must live behind a narrow adapter boundary
- future adapter ownership should prefer one small isolated module first
- `rytm_randomizer/real_midi_adapter.py` is an acceptable future placeholder
  name for design discussion
- real MIDI imports must be lazy and isolated
- real MIDI dependency selection remains deferred
- future port discovery must be explicit and isolated
- future sender construction must be explicit and guarded
- passive CLI commands must remain read-only
- passive CLI commands must not import real MIDI libraries
- passive CLI commands must not open ports
- passive CLI commands must not send MIDI
- adapter failure behavior must be deterministic and safe
- adapter-specific tests must be planned before implementation
- hardware validation requires a later explicit checklist and approval
- active-boundary scope remains limited to group profile `"2"` / My BD Hard
- profile `"3"` remains unsupported by the active boundary
- profile `"4"` remains parked and unsupported

## 5. Confirmed Absent Behavior

Confirmed absent:

- no `mido`
- no real MIDI dependency
- no real MIDI adapter module
- no real MIDI backend
- no MIDI port opening
- no MIDI sending
- no active CLI command
- no execute-command
- no send-command
- no hardware-test
- no dispatch
- no command execution
- no scene execution
- no hardware behavior
- no hardware detection
- no SysEx
- no GUI/capture
- no Analog Four support
- no Pads 5-12 support
- no machine/profile expansion
- no profile `"4"` implementation
- no profile `"3"` active-boundary support
- no hardware validation

## 6. Passive Commands Remain Read-Only

These passive commands remain read-only and must not reach real MIDI adapter
behavior:

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
- active-boundary-report

## 7. Accepted Future Test Planning Requirements

A future adapter-specific test plan must be documentation-only first.

That future plan should define tests for:

- passive imports not importing real MIDI libraries
- passive CLI commands not importing real MIDI libraries
- passive CLI commands not opening ports
- passive CLI commands not sending MIDI
- future adapter import not opening ports
- missing dependency safe failure
- fake port provider behavior
- unknown port safe failure
- missing arming safe failure
- missing dry-run confirmation safe failure
- unsupported key safe failure
- profile `"3"` remaining unsupported by the active boundary
- profile `"4"` remaining parked and unsupported
- V1.34 reference remaining untouched

The future test plan must not implement tests by itself.

## 8. Preconditions Before Future Adapter-Specific Test Plan

Before a documentation-only adapter-specific test plan begins:

- clean Git status
- closeout passes
- V1.34 reference diff is empty
- real MIDI dependency decision review is accepted
- real MIDI adapter boundary gate review is accepted
- real MIDI adapter boundary design review is accepted
- import safety tests remain in closeout
- passive CLI safety tests remain in closeout
- passive CLI remains read-only
- `mido` remains absent
- no real MIDI dependency is installed
- no hardware required
- hardware remains off

## 9. Preconditions Before Future Adapter Implementation

This review does not authorize adapter implementation.

Before any future adapter implementation:

- adapter-specific test plan exists
- adapter-specific test plan is reviewed and accepted
- adapter-specific tests are implemented with fake providers only
- adapter-specific tests are reviewed and accepted
- dependency addition is separately approved
- implementation scope is separately approved
- closeout passes
- V1.34 reference diff is empty
- passive commands remain proven passive
- hardware remains off

## 10. Preconditions Before Future Hardware Validation

This review does not authorize hardware validation.

Before any future hardware validation:

- all mock-only tests must pass
- all import and port safety tests must pass
- all future adapter tests must pass
- adapter implementation must be reviewed and accepted
- exact target device must be selected
- exact MIDI output port must be confirmed
- exact command/pad/channel scope must be confirmed
- current Analog Rytm kit/project must be saved
- monitoring volume must be lowered
- hardware validation checklist must be accepted
- user must explicitly confirm hardware validation is starting

Analog Rytm and Analog Four remain off during this review.

## 11. Safe Next Options

Safe next options:

- pause at this accepted adapter boundary design checkpoint
- create a documentation-only adapter-specific test plan
- return to passive/project documentation

Unsafe next moves:

- adding a real MIDI dependency
- adding `mido`
- importing real MIDI libraries
- opening ports
- sending MIDI
- adding active CLI commands
- wiring passive CLI to active boundary evaluation
- starting hardware validation
- turning on hardware
- implementing profile `"4"` without separate approval
- adding profile `"3"` active-boundary support without separate approval

## 12. Recommendation

Prefer a documentation-only real MIDI adapter-specific test plan next.

That future test plan should define tests with fake providers only and should
keep all real MIDI dependencies, port opening, MIDI sending, active CLI
commands, and hardware validation blocked.

Do not implement real MIDI.

Do not add `mido`.

Do not install dependencies.

Do not open ports.

Do not add active CLI commands.

Do not turn on hardware.

## 13. Decision

The real MIDI adapter boundary design is accepted for planning.

Real MIDI adapter-specific test planning may be written next as
documentation-only work.

Adapter implementation remains blocked.

Real MIDI dependency selection remains deferred.

Hardware validation remains blocked.

Hardware remains off.

No implementation is added in this slice.

## 14. Adapter-Specific Test Plan

The real MIDI adapter-specific test plan now lives in:

- `Docs/REAL_MIDI_ADAPTER_SPECIFIC_TEST_PLAN.md`

The plan defines future adapter-specific tests that must exist before any real
MIDI adapter implementation. It covers future test ownership,
fake-provider-only behavior, adapter import safety, dependency absence,
unknown port safe failure, sender construction guards, passive CLI regression
coverage, active-boundary scope guards, V1.34 reference protection, future
closeout integration, and implementation sequencing.

The plan adds no implementation, tests, runtime modules, real MIDI
dependencies, port opening, MIDI sending, active CLI commands, dispatch,
command execution, scene execution, hardware behavior, profile `"4"`
implementation, profile `"3"` active-boundary support, hardware validation, or
hardware-on authorization.
