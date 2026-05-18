"""Enforce the expected package layout from ``docs/ARCHITECTURE.md``.

These tests assert that the modules listed in the architecture spec actually
exist (so a future refactor cannot quietly delete them).

The V1.34 ``rytm_hybrid_randomizer_v134.py`` monolith that once lived at the
repo root has been retired; its reference behavior is now captured as JSON
goldens under ``tests/fixtures/v134_parity/`` and enforced by the parity tests
that previously diffed against it.
"""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path

import pytest

# WS-M4: mark this module as fast-suite; pytest -m fast skips the 505
# warm-worker V1.34 parity fixtures and runs in <60s.
pytestmark = pytest.mark.fast

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PACKAGE_ROOT = PROJECT_ROOT / "rytm_randomizer"


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
    "rytm_randomizer/reports/__init__.py",
    "rytm_randomizer/reports/formatter.py",
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
        "from docs/ARCHITECTURE.md has been broken. Missing:\n  " + "\n  ".join(missing)
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
# The retired V1.34 monolith must not have been resurrected inside the package
# ---------------------------------------------------------------------------


def test_retired_monolith_has_not_been_resurrected() -> None:
    """The V1.34 monolith was retired in favor of JSON goldens.

    Both the original repo-root location and the inside-the-package location
    must stay missing -- the only authoritative source of V1.34 reference
    behavior is now ``tests/fixtures/v134_parity/``.
    """

    forbidden = [
        PROJECT_ROOT / "rytm_hybrid_randomizer_v134.py",
        PACKAGE_ROOT / "rytm_hybrid_randomizer_v134.py",
    ]
    present = [str(p) for p in forbidden if p.exists()]
    assert not present, (
        "The V1.34 monolith has been retired -- the reference behavior is "
        "captured as JSON goldens under tests/fixtures/v134_parity/. Re-adding "
        "the monolith resurrects a frozen file that is no longer the source of "
        f"truth.\n  Found: {present}"
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
        str(p.relative_to(PROJECT_ROOT)).replace("\\", "/") for p in PACKAGE_ROOT.rglob("*.py")
    )
    digest = hashlib.sha256("\n".join(modules).encode("utf-8")).hexdigest()
    assert digest  # informational
    # Also stash on the test for debugging.
    sys.stderr.write(
        f"[architecture] package-layout fingerprint = {digest[:16]} " f"({len(modules)} modules)\n"
    )
