# Autonomous Run Playbook

How to run the next autonomous multi-WS simplification or refactor in this repo, distilled from the run that produced PR #35 (Wave 1 bundle).

This playbook assumes the executor (Claude Code orchestrator) has `acceptEdits` permission, `gh` CLI installed, and the repo cloned at the working directory.

---

## 1. Write the plan

Author `docs/<PLAN_NAME>.md`. The plan MUST conform to all 16 gates in `docs/PLAN_REQUIREMENTS.md`, including:

- Workstream graph (table with explicit dependencies — anything not dependency-linked is parallel-eligible).
- Per-WS worktree assignment or bundled-branch assignment (one or the other, not both).
- Disjoint-file ownership per WS (the parallel-agent-bundle pattern requires explicit FORBIDDEN lists).
- Agent crew per WS (planner → tdd-guide → orchestrator implement → refactor-cleaner → coverage gate → reviewers → doc-updater → PR open).
- Self-driving decision rules (zero `AskUserQuestion` calls during the run).
- Auto-merge cascade or bundle decision (see step 5 below).
- Persistent state on disk (`docs/<PLAN>_STATE.json` + `docs/<PLAN>_RUN_LOG.md`).
- Hard time budget (default 24h after the PR #35 measurement; original plans defaulted to 72h which was 6x too high).

The plan-PR's body MUST contain the conformance checklist marker `Per docs/PLAN_REQUIREMENTS.md`. The architecture test `tests/architecture/test_plan_requirements_referenced.py` enforces this.

## 2. Branch off the canonical base

```powershell
git fetch origin
git checkout -b chore/<plan>-bootstrap origin/modularize-v1.34
# Persist initial state files.
git add docs/<PLAN>_STATE.json docs/<PLAN>_RUN_LOG.md
git commit -m "chore(<plan>): bootstrap state files"
git push -u origin chore/<plan>-bootstrap
gh pr create --base modularize-v1.34 --title "Bootstrap <plan> orchestrator"
```

## 3. Decide: per-PR cascade or bundled branch?

**Per-PR cascade** (one PR per WS, `gh pr merge --squash` per WS):

- Use when base branch is **not** protection-gated on per-PR human approval.
- Each WS gets its own `git worktree add` (see `.claude/skills/learned/parallel-agents-need-git-worktrees/`).
- Auto-rebase the next WS on top when its predecessor merges (see `.claude/skills/learned/rebase-after-squash-merge/`).
- This was the PR #22-#28 pattern.

**Bundled branch** (one PR for N WSes, merged together):

- Use when base branch requires per-PR human approval and that approval would stall the cascade.
- Create one integration branch (`refactor/<plan>-bundled`); each WS commits directly to it (or onto its own sub-branch that gets `git merge --no-ff`-bundled).
- See `.claude/skills/learned/cascade-merge-pattern/` for the merge-and-conflict-resolution mechanics.
- This was the PR #35 pattern.

The choice goes into the plan body and the orchestrator state machine. **Do not change mid-run.**

## 4. Dispatch parallel agents per wave

For each wave of dependency-independent WSes, dispatch all of them in a single message (each as its own background task or each as its own Skill / Agent invocation):

```
Single message, N tool calls:
- WS-A planner: "Plan WS-A. Owned files: X, Y, Z. FORBIDDEN: shared file list."
- WS-B planner: "Plan WS-B. Owned files: A, B, C. FORBIDDEN: shared file list."
- WS-C planner: "Plan WS-C. Owned files: P, Q, R. FORBIDDEN: shared file list."
```

Measured cadence from PR #35 Wave 1: 7 planners returned in 369s wall-clock (slowest); serial would have been 1855s. 5x compression.

For the **implementation phase** of bundled-branch plans, the disjoint-file rule (see `.claude/skills/learned/parallel-agent-bundle/`) lets the agents write to the same branch simultaneously — no worktree-per-agent required. The 4-way batch (WS-S6/S7/S9/M3) in PR #35 proved this at N=4.

## 5. Run the gate cascade per WS

Each WS must clear all 16 gates from `docs/PLAN_REQUIREMENTS.md` before its branch is mergeable. Spot-checks at minimum:

```powershell
# Gate 1 (100% branch coverage on touched files)
$touched = git diff --name-only origin/<base>...HEAD -- 'rytm_randomizer/*.py'
$cov_args = $touched | ForEach-Object { "--cov=$($_ -replace '/', '.' -replace '\.py$','')" }
pytest @cov_args --cov-branch --cov-fail-under=100 --cov-report=term-missing

# Gate 2 (V1.34 parity)
pytest tests/test_engines_pad*.py tests/test_group_runner.py tests/test_scene_runner.py -q

# Gate 3 (lint/format/type clean)
python -m ruff check .
python -m black --check .
python -m isort --profile black --check-only .
python -m pyright --strict $touched

# Architecture tests (the WS-S8 set, when present)
pytest tests/architecture/ -q
```

If any gate fails, auto-revert the last commit + re-dispatch `tdd-guide` (Gate 1 gap) or `architect` (Gate 2 / structural failure). Max 2 retries per WS; 3rd retry escalates to a blocked-WS state and the orchestrator continues with remaining WSes.

## 6. Security review before opening the PR

Dispatch `security-reviewer` on the full WS diff (or on the bundle as a whole, before opening PR for review). Triage:

- CRITICAL / HIGH: fix in same PR / bundle, do not open until clean.
- MED: fix in same PR / bundle (PR #35 had 1 MED, remediated in ~30 min).
- LOW: fix opportunistically, can defer to follow-up if budget tight (PR #35 had 3 LOW, all remediated same PR).

## 7. Open the PR and wait for human approval

```powershell
gh pr create --base modularize-v1.34 --title "<plan>: Wave N bundle" `
  --body "Implements WSes <list>. Per docs/<PLAN>.md and docs/PLAN_REQUIREMENTS.md..."
```

The orchestrator now waits. Wake-up cadence: **1200s** while waiting on CI; **60-90s** while reconciling cascade conflicts. If `mergeable=BLOCKED` for >2h with no human activity, log and continue with other waves — do not poll uselessly.

## 8. Run the learning phase

Once all code waves merge, before declaring DONE, run the learning extraction phase (Gate 15):

- Extract reusable patterns into `.claude/skills/learned/<name>/SKILL.md`.
- Extract rules into `.claude/rules/<topic>.md`.
- Write the run report (`docs/<PLAN>_RUN_REPORT.md`), architecture diff (`docs/<PLAN>_ARCHITECTURE_BEFORE_AFTER.md`), and replay playbook update.
- Generate the collaborator hand-off if applicable (`docs/PR<N>_REBASE_GUIDE.md` + `docs/PR<N>_MODULE_MAPPING.md`).

## 9. Terminate

Write `DONE` to `docs/<PLAN>_RUN_LOG.md`. Call `TaskStop` on any active monitors. Stop scheduling wake-ups.

If the time budget exhausts before DONE, write `BUDGET_EXCEEDED` instead with the current state snapshot, and stop.

---

## Quick reference: when each skill / rule fires

| Situation | Consult |
|---|---|
| Base allows agent auto-merge | `.claude/skills/learned/parallel-agents-need-git-worktrees/` (per-PR cascade) |
| Base requires per-PR approval | `.claude/skills/learned/cascade-merge-pattern/` (bundle pattern) |
| Dispatching N agents at one branch | `.claude/skills/learned/parallel-agent-bundle/` |
| Adding a new Elektron device | `.claude/skills/learned/elektron-sysex-envelope/` |
| Touching parity-fixture-adjacent code | `.claude/rules/parity-fixture-discipline.md` |
| Computing coverage for a WS | `.claude/rules/coverage-gate-100pct.md` |
| Picking per-PR vs bundle | `.claude/rules/cascade-merge-pattern.md` |
| Rebasing after a squash merge | `.claude/skills/learned/rebase-after-squash-merge/` |
| Branch-protection + path-filtered jobs | `.claude/skills/learned/branch-protection-with-path-filters/` |
| Coverage numbers disagreeing | `.claude/skills/learned/coverage-py-blended-vs-pure-branch/` |

---

## Cross-references

- `docs/SIMPLIFICATION_PLAN.md` — the worked example this playbook generalizes.
- `docs/SIMPLIFICATION_RUN_REPORT.md` — narrative outcome of the PR #35 run.
- `docs/PLAN_REQUIREMENTS.md` — the 16 gates every plan in this repo inherits.
