"""Declarative import-direction matrix for every ``rytm_randomizer`` subpackage.

``test_import_direction.py`` enforces the original hand-written layer rules
for a handful of modules. This module is ADDITIVE: it freezes the complete
observed package-level import graph as of the 2026-07-18 rival-program
analysis, so that *every* package — including the ones the original test
never covered (``cockpit``, ``reports``, ``local_ai``, ``dual_machine``, …) —
has a declared row.

**Nested packages get their own rows.** An earlier revision scanned only
first-level subpackages, which collapsed nine distinct cockpit packages
(``cockpit/ws``, ``cockpit/device``, ``cockpit/library``, …) plus
``devices/strategies`` and the three ``reports/*`` packages into three
coarse rows. That made the matrix nearly vacuous exactly where the graph is
densest: ``cockpit.ws`` importing ``senders`` and ``cockpit.data``
importing only ``data`` were indistinguishable, and an intra-``cockpit``
edge (say ``cockpit/data`` reaching up into ``cockpit/ws``) was invisible.
Every package with an ``__init__.py``, at any depth, now has its own row,
and edges BETWEEN nested siblings are recorded.

The ``ALLOWED`` table below is a FREEZE of today's reality, not a judgment:
questionable edges are kept (with a ``TODO(rival-program)`` marker) so the
suite is green on the current tree, and tightening a row is a deliberate,
reviewable one-line diff.

Mechanics:

* Imports are discovered with ``ast`` (never regex), so docstrings and
  comments cannot produce false positives.
* Relative imports are resolved against the importing file's package path
  (``from ..data import x`` inside ``reports/foo.py`` resolves to ``data``).
* An import target is attributed to the LONGEST declared package that
  prefixes it, so ``from ...cockpit.ws.protocol import X`` is an edge to
  ``cockpit.ws``, not to ``cockpit``.
* A package's own files exclude those owned by a deeper package, so
  ``cockpit``'s row covers only ``cockpit/*.py``, not ``cockpit/ws/*.py``.
* Edges to a package's own ancestors or descendants are NOT recorded —
  those are intra-package, not cross-package, imports.

Two guarantees:

1. Every package on disk (any depth) has a row — a brand-new package fails
   until it declares its layer here.
2. No package imports a sibling (or top-level module) missing from its
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
# The frozen matrix (2026-07-18 baseline; nested rows added 2026-07-30).
#
# Row = dotted package name relative to ``rytm_randomizer`` (nested packages
# included: ``cockpit.ws``, ``devices.strategies``, …); value = the packages
# and top-level rytm_randomizer modules that package is allowed to import.
# Removing an entry (tightening) is encouraged; adding one is an architecture
# decision.
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
    # ``cockpit`` itself is thin: the package root only wires logging and the
    # passive provider. The real graph lives in the nested rows below.
    "cockpit": frozenset(
        {
            # TODO(rival-program): review this edge — cockpit reaching the
            # armed MIDI boundary module directly should be funneled through
            # app-owned wiring.
            "mido_provider",
            "observability",
            # Live-kit targeting owns only the device-neutral include/lock
            # view; the reusable scope record remains in snapshot/.
            "snapshot",
        }
    ),
    "cockpit.capture": frozenset(
        {
            "cockpit.data",
            "data",
            "devices",
            "devices.strategies",
            # Capture validates and round-trips the canonical saved-KIT
            # codecs already owned by the engine layer; it does not fork a
            # second Elektron envelope implementation.
            "engines",
            "observability",
        }
    ),
    "cockpit.data": frozenset({"data"}),
    "cockpit.device": frozenset(
        {
            "cockpit.data",
            "cockpit.ws",
            "data",
            # I9: the passive MIDI monitor picks its per-family decoder from
            # the devices registry instead of assuming every connection is a
            # Rytm. Registry-only (``all_devices``) — never a concrete family.
            "devices",
            "observability",
            # TODO(rival-program): review this edge — the device layer holds
            # the passive port provider surface directly.
            "real_midi_adapter",
            # Wave 4: the live MIDI monitor decodes CC labels via the
            # passive state/rytm_cc_observe helpers.
            "state",
        }
    ),
    "cockpit.engine": frozenset(
        {
            "cockpit.data",
            "observability",
            "snapshot",
        }
    ),
    "cockpit.export": frozenset(
        {
            "behavior",  # PR #214 merge: consumes behavior.midi_event_plan validation
            "cli_registry",
            "cockpit.data",
            "cockpit.profiles",
            "data",
            "devices",
            "observability",
            # AL16 offline export reads the shared Elektron ASCII-name
            # envelope primitive while auditing saved-kit payloads.
            "snapshot",
            "style_analysis",
        }
    ),
    "cockpit.history": frozenset(
        {
            "cockpit.data",
            "observability",
        }
    ),
    "cockpit.library": frozenset(
        {
            "cockpit.export",
            "cockpit.profiles",
            # Wave 4: the library importer decodes captures through the
            # devices registry (device-generic decode) and extracts SysEx
            # payloads via snapshot/sysex_file.
            "devices",
            "snapshot",
        }
    ),
    "cockpit.profiles": frozenset(
        {
            "cockpit.data",
            "cockpit.export",
            "observability",
        }
    ),
    "cockpit.wizard": frozenset(
        {
            "cockpit.data",
            "observability",
            "style_analysis",
        }
    ),
    "cockpit.ws": frozenset(
        {
            "cockpit.capture",
            "cockpit.data",
            "cockpit.device",
            "cockpit.engine",
            "cockpit.export",
            "cockpit.history",
            "cockpit.library",
            "cockpit.profiles",
            "cockpit.wizard",
            "devices",
            # TODO(rival-program): review this edge — see cockpit note above.
            "mido_provider",
            "observability",
            "reports",
            # Wave 4: all cockpit outbound transmit routes through the
            # senders ArmedApply seam (the arm command constructs the
            # real adapter through it exclusively).
            "senders",
        }
    ),
    "data": frozenset(),
    "devices": frozenset(
        {
            "mock_midi",
            "snapshot",
        }
    ),
    "devices.strategies": frozenset(
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
            "devices.strategies",
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
            "observability",  # PR #214 merge: patch-batch reports emit bounded RED telemetry
            "active_boundary",
            "behavior",
            "cli_registry",
            # TODO(rival-program): review these edges — reports/ is a passive
            # formatter layer; importing cockpit (and senders below) points
            # the arrow at a higher/active layer.
            "cockpit.data",
            "cockpit.export",
            "cockpit.profiles",
            "data",
            "devices",
            "devices.strategies",
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
    "reports.live_gui_overlay": frozenset(
        {
            "data",
            "style_analysis",
        }
    ),
    "reports.performance_console": frozenset(),
    "reports.style_performance": frozenset(
        {
            "cli_registry",
            "data",
            "style_analysis",
        }
    ),
    "senders": frozenset(
        {
            "behavior",  # PR #214 merge: CcNrpnEvent Protocol moved to behavior.midi_event_plan
            "data",  # PR #214 merge: senders validate against canonical A4 CC/NRPN address tables
            "devices",
            "midi_io",
            # Wave 4: ArmedApplyError is a MidiError taxonomy member
            # (observability/errors) per the OBS O4 fingerprint discipline.
            "observability",
        }
    ),
    "snapshot": frozenset(
        {
            "devices",
            # Typed packed-payload validation failures participate in the
            # package-wide BoundaryError taxonomy.
            "observability",
        }
    ),
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
            "behavior",  # PR #214 merge: send-plan compiler validates via behavior.midi_event_plan
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


def _package_paths() -> dict[str, Path]:
    """Return ``{dotted name: directory}`` for every package at any depth.

    Recurses, so ``cockpit/ws/`` yields ``cockpit.ws`` alongside ``cockpit``.
    A directory counts as a package only when it holds an ``__init__.py``.
    """

    found: dict[str, Path] = {}

    def _walk(root: Path, prefix: str) -> None:
        for entry in sorted(root.iterdir()):
            if not (entry.is_dir() and (entry / "__init__.py").is_file()):
                continue
            dotted = f"{prefix}{entry.name}"
            found[dotted] = entry
            _walk(entry, f"{dotted}.")

    _walk(PACKAGE_ROOT, "")
    return found


def _subpackage_names() -> frozenset[str]:
    """Return every package name on disk (nested packages included)."""

    return frozenset(_package_paths())


def _owned_sources(name: str, packages: Mapping[str, Path]) -> list[Path]:
    """Return the ``*.py`` files a package owns, excluding nested packages.

    ``cockpit`` owns ``cockpit/*.py`` but NOT ``cockpit/ws/handlers.py`` —
    that file belongs to the ``cockpit.ws`` row.
    """

    root = packages[name]
    deeper = tuple(path for other, path in packages.items() if other.startswith(f"{name}."))
    return [
        source
        for source in sorted(root.rglob("*.py"))
        if "__pycache__" not in source.parts
        and not any(d == source.parent or d in source.parents for d in deeper)
    ]


def _owning_package(parts: tuple[str, ...], packages: Mapping[str, Path]) -> str | None:
    """Attribute an import target to its LONGEST declared package prefix.

    ``("cockpit", "ws", "protocol")`` resolves to ``cockpit.ws`` (not
    ``cockpit``); a top-level module stem resolves to itself; anything else
    (stdlib, third party) resolves to ``None``.
    """

    for size in range(len(parts), 0, -1):
        candidate = ".".join(parts[:size])
        if candidate in packages:
            return candidate
    if parts and parts[0] in _top_level_module_names():
        return parts[0]
    return None


def _top_level_module_names() -> frozenset[str]:
    """Return every ``rytm_randomizer/*.py`` module stem (sans ``__init__``)."""

    return frozenset(path.stem for path in PACKAGE_ROOT.glob("*.py") if path.name != "__init__.py")


def _import_targets(
    node: ast.Import | ast.ImportFrom, file_pkg_parts: tuple[str, ...]
) -> list[tuple[str, ...]]:
    """Resolve one import node to package-root-relative dotted part tuples.

    The FULL path is returned (not just the first component) so a nested
    package can be attributed correctly: ``from ...cockpit.ws.protocol
    import X`` yields ``("cockpit", "ws", "protocol")``, which
    :func:`_owning_package` attributes to ``cockpit.ws``. Imports of
    third-party / stdlib modules resolve to nothing.
    """

    targets: list[tuple[str, ...]] = []
    if isinstance(node, ast.Import):
        for alias in node.names:
            if alias.name.startswith(f"{PACKAGE_NAME}."):
                targets.append(tuple(alias.name.split(".")[1:]))
        return targets

    if node.level == 0:
        module = node.module or ""
        if module == PACKAGE_NAME:
            targets.extend((alias.name,) for alias in node.names)
        elif module.startswith(f"{PACKAGE_NAME}."):
            targets.append(tuple(module.split(".")[1:]))
        return targets

    # Relative import: resolve against the importing file's package parts.
    ascend = node.level - 1
    base = list(file_pkg_parts[: len(file_pkg_parts) - ascend])
    module_parts = (node.module or "").split(".") if node.module else []
    resolved = base + module_parts
    if resolved:
        targets.append(tuple(resolved))
    else:
        # ``from .. import x`` at package-root level: names are the targets.
        targets.extend((alias.name,) for alias in node.names)
    return targets


def _is_intra_package(source_pkg: str, target_pkg: str) -> bool:
    """True when ``target_pkg`` is ``source_pkg``, an ancestor, or a descendant.

    ``cockpit.ws`` importing ``cockpit.ws.protocol`` (itself), ``cockpit``
    (ancestor), or a hypothetical ``cockpit.ws.sub`` (descendant) are all
    internal structure, not cross-package edges.
    """

    return (
        target_pkg == source_pkg
        or target_pkg.startswith(f"{source_pkg}.")
        or source_pkg.startswith(f"{target_pkg}.")
    )


def _observed_graph() -> dict[str, frozenset[str]]:
    """Derive the current package import graph from the tree via ast.

    Every package at any depth gets its own entry; a package's own files
    exclude those owned by a deeper package.
    """

    packages = _package_paths()
    graph: dict[str, set[str]] = {name: set() for name in sorted(packages)}

    for name in sorted(packages):
        for source in _owned_sources(name, packages):
            file_pkg_parts = source.relative_to(PACKAGE_ROOT).parts[:-1]
            tree = ast.parse(source.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if not isinstance(node, (ast.Import, ast.ImportFrom)):
                    continue
                for target in _import_targets(node, file_pkg_parts):
                    owner = _owning_package(target, packages)
                    if owner is None or _is_intra_package(name, owner):
                        continue
                    graph[name].add(owner)

    return {name: frozenset(edges) for name, edges in graph.items()}


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_every_subpackage_declares_a_matrix_row() -> None:
    """Every on-disk package (any depth) has a row, and no row is stale.

    A new package — including a nested one like ``cockpit/ws`` — fails here
    until its author declares its layer, i.e. which packages and top-level
    modules it is allowed to import.
    """

    present = _subpackage_names()
    declared = frozenset(ALLOWED)

    missing_rows = sorted(present - declared)
    assert not missing_rows, (
        "Package(s) without an import-direction matrix row. A new package — "
        "nested ones included — must declare its layer in ALLOWED (this "
        "file) before it can land: list exactly the packages/top-level "
        "modules it imports.\n"
        "  Missing rows:\n    " + "\n    ".join(missing_rows)
    )

    stale_rows = sorted(declared - present)
    assert not stale_rows, (
        "ALLOWED declares row(s) for packages that no longer exist. "
        "Remove the stale rows in the same PR that removed the packages.\n"
        "  Stale rows:\n    " + "\n    ".join(stale_rows)
    )


def test_nested_packages_have_independent_rows() -> None:
    """Nested packages are scanned, not collapsed into their parent's row.

    The regression this pins: an earlier revision walked only
    ``PACKAGE_ROOT.iterdir()``, so ``cockpit/ws``, ``cockpit/device``,
    ``devices/strategies`` and the ``reports/*`` packages had NO row of
    their own — their edges were attributed to the coarse parent row,
    hiding both the density of the cockpit graph and every intra-cockpit
    edge. Each nested package must appear as its own key.
    """

    present = _subpackage_names()
    nested = sorted(name for name in present if "." in name)
    assert nested, (
        "No nested package rows were discovered. The matrix must recurse "
        "into nested packages — if the tree genuinely flattened, delete "
        "this test in the same commit."
    )

    undeclared = sorted(name for name in nested if name not in ALLOWED)
    assert (
        not undeclared
    ), "Nested package(s) missing an independent ALLOWED row:\n    " + "\n    ".join(undeclared)

    # A parent row must not silently absorb a child's edges: a package's own
    # files are only its direct ``*.py``, never a nested package's.
    packages = _package_paths()
    for parent in sorted(name for name in present if "." not in name):
        owned = {source.parent for source in _owned_sources(parent, packages)}
        assert owned <= {packages[parent]}, (
            f"``{parent}``'s owned sources leak into a nested package "
            "directory; nested files belong to the nested row."
        )


def test_no_subpackage_imports_outside_its_declared_row() -> None:
    """No package imports a sibling/top-level module absent from its row.

    Adding a cross-package edge is an architecture decision: extend the
    package's ``ALLOWED`` row in this file (with review) rather than
    letting the graph drift silently. Nested packages are checked
    independently, so an intra-``cockpit`` edge is a real violation.
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
