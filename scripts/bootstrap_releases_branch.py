#!/usr/bin/env python3
"""Publish the seed content of the orphan ``releases`` branch, exactly once.

The ``releases`` branch is the static distribution surface of the auto-update
system (spec §3): ``stable.json`` and ``beta.json`` are the channel manifests
every installed client polls, and ``fleet-history.json`` is the snapshot log the
dashboard renders. Those files are machine-written from then on — by
``release.yml``, ``promote.yml`` and ``fleet-snapshot.yml`` respectively — so
this script's only job is to bring the branch into existence with a valid,
empty starting state.

Design constraints, all mechanically enforced by the sibling test module:

* **Idempotent.** If the branch already exists the script reports that and exits
  0. It never rewrites, never amends, never force-updates a ref.
* **Single-ref.** The only ref it may create is ``refs/heads/<branch>``, and only
  when that ref is absent. It never checks out, never moves ``HEAD``, and never
  touches the caller's working tree or index — the commit is built entirely
  through plumbing (``hash-object`` -> ``mktree`` -> ``commit-tree`` ->
  ``update-ref``) against a temporary index file.
* **Local-only.** No ``push``, no ``fetch``, no network verb of any kind. The
  operator (or a workflow with an explicit token) publishes the branch.
* **Validated before it is written.** Every seeded manifest is run through the
  R1 validator (``scripts/release_lib.validate_manifest``) first, so the branch
  can never be seeded with a payload the ``manifest-validate.yml`` gate would
  immediately reject.

Observability (Gate 7): every failure path raises
:class:`BootstrapReleasesBranchError` carrying a code from the closed
:data:`ErrorCode` vocabulary; every boundary emits one structured log record.
Emitted details are bounded and repository-relative — no absolute path and no
raw exception string ever reaches a log line or an error detail.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import shutil
import subprocess
import sys
import tempfile
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Final, Literal

REPO_ROOT: Final[Path] = Path(__file__).resolve().parents[1]
SEED_RELATIVE_PATH: Final[str] = "releases_branch_seed"
DEFAULT_BRANCH: Final[str] = "releases"
COMMIT_MESSAGE: Final[str] = "chore: seed the releases distribution branch"
COMMIT_AUTHOR_NAME: Final[str] = "rytm-randomizer-release-bot"
COMMIT_AUTHOR_EMAIL: Final[str] = "release-bot@rytm-randomizer.invalid"
MANIFEST_FILENAMES: Final[tuple[str, ...]] = ("beta.json", "stable.json")
REGULAR_FILE_MODE: Final[str] = "100644"
LOGGER_NAME: Final[str] = "rytm_randomizer.release.bootstrap_releases_branch"

#: Closed error vocabulary. Every failure maps to exactly one of these codes;
#: callers (and the CI step summary) branch on the code, never on prose.
ErrorCode = Literal[
    "bootstrap.git_missing",
    "bootstrap.git_command_failed",
    "bootstrap.not_a_repository",
    "bootstrap.seed_missing",
    "bootstrap.seed_empty",
    "bootstrap.seed_unreadable",
    "bootstrap.manifest_invalid",
    "bootstrap.validator_unavailable",
]

#: The R1 validator's call shape. ``validate_manifest`` raises on an invalid
#: document; this module only cares that it did not raise.
ManifestValidator = Callable[[object], object]

_LOGGER: Final[logging.Logger] = logging.getLogger(LOGGER_NAME)


class BootstrapReleasesBranchError(RuntimeError):
    """A typed bootstrap failure carrying a closed-vocabulary error code."""

    def __init__(self, code: ErrorCode, detail: str) -> None:
        super().__init__(f"{code}: {detail}")
        self.code: Final[ErrorCode] = code
        self.detail: Final[str] = detail


@dataclass(frozen=True)
class BootstrapOutcome:
    """The result of one bootstrap attempt.

    ``created`` is ``False`` both when the branch already existed and when the
    run was a dry run; ``action`` distinguishes the three cases.
    """

    action: Literal["created", "already_exists", "dry_run"]
    branch: str
    commit: str | None
    seeded_files: tuple[str, ...]

    @property
    def created(self) -> bool:
        """Whether this run actually created the branch ref."""

        return self.action == "created"


def _log(event: str, **fields: object) -> None:
    """Emit one structured, bounded log record for a boundary event."""

    rendered = " ".join(f"{key}={value}" for key, value in sorted(fields.items()))
    _LOGGER.info("event=%s %s", event, rendered)


def _relative_to_repo(path: Path, *, repo_root: Path) -> str:
    """Render ``path`` repo-relative so no absolute path escapes into output."""

    try:
        return path.resolve().relative_to(repo_root.resolve()).as_posix()
    except ValueError:
        # Outside the repository: fall back to the basename, never the full
        # path, so a caller-supplied location cannot leak the filesystem layout.
        return path.name


def _git_executable() -> str:
    """Locate ``git``, or fail with the typed missing-tool code."""

    found = shutil.which("git")
    if found is None:
        raise BootstrapReleasesBranchError(
            "bootstrap.git_missing",
            "git executable was not found on PATH",
        )
    return found


def _run_git(
    arguments: Sequence[str],
    *,
    repo_root: Path,
    stdin: bytes | None = None,
    env: Mapping[str, str] | None = None,
) -> str:
    """Run one git command in ``repo_root`` and return its stripped stdout."""

    completed = subprocess.run(  # noqa: S603 - fixed argv, no shell
        [_git_executable(), *arguments],
        cwd=repo_root,
        input=stdin,
        capture_output=True,
        check=False,
        env=None if env is None else {**os.environ, **env},
    )
    if completed.returncode != 0:
        # The subprocess's stderr is deliberately dropped: it can contain
        # absolute paths, and Gate 7 forbids raw passthrough into details.
        raise BootstrapReleasesBranchError(
            "bootstrap.git_command_failed",
            f"git {arguments[0]} exited {completed.returncode}",
        )
    return completed.stdout.decode("utf-8", errors="replace").strip()


def _require_repository(repo_root: Path) -> None:
    """Fail fast unless ``repo_root`` is inside a git work tree."""

    try:
        inside = _run_git(["rev-parse", "--is-inside-work-tree"], repo_root=repo_root)
    except BootstrapReleasesBranchError as error:
        if error.code == "bootstrap.git_command_failed":
            raise BootstrapReleasesBranchError(
                "bootstrap.not_a_repository",
                "target directory is not inside a git work tree",
            ) from error
        raise
    if inside != "true":
        raise BootstrapReleasesBranchError(
            "bootstrap.not_a_repository",
            "target directory is not inside a git work tree",
        )


def branch_exists(branch: str, *, repo_root: Path) -> bool:
    """Whether ``refs/heads/<branch>`` already exists locally."""

    listed = _run_git(
        ["for-each-ref", "--format=%(refname)", f"refs/heads/{branch}"],
        repo_root=repo_root,
    )
    return listed != ""


def collect_seed_files(
    seed_dir: Path,
    *,
    repo_root: Path,
) -> tuple[tuple[str, bytes], ...]:
    """Read the seed directory into ``(name, content)`` pairs, sorted by name.

    Only the seed directory's own regular files are read; the seed is a flat
    directory by construction, and refusing to recurse keeps the published tree
    exactly as reviewable as the directory listing.
    """

    if not seed_dir.is_dir():
        raise BootstrapReleasesBranchError(
            "bootstrap.seed_missing",
            f"seed directory {_relative_to_repo(seed_dir, repo_root=repo_root)} does not exist",
        )
    collected: list[tuple[str, bytes]] = []
    for entry in sorted(seed_dir.iterdir()):
        if not entry.is_file():
            continue
        try:
            collected.append((entry.name, entry.read_bytes()))
        except OSError as error:
            raise BootstrapReleasesBranchError(
                "bootstrap.seed_unreadable",
                f"seed file {entry.name} could not be read",
            ) from error
    if not collected:
        raise BootstrapReleasesBranchError(
            "bootstrap.seed_empty",
            f"seed directory {_relative_to_repo(seed_dir, repo_root=repo_root)} holds no files",
        )
    return tuple(collected)


def load_validate_manifest() -> ManifestValidator | None:
    """Resolve the R1 validator, or ``None`` when the toolkit is absent.

    ``scripts/release_lib.py`` is the single home of manifest validation (reuse
    contract R1). It is authored in parallel with this script, so its absence is
    a tolerated, *reported* condition rather than an excuse to reimplement
    validation here.
    """

    script_dir = str(Path(__file__).resolve().parent)
    if script_dir not in sys.path:
        sys.path.insert(0, script_dir)
    try:
        from release_lib import validate_manifest  # type: ignore[import-not-found]
    except ImportError:
        return None
    validator: ManifestValidator = validate_manifest
    return validator


def validate_seed_manifests(
    seed_files: Sequence[tuple[str, bytes]],
    *,
    strict: bool = False,
) -> tuple[str, ...]:
    """Validate every seeded channel manifest through the R1 validator.

    Returns the names of the manifests actually validated. When
    ``scripts/release_lib.py`` is not importable the manifests are only parsed as
    JSON and the skip is logged; passing ``strict=True`` turns that skip into a
    ``bootstrap.validator_unavailable`` failure (the release pipeline sets it).
    """

    validator = load_validate_manifest()
    if validator is None:
        if strict:
            raise BootstrapReleasesBranchError(
                "bootstrap.validator_unavailable",
                "scripts/release_lib.py does not provide validate_manifest",
            )
        _log("seed_validation_skipped", reason="release_lib_unavailable")
    validated: list[str] = []
    for name, content in seed_files:
        if name not in MANIFEST_FILENAMES:
            continue
        try:
            document = json.loads(content.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise BootstrapReleasesBranchError(
                "bootstrap.manifest_invalid",
                f"seed manifest {name} is not valid JSON",
            ) from error
        if validator is not None:
            try:
                validator(document)
            except Exception as error:  # noqa: BLE001 - normalized to a typed code
                raise BootstrapReleasesBranchError(
                    "bootstrap.manifest_invalid",
                    f"seed manifest {name} was rejected by validate_manifest",
                ) from error
        validated.append(name)
    _log(
        "seed_validated",
        manifests=len(validated),
        validator_available=validator is not None,
    )
    return tuple(validated)


def _write_branch_commit(
    seed_files: Sequence[tuple[str, bytes]],
    *,
    branch: str,
    repo_root: Path,
) -> str:
    """Build an orphan commit from ``seed_files`` and point ``branch`` at it.

    Uses a throwaway index file so the caller's own index and working tree are
    untouched, and creates the ref with ``update-ref``'s empty old-value form so
    the write is creation-only — never a force update of an existing ref.
    """

    entries: list[str] = []
    for name, content in seed_files:
        blob = _run_git(
            ["hash-object", "-w", "--stdin"],
            repo_root=repo_root,
            stdin=content,
        )
        entries.append(f"{REGULAR_FILE_MODE} blob {blob}\t{PurePosixPath(name)}")
    tree = _run_git(
        ["mktree"],
        repo_root=repo_root,
        stdin=("\n".join(entries) + "\n").encode("utf-8"),
    )
    identity = {
        "GIT_AUTHOR_NAME": COMMIT_AUTHOR_NAME,
        "GIT_AUTHOR_EMAIL": COMMIT_AUTHOR_EMAIL,
        "GIT_COMMITTER_NAME": COMMIT_AUTHOR_NAME,
        "GIT_COMMITTER_EMAIL": COMMIT_AUTHOR_EMAIL,
    }
    with tempfile.TemporaryDirectory() as scratch:
        env = {**identity, "GIT_INDEX_FILE": str(Path(scratch) / "index")}
        commit = _run_git(
            ["commit-tree", tree, "-m", COMMIT_MESSAGE],
            repo_root=repo_root,
            env=env,
        )
    _run_git(["update-ref", f"refs/heads/{branch}", commit, ""], repo_root=repo_root)
    return commit


def bootstrap(
    *,
    repo_root: Path | None = None,
    branch: str = DEFAULT_BRANCH,
    seed_dir: Path | None = None,
    dry_run: bool = False,
    strict_validation: bool = False,
) -> BootstrapOutcome:
    """Create ``branch`` from the seed directory, or report that it exists.

    ``repo_root`` and the seed location are resolved at call time (not bound as
    default arguments) so a caller — and the test suite — can retarget the
    script at a throwaway repository without ever reaching the real one.
    """

    root = REPO_ROOT if repo_root is None else repo_root
    resolved_seed = (root / SEED_RELATIVE_PATH) if seed_dir is None else seed_dir
    _require_repository(root)
    seed_files = collect_seed_files(resolved_seed, repo_root=root)
    validate_seed_manifests(seed_files, strict=strict_validation)
    names = tuple(name for name, _ in seed_files)

    if branch_exists(branch, repo_root=root):
        _log("bootstrap_noop", branch=branch, reason="branch_exists")
        return BootstrapOutcome(
            action="already_exists",
            branch=branch,
            commit=None,
            seeded_files=names,
        )
    if dry_run:
        _log("bootstrap_dry_run", branch=branch, files=len(names))
        return BootstrapOutcome(
            action="dry_run",
            branch=branch,
            commit=None,
            seeded_files=names,
        )
    commit = _write_branch_commit(seed_files, branch=branch, repo_root=root)
    _log("bootstrap_created", branch=branch, commit=commit[:12], files=len(names))
    return BootstrapOutcome(
        action="created",
        branch=branch,
        commit=commit,
        seeded_files=names,
    )


def describe(outcome: BootstrapOutcome) -> str:
    """Render the one-line operator-facing summary for ``outcome``."""

    if outcome.action == "already_exists":
        return f"Branch '{outcome.branch}' already exists; nothing to do."
    if outcome.action == "dry_run":
        listing = ", ".join(outcome.seeded_files)
        return f"[dry-run] Would create branch '{outcome.branch}' with: {listing}"
    return (
        f"Created branch '{outcome.branch}' at {outcome.commit} "
        f"with {len(outcome.seeded_files)} files."
    )


def build_parser() -> argparse.ArgumentParser:
    """Build the CLI parser for this thin wrapper over :func:`bootstrap`."""

    parser = argparse.ArgumentParser(
        description="Seed the orphan releases distribution branch, once.",
    )
    parser.add_argument(
        "--branch",
        default=DEFAULT_BRANCH,
        help=f"branch to create (default: {DEFAULT_BRANCH})",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="report what would be created without writing any ref",
    )
    parser.add_argument(
        "--strict-validation",
        action="store_true",
        help="fail when scripts/release_lib.py cannot provide validate_manifest",
    )
    parser.add_argument(
        "--repo-root",
        default=None,
        help="repository to operate on (default: the repository holding this script)",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point: 0 on success (including the no-op), 1 on a typed failure."""

    arguments = build_parser().parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(message)s", stream=sys.stderr)
    try:
        outcome = bootstrap(
            repo_root=None if arguments.repo_root is None else Path(arguments.repo_root),
            branch=arguments.branch,
            dry_run=arguments.dry_run,
            strict_validation=arguments.strict_validation,
        )
    except BootstrapReleasesBranchError as error:
        _log("bootstrap_failed", code=error.code)
        print(f"error [{error.code}]: {error.detail}", file=sys.stderr)
        return 1
    print(describe(outcome))
    return 0


# The module-level entry guard cannot execute under import; main() itself
# is covered directly.
if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
