# First-Candidate Mock-Only Active Test Design Review

## 1. Purpose

Review and accept `Docs/FIRST_CANDIDATE_MOCK_ONLY_ACTIVE_TEST_DESIGN.md` as
the current planning gate for the first mock-only active test candidate.

This is a review checkpoint only. It does not implement tests, active behavior,
MIDI, port opening, CLI execution, dispatch, or hardware validation.

## 2. Current Clean Baseline

Current branch:

- modularize-v1.34

Current HEAD before this slice:

- 833aad9 Add passive mock parallel workstream plan

Current phase:

- Passive/Mock Foundation Phase
- parallel workstream plan created
- first-candidate mock-only active test design now being reviewed

Hardware status:

- Analog Rytm MKII off
- Analog Four MKII off
- hardware not required

## 3. Review Decision

`Docs/FIRST_CANDIDATE_MOCK_ONLY_ACTIVE_TEST_DESIGN.md` is accepted as the
current planning gate.

Accepted candidate:

- group profile `"2"` / My BD Hard

The candidate remains mock-only. It is not a real hardware candidate yet.

This review does not authorize hardware validation by itself.

## 4. Accepted Candidate Scope

The accepted candidate may be used later to plan or implement mock-only tests
that prove:

- deterministic inert mock messages can be produced for group profile `"2"`
- `MockMidiSender` can record those messages in order
- candidate metadata can be inspected safely
- unknown keys fail safely
- unsupported keys fail safely
- passive CLI behavior remains read-only
- V1.34 reference remains untouched

Any implementation must remain mock-only and test-only until separately
approved.

## 5. Confirmed Boundaries

The accepted candidate does not add:

- real MIDI
- mido
- MIDI port opening
- MIDI sending
- active execution
- active CLI command
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
- profile `"4"` implementation

## 6. Profile 4 Position

Group profile `"4"` / My BD Acoustic remains parked.

It remains intentionally unsupported/safe and is not part of the accepted
first candidate.

Any future profile `"4"` support still requires a separate design/review slice.

## 7. Preconditions Before Mock-Only Implementation

Before implementing mock-only tests for this candidate:

- closeout must pass
- git status must be clean
- V1.34 reference diff must be empty
- implementation plan must be written first
- tests must use `MockMidiSender` only
- no real MIDI libraries may be imported
- no ports may open
- no hardware may be required
- passive CLI must remain read-only
- active CLI commands must remain absent

## 8. Safe Parallelization Position

The accepted next work is small enough to keep in the main thread for now.

Subagents are not needed yet.

Parallelization may be reconsidered later only if tasks have disjoint file
ownership and the user explicitly approves delegated work.

## 9. Next Recommended Task

Create a mock-only active test implementation plan for group profile `"2"` /
My BD Hard.

The plan should define:

- tests to add
- expected mock message behavior
- exact files to touch
- closeout requirements
- forbidden scope
- commit boundary

Do not implement tests in this review slice.

## 10. Decision

First-candidate mock-only active test design accepted.

Proceed next with a mock-only active test implementation plan.

Hardware remains off.

No implementation in this slice.
