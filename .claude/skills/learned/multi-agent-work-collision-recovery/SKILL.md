---
name: multi-agent-work-collision-recovery
description: "When a peer agent independently did your task and pushed first: reset, rebase onto their HEAD, keep only your non-redundant delta."
user-invocable: false
origin: auto-extracted
---

# Multi-agent work-collision recovery

**Extracted:** 2026-05-19
**Context:** This repo has multiple concurrent contributors — a human running Claude Code, the OpenAI `codex` agent on `codex/*` branches, and sometimes more than one Claude session. You complete a task locally, then discover a peer agent already did the same (or overlapping) task and pushed it to the same branch.

## Problem

You are told "make change X on branch B." You do it — several file edits, a local commit. Before you push, you fetch and discover branch B's remote HEAD has *moved*: a peer agent independently did **the same task** and pushed it.

Now your local commit and the remote commit both rewrite the same files. Naively:

- **`git push`** -> rejected (non-fast-forward).
- **`git push --force`** -> destroys the peer's work.
- **`git rebase` then resolve every conflict by keeping your side** -> you re-introduce a redundant duplicate of work already done, and may overwrite the peer's *better* version.

The real task is: **keep only the part of your work the peer did NOT do, discard the redundant part, and take the peer's version where they overlapped.**

This happened in the PR #44 (`codex/dual-machine-strategy-redo`) session: both this agent and codex were told "update the README for dual-machine support." Codex pushed first.

## Solution

A five-step procedure. The key insight: **separate your commit into "unique delta" vs "redundant delta" by file, then keep only the unique files.**

### Step 1 — Detect the collision before pushing

Always fetch + compare before pushing to a shared branch:

```bash
git fetch origin <branch>
git log --oneline HEAD..origin/<branch>                     # commits the peer added
git rev-list --left-right --count HEAD...origin/<branch>    # "ahead  behind"
```

If "behind" is non-zero, the branch diverged — a peer pushed. Do not push.

### Step 2 — Assess what the peer changed vs what you changed

```bash
# What files did the peer touch?
git diff --stat <your-fork-point>..origin/<branch>
# What exactly did the peer do to a file you also changed?
git diff <your-fork-point>..origin/<branch> -- <overlapping-file>
```

Classify each file in your commit:

- **Unique** — the peer did NOT touch it. Your work here is the contribution; keep it.
- **Redundant** — the peer made an equivalent or better change. Discard yours; take theirs.
- **Genuinely-conflicting** — both changed it in incompatible ways that both need to survive. Rare; needs a real 3-way merge.

### Step 3 — Soft-reset your commit, stash the working tree

```bash
git reset --soft HEAD~1            # uncommit, keep changes staged
git stash push -u -m "my work"     # park everything (-u includes new files)
```

### Step 4 — Move onto the peer's HEAD, then pop

```bash
git reset --hard origin/<branch>   # local branch now == peer's pushed HEAD
git stash pop                      # re-apply your work on top
```

`git stash pop` cleanly applies files the peer didn't touch (your **unique** files) and reports a conflict on files you both changed (your **redundant** files).

### Step 5 — Resolve conflicts by ownership

For each conflicted file, decide: unique or redundant?

- **Redundant** (peer did it equivalently/better) — take the peer's committed version. During a stash-pop conflict, the peer's version is `HEAD`:
  ```bash
  git checkout HEAD -- <redundant-file>
  git add <redundant-file>
  ```
  > **Gotcha:** in a stash-pop, `git checkout --theirs` takes the *stash* (your work), `--ours` / `HEAD` takes the peer's commit. This is the **opposite** of a normal merge's intuition. Verify with `sed -n '3p' <file>` or `grep` for a known string before trusting it.

- **Genuinely-conflicting** — open the file, do a real 3-way merge keeping both intents.

Then drop the stash and verify the final staged set is *only* your unique delta:

```bash
git stash drop
git status --short      # should list only the files the peer did NOT do
```

## Worked example (PR #44)

Two agents both got "update the README for dual-machine support." Codex pushed first. The recovering agent's commit touched 7 files. After the procedure:

- `README.md`, `.github/PULL_REQUEST_TEMPLATE.md` -> **redundant** (codex did equivalent/better) -> took codex's `HEAD` version via `git checkout HEAD -- <file>`.
- `tests/architecture/test_readme_freshness.py`, `.claude/rules/readme-freshness.md`, `docs/PLAN_REQUIREMENTS.md`, `CONTRIBUTING.md`, `docs/ARCHITECTURE_DIAGRAMS.md` -> **unique** (codex did NOT add the mechanical CI gate) -> kept.

Result: the final commit was a clean 5-file non-overlapping delta — the genuine new value (a CI test enforcing the very README-freshness both agents had just hand-applied), with zero duplicate of codex's README prose.

## When to use

- You are about to `git push` to a branch a peer agent also works on (any `codex/*` branch, or a branch a second Claude session touched).
- `git fetch` shows the remote HEAD moved since you branched.
- You and a peer were given the same or overlapping task.
- A PR review asks you to "check what the other agent did before you push."

## When NOT to use

- You own the branch exclusively — just `git pull --rebase` and push.
- The peer's changes are in entirely different files — a plain rebase has no conflicts; no ownership triage needed.
- You genuinely need both versions of an overlapping file — that's a normal 3-way merge, not a discard-the-redundant-side situation.

## Prevention

The cheapest fix is to not collide: **`git fetch` and check `HEAD..origin/<branch>` at the START of the task, not just before pushing.** If a peer is already on the branch, coordinate scope first (disjoint file ownership) — see `.claude/skills/learned/parallel-agent-bundle/SKILL.md` and `.claude/rules/cascade-merge-pattern.md`. This skill is the recovery path for when prevention did not happen.

## Cross-references

- `.claude/rules/cascade-merge-pattern.md` — bundling N workstreams into one PR (prevention of divergence at the PR level).
- `.claude/skills/learned/parallel-agent-bundle/SKILL.md` — dispatching parallel agents with pre-declared disjoint file scopes (prevention at the in-session level).
- `.claude/rules/codex-contribution-guide.md` — codex-specific guardrails; codex is the most common peer agent on this repo.
- `.claude/rules/maximize-parallelization.md` — when parallel work is correct; the disjoint-ownership rule that prevents this collision.
