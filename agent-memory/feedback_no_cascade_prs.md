---
name: feedback-no-cascade-prs
description: "User prefers ONE bundled PR per phase, not cascade PRs across many small branches"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: b2a9f27a-6737-437c-b063-6015a588d52d
---

User on RytmRandomizer strongly prefers **one bundled PR per phase**, not a cascade of small PRs across many branches.

**Why:** Direct user quote (2026-05-25): "i thought this was going to be all one PR. we dont need cascade PRs". The precedent: wizard Phase 2 shipped as one PR (#102) with "7 fix workstreams shipped in the same PR." Phase 3 (#106) shipped 7 workstreams in one PR.

**How to apply:**
- When executing multi-PR plans (like the CODE_REVIEW.md follow-up sweep), create a single consolidation branch (`fix/<feature>-bundle`) and merge every sub-branch into it. The bundle is what becomes the PR.
- Sub-branches are fine as intermediate worktrees for parallel agents — but they should never become PRs of their own. Salvage agents push to their branch; the controller merges into the bundle.
- Exception: independent infrastructure fixes (like the pre-push hook fix) CAN open their own PR if they're truly orthogonal and might want to land before the bundle.
- When in doubt, ask before opening a second PR.

If a cascade PR opens accidentally, close it immediately with a comment saying "consolidating into single PR per user direction." See PRs #111 and #112 (closed) vs #110 (kept because infrastructure).
