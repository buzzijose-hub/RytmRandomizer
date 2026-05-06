# Passive-To-Active Boundary Review

## Purpose

This document reviews and accepts the passive-to-active boundary design.

It confirms that the project is still passive/read-only and that no
hardware-facing behavior has been implemented.

## Current Clean Baseline

Current branch:

- modularize-v1.34

Current HEAD before this slice:

- 6282cbc Add passive-to-active boundary design

Current phase:

- passive CLI / dry-run foundation

Current hardware status:

- Analog Rytm MKII off
- Analog Four MKII off
- hardware not required

## Boundary Acceptance Summary

`PASSIVE_TO_ACTIVE_BOUNDARY.md` is accepted as the current planning boundary.

- Passive CLI remains read-only by default.
- Future active execution must be isolated behind explicit active commands.
- Future active execution must require explicit operator intent and arming.
- Passive commands must never accidentally reach hardware execution.

## Current Passive CLI Capability

- report
- list commands/scenes/group profiles
- search commands/scenes/group profiles
- inspect commands/scenes/group profiles
- preview commands/scenes/group profiles

## Confirmed Safety Invariants

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

## Preconditions Before Any Future Hardware-Facing Implementation

- clean Git status
- closeout passes
- V1.34 reference diff is empty
- passive preview exists for intended action
- active layer design/spec exists
- MIDI interface is mockable/testable
- missing arming fails safely
- user explicitly confirms hardware is ready
- Analog Rytm project/kit saved
- monitoring volume lowered
- correct MIDI port identified

## First Active-Layer Design Target

Do not implement active behavior yet.

The active-layer design/spec lives in:

- `Docs/ACTIVE_LAYER_DESIGN_SPEC.md`
- `Docs/ACTIVE_LAYER_DESIGN_SPEC_REVIEW.md`

The spec defines:

- mockable MIDI boundary
- arming model
- allowed first test candidate
- forbidden actions
- tests before any real hardware validation

The mock MIDI boundary test plan lives in:

- `Docs/MOCK_MIDI_BOUNDARY_TEST_PLAN.md`
- `Docs/MOCK_MIDI_BOUNDARY_TEST_PLAN_REVIEW.md`

That plan defines the future mock MIDI boundary before implementation, keeps
all MIDI behavior test-only and mockable, prevents real port opening in tests,
and keeps hardware off.

The review accepts the mock MIDI boundary test plan for planning and sets the
next recommended task as test-only mock MIDI scaffold/design.

## Rejected/Forbidden Next Moves

- Do not jump directly to MIDI sending.
- Do not turn on the Rytm yet.
- Do not add execute-command yet.
- Do not add send-command yet.
- Do not add scene execution.
- Do not add global mutation execution.
- Do not add Pads 5-12.
- Do not add Analog Four.
- Do not add GUI/capture.

## Decision

- Boundary accepted for planning.
- Active-layer design/spec accepted for planning.
- Mock MIDI boundary test plan accepted for planning.
- Proceed next with test-only mock MIDI scaffold/design.
- Hardware remains off.
