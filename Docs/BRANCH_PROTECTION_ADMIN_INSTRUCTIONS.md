# Branch Protection Admin Instructions

## Purpose

Document how the repository owner can apply branch protection after reviewing
PR #2.

This is an admin instruction document only. It does not apply branch
protection, change repository settings, run GitHub API commands, add runtime
behavior, open ports, send MIDI, or touch hardware.

## Current Baseline

Current review branch:

- `codex/execute-eddie-plan`

Current HEAD before this slice:

- `5d1e6e3 Add PR 2 readiness checkpoint`

Draft PR:

- <https://github.com/buzzijose-hub/RytmRandomizer/pull/2>

Target protected branch:

- `modularize-v1.34`

Repository:

- `buzzijose-hub/RytmRandomizer`

Hardware status:

- Analog Rytm MKII off
- Analog Four MKII off
- hardware not required

## When To Apply Protection

Do not apply branch protection before:

- PR #2 has been reviewed by the owner
- collaborator review has been considered
- the V1.34 import-safety diff has been inspected
- package metadata has been inspected
- GitHub Actions are green on the final PR head
- the owner is ready for PR-based changes to become the normal workflow

Branch protection is not required for local development. It is a repository
governance step for keeping the shared GitHub branch stable.

## Recommended Initial Protection Policy

Recommended first policy for `modularize-v1.34`:

- require a pull request before merging
- require at least one approval
- require status checks to pass
- require branches to be up to date before merging
- include administrators only if the owner wants the same rules to apply to
  their own pushes
- allow force pushes: disabled
- allow deletions: disabled

Recommended required status checks after the cost-control update:

- `windows-latest / Python 3.13`
- `macos-latest / Python 3.13`
- `ubuntu-latest / Python 3.13`

The full Windows/macOS/Ubuntu and Python 3.11/3.12/3.13 matrix remains
available as the manual `tests-full-matrix` workflow for final PR readiness.
Do not require manual-only checks in branch protection unless the owner wants
to manually run them before every merge.

Optional later checks:

- CodeQL
- release dry-run or package publish gate
- stronger coverage ratchet, only after separate approval

## GitHub UI Path

Safer manual path:

1. Open the repository on GitHub.
2. Go to `Settings`.
3. Open `Branches`.
4. Add a branch protection rule.
5. Branch name pattern:
   - `modularize-v1.34`
6. Enable pull request requirement.
7. Require at least one approval.
8. Require status checks.
9. Select the required checks listed above.
10. Disable force pushes.
11. Disable branch deletion.
12. Save the rule.

This UI path is preferred for the first setup because the owner can inspect
every setting before applying it.

## Scripted Path

Script present in the repo:

- `Scripts/apply_branch_protection.ps1`

Example command:

```powershell
powershell -ExecutionPolicy Bypass -File .\Scripts\apply_branch_protection.ps1 `
    -Repository "buzzijose-hub/RytmRandomizer" `
    -Branch "modularize-v1.34"
```

Important:

- The script requires authenticated `gh`.
- The script calls the GitHub API.
- The script changes remote repository settings.
- Do not run it unless the owner intentionally chooses the scripted path.

The script should be reviewed before use. If GitHub branch protection schema
changes or stricter status-check names are needed, update the script in a
separate reviewed slice before running it.

## What This Does Not Authorize

This document does not authorize:

- merging PR #2
- marking PR #2 ready for review
- publishing a release
- making the repository public
- changing license policy
- deleting docs
- editing V1.34
- adding real MIDI behavior
- opening MIDI ports
- sending MIDI
- adding active CLI execution
- running hardware validation

## Safety Boundaries

Branch protection is repository governance only.

It must not change:

- passive CLI behavior
- package runtime behavior
- mock MIDI behavior
- active boundary behavior
- V1.34 reference behavior
- hardware state

Hardware remains off.

## Recommended Next Task

Review PR #2 with Eddie and decide whether to:

- keep it draft for more review
- update PR documentation
- create a docs inventory plan
- create a package release checklist
- create contributor onboarding polish
- apply branch protection after merge readiness is clear
