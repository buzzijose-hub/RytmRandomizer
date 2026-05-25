"""Architecture invariants pinning the cockpit send-plan rehearsal-surface contract.

The PR #104 review surfaced a missing architecture file: the rehearsal
surface (``rytm_randomizer/reports/cockpit_send_plan_rehearsal_surface.py``)
is the passive blueprint that Phase 3's export-rehearsal report is modeled
on. Without this guard, a future PR can:

* drop the module name and re-spell the contract,
* silently delete the safety lines that document the report's passive
  posture,
* rename the CLI subcommand string (breaking every operator runbook
  that pins the name),
* let a forbidden import (``mido``, ``cockpit.ws.server``, ``socket``,
  ``subprocess``, ``threading``, ``asyncio``) creep into the module and
  void its passive-only guarantee.

Each test in this module exists to make exactly one of those breakage
classes a loud test failure instead of a silent runbook regression.

These tests are intentionally tolerant of attribute renames within the
module (we read text and grep for the safety phrases) so a contributor
refactoring an internal helper does not have to re-write the test — only
the externally-observable surface (module path, version constant, safety
phrases, CLI name, forbidden-import set) is pinned.

Every test is fast (file IO + import / regex / text scan only).
"""

from __future__ import annotations

from pathlib import Path
from typing import Final

import pytest

pytestmark = pytest.mark.fast

PROJECT_ROOT: Final[Path] = Path(__file__).resolve().parents[2]
REPORTS_ROOT: Final[Path] = PROJECT_ROOT / "rytm_randomizer" / "reports"
REHEARSAL_SURFACE_PATH: Final[Path] = REPORTS_ROOT / "cockpit_send_plan_rehearsal_surface.py"
EXPECTED_CLI_COMMAND_NAME: Final[str] = "cockpit-send-plan-rehearsal-surface-report"


# ---------------------------------------------------------------------------
# Module location
# ---------------------------------------------------------------------------


def test_rehearsal_surface_module_under_reports_dir() -> None:
    """The rehearsal-surface module must live at the documented import path.

    Regression guard: the PR #104 review's blueprint pins the rehearsal
    surface to ``rytm_randomizer/reports/cockpit_send_plan_rehearsal_surface.py``.
    Moving it elsewhere (``cockpit/``, ``profiles/``, etc.) breaks the
    discoverability the operator runbook depends on; the lazy-command
    table in ``cli.py`` also pins this import path. This test pins the
    location so a rename triggers a clear failure rather than a quiet
    re-implementation in a sibling subpackage.
    """

    assert REHEARSAL_SURFACE_PATH.is_file(), (
        "rytm_randomizer/reports/cockpit_send_plan_rehearsal_surface.py "
        "must exist. PR #104 surfaced this gap; the rehearsal-surface "
        "module is the passive blueprint Phase 3's export-rehearsal "
        f"report is modeled on. Got: {REHEARSAL_SURFACE_PATH} does not exist."
    )


# ---------------------------------------------------------------------------
# Version constant
# ---------------------------------------------------------------------------


def test_rehearsal_surface_exports_version_constant() -> None:
    """The module must expose a ``SEND_PLAN_REHEARSAL_SURFACE_VERSION`` constant.

    Regression guard: every passive report module in the codebase carries
    a ``<NAME>_VERSION`` constant so the operator runbook and downstream
    artifact-comparison tools can pin a version string. Dropping the
    constant (or renaming it) breaks every consumer that records the
    version in a report-id or in an audit log. This test pins the name
    and that it carries a non-empty value.
    """

    if not REHEARSAL_SURFACE_PATH.is_file():
        pytest.fail(
            "Cannot check SEND_PLAN_REHEARSAL_SURFACE_VERSION: module "
            f"{REHEARSAL_SURFACE_PATH} does not exist yet. See "
            "test_rehearsal_surface_module_under_reports_dir."
        )

    from rytm_randomizer.reports import cockpit_send_plan_rehearsal_surface as module

    assert hasattr(module, "SEND_PLAN_REHEARSAL_SURFACE_VERSION"), (
        "rytm_randomizer/reports/cockpit_send_plan_rehearsal_surface.py "
        "must expose SEND_PLAN_REHEARSAL_SURFACE_VERSION; every passive "
        "report carries a version constant for runbook / audit pinning."
    )
    version = module.SEND_PLAN_REHEARSAL_SURFACE_VERSION
    # The peer module (``cockpit_send_plan_operator_readiness``) uses a
    # version *string* like ``"cockpit-send-plan-operator-readiness-v1"``.
    # We accept either ``int >= 1`` or a non-empty ``str`` (so the
    # contract is "there is a meaningful version marker") — refactors
    # that switch the literal form are not regressions.
    if isinstance(version, int):
        assert (
            version >= 1
        ), f"SEND_PLAN_REHEARSAL_SURFACE_VERSION as int must be >= 1; got {version}"
    else:
        assert isinstance(version, str), (
            "SEND_PLAN_REHEARSAL_SURFACE_VERSION must be int or non-empty str; "
            f"got {type(version).__name__}"
        )
        assert version.strip(), "SEND_PLAN_REHEARSAL_SURFACE_VERSION must be a non-empty string"


# ---------------------------------------------------------------------------
# Safety lines
# ---------------------------------------------------------------------------


def test_rehearsal_surface_safety_lines_claim_passive() -> None:
    """The module source must document its passive / no-MIDI-send posture.

    Regression guard: every passive report module in this codebase
    embeds a ``SAFETY_LINES`` (or equivalent) tuple containing phrases
    like ``"no MIDI sending"`` and ``"passive"``. These phrases are how
    operators (and the JSON consumers of these reports) recognize the
    report is safe to run unattended. A refactor that removes the
    phrases — even if the underlying code stays passive — strips a
    contract operators rely on. This test grep-scans the module text
    so attribute renames (``SAFETY_LINES`` -> ``_SAFETY_LINES``) do
    not falsely regress.
    """

    if not REHEARSAL_SURFACE_PATH.is_file():
        pytest.fail(
            "Cannot check safety lines: module "
            f"{REHEARSAL_SURFACE_PATH} does not exist yet. See "
            "test_rehearsal_surface_module_under_reports_dir."
        )

    source = REHEARSAL_SURFACE_PATH.read_text(encoding="utf-8")
    assert "no MIDI sending" in source, (
        "cockpit_send_plan_rehearsal_surface.py must contain the literal "
        "phrase 'no MIDI sending' in its SAFETY_LINES (or equivalent). "
        "This phrase is the contract operators look for to confirm the "
        "report is safe to run unattended."
    )
    assert "passive" in source, (
        "cockpit_send_plan_rehearsal_surface.py must contain the word "
        "'passive' (typically in SAFETY_LINES like 'passive/read-only'); "
        "the phrase is the operator's quick-scan signal."
    )


# ---------------------------------------------------------------------------
# CLI command name
# ---------------------------------------------------------------------------


def test_rehearsal_surface_command_name_is_pinned() -> None:
    """The registered CLI subcommand must be exactly the documented name.

    Regression guard: operator runbooks and integration scripts call
    ``python -m rytm_randomizer.cli cockpit-send-plan-rehearsal-surface-report``.
    Renaming the registered subcommand silently breaks every external
    consumer; the rename is a contract bump that needs explicit
    acknowledgement, not a quiet refactor.
    """

    if not REHEARSAL_SURFACE_PATH.is_file():
        pytest.fail(
            "Cannot check CLI command name: module "
            f"{REHEARSAL_SURFACE_PATH} does not exist yet. See "
            "test_rehearsal_surface_module_under_reports_dir."
        )

    source = REHEARSAL_SURFACE_PATH.read_text(encoding="utf-8")
    assert EXPECTED_CLI_COMMAND_NAME in source, (
        "cockpit_send_plan_rehearsal_surface.py source must reference the "
        f"CLI subcommand name {EXPECTED_CLI_COMMAND_NAME!r} (typically as "
        "the ``name`` field of the registered ``CliCommand``). This is the "
        "name operator runbooks depend on."
    )

    # If the module is importable and registers a CliCommand, double-pin
    # by reading the registry entry.
    try:
        from rytm_randomizer import cli_registry
        from rytm_randomizer.reports import (  # noqa: F401  (import for side effect — registers the command)
            cockpit_send_plan_rehearsal_surface,
        )
    except ImportError as exc:
        pytest.fail(
            "Module exists on disk but cannot be imported: "
            f"{exc!r}. Check the module's top-level imports."
        )

    command = cli_registry.get(EXPECTED_CLI_COMMAND_NAME)
    assert command is not None, (
        f"CLI subcommand {EXPECTED_CLI_COMMAND_NAME!r} is not registered "
        "after importing rytm_randomizer.reports.cockpit_send_plan_rehearsal_surface. "
        "The module must call ``cli_registry.register(...)`` at import "
        "time (matches the pattern in cockpit_send_plan_operator_readiness.py)."
    )
    assert command.name == EXPECTED_CLI_COMMAND_NAME, (
        f"Registered CLI command name must be exactly {EXPECTED_CLI_COMMAND_NAME!r}; "
        f"got {command.name!r}."
    )


# ---------------------------------------------------------------------------
# Forbidden imports
# ---------------------------------------------------------------------------


def test_rehearsal_surface_has_no_forbidden_imports() -> None:
    """The module must not pull MIDI / IPC / concurrency modules into its source.

    Regression guard: the rehearsal surface is a passive report; it is
    contractually forbidden from importing ``mido``, ``rtmidi``,
    ``real_midi_adapter``, ``midi_io``, ``cockpit.ws.server``,
    ``socket``, ``subprocess``, ``threading``, or ``asyncio``. Any of
    these would either (a) drag in a hardware-MIDI dependency that
    breaks the passive-CLI sweep guarantee or (b) introduce a
    concurrency / IPC surface that the report's deterministic-text
    output contract cannot guarantee. This text-scan check catches the
    breakage at the source level — earlier than the runtime
    ``test_passive_cli_sweep_does_not_import_real_midi_or_adapter_modules``
    check, which fails only when the import path actually executes.
    """

    if not REHEARSAL_SURFACE_PATH.is_file():
        pytest.fail(
            "Cannot check forbidden imports: module "
            f"{REHEARSAL_SURFACE_PATH} does not exist yet. See "
            "test_rehearsal_surface_module_under_reports_dir."
        )

    source = REHEARSAL_SURFACE_PATH.read_text(encoding="utf-8")
    forbidden_substrings = (
        "import mido",
        "from mido",
        "import rtmidi",
        "from rtmidi",
        "import pythonrtmidi",
        "from pythonrtmidi",
        "rytm_randomizer.real_midi_adapter",
        "rytm_randomizer.midi_io",
        "rytm_randomizer.cockpit.ws",
        "import socket",
        "from socket",
        "import subprocess",
        "from subprocess",
        "import threading",
        "from threading",
        "import asyncio",
        "from asyncio",
    )
    violations = [needle for needle in forbidden_substrings if needle in source]
    assert not violations, (
        "cockpit_send_plan_rehearsal_surface.py must not import MIDI / IPC / "
        "concurrency modules. Forbidden imports found: "
        f"{violations}. The module is a passive report and is contractually "
        "barred from these dependencies."
    )
