"""Architecture tests: _parity_worker._update_index behaviour.

These tests cover the capture-mode safety contract of the V1.34 parity
worker (``tests/_parity_worker.py``): in check mode (default), the
fixture index ``_INDEX.json`` must never be touched; in capture mode
(``PARITY_CAPTURE_MODE=1``), ``_update_index`` must create the file and
remain idempotent across repeat calls. Per PLAN_REQUIREMENTS.md Gate 13.

Import strategy
---------------

We load ``tests/_parity_worker.py`` by explicit file path rather than
via ``from tests._parity_worker import ...``. The package-style import
is fragile in two ways that this test specifically must avoid:

1. ``tests/`` has no ``__init__.py`` (it's a PEP 420 namespace package).
   Implicit namespace resolution depends on ``sys.path`` ordering, which
   is sensitive to developer-environment pollution — e.g. another
   editable-installed project on the same machine that also has a
   ``tests/`` directory will shadow this one.
2. The fixture mutates module-level globals (``FIXTURE_ROOT``) via
   ``monkeypatch.setattr``. Two different import paths yielding two
   distinct module objects in ``sys.modules`` would silently make the
   fixture patch the wrong module while the tests read the unpatched
   one — a classic invisible-fixture-leak bug.

The explicit file-path loader binds *one* canonical module object,
keyed on the canonical name ``_parity_worker_arch_test`` (distinct from
the test files' ``from _parity_worker import ...`` import, which uses
the bare-name slot in ``sys.modules``). Same module object across all
calls in this file; no shadowing; the fixture and the asserting code
see the same ``FIXTURE_ROOT``.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType
from typing import Final

import pytest

pytestmark = pytest.mark.fast

_PARITY_WORKER_PATH: Final[Path] = Path(__file__).resolve().parents[1] / "_parity_worker.py"
_PARITY_WORKER_MODULE_NAME: Final[str] = "_parity_worker_arch_test"


def _load_parity_worker() -> ModuleType:
    """Load ``tests/_parity_worker.py`` by file path, exactly once per session.

    Caches the loaded module under a dedicated name in ``sys.modules``
    so subsequent calls (across the three tests + the fixture) return
    the same module object. That single shared instance is what
    ``monkeypatch.setattr`` mutates and what the tests read — without
    this caching, each call would produce a fresh module and the
    fixture's patch would be invisible to the asserting code.
    """

    cached = sys.modules.get(_PARITY_WORKER_MODULE_NAME)
    if cached is not None:
        return cached

    if not _PARITY_WORKER_PATH.is_file():
        pytest.fail(
            f"{_PARITY_WORKER_PATH} does not exist. The parity worker is "
            "the V1.34 reference behavior keeper; restore it from git "
            "history or check the repo layout."
        )

    spec = importlib.util.spec_from_file_location(_PARITY_WORKER_MODULE_NAME, _PARITY_WORKER_PATH)
    if spec is None or spec.loader is None:
        pytest.fail(f"Could not build import spec for {_PARITY_WORKER_PATH}")

    module = importlib.util.module_from_spec(spec)
    sys.modules[_PARITY_WORKER_MODULE_NAME] = module
    spec.loader.exec_module(module)
    return module


def _import_update_index() -> object:
    """Return the ``_update_index`` callable from the parity worker.

    Fails clearly if the symbol is missing — that would mean the
    capture-mode pipeline has regressed and should not be allowed to
    ship.
    """

    module = _load_parity_worker()
    update_index = getattr(module, "_update_index", None)
    if update_index is None:
        pytest.fail(
            f"{_PARITY_WORKER_PATH} exists but does not expose "
            "_update_index; restore it (see PLAN_REQUIREMENTS.md Gate 13)."
        )
    return update_index


def _import_capture_mode_enabled() -> object:
    """Return the ``_capture_mode_enabled`` callable from the parity worker."""

    module = _load_parity_worker()
    fn = getattr(module, "_capture_mode_enabled", None)
    if fn is None:
        pytest.fail(
            f"{_PARITY_WORKER_PATH} exists but does not expose "
            "_capture_mode_enabled; restore it (see PLAN_REQUIREMENTS.md Gate 13)."
        )
    return fn


@pytest.fixture()
def patched_fixture_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Redirect ``FIXTURE_ROOT`` to a temp directory for isolation.

    Mutates the *cached* parity-worker module (see ``_load_parity_worker``)
    so the patch is visible to the same module that ``_update_index``
    reads from when it computes the index path. ``monkeypatch`` rolls
    the attribute back at teardown — the cache itself is intentionally
    long-lived so back-to-back tests share one module instance.
    """

    pw = _load_parity_worker()
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
