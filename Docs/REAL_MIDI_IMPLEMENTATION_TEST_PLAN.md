# Real MIDI Implementation Test Plan

## 1. Purpose

Define the future test plan that must be accepted before any real MIDI
boundary tests or implementation can begin.

Keep this document at planning altitude only.

This document does not add tests.

This document does not add real MIDI code.

This document does not add a real MIDI dependency.

This document does not authorize opening ports, sending MIDI, adding active
CLI commands, dispatching commands, executing scenes, mutating hardware, or
turning hardware on.

## 2. Current Clean Baseline

Current branch:

- modularize-v1.34

Current HEAD before this slice:

- 48941d8 Add real MIDI implementation design review

Current phase:

- Passive/Mock Foundation Phase
- project-level roadmap update accepted
- mock-first active boundary safety baseline accepted
- real MIDI boundary planning gate accepted
- real MIDI boundary plan accepted
- real MIDI implementation design/spec accepted
- real MIDI implementation test plan now being documented
- no real MIDI or hardware validation started

Hardware status:

- Analog Rytm MKII off
- Analog Four MKII off
- hardware not required

## 3. Test Plan Scope

This test plan defines future coverage only.

It may describe:

- future test file ownership
- future passive import safety tests
- future passive CLI safety tests
- future dependency absence tests
- future port-provider isolation tests
- future sender safe-failure tests
- future active-boundary scope guard tests
- future closeout integration

It does not create test files.

It does not modify closeout.

It does not add test code.

It does not add implementation code.

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

The future test plan must preserve this scope.

## 5. Future Test File Ownership

Future test implementation may use files like:

- `tests/test_real_midi_import_safety.py`
- `tests/test_real_midi_boundary.py`
- `tests/test_real_midi_passive_cli_safety.py`

Future closeout may add labels like:

- `=== Test: Real MIDI Import Safety ===`
- `=== Test: Real MIDI Boundary ===`

These files and closeout labels are proposed for future planning only.

They are not created in this slice.

## 6. Passive Import Safety Tests

Future tests must prove passive imports do not import real MIDI libraries.

Future tests should cover imports of:

- `rytm_randomizer.cli`
- `rytm_randomizer.mock_midi`
- `rytm_randomizer.mock_message_mapper`
- `rytm_randomizer.mock_mapper_report`
- `rytm_randomizer.active_boundary`
- `rytm_randomizer.active_boundary_report`

Future tests must prove these imports:

- print nothing
- do not import mido
- do not import a real MIDI backend
- do not discover ports
- do not open ports
- do not send MIDI
- do not require hardware

## 7. Passive CLI Safety Tests

Future tests must prove passive CLI commands remain read-only.

Commands that must stay passive:

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

Future tests must prove these commands do not:

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

## 8. Dependency Absence Tests

Future tests must prove ordinary test and passive CLI flows pass without real
MIDI dependencies installed.

The future dependency absence strategy should prove:

- passive import paths work without mido
- passive CLI commands work without mido
- mock-only active boundary tests work without mido
- closeout works without mido

No real MIDI dependency is added by this test plan.

## 9. Port Provider Isolation Tests

Future port-provider tests must be mock-only.

They must prove:

- port listing does not happen during passive imports
- port listing does not happen during passive CLI commands
- port listing requires an explicit future hardware-facing path
- missing port selection fails safely
- no default port is selected silently
- no port opens during ordinary unit tests

These tests must not use real ports.

These tests must not require connected hardware.

## 10. Sender Safe-Failure Tests

Future sender tests must be mock-only until a later approved hardware phase.

They must prove safe failure for:

- missing arming
- missing target port
- unavailable backend dependency
- unsupported message shape
- unknown source key
- unsupported source key
- unsupported profile `"3"`
- parked profile `"4"`

They must prove no messages are sent when validation fails.

They must prove no port opens when validation fails.

## 11. Active-Boundary Scope Guard Tests

Future tests must preserve current active-boundary scope:

- group profile `"2"` / My BD Hard is the only accepted active-boundary
  candidate
- group profile `"3"` / My BD Classic remains unsupported by the active
  boundary
- group profile `"4"` / My BD Acoustic remains parked and unsupported
- scenes remain unsupported
- commands remain unsupported
- active CLI commands remain absent

Any future widening of this scope requires a separate design/review gate.

## 12. Passive CLI Regression Tests

Future tests must preserve existing passive CLI behavior.

They must prove top-level help does not expose:

- `execute-command`
- `send-command`
- `hardware-test`
- real MIDI options
- port selection options

They must prove existing passive outputs remain deterministic.

They must prove `active-boundary-report` remains a read-only report command.

## 13. V1.34 Reference Protection

Future test implementation must preserve the current V1.34 reference rule:

- `rytm_hybrid_randomizer_v134.py` must remain untouched
- `git diff -- rytm_hybrid_randomizer_v134.py` must remain empty
- closeout must continue to report an empty V1.34 reference diff

## 14. Future Closeout Integration

Future test implementation may update closeout only after this test plan is
reviewed and accepted.

Future closeout labels should be explicit and non-duplicative.

Potential labels:

- `=== Test: Real MIDI Import Safety ===`
- `=== Test: Real MIDI Boundary ===`

Closeout must still include all current labels:

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

## 15. Future Implementation Sequence

If this test plan is reviewed and accepted, the safe future sequence is:

1. Create a narrow tests-only implementation plan.
2. Review and accept that plan.
3. Add only mock/import-safety tests.
4. Update closeout only for those accepted tests.
5. Run full closeout.
6. Review the completed tests.
7. Only then consider a tiny adapter scaffold with no real send behavior.

This sequence does not authorize adding real MIDI.

This sequence does not authorize opening ports.

This sequence does not authorize turning hardware on.

## 16. Hardware Validation Remains Later

This test plan does not authorize hardware validation.

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

This test plan does not authorize:

- implementation
- test implementation
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

- review and accept this real MIDI implementation test plan
- pause at this clean planning checkpoint
- return to passive/project documentation
- create a tests-only implementation plan after this test plan is accepted

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

Review and accept this test plan before any real MIDI-facing tests are added.

Do not implement tests in this slice.

Do not implement real MIDI.

Do not add mido.

Do not open ports.

Do not add active CLI commands.

Do not turn on hardware.

## 20. Decision

The future real MIDI implementation test strategy is defined at planning
level only.

Real MIDI implementation remains blocked.

Real MIDI test implementation remains blocked until this plan is reviewed.

Hardware validation remains blocked.

Hardware remains off.

No tests or implementation are added in this slice.

## 21. Review Gate

This real MIDI implementation test plan is reviewed and accepted by:

- `Docs/REAL_MIDI_IMPLEMENTATION_TEST_PLAN_REVIEW.md`

The review accepts this document as the current real MIDI-facing test planning
baseline. It does not authorize test implementation, real MIDI imports, mido,
port opening, MIDI sending, active CLI commands, dispatch, command execution,
scene execution, hardware behavior, profile `"4"` implementation, profile
`"3"` active-boundary support, hardware validation, or turning hardware on.
