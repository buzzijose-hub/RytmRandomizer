# Collaborator Review Intake Checkpoint

## Purpose

Record the collaboration/review intake process now that an outside collaborator
can review the private repository.

This checkpoint defines how to receive Eddie's external AI-assisted review
without blindly changing the codebase, widening scope, or crossing any
MIDI/hardware boundary.

This document is documentation-only.

## Current Clean Baseline

Current branch:

- `modularize-v1.34`

Current HEAD before this slice:

- `3b207bd Add project status API visibility checkpoint`

Current phase:

- Passive/Mock Runtime Visibility Phase
- passive project-status dashboard includes public API hardening visibility
- real MIDI, ports, active behavior, runtime execution, dispatch, and hardware
  behavior remain absent

Hardware status:

- Analog Rytm MKII off
- Analog Four MKII off
- hardware not required

## Collaboration Context

Eddie has accepted the private repository collaboration invite and is running
an external AI-assisted review.

The screenshot indicates the review may cover:

- cross-OS consumer distribution
- code quality / architecture
- collaboration / repository hygiene

Before any action is taken, the review output should be provided as text or
Markdown so each finding can be copied, searched, referenced, and verified.

## Intake Requirements

External review findings should include:

- exact finding text
- affected file paths
- affected line numbers when possible
- severity or priority
- rationale
- suggested change
- whether the finding is about current behavior, future packaging, docs, or
  project hygiene

Screenshots alone are not enough for implementation.

## Triage Categories

Each incoming finding should be classified as one of:

- valid and urgent
- valid but later
- already handled
- needs more evidence
- not applicable to this repo
- conflicts with safety constraints
- conflicts with current user-approved project direction

Only verified findings should become implementation work.

## Verification Rules

Before implementing any external recommendation:

- inspect the relevant local files
- confirm the finding matches the current branch
- confirm the suggestion is technically correct for this codebase
- confirm the suggestion does not break existing tests or CLI behavior
- confirm the suggestion does not add scope beyond the current phase
- confirm it does not require package metadata changes unless separately
  approved
- confirm it does not affect `rytm_hybrid_randomizer_v134.py`
- run targeted tests when code changes are needed
- run full closeout before committing

## Safety Boundaries

External review feedback must not introduce:

- real MIDI
- `mido`
- `rtmidi`
- MIDI port opening
- MIDI sending
- active CLI commands
- dispatch
- command execution
- runtime execution
- hardware behavior
- SysEx
- GUI/capture
- Analog Four support
- Pads 5-12 support
- package metadata changes without explicit approval
- changes to `rytm_hybrid_randomizer_v134.py`

## Likely Useful Review Areas

The most useful near-term review findings are likely:

- Windows/macOS/Linux command assumptions
- repository hygiene
- documentation navigation
- test organization
- fixture stability
- closeout/quick-status developer workflow
- packaging readiness notes that remain planning-only for now
- code duplication or architectural seams that are already under test

## Likely Deferred Review Areas

The following should be deferred unless separately approved:

- distribution packaging implementation
- installer creation
- dependency metadata changes
- real MIDI backend changes
- active hardware behavior
- GUI implementation
- Analog Four implementation
- Pads 5-12 expansion
- large refactors without a narrow test-backed plan

## Response Process

When Eddie sends findings:

1. Save or paste the full review text into the conversation.
2. Create a triage table.
3. Verify each finding against the current codebase.
4. Identify safe quick wins.
5. Park broad or future-facing items.
6. Implement only one narrow verified item at a time.
7. Run targeted tests and full closeout.
8. Commit with a focused message.

## Current Decision

External review is welcome, but it is advisory.

The project will continue to prioritize:

- V1.34 reference protection
- passive/mock-only safety
- test-first changes
- closeout before commits
- explicit user approval for scope-widening changes

## Next Recommended Task

While waiting for Eddie's full review text:

- continue with a safe passive/mock-only software or documentation slice

After Eddie sends the review text:

- create a collaborator review triage document
- classify findings before implementation
- implement only verified, narrow, safe items

## Follow-Up: Project Status Visibility

The collaborator review intake process is now visible in the passive
project-status dashboard:

- `78ef58a Add collaborator review status visibility`
- `Docs/COLLABORATOR_REVIEW_STATUS_VISIBILITY_CHECKPOINT.md`

The dashboard records that collaborator review intake is checkpointed, findings
have not been received yet, findings should arrive as text or Markdown, and
implementation remains verify-before-implementing.
