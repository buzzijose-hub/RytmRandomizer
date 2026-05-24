"""Guard desktop shell bundle assets before GitHub Actions discovers drift."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

pytestmark = pytest.mark.fast

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SHELL_ROOT = PROJECT_ROOT / "desktop" / "shell"
TAURI_CONFIG = SHELL_ROOT / "tauri.conf.json"


def _object_map(value: object, label: str) -> dict[str, object]:
    assert isinstance(value, dict), f"{label} must be a JSON object"
    return value


def _string_value(value: object, label: str) -> str:
    assert isinstance(value, str) and value, f"{label} must be a non-empty string"
    return value


def _string_list(value: object, label: str) -> list[str]:
    assert isinstance(value, list), f"{label} must be a JSON array"
    assert all(
        isinstance(item, str) and item for item in value
    ), f"{label} must contain only non-empty strings"
    return value


def _load_tauri_config() -> dict[str, object]:
    assert TAURI_CONFIG.is_file(), "desktop shell tauri.conf.json is missing"
    config = json.loads(TAURI_CONFIG.read_text(encoding="utf-8"))
    return _object_map(config, "tauri config")


def _shell_asset(relative_path: str) -> Path:
    return SHELL_ROOT / relative_path


def test_tauri_shell_icon_assets_are_declared_and_committed() -> None:
    """Windows Tauri builds need icon.ico in addition to the tray PNG."""

    config = _load_tauri_config()
    app = _object_map(config.get("app"), "app")
    tray_icon = _object_map(app.get("trayIcon"), "app.trayIcon")
    tray_icon_path = _string_value(tray_icon.get("iconPath"), "app.trayIcon.iconPath")

    bundle = _object_map(config.get("bundle"), "bundle")
    bundle_icons = _string_list(bundle.get("icon"), "bundle.icon")

    declared_icons = [tray_icon_path, *bundle_icons]
    missing = sorted(
        relative_path
        for relative_path in declared_icons
        if not _shell_asset(relative_path).is_file()
    )
    assert not missing, "Tauri shell declares icon assets that are not committed: " + ", ".join(
        missing
    )

    assert "icons/icon.ico" in bundle_icons, (
        "Windows Tauri resource generation requires desktop/shell/icons/icon.ico. "
        "Declare it in bundle.icon and commit the matching asset."
    )
