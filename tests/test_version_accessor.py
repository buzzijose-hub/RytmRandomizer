"""Tests for ``rytm_randomizer/_version.py`` — interface contract I7.

``rytm_randomizer._version.__version__`` is a **frozen import path**: the WS
bootstrap surfaces it as ``session_status.app_version`` (contract I1), the
update beacon reports it, and the update check compares against it. These
tests pin the name, the resolution order, and — most importantly — the
promise that importing this module can never raise, because a diagnostics
accessor that throws takes the whole app's bootstrap with it.
"""

from __future__ import annotations

import importlib
import importlib.metadata
import sys
from pathlib import Path
from typing import Final

import pytest

from rytm_randomizer import _version

PROJECT_ROOT: Final[Path] = Path(__file__).resolve().parents[1]

pytestmark = pytest.mark.fast


def _reload() -> object:
    return importlib.reload(_version)


@pytest.fixture(autouse=True)
def _restore_module() -> object:
    """Leave the imported module in its pristine state for every other test."""
    yield
    importlib.reload(_version)


# ---------------------------------------------------------------------------
# The frozen contract (I7)
# ---------------------------------------------------------------------------


def test_version_is_exposed_at_the_frozen_import_path() -> None:
    from rytm_randomizer._version import __version__

    assert isinstance(__version__, str)
    assert __version__


def test_version_matches_the_canonical_version_file() -> None:
    canonical = (PROJECT_ROOT / "VERSION").read_text(encoding="utf-8").strip()
    assert _version.__version__ == canonical


def test_version_is_strict_semver() -> None:
    sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
    from release_lib import is_valid_version

    assert is_valid_version(_version.__version__)


def test_distribution_name_matches_pyproject() -> None:
    assert _version.DISTRIBUTION_NAME == "rytm-randomizer"


def test_unknown_sentinel_is_valid_semver_that_sorts_below_every_release() -> None:
    sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
    from release_lib import compare_versions, is_valid_version

    assert is_valid_version(_version.UNKNOWN_VERSION)
    assert compare_versions(_version.UNKNOWN_VERSION, "0.0.1") == -1


# ---------------------------------------------------------------------------
# Layering — a leaf that imports nothing from its own package
# ---------------------------------------------------------------------------


def test_module_imports_nothing_from_its_own_package() -> None:
    source = (PROJECT_ROOT / "rytm_randomizer" / "_version.py").read_text(encoding="utf-8")
    assert "from rytm_randomizer" not in source
    assert "import rytm_randomizer" not in source


def test_module_does_not_import_mido() -> None:
    source = (PROJECT_ROOT / "rytm_randomizer" / "_version.py").read_text(encoding="utf-8")
    assert "mido" not in source


# ---------------------------------------------------------------------------
# Resolution order
# ---------------------------------------------------------------------------


def test_installed_distribution_metadata_wins(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(importlib.metadata, "version", lambda _name: "9.9.9")
    reloaded = _reload()
    assert reloaded.__version__ == "9.9.9"  # type: ignore[attr-defined]


def test_falls_back_to_the_version_file_for_a_source_checkout(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def _not_installed(name: str) -> str:
        raise importlib.metadata.PackageNotFoundError(name)

    monkeypatch.setattr(importlib.metadata, "version", _not_installed)
    reloaded = _reload()
    canonical = (PROJECT_ROOT / "VERSION").read_text(encoding="utf-8").strip()
    assert reloaded.__version__ == canonical  # type: ignore[attr-defined]


def test_falls_back_to_the_sentinel_when_nothing_is_readable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def _not_installed(name: str) -> str:
        raise importlib.metadata.PackageNotFoundError(name)

    # `_version` binds the metadata lookup at import time, so the module-level
    # alias is what has to be replaced — patching importlib.metadata alone
    # would leave the real (installed) lookup in place.
    monkeypatch.setattr(_version, "_distribution_version", _not_installed)
    monkeypatch.setattr(_version, "_read_version_file", lambda: None)
    assert _version._resolve_version() == _version.UNKNOWN_VERSION


# ---------------------------------------------------------------------------
# The VERSION-file reader never raises
# ---------------------------------------------------------------------------


def test_reader_returns_the_stripped_contents(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "VERSION"
    path.write_text("  1.2.3  \n", encoding="utf-8")
    monkeypatch.setattr(_version, "_VERSION_FILE", path)
    assert _version._read_version_file() == "1.2.3"


def test_reader_returns_none_for_a_missing_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(_version, "_VERSION_FILE", tmp_path / "absent")
    assert _version._read_version_file() is None


@pytest.mark.parametrize("content", ["", "   ", "\n\n"])
def test_reader_returns_none_for_a_blank_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, content: str
) -> None:
    path = tmp_path / "VERSION"
    path.write_text(content, encoding="utf-8")
    monkeypatch.setattr(_version, "_VERSION_FILE", path)
    assert _version._read_version_file() is None


def test_reader_returns_none_for_undecodable_bytes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "VERSION"
    path.write_bytes(b"\xff\xfe\x00invalid")
    monkeypatch.setattr(_version, "_VERSION_FILE", path)
    assert _version._read_version_file() is None


def test_reader_returns_none_when_the_path_is_a_directory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    directory = tmp_path / "VERSION"
    directory.mkdir()
    monkeypatch.setattr(_version, "_VERSION_FILE", directory)
    assert _version._read_version_file() is None
