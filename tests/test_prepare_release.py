"""Tests for ``scripts/prepare_release.py`` — the conventional-commit deriver.

Every test feeds a **synthetic** commit log as an injected string; nothing here
shells out to ``git``, so the suite is hermetic and reproducible. The script is
loaded by file path (the ``scripts/`` directory is not an importable package),
matching ``tests/test_typecheck_touched_script.py``.

``scripts/prepare_release.py`` imports ``release_lib`` (agent A1's module). If
that module has not landed yet, this file raises a single explicit
``pytest.fail`` at collection time with an actionable message instead of an
opaque ``ImportError`` traceback.
"""

from __future__ import annotations

import io
import json
import logging
import sys
from pathlib import Path
from types import ModuleType
from typing import Final

import pytest

pytestmark = pytest.mark.fast

_REPO_ROOT: Final[Path] = Path(__file__).resolve().parents[1]
_SCRIPT: Final[Path] = _REPO_ROOT / "scripts" / "prepare_release.py"
_RELEASE_LIB: Final[Path] = _REPO_ROOT / "scripts" / "release_lib.py"


def _load_script_module() -> ModuleType:
    import importlib.util

    if not _RELEASE_LIB.exists():
        pytest.fail(
            "scripts/release_lib.py is missing. scripts/prepare_release.py imports "
            "parse_version / compare_versions / read_version_file / Version from it "
            "(reuse contract R1). Land release_lib.py before running this suite.",
            pytrace=False,
        )
    spec = importlib.util.spec_from_file_location("prepare_release_under_test", _SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    # `@dataclass` resolves `cls.__module__` through `sys.modules`, so the
    # module must be registered before `exec_module` runs its class bodies.
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


prepare_release_mod = _load_script_module()
Version = prepare_release_mod.Version


@pytest.fixture(autouse=True)
def _reset_metrics() -> None:
    prepare_release_mod.reset_metrics()


def _v(text: str) -> object:
    return prepare_release_mod.parse_version(text)


DATE: Final[str] = "2026-09-07"


# --------------------------------------------------------------------------
# split_commit_log
# --------------------------------------------------------------------------


def test_split_commit_log_uses_nul_separator_when_present() -> None:
    log = "feat: one\n\nbody line\x00fix: two\x00"
    assert prepare_release_mod.split_commit_log(log) == ("feat: one\n\nbody line", "fix: two")


def test_split_commit_log_falls_back_to_blank_lines() -> None:
    log = "feat: one\n\nfix: two\n \nchore: three\n"
    assert prepare_release_mod.split_commit_log(log) == ("feat: one", "fix: two", "chore: three")


def test_split_commit_log_returns_empty_for_whitespace_only() -> None:
    assert prepare_release_mod.split_commit_log("   \n\n  \n") == ()


# --------------------------------------------------------------------------
# parse_commit
# --------------------------------------------------------------------------


def test_parse_commit_plain_feat() -> None:
    commit = prepare_release_mod.parse_commit("feat: add the update panel")
    assert commit.commit_type == "feat"
    assert commit.scope is None
    assert commit.subject == "add the update panel"
    assert commit.breaking is False
    assert commit.pr_number is None
    assert commit.conventional is True
    assert commit.bump == prepare_release_mod.BUMP_MINOR


def test_parse_commit_with_scope_and_pr_number() -> None:
    commit = prepare_release_mod.parse_commit("fix(updater): drop stale token (#241)")
    assert commit.commit_type == "fix"
    assert commit.scope == "updater"
    assert commit.subject == "drop stale token"
    assert commit.pr_number == 241
    assert commit.bump == prepare_release_mod.BUMP_PATCH


def test_parse_commit_empty_scope_parens_are_dropped() -> None:
    commit = prepare_release_mod.parse_commit("fix(  ): tighten the guard")
    assert commit.scope is None
    assert commit.commit_type == "fix"


def test_parse_commit_bang_marks_breaking() -> None:
    commit = prepare_release_mod.parse_commit("feat(api)!: rename the manifest field")
    assert commit.breaking is True
    assert commit.bump == prepare_release_mod.BUMP_MAJOR


def test_parse_commit_breaking_change_footer_marks_breaking() -> None:
    commit = prepare_release_mod.parse_commit(
        "fix: correct the rollout bucket\n\nBREAKING CHANGE: bucketing changed\n"
    )
    assert commit.breaking is True
    assert commit.bump == prepare_release_mod.BUMP_MAJOR


def test_parse_commit_hyphenated_breaking_change_footer() -> None:
    commit = prepare_release_mod.parse_commit("chore: bump\n\nBREAKING-CHANGE: yes")
    assert commit.breaking is True


def test_parse_commit_malformed_subject_is_unconventional() -> None:
    commit = prepare_release_mod.parse_commit("Merge pull request #230 from foo/bar")
    assert commit.conventional is False
    assert commit.commit_type is None
    assert commit.scope is None
    assert commit.bump == prepare_release_mod.BUMP_NONE


def test_parse_commit_unconventional_subject_still_captures_pr_and_breaking() -> None:
    commit = prepare_release_mod.parse_commit(
        "wholesale rewrite (#99)\n\nBREAKING CHANGE: everything"
    )
    assert commit.conventional is False
    assert commit.pr_number == 99
    assert commit.breaking is True
    assert commit.bump == prepare_release_mod.BUMP_MAJOR


def test_parse_commit_skips_leading_blank_lines() -> None:
    commit = prepare_release_mod.parse_commit("\n\n   \nfeat: after blanks")
    assert commit.commit_type == "feat"
    assert commit.subject == "after blanks"


def test_parse_commit_all_blank_message_yields_empty_unconventional() -> None:
    commit = prepare_release_mod.parse_commit("\n \n")
    assert commit.conventional is False
    assert commit.raw_subject == ""
    assert commit.bump == prepare_release_mod.BUMP_NONE


def test_parse_commit_unknown_type_contributes_no_bump() -> None:
    commit = prepare_release_mod.parse_commit("wibble: something odd")
    assert commit.conventional is True
    assert commit.commit_type == "wibble"
    assert commit.bump == prepare_release_mod.BUMP_NONE


def test_parse_commit_type_is_lowercased() -> None:
    commit = prepare_release_mod.parse_commit("FEAT: shouty")
    assert commit.commit_type == "feat"
    assert commit.bump == prepare_release_mod.BUMP_MINOR


# --------------------------------------------------------------------------
# classify_commits / derive_bump
# --------------------------------------------------------------------------


def test_classify_commits_on_empty_log_raises_typed_error() -> None:
    with pytest.raises(prepare_release_mod.CommitLogEmptyError) as excinfo:
        prepare_release_mod.classify_commits("   \n\n")
    assert excinfo.value.fingerprint == "release.prepare.log.empty"
    metrics = prepare_release_mod.get_metrics()
    assert metrics.errors_by_fingerprint["release.prepare.log.empty"] == 1


@pytest.mark.parametrize(
    ("log", "expected"),
    [
        ("feat!: nuke\x00fix: patch", "major"),
        ("feat: add\x00fix: patch\x00docs: note", "minor"),
        ("fix: patch\x00docs: note", "patch"),
        ("perf: faster", "patch"),
        ("revert: undo", "patch"),
        # Spec §2 rule 4: "else PATCH" — a trivial-only range still cuts a patch.
        ("docs: note\x00chore: tidy\x00ci: pin\x00test: cover", "patch"),
        ("Merge branch 'x'", "patch"),
    ],
)
def test_derive_bump_reports_the_highest_applicable(log: str, expected: str) -> None:
    commits = prepare_release_mod.classify_commits(log)
    assert prepare_release_mod.derive_bump(commits) == expected


@pytest.mark.parametrize(
    ("log", "expected"),
    [
        ("docs: note\x00chore: tidy", "none"),
        ("Merge branch 'x'", "none"),
        ("fix: repair", "patch"),
        ("feat: add", "minor"),
        ("feat!: break", "major"),
    ],
)
def test_derive_bump_with_a_none_floor_uses_the_strict_reading(log: str, expected: str) -> None:
    commits = prepare_release_mod.classify_commits(log)
    assert prepare_release_mod.derive_bump(commits, floor=prepare_release_mod.BUMP_NONE) == expected


def test_derive_bump_on_no_commits_returns_the_floor() -> None:
    assert prepare_release_mod.derive_bump(()) == prepare_release_mod.BUMP_PATCH
    assert (
        prepare_release_mod.derive_bump((), floor=prepare_release_mod.BUMP_NONE)
        == prepare_release_mod.BUMP_NONE
    )


# --------------------------------------------------------------------------
# apply_bump
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("current", "bump", "expected"),
    [
        ("1.34.0", "major", "2.0.0"),
        ("1.34.0", "minor", "1.35.0"),
        ("1.34.0", "patch", "1.34.1"),
        ("1.34.0", "none", "1.34.0"),
        ("1.34.2", "minor", "1.35.0"),
    ],
)
def test_apply_bump_release_versions(current: str, bump: str, expected: str) -> None:
    assert str(prepare_release_mod.apply_bump(_v(current), bump)) == expected


def test_apply_bump_finalizes_a_prerelease_when_bump_already_encoded() -> None:
    # 1.35.0-beta.1 already encodes the minor bump -> finalize, do not re-bump.
    assert str(prepare_release_mod.apply_bump(_v("1.35.0-beta.1"), "minor")) == "1.35.0"
    assert str(prepare_release_mod.apply_bump(_v("1.35.0-beta.1"), "patch")) == "1.35.0"


def test_apply_bump_finalizes_major_prerelease() -> None:
    assert str(prepare_release_mod.apply_bump(_v("2.0.0-rc.1"), "major")) == "2.0.0"


def test_apply_bump_finalizes_patch_prerelease() -> None:
    assert str(prepare_release_mod.apply_bump(_v("1.34.1-beta.1"), "patch")) == "1.34.1"


def test_apply_bump_stronger_bump_moves_past_a_prerelease() -> None:
    assert str(prepare_release_mod.apply_bump(_v("1.35.0-beta.1"), "major")) == "2.0.0"
    assert str(prepare_release_mod.apply_bump(_v("1.34.1-beta.1"), "minor")) == "1.35.0"


def test_apply_bump_none_leaves_a_prerelease_untouched() -> None:
    assert str(prepare_release_mod.apply_bump(_v("1.35.0-beta.1"), "none")) == "1.35.0-beta.1"


# --------------------------------------------------------------------------
# render_changelog_section
# --------------------------------------------------------------------------


def test_render_changelog_section_groups_by_type_in_canonical_order() -> None:
    commits = prepare_release_mod.classify_commits(
        "chore: tidy\x00fix: repair the chip (#12)\x00feat(update): add panel\x00Merge foo"
    )
    section = prepare_release_mod.render_changelog_section(_v("1.35.0"), commits, release_date=DATE)
    assert section.startswith("## [1.35.0] - 2026-09-07\n")
    assert section.index("### Added") < section.index("### Fixed")
    assert section.index("### Fixed") < section.index("### Chores")
    assert section.index("### Chores") < section.index("### Other")
    assert "- **update**: add panel" in section
    assert (
        "- repair the chip "
        "([#12](https://github.com/buzzijose-hub/RytmRandomizer/pull/12))" in section
    )
    assert "- Merge foo" in section
    assert section.endswith("\n")
    assert not section.endswith("\n\n")


def test_render_changelog_section_marks_breaking_entries() -> None:
    commits = prepare_release_mod.classify_commits("feat!: rename manifest field")
    section = prepare_release_mod.render_changelog_section(_v("2.0.0"), commits, release_date=DATE)
    assert "- **BREAKING** — rename manifest field" in section


def test_render_changelog_section_honors_a_custom_pr_base_url() -> None:
    commits = prepare_release_mod.classify_commits("fix: thing (#7)")
    section = prepare_release_mod.render_changelog_section(
        _v("1.34.1"), commits, release_date=DATE, pr_base_url="https://example.test/pr"
    )
    assert "([#7](https://example.test/pr/7))" in section


def test_render_changelog_section_with_no_commits_raises_typed_error() -> None:
    with pytest.raises(prepare_release_mod.ChangelogRenderError) as excinfo:
        prepare_release_mod.render_changelog_section(_v("1.0.0"), (), release_date=DATE)
    assert excinfo.value.fingerprint == "release.prepare.changelog.render_failed"


def test_render_changelog_section_is_deterministic() -> None:
    commits = prepare_release_mod.classify_commits("feat: a\x00fix: b")
    first = prepare_release_mod.render_changelog_section(_v("1.35.0"), commits, release_date=DATE)
    second = prepare_release_mod.render_changelog_section(_v("1.35.0"), commits, release_date=DATE)
    assert first == second


# --------------------------------------------------------------------------
# prepare_release
# --------------------------------------------------------------------------


def test_prepare_release_end_to_end_minor() -> None:
    result = prepare_release_mod.prepare_release(
        "feat: add the update chip (#240)\x00fix: repair a leak",
        current_version=_v("1.34.0"),
        release_date=DATE,
    )
    assert result.bump == "minor"
    assert str(result.next_version) == "1.35.0"
    assert result.changed is True
    assert len(result.commits) == 2


def test_prepare_release_trivial_range_still_cuts_a_patch_by_default() -> None:
    # Spec §2 rule 4: BREAKING/! => MAJOR, feat => MINOR, else PATCH.
    result = prepare_release_mod.prepare_release(
        "docs: tidy the README",
        current_version=_v("1.34.0"),
        release_date=DATE,
    )
    assert result.bump == "patch"
    assert str(result.next_version) == "1.34.1"
    assert result.changed is True
    assert prepare_release_mod.get_metrics().outcomes["derived"] == 1


def test_prepare_release_no_bump_floor_keeps_the_current_version() -> None:
    result = prepare_release_mod.prepare_release(
        "docs: tidy the README",
        current_version=_v("1.34.0"),
        release_date=DATE,
        bump_floor=prepare_release_mod.BUMP_NONE,
    )
    assert result.bump == "none"
    assert str(result.next_version) == "1.34.0"
    assert result.changed is False
    assert prepare_release_mod.get_metrics().outcomes["no_bump"] == 1


def test_prepare_release_records_the_derived_outcome_metric() -> None:
    prepare_release_mod.prepare_release("feat: x", current_version=_v("1.0.0"), release_date=DATE)
    assert prepare_release_mod.get_metrics().outcomes["derived"] == 1


@pytest.fixture
def propagating_package_logger(monkeypatch: pytest.MonkeyPatch) -> None:
    """Let caplog see records from a ``rytm_randomizer.*`` logger.

    ``tests/conftest.py``'s ``isolated_observability`` fixture leaves
    ``logging.getLogger("rytm_randomizer").propagate = False`` behind, so once
    any observability test has run, records from descendant loggers never reach
    caplog's root handler — and log assertions here fail ONLY when the suites
    run together. Restore propagation for the duration of the test.
    """
    monkeypatch.setattr(logging.getLogger("rytm_randomizer"), "propagate", True)


def test_prepare_release_logs_a_structured_record(
    caplog: pytest.LogCaptureFixture, propagating_package_logger: None
) -> None:
    with caplog.at_level(logging.INFO, logger=prepare_release_mod.LOGGER_NAME):
        prepare_release_mod.prepare_release(
            "feat: x", current_version=_v("1.0.0"), release_date=DATE
        )
    # Select by fingerprint rather than position: `caplog` sees every logger,
    # so a sibling module logging during this call would make `records[-1]`
    # the wrong record (or the list empty) only when the suites run together.
    derived = [
        r for r in caplog.records if getattr(r, "fingerprint", None) == "release.prepare.derived"
    ]
    assert (
        derived
    ), f"no derived record; saw {[getattr(r, 'fingerprint', r.msg) for r in caplog.records]}"
    record = derived[-1]
    assert record.fingerprint == "release.prepare.derived"
    assert record.bump == "minor"
    assert record.next_version == "1.1.0"


def test_prepare_release_rejects_a_non_advancing_derivation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(prepare_release_mod, "apply_bump", lambda current, bump: _v("0.0.1"))
    with pytest.raises(prepare_release_mod.VersionDerivationError) as excinfo:
        prepare_release_mod.prepare_release(
            "feat: x", current_version=_v("1.34.0"), release_date=DATE
        )
    assert excinfo.value.fingerprint == "release.prepare.version.invalid"
    assert "1.34.0" in excinfo.value.detail


def test_prepare_release_error_detail_carries_no_absolute_path() -> None:
    with pytest.raises(prepare_release_mod.CommitLogEmptyError) as excinfo:
        prepare_release_mod.prepare_release("", current_version=_v("1.0.0"), release_date=DATE)
    assert "/" not in excinfo.value.detail


def test_to_json_object_shape() -> None:
    result = prepare_release_mod.prepare_release(
        "feat!: break it (#5)\x00Merge branch 'x'",
        current_version=_v("1.34.0"),
        release_date=DATE,
    )
    payload = result.to_json_object()
    assert payload["current_version"] == "1.34.0"
    assert payload["next_version"] == "2.0.0"
    assert payload["bump"] == "major"
    assert payload["changed"] is True
    assert payload["commit_count"] == 2
    assert payload["breaking_count"] == 1
    assert payload["unconventional_count"] == 1
    assert payload["commits"][0]["pr_number"] == 5


# --------------------------------------------------------------------------
# render_pr_body
# --------------------------------------------------------------------------


def test_render_pr_body_includes_breaking_section() -> None:
    result = prepare_release_mod.prepare_release(
        "feat!: rename the manifest field",
        current_version=_v("1.34.0"),
        release_date=DATE,
    )
    body = prepare_release_mod.render_pr_body(result)
    assert "# Release 2.0.0" in body
    assert "Derived bump: **major**." in body
    assert "## Breaking changes" in body
    assert "- rename the manifest field" in body
    assert "scripts/sync_version.py" in body


def test_render_pr_body_no_bump_omits_breaking_section() -> None:
    result = prepare_release_mod.prepare_release(
        "docs: tidy",
        current_version=_v("1.34.0"),
        release_date=DATE,
        bump_floor=prepare_release_mod.BUMP_NONE,
    )
    body = prepare_release_mod.render_pr_body(result)
    assert "No release-worthy commits in range" in body
    assert "## Breaking changes" not in body


def test_render_pr_body_breaking_falls_back_to_raw_subject() -> None:
    # An unconventional subject has `subject == raw_subject`; an empty-string
    # subject (all-blank message) must fall through to the raw subject rather
    # than emitting a bare "- " bullet.
    commit = prepare_release_mod.ParsedCommit(
        raw_subject="rewrote everything",
        commit_type=None,
        scope=None,
        subject="",
        breaking=True,
        pr_number=None,
        conventional=False,
    )
    preparation = prepare_release_mod.ReleasePreparation(
        current_version=_v("1.34.0"),
        next_version=_v("2.0.0"),
        bump="major",
        commits=(commit,),
        changelog_section="## [2.0.0] - 2026-09-07\n",
    )
    body = prepare_release_mod.render_pr_body(preparation)
    assert "## Breaking changes" in body
    assert "- rewrote everything" in body


def test_render_pr_body_breaking_footer_on_the_subject_line_is_unconventional() -> None:
    # `git log` bodies that lead with the footer put it on the subject line;
    # the deriver treats that as an unconventional subject and no bump.
    result = prepare_release_mod.prepare_release(
        "\n\nBREAKING CHANGE: no subject line at all",
        current_version=_v("1.34.0"),
        release_date=DATE,
        bump_floor=prepare_release_mod.BUMP_NONE,
    )
    assert result.bump == "none"
    assert result.commits[0].conventional is False
    assert "## Breaking changes" not in prepare_release_mod.render_pr_body(result)


# --------------------------------------------------------------------------
# metrics surface
# --------------------------------------------------------------------------


def test_metrics_format_summary_empty_and_populated() -> None:
    metrics = prepare_release_mod.get_metrics()
    assert metrics.format_summary() == "ReleasePrepareMetrics(outcomes=-, errors=-)"
    metrics.record_outcome("derived")
    metrics.record_error("release.prepare.log.empty")
    summary = metrics.format_summary()
    assert "derived=1" in summary
    assert "release.prepare.log.empty=1" in summary


def test_reset_metrics_clears_both_counters() -> None:
    metrics = prepare_release_mod.get_metrics()
    metrics.record_outcome("derived")
    metrics.record_error("x")
    prepare_release_mod.reset_metrics()
    assert metrics.format_summary() == "ReleasePrepareMetrics(outcomes=-, errors=-)"


def test_base_error_carries_the_placeholder_fingerprint() -> None:
    error = prepare_release_mod.ReleasePreparationError("boom")
    assert error.fingerprint == "release.prepare.error.unspecified"
    assert "release.prepare.error.unspecified" in str(error)
    assert error.detail == "boom"


def test_failure_emits_a_structured_error_log(
    caplog: pytest.LogCaptureFixture, propagating_package_logger: None
) -> None:
    with caplog.at_level(logging.ERROR, logger=prepare_release_mod.LOGGER_NAME):
        with pytest.raises(prepare_release_mod.CommitLogEmptyError):
            prepare_release_mod.classify_commits("")
    empty = [
        r for r in caplog.records if getattr(r, "fingerprint", None) == "release.prepare.log.empty"
    ]
    assert (
        empty
    ), f"no empty-log record; saw {[getattr(r, 'fingerprint', r.msg) for r in caplog.records]}"
    record = empty[-1]
    assert record.fingerprint == "release.prepare.log.empty"
    assert "ReleasePrepareMetrics" in record.metrics


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------


def _run(argv: list[str], *, stdin_text: str | None = None) -> tuple[int, str]:
    stream = io.StringIO()
    code = prepare_release_mod.main(argv, stdin_text=stdin_text, stream=stream)
    return code, stream.getvalue()


def test_cli_stdin_default_output() -> None:
    code, out = _run(
        ["--log-stdin", "--date", DATE, "--current-version", "1.34.0"],
        stdin_text="feat: add a chip\x00fix: repair (#3)",
    )
    assert code == 0
    assert "bump: minor" in out
    assert "next_version: 1.35.0" in out
    assert "## [1.35.0] - 2026-09-07" in out


def test_cli_json_mode_is_machine_readable() -> None:
    code, out = _run(
        ["--log-stdin", "--date", DATE, "--current-version", "1.34.0", "--json"],
        stdin_text="fix: repair",
    )
    assert code == 0
    payload = json.loads(out)
    assert payload["next_version"] == "1.34.1"
    assert payload["bump"] == "patch"


def test_cli_defaults_to_the_spec_patch_floor() -> None:
    code, out = _run(
        ["--log-stdin", "--date", DATE, "--current-version", "1.34.0"],
        stdin_text="docs: tidy the README",
    )
    assert code == 0
    assert "bump: patch" in out
    assert "next_version: 1.34.1" in out


def test_cli_no_bump_on_trivial_selects_the_strict_reading() -> None:
    code, out = _run(
        [
            "--log-stdin",
            "--date",
            DATE,
            "--current-version",
            "1.34.0",
            "--no-bump-on-trivial",
        ],
        stdin_text="docs: tidy the README",
    )
    assert code == 0
    assert "bump: none" in out
    assert "next_version: 1.34.0" in out


def test_cli_pr_body_mode() -> None:
    code, out = _run(
        ["--log-stdin", "--date", DATE, "--current-version", "1.34.0", "--pr-body"],
        stdin_text="feat: add a chip",
    )
    assert code == 0
    assert "# Release 1.35.0" in out


def test_cli_dry_run_prints_a_banner_and_writes_nothing(tmp_path: Path) -> None:
    before = sorted(tmp_path.iterdir())
    code, out = _run(
        ["--log-stdin", "--date", DATE, "--current-version", "1.34.0", "--dry-run"],
        stdin_text="feat: add a chip",
    )
    assert code == 0
    assert "dry-run: proposing only" in out
    assert sorted(tmp_path.iterdir()) == before


def test_cli_dry_run_combined_with_pr_body() -> None:
    code, out = _run(
        [
            "--log-stdin",
            "--date",
            DATE,
            "--current-version",
            "1.34.0",
            "--dry-run",
            "--pr-body",
        ],
        stdin_text="feat: add a chip",
    )
    assert code == 0
    assert "dry-run: proposing only" in out
    assert "# Release 1.35.0" in out


def test_cli_log_file_source(tmp_path: Path) -> None:
    log_path = tmp_path / "commits.txt"
    log_path.write_text("feat: from a file", encoding="utf-8")
    code, out = _run(["--log-file", str(log_path), "--date", DATE, "--current-version", "1.0.0"])
    assert code == 0
    assert "next_version: 1.1.0" in out


def test_cli_missing_log_file_reports_the_typed_error(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    missing = tmp_path / "nope.txt"
    code, _out = _run(["--log-file", str(missing), "--date", DATE, "--current-version", "1.0.0"])
    assert code == 1
    captured = capsys.readouterr()
    assert "release.prepare.log.read_failed" in captured.err
    assert (
        prepare_release_mod.get_metrics().errors_by_fingerprint["release.prepare.log.read_failed"]
        == 1
    )


def test_cli_non_utf8_log_file_reports_the_typed_error(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    log_path = tmp_path / "bad.bin"
    log_path.write_bytes(b"\xff\xfe not utf-8")
    code, _out = _run(["--log-file", str(log_path), "--date", DATE, "--current-version", "1.0.0"])
    assert code == 1
    assert "release.prepare.log.read_failed" in capsys.readouterr().err


def test_cli_invalid_current_version_reports_the_typed_error(
    capsys: pytest.CaptureFixture[str],
) -> None:
    code, _out = _run(
        ["--log-stdin", "--date", DATE, "--current-version", "not-a-version"],
        stdin_text="feat: x",
    )
    assert code == 1
    assert "release.prepare.version.invalid" in capsys.readouterr().err


def test_cli_reads_the_version_file_when_no_override(tmp_path: Path) -> None:
    (tmp_path / "VERSION").write_text("1.34.0\n", encoding="utf-8")
    code, out = _run(
        ["--log-stdin", "--date", DATE, "--repo-root", str(tmp_path)],
        stdin_text="fix: repair",
    )
    assert code == 0
    assert "next_version: 1.34.1" in out


def test_cli_missing_version_file_reports_the_typed_error(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    code, _out = _run(
        ["--log-stdin", "--date", DATE, "--repo-root", str(tmp_path / "absent")],
        stdin_text="fix: repair",
    )
    assert code == 1
    assert "release.prepare.version.invalid" in capsys.readouterr().err


def test_cli_empty_log_reports_the_typed_error(capsys: pytest.CaptureFixture[str]) -> None:
    code, _out = _run(
        ["--log-stdin", "--date", DATE, "--current-version", "1.0.0"], stdin_text="  \n"
    )
    assert code == 1
    assert "release.prepare.log.empty" in capsys.readouterr().err


def test_cli_requires_a_log_source() -> None:
    with pytest.raises(SystemExit):
        prepare_release_mod.main(["--date", DATE], stdin_text="")


def test_cli_reads_real_stdin_when_no_injection(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("sys.stdin", io.StringIO("feat: piped in"))
    stream = io.StringIO()
    code = prepare_release_mod.main(
        ["--log-stdin", "--date", DATE, "--current-version", "1.0.0"], stream=stream
    )
    assert code == 0
    assert "next_version: 1.1.0" in stream.getvalue()


def test_cli_defaults_to_sys_stdout(capsys: pytest.CaptureFixture[str]) -> None:
    code = prepare_release_mod.main(
        ["--log-stdin", "--date", DATE, "--current-version", "1.0.0"],
        stdin_text="fix: repair",
    )
    assert code == 0
    assert "next_version: 1.0.1" in capsys.readouterr().out


def test_cli_argv_defaults_to_process_arguments(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "sys.argv",
        ["prepare_release.py", "--log-stdin", "--date", DATE, "--current-version", "1.0.0"],
    )
    stream = io.StringIO()
    code = prepare_release_mod.main(stdin_text="feat: x", stream=stream)
    assert code == 0
    assert "next_version: 1.1.0" in stream.getvalue()


# --------------------------------------------------------------------------
# The script never writes the VERSION file (spec §2.4 rule 5)
# --------------------------------------------------------------------------


def test_script_source_never_writes_the_version_file() -> None:
    source = _SCRIPT.read_text(encoding="utf-8")
    for forbidden in ("write_text(", "open(", "write_bytes(", "mkdir("):
        assert forbidden not in source, f"prepare_release.py must not call {forbidden}"


def test_module_docstring_states_it_never_writes_version() -> None:
    assert "NEVER writes the ``VERSION`` file" in prepare_release_mod.__doc__
