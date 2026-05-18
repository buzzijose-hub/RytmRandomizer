"""Architecture tests: _parity_worker._update_index behaviour.

RED phase — these tests fail until WS-M4 Phase 5 adds ``_update_index``
and ``_index_path`` to ``tests/_parity_worker.py``.

Per WS-M4-PLAN.md §4 and PLAN_REQUIREMENTS.md Gate 13.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

pytestmark = pytest.mark.fast


# ---------------------------------------------------------------------------
# Helpers — lazy imports so collection does not blow up when the symbols
# do not exist yet (RED phase).
# ---------------------------------------------------------------------------


def _import_update_index():  # type: ignore[return]
    """Import ``_update_index`` from ``tests._parity_worker``; fail clearly if missing."""
    try:
        from tests._parity_worker import _update_index  # type: ignore[attr-defined]

        return _update_index
    except ImportError as exc:
        pytest.fail(f"tests._parity_worker does not exist as a module: {exc}")
    except AttributeError:
        pytest.fail(
            "tests/_parity_worker.py exists but does not define _update_index; "
            "add it as part of WS-M4 Phase 5."
        )


def _import_capture_mode_enabled():
    """Import ``_capture_mode_enabled`` from ``tests._parity_worker``."""
    from tests._parity_worker import _capture_mode_enabled  # noqa: PLC0415

    return _capture_mode_enabled


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def patched_fixture_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Redirect ``FIXTURE_ROOT`` to a temp directory for isolation."""
    import tests._parity_worker as pw

    fake_root = tmp_path / "v134_parity"
    fake_root.mkdir(parents=True)
    monkeypatch.setattr(pw, "FIXTURE_ROOT", fake_root)
    return fake_root


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_update_index_creates_file_in_capture(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    patched_fixture_root: Path,
) -> None:
    """``_update_index`` must create ``_INDEX.json`` inside FIXTURE_ROOT."""
    _update_index = _import_update_index()

    module_id = "tests.test_engines_pad1"
    payload = {"seed": 42, "steps": [["load_pad1_bd_profile", ["2"]]]}
    # Construct a fake fixture path inside the patched root.
    fixture_path = patched_fixture_root / "test_engines_pad1__deadbeef1234abcd.json"

    _update_index(module_id, fixture_path, payload)

    index_path = patched_fixture_root / "_INDEX.json"
    assert index_path.exists(), "_update_index must create _INDEX.json inside FIXTURE_ROOT"

    data = json.loads(index_path.read_text(encoding="utf-8"))
    assert "_meta" in data, "_INDEX.json must contain a '_meta' key"
    assert data["_meta"].get("schema_version") == 1, "_meta.schema_version must be 1"

    digest_key = fixture_path.stem  # filename without .json
    assert digest_key in data, f"_INDEX.json must contain entry for '{digest_key}'"
    entry = data[digest_key]
    assert entry["module_id"] == module_id
    assert entry["seed"] == 42


def test_update_index_is_idempotent(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    patched_fixture_root: Path,
) -> None:
    """Calling ``_update_index`` twice must not duplicate the entry."""
    _update_index = _import_update_index()

    module_id = "tests.test_engines_pad1"
    payload = {"seed": 99, "steps": []}
    fixture_path = patched_fixture_root / "test_engines_pad1__aabbccdd11223344.json"

    _update_index(module_id, fixture_path, payload)
    _update_index(module_id, fixture_path, payload)

    index_path = patched_fixture_root / "_INDEX.json"
    data = json.loads(index_path.read_text(encoding="utf-8"))

    # Count non-_meta keys.
    entry_count = sum(1 for k in data if k != "_meta")
    assert entry_count == 1, (
        f"_INDEX.json must contain exactly 1 entry after two identical calls; " f"got {entry_count}"
    )
    assert (
        data["_meta"]["fixture_count"] == 1
    ), "_meta.fixture_count must reflect the real count (1), not be doubled"


def test_check_mode_does_not_touch_index(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    patched_fixture_root: Path,
) -> None:
    """When PARITY_CAPTURE_MODE is unset, ``_capture_mode_enabled()`` is False.

    This validates the safe-default requirement (Gate 13): normal test runs
    must never create or modify _INDEX.json.
    """
    _capture_mode_enabled = _import_capture_mode_enabled()

    # Remove the env var so we are in check (safe) mode.
    monkeypatch.delenv("PARITY_CAPTURE_MODE", raising=False)

    assert (
        _capture_mode_enabled() is False
    ), "_capture_mode_enabled() must return False when PARITY_CAPTURE_MODE is unset"

    index_path = patched_fixture_root / "_INDEX.json"
    assert (
        not index_path.exists()
    ), "_INDEX.json must NOT be created during check mode (PARITY_CAPTURE_MODE unset)"
