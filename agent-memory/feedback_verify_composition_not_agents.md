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
