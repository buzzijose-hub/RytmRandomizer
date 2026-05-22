---
name: cascade-merge-pattern
description: Bundle N workstream branches into one PR via `git merge --no-ff` with keep-both conflict resolution on shared changelog files; the workaround when CI requires per-PR human approval that would stall a cascade.
user-invocable: false
origin: auto-extracted-2026-05-18
---

# Cascade merge pattern: bundle N WSes into one PR when per-PR approval gates a cascade

**Extracted:** 2026-05-18
**Context:** Autonomous simplification run that produced ~13 workstreams (WS-S1..S9, WS-M1..M4) for `modularize-v1.34`. Branch protection on the base required CodeRabbit + human approval per PR. The original plan (one PR per WS, cascade-merged via `gh pr merge --squash`) would have blocked indefinitely on per-PR human review.

## Problem

You have N independent workstream branches (`refactor/ws-s1`, `refactor/ws-s2`, ...) that all need to land on the same base branch. The "one PR per WS" pattern from PRs #22-#28 works only when:

- The base branch's protection rules allow agent-triggered auto-merge, OR
- A human is actively reviewing each PR within minutes of it opening.

In a fully autonomous run with `req=approval` required, each PR sits in `mergeable=BLOCKED` waiting for human attention. The cascade stalls: WS-S2 can't rebase onto WS-S1 because WS-S1 isn't merged; the autonomous orchestrator's wake-ups burn budget polling unchanged state; eventually the time budget exhausts with all PRs still open.

## Solution

Bundle all N WSes into a single integration branch and open **one** PR. The single PR still needs the per-PR approval, but the human reviews once for N WSes instead of N times.

```powershell
# 1. Create the bundle branch off latest base.
git fetch origin modularize-v1.34
git checkout -b refactor/wave1-bundled origin/modularize-v1.34

# 2. Merge each WS branch in order with --no-ff (preserves WS attribution in history).
foreach ($ws in @('refactor/ws-s1','refactor/ws-s4','refactor/ws-m1','refactor/ws-m4',
                  'refactor/ws-s3','refactor/ws-m2','refactor/ws-s2','refactor/ws-s5')) {
    git merge --no-ff $ws -m "Merge $ws into wave1 bundle"
    # If conflict on docs/STATUS.md "Recent Cleanup" or docs/SIMPLIFICATION_STATE.json:
    # apply keep-both rule below, then `git add` + `git commit --no-edit`.
}

# 3. Push and open a single PR.
git push -u origin refactor/wave1-bundled
python scripts/create_pr.py --title "Wave 1 bundle: WS-S1..S5 + WS-M1..M4" `
  --body-file docs/superpowers/plans/wave1-bundle-pr-body.md
```

### The keep-both conflict rule

The cascade pattern from PRs #22-#28 collides on exactly two file shapes:

| File | Conflict shape | Resolution |
|---|---|---|
| `docs/STATUS.md` "Recent Cleanup" section | Each WS prepends a one-line entry under the same heading | Keep both entries; preserve WS order (more recent at top) |
| `docs/SIMPLIFICATION_STATE.json` | Each WS updates its own row in the workstream table | Merge by WS-id key; never lose a row |

Mechanical resolution for `docs/STATUS.md`:

```powershell
# After `git merge --no-ff` reports CONFLICT on docs/STATUS.md:
# 1. Open the file, find the <<<<<<< / ======= / >>>>>>> markers under "## Recent Cleanup".
# 2. Both sides added a new entry at the top of the list. Delete the markers; keep both entries.
# 3. `git add docs/STATUS.md` ; `git commit --no-edit`.
```

For `docs/SIMPLIFICATION_STATE.json`, prefer the side with the more advanced state per WS (`merged` > `pr_open` > `implementing` > `pending`).

## When to Use

Trigger conditions:

- Autonomous multi-PR refactor where the base branch requires per-PR human approval.
- N workstreams (N >= 3) ready to merge, all independent.
- The orchestrator's time budget would be dominated by polling-for-approval, not by actual work.
- A single squash merge of the bundle still produces a reviewable diff (< ~3k LOC ideally, ~10k acceptable).

DO NOT use this pattern when:

- The base branch allows agent auto-merge — use `gh pr merge --squash` per WS as in PRs #22-#28.
- WSes have dependencies on each other beyond shared docs — the bundle won't merge cleanly and the keep-both rule won't cover code conflicts.
- The combined diff exceeds ~10k LOC — the reviewer's signal-to-noise collapses and you've defeated the purpose. Split into 2-3 mid-size bundles instead.
- Individual WSes need independent revert capability — squashing them together makes revert require re-implementing one inside a new PR.

Anti-pattern to recognize: opening N PRs into a protection-gated base and then sitting in a polling loop for human review. If the orchestrator's run log shows >2h with no merges and the same PRs stuck in `BLOCKED`, abandon the per-PR cascade and rebundle.

## Cross-references

- `.claude/skills/learned/parallel-agent-bundle/SKILL.md` — how to dispatch the WSes themselves without race conditions.
- `.claude/rules/cascade-merge-pattern.md` — the agent-runtime rule that points here.
- `docs/SIMPLIFICATION_RUN_REPORT.md` — concrete timeline of the run this pattern was extracted from (PR #35).
