---
name: feedback-cleanup-worktrees-as-you-go
description: "Clean up RytmRandomizer worktrees AS each PR ships, not at the very end — the parent has accumulated dozens of stale ones"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: b2a9f27a-6737-437c-b063-6015a588d52d
---

User feedback (2026-05-25, repeated twice): "please also make sure to clean up all the worktree folders when we are done with them" → "also cleanup worktree folders when your done with them. i see sooo many!"

**Why:** RytmRandomizer-worktrees has accumulated dozens of stale worktrees (cockpit-bundle, fix-a-tauri-shell, p3-ws-a-signing, ws-a-data-model, etc.) from prior agentic sweeps. Each worktree is a full repo checkout (~hundreds of MB on Windows). They eat disk space, confuse `git worktree list`, and clutter the directory listing.

**How to apply:**
1. **Clean up each worktree as soon as its branch merges into the bundle** — don't batch the cleanup to the very end. Right after a successful merge:
   ```
   git worktree remove ../RytmRandomizer-worktrees/cr-prN-<slug>
   ```
2. **Keep ONLY the bundle worktree open** during execution — sub-branch worktrees are intermediate; once merged they're dead weight.
3. **Use `git worktree remove --force` if the worktree has uncommitted CRLF noise** (Windows + .gitattributes interaction — see [[windows-gitattributes-crlf-merge-block]] skill). The noise is harmless and the agent's real work is already on the branch.
4. **For deferred / blocked work** (like PR 11 which couldn't be salvaged in one session), keep its worktree until the next session picks it up.
5. **At the very end of a sweep**, do one final `git worktree list` and prune anything remaining that has been merged. Branches can stay (they're cheap) — only the worktree directories are heavy.

**Anti-pattern:** running 10 agents in parallel, merging all 10 branches, then NEVER cleaning up the 10 worktree directories. The user has explicitly flagged this as a problem on their machine.
