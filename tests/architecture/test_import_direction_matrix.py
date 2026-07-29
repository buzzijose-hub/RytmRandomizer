"""Declarative import-direction matrix for every ``rytm_randomizer`` subpackage.

``test_import_direction.py`` enforces the original hand-written layer rules
for a handful of modules. This module is ADDITIVE: it freezes the complete
observed subpackage-level import graph as of the 2026-07-18 rival-program
analysis, so that *every* subpackage — including the ones the original test
never covered (``cockpit``, ``reports``, ``local_ai``, ``dual_machine``, …) —
has a declared row.

The ``ALLOWED`` table below is a FREEZE of today's reality, not a judgment:
questionable edges are kept (with a ``TODO(rival-program)`` marker) so the
suite is green on the current tree, and tightening a row is a deliberate,
reviewable one-line diff.

Mechanics:

* Imports are discovered with ``ast`` (never regex), so docstrings and
  comments cannot produce false positives.
* Relative imports are resolved against the importing file's package path
  (``from ..data import x`` inside ``reports/foo.py`` resolves to ``data``).
* An edge is recorded when a subpackage imports a SIBLING subpackage or a
  top-level ``rytm_randomizer/*.py`` module.

Two guarantees:

1. Every subpackage on disk has a row — a brand-new subpackage fails until
   it declares its layer here.
2. No subpackage imports a sibling (or top-level module) missing from its
   row — new cross-package edges are a deliberate, reviewed decision.
"""

from __future__ import annotations

import ast
from collections.abc import Mapping
from pathlib import Path
from typing import Final

import pytest

pytestmark = pytest.mark.fast

PROJECT_ROOT: Final[Path] = Path(__file__).resolve().parents[2]
PACKAGE_ROOT: Final[Path] = PROJECT_ROOT / "rytm_randomizer"
PACKAGE_NAME: Final[str] = "rytm_randomizer"

# ---------------------------------------------------------------------------
# The frozen matrix (2026-07-18 baseline).
#
# Row = subpackage name; value = the sibling subpackages and top-level
# rytm_randomizer modules that subpackage is allowed to import. Removing an
# entry (tightening) is encouraged; adding one is an architecture decision.
# ---------------------------------------------------------------------------

ALLOWED: Final[Mapping[str, frozenset[str]]] = {
    "behavior": frozenset(
        {
            "commands",
            "constants",
            "data",
            "profile_lookup",
            "scenes",
            "state",
        }
    ),
    "cockpit": frozenset(
        {
            "cli_registry",
            "data",
            # Wave 4: the library importer decodes captures through the
            # devices registry (device-generic decode).
            "devices",
            # TODO(rival-program): review this edge — cockpit reaching the
            # armed MIDI boundary modules directly (mido_provider /
            # real_midi_adapter) should be funneled through app-owned wiring.
            "mido_provider",
            "mock_midi",
            "observability",
            "real_midi_adapter",
            "reports",
            # Wave 4: all cockpit outbound transmit routes through the
            # senders ArmedApply seam (the arm command constructs the
            # real adapter through it exclusively).
            "senders",
            # Wave 4: the library importer extracts SysEx payloads via
            # snapshot/sysex_file.
            "snapshot",
            # Wave 4: the live MIDI monitor decodes CC labels via the
            # passive state/rytm_cc_observe helpers.
            "state",
            "style_analysis",
        }
    ),
    "data": frozenset(),
    "devices": frozenset(
        {
            "data",
            "guardrails",
            "mock_midi",
            "observability",
            "snapshot",
        }
    ),
    "dual_machine": frozenset({"devices"}),
    "engines": frozenset(
        {
            "data",
            # TODO(rival-program): review this edge — engines/ predates the
            # devices/ strategy seam; the original layer rules did not list
            # devices as an engines dependency.
            "devices",
            "guardrails",
            "midi_io",
            "observability",
            "randomization",
        }
    ),
    "guardrails": frozenset(
        {
            "data",
            "observability",
        }
    ),
    "local_ai": frozenset({"observability"}),
    "observability": frozenset(),
    "reports": frozenset(
        {
            "active_boundary",
            "behavior",
            "cli_registry",
            # TODO(rival-program): review this edge — reports/ is a passive
            # formatter layer; importing cockpit (and senders below) points
            # the arrow at a higher/active layer.
            "cockpit",
            "data",
            "devices",
            "engines",
            "guardrails",
            "local_ai",
            "mock_message_mapper",
            "mock_midi",
            "profile_lookup",
            "registry",
            "runtime_plan",
            # TODO(rival-program): review this edge — see cockpit note above.
            "senders",
            "snapshot",
            "state",
            "style_analysis",
        }
    ),
    "senders": frozenset(
        {
            "devices",
            "midi_io",
            # Wave 4: ArmedApplyError is a MidiError taxonomy member
            # (observability/errors) per the OBS O4 fingerprint discipline.
            "observability",
        }
    ),
    "snapshot": frozenset({"devices"}),
    "state": frozenset(
        {
            # TODO(rival-program): review this edge — the original layer
            # rules said state/ imports stdlib only; the commands edge crept
            # in and should be inverted or replaced with a shared DTO.
            "commands",
        }
    ),
    "style_analysis": frozenset(
        {
            "data",
            "guardrails",
            "local_ai",
            "observability",
        }
    ),
}

# ---------------------------------------------------------------------------
# Graph derivation (ast-based; mirrors how the baseline above was captured)
# ---------------------------------------------------------------------------


def _subpackage_names() -> frozenset[str]:
    """Return every ``rytm_randomizer/<sub>/`` package name on disk."""

    return frozenset(
        entry.name
        for entry in PACKAGE_ROOT.iterdir()
        if entry.is_dir() and (entry / "__init__.py").is_file()
    )


def _top_level_module_names() -> frozenset[str]:
    """Return every ``rytm_randomizer/*.py`` module stem (sans ``__init__``)."""

    return frozenset(path.stem for path in PACKAGE_ROOT.glob("*.py") if path.name != "__init__.py")


def _first_target_component(
    node: ast.Import | ast.ImportFrom, file_pkg_parts: tuple[str, ...]
) -> list[str]:
    """Resolve one import node to package-root-relative first components.

    ``from ..data import x`` inside ``reports/foo.py`` resolves to ``data``;
    ``from rytm_randomizer import engines`` resolves to ``engines``; imports
    of third-party / stdlib modules resolve to nothing.
    """

    targets: list[str] = []
    if isinstance(node, ast.Import):
        for alias in node.names:
            if alias.name.startswith(f"{PACKAGE_NAME}."):
                targets.append(alias.name.split(".")[1])
        return targets

    if node.level == 0:
        module = node.module or ""
        if module == PACKAGE_NAME:
            targets.extend(alias.name for alias in node.names)
        elif module.startswith(f"{PACKAGE_NAME}."):
            targets.append(module.split(".")[1])
        return targets

    # Relative import: resolve against the importing file's package parts.
    ascend = node.level - 1
    base = list(file_pkg_parts[: len(file_pkg_parts) - ascend])
    module_parts = (node.module or "").split(".") if node.module else []
    resolved = base + module_parts
    if resolved:
        targets.append(resolved[0])
    else:
        # ``from .. import x`` at package-root level: names are the targets.
        targets.extend(alias.name for alias in node.names)
    return targets


def _observed_graph() -> dict[str, frozenset[str]]:
    """Derive the current subpackage import graph from the tree via ast."""

    subpackages = _subpackage_names()
    top_modules = _top_level_module_names()
    graph: dict[str, set[str]] = {name: set() for name in sorted(subpackages)}

    for sub in sorted(subpackages):
        for source in sorted((PACKAGE_ROOT / sub).rglob("*.py")):
            rel_parts = source.relative_to(PACKAGE_ROOT).parts
            file_pkg_parts = rel_parts[:-1]
            tree = ast.parse(source.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if not isinstance(node, (ast.Import, ast.ImportFrom)):
                    continue
                for target in _first_target_component(node, file_pkg_parts):
                    if target == sub:
                        continue  # Intra-package import; not an edge.
                    if target in subpackages or target in top_modules:
                        graph[sub].add(target)

    return {name: frozenset(edges) for name, edges in graph.items()}


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_every_subpackage_declares_a_matrix_row() -> None:
    """Every on-disk subpackage has an ``ALLOWED`` row, and no row is stale.

    A new subpackage fails here until its author declares its layer — i.e.
    which siblings and top-level modules it is allowed to import.
    """

    present = _subpackage_names()
    declared = frozenset(ALLOWED)

    missing_rows = sorted(present - declared)
    assert not missing_rows, (
        "Subpackage(s) without an import-direction matrix row. A new "
        "subpackage must declare its layer in ALLOWED (this file) before it "
        "can land — list exactly the siblings/top-level modules it imports.\n"
        "  Missing rows:\n    " + "\n    ".join(missing_rows)
    )

    stale_rows = sorted(declared - present)
    assert not stale_rows, (
        "ALLOWED declares row(s) for subpackages that no longer exist. "
        "Remove the stale rows in the same PR that removed the packages.\n"
        "  Stale rows:\n    " + "\n    ".join(stale_rows)
    )


def test_no_subpackage_imports_outside_its_declared_row() -> None:
    """No subpackage imports a sibling/top-level module absent from its row.

    Adding a cross-package edge is an architecture decision: extend the
    subpackage's ``ALLOWED`` row in this file (with review) rather than
    letting the graph drift silently.
    """

    observed = _observed_graph()
    violations: list[str] = []
    for sub in sorted(observed):
        allowed = ALLOWED.get(sub, frozenset())
        undeclared = sorted(observed[sub] - allowed)
        if undeclared:
            violations.append(f"{sub} -> {', '.join(undeclared)}")

    assert not violations, (
        "Undeclared cross-subpackage import edge(s). Either remove the "
        "import or — deliberately, with review — add the edge to the "
        "subpackage's ALLOWED row in this file.\n"
        "  Undeclared edges:\n    " + "\n    ".join(violations)
    )
