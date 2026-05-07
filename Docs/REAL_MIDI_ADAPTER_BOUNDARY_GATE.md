# Real MIDI Adapter Boundary Gate

## 1. Purpose

Establish the planning gate before any real MIDI adapter boundary design or
implementation work.

This is a documentation-only gate.

This document does not implement an adapter.

This document does not install dependencies.

This document does not import real MIDI libraries, open ports, send MIDI, add
active CLI commands, add hardware behavior, or start hardware validation.

## 2. Current Clean Baseline

Current branch:

- modularize-v1.34

Current HEAD before this slice:

- f9bb383 Add real MIDI dependency decision review

Accepted safety baseline:

- real MIDI import safety tests are in closeout
- real MIDI passive CLI safety tests are in closeout
- real MIDI dependency selection is deferred
- `mido` remains absent
- no real MIDI backend exists
- no hardware validation has started

Current phase:

- Passive/Mock Foundation Phase
- mock-first active boundary exists for test-only evaluation
- real MIDI dependency decision is reviewed and accepted
- real MIDI adapter boundary gate is now being documented

Hardware status:

- Analog Rytm MKII off
- Analog Four MKII off
- hardware not required

## 3. Gate Decision

A real MIDI adapter boundary design may be written next.

That future design must remain documentation-only until separately reviewed.

This gate does not authorize:

- adding `mido`
- adding another real MIDI dependency
- implementing an adapter
- opening ports
- sending MIDI
- adding active CLI commands
- starting hardware validation

## 4. Required Future Adapter Design Topics

The future real MIDI adapter boundary design must define:

- adapter module ownership
- import isolation rules
- dependency isolation rules
- port discovery rules
- sender construction rules
- no-import side effects
- no-port-opening import behavior
- passive CLI separation
- active boundary separation
- mockable test interfaces
- failure behavior when dependency is absent
- failure behavior when port discovery fails
- failure behavior when a port is unknown
- failure behavior when arming is missing
- failure behavior when dry-run confirmation is missing
- V1.34 reference protection
- closeout integration expectations

## 5. Proposed Future Module Ownership

Future design may discuss module names such as:

- `rytm_randomizer/real_midi_adapter.py`
- `rytm_randomizer/midi_ports.py`
- `rytm_randomizer/hardware_sender.py`

These names are design placeholders only.

No module is created by this gate.

No module name is accepted for implementation by this gate.

The future design should prefer the smallest possible boundary and should keep
passive modules free of real MIDI imports.

## 6. Import Isolation Requirement

Any future real MIDI dependency must be isolated away from:

- `rytm_randomizer.cli`
- `rytm_randomizer.mock_midi`
- `rytm_randomizer.mock_message_mapper`
- `rytm_randomizer.mock_mapper_report`
- `rytm_randomizer.active_boundary`
- `rytm_randomizer.active_boundary_report`
- passive registry/report/lookup modules

Passive imports must remain quiet.

Passive imports must not import real MIDI libraries.

Passive CLI commands must not import real MIDI libraries.

## 7. Port Boundary Requirement

Any future port provider must be isolated behind an explicit adapter boundary.

Future port discovery must not happen:

- during import
- during passive CLI commands
- during report/list/search/inspect/preview commands
- during `mock-mapper-report`
- during `active-boundary-report`
- during mock-only tests

Future port discovery must require explicit active/hardware-validation intent
and separate approval.

## 8. Sender Boundary Requirement

Any future real sender must be isolated from:

- passive CLI
- passive registry/report modules
- mock MIDI scaffold
- mock message mapper
- mock mapper report
- active boundary report

Future sender construction must not happen during passive commands.

Future sender construction must not happen during import.

Future sender construction must require explicit active/hardware-validation
intent, arming, dry-run confirmation, and port selection.

## 9. Tests Required Before Any Adapter Implementation

Before any adapter implementation:

- real MIDI import safety tests must remain in closeout
- real MIDI passive CLI safety tests must remain in closeout
- tests must prove passive imports do not import real MIDI libraries
- tests must prove passive CLI commands do not import real MIDI libraries
- tests must prove passive CLI commands do not open ports
- tests must prove passive CLI commands do not send MIDI
- tests must prove missing arming fails safely
- tests must prove missing dry-run confirmation fails safely
- tests must prove unknown and unsupported keys fail safely
- tests must prove V1.34 reference remains untouched

Additional adapter-specific tests must be designed before implementation.

## 10. Current Accepted Active-Boundary Scope

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

## 11. Forbidden In This Slice

This slice forbids:

- adding `mido`
- adding any real MIDI dependency
- editing package metadata for MIDI
- editing dependency lockfiles for MIDI
- importing real MIDI libraries
- opening MIDI ports
- sending MIDI
- detecting hardware
- adding active CLI commands
- wiring passive CLI to active boundary evaluation
- changing active-boundary scope
- implementing profile `"4"`
- adding profile `"3"` active-boundary support
- editing `rytm_hybrid_randomizer_v134.py`
- turning on hardware

## 12. Preconditions Before Any Future Adapter Design

Before writing a future adapter boundary design:

- clean Git status
- closeout passes
- V1.34 reference diff is empty
- this gate is reviewed and accepted
- dependency decision remains accepted
- import/port safety tests remain in closeout
- passive CLI remains read-only
- hardware remains off

## 13. Preconditions Before Any Future Adapter Implementation

Before any future adapter implementation:

- real MIDI adapter boundary design exists
- real MIDI adapter boundary design is reviewed and accepted
- adapter-specific test plan exists
- adapter-specific test plan is reviewed and accepted
- implementation scope is separately approved
- dependency addition is separately approved
- closeout passes
- V1.34 reference diff is empty
- hardware remains off

## 14. Preconditions Before Hardware Validation

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

Analog Rytm and Analog Four remain off during this gate.

## 15. Safe Next Options

Safe next options:

- review and accept this adapter boundary gate
- pause at this clean adapter planning checkpoint
- create a documentation-only real MIDI adapter boundary design
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

## 16. Recommendation

Prefer a documentation-only review/acceptance gate for this adapter boundary
gate next.

After that, create a documentation-only real MIDI adapter boundary design.

Do not implement real MIDI.

Do not add `mido`.

Do not install dependencies.

Do not open ports.

Do not add active CLI commands.

Do not turn on hardware.

## 17. Decision

The real MIDI adapter boundary remains planning-only.

Adapter design may be planned next after this gate is reviewed and accepted.

Adapter implementation remains blocked.

Real MIDI dependency selection remains deferred.

Hardware validation remains blocked.

Hardware remains off.

No implementation is added in this slice.

## 18. Review Gate

This gate is reviewed and accepted in:

- `Docs/REAL_MIDI_ADAPTER_BOUNDARY_GATE_REVIEW.md`

The review accepts this gate as the current planning checkpoint before any
documentation-only real MIDI adapter boundary design.

The review does not authorize real MIDI dependency installation, adapter
implementation, port opening, MIDI sending, active CLI commands, hardware
behavior, hardware validation, or turning hardware on.

## 19. Adapter Boundary Design

The documentation-only real MIDI adapter boundary design now lives in:

- `Docs/REAL_MIDI_ADAPTER_BOUNDARY_DESIGN.md`

The design expands this gate into planning-level adapter ownership, import
isolation, dependency isolation, port provider boundary, sender boundary,
passive CLI separation, active-boundary scope limits, safe failure behavior,
required future tests, implementation sequencing, and hardware validation
preconditions.

The design does not authorize real MIDI dependency installation, adapter
implementation, port opening, MIDI sending, active CLI commands, hardware
behavior, hardware validation, or turning hardware on.
