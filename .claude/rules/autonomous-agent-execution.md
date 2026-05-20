# Autonomous agent execution — no human intervention required

**Authority:** This file + `.claude/rules/maximize-parallelization.md` (the sister rule) + `AGENTS.md` § "How to open a PR (autonomous-agent compatible)".
**Scope:** Any AI-agent session doing work in this repo (Claude Code, codex, or any other agent) where the user has asked the agent to drive a task to completion.

## The rule

When the user has asked the agent to **complete a task**, the agent executes end-to-end **without pausing for human confirmation on routine steps**. The agent stops only for:

1. Genuinely irreversible actions (force-push to a protected branch, dropping CODEOWNERS, bumping hardware-pinned packages, deleting refs).
2. Contradictions in the user's instructions that the agent cannot resolve without input.
3. The agent has exhausted its known options and is genuinely stuck.

Pausing after every step ("step 1 done; shall I proceed with step 2?") when the steps are obviously chained is an anti-pattern and will be flagged. Round-trip "may I continue?" latency is the single biggest cost in agentic workflows; eliminate it on routine steps.

This rule is the companion to `.claude/rules/maximize-parallelization.md`: that rule eliminates wall-clock latency within a session; this rule eliminates human-in-the-loop latency between sessions.

## What you MUST do

1. **Continue automatically through chained steps.** If the user asked for "lint clean + commit + push + open PR", complete all four without intermediate confirmation. Report at the end, not at each step.
2. **Make routine local decisions independently.** File edits, formatter fixes, adding a test for a missed branch, running `pytest`, opening a draft PR — all routine. Do them without asking.
3. **Bundle status into one report.** When a sequence is done, report once with the outcome. Don't narrate every tool call.
4. **Use background agents for slow work + continue foreground work.** When you dispatch parallel agents per the parallelization rule, do not idle waiting for them. Do the next non-blocking task. Wait passively only when the next step truly depends on the agent's output.
5. **Treat the user's standing instructions as durable.** If the user said "open a PR and iterate to green," do not ask "may I push commit 3 of the iteration?" Continue iterating.
6. **Surface the right level of detail.** A final status message should answer: what changed, what passed/failed, what the next blocker is (if any), and what (if anything) the user needs to do. Skip the play-by-play.
7. **When in doubt, prefer continuation.** If you cannot decide whether to continue or stop, continuing is usually correct — the user can interrupt you. Stopping wastes their attention.

## What you MUST NOT do

- **Do not** ask "should I continue?" between steps that are obviously chained by the original request.
- **Do not** split a 9-file write into 9 separate "I edited file X, will you review?" messages. One message, all edits parallel (see `maximize-parallelization`), one final report.
- **Do not** pause for human approval on a tool call the user already authorized as part of a larger task. (E.g. "you asked me to open a PR; I will not pause before pushing the branch.")
- **Do not** narrate each tool call. Internal deliberation is not user-facing communication.
- **Do not** stop at "step 3 done" when steps 4-7 were obviously implied.
- **Do not** ask the user to confirm formatter fixes, test-suite invocations, or local file edits. These are reversible.
- **Do not** invent fake stops to manage your own context window — that is what compaction is for.

## Hard stops — when you MUST pause for the user

- **Force-pushing** to `main`, `modularize-v1.34`, or any other protected branch.
- **Bypassing pre-commit hooks** (`--no-verify`, `--no-gpg-sign`).
- **Bumping hardware-pinned packages** (`mido==1.3.3`, `python-rtmidi==1.5.8`). See `.claude/rules/hardware-pinned-packages.md`.
- **Regenerating V1.34 parity fixtures.** See `.claude/rules/parity-fixture-discipline.md`.
- **Dropping CODEOWNERS** or modifying branch-protection rules.
- **`git reset --hard`** / `git clean -fdx` / `git branch -D` on branches the agent doesn't own.
- **Closing a PR the user opened.** (Opening / commenting on / approving PRs you own is fine.)
- **Adding a new entry to a drained architecture-test allowlist** — every entry requires explicit reviewer approval per its rule.
- **The user explicitly paused you** ("wait", "stop", "let me check").
- **A contradiction in the user's prior instructions** that you cannot resolve. State the contradiction concisely; ask one specific question.
- **Genuine ambiguity** about what the user wants. State the ambiguity; offer the two most-likely interpretations; ask which.

## Why this is a rule and not just guidance

Round-trip latency between the user and the agent is the largest single cost in agentic workflows. A 10-step task with a "may I continue?" pause after each step costs 10 round trips. The same task executed autonomously costs 1 round trip. With LLM context costs and human attention both finite, the cumulative cost difference is enormous.

The fix is not "trust the agent more"; it is "encode the autonomy expectation as a rule the agent applies by default, with hard stops for the actions that need human approval." The hard-stops list above is short and specific; everything else is routine and the agent owns the decision.

Past failures this rule prevents:
- PR #35 had an autonomous-multi-WS run that paused 6 times for "shall I commit the WS-S1 work before starting WS-S2?" The user's standing instruction was "do the whole thing, and continue to execute the plan with maximum parallelization and do it autonomously without human intervention. we just want 1 PR at the end of the entire plan execution." The pauses were against the standing instruction.
- The dual-machine cascade (PRs #36 → #37 → ... → #41) was opened serially because the agent treated each WS as needing user confirmation before opening the next PR. The user's standing instruction was for one bundled PR.

## When this rule applies

- The user has asked the agent to **complete a task**, not to **explore options**.
- The user has used phrases like "autonomously", "without intervention", "maximize parallelization", "drive it to green", "iterate until merged", "do all the things", "don't stop until X".
- The agent is in the middle of a multi-step task the user already approved.
- The agent has dispatched parallel sub-agents and they have returned; integrating their work is routine continuation.
- Routine CI iteration on a PR the user opened: fix lint, push, re-watch CI.

## When this rule does NOT apply

- **Exploratory or design questions.** "What do you think of approach X?" expects discussion, not autonomous execution.
- **The user paused the agent.** "Wait" / "stop" / "hold on" override this rule until the user releases.
- **The action hits a hard-stop** from the list above.
- **The agent has genuinely run out of options.** Stating "I have tried A, B, C; all failed; I'm stuck on Y" is correct and is not a violation of this rule.
- **The user has explicitly asked to review each step.** Plain-language overrides — if the user says "show me each commit before pushing", do that.

## How to communicate progress without pausing

The point of this rule is not to suppress communication — it is to suppress *confirmation requests*. The agent should still communicate:

- **At kickoff:** a one-sentence statement of what's about to happen.
- **At key inflection points:** "I found X; pivoting to Y" or "the sub-agent returned; integrating now."
- **At completion:** a final status message with what changed, what passed/failed, and what's next.
- **At hard stops:** state the hard stop, name the rule, ask one specific question.

What to suppress:
- "Step 1 of 9 done. Should I continue with step 2?" (when the user asked for all 9).
- Narrating every Read / Grep / Bash call (the tool calls themselves are visible to the harness; agents do not need to mirror them in text).
- Asking permission for actions already authorized by the original request.

## Examples

- **GOOD:** User: "lint, commit, and push." Agent runs lint, fixes one isort issue, commits, pushes, reports the SHA and CI URL. One message at the end.
- **GOOD:** User: "iterate until CI is green." Agent monitors CI, fixes the failure, pushes, re-watches, repeats. Reports the final green state. Does not ask permission for each iteration.
- **GOOD:** Agent dispatches 4 parallel sub-agents per the parallelization rule, continues with non-blocking edit work in the foreground, integrates the sub-agents' outputs when they return, commits, pushes, opens PR. Final status: one comprehensive summary.
- **BAD:** Agent finishes one of 4 parallel sub-agent tasks and asks "agent 1 is done; shall I dispatch agent 2?" (all 4 should have been dispatched together).
- **BAD:** Agent commits a change locally and asks "shall I push now?" when the user said "commit and push".
- **BAD:** Agent re-asks "I have CI red on coverage; shall I add a test?" when the user said "iterate to green" and the cause is obvious.
- **BAD:** Agent stops after each gate of an 18-gate conformance check to ask if the gate was filled correctly.

## How this composes with the other rules

- `maximize-parallelization` says: do the work in parallel.
- `autonomous-agent-execution` (this rule) says: don't pause for human confirmation between parallel batches OR within a chained sequence.

Together they say: identify all independent work, dispatch in parallel, integrate, continue, report once at the end. The wall-clock + round-trip-count product is minimized.

## Cross-references

- `.claude/rules/maximize-parallelization.md` — the sister rule (within-session latency).
- `.claude/rules/cascade-merge-pattern.md` — the same fan-out + integrate shape applied to PRs.
- `.claude/rules/pr-body-conformance-checklist.md` — the gate the agent must fill at PR-open time.
- `.claude/rules/hardware-pinned-packages.md` — the hard-stop on mido/rtmidi bumps.
- `.claude/rules/parity-fixture-discipline.md` — the hard-stop on V1.34 fixture regeneration.
- `AGENTS.md` § "How to open a PR (autonomous-agent compatible)" — the operational recipe.
- `CLAUDE.md` — the per-session guardrails that reference this rule.
