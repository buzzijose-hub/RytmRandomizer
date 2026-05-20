# Code-Review Hook Setup

RytmRandomizer runs an automated code review after every `git push`. The
review is **fully automatic and needs no human interaction** — no
copy-paste, no manual step — for both supported agents (Claude Code and
codex) and for plain `git`. This doc explains the three mechanisms that
make that true, how they share one implementation, and why a violation
can never slip through even if a local hook is disabled.

## The 8-step review, and the mechanical / judgement split

Every review walks the 8-step procedure in
[`.claude/skills/code-review/SKILL.md`](../.claude/skills/code-review/SKILL.md).
The eight steps fall into two halves:

- **Steps 1-6 + the lint/architecture/parity gates — *mechanical*.** A
  script can check these: import direction, house style, data-not-code,
  side-effect freedom, no-`Any`, device-Protocol enforcement, the V1.34
  parity goldens, the lint trio.
- **Steps 7-8 — *judgement*.** No script can make these calls:
  - **Step 7 — abstraction reuse / genericization.** For every new
    module/class/function: could it be generalized further, AND does an
    existing abstraction (`Device` Protocol, `snapshot/envelope.py`
    helpers, the generic senders, `cli_registry`, `data/`,
    `observability/metrics`, the report formatter, ...) already cover it?
  - **Step 8 — architecture-doc + diagram freshness.** If the change adds
    a subpackage / Protocol / registry / CLI surface / architecture test,
    `docs/ARCHITECTURE.md` AND `docs/ARCHITECTURE_DIAGRAMS.md` (the mermaid
    diagrams) must be updated, and every count the docs quote must still
    match reality.

So the automation always does the same two things: **run the mechanical
gates with a script, then hand off to an agent for the judgement steps.**
The hand-off is wired differently per environment (below) — but the
contributor never has to do anything by hand.

## One agent per review dimension

The agent half of the review is **not** run as a single wide agent
covering every step. Targeted reviews go deeper — a single agent spread
across architecture + maintainability + observability + docs + abstraction
does each one shallowly. So the review fans out: **one targeted agent per
dimension, dispatched in parallel** (architecture/import-direction, house
style/type hygiene, parity + test hygiene, side effects + mido leakage,
observability, abstraction reuse, docs + diagram freshness), each scoped
to only its dimension and the plan-requirement gates it owns. An
orchestrator then **synthesizes** the per-dimension finding lists into one
consolidated Critical/Important/Minor/Abstraction/Docs verdict and posts a
single PR comment. The dimension→step→gate table is in
[`code-review/SKILL.md`](../.claude/skills/code-review/SKILL.md)
§ "Execution model". This applies to all three mechanisms below.

## One shared gate script

All three mechanisms call **one** implementation of the mechanical gates:
[`scripts/code_review_gate.py`](../scripts/code_review_gate.py). It runs
lint (ruff + black + isort) + `pytest tests/architecture/` + the 685 V1.34
parity items, and has three `--mode`s — `cli`, `codex-hook`, `git-hook` —
one per caller. Because there is a single script, the gates can never
drift between "what `just review` runs" and "what the hook runs".

## The three mechanisms

### 1. Claude Code — `.claude/settings.json` (automatic, zero setup)

Claude Code reads [`.claude/settings.json`](../.claude/settings.json) from
the repo root automatically. The `PostToolUse` hook there fires the
`code-reviewer` agent on any Bash command matching `^\s*git\s+push`. The
agent walks all 8 steps — including the judgement steps 7-8 — and emits the
verdict. **Nothing to install**: clone the repo and it is live.

If your Claude Code version does not support the `Agent` hook action type,
the hook is ignored harmlessly — run the review manually with
`/agent code-reviewer` or `/skill code-review`. (The `.githooks/pre-push`
hook below still runs the mechanical gates regardless.)

### 2. Codex — `.codex/hooks.json` (automatic, zero setup)

Codex reads [`.codex/hooks.json`](../.codex/hooks.json) from the repo root
automatically — it is the codex analogue of `.claude/settings.json`, and
just as zero-setup. Its `PostToolUse` hook runs
`scripts/code_review_gate.py --mode codex-hook` after every tool call. The
script:

- reads the hook's JSON payload on stdin and **no-ops silently** unless the
  tool call was a `git push`;
- on a `git push`, runs the mechanical gates and writes a JSON response:
  - **pass** → `hookSpecificOutput.additionalContext` carrying an
    instruction that re-prompts the codex model to perform the 8-step
    review (Steps 7-8 included) and post the verdict;
  - **fail** → `decision: "block"` with the failing-gate reason, so codex
    sees the failure and self-corrects instead of proceeding.

**Why a `command` hook, not an `agent` hook.** Codex currently runs only
`type: "command"` hook handlers — `prompt` and `agent` handlers are parsed
but *skipped*. So `.codex/hooks.json` cannot dispatch the `code-reviewer`
agent directly the way `.claude/settings.json` can. The workaround is the
`additionalContext` channel: the `command` hook runs the gate script, and
the script injects the 8-step instruction back into the model's own
context. Same review outcome, different plumbing — and still no human in
the loop.

### 3. `.githooks/pre-push` — the universal backstop (every tool)

[`.githooks/pre-push`](../.githooks/pre-push) is a git hook that fires on
**every** `git push` no matter what drives it — Claude Code, codex, a human
at a terminal, an IDE button. It runs `scripts/code_review_gate.py
--mode git-hook` and **aborts the push** (non-zero exit) if any mechanical
gate fails.

It is versioned in the repo and activated by pointing git at it:

```bash
git config core.hooksPath .githooks
```

`just install` and the dev container's `postCreateCommand` run that for
you, so a fresh clone is one `just install` away from having it live. The
pre-push hook covers only the *mechanical* half; the agent hooks (1 and 2)
complete the judgement half.

## `just review` — the explicit one-command full review

`just review` runs the same review on demand (e.g. before you are ready to
push). It runs the mechanical gates via the shared script, then dispatches
the agent by **environment detection** — never a copy-paste:

- Claude Code exports `$CLAUDE_CODE_EXECPATH`; `just review` invokes that
  binary non-interactively (`-p ... --agent code-reviewer`).
- Under codex, `.codex/hooks.json` already runs the review on `git push`;
  `just review` says so and exits.
- If *no* known agent environment is detected, `just review` **fails loudly
  (exit 1)** rather than degrading to a manual checklist — the judgement
  review must not be silently skipped.

`just` is optional (every recipe's raw command is in the
[`Justfile`](../Justfile)); install instructions are in
[`CONTRIBUTING.md` § Local development setup](../CONTRIBUTING.md#local-development-setup).

## Why a disabled hook is still safe — defence in depth

The review is enforced in **four** layers, so disabling any one never lets
a violation merge:

1. **`.githooks/pre-push`** — mechanical gates, every tool, blocks the push.
2. **`.claude/settings.json`** — Claude Code agent review (8 steps).
3. **`.codex/hooks.json`** — codex agent review (8 steps, via re-prompt).
4. **CI** — the `architecture` job in `.github/workflows/test.yml` runs
   `pytest tests/architecture/` (16 test files, ~234 tests) on every PR and
   is a **required status check**. It mechanically re-checks the compliance
   subset server-side (import direction, house style, data-not-code, side
   effects, no-`Any`, device-Protocol enforcement, README freshness, ...).

Layers 1-3 are local and fast; layer 4 is the server-side guarantee. The
agent hooks (2, 3) and `just review` catch the **judgement-level** findings
CI cannot — Step 7 abstraction reuse, Step 8 diagram freshness, missing
tests for new public surface. CI catches the mechanical violations even if
every local hook is off.

## Disabling a hook locally (if it misfires)

- **Claude Code hook** — do not edit the committed `.claude/settings.json`.
  Create `.claude/settings.local.json` (git-ignored); Claude Code merges it
  over `settings.json`.
- **codex hook** — use `/hooks` in the codex CLI to disable an individual
  non-managed hook for your session; do not delete `.codex/hooks.json`.
- **git pre-push hook** — for a genuine emergency only, `git push
  --no-verify` skips it for one push. Discouraged: CI still rejects the
  violation, so you have only deferred the failure.

Do not commit a disabled hook — the team relies on all four layers.

## Cross-references

- [`scripts/code_review_gate.py`](../scripts/code_review_gate.py) — the
  shared mechanical-gate script (3 modes: cli / codex-hook / git-hook).
- [`.claude/settings.json`](../.claude/settings.json) — Claude Code hook.
- [`.codex/hooks.json`](../.codex/hooks.json) — codex hook.
- [`.githooks/pre-push`](../.githooks/pre-push) — universal git pre-push hook.
- [`.claude/agents/code-reviewer.md`](../.claude/agents/code-reviewer.md) —
  the agent definition.
- [`.claude/skills/code-review/SKILL.md`](../.claude/skills/code-review/SKILL.md)
  — the 8-step review procedure.
- [`docs/CODEX_CONTRIBUTING.md`](CODEX_CONTRIBUTING.md) — codex's full
  contribution guide.
- [`.claude/rules/codex-contribution-guide.md`](../.claude/rules/codex-contribution-guide.md)
  — the short codex rule.
- [`CONTRIBUTING.md`](../CONTRIBUTING.md) § Verification gate / § Automated
  post-push code review — the human-facing summary.
- [`.github/workflows/test.yml`](../.github/workflows/test.yml) — the
  `architecture` CI job (the server-side backstop).
