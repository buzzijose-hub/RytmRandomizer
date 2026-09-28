"""Tests for ``scripts/sync_version.py`` — the thin CLI over R1.

The script's whole job is: read the canonical ``VERSION`` once, then rewrite
exactly four derived literals without disturbing any other byte. These tests
therefore lean hard on two properties that a naive implementation gets wrong —
**surgical rewrites** (formatting, key order, and trailing newline survive) and
**idempotence** (running twice changes nothing).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Final

import pytest

PROJECT_ROOT: Final[Path] = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from release_lib import ReleaseError, ViolationCode, parse_version  # noqa: E402
from sync_version import (  # noqa: E402
    DERIVED_SITES,
    EXIT_DRIFT,
    EXIT_OK,
    EXIT_REFUSED,
    DerivedSite,
    SiteResult,
    main,
    sync_versions,
)

pytestmark = pytest.mark.fast

_CARGO: Final[str] = '[package]\nname = "shell"\nversion = "0.1.0"\nedition = "2021"\n'
_TAURI: Final[str] = (
    '{\n  "$schema": "x",\n  "productName": "R",\n  "version": "0.1.0",\n  "identifier": "com.x"\n}\n'
)
_PACKAGE: Final[str] = '{\n  "name": "web",\n  "version": "0.1.0",\n  "private": true\n}\n'
_PYPROJECT: Final[str] = (
    '[project]\nname = "rytm-randomizer"\ndynamic = ["version"]\n\n'
    '[tool.briefcase]\nproject_name = "RytmRandomizer"\nversion = "1.0.0"\n'
    'url = "https://example.invalid"\n'
)


@pytest.fixture
def fake_root(tmp_path: Path) -> Path:
    """A miniature repo carrying all four derived sites plus ``VERSION``."""
    (tmp_path / "VERSION").write_text("1.34.0\n", encoding="utf-8")
    (tmp_path / "pyproject.toml").write_text(_PYPROJECT, encoding="utf-8")
    (tmp_path / "desktop" / "shell").mkdir(parents=True)
    (tmp_path / "desktop" / "web").mkdir(parents=True)
    (tmp_path / "desktop" / "shell" / "Cargo.toml").write_text(_CARGO, encoding="utf-8")
    (tmp_path / "desktop" / "shell" / "tauri.conf.json").write_text(_TAURI, encoding="utf-8")
    (tmp_path / "desktop" / "web" / "package.json").write_text(_PACKAGE, encoding="utf-8")
    return tmp_path


def _read(root: Path, relative: str) -> str:
    return (root / relative).read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# The site table
# ---------------------------------------------------------------------------


def test_all_four_derived_sites_are_declared() -> None:
    """Spec §2.2 + the briefcase literal — four targets, no more, no fewer."""
    assert [site.relative_path for site in DERIVED_SITES] == [
        "pyproject.toml",
        "desktop/shell/Cargo.toml",
        "desktop/shell/tauri.conf.json",
        "desktop/web/package.json",
    ]


def test_every_declared_site_exists_in_the_real_repo() -> None:
    for site in DERIVED_SITES:
        assert (PROJECT_ROOT / site.relative_path).is_file(), site.relative_path


def test_site_label_is_the_relative_path() -> None:
    assert DERIVED_SITES[0].label == "pyproject.toml"


def test_the_real_repo_is_in_sync() -> None:
    """The committed tree must already satisfy `sync_version.py --check`."""
    results = sync_versions(parse_version("1.34.0"), check_only=True, project_root=PROJECT_ROOT)
    assert all(result.in_sync for result in results), [
        (r.site.label, r.previous) for r in results if not r.in_sync
    ]


def test_site_result_reports_sync_state() -> None:
    site = DERIVED_SITES[0]
    assert SiteResult(site=site, previous="1.0.0", canonical="1.0.0").in_sync
    assert not SiteResult(site=site, previous="0.1.0", canonical="1.0.0").in_sync


# ---------------------------------------------------------------------------
# Writing
# ---------------------------------------------------------------------------


def test_sync_rewrites_every_drifted_site(fake_root: Path) -> None:
    results = sync_versions(parse_version("1.34.0"), check_only=False, project_root=fake_root)
    assert len(results) == 4
    assert json.loads(_read(fake_root, "desktop/web/package.json"))["version"] == "1.34.0"
    assert json.loads(_read(fake_root, "desktop/shell/tauri.conf.json"))["version"] == "1.34.0"
    assert 'version = "1.34.0"' in _read(fake_root, "desktop/shell/Cargo.toml")
    assert 'version = "1.34.0"' in _read(fake_root, "pyproject.toml")


def test_sync_reports_the_previous_value_per_site(fake_root: Path) -> None:
    results = sync_versions(parse_version("1.34.0"), check_only=False, project_root=fake_root)
    previous = {result.site.relative_path: result.previous for result in results}
    assert previous == {
        "pyproject.toml": "1.0.0",
        "desktop/shell/Cargo.toml": "0.1.0",
        "desktop/shell/tauri.conf.json": "0.1.0",
        "desktop/web/package.json": "0.1.0",
    }


def test_sync_is_idempotent(fake_root: Path) -> None:
    sync_versions(parse_version("1.34.0"), check_only=False, project_root=fake_root)
    snapshot = {site.relative_path: _read(fake_root, site.relative_path) for site in DERIVED_SITES}
    results = sync_versions(parse_version("1.34.0"), check_only=False, project_root=fake_root)
    assert all(result.in_sync for result in results)
    for relative, text in snapshot.items():
        assert _read(fake_root, relative) == text


def test_sync_preserves_every_other_byte(fake_root: Path) -> None:
    """A surgical span replacement — formatting, key order and newline survive."""
    sync_versions(parse_version("1.34.0"), check_only=False, project_root=fake_root)
    assert _read(fake_root, "desktop/web/package.json") == _PACKAGE.replace("0.1.0", "1.34.0")
    assert _read(fake_root, "desktop/shell/tauri.conf.json") == _TAURI.replace("0.1.0", "1.34.0")
    assert _read(fake_root, "desktop/shell/Cargo.toml") == _CARGO.replace("0.1.0", "1.34.0")


def test_sync_writes_a_prerelease_version(fake_root: Path) -> None:
    sync_versions(parse_version("1.35.0-beta.1"), check_only=False, project_root=fake_root)
    assert json.loads(_read(fake_root, "desktop/web/package.json"))["version"] == "1.35.0-beta.1"


def test_check_only_never_writes(fake_root: Path) -> None:
    before = {site.relative_path: _read(fake_root, site.relative_path) for site in DERIVED_SITES}
    results = sync_versions(parse_version("1.34.0"), check_only=True, project_root=fake_root)
    assert not all(result.in_sync for result in results)
    for relative, text in before.items():
        assert _read(fake_root, relative) == text


# ---------------------------------------------------------------------------
# Refusals — never guess
# ---------------------------------------------------------------------------


def test_missing_target_file_is_a_typed_refusal(fake_root: Path) -> None:
    (fake_root / "desktop" / "web" / "package.json").unlink()
    with pytest.raises(ReleaseError) as excinfo:
        sync_versions(parse_version("1.34.0"), check_only=True, project_root=fake_root)
    assert excinfo.value.code is ViolationCode.VERSION_FILE_MISSING


def test_a_second_pyproject_version_literal_is_refused(fake_root: Path) -> None:
    """A hand-reintroduced ``[project] version`` must fail loudly, not be skipped."""
    text = _read(fake_root, "pyproject.toml").replace('dynamic = ["version"]', 'version = "9.9.9"')
    (fake_root / "pyproject.toml").write_text(text, encoding="utf-8")
    with pytest.raises(ReleaseError) as excinfo:
        sync_versions(parse_version("1.34.0"), check_only=True, project_root=fake_root)
    assert excinfo.value.code is ViolationCode.VERSION_MALFORMED
    assert "2 version declarations" in excinfo.value.detail


def test_a_missing_version_literal_is_refused(fake_root: Path) -> None:
    (fake_root / "desktop" / "shell" / "Cargo.toml").write_text(
        '[package]\nname = "shell"\n', encoding="utf-8"
    )
    with pytest.raises(ReleaseError) as excinfo:
        sync_versions(parse_version("1.34.0"), check_only=True, project_root=fake_root)
    assert excinfo.value.code is ViolationCode.VERSION_MALFORMED
    assert "0 version declarations" in excinfo.value.detail


def test_refusal_detail_carries_no_absolute_path(fake_root: Path) -> None:
    """Gate 7 — a refusal names a repo-relative file, never a home directory."""
    (fake_root / "desktop" / "web" / "package.json").unlink()
    with pytest.raises(ReleaseError) as excinfo:
        sync_versions(parse_version("1.34.0"), check_only=True, project_root=fake_root)
    assert not excinfo.value.detail.startswith("/")
    assert str(fake_root) not in excinfo.value.detail


def test_indented_dependency_versions_are_not_matched(fake_root: Path) -> None:
    """A Cargo dependency version is indented / inline — it must never be rewritten."""
    text = _CARGO + '\n[dependencies]\nserde = { version = "1.0.0" }\n  version = "2.0.0"\n'
    (fake_root / "desktop" / "shell" / "Cargo.toml").write_text(text, encoding="utf-8")
    sync_versions(parse_version("1.34.0"), check_only=False, project_root=fake_root)
    updated = _read(fake_root, "desktop/shell/Cargo.toml")
    assert 'serde = { version = "1.0.0" }' in updated
    assert '  version = "2.0.0"' in updated
    assert 'version = "1.34.0"\nedition' in updated


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


@pytest.fixture
def rooted(fake_root: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Point both the toolkit and the script at the miniature repo."""
    import release_lib
    import sync_version

    monkeypatch.setattr(release_lib, "PROJECT_ROOT", fake_root)
    monkeypatch.setattr(sync_version, "PROJECT_ROOT", fake_root)
    return fake_root


def test_cli_writes_and_reports(rooted: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert main([]) == EXIT_OK
    out = capsys.readouterr().out
    assert "desktop/web/package.json: 0.1.0 -> 1.34.0" in out
    assert json.loads(_read(rooted, "desktop/web/package.json"))["version"] == "1.34.0"


def test_cli_is_idempotent(rooted: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert main([]) == EXIT_OK
    capsys.readouterr()
    assert main([]) == EXIT_OK
    assert "4 declarations already at 1.34.0" in capsys.readouterr().out


def test_cli_check_reports_drift_and_writes_nothing(
    rooted: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    before = _read(rooted, "desktop/web/package.json")
    assert main(["--check"]) == EXIT_DRIFT
    err = capsys.readouterr().err
    assert "declaration(s) drifted from VERSION" in err
    assert "just version-sync" in err
    assert _read(rooted, "desktop/web/package.json") == before


def test_cli_check_passes_once_synced(rooted: Path, capsys: pytest.CaptureFixture[str]) -> None:
    main([])
    capsys.readouterr()
    assert main(["--check"]) == EXIT_OK


def test_cli_refuses_without_a_version_file(
    rooted: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    (rooted / "VERSION").unlink()
    assert main(["--check"]) == EXIT_REFUSED
    err = capsys.readouterr().err
    assert ViolationCode.VERSION_FILE_MISSING.value in err


def test_cli_refuses_a_malformed_version_file(
    rooted: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    (rooted / "VERSION").write_text("not-a-version\n", encoding="utf-8")
    assert main(["--check"]) == EXIT_REFUSED
    assert ViolationCode.VERSION_MALFORMED.value in capsys.readouterr().err


def test_cli_refusal_output_carries_no_absolute_path(
    rooted: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    (rooted / "VERSION").unlink()
    main(["--check"])
    assert str(rooted) not in capsys.readouterr().err


def test_cli_defaults_argv_to_sys_argv(
    rooted: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(sys, "argv", ["sync_version.py", "--check"])
    assert main() == EXIT_DRIFT
    capsys.readouterr()


def test_cli_rejects_an_unknown_flag(rooted: Path) -> None:
    with pytest.raises(SystemExit) as excinfo:
        main(["--nope"])
    assert excinfo.value.code == 2


def test_derived_site_is_frozen() -> None:
    site = DerivedSite("x", DERIVED_SITES[0].pattern)
    with pytest.raises(AttributeError):
        site.relative_path = "y"  # type: ignore[misc]
