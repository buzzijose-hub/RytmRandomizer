# Eddie Implementation Review Request Packet

## Purpose

Provide a short message and checklist to send to Eddie when his larger
implementation branch is ready.

This packet is a practical companion to:

- `Docs/COLLABORATOR_IMPLEMENTATION_BRANCH_INTAKE_PROTOCOL.md`

This is documentation-only. It does not fetch, merge, cherry-pick, change
code, change tests, open MIDI ports, send MIDI, run hardware, publish a
package, or apply repository admin settings.

## Current Baseline

Current local branch:

- `codex/execute-eddie-plan`

Current HEAD before this slice:

- `f923c04 Add collaborator implementation branch intake protocol`

Current draft PR:

- <https://github.com/buzzijose-hub/RytmRandomizer/pull/2>

Current remote branches checked before this packet:

- `origin/modularize-v1.34`
- `origin/codex/execute-eddie-plan`
- `origin/docs/review-and-execution-plan`

Eddie's larger implementation branch has not been observed on the remote yet.

Hardware status:

- Analog Rytm MKII off
- Analog Four MKII off
- hardware not required

## Message To Send Eddie

```text
When your implementation branch is ready, please push it as a separate branch
or open a separate PR.

Please send:

1. branch name
2. PR URL, if you opened one
3. final commit hash
4. base branch used
5. exact test command(s) you ran
6. full test result / test count
7. coverage result, if available
8. whether V1.34 was edited
9. whether V1.34 behavior parity was checked
10. whether any real MIDI, MIDI ports, active CLI behavior, command dispatch,
    package publishing, branch protection, or hardware behavior was added
11. summary of new modules
12. summary of deleted/renamed files

We'll intake it through our branch intake protocol, run closeout, inspect the
V1.34 diff, classify the changes, and integrate only reviewed packets.
```

## Short Version For WhatsApp

```text
Push the branch/PR when ready and send the branch name, commit hash, base
branch, full test result, V1.34 status, and whether anything touches real
MIDI/ports/active CLI/hardware. We'll run our closeout and split anything
useful into reviewed integration packets before merging.
```

## What We Need Before Review

Required:

- branch name
- commit hash
- test result
- V1.34 diff/status
- MIDI/ports/active/hardware status

Strongly preferred:

- PR URL
- coverage result
- summary of module extraction
- summary of E2E validation
- list of new files
- list of deleted or renamed files

Not enough by itself:

- screenshot of progress
- claim that tests passed without command/output
- claim of parity without explaining how it was checked

## Owner Intake Steps After Eddie Pushes

Run:

```powershell
git fetch --all --prune
git branch -r
```

Then inspect:

```powershell
git log --oneline --decorate --graph --max-count=30 origin/<branch-name>
git diff --stat modularize-v1.34...origin/<branch-name>
git diff --name-status modularize-v1.34...origin/<branch-name>
git diff modularize-v1.34...origin/<branch-name> -- rytm_hybrid_randomizer_v134.py
```

Do not merge during first intake.

## Review Boundaries

Keep PR #2 as the current stable foundation PR while Eddie's branch is being
reviewed.

Do not merge Eddie's branch directly if it:

- edits V1.34 without clear parity evidence
- opens MIDI ports in passive paths
- sends MIDI from tests
- adds active CLI execution
- runs hardware validation
- publishes packages
- applies branch protection
- deletes large docs areas without inventory
- retires the monolith without explicit owner approval

## Expected Outcome

The expected next outcome is:

- Eddie pushes a branch or PR
- we run the collaborator implementation branch intake protocol
- we classify the changes
- we decide which packets are safe to integrate

Hardware remains off.
