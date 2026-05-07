# Project-Level Roadmap Update

## 1. Purpose

Provide a fresh project-level roadmap update after the accepted active
boundary safety progress report review.

Zoom out from the current passive/mock foundation and mock-first active
boundary safety baseline.

Clarify what is complete, what remains intentionally absent, what is parked,
and what the safe next branches are.

This roadmap is documentation-only.

No implementation, tests, real MIDI, ports, active behavior, CLI execution,
dispatch, or hardware behavior is added by this document.

## 2. Current Clean Baseline

Current branch:

- modularize-v1.34

Current HEAD before this slice:

- b21eecc Add active boundary safety progress report review

Current phase:

- Passive/Mock Foundation Phase
- mock-first active boundary safety baseline accepted
- passive CLI visibility exists
- read-only active boundary report and CLI preview exist
- no real MIDI or hardware validation started

Hardware status:

- Analog Rytm MKII off
- Analog Four MKII off
- hardware not required

## 3. Current Phase Name

Current phase:

- Passive/Mock Foundation Phase with accepted mock-first active boundary
  safety baseline

This phase is still:

- passive by default
- mock-only for active-boundary evaluation
- read-only from CLI
- hardware-off
- not a real MIDI phase
- not a hardware validation phase

## 4. Completed Safe Foundation

The current safe foundation includes:

- protected V1.34 reference
- passive metadata scaffold
- passive validation, inspection, preview, and audit helpers
- passive registry
- passive registry report
- passive CLI
- passive CLI report/list/search/inspect/preview paths
- passive CLI operator quickstart
- mock MIDI scaffold
- mock message mapper
- mock mapper report
- mock mapper report CLI preview
- future active test plan and review
- passive/mock foundation roadmap and review
- first-candidate mock-only active test design and review
- mock-only active candidate tests
- active boundary implementation planning gate
- active boundary implementation design/spec and review
- active boundary implementation plan
- mock-first active boundary
- mock-first active boundary checkpoint and review
- mock-only active boundary safety tests
- read-only active boundary report
- active-boundary-report passive CLI preview
- project-level progress checkpoint and review
- additional active boundary safety tests
- active boundary safety progress report and review

## 5. Current CLI Visibility

Known safe passive CLI paths include:

```powershell
python -m rytm_randomizer.cli report
python -m rytm_randomizer.cli list-commands
python -m rytm_randomizer.cli list-scenes
python -m rytm_randomizer.cli list-group-profiles
python -m rytm_randomizer.cli search-commands BD
python -m rytm_randomizer.cli search-scenes Wild
python -m rytm_randomizer.cli inspect-command J
python -m rytm_randomizer.cli inspect-scene S1A
python -m rytm_randomizer.cli inspect-group-profile 2
python -m rytm_randomizer.cli preview-command J
python -m rytm_randomizer.cli preview-scene S1A
python -m rytm_randomizer.cli preview-group-profile 2
python -m rytm_randomizer.cli mock-mapper-report
python -m rytm_randomizer.cli active-boundary-report
```

These commands remain read-only.

They do not evaluate active boundary requests.

They do not construct `MockMidiSender`.

They do not open ports or send MIDI.

## 6. Current Mock And Active-Boundary Scope

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

Profile `"3"` active-boundary support and profile `"4"` implementation remain
blocked unless separately approved through a future design/review gate.

## 7. Current Closeout Coverage

The closeout suite includes:

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

The closeout workflow also checks:

- `git diff -- rytm_hybrid_randomizer_v134.py`
- `git status --short`

## 8. What Remains Intentionally Absent

The project still has no:

- real MIDI
- mido
- MIDI port opening
- MIDI sending
- hardware detection
- hardware send
- active CLI command
- active execution
- passive CLI active-boundary evaluation
- passive CLI construction of `MockMidiSender`
- dispatch
- command execution
- scene execution
- hardware behavior
- hardware mutation
- SysEx
- GUI/capture
- Analog Four support
- Pads 5-12 support
- machine/profile expansion
- execute-command
- send-command
- hardware-test
- hardware validation
- profile `"4"` implementation
- profile `"3"` active-boundary support

## 9. Roadmap From Here

Current checkpoint:

- accepted mock-first active boundary safety baseline

Immediate safe options:

- pause at this clean roadmap checkpoint
- review and accept this roadmap update
- return to passive/project documentation
- create a docs-only design for any future mock-only safety tests
- create a docs-only design for any future passive visibility layer

Later planning options, still documentation-only:

- design a real MIDI boundary without implementation
- design a hardware validation checklist without turning hardware on
- design future active CLI naming without adding commands
- design profile `"3"` active-boundary support only if explicitly approved
- design profile `"4"` mock or active-boundary support only if explicitly
  approved

Much later, only after explicit approval and additional gates:

- mock-only implementation expansion
- real MIDI adapter design and tests
- hardware validation planning
- real hardware validation

## 10. Profile 3 And Profile 4 Position

Profile `"3"` / My BD Classic:

- supported by the mock message mapper
- visible in mock mapper reporting
- unsupported by the active boundary
- must not become active-boundary scope without separate approval

Profile `"4"` / My BD Acoustic:

- parked
- unsupported by the mock mapper
- unsupported by the active boundary
- useful as an unsupported/safe case
- must not be implemented without separate approval

## 11. Real MIDI And Hardware Position

Real MIDI remains out of scope.

Hardware validation remains out of scope.

Before any real MIDI or hardware work, the project still needs:

- a docs-only real MIDI boundary plan
- a separate review gate for that plan
- mock-only tests proving passive commands remain passive
- mock-only tests proving any candidate behavior is isolated
- explicit operator confirmation
- clean closeout
- clean Git status
- empty V1.34 reference diff
- saved Analog Rytm kit/project
- lowered monitoring volume
- confirmed exact MIDI port
- explicit hardware validation phase

Analog Rytm and Analog Four remain off.

## 12. Recommendation

Prefer review/acceptance of this roadmap update or pause at this clean
checkpoint.

Do not add real MIDI.

Do not open ports.

Do not add active CLI commands.

Do not turn on hardware.

Keep profile `"3"` and profile `"4"` outside active-boundary scope unless a
future design/review explicitly approves otherwise.

## 13. Decision

The current roadmap keeps the project in the Passive/Mock Foundation Phase
with an accepted mock-first active boundary safety baseline.

Hardware remains off.

No implementation is added in this slice.
