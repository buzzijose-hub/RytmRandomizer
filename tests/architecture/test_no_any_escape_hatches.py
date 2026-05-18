"""Gate 6 — type-system hygiene: no bare ``X = Any`` escape hatches.

Per ``docs/PLAN_REQUIREMENTS.md`` Gate 6, no module may declare a top-level
type alias whose RHS is the bare ``typing.Any`` name. The historical pattern
was ``Sender = Any`` (and similar) as a duck-typed boundary marker; PR #35
retired all six occurrences in favor of a ``MidiSender`` Protocol.

This test walks every ``rytm_randomizer/**/*.py`` module, parses it with
``ast``, and fails if any module declares a module-level ``Assign`` of the
form ``X = Any`` where the RHS is the bare ``ast.Name(id='Any')`` node.

What this test DOES catch:

* ``Sender = Any``
* ``MyType: TypeAlias = Any``

What this test does NOT catch (and must not):

* ``Mapping[str, Any]`` — generic parameter, not a bare alias.
* ``def f(x: Any) -> Any: ...`` — annotation, not a top-level alias.
* ``cast(Any, x)`` — call argument, not an alias.

If a real ``X = Any`` must be re-introduced (extremely rare; would need to be
a Wave-3 / Wave-4 escape hatch with an architect sign-off), add the module
path + line number to ``_ALLOWLIST`` below with a one-line rationale.
"""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Final

import pytest

# WS-M4: mark this module as fast-suite; pytest -m fast skips the 505
# warm-worker V1.34 parity fixtures and runs in <60s.
pytestmark = pytest.mark.fast

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PACKAGE_ROOT = PROJECT_ROOT / "rytm_randomizer"

# Allowlist for any historical (or temporarily justified) ``X = Any``
# declarations. Each entry is "<relpath>:<lineno>" and requires a one-line
# rationale comment. Today this list is intentionally empty — PR #35 cleared
# the last six ``Sender = Any`` aliases as part of the WS-S1 Protocol roll-out.
_ALLOWLIST: Final[frozenset[str]] = frozenset()


def _all_package_files() -> list[Path]:
    return sorted(PACKAGE_ROOT.rglob("*.py"))


def _is_bare_any(value: ast.expr) -> bool:
    """Return True if ``value`` is the bare ``Any`` name (``ast.Name(id='Any')``)."""

    return isinstance(value, ast.Name) and value.id == "Any"


def _bare_any_aliases(path: Path) -> list[str]:
    """Return ``<relpath>:<lineno>`` for every top-level ``X = Any`` in ``path``.

    Only module-level ``Assign`` / ``AnnAssign`` nodes whose RHS is the bare
    ``Any`` name count. Generic parameters (``Mapping[str, Any]``), function
    annotations, and ``cast(Any, ...)`` calls are deliberately not flagged.
    """

    src = path.read_text(encoding="utf-8")
    tree = ast.parse(src, filename=str(path))
    out: list[str] = []
    rel = path.relative_to(PROJECT_ROOT).as_posix()
    for node in tree.body:
        if isinstance(node, (ast.Assign, ast.AnnAssign)) and (
            node.value is not None and _is_bare_any(node.value)
        ):
            out.append(f"{rel}:{node.lineno}")
    return out


def test_no_bare_any_aliases_in_package() -> None:
    """No top-level ``X = Any`` declaration may appear in ``rytm_randomizer/``.

    Enforces Gate 6 of ``docs/PLAN_REQUIREMENTS.md``. New module boundaries
    must declare a ``Protocol`` (with ``@runtime_checkable`` when ``isinstance``
    is needed) instead of a duck-typed ``X = Any`` placeholder.
    """

    violations: list[str] = []
    for path in _all_package_files():
        for entry in _bare_any_aliases(path):
            if entry in _ALLOWLIST:
                continue
            violations.append(entry)

    assert not violations, (
        "Bare ``X = Any`` aliases are forbidden by Gate 6 (type-system "
        "hygiene). Replace each with a ``Protocol`` boundary, or — if it "
        "is truly unavoidable — add the line to ``_ALLOWLIST`` with a "
        "one-line rationale.\n  Violations:\n    " + "\n    ".join(violations)
    )
