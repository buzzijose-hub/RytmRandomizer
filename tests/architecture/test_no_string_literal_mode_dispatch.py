"""Gate 10 — string-literal dispatch hygiene.

Per ``docs/PLAN_REQUIREMENTS.md`` Gate 10, no module may dispatch on the
canonical mode / intensity / page / mutation-kind / pad-1-machine string
values via inline string equality. The single source of truth is
``rytm_randomizer/data/modes.py`` (introduced by WS-M3), which exports each
concept as both a ``Literal[...]`` type and a ``Final`` tuple of strings.

This test walks every ``rytm_randomizer/**/*.py`` module and parses it with
``ast``, then fails if any ``ast.Compare`` node uses ``==`` or ``!=`` against
a constant matching one of ``_GUARDED_STRINGS``.

What this test catches:

* ``mode == "balanced"``
* ``"discovery" != kind``
* ``intensity == "harder" or intensity == "intense"``

What this test does NOT catch (and must not):

* ``mode in ("balanced", "deeper")`` — membership, not equality dispatch.
* ``f"mode={mode}"`` — string interpolation.
* String literals as dictionary keys, default values, log payloads.
* ``case "balanced":`` — match statements are a structural improvement over
  ``==`` chains, so they're not flagged.

The module ``rytm_randomizer/data/modes.py`` is intentionally exempt: it IS
the canonical declaration site.

**Allowlist policy.** Today many dispatch sites still use inline string
equality (the migration to ``data/modes.py`` constants is gated on WS-M3 +
follow-up call-site sweeps). Each entry in ``_KNOWN_LEGACY_SITES`` is a
deferred migration target — the dispatch site should eventually consume the
constants from ``rytm_randomizer.data.modes``. Adding a new entry requires
explicit reviewer approval; the test will only stay green if no NEW dispatch
sites are introduced.
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

# Single source of truth lives in ``rytm_randomizer/data/modes.py``; this
# module is intentionally exempt from the gate.
_EXEMPT_MODULES: Final[frozenset[str]] = frozenset(
    {
        "data/modes.py",
    }
)

_GUARDED_STRINGS: Final[frozenset[str]] = frozenset(
    {
        # Intensity (data/modes.py::INTENSITY_MODES)
        "balanced",
        "deeper",
        "intense",
        "harder",
        # Page (data/modes.py::PAGE_MODES)
        "src",
        "filter",
        "amp",
        "lfo",
        "morph",
        "body",
        "grit",
        # Mutation kind (data/modes.py::MUTATION_KINDS)
        "discovery",
        "mutation",
        # Pad-1 machine (data/modes.py::PAD1_MODES)
        "sharp",
        "hard",
        "classic",
        "fm",
    }
)

# Known legacy dispatch sites. Each entry is "<relpath>:<lineno>:<literal>".
# Every entry is a deferred migration target — the dispatch site should
# eventually consume the constants from ``rytm_randomizer.data.modes``
# instead of comparing against the inline string. Adding a NEW entry requires
# explicit reviewer approval; the test stays green only if no new dispatch
# sites are introduced.
_KNOWN_LEGACY_SITES: Final[frozenset[str]] = frozenset(
    {
        "behavior/pad_lane.py:1174:discovery",
        "behavior/pad_lane.py:1175:mutation",
        "behavior/pad_lane.py:1177:discovery",
        "engines/pad2.py:235:grit",
        "engines/pad4.py:364:filter",
        "engines/pad4.py:412:filter",
        "randomization.py:156:sharp",
        "randomization.py:167:hard",
        "randomization.py:178:classic",
        "randomization.py:189:fm",
    }
)


def _all_package_files() -> list[Path]:
    return sorted(PACKAGE_ROOT.rglob("*.py"))


def _is_guarded_constant(node: ast.expr) -> str | None:
    """Return the guarded string if ``node`` is a matching ``ast.Constant``."""

    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        if node.value in _GUARDED_STRINGS:
            return node.value
    return None


def _string_dispatch_violations(path: Path) -> list[str]:
    """Return ``<relpath>:<lineno>:<literal>`` for every guarded ``==``/``!=`` site."""

    src = path.read_text(encoding="utf-8")
    tree = ast.parse(src, filename=str(path))
    rel = path.relative_to(PACKAGE_ROOT).as_posix()
    out: list[str] = []

    for node in ast.walk(tree):
        if not isinstance(node, ast.Compare):
            continue
        # ``ast.Compare`` has one ``left`` and a parallel list of ``ops`` /
        # ``comparators``. We only care about ``==``/``!=`` ops paired with a
        # guarded string literal on either side of the comparison. For a chain
        # ``a == b == c``, the pairs are ``(a, b)`` and ``(b, c)``; ``operands``
        # mirrors that layout so ``operands[i]`` is the left side of ``ops[i]``.
        operands: list[ast.expr] = [node.left, *node.comparators]
        for i, op in enumerate(node.ops):
            if not isinstance(op, (ast.Eq, ast.NotEq)):
                continue
            left = operands[i]
            right = operands[i + 1]
            for side in (left, right):
                literal = _is_guarded_constant(side)
                if literal is not None:
                    out.append(f"{rel}:{node.lineno}:{literal}")
                    # Don't double-count both sides of a single ``==``.
                    break
    return out


def test_no_unallowlisted_string_literal_mode_dispatch() -> None:
    """No new string-equality dispatch on the canonical mode/page strings.

    Enforces Gate 10 of ``docs/PLAN_REQUIREMENTS.md``. The canonical strings
    live in ``rytm_randomizer/data/modes.py`` and must be consumed via the
    exported ``Literal[...]`` types and ``Final`` tuples.
    """

    violations: list[str] = []
    for path in _all_package_files():
        rel = path.relative_to(PACKAGE_ROOT).as_posix()
        if rel in _EXEMPT_MODULES:
            continue
        for entry in _string_dispatch_violations(path):
            if entry in _KNOWN_LEGACY_SITES:
                continue
            violations.append(entry)

    assert not violations, (
        "New string-equality dispatch on canonical mode/intensity/page/"
        "mutation-kind/pad-1-machine strings is forbidden by Gate 10. "
        "Import the constant from ``rytm_randomizer.data.modes`` instead. "
        "If this site is truly a legacy holdover, add it to "
        "``_KNOWN_LEGACY_SITES`` with reviewer approval.\n"
        "  Violations:\n    " + "\n    ".join(violations)
    )


def test_legacy_allowlist_entries_still_exist() -> None:
    """Every ``_KNOWN_LEGACY_SITES`` entry must still match a real dispatch site.

    Keeps the allowlist honest: as legacy sites are migrated to consume the
    ``data/modes.py`` constants, the corresponding allowlist entry MUST be
    removed in the same PR (otherwise the allowlist rots into a graveyard).
    """

    actual: set[str] = set()
    for path in _all_package_files():
        rel = path.relative_to(PACKAGE_ROOT).as_posix()
        if rel in _EXEMPT_MODULES:
            continue
        actual.update(_string_dispatch_violations(path))

    stale = sorted(_KNOWN_LEGACY_SITES - actual)
    assert not stale, (
        "``_KNOWN_LEGACY_SITES`` lists sites that no longer exist (either the "
        "line moved or the dispatch was migrated to ``data/modes.py``). "
        "Remove the stale entries in the same PR.\n"
        "  Stale entries:\n    " + "\n    ".join(stale)
    )
