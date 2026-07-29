"""Tests for the dynamic strict-production Pyright runner."""

from __future__ import annotations

import importlib.util
import json
import subprocess
from pathlib import Path
from types import ModuleType, SimpleNamespace
from typing import Final

import pytest

pytestmark = pytest.mark.fast

_REPO_ROOT: Final[Path] = Path(__file__).resolve().parents[1]
_SCRIPT: Final[Path] = _REPO_ROOT / "scripts" / "typecheck_touched.py"


def _load_script_module() -> ModuleType:
    spec = importlib.util.spec_from_file_location("typecheck_touched", _SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


typecheck_touched = _load_script_module()


def _git(repo: Path, *arguments: str) -> str:
    completed = subprocess.run(
        ["git", *arguments],
        cwd=repo,
        capture_output=True,
        check=True,
        text=True,
    )
    return completed.stdout.strip()


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_collect_touched_production_files_covers_committed_working_and_untracked(
    tmp_path: Path,
) -> None:
    _git(tmp_path, "init")
    _git(tmp_path, "config", "user.email", "tests@example.invalid")
    _git(tmp_path, "config", "user.name", "RytmRandomizer Tests")
    _write(tmp_path / "rytm_randomizer" / "committed.py", "VALUE = 1\n")
    _write(tmp_path / "rytm_randomizer" / "working.py", "VALUE = 1\n")
    _write(tmp_path / "rytm_randomizer" / "deleted.py", "VALUE = 1\n")
    _write(tmp_path / "rytm_randomizer" / "old_name.py", "VALUE = 1\n")
    _write(tmp_path / "tests" / "ignored.py", "VALUE = 1\n")
    _git(tmp_path, "add", "rytm_randomizer", "tests")
    _git(tmp_path, "commit", "-m", "baseline")
    base = _git(tmp_path, "rev-parse", "HEAD")

    _write(tmp_path / "rytm_randomizer" / "committed.py", "VALUE = 2\n")
    _git(
        tmp_path,
        "mv",
        "rytm_randomizer/old_name.py",
        "rytm_randomizer/renamed.py",
    )
    _git(tmp_path, "add", "rytm_randomizer/committed.py")
    _git(tmp_path, "commit", "-m", "committed production change")
    _write(tmp_path / "rytm_randomizer" / "working.py", "VALUE = 2\n")
    (tmp_path / "rytm_randomizer" / "deleted.py").unlink()
    _write(tmp_path / "rytm_randomizer" / "untracked.py", "VALUE = 3\n")
    _write(tmp_path / "tests" / "untracked_test.py", "VALUE = 3\n")

    assert typecheck_touched.collect_touched_production_files(
        repo_root=tmp_path,
        base_ref=base,
    ) == (
        "rytm_randomizer/committed.py",
        "rytm_randomizer/renamed.py",
        "rytm_randomizer/untracked.py",
        "rytm_randomizer/working.py",
    )


def test_resolve_base_ref_prefers_explicit_then_github_base() -> None:
    assert (
        typecheck_touched.resolve_base_ref({"TYPECHECK_BASE_REF": "origin/main"}) == "origin/main"
    )
    assert typecheck_touched.resolve_base_ref({"GITHUB_BASE_REF": "release"}) == "origin/release"
    assert typecheck_touched.resolve_base_ref({}) == "origin/modularize-v1.34"


def test_validate_config_requires_strict_python_311(tmp_path: Path) -> None:
    config_path = tmp_path / "pyrightconfig.strict.json"
    config_path.write_text(
        json.dumps({"typeCheckingMode": "basic", "pythonVersion": "3.11"}),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="typeCheckingMode"):
        typecheck_touched._validate_config(config_path)


def test_main_invokes_pyright_and_propagates_its_exit_code(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[tuple[list[str], Path, bool]] = []

    monkeypatch.setattr(typecheck_touched, "_validate_config", lambda: None)
    monkeypatch.setattr(
        typecheck_touched,
        "collect_touched_production_files",
        lambda: ("rytm_randomizer/app.py",),
    )

    def fake_run(
        command: list[str],
        *,
        cwd: Path,
        check: bool,
    ) -> SimpleNamespace:
        calls.append((command, cwd, check))
        return SimpleNamespace(returncode=7)

    monkeypatch.setattr(typecheck_touched.subprocess, "run", fake_run)

    assert typecheck_touched.main() == 7
    command, cwd, check = calls[0]
    assert command[:3] == [
        typecheck_touched.sys.executable,
        "-m",
        "pyright",
    ]
    assert "--project" in command
    assert "--pythonpath" in command
    assert command[-1] == "rytm_randomizer/app.py"
    assert cwd == typecheck_touched.REPO_ROOT
    assert check is False
