# Passive Mock Foundation Decision Checkpoint

## Purpose

This document provides one current-state decision checkpoint for the
passive/mock foundation.

It summarizes what exists, what remains intentionally absent, and safe next
branches without implementing anything.

## Current Clean Baseline

Current branch:

- modularize-v1.34

Current HEAD before this slice:

- 55c5097 Update checkpoint after passive mock mapper report

Latest passive visibility milestone:

- 19659e5 Add passive mock mapper report CLI preview

Latest phase review:

- efaf086 Update checkpoint after passive mock mapper report CLI preview
- `Docs/PASSIVE_MOCK_MAPPER_CLI_PREVIEW_PHASE_REVIEW.md`

Current phase:

- passive CLI / dry-run foundation complete enough for report/list/search/inspect/preview
- mock MIDI scaffold exists and remains test-only/inert
- mock message mapper exists and remains test-only/inert
- mock mapper report exists and is included in closeout
- passive mock mapper report CLI preview exists and remains read-only
- passive mock mapper CLI preview phase review exists

Hardware status:

- Analog Rytm MKII off
- Analog Four MKII off
- hardware not required

## What Exists Now

Passive CLI:

- report
- list commands/scenes/group profiles
- search commands/scenes/group profiles
- inspect commands/scenes/group profiles
- preview commands/scenes/group profiles

Passive/mock foundation:

- passive registry/report layer
- test-only mock MIDI scaffold
- test-only mock message mapper
- passive mock mapper report
- passive mock mapper report CLI preview

Closeout coverage:

- Mock MIDI
- Mock Message Mapper
- Mock Mapper Report

## Current Mock Mapper Boundary

Supported:

- group profile `"2"` / My BD Hard
- group profile `"3"` / My BD Classic

Unsupported/safe:

- group profile `"4"` / My BD Acoustic

Profile `"4"` remains unsupported unless separately approved.

## What Remains Intentionally Absent

- real MIDI
- mido
- port opening
- MIDI sending
- active execution
- CLI wiring to mock mapper
- dispatch
- hardware behavior
- SysEx
- GUI/capture
- Analog Four support
- Pads 5-12 support
- machine/profile expansion
- execute-command
- send-command
- hardware-test

## Safety Invariants

- V1.34 reference remains untouched.
- Passive CLI remains read-only.
- Mock MIDI remains test-only.
- Mock message mapper remains test-only.
- Mock mapper report remains read-only/in-memory.
- Hardware remains off.
- No real MIDI libraries are required.

## Safe Next Branch Options

- Option A: freeze mock mapper scope here and stop/pause.
- Option B: create a profile 4 mock-only support plan, not implementation.
- Option C: write a larger project progress report.
- Option D: review whether the passive/mock foundation is ready for a future active-layer test plan, still without implementation.
- Option E: create a mock-only active command test plan, still no real MIDI and no hardware.

## Recommendation

- Do not jump to real MIDI.
- Do not turn on the Rytm.
- Do not add active CLI commands yet.
- Prefer a broader project milestone report or a future active test-plan document, still documentation-only.

## Stop Conditions

- Any real MIDI import
- Any port opening
- Any CLI active behavior
- Any dispatch/execution behavior
- Any V1.34 reference diff
- Any Pads 5-12 or Analog Four scope
- Any uncertainty about hardware state

## Decision

- Passive/mock foundation is stable enough to pause or continue with another passive-only visibility layer.
- Hardware remains off.
- No implementation in this slice.
