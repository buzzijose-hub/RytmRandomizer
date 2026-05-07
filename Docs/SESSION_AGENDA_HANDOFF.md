# Session Agenda Handoff

## 1. Purpose

Provide a compact current-session agenda and handoff after the accepted
project-level progress checkpoint.

This document is a practical next-work menu. It does not implement anything.

No code, tests, real MIDI, ports, active behavior, CLI execution, or hardware
behavior is added by this document.

## 2. Current Clean Baseline

Current date:

- 2026-05-07

Current branch:

- modularize-v1.34

Current HEAD before this slice:

- 6e4b35f Add project-level progress checkpoint review

Current phase:

- Passive/Mock Foundation Phase
- project-level progress checkpoint accepted
- mock-first active boundary exists for test-only evaluation
- read-only active boundary visibility exists
- no real MIDI or hardware validation started

Hardware status:

- Analog Rytm MKII off
- Analog Four MKII off
- hardware not required

## 3. Current Working Foundation

The project currently has:

- passive CLI report/list/search/inspect/preview
- passive registry and registry report
- mock MIDI scaffold
- mock message mapper and report
- mock mapper report CLI preview
- mock-only active candidate tests
- mock-first active boundary for group profile `"2"` / My BD Hard
- mock-only active boundary safety tests
- read-only active boundary report
- `active-boundary-report` passive CLI preview
- project-level progress checkpoint and review

## 4. Current Safe CLI Visibility

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

## 5. Current Scope Boundaries

Current mock mapper support:

- group profile `"2"` / My BD Hard
- group profile `"3"` / My BD Classic

Current active-boundary support:

- group profile `"2"` / My BD Hard only

Parked or unsupported:

- group profile `"3"` / My BD Classic remains unsupported by the active
  boundary
- group profile `"4"` / My BD Acoustic remains parked and unsupported
- scenes remain unsupported by the active boundary
- commands remain unsupported by the active boundary
- real hardware paths remain absent

## 6. Today's Safe Work Menu

Safe next choices are:

- pause at this clean handoff checkpoint
- write a tiny docs-only review for this session agenda
- plan additional mock-only active boundary safety coverage through a separate
  design gate
- write a future mock-only active-boundary expansion design only if scope is
  explicitly approved
- return to passive/project documentation

The most conservative next move is:

- review/accept this session agenda handoff, then decide whether to pause or
  plan additional mock-only safety coverage

## 7. Still Forbidden

Do not add:

- real MIDI
- mido
- MIDI port opening
- MIDI sending
- hardware detection
- hardware send
- active CLI command
- active execution
- dispatch
- command execution
- scene execution
- hardware behavior
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

## 8. Closeout Command

Use this command before accepting any future slice:

```powershell
powershell -ExecutionPolicy Bypass -File .\Scripts\closeout_check.ps1
```

Then confirm:

```powershell
git diff -- rytm_hybrid_randomizer_v134.py
git status --short
```

## 9. Stop Conditions

Stop immediately if:

- any real MIDI import appears
- any port opening appears
- any active CLI behavior appears
- any dispatch or execution behavior appears
- any V1.34 reference diff appears
- closeout fails
- Git status is unclear
- profile `"4"` is being implemented without explicit approval
- profile `"3"` active-boundary support is being added without explicit
  approval
- hardware state is uncertain

## 10. Decision

The session is safe to continue from the accepted project-level checkpoint.

The next recommended action is review/acceptance of this handoff or a pause at
this clean state.

Hardware remains off.

No implementation is added in this slice.

## 11. Review Gate

This handoff is reviewed and accepted by:

- `Docs/SESSION_AGENDA_HANDOFF_REVIEW.md`

The review accepts this handoff as the current practical working menu. It does
not authorize active execution, real MIDI, ports, active CLI commands,
dispatch, hardware behavior, profile `"4"` implementation, or profile `"3"`
active-boundary support.
