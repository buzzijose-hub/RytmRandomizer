"""Tests for ``ProfileRegistry.save``'s atomic + no-overwrite semantics (PR 7 — M7).

Pins the contract that PR 7 introduced:

* ``save()`` routes through :func:`cockpit.export.writer.atomic_write`
  so a crash mid-write cannot corrupt the destination — the prior file
  (if any) is preserved verbatim.
* ``save()`` defaults to ``overwrite=False``; the second save for a
  given ``profile_id`` raises :class:`ProfileAlreadyExistsError`
  (subclass of :class:`DataError` + :class:`FileExistsError`) so a
  retried ``wizard_save`` cannot silently obliterate prior user
  content.
* ``save(profile, overwrite=True)`` replaces the prior file atomically
  and the in-memory cache reflects the new bytes.
* Catastrophic write failures (the underlying :func:`os.replace`
  raising :class:`OSError`) leave the *original* destination file
  intact — that is the atomic-write contract end-to-end.

See ``rytm_randomizer/cockpit/export/writer.py`` for the canonical
``atomic_write`` surface this test pins.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from rytm_randomizer.cockpit.data import ProfileModel, StyleTrait, TraitPadWeight
from rytm_randomizer.cockpit.export.writer import WriteError
from rytm_randomizer.cockpit.profiles import (
    ProfileAlreadyExistsError,
    ProfileRegistry,
)
from rytm_randomizer.observability.errors import DataError

pytestmark = pytest.mark.fast


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _make_user_profile(
    *,
    profile_id: str = "01HXY5Q9PJM0123456789ABCD0",
    name: str = "atomic-test",
    trait_value: float = 0.8,
) -> ProfileModel:
    return ProfileModel(
        profile_id=profile_id,
        name=name,
        kind="user",
        model_version="1.0.0",
        traits=(StyleTrait(name="rolling_low_end", value=trait_value),),
        pad_mappings=(TraitPadWeight(trait="rolling_low_end", pad_id=1, weight=trait_value),),
        transition_curve="linear",
        source_summary=f"test profile {name}",
    )


# ---------------------------------------------------------------------------
# Taxonomy membership — the dual-inheritance contract
# ---------------------------------------------------------------------------


def test_profile_already_exists_error_is_both_data_error_and_file_exists_error() -> None:
    """The exception must satisfy both ``except DataError`` and ``except FileExistsError``."""

    assert issubclass(ProfileAlreadyExistsError, DataError)
    assert issubclass(ProfileAlreadyExistsError, FileExistsError)


def test_profile_already_exists_error_can_be_caught_as_file_exists_error() -> None:
    """Stdlib ``except FileExistsError`` callers continue to work without imports."""

    try:
        raise ProfileAlreadyExistsError("boom")
    except FileExistsError as exc:
        assert isinstance(exc, ProfileAlreadyExistsError)


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------


def test_save_to_fresh_path_writes_correct_content(tmp_path: Path) -> None:
    """A first save lands the encoded bytes at the canonical path."""

    registry = ProfileRegistry(profiles_dir=tmp_path)
    profile = _make_user_profile()
    result = registry.save(profile)
    # IH2: save() returns None — the prior ``-> Path`` return was dead surface.
    assert result is None
    target = tmp_path / "user" / f"{profile.profile_id}.json"
    assert target.is_file()
    payload = json.loads(target.read_text(encoding="utf-8"))
    assert ProfileModel.from_dict(payload) == profile


def test_save_returns_none(tmp_path: Path) -> None:
    """IH2: the contract is now ``save -> None`` (no dead return value)."""

    registry = ProfileRegistry(profiles_dir=tmp_path)
    assert registry.save(_make_user_profile()) is None


# ---------------------------------------------------------------------------
# Overwrite=False (the default) — refuse to clobber
# ---------------------------------------------------------------------------


def test_save_twice_with_default_overwrite_false_raises(tmp_path: Path) -> None:
    """Second save with same profile_id is rejected, not silently overwritten."""

    registry = ProfileRegistry(profiles_dir=tmp_path)
    profile = _make_user_profile()
    registry.save(profile)
    with pytest.raises(ProfileAlreadyExistsError) as excinfo:
        registry.save(profile)
    # The error message should mention the profile id so a confused
    # operator can immediately spot the collision.
    assert profile.profile_id in str(excinfo.value)


def test_save_twice_with_default_can_be_caught_as_file_exists_error(tmp_path: Path) -> None:
    """``except FileExistsError:`` works without import changes."""

    registry = ProfileRegistry(profiles_dir=tmp_path)
    profile = _make_user_profile()
    registry.save(profile)
    with pytest.raises(FileExistsError):
        registry.save(profile)


def test_save_no_overwrite_does_not_change_existing_file(tmp_path: Path) -> None:
    """A rejected second save must leave the original bytes intact."""

    registry = ProfileRegistry(profiles_dir=tmp_path)
    first = _make_user_profile(name="original")
    registry.save(first)
    target = tmp_path / "user" / f"{first.profile_id}.json"
    original_bytes = target.read_bytes()

    second = _make_user_profile(name="would-overwrite", trait_value=0.1)
    with pytest.raises(ProfileAlreadyExistsError):
        registry.save(second)

    # File on disk still contains the first profile's bytes verbatim.
    assert target.read_bytes() == original_bytes


# ---------------------------------------------------------------------------
# Overwrite=True — explicit replacement
# ---------------------------------------------------------------------------


def test_save_twice_with_overwrite_true_succeeds(tmp_path: Path) -> None:
    """Explicit opt-in to overwrite atomically replaces the prior file."""

    registry = ProfileRegistry(profiles_dir=tmp_path)
    first = _make_user_profile(name="first", trait_value=0.2)
    registry.save(first)

    second = _make_user_profile(name="second", trait_value=0.9)
    registry.save(second, overwrite=True)

    target = tmp_path / "user" / f"{first.profile_id}.json"
    payload = json.loads(target.read_text(encoding="utf-8"))
    loaded = ProfileModel.from_dict(payload)
    assert loaded.name == "second"
    assert loaded.traits[0].value == 0.9
    # In-memory cache reflects the latest write.
    assert registry.get(first.profile_id) == second


def test_save_overwrite_true_with_no_existing_file_is_fine(tmp_path: Path) -> None:
    """``overwrite=True`` on a fresh path is harmless (no preflight failure)."""

    registry = ProfileRegistry(profiles_dir=tmp_path)
    profile = _make_user_profile()
    # No exception raised; the file lands as if overwrite were False.
    registry.save(profile, overwrite=True)
    assert (tmp_path / "user" / f"{profile.profile_id}.json").is_file()


# ---------------------------------------------------------------------------
# Atomic-write contract under failure: original file must survive
# ---------------------------------------------------------------------------


def test_failed_overwrite_leaves_original_file_intact(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Simulate an ``os.replace`` failure mid-write; original bytes must survive.

    The atomic-write writer first writes the new bytes to a sibling
    ``.tmp`` file, then ``os.replace``s it onto the destination. If the
    rename step fails (simulated here), the destination file must
    contain the *prior* bytes — never a corrupted partial. The temp
    file is best-effort unlinked.
    """

    registry = ProfileRegistry(profiles_dir=tmp_path)
    original = _make_user_profile(name="original", trait_value=0.5)
    registry.save(original)
    target = tmp_path / "user" / f"{original.profile_id}.json"
    original_bytes = target.read_bytes()

    real_replace = os.replace

    def failing_replace(src: str, _dst: str) -> None:
        # Mid-flight failure during the rename — the new bytes are
        # already written to ``src`` (the temp file) but never made it
        # to ``dst`` (the destination).
        raise OSError("simulated rename failure")

    monkeypatch.setattr(os, "replace", failing_replace)
    second = _make_user_profile(name="would-clobber", trait_value=0.99)
    with pytest.raises(WriteError):
        registry.save(second, overwrite=True)

    # Destination still has the ORIGINAL bytes — atomic contract held.
    monkeypatch.setattr(os, "replace", real_replace)  # restore so cleanup works
    assert target.read_bytes() == original_bytes

    # No leaked ``.tmp`` siblings (best-effort cleanup happened).
    user_dir = tmp_path / "user"
    leaked = [p for p in user_dir.iterdir() if p.suffix == ".tmp"]
    assert leaked == [], f"leaked temp files: {leaked}"


def test_write_error_bubbles_up_unwrapped(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """An underlying :class:`WriteError` propagates from ``save()`` as-is.

    Per the M7 contract: only ``FileExistsError`` is translated to
    ``ProfileAlreadyExistsError``. Every other write failure surfaces as
    a plain ``WriteError`` (already a taxonomy member).
    """

    registry = ProfileRegistry(profiles_dir=tmp_path)

    def failing_rename(src: str, _dst: str | Path) -> None:
        raise OSError("ENOSPC simulated")

    monkeypatch.setattr(os, "rename", failing_rename)
    with pytest.raises(WriteError):
        registry.save(_make_user_profile())


# ---------------------------------------------------------------------------
# Read-only target directory — surfaces a write failure, not silent loss
# ---------------------------------------------------------------------------


@pytest.mark.skipif(
    os.name == "nt",
    reason=(
        "Windows POSIX ``chmod 0o555`` does not actually prevent writes the way "
        "POSIX does (NTFS uses ACLs). Equivalent permission-denied semantics "
        "are exercised end-to-end in test_failed_overwrite_leaves_original_file_intact "
        "via a mocked ``os.replace``."
    ),
)
def test_save_to_readonly_directory_raises_write_error(tmp_path: Path) -> None:
    """A read-only target directory surfaces a ``WriteError`` (not silent loss)."""

    user_dir = tmp_path / "user"
    user_dir.mkdir()
    user_dir.chmod(0o555)  # r-x for everyone, no write
    try:
        registry = ProfileRegistry(profiles_dir=tmp_path)
        with pytest.raises((WriteError, OSError)):
            registry.save(_make_user_profile())
    finally:
        # Always restore writability so the tmp_path cleanup doesn't fail.
        user_dir.chmod(0o755)
