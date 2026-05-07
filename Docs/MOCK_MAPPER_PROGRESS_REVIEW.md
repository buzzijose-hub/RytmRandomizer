# Mock Mapper Progress Review

## Purpose

This document summarizes current mock mapper progress, confirms the supported
and unsupported profile scope, and captures next decision options without
implementing anything.

## Current Clean Baseline

Current branch:

- modularize-v1.34

Current HEAD before this slice:

- 55b973d Add mock mapper profile 4 decision note

Latest implemented reporting milestone:

- f7c14f2 Add passive mock mapper report

Current phase:

- passive CLI / dry-run foundation complete
- test-only mock MIDI scaffold complete
- test-only mock message mapper supports limited existing profiles

Hardware status:

- Analog Rytm MKII off
- Analog Four MKII off
- hardware not required

## Current Mock Mapper Support

Supported:

- group profile `"2"` / My BD Hard
- group profile `"3"` / My BD Classic

Unsupported by current decision:

- group profile `"4"` / My BD Acoustic

Profile `"4"` remains intentionally unsupported/safe until separately
approved.

## Passive Mock Mapper Report

The passive mock mapper report milestone adds:

- `rytm_randomizer/mock_mapper_report.py`
- `tests/test_mock_mapper_report.py`
- `Scripts/closeout_check.ps1`

The report summarizes current mock mapper state in memory only:

- supported mock mapper profiles: `"2"` / My BD Hard and `"3"` / My BD Classic
- unsupported/safe profile: `"4"` / My BD Acoustic
- mock-only status: true
- real MIDI: absent
- port opening: absent
- CLI wiring: absent
- active behavior: absent
- hardware required: false

The closeout suite now includes "Test: Mock Mapper Report".

## Current Safety Status

- No real MIDI
- No mido
- No MIDI port opening
- No MIDI sending
- No active execution
- No CLI wiring to mock mapper
- No dispatch
- No hardware behavior
- No SysEx
- No GUI/capture
- No Analog Four support
- No Pads 5-12 support
- No machine/profile expansion
- V1.34 reference remains untouched

## What Has Been Proven

- Mock mapper can support more than one existing group profile.
- Profile `"2"` behavior remained stable while adding profile `"3"`.
- Unknown keys still fail safely.
- Existing unsupported profile `"4"` remains a useful safety case.
- Mock MIDI and Mock Message Mapper tests are part of closeout.
- The mapper remains mock-only and test-only.

## Current Closeout Coverage

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

## Next Decision Options

- Option A: keep mapper scope frozen for now.
- Option B: plan profile `"4"` mock-only support in a separate reviewed slice.
- Option C: pause mapper work and write a larger project progress report.

## Recommendation

- Do not implement profile `"4"` immediately.
- Prefer either:
  - keep mapper scope frozen and produce a broader progress report
  - plan profile `"4"` support only after explicit approval
- Any profile `"4"` expansion should require explicit approval and remain
  mock-only/test-only.

## Decision

- No implementation in this slice.
- Keep profile `"4"` unsupported for now.
- Use this document as a checkpoint before deciding the next mapper direction.
