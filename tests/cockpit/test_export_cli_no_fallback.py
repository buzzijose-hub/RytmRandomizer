"""Regression tests pinning the export CLI's hard-import contract for the writer.

Before PR 3 (CODE_REVIEW.md §C3) the CLI module carried a ~60-LOC
``try/except ImportError`` block that re-implemented :func:`atomic_write`,
:class:`WriteResult`, and :func:`default_export_dir` inline. That fallback
was dead code in any shipping build (``writer.py`` is always present) but
its behaviour silently disagreed with the canonical writer on three
observable axes:

* Overwrite refusal raised :class:`ValueError` instead of
  :class:`FileExistsError`.
* Underlying :class:`OSError`s leaked raw instead of being wrapped in
  :class:`WriteError`.
* The default export directory was ``~/.rytm-randomizer/exports`` on
  every platform instead of the XDG / APPDATA-aware path
  :func:`writer.default_export_dir` returns.

These tests pin three invariants that together prevent the fallback (or
any drop-in lookalike) from creeping back in:

1. ``rytm_randomizer.cockpit.export.cli.atomic_write`` is **the same
   function object** as ``rytm_randomizer.cockpit.export.writer.atomic_write``.
   Re-implementing it locally would necessarily produce a *different*
   function object and break this identity check.
2. Simulating a missing ``writer`` module (the only scenario the
   fallback ever activated under) must raise :class:`ImportError` at
   module reload — the CLI must fail loudly, not silently swap
   implementations.
3. The overwrite-refusal path raises :class:`FileExistsError` (the
   writer's canonical behaviour) — not :class:`ValueError` (the deleted
   fallback's behaviour). This is the divergence test that pins the
   unification.

Mark: ``pytest.mark.fast`` (matches every other cockpit test module).
"""

from __future__ import annotations

import importlib
import sys
from pathlib import Path
from typing import Final

import pytest

from rytm_randomizer.cockpit.data import ProfileModel, StyleTrait, TraitPadWeight
from rytm_randomizer.cockpit.export import cli as cli_module
from rytm_randomizer.cockpit.export import writer as writer_module
from rytm_randomizer.cockpit.profiles import ProfileRegistry

pytestmark = pytest.mark.fast


# ---------------------------------------------------------------------------
# Fixtures / helpers
# ---------------------------------------------------------------------------


_PROFILE_ID: Final[str] = "user-no-fallback"


def _make_profile() -> ProfileModel:
    """Build a small, fully-valid ``ProfileModel`` for round-trip testing."""

    return ProfileModel(
        profile_id=_PROFILE_ID,
        name="No fallback",
        kind="user",
        model_version="1.0.0",
        traits=(StyleTrait(name="rolling_low_end", value=0.5),),
        pad_mappings=(TraitPadWeight(trait="rolling_low_end", pad_id=1, weight=0.9),),
        transition_curve="progressive",
        source_summary="pins the no-fallback unification",
    )


def _save_profile(profiles_dir: Path, profile: ProfileModel) -> None:
    """Persist ``profile`` via a fresh ``ProfileRegistry``."""

    ProfileRegistry(profiles_dir).save(profile)


# ---------------------------------------------------------------------------
# Identity: cli surface is literally the writer surface
# ---------------------------------------------------------------------------


def test_cli_atomic_write_is_writer_atomic_write() -> None:
    """``cli.atomic_write`` must *be* :func:`writer.atomic_write`.

    Regression guard: the deleted fallback shipped its own
    ``atomic_write`` definition, so the two names referenced *different*
    function objects depending on whether the ``try/except`` import
    succeeded. With the hard import in place they must reference the
    same object. Anyone re-introducing a local re-implementation will
    necessarily break this identity check.
    """

    assert cli_module.atomic_write is writer_module.atomic_write, (
        "cli.atomic_write must be the canonical writer.atomic_write — "
        "no module-local re-implementation. See CODE_REVIEW.md §C3."
    )


def test_cli_write_result_is_writer_write_result() -> None:
    """``cli.WriteResult`` must *be* :class:`writer.WriteResult`.

    Regression guard: same as above but for the dataclass. A local
    re-definition would survive type-checking (both shapes are
    structurally identical) but break ``isinstance`` checks against the
    canonical type.
    """

    assert cli_module.WriteResult is writer_module.WriteResult, (
        "cli.WriteResult must be the canonical writer.WriteResult — "
        "no module-local re-implementation. See CODE_REVIEW.md §C3."
    )


def test_cli_default_export_dir_is_writer_default_export_dir() -> None:
    """``cli.default_export_dir`` must *be* :func:`writer.default_export_dir`.

    Regression guard: the deleted fallback returned
    ``~/.rytm-randomizer/exports`` on every platform; the canonical
    writer returns the XDG / APPDATA-aware path. A local re-implementation
    would silently revert that behaviour.
    """

    assert cli_module.default_export_dir is writer_module.default_export_dir, (
        "cli.default_export_dir must be the canonical writer.default_export_dir — "
        "no module-local re-implementation. See CODE_REVIEW.md §C3."
    )


def test_cli_write_error_is_writer_write_error() -> None:
    """``cli.WriteError`` must *be* :class:`writer.WriteError`.

    Regression guard: the deleted fallback re-raised raw ``OSError``s;
    the canonical writer wraps them in :class:`WriteError` (a
    ``DataError`` + ``OSError`` so the observability taxonomy and the
    legacy ``except OSError`` callers both keep working). A local
    re-export of a stand-in class would break ``isinstance`` against
    the project's typed exception.
    """

    assert cli_module.WriteError is writer_module.WriteError, (
        "cli.WriteError must be the canonical writer.WriteError — "
        "no module-local re-implementation. See CODE_REVIEW.md §C3."
    )


# ---------------------------------------------------------------------------
# Hard-import contract: missing writer must surface as ImportError
# ---------------------------------------------------------------------------


def test_cli_module_fails_loudly_if_writer_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Reloading ``cli`` with ``writer`` purged from ``sys.modules`` and
    blocked from re-import must raise :class:`ImportError`.

    Regression guard: the deleted fallback ``try/except ImportError``
    block silently swapped in a behavioural near-duplicate when
    ``writer`` could not be imported. With the hard import in place,
    the same scenario must fail loudly at module load. This is the
    *single* test that pins "no silent substitution".
    """

    target_name = "rytm_randomizer.cockpit.export.writer"
    cli_name = "rytm_randomizer.cockpit.export.cli"

    # Snapshot the modules we plan to mutate so we can restore them
    # cleanly even if the import we're about to attempt raises.
    saved_writer = sys.modules.pop(target_name, None)
    saved_cli = sys.modules.pop(cli_name, None)

    class _BlockWriterFinder:
        """Meta-path finder that pretends ``writer`` cannot be imported.

        Returns a ``ModuleSpec`` with a loader whose ``exec_module``
        raises ``ImportError`` — that's how Python signals "module not
        installed" to any caller using ``import``.
        """

        def find_spec(self, fullname: str, path: object, target: object = None):
            if fullname != target_name:
                return None
            import importlib.machinery as _machinery  # noqa: PLC0415 - local

            class _RaisingLoader:
                def create_module(self, spec: object) -> object | None:
                    return None

                def exec_module(self, module: object) -> None:
                    raise ImportError("simulated: writer module unavailable (test fixture)")

            return _machinery.ModuleSpec(fullname, _RaisingLoader())

    finder = _BlockWriterFinder()
    sys.meta_path.insert(0, finder)
    try:
        with pytest.raises(ImportError):
            importlib.import_module(cli_name)
    finally:
        # Restore meta_path and the original modules in every case so
        # later tests in the same session keep seeing the real cli /
        # writer surface.
        try:
            sys.meta_path.remove(finder)
        except ValueError:
            pass
        sys.modules.pop(cli_name, None)
        sys.modules.pop(target_name, None)
        if saved_writer is not None:
            sys.modules[target_name] = saved_writer
        if saved_cli is not None:
            sys.modules[cli_name] = saved_cli
        else:
            # Force a clean re-import so the real module replaces any
            # half-baked state the failed import left behind.
            importlib.import_module(cli_name)


# ---------------------------------------------------------------------------
# Behavioural divergence: overwrite-refusal raises FileExistsError
# ---------------------------------------------------------------------------


def test_overwrite_refusal_raises_file_exists_error_not_value_error(
    tmp_path: Path,
) -> None:
    """The writer (and now the only ``atomic_write`` path) refuses to
    overwrite by raising :class:`FileExistsError` — *not*
    :class:`ValueError`.

    Regression guard: the deleted fallback raised ``ValueError`` so its
    error path was caught by ``except ValueError`` callers but rejected
    by ``except FileExistsError`` callers (and vice-versa for the
    canonical writer). Pinning the writer's behaviour here means any
    re-introduction of the fallback necessarily breaks this test.
    """

    target = tmp_path / "preexisting.rymp"
    target.write_bytes(b"existing content")

    with pytest.raises(FileExistsError):
        cli_module.atomic_write(target, b"new content", overwrite=False)

    # Original bytes preserved — refusal happens before any write attempt.
    assert target.read_bytes() == b"existing content"


def test_overwrite_refusal_is_caught_by_handler_as_oserror_subclass(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """The CLI handler catches the writer's :class:`FileExistsError` via
    the broader :class:`OSError` arm and emits ``ok=False`` without
    crashing.

    Regression guard: the operator-facing ack contract is "no exception
    ever escapes" (cli.py docstring). With the fallback gone, the only
    way overwrite-refusal reaches the handler is as a
    :class:`FileExistsError`. The handler's ``except (..., OSError, ...)``
    arm has to catch it.
    """

    profile = _make_profile()
    _save_profile(tmp_path, profile)
    output = tmp_path / "out.rymp"
    output.write_bytes(b"existing content")

    exit_code = cli_module.handle_export_profile_model(
        [
            "--profile-id",
            profile.profile_id,
            "--profiles-dir",
            str(tmp_path),
            "--output",
            str(output),
            "--unsigned",
            "--json",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code != 0
    # The handler returned a structured ack — no traceback on stderr.
    assert captured.err == ""
    assert '"ok": false' in captured.out
    # Original bytes preserved — atomic_write refused to overwrite.
    assert output.read_bytes() == b"existing content"


# ---------------------------------------------------------------------------
# Malformed input → handler returns ok=False (covers the expanded
# exception filter for M9: ValueError / TypeError / OverflowError /
# OSError / PackException).
# ---------------------------------------------------------------------------


def test_handler_swallows_pack_failure_from_malformed_model(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """If :func:`pack_profile_model` raises a ``PackException`` from
    msgpack, the handler returns ``ok=False`` — not a crash.

    Regression guard: M9 in CODE_REVIEW.md called out the original
    ``except (ValueError, TypeError, OSError)`` as incomplete —
    ``msgpack.exceptions.PackException`` is a bare ``Exception``
    subclass and would have escaped. We simulate it by patching
    ``pack_profile_model`` to raise ``PackException`` and assert the
    handler catches it.
    """

    import msgpack.exceptions

    def _raises_pack_exception(profile: ProfileModel) -> bytes:
        raise msgpack.exceptions.PackException("simulated pack failure")

    monkeypatch.setattr(
        "rytm_randomizer.cockpit.export.cli.pack_profile_model",
        _raises_pack_exception,
    )

    profile = _make_profile()
    _save_profile(tmp_path, profile)
    output = tmp_path / "out.rymp"

    exit_code = cli_module.handle_export_profile_model(
        [
            "--profile-id",
            profile.profile_id,
            "--profiles-dir",
            str(tmp_path),
            "--output",
            str(output),
            "--unsigned",
            "--json",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code != 0
    assert '"ok": false' in captured.out
    assert "simulated pack failure" in captured.out
    # Bytes were never written — the failure happened before atomic_write.
    assert not output.exists()


def test_handler_swallows_overflow_error_from_pack(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """``OverflowError`` from :func:`pack_profile_model` is caught (M9).

    Regression guard: ``msgpack.packb`` raises
    ``msgpack.exceptions.PackOverflowError`` (an ``OverflowError``
    subclass) when an integer overflows the wire range. The original
    catch tuple did not include ``OverflowError`` so this would have
    crashed the handler.
    """

    def _raises_overflow(profile: ProfileModel) -> bytes:
        raise OverflowError("simulated int overflow")

    monkeypatch.setattr(
        "rytm_randomizer.cockpit.export.cli.pack_profile_model",
        _raises_overflow,
    )

    profile = _make_profile()
    _save_profile(tmp_path, profile)
    output = tmp_path / "out.rymp"

    exit_code = cli_module.handle_export_profile_model(
        [
            "--profile-id",
            profile.profile_id,
            "--profiles-dir",
            str(tmp_path),
            "--output",
            str(output),
            "--unsigned",
            "--json",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code != 0
    assert '"ok": false' in captured.out
    assert "simulated int overflow" in captured.out
    assert not output.exists()
