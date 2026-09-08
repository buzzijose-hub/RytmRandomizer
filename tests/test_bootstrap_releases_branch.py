"""Tests for the idempotent ``releases`` branch bootstrapper.

Every test that touches git runs against a throwaway repository created under
``tmp_path``. The real repository is never written to, and no test invokes a
network verb — a sentinel test asserts that the script's source contains no
``push``/``fetch`` and no force-update flag at all.
"""

from __future__ import annotations

import importlib.util
import json
import logging
import subprocess
import sys
from pathlib import Path
from types import ModuleType
from typing import Final

import pytest

pytestmark = pytest.mark.fast

_REPO_ROOT: Final[Path] = Path(__file__).resolve().parents[1]
_SCRIPT: Final[Path] = _REPO_ROOT / "scripts" / "bootstrap_releases_branch.py"
_SEED_DIR: Final[Path] = _REPO_ROOT / "releases_branch_seed"
_SEED_FILENAMES: Final[frozenset[str]] = frozenset(
    {"README.md", "beta.json", "fleet-history.json", "stable.json"}
)


def _load_script_module() -> ModuleType:
    spec = importlib.util.spec_from_file_location("bootstrap_releases_branch", _SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    # Register before execution: the module defines a dataclass, and
    # ``dataclasses`` resolves the defining module through ``sys.modules``.
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


bootstrap_releases_branch = _load_script_module()
BootstrapError = bootstrap_releases_branch.BootstrapReleasesBranchError


def _git(repo: Path, *arguments: str) -> str:
    completed = subprocess.run(
        ["git", *arguments],
        cwd=repo,
        capture_output=True,
        check=True,
        text=True,
    )
    return completed.stdout.strip()


@pytest.fixture()
def temp_repo(tmp_path: Path) -> Path:
    """An initialized repository with one commit on its default branch."""

    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init")
    _git(repo, "config", "user.email", "tests@example.invalid")
    _git(repo, "config", "user.name", "RytmRandomizer Tests")
    (repo / "keep.txt").write_text("baseline\n", encoding="utf-8")
    _git(repo, "add", "keep.txt")
    _git(repo, "commit", "-m", "baseline")
    return repo


def _write_seed(repo: Path, *, extra: dict[str, str] | None = None) -> Path:
    """Copy the real seed directory into ``repo`` and return its path."""

    seed = repo / bootstrap_releases_branch.SEED_RELATIVE_PATH
    seed.mkdir(parents=True)
    for source in sorted(_SEED_DIR.iterdir()):
        if source.is_file():
            (seed / source.name).write_bytes(source.read_bytes())
    for name, content in (extra or {}).items():
        (seed / name).write_text(content, encoding="utf-8")
    return seed


# --------------------------------------------------------------------------
# The load-bearing semantic: an empty manifest means "no update available".
# --------------------------------------------------------------------------


@pytest.mark.parametrize("manifest_name", ["stable.json", "beta.json"])
def test_seeded_manifest_parses_as_no_update_available_never_an_error(
    manifest_name: str,
) -> None:
    """The first manifest every client fetches must read as "you are current".

    This is the single most load-bearing semantic on the branch: a fleet-wide
    false error on day one would be indistinguishable from the whole update
    system being broken. The seed therefore encodes "no update" three
    independent ways, each asserted below.
    """

    document = json.loads((_SEED_DIR / manifest_name).read_text(encoding="utf-8"))

    # It parses at all, so a client can never treat the seed as a failed check.
    assert isinstance(document, dict)
    # Schema-identifying fields are present so a client can dispatch on them.
    assert document["schema_version"] == 1
    assert document["channel"] == manifest_name.removesuffix(".json")

    # 1. Strict SemVer (spec §4) — NOT null, which would fail validation and
    #    turn the very first fetch into an error instead of a clean "no update".
    #    "0.0.0" is the lowest possible version, so it is never *newer* than a
    #    running install and the §4 "act only when newer" rule declines on it.
    assert document["version"] == "0.0.0"
    # 2. No artifact exists for any target, so there is nothing to stage.
    assert document["platforms"] == {}
    # 3. No bucket satisfies ``bucket < 0``, so it is offered to nobody.
    assert document["rollout_percent"] == 0

    # The reserved advisory field exists from day one (spec §4) but is unset.
    assert document["minimum_version"] is None
    assert document["hardware_revalidation"] is False


@pytest.mark.parametrize("manifest_name", ["stable.json", "beta.json"])
def test_seeded_manifest_version_is_never_newer_than_any_real_release(
    manifest_name: str,
) -> None:
    """The seed version must lose a SemVer comparison against any real version."""

    document = json.loads((_SEED_DIR / manifest_name).read_text(encoding="utf-8"))
    seed_version = tuple(int(part) for part in document["version"].split("."))

    # Against today's shipping version and against the lowest plausible release.
    assert seed_version < (1, 34, 0)
    assert seed_version < (0, 0, 1)


@pytest.mark.parametrize("manifest_name", ["stable.json", "beta.json"])
def test_seeded_manifest_carries_inert_provenance(manifest_name: str) -> None:
    """``build`` is informational only (spec §4) — present, but zero-valued."""

    document = json.loads((_SEED_DIR / manifest_name).read_text(encoding="utf-8"))
    build = document["build"]

    assert set(build) == {"source_sha", "workflow_run_url", "builder_workflow_sha"}
    assert build["source_sha"] == "0" * 40
    assert build["builder_workflow_sha"] == "0" * 40


def test_seeded_fleet_history_is_an_empty_array() -> None:
    """An empty history is a fleet nobody has measured yet — not an error."""

    document = json.loads((_SEED_DIR / "fleet-history.json").read_text(encoding="utf-8"))

    assert document == []


def test_seed_directory_holds_exactly_the_four_expected_files() -> None:
    present = {entry.name for entry in _SEED_DIR.iterdir() if entry.is_file()}

    assert present == set(_SEED_FILENAMES)


def test_seed_readme_documents_the_no_update_semantic_and_machine_authorship() -> None:
    readme = (_SEED_DIR / "README.md").read_text(encoding="utf-8")

    assert "No update is available" in readme
    assert "Do not hand-edit" in readme
    # It must name which workflow writes each file.
    for workflow in ("release.yml", "promote.yml", "fleet-snapshot.yml"):
        assert workflow in readme


# --------------------------------------------------------------------------
# Idempotency and ref discipline.
# --------------------------------------------------------------------------


def test_bootstrap_creates_the_branch_with_the_seed_content(temp_repo: Path) -> None:
    seed = _write_seed(temp_repo)

    outcome = bootstrap_releases_branch.bootstrap(repo_root=temp_repo, seed_dir=seed)

    assert outcome.action == "created"
    assert outcome.created is True
    assert outcome.branch == "releases"
    assert outcome.commit is not None
    assert set(outcome.seeded_files) == set(_SEED_FILENAMES)
    listed = _git(temp_repo, "ls-tree", "--name-only", "releases").splitlines()
    assert sorted(listed) == sorted(outcome.seeded_files)
    blob = _git(temp_repo, "show", "releases:stable.json")
    assert json.loads(blob)["version"] == "0.0.0"


def test_bootstrap_creates_an_orphan_commit_and_leaves_head_untouched(
    temp_repo: Path,
) -> None:
    seed = _write_seed(temp_repo)
    head_before = _git(temp_repo, "rev-parse", "HEAD")
    branch_before = _git(temp_repo, "rev-parse", "--abbrev-ref", "HEAD")
    refs_before = set(
        _git(temp_repo, "for-each-ref", "--format=%(refname)", "refs/heads/").splitlines()
    )
    tracked_before = _git(temp_repo, "ls-files")

    bootstrap_releases_branch.bootstrap(repo_root=temp_repo, seed_dir=seed)

    # The new commit has no parent — a true orphan branch.
    assert _git(temp_repo, "rev-list", "--count", "releases") == "1"
    # HEAD, the checked-out branch, and every pre-existing ref are unchanged.
    assert _git(temp_repo, "rev-parse", "HEAD") == head_before
    assert _git(temp_repo, "rev-parse", "--abbrev-ref", "HEAD") == branch_before
    refs_after = set(
        _git(temp_repo, "for-each-ref", "--format=%(refname)", "refs/heads/").splitlines()
    )
    assert refs_after - refs_before == {"refs/heads/releases"}
    assert refs_before <= refs_after
    # Nothing was staged: the index is untouched, so the seed files were never
    # added to the caller's index and the tracked file set is unchanged.
    assert _git(temp_repo, "diff", "--cached", "--name-only") == ""
    assert _git(temp_repo, "ls-files") == tracked_before


def test_bootstrap_is_a_no_op_when_the_branch_already_exists(temp_repo: Path) -> None:
    seed = _write_seed(temp_repo)
    first = bootstrap_releases_branch.bootstrap(repo_root=temp_repo, seed_dir=seed)

    second = bootstrap_releases_branch.bootstrap(repo_root=temp_repo, seed_dir=seed)

    assert second.action == "already_exists"
    assert second.created is False
    assert second.commit is None
    # The existing branch is untouched — not rewritten, not amended.
    assert _git(temp_repo, "rev-parse", "releases") == first.commit


def test_bootstrap_no_op_does_not_rewrite_a_diverged_existing_branch(
    temp_repo: Path,
) -> None:
    """An unrelated pre-existing ``releases`` ref must survive verbatim."""

    seed = _write_seed(temp_repo)
    _git(temp_repo, "branch", "releases")
    existing = _git(temp_repo, "rev-parse", "releases")

    outcome = bootstrap_releases_branch.bootstrap(repo_root=temp_repo, seed_dir=seed)

    assert outcome.action == "already_exists"
    assert _git(temp_repo, "rev-parse", "releases") == existing


def test_dry_run_reports_the_plan_and_writes_no_ref(temp_repo: Path) -> None:
    seed = _write_seed(temp_repo)

    outcome = bootstrap_releases_branch.bootstrap(repo_root=temp_repo, seed_dir=seed, dry_run=True)

    assert outcome.action == "dry_run"
    assert outcome.created is False
    assert outcome.commit is None
    assert "stable.json" in outcome.seeded_files
    assert bootstrap_releases_branch.branch_exists("releases", repo_root=temp_repo) is False


def test_dry_run_on_an_existing_branch_reports_the_no_op(temp_repo: Path) -> None:
    seed = _write_seed(temp_repo)
    _git(temp_repo, "branch", "releases")

    outcome = bootstrap_releases_branch.bootstrap(repo_root=temp_repo, seed_dir=seed, dry_run=True)

    assert outcome.action == "already_exists"


def test_custom_branch_name_is_honored(temp_repo: Path) -> None:
    seed = _write_seed(temp_repo)

    outcome = bootstrap_releases_branch.bootstrap(
        repo_root=temp_repo, seed_dir=seed, branch="releases-scratch"
    )

    assert outcome.branch == "releases-scratch"
    assert bootstrap_releases_branch.branch_exists("releases-scratch", repo_root=temp_repo)
    assert bootstrap_releases_branch.branch_exists("releases", repo_root=temp_repo) is False


def test_seed_dir_defaults_to_the_repository_seed_directory(temp_repo: Path) -> None:
    _write_seed(temp_repo)

    outcome = bootstrap_releases_branch.bootstrap(repo_root=temp_repo, seed_dir=None)

    assert outcome.action == "created"


def test_nested_directories_inside_the_seed_are_not_published(temp_repo: Path) -> None:
    seed = _write_seed(temp_repo)
    (seed / "nested").mkdir()
    (seed / "nested" / "ignored.json").write_text("{}", encoding="utf-8")

    outcome = bootstrap_releases_branch.bootstrap(repo_root=temp_repo, seed_dir=seed)

    assert "nested" not in outcome.seeded_files
    assert "nested" not in _git(temp_repo, "ls-tree", "--name-only", "releases")


# --------------------------------------------------------------------------
# Typed failure paths.
# --------------------------------------------------------------------------


def test_missing_seed_directory_raises_seed_missing(temp_repo: Path) -> None:
    with pytest.raises(BootstrapError) as caught:
        bootstrap_releases_branch.bootstrap(repo_root=temp_repo, seed_dir=temp_repo / "absent")

    assert caught.value.code == "bootstrap.seed_missing"


def test_empty_seed_directory_raises_seed_empty(temp_repo: Path) -> None:
    seed = temp_repo / bootstrap_releases_branch.SEED_RELATIVE_PATH
    seed.mkdir(parents=True)

    with pytest.raises(BootstrapError) as caught:
        bootstrap_releases_branch.bootstrap(repo_root=temp_repo, seed_dir=seed)

    assert caught.value.code == "bootstrap.seed_empty"


def test_seed_directory_holding_only_subdirectories_raises_seed_empty(
    temp_repo: Path,
) -> None:
    """The ``continue`` branch must not be able to yield an empty publish."""

    seed = temp_repo / bootstrap_releases_branch.SEED_RELATIVE_PATH
    (seed / "only_a_dir").mkdir(parents=True)

    with pytest.raises(BootstrapError) as caught:
        bootstrap_releases_branch.bootstrap(repo_root=temp_repo, seed_dir=seed)

    assert caught.value.code == "bootstrap.seed_empty"


def test_unreadable_seed_file_raises_seed_unreadable(
    temp_repo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    seed = _write_seed(temp_repo)
    original = Path.read_bytes

    def _explode(self: Path) -> bytes:
        if self.name == "stable.json":
            raise OSError("unreadable")
        return original(self)

    monkeypatch.setattr(Path, "read_bytes", _explode)

    with pytest.raises(BootstrapError) as caught:
        bootstrap_releases_branch.collect_seed_files(seed, repo_root=temp_repo)

    assert caught.value.code == "bootstrap.seed_unreadable"
    assert "stable.json" in caught.value.detail


def test_malformed_manifest_json_raises_manifest_invalid(temp_repo: Path) -> None:
    seed = _write_seed(temp_repo)
    (seed / "stable.json").write_text("{not json", encoding="utf-8")

    with pytest.raises(BootstrapError) as caught:
        bootstrap_releases_branch.bootstrap(repo_root=temp_repo, seed_dir=seed)

    assert caught.value.code == "bootstrap.manifest_invalid"
    assert bootstrap_releases_branch.branch_exists("releases", repo_root=temp_repo) is False


def test_non_utf8_manifest_raises_manifest_invalid(temp_repo: Path) -> None:
    seed = _write_seed(temp_repo)
    (seed / "beta.json").write_bytes(b"\xff\xfe not utf-8")

    with pytest.raises(BootstrapError) as caught:
        bootstrap_releases_branch.bootstrap(repo_root=temp_repo, seed_dir=seed)

    assert caught.value.code == "bootstrap.manifest_invalid"


def test_not_a_repository_raises_not_a_repository(tmp_path: Path) -> None:
    outside = tmp_path / "plain"
    outside.mkdir()

    with pytest.raises(BootstrapError) as caught:
        bootstrap_releases_branch.bootstrap(repo_root=outside, seed_dir=outside)

    assert caught.value.code == "bootstrap.not_a_repository"


def test_require_repository_rejects_a_bare_repository(tmp_path: Path) -> None:
    """A bare repo answers ``false``, exercising the non-exception branch."""

    bare = tmp_path / "bare.git"
    bare.mkdir()
    _git(bare, "init", "--bare")

    with pytest.raises(BootstrapError) as caught:
        bootstrap_releases_branch._require_repository(bare)

    assert caught.value.code == "bootstrap.not_a_repository"


def test_require_repository_propagates_a_non_command_failure(
    temp_repo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def _explode(*_args: object, **_kwargs: object) -> str:
        raise BootstrapError("bootstrap.git_missing", "no git")

    monkeypatch.setattr(bootstrap_releases_branch, "_run_git", _explode)

    with pytest.raises(BootstrapError) as caught:
        bootstrap_releases_branch._require_repository(temp_repo)

    assert caught.value.code == "bootstrap.git_missing"


def test_missing_git_executable_raises_git_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(bootstrap_releases_branch.shutil, "which", lambda _name: None)

    with pytest.raises(BootstrapError) as caught:
        bootstrap_releases_branch._git_executable()

    assert caught.value.code == "bootstrap.git_missing"


def test_failing_git_command_raises_git_command_failed(temp_repo: Path) -> None:
    with pytest.raises(BootstrapError) as caught:
        bootstrap_releases_branch._run_git(["rev-parse", "refs/heads/absent"], repo_root=temp_repo)

    assert caught.value.code == "bootstrap.git_command_failed"
    assert "rev-parse" in caught.value.detail


def test_failing_git_command_detail_omits_the_subprocess_stderr(
    temp_repo: Path,
) -> None:
    """Gate 7: no raw error passthrough — stderr may carry absolute paths."""

    with pytest.raises(BootstrapError) as caught:
        bootstrap_releases_branch._run_git(
            ["cat-file", "-p", "refs/heads/definitely-absent"], repo_root=temp_repo
        )

    assert caught.value.code == "bootstrap.git_command_failed"
    assert str(temp_repo) not in caught.value.detail
    assert "fatal" not in caught.value.detail.lower()


def test_run_git_merges_the_supplied_environment(temp_repo: Path) -> None:
    value = bootstrap_releases_branch._run_git(
        ["config", "--get", "user.name"],
        repo_root=temp_repo,
        env={"GIT_CONFIG_COUNT": "0"},
    )

    assert value == "RytmRandomizer Tests"


# --------------------------------------------------------------------------
# R1 validator integration (present, absent, rejecting).
# --------------------------------------------------------------------------


def test_validator_is_used_when_release_lib_is_importable(
    temp_repo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    seen: list[dict[str, object]] = []
    fake = ModuleType("release_lib")

    def _validate_manifest(document: dict[str, object]) -> None:
        seen.append(document)

    fake.validate_manifest = _validate_manifest  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "release_lib", fake)
    seed = _write_seed(temp_repo)

    outcome = bootstrap_releases_branch.bootstrap(repo_root=temp_repo, seed_dir=seed)

    assert outcome.action == "created"
    # Both channel manifests are validated, and only those two.
    assert [document["channel"] for document in seen] == ["beta", "stable"]


def test_validator_rejection_aborts_before_any_ref_is_written(
    temp_repo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake = ModuleType("release_lib")

    def _validate_manifest(_document: dict[str, object]) -> None:
        raise ValueError("rollout_percent out of range")

    fake.validate_manifest = _validate_manifest  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "release_lib", fake)
    seed = _write_seed(temp_repo)

    with pytest.raises(BootstrapError) as caught:
        bootstrap_releases_branch.bootstrap(repo_root=temp_repo, seed_dir=seed)

    assert caught.value.code == "bootstrap.manifest_invalid"
    # The validator's message never leaks verbatim into the emitted detail.
    assert "rollout_percent out of range" not in caught.value.detail
    assert bootstrap_releases_branch.branch_exists("releases", repo_root=temp_repo) is False


def test_absent_release_lib_is_tolerated_and_logged(
    temp_repo: Path, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    monkeypatch.setattr(bootstrap_releases_branch, "load_validate_manifest", lambda: None)
    seed = _write_seed(temp_repo)

    # Force propagation for the duration: a sibling suite that attaches its own
    # handler (or flips propagate off) on this logger leaves caplog empty here,
    # and only when the suites run together. Capture at the root as well so the
    # assertion depends on the log CONTENT, not on handler wiring.
    # tests/conftest.py's isolated_observability fixture leaves
    # logging.getLogger("rytm_randomizer").propagate = False behind, and this
    # script logs under a descendant of it — so once any observability test has
    # run, caplog sees nothing here and this fails ONLY in a combined run.
    monkeypatch.setattr(logging.getLogger("rytm_randomizer"), "propagate", True)
    monkeypatch.setattr(logging.getLogger(bootstrap_releases_branch.LOGGER_NAME), "propagate", True)

    with caplog.at_level("INFO"):
        outcome = bootstrap_releases_branch.bootstrap(repo_root=temp_repo, seed_dir=seed)

    assert outcome.action == "created"
    assert "seed_validation_skipped" in caplog.text
    assert "release_lib_unavailable" in caplog.text


def test_strict_validation_fails_when_release_lib_is_absent(
    temp_repo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(bootstrap_releases_branch, "load_validate_manifest", lambda: None)
    seed = _write_seed(temp_repo)

    with pytest.raises(BootstrapError) as caught:
        bootstrap_releases_branch.bootstrap(
            repo_root=temp_repo, seed_dir=seed, strict_validation=True
        )

    assert caught.value.code == "bootstrap.validator_unavailable"
    assert bootstrap_releases_branch.branch_exists("releases", repo_root=temp_repo) is False


def test_load_validate_manifest_returns_the_callable_when_release_lib_exists(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake = ModuleType("release_lib")

    def _validate_manifest(_document: object) -> None:
        return None

    fake.validate_manifest = _validate_manifest  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "release_lib", fake)

    resolved = bootstrap_releases_branch.load_validate_manifest()

    assert resolved is _validate_manifest


def test_load_validate_manifest_returns_none_when_release_lib_is_absent(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """R1 is authored in parallel; its absence degrades, never raises."""

    # The loader uses a plain ``from release_lib import ...``, which consults
    # sys.modules and then the meta-path finders — NOT importlib.util.find_spec.
    # Patching find_spec therefore hid nothing once release_lib existed beside
    # the script (it did not, in the isolated worktree this test was written in).
    # Block it at the meta_path level, which a real import genuinely goes through.
    monkeypatch.delitem(sys.modules, "release_lib", raising=False)

    class _BlockReleaseLib:
        @staticmethod
        def find_spec(name: str, path: object = None, target: object = None) -> None:
            if name == "release_lib":
                raise ImportError("release_lib is hidden for this test")
            return None

    monkeypatch.setattr(sys, "meta_path", [_BlockReleaseLib(), *sys.meta_path])

    assert bootstrap_releases_branch.load_validate_manifest() is None


def test_load_validate_manifest_does_not_duplicate_the_scripts_path_entry() -> None:
    bootstrap_releases_branch.load_validate_manifest()
    before = list(sys.path)

    bootstrap_releases_branch.load_validate_manifest()

    assert list(sys.path) == before


def test_validate_seed_manifests_skips_non_manifest_files() -> None:
    validated = bootstrap_releases_branch.validate_seed_manifests(
        (("README.md", b"# not a manifest"), ("fleet-history.json", b"[]"))
    )

    assert validated == ()


def test_the_real_seed_manifests_pass_the_validator_when_it_is_available() -> None:
    """If R1 has landed, the committed seed must satisfy it verbatim."""

    if bootstrap_releases_branch.load_validate_manifest() is None:
        pytest.skip("scripts/release_lib.py (R1) has not landed yet")
    seed_files = tuple(
        (entry.name, entry.read_bytes()) for entry in sorted(_SEED_DIR.iterdir()) if entry.is_file()
    )

    validated = bootstrap_releases_branch.validate_seed_manifests(seed_files, strict=True)

    assert set(validated) == {"beta.json", "stable.json"}


# --------------------------------------------------------------------------
# Path hygiene, logging, and the no-network guarantee.
# --------------------------------------------------------------------------


def test_no_absolute_path_appears_in_any_error_detail(temp_repo: Path) -> None:
    with pytest.raises(BootstrapError) as caught:
        bootstrap_releases_branch.bootstrap(
            repo_root=temp_repo, seed_dir=temp_repo / "nowhere" / "absent"
        )

    assert str(temp_repo) not in caught.value.detail
    assert caught.value.detail.startswith("seed directory nowhere/absent")


def test_relative_to_repo_falls_back_to_the_basename_outside_the_repo(
    temp_repo: Path, tmp_path: Path
) -> None:
    outside = tmp_path / "elsewhere" / "stable.json"

    rendered = bootstrap_releases_branch._relative_to_repo(outside, repo_root=temp_repo)

    assert rendered == "stable.json"
    assert str(tmp_path) not in rendered


def test_script_never_pushes_fetches_or_force_updates_a_ref() -> None:
    source = _SCRIPT.read_text(encoding="utf-8")

    for forbidden in ('"push"', '"fetch"', '"--force"', '"-f"', '"checkout"', '"reset"'):
        assert forbidden not in source, f"script must not use git {forbidden}"


def test_running_the_test_suite_leaves_the_real_repository_branches_unchanged() -> None:
    """Sentinel: nothing in this module may create a ref in the real repo."""

    refs = _git(_REPO_ROOT, "for-each-ref", "--format=%(refname)", "refs/heads/").splitlines()

    assert "refs/heads/releases" not in refs


# --------------------------------------------------------------------------
# CLI surface.
# --------------------------------------------------------------------------


def _cli_root(temp_repo: Path, seed: Path, monkeypatch: pytest.MonkeyPatch) -> list[str]:
    monkeypatch.setattr(
        bootstrap_releases_branch,
        "SEED_RELATIVE_PATH",
        str(seed.relative_to(temp_repo)),
    )
    return ["--repo-root", str(temp_repo)]


def test_main_creates_the_branch_and_prints_the_summary(
    temp_repo: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    root = _cli_root(temp_repo, _write_seed(temp_repo), monkeypatch)

    exit_code = bootstrap_releases_branch.main(root)

    assert exit_code == 0
    assert "Created branch 'releases'" in capsys.readouterr().out


def test_main_is_idempotent_across_two_runs(
    temp_repo: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    root = _cli_root(temp_repo, _write_seed(temp_repo), monkeypatch)

    assert bootstrap_releases_branch.main(root) == 0
    capsys.readouterr()

    assert bootstrap_releases_branch.main(root) == 0
    assert "already exists" in capsys.readouterr().out


def test_main_dry_run_reports_the_plan(
    temp_repo: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    root = _cli_root(temp_repo, _write_seed(temp_repo), monkeypatch)

    exit_code = bootstrap_releases_branch.main([*root, "--dry-run"])

    assert exit_code == 0
    assert "[dry-run] Would create branch 'releases'" in capsys.readouterr().out
    assert bootstrap_releases_branch.branch_exists("releases", repo_root=temp_repo) is False


def test_main_honors_a_custom_branch_argument(
    temp_repo: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    root = _cli_root(temp_repo, _write_seed(temp_repo), monkeypatch)

    assert bootstrap_releases_branch.main([*root, "--branch", "releases-scratch"]) == 0
    assert "releases-scratch" in capsys.readouterr().out


def test_main_returns_one_and_prints_the_typed_code_on_failure(
    temp_repo: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(bootstrap_releases_branch, "SEED_RELATIVE_PATH", "absent_seed")

    exit_code = bootstrap_releases_branch.main(["--repo-root", str(temp_repo)])

    assert exit_code == 1
    captured = capsys.readouterr()
    assert "error [bootstrap.seed_missing]" in captured.err
    assert str(temp_repo) not in captured.err


def test_main_strict_validation_flag_reaches_the_bootstrap(
    temp_repo: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    root = _cli_root(temp_repo, _write_seed(temp_repo), monkeypatch)
    monkeypatch.setattr(bootstrap_releases_branch, "load_validate_manifest", lambda: None)

    exit_code = bootstrap_releases_branch.main([*root, "--strict-validation"])

    assert exit_code == 1
    assert "bootstrap.validator_unavailable" in capsys.readouterr().err


def test_main_defaults_repo_root_to_none_when_the_flag_is_absent(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """The ``--repo-root`` default branch must resolve to the script's repo."""

    captured_kwargs: dict[str, object] = {}

    def _fake_bootstrap(**kwargs: object) -> object:
        captured_kwargs.update(kwargs)
        return bootstrap_releases_branch.BootstrapOutcome(
            action="dry_run", branch="releases", commit=None, seeded_files=("stable.json",)
        )

    monkeypatch.setattr(bootstrap_releases_branch, "bootstrap", _fake_bootstrap)

    assert bootstrap_releases_branch.main(["--dry-run"]) == 0
    assert captured_kwargs["repo_root"] is None
    assert "[dry-run]" in capsys.readouterr().out


def test_describe_covers_every_outcome_action() -> None:
    outcome_type = bootstrap_releases_branch.BootstrapOutcome
    created = outcome_type(
        action="created", branch="releases", commit="abc123", seeded_files=("a",)
    )
    existing = outcome_type(
        action="already_exists", branch="releases", commit=None, seeded_files=("a",)
    )
    dry = outcome_type(action="dry_run", branch="releases", commit=None, seeded_files=("a",))

    assert "Created branch" in bootstrap_releases_branch.describe(created)
    assert "already exists" in bootstrap_releases_branch.describe(existing)
    assert "[dry-run]" in bootstrap_releases_branch.describe(dry)
    assert created.created is True
    assert existing.created is False
    assert dry.created is False


def test_build_parser_exposes_the_documented_flags() -> None:
    parsed = bootstrap_releases_branch.build_parser().parse_args([])

    assert parsed.branch == bootstrap_releases_branch.DEFAULT_BRANCH
    assert parsed.dry_run is False
    assert parsed.strict_validation is False
    assert parsed.repo_root is None


def test_module_entry_point_guard_is_present() -> None:
    source = _SCRIPT.read_text(encoding="utf-8")

    assert 'if __name__ == "__main__":' in source
    assert "raise SystemExit(main())" in source
