# Auto-update parallel run — report and post-mortem

**Date:** 2026-09-07 → 2026-09-08
**Program:** auto-update / distribution
([spec](superpowers/plans/2026-08-03-autoupdate-distribution.md),
[plan](superpowers/plans/2026-09-07-autoupdate-implementation.md))
**Shape:** 11 implementation agents in parallel git worktrees + 4 adversarial
review lenses.
**Outcome:** all 15 agents completed; **7 blockers** found before any PR opened.

This document exists because the failure mode was not "agents did bad work" —
it was the opposite, and that is the interesting part.

---

## 1. What the agents produced

Every agent's individual work was strong:

| track | evidence |
|---|---|
| A1 version spine | wheel builds as `rytm_randomizer-1.34.0` — hatchling genuinely reads `VERSION`; 8747 tests |
| A2 release-prep | 80 tests, 100% branch; **caught a contradiction between its brief and the spec** |
| A3 app-version | 8533 tests; lazy I7 import, no path leakage, #238-safe |
| A4 persisted-state | 8587 tests; drift guard mutation-proven |
| A5 workflows | 808 arch tests; `test_ci_workflow.py` grown 4 → 18 assertions |
| A6 releases-branch | 53 tests, 100% branch |
| B-rust | 159 cargo tests, clippy clean; **consent is a compile-time guarantee** |
| B-web | 845 vitest at 100% statements/branches/functions/lines |
| C-e2e | 31 passed / 24 deliberately `.fixme`'d; no regression in the existing 20 |
| C-snap | 87 tests; **found a real macOS data-loss bug in salvaged code** |
| C-dash | 38 tests |

Gate 17 came back clean repo-wide: SemVer parsing in exactly one file, one
log-list component, no parallel schema or registry anywhere. The disjoint
file-ownership matrix produced **one** doc-comment conflict across eleven
agents.

## 2. What the merge produced

**21 failures.** Seven blockers, every one in a producer/consumer seam:

| # | Defect | Why no agent could see it |
|---|---|---|
| B1 | Shell emits Tauri IPC; web listens for a DOM event. `@tauri-apps/api` not a dependency. **Feature totally inert.** | Both sides individually correct and 100% green |
| B2 | `Version.prerelease` is `()` not `None`; consumer guards `is not None` → `apply_bump` returns the **current** version, so releases never bump | Consumer's correct test never ran (see §3) |
| B3 | Two workflows run `python release_lib.py generate`; the file is a library with no `__main__` → exits 0, writes nothing | Producer shipped what its contract said; consumer wrote valid YAML |
| B4 | `validate_manifest.py` loads the module without `sys.modules` registration; `@dataclass(slots=True)` → `AttributeError` on **every** invocation | Its tests stubbed the collaborator; 100% coverage on a 100%-broken script |
| B5 | **Security:** Python pins the URL host but not the required `/releases/download/` path; Rust pins both | Two agents read one spec clause independently |
| B6 | Corpus contract "both languages reject all 33" — Python accepts 5 | Rust's loop was inside `if let Ok(read_dir)`; dir absent → dead code, green |
| B7 | Seed manifests are *rejected*, not read as "no update available" | Producer and consumer of the same artifact never shared a tree |

## 3. Root cause

> The 11-way split was close to right. It was **verified as if it were 11
> separate programs.**

The decisive measurement. Agent A2's suite, in its own worktree:

```
ERROR tests/test_prepare_release.py - Failed: scripts/release_lib.py is missing
18 errors in 0.53s          <- ZERO tests ran; recorded as "green"
```

The same **untouched** suite with the real collaborator present:

```
15 failed, 65 passed in 0.58s
```

led by `test_apply_bump_release_versions[1.34.0-minor-1.35.0]` — B2, which
accounts for 17 of the 21 merge failures. **The correct test already existed
and had never executed.** B2 was not a decomposition failure or a testing
failure; it was a **reporting** failure: the run could not distinguish
"passed" from "did not run".

B3 and B4 are the same shape — one command each against a composed tree.

### The sharpest finding

This repo already carries **eight** drift guards referencing `desktop/web`,
including `tests/architecture/test_frontend_matches_handshake_contract.py`,
which pins the two-argument `new WebSocket(url, subprotocol)` **call form** —
written after PR #113 shipped the one-argument shape. That is exactly the
transport check B1 needed.

The plan added **zero** such guards for its nine interface contracts. The
machinery existed and was not reused: **a Gate 17 violation by the plan
itself**, the one rule it made binding on every agent.

Corroborating: the single contract that used the repo's generate-and-`--check`
mechanism (I1, `app_version`) produced **no** defect. Every hand-declared
cross-language contract produced one.

## 4. The honest split

| cause | blockers | fix |
|---|---|---|
| Reporting (green ≠ ran) | B2 | Parse the runner's summary |
| Never composed until merge | B3, B4, B7 | One integration checkpoint |
| Fail-open cross-track guard | B6 | Assert fixture exists outside the conditional |
| Contract named a noun, not a verb | B1 | Drift guard on the call form |
| **Spec defect** | **B5, B7** | **A human reads the clause against every implementation** |

B5 is unreachable by any decomposition: the 33-fixture corpus contains host
and scheme fixtures and **no path-violation fixture**, so a perfect
corpus-iterating test passes against both implementations and still ships the
gap. A shared corpus enforces agreement only on cases someone thought to write
down. B5 and B7 are **spec defects wearing decomposition costumes**.

## 5. What was rejected

**Re-splitting by seam** (merging B-rust + B-web into one agent). Correct
diagnosis, wrong remedy: it collapses the two largest agents to prevent one
blocker that a static guard prevents for free. *Do not re-decompose to fix a
reporting bug.*

## 6. What landed

- [`.claude/rules/parallel-agent-composition.md`](../.claude/rules/parallel-agent-composition.md) — mandatory rule, 6 clauses (`CLAUDE.md` hard rule 13)
- `scripts/check_agent_report.py` — RAN/PASSED · RAN/FAILED · **DID NOT RUN**; 100% branch
- `tests/architecture/test_workflow_script_invocations_resolve.py` — mutation-proven against B3
- `tests/architecture/test_cross_language_event_seams_agree.py` — mutation-proven against B1
- `tests/architecture/test_scripts_directory_case.py` — the `scripts/` vs `Scripts/` trap
- Learned skills: `agent-report-did-not-run`, `cross-language-seam-drift-guard`, `worktree-base-and-lint-traps`
- `pyproject.toml` — `.claude/worktrees` excluded from black + isort

## 7. Process failures worth recording

Three were the orchestrator's, not the agents':

1. **Agents were dispatched against a stale base.** The 714-line spec lived
   only on an unmerged branch; worktrees carried an obsolete 272-line draft
   with **colliding section numbers** (old §5 was "Speed of distribution", new
   §5 is the state machine). The first run was stopped and relaunched. Caught
   only because an agent reported the plan file missing.
2. **A brief contradicted the spec.** The dispatch said "else none" for bump
   derivation; spec §2 says "else PATCH" and no "none" level exists in 714
   lines. A2 deferred to the spec, preserved the other reading behind a flag,
   and escalated. Ratified.
3. **The first seam guard was fail-open** — the exact flaw it was written to
   catch. It passed on the real defect because the `emit` and its `const` live
   in different Rust files and constants were resolved per-file. Mutation
   testing against the real defect is what caught it. *A guard you have not
   tried to break is a guard you do not have.*

Also: two untracked in-flight Digitakt data files were deleted during a stray-
file cleanup and are unrecoverable. Check references before deleting untracked
files in a shared tree.
