# Branch Protection Ruleset

This document describes the branch-protection ruleset for the RytmRandomizer
repository and how it is applied.

## Integration branch

`main` is the integration branch. It does **not** exist yet — it is created as
a live-repo operation at integration time (not from a worktree). All feature
workstream branches (e.g. `ws-e-cicd`) branch from `modularize-v1.34` and merge
into `main` once it exists.

## Applying the ruleset

The ruleset is applied by an admin running:

```bash
scripts/apply-branch-protection.sh
```

That script issues the exact `gh api` call against
`/repos/buzzijose-hub/RytmRandomizer/branches/main/protection`. It must be run
once, after `main` is created, by someone with admin rights on the repo. It is
**not** run from CI or from a worktree.

## The ruleset for `main`

| Setting | Value |
|---|---|
| Require status checks to pass | Yes |
| Require branches to be up to date before merging (`strict`) | Yes |
| Required status checks | `test (windows-latest, py3.11)`, `test (macos-latest, py3.11)`, `test (ubuntu-latest, py3.11)` |
| Require pull request reviews | Yes |
| Required approving reviews | 1 |
| Dismiss stale approvals on new commits | Yes |
| Require review from Code Owners | Yes (see `.github/CODEOWNERS`) |
| Require conversation resolution before merging | Yes |
| Allow direct pushes | No (PR required) |
| Allow force pushes | No |
| Allow branch deletion | No |
| Enforce for admins | Yes |

## Required status checks — future additions

The required status check list currently covers the cross-platform test matrix
from `.github/workflows/test.yml`. Two more checks will be added to the required
list (in both `scripts/apply-branch-protection.sh` and the table above) when
their workstreams land:

- **Coverage job** — from WS-I.
- **End-to-end (e2e) job** — from WS-R.

When those jobs are added as sibling jobs in the workflow, update the `checks`
array in `scripts/apply-branch-protection.sh` and re-run the script.
