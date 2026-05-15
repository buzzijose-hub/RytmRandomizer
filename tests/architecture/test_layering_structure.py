"""Enforce the expected package layout from ``docs/ARCHITECTURE.md``.

These tests assert that the modules listed in the architecture spec actually
exist (so a future refactor cannot quietly delete them) and that the V1.34
monolith is the frozen byte-reference at the repository root (not a thin
shim inside the package).
"""

from __future__ import annotations

import hashlib
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PACKAGE_ROOT = PROJECT_ROOT / "rytm_randomizer"
MONOLITH_PATH = PROJECT_ROOT / "rytm_hybrid_randomizer_v134.py"


# Modules that MUST exist for the architecture to be intact.
_REQUIRED_PACKAGE_MODULES: tuple[str, ...] = (
    "rytm_randomizer/__init__.py",
    "rytm_randomizer/app.py",
    "rytm_randomizer/cli.py",
    "rytm_randomizer/shell.py",
    "rytm_randomizer/midi_io.py",
    "rytm_randomizer/randomization.py",
    "rytm_randomizer/mock_midi.py",
    "rytm_randomizer/real_midi_adapter.py",
    "rytm_randomizer/mido_provider.py",
    "rytm_randomizer/scene_runner.py",
    "rytm_randomizer/group_runner.py",
    "rytm_randomizer/reports.py",
    "rytm_randomizer/inspection.py",
    # data/ sub-package
    "rytm_randomizer/data/__init__.py",
    "rytm_randomizer/data/param_maps.py",
    "rytm_randomizer/data/plans.py",
    "rytm_randomizer/data/profiles.py",
    "rytm_randomizer/data/scenes.py",
    # state/ sub-package
    "rytm_randomizer/state/__init__.py",
    "rytm_randomizer/state/anchor.py",
    "rytm_randomizer/state/group.py",
    "rytm_randomizer/state/pad_mode.py",
    "rytm_randomizer/state/scene.py",
    "rytm_randomizer/state/selection.py",
    # engines/ sub-package
    "rytm_randomizer/engines/__init__.py",
    "rytm_randomizer/engines/pad1.py",
    "rytm_randomizer/engines/pad2.py",
    "rytm_randomizer/engines/pad3.py",
    "rytm_randomizer/engines/pad4.py",
)


# ---------------------------------------------------------------------------
# Required modules exist
# ---------------------------------------------------------------------------


def test_required_package_modules_exist() -> None:
    """All architectural modules in the spec must exist on disk."""

    missing: list[str] = []
    for rel in _REQUIRED_PACKAGE_MODULES:
        if not (PROJECT_ROOT / rel).is_file():
            missing.append(rel)
    assert not missing, (
        "Required architectural modules are missing -- the layered structure "
        "from docs/ARCHITECTURE.md has been broken. Missing:\n  "
        + "\n  ".join(missing)
    )


# ---------------------------------------------------------------------------
# Sub-packages have __init__.py
# ---------------------------------------------------------------------------


def test_subpackages_have_init_files() -> None:
    """``data/``, ``state/``, and ``engines/`` must be real sub-packages."""

    for sub in ("data", "state", "engines"):
        init = PACKAGE_ROOT / sub / "__init__.py"
        assert init.is_file(), f"Missing sub-package init file: {init}"


# ---------------------------------------------------------------------------
# Monolith lives at the repo root, NOT inside the package
# ---------------------------------------------------------------------------


def test_monolith_is_at_repo_root_not_inside_package() -> None:
    """The V1.34 monolith is the frozen reference at the repo root.

    It must not have been moved into ``rytm_randomizer/`` (which would expose
    it as a package module).
    """

    assert MONOLITH_PATH.is_file(), (
        f"Expected the V1.34 monolith at {MONOLITH_PATH}, but it is missing."
    )
    inside = PACKAGE_ROOT / "rytm_hybrid_randomizer_v134.py"
    assert not inside.exists(), (
        f"The V1.34 monolith must remain at the repo root (frozen reference). "
        f"It must NOT live inside the package at {inside}."
    )


# ---------------------------------------------------------------------------
# Monolith has no working-tree diff (byte-identical to its tagged form)
# ---------------------------------------------------------------------------


def test_monolith_has_no_working_tree_diff() -> None:
    """The monolith must remain byte-identical to its committed form.

    This mirrors ``tests/test_real_midi_import_safety.py::
    test_v134_reference_has_no_working_tree_diff``; we duplicate it under
    ``tests/architecture/`` so the architecture gate alone catches any drift.
    """

    result = subprocess.run(
        ["git", "diff", "--", str(MONOLITH_PATH.relative_to(PROJECT_ROOT))],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout == "", (
        "The V1.34 monolith has uncommitted edits. The monolith is a frozen "
        "byte-parity reference -- do not edit it. Use the package modules "
        "for new work.\n" + result.stdout
    )


# ---------------------------------------------------------------------------
# Package SHA-256 fingerprint of layout (informational; non-failing)
# ---------------------------------------------------------------------------


def test_layout_summary_is_readable() -> None:
    """Compute a fingerprint of the package module set.

    This test never fails; it exists so that ``pytest -v
    tests/architecture/test_layering_structure.py`` prints the current
    layout fingerprint, which is useful when reviewing a layout-affecting
    diff. The value is deterministic and changes when modules are added /
    removed.
    """

    modules = sorted(
        str(p.relative_to(PROJECT_ROOT)).replace("\\", "/")
        for p in PACKAGE_ROOT.rglob("*.py")
    )
    digest = hashlib.sha256("\n".join(modules).encode("utf-8")).hexdigest()
    assert digest  # informational
    # Also stash on the test for debugging.
    sys.stderr.write(
        f"[architecture] package-layout fingerprint = {digest[:16]} "
        f"({len(modules)} modules)\n"
    )
