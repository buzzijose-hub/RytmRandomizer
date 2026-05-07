# Project-Level No-Dependency Roadmap Update

## 1. Purpose

Provide a project-level roadmap update after the accepted real MIDI
no-dependency progress checkpoint.

Zoom out from the current passive/mock foundation, mock-first active boundary,
fake-provider-only adapter boundary, and accepted dependency candidate
evaluation.

Clarify what is complete, what remains intentionally absent, what is parked,
and what the safe next branches are before any future dependency, package
metadata, real MIDI, or hardware-facing work.

This roadmap is documentation-only.

No implementation, tests, dependency selection, package metadata edits, real
MIDI, ports, active CLI behavior, dispatch, execution, or hardware behavior is
added by this document.

## 2. Current Clean Baseline

Current branch:

- modularize-v1.34

Current HEAD before this slice:

- 46e5ca8 Add real MIDI no-dependency progress checkpoint

Current phase:

- Passive/Mock Foundation Phase
- mock-first active boundary exists for test-only evaluation
- read-only active boundary report and CLI preview exist
- first fake-provider-only real MIDI adapter boundary exists
- real MIDI dependency candidate evaluation and review are accepted
- real MIDI no-dependency progress checkpoint exists
- no real MIDI dependency is selected

Hardware status:

- Analog Rytm MKII off
- Analog Four MKII off
- hardware not required

## 3. Current Phase Name

Current phase:

- Passive/Mock Foundation Phase with fake-provider-only adapter boundary
  safety and accepted no-dependency decision

This phase is still:

- passive by default
- mock-only for active-boundary evaluation
- fake-provider-only for real MIDI adapter boundary tests
- read-only from CLI
- hardware-off
- not a real MIDI dependency phase
- not a package metadata change phase
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
- active boundary implementation planning gate, design/spec, plan, and reviews
- mock-first active boundary
- mock-first active boundary checkpoint and review
- mock-only active boundary safety tests
- additional mock-only active boundary safety tests
- read-only active boundary report
- active-boundary-report passive CLI preview
- active boundary safety progress report and review
- real MIDI boundary planning gates
- real MIDI adapter-specific test planning gates
- real MIDI import and passive CLI safety tests
- fake-provider-only real MIDI adapter boundary
- real MIDI dependency decision and re-decision gates
- real MIDI dependency candidate evaluation and review
- real MIDI no-dependency progress checkpoint

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

They do not construct or use real MIDI backends.

They do not open ports or send MIDI.

They do not require hardware.

## 6. Current Mock And Boundary Scope

Current mock mapper support:

- group profile `"2"` / My BD Hard
- group profile `"3"` / My BD Classic

Current parked or unsupported mapper scope:

- group profile `"4"` / My BD Acoustic remains unsupported/safe

Current active-boundary support:

- group profile `"2"` / My BD Hard only

Current unsupported active-boundary scope:

- group profile `"3"` / My BD Classic
- group profile `"4"` / My BD Acoustic
- scenes
- commands
- global mutations
- unsupported source kinds
- real hardware paths

Current fake-provider-only real MIDI adapter boundary:

- can be tested without a real MIDI dependency
- does not import `mido`
- does not open real ports
- does not send MIDI
- remains isolated from passive CLI behavior

## 7. Accepted Dependency Position

The accepted dependency position is:

- Candidate A: continue with no real MIDI dependency
- dependency selection remains deferred
- package metadata remains unchanged
- fake-provider-only adapter boundary remains the current adapter baseline
- passive CLI remains isolated from MIDI backend behavior
- hardware validation remains blocked
- hardware remains off

The following candidates remain not selected:

- Candidate B: future `mido`-style adapter backend
- Candidate C: future direct backend adapter
- Candidate D: custom or OS-specific MIDI path

## 8. What Remains Intentionally Absent

Intentionally absent:

- `mido`
- real MIDI dependency
- package metadata changes
- real MIDI backend
- real port discovery
- real port listing
- real port opening
- real MIDI sending
- active CLI command
- execute-command
- send-command
- hardware-test
- dispatch
- command execution
- scene execution
- hardware behavior
- hardware detection
- SysEx
- GUI/capture
- Analog Four support
- Pads 5-12 support
- machine/profile expansion
- profile `"4"` implementation
- profile `"3"` active-boundary support
- hardware validation
- hardware-on authorization

## 9. Current Closeout Coverage

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
- real MIDI import safety
- real MIDI passive CLI safety
- real MIDI adapter boundary

The closeout workflow also checks:

- protected V1.34 reference diff
- Git status

## 10. What This Roadmap Means

The project now has a substantial passive/mock foundation and a fake-provider
adapter boundary, but it is still intentionally not a real MIDI or hardware
validation system.

This roadmap keeps the project oriented around the safest current path:

- preserve the working V1.34 reference
- keep passive CLI behavior passive
- keep adapter work fake-provider-only
- keep dependency selection deferred
- keep package metadata unchanged
- keep hardware off

## 11. Safe Next Branches

Safe next branches:

- pause at this clean roadmap checkpoint
- create a documentation-only review/acceptance gate for this roadmap
- return to passive/project documentation
- create a documentation-only package metadata plan only after explicit
  approval
- create a future dependency selection review only after explicit approval
- create broader user-facing progress notes if a session handoff is needed

## 12. Recommendation

Do a documentation-only review/acceptance gate for this roadmap next.

Do not select a real MIDI dependency yet.

Do not change package metadata.

Do not add active CLI commands.

Do not open ports.

Do not send MIDI.

Do not turn on hardware.

## 13. Decision

The current project remains in the Passive/Mock Foundation Phase with
fake-provider-only adapter boundary safety and accepted no-dependency
position.

The roadmap is updated for planning.

Hardware remains off.

No implementation is added by this slice.
