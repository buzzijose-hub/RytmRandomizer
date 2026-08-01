"""Capture byte-exact goldens for zero-argument passive CLI report commands.

WHAT
====

Enumerates every passive CLI subcommand reachable through
``python -m rytm_randomizer.cli`` — the eagerly-registered
``cli_registry`` commands, the lazy-import manifest in
``rytm_randomizer/cli.py`` (``lazy_commands``), and the grandfathered
inline ``if args == [...]`` arms in ``cli.py:main`` — then runs each one
with ZERO arguments in a subprocess:

* exit 0 → stdout saved byte-for-byte to
  ``tests/fixtures/report_goldens/<cmd>.txt``; the ``--json`` variant is
  also tried and, when it exits 0, saved to ``<cmd>.json.txt``.
* non-zero exit / timeout → recorded in
  ``tests/fixtures/report_goldens/_skipped.json`` as
  ``{command: reason}`` so the meta-test in
  ``tests/test_report_command_goldens.py`` can prove no command dodged
  the net.
* nondeterministic output (two back-to-back runs differ) → NOT golden'd;
  recorded in ``_skipped.json`` with reason ``"nondeterministic"``.
  Normalization is deliberately not allowed — goldens stay byte-exact.

WHY
===

These goldens are the byte-verification net for the ReportSpec / CLI
refactors: any refactor that changes a single output byte of any passive
report command fails ``tests/test_report_command_goldens.py``.

This is NOT the V1.34 parity mechanism. The V1.34 goldens live under
``tests/fixtures/v134_parity/`` and are regenerated only under
``PARITY_CAPTURE_MODE=1`` with explicit approval — see
``.claude/rules/parity-fixture-discipline.md``. This capture script
mirrors that discipline with its own flag:

USAGE
=====

::

    RYTM_REPORT_GOLDEN_CAPTURE=1 .venv/bin/python scripts/capture_report_goldens.py

Without ``RYTM_REPORT_GOLDEN_CAPTURE=1`` the script refuses to run, so a
stray invocation cannot silently absorb an output regression into the
goldens.

The CLI under capture is passive by architecture (``cli.py`` cannot
import ``mido`` — see ``.claude/rules/architecture.md`` rule 7), so
running every command opens no MIDI port and touches no hardware.
"""

from __future__ import annotations

import ast
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Final

REPO_ROOT: Final[Path] = Path(__file__).resolve().parents[1]
CLI_SOURCE: Final[Path] = REPO_ROOT / "rytm_randomizer" / "cli.py"
GOLDEN_DIR: Final[Path] = REPO_ROOT / "tests" / "fixtures" / "report_goldens"
SKIPPED_FILENAME: Final[str] = "_skipped.json"
CAPTURE_ENV_FLAG: Final[str] = "RYTM_REPORT_GOLDEN_CAPTURE"
COMMAND_TIMEOUT_SECONDS: Final[int] = 60
_STDERR_REASON_LIMIT: Final[int] = 200

# Inline-arm shapes in ``cli.py:main`` — same patterns as
# ``tests/architecture/test_cli_no_inline_arms.py`` so the enumeration
# stays in lockstep with the inline-arm ratchet.
_INLINE_ARM_PATTERNS: Final[tuple[re.Pattern[str], ...]] = (
    re.compile(r'^    if args == \["([a-z][a-z0-9-]*)"', re.MULTILINE),
    re.compile(r'^    if len\(args\) == 2 and args\[0\] == "([a-z][a-z0-9-]*)"', re.MULTILINE),
    re.compile(r'^    if args and args\[0\] == "([a-z][a-z0-9-]*)"', re.MULTILINE),
)


@dataclass(frozen=True)
class CliRunResult:
    """Outcome of one passive-CLI subprocess invocation."""

    returncode: int
    stdout: bytes
    stderr: bytes
    timed_out: bool


def parse_lazy_command_names() -> tuple[str, ...]:
    """Return every key of the ``lazy_commands`` dict in ``cli.py``.

    AST-based (same proven approach as
    ``tests/test_real_midi_passive_cli_safety.py``) so enumeration never
    imports any report module — a pure read of the manifest.
    """

    tree = ast.parse(CLI_SOURCE.read_text(encoding="utf-8"))
    names: list[str] = []
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Assign)
            and len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name)
            and node.targets[0].id == "lazy_commands"
            and isinstance(node.value, ast.Dict)
        ):
            for key_node in node.value.keys:
                if isinstance(key_node, ast.Constant) and isinstance(key_node.value, str):
                    names.append(key_node.value)
    if not names:
        raise RuntimeError(
            "Could not locate the 'lazy_commands' dict in "
            "rytm_randomizer/cli.py. The parser expects an assignment of "
            "the form `lazy_commands = {...}` with string-literal keys."
        )
    return tuple(sorted(set(names)))


def parse_inline_arm_names() -> tuple[str, ...]:
    """Return the subcommand tokens dispatched by inline arms in ``cli.py:main``."""

    source = CLI_SOURCE.read_text(encoding="utf-8")
    tokens: set[str] = set()
    for pattern in _INLINE_ARM_PATTERNS:
        tokens.update(pattern.findall(source))
    return tuple(sorted(tokens))


def eager_command_names() -> tuple[str, ...]:
    """Return command names eagerly registered after importing ``rytm_randomizer.cli``.

    Runs in a fresh subprocess so the result never depends on which
    report modules the current process happens to have imported already.
    """

    code = (
        "import rytm_randomizer.cli\n"
        "from rytm_randomizer import cli_registry\n"
        "print('\\n'.join(sorted(cli_registry.all_commands())))\n"
    )
    proc = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
        timeout=COMMAND_TIMEOUT_SECONDS,
        cwd=REPO_ROOT,
        check=True,
    )
    return tuple(sorted(line for line in proc.stdout.splitlines() if line))


def enumerate_report_commands() -> tuple[str, ...]:
    """Return the full deterministic passive-CLI subcommand enumeration."""

    names = set(parse_lazy_command_names())
    names.update(parse_inline_arm_names())
    names.update(eager_command_names())
    return tuple(sorted(names))


def run_cli_command(args: tuple[str, ...]) -> CliRunResult:
    """Run ``python -m rytm_randomizer.cli <args>`` and capture raw bytes."""

    try:
        proc = subprocess.run(
            [sys.executable, "-m", "rytm_randomizer.cli", *args],
            capture_output=True,
            timeout=COMMAND_TIMEOUT_SECONDS,
            cwd=REPO_ROOT,
        )
    except subprocess.TimeoutExpired as exc:
        return CliRunResult(
            returncode=-1,
            stdout=exc.stdout or b"",
            stderr=exc.stderr or b"",
            timed_out=True,
        )
    return CliRunResult(
        returncode=proc.returncode,
        stdout=proc.stdout,
        stderr=proc.stderr,
        timed_out=False,
    )


def _skip_reason(result: CliRunResult) -> str:
    """Render a one-line skip reason from a failed invocation."""

    if result.timed_out:
        return f"timeout after {COMMAND_TIMEOUT_SECONDS}s"
    first_stderr_line = result.stderr.decode("utf-8", errors="replace").splitlines()
    detail = first_stderr_line[0] if first_stderr_line else ""
    if len(detail) > _STDERR_REASON_LIMIT:
        detail = detail[:_STDERR_REASON_LIMIT] + "..."
    return f"exit {result.returncode}: {detail}" if detail else f"exit {result.returncode}"


def _capture_variant(args: tuple[str, ...], golden_path: Path, skipped: dict[str, str]) -> bool:
    """Capture one invocation variant; return True when a golden was written.

    Runs the command twice back-to-back: if the two byte streams differ
    the command is nondeterministic and is recorded in ``skipped``
    instead of golden'd (normalization is not allowed — goldens must be
    byte-exact).
    """

    skip_key = " ".join(args)
    first = run_cli_command(args)
    if first.timed_out or first.returncode != 0:
        skipped[skip_key] = _skip_reason(first)
        return False
    second = run_cli_command(args)
    if second.timed_out or second.returncode != 0 or second.stdout != first.stdout:
        skipped[skip_key] = "nondeterministic"
        return False
    golden_path.write_bytes(first.stdout)
    return True


def capture_all() -> tuple[int, int, dict[str, str]]:
    """Capture every enumerable command; return (text_count, json_count, skipped)."""

    GOLDEN_DIR.mkdir(parents=True, exist_ok=True)
    for stale in GOLDEN_DIR.glob("*.txt"):
        stale.unlink()
    stale_skipped = GOLDEN_DIR / SKIPPED_FILENAME
    if stale_skipped.exists():
        stale_skipped.unlink()

    skipped: dict[str, str] = {}
    text_count = 0
    json_count = 0
    for command in enumerate_report_commands():
        wrote_text = _capture_variant((command,), GOLDEN_DIR / f"{command}.txt", skipped)
        if wrote_text:
            text_count += 1
            if _capture_variant((command, "--json"), GOLDEN_DIR / f"{command}.json.txt", skipped):
                json_count += 1

    (GOLDEN_DIR / SKIPPED_FILENAME).write_text(
        json.dumps(skipped, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return text_count, json_count, skipped


def main() -> int:
    """Guarded entry point — refuses to run without the capture flag."""

    if os.environ.get(CAPTURE_ENV_FLAG) != "1":
        sys.stderr.write(
            f"Refusing to capture: set {CAPTURE_ENV_FLAG}=1 to regenerate the "
            "report goldens under tests/fixtures/report_goldens/. This guard "
            "mirrors the V1.34 parity-capture discipline so a stray run "
            "cannot silently absorb an output regression.\n"
        )
        return 2

    text_count, json_count, skipped = capture_all()
    nondeterministic = sorted(k for k, v in skipped.items() if v == "nondeterministic")
    sys.stdout.write(
        f"Captured {text_count} text goldens and {json_count} json goldens "
        f"into {GOLDEN_DIR.relative_to(REPO_ROOT)}.\n"
        f"Skipped {len(skipped)} invocations (see {SKIPPED_FILENAME}).\n"
    )
    if nondeterministic:
        sys.stdout.write("Nondeterministic commands:\n")
        for name in nondeterministic:
            sys.stdout.write(f"  - {name}\n")
    else:
        sys.stdout.write("Nondeterministic commands: none.\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
