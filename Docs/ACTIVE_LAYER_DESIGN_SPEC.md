# Active Layer Design Spec

## Purpose

This document defines the future active hardware-facing layer for
RytmRandomizer.

It is design/spec only. No active behavior is implemented by this document.

## Current Baseline

Current branch:

- modularize-v1.34

Current HEAD before this slice:

- dc277e8 Add passive-to-active boundary review

Current state:

- passive CLI / dry-run foundation complete enough for report/list/search/inspect/preview

Hardware status:

- Analog Rytm MKII off
- Analog Four MKII off
- hardware not required

## Current Passive Capabilities

- report
- list commands/scenes/group profiles
- search commands/scenes/group profiles
- inspect commands/scenes/group profiles
- preview commands/scenes/group profiles

## Active Layer Non-Negotiables

- Passive CLI commands must stay passive.
- Active behavior must live behind an explicit boundary.
- No passive import may open MIDI ports.
- No passive CLI command may send MIDI.
- No active command may execute without arming.
- No hardware-facing command may run without explicit user/operator intent.

## Proposed Architecture

- Passive registry remains source of metadata truth.
- Passive preview remains the required preflight.
- Future active layer should be separate from CLI browsing/inspection code.
- Future active layer should use a mockable MIDI interface.
- Future active layer should not directly call mido/ports from high-level command logic.
- Future hardware execution should be isolated behind an adapter such as:
  - MidiPortProvider
  - MidiSender
  - HardwareExecutionContext
  - ActiveCommandExecutor

These are names for design discussion only, not implementation.

## Mockable MIDI Boundary

The future MIDI send behavior should sit behind a conceptual interface.

That interface should allow tests to verify intended CC messages without
opening real ports. It should make it impossible for unit tests to hit real
hardware accidentally.

Real MIDI output should only be used in an explicit hardware-validation script
or active command path.

## Arming Model

Future active commands must require:

- dry-run preview first
- explicit `--armed` flag
- explicit target device/port confirmation
- visible safety summary
- exact command key
- exact pad/channel scope where applicable

Missing `--armed` must fail safely. Unknown command keys must fail safely.
Unsupported command types must fail safely.

## First Active Test Candidate Constraints

Do not choose the final hardware test yet if uncertain.

The first test must be tiny, isolated, reversible, and low-risk.

It must:

- target one validated pad only
- not be a scene
- not be global mutation
- not be wild/random discovery
- not save kits/projects
- not change patterns
- not start/stop transport
- not change clock
- not use SysEx
- not touch Pads 5-12
- not touch Analog Four

## Candidate Categories For Later Review

- Single known-safe anchor load on Pad 1, if verified as reversible.
- Single simple CC on a validated pad, if it can be reset by anchor.
- No final candidate selected in this design/spec.

## Forbidden Early Active Scope

- scenes
- global mutations
- wild/random discovery
- project changes
- kit save/clear
- pattern changes
- transport/clock
- SysEx
- Pads 5-12
- Analog Four
- GUI
- capture
- reference/audio analysis
- machine/profile expansion

## Future Active CLI Naming

Possible future names only:

```powershell
python -m rytm_randomizer.cli hardware-test <key> --armed
python -m rytm_randomizer.cli execute-command <key> --armed
python -m rytm_randomizer.cli send-command <key> --armed
```

Recommendation:

- Prefer `hardware-test` for the earliest validation phase.
- Do not add these commands yet.

## Required Tests Before Implementation

Future tests must prove:

- passive report/list/search/inspect/preview commands still do not open ports
- imports are side-effect free
- missing `--armed` fails safely
- unknown key fails safely
- unsupported active command fails safely
- mocked MIDI receives expected messages only when armed
- V1.34 reference remains untouched
- no Pads 5-12 exposed
- no Analog Four exposed
- no SysEx added

## Required Operator Checklist Before First Hardware Validation

- Run closeout.
- Confirm git status clean.
- Confirm V1.34 reference diff empty.
- Save current Rytm kit/project.
- Lower monitoring volume.
- Confirm correct USB/MIDI connection.
- Confirm correct MIDI output port.
- Run passive preview for intended command.
- Confirm exact action.
- Only then turn on hardware if explicitly entering hardware-validation phase.

## Stop Conditions

- Any unexpected port opening.
- Any unexpected MIDI send.
- Any V1.34 reference change.
- Any failed closeout.
- Any unclear command scope.
- Any uncertainty about target pad/channel.
- Any user hesitation.

## Non-Goals

- no implementation
- no MIDI code
- no port opening
- no active CLI command
- no execution
- no hardware testing
- no GUI
- no capture
- no Analog Four
- no Pads 5-12
- no machine/profile expansion

## Next Recommended Task After This Spec

Review status:

- `Docs/ACTIVE_LAYER_DESIGN_SPEC_REVIEW.md`

The active-layer design/spec is accepted for planning. The next recommended
task is a test-only mock MIDI boundary plan/spec.

Mock MIDI boundary test plan:

- `Docs/MOCK_MIDI_BOUNDARY_TEST_PLAN.md`

The plan defines the future mock MIDI boundary before implementation, keeps all
MIDI behavior test-only and mockable, prevents real port opening in tests, and
keeps hardware off.

Do not implement real MIDI yet.

Hardware remains off.
