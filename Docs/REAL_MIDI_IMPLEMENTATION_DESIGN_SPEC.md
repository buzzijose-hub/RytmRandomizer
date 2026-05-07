# Real MIDI Implementation Design Spec

## 1. Purpose

Define a future implementation design/spec for a real MIDI boundary without
implementing it.

Keep this document at planning altitude only.

This document does not add real MIDI code.

This document does not add a real MIDI dependency.

This document does not add active CLI commands.

This document does not authorize opening ports, sending MIDI, dispatching
commands, executing scenes, mutating hardware, or turning hardware on.

## 2. Current Clean Baseline

Current branch:

- modularize-v1.34

Current HEAD before this slice:

- ddc0e03 Add real MIDI boundary plan review

Current phase:

- Passive/Mock Foundation Phase
- project-level roadmap update accepted
- mock-first active boundary safety baseline accepted
- real MIDI boundary planning gate accepted
- real MIDI boundary plan accepted
- real MIDI implementation design/spec now being documented
- no real MIDI or hardware validation started

Hardware status:

- Analog Rytm MKII off
- Analog Four MKII off
- hardware not required

## 3. Design Scope

This design/spec defines only the future shape of a real MIDI boundary.

It may describe:

- future module ownership
- future conceptual interfaces
- future dependency isolation
- future port-provider boundary
- future sender boundary
- future active-boundary integration points
- future test requirements
- future implementation sequencing

It does not create any of those modules.

It does not add code.

It does not add tests.

It does not add dependencies.

## 4. Current Accepted Scope

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

The future real MIDI boundary must not widen this scope.

## 5. Architecture Principle

The real MIDI boundary must sit below the active boundary and behind an
injected sender-style interface.

High-level active boundary logic must not import real MIDI libraries.

Passive CLI modules must not import real MIDI libraries.

Passive CLI modules must not construct senders.

Passive CLI modules must not discover or open ports.

The first future implementation, if later approved, should prove isolation and
safe failures before it can ever send a real message.

## 6. Proposed Future File Ownership

Future implementation may use files with responsibilities like these:

- `rytm_randomizer/midi_message_plan.py`
  - defines future translation rules between inert mock messages and backend
    send payloads
  - does not import real MIDI libraries
- `rytm_randomizer/midi_port_provider.py`
  - owns future real port listing and explicit port selection
  - must not be imported by passive CLI paths
- `rytm_randomizer/midi_sender.py`
  - owns future real send adapter behavior
  - must not be imported by passive CLI paths
- `tests/test_real_midi_boundary.py`
  - future mock-only tests proving isolation and safe failure behavior
  - must not open real ports
- `tests/test_real_midi_import_safety.py`
  - future tests proving passive imports do not import real MIDI dependencies
  - must not require hardware

These files are proposed for future planning only.

They are not created in this slice.

## 7. Conceptual Interfaces

Future concepts may include:

- `MidiBackendUnavailable`
- `MidiPortSelection`
- `RealMidiPortProvider`
- `RealMidiSender`
- `RealMidiSendRequest`
- `RealMidiSendResult`

These names are conceptual.

They do not exist in this slice.

If implemented later, these interfaces must keep real MIDI backend access at
the edge of the system and keep high-level active-boundary logic mockable.

## 8. Message Translation Rule

The future real MIDI layer should consume validated, inert message data from
the accepted mock-first boundary.

The real MIDI layer should not reinterpret registry metadata directly.

The real MIDI layer should not call the mock message mapper directly from
passive CLI paths.

The real MIDI layer should translate only explicitly accepted message shapes.

Unsupported message shapes must fail safely before any port is opened.

Unknown source keys must fail safely before any port is opened.

Profile `"3"` and profile `"4"` must remain unsupported by the active boundary
unless separately approved.

## 9. Dependency Boundary

No real MIDI dependency is added by this design/spec.

If a real MIDI dependency is considered later, the dependency decision must be
made in a separate approved implementation plan.

Future ordinary unit tests must pass without the real MIDI dependency
installed.

Future passive imports must pass without the real MIDI dependency installed.

Future passive CLI commands must pass without the real MIDI dependency
installed.

Any future real MIDI import must live only inside a tiny hardware-facing
adapter module.

## 10. Port Provider Boundary

Future port provider behavior must be explicit.

It must not run during:

- package import
- passive CLI `--help`
- passive CLI report/list/search/inspect/preview
- `mock-mapper-report`
- `active-boundary-report`
- mock message mapping
- mock-first active boundary evaluation
- ordinary closeout tests

Future port selection must require explicit operator selection.

No default port should be opened silently.

No real port may open before arming, target confirmation, and explicit
hardware validation approval.

## 11. Sender Boundary

Future real sender behavior must:

- accept explicit validated message data
- require explicit target port information
- require armed hardware-facing context
- return deterministic result metadata
- fail safely if backend dependency is unavailable
- fail safely if port selection is missing
- fail safely if arming is missing
- fail safely if message shape is unsupported

Future real sender behavior must not:

- discover ports implicitly
- open ports from passive CLI
- send MIDI from passive CLI
- send MIDI from import-time code
- dispatch commands
- execute scenes
- mutate hardware without explicit future hardware-validation phase approval

## 12. Active Boundary Integration

Future integration with the active boundary must be explicit and later
approved.

The current active boundary remains mock-first and test-only.

The current active boundary supports only:

- group profile `"2"` / My BD Hard

Future real MIDI integration must not add:

- profile `"3"` active-boundary support
- profile `"4"` implementation
- scene execution
- command execution
- active CLI commands

Any future real MIDI integration must happen only after this design/spec is
reviewed, a test plan is accepted, and a separate implementation plan is
approved.

## 13. Passive CLI Separation

The passive CLI must remain read-only.

These commands must remain passive:

- `report`
- `list-commands`
- `list-scenes`
- `list-group-profiles`
- `search-commands`
- `search-scenes`
- `search-group-profiles`
- `inspect-command`
- `inspect-scene`
- `inspect-group-profile`
- `preview-command`
- `preview-scene`
- `preview-group-profile`
- `mock-mapper-report`
- `active-boundary-report`

They must never:

- import real MIDI libraries
- construct a real sender
- construct `MockMidiSender`
- evaluate active boundary requests
- discover ports
- open ports
- send MIDI
- execute commands
- execute scenes
- mutate hardware

## 14. Required Future Test Categories

Before any implementation, a separate test plan must define tests for:

- passive import safety
- passive CLI no-port behavior
- passive CLI no-send behavior
- passive CLI no-active-boundary-evaluation behavior
- dependency absence safety
- port provider isolation
- missing arming safe failure
- missing port safe failure
- unsupported message shape safe failure
- unknown key safe failure
- profile `"3"` active-boundary unsupported behavior
- profile `"4"` parked behavior
- V1.34 reference untouched check
- closeout integration

These tests are not added in this slice.

## 15. Future Implementation Sequence

If this design/spec is reviewed and accepted, the safe future sequence is:

1. Create a documentation-only real MIDI implementation test plan.
2. Review and accept that test plan.
3. Create a narrow implementation plan for tests only.
4. Add mock-only import and port isolation tests.
5. Review the completed tests.
6. Only then consider a tiny adapter scaffold with no real send behavior.
7. Review the adapter scaffold.
8. Only much later consider hardware-validation planning.

This sequence does not authorize skipping directly to real MIDI sending.

## 16. Hardware Validation Remains Later

This design/spec does not authorize hardware validation.

Before hardware validation could be considered later:

- all passive safety tests must pass
- all mock-only active-boundary tests must pass
- all real MIDI boundary tests must pass
- real MIDI adapter implementation must be reviewed and accepted
- exact target device must be selected
- exact MIDI output port must be confirmed
- exact command/pad/channel scope must be confirmed
- current Analog Rytm kit/project must be saved
- monitoring volume must be lowered
- hardware validation checklist must be accepted
- user must explicitly confirm that hardware validation is starting

Analog Rytm and Analog Four remain off during this planning phase.

## 17. Forbidden Scope

This design/spec does not authorize:

- implementation
- real MIDI imports
- mido dependency
- MIDI port opening
- MIDI sending
- hardware detection
- hardware send
- active CLI commands
- passive CLI active-boundary evaluation
- passive CLI construction of `MockMidiSender`
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

## 18. Safe Next Options

Safe next options:

- review and accept this real MIDI implementation design/spec
- pause at this clean planning checkpoint
- return to passive/project documentation
- create a documentation-only real MIDI implementation test plan after this
  design/spec is accepted

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

## 19. Recommendation

Review and accept this design/spec before any further real MIDI-facing work.

Do not implement real MIDI.

Do not add mido.

Do not open ports.

Do not add active CLI commands.

Do not turn on hardware.

## 20. Decision

The future real MIDI implementation shape is defined at design/spec level
only.

Real MIDI implementation remains blocked.

Hardware validation remains blocked.

Hardware remains off.

No implementation is added in this slice.

## 21. Review Gate

This real MIDI implementation design/spec is reviewed and accepted by:

- `Docs/REAL_MIDI_IMPLEMENTATION_DESIGN_SPEC_REVIEW.md`

The review accepts this document as the current real MIDI implementation
design/spec baseline. It does not authorize implementation, tests, real MIDI
imports, mido, port opening, MIDI sending, active CLI commands, dispatch,
command execution, scene execution, hardware behavior, profile `"4"`
implementation, profile `"3"` active-boundary support, hardware validation,
or turning hardware on.
