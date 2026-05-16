---
name: rebase-after-squash-merge
description: After a squash merge collapses N commits into 1, branches based on the old N-commit history see "91 conflicts to rebase". The fix is `git reset --hard <new-base>` + cherry-pick only the actually-new commits, not `git rebase`.
user-invocable: false
origin: auto-extracted
---

# Rebase after a squash merge: reset and cherry-pick, don't replay

**Extracted:** 2026-05-16
**Context:** Your repo uses squash-merge (most do). You had a long-running feature branch `feature/foo` based on `main` at some earlier point. A teammate's PR squash-merged into `main`, collapsing 91 commits into one. Your branch is now N commits "behind" but also has 91 phantom commits that no longer exist as themselves on `main`.

## Problem

You run `git rebase main` (or `git pull --rebase`). Git starts replaying every commit since your branch's merge-base with `main`. But your merge-base is *before* the squash, so git sees 91+M commits to apply. Each one of them — code that's ALREADY been merged into `main` as part of the squash — produces a conflict, because the squash-merge collapsed them all into one commit whose content overlaps almost everything.

You spend an hour resolving "conflicts" that are actually re-applying code that's already in `main`. Worse, the rebase succeeds with the wrong content (an accidental revert of someone else's changes).

Symptoms:
- `git rebase <main>` says "Rebasing (1/91)" when you only made 2-3 commits.
- Each conflict shows your branch deleting code that `main` has, where the deletion is actually the OLD pre-squash code that was never `main`'s.
- `git diff <new-base>...HEAD --stat` shows files you never touched.

## Solution

Find the merge-base. Identify your actually-new commits. Reset and cherry-pick.

```bash
# 1. Find where your branch diverged from the squash-merged base.
mb=$(git merge-base origin/main HEAD)
echo "merge base: $mb"

# 2. List commits on your branch since that merge-base. Look for the ones
#    that are YOUR work, not the 91 that got squashed.
git log --oneline $mb..HEAD | head -20

# 3. Identify the 1-3 commits that represent your real changes. The rest
#    are pre-squash history that's now redundant.
real_commits="abc123 def456"  # whatever you actually wrote

# 4. Reset to the new base, then cherry-pick only your real commits.
git reset --hard origin/main
git cherry-pick $real_commits

# 5. Resolve any genuine conflicts (these are the ones that matter), then:
git push --force-with-lease
```

If you're not sure which commits are yours, look at `git log --author="$(git config user.email)" $mb..HEAD`. Or look for commits whose summary describes the feature you're working on. The pre-squash commits are usually named after individual work-in-progress steps.

## When to Use

Trigger conditions:

- A teammate's PR was just merged into the integration branch.
- Your repo uses squash-merge (most do).
- Your feature branch has been alive for more than one merge cycle.
- `git rebase main` reports replaying way more commits than you wrote yourself.
- Conflicts during rebase look like "your branch deleted code main has" but you never touched those files.

DO NOT use this pattern when:

- The base branch uses merge commits (not squash). Standard rebase works fine then.
- Your feature branch only has commits AFTER the squash merge. Standard rebase or merge is fine.
- You're sure your branch's commits each represent meaningful, isolated changes and you WANT to preserve them in the rebased history.

Anti-pattern to recognize: stubbornly fighting through 91 rebase conflicts when you only wrote 2 commits. If the conflict count vastly exceeds your commit count, stop, abort the rebase, and use reset + cherry-pick instead.
