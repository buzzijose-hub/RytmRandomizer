---
name: worktree-base-and-lint-traps
description: Harness-created agent worktrees branch from the repo's original HEAD (not your checked-out branch) and live under .claude/worktrees — so agents can silently get a stale base, and repo-root lint walks into siblings' half-written files and fails your pre-push on someone else's code.
user-invocable: false
origin: auto-extracted-2026-09-08
---

# Two worktree traps that cost a whole run

**Extracted:** 2026-09-08
**Context:** The auto-update program. Both traps fire silently and look like
something else.

## Trap 1: agents get a STALE BASE, and the docs they were told to read do not exist

The harness creates agent worktrees under `.claude/worktrees/<run-id>-N`,
branched from the repo's **original HEAD** — *not* from whatever branch the
orchestrator has checked out. Worktree creation also races the orchestrator's
`git checkout`, so a single run can produce a mix: worktree `-1` on the old
commit, worktree `-10` on the new one.

The auto-update run dispatched 11 agents told to read a 714-line spec that
existed only on an unmerged branch. Their worktrees carried an **obsolete
272-line draft** of the same filename, and the section numbers **collided**:

| brief said | agents actually read |
|---|---|
| §4 manifest schema | "Gating: who gets what, when" |
| §5 state machine | "Speed of distribution" |
| §5.1, §7.1, §9, §11 | *did not exist* |

Every agent following a section reference built the wrong thing. Nothing
errored.

**Fixes, in order of reliability:**

1. Make the docs reachable from **every** ref a worktree might branch from —
   fast-forward the *local* integration branch (never push a self-authored,
   unreviewed PR into a shared branch just to fix tooling).
2. Give every agent a **self-check plus self-heal** as its first instruction:
   ```
   wc -l docs/.../spec.md          # must be 714
   grep -n '^### 7.1' docs/.../spec.md   # must exist
   # if either fails:
   git checkout <integration-branch> -- docs/ tests/architecture/<guards>.py
   ```
   In the relaunch, **most** agents reported hitting the stale base and healing
   themselves. Without that instruction they would have silently rebuilt the
   wrong thing a second time.
3. **Verify before trusting**: after dispatch, check each worktree actually has
   the expected content. Do not assume the fix took.

## Trap 2: repo-root lint walks into other agents' worktrees

`.claude/worktrees/` sits *inside* the repo. Any repo-root lint (`isort .`,
`black .`) descends into sibling worktrees and reports **another agent's
half-written file** as a violation of the branch you are pushing:

```
ERROR .claude/worktrees/wf_x-1/rytm_randomizer/_version.py Imports are incorrectly sorted
[pre-push] BLOCKED — gates failed: Lint: isort --check-only.
```

The tempting "fix" is `--no-verify`, which this repo bans.

This repo's skip lists already carried `.worktrees` — a *different* path that
never matched `.claude/worktrees`. Fixed in `pyproject.toml`: black
`extend-exclude` gained `\.claude/worktrees`, isort `skip` gained `.claude`.
**Ruff was already immune** because it honors `.gitignore`, which has
`.claude/*` — a useful reminder that not all three linters resolve paths the
same way.

## Trap 3 (same family): the case-insensitive path collision

This repo intentionally tracks both `scripts/` (Python) and `Scripts/` (two
legacy `.ps1`). On macOS they are ONE physical directory but TWO git paths, so
`git add scripts/foo.py` can stage `Scripts/foo.py` — which on Linux CI lands
where nothing imports it. It hit four agents in one run, and hit the
orchestrator twice afterward.

Restage recipe (also in the guard's failure message):
```bash
git rm --cached Scripts/foo.py
sha=$(git hash-object -w scripts/foo.py)
git update-index --add --cacheinfo 100644,$sha,scripts/foo.py
```
Pinned by `tests/architecture/test_scripts_directory_case.py`.

## Bonus: salvage before you stop a run

Stopping a workflow does **not** immediately reclaim its worktrees, but do not
rely on that. Copy each worktree's real work out first — filter the repo's
inherited dirty baseline (here: 473 CRLF-only files) with
`git status --porcelain | cut -c4-` and a `git diff --quiet --ignore-cr-at-eol`
check. 121 files were salvaged this way and re-offered to the relaunched agents
as starting points. **Note `cut -c4-`**: `awk '{print $2}'` silently drops the
filename for two-character status codes like `A `.

## Cross-references

- `.claude/rules/parallel-agent-composition.md`
- `.claude/skills/learned/parallel-agents-need-git-worktrees/SKILL.md`
- `.claude/skills/learned/multi-agent-work-collision-recovery/SKILL.md`
- `tests/architecture/test_scripts_directory_case.py`
