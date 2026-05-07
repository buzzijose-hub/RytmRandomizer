# Real MIDI Dependency Decision Review

## 1. Purpose

Review and accept `Docs/REAL_MIDI_DEPENDENCY_DECISION_NOTE.md` as the current
dependency decision checkpoint.

This is a review checkpoint only.

This document does not install dependencies.

This document does not import real MIDI libraries.

This document does not implement adapters, open ports, send MIDI, add active
CLI commands, add hardware behavior, or start hardware validation.

## 2. Current Clean Baseline

Current branch:

- modularize-v1.34

Current HEAD before this slice:

- d1a2b07 Add real MIDI dependency decision note

Accepted dependency decision:

- defer real MIDI dependency selection
- do not add `mido`
- do not add any real MIDI backend
- do not install MIDI packages
- do not edit dependency metadata for MIDI

Current phase:

- Passive/Mock Foundation Phase
- mock-first active boundary exists for test-only evaluation
- real MIDI import and port safety tests are in closeout
- real MIDI dependency selection is deferred
- no real MIDI or hardware validation started

Hardware status:

- Analog Rytm MKII off
- Analog Four MKII off
- hardware not required

## 3. Review Decision

`Docs/REAL_MIDI_DEPENDENCY_DECISION_NOTE.md` is accepted as the current real
MIDI dependency decision checkpoint.

The current decision is accepted:

- defer dependency selection
- keep `mido` absent
- keep real MIDI backend absent
- keep dependency metadata unchanged
- require a separate adapter boundary design before dependency work

This review does not authorize real MIDI implementation.

This review does not authorize adding dependencies.

This review does not authorize hardware validation.

## 4. Accepted Dependency Position

Accepted current dependency position:

- no real MIDI dependency
- no `mido`
- no `python-rtmidi`
- no port provider dependency
- no sender dependency
- no real MIDI backend
- no dependency installation
- no dependency lockfile change
- no package metadata change

Future dependency candidates may be discussed later, but none are selected by
this review.

## 5. Required Next Design

Before any dependency can be added, the project must create and review a
documentation-only real MIDI adapter boundary gate or design.

That future design must define:

- adapter module ownership
- import isolation rules
- port discovery rules
- sender construction rules
- no-import side effects
- no-port-opening import behavior
- no passive CLI dependency on real MIDI
- mockable test interfaces
- failure behavior when dependency is absent
- failure behavior when a port is unknown
- failure behavior when arming is missing

## 6. Existing Guardrails That Must Remain

These guardrails must remain in closeout:

- `=== Test: Real MIDI Import Safety ===`
- `=== Test: Real MIDI Passive CLI Safety ===`

Those tests must continue proving:

- passive imports remain quiet
- passive imports do not import real MIDI libraries
- passive CLI commands do not import real MIDI libraries
- passive CLI commands do not open ports
- passive CLI commands do not send MIDI
- passive CLI does not construct sender objects
- passive CLI does not evaluate active boundary requests
- active-boundary scope remains explicitly controlled
- V1.34 reference remains untouched

## 7. Confirmed Absent Behavior

This review confirms the project still has no:

- real MIDI dependency
- `mido`
- `python-rtmidi`
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
- profile `"4"` implementation
- profile `"3"` active-boundary support
- hardware validation

## 8. Current Active-Boundary Scope

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

## 9. Preconditions Before Any Dependency Slice

Before any future dependency slice:

- clean Git status
- closeout passes
- V1.34 reference diff is empty
- this review is committed
- real MIDI adapter boundary design exists
- real MIDI adapter boundary design is reviewed and accepted
- import/port safety tests remain in closeout
- passive CLI remains read-only
- dependency addition is explicitly approved
- hardware remains off

## 10. Preconditions Before Hardware Validation

This review does not authorize hardware validation.

Before any future hardware validation:

- all mock-only tests must pass
- all import and port safety tests must pass
- all future real MIDI boundary tests must pass
- real MIDI dependency decision must be reviewed and accepted
- real MIDI adapter implementation must be reviewed and accepted
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

- pause at this accepted dependency checkpoint
- create a documentation-only real MIDI adapter boundary gate
- return to passive/project documentation

Unsafe next moves:

- adding a real MIDI dependency
- importing mido
- opening ports
- sending MIDI
- adding active CLI commands
- wiring passive CLI to active boundary evaluation
- turning on hardware
- implementing profile `"4"` without separate approval
- adding profile `"3"` active-boundary support without separate approval

## 12. Recommendation

Prefer a documentation-only real MIDI adapter boundary gate next.

Do not implement real MIDI.

Do not add `mido`.

Do not install dependencies.

Do not open ports.

Do not add active CLI commands.

Do not turn on hardware.

## 13. Decision

The real MIDI dependency decision note is accepted.

Real MIDI dependency selection remains deferred.

Real MIDI implementation remains blocked.

Hardware validation remains blocked.

The recommended next branch is a documentation-only real MIDI adapter boundary
gate.

Hardware remains off.

No implementation is added in this slice.

## 14. Adapter Boundary Gate

The real MIDI adapter boundary gate now lives in:

- `Docs/REAL_MIDI_ADAPTER_BOUNDARY_GATE.md`

The gate establishes the planning checkpoint before any real MIDI adapter
boundary design or implementation. It defines required future adapter design
topics, import isolation rules, port boundary rules, sender boundary rules,
and tests required before adapter implementation.

The gate adds no implementation, tests, runtime modules, real MIDI
dependencies, port opening, MIDI sending, active CLI commands, dispatch,
command execution, scene execution, hardware behavior, profile `"4"`
implementation, profile `"3"` active-boundary support, hardware validation, or
hardware-on authorization.

## 15. Adapter Boundary Gate Review

The real MIDI adapter boundary gate review now lives in:

- `Docs/REAL_MIDI_ADAPTER_BOUNDARY_GATE_REVIEW.md`

The review accepts:

- `Docs/REAL_MIDI_ADAPTER_BOUNDARY_GATE.md`
- 75d25c5 Add real MIDI adapter boundary gate

The review accepts the adapter boundary gate as the current planning checkpoint
before any documentation-only real MIDI adapter boundary design.

The review keeps real MIDI adapter implementation blocked, real MIDI
dependency selection deferred, hardware validation blocked, passive CLI
read-only, profile `"3"` unsupported by the active boundary, profile `"4"`
parked and unsupported, and hardware off.

The review adds no implementation, tests, runtime modules, real MIDI
dependencies, port opening, MIDI sending, active CLI commands, dispatch,
command execution, scene execution, hardware behavior, profile `"4"`
implementation, profile `"3"` active-boundary support, hardware validation, or
hardware-on authorization.
