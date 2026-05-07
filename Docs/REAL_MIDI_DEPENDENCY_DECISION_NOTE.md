# Real MIDI Dependency Decision Note

## 1. Purpose

Record the current dependency decision after the reviewed real MIDI import and
port safety tests and the next-phase planning gate.

This is a documentation-only decision note.

This document does not install dependencies.

This document does not import real MIDI libraries.

This document does not implement adapters, open ports, send MIDI, add active
CLI commands, add hardware behavior, or start hardware validation.

## 2. Current Clean Baseline

Current branch:

- modularize-v1.34

Current HEAD before this slice:

- 49b194f Add real MIDI next phase planning gate

Accepted safety baseline:

- 457b6be Add real MIDI import and port safety tests
- 8f9fa46 Add real MIDI import safety tests review
- 49b194f Add real MIDI next phase planning gate

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

## 3. Decision

Do not add a real MIDI dependency yet.

Do not add `mido` yet.

Do not add any real MIDI backend yet.

Do not install packages for MIDI yet.

Do not import real MIDI libraries in runtime, tests, passive CLI, or mock
modules yet.

Keep all real MIDI dependency decisions deferred until a separate adapter
boundary design and dependency review are accepted.

## 4. Rationale

The project now has closeout-protected guardrails proving passive/mock imports
and representative passive CLI paths do not import real MIDI libraries or
expose port/send/active command affordances.

Adding a real MIDI dependency before an adapter boundary exists would weaken
that safety line.

The next responsible step is to preserve the current import/port safety
baseline and decide dependency shape only after the adapter boundary is
documented, reviewed, and test-gated.

## 5. Current Dependency Position

Current dependency position:

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
this note.

## 6. Candidate Direction For Later

If the project later chooses a real MIDI library, the likely future shape is:

- keep passive CLI imports free of real MIDI dependencies
- keep real MIDI dependency isolated behind a dedicated adapter module
- keep the adapter absent from passive report/list/search/inspect/preview paths
- keep real MIDI import tests in closeout
- keep passive CLI safety tests in closeout
- prove no ports open during import
- prove no ports open during passive CLI commands
- require explicit user approval before adding the dependency

The future adapter may consider `mido` or another real MIDI library, but this
note does not choose one.

## 7. Required Tests Before Any Dependency Is Added

Before any future dependency is added, tests must prove:

- passive imports remain quiet
- passive imports do not import real MIDI libraries
- passive CLI commands do not import real MIDI libraries
- passive CLI commands do not open ports
- passive CLI commands do not send MIDI
- passive CLI does not construct sender objects
- passive CLI does not evaluate active boundary requests
- active-boundary scope remains explicitly controlled
- missing arming fails safely
- unknown and unsupported keys fail safely
- V1.34 reference remains untouched

The existing real MIDI import and passive CLI safety tests must remain in
closeout.

## 8. Required Design Before Any Dependency Is Added

Before adding any real MIDI dependency, the project needs a separate
documentation-only real MIDI adapter boundary design.

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

That future design must be reviewed before implementation.

## 9. Forbidden In This Slice

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

## 10. Preconditions Before Any Future Dependency Slice

Before any future dependency slice:

- clean Git status
- closeout passes
- V1.34 reference diff is empty
- this decision note is reviewed and accepted
- real MIDI adapter boundary design exists
- real MIDI adapter boundary design is reviewed and accepted
- import/port safety tests remain in closeout
- passive CLI remains read-only
- dependency addition is explicitly approved
- hardware remains off

## 11. Preconditions Before Hardware Validation

This note does not authorize hardware validation.

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

Analog Rytm and Analog Four remain off during this decision note.

## 12. Safe Next Options

Safe next options:

- review and accept this dependency decision note
- pause at this clean dependency decision checkpoint
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

## 13. Decision

The current decision is to defer real MIDI dependency selection.

No real MIDI dependency is added.

No `mido` dependency is added.

Real MIDI implementation remains blocked.

Hardware validation remains blocked.

The recommended next branch is a documentation-only review/acceptance gate for
this dependency decision note.

Hardware remains off.

No implementation is added in this slice.
