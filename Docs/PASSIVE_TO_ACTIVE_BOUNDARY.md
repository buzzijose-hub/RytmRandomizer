# Passive-To-Active Boundary

## Purpose

This document defines how RytmRandomizer eventually moves from passive preview
into controlled hardware execution.

It is planning only. It does not implement active behavior, MIDI behavior,
command execution, scene execution, port opening, hardware mutation, or runtime
wiring.

## Current Passive Foundation

Current branch:

- modularize-v1.34

Current HEAD before this slice:

- 163b39d Add next action handoff

Current passive CLI capability:

- report commands, scenes, and group profiles
- list commands, scenes, and group profiles
- search commands, scenes, and group profiles
- inspect commands, scenes, and group profiles
- preview commands, scenes, and group profiles

Current hardware status:

- Analog Rytm MKII off
- Analog Four MKII off
- hardware not required

## Strict Current Safety Boundary

The current phase remains passive/read-only:

- no MIDI sending
- no MIDI port opening
- no dispatch
- no command execution
- no scene execution
- no hardware mutation
- no SysEx
- no GUI
- no capture
- no Analog Four support
- no Pads 5-12 support
- no machine/profile expansion
- `rytm_hybrid_randomizer_v134.py` remains untouched

## Future Active Layer Concept

Active execution must be isolated behind an explicit boundary.

The passive CLI must remain read-only by default. Future active behavior must
require an explicit command, explicit operator intent, and clear safety checks.

The future active layer should never be reachable accidentally from passive
commands such as:

- report
- list
- search
- inspect
- preview

## Required Preconditions Before Any Hardware-Facing Test

Before any hardware-facing test is considered:

- Git status must be clean.
- Closeout must pass.
- `git diff -- rytm_hybrid_randomizer_v134.py` must be empty.
- The current kit/project must be saved on the Analog Rytm.
- Hardware volume must be lowered.
- The correct MIDI port must be identified.
- Dry-run preview must confirm the intended action.
- One tiny safe test must be selected.
- Rollback or anchor behavior must be documented.
- The user must explicitly confirm hardware is on and ready.

## Proposed Future Command Model

This section is future design only, not implementation.

Passive commands should stay as they are:

- report
- list
- search
- inspect
- preview

Future active commands should use a clearly separate verb or mode, such as:

```powershell
python -m rytm_randomizer.cli execute-command <key> --armed
python -m rytm_randomizer.cli send-command <key> --armed
python -m rytm_randomizer.cli hardware-test <key> --armed
```

Active command names should not be added until the execution boundary and tests
are designed.

## Arming Model

Future hardware-facing behavior should require:

- dry-run preview first
- explicit `--armed` flag
- explicit hardware target or port selection
- visible safety summary before send
- no default send behavior

Missing `--armed` should fail safely.

## First Hardware-Facing Test Candidate

The first active test should be tiny and low-risk.

It should not be:

- scenes
- global mutation
- wild mutation
- pattern changes
- kit saves
- project changes
- SysEx
- transport
- clock

A candidate could be a known safe anchor or a simple CC on a single validated
pad only after design review.

This remains planning only. No final hardware-facing test is selected here.

## Forbidden Active Actions For Early Hardware Phase

Early hardware-facing work must not include:

- project change
- kit save
- kit clear
- pattern change
- transport start/stop
- clock changes
- unvalidated SysEx
- Pads 5-12
- Analog Four
- scenes/global mutation
- wild/random discovery commands
- any action without preview and arming

## Testing Requirements For Future Active Layer

Future active behavior must have tests proving:

- passive commands remain passive
- no ports open during passive imports or passive CLI commands
- missing `--armed` fails safely
- `rytm_hybrid_randomizer_v134.py` remains untouched
- MIDI sending is isolated behind a mockable interface before real hardware validation

## Operator Checklist Before Turning Hardware On

Before turning hardware on for a future hardware-facing validation phase:

- Save current Rytm kit/project.
- Lower monitoring volume.
- Confirm USB/MIDI connection.
- Confirm correct MIDI port.
- Run closeout.
- Run preview.
- Confirm exact intended action.
- Turn on hardware only when explicitly entering a hardware-facing validation phase.

## Non-Goals

This slice does not include:

- implementation
- MIDI code
- port opening
- execution command
- GUI
- capture
- Analog Four
- Pads 5-12
- hardware testing

## Next Recommended Task

Review status:

- `Docs/PASSIVE_TO_ACTIVE_BOUNDARY_REVIEW.md`

The boundary has an acceptance checkpoint for planning. That review confirms no
active behavior exists yet, keeps hardware off, and sets the next recommended
task as active-layer design/spec only.

Active-layer design/spec:

- `Docs/ACTIVE_LAYER_DESIGN_SPEC.md`

The spec designs the future active/hardware-facing layer without
implementation, preserves passive behavior, keeps hardware off, and defines
arming, a mock MIDI boundary, forbidden scope, and testing requirements.

Active-layer design/spec review:

- `Docs/ACTIVE_LAYER_DESIGN_SPEC_REVIEW.md`

The review confirms acceptance of the active-layer design/spec for planning,
records that no active behavior exists yet, sets the next recommended task as
mock MIDI boundary planning/test-only design, and keeps hardware off.

Mock MIDI boundary test plan:

- `Docs/MOCK_MIDI_BOUNDARY_TEST_PLAN.md`

The plan defines the future mock MIDI boundary before implementation, keeps all
MIDI behavior test-only and mockable, prevents real port opening in tests, and
keeps hardware off.

Keep hardware off until then.
