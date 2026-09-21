# Updater collaborator migration guide

> Status: in-flight — replacement #248 published; protected review required

Per [PLAN_REQUIREMENTS.md](../../PLAN_REQUIREMENTS.md), Gate 15. The replacement
branch is `codex/autoupdate-complete-bundle`, based on `modularize-v1.34`.
The verified replacement is [PR #248](https://github.com/buzzijose-hub/RytmRandomizer/pull/248).
Its local gates and all hosted checks at `e2e46d6e` passed; Eddie's protected
review remains required. The linked PR is the authority for later source/check
changes and protected review. All four originals were closed as superseded on
September 21 after their latest heads were verified as ancestors of `e2e46d6e`.

| Original PR | Preserved latest head | Disposition |
| --- | --- | --- |
| [#239](https://github.com/buzzijose-hub/RytmRandomizer/pull/239) | `0871194b` | Closed as superseded; distribution specification and corrected normative context retained. |
| [#241](https://github.com/buzzijose-hub/RytmRandomizer/pull/241) | `2004322c` | Closed as superseded; version/release tooling plus assembly/promotion repairs retained. |
| [#242](https://github.com/buzzijose-hub/RytmRandomizer/pull/242) | `71171435` | Closed as superseded; shell/frontend plus IPC, scheduling and lifecycle repairs retained. |
| [#243](https://github.com/buzzijose-hub/RytmRandomizer/pull/243) | `a270ff11` | Closed as superseded; executable boundary tests and accurate fleet/dashboard estimator limits retained. |

The original inspected stack ended at `6d1c6228`; subsequent author snapshots
included `17891251` and `a270ff11`. Integration uses merges to preserve authorship.
Each closure comment links #248 and preserves the remaining human/Gate 9 approval
requirements. Branches were retained. Closed originals are not protected merges,
and a later author change still needs exact-head reconciliation.

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
