# Maximize parallelization of independent work

**Authority:** This file + `.claude/skills/learned/parallel-agent-bundle/SKILL.md` (operational mechanics).
**Scope:** Any AI-agent session doing work in this repo (Claude Code, codex, or any other agent) where the requested task can be decomposed into two or more independent units of work.

## The rule

When an agent identifies N independent units of work — units whose inputs do not depend on each other's outputs — it **must** dispatch them in parallel, not serially. "In parallel" means:

- Multiple tool calls in a **single** assistant message (Read / Grep / Bash / Edit / Agent), OR
- Multiple `Agent` tool calls with `run_in_background: true` in a single message, then continuing with non-overlapping work while they execute.

Serial dispatch (`call; wait; call; wait; ...`) of independent work is an anti-pattern and will be flagged in code review.

This is the same shape as `.claude/rules/cascade-merge-pattern.md` applied to in-session work: parallel fan-out, then integrate at the end.

## What you MUST do

1. **Decompose first.** Before issuing any tool call, scan the task for independent units (disjoint files, independent checks, unrelated research topics, independent file reads).
2. **Bundle independent tool calls into one message.** Reads, Greps, and Bash commands with no inter-dependencies go into a single assistant turn so the harness executes them concurrently.
3. **Use background agents for slow work.** When dispatching multiple `Agent` calls, set `run_in_background: true` and pre-declare each agent's file scope in its prompt so scopes stay disjoint. Then continue with non-overlapping work while they run.
4. **Enforce disjoint file ownership across parallel agents.** Each agent in a parallel bundle owns a distinct set of files — never two agents writing the same file. The orchestrator declares the scope; see `.claude/skills/learned/parallel-agent-bundle/SKILL.md` for the operational pattern and `.claude/skills/learned/parallel-agents-need-git-worktrees/SKILL.md` for the isolation mechanism when checkouts diverge.
5. **Integrate at the end.** Collect outputs, resolve any boundary stitching, then commit. The fan-out + merge shape is the same as `cascade-merge-pattern`.
6. **Run independent checks together.** `pytest`, `ruff`, `black --check`, `isort --check-only`, and architecture tests have no inter-dependencies — dispatch them as multiple `Bash` tool calls in **one** message.

## What you MUST NOT do

- **Do not** write N unrelated files in N sequential `Edit`/`Write` calls across N messages when no file's content depends on another's. One message, N parallel calls.
- **Do not** spawn agents sequentially (`Agent(); wait; Agent(); wait; ...`) when each agent's prompt is independent of the others' outputs.
- **Do not** run `pytest`, `ruff`, `black --check`, `isort --check-only` as four separate `Bash` calls in four separate messages. They are independent — one message, four calls.
- **Do not** read six files one at a time when none of the content informs which file to read next. One message, six `Read` calls.
- **Do not** dispatch parallel agents that overlap on the same files. Overlap turns parallel work into a merge-conflict generator; pre-declare scope and refuse to dispatch on overlap.
- **Do not** force parallelism where real dependencies exist. Inventing fake independence to justify parallel dispatch produces wrong answers; see the "When this rule does NOT apply" section.

## Why this is a rule and not just guidance

Agent sessions in this repo are wall-clock-bound by the **slowest** tool call in a chain. Serial dispatch of independent work multiplies that latency linearly with N. The cascade-merge run (PR #35) and the dual-machine redo (PR #36 target) both have many independent WS-shaped units; running them in series was the original failure mode the orchestrator was rewritten to avoid. Encoding the parallel-dispatch expectation as a rule — not a suggestion — keeps future orchestrators (Claude Code, codex, or whatever comes next) from regressing to serial fan-out the moment the prompt gets long.

Guidance gets forgotten under context pressure. A rule is checked.

## When this rule applies

- Multi-file edits across **disjoint** files (writing several test files for different modules; updating multiple unrelated docs; touching `AGENTS.md`, `CLAUDE.md`, and `.gitattributes` in one pass).
- Running multiple independent checks (lint + architecture tests + parity tests + full `pytest`) as part of a verification phase.
- Spawning multiple `Agent` calls where each agent's `subagent_type`, prompt, and file scope differ but none consumes the others' outputs.
- Researching multiple topics that don't inform each other (e.g. "look up the Analog Four SysEx envelope" and "summarize the V1.34 scene runner" in the same session).
- Reading multiple files where the content of one doesn't determine which file to read next (e.g. reading `cascade-merge-pattern.md` and `device-protocol-strategy.md` together when drafting a new rule).

## When this rule does NOT apply

- **Sequential dependencies.** When a later step needs the output of an earlier one ("first survey the codebase, then write tests based on what you found"; "first read `docs/STATUS.md`, then update it"), serial execution is correct. Don't fabricate independence.
- **Decision-then-action.** When the first tool call's output decides whether the second call is even needed (e.g. `git status` to check if there is anything to commit, then `git commit` only if yes), the calls are dependent.
- **Same-file edits.** Two `Edit` calls against the same file must be sequential — the second `Edit` reads the file state the first one wrote.
- **Confirmation gates.** When a step requires user confirmation before proceeding (commit, push, destructive operations), do not parallelize past the gate.
- **Single-step tasks.** If the task is one tool call, this rule is a no-op.

## How to identify parallelizable work

A practical heuristic — for each candidate tool call in a planned sequence, ask:

1. **Does call B's prompt or arguments depend on call A's output?** If no, they are independent.
2. **Does call B write to a file call A also writes?** If yes, they conflict and must be sequential (or split across worktrees per `parallel-agents-need-git-worktrees`).
3. **Does call B's correctness depend on call A having already happened?** If no, they are independent.

If all three answers point to independence, the calls **must** be bundled into one message. If any answer flips, keep them sequential.

For agents, the same test applies to each agent's prompt: if you can write each prompt without referring to "the output of the previous agent," they are independent and must be dispatched in one message.

### Examples

- **GOOD:** 4 parallel `Agent` calls in one message, each writing one test file for a different module (e.g. `tests/test_devices_strategies_analog_rytm_snapshot_decoder.py`, `..._mutation_planner.py`, `..._message_renderer.py`, `..._registration.py`) — disjoint files, independent prompts.
- **GOOD:** 3 `Bash` calls in one message: `pytest -o addopts='' tests/architecture/`, `ruff check rytm_randomizer/`, `black --check rytm_randomizer/`. Independent verifiers, no shared state.
- **GOOD:** 2 `Read` calls in one message reading `.claude/rules/cascade-merge-pattern.md` and `.claude/rules/device-protocol-strategy.md` when drafting a new rule that needs to match both styles.
- **BAD:** Writing `AGENTS.md`, then `CLAUDE.md`, then `.gitattributes` in three separate sequential `Edit` calls across three messages when none depend on the others.
- **BAD:** Dispatching agent 1, waiting for its completion, then dispatching agent 2, when agent 2's prompt was knowable up front.
- **BAD:** Running `pytest`, `ruff`, `black --check`, and `isort --check-only` as 4 separate `Bash` calls across 4 separate messages.
- **BAD:** Reading 6 files one at a time across 6 messages when the file list was already known and no file's content determines what to read next.

## Cross-references

- `.claude/rules/parallel-agent-composition.md` — **the companion rule**: this
  file says dispatch in parallel; that one says how to verify the parallel
  outputs actually compose. A run that follows this rule and not that one
  produces eleven individually-green agents and a broken merge.
- `.claude/skills/learned/parallel-agent-bundle/SKILL.md` — operational pattern for dispatching parallel agents with pre-declared disjoint file scopes.
- `.claude/skills/learned/parallel-agents-need-git-worktrees/SKILL.md` — when parallel agents must each have an isolated checkout (file overlap or branch divergence).
- `.claude/rules/cascade-merge-pattern.md` — the same fan-out + integrate shape applied to PRs instead of in-session work.
- `AGENTS.md` — the top-level agent contract for this repo.
