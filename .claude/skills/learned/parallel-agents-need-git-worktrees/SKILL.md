---
name: parallel-agents-need-git-worktrees
description: When dispatching multiple parallel agents that modify code, give each its own git worktree, not just its own branch. Shared working tree → checkouts trample each other.
user-invocable: false
origin: auto-extracted
---

# Parallel agents need git worktrees, not just branches

**Extracted:** 2026-05-15
**Context:** When you dispatch 2+ background agents in the same conversation, each on its own branch, to refactor different parts of a codebase in parallel.

## Problem

You dispatch three agents, telling each to:

1. `git checkout -b feature-x off main`
2. Make focused edits
3. Commit and push

This LOOKS isolated — each has its own branch. It is NOT isolated. All three agents share the same physical working directory. The result:

- Agent A does `git checkout feature-a` → working tree now reflects branch A.
- Agent B simultaneously does `git checkout feature-b` → working tree now reflects branch B. Agent A's uncommitted edits are stashed or overwritten.
- Agent A's next Edit happens against branch B's content. Agent A then commits *Agent B's working state on Agent A's branch*.
- You see commits like `wip` with diffs that make no sense, branches missing their own work, and tests passing on one machine but failing in CI because the actually-pushed code is a chimera.

The git index is a single shared resource. Branches are pointers, not isolated workspaces.

## Solution

Create one `git worktree` per agent. Each worktree has its own physical directory and its own checkout. They share the same `.git` object database (cheap) but never collide on the working tree.

```bash
# Orchestrator setup BEFORE dispatching agents:
mkdir -p ../my-repo-worktrees
git worktree add ../my-repo-worktrees/feature-a -b feature-a main
git worktree add ../my-repo-worktrees/feature-b -b feature-b main
git worktree add ../my-repo-worktrees/feature-c -b feature-c main

# Verify:
git worktree list
# /path/to/my-repo                          abc1234 [main]
# /path/to/my-repo-worktrees/feature-a      abc1234 [feature-a]
# /path/to/my-repo-worktrees/feature-b      abc1234 [feature-b]
# /path/to/my-repo-worktrees/feature-c      abc1234 [feature-c]
```

Then dispatch each agent with an explicit `cd` to its worktree as the FIRST instruction in the prompt, plus a rule:

```
YOUR WORKTREE: /path/to/my-repo-worktrees/feature-a
- ALL your work happens in that directory.
- Do NOT `cd` outside it.
- Do NOT `git checkout <other-branch>` (git would refuse since the other branches are checked out elsewhere, but don't try).
- Do NOT touch the parent /path/to/my-repo directory; that's the orchestrator's.
```

When the agent is done and pushes, the worktree can be cleaned up:

```bash
git worktree remove ../my-repo-worktrees/feature-a
```

## When to Use

Trigger conditions:

- Dispatching 2+ background agents in one conversation, each with file-modification authority.
- The agents will each open a PR (so each needs its own branch AND its own commit history).
- Failure mode you're trying to avoid: an agent reports "the file changed under me" or "my git status shows files I didn't touch" or "another agent is interfering" — these all mean shared-working-tree collision.

DO NOT use worktrees when:

- The agents are read-only (research, audit, summary).
- Only one agent will write code; others just observe.
- The agents will explicitly serialize (one commits, then the next reads, etc.).

Anti-pattern to recognize in your own behavior: telling agents `git checkout -b <branch>` and assuming that's enough. It isn't. The checkout writes to the shared working tree.
