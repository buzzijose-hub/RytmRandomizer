---
name: feedback-maximum-parallelization-worktrees
description: "Always work with maximum parallelization across multiple parallel agents in worktrees — this is the default mode on RytmRandomizer, not an exception"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: b2a9f27a-6737-437c-b063-6015a588d52d
---

User directive (2026-05-25, repeated multiple times): **"always work with maximum parallelization. and in worktrees where applicable."** Quote: "and you should be doing that now!"

**Why:** Single-threaded sequential work wastes wall-clock time on a project with this many parallel tracks. The user has explicitly directed this multiple times across sessions. Combined with the no-cascade-PRs feedback ([[feedback_no_cascade_prs]]), this means: fan out implementer agents in worktrees, merge their branches into a consolidation bundle, ship the bundle as one PR.

**How to apply:**
1. **At the start of any multi-PR / multi-fix sweep**, immediately:
   - Identify independent units of work (different files, different concerns)
   - Create one worktree per unit via `git worktree add ../RytmRandomizer-worktrees/cr-prN-<slug> -b <branch> origin/<base>`
   - Dispatch one implementer agent per worktree IN PARALLEL (single message, multiple Agent tool calls)
   - The controller (me) only does cross-PR coordination: merging branches into the bundle, resolving conflicts
2. **Don't pause to wait for one agent before starting the next** — fire them all at once and let completion notifications arrive
3. **Worktree naming convention:** `cr-pr<N>-<slug>` for code-review PRs; `cr-<phase>-<slug>` for survey/audit phases (dead-code, docs)
4. **The bundle pattern:** one consolidation worktree (`cr-bundle`) that merges every sub-branch via `git merge --no-ff origin/<branch>`. Sub-branches never become PRs; only the bundle becomes a PR (per [[feedback_no_cascade_prs]]).
5. **Salvage agents follow the same parallel pattern** — if N implementer agents were killed by quota, dispatch N salvage agents in parallel to resume their work.

**Token economics:** parallel agents share the harness's overall quota but each consumes its own; if the budget is tight, prefer 3-5 simultaneous agents over 10. The controller can also do work in parallel with the agents (writing prevention tests, updating tracker, etc.) as long as the controller's files don't conflict with any agent's files.

**Anti-pattern to avoid:** doing work serially in a single worktree when independent files could be parallelized. The user has called this out explicitly as wrong.
