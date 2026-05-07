# Real MIDI Adapter First Implementation Planning Gate

## 1. Purpose

Establish the planning gate before any first real MIDI adapter implementation
design/spec or implementation plan.

This document allows only future documentation-only planning.

This document does not implement an adapter.

This document does not add tests.

This document does not add dependencies, import real MIDI libraries, open
ports, send MIDI, add active CLI commands, add hardware behavior, or start
hardware validation.

## 2. Current Clean Baseline

Current branch:

- modularize-v1.34

Current HEAD before this slice:

- f705eae Add real MIDI adapter boundary safety tests review

Current phase:

- Passive/Mock Foundation Phase
- mock-first active boundary exists for test-only evaluation
- real MIDI adapter boundary design is reviewed and accepted
- real MIDI adapter-specific test plan is reviewed and accepted
- real MIDI adapter boundary safety tests are implemented and reviewed
- first adapter implementation planning gate is now being documented

Accepted safety baseline:

- real MIDI import safety tests are in closeout
- real MIDI passive CLI safety tests are in closeout
- real MIDI adapter boundary safety tests are in closeout
- real MIDI dependency selection remains deferred
- `mido` remains absent
- no real MIDI backend exists
- no real MIDI adapter module exists
- no hardware validation has started

Hardware status:

- Analog Rytm MKII off
- Analog Four MKII off
- hardware not required

## 3. Gate Decision

This gate permits a future documentation-only first adapter implementation
design/spec.

This gate does not permit implementation.

This gate does not permit creating `rytm_randomizer/real_midi_adapter.py`.

This gate does not permit adding a real MIDI dependency.

This gate does not permit adding active CLI commands.

This gate does not permit opening ports, sending MIDI, or turning hardware on.

## 4. Accepted Inputs To This Gate

The accepted inputs are:

- `Docs/REAL_MIDI_ADAPTER_BOUNDARY_GATE.md`
- `Docs/REAL_MIDI_ADAPTER_BOUNDARY_GATE_REVIEW.md`
- `Docs/REAL_MIDI_ADAPTER_BOUNDARY_DESIGN.md`
- `Docs/REAL_MIDI_ADAPTER_BOUNDARY_DESIGN_REVIEW.md`
- `Docs/REAL_MIDI_ADAPTER_SPECIFIC_TEST_PLAN.md`
- `Docs/REAL_MIDI_ADAPTER_SPECIFIC_TEST_PLAN_REVIEW.md`
- `Docs/REAL_MIDI_ADAPTER_BOUNDARY_SAFETY_TESTS_CHECKPOINT.md`
- `Docs/REAL_MIDI_ADAPTER_BOUNDARY_SAFETY_TESTS_CHECKPOINT_REVIEW.md`

The accepted tests-only guardrails are:

- `tests/test_real_midi_import_safety.py`
- `tests/test_real_midi_passive_cli_safety.py`
- `tests/test_real_midi_adapter_boundary.py`

The accepted closeout labels are:

- `=== Test: Real MIDI Import Safety ===`
- `=== Test: Real MIDI Passive CLI Safety ===`
- `=== Test: Real MIDI Adapter Boundary ===`

## 5. Required Shape Of Future First Adapter Planning

Any future first adapter implementation design/spec must remain
documentation-only.

It must define:

- future module ownership
- future dependency isolation
- future lazy import behavior
- future port provider boundary
- future sender boundary
- fake-provider-only test path
- dependency-absent safe failure behavior
- passive CLI separation
- active-boundary scope limits
- forbidden early active scope
- V1.34 reference protection
- future implementation stop conditions

It must not implement those pieces.

## 6. Future Implementation Scope Discussion

A future design/spec may discuss these names as design concepts only:

- `rytm_randomizer/real_midi_adapter.py`
- `RealMidiDependencyError`
- `RealMidiPortProvider`
- `RealMidiSender`
- `RealMidiSendResult`
- `build_real_midi_sender`

Those names are not implemented by this gate.

The future implementation should remain narrow:

- dependency import isolation only
- provider/sender boundary only
- safe failure when dependency is absent
- fake-provider tests before real dependency use
- no passive CLI integration
- no active CLI command
- no hardware validation

## 7. Required Tests Before Any Adapter Implementation

Before any adapter implementation is allowed, tests must prove:

- passive imports do not load real MIDI dependencies
- passive CLI commands do not load adapter or real MIDI dependencies
- dependency absence fails safely
- fake providers can be used without real ports
- no ports open during unit tests
- no MIDI is sent during unit tests
- passive CLI remains read-only
- active-boundary scope remains limited to group profile `"2"` / My BD Hard
- group profile `"3"` / My BD Classic remains unsupported by the active
  boundary
- group profile `"4"` / My BD Acoustic remains parked and unsupported
- V1.34 reference diff remains empty

The existing adapter boundary safety tests must remain in closeout.

## 8. Confirmed Absent Behavior

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

## 9. Preconditions Before Future First Adapter Design/Spec

Before any first adapter implementation design/spec begins:

- clean Git status
- closeout passes
- V1.34 reference diff is empty
- this planning gate is reviewed and accepted
- real MIDI adapter boundary safety tests remain in closeout
- passive CLI remains read-only
- `mido` remains absent
- no real MIDI dependency is installed
- no hardware required
- hardware remains off

## 10. Preconditions Before Future Adapter Code

This gate does not authorize adapter code.

Before any future adapter code:

- first adapter implementation design/spec must exist and be reviewed
- first adapter implementation plan must exist and be reviewed
- fake-provider-only tests must exist
- dependency-absent safe-failure tests must exist
- passive CLI regression tests must remain green
- active-boundary scope guard tests must remain green
- closeout must pass
- V1.34 reference diff must be empty
- dependency addition must remain separately approved
- hardware must remain off

## 11. Preconditions Before Future Dependency Selection

This gate does not authorize selecting or installing a real MIDI dependency.

Before any future dependency selection:

- adapter design/spec must exist and be reviewed
- adapter implementation plan must exist and be reviewed
- dependency decision note must be revisited
- dependency decision review must be accepted
- package metadata changes must be explicitly approved
- unit tests must still avoid real ports
- hardware must remain off

## 12. Preconditions Before Future Hardware Validation

This gate does not authorize hardware validation.

Before any future hardware validation:

- all mock-only tests must pass
- all real MIDI import and port safety tests must pass
- all adapter boundary safety tests must pass
- adapter implementation must be reviewed and accepted
- dependency decision must be revisited and accepted
- exact target device must be selected
- exact MIDI output port must be confirmed
- exact command/pad/channel scope must be confirmed
- current Analog Rytm kit/project must be saved
- monitoring volume must be lowered
- hardware validation checklist must be accepted
- user must explicitly confirm hardware validation is starting

Analog Rytm and Analog Four remain off during this planning gate.

## 13. Safe Next Options

Safe next options:

- review and accept this planning gate
- pause at this clean planning checkpoint
- return to passive/project documentation

Unsafe next moves:

- adding real MIDI dependencies
- creating `rytm_randomizer/real_midi_adapter.py`
- importing real MIDI libraries
- opening ports
- sending MIDI
- adding active CLI commands
- turning on hardware
- implementing profile `"4"`
- adding profile `"3"` active-boundary support

## 14. Recommendation

Prefer a documentation-only review/acceptance gate for this planning gate next.

After that, create a documentation-only first adapter implementation
design/spec.

Do not implement real MIDI yet.

Do not add `mido`.

Do not install dependencies.

Do not open ports.

Do not add active CLI commands.

Do not turn on hardware.

## 15. Review Gate

The review gate for this planning checkpoint is:

- `Docs/REAL_MIDI_ADAPTER_FIRST_IMPLEMENTATION_PLANNING_GATE_REVIEW.md`

The review accepts this planning gate as the current checkpoint before any
documentation-only first adapter implementation design/spec.

The review does not authorize creating `rytm_randomizer/real_midi_adapter.py`,
selecting or installing a real MIDI dependency, package metadata changes, port
opening, MIDI sending, active CLI commands, hardware behavior, hardware
validation, profile `"4"` implementation, or profile `"3"` active-boundary
support.

## 16. First Adapter Implementation Design Spec

The first adapter implementation design/spec now lives in:

- `Docs/REAL_MIDI_ADAPTER_FIRST_IMPLEMENTATION_DESIGN_SPEC.md`

The design/spec documents the future adapter shape at planning level only:
future module ownership, dependency isolation, lazy import behavior, port
provider boundary, sender boundary, dependency-absent safe failure, passive CLI
separation, active-boundary scope limits, fake-provider-only test
requirements, V1.34 reference protection, and stop conditions.

The design/spec does not authorize creating `rytm_randomizer/real_midi_adapter.py`,
selecting or installing a real MIDI dependency, package metadata changes, port
opening, MIDI sending, active CLI commands, hardware behavior, hardware
validation, profile `"4"` implementation, or profile `"3"` active-boundary
support.

## 17. Decision

The first adapter implementation planning gate is established.

Adapter implementation remains blocked.

Real MIDI dependency selection remains deferred.

Hardware validation remains blocked.

Hardware remains off.

No implementation is added in this slice.
