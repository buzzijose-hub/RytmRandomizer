# Collaborator Execution Plan Workstream Map

## Purpose

Convert Eddie's `EXECUTION_PLAN.md` into a safe, local workstream map before
any further implementation.

This document records which parts of the collaborator plan have already been
executed safely on `codex/execute-eddie-plan`, which parts remain useful but
need separate approval, and which parts are blocked by the current hardware
safety boundary.

This is documentation-only. It does not implement new code, change tests,
open ports, send MIDI, add active execution, apply GitHub admin settings, or
touch hardware.

## Current Clean Baseline

Current branch:

- `codex/execute-eddie-plan`

Current HEAD before this slice:

- `ecdae14 Add package module entry point checkpoint`

Base branch:

- `modularize-v1.34`

Draft PR:

- <https://github.com/buzzijose-hub/RytmRandomizer/pull/2>

Collaborator source branch:

- `origin/docs/review-and-execution-plan`

Collaborator source documents:

- `CODE_REVIEW_SUGGESTIONS.md`
- `EXECUTION_PLAN.md`
- `WHY_THIS_MATTERS.md`

Hardware status:

- Analog Rytm MKII off
- Analog Four MKII off
- hardware not required

## Superpowers Execution Interpretation

Eddie's plan is useful, but it is not safe to execute as one unattended
repo-wide run.

Accepted interpretation:

- Use `EXECUTION_PLAN.md` as a workstream menu.
- Execute only narrow workstreams or sub-workstreams that fit the current
  project safety boundary.
- Verify each slice locally before committing.
- Keep PR work reviewable.
- Keep hardware-facing work blocked until later explicit approval.

Rejected interpretation:

- Do not run the whole plan unattended.
- Do not merge the collaborator branch as-is.
- Do not delete or rewrite large doc areas without a curation plan.
- Do not apply branch protection/admin settings automatically.
- Do not jump to real MIDI, active CLI execution, or hardware validation.

## Work Completed Safely On This PR

The current review branch has already executed a safe subset of Eddie's plan:

- `4d74c12 Execute Wave 1 foundation plan`
- `781e9bc Add shared passive data layer`
- `2a7d979 Add repo hygiene and release scaffolding`
- `86e25f2 Fix CI portability for review branch`
- `21f1a9e Restrict quick status execution test to Windows`
- `2f30880 Install Linux MIDI build dependencies in CI`
- `3486e17 Add quality gate scaffolding`
- `008f3a4 Add cross-platform closeout check`
- `6a9b72b Route package entry point to passive CLI`
- `44193a8 Add package build verification gate`
- `4eb8d93 Add wheel install smoke gate`
- `63b6335 Add package module entry point`
- `ecdae14 Add package module entry point checkpoint`

Current safe foundation added by the branch:

- package metadata and editable install support
- passive console script entry point
- passive package module entry point
- GitHub Actions test matrix
- build verification
- installed-wheel smoke test
- cross-platform closeout script
- repo hygiene checks
- collaborator onboarding files
- README / CONTRIBUTING / SECURITY / changelog scaffolding
- passive shared data package

Important nuance:

- The branch declares MIDI dependencies because the legacy hardware script
  depends on them.
- Passive package commands remain guarded against opening ports or sending
  MIDI.
- The branch includes earlier import-safety work around the V1.34 reference;
  this document adds no additional V1.34 edits.

## Workstream Status Map

| Workstream | Eddie Plan Theme | Local Status | Decision |
| --- | --- | --- | --- |
| WS-A | Packaging foundation | Partially executed | Safe subset done: `pyproject.toml`, entry points, build, wheel smoke. Future release/version policy remains separate. |
| WS-B | Make monolith importable | Partially executed in guarded form | No more V1.34 edits without explicit approval and targeted tests. |
| WS-C | Onboarding documentation | Partially executed | README, CONTRIBUTING, PR template, collaborator quickstart, and status docs improved. Continue only with narrow docs updates. |
| WS-D | Docs accuracy triage | Not executed as broad cleanup | Needs inventory/curation plan. Do not mass-delete checkpoint docs. |
| WS-E | Repo + CI + gating | Partially executed | CI matrix, CodeQL, Dependabot, release workflow, and closeout gates added. Branch protection requires owner/admin action. |
| WS-F | Shared data layer | Partially executed | Passive shared data package exists. Further convergence needs separate design. |
| WS-G | Collapse pad-lane modules | Parked | Refactor only after behavior-parity scope stabilizes and file ownership is clear. |
| WS-H | Wire real MIDI behind `--arm` | Blocked | Future active/hardware-facing work. Not authorized on this PR. |
| WS-I | Quality gates + tooling | Partially executed | Coverage gate, repo hygiene checks, and cross-platform closeout exist. Eddie's immediate 100% coverage target is not adopted. |
| WS-J | Release process | Partially planned | Release workflow and changelog exist. Public release policy remains separate. |
| WS-K | MIDI I/O + randomization | Blocked | Requires future real MIDI boundary review and hardware validation checklist. |
| WS-L | Per-domain state objects | Parked | Needs design after behavior parity and runtime planning stabilize. |
| WS-M | Per-pad engines | Parked | Needs design after current read-only behavior helpers settle. |
| WS-N | Scene/group orchestration | Parked | No scene execution or hardware-facing orchestration yet. |
| WS-O | Shell + retire monolith | Blocked | V1.34 remains protected behavior reference. No retirement plan approved. |
| WS-P | Consolidate report modules | Parked | Possible future refactor, not urgent. Requires focused plan. |
| WS-Q | Extract CLI help text | Parked | Possible small passive cleanup, but not necessary for PR readiness. |
| WS-R | E2E validation suite | Future only | Automated passive tests exist. Real hardware validation remains later and explicit. |

## Safe To Continue On This PR

The following are safe next branches if kept narrow:

- PR readiness/status document for the current draft PR.
- Branch protection/admin instructions document, without applying settings.
- Contributor onboarding refinement.
- Docs inventory plan, without deleting docs.
- Package release checklist, without publishing.
- Passive CLI version/status visibility, if separately approved.

## Requires Separate Approval

The following need explicit approval before implementation:

- more edits to `rytm_hybrid_randomizer_v134.py`
- broad docs deletion or archival
- license/public release policy changes
- package publishing/release decisions
- branch protection/admin automation
- 100% coverage ratchet
- module consolidation refactors
- CLI help extraction
- shared data convergence beyond the current passive package

## Blocked Until Later Hardware Gates

The following remain blocked:

- real MIDI send path
- real MIDI port opening
- active CLI execution
- `execute-command`
- `send-command`
- `hardware-test`
- scene execution
- command dispatch
- runtime hardware mutation
- SysEx
- Analog Four support
- Pads 5-12 expansion
- monolith retirement
- real hardware validation

## Execution Rules For Future Workstreams

Every future workstream or sub-workstream must have:

- exact files owned by the slice
- explicit safety boundary
- targeted tests or docs-only constraints
- local verification
- full closeout
- V1.34 reference diff check for the current worktree
- clean git status before commit
- reviewable commit and PR update

## Current Decision

The collaborator plan is accepted as strategic input, not as an unattended
execution order.

The current PR has already executed the safe foundation subset. Remaining work
should continue through narrow, verified slices with the hardware boundary
intact.

## Recommended Next Task

Create a PR readiness/status checkpoint for `codex/execute-eddie-plan`, then
decide whether the next work should be:

- branch protection/admin instructions
- contributor onboarding polish
- docs inventory planning
- package release checklist
- passive CLI version/status visibility

Hardware remains off.
