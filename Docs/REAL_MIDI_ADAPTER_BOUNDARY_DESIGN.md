# Real MIDI Adapter Boundary Design

## 1. Purpose

Define the future real MIDI adapter boundary at design level only.

This document explains where real MIDI dependency use may eventually live, how
that boundary must stay isolated from passive code, how future port discovery
and sender construction must be controlled, and what must be tested before any
adapter implementation.

This is a documentation-only design.

This document does not implement an adapter.

This document does not add `mido` or any real MIDI dependency.

This document does not import real MIDI libraries, open ports, send MIDI, add
active CLI commands, add hardware behavior, or start hardware validation.

## 2. Current Clean Baseline

Current branch:

- modularize-v1.34

Current HEAD before this slice:

- 9fc92d2 Add real MIDI adapter boundary gate review

Current phase:

- Passive/Mock Foundation Phase
- mock-first active boundary exists for test-only evaluation
- real MIDI dependency decision is reviewed and accepted
- real MIDI adapter boundary gate is reviewed and accepted
- real MIDI adapter boundary design is now being documented

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

## 3. Design Decision

Any future real MIDI behavior must live behind a narrow adapter boundary.

The adapter boundary must be separate from:

- passive CLI browsing
- passive registry/report/lookup modules
- mock MIDI scaffold
- mock message mapper
- mock mapper report
- active boundary report
- passive imports

The boundary must be explicit, lazy, testable, and inactive unless a future
hardware-facing path intentionally asks for it.

## 4. Non-Goals

This design does not authorize:

- adding `mido`
- adding another real MIDI dependency
- editing dependency metadata
- editing lockfiles
- creating runtime adapter modules
- opening MIDI ports
- sending MIDI
- adding active CLI commands
- wiring passive CLI to active execution
- detecting hardware
- starting hardware validation
- implementing profile `"4"`
- adding profile `"3"` active-boundary support
- touching `rytm_hybrid_randomizer_v134.py`
- turning on hardware

## 5. Future Module Ownership

If implementation is later approved, future ownership should stay small and
isolated.

Preferred future module shape:

- `rytm_randomizer/real_midi_adapter.py`

Conceptual responsibilities:

- hold real MIDI dependency import isolation
- expose future adapter-specific error types
- expose future port provider protocol or implementation
- expose future real sender protocol or implementation
- keep real MIDI dependency use out of passive modules

Avoid splitting into multiple files until implementation pressure proves it is
needed.

Future names such as `midi_ports.py` or `hardware_sender.py` remain possible
later, but the first implementation should prefer one small adapter boundary
unless tests show a clear need for separate modules.

## 6. Import Isolation Design

Real MIDI imports must be lazy and isolated.

Future adapter code must not import a real MIDI library at package import time.

Future adapter code must not cause these modules to import real MIDI
libraries:

- `rytm_randomizer.cli`
- `rytm_randomizer.registry_report`
- `rytm_randomizer.mock_midi`
- `rytm_randomizer.mock_message_mapper`
- `rytm_randomizer.mock_mapper_report`
- `rytm_randomizer.active_boundary`
- `rytm_randomizer.active_boundary_report`
- passive registry/report/lookup modules

If a real MIDI dependency is absent, passive imports must still succeed.

Dependency absence must fail safely only inside the future explicit adapter
path, not during passive CLI or passive import paths.

## 7. Dependency Boundary Design

Real MIDI dependency selection remains deferred.

The future adapter should treat the real MIDI library as an optional boundary
dependency.

Before any dependency is added:

- adapter tests must be written
- dependency absence behavior must be designed
- dependency absence behavior must be tested
- passive import safety tests must remain in closeout
- passive CLI safety tests must remain in closeout
- package metadata changes must be separately approved

The adapter must not leak real dependency objects into passive reports or
mock-only tests.

## 8. Port Provider Design

Future port discovery must be explicit.

Port discovery must not happen:

- during import
- during passive CLI commands
- during `report`
- during list/search/inspect/preview commands
- during `mock-mapper-report`
- during `active-boundary-report`
- during mock-only tests
- during closeout passive test runs unless an explicit future adapter test
  uses a fake provider

Future port provider behavior should be modeled as a small boundary that can:

- list available output ports only when explicitly requested
- fail safely if the dependency is absent
- fail safely if no ports are available
- fail safely if the requested port is unknown
- return deterministic simple data for tests

Future unit tests must use fake providers, not real hardware ports.

## 9. Sender Boundary Design

Future real sender construction must be explicit and guarded.

Sender construction must not happen:

- during import
- during passive CLI commands
- during passive report generation
- during mock mapper reporting
- during active boundary reporting
- during mock-only active tests

Future sender construction must require:

- explicit hardware-facing phase approval
- explicit operator intent
- exact target device
- exact MIDI output port
- exact command or profile key
- dry-run preview reference
- arming confirmation
- clean closeout
- clean Git status

Missing any requirement must fail safely before any port opens.

## 10. Conceptual Interfaces

These names are design placeholders only.

Possible future concepts:

- `RealMidiAdapterError`
- `RealMidiDependencyUnavailable`
- `RealMidiPortNotFound`
- `RealMidiPortProvider`
- `RealMidiSender`
- `RealMidiAdapterConfig`

Possible future responsibilities:

- `RealMidiPortProvider.list_output_ports()` returns simple port names or
  simple copied port records
- `RealMidiSender.send(message)` sends one already validated message only
  after explicit construction
- `RealMidiSender.send_many(messages)` sends already validated messages in
  order only after explicit construction
- adapter errors describe safe failures without touching hardware

These interfaces are not implemented in this slice.

## 11. Passive CLI Separation

Passive CLI commands must remain read-only.

The following commands must not import real MIDI libraries, open ports, send
MIDI, construct senders, or construct port providers:

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

The passive CLI must not route through a real MIDI adapter.

The passive CLI must not add active command names as part of adapter design.

## 12. Active Boundary Relationship

Current accepted active-boundary scope remains:

- group profile `"2"` / My BD Hard

Unsupported active-boundary scope remains:

- group profile `"3"` / My BD Classic
- group profile `"4"` / My BD Acoustic
- scenes
- commands
- unknown keys
- unsupported source kinds

Future real MIDI adapter work must not expand active-boundary scope.

Future real MIDI adapter work must not implement profile `"4"`.

Future real MIDI adapter work must not add profile `"3"` active-boundary
support without separate approval.

## 13. Failure Behavior

Future adapter failure behavior must be deterministic and safe.

Safe failures must occur before port opening or MIDI sending for:

- missing dependency
- missing arming
- missing dry-run confirmation
- missing target device
- missing target port
- unknown port
- unknown key
- unsupported key
- unsupported source kind
- unsupported command scope
- profile `"3"` active-boundary requests
- profile `"4"` active-boundary requests

Failure messages should be human-readable and should clearly state that no MIDI
was sent and no hardware was mutated.

## 14. Required Tests Before Implementation

Before implementation, a separate adapter-specific test plan must define tests
that prove:

- importing passive modules does not import real MIDI libraries
- passive CLI commands do not import real MIDI libraries
- passive CLI commands do not open ports
- passive CLI commands do not send MIDI
- adapter module import does not open ports
- dependency absence fails safely
- fake port provider can be used without hardware
- unknown port fails safely
- missing arming fails safely
- missing dry-run confirmation fails safely
- unsupported keys fail safely
- profile `"3"` remains unsupported by the active boundary
- profile `"4"` remains parked and unsupported
- V1.34 reference remains untouched

These tests must be reviewed before adapter implementation.

## 15. Implementation Sequence

If this design is later reviewed and accepted, the future sequence should be:

1. Create a documentation-only adapter-specific test plan.
2. Review and accept that test plan.
3. Implement tests with fake providers only.
4. Review the completed tests.
5. Decide whether dependency addition is still necessary.
6. Separately approve any dependency metadata change.
7. Implement the smallest adapter boundary that satisfies the approved tests.
8. Review implementation before any hardware-facing validation.

No implementation is authorized by this design.

## 16. Hardware Validation Boundary

Hardware validation remains blocked.

Before future hardware validation:

- all mock-only tests must pass
- all import and port safety tests must pass
- all future adapter tests must pass
- adapter implementation must be reviewed and accepted
- dependency decision must be revisited and accepted
- exact target device must be selected
- exact MIDI output port must be confirmed
- exact command/pad/channel scope must be confirmed
- current Analog Rytm kit/project must be saved
- monitoring volume must be lowered
- user must explicitly confirm hardware validation is starting

Analog Rytm and Analog Four remain off during this design.

## 17. Stop Conditions

Stop immediately if any future work introduces:

- real MIDI dependency without separate approval
- `mido` without separate approval
- import-time real MIDI dependency loading
- port opening during passive commands
- MIDI sending during passive commands
- active CLI command names without separate approval
- passive CLI routing to adapter behavior
- profile `"4"` implementation
- profile `"3"` active-boundary support
- V1.34 reference diff
- hardware validation without explicit approval
- uncertainty about hardware state

## 18. Safe Next Options

Safe next options:

- review and accept this adapter boundary design
- pause at this clean design checkpoint
- create a documentation-only adapter-specific test plan
- return to passive/project documentation

Unsafe next moves:

- adding real MIDI dependencies
- importing real MIDI libraries
- opening ports
- sending MIDI
- adding active CLI commands
- turning on hardware
- implementing profile `"4"`
- adding profile `"3"` active-boundary support

## 19. Recommendation

Prefer a documentation-only review/acceptance gate for this design next.

After that, create a documentation-only adapter-specific test plan.

Do not implement real MIDI.

Do not add dependencies.

Do not open ports.

Do not add active CLI commands.

Do not turn on hardware.

## 20. Decision

The real MIDI adapter boundary design is documented for planning.

Adapter implementation remains blocked.

Real MIDI dependency selection remains deferred.

Hardware validation remains blocked.

Hardware remains off.

No implementation is added in this slice.

## 21. Review Gate

This design is reviewed and accepted in:

- `Docs/REAL_MIDI_ADAPTER_BOUNDARY_DESIGN_REVIEW.md`

The review accepts this design as the current planning checkpoint before any
documentation-only real MIDI adapter-specific test plan.

The review does not authorize real MIDI dependency installation, adapter
implementation, port opening, MIDI sending, active CLI commands, hardware
behavior, hardware validation, or turning hardware on.
