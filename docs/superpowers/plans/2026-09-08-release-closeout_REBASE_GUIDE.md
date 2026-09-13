# Updater collaborator migration guide

> Status: in-flight — replacement publication pending

Per [PLAN_REQUIREMENTS.md](../../PLAN_REQUIREMENTS.md), Gate 15. The replacement
branch is `codex/autoupdate-complete-bundle`, based on `modularize-v1.34`.
No replacement PR number is recorded until GitHub has the verified result.

| Original PR | Scope | Disposition |
| --- | --- | --- |
| #239 | Distribution specification | Retain author history and corrected normative context. |
| #241 | Version and release tooling | Retain history plus verified assembly/promotion repairs. |
| #242 | Native shell and frontend updater | Retain history plus real IPC, scheduling and lifecycle repairs. |
| #243 | Native acceptance, fleet and dashboard | Retain history plus executable boundary tests and accurate estimator limits. |

The original inspected stack ended at `6d1c6228`; subsequent author snapshots
included `17891251` and `a270ff11`. Integration uses merges to preserve authorship.
The original PRs remain open until the root links a verified replacement; only
then update this mapping and close the superseded stack with the replacement URL.

For a later collaborator change, fetch and compare its exact source revision
against the replacement before applying it. Do not replay all original commits
on top of a merge that already contains them. Apply only subsequent missing
commits, preserve attribution, resolve shared native/frontend/docs boundaries,
and rerun the relevant composed checks. Never force over concurrent author work.

#238 Forge is merged; its #245 UI follow-up is independent. #240 Digitakt is a
separate passive-device PR. Neither should become a base dependency for the
updater PR. Required approvals and normal checks remain in force. The
[state](2026-09-08-release-closeout_STATE.json) and
[run report](2026-09-08-release-closeout_RUN_REPORT.md) provide restart points.
