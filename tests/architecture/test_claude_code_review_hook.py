"""Claude Code post-push code-review hook wiring.

Guards the two halves of the Claude Code review mechanism that was wired up
alongside the settings parse-error fix:

1. ``.claude/settings.json`` declares a SCHEMA-VALID ``PostToolUse`` hook —
   a STRING ``matcher`` plus a nested ``hooks`` array of ``type: command``
   entries — that invokes ``scripts/code_review_gate.py --mode claude-hook``.
   The string-matcher assertion is a regression guard for the original
   "settings file failed to parse / expected string, received object" error:
   a matcher OBJECT must never come back.
2. ``--mode claude-hook`` no-ops on anything that is not a ``git push`` and
   emits the expected hook JSON on a push (``additionalContext`` on pass,
   ``decision: block`` on gate failure).
"""

from __future__ import annotations

import importlib.util
import io
import json
import subprocess
import sys
from pathlib import Path
from types import ModuleType
from typing import Final

import pytest

pytestmark = pytest.mark.fast

_REPO_ROOT: Final[Path] = Path(__file__).resolve().parents[2]
_SETTINGS: Final[Path] = _REPO_ROOT / ".claude" / "settings.json"
_GATE: Final[Path] = _REPO_ROOT / "scripts" / "code_review_gate.py"


def _load_gate_module() -> ModuleType:
    spec = importlib.util.spec_from_file_location("code_review_gate", _GATE)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _run_gate_subprocess(payload: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(_GATE), "--mode", "claude-hook"],
        input=payload,
        capture_output=True,
        text=True,
        cwd=_REPO_ROOT,
    )


def test_claude_settings_hook_is_schema_valid() -> None:
    data = json.loads(_SETTINGS.read_text(encoding="utf-8"))
    post = data["hooks"]["PostToolUse"]
    assert isinstance(post, list) and post, "PostToolUse must be a non-empty list"

    commands: list[str] = []
    for entry in post:
        assert isinstance(entry["matcher"], str), (
            "hook `matcher` must be a STRING, not an object — a matcher object "
            "fails Claude Code settings validation ('expected string, received "
            "object'); see the original parse-error fix."
        )
        assert isinstance(entry["hooks"], list) and entry["hooks"]
        for hook in entry["hooks"]:
            assert hook["type"] == "command"
            assert isinstance(hook["command"], str)
            commands.append(hook["command"])

    assert any("--mode claude-hook" in command for command in commands), (
        "expected a PostToolUse command hook invoking "
        "scripts/code_review_gate.py --mode claude-hook"
    )


def test_claude_hook_noops_on_non_git_push() -> None:
    proc = _run_gate_subprocess(
        json.dumps({"tool_name": "Bash", "tool_input": {"command": "ls -la"}})
    )
    assert proc.returncode == 0
    assert proc.stdout.strip() == "", "non-`git push` calls must emit no hook output"


def test_claude_hook_ignores_non_shell_tool() -> None:
    proc = _run_gate_subprocess(json.dumps({"tool_name": "Read", "tool_input": {"file_path": "x"}}))
    assert proc.returncode == 0
    assert proc.stdout.strip() == ""


def test_claude_hook_emits_additional_context_on_pass(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    gate = _load_gate_module()
    monkeypatch.setattr(gate, "run_mechanical_gates", lambda *, quiet: (True, []))
    monkeypatch.setattr(
        gate.sys,
        "stdin",
        io.StringIO(
            json.dumps({"tool_name": "Bash", "tool_input": {"command": "git push origin HEAD"}})
        ),
    )

    assert gate._mode_claude_hook() == 0
    response = json.loads(capsys.readouterr().out)
    assert response["hookSpecificOutput"]["hookEventName"] == "PostToolUse"
    assert "code-review" in response["hookSpecificOutput"]["additionalContext"]
    assert "decision" not in response


def test_claude_hook_blocks_on_gate_failure(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    gate = _load_gate_module()
    monkeypatch.setattr(gate, "run_mechanical_gates", lambda *, quiet: (False, ["Lint: ruff"]))
    monkeypatch.setattr(
        gate.sys,
        "stdin",
        io.StringIO(json.dumps({"tool_name": "Bash", "tool_input": {"command": "git push"}})),
    )

    assert gate._mode_claude_hook() == 0
    response = json.loads(capsys.readouterr().out)
    assert response["decision"] == "block"
    assert "Lint: ruff" in response["reason"]
