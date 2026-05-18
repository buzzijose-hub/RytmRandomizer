"""Enforce the house-style rules from ``docs/ARCHITECTURE.md`` section 4.

Rules checked here:

1. **Frozen dataclasses.** Every ``@dataclass`` in ``state/`` is
   ``frozen=True``. DTOs in the architectural core (``midi_io.py``,
   ``randomization.py``, ``real_midi_adapter.py``, ``mock_midi.py``,
   ``shell.py``) are likewise ``frozen=True``.

2. **Type annotations on public signatures.** Every public (non-underscore)
   function / method in the architectural core has type annotations on all
   parameters and a return annotation. The "architectural core" is defined
   below as ``_HOUSE_STYLE_SCOPE`` and covers ``state/``, ``data/``,
   ``engines/``, plus the runtime files (``app``, ``midi_io``,
   ``randomization``, ``mock_midi``, ``real_midi_adapter``,
   ``mido_provider``, ``group_runner``, ``scene_runner``, ``shell``). The
   legacy passive-report / behavior-* modules are out of scope until WS-U.

3. **No module-level mutable globals in the architectural core.** In
   ``state/`` and the runtime core, module-level assignments must be
   constants. ``__all__`` (list) and any ``UPPER_SNAKE_NAME`` (treated as a
   constant by convention) are allow-listed; anything else that is a plain
   ``dict`` / ``list`` / ``set`` literal at module scope is rejected.
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


# The architectural core that house-style rules apply to. The legacy
# behavior_* / passive report modules (``cli.py``, ``reports.py``,
# ``inspection.py``, ``behavior_*``, ``commands.py``, ``profiles.py``,
# ``scenes.py``, ``constants.py``, etc.) are out of scope -- they predate
# the current standard.
_HOUSE_STYLE_CORE_FILES: tuple[str, ...] = (
    "app.py",
    "midi_io.py",
    "randomization.py",
    "mock_midi.py",
    "real_midi_adapter.py",
    "mido_provider.py",
    "group_runner.py",
    "scene_runner.py",
    "shell.py",
)


def _house_style_scope() -> list[Path]:
    """Return the files that house-style rules apply to."""

    files: list[Path] = []
    for name in _HOUSE_STYLE_CORE_FILES:
        p = PACKAGE_ROOT / name
        if p.exists():
            files.append(p)
    for sub in ("state", "data", "engines"):
        files.extend(sorted((PACKAGE_ROOT / sub).rglob("*.py")))
    return sorted(files)


def _all_state_dataclasses() -> list[Path]:
    return sorted((PACKAGE_ROOT / "state").rglob("*.py"))


def _dataclass_decorator_is_frozen(deco: ast.expr) -> bool:
    """Return True if ``deco`` is a ``@dataclass(frozen=True)`` call."""

    if not isinstance(deco, ast.Call):
        return False
    # Identify the underlying name ('dataclass' or '<x>.dataclass').
    name = None
    if isinstance(deco.func, ast.Name):
        name = deco.func.id
    elif isinstance(deco.func, ast.Attribute):
        name = deco.func.attr
    if name != "dataclass":
        return False
    for kw in deco.keywords:
        if kw.arg == "frozen" and isinstance(kw.value, ast.Constant) and kw.value.value is True:
            return True
    return False


def _is_plain_dataclass_decorator(deco: ast.expr) -> bool:
    """Return True if the decorator is ``@dataclass`` (no args) or a Call.

    We use this to spot dataclasses that are NOT explicitly frozen.
    """

    if isinstance(deco, ast.Name) and deco.id == "dataclass":
        return True
    if isinstance(deco, ast.Attribute) and deco.attr == "dataclass":
        return True
    if isinstance(deco, ast.Call):
        if isinstance(deco.func, ast.Name) and deco.func.id == "dataclass":
            return True
        if isinstance(deco.func, ast.Attribute) and deco.func.attr == "dataclass":
            return True
    return False


# ---------------------------------------------------------------------------
# Rule 1: every state/* @dataclass is frozen=True
# ---------------------------------------------------------------------------


def test_every_state_dataclass_is_frozen() -> None:
    """Every ``@dataclass`` under ``rytm_randomizer/state/`` must be frozen."""

    violations: list[str] = []
    for path in _all_state_dataclasses():
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                for deco in node.decorator_list:
                    if not _is_plain_dataclass_decorator(deco):
                        continue
                    if not _dataclass_decorator_is_frozen(deco):
                        violations.append(
                            f"{path.relative_to(PROJECT_ROOT)}:{node.lineno} "
                            f"class {node.name} -- @dataclass must be frozen=True"
                        )
    assert not violations, "\n  " + "\n  ".join(violations)


# ---------------------------------------------------------------------------
# Rule 1b: DTOs in the runtime core are frozen
# ---------------------------------------------------------------------------


_CORE_DTO_FILES: tuple[str, ...] = (
    "midi_io.py",
    "randomization.py",
    "real_midi_adapter.py",
    "mock_midi.py",
    "shell.py",
)


def test_core_dtos_are_frozen() -> None:
    """``@dataclass`` instances in the runtime core must be frozen."""

    violations: list[str] = []
    for name in _CORE_DTO_FILES:
        path = PACKAGE_ROOT / name
        if not path.exists():
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                for deco in node.decorator_list:
                    if not _is_plain_dataclass_decorator(deco):
                        continue
                    if not _dataclass_decorator_is_frozen(deco):
                        violations.append(
                            f"{path.relative_to(PROJECT_ROOT)}:{node.lineno} "
                            f"class {node.name} -- @dataclass must be frozen=True"
                        )
    assert not violations, "\n  " + "\n  ".join(violations)


# ---------------------------------------------------------------------------
# Rule 2: public functions in the core have type annotations
# ---------------------------------------------------------------------------


def _public_unannotated_signatures(path: Path) -> list[str]:
    src = path.read_text(encoding="utf-8")
    tree = ast.parse(src, filename=str(path))
    out: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        if node.name.startswith("_"):
            continue
        # Skip dunders (their signatures are conventional).
        if node.name.startswith("__") and node.name.endswith("__"):
            continue
        args = node.args
        missing: list[str] = []
        for arg in list(args.args) + list(args.kwonlyargs):
            if arg.annotation is None and arg.arg not in ("self", "cls"):
                missing.append(arg.arg)
        if node.returns is None:
            missing.append("->return")
        if missing:
            out.append(
                f"{path.relative_to(PROJECT_ROOT)}:{node.lineno} "
                f"{node.name}({', '.join(missing)})"
            )
    return out


@pytest.mark.parametrize(
    "path", _house_style_scope(), ids=lambda p: str(p.relative_to(PROJECT_ROOT))
)
def test_public_signatures_are_annotated_in_core(path: Path) -> None:
    """Every public function in the architectural core has type annotations."""

    issues = _public_unannotated_signatures(path)
    assert not issues, (
        "Missing type annotations on public signatures in the architectural "
        "core (see docs/ARCHITECTURE.md section 4):\n  " + "\n  ".join(issues)
    )


# ---------------------------------------------------------------------------
# Rule 3: no module-level mutable globals in the architectural core
# ---------------------------------------------------------------------------


def _module_level_mutable_globals(path: Path) -> list[str]:
    src = path.read_text(encoding="utf-8")
    tree = ast.parse(src, filename=str(path))
    out: list[str] = []
    for node in tree.body:
        if not isinstance(node, (ast.Assign, ast.AnnAssign)):
            continue
        if isinstance(node, ast.Assign):
            targets = [t for t in node.targets if isinstance(t, ast.Name)]
            value = node.value
        else:  # AnnAssign
            if not isinstance(node.target, ast.Name):
                continue
            targets = [node.target]
            value = node.value
        if value is None:
            continue
        for tgt in targets:
            # __all__ list is conventional and allowed.
            if tgt.id == "__all__":
                continue
            # UPPER_SNAKE_NAME is conventionally a constant (the table-of-
            # facts data layer uses this; we trust the convention).
            if tgt.id.isupper():
                continue
            # Allow names that consist of UPPER_SNAKE with leading underscore
            # (private constants).
            if tgt.id.startswith("_") and tgt.id.lstrip("_").isupper():
                continue
            # Detect mutable literals / calls.
            if isinstance(value, (ast.Dict, ast.List, ast.Set)):
                out.append(
                    f"{path.relative_to(PROJECT_ROOT)}:{node.lineno} "
                    f"{tgt.id} = <{type(value).__name__}>"
                )
            elif (
                isinstance(value, ast.Call)
                and isinstance(value.func, ast.Name)
                and value.func.id in {"dict", "list", "set"}
            ):
                out.append(
                    f"{path.relative_to(PROJECT_ROOT)}:{node.lineno} "
                    f"{tgt.id} = {value.func.id}()"
                )
    return out


@pytest.mark.parametrize(
    "path", _house_style_scope(), ids=lambda p: str(p.relative_to(PROJECT_ROOT))
)
def test_no_module_level_mutable_globals_in_core(path: Path) -> None:
    """Architectural core may not declare module-level mutable globals.

    Allow-list: ``__all__``, ``UPPER_SNAKE_NAME`` constants (and their
    private ``_UPPER_SNAKE_NAME`` counterparts).
    """

    issues = _module_level_mutable_globals(path)
    assert not issues, (
        "Module-level mutable globals are not allowed in the architectural "
        "core (see docs/ARCHITECTURE.md section 4):\n  " + "\n  ".join(issues)
    )
