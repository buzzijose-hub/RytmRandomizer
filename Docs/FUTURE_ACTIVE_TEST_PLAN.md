# Future Active Test Plan

## Purpose

This document defines what must be proven before active/hardware-facing
behavior exists.

It stays at planning altitude only:

- no active execution is implemented by this document
- no MIDI code is implemented by this document
- no hardware validation is performed by this document

## Current Clean Baseline

Current branch:

- modularize-v1.34

Current HEAD before this slice:

- 2e951c2 Add passive mock foundation progress report

Current phase:

- passive CLI / dry-run foundation complete
- mock MIDI scaffold complete
- mock message mapper/report complete
- future active test-plan now being documented

Hardware status:

- Analog Rytm MKII off
- Analog Four MKII off
- hardware not required

## What Must Be Proven With Mock-Only Tests First

- Passive CLI commands do not open ports.
- Passive CLI commands do not send MIDI.
- Passive imports are side-effect free.
- Mock MIDI messages can represent intended actions.
- Mock senders record messages in memory only.
- Unknown keys fail safely.
- Unsupported keys fail safely.
- Missing arming fails safely in any future active path.
- No real MIDI libraries are imported in unit tests.
- No real hardware is required.
- V1.34 reference remains untouched.

## Passive Commands That Must Remain Untouched

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

These must remain read-only and must never trigger active behavior.

## Future Meaning Of Armed

This is a future concept only.

Armed should mean:

- explicit operator confirmation
- not default behavior
- required before any future hardware-facing path

Missing `--armed` must fail safely.

Armed mode must still require:

- exact command key
- exact target device
- exact MIDI port
- passive preview first
- visible safety summary
- clean closeout
- clean git status

Armed mode does not exist yet.

## First Real-Hardware Candidate Discussion

This document does not select the final candidate.

The candidate must be:

- tiny
- isolated
- reversible
- low-risk
- limited to one validated pad only

The candidate must not be:

- a scene
- global mutation
- wild/random discovery
- kit/project save behavior
- pattern change
- transport start/stop
- clock change
- SysEx
- Pads 5-12
- Analog Four

Potential categories for later review:

- a single known-safe anchor-related action on Pad 1
- a single simple CC-like mock-mapped action on a validated pad
- a test-only command proven in MockMidiSender first

## Required Pre-Hardware Checklist

- Run full closeout.
- Confirm git status clean.
- Confirm V1.34 reference diff empty.
- Save current Rytm kit/project.
- Lower monitoring volume.
- Confirm correct USB/MIDI connection.
- Confirm exact MIDI output port.
- Run passive preview for intended action.
- Run mock test for intended action.
- Confirm exact pad/channel scope.
- Confirm no forbidden action involved.
- User explicitly confirms hardware validation phase.

## Exact Stop Conditions

Stop immediately if:

- any real MIDI library is introduced unexpectedly
- any port opens during passive commands
- any MIDI is sent outside an explicit future hardware-validation phase
- any passive command triggers active behavior
- any V1.34 reference diff appears
- any closeout test fails
- any git status is not clean
- any target pad/channel is unclear
- any command scope is unclear
- any scene/global mutation is proposed as first hardware test
- any SysEx/project/kit/pattern/transport/clock behavior appears
- user hesitates or hardware state is uncertain

## Forbidden First-Active Scope

- scenes
- global mutations
- wild/random discovery
- project change
- kit save
- kit clear
- pattern change
- transport
- clock
- SysEx
- Pads 5-12
- Analog Four
- GUI/capture
- reference/audio analysis
- machine/profile expansion

## Required Future Test Categories

Before implementation:

- passive safety regression tests
- mock message mapping tests
- arming failure tests
- unknown/unsupported key tests
- no-port-opening tests
- no-real-MIDI-import tests
- V1.34 untouched test/check
- first-candidate mock behavior tests

## Hardware Stays Off

- Analog Rytm MKII remains off during this planning phase.
- Analog Four MKII remains off during this planning phase.
- Hardware is not required for this document.
- Hardware must not be turned on until a later explicit hardware-validation phase.

## Non-Goals

- no implementation
- no active CLI command
- no real MIDI
- no port opening
- no hardware validation
- no execution
- no dispatch
- no SysEx
- no GUI
- no capture
- no Analog Four
- no Pads 5-12
- no profile 4 implementation

## Next Recommended Task

Review status:

- `Docs/FUTURE_ACTIVE_TEST_PLAN_REVIEW.md`

The future active test-plan is accepted as the current planning gate. The
review confirms that no implementation exists, hardware remains off, and this
plan does not authorize implementation or hardware validation by itself.

Then decide whether to:

- add more mock-only test coverage
- create a first-candidate mock-only test design
- pause and produce a broader project roadmap

Hardware remains off.
