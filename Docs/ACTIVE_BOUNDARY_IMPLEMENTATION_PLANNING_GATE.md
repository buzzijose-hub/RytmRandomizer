# Active Boundary Implementation Planning Gate

## 1. Purpose

Define the planning gate before any future active boundary implementation work.

This gate exists because the project now has a completed mock-only proof for
group profile `"2"` / My BD Hard. That proof allows active-boundary planning to
be discussed more concretely, but it does not authorize active implementation,
real MIDI, port opening, CLI execution, or hardware validation.

This document is documentation-only.

## 2. Current Clean Baseline

Current branch:

- modularize-v1.34

Current HEAD before this slice:

- 269fb39 Add mock-only active candidate tests review

Current phase:

- Passive/Mock Foundation Phase
- mock-only active candidate tests accepted
- active boundary implementation planning gate now being documented

Hardware status:

- Analog Rytm MKII off
- Analog Four MKII off
- hardware not required

## 3. Accepted Proof Available

Accepted mock-only proof:

- group profile `"2"` / My BD Hard

Proof coverage:

- deterministic inert mock messages
- explicit mock-only metadata
- `MockMidiSender` in-memory recording
- unknown key safe failure
- profile `"4"` unsupported/safe behavior
- passive CLI report regression
- no real MIDI imports
- no active behavior names exposed
- closeout coverage under `=== Test: Mock-Only Active Candidate ===`

This proof remains mock-only and test-only.

## 4. Gate Decision

Active boundary implementation may not begin yet.

The next allowed step is documentation-only:

- create an active boundary implementation design/spec

That future design/spec may describe interfaces, failure modes, arming
semantics, test categories, and file ownership. It must not implement them.

## 5. Required Boundary Properties

Any future active boundary design must preserve:

- passive CLI remains read-only
- imports remain side-effect free
- no default active behavior
- no real MIDI backend
- no port opening
- no MIDI sending
- no hardware requirement
- missing arming fails safely
- unknown keys fail safely
- unsupported keys fail safely
- profile `"4"` remains parked unless separately approved
- V1.34 reference remains untouched

## 6. Future Design Questions

The next design/spec should answer:

- What is the smallest mock-first active boundary?
- What does an armed request look like in tests?
- What data does the boundary receive from passive metadata?
- What does the boundary return when not armed?
- What does the boundary return for unknown or unsupported keys?
- How does the boundary avoid importing real MIDI libraries?
- How do tests prove passive CLI commands remain passive?
- Which files would a later implementation be allowed to touch?
- What closeout label would future tests need?

## 7. Forbidden In This Gate

This gate does not add:

- implementation
- tests
- real MIDI
- mido
- MIDI port opening
- MIDI sending
- active execution
- active CLI commands
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

## 8. Preconditions Before Any Later Implementation

Before any future active boundary implementation:

- active boundary implementation design/spec must exist
- design/spec must be reviewed and accepted
- closeout must pass
- git status must be clean
- V1.34 reference diff must be empty
- passive CLI must remain read-only
- mock-only candidate tests must pass
- no real MIDI libraries may be imported
- no ports may open
- no hardware may be required

## 9. Safe Next Options

Safe next options:

- create a docs-only active boundary implementation design/spec
- pause at this clean planning gate
- create a broader progress report covering passive/mock proof
- add more mock-only safety tests only after a separate plan

## 10. Recommendation

Create a docs-only active boundary implementation design/spec next.

That spec should remain mock-first and should not add code. It should define
the future boundary carefully enough that a later implementation can be tested
without real MIDI or hardware.

## 11. Decision

Active boundary implementation planning gate is established.

The next recommended task is a docs-only active boundary implementation
design/spec.

Hardware remains off.

No implementation in this slice.
