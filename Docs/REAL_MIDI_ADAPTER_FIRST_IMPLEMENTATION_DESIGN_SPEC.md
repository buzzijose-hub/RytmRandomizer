# Real MIDI Adapter First Implementation Design Spec

## 1. Purpose

Define the future first implementation shape for a real MIDI adapter boundary.

This is a design/spec document only.

This document does not implement an adapter.

This document does not add tests.

This document does not add dependencies, import real MIDI libraries, open
ports, send MIDI, add active CLI commands, add hardware behavior, or start
hardware validation.

## 2. Current Clean Baseline

Current branch:

- modularize-v1.34

Current HEAD before this slice:

- cdbf58a Add real MIDI adapter first implementation planning gate review

Current phase:

- Passive/Mock Foundation Phase
- mock-first active boundary exists for test-only evaluation
- real MIDI adapter boundary safety tests are in closeout
- first adapter implementation planning gate is reviewed and accepted
- first adapter implementation design/spec is now being documented

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

## 3. Design Decision

The first real MIDI adapter implementation, if separately approved later,
should be a narrow adapter boundary only.

It should not be an active feature.

It should not add CLI execution.

It should not connect passive CLI commands to hardware.

It should not select or install a real MIDI dependency in the same step unless
a separate dependency decision is accepted.

The first adapter implementation should prove safe boundaries before any real
hardware use:

- dependency import isolation
- dependency-absent safe failure
- fake-provider-only tests
- no passive import side effects
- no passive CLI port opening
- no passive CLI MIDI sending

## 4. Future Module Ownership

The future adapter boundary may live in:

- `rytm_randomizer/real_midi_adapter.py`

That file does not exist yet.

The future module should own only real MIDI adapter concerns:

- dependency loading boundary
- port provider boundary
- sender boundary
- safe failure types/results
- conversion from approved mock message data into future backend send calls

It should not own:

- passive CLI commands
- active CLI commands
- command dispatch
- scene execution
- group profile metadata
- mock message mapping
- mock-first active boundary decisions
- hardware validation scripts

## 5. Dependency Isolation

Real MIDI dependency selection remains deferred.

The future adapter must not import a real MIDI dependency at module import time.

If a future dependency such as `mido` is selected later, it must be imported
only inside the real backend/provider path.

The future adapter should allow tests to import `rytm_randomizer.real_midi_adapter`
without requiring real MIDI libraries.

Dependency absence must fail safely with deterministic errors or results.

The first future implementation should not modify package metadata unless a
separate dependency decision explicitly approves it.

## 6. Conceptual Types

The following names are design concepts only:

- `RealMidiDependencyError`
- `RealMidiPortError`
- `RealMidiSendError`
- `RealMidiPortProvider`
- `RealMidiSender`
- `RealMidiSendResult`
- `build_real_midi_sender`

These names are not implemented by this document.

The future types should be small and explicit:

- dependency errors should be deterministic and testable
- port errors should not open fallback ports
- send results should describe attempted mock-message metadata and success
  state without hiding failures
- sender construction should require explicit provider/port inputs
- no sender should be constructed by passive CLI paths

## 7. Future Port Provider Boundary

The future port provider boundary should isolate port lookup and opening.

It should support fake providers in tests.

It should not list or open real ports during passive imports.

It should not list or open real ports during passive CLI commands.

It should not guess a default hardware port.

It should fail safely if a requested port is missing or ambiguous.

Any real port opening must remain blocked until a later explicitly approved
hardware-validation phase.

## 8. Future Sender Boundary

The future sender boundary should receive already-approved message data from a
future active path.

It should not decide whether an action is armed.

It should not perform registry lookup.

It should not evaluate passive previews.

It should not dispatch commands or scenes.

It should not create messages from profile metadata directly.

It should send only through an injected provider/backend after all upstream
safety checks have passed.

In unit tests, the sender must use fake providers only.

## 9. Future Message Translation Boundary

The future adapter may translate inert `MidiMessage` data into backend-specific
message objects only after implementation is separately approved.

The initial real adapter design should remain CC-like and narrow if a future
implementation reaches translation.

The adapter must not add:

- SysEx
- scenes
- global mutation execution
- pattern/project/kit save or clear
- transport
- clock behavior
- Pads 5-12
- Analog Four

The adapter should preserve metadata needed for traceability:

- source kind
- source key
- source name
- target concept
- group pad
- machine value
- mock-only lineage
- sends-real-MIDI decision point

## 10. Passive CLI Separation

Passive CLI commands must not import or construct the future real MIDI adapter.

Passive CLI commands must remain read-only:

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

These commands must not open ports, send MIDI, create sender objects, or
trigger active behavior.

## 11. Active Boundary Relationship

The current mock-first active boundary remains limited to group profile `"2"` /
My BD Hard.

The future real MIDI adapter must not widen active-boundary scope.

Profile `"3"` / My BD Classic remains unsupported by the active boundary.

Profile `"4"` / My BD Acoustic remains parked and unsupported.

Any future adapter implementation must not implement profile `"4"` or add
profile `"3"` active-boundary support.

The adapter should only be reachable from a separately approved active path,
not from passive CLI or passive reporting.

## 12. Future Tests Required Before Adapter Code

Before adapter code is implemented, a future implementation plan should define
tests proving:

- importing the adapter prints nothing
- importing the adapter does not require `mido`
- passive imports do not import the adapter
- passive CLI commands do not import the adapter
- missing dependency fails safely
- fake providers can stand in for real ports
- unknown port names fail safely
- sender construction requires explicit target/provider inputs
- send attempts through fake providers are observable without real MIDI
- no real ports open in tests
- no MIDI is sent in tests
- profile `"3"` remains unsupported by the active boundary
- profile `"4"` remains parked and unsupported
- V1.34 reference diff remains empty

The existing closeout labels must remain:

- `=== Test: Real MIDI Import Safety ===`
- `=== Test: Real MIDI Passive CLI Safety ===`
- `=== Test: Real MIDI Adapter Boundary ===`

## 13. Future Implementation Sequence

The future sequence should be:

1. Review and accept this design/spec.
2. Create a documentation-only first adapter implementation plan.
3. Implement fake-provider-only tests if the plan is accepted.
4. Implement the smallest adapter boundary needed to satisfy those tests.
5. Keep dependency selection deferred unless separately approved.
6. Keep hardware validation blocked until much later.

Do not combine dependency selection, adapter implementation, active CLI
commands, or hardware validation into one slice.

## 14. Forbidden Scope

Still forbidden:

- adding `mido`
- adding any real MIDI dependency
- package metadata changes
- opening ports
- sending MIDI
- active CLI commands
- execute-command
- send-command
- hardware-test
- passive CLI wiring to the adapter
- command dispatch
- command execution
- scene execution
- hardware detection
- hardware behavior
- SysEx
- GUI/capture
- Analog Four
- Pads 5-12
- machine/profile expansion
- profile `"4"` implementation
- profile `"3"` active-boundary support
- hardware validation
- turning hardware on

## 15. Stop Conditions

Stop immediately if a future slice proposes:

- a real MIDI import in passive code
- a package dependency change without a reviewed dependency decision
- port opening in tests
- MIDI sending in tests
- passive CLI adapter construction
- active CLI command creation
- command dispatch or execution
- scene execution
- profile `"4"` implementation
- profile `"3"` active-boundary support
- V1.34 reference changes
- hardware validation
- turning on Analog Rytm or Analog Four

## 16. Preconditions Before Future Hardware Validation

This design/spec does not authorize hardware validation.

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

Analog Rytm and Analog Four remain off during this design/spec.

## 17. Safe Next Options

Safe next options:

- review and accept this design/spec
- pause at this clean design checkpoint
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

## 18. Recommendation

Prefer a documentation-only review/acceptance gate for this design/spec next.

After that, create a documentation-only first adapter implementation plan.

Do not implement real MIDI yet.

Do not add `mido`.

Do not install dependencies.

Do not open ports.

Do not add active CLI commands.

Do not turn on hardware.

## 19. Review Gate

The review gate for this design/spec is:

- `Docs/REAL_MIDI_ADAPTER_FIRST_IMPLEMENTATION_DESIGN_SPEC_REVIEW.md`

The review accepts this design/spec as the current checkpoint before any
documentation-only first adapter implementation plan.

The review does not authorize creating `rytm_randomizer/real_midi_adapter.py`,
selecting or installing a real MIDI dependency, package metadata changes, port
opening, MIDI sending, active CLI commands, hardware behavior, hardware
validation, profile `"4"` implementation, or profile `"3"` active-boundary
support.

## 20. Decision

The first adapter implementation design/spec is documented.

Adapter implementation remains blocked.

Real MIDI dependency selection remains deferred.

Hardware validation remains blocked.

Hardware remains off.

No implementation is added in this slice.
