# GitHub Actions Node 24 Readiness Checkpoint

## Purpose

Record the GitHub Actions maintenance update after PR #2 showed Node.js 20
deprecation warnings for JavaScript-based Actions.

This checkpoint keeps CI ready for GitHub's Node 24 runner transition without
changing runtime behavior.

## Current Baseline

Current branch:

- `codex/execute-eddie-plan`

Current HEAD before this slice:

- `3170470 Add GitHub Actions cost controls`

Current PR:

- <https://github.com/buzzijose-hub/RytmRandomizer/pull/2>

Hardware status:

- Analog Rytm MKII off
- Analog Four MKII off
- hardware not required

## What Changed

Workflow action versions were updated to current major versions that are
available upstream:

- `actions/checkout@v4` to `actions/checkout@v5`
- `actions/setup-python@v5` to `actions/setup-python@v6`
- `actions/upload-artifact@v4` to `actions/upload-artifact@v5`
- `github/codeql-action/init@v3` to `github/codeql-action/init@v4`
- `github/codeql-action/analyze@v3` to `github/codeql-action/analyze@v4`

Updated workflows:

- `.github/workflows/test.yml`
- `.github/workflows/test-full-matrix.yml`
- `.github/workflows/release.yml`
- `.github/workflows/codeql.yml`

## Why This Helps

GitHub Actions reported that Node.js 20-based actions are deprecated and will
move to Node 24 defaults.

Updating the action major versions now should prevent PR #2 from carrying that
warning forward and keeps the repository prepared for later CI runs.

## Safety Boundaries

This slice changes CI workflow configuration, repo-hygiene tests, and
documentation only.

It adds no:

- real MIDI
- MIDI port opening
- MIDI sending
- active CLI command
- command dispatch
- runtime execution
- hardware behavior
- package publishing
- collaborator branch merge
- V1.34 reference edit

## Verification

Targeted verification:

- `pytest tests/test_repo_hygiene.py::test_github_actions_use_node_24_ready_action_versions`
- `pytest tests/test_repo_hygiene.py`

Final closeout must still pass before commit.

## Next Recommended Task

Keep the cost-controlled PR workflow as the routine remote gate.

Run the manual full matrix only before final PR readiness or a major merge
decision.

Continue waiting for Eddie's implementation branch or PR before running the
collaborator implementation intake protocol.
