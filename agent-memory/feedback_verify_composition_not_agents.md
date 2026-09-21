---
name: feedback_verify_composition_not_agents
description: Parallel agents that each verify themselves produce individually-green work that does not compose. Verify the seams, not the agents — a green report that did not run is a red report.
metadata:
  type: feedback
---

# Verify composition, not agents

An 11-agent parallel run on this repo (auto-update program, 2026-09-07)
produced excellent individual work — 100% branch coverage per track, a
compile-time consent guarantee in Rust, Gate 17 clean repo-wide, 159/159
cargo, 854/854 vitest — and a merged tree with **21 failures and seven
blockers, every one in a producer/consumer seam**.

The post-mortem's conclusion is narrower than "the split was wrong":

> The 11-way split was close to right. It was **verified as if it were 11
> separate programs.**

The reuse contracts held (agents imported rather than forked). The disjoint
file matrix held (one doc-comment conflict across eleven agents). What was
missing was composition verification.

**Why:** each agent's own suite is, by construction, blind to the one thing
that can only fail between agents. Worse, an agent whose collaborator is
absent reports *green* — its suite errors at collection and never runs. The
biggest defect of that run (17 of 21 failures) was caught by a test the agent
had already written correctly and that never executed; dropping the real
collaborator beside it produced 15 failures in 0.58s.

**How to apply:**
1. Never accept a green report without the runner's own summary line. Use
   `scripts/check_agent_report.py` — exit 2 means DID NOT RUN, which is not a pass.
2. Take **one** integration checkpoint at first cross-agent import. Run only
   mechanical checks (execute every workflow command line; invoke every
   `__main__` on its fixture; feed each producer's output to its consumer's
   real validator). Four of the seven blockers die here, hours earlier.
3. Contracts name the **call form**, not just the payload — see
   [[cross-language-seam-drift-guard]].
4. Budget a human read for security-boundary spec clauses. Two blockers were
   spec defects no split or test rule could reach.

Full rule: `.claude/rules/parallel-agent-composition.md`.
Run report: `docs/AUTOUPDATE_PARALLEL_RUN_REPORT.md`.
Related: [[feedback_maximum_parallelization_worktrees]], [[feedback_cleanup_worktrees_as_you_go]].

## September 13, 2026 closeout reassessment

An optional panel's state subscription is not a reliable dependency for a
different surface's diagnostic export. Connection Doctor now reads the local
native snapshot on demand through the same typed adapter; its exported journal
does not depend on having visited Updates first. Verify this with the actual
Tauri SDK command path and assert that no network check or backend WS command
is dispatched.

Keep manifest policy, verified artifact bytes and installer input bound to one
checked identity. A configured signing secret or a boolean “signed” field does
not establish that a signature exists or verifies; run the actual verifier on
the assembled bytes and a tampered control. Record the exact package source/tree
and both shell/sidecar hashes when handing off a build. A passing smoke from an
earlier artifact cannot certify a later UI fix. See the tracked
`docs/superpowers/plans/2026-09-08-release-closeout_LEARNING_REPORT.md` for the
boundary tests, remaining physical evidence and replay paths.

Policy-only green tests did not prove that the plugin forwarded its actual raw
manifest, preserved the checked signed bytes, or that frontend consent reached
native IPC. Exercise the real SDK/plugin boundary: subscribe then snapshot to
recover startup events, and require the native acknowledgment before dismissing
consent. A native terminal recorder proves that the verified bytes and requested
restart choice reach the install boundary; it does not prove that an OS installer
actually installs or relaunches successfully.
