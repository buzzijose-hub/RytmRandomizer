---
name: parallel-agent-bundle
description: Dispatch N parallel agents to the SAME working branch by enforcing strict disjoint-file ownership — each agent owns a subpackage or a non-overlapping file set, so simultaneous writes never race.
user-invocable: false
origin: auto-extracted-2026-05-18
---

# Parallel agent bundle: disjoint-file ownership enables shared-branch concurrency

**Extracted:** 2026-05-18
**Context:** PR #35 (Wave 1 bundle on `refactor/wave1-bundled`) dispatched 4 agents simultaneously — WS-S6 (snapshot envelope), WS-S7 (CLI registry), WS-S9 (observability metrics), WS-M3 (data/modes Literal migration) — and all 4 successfully wrote to the same branch without a single conflict or stomp. The companion pattern `parallel-agents-need-git-worktrees` solves the *checkout collision* problem; this skill solves the *write collision* problem when agents must share one branch.

## Problem

The standard advice "one git worktree per agent" (see `parallel-agents-need-git-worktrees`) works when each agent opens its own PR. But the cascade-merge bundle pattern (`cascade-merge-pattern`) puts N WSes on **one** branch, and the orchestrator wants to run the *implementation phases* of independent WSes in parallel to compress wall-clock time.

If you naively dispatch 4 agents at the bundle branch:

- Agent A creates `rytm_randomizer/devices/base.py`.
- Agent B creates `rytm_randomizer/snapshot/envelope.py`.
- Both also need to register their subpackage in some shared `tests/architecture/test_layering_structure.py` allowlist.
- They both `git add` and `git commit`. The second commit either silently overwrites the first's edit to the shared file, or git refuses to commit cleanly and you've got a manual rebase.

The shared-file problem is unavoidable in a real refactor (architecture tests, `__init__.py` re-exports, `STATUS.md`).

## Solution

Give each parallel agent **a complete subpackage** (or an explicitly disjoint file set) plus a **forbidden-shared-file list**. The agent owns its files end-to-end. Shared files are touched by a serializing follow-up step the orchestrator runs after all parallel agents return.

### Dispatch contract

For each parallel agent, the prompt includes:

```
YOUR OWNED FILES (NEW only — you create these from scratch):
- rytm_randomizer/snapshot/envelope.py
- rytm_randomizer/snapshot/decoder.py
- rytm_randomizer/snapshot/planner.py
- rytm_randomizer/snapshot/mock_runtime.py
- rytm_randomizer/snapshot/__init__.py
- tests/snapshot/test_envelope.py
- tests/snapshot/test_decoder_protocol.py
- tests/snapshot/test_planner_protocol.py
- tests/snapshot/test_mock_runtime.py
- tests/snapshot/__init__.py

FORBIDDEN — do NOT touch these (another agent or the orchestrator owns them):
- rytm_randomizer/__init__.py        (orchestrator post-pass adds re-exports)
- tests/architecture/*.py            (architect agent owns allowlist updates)
- docs/STATUS.md                     (doc-updater agent owns the changelog entry)
- docs/SIMPLIFICATION_STATE.json     (orchestrator owns state transitions)
- any file under another agent's owned-files list

If your work requires touching a forbidden file, STOP and return a deferral note; the orchestrator will sequence the change after parallel phase completes.
```

### Proof that it works

PR #35's parallel batch:

| Agent | Owned subpackage | Files created |
|---|---|---|
| WS-S6 | `rytm_randomizer/snapshot/` + `tests/snapshot/` | 5 source + 4 tests |
| WS-S7 | `rytm_randomizer/cli_registry.py` + `tests/test_cli_registry.py` | 1 source + 1 test |
| WS-S9 | `rytm_randomizer/observability/metrics.py` + `tests/test_metrics.py` | 1 source + 1 test |
| WS-M3 | `rytm_randomizer/data/modes.py` + `tests/data/test_modes.py` | 1 source + 1 test |

All 4 agents ran simultaneously, each in the same `refactor/wave1-bundled` working tree (no worktree-per-agent), and completed without a single shared-file conflict. The orchestrator's post-pass touched the 3 forbidden shared files in a serialized step (~30 seconds, deterministic).

### Why this works on one branch instead of N worktrees

- The agents never read each other's files during their phase, so the shared working tree never matters.
- New-files-only ownership means git's index has no contended rows; each agent's `git add` is over a disjoint path set.
- Architecture/allowlist updates that *would* contend are explicitly deferred to a serialized post-pass.

This is cheaper than N worktrees (no `git worktree add` overhead, no path-translation in the dispatch prompts, no orphan-worktree cleanup) when the bundle pattern is already in use.

## When to Use

Trigger conditions:

- The cascade-merge bundle pattern (`cascade-merge-pattern`) is already chosen.
- N (>=2) WSes can be partitioned into mutually disjoint file sets — each WS adds a new subpackage or a small set of new top-level files.
- Each WS's implementation phase is >2 minutes (otherwise serial dispatch is fine).
- The orchestrator can enforce the FORBIDDEN list in the agent prompts.

DO NOT use this pattern when:

- WSes share even one source file in their owned set — go back to worktrees.
- A WS needs to edit existing production code that another WS will also touch (e.g. both modify `shell.py`) — sequence them.
- The orchestrator can't reliably author the FORBIDDEN list ahead of time (e.g. for a discovery-shaped WS where the agent decides which files to create after research).

Anti-pattern to recognize: dispatching N agents at the same branch without a written FORBIDDEN list and hoping nobody touches the same file. They will.

## Cross-references

- `.claude/skills/learned/parallel-agents-need-git-worktrees/SKILL.md` — the prior pattern; use when N PRs (not N WSes in one PR).
- `.claude/skills/learned/cascade-merge-pattern/SKILL.md` — the bundle pattern this skill complements.
- `docs/SIMPLIFICATION_RUN_REPORT.md` — the run that proved this works at N=4.
