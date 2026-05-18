"""Enforce the dependency-direction rules from ``docs/ARCHITECTURE.md``.

These tests parse every ``rytm_randomizer/`` module with ``ast`` and assert
that its top-level imports respect the layered architecture. The rules
mirror :ref:`section 3 of docs/ARCHITECTURE.md` one-for-one.

If a rule changes, change ``docs/ARCHITECTURE.md`` first, then update the
corresponding test below.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

# WS-M4: mark this module as fast-suite; pytest -m fast skips the 505
# warm-worker V1.34 parity fixtures and runs in <60s.
pytestmark = pytest.mark.fast

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PACKAGE_ROOT = PROJECT_ROOT / "rytm_randomizer"
PACKAGE_NAME = "rytm_randomizer"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _module_name(path: Path) -> tuple[str, bool]:
    """Return ``(fq_name, is_init)`` for ``path``.

    ``fq_name`` is the dotted module name. ``is_init`` indicates whether the
    path is an ``__init__.py`` (the module IS its package, which changes how
    relative imports resolve).
    """

    rel = path.relative_to(PROJECT_ROOT).with_suffix("")
    parts = rel.parts
    is_init = parts[-1] == "__init__"
    if is_init:
        parts = parts[:-1]
    return ".".join(parts), is_init


def _iter_package_files() -> list[Path]:
    return sorted(p for p in PACKAGE_ROOT.rglob("*.py"))


def _resolve_import(node: ast.ImportFrom, module_name: str, is_init: bool) -> str | None:
    """Resolve a relative ``from .x import ...`` to its absolute name.

    Returns ``None`` for absolute imports outside ``rytm_randomizer``.

    For an ``__init__.py``, the module name IS the package; relative imports
    resolve against ``module_name`` directly. For a regular module
    ``pkg.sub.mod``, ``from .`` resolves against ``pkg.sub``.
    """

    if node.level == 0:
        # Absolute import. Return as-is if it begins with our package name.
        if node.module and (
            node.module == PACKAGE_NAME or node.module.startswith(PACKAGE_NAME + ".")
        ):
            return node.module
        return None

    # Relative import. Compute the package the import is relative to.
    base_parts = module_name.split(".") if module_name else []
    # For ``__init__.py``, level=1 means "this package". For a regular
    # module, level=1 means "the package this module is in".
    drop = node.level - 1 if is_init else node.level
    if drop:
        base_parts = base_parts[: max(0, len(base_parts) - drop)]
    tail = node.module.split(".") if node.module else []
    resolved_parts = base_parts + tail
    return ".".join(p for p in resolved_parts if p)


def _imported_package_modules(path: Path) -> list[tuple[int, str]]:
    """Return the ``(lineno, fqname)`` of every package-internal import in ``path``."""

    src = path.read_text(encoding="utf-8")
    tree = ast.parse(src, filename=str(path))
    mod, is_init = _module_name(path)
    out: list[tuple[int, str]] = []
    for node in tree.body:
        if isinstance(node, ast.Import):
            for n in node.names:
                if n.name == PACKAGE_NAME or n.name.startswith(PACKAGE_NAME + "."):
                    out.append((node.lineno, n.name))
        elif isinstance(node, ast.ImportFrom):
            resolved = _resolve_import(node, mod, is_init)
            if resolved and (resolved == PACKAGE_NAME or resolved.startswith(PACKAGE_NAME + ".")):
                out.append((node.lineno, resolved))
    return out


def _all_top_level_import_tokens(path: Path) -> list[str]:
    """Return every top-level imported name (absolute, unresolved) in ``path``."""

    src = path.read_text(encoding="utf-8")
    tree = ast.parse(src, filename=str(path))
    out: list[str] = []
    for node in tree.body:
        if isinstance(node, ast.Import):
            for n in node.names:
                out.append(n.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                out.append(node.module)
    return out


# ---------------------------------------------------------------------------
# Rule 1: data/ is a leaf (no rytm_randomizer.* imports)
# ---------------------------------------------------------------------------


def test_data_layer_does_not_import_from_package() -> None:
    """``rytm_randomizer/data/*`` may import only stdlib + sibling data modules."""

    violations: list[str] = []
    for path in sorted((PACKAGE_ROOT / "data").rglob("*.py")):
        for lineno, fq in _imported_package_modules(path):
            if not fq.startswith(f"{PACKAGE_NAME}.data"):
                violations.append(f"{path.relative_to(PROJECT_ROOT)}:{lineno} imports {fq}")
    assert not violations, (
        "data/ modules must not import from rytm_randomizer (only stdlib + "
        "sibling data modules). Violations:\n  " + "\n  ".join(violations)
    )


# ---------------------------------------------------------------------------
# Rule 2: state/ imports only stdlib (no engines, no runners, no mido)
# ---------------------------------------------------------------------------


def test_state_layer_imports_only_stdlib() -> None:
    """``rytm_randomizer/state/*`` may import only stdlib."""

    forbidden_prefixes = (
        f"{PACKAGE_NAME}.engines",
        f"{PACKAGE_NAME}.scene_runner",
        f"{PACKAGE_NAME}.group_runner",
        f"{PACKAGE_NAME}.shell",
        f"{PACKAGE_NAME}.app",
        f"{PACKAGE_NAME}.cli",
        f"{PACKAGE_NAME}.midi_io",
        f"{PACKAGE_NAME}.randomization",
        f"{PACKAGE_NAME}.mido_provider",
        f"{PACKAGE_NAME}.real_midi_adapter",
        "mido",
        "rtmidi",
    )
    # WS-M2: the inert-validation modules (anchor_validation,
    # selected_target_validation, selected_isolated_pad_validation) were
    # relocated from top-level. They import the passive command-surface
    # data from ``rytm_randomizer.commands`` -- a frozen, side-effect-free
    # data module. This is the same import they had before the relocation;
    # explicitly allow it.
    allowed_extra: dict[str, frozenset[str]] = {
        "state/anchor_validation.py": frozenset({f"{PACKAGE_NAME}.commands"}),
        "state/selected_target_validation.py": frozenset({f"{PACKAGE_NAME}.commands"}),
        "state/selected_isolated_pad_validation.py": frozenset({f"{PACKAGE_NAME}.commands"}),
    }
    violations: list[str] = []
    for path in sorted((PACKAGE_ROOT / "state").rglob("*.py")):
        rel = path.relative_to(PACKAGE_ROOT).as_posix()
        per_file_allowed = allowed_extra.get(rel, frozenset())
        # Allow ``from . import x`` / ``from .scene import ...`` within state/.
        for lineno, fq in _imported_package_modules(path):
            if fq.startswith(f"{PACKAGE_NAME}.state"):
                continue
            if fq in per_file_allowed:
                continue
            violations.append(f"{path.relative_to(PROJECT_ROOT)}:{lineno} imports package {fq}")
        for token in _all_top_level_import_tokens(path):
            if any(token == p or token.startswith(p + ".") for p in forbidden_prefixes):
                violations.append(
                    f"{path.relative_to(PROJECT_ROOT)} imports forbidden token {token}"
                )
    assert not violations, (
        "state/ modules may import stdlib + sibling state modules only. "
        "Violations:\n  " + "\n  ".join(violations)
    )


# ---------------------------------------------------------------------------
# Rule 3: engines/ may not import cli/shell/app/runners/mido_provider
# ---------------------------------------------------------------------------


def test_engines_do_not_import_upper_layers() -> None:
    forbidden_prefixes = (
        f"{PACKAGE_NAME}.cli",
        f"{PACKAGE_NAME}.shell",
        f"{PACKAGE_NAME}.app",
        f"{PACKAGE_NAME}.scene_runner",
        f"{PACKAGE_NAME}.group_runner",
        f"{PACKAGE_NAME}.mido_provider",
    )
    violations: list[str] = []
    for path in sorted((PACKAGE_ROOT / "engines").rglob("*.py")):
        for lineno, fq in _imported_package_modules(path):
            if any(fq == p or fq.startswith(p + ".") for p in forbidden_prefixes):
                violations.append(f"{path.relative_to(PROJECT_ROOT)}:{lineno} imports {fq}")
    assert not violations, (
        "engines/* may import data + state + midi_io + randomization + "
        "mock_midi only. Violations:\n  " + "\n  ".join(violations)
    )


# ---------------------------------------------------------------------------
# Rule 4: scene_runner / group_runner may not import cli/shell/app
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("module_path", ["scene_runner.py", "group_runner.py"])
def test_runners_do_not_import_upper_layers(module_path: str) -> None:
    forbidden_prefixes = (
        f"{PACKAGE_NAME}.cli",
        f"{PACKAGE_NAME}.shell",
        f"{PACKAGE_NAME}.app",
    )
    path = PACKAGE_ROOT / module_path
    violations: list[str] = []
    for lineno, fq in _imported_package_modules(path):
        if any(fq == p or fq.startswith(p + ".") for p in forbidden_prefixes):
            violations.append(f"{path.relative_to(PROJECT_ROOT)}:{lineno} imports {fq}")
    assert (
        not violations
    ), f"{module_path} must not import cli/shell/app. Violations:\n  " + "\n  ".join(violations)


# ---------------------------------------------------------------------------
# Rule 5: shell.py must not import app or cli
# ---------------------------------------------------------------------------


def test_shell_does_not_import_app_or_cli() -> None:
    forbidden = (f"{PACKAGE_NAME}.app", f"{PACKAGE_NAME}.cli")
    path = PACKAGE_ROOT / "shell.py"
    violations: list[str] = []
    for lineno, fq in _imported_package_modules(path):
        if fq in forbidden:
            violations.append(f"{path.relative_to(PROJECT_ROOT)}:{lineno} imports {fq}")
    assert not violations, (
        "shell.py must not import app or cli (it is below them in the layered "
        "graph). Violations:\n  " + "\n  ".join(violations)
    )


# ---------------------------------------------------------------------------
# Rule 6: nothing in the package imports app
# ---------------------------------------------------------------------------


def test_nothing_in_package_imports_app() -> None:
    violations: list[str] = []
    for path in _iter_package_files():
        if path == PACKAGE_ROOT / "app.py":
            continue
        for lineno, fq in _imported_package_modules(path):
            if fq == f"{PACKAGE_NAME}.app":
                violations.append(f"{path.relative_to(PROJECT_ROOT)}:{lineno} imports {fq}")
    assert not violations, (
        "app.py is the top of the layered graph -- no other module may import "
        "it. Violations:\n  " + "\n  ".join(violations)
    )


# ---------------------------------------------------------------------------
# Rule 7: cli.py is passive -- no mido, no engines, no shell, no app, no runners
# ---------------------------------------------------------------------------


def test_cli_is_passive() -> None:
    """``cli.py`` is the passive entry point: NO real MIDI, NO engines, NO shell."""

    path = PACKAGE_ROOT / "cli.py"
    forbidden_fq = {
        f"{PACKAGE_NAME}.shell",
        f"{PACKAGE_NAME}.app",
        f"{PACKAGE_NAME}.scene_runner",
        f"{PACKAGE_NAME}.group_runner",
        f"{PACKAGE_NAME}.midi_io",
        f"{PACKAGE_NAME}.randomization",
        f"{PACKAGE_NAME}.real_midi_adapter",
        f"{PACKAGE_NAME}.mido_provider",
    }
    forbidden_prefix = (f"{PACKAGE_NAME}.engines",)
    forbidden_external = ("mido", "rtmidi")

    package_violations: list[str] = []
    for lineno, fq in _imported_package_modules(path):
        if fq in forbidden_fq or any(fq.startswith(p + ".") or fq == p for p in forbidden_prefix):
            package_violations.append(f"{path.relative_to(PROJECT_ROOT)}:{lineno} imports {fq}")

    external_violations: list[str] = []
    for token in _all_top_level_import_tokens(path):
        if any(token == p or token.startswith(p + ".") for p in forbidden_external):
            external_violations.append(
                f"{path.relative_to(PROJECT_ROOT)} imports {token} (passive CLI must not pull real MIDI)"
            )

    all_violations = package_violations + external_violations
    assert not all_violations, (
        "cli.py must remain passive: no mido / mido_provider / engines / shell "
        "/ app / runners / midi_io / randomization. Violations:\n  " + "\n  ".join(all_violations)
    )


# ---------------------------------------------------------------------------
# Rule 8: no package module imports the retired V1.34 monolith
# ---------------------------------------------------------------------------


def test_no_package_module_imports_monolith() -> None:
    """The V1.34 monolith has been retired.

    Its reference behavior lives as JSON goldens under
    ``tests/fixtures/v134_parity/``. No package module may import it (whether
    the name happens to resolve to a leftover file or not), and no test
    helper may either -- ``app.py`` is allowed to *look up* the name in
    ``sys.modules`` as a test seam, but it never imports.
    """

    monolith_name = "rytm_hybrid_randomizer_v134"
    violations: list[str] = []
    for path in _iter_package_files():
        for token in _all_top_level_import_tokens(path):
            if token == monolith_name or token.startswith(monolith_name + "."):
                violations.append(
                    f"{path.relative_to(PROJECT_ROOT)} imports {token} "
                    "(the V1.34 monolith was retired; use the JSON goldens "
                    "under tests/fixtures/v134_parity/)"
                )
    assert not violations, "\n  " + "\n  ".join(violations)


# ---------------------------------------------------------------------------
# Rule 9: no eager `import mido` / `from mido` anywhere in the package
# ---------------------------------------------------------------------------


def test_no_eager_mido_import_in_package() -> None:
    """``mido`` must be lazy -- never at module top level in the package."""

    violations: list[str] = []
    for path in _iter_package_files():
        for token in _all_top_level_import_tokens(path):
            if token == "mido" or token.startswith("mido."):
                violations.append(
                    f"{path.relative_to(PROJECT_ROOT)} has eager `import {token}` "
                    "(mido must be lazy and imported inside methods)"
                )
            if token == "rtmidi" or token.startswith("rtmidi."):
                violations.append(
                    f"{path.relative_to(PROJECT_ROOT)} has eager `import {token}` "
                    "(rtmidi must not be imported at module load time)"
                )
    assert not violations, "\n  " + "\n  ".join(violations)


if __name__ == "__main__":
    test_data_layer_does_not_import_from_package()
    test_state_layer_imports_only_stdlib()
    test_engines_do_not_import_upper_layers()
    for mod in ("scene_runner.py", "group_runner.py"):
        test_runners_do_not_import_upper_layers(mod)
    test_shell_does_not_import_app_or_cli()
    test_nothing_in_package_imports_app()
    test_cli_is_passive()
    test_no_package_module_imports_monolith()
    test_no_eager_mido_import_in_package()
