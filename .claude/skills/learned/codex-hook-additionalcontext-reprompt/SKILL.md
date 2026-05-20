---
name: codex-hook-additionalcontext-reprompt
description: "Codex CLI hooks run only type:command handlers (agent/prompt are skipped). Re-prompt the model via hookSpecificOutput.additionalContext."
user-invocable: false
origin: auto-extracted
---

# Codex CLI hooks: re-prompt the model via `additionalContext`

**Extracted:** 2026-05-19
**Context:** Wiring an automatic post-push code review for both Claude Code
and the OpenAI codex CLI from one repo (RytmRandomizer's
`docs/CODE_REVIEW_HOOK_SETUP.md`). Codex hooks cannot dispatch an agent the
way Claude Code's `.claude/settings.json` `Agent` action can.

## Problem

You want a hook (e.g. a `PostToolUse` hook on `git push`) to make the agent
*do something* — run a review, follow a checklist, call a sub-agent.

- **Claude Code** supports `"action": {"type": "Agent", "agent": "..."}` in
  `.claude/settings.json` — the hook directly dispatches an agent.
- **Codex CLI** (hooks GA, May 2026) parses `prompt` and `agent` hook
  handler types **but skips them — only `type: "command"` handlers run.**

So a codex hook can only run a *shell command*. It cannot, by itself, make
the codex model perform a multi-step task. A naive port of a Claude Code
`Agent` hook to codex silently does nothing.

## Solution

A codex `type: "command"` hook script can still steer the model: it writes
JSON to **stdout**, and the `hookSpecificOutput.additionalContext` field is
injected back into the model's context as extra developer instructions. Use
the command hook to do the mechanical work, then emit `additionalContext`
that *re-prompts the model* to do the judgement work.

### Codex hook config — `<repo>/.codex/hooks.json` (zero-setup, repo-local)

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "^(Bash|shell|local_shell)$",
        "hooks": [
          {
            "type": "command",
            "command": "python3 \"$(git rev-parse --show-toplevel)/scripts/my_hook.py\"",
            "timeout": 240,
            "statusMessage": "Running the post-push gate"
          }
        ]
      }
    ]
  }
}
```

Codex auto-discovers `<repo>/.codex/hooks.json` (and `~/.codex/hooks.json`,
or inline `[hooks]` tables in `config.toml`). The `matcher` matches the
**tool name**, not the command string — so the script must filter for the
specific command itself.

### The hook script — stdin/stdout contract

The hook receives JSON on **stdin**:
```json
{
  "session_id": "...", "cwd": "...", "hook_event_name": "PostToolUse",
  "tool_name": "Bash", "tool_input": {"command": "git push ..."},
  "tool_response": ...
}
```

The script writes a JSON response to **stdout**:
- **Steer the model:** `{"hookSpecificOutput": {"hookEventName":
  "PostToolUse", "additionalContext": "Now do X, Y, Z..."}}` — the
  `additionalContext` string becomes developer context the model acts on.
  This is how you "dispatch an agent task" without an `agent` handler.
- **Block / report failure:** `{"decision": "block", "reason": "..."}` —
  for `PostToolUse` this does not undo the completed tool call; codex
  records the reason, replaces the tool result with it, and continues the
  model from there (so the model sees the failure and self-corrects).
- Exit code `2` + feedback on **stderr** is an alternative failure signal.
- The hook process itself can exit `0`; the JSON carries the verdict.

```python
#!/usr/bin/env python3
import json, re, sys

payload = json.loads(sys.stdin.read() or "{}")
if payload.get("tool_name") not in {"Bash", "shell", "local_shell"}:
    sys.exit(0)                                   # not a shell call -> no-op
command = (payload.get("tool_input") or {}).get("command", "")
if not re.search(r"^\s*git\s+push(\s|$)", command):
    sys.exit(0)                                   # not `git push` -> no-op

passed = run_mechanical_gates()                   # your work here
if passed:
    out = {"hookSpecificOutput": {
        "hookEventName": "PostToolUse",
        "additionalContext": "Gates passed. Now walk the 8-step review "
                             "in .claude/skills/code-review/SKILL.md and "
                             "post the verdict as a PR comment."}}
else:
    out = {"decision": "block",
           "reason": "Gates FAILED — fix the cause before continuing."}
json.dump(out, sys.stdout)
sys.exit(0)
```

In this repo the real implementation is `scripts/code_review_gate.py`
(`--mode codex-hook`) and the hook config is `.codex/hooks.json`. The same
script also serves `just review` (`--mode cli`) and the `.githooks/pre-push`
hook (`--mode git-hook`) — one mechanical-gate implementation, three callers.

## When to Use

- Porting a Claude Code `Agent`-action hook to codex — it will not work as
  an `agent` handler; convert it to a `command` handler that emits
  `additionalContext`.
- Any time you want a codex hook to make the *model* (not just a script) do
  follow-up work.
- Cross-agent automation: keep one shared script doing the mechanical part,
  and give each agent its own thin hook config (Claude Code: native `Agent`
  action; codex: `command` hook + `additionalContext` re-prompt).

## Pitfalls

- The codex hook `matcher` matches **tool name only**. Filter the actual
  command (e.g. `git push`) inside the script.
- A codex-hook script that writes anything other than the response JSON to
  **stdout** corrupts the channel — send diagnostics to **stderr**.
- A hook that hard-fails on a parse error or a missing dependency can block
  every tool call. Make the no-op path bulletproof: unparseable stdin,
  empty stdin, wrong tool → `exit 0`, write nothing.

## Cross-references

- `docs/CODE_REVIEW_HOOK_SETUP.md` — the full three-mechanism review wiring
  this pattern is part of.
- `.codex/hooks.json` · `scripts/code_review_gate.py` — the live
  implementation in this repo.
- [[parallel-agent-bundle]] — related multi-agent execution pattern.
