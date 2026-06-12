"""Live GUI frontend types must mirror the Python report TypedDict contracts."""

from __future__ import annotations

import ast
import re
from pathlib import Path
from typing import Final

import pytest

pytestmark = pytest.mark.fast

PROJECT_ROOT: Final[Path] = Path(__file__).resolve().parents[2]
LIVE_GUI_PROTOCOL_TS: Final[Path] = (
    PROJECT_ROOT / "desktop" / "web" / "src" / "types" / "live_gui_protocol.ts"
)
LIVE_READINESS_PANEL_TSX: Final[Path] = (
    PROJECT_ROOT / "desktop" / "web" / "src" / "cockpit" / "LiveReadinessPanel.tsx"
)
LIVE_GUI_MODEL_MODULES: Final[tuple[Path, ...]] = (
    PROJECT_ROOT / "rytm_randomizer" / "reports" / "live_gui_12_pad_surface_model.py",
    PROJECT_ROOT / "rytm_randomizer" / "reports" / "live_gui_device_inventory_model.py",
    PROJECT_ROOT / "rytm_randomizer" / "reports" / "live_gui_scene_queue_model.py",
    PROJECT_ROOT / "rytm_randomizer" / "reports" / "live_gui_status_footer_model.py",
    PROJECT_ROOT / "rytm_randomizer" / "reports" / "live_gui_snapshot_history_model.py",
    PROJECT_ROOT / "rytm_randomizer" / "reports" / "live_gui_safety_checklist_model.py",
    PROJECT_ROOT / "rytm_randomizer" / "reports" / "live_gui_command_queue_model.py",
    PROJECT_ROOT / "rytm_randomizer" / "reports" / "live_gui_analyzer_panel_model.py",
    PROJECT_ROOT / "rytm_randomizer" / "reports" / "live_gui_hardware_rail_model.py",
    PROJECT_ROOT / "rytm_randomizer" / "reports" / "live_gui_snapshot_compatibility_model.py",
    PROJECT_ROOT / "rytm_randomizer" / "reports" / "live_gui_dual_device_rig_readiness_model.py",
    PROJECT_ROOT / "rytm_randomizer" / "reports" / "live_gui_performance_flow_model.py",
    PROJECT_ROOT / "rytm_randomizer" / "reports" / "live_gui_performance_console_model.py",
)

_TS_INTERFACE_RE: Final[re.Pattern[str]] = re.compile(
    r"export\s+interface\s+(?P<name>[A-Za-z_][A-Za-z0-9_]*)\s*\{(?P<body>.*?)\n\}",
    re.DOTALL,
)
_TS_FIELD_RE: Final[re.Pattern[str]] = re.compile(
    r"^\s*(?P<name>[A-Za-z_][A-Za-z0-9_]*)\??\s*:",
    re.MULTILINE,
)
_LOCAL_INTERFACE_RE: Final[re.Pattern[str]] = re.compile(
    r"^\s*(?:export\s+)?interface\s+[A-Za-z_][A-Za-z0-9_]*",
    re.MULTILINE,
)


def _class_name(node: ast.expr) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    if isinstance(node, ast.Subscript):
        return _class_name(node.value)
    return ""


def _is_frozen_dataclass(node: ast.ClassDef) -> bool:
    for decorator in node.decorator_list:
        if isinstance(decorator, ast.Call) and _class_name(decorator.func) == "dataclass":
            return any(
                keyword.arg == "frozen"
                and isinstance(keyword.value, ast.Constant)
                and keyword.value.value is True
                for keyword in decorator.keywords
            )
    return False


def _is_typed_dict(node: ast.ClassDef) -> bool:
    return any(_class_name(base) == "TypedDict" for base in node.bases)


def _class_fields(node: ast.ClassDef) -> tuple[str, ...]:
    return tuple(
        statement.target.id
        for statement in node.body
        if isinstance(statement, ast.AnnAssign) and isinstance(statement.target, ast.Name)
    )


def _python_contracts() -> dict[str, tuple[Path, tuple[str, ...]]]:
    contracts: dict[str, tuple[Path, tuple[str, ...]]] = {}
    for source_path in LIVE_GUI_MODEL_MODULES:
        tree = ast.parse(source_path.read_text(encoding="utf-8"), filename=str(source_path))
        classes = {node.name: node for node in tree.body if isinstance(node, ast.ClassDef)}
        typed_dict_fields = {
            node.name: _class_fields(node) for node in classes.values() if _is_typed_dict(node)
        }
        for node in classes.values():
            if not _is_frozen_dataclass(node):
                continue
            dict_name = f"{node.name}Dict"
            assert dict_name in typed_dict_fields, (
                f"{source_path.relative_to(PROJECT_ROOT).as_posix()} defines frozen dataclass "
                f"{node.name} but is missing sibling TypedDict {dict_name}."
            )
            dataclass_fields = _class_fields(node)
            assert typed_dict_fields[dict_name] == dataclass_fields, (
                f"{dict_name} in {source_path.relative_to(PROJECT_ROOT).as_posix()} must "
                f"mirror {node.name} field-for-field. Expected {dataclass_fields!r}, "
                f"got {typed_dict_fields[dict_name]!r}."
            )
            contracts[dict_name] = (source_path, dataclass_fields)
    return contracts


def _ts_interfaces() -> dict[str, tuple[str, ...]]:
    assert LIVE_GUI_PROTOCOL_TS.is_file(), (
        "desktop/web/src/types/live_gui_protocol.ts is required as the single "
        "TypeScript mirror of the Python live_gui_*_model.py TypedDict contracts."
    )
    source = LIVE_GUI_PROTOCOL_TS.read_text(encoding="utf-8")
    return {
        match.group("name"): tuple(_TS_FIELD_RE.findall(match.group("body")))
        for match in _TS_INTERFACE_RE.finditer(source)
    }


def test_live_gui_python_models_define_typed_dict_siblings() -> None:
    """Every frozen live-GUI model dataclass has a same-field TypedDict sibling."""

    contracts = _python_contracts()

    assert contracts, "Expected at least one live GUI Python TypedDict contract."


def test_live_gui_typescript_protocol_mirrors_python_typeddicts() -> None:
    """The shared TS protocol mirrors the Python TypedDict field names exactly."""

    python_contracts = _python_contracts()
    ts_interfaces = _ts_interfaces()

    missing = sorted(set(python_contracts) - set(ts_interfaces))
    assert not missing, (
        "desktop/web/src/types/live_gui_protocol.ts is missing interfaces for "
        f"Python TypedDict contracts: {missing!r}."
    )

    for dict_name, (source_path, python_fields) in python_contracts.items():
        ts_fields = ts_interfaces[dict_name]
        assert ts_fields == python_fields, (
            f"TypeScript interface {dict_name} must mirror "
            f"{source_path.relative_to(PROJECT_ROOT).as_posix()} field order and names. "
            f"Expected {python_fields!r}, got {ts_fields!r}."
        )


def test_live_readiness_panel_imports_shared_protocol_without_local_interfaces() -> None:
    """The consumer imports shared live-GUI types instead of declaring local copies."""

    source = LIVE_READINESS_PANEL_TSX.read_text(encoding="utf-8")

    assert "../types/live_gui_protocol" in source, (
        "LiveReadinessPanel.tsx must import its model types from "
        "desktop/web/src/types/live_gui_protocol.ts."
    )
    assert _LOCAL_INTERFACE_RE.search(source) is None, (
        "LiveReadinessPanel.tsx must not define local TypeScript interfaces for "
        "live-GUI model shapes; add them to desktop/web/src/types/live_gui_protocol.ts."
    )
