# Real MIDI Adapter-Specific Test Plan Review

## 1. Purpose

Review and accept `Docs/REAL_MIDI_ADAPTER_SPECIFIC_TEST_PLAN.md` as the
current planning gate before any real MIDI adapter-specific test
implementation.

This is a review checkpoint only.

This document does not implement tests.

This document does not implement an adapter.

This document does not install dependencies.

This document does not import real MIDI libraries, open ports, send MIDI, add
active CLI commands, add hardware behavior, or start hardware validation.

## 2. Current Clean Baseline

Current branch:

- modularize-v1.34

Current HEAD before this slice:

- 1f352de Add real MIDI adapter-specific test plan

Current phase:

- Passive/Mock Foundation Phase
- mock-first active boundary exists for test-only evaluation
- real MIDI dependency decision is reviewed and accepted
- real MIDI adapter boundary gate is reviewed and accepted
- real MIDI adapter boundary design is reviewed and accepted
- real MIDI adapter-specific test plan has been documented
- real MIDI adapter-specific test plan is now being reviewed

Accepted safety baseline:

- real MIDI import safety tests are in closeout
- real MIDI passive CLI safety tests are in closeout
- real MIDI dependency selection remains deferred
- `mido` remains absent
- no real MIDI backend exists
- no real MIDI adapter module exists
- no adapter-specific tests are implemented yet
- no hardware validation has started

Hardware status:

- Analog Rytm MKII off
- Analog Four MKII off
- hardware not required

## 3. Review Decision

`Docs/REAL_MIDI_ADAPTER_SPECIFIC_TEST_PLAN.md` is accepted as the current
planning gate before any adapter-specific test implementation.

The plan remains documentation-only.

The plan does not authorize adapter implementation by itself.

The plan does not authorize adding a real MIDI dependency by itself.

The plan does not authorize turning hardware on by itself.

## 4. Accepted Test Planning Concepts

The review accepts these test planning concepts:

- future tests must be fake-provider-only
- future tests must not require real MIDI dependencies
- future tests must not open ports
- future tests must not send MIDI
- future tests must not require hardware
- future test ownership may use `tests/test_real_midi_adapter_boundary.py`
- future closeout coverage may add `=== Test: Real MIDI Adapter Boundary ===`
- future tests may target `rytm_randomizer/real_midi_adapter.py` only after a
  tests-only implementation slice is approved
- existing real MIDI import safety tests must remain in closeout
- existing real MIDI passive CLI safety tests must remain in closeout
- passive CLI commands must remain read-only
- active-boundary scope remains limited to group profile `"2"` / My BD Hard
- profile `"3"` remains unsupported by the active boundary
- profile `"4"` remains parked and unsupported

## 5. Accepted Future Test Categories

The accepted future test categories are:

- adapter import safety
- dependency absence safe failure
- fake port provider behavior
- unknown port safe failure
- sender construction guards
- message send guards
- passive CLI regression safety
- active-boundary scope guard safety
- V1.34 reference protection
- closeout integration

These categories are accepted for a future tests-only slice.

No tests are implemented by this review.

## 6. Confirmed Absent Behavior

Confirmed absent:

- no `mido`
- no real MIDI dependency
- no real MIDI adapter module
- no real MIDI backend
- no adapter-specific test implementation
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

## 7. Passive Commands Remain Read-Only

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

## 8. Preconditions Before Future Tests-Only Implementation

Before a tests-only adapter boundary implementation slice begins:

- clean Git status
- closeout passes
- V1.34 reference diff is empty
- real MIDI dependency decision review is accepted
- real MIDI adapter boundary gate review is accepted
- real MIDI adapter boundary design review is accepted
- real MIDI adapter-specific test plan review is accepted
- import safety tests remain in closeout
- passive CLI safety tests remain in closeout
- passive CLI remains read-only
- `mido` remains absent
- no real MIDI dependency is installed
- no hardware required
- hardware remains off

## 9. Allowed Future Tests-Only Slice

A future tests-only slice may include:

- `tests/test_real_midi_adapter_boundary.py`
- `Scripts/closeout_check.ps1`

The future closeout label may be:

- `=== Test: Real MIDI Adapter Boundary ===`

The future tests-only slice may introduce failing tests first for a future
adapter module, or it may introduce skipped/planning-compatible tests only if
explicitly approved at that time.

The preferred path is test-first, fake-provider-only coverage that does not
require real MIDI libraries, real ports, or hardware.

## 10. Still Forbidden

The future tests-only slice must not:

- add `mido`
- add another real MIDI dependency
- import real MIDI libraries
- open ports
- send MIDI
- require hardware
- add active CLI commands
- add execute-command
- add send-command
- add hardware-test
- wire passive CLI to adapter behavior
- implement profile `"4"`
- add profile `"3"` active-boundary support
- edit `rytm_hybrid_randomizer_v134.py`
- turn on hardware

## 11. Preconditions Before Future Adapter Implementation

This review does not authorize adapter implementation.

Before any future adapter implementation:

- adapter-specific tests must be implemented with fake providers only
- adapter-specific tests must be reviewed and accepted
- closeout must pass
- V1.34 reference diff must be empty
- dependency addition must be separately approved
- implementation scope must be separately approved
- hardware must remain off

## 12. Preconditions Before Future Hardware Validation

This review does not authorize hardware validation.

Before any future hardware validation:

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
- hardware validation checklist must be accepted
- user must explicitly confirm hardware validation is starting

Analog Rytm and Analog Four remain off during this review.

## 13. Safe Next Options

Safe next options:

- pause at this accepted test planning checkpoint
- create a tests-only implementation slice for adapter boundary tests
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

## 14. Recommendation

Prefer a tests-only adapter boundary safety implementation slice next, limited
to fake-provider-only tests and closeout integration.

Do not implement real MIDI.

Do not add `mido`.

Do not install dependencies.

Do not open ports.

Do not add active CLI commands.

Do not turn on hardware.

## 15. Decision

The real MIDI adapter-specific test plan is accepted for planning.

Adapter-specific tests may be implemented next only as a tests-only,
fake-provider-only slice.

Adapter implementation remains blocked.

Real MIDI dependency selection remains deferred.

Hardware validation remains blocked.

Hardware remains off.

No implementation is added in this slice.
