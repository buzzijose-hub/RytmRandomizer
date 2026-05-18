# Branch Protection Ruleset

This document describes the branch-protection ruleset for the RytmRandomizer
repository and how it is applied.

## Protected integration branch

`modularize-v1.34` is the current GitHub default branch and protected
integration branch. All feature workstream branches merge into it through pull
requests after the gated build passes.

## Applying the ruleset

The ruleset is applied by an admin running:

```bash
scripts/apply-branch-protection.sh
```

That script issues the exact `gh api` call against
`/repos/buzzijose-hub/RytmRandomizer/branches/modularize-v1.34/protection`. It
must be run by someone with admin rights on the repo. It is **not** run from CI.

## The ruleset for `modularize-v1.34`

| Setting | Value |
|---|---|
| Require status checks to pass | Yes |
| Require branches to be up to date before merging (`strict`) | Yes |
| Required status checks | `required-checks` (one aggregate gate) |
| Require pull request reviews | Yes |
| Required approving reviews | 1 |
| Dismiss stale approvals on new commits | Yes |
| Require review from Code Owners | Yes (see `.github/CODEOWNERS`) |
| Require conversation resolution before merging | Yes |
| Allow direct pushes | No (PR required) |
| Allow force pushes | No |
| Allow branch deletion | No |
| Enforce for admins | Yes |

## Required status checks — the aggregate pattern

Branch protection requires exactly one status check: `required-checks`. This is
an aggregate job in `.github/workflows/test.yml` that depends on every actual
gate (`lint`, `security`, `architecture`, the 3-OS `test` matrix, the 3-OS
`e2e` matrix) and enforces the contract:

> Every upstream job either succeeded or was correctly skipped.

The individual jobs are not listed in branch protection. Two reasons:

1. **Path filtering.** Each upstream job is gated by a `detect-changes`
   preamble that classifies what files changed. A docs-only PR skips the
   3-OS test matrix entirely. Without the aggregate, GitHub branch
   protection treats a skipped required check as **pending** and blocks
   the PR forever — the aggregate translates `skipped` to `success` so
   the PR can merge.
2. **Decoupling.** Adding or renaming a matrix entry no longer requires
   editing `scripts/apply-branch-protection.sh`; only the aggregate
   job's `needs:` list changes.

When a new gate is added (e.g. a future `mypy` or `pyright` workstream),
add it to the aggregate job's `needs:` list. Do not add the new gate name
to branch protection separately.
