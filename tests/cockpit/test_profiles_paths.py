"""Tests for ``rytm_randomizer.cockpit.profiles.paths``.

Verifies that ``default_profiles_dir()`` resolves to the correct
per-platform location, honors XDG on Linux, and falls back sensibly when
the relevant environment variables are not set.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from rytm_randomizer.cockpit.profiles import paths
from rytm_randomizer.cockpit.profiles.paths import default_profiles_dir

pytestmark = pytest.mark.fast


# ---------------------------------------------------------------------------
# Linux + XDG
# ---------------------------------------------------------------------------


def test_linux_uses_xdg_config_home_when_set(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(paths.sys, "platform", "linux")
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    assert default_profiles_dir() == tmp_path / "rytm-randomizer" / "profiles"


def test_linux_falls_back_to_dot_config_when_xdg_unset(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(paths.sys, "platform", "linux")
    monkeypatch.delenv("XDG_CONFIG_HOME", raising=False)
    monkeypatch.setattr(paths.Path, "home", classmethod(lambda cls: tmp_path))
    assert default_profiles_dir() == tmp_path / ".config" / "rytm-randomizer" / "profiles"


def test_linux_falls_back_to_dot_config_when_xdg_is_empty_string(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """An empty string should be treated as "unset" per XDG spec."""

    monkeypatch.setattr(paths.sys, "platform", "linux")
    monkeypatch.setenv("XDG_CONFIG_HOME", "")
    monkeypatch.setattr(paths.Path, "home", classmethod(lambda cls: tmp_path))
    assert default_profiles_dir() == tmp_path / ".config" / "rytm-randomizer" / "profiles"


# ---------------------------------------------------------------------------
# macOS
# ---------------------------------------------------------------------------


def test_macos_uses_application_support(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(paths.sys, "platform", "darwin")
    monkeypatch.setattr(paths.Path, "home", classmethod(lambda cls: tmp_path))
    assert default_profiles_dir() == (
        tmp_path / "Library" / "Application Support" / "rytm-randomizer" / "profiles"
    )


# ---------------------------------------------------------------------------
# Windows
# ---------------------------------------------------------------------------


def test_windows_uses_appdata_when_set(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(paths.sys, "platform", "win32")
    monkeypatch.setenv("APPDATA", str(tmp_path))
    assert default_profiles_dir() == tmp_path / "rytm-randomizer" / "profiles"


def test_windows_falls_back_to_roaming_when_appdata_unset(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(paths.sys, "platform", "win32")
    monkeypatch.delenv("APPDATA", raising=False)
    monkeypatch.setattr(paths.Path, "home", classmethod(lambda cls: tmp_path))
    assert default_profiles_dir() == (
        tmp_path / "AppData" / "Roaming" / "rytm-randomizer" / "profiles"
    )


# ---------------------------------------------------------------------------
# Other platforms
# ---------------------------------------------------------------------------


def test_unknown_platform_uses_xdg_resolution_with_env(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Unknown POSIX-like platforms still honor XDG_CONFIG_HOME."""

    monkeypatch.setattr(paths.sys, "platform", "freebsd14")
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    assert default_profiles_dir() == tmp_path / "rytm-randomizer" / "profiles"


def test_unknown_platform_falls_back_to_dot_config(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(paths.sys, "platform", "freebsd14")
    monkeypatch.delenv("XDG_CONFIG_HOME", raising=False)
    monkeypatch.setattr(paths.Path, "home", classmethod(lambda cls: tmp_path))
    assert default_profiles_dir() == tmp_path / ".config" / "rytm-randomizer" / "profiles"


# ---------------------------------------------------------------------------
# Purity
# ---------------------------------------------------------------------------


def test_default_profiles_dir_does_not_create_anything(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """The path resolver must be pure — no I/O."""

    monkeypatch.setattr(paths.sys, "platform", "linux")
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    resolved = default_profiles_dir()
    # tmp_path itself exists, but the rytm-randomizer subtree must not.
    assert not (tmp_path / "rytm-randomizer").exists()
    assert isinstance(resolved, Path)
