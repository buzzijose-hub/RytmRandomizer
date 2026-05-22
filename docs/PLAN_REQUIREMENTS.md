# Plan Requirements — RytmRandomizer

**Status:** Required for every plan that touches `rytm_randomizer/`, `tests/`, or `Scripts/`.
**Scope:** This document is the canonical contract. Any `docs/*PLAN*.md` (manual or auto-generated) that proposes code changes must either satisfy these requirements per workstream or explicitly document why a requirement does not apply (with a one-line rationale).
**Authority:** This file is the single source of truth. If `docs/SIMPLIFICATION_PLAN.md` and this file ever disagree, this file wins.
**Owner:** Updated by any PR that demonstrably uncovers a new gated requirement (see "How to update" at the bottom).

---

## Why this exists

The cleanup batch (PRs #22–#28) and the in-flight simplification plan converged on the same set of non-negotiable gates. Re-deriving them per plan wastes effort and risks drift. This file lifts them out of any one plan so every future contributor — human or agent — inherits them automatically.

When this file is updated, every open plan PR is expected to rebase and re-validate against the new requirements.

---

## The hard gates (apply per workstream, no exceptions)

A workstream does not reach `pr_open` (i.e. cannot call `scripts/create_pr.py` / `gh pr create`) until **every gate below** passes locally. CI failures in any gate auto-revert the last commit and re-enter the implementation phase.

### Gate 1 — Branch coverage on touched files: **100%**

```powershell
$touched = git diff --name-only origin/<base>...HEAD -- 'rytm_randomizer/*.py'
$cov_args = $touched | ForEach-Object { "--cov=$($_ -replace '/', '.' -replace '\.py$','')" }
pytest @cov_args --cov-branch --cov-fail-under=100 --cov-report=term-missing
```

- Branch (not line) coverage. Catches `if resolved_bounds is None` and `if depth == 0` corners that the duck-typed boundaries currently let slip.
- Applies to **touched files only**. The whole-package floor in `.coveragerc` is a separate ratchet; this gate is stricter and per-WS.
- A gap re-spawns `tdd-guide` with the missing-branch report. Max 2 retries before escalating to `architect`.
- `# pragma: no cover` requires a one-line justification comment pointing at either `docs/ARCHITECTURE.md` §8 (parity API) or a specific `docs/SIMPLIFICATION_RUN_LOG.md` incident.

### Gate 2 — V1.34 parity fixtures byte-identical

```powershell
pytest tests/test_engines_pad*.py tests/test_group_runner.py tests/test_scene_runner.py
```

- All 505 JSON fixtures in `tests/fixtures/v134_parity/` byte-identical.
- The orchestrator **never** sets `PARITY_CAPTURE_MODE=1` in any WS — capture is a deliberate, separate workstream by itself.
- The 11 parity-API symbols in `docs/ARCHITECTURE.md` §8 are untouchable; any plan proposing to remove one of them must include a parity-layer change as a sibling WS.

### Gate 3 — Lint / format / type clean

```powershell
python -m ruff check .
python -m black --check .
python -m isort --profile black --check-only .
python -m pyright --strict <touched paths>
```

- `ruff` rule packs at minimum: `E,F,B,S,SIM,UP,C4,PLR,ERA,ARG`. `B904` (raise-from in except) is **always on** — no opt-out.
- `black` `target-version` is pinned to the CI matrix (`py39, py310, py311` only — `py312`/`py313` excluded per the PR #28 lesson).
- `pyright --strict` on touched paths, not the whole package (whole-package pyright is a separate future workstream).

### Gate 4 — Dead-code purge clean

Runs before Gate 1 (coverage gate). Catches dead code so it doesn't get tested into permanence.

```powershell
python -m vulture $touched --min-confidence 80
python -m ruff check --select F401,F811,F841,ARG001,ARG002,ERA001 $touched
```

- Vulture clean at confidence 80; borderline cases re-run at 60 and require a `# vulture: ignore` + parity-API §8 reference if kept.
- Zero commented-out code, zero unused imports, zero assigned-but-unused locals.
- Whole-package sweep (`vulture --min-confidence 70` on `rytm_randomizer/`) runs in a dedicated sweep WS once per plan.

### Gate 5 — Documentation update

The `everything-claude-code:doc-updater` agent runs **before** PR open, not after merge.

- `docs/STATUS.md` "Recent Cleanup" entry committed in the same PR. **No exceptions.**
- `docs/ARCHITECTURE.md` updated if the WS touches a documented boundary (Protocols, registries, subpackages, the parity API surface).
- `docs/CODEMAPS/*` updated if the WS adds new top-level modules.
- Cross-links resolve: `grep -rE '\]\([^)]+\)' docs/ .claude/ | grep -v http` returns no broken paths.
- **`README.md` updated when the user-facing surface changes** — a new device family, a new CLI command, a new install path, a changed default. `README.md` is the front door; a stale front door is a Gate 5 failure. Mechanically enforced by `tests/architecture/test_readme_freshness.py` (a required CI check): every registered device must be named in the README, every internal README link must resolve, and the README must carry no stale placeholder tokens. See `.claude/rules/readme-freshness.md`.

### Gate 6 — Type-system hygiene (Pattern-Review-WS-S1 findings, made permanent)

Lifted from the holistic pattern review of 2026-05-18. Made permanent because the patterns recur across every new module:

| Rule | Enforcement |
|---|---|
| No new `Sender = Any` or equivalent module-level type aliases that resolve to `Any`. | `tests/architecture/test_no_any_escape_hatches.py` greps for `^\s*\w+\s*=\s*Any\s*$` outside the modules WS-S1 is explicitly refactoring. |
| Every new module boundary uses a `Protocol` (with `@runtime_checkable` when `isinstance` is needed), never an ABC. | Code review by `python-reviewer`; ABCs are not banned globally, but new boundaries must justify the choice in the module docstring. |
| Every new record-shaped value is a `@dataclass(frozen=True)` or `TypedDict`. No new `Mapping[str, Any]` DTOs at module boundaries. | `python-reviewer` flags any new `Mapping[str, Any]` parameter in a public function signature. |
| `raise X(...) from exc` is mandatory inside `except` blocks. | `ruff B904` always on. Today only 2 of N translation sites comply; new code must comply. |
| `from __future__ import annotations` at the top of every new module. | Project convention; `ruff` rule via `--select FA100`. |

### Gate 7 — Observability adoption (Pattern-Review-WS-S9 findings, made permanent)

Every module that performs a **state transition**, **sends a CC**, or **makes a guardrail decision** must:

1. Obtain `_logger = get_logger(__name__)` at module level.
2. Emit a structured `_logger.debug` (or `info`/`warning`/`error` per severity) per decision, with `extra={...}` payload containing at least: the decision name, the inputs, the outcome.
3. Use `@trace` (from `observability.tracing`) on any function whose execution time is operator-relevant (e.g. "this scene = N CC sends").
4. Increment the appropriate `observability/metrics.py` counter (when introduced by WS-S9).
5. Chain to `raise X from exc` so the trace span captures the cause.

Enforcement: `tests/architecture/test_observability_adoption.py` walks `rytm_randomizer/engines/`, `rytm_randomizer/randomization.py`, `rytm_randomizer/scene_runner.py`, `rytm_randomizer/group_runner.py`, `rytm_randomizer/behavior_*.py`, `rytm_randomizer/guardrails/` and fails if any module performs a decision-shaped operation without a logger and a per-decision log line.

Blocked-by-guardrail sends are **never silent** — a `clamped is None` branch always emits `_logger.debug("guardrail_block", extra={...})`.

The `observability/` library itself (`logging.py`, `tracing.py`, `errors.py`, future `metrics.py`) is already world-class — this gate enforces *adoption on the hot path*, not redesign of the library.

### Gate 8 — Test hygiene

- Tests reuse fixtures from `tests/conftest.py` and `tests/_parity_worker.py`. **Do not** redefine `RecordingOut`, `_FakeMessage`, or `_install_fake_mido` per file. The cleanup batch found these duplicated across `tests/test_engines_pad{1,2,3,4}.py`.
- New tests named to communicate intent: `test_<unit>_<behavior>_when_<condition>`.
- Test files mirror source structure: `tests/test_X.py` ↔ `rytm_randomizer/X.py` (or `tests/<subpackage>/test_X.py` for subpackaged sources).
- `unittest.mock.patch` is the exception, not the rule. Manual fakes (`MockMidiSender`) are preferred for hardware-shape behavior.

### Gate 9 — Module-organization hygiene

- **New top-level modules require architect sign-off.** Default home for a new concept is a subpackage. The PR #21 lesson: 33 new top-level files is not a refactor, it's a flood.
- Subpackages that exist and should grow when relevant: `data/`, `engines/`, `guardrails/`, `observability/`, `state/`, `style_analysis/`, `behavior/` (when WS-M2 lands).
- New subpackages need a one-line `__init__.py` docstring stating their purpose.
- If a plan adds more than 3 new top-level modules, it must justify each in the plan body or relocate them into a subpackage.
- Imports inside subpackages must be **relative** (`from ..data import ...`), never absolute (`from rytm_randomizer.data import ...`). Existing absolute-import violators in `style_analysis/` are tracked for WS-S8 cleanup.

### Gate 10 — String-literal dispatch hygiene (Maintainability-Review-WS-M3 findings)

No new string-equality dispatch on mode / intensity / page / mutation-kind values. Every such value lives in `rytm_randomizer/data/modes.py` (introduced by WS-M3) as a `Literal[...]` type or `Final` constant or `StrEnum` member.

Today's load-bearing strings to retire (and not re-introduce):

| Concept | Strings | Current dispatch sites |
|---|---|---|
| Intensity | `"balanced"`, `"deeper"`, `"intense"`, `"harder"` | `shell.py`, `group_runner.py`, `behavior_scene_group.py` |
| Page | `"src"`, `"filter"`, `"amp"`, `"lfo"`, `"morph"`, `"body"`, `"grit"` | `shell.py`, `group_runner.py` |
| Mutation kind | `"discovery"`, `"mutation"` | `behavior_pad_lane.py` (~20 sites) |
| Pad-1 machine | `"sharp"`, `"hard"`, `"classic"`, `"fm"` | `randomization.py` |

Enforcement: `tests/architecture/test_no_string_literal_mode_dispatch.py` greps for any of the above strings appearing inside an `==` comparison in any `rytm_randomizer/*.py` other than `data/modes.py`. Existing PR-frozen parity callers may be allowlisted with a `# parity-string` comment + ARCHITECTURE.md §8 reference.

### Gate 11 — Shared test fixtures

Test fixtures used in >1 test file live in `tests/conftest.py` (or a `tests/<subpackage>/conftest.py` for subpackage-scoped fixtures). Duplicating a fixture body across test files is rejected at code review.

Known fixtures to centralize when WS-M4 lands: `recording_out`, `fake_mido_session`, `no_sleep`. Today these are inlined in `tests/test_engines_pad{1,2,3,4}.py` and similar.

Enforcement: code review by `code-reviewer`. Optional architecture test (post-WS-M4): `tests/architecture/test_no_duplicate_fixtures.py` greps for `class RecordingOut|class _FakeMessage|def _install_fake_mido|def _no_sleep` and fails if found in >1 location.

### Gate 12 — Module-level constants use `Final` (or frozen dataclass)

Every new module-level constant must be annotated with `typing.Final[T]` (or be a `@dataclass(frozen=True)` instance for grouped constants). Extends the existing house-style rule in `docs/ARCHITECTURE.md` §4.

Bare assignments at module level (`X = 5`) that look like constants but lack `Final` are flagged by `python-reviewer` in code review.

### Gate 13 — Env vars require docs + safe default

Any new environment variable:
1. Must be documented in `CONTRIBUTING.md` AND `docs/LOCAL_DEV_TOOLING_NOTES.md`.
2. Must have a safe default — running without setting it must work.
3. Existing example to mirror: `PARITY_CAPTURE_MODE` (unset = check mode; set = capture mode). Default is safe; capture mode is opt-in.

### Gate 14 — Maintainability review (every plan, every wave)

Every plan must include an explicit **maintainability audit** before the first WS opens its PR, AND a re-audit after the final code WS merges (before the learning phase starts). The audit's findings become inputs to the plan; the re-audit confirms the plan delivered on them.

**Pre-plan audit** must answer (in the plan body or a sibling `docs/<plan>_MAINTAINABILITY_AUDIT.md`):

1. **Onboarding curve** — can a new contributor answer "where do I add X?" using only the repo, in <30 min?
2. **Naming hygiene** — are top-level modules and symbols self-explanatory? Are abbreviations consistent?
3. **Coupling / module boundaries** — any cross-module cycles? Does the architecture diagram match reality?
4. **Magic numbers / strings** — is string-equality dispatch enumerated (Gate 10)? Are constants `Final` (Gate 12)?
5. **Configuration vs convention** — are runtime choices (channels, env vars) configurable or hardcoded?
6. **Test maintainability** — shared fixtures (Gate 11)? Intent-named tests (Gate 8)? Fast-iteration loop documented?
7. **Build / dev loop friction** — clean install + test runtime under what threshold? Pre-commit hooks? Single verify-before-commit script?
8. **Error messages** — does a failure point at the source of truth or at a derived check?
9. **Versioning / release** — single source of truth for version? Documented release script?
10. **Future-proofing** — for the next plausible extension after this plan, how many files does a contributor touch?

**Post-plan re-audit** scores each of the 10 against the pre-plan baseline and lands as `docs/<plan>_MAINTAINABILITY_REPORT.md` alongside the learning report. Net-negative deltas (regressions) are blockers — the plan must add a corrective WS before WS-L (learning) can start.

Enforcement: the WS-S8 sweep includes `tests/architecture/test_maintainability_review_present.py` which fails if a plan referenced in `docs/*PLAN*.md` doesn't have a paired `docs/*MAINTAINABILITY_AUDIT.md` (pre) and `docs/*MAINTAINABILITY_REPORT.md` (post).

The simplification plan's pre-plan audit is the report produced by the agent run on 2026-05-18 (folded into `SIMPLIFICATION_PLAN.md` as WS-M1..WS-M4). The post-plan re-audit runs as part of WS-S8 sweep before Wave 4 starts.

### Gate 15 — Learning phase (every plan, every run)

Every plan must terminate with a **learning extraction phase** that captures non-obvious patterns into the repo, not user-home or session memory. Without this, lessons evaporate and the next plan re-learns them.

**Required outputs (all committed to the repo):**

| Artifact | Path | Purpose |
|---|---|---|
| Reusable agent skills | `.claude/skills/learned/<name>/SKILL.md` | Auto-loaded by future agents; uses `everything-claude-code:learn-eval` rubric (≥3/5 on all dimensions). |
| Project rules | `.claude/rules/<topic>.md` | E.g. `parity-fixture-discipline`, `coverage-gate-100pct`, `cascade-merge-pattern`. |
| Project agent guidance | `.claude/CLAUDE.md` or repo-root `CLAUDE.md` | Appendix linking new skills + rules. |
| Run report | `docs/<plan>_RUN_REPORT.md` | Human-readable: timeline, escalations, lessons, LOC impact. |
| Run log (preserved) | `docs/<plan>_RUN_LOG.md` | Append-only event log from the run. **Not** gitignored. |
| Architecture diff | `docs/<plan>_ARCHITECTURE_BEFORE_AFTER.md` | Side-by-side: module list / new Protocols / deleted-renamed mapping. |
| Replay playbook | `docs/AUTONOMOUS_RUN_PLAYBOOK.md` (or per-plan equivalent) | "How to run the next autonomous multi-PR refactor in this repo." |
| State-file schema | `docs/<plan>_STATE.schema.json` | JSON Schema for the orchestrator state file. |

**Fresh-clone test:** before opening the learning PR, the orchestrator simulates a fresh clone and must answer 5 onboarding questions about what the plan did using only in-repo files. Any gap triggers `doc-updater` and re-validates.

**Forward-port rule:** if the plan extracted user-home `.claude/skills/learned/*` during the run, those skills MUST be forward-ported into the repo-scoped `.claude/skills/learned/` as part of the learning PR. The repo is the canonical home; user-home is convenience-only.

**Codex / collaborator handoff:** if the plan involves an external collaborator's open PR (codex's PR #21 is the current example), the learning phase generates an **in-repo** migration guide (`docs/<plan>_<collaborator>_REBASE_GUIDE.md`), not just a GitHub issue. Issues can be closed; the repo is forever.

Enforcement: `tests/architecture/test_learning_phase_complete.py` (post-WS-S8) fails if a closed plan PR lacks the artifacts above, OR if `.claude/skills/learned/` has user-home skills referenced by the run log but not present in the repo.

### Gate 16 — Execution shape (parallel agents, worktrees, autonomous start-to-finish)

**Every plan in this repo is structured for parallel-agent execution in isolated git worktrees and runs fully autonomously from kickoff through learning-PR-merged with zero human intervention.**

This is a structural rule about how plans are *written*, not just how they're executed. A plan that has manual checkpoints, single-thread sequencing, or "human reviews and approves" steps is rejected at plan-PR review.

#### Mandatory structural elements

Every plan MUST contain, by section:

1. **Workstream graph** — explicit table of WSes with dependencies. WSes with no dependency edge between them MUST be runnable in parallel. Any plan with everything sequential is presumed wrong and must justify the chain.

2. **Per-WS worktree assignment** — every WS names its isolated git worktree path (`<repo>-worktrees/<ws-id>-<short-name>`) and branch (`refactor/<topic>` or `feat/<topic>`). No WS shares a worktree with another WS.

3. **Disjoint-file ownership** — every WS lists the files it owns. Two WSes in the same wave MUST own disjoint file sets; any overlap is a sequencing violation flagged at plan review.

4. **Agent crew per WS** — explicit phase-by-phase agent assignment (planner → tdd-guide → orchestrator implement → refactor-cleaner → coverage gate → reviewers in parallel → doc-updater → PR open). The crew table is the source of truth; the orchestrator dispatches accordingly.

5. **Self-driving decision rules** — for every state the orchestrator can enter, a deterministic action is enumerated. Zero `AskUserQuestion` calls during the run. If a state isn't enumerated, the orchestrator logs and continues with the next eligible action.

6. **Auto-merge cascade** — every plan adopts the cascade-merge pattern proven in PRs #22–#28: `gh pr merge --squash` on `req=SUCCESS`, auto-rebase on cascade DIRTY, keep-both-entries on `docs/STATUS.md` "Recent Cleanup" conflicts. No `--auto`-with-wait; immediate squash-merge.

7. **Auto-rebase rules** — every plan documents the cascade-conflict resolution (typically: `reset --hard origin/<base>` + cherry-pick own commits + auto-resolve known shared-file conflicts + force-push). Conflicts in files no automation knows how to resolve trigger `architect`, never the user.

8. **Persistent state on disk** — every plan defines a `docs/<plan>_STATE.json` (orchestrator current state, per-WS phase, last-merge SHAs) and `docs/<plan>_RUN_LOG.md` (append-only event log). Plans must survive context compaction; on a fresh wake-up the orchestrator reads these files and reconciles via `gh pr list`.

9. **Kickoff trigger** — one of:
   - `/loop run docs/<plan>.md` (manual one-shot via the loop skill, with `<<autonomous-loop-dynamic>>` sentinel re-entry).
   - `CronCreate` armed with `<<autonomous-loop>>` (autonomous from cold).

   Plans must specify which kickoff form they're written for. Both forms work without any further human input.

10. **Termination condition** — explicit, on-disk. Typically: all plan PRs MERGED + learning PR (Gate 15) MERGED + (optional) collaborator handoff issue opened. Orchestrator writes `DONE` to the run log, `TaskStop`s monitors, stops scheduling wake-ups.

11. **Hard time budget** — explicit wall-clock cap (default 72h). At budget exhaustion, orchestrator writes `BUDGET_EXCEEDED` to the run log with current state snapshot and stops. No silent stalls.

12. **Recovery procedure** — explicit steps the orchestrator runs on every wake-up: read state file → query `gh pr list` for live state → reconcile → pick next eligible action. Works after context compaction, after process crash, after user interruption.

13. **Permission profile** — every plan declares the minimum permission mode it runs under (`acceptEdits` for most refactors; `bypassPermissions` only when absolutely necessary and with a documented justification). The orchestrator hard-codes a refuse-list (force-push to base branches, delete branches it doesn't own, close external collaborator PRs).

14. **Stop signals** — every plan documents how a human can interrupt: send `STOP` → orchestrator writes `INTERRUPTED` + `TaskStop`s monitors; `CronDelete` → cron-armed plans halt; close the plan PR → orchestrator detects on next wake and writes `PLAN_REVOKED`.

#### Plans NOT permitted

- ❌ Plans with "wait for user to approve" or "ask the user which approach" steps inside the run.
- ❌ Plans that sequentialize naturally-parallel WSes ("first do A, then B, then C" when A/B/C touch disjoint files).
- ❌ Plans that share a worktree across WSes (the cascade-rebase pattern only works with isolated worktrees).
- ❌ Plans without a written termination condition (open-ended loops are rejected).
- ❌ Plans without a written hard time budget.
- ❌ Plans without an on-disk state file (in-conversation state doesn't survive compaction).
- ❌ Plans whose recovery procedure is "ask the user where we are."

#### Enforcement

- `tests/architecture/test_plan_execution_shape.py` (added in WS-S8) checks every `docs/*PLAN*.md` for the 14 mandatory sections. A plan missing any is a CI failure on the plan PR.
- Plan-PR template (`.github/PULL_REQUEST_TEMPLATE/plan.md`, added in WS-M1) requires the author to confirm each of the 14 elements with file-line citations.
- The `everything-claude-code:planner` agent is configured (via `.claude/CLAUDE.md`) to reject any plan request that can't be structured per this gate, and to refuse "manual" or "step-through" plan shapes.

#### Why this is structural, not stylistic

Every gate in this file is enforced because something went wrong without it. The PRs #22–#28 cleanup batch + the in-flight simplification plan both demonstrated that:

- **Parallel beats serial by 5-10× in wall-clock** when WSes are truly independent (Wave 1's 4 worktrees vs sequential).
- **Worktree isolation eliminates merge conflicts** that would otherwise burn hours of human attention.
- **Autonomous execution beats manual oversight** because human attention is the actual bottleneck; agents are not.
- **On-disk state survives compaction**; in-conversation state does not. Plans that depend on conversation continuity become un-resumable.

Plans that violate Gate 16 are not slower — they are differently structured systems with different failure modes. This repo has decided autonomous parallel execution is its single execution model. Future plans inherit that decision.

### Gate 17 — Abstraction reuse and genericization (codex-dual-machine-cascade findings, made permanent)

**Before any new module / class / non-trivial function lands, two questions must be asked and answered in writing: (a) could it be generalized further, and (b) does an existing abstraction already cover it.**

Lifted from the codex dual-machine cascade (PRs #21, #36-#41), which shipped ~15k LOC of parallel per-device subpackages because nobody asked whether an abstraction already existed. Made permanent because the failure mode recurs whenever new code is written without surveying what is already there.

For every new module / class / non-trivial function in a WS:

1. **Could it be generalized?** If the WS adds N near-identical things (senders, decoders, report builders, dispatch arms, `pad{1-4}_*` functions), they must be ONE generic thing parameterized by a `data/` table — not N copies. Hard-coded counts / ids / CC numbers must be read from `data/` or from a Protocol attribute, not inlined.

2. **Does an existing abstraction cover it?** The new code must consume, not reimplement, the existing abstractions:

   | Abstraction | Location | Reuse when |
   |---|---|---|
   | `Device` Protocol + registry | `devices/` | adding any Elektron device family |
   | `SnapshotDecoder` / `MutationPlanner` / `MessageRenderer` strategies | `devices/strategies/` + `snapshot/` | per-device snapshot decode / plan / render |
   | Elektron SysEx envelope helpers | `snapshot/envelope.py` | any 7-bit unstuffing, kit-record location, ASCII-name read |
   | Generic guarded / hardware senders | `senders/` | sending a device's plan |
   | `dual_machine` target resolver | `dual_machine/targets.py` | resolving `rytm` / `a4` / `both` |
   | `data/` fact tables | `data/` | any "table of facts" |
   | `data/modes.py` `Literal` + `Final` tuples | `data/modes.py` | dispatching on a mode/intensity/page/kind string |
   | `cli_registry.CliCommand` | `cli_registry.py` | adding a CLI command |
   | `MidiMetrics` / `get_metrics()` | `observability/metrics.py` | a hot path sending a CC / making a guardrail decision |
   | `PassiveReportHeader` + formatter helpers | `reports/formatter.py` | a new passive report |
   | `PadRuntimeMixin` / `IsolatedPadMixin` / `PadRuntime` | `engines/_runtime.py` | per-pad runtime state |
   | shared test fixtures | `tests/conftest.py` | `RecordingOut`, `_FakeMessage`, `_install_fake_mido`, `no_sleep` |

Net-new behavior with no existing abstraction is permitted — but the WS must *state* that the question was asked and the shape is justified. "I didn't check" is the violation, not "there is no existing abstraction."

**Enforcement.** Step 7 of the `code-review` skill (`.claude/skills/code-review/SKILL.md`) — the post-push `code-reviewer` agent (`.claude/settings.json` hook) and the codex pre-push review (`docs/CODE_REVIEW_HOOK_SETUP.md`) both produce a mandatory **Abstraction** section. Reimplementing an existing abstraction is at least an Important finding; bypassing a Protocol that an architecture test enforces is Critical. The `tests/architecture/test_device_protocol_enforcement.py` mechanical gate catches the device-family subset.

### Gate 18 — Architecture-doc and diagram freshness (PR-#44-review findings, made permanent)

**A change that adds a subpackage, Protocol, registry, CLI surface, architecture test, or dependency-direction rule MUST update `docs/ARCHITECTURE.md` AND `docs/ARCHITECTURE_DIAGRAMS.md` (the mermaid diagrams) in the same PR.**

Gate 5 already requires "docs updated", but Gate 5 was being satisfied by a `docs/STATUS.md` line alone — leaving the architecture diagrams and the counts they quote silently stale. Gate 18 makes the architecture-doc + diagram freshness explicit and separately checkable. The PR #44 review found `docs/ARCHITECTURE_DIAGRAMS.md` carrying "the architecture map will land in a follow-up wave" two waves after it had landed, and arch-test counts off by `+14`.

For every WS, determine whether it touches the architecture surface, and if so:

1. **New subpackage** → `ARCHITECTURE.md` §2 + `ARCHITECTURE_DIAGRAMS.md` §2 show it.
2. **New Protocol / registry / strategy** → the relevant `ARCHITECTURE.md` section + a diagram reflect it.
3. **New architecture test** → `ARCHITECTURE.md` §7 lists it + the `ARCHITECTURE_DIAGRAMS.md` arch-test counts (§10, §13) are bumped.
4. **New CLI command** → `ARCHITECTURE_DIAGRAMS.md` §14 / §25 show it.
5. **New device family** → §3 / §18 / §19 device diagrams reflect it.
6. **New dependency-direction rule** → `ARCHITECTURE.md` §3 states it.

Then verify, for every touched doc section: the prose is accurate post-change (no "will land later" for landed work, no stale module names); every **count** the docs quote (subpackage / module / test-file / arch-test / golden / device count) matches reality; the affected mermaid diagrams are updated; internal cross-links resolve.

**Enforcement.** Step 8 of the `code-review` skill produces a mandatory **Docs** section. A change that touches the architecture surface without updating the diagrams is an Important finding. `tests/architecture/test_readme_freshness.py` is the mechanical backstop for `README.md` freshness; the architecture-diagram freshness is the human-judgement check the post-push / pre-push review performs.

---

## How a plan declares conformance

Every plan PR must include, in its body, a checklist confirming each gate:

```markdown
## Plan-requirements conformance

Per docs/PLAN_REQUIREMENTS.md, this plan commits to:

- [x] Gate 1 (100% branch coverage on touched files) — applies to all WS.
- [x] Gate 2 (V1.34 parity fixtures byte-identical) — applies to all WS.
- [x] Gate 3 (lint/format/type clean) — applies to all WS.
- [x] Gate 4 (dead-code purge) — per-WS step + dedicated sweep WS.
- [x] Gate 5 (docs updated before PR open) — `doc-updater` is mandatory phase 9.
- [x] Gate 6 (type-system hygiene) — Protocols + frozen dataclasses, no `Any`.
- [x] Gate 7 (observability adoption) — every hot-path module logs + traces.
- [x] Gate 8 (test hygiene) — intent-named tests; mirrors source structure.
- [x] Gate 9 (module-organization hygiene) — subpackages by default; relative imports inside subpackages.
- [x] Gate 10 (string-literal dispatch hygiene) — no new mode/intensity/page strings; use `data/modes.py`.
- [x] Gate 11 (shared test fixtures) — multi-file fixtures live in `tests/conftest.py`.
- [x] Gate 12 (module-level constants use `Final`) — extends house-style rule.
- [x] Gate 13 (env vars: docs + safe default) — every new env var documented and opt-in.
- [x] Gate 14 (maintainability review) — pre-plan audit + post-plan re-audit; regressions block learning phase.
- [x] Gate 15 (learning phase) — every plan ends with learning extraction to repo (skills + rules + reports + handoff guides).
- [x] Gate 16 (execution shape) — parallel agents in worktrees, autonomous start-to-finish, on-disk state, no human gates.
- [x] Gate 17 (abstraction reuse and genericization) — every new module/class surveyed against the existing-abstraction catalog; no reimplementation; net-new shapes justified in writing.
- [x] Gate 18 (architecture-doc and diagram freshness) — `docs/ARCHITECTURE.md` + `docs/ARCHITECTURE_DIAGRAMS.md` updated for every architecture-surface change; quoted counts re-verified.

Exceptions (with rationale):
- (none, or list with one-line rationale each)
```

Plans that omit this checklist are not approved.

---

## How to update this file

This document is itself maintained under the same gates. Updates land via a PR that:

1. Adds the new rule with an enforcement mechanism (CI check, lint rule, architecture test, or reviewer protocol).
2. Cites the run-log entry, PR, or incident that demonstrates the rule is needed.
3. Updates `tests/architecture/test_plan_requirements_referenced.py` so every `docs/*PLAN*.md` is greppable for "Per docs/PLAN_REQUIREMENTS.md".
4. Updates `.claude/CLAUDE.md` if the rule affects every-session agent behavior (not just specific plans).

The file is **append-only-by-default** — gates are removed only when their underlying issue is structurally impossible (e.g. the dead-code purge gate could relax if the language gained native dead-code detection). Loosening a gate requires the same kind of post-mortem evidence that tightening one does.

---

## Cross-references

- `docs/SIMPLIFICATION_PLAN.md` — the current in-flight plan; first plan governed by this file.
- `docs/ARCHITECTURE.md` §8 — the V1.34 parity API surface (untouchable).
- `docs/STATUS.md` — append entries for every cleanup that lands.
- `.claude/skills/learned/` — reusable agent skills extracted from past runs.
- `.claude/rules/` — agent-runtime rules (separate from plan-time rules); see `parity-fixture-discipline.md`, `coverage-gate-100pct.md`, `cascade-merge-pattern.md` when WS-L lands.
- `.coveragerc` — the package-wide coverage ratchet (currently 87% floor; targeted to ratchet to 100% as part of WS-S8).
- `pyproject.toml [tool.ruff]` + `[tool.black]` — the enforcement config for Gate 3.
