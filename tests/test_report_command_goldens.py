"""Byte-exact golden tests for zero-argument passive CLI report commands.

Every golden under ``tests/fixtures/report_goldens/`` is the frozen
stdout of one ``python -m rytm_randomizer.cli <cmd>`` invocation (the
``<cmd>.json.txt`` variants add ``--json``). Each test here re-runs the
command in a subprocess and asserts stdout matches the golden
byte-for-byte, making the ReportSpec / CLI-dispatcher refactors
byte-verifiable: any refactor that changes a single output byte of any
passive report command fails this module.

A meta-test additionally asserts that EVERY enumerable passive
subcommand (the ``lazy_commands`` manifest in ``rytm_randomizer/cli.py``,
the eagerly-registered ``cli_registry`` commands, and the grandfathered
inline arms in ``cli.py:main``) has either a golden or an entry in
``_skipped.json`` — so a newly added command cannot silently dodge the
net.

REGENERATION
============

Goldens are regenerated ONLY via the guarded capture script::

    RYTM_REPORT_GOLDEN_CAPTURE=1 .venv/bin/python scripts/capture_report_goldens.py

The environment flag mirrors the parity-capture discipline: without it
the script refuses to run, so a stray invocation cannot silently absorb
an output regression into the goldens. Commands whose output is
nondeterministic are never golden'd (no normalization allowed); they are
recorded in ``_skipped.json`` with reason ``"nondeterministic"``.

This is NOT the V1.34 parity mechanism. The V1.34 goldens live under
``tests/fixtures/v134_parity/`` with their own ``PARITY_CAPTURE_MODE=1``
discipline (see ``.claude/rules/parity-fixture-discipline.md``); this
module covers the passive report CLI surface only.

This module is deliberately NOT marked ``pytest.mark.fast`` — every case
spawns a fresh interpreter subprocess.
"""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path
from types import ModuleType
from typing import Final

import pytest

# Subprocess-heavy but xdist-parallel (~3s wall); carries the fast marker per
# the repo-wide rule in tests/architecture/test_fast_marker_coverage.py (only
# the six V1.34 parity files are exempt).
pytestmark = pytest.mark.fast

PROJECT_ROOT: Final[Path] = Path(__file__).resolve().parents[1]
GOLDEN_DIR: Final[Path] = PROJECT_ROOT / "tests" / "fixtures" / "report_goldens"
SKIPPED_PATH: Final[Path] = GOLDEN_DIR / "_skipped.json"
CAPTURE_SCRIPT: Final[Path] = PROJECT_ROOT / "scripts" / "capture_report_goldens.py"

_JSON_GOLDEN_SUFFIX: Final[str] = ".json.txt"
_TEXT_GOLDEN_SUFFIX: Final[str] = ".txt"


def _load_capture_module() -> ModuleType:
    """Load the capture script as a module (it lives outside the package).

    Importing is side-effect-free: the script only captures when its
    ``main()`` runs under ``RYTM_REPORT_GOLDEN_CAPTURE=1``. Sharing the
    script's enumeration helpers keeps the meta-test's notion of "every
    enumerable command" in lockstep with what the capture actually
    captured.
    """

    module_name = "capture_report_goldens_under_test"
    spec = importlib.util.spec_from_file_location(module_name, CAPTURE_SCRIPT)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    # Register before exec: the script's frozen dataclass resolves its
    # annotations through ``sys.modules[cls.__module__]`` at class-build
    # time, which is None for an unregistered module.
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


_CAPTURE: Final[ModuleType] = _load_capture_module()

GOLDEN_NAMES: Final[tuple[str, ...]] = tuple(
    sorted(path.name for path in GOLDEN_DIR.glob(f"*{_TEXT_GOLDEN_SUFFIX}"))
)


def _cli_args_for_golden(golden_name: str) -> tuple[str, ...]:
    """Map a golden filename back to the CLI argv tail that produced it."""

    if golden_name.endswith(_JSON_GOLDEN_SUFFIX):
        return (golden_name[: -len(_JSON_GOLDEN_SUFFIX)], "--json")
    return (golden_name[: -len(_TEXT_GOLDEN_SUFFIX)],)


def test_golden_directory_is_populated() -> None:
    """The golden net must exist and be non-trivially populated.

    Guards against a checkout / refactor that silently drops the fixture
    directory — an empty glob would otherwise skip every parametrized
    case below without failing anything.
    """

    assert GOLDEN_DIR.is_dir(), (
        f"{GOLDEN_DIR} is missing. Regenerate with "
        "RYTM_REPORT_GOLDEN_CAPTURE=1 .venv/bin/python scripts/capture_report_goldens.py"
    )
    assert GOLDEN_NAMES, "No report goldens found — the byte-verification net is empty."
    assert SKIPPED_PATH.is_file(), f"{SKIPPED_PATH} is missing — capture was incomplete."


@pytest.mark.parametrize("golden_name", GOLDEN_NAMES)
def test_report_command_output_matches_golden(golden_name: str) -> None:
    """Re-run the command and compare stdout to the golden byte-for-byte."""

    args = _cli_args_for_golden(golden_name)
    proc = subprocess.run(
        [sys.executable, "-m", "rytm_randomizer.cli", *args],
        capture_output=True,
        timeout=120,
        cwd=PROJECT_ROOT,
    )
    assert proc.returncode == 0, (
        f"`python -m rytm_randomizer.cli {' '.join(args)}` exited "
        f"{proc.returncode}; stderr:\n{proc.stderr.decode('utf-8', errors='replace')}"
    )
    golden = (GOLDEN_DIR / golden_name).read_bytes()
    assert proc.stdout == golden, (
        f"stdout of `python -m rytm_randomizer.cli {' '.join(args)}` no longer "
        f"matches {golden_name} byte-for-byte. If this output change is "
        "intentional, regenerate the goldens with RYTM_REPORT_GOLDEN_CAPTURE=1 "
        ".venv/bin/python scripts/capture_report_goldens.py and commit the "
        "diff for review."
    )


def test_every_enumerable_command_is_goldened_or_skipped() -> None:
    """No passive subcommand may dodge the golden net.

    Every command enumerable from the lazy manifest, the eager registry,
    and the inline arms must have either a ``<cmd>.txt`` golden or a
    ``_skipped.json`` entry recorded by the capture script. A new command
    that has neither fails here until the goldens are regenerated.
    """

    skipped: dict[str, str] = json.loads(SKIPPED_PATH.read_text(encoding="utf-8"))
    golden_names = set(GOLDEN_NAMES)
    missing = [
        command
        for command in _CAPTURE.enumerate_report_commands()
        if f"{command}{_TEXT_GOLDEN_SUFFIX}" not in golden_names and command not in skipped
    ]
    assert not missing, (
        "These passive CLI commands have neither a golden under "
        "tests/fixtures/report_goldens/ nor a _skipped.json entry:\n  "
        + "\n  ".join(sorted(missing))
        + "\nRegenerate the goldens with RYTM_REPORT_GOLDEN_CAPTURE=1 "
        ".venv/bin/python scripts/capture_report_goldens.py"
    )


def test_skipped_entries_reference_enumerable_commands() -> None:
    """``_skipped.json`` keys must map back to enumerable commands.

    Each key is either ``<cmd>`` or ``<cmd> --json``; a key whose base
    command is no longer enumerable is stale and means the goldens need
    regeneration (a command was removed or renamed).
    """

    skipped: dict[str, str] = json.loads(SKIPPED_PATH.read_text(encoding="utf-8"))
    enumerable = set(_CAPTURE.enumerate_report_commands())
    stale = [key for key in skipped if key.split(" ")[0] not in enumerable]
    assert not stale, (
        "Stale _skipped.json entries (base command no longer enumerable):\n  "
        + "\n  ".join(sorted(stale))
        + "\nRegenerate the goldens with RYTM_REPORT_GOLDEN_CAPTURE=1 "
        ".venv/bin/python scripts/capture_report_goldens.py"
    )
