# Collaborator Implementation Branch Intake Protocol

## Purpose

Define how to safely intake a large collaborator implementation branch before
reviewing, merging, or cherry-picking any code.

This protocol exists because Eddie is preparing a larger autonomous
implementation branch that appears to include monolith decomposition,
additional engine modules, package/setup work, and E2E validation work.

This is documentation-only. It does not fetch or merge a collaborator branch,
change code, change tests, open MIDI ports, send MIDI, run hardware, publish a
package, or apply repository admin settings.

## Current Baseline

Current local branch:

- `codex/execute-eddie-plan`

Current HEAD before this slice:

- `2ba3b68 Add collaborator PR review checklist`

Current draft PR:

- <https://github.com/buzzijose-hub/RytmRandomizer/pull/2>

Current remote branches seen before this protocol:

- `origin/modularize-v1.34`
- `origin/codex/execute-eddie-plan`
- `origin/docs/review-and-execution-plan`

Eddie's larger implementation branch has not been observed on the remote yet.

Hardware status:

- Analog Rytm MKII off
- Analog Four MKII off
- hardware not required

## Intake Principle

Treat Eddie's implementation branch as a candidate implementation, not as an
automatic replacement for the current foundation branch.

The correct sequence is:

1. receive the branch/PR
2. inspect metadata
3. run verification
4. compare against V1.34 and PR #2
5. classify changes into safe packets
6. integrate only reviewed packets

Do not merge a large implementation branch directly into `modularize-v1.34`.

## Required Information From Eddie

Before implementation intake begins, ask for:

- branch name
- PR URL, if one exists
- final commit hash
- base branch used
- test command used
- full test result
- coverage result, if available
- whether V1.34 behavior parity was checked
- whether V1.34 was edited
- whether any real MIDI library behavior changed
- whether any MIDI ports can open
- whether any MIDI can be sent
- whether any active CLI command was added
- whether any hardware behavior was added
- summary of new modules
- summary of deleted or renamed files
- summary of generated files, if any

Screenshot-only status is not enough. The branch and review findings must be
available as text, Markdown, PR diff, or commits.

## Safe Local Intake Commands

Fetch remote updates:

```powershell
git fetch --all --prune
git branch -r
```

Inspect the candidate branch without switching:

```powershell
git log --oneline --decorate --graph --max-count=30 origin/<branch-name>
git diff --stat modularize-v1.34...origin/<branch-name>
git diff --name-status modularize-v1.34...origin/<branch-name>
```

Inspect V1.34 changes specifically:

```powershell
git diff modularize-v1.34...origin/<branch-name> -- rytm_hybrid_randomizer_v134.py
```

Inspect potentially hardware-facing areas:

```powershell
git diff modularize-v1.34...origin/<branch-name> -- rytm_randomizer .github Scripts tests pyproject.toml README.md CONTRIBUTING.md
```

Do not merge during intake.

## Quarantine Review Branch

If local hands-on review is needed, create a separate local review branch or
worktree.

Preferred local branch pattern:

```powershell
git checkout -b codex/review-eddie-implementation origin/<branch-name>
```

Alternative worktree pattern:

```powershell
git worktree add ..\RytmRandomizer-eddie-review origin/<branch-name>
```

The review branch/worktree is for inspection and tests only. Do not merge it
into `modularize-v1.34` or `codex/execute-eddie-plan` during intake.

## Verification Gate

Run, at minimum:

```powershell
git diff --check
powershell -ExecutionPolicy Bypass -File .\Scripts\closeout_check.ps1
python .\Scripts\closeout_check.py
git diff -- rytm_hybrid_randomizer_v134.py
git status --short
```

If the branch claims package readiness, also verify:

```powershell
python -m build
python .\Scripts\smoke_test_wheel_install.py
```

If the branch has a new E2E suite, run it only after confirming it does not
open ports, send MIDI, or require hardware.

## Review Areas

Review these areas first:

- `rytm_hybrid_randomizer_v134.py`
- `pyproject.toml`
- `.github/workflows/`
- `Scripts/closeout_check.py`
- `Scripts/smoke_test_wheel_install.py`
- any new `rytm_randomizer/engines/` modules
- any new `rytm_randomizer/state/` modules
- any new MIDI or runtime modules
- any new shell/entry-point modules
- E2E validation files
- deleted or renamed docs
- generated files or artifacts

## Classification

Classify branch changes into these buckets:

- safe to keep as-is
- safe after small fixes
- needs tests before acceptance
- needs design review before acceptance
- duplicates current PR #2 work
- conflicts with current PR #2 work
- requires owner decision
- blocked by hardware/MIDI safety boundary

## High-Risk Signals

Stop and review with the owner if the branch:

- edits V1.34 beyond import-safety or clearly reviewed parity changes
- deletes large numbers of docs without a docs inventory
- opens MIDI ports in passive paths
- sends MIDI from tests
- introduces active CLI behavior
- runs hardware validation
- adds `execute-command`, `send-command`, or `hardware-test`
- changes package publication behavior
- pushes release tags
- applies branch protection settings
- retires the monolith without explicit owner approval
- claims parity without showing how parity was verified

## Integration Rule

Do not merge Eddie's large branch as one unit unless:

- closeout passes
- GitHub Actions pass
- V1.34 diff is reviewed
- hardware boundaries remain intact
- owner approves the merge strategy
- collaborator review is complete
- high-risk changes are understood

Preferred integration method:

- split useful work into narrow packets
- preserve tests with each packet
- run closeout after each packet
- keep PR #2 reviewable

## Relationship To PR #2

PR #2 is the current stable foundation PR.

It includes:

- package metadata
- passive entry points
- CI matrix
- closeout tooling
- wheel install smoke
- repo hygiene
- collaborator onboarding
- release/admin safety docs

Eddie's implementation branch should be compared against PR #2 before
integration. If the branch duplicates PR #2 work, prefer the already-green PR
#2 foundation unless Eddie's version is demonstrably safer or clearer.

## What To Tell Eddie

Suggested message:

```text
Push the implementation branch or PR when ready. Please include the branch
name, final commit hash, base branch, full test command/output, whether V1.34
was edited, and whether any real MIDI, ports, active CLI behavior, or hardware
behavior was added. We'll run our closeout and classify the changes into safe
integration packets before merging anything.
```

## Decision

No collaborator implementation branch is merged by this protocol.

The next step is to wait for Eddie's branch/PR, then run this intake protocol
before deciding what to integrate.

Hardware remains off.
