# Future Active Test Plan Review

## Purpose

This document reviews and accepts `Docs/FUTURE_ACTIVE_TEST_PLAN.md` as the
current planning gate.

This is a review checkpoint only. It adds no implementation.

## Current Clean Baseline

Current branch:

- modularize-v1.34

Current HEAD before this slice:

- f8aa7aa Add future active test plan

Current phase:

- passive/mock foundation complete enough for current planning
- future active test plan created
- future active test plan now being reviewed

Hardware status:

- Analog Rytm MKII off
- Analog Four MKII off
- hardware not required

## Review Decision

- `Docs/FUTURE_ACTIVE_TEST_PLAN.md` is accepted as the current planning gate.
- The plan remains documentation-only.
- The plan does not authorize implementation by itself.
- The plan does not authorize turning hardware on by itself.

## Confirmed Absent Behavior

- no real MIDI
- no mido
- no MIDI port opening
- no MIDI sending
- no active execution
- no CLI wiring to active behavior
- no dispatch
- no hardware behavior
- no SysEx
- no GUI/capture
- no Analog Four support
- no Pads 5-12 support
- no machine/profile expansion
- no execute-command
- no send-command
- no hardware-test
- no hardware validation started

## Passive Commands Remain Read-Only

These remain passive/read-only:

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

## Preconditions Before Any Future Mock-Only Active Test Design

Before any mock-only active test design begins:

- clean Git status
- closeout passes
- V1.34 reference diff is empty
- `Docs/FUTURE_ACTIVE_TEST_PLAN.md` accepted
- passive/mock foundation checkpoint exists
- passive commands remain read-only
- mock MIDI remains test-only/inert
- mock mapper remains test-only/inert
- no real MIDI libraries required
- no hardware required
- no ports opened
- no active CLI behavior added

## Preconditions Before Any Future Real Hardware Validation

This remains later and is not authorized by this review.

Before any future real hardware validation:

- all mock-only test design must be reviewed
- all mock tests must pass
- missing arming must fail safely
- unknown/unsupported key must fail safely
- exact target device/port must be known
- exact command/pad/channel scope must be known
- current Rytm kit/project must be saved
- monitoring volume must be lowered
- user must explicitly confirm hardware validation phase

## Safe Next Options

- Option A: roadmap review/acceptance checkpoint.
- Option B: pause at this clean planning checkpoint.
- Option C: create a first-candidate mock-only active test design document.
- Option D: add more mock-only safety tests, but only after a separate approved design.
- Option E: keep active planning frozen and return to passive/project documentation.

## Recommendation

- Do not implement active behavior yet.
- Do not turn on hardware.
- Prefer roadmap review/acceptance next.
- Then create a first-candidate mock-only active test design document.
- Keep all future active-facing work mock-only and documentation/test-gated until explicitly approved.

## Decision

- `Docs/FUTURE_ACTIVE_TEST_PLAN.md` accepted for planning.
- `Docs/PASSIVE_MOCK_FOUNDATION_ROADMAP.md` is the next roadmap checkpoint.
- Hardware remains off.
- No implementation in this slice.
