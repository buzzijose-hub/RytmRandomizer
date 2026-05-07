# Passive Mock Foundation Roadmap

## Purpose

This document provides a current roadmap/timeline update after the
passive/mock foundation work.

It clarifies what phase the project is in now, what is complete and safe, what
must happen before mock-only active tests, and what must happen before any real
hardware validation.

This document is planning-only.

## Current Clean Baseline

Current branch:

- modularize-v1.34

Current HEAD before this slice:

- 75a2afd Add future active test plan review

Current phase:

- passive/mock foundation complete enough for planning
- future active test plan accepted as planning gate

Hardware status:

- Analog Rytm MKII off
- Analog Four MKII off
- hardware not required

## Current Phase Name

Passive/Mock Foundation Phase.

This phase is complete enough to support future planning.

It does not include:

- real MIDI
- active execution
- hardware validation

## What Is Complete And Safe

- V1.34 reference protection
- passive metadata scaffold
- validation/inspection/preview/audit helpers
- passive registry
- passive registry report
- passive CLI
- passive CLI report/list/search/inspect/preview
- passive CLI operator quickstart
- passive-to-active boundary design and review
- active-layer design/spec and review
- mock MIDI boundary plan and review
- test-only mock MIDI scaffold
- mock message mapping design/spec and review
- test-only mock message mapper
- mock mapper report
- mock mapper report CLI preview
- passive/mock foundation progress report
- future active test plan and review

## Current Supported Mock Scope

- group profile `"2"` / My BD Hard supported in mock mapper
- group profile `"3"` / My BD Classic supported in mock mapper
- group profile `"4"` / My BD Acoustic intentionally unsupported/safe
- profile 4 remains parked unless separately approved

## What Remains Intentionally Absent

- real MIDI
- mido
- MIDI port opening
- MIDI sending
- active execution
- CLI wiring to active behavior
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
- hardware validation

## Next Planning Gates

Planned gates in order:

- roadmap review / acceptance
- first-candidate mock-only active test design
- mock-only active candidate tests
- active boundary review after mock tests
- real MIDI boundary design, later
- hardware validation checklist, later
- real hardware validation, much later and only after explicit approval

## What Must Happen Before Mock-Only Active Tests

- roadmap accepted
- first-candidate mock-only design written
- candidate must be tiny, isolated, reversible, and low-risk
- no real MIDI libraries
- no ports
- no hardware
- no active CLI execution
- tests must use MockMidiSender only
- passive CLI must remain read-only
- V1.34 reference diff must remain empty
- closeout must pass
- git status must be clean

## What Must Happen Before Real Hardware Validation

- all mock-only candidate tests pass
- passive commands proven passive
- missing arming fails safely
- unknown/unsupported key fails safely
- real MIDI boundary separately designed/reviewed
- exact MIDI port confirmed
- exact command/pad/channel scope confirmed
- current Analog Rytm kit/project saved
- monitoring volume lowered
- user explicitly confirms hardware validation phase
- hardware turned on only when explicitly instructed

## Profile 4 Position

Profile `"4"` / My BD Acoustic remains parked.

Do not implement profile 4 unless separately approved.

Reasons to keep parked:

- profiles 2 and 3 already prove multiple-profile mock support
- profile 4 remains useful as unsupported/safe coverage
- no need to widen mapper scope before future active planning

Future options:

- keep parked
- write profile 4 mock-only support plan
- implement profile 4 mock-only support after explicit approval

## Suggested Next Branches

- Option A: roadmap review/acceptance checkpoint
- Option B: first-candidate mock-only active test design document
- Option C: profile 4 support plan
- Option D: pause/freeze scope at current foundation
- Option E: larger user-facing progress/timeline report

## Recommendation

- Do roadmap review/acceptance next.
- Then create first-candidate mock-only active test design.
- Do not turn on hardware.
- Do not add real MIDI.
- Do not add active CLI commands yet.
- Keep profile 4 parked.

## Decision

- Current passive/mock foundation is complete enough for planning.
- Next recommended task is roadmap review/acceptance.
- Hardware remains off.
- No implementation in this slice.
