# Collaborator Review Triage Template

## Purpose

Provide a reusable template for triaging Eddie's external AI-assisted review
findings before any implementation.

This document is intentionally empty of findings until Eddie sends the review
as text or Markdown. It exists so the next review step has a clear, safe
landing zone.

This template is documentation-only. It does not implement findings, change
code, change tests, add package metadata, add MIDI, open ports, add active
behavior, or touch hardware.

## Current Clean Baseline

Current branch:

- `modularize-v1.34`

Current HEAD before this slice:

- `0c6a98b Add collaborator review status visibility review`

Current review state:

- Eddie has collaborator access to the private repository.
- External AI-assisted review is pending.
- No findings have been received as text or Markdown yet.
- Screenshot-only review output is not enough for implementation.

Hardware status:

- Analog Rytm MKII off
- Analog Four MKII off
- hardware not required

## Intake Rules

Before a finding becomes work, record:

- exact finding text
- source of finding
- affected file path
- affected line number when available
- severity or priority
- rationale
- proposed change
- local verification notes
- final triage category
- recommended next action

If any of those fields are missing, the finding can still be recorded, but it
should usually be classified as `needs_more_evidence` until verified locally.

## Triage Categories

Use exactly one category per finding:

- `valid_and_urgent`
- `valid_but_later`
- `already_handled`
- `needs_more_evidence`
- `not_applicable_to_this_repo`
- `conflicts_with_safety_constraints`
- `conflicts_with_current_project_direction`

## Safety Boundaries

No external review finding may introduce these without separate explicit
approval:

- real MIDI
- `mido`
- `rtmidi`
- MIDI port opening
- MIDI sending
- active CLI command
- dispatch
- command execution
- runtime execution
- hardware behavior
- SysEx
- GUI/capture
- Analog Four support
- Pads 5-12 support
- package metadata changes
- changes to `rytm_hybrid_randomizer_v134.py`

## Finding Table

Use this table when review text arrives.

| ID | Source | Finding | Files / Lines | Severity | Local Verification | Triage Category | Recommended Action | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| CR-001 | pending | pending review text | pending | pending | pending | needs_more_evidence | wait for text or Markdown finding | pending |

## Verification Checklist For Each Finding

For each finding, confirm:

- the finding applies to the current branch
- the affected file still exists
- the cited code still matches the finding
- the finding is not already handled
- the suggested fix is compatible with current architecture
- the suggested fix preserves passive/mock-only boundaries
- the suggested fix does not require package metadata unless separately
  approved
- the suggested fix does not touch `rytm_hybrid_randomizer_v134.py`
- targeted tests are identified before implementation
- full closeout remains required before commit

## Implementation Gate

Do not implement directly from this template.

Implementation requires a separate narrow work slice with:

- one verified finding or a small tightly related set of findings
- clear file ownership
- targeted tests when code changes are needed
- full closeout
- protected V1.34 reference diff check
- package metadata diff check

## Current Decision

This template is ready for Eddie's full review text.

Until findings arrive as text or Markdown, continue with safe
passive/mock-only work.

## Next Recommended Task

If Eddie sends review text:

- create a filled collaborator review triage document from this template
- classify findings before implementation
- implement only verified, narrow, safe items

If no review text has arrived:

- continue with passive/mock-only behavior parity, visibility, or
  documentation work
