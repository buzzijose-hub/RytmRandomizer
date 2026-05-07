# Real MIDI Adapter First Implementation Design Spec Review

## 1. Purpose

Review and accept `Docs/REAL_MIDI_ADAPTER_FIRST_IMPLEMENTATION_DESIGN_SPEC.md`
as the current design/spec before any first real MIDI adapter implementation
plan.

This is a review checkpoint only.

This document does not implement an adapter.

This document does not add tests.

This document does not add dependencies, import real MIDI libraries, open
ports, send MIDI, add active CLI commands, add hardware behavior, or start
hardware validation.

## 2. Current Clean Baseline

Current branch:

- modularize-v1.34

Current HEAD before this slice:

- 869535f Add real MIDI adapter first implementation design spec

Current phase:

- Passive/Mock Foundation Phase
- mock-first active boundary exists for test-only evaluation
- real MIDI adapter boundary safety tests are in closeout
- first adapter implementation planning gate is reviewed and accepted
- first adapter implementation design/spec has been documented
- first adapter implementation design/spec is now being reviewed

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

## 3. Review Decision

`Docs/REAL_MIDI_ADAPTER_FIRST_IMPLEMENTATION_DESIGN_SPEC.md` is accepted as
the current first adapter implementation design/spec.

The review accepts:

- 869535f Add real MIDI adapter first implementation design spec
- future narrow adapter boundary only
- future dependency isolation and lazy import behavior
- future port provider boundary
- future sender boundary
- future dependency-absent safe failure behavior
- future fake-provider-only test path
- passive CLI separation
- active-boundary scope limits
- V1.34 reference protection

The design/spec remains documentation-only.

The design/spec does not authorize adapter implementation by itself.

The design/spec does not authorize adding a real MIDI dependency by itself.

The design/spec does not authorize package metadata changes by itself.

The design/spec does not authorize turning hardware on by itself.

## 4. Accepted Future Adapter Shape

The review accepts the future adapter as a narrow boundary only.

The future adapter may be discussed as:

- `rytm_randomizer/real_midi_adapter.py`

That file still does not exist.

The future adapter should own only:

- dependency loading boundary
- port provider boundary
- sender boundary
- safe failure types/results
- future backend message send calls after upstream safety checks

The future adapter must not own:

- passive CLI commands
- active CLI commands
- command dispatch
- scene execution
- group profile metadata
- mock message mapping
- mock-first active boundary decisions
- hardware validation scripts

## 5. Accepted Future Concept Names

The review accepts these names as future design concepts only:

- `RealMidiDependencyError`
- `RealMidiPortError`
- `RealMidiSendError`
- `RealMidiPortProvider`
- `RealMidiSender`
- `RealMidiSendResult`
- `build_real_midi_sender`

These names are not implemented by this review.

## 6. Accepted Dependency Rules

The review accepts these dependency rules:

- real MIDI dependency selection remains deferred
- no real MIDI dependency is installed by this design/spec
- no package metadata changes are authorized by this design/spec
- no real MIDI dependency may be imported at module import time
- a future dependency, if approved later, must be imported only inside a real
  backend/provider path
- dependency absence must fail safely with deterministic errors or results
- tests must be able to import the future adapter without requiring real MIDI
  libraries

## 7. Accepted Port And Sender Rules

The review accepts these port and sender rules:

- port lookup and opening must be isolated behind a provider boundary
- tests must use fake providers
- passive imports must not list or open real ports
- passive CLI commands must not list or open real ports
- no default hardware port may be guessed
- missing or ambiguous requested ports must fail safely
- sender construction must require explicit provider/target inputs
- sender behavior must not decide arming
- sender behavior must not dispatch commands or scenes
- sender behavior must not perform registry lookup
- sender behavior must not create messages from profile metadata directly

## 8. Passive CLI Remains Read-Only

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

## 9. Active Boundary Scope Remains Narrow

The current mock-first active boundary remains limited to:

- group profile `"2"` / My BD Hard

The future real MIDI adapter must not widen active-boundary scope.

Profile `"3"` / My BD Classic remains unsupported by the active boundary.

Profile `"4"` / My BD Acoustic remains parked and unsupported.

Any future adapter implementation must not implement profile `"4"` or add
profile `"3"` active-boundary support.

## 10. Current Closeout Coverage

Closeout includes:

- scaffold
- validation
- inspection
- preview
- audit
- profile lookup
- scene lookup
- command lookup
- registry
- registry report
- registry report CLI
- passive CLI
- mock MIDI
- mock message mapper
- mock mapper report
- mock-only active candidate
- active boundary
- active boundary report
- real MIDI import safety
- real MIDI passive CLI safety
- real MIDI adapter boundary

## 11. Confirmed Absent Behavior

Confirmed absent:

- no `mido`
- no real MIDI dependency
- no real MIDI adapter module
- no real MIDI backend
- no package metadata changes
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

## 12. Preconditions Before Future First Adapter Implementation Plan

Before any first adapter implementation plan begins:

- clean Git status
- closeout passes
- V1.34 reference diff is empty
- this design/spec review is accepted
- real MIDI adapter boundary safety tests remain in closeout
- passive CLI remains read-only
- `mido` remains absent
- no real MIDI dependency is installed
- no real MIDI adapter module exists
- no hardware required
- hardware remains off

## 13. Preconditions Before Future Adapter Code

This review does not authorize adapter code.

Before any future adapter code:

- first adapter implementation plan must exist and be reviewed
- fake-provider-only tests must exist
- dependency-absent safe-failure tests must exist
- passive CLI regression tests must remain green
- active-boundary scope guard tests must remain green
- closeout must pass
- V1.34 reference diff must be empty
- dependency addition must remain separately approved
- hardware must remain off

## 14. Preconditions Before Future Dependency Selection

This review does not authorize selecting or installing a real MIDI dependency.

Before any future dependency selection:

- first adapter implementation plan must exist and be reviewed
- dependency decision note must be revisited
- dependency decision review must be accepted
- package metadata changes must be explicitly approved
- unit tests must still avoid real ports
- hardware must remain off

## 15. Preconditions Before Future Hardware Validation

This review does not authorize hardware validation.

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

Analog Rytm and Analog Four remain off during this review.

## 16. Safe Next Options

Safe next options:

- create a documentation-only first adapter implementation plan
- pause at this accepted design/spec checkpoint
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

## 17. Recommendation

Prefer a documentation-only first adapter implementation plan next.

Do not implement real MIDI yet.

Do not add `mido`.

Do not install dependencies.

Do not open ports.

Do not add active CLI commands.

Do not turn on hardware.

## 18. First Adapter Implementation Plan

The first adapter implementation plan now lives in:

- `Docs/REAL_MIDI_ADAPTER_FIRST_IMPLEMENTATION_PLAN.md`

The plan defines a future fake-provider-only implementation slice for
`rytm_randomizer/real_midi_adapter.py` and
`tests/test_real_midi_adapter_boundary.py`. It includes concrete future test
snippets, future adapter boundary code snippets, targeted verification, full
closeout, V1.34 reference protection, and commit boundaries.

The plan does not authorize adapter implementation until it is reviewed and
accepted. It does not authorize `mido`, real MIDI dependency selection,
package metadata changes, port opening, MIDI sending, active CLI commands,
hardware behavior, hardware validation, profile `"4"` implementation, or
profile `"3"` active-boundary support.

## 19. First Adapter Implementation Plan Review

The first adapter implementation plan review now lives in:

- `Docs/REAL_MIDI_ADAPTER_FIRST_IMPLEMENTATION_PLAN_REVIEW.md`

The review accepts the plan as the current checkpoint before any first adapter
boundary code. It allows a future implementation slice limited to
`rytm_randomizer/real_midi_adapter.py` and
`tests/test_real_midi_adapter_boundary.py`, using fake providers only.

The review keeps `mido`, real MIDI dependency selection, package metadata
changes, real port opening, MIDI sending, active CLI commands, hardware
behavior, hardware validation, profile `"4"` implementation, and profile `"3"`
active-boundary support blocked.

## 20. Decision

The real MIDI adapter first implementation design/spec is accepted.

The next safe branch may be the tiny first adapter boundary implementation
slice.

Adapter implementation remains blocked.

Real MIDI dependency selection remains deferred.

Hardware validation remains blocked.

Hardware remains off.

No implementation is added in this slice.
