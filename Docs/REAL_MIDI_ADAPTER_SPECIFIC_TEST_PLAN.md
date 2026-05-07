# Real MIDI Adapter-Specific Test Plan

## 1. Purpose

Define the future adapter-specific tests that must exist before any real MIDI
adapter implementation can begin.

This is a documentation-only test plan.

This document does not implement tests.

This document does not implement an adapter.

This document does not add `mido` or any real MIDI dependency.

This document does not import real MIDI libraries, open ports, send MIDI, add
active CLI commands, add hardware behavior, or start hardware validation.

## 2. Current Clean Baseline

Current branch:

- modularize-v1.34

Current HEAD before this slice:

- c14c869 Add real MIDI adapter boundary design review

Current phase:

- Passive/Mock Foundation Phase
- mock-first active boundary exists for test-only evaluation
- real MIDI dependency decision is reviewed and accepted
- real MIDI adapter boundary gate is reviewed and accepted
- real MIDI adapter boundary design is reviewed and accepted
- real MIDI adapter-specific tests are now being planned

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

## 3. Test Plan Decision

Future real MIDI adapter work must be preceded by adapter-specific tests.

Those future tests must use fake providers only.

Those future tests must not require a real MIDI dependency.

Those future tests must not open ports.

Those future tests must not send MIDI.

Those future tests must not require hardware.

## 4. Future Test Ownership

Future test file:

- `tests/test_real_midi_adapter_boundary.py`

Future closeout label:

- `=== Test: Real MIDI Adapter Boundary ===`

Future closeout update:

- `Scripts/closeout_check.ps1`

These files are not created or edited in this slice.

## 5. Future Runtime Ownership Under Test

Future runtime file under test:

- `rytm_randomizer/real_midi_adapter.py`

That file does not exist yet.

The future adapter module must remain small, isolated, and optional.

The future adapter module must not be imported by passive CLI paths.

The future adapter module must not open ports during import.

The future adapter module must not send MIDI during import.

## 6. Existing Tests That Must Remain In Closeout

The following existing closeout coverage must remain in place:

- `=== Test: Real MIDI Import Safety ===`
- `=== Test: Real MIDI Passive CLI Safety ===`

These tests must continue proving:

- passive/mock imports do not import real MIDI libraries
- representative passive CLI commands do not import real MIDI libraries
- representative passive CLI commands do not expose port-opening behavior
- representative passive CLI commands do not expose MIDI-send behavior
- passive CLI remains read-only
- active-boundary scope does not expand

## 7. Future Adapter Import Safety Tests

Future tests should prove:

- importing `rytm_randomizer.real_midi_adapter` prints nothing
- importing `rytm_randomizer.real_midi_adapter` does not open ports
- importing `rytm_randomizer.real_midi_adapter` does not send MIDI
- importing `rytm_randomizer.real_midi_adapter` does not require hardware
- importing `rytm_randomizer.real_midi_adapter` does not require `mido`

The adapter import may define types and safe errors only.

The adapter import must not perform dependency discovery.

The adapter import must not perform port discovery.

## 8. Future Dependency Absence Tests

Future tests should prove:

- dependency absence is represented as a safe adapter error
- dependency absence does not break passive imports
- dependency absence does not break passive CLI commands
- dependency absence does not open ports
- dependency absence does not send MIDI
- dependency absence produces deterministic human-readable failure text

The future test should use a fake dependency loader or fake adapter dependency
state, not a real MIDI library.

## 9. Future Fake Port Provider Tests

Future tests should prove a fake port provider can:

- list deterministic fake output ports
- return copied port data
- avoid hardware access
- avoid real MIDI imports
- avoid port opening
- fail safely when no ports are available
- fail safely when an unknown port is requested

The fake provider must be test-only.

The fake provider must not be connected to passive CLI behavior.

## 10. Future Sender Construction Guard Tests

Future tests should prove real sender construction fails safely before port
opening when any required condition is missing:

- missing dependency
- missing explicit hardware-facing phase approval
- missing arming
- missing dry-run confirmation
- missing target device
- missing target port
- unknown target port
- missing command/profile key
- unsupported command/profile key

No test should construct a real hardware sender.

No test should open a real port.

## 11. Future Message Send Guard Tests

Future tests should prove that send behavior is inaccessible unless a sender
has been explicitly constructed through the approved future adapter boundary.

Future tests should prove no messages are sent when:

- sender construction fails
- arming is missing
- dry-run confirmation is missing
- target port is unknown
- key is unknown
- key is unsupported
- source kind is unsupported
- profile `"3"` is requested through active-boundary scope
- profile `"4"` is requested through active-boundary scope

The test implementation must use inert message objects and fake send
recording only.

## 12. Future Passive CLI Regression Tests

Future adapter-specific tests or existing passive CLI tests must prove the
following commands do not import adapter behavior, open ports, or send MIDI:

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

These commands must remain passive/read-only.

## 13. Future Active-Boundary Scope Guard Tests

Future adapter-specific tests must preserve accepted active-boundary scope.

Accepted active-boundary candidate:

- group profile `"2"` / My BD Hard

Unsupported active-boundary scope:

- group profile `"3"` / My BD Classic
- group profile `"4"` / My BD Acoustic
- scenes
- commands
- unknown keys
- unsupported source kinds

The future adapter must not expand this scope.

Profile `"3"` must remain mock-mapper/report scope only unless separately
approved.

Profile `"4"` must remain parked and unsupported unless separately approved.

## 14. Future V1.34 Reference Protection Tests

Future adapter-specific test work must preserve:

- `git diff -- rytm_hybrid_randomizer_v134.py` is empty
- no edits to `rytm_hybrid_randomizer_v134.py`
- no behavior changes to the protected V1.34 reference

The closeout script must continue checking the V1.34 reference diff.

## 15. Future Test Implementation Sequence

If this plan is reviewed and accepted, the future sequence should be:

1. Create a review gate for this plan.
2. Create a tests-only implementation slice for adapter boundary tests.
3. Add `tests/test_real_midi_adapter_boundary.py`.
4. Add the `=== Test: Real MIDI Adapter Boundary ===` closeout label.
5. Keep tests fake-provider-only.
6. Keep tests hardware-free.
7. Keep real MIDI dependency absent.
8. Run full closeout.
9. Confirm V1.34 reference diff is empty.
10. Review completed adapter boundary tests before any adapter implementation.

No test implementation is authorized by this document alone.

## 16. Future Test Cases To Define

The future test implementation should include deterministic tests for:

- import of adapter module is quiet
- adapter import does not load real MIDI libraries
- adapter import does not open ports
- dependency absence fails safely
- fake provider lists fake ports only
- fake provider returns copied data
- unknown fake port fails safely
- sender construction requires arming
- sender construction requires dry-run confirmation
- sender construction requires target device
- sender construction requires target port
- sender construction rejects unsupported keys
- sender construction rejects profile `"3"` active-boundary requests
- sender construction rejects profile `"4"` active-boundary requests
- sender construction emits no messages on failure
- passive CLI remains unchanged
- V1.34 reference remains untouched

## 17. Forbidden In Future Test Implementation

The future test implementation must not:

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

## 18. Preconditions Before Adapter Implementation

Before any adapter implementation:

- this plan must be reviewed and accepted
- adapter boundary tests must be implemented with fake providers only
- adapter boundary tests must be reviewed and accepted
- closeout must pass
- V1.34 reference diff must be empty
- dependency addition must be separately approved
- implementation scope must be separately approved
- hardware must remain off

## 19. Preconditions Before Hardware Validation

This plan does not authorize hardware validation.

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

Analog Rytm and Analog Four remain off during this plan.

## 20. Safe Next Options

Safe next options:

- review and accept this adapter-specific test plan
- pause at this clean test planning checkpoint
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

## 21. Recommendation

Prefer a documentation-only review/acceptance gate for this test plan next.

After that, consider a tests-only implementation slice using fake providers
only.

Do not implement real MIDI.

Do not add dependencies.

Do not open ports.

Do not add active CLI commands.

Do not turn on hardware.

## 22. Decision

The real MIDI adapter-specific test plan is documented for planning.

Adapter-specific test implementation remains blocked until review.

Adapter implementation remains blocked.

Real MIDI dependency selection remains deferred.

Hardware validation remains blocked.

Hardware remains off.

No implementation is added in this slice.

## 23. Review Gate

This test plan is reviewed and accepted in:

- `Docs/REAL_MIDI_ADAPTER_SPECIFIC_TEST_PLAN_REVIEW.md`

The review accepts this plan as the current planning checkpoint before any
tests-only adapter boundary safety implementation slice.

The review does not authorize real MIDI dependency installation, adapter
implementation, port opening, MIDI sending, active CLI commands, hardware
behavior, hardware validation, or turning hardware on.

## 24. Tests-Only Checkpoint

The tests-only real MIDI adapter boundary safety milestone is recorded in:

- `Docs/REAL_MIDI_ADAPTER_BOUNDARY_SAFETY_TESTS_CHECKPOINT.md`

The milestone is:

- 0e5dd03 Add real MIDI adapter boundary safety tests

The milestone adds:

- `tests/test_real_midi_adapter_boundary.py`
- `Scripts/closeout_check.ps1`
- `=== Test: Real MIDI Adapter Boundary ===`

The tests remain fake-provider-safe and prove no adapter module, real MIDI
dependency, port opening, MIDI sending, active CLI command, hardware behavior,
profile `"4"` implementation, or profile `"3"` active-boundary support was
introduced.
