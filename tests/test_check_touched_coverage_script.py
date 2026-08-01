"""Tests for the Gate-1 touched-file coverage gate script.

Pins the base-ref resolution branches — in particular that an unresolvable
base ref FAILS on CI (a gate must never report success on a diff it never
inspected) while still SKIPping loudly in a local shallow clone.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType
from typing import Final

import pytest

pytestmark = pytest.mark.fast

_REPO_ROOT: Final[Path] = Path(__file__).resolve().parents[1]
_SCRIPT: Final[Path] = _REPO_ROOT / "scripts" / "check_touched_coverage.py"


def _load_script_module() -> ModuleType:
    spec = importlib.util.spec_from_file_location("check_touched_coverage", _SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


check_touched_coverage = _load_script_module()


_COVERAGE_XML: Final[str] = """<?xml version="1.0" ?>
<coverage>
  <packages><package><classes>
    <class filename="rytm_randomizer/example.py">
      <lines><line number="1" hits="1"/></lines>
    </class>
  </classes></package></packages>
</coverage>
"""


def _write_coverage(tmp_path: Path) -> Path:
    path = tmp_path / "coverage.xml"
    path.write_text(_COVERAGE_XML, encoding="utf-8")
    return path


def test_running_in_ci_reads_github_actions(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("GITHUB_ACTIONS", raising=False)
    assert check_touched_coverage._running_in_ci() is False
    monkeypatch.setenv("GITHUB_ACTIONS", "")
    assert check_touched_coverage._running_in_ci() is False
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    assert check_touched_coverage._running_in_ci() is True


def test_unresolvable_base_ref_fails_on_ci(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """CI must never silently skip Gate 1 — an unresolvable base ref is a FAIL."""

    coverage_xml = _write_coverage(tmp_path)
    monkeypatch.setattr(check_touched_coverage, "_base_ref_is_available", lambda _ref: False)
    monkeypatch.setattr(check_touched_coverage, "_fetch_base_ref", lambda _ref: False)
    monkeypatch.setenv("GITHUB_ACTIONS", "true")

    assert check_touched_coverage.main(["prog", str(coverage_xml)]) == 1
    captured = capsys.readouterr()
    assert "FAIL" in captured.err
    assert "fetch-depth: 0" in captured.err
    # The loud local SKIP must NOT be what CI printed.
    assert "SKIP" not in captured.out


def test_unresolvable_base_ref_skips_locally(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Off CI a shallow clone SKIPs loudly rather than failing the developer."""

    coverage_xml = _write_coverage(tmp_path)
    monkeypatch.setattr(check_touched_coverage, "_base_ref_is_available", lambda _ref: False)
    monkeypatch.setattr(check_touched_coverage, "_fetch_base_ref", lambda _ref: False)
    monkeypatch.delenv("GITHUB_ACTIONS", raising=False)

    assert check_touched_coverage.main(["prog", str(coverage_xml)]) == 0
    captured = capsys.readouterr()
    assert "SKIP" in captured.out
    assert captured.err == ""


def test_missing_coverage_xml_fails_everywhere(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.delenv("GITHUB_ACTIONS", raising=False)
    assert check_touched_coverage.main(["prog", str(tmp_path / "absent.xml")]) == 1
    assert "not found" in capsys.readouterr().err
