# GitHub Actions Cost Control Checkpoint

## Purpose

Record the GitHub Actions cost-control update after the account reached the
90% included-minutes warning.

This checkpoint keeps CI useful while reducing routine Actions-minute burn on
the private repository.

## Current Baseline

Current branch:

- `codex/execute-eddie-plan`

Current HEAD before this slice:

- `74c9c7e Add collaborator implementation intake status visibility`

Current PR:

- <https://github.com/buzzijose-hub/RytmRandomizer/pull/2>

Billing context:

- GitHub reported about 90% of included Actions minutes used.
- The account Actions budget is set to `$0`.
- Actions overage should stop instead of creating surprise spend.

Hardware status:

- Analog Rytm MKII off
- Analog Four MKII off
- hardware not required

## What Changed

Default test workflow:

- `.github/workflows/test.yml`

Changes:

- removed direct `push` trigger
- later removed automatic `pull_request` trigger in favor of the manual gate
- kept `workflow_dispatch`
- added `concurrency`
- enabled `cancel-in-progress: true`
- reduced the gated matrix to:
  - Ubuntu / Python 3.13
  - Windows / Python 3.13
  - macOS / Python 3.13

Manual full-matrix workflow:

- `.github/workflows/test-full-matrix.yml`

Purpose:

- preserve the full cross-OS / cross-Python safety check for final readiness
- run only when explicitly triggered

Manual full matrix:

- Windows / Python 3.11, 3.12, 3.13
- macOS / Python 3.11, 3.12, 3.13
- Ubuntu / Python 3.11, 3.12, 3.13

## Why This Helps

Before this checkpoint, one branch update with an open PR could run both:

- `push`
- `pull_request`

Each event ran the full 9-job matrix.

After this checkpoint:

- gated test runs use one 3-job matrix
- older superseded manual runs are canceled
- the full 9-job matrix remains available on demand

This keeps CI useful while protecting the remaining free Actions minutes.

## Safety Boundaries

This slice changes CI workflow configuration and tests only.

It adds no:

- real MIDI
- MIDI port opening
- MIDI sending
- active CLI command
- command dispatch
- runtime execution
- hardware behavior
- package publishing
- branch protection setting change
- collaborator branch merge
- V1.34 reference edit

## Verification

Targeted verification:

- `pytest tests/test_repo_hygiene.py::test_test_workflow_limits_actions_minutes_by_avoiding_duplicate_push_runs tests/test_repo_hygiene.py::test_test_workflow_uses_lean_pr_matrix_for_actions_minutes tests/test_repo_hygiene.py::test_full_matrix_workflow_is_manual_for_final_pr_readiness`
- `pytest tests/test_repo_hygiene.py`

Final closeout must still pass before commit.

## Next Recommended Task

Keep using local closeout for frequent feedback.

Use the regular PR workflow for pushed review updates.

Run `tests-full-matrix` manually before marking PR #2 ready or before any
major merge decision.

Follow-ups:

- `Docs/GITHUB_ACTIONS_MANUAL_GATE_CHECKPOINT.md` records the later no-pay
  policy update that made GitHub Actions manual-only during execution-plan
  work.

- `Docs/GITHUB_ACTIONS_NODE24_READINESS_CHECKPOINT.md` records the later
  workflow action-version update made after PR #2 showed Node.js 20
  deprecation warnings.
