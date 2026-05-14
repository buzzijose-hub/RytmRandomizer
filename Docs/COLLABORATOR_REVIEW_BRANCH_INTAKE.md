# Collaborator Review Branch Intake

## Purpose

Record Eddie's pushed review branch as an external review packet before any
implementation.

This document captures what was received, what was verified locally, which
parts look useful, and why the branch should not be merged as-is.

This is documentation-only. It does not implement findings, merge the review
branch, change code, change tests, add package metadata, add MIDI, open ports,
add active behavior, publish the repository, change licensing, or touch
hardware.

## Current Clean Baseline

Current branch:

- `modularize-v1.34`

Current HEAD before this slice:

- `e8cf521 Add collaborator quickstart`

Current source branch reviewed:

- `origin/docs/review-and-execution-plan`

Source branch commits:

- `8bfa9d1 Add code review findings and parallel execution plan`
- `e9305ac Expand execution plan and add rationale document`

Merge base with current branch:

- `1c68dc048d4def7c571cb3fcdcea73559c61293b`

Hardware status:

- Analog Rytm MKII off
- Analog Four MKII off
- hardware not required

## What Eddie Pushed

The source branch adds three top-level review/planning files:

- `CODE_REVIEW_SUGGESTIONS.md`
- `EXECUTION_PLAN.md`
- `WHY_THIS_MATTERS.md`

The review covers:

- cross-OS installation and packaging gaps
- dependency declaration gaps
- README / CONTRIBUTING / LICENSE gaps
- CI and branch protection gaps
- documentation sprawl and accuracy risks
- monolith import side effects
- V1.34 monolith versus modular package convergence risk
- shared data-layer needs
- report and CLI module sprawl
- future dry-run / arming / hardware boundary ideas
- possible parallel workstream structure

## Local Verification

The branch was inspected without checkout, merge, or cherry-pick.

Commands used:

- `git fetch --prune origin`
- `git diff --name-status HEAD..origin/docs/review-and-execution-plan`
- `git diff --stat HEAD..origin/docs/review-and-execution-plan`
- `git show origin/docs/review-and-execution-plan:CODE_REVIEW_SUGGESTIONS.md`
- `git show origin/docs/review-and-execution-plan:EXECUTION_PLAN.md`
- `git show origin/docs/review-and-execution-plan:WHY_THIS_MATTERS.md`
- `git merge-base HEAD origin/docs/review-and-execution-plan`

Verified diff shape:

- 23 files changed
- 1140 insertions
- 2840 deletions

The review files are useful as advisory input. The branch itself is not safe
to merge directly.

## Merge Safety Decision

Do not merge `origin/docs/review-and-execution-plan` as-is.

Reason:

- The branch was created from an older base.
- It would delete current collaborator review documents.
- It would remove recent project-status visibility work.
- It would modify runtime/status code and tests outside a narrow approved
  work slice.
- It includes a broad execution plan that conflicts with this project's
  current verify-before-implementing safety process.

Examples of current files the branch would delete:

- `Docs/COLLABORATOR_QUICKSTART.md`
- `Docs/COLLABORATOR_REVIEW_INTAKE_CHECKPOINT.md`
- `Docs/COLLABORATOR_REVIEW_STATUS_VISIBILITY_CHECKPOINT.md`
- `Docs/COLLABORATOR_REVIEW_STATUS_VISIBILITY_CHECKPOINT_REVIEW.md`
- `Docs/COLLABORATOR_REVIEW_TRIAGE_TEMPLATE.md`
- `Docs/COLLABORATOR_REVIEW_TRIAGE_TEMPLATE_REVIEW.md`
- `Docs/COLLABORATOR_TRIAGE_TEMPLATE_STATUS_VISIBILITY_CHECKPOINT.md`
- `Docs/PROJECT_STATUS_API_HARDENING_VISIBILITY_CHECKPOINT.md`
- `Docs/PUBLIC_API_HARDENING_PROGRESS_CHECKPOINT.md`
- `Docs/RUNTIME_PLAN_PUBLIC_API_EXPORTS_CHECKPOINT.md`

The correct path is to extract and triage the findings one by one.

## Intake Summary

The external review contains useful strategic findings, but those findings are
not implementation orders.

Accepted intake posture:

- Treat `CODE_REVIEW_SUGGESTIONS.md` as external review input.
- Treat `EXECUTION_PLAN.md` as an aggressive proposal, not an approved plan.
- Treat `WHY_THIS_MATTERS.md` as rationale, not a work authorization.
- Verify each finding against the current branch before implementation.
- Keep V1.34 protection and hardware-safety boundaries in force.
- Preserve current collaborator docs and status visibility.

## Execution Plan Workstream Map

Follow-up workstream map:

- `Docs/COLLABORATOR_EXECUTION_PLAN_WORKSTREAM_MAP.md`

The workstream map applies the Superpowers execution posture to Eddie's
`EXECUTION_PLAN.md`:

- treat the plan as a workstream menu
- record which safe foundation work has already been executed on
  `codex/execute-eddie-plan`
- keep broad or risky work parked until separately approved
- keep real MIDI, active CLI execution, port opening, and hardware validation
  blocked by later gates

This preserves the intake decision: do not merge the review branch as-is and
do not execute the plan unattended.

## Initial Triage Table

| ID | Source Theme | Local Assessment | Triage Category | Recommended Action | Status |
| --- | --- | --- | --- | --- | --- |
| CRB-001 | Packaging / dependency declaration | Likely valid, but requires package metadata changes that were previously protected unless explicitly approved. | valid_but_later | Create a separate package metadata design/approval slice before editing `pyproject.toml` or dependency files. | pending |
| CRB-002 | Cross-OS CI / branch protection | Likely valid and useful for collaboration. | valid_but_later | Create a docs-only CI/branch protection plan before adding `.github` workflow files. | pending |
| CRB-003 | README / CONTRIBUTING / LICENSE | Likely valid. License/open-source decisions require explicit owner approval and legal/project care. | valid_but_later | Create an onboarding documentation plan; keep license/public release changes separate. | pending |
| CRB-004 | Documentation sprawl / accuracy | Directionally valid, but broad deletion is risky and conflicts with current checkpoint preservation. | needs_more_evidence | Create a docs inventory/curation plan; do not delete docs wholesale. | pending |
| CRB-005 | Make V1.34 monolith importable | Technically plausible, but touches the protected reference file. | conflicts_with_safety_constraints | Requires a separate explicit approval, tight test plan, and V1.34 behavior-preservation strategy. | parked |
| CRB-006 | Shared data layer / drift prevention | Likely important for long-term convergence. | valid_but_later | Create a design/spec before moving metadata or changing runtime behavior. | pending |
| CRB-007 | `--dry-run` / `--arm` active path | Aligns with future goals, but crosses into active-facing design. | valid_but_later | Continue through approved mock-only active test planning before implementation. | pending |
| CRB-008 | Report/CLI module consolidation | Potentially useful, but not urgent while behavior parity and safety gates are active. | valid_but_later | Defer until a focused refactor plan exists. | pending |
| CRB-009 | Parallel workstreams | Useful concept after file ownership and dependencies are clear. | valid_but_later | Use only for independent work slices; avoid unattended broad execution. | pending |
| CRB-010 | Open source / license | Project policy decision, not a code finding. | needs_more_evidence | Confirm desired license, public/private repo state, and release timing in a separate approval slice. | pending |

## Confirmed Safety Boundaries

This intake does not add:

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
- license changes
- public repository changes
- changes to `rytm_hybrid_randomizer_v134.py`

## Implementation Gate

No finding from Eddie's branch may be implemented directly from this intake.

Each implementation requires a separate narrow slice with:

- exact finding selected
- current-code verification
- scope and file ownership
- safety boundary check
- targeted tests or docs-only constraints
- full closeout
- V1.34 reference diff check
- clean git status

## Recommended Next Task

Create a documentation-only review/acceptance gate for this branch intake.

After that, choose one narrow follow-up:

- CI/branch protection planning
- onboarding documentation planning
- docs inventory/curation planning
- package metadata approval planning
- first-candidate mock-only active test design

Do not merge Eddie's branch as-is.

Hardware remains off.

## Review Status

Review gate:

- `Docs/COLLABORATOR_REVIEW_BRANCH_INTAKE_REVIEW.md`

Decision:

- intake accepted
- branch remains unmerged
- findings remain advisory until separately selected and verified
