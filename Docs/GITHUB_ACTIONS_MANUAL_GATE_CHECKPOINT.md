# GitHub Actions Manual Gate Checkpoint

## Purpose

Record the no-pay GitHub Actions policy for PR #2.

GitHub Actions are now treated as an intentional gated pipeline, not a
meter-running feedback loop during active execution-plan work.

## Current Baseline

Current branch:

- `codex/execute-eddie-plan`

Current HEAD before this slice:

- `ea8ff85 Add GitHub Actions Node 24 readiness`

Current PR:

- <https://github.com/buzzijose-hub/RytmRandomizer/pull/2>

Billing context:

- GitHub reported about 90% of included Actions minutes used.
- The account Actions budget is set to `$0`.
- Routine verification should happen locally.
- GitHub-hosted Actions should run only when explicitly triggered.

Hardware status:

- Analog Rytm MKII off
- Analog Four MKII off
- hardware not required

## What Changed

Default test workflow:

- `.github/workflows/test.yml`

Current behavior:

- manual-only with `workflow_dispatch`
- no automatic `pull_request` trigger
- no automatic `push` trigger
- lean Windows/macOS/Ubuntu Python 3.13 gate remains available on demand

Full matrix workflow:

- `.github/workflows/test-full-matrix.yml`

Current behavior:

- manual-only with `workflow_dispatch`
- Windows/macOS/Ubuntu and Python 3.11/3.12/3.13 remain available on demand

Release workflow:

- `.github/workflows/release.yml`

Current behavior:

- manual-only with `workflow_dispatch`
- no automatic tag-triggered run during the current execution-plan phase
- builds artifacts only when explicitly triggered

CodeQL workflow:

- `.github/workflows/codeql.yml`

Current behavior:

- manual-only with `workflow_dispatch`

## Intended Daily Workflow

Use local verification while implementing:

- `powershell -ExecutionPolicy Bypass -File .\Scripts\closeout_check.ps1`
- `git diff -- rytm_hybrid_randomizer_v134.py`
- `git status --short`

Use GitHub Actions only as a deliberate gate:

- before marking PR #2 ready
- before a major merge decision
- before accepting or merging Eddie's implementation branch
- before a release-readiness decision

## Why This Helps

This policy avoids automatic GitHub-hosted runner usage while the execution
plan is still moving quickly.

It preserves the gated pipeline without spending Actions minutes on every push
or PR update.

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

## Branch Protection Note

Do not require automatic Actions status checks while workflows are manual-only
unless the owner is prepared to run the relevant manual gate for every merge.

Use PR review plus local closeout evidence as the default near-term governance
model.

## Next Recommended Task

Keep local closeout as the daily gate.

Run manual GitHub Actions only when a work packet, PR, or collaborator intake
has reached a meaningful review checkpoint.

Continue waiting for Eddie's implementation branch or PR before running the
collaborator implementation intake protocol.
