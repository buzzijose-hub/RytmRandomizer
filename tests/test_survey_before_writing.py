"""The survey tool must find the real thing and stay quiet otherwise.

A survey that flags everything gets ignored, and one that flags nothing is
decoration. These tests pin both ends against the incident that produced it.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from typing import Final

import pytest

pytestmark = pytest.mark.fast

_SCRIPT: Final[Path] = Path(__file__).resolve().parents[1] / "scripts" / "survey_before_writing.py"
_spec = importlib.util.spec_from_file_location("survey_before_writing", _SCRIPT)
assert _spec is not None and _spec.loader is not None
survey = importlib.util.module_from_spec(_spec)
sys.modules["survey_before_writing"] = survey
_spec.loader.exec_module(survey)


def test_it_finds_the_script_i_actually_forked(capsys: pytest.CaptureFixture[str]) -> None:
    """The regression case: this exact query had to stop me and did not."""
    assert survey.main(["check_touched_branch_coverage"]) == 1
    out = capsys.readouterr().out
    assert "scripts/check_touched_coverage.py" in out
    assert "READ THESE FIRST" in out


def test_a_genuinely_new_name_is_not_flagged(capsys: pytest.CaptureFixture[str]) -> None:
    assert survey.main(["oscilloscope renderer"]) == 0
    assert "proceed" in capsys.readouterr().out


def test_character_similarity_alone_is_not_a_match(capsys: pytest.CaptureFixture[str]) -> None:
    """ "bluetooth" vs "blueprint" is a spelling coincidence, not a relationship."""
    assert survey.main(["bluetooth pairing"]) == 0
    assert "proceed" in capsys.readouterr().out


def test_keyword_mode_searches_docstrings(capsys: pytest.CaptureFixture[str]) -> None:
    assert survey.main(["validate update manifest schema", "--keywords"]) == 1
    assert "validate_manifest.py" in capsys.readouterr().out


def test_a_single_word_query_does_not_trigger_docstring_scanning() -> None:
    """One token overlaps too much prose to mean anything."""
    assert survey._by_docstring("coverage", [_SCRIPT]) == []


def test_a_missing_search_root_is_skipped(monkeypatch: pytest.MonkeyPatch) -> None:
    """The roots are a fixed list; one absent must not crash the survey."""
    monkeypatch.setattr(survey, "_SEARCH_ROOTS", ("scripts", "no_such_directory"))
    found = survey._candidates()
    assert found
    assert all("no_such_directory" not in str(p) for p in found)


def test_an_unreadable_file_is_skipped_not_fatal(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """A survey that dies on one unreadable file is a survey nobody runs."""
    unreadable = tmp_path / "locked.py"
    unreadable.write_text("x = 1\n", encoding="utf-8")

    def _boom(*args: object, **kwargs: object) -> str:
        raise OSError("permission denied")

    monkeypatch.setattr(Path, "read_text", _boom)
    assert survey._by_docstring("manifest validation schema", [unreadable]) == []


def test_output_uses_posix_separators_on_every_os(capsys: pytest.CaptureFixture[str]) -> None:
    """Windows rendered `scripts\\foo.py` and failed a test asserting `scripts/foo.py`.

    The survey's output is read by humans and asserted by tests on three OSes;
    OS-native separators make it differ per platform for no benefit.
    """
    survey.main(["check_touched_branch_coverage"])
    out = capsys.readouterr().out
    assert "scripts/check_touched_coverage.py" in out
    assert "\\" not in out


def test_rel_is_repo_relative_and_posix() -> None:
    rendered = survey._rel(survey.PROJECT_ROOT / "scripts" / "survey_before_writing.py")
    assert rendered == "scripts/survey_before_writing.py"
