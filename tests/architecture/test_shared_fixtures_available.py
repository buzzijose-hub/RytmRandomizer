"""Architecture tests: shared fixtures must be centralised in tests/conftest.py.

RED phase — these tests fail until WS-M4 Phase 1 lands:
  * tests/conftest.py created with RecordingOut, _FakeMessage, and fixtures.
  * In-scope duplicates removed from the 6 test files.

Per WS-M4-PLAN.md §8 and PLAN_REQUIREMENTS.md Gate 11.
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.fast

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

_TESTS_DIR = Path(__file__).resolve().parents[1]
_CONFTEST = _TESTS_DIR / "conftest.py"

# Files that are *allowed* to keep a local definition (plan §1 allowlist).
_ALLOWLIST_FAKE_MESSAGE: frozenset[str] = frozenset(
    [
        "test_guardrails_e2e.py",
        "test_midi_io.py",
    ]
)
_ALLOWLIST_INSTALL_FAKE_MIDO: frozenset[str] = frozenset(
    [
        "test_mido_provider.py",
    ]
)

# Canonical symbols and their per-symbol allowlists.
_SYMBOL_ALLOWLISTS: dict[str, frozenset[str]] = {
    "RecordingOut": frozenset(),
    "_FakeMessage": _ALLOWLIST_FAKE_MESSAGE,
    "_install_fake_mido": _ALLOWLIST_INSTALL_FAKE_MIDO,
    "_no_sleep": frozenset(),
}

# The 8 in-scope test files that must import (not define) the shared helpers.
_IN_SCOPE_FILES = [
    "test_engines_pad1.py",
    "test_engines_pad2.py",
    "test_engines_pad3.py",
    "test_engines_pad4.py",
    "test_group_runner.py",
    "test_scene_runner.py",
    "test_midi_io.py",
    "test_randomization.py",
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _defined_symbol_locations(symbol: str) -> list[str]:
    """Return the tests/*.py filenames that contain a class/def named *symbol*.

    Includes ``conftest.py`` so the symmetric "conftest.py must define it"
    assertion can locate the canonical definition.
    """

    found: list[str] = []
    candidates = sorted(_TESTS_DIR.glob("test_*.py"))
    conftest = _TESTS_DIR / "conftest.py"
    if conftest.is_file():
        candidates.append(conftest)
    for path in candidates:
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
                if node.name == symbol:
                    found.append(path.name)
                    break
    return found


# ---------------------------------------------------------------------------
# Test: each canonical symbol defined exactly once outside allowlist
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "symbol",
    ["RecordingOut", "_FakeMessage", "_install_fake_mido", "_no_sleep"],
)
def test_symbol_defined_exactly_once_outside_allowlist(symbol: str) -> None:
    """Each canonical symbol must appear in *tests/conftest.py* only.

    Files in the per-symbol allowlist may keep local definitions (plan §1).
    Any other test_*.py file that defines the symbol is a duplication violation.
    """
    allowlist = _SYMBOL_ALLOWLISTS[symbol]
    locations = _defined_symbol_locations(symbol)

    # conftest.py is the one allowed definition outside the allowlist.
    violations = [f for f in locations if f not in allowlist and f != "conftest.py"]
    assert violations == [], (
        f"Symbol '{symbol}' is defined in {violations}; "
        "it should live only in tests/conftest.py (or the per-symbol allowlist)."
    )

    # conftest.py itself must export the symbol.
    assert "conftest.py" in locations or any(
        f in locations for f in allowlist
    ), f"Symbol '{symbol}' not found anywhere — conftest.py must define it."


# ---------------------------------------------------------------------------
# Test: conftest.py exports the two classes directly importable
# ---------------------------------------------------------------------------


def test_conftest_exports_recording_out_class() -> None:
    """``from conftest import RecordingOut`` must succeed."""
    # If conftest.py does not exist yet this import raises ModuleNotFoundError.
    import importlib

    conftest = importlib.import_module("conftest")
    assert hasattr(conftest, "RecordingOut"), "tests/conftest.py must define the class RecordingOut"


def test_conftest_exports_fake_message_class() -> None:
    """``from conftest import _FakeMessage`` must succeed."""
    import importlib

    conftest = importlib.import_module("conftest")
    assert hasattr(conftest, "_FakeMessage"), "tests/conftest.py must define the class _FakeMessage"


# ---------------------------------------------------------------------------
# Test: recording_out fixture usable from each in-scope file (import guard)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("filename", _IN_SCOPE_FILES)
def test_recording_out_fixture_usable_from_file(filename: str) -> None:
    """The named test file must NOT redefine RecordingOut locally.

    After WS-M4 migration the symbol is imported from conftest, not
    copy-pasted in place.  A local class-def is the violation signal.
    """
    path = _TESTS_DIR / filename
    assert path.exists(), f"Expected test file not found: {path}"

    tree = ast.parse(path.read_text(encoding="utf-8"))
    local_defs = [
        node.name
        for node in ast.walk(tree)
        if isinstance(node, ast.ClassDef) and node.name == "RecordingOut"
    ]
    assert local_defs == [], (
        f"{filename} still defines RecordingOut locally; " "delete it and import from conftest."
    )


# ---------------------------------------------------------------------------
# Test: live fixture smoke tests (require conftest.py to already exist)
# ---------------------------------------------------------------------------


def test_no_sleep_fixture_is_a_callable(no_sleep) -> None:  # type: ignore[no-untyped-def]
    """The ``no_sleep`` fixture must be a callable that accepts a float."""
    assert callable(no_sleep), "no_sleep fixture must be callable"
    result = no_sleep(1.5)
    assert result is None, "no_sleep must return None"


def test_fake_mido_session_installs_and_removes(fake_mido_session) -> None:  # type: ignore[no-untyped-def]
    """The ``fake_mido_session`` fixture must patch sys.modules['mido']."""
    import types

    assert "mido" in sys.modules, "fake_mido_session must install mido into sys.modules"
    installed = sys.modules["mido"]
    assert isinstance(installed, types.ModuleType), "installed mido must be a ModuleType"
    assert (
        installed is fake_mido_session
    ), "sys.modules['mido'] must be the fake module yielded by the fixture"
