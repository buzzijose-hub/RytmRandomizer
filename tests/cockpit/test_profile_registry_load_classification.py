"""Tests for ``ProfileRegistry`` load-error classification (PR 7 — M6).

The classifier in :func:`_safe_load_profile` distinguishes three
severity tiers:

* **Permission denied** (``PermissionError`` or ``OSError`` with
  ``errno`` in ``{EACCES, EPERM}``) is an infrastructure problem — the
  registry raises :class:`ProfileRegistryAccessError` so the cockpit
  refuses to boot with a confusing empty registry.
* **Single-file data problems** (malformed JSON, missing required
  keys, invalid trait values) warn + skip — a single corrupted profile
  must not take down the whole cockpit.
* **FileNotFoundError** during read (the file vanished between
  directory scan and read) is a benign race; DEBUG-log + skip silently.

Empty directories load cleanly with zero user profiles (only built-in
scenes appear in :meth:`ProfileRegistry.list_profiles`).
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

import pytest

from rytm_randomizer.cockpit.data import ProfileModel, StyleTrait, TraitPadWeight
from rytm_randomizer.cockpit.profiles import (
    ProfileRegistry,
    ProfileRegistryAccessError,
)
from rytm_randomizer.cockpit.profiles.builtin import BUILTIN_SCENES
from rytm_randomizer.observability.errors import DataError

pytestmark = pytest.mark.fast


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def registry_logger_caplog(
    caplog: pytest.LogCaptureFixture,
) -> pytest.LogCaptureFixture:
    """Capture registry logs even when package propagation is disabled."""

    logger = logging.getLogger("rytm_randomizer.cockpit.profiles.registry")
    logger.addHandler(caplog.handler)
    try:
        yield caplog
    finally:
        logger.removeHandler(caplog.handler)


def _make_user_profile(
    *,
    profile_id: str = "01HXY5Q9PJM0123456789VALID",
    name: str = "valid-load",
) -> ProfileModel:
    return ProfileModel(
        profile_id=profile_id,
        name=name,
        kind="user",
        model_version="1.0.0",
        traits=(StyleTrait(name="rolling_low_end", value=0.7),),
        pad_mappings=(TraitPadWeight(trait="rolling_low_end", pad_id=1, weight=0.7),),
        transition_curve="linear",
        source_summary=f"valid {name}",
    )


# ---------------------------------------------------------------------------
# Taxonomy membership — the dual-inheritance contract
# ---------------------------------------------------------------------------


def test_profile_registry_access_error_is_both_data_error_and_permission_error() -> None:
    """Both ``except DataError`` and ``except PermissionError`` catch it."""

    assert issubclass(ProfileRegistryAccessError, DataError)
    assert issubclass(ProfileRegistryAccessError, PermissionError)


def test_profile_registry_access_error_can_be_caught_as_permission_error() -> None:
    """Stdlib ``except PermissionError`` callers continue to work without imports."""

    try:
        raise ProfileRegistryAccessError("boom")
    except PermissionError as exc:
        assert isinstance(exc, ProfileRegistryAccessError)


# ---------------------------------------------------------------------------
# Empty directory — clean load with only built-ins
# ---------------------------------------------------------------------------


def test_empty_directory_loads_cleanly(tmp_path: Path) -> None:
    """No user dir, no user files — only built-in scenes appear."""

    registry = ProfileRegistry(profiles_dir=tmp_path)
    profiles = registry.list_profiles()
    assert all(p.kind == "scene" for p in profiles)
    assert len(profiles) == len(BUILTIN_SCENES)


def test_empty_user_subdirectory_loads_cleanly(tmp_path: Path) -> None:
    """User subdirectory exists but is empty — still only built-ins."""

    (tmp_path / "user").mkdir()
    registry = ProfileRegistry(profiles_dir=tmp_path)
    profiles = registry.list_profiles()
    assert all(p.kind == "scene" for p in profiles)


# ---------------------------------------------------------------------------
# PermissionError → raise (refuse to boot)
# ---------------------------------------------------------------------------


def test_permission_error_on_read_raises_registry_access_error(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    registry_logger_caplog: pytest.LogCaptureFixture,
) -> None:
    """A profile the operator cannot read raises, not warns + silently skips."""

    user_dir = tmp_path / "user"
    user_dir.mkdir()
    target = user_dir / "locked.json"
    target.write_text("{}", encoding="utf-8")

    real_read_text = Path.read_text

    def boom(self: Path, *args: object, **kwargs: object) -> str:
        if self == target:
            raise PermissionError("simulated EACCES")
        return real_read_text(self, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", boom)
    registry = ProfileRegistry(profiles_dir=tmp_path)
    with (
        registry_logger_caplog.at_level(logging.ERROR),
        pytest.raises(ProfileRegistryAccessError) as excinfo,
    ):
        registry.list_profiles()
    # The path appears in the error message so an operator can locate it.
    assert "locked.json" in str(excinfo.value)
    # And the failure was logged at ERROR level, not buried at WARNING.
    error_records = [r for r in registry_logger_caplog.records if r.levelno == logging.ERROR]
    assert any("locked.json" in r.message for r in error_records)


def test_permission_error_can_be_caught_as_permission_error(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """``except PermissionError`` from stdlib still works (dual-inherit contract)."""

    user_dir = tmp_path / "user"
    user_dir.mkdir()
    (user_dir / "locked.json").write_text("{}", encoding="utf-8")

    def boom(self: Path, *args: object, **kwargs: object) -> str:
        raise PermissionError("simulated EACCES")

    monkeypatch.setattr(Path, "read_text", boom)
    registry = ProfileRegistry(profiles_dir=tmp_path)
    with pytest.raises(PermissionError):
        registry.list_profiles()


# ---------------------------------------------------------------------------
# FileNotFoundError during read → silent skip (benign race condition)
# ---------------------------------------------------------------------------


def test_file_not_found_during_read_is_silently_skipped(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    registry_logger_caplog: pytest.LogCaptureFixture,
) -> None:
    """A file that vanishes between scan and read is logged at DEBUG, not WARN."""

    user_dir = tmp_path / "user"
    user_dir.mkdir()
    # Two files: one that "vanishes" mid-read and one that loads cleanly.
    ghost = user_dir / "vanished.json"
    ghost.write_text("{}", encoding="utf-8")
    good_profile = _make_user_profile()
    good_path = user_dir / f"{good_profile.profile_id}.json"
    good_path.write_text(json.dumps(good_profile.to_dict()), encoding="utf-8")

    real_read_text = Path.read_text

    def selective_read(self: Path, *args: object, **kwargs: object) -> str:
        if self == ghost:
            raise FileNotFoundError("file vanished between scan and read")
        return real_read_text(self, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", selective_read)
    registry = ProfileRegistry(profiles_dir=tmp_path)
    with registry_logger_caplog.at_level(logging.DEBUG):
        profiles = registry.list_profiles()

    # The good profile loaded; the ghost was silently skipped.
    user_profiles = [p for p in profiles if p.kind == "user"]
    assert user_profiles == [good_profile]

    # No WARNING / ERROR for the vanished file — it surfaces at DEBUG.
    noisy_records = [r for r in registry_logger_caplog.records if r.levelno >= logging.WARNING]
    assert all("vanished.json" not in r.message for r in noisy_records)


# ---------------------------------------------------------------------------
# Mixed dir: malformed + valid — valid survives, malformed warns + skip
# ---------------------------------------------------------------------------


def test_malformed_and_valid_coexist(
    tmp_path: Path,
    registry_logger_caplog: pytest.LogCaptureFixture,
) -> None:
    """A malformed sibling does not block the valid profile from loading."""

    user_dir = tmp_path / "user"
    user_dir.mkdir()
    # Malformed JSON.
    (user_dir / "broken.json").write_text("{not valid json", encoding="utf-8")
    # Valid profile.
    good = _make_user_profile(name="survivor")
    (user_dir / f"{good.profile_id}.json").write_text(json.dumps(good.to_dict()), encoding="utf-8")

    registry = ProfileRegistry(profiles_dir=tmp_path)
    with registry_logger_caplog.at_level(logging.WARNING):
        profiles = registry.list_profiles()

    user_profiles = [p for p in profiles if p.kind == "user"]
    assert user_profiles == [good]
    # The malformed file generated a WARNING.
    warning_records = [r for r in registry_logger_caplog.records if r.levelno == logging.WARNING]
    assert any("malformed profile file" in r.message.lower() for r in warning_records)


# ---------------------------------------------------------------------------
# Generic OSError (non-permission, no errno) → warn + skip (not raise)
# ---------------------------------------------------------------------------


def test_generic_os_error_warns_and_skips(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    registry_logger_caplog: pytest.LogCaptureFixture,
) -> None:
    """A non-permission OSError on read warns and skips; does NOT raise."""

    user_dir = tmp_path / "user"
    user_dir.mkdir()
    target = user_dir / "io-error.json"
    target.write_text("{}", encoding="utf-8")

    def boom(self: Path, *args: object, **kwargs: object) -> str:
        if self == target:
            # Bare OSError without errno=EACCES — exercises the
            # generic-OSError branch (warn + skip), not the
            # permission-error branch (raise).
            raise OSError("transient I/O hiccup")
        return Path.read_text(self, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", boom)
    registry = ProfileRegistry(profiles_dir=tmp_path)
    with registry_logger_caplog.at_level(logging.WARNING):
        # Must NOT raise — the registry is allowed to limp along.
        profiles = registry.list_profiles()
    assert all(p.kind == "scene" for p in profiles)
    assert any(
        "unreadable profile file" in r.message.lower() for r in registry_logger_caplog.records
    )


# ---------------------------------------------------------------------------
# Data-shape problems (missing fields, invalid kind) → warn + skip
# ---------------------------------------------------------------------------


def test_missing_required_field_warns_and_skips(
    tmp_path: Path,
    registry_logger_caplog: pytest.LogCaptureFixture,
) -> None:
    """A profile missing required keys warns and skips."""

    user_dir = tmp_path / "user"
    user_dir.mkdir()
    (user_dir / "incomplete.json").write_text(
        json.dumps({"profile_id": "01H", "name": "incomplete"}),
        encoding="utf-8",
    )
    registry = ProfileRegistry(profiles_dir=tmp_path)
    with registry_logger_caplog.at_level(logging.WARNING):
        profiles = registry.list_profiles()
    assert all(p.kind == "scene" for p in profiles)
    assert any("invalid profile file" in r.message.lower() for r in registry_logger_caplog.records)
