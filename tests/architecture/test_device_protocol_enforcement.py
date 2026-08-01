"""Enforce the ``Device`` Protocol as the single cross-machine abstraction.

The ``rytm_randomizer.devices.Device`` Protocol (WS-S5) is the canonical
boundary for every Elektron device family the tool can target. The
registry at ``rytm_randomizer.devices.registry`` is the canonical lookup
surface (one entry per ``device_id``).

These tests turn the *advisory* "use the Device Protocol" rule into a
*mechanical* one. They catch the most common ways a contributor (human
or autonomous agent) can bypass the abstraction:

1. **A new device-family subpackage that does not register with the
   ``devices/`` registry.** Any new top-level package whose name matches a
   known Elektron device family (``analog_four/``, ``digitakt/``, etc.)
   must register a ``Device`` instance at import time. Otherwise the
   per-family code is invisible to ``devices.all_devices()`` and the
   single-source-of-truth registry contract breaks.

2. **A device-family subpackage that imports a sibling device family's
   private API.** Cross-family imports must go through the ``devices/``
   registry (``get_device("analog_rytm_mk2")``), never through
   ``from ..analog_four.snapshot_decoder import _find_kit_record``-style
   private-import coupling. This was a real finding in the codex review of
   the dual-machine cascade (``analog_four/controlled_diff.py:14-27``
   reaches into ``snapshot/rytm_decoder.py`` privates).

3. **The ``dual_machine`` orchestrator depending on concrete device
   subpackages instead of the registry surface.** ``dual_machine/`` is the
   shared orchestration / validation / reporting layer per Jose's spec; it
   must consume ``Mapping[str, Device]`` from ``devices.all_devices()`` so
   adding a fourth machine family does not require touching
   ``dual_machine/``.

4. **A concrete ``Device`` subclass that does not satisfy the Protocol
   at import time.** Every registered device must pass
   ``isinstance(dev, Device)`` (Protocol is ``@runtime_checkable``).

5. **A second registry or lookup helper outside ``devices/``.** Only one
   registry exists; anything else is a parallel surface that breaks the
   single-source-of-truth contract.

**Allowlist policy.** Each test uses a ``frozenset`` allowlist of legacy
violations (matching the pattern of
``test_no_string_literal_mode_dispatch.py``). Today the allowlists are
*empty* because the base branch has no sibling device subpackages.
**Adding a new entry requires explicit reviewer approval** in the PR body
("Add ``<entry>`` to ``_KNOWN_LEGACY_*`` with rationale: ..."), and every
entry is a deferred-migration target — the long-term state is an empty
allowlist.

Per Gate 6 (PLAN_REQUIREMENTS) the test enforces a Protocol surface, not
ABC inheritance: a structural ``Device`` implementation drops in without
inheriting from any base class.

Per Gate 9 (module-organization hygiene) the test rejects new top-level
device-family modules; new device families go under
``rytm_randomizer/devices/<family>/`` as subpackages of ``devices/``, OR
land as flat sibling subpackages that the allowlist explicitly accepts
during the migration.
"""

from __future__ import annotations

import ast
import importlib
from pathlib import Path
from typing import Final, get_type_hints

import pytest

# WS-M4: mark this module as fast-suite; pytest -m fast skips the 505
# warm-worker V1.34 parity fixtures and runs in <60s.
pytestmark = pytest.mark.fast

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PACKAGE_ROOT = PROJECT_ROOT / "rytm_randomizer"


# ---------------------------------------------------------------------------
# Catalog of known device-family names. Top-level subpackages whose name
# matches an entry here are *device families* and must route through the
# Device Protocol / registry. New families are added here as new Elektron
# machines come into scope.
# ---------------------------------------------------------------------------
_DEVICE_FAMILY_PACKAGE_NAMES: Final[frozenset[str]] = frozenset(
    {
        "analog_four",
        "analog_rytm",
        "digitakt",
        "digitone",
        "syntakt",
        "octatrack",
        # ``rytm`` is the short alias for ``analog_rytm`` used by codex's
        # dual-machine cascade; treat it as a device-family package too.
        "rytm",
        # ``essence/`` is the misnamed Rytm engine internals subpackage
        # (per the architecture review) -- listed here so it cannot
        # silently grow into a parallel device surface.
        "essence",
    }
)


# ---------------------------------------------------------------------------
# Allowlists. Empty today; each entry below would document a deferred
# migration target. Adding a new entry REQUIRES explicit reviewer approval
# in the PR body. The long-term state is an empty allowlist.
# ---------------------------------------------------------------------------

# Device-family subpackages that exist but do NOT yet register with the
# registry. Format: ``"<package_name>"``.
_KNOWN_LEGACY_UNREGISTERED_FAMILIES: Final[frozenset[str]] = frozenset()

# Cross-family private-API imports (``from ..<other_family>...`` patterns).
# Format: ``"<importing_module_relpath>:<imported_symbol>"``.
_KNOWN_LEGACY_CROSS_FAMILY_PRIVATE_IMPORTS: Final[frozenset[str]] = frozenset()

# ``dual_machine/`` modules that import directly from a device family
# (instead of going through the registry). Format: ``"<importing_relpath>"``.
_KNOWN_LEGACY_DUAL_MACHINE_DIRECT_IMPORTS: Final[frozenset[str]] = frozenset()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _all_package_files() -> list[Path]:
    """Every ``.py`` file under ``rytm_randomizer/``."""

    return sorted(PACKAGE_ROOT.rglob("*.py"))


def _relpath(path: Path) -> str:
    """Return a forward-slash relpath of ``path`` from PROJECT_ROOT."""

    return str(path.relative_to(PROJECT_ROOT)).replace("\\", "/")


def _top_level_package(rel: str) -> str | None:
    """Return the first segment after ``rytm_randomizer/`` or ``None``.

    ``rytm_randomizer/analog_four/x.py`` -> ``"analog_four"``.
    ``rytm_randomizer/x.py`` -> ``None`` (top-level file, not a subpackage).
    """

    parts = rel.split("/")
    if len(parts) < 3 or parts[0] != "rytm_randomizer":
        return None
    return parts[1]


def _is_device_family_subpackage(top: str | None) -> bool:
    """``True`` if ``top`` names a device-family subpackage."""

    return top is not None and top in _DEVICE_FAMILY_PACKAGE_NAMES


# ---------------------------------------------------------------------------
# Test 1: every device-family subpackage routes through devices/ registry
# ---------------------------------------------------------------------------


def test_every_device_family_subpackage_registers_with_devices_registry() -> None:
    """If a subpackage's name matches a known device family, the family's
    ``__init__.py`` (or one of its modules) must call
    ``rytm_randomizer.devices.registry.register_device``.

    The check is purely textual (``register_device(`` literal substring) so
    it stays cheap and works for both eager and lazy registration patterns.
    The point is mechanical pressure: a contributor adding a new device
    family must either (a) wire it through the registry, or (b) get an
    explicit allowlist entry approved.
    """

    violations: list[str] = []
    for top in sorted(_DEVICE_FAMILY_PACKAGE_NAMES):
        subpkg = PACKAGE_ROOT / top
        if not subpkg.is_dir():
            # Family does not exist on this branch — that's fine.
            continue
        if top in _KNOWN_LEGACY_UNREGISTERED_FAMILIES:
            continue
        registers = False
        for path in subpkg.rglob("*.py"):
            text = path.read_text(encoding="utf-8")
            if "register_device(" in text:
                registers = True
                break
        if not registers:
            violations.append(top)

    assert not violations, (
        "Device-family subpackages must register with the canonical "
        "registry at ``rytm_randomizer.devices.registry``. The "
        "following families exist on disk but never call "
        "``register_device(...)``:\n  "
        + "\n  ".join(violations)
        + "\n\nFix: in the subpackage's ``__init__.py`` (or a module it "
        "imports at top level), construct a Device-conforming instance "
        "and call ``register_device(my_device)`` at import time. See "
        "``rytm_randomizer/devices/analog_rytm.py`` for the reference "
        "implementation."
    )


# ---------------------------------------------------------------------------
# Test 2: no cross-family private-API imports
# ---------------------------------------------------------------------------


def _iter_imports(tree: ast.AST) -> list[tuple[str | None, str, int]]:
    """Yield ``(from_module, imported_name, lineno)`` triples for every
    import statement in ``tree``.

    ``from_module`` is ``None`` for plain ``import x`` (we only flag
    cross-family imports via ``from`` statements; bare ``import x``
    cross-family is fine because it never reaches a private symbol).
    """

    out: list[tuple[str | None, str, int]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            module = node.module or ""
            # Relative imports: ``from ..analog_four.snapshot_decoder import _x``
            # has node.level >= 1 and node.module="analog_four.snapshot_decoder".
            # Absolute imports: ``from rytm_randomizer.analog_four.snapshot_decoder import _x``.
            for alias in node.names:
                out.append((module, alias.name, node.lineno))
    return out


def test_no_cross_family_private_api_imports() -> None:
    """A device family must NOT import private symbols (``_foo``,
    ``_BAR``) from a sibling device family. Cross-family coupling must go
    through the public ``devices/`` registry surface.

    This was a real finding in the dual-machine cascade
    (``analog_four/controlled_diff.py`` reached into
    ``snapshot/rytm_decoder.py`` privates). The fix is to expose the
    shared functionality as a public symbol of a shared module (e.g.
    ``snapshot/elektron_envelope.py``), not to keep poking private API.
    """

    violations: list[str] = []
    for path in _all_package_files():
        rel = _relpath(path)
        top = _top_level_package(rel)
        if not _is_device_family_subpackage(top):
            continue
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except SyntaxError:
            continue
        for from_module, name, lineno in _iter_imports(tree):
            if from_module is None or not name.startswith("_"):
                continue
            # Detect a sibling device family in the from_module path.
            for sibling in _DEVICE_FAMILY_PACKAGE_NAMES:
                if sibling == top:
                    continue
                # Match both relative (``analog_four.snapshot_decoder``)
                # and absolute (``rytm_randomizer.analog_four.snapshot_decoder``).
                module_parts = from_module.split(".")
                if sibling in module_parts:
                    key = f"{rel}:{name}"
                    if key in _KNOWN_LEGACY_CROSS_FAMILY_PRIVATE_IMPORTS:
                        break
                    violations.append(f"{rel}:{lineno} imports {name!r} from {from_module!r}")
                    break

    assert not violations, (
        "Device-family subpackages must not import private symbols from "
        "sibling families. Cross-family coupling goes through the "
        "``devices/`` registry; shared helpers go into a neutral module "
        "(``snapshot/elektron_envelope.py``, ``core/...``).\n\n"
        "Offending imports:\n  " + "\n  ".join(violations)
    )


# ---------------------------------------------------------------------------
# Test 3: dual_machine/ depends only on devices/, not on concrete families
# ---------------------------------------------------------------------------


def test_dual_machine_does_not_import_concrete_device_families() -> None:
    """``dual_machine/`` is the shared orchestrator layer. It must consume
    devices through ``Mapping[str, Device]`` (from
    ``devices.all_devices()``), not by importing each device family
    directly.

    Adding a fourth machine family (Syntakt, Digitone, ...) must NOT
    require any edit under ``dual_machine/``. The way you guarantee that
    is by forbidding direct device-family imports here.

    Allowed: ``from ..devices import all_devices, get_device, Device``.
    Forbidden: ``from ..analog_four import ...``,
    ``from ..rytm import ...``, ``from ..essence import ...``.
    """

    dual_machine = PACKAGE_ROOT / "dual_machine"
    if not dual_machine.is_dir():
        pytest.skip("dual_machine/ does not exist on this branch")

    violations: list[str] = []
    for path in dual_machine.rglob("*.py"):
        rel = _relpath(path)
        if rel in _KNOWN_LEGACY_DUAL_MACHINE_DIRECT_IMPORTS:
            continue
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except SyntaxError:
            continue
        for from_module, _name, lineno in _iter_imports(tree):
            if from_module is None:
                continue
            module_parts = from_module.split(".")
            for family in _DEVICE_FAMILY_PACKAGE_NAMES:
                if family in module_parts:
                    violations.append(
                        f"{rel}:{lineno} imports from {from_module!r} "
                        f"(family={family!r}) -- use devices.get_device({family!r}) instead"
                    )
                    break

    assert not violations, (
        "``dual_machine/`` must depend only on the ``devices/`` registry "
        "surface, not on concrete device families. Adding a new family "
        "must not require touching dual_machine/.\n\n"
        "Offending imports:\n  " + "\n  ".join(violations)
    )


# ---------------------------------------------------------------------------
# Test 4: every registered device satisfies the Protocol at import time
# ---------------------------------------------------------------------------


def test_every_registered_device_satisfies_device_protocol() -> None:
    """Importing ``rytm_randomizer.devices`` triggers each family's
    ``register_device(...)`` call. After that, every entry in
    ``all_devices()`` must pass ``isinstance(dev, Device)``.

    Because ``Device`` is ``@runtime_checkable``, isinstance is the
    structural check the type system would also enforce: missing methods
    or mistyped attributes fail loudly here at import time, not at first
    use.
    """

    from rytm_randomizer.devices import Device, all_devices

    devices = all_devices()
    assert devices, (
        "The device registry is empty after importing "
        "``rytm_randomizer.devices``. At least one concrete device must "
        "register at import time (today: ``AnalogRytmDevice``). If you "
        "see this, the registration side effect was removed or moved to "
        "a non-imported module."
    )

    failures: list[str] = []
    for device_id, device in devices.items():
        if not isinstance(device, Device):
            failures.append(
                f"{device_id!r} ({type(device).__name__}) does not satisfy " "the Device protocol"
            )

    assert not failures, (
        "Registered devices that fail the structural Device check:\n  "
        + "\n  ".join(failures)
        + "\n\nFix: add or correct the missing attribute / method on the "
        "concrete class. Required attributes: device_id, display_name, "
        "default_midi_channel, track_count, sysex_manufacturer_id, "
        "snapshot_decoder, mutation_planner, message_renderer, "
        "report_header. Required methods: decode_snapshot, plan_mutation, "
        "to_mock_messages, to_cc_messages."
    )


# ---------------------------------------------------------------------------
# Test 5: only one registry exists. No parallel registries / lookup tables
# ---------------------------------------------------------------------------


_DEVICE_REGISTRY_EXEMPT_PATHS: Final[frozenset[str]] = frozenset(
    {
        # The canonical registry itself.
        "rytm_randomizer/devices/registry.py",
        # cli_registry.py is the CLI-command registry, a different concern.
        "rytm_randomizer/cli_registry.py",
        # The pad-mode / scene / state registries are not device registries.
        "rytm_randomizer/state/anchor.py",
        "rytm_randomizer/state/group.py",
        "rytm_randomizer/state/pad_mode.py",
        "rytm_randomizer/state/scene.py",
        "rytm_randomizer/state/selection.py",
        # The reports registry index (build a list of reports).
        "rytm_randomizer/reports/__init__.py",
        # The shell command-dispatch table at ``shell.py``.
        "rytm_randomizer/shell.py",
        # registry.py at top level: the existing operator-side registry
        # for V1.34 commands (not a Device registry).
        "rytm_randomizer/registry.py",
    }
)


def test_no_parallel_device_registry() -> None:
    """Only ``rytm_randomizer.devices.registry`` may define a device
    registry. A second registry would split the source of truth.

    The check rejects modules that define BOTH:
      * a module-level mutable dict / list named ``_DEVICES`` /
        ``_REGISTRY`` / ``DEVICES`` / ``REGISTRY`` (case-insensitive),
        AND
      * a function literally named ``register_device``.

    Exempt: ``devices/registry.py`` itself, plus the unrelated registries
    (state, cli, reports) enumerated in ``_DEVICE_REGISTRY_EXEMPT_PATHS``.
    """

    violations: list[str] = []
    for path in _all_package_files():
        rel = _relpath(path)
        if rel in _DEVICE_REGISTRY_EXEMPT_PATHS:
            continue
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except SyntaxError:
            continue
        has_register_device = False
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == "register_device":
                has_register_device = True
                break
        if not has_register_device:
            continue
        # A function literally named register_device exists outside the
        # canonical module -- that's the smell.
        violations.append(f"{rel} defines ``register_device`` outside ``devices/registry.py``")

    assert not violations, (
        "Only ``rytm_randomizer.devices.registry`` may define "
        "``register_device``. Adding a parallel registry splits the "
        "source-of-truth contract.\n\nOffenders:\n  " + "\n  ".join(violations)
    )


# ---------------------------------------------------------------------------
# Test 6: snapshot decoder / planner / mock_runtime Protocols are NOT
# bypassed by concrete per-device modules under sibling subpackages
# ---------------------------------------------------------------------------


_SNAPSHOT_CAPABILITY_PROTOCOLS: Final[tuple[str, ...]] = (
    "SnapshotDecoder",
    "MutationPlanner",
    "SnapshotMockRuntime",
)


def test_snapshot_capabilities_route_through_protocol_module() -> None:
    """The WS-S6 Protocols at ``snapshot/decoder.py``, ``snapshot/planner.py``,
    ``snapshot/mock_runtime.py`` exist specifically to be implemented per
    device. Per-device implementations must reference these Protocols (so
    structural conformance is documented at the type level), even when
    the implementation does not inherit from them.

    A module is considered to "route through" the Protocol module if it
    imports any of ``SnapshotDecoder`` / ``MutationPlanner`` /
    ``SnapshotMockRuntime`` from ``rytm_randomizer.snapshot``.

    This test currently warns rather than fails (the per-device decoder
    bodies on the open codex cascade do not yet declare conformance).
    Tighten by adding the offending file to the failure list once the
    migration lands.
    """

    snapshot_pkg = PACKAGE_ROOT / "snapshot"
    if not snapshot_pkg.is_dir():
        pytest.skip("snapshot/ does not exist")

    # Discover modules that LOOK like per-device snapshot impls by
    # filename: ``*_decoder.py``, ``*_mutation_planner.py``,
    # ``*_mock_runtime.py`` under a device-family subpackage.
    candidates: list[Path] = []
    for top in sorted(_DEVICE_FAMILY_PACKAGE_NAMES):
        subpkg = PACKAGE_ROOT / top
        if not subpkg.is_dir():
            continue
        for suffix in ("decoder.py", "mutation_planner.py", "mock_runtime.py"):
            for path in subpkg.rglob(f"*{suffix}"):
                candidates.append(path)

    missing_conformance: list[str] = []
    for path in candidates:
        rel = _relpath(path)
        text = path.read_text(encoding="utf-8")
        if not any(name in text for name in _SNAPSHOT_CAPABILITY_PROTOCOLS):
            missing_conformance.append(rel)

    # Informational stderr only; the assertion is "no NEW per-device
    # decoder bypasses the Protocol surface" once the allowlist is
    # introduced. For now, the test stays green: it documents the gap.
    if missing_conformance:
        import sys

        sys.stderr.write(
            "[architecture] WS-S6 Protocol-conformance gap: "
            f"{len(missing_conformance)} per-device decoder/planner/runtime "
            "modules do not reference any of "
            f"{_SNAPSHOT_CAPABILITY_PROTOCOLS!r}:\n  " + "\n  ".join(missing_conformance) + "\n"
        )


# ---------------------------------------------------------------------------
# Test 7: the canonical Device Protocol is importable and has the expected
# attribute surface (defends against accidental Protocol-shape changes)
# ---------------------------------------------------------------------------


_EXPECTED_DEVICE_ATTRIBUTES: Final[tuple[str, ...]] = (
    # Identity / hardware-config attributes.
    "device_id",
    "display_name",
    "default_midi_channel",
    "track_count",
    "sysex_manufacturer_id",
    # Strategy capabilities (Strategy pattern). Every Device must wire its
    # own implementation of each. The three Protocol shapes are checked
    # by ``test_every_registered_device_satisfies_device_protocol``.
    "snapshot_decoder",
    "mutation_planner",
    "message_renderer",
    # Operator-facing report header used by guarded / hardware senders.
    "report_header",
)

_EXPECTED_DEVICE_PROPERTIES: Final[tuple[str, ...]] = (
    "device_id",
    "display_name",
    "default_midi_channel",
    "track_count",
    "sysex_manufacturer_id",
    "report_header",
    "snapshot_decoder",
    "mutation_planner",
    "message_renderer",
)

_EXPECTED_DEVICE_METHODS: Final[tuple[str, ...]] = (
    "decode_snapshot",
    "plan_mutation",
    "to_mock_messages",
    "to_cc_messages",
)


def test_device_protocol_surface_is_stable() -> None:
    """The ``Device`` Protocol's attribute and method surface is a public
    contract. This test pins the surface so a future edit cannot silently
    rename / remove a capability without updating both the Protocol AND
    this test in the same change set.
    """

    devices_mod = importlib.import_module("rytm_randomizer.devices")
    Device = devices_mod.Device  # noqa: N806 - mirroring the class name

    annotations = get_type_hints(Device, include_extras=True)
    missing_attrs = [
        name
        for name in _EXPECTED_DEVICE_ATTRIBUTES
        if name not in annotations and not hasattr(Device, name)
    ]
    assert not missing_attrs, (
        f"Device Protocol is missing expected attributes: {missing_attrs}. "
        "If you intentionally renamed or removed one, update "
        "_EXPECTED_DEVICE_ATTRIBUTES in this test in the same change set."
    )

    non_properties = [
        name
        for name in _EXPECTED_DEVICE_PROPERTIES
        if not isinstance(getattr(Device, name, None), property)
    ]
    assert (
        not non_properties
    ), f"Device Protocol metadata and strategies must remain read-only: {non_properties}."

    missing_methods = [
        m for m in _EXPECTED_DEVICE_METHODS if not callable(getattr(Device, m, None))
    ]
    assert not missing_methods, (
        f"Device Protocol is missing expected methods: {missing_methods}. "
        "If you intentionally renamed or removed one, update "
        "_EXPECTED_DEVICE_METHODS in this test in the same change set."
    )
