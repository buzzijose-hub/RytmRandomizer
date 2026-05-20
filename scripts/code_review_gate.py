#!/usr/bin/env python3
"""Shared code-review gate for RytmRandomizer.

ONE script, three callers — so the review behaves identically no matter who
or what triggers it (Claude Code, codex, a human, or plain ``git``):

  * ``--mode cli``       ``just review`` runs this directly. Runs the
                         mechanical gates and exits non-zero on failure.
  * ``--mode codex-hook`` The codex ``PostToolUse`` hook
                         (``.codex/hooks.json``) runs this. It reads the
                         hook JSON on stdin, no-ops unless the tool call was
                         a ``git push``, runs the gates, and writes a JSON
                         response on stdout: on success an
                         ``additionalContext`` instruction telling the codex
                         model to perform the 8-step code review; on failure
                         a ``decision: block`` with the failure reason.
  * ``--mode git-hook``  The ``.githooks/pre-push`` script runs this. Runs
                         the gates and exits non-zero (which aborts the
                         push) on failure. Works for ANY tool, including raw
                         ``git`` with no agent at all.

The "mechanical gates" are the part a script CAN check on its own:

  1. lint trio   -- ruff + black --check + isort --check-only
  2. architecture -- pytest tests/architecture/ -q
  3. V1.34 parity -- pytest -m "not fast" -q  (the 685 parity items)

The two judgement steps of the 8-step review — Step 7 (abstraction reuse /
genericization) and Step 8 (architecture-doc + diagram freshness) — are NOT
mechanical. No script can make those calls. So this gate's job is:
run the mechanical part, then HAND OFF to an agent for the judgement part.
The hand-off is mode-specific (see the per-mode docs above and
docs/CODE_REVIEW_HOOK_SETUP.md).

Usage:
    python scripts/code_review_gate.py --mode cli
    python scripts/code_review_gate.py --mode codex-hook   # stdin = hook JSON
    python scripts/code_review_gate.py --mode git-hook
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

# Matches a `git push` invocation as the *command* the agent ran. Anchored so
# `git push-mirror`-style typos or a `git log --grep="push"` do not trip it.
_GIT_PUSH_RE = re.compile(r"^\s*git\s+push(\s|$)")

# The instruction handed back to the codex model after the mechanical gates
# pass. Codex's hook `agent`/`prompt` handler types are parsed-but-skipped
# (only `command` runs), so we cannot dispatch the code-reviewer agent from
# the hook directly. Instead the `command` hook injects this as
# `additionalContext` — extra developer context the model acts on — which
# re-prompts codex to run the judgement half itself.
_CODEX_HANDOFF = (
    "A `git push` just completed. The mechanical code-review gates "
    "(lint + architecture + V1.34 parity) PASSED. You must now complete the "
    "code review of the pushed commits (`git diff modularize-v1.34...HEAD`) "
    "by following .claude/skills/code-review/SKILL.md. Run it as ONE "
    "TARGETED AGENT PER REVIEW DIMENSION, in parallel — not one wide agent "
    "covering every dimension (see the skill's 'Execution model' section "
    "for the dimension table). Spawn separate agents for: architecture / "
    "import-direction; house style / type hygiene; parity + test hygiene; "
    "side effects + mido leakage; observability; abstraction reuse / "
    "genericization (Step 7 — could the new code be generalized, or does an "
    "existing abstraction such as the Device Protocol, snapshot/envelope "
    "helpers, the generic senders, cli_registry, data/, observability/"
    "metrics, or the report formatter already cover it); and docs + diagram "
    "freshness (Step 8 — are docs/ARCHITECTURE.md and "
    "docs/ARCHITECTURE_DIAGRAMS.md updated for any architecture-surface "
    "change, and do the counts the docs quote still match). Then synthesize "
    "the per-dimension findings into ONE structured "
    "Critical/Important/Minor/Abstraction/Docs verdict and post it as a "
    "single PR comment."
)

# Each gate: (label, argv). argv runs with cwd=REPO_ROOT.
_GATES: tuple[tuple[str, list[str]], ...] = (
    ("Lint: ruff", [sys.executable, "-m", "ruff", "check", "."]),
    (
        "Lint: black --check",
        [sys.executable, "-m", "black", "--check", "--target-version=py311", "."],
    ),
    (
        "Lint: isort --check-only",
        [sys.executable, "-m", "isort", "--profile", "black", "--check-only", "."],
    ),
    (
        "Architecture tests",
        [sys.executable, "-m", "pytest", "tests/architecture/", "-q"],
    ),
    (
        "V1.34 parity (685 items)",
        [sys.executable, "-m", "pytest", "-m", "not fast", "-q"],
    ),
)


def _run_gate(label: str, argv: list[str], *, quiet: bool) -> tuple[bool, str]:
    """Run one gate. Return (passed, captured_output).

    When ``quiet`` (the codex-hook path — stdout is reserved for the hook's
    JSON response) the gate's output is captured and only surfaced on
    failure. Otherwise it streams live.
    """
    if quiet:
        proc = subprocess.run(argv, cwd=REPO_ROOT, capture_output=True, text=True)
        return proc.returncode == 0, (proc.stdout or "") + (proc.stderr or "")
    print(f"=== {label} ===", flush=True)
    proc = subprocess.run(argv, cwd=REPO_ROOT)
    ok = proc.returncode == 0
    print(
        f"--- {label}: {'PASSED' if ok else f'FAILED (exit {proc.returncode})'} ---\n",
        flush=True,
    )
    return ok, ""


def run_mechanical_gates(*, quiet: bool) -> tuple[bool, list[str]]:
    """Run all mechanical gates. Return (all_passed, failure_labels)."""
    failures: list[str] = []
    for label, argv in _GATES:
        passed, output = _run_gate(label, argv, quiet=quiet)
        if not passed:
            failures.append(label)
            if quiet and output:
                # Surface failing-gate output on stderr so it is not lost
                # (stdout is the hook's JSON channel).
                print(f"--- {label} FAILED ---\n{output}", file=sys.stderr)
    return not failures, failures


def _mode_cli() -> int:
    """`just review` path: run gates, exit non-zero on failure."""
    passed, failures = run_mechanical_gates(quiet=False)
    if not passed:
        print(
            f"Mechanical review gates FAILED: {', '.join(failures)}.\n"
            "Fix the cause before pushing — do not bypass the gate.",
            flush=True,
        )
        return 1
    print("Mechanical review gates passed (lint + architecture + parity).")
    return 0


def _read_codex_hook_command() -> str | None:
    """Parse the codex hook JSON on stdin. Return the Bash command, or None.

    The codex PostToolUse hook delivers a JSON object on stdin with
    ``tool_name`` and ``tool_input``. For a Bash tool call ``tool_input`` has
    a ``command`` string. Returns None when the payload is not a Bash call or
    is unparseable (the hook then no-ops, never blocks).
    """
    raw = sys.stdin.read()
    if not raw.strip():
        return None
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        return None
    if not isinstance(payload, dict):
        return None
    if payload.get("tool_name") not in {"Bash", "shell", "local_shell"}:
        return None
    tool_input = payload.get("tool_input")
    if not isinstance(tool_input, dict):
        return None
    command = tool_input.get("command")
    return command if isinstance(command, str) else None


def _mode_codex_hook() -> int:
    """Codex PostToolUse hook path.

    Reads the hook JSON on stdin. If the tool call was not a `git push`,
    writes nothing and exits 0 (silent no-op). If it WAS a `git push`, runs
    the mechanical gates and writes a JSON response on stdout:
      * pass -> hookSpecificOutput.additionalContext = the 8-step hand-off.
      * fail -> decision "block" + reason, so codex sees the failure and
                self-corrects rather than proceeding.
    The hook process itself always exits 0; the JSON carries the verdict.
    """
    command = _read_codex_hook_command()
    if command is None or not _GIT_PUSH_RE.search(command):
        return 0  # not a git push (or not a shell call) -> no-op

    passed, failures = run_mechanical_gates(quiet=True)
    if passed:
        response = {
            "hookSpecificOutput": {
                "hookEventName": "PostToolUse",
                "additionalContext": _CODEX_HANDOFF,
            }
        }
    else:
        response = {
            "decision": "block",
            "reason": (
                "Code-review mechanical gates FAILED after `git push`: "
                f"{', '.join(failures)}. Fix the cause (see the failing "
                "output above), re-run, and do not bypass the gate. Then "
                "complete the 8-step code review in "
                ".claude/skills/code-review/SKILL.md."
            ),
        }
    json.dump(response, sys.stdout)
    sys.stdout.write("\n")
    return 0


def _mode_git_hook() -> int:
    """git pre-push hook path: run gates, non-zero exit aborts the push."""
    print("[pre-push] Running mechanical code-review gates…", flush=True)
    passed, failures = run_mechanical_gates(quiet=False)
    if not passed:
        print(
            f"[pre-push] BLOCKED — gates failed: {', '.join(failures)}.\n"
            "[pre-push] Fix the cause and push again. To bypass in a genuine "
            "emergency only: `git push --no-verify` (discouraged — CI will "
            "still reject the violation).",
            file=sys.stderr,
            flush=True,
        )
        return 1
    print(
        "[pre-push] Mechanical gates passed. NOTE: the 8-step review's "
        "Step 7 (abstraction reuse) and Step 8 (architecture-doc/diagram "
        "freshness) are judgement calls — your agent's post-push hook, or a "
        "manual `just review`, completes them. See "
        "docs/CODE_REVIEW_HOOK_SETUP.md.",
        flush=True,
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Shared code-review gate (see module docstring).")
    parser.add_argument(
        "--mode",
        required=True,
        choices=("cli", "codex-hook", "git-hook"),
        help="Which caller is invoking the gate.",
    )
    args = parser.parse_args(argv)
    if args.mode == "cli":
        return _mode_cli()
    if args.mode == "codex-hook":
        return _mode_codex_hook()
    return _mode_git_hook()


if __name__ == "__main__":
    raise SystemExit(main())
