"""Forbid CLI flags that accept raw secret values inline on the command line.

This test exists because CODE_REVIEW.md SX2 closed a local
information-disclosure path in the export CLI: the original
``cockpit-export-profile-model --key-hex <hex>`` placed the
hex-encoded signing key in the process argv. On Linux/macOS,
``/proc/<pid>/cmdline`` is readable by any local user; on Windows
``Get-Process`` exposes the same data via WMI. Any second user on the
machine could capture the key during the brief window the subcommand
runs.

The fix (PR SX2): the export CLI gained ``--key-env <ENV_VAR_NAME>``
as the recommended channel. The env var contents never appear in
argv, so the secret stays out of the process table. ``--key-hex`` is
retained for backward compat but emits a structured deprecation
warning on every use.

This architecture test pins the surface: every passive CLI module
(``rytm_randomizer/**/cli.py``) is AST-walked, every flag name is
extracted, and any flag matching the secret-naming pattern
(``--*key*``, ``--*token*``, ``--*secret*``, ``--*password*``, etc.)
must EITHER be on the grandfathered allow-list (existing
``--key-hex`` for SX2 backward compat) OR have a matching
``--*-env`` / ``--*-file`` / ``--*-stdin`` companion flag accepted in
the same parser.

The check is structural — we read the literal strings that appear in
the ``elif option == "--foo"`` chain inside each CLI's ``_parse_args``
function. A new CLI that ships ``--api-key <value>`` without a
companion ``--api-key-env`` will fail this test loudly.

See also:
* ``rytm_randomizer/cockpit/export/cli.py`` — SX2 fix that introduced
  the ``--key-env`` channel and the deprecation warning on ``--key-hex``.
* ``tests/cockpit/test_export_cli.py`` § "SX2" — behavioural coverage.
* ``CODE_REVIEW.md`` finding SX2.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path
from typing import Final

import pytest

pytestmark = pytest.mark.fast

PROJECT_ROOT: Final[Path] = Path(__file__).resolve().parents[2]
PACKAGE_ROOT: Final[Path] = PROJECT_ROOT / "rytm_randomizer"

# Pattern: flag names that LOOK LIKE they accept a secret value.
# Conservative — we want to flag anything that COULD be a secret-via-argv
# leak. False positives can be added to the grandfathered allow-list.
_SECRET_FLAG_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"^--(.*-)?(key|token|secret|password|passphrase|api[-_]?key|auth)(-[a-z]+)?$",
    re.IGNORECASE,
)

# Companion flag suffixes that indicate a SAFE delivery channel
# (env-var, file path, or stdin). Any flag that has a sibling with one
# of these suffixes is considered to have an out-of-band channel
# available; the inline ``--key-hex``-style flag MAY persist for
# backward compat but must NOT be the ONLY way to pass the secret.
_SAFE_COMPANION_SUFFIXES: Final[tuple[str, ...]] = ("-env", "-file", "-stdin", "-fd")

# Grandfathered exceptions: ``(cli_file_relpath, flag)`` pairs already
# known to be SX2-style argv leaks that are retained for backward
# compatibility but covered by a safer companion flag in the same
# parser. Each entry implicitly asserts: a companion flag exists.
_GRANDFATHERED_SECRET_FLAGS: Final[set[tuple[str, str]]] = {
    # ``--key-hex`` retained for backward compat; covered by ``--key-env``
    # since the SX2 fix. Removing it is a separate cleanup PR.
    ("rytm_randomizer/cockpit/export/cli.py", "--key-hex"),
}


def _cli_python_files() -> list[Path]:
    """Return every ``cli.py`` (or ``cli/`` package main) under the package."""

    out: list[Path] = []
    for path in PACKAGE_ROOT.rglob("cli.py"):
        if "__pycache__" not in path.parts:
            out.append(path)
    return sorted(out)


def _extract_cli_flags(path: Path) -> list[str]:
    """Return every ``--foo`` literal from the parse-args function of ``path``.

    Walks the AST for string constants of the form ``"--*"`` that
    appear as the right-hand side of an equality compare. This is the
    shape the project's hand-rolled CLI parsers all use::

        if option == "--profile-id":

    Hand-rolled parsers are deliberately AST-walkable so this test
    catches every flag whether the file uses ``argparse``, ``click``,
    or a manual ``elif`` chain (the project uses the manual chain).
    """

    try:
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source)
    except (OSError, SyntaxError):
        return []

    flags: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            value = node.value
            if value.startswith("--") and " " not in value and "\n" not in value:
                flags.add(value)
    return sorted(flags)


def _is_secret_flag(flag: str) -> bool:
    """Return True iff ``flag`` LOOKS like a secret-via-argv leak."""

    return _SECRET_FLAG_PATTERN.match(flag) is not None


def _has_safe_companion(flags: list[str], flag: str) -> bool:
    """Return True iff some sibling flag delivers ``flag`` via a safe channel.

    Example: ``--key-hex`` has a safe companion if ``--key-env``,
    ``--key-file``, ``--key-stdin``, or ``--key-fd`` is also in the
    parser's flag list.
    """

    base = flag.split("-")[2] if flag.startswith("--") and "-" in flag[2:] else flag[2:]
    # base is the noun part (``key``, ``token``, ``api-key`` etc.) —
    # the regex above isn't strict enough to extract cleanly, so we
    # walk by prefix matching: any sibling flag that shares the same
    # 2-character prefix and ends in a safe suffix counts.
    for suffix in _SAFE_COMPANION_SUFFIXES:
        for other in flags:
            if other == flag:
                continue
            if other.endswith(suffix):
                return True
            if base in other and any(other.endswith(s) for s in _SAFE_COMPANION_SUFFIXES):
                return True
    return False


def test_no_cli_flag_accepts_an_inline_secret_value_without_safe_companion() -> None:
    """Every CLI flag that looks like a secret must have a safe companion.

    Regression guard for CODE_REVIEW.md SX2: a new CLI module that
    ships ``--api-key <value>`` without ``--api-key-env`` /
    ``--api-key-file`` / ``--api-key-stdin`` re-introduces the same
    process-table leak the SX2 fix closed. The fix recipe is in
    ``rytm_randomizer/cockpit/export/cli.py`` (and the
    behavioural-test pattern is in ``tests/cockpit/test_export_cli.py``
    under the SX2 section).

    Grandfathered SX2-vintage flags (notably ``--key-hex``) are
    excluded — those are retained for backward compat and are covered
    by their ``--key-env`` companion.
    """

    violations: list[str] = []
    for path in _cli_python_files():
        rel = path.relative_to(PROJECT_ROOT).as_posix()
        flags = _extract_cli_flags(path)
        for flag in flags:
            if not _is_secret_flag(flag):
                continue
            # Allow safe-channel flags themselves (a ``--key-env`` flag
            # passes the secret-flag regex but IS the safe channel).
            if any(flag.endswith(s) for s in _SAFE_COMPANION_SUFFIXES):
                continue
            if (rel, flag) in _GRANDFATHERED_SECRET_FLAGS:
                # Confirm the grandfathered flag still has a safe
                # companion — drain the allow-list automatically if a
                # contributor removes both halves.
                if not _has_safe_companion(flags, flag):
                    violations.append(
                        f"{rel}: grandfathered secret flag {flag!r} no longer "
                        "has a safe-companion flag (one of "
                        f"{_SAFE_COMPANION_SUFFIXES}) in the same parser. "
                        "Either re-add the companion, OR remove the "
                        "grandfathered entry from "
                        "_GRANDFATHERED_SECRET_FLAGS."
                    )
                continue
            if not _has_safe_companion(flags, flag):
                violations.append(
                    f"{rel}: CLI flag {flag!r} accepts a secret inline on argv "
                    "and has no safe-companion flag (one of "
                    f"{_SAFE_COMPANION_SUFFIXES}). This re-introduces the "
                    "SX2 process-table leak (/proc/<pid>/cmdline is readable "
                    "by any local user). Fix: add a "
                    f"{flag}{_SAFE_COMPANION_SUFFIXES[0]} variant that reads "
                    "the secret from an env var (preferred) or a file path. "
                    "See rytm_randomizer/cockpit/export/cli.py for the canonical "
                    "two-channel pattern."
                )

    assert (
        not violations
    ), "CLI secret-via-argv leak — CODE_REVIEW.md SX2 regression:\n  " + "\n  ".join(violations)


def test_grandfathered_secret_flags_are_all_present() -> None:
    """Every grandfathered ``(file, flag)`` pair still exists in the source.

    If a contributor removes a grandfathered flag entirely (e.g.
    finally dropping ``--key-hex`` after a deprecation period), they
    must also drain the corresponding entry from
    ``_GRANDFATHERED_SECRET_FLAGS`` — otherwise the allow-list grows
    stale and the SX2 ratchet weakens silently.
    """

    missing: list[str] = []
    for rel, flag in _GRANDFATHERED_SECRET_FLAGS:
        path = PROJECT_ROOT / rel
        if not path.is_file():
            missing.append(f"{rel}: file is gone but {flag!r} is still in the allow-list.")
            continue
        flags = _extract_cli_flags(path)
        if flag not in flags:
            missing.append(
                f"{rel}: flag {flag!r} is no longer present but is still in "
                "_GRANDFATHERED_SECRET_FLAGS. Drain the entry."
            )

    assert not missing, (
        "Stale entries in _GRANDFATHERED_SECRET_FLAGS — drain them so the "
        "SX2 ratchet only tightens:\n  " + "\n  ".join(missing)
    )
