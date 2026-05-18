"""Architecture tests: @pytest.mark.fast marker coverage.

RED phase — these tests fail until WS-M4 Phase 6 adds:
  * ``pytestmark = pytest.mark.fast`` to every non-parity test_*.py file.
  * ``"fast"`` marker registration in pyproject.toml.

Per WS-M4-PLAN.md §5 and PLAN_REQUIREMENTS.md Gate 8.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

pytestmark = pytest.mark.fast

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

_TESTS_DIR = Path(__file__).resolve().parents[1]
_PROJECT_ROOT = _TESTS_DIR.parent

# Parity suite files that must NOT carry the fast marker (they are slow).
_PARITY_FILES: frozenset[str] = frozenset(
    [
        "test_engines_pad1.py",
        "test_engines_pad2.py",
        "test_engines_pad3.py",
        "test_engines_pad4.py",
        "test_group_runner.py",
        "test_scene_runner.py",
    ]
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _has_fast_marker(path: Path) -> bool:
    """Return True if the module has ``pytestmark = pytest.mark.fast``."""
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except SyntaxError:
        return False

    for node in ast.walk(tree):
        # Match: pytestmark = pytest.mark.fast
        if not isinstance(node, ast.Assign):
            continue
        targets = node.targets
        if len(targets) != 1:
            continue
        target = targets[0]
        if not (isinstance(target, ast.Name) and target.id == "pytestmark"):
            continue
        value = node.value
        # pytest.mark.fast  →  Attribute(value=Attribute(value=Name('pytest'), attr='mark'), attr='fast')
        if (
            isinstance(value, ast.Attribute)
            and value.attr == "fast"
            and isinstance(value.value, ast.Attribute)
            and value.value.attr == "mark"
            and isinstance(value.value.value, ast.Name)
            and value.value.value.id == "pytest"
        ):
            return True
    return False


def _all_non_parity_test_files() -> list[Path]:
    """Return all tests/test_*.py that are outside the parity suite."""
    return [p for p in sorted(_TESTS_DIR.glob("test_*.py")) if p.name not in _PARITY_FILES]


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_every_non_parity_test_file_has_fast_marker() -> None:
    """Every tests/test_*.py outside the parity suite must carry the fast marker.

    This enables ``pytest -m fast`` as a <60s iteration loop (WS-M4-PLAN §5).
    """
    missing: list[str] = []
    for path in _all_non_parity_test_files():
        if not _has_fast_marker(path):
            missing.append(path.name)

    assert missing == [], (
        "The following test files are missing 'pytestmark = pytest.mark.fast':\n"
        + "\n".join(f"  tests/{f}" for f in sorted(missing))
        + "\nAdd the marker right after 'import pytest' in each file."
    )


def test_no_parity_file_has_fast_marker() -> None:
    """Parity test files must NOT have the fast marker — they are slow.

    test_engines_pad{1-4}.py, test_group_runner.py, test_scene_runner.py run
    505 parity fixtures via warm subprocesses and must be excluded from -m fast.
    """
    violators: list[str] = []
    for filename in sorted(_PARITY_FILES):
        path = _TESTS_DIR / filename
        if path.exists() and _has_fast_marker(path):
            violators.append(filename)

    assert violators == [], (
        "The following parity files incorrectly have the fast marker:\n"
        + "\n".join(f"  tests/{f}" for f in violators)
        + "\nRemove 'pytestmark = pytest.mark.fast' from parity suite files."
    )


def test_fast_marker_registered_in_pyproject() -> None:
    """pyproject.toml must register the 'fast' marker in [tool.pytest.ini_options].

    Without registration pytest emits PytestUnknownMarkWarning for every
    test that carries the marker, and --strict-markers would fail.
    """
    pyproject = _PROJECT_ROOT / "pyproject.toml"
    assert pyproject.exists(), f"pyproject.toml not found at {pyproject}"

    content = pyproject.read_text(encoding="utf-8")

    # Check that a markers list exists and contains the "fast" marker.
    assert (
        "markers" in content
    ), "pyproject.toml [tool.pytest.ini_options] must contain a 'markers' key"
    assert '"fast"' in content or "'fast'" in content or "fast:" in content, (
        "pyproject.toml markers list must include the 'fast' marker; "
        "add: fast: lightweight, in-process tests..."
    )
