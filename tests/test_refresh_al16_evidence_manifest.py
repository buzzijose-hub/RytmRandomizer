"""Guards on the AL02 evidence-manifest refresh tool.

The script rewrites committed provenance, so its refusals matter more than
its happy path. These tests pin the three behaviors that keep it from
quietly destroying evidence:

* it will not run without its explicit capture flag,
* it will not run against a manifest bound to real exported bytes,
* it will not paper over a change to the pinned dependency set.
"""

from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.fast

_REPO_ROOT = Path(__file__).resolve().parents[1]
_SCRIPT = _REPO_ROOT / "scripts" / "refresh_al16_evidence_manifest.py"
_MANIFEST = _REPO_ROOT / "output" / "al16" / "AL02_LOCK_RYTM_manifest.json"
_FLAG = "RYTM_AL16_MANIFEST_REFRESH"


def _load_script():
    spec = importlib.util.spec_from_file_location("_al16_refresh", _SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_script_exists_so_the_manifest_is_never_hand_edited() -> None:
    assert _SCRIPT.is_file()


def test_refuses_to_run_without_the_capture_flag() -> None:
    env = {k: v for k, v in os.environ.items() if k != _FLAG}
    result = subprocess.run(
        [sys.executable, str(_SCRIPT)],
        capture_output=True,
        text=True,
        env=env,
        cwd=_REPO_ROOT,
    )

    assert result.returncode != 0
    assert _FLAG in (result.stdout + result.stderr)
    # The manifest is untouched by a refused run.
    assert json.loads(_MANIFEST.read_text(encoding="utf-8"))


def test_is_idempotent_when_digests_are_already_current(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """A no-op refresh reports success without rewriting the manifest.

    Runs against a *copy*: this test must never invoke the script on the
    real committed manifest, or a passing run would mutate tracked
    provenance and break ``test_al16_rytm_export.py`` for everything that
    executes after it.
    """

    module = _load_script()
    copy = tmp_path / "AL02_LOCK_RYTM_manifest.json"
    copy.write_bytes(_MANIFEST.read_bytes())
    before = copy.read_bytes()

    monkeypatch.setattr(module, "_MANIFEST_PATH", copy)
    monkeypatch.setenv(_FLAG, "1")

    assert module.main() == 0
    assert copy.read_bytes() == before
    # The real manifest was never opened for writing by this test.
    assert _MANIFEST.read_bytes() == before


def test_refuses_when_the_manifest_records_a_real_exported_artifact(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Provenance for shipped bytes needs a reviewed export, not a bulk refresh."""

    module = _load_script()
    shipped = json.loads(_MANIFEST.read_text(encoding="utf-8"))
    shipped["output_sha256"] = "0" * 64
    fake = tmp_path / "AL02_LOCK_RYTM_manifest.json"
    fake.write_text(json.dumps(shipped, indent=2), encoding="utf-8")

    monkeypatch.setattr(module, "_MANIFEST_PATH", fake)
    monkeypatch.setenv(_FLAG, "1")

    with pytest.raises(SystemExit, match="real exported artifact"):
        module.main()


def test_refuses_when_the_pinned_dependency_set_changed(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """A changed contract must be reviewed, not silently absorbed."""

    module = _load_script()
    drifted = json.loads(_MANIFEST.read_text(encoding="utf-8"))
    drifted["generator_dependency_sha256"].pop(next(iter(drifted["generator_dependency_sha256"])))
    fake = tmp_path / "AL02_LOCK_RYTM_manifest.json"
    fake.write_text(json.dumps(drifted, indent=2), encoding="utf-8")

    monkeypatch.setattr(module, "_MANIFEST_PATH", fake)
    monkeypatch.setenv(_FLAG, "1")

    with pytest.raises(SystemExit, match="dependency set changed"):
        module.main()
