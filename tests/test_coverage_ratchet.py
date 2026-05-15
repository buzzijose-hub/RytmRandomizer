"""Behavior tests for scripts/coverage_ratchet.py.

The ratchet pins against PURE-BRANCH coverage (the stricter metric
exposed as the ``branch-rate`` attribute on coverage.xml's root element).
Tests here pin that contract: the floor is read from .coveragerc, the
measured number is read from branch-rate, and the script fails / no-ops /
ratchets based on the delta between them.

Importantly, the ratchet does NOT use coverage.py's blended line+branch
``fail_under`` metric. We deliberately picked the stricter pure-branch
number so the floor moves only when branch coverage actually improves;
line coverage growing alone (e.g. via dead-code addition) does not
mask insufficient branch testing.
"""

import importlib.util
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
COVERAGE_RATCHET_PATH = PROJECT_ROOT / "scripts" / "coverage_ratchet.py"


def _load_coverage_ratchet():
    """Import coverage_ratchet.py as a one-off module for testing."""

    spec = importlib.util.spec_from_file_location(
        "coverage_ratchet_under_test", COVERAGE_RATCHET_PATH
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _write_coverage_xml(path: Path, *, branch_rate: float) -> None:
    """Write a minimal coverage.xml with the given branch-rate value."""

    path.write_text(
        f'<coverage branch-rate="{branch_rate:.4f}"></coverage>',
        encoding="utf-8",
    )


def test_ratchet_passes_when_branch_coverage_exactly_at_floor(tmp_path, monkeypatch, capsys):
    """Measured branch-rate equal to floor -> no failure, no bump."""

    coverage_ratchet = _load_coverage_ratchet()
    coveragerc = tmp_path / ".coveragerc"
    coveragerc.write_text("[report]\nfail_under = 78\n", encoding="utf-8")
    coverage_xml = tmp_path / "coverage.xml"
    _write_coverage_xml(coverage_xml, branch_rate=0.7860)
    monkeypatch.setattr(coverage_ratchet, "COVERAGERC", coveragerc)

    result = coverage_ratchet.main(["coverage_ratchet.py", str(coverage_xml)])

    captured = capsys.readouterr()
    assert result == 0
    assert "measured pure-branch coverage 78.60%" in captured.out
    assert "No bump" in captured.out
    # Floor unchanged.
    assert coveragerc.read_text(encoding="utf-8") == "[report]\nfail_under = 78\n"


def test_ratchet_fails_when_branch_coverage_below_floor(tmp_path, monkeypatch, capsys):
    """Measured branch-rate below floor -> exit code 1 with diagnostic."""

    coverage_ratchet = _load_coverage_ratchet()
    coveragerc = tmp_path / ".coveragerc"
    coveragerc.write_text("[report]\nfail_under = 86\n", encoding="utf-8")
    coverage_xml = tmp_path / "coverage.xml"
    _write_coverage_xml(coverage_xml, branch_rate=0.7860)
    monkeypatch.setattr(coverage_ratchet, "COVERAGERC", coveragerc)

    result = coverage_ratchet.main(["coverage_ratchet.py", str(coverage_xml)])

    captured = capsys.readouterr()
    assert result == 1
    assert "FAIL" in captured.err
    assert "78.60%" in captured.err
    assert "floor=86%" in captured.err
    # Floor unchanged on failure.
    assert coveragerc.read_text(encoding="utf-8") == "[report]\nfail_under = 86\n"


def test_ratchet_bumps_floor_when_branch_coverage_rises_by_threshold(tmp_path, monkeypatch, capsys):
    """Measured >= floor + 1pp -> .coveragerc rewritten with new floor."""

    coverage_ratchet = _load_coverage_ratchet()
    coveragerc = tmp_path / ".coveragerc"
    coveragerc.write_text("[report]\nfail_under = 78\n", encoding="utf-8")
    coverage_xml = tmp_path / "coverage.xml"
    _write_coverage_xml(coverage_xml, branch_rate=0.8200)
    monkeypatch.setattr(coverage_ratchet, "COVERAGERC", coveragerc)

    result = coverage_ratchet.main(["coverage_ratchet.py", str(coverage_xml)])

    captured = capsys.readouterr()
    assert result == 0
    assert "RATCHETED" in captured.out
    assert "78% -> 82%" in captured.out
    assert coveragerc.read_text(encoding="utf-8") == "[report]\nfail_under = 82\n"
