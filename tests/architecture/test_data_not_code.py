"""Enforce the data-not-code rule from ``docs/ARCHITECTURE.md`` section 4.

The data-not-code rule states that any "table of facts" (CC numbers,
anchors, deltas, zones, scenes, profiles, mutation plans, layouts) lives
under ``rytm_randomizer/data/`` exactly once. Wrapper modules (``profiles``,
``scenes``, ``constants``, etc.) MUST derive their values from ``data/``
instead of re-typing them.

These tests:

1. Assert every fact table is declared under ``data/``.
2. Assert no other module redefines a name that already exists in ``data/``
   (and isn't re-exporting it via an import alias).
3. Assert the public ``data/__init__.py`` exports the canonical set so
   consumers have a single import surface.

This extends WS-F's ``tests/test_data_layer.py`` drift-guard with a
structural rule that fails at AST level, not at value-level.
"""

from __future__ import annotations

import ast
import importlib
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PACKAGE_ROOT = PROJECT_ROOT / "rytm_randomizer"
DATA_ROOT = PACKAGE_ROOT / "data"


def _all_assignments_in(path: Path) -> set[str]:
    """Return every module-level NAME that ``path`` binds via assignment."""

    src = path.read_text(encoding="utf-8")
    tree = ast.parse(src, filename=str(path))
    out: set[str] = set()
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for tgt in node.targets:
                if isinstance(tgt, ast.Name):
                    out.add(tgt.id)
        elif isinstance(node, ast.AnnAssign):
            if isinstance(node.target, ast.Name):
                out.add(node.target.id)
    return out


def _import_aliases_in(path: Path) -> set[str]:
    """Return the set of names that ``path`` BINDS by importing them.

    A name appears in this set if it is brought into module scope by an
    ``import x as y`` or ``from x import y`` statement, where ``y`` is the
    bound local name. This lets us distinguish an "alias re-export" from a
    real redefinition.
    """

    src = path.read_text(encoding="utf-8")
    tree = ast.parse(src, filename=str(path))
    out: set[str] = set()
    for node in tree.body:
        if isinstance(node, ast.Import):
            for n in node.names:
                out.add(n.asname or n.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            for n in node.names:
                out.add(n.asname or n.name)
    return out


def _data_layer_names() -> dict[str, Path]:
    """Return the set of UPPER_SNAKE names defined under ``data/``.

    Excludes ``data/__init__.py`` (that file is the public re-export surface,
    not a source-of-truth definition site).
    """

    names: dict[str, Path] = {}
    for path in sorted(DATA_ROOT.rglob("*.py")):
        if path.name == "__init__.py":
            continue
        src = path.read_text(encoding="utf-8")
        tree = ast.parse(src, filename=str(path))
        for node in tree.body:
            if isinstance(node, ast.Assign):
                for tgt in node.targets:
                    if isinstance(tgt, ast.Name) and tgt.id.isupper():
                        names.setdefault(tgt.id, path)
            elif isinstance(node, ast.AnnAssign):
                if isinstance(node.target, ast.Name) and node.target.id.isupper():
                    names.setdefault(node.target.id, path)
    return names


# Names of well-known fact tables that we expect to live under data/.
_CANONICAL_FACT_TABLES: tuple[str, ...] = (
    "MACHINE_CC",
    "PROFILES",
    "SCENE_PRESETS",
    "GROUP_LAYOUT",
    "INTENSITY_PLANS",
    "GLOBAL_PAGE_PLANS",
    "PAD3_MODE_MUTATION_PLANS",
    "PAD4_MODE_MUTATION_PLANS",
    "PAD1_BD_MUTATION_PLANS",
    "PAD2_MUTATION_PLANS",
)


# ---------------------------------------------------------------------------
# Rule: the canonical fact tables live under data/
# ---------------------------------------------------------------------------


def test_canonical_fact_tables_live_in_data_layer() -> None:
    """Every well-known fact table must be defined under ``data/``."""

    data_names = _data_layer_names()
    missing = [name for name in _CANONICAL_FACT_TABLES if name not in data_names]
    assert not missing, (
        "These canonical fact tables MUST live under rytm_randomizer/data/ "
        "(see docs/ARCHITECTURE.md section 4 'Data, not code, for fact "
        "tables'). Missing:\n  " + "\n  ".join(missing)
    )


# ---------------------------------------------------------------------------
# Rule: no other module redefines a name that exists in data/
# ---------------------------------------------------------------------------


def test_no_module_redefines_a_data_layer_name() -> None:
    """No module outside ``data/`` may assign a name already defined in ``data/``.

    A name appearing on the LHS of an assignment is a redefinition. A name
    appearing only as an import alias is a re-export, which is allowed.
    """

    data_names = set(_data_layer_names().keys())
    violations: list[str] = []
    for path in sorted(PACKAGE_ROOT.rglob("*.py")):
        if path.is_relative_to(DATA_ROOT):
            continue
        assignments = _all_assignments_in(path)
        aliases = _import_aliases_in(path)
        for name in sorted(assignments):
            if name in data_names and name not in aliases:
                violations.append(
                    f"{path.relative_to(PROJECT_ROOT)} redefines {name} "
                    f"(canonical definition lives in data/)"
                )
    assert not violations, (
        "Modules outside data/ MUST NOT redefine a name that already exists "
        "in the data layer. Re-export from data/ instead.\n  " + "\n  ".join(violations)
    )


# ---------------------------------------------------------------------------
# Rule: data/__init__.py re-exports the canonical fact tables
# ---------------------------------------------------------------------------


def test_data_init_re_exports_canonical_fact_tables() -> None:
    """``rytm_randomizer.data.__init__`` must publicly expose the canonical names."""

    data_mod = importlib.import_module("rytm_randomizer.data")
    missing = [name for name in _CANONICAL_FACT_TABLES if not hasattr(data_mod, name)]
    assert not missing, (
        "rytm_randomizer.data.__init__ must re-export the canonical fact "
        "tables (single public import surface for consumers). Missing:\n  " + "\n  ".join(missing)
    )


# ---------------------------------------------------------------------------
# Rule: the public data namespace is non-empty and consistently UPPER_SNAKE
# ---------------------------------------------------------------------------


def test_data_namespace_is_upper_snake_constants() -> None:
    """Every public name in ``data/__init__.py.__all__`` is UPPER_SNAKE."""

    data_mod = importlib.import_module("rytm_randomizer.data")
    public = list(getattr(data_mod, "__all__", []) or [])
    assert public, "data/__init__.py must define __all__ with the public names."
    bad = [name for name in public if not name.isupper()]
    assert not bad, (
        "All public data-layer names must be UPPER_SNAKE constants. " f"Offenders: {bad}"
    )
