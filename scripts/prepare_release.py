"""Derive the next release version, changelog section, and release-PR body.

WHAT
====

``scripts/prepare_release.py`` is the **conventional-commit bump deriver** for
the auto-update program (see
``docs/superpowers/plans/2026-08-03-autoupdate-distribution.md`` §2.4). Given
the ``git log <last-tag>..HEAD`` subject/body stream it:

1. classifies every commit against the Conventional Commits grammar
   (``type(scope)!: subject`` plus a ``BREAKING CHANGE:`` footer),
2. derives the highest applicable SemVer bump — ``BREAKING CHANGE`` / ``!``
   → **major**, ``feat`` → **minor**, everything else → **patch**, exactly as
   spec §2 rule 4 states it. ``fix`` / ``perf`` / ``revert`` are classified as
   patch on their own merits; ``docs`` / ``chore`` / ``refactor`` / ``test`` /
   ``ci`` / ``build`` / ``style`` and unparseable subjects contribute nothing
   individually but still land on the **patch floor**, because a non-empty
   commit range on the ``cut-release`` path is a release. Pass
   ``--no-bump-on-trivial`` (or ``bump_floor=BUMP_NONE``) to drop that floor
   and get a ``none`` bump for a trivial-only range,
3. renders the ``CHANGELOG.md`` section for the proposed version, grouped by
   commit type, linking ``(#NNN)`` subject suffixes to their pull requests,
4. renders the release-PR body.

**This script NEVER writes the ``VERSION`` file, and never writes any file at
all.** It *proposes*; ``scripts/sync_version.py`` *applies*. That split keeps
the single-source-of-truth writer in exactly one place: a deriver that also
mutated ``VERSION`` would make "what would the next release be?" a
side-effecting question, and would give the release workflow two candidate
writers to race. ``--dry-run`` and the default mode therefore differ only in
what they *print*; neither touches the filesystem.

WHY THE SHAPE
=============

* **Determinism.** Nothing on the derivation path reads the wall clock, the
  environment, or ``git``. The commit log arrives as an injected string
  (``--log-file``, ``--log-stdin``, or the ``commit_log`` argument of
  :func:`prepare_release`), and the changelog date arrives as an injected
  ``--date``. Tests reproduce byte-for-byte; the release workflow passes the
  tag date explicitly so a re-run of a failed job produces the same artifact.
* **Reuse (R1).** SemVer parsing, comparison, the ``Version`` DTO, and reading
  the ``VERSION`` file all come from :mod:`release_lib`. This module owns only
  the conventional-commit grammar and the two renderers.
* **Machine-readable mode.** ``--json`` emits the whole derivation as one JSON
  object so a workflow step consumes ``.next_version`` instead of scraping
  human text.

OBSERVABILITY
=============

Every failure exits through the typed taxonomy in this module
(:class:`ReleasePreparationError` and its four concrete subclasses), each
carrying a stable dotted ``fingerprint`` — the same discipline as
``rytm_randomizer/observability/errors.py``. Failures and the successful
derivation both emit a structured log record and bump a counter on the
in-process metrics surface (``release.prepare.*``). No emitted detail ever
contains an absolute path: filesystem errors report the ``--log-file``
argument exactly as the operator typed it, and nothing else.

USAGE
=====

.. code-block:: console

    $ python scripts/prepare_release.py --log-stdin < commits.txt
    $ git log v1.34.0..HEAD --format=%B%x00 | python scripts/prepare_release.py \
          --log-stdin --json --date 2026-09-07
    $ python scripts/prepare_release.py --log-file commits.txt --dry-run

Commits are separated by NUL bytes when ``git log --format=%B%x00`` is used;
a blank-line-separated stream is also accepted. See
:func:`split_commit_log`.
"""

from __future__ import annotations

import argparse
import json
import logging
import re
import sys
from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Final

_SCRIPTS_DIR: Final[Path] = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:  # pragma: no cover - import-path bootstrap
    sys.path.insert(0, str(_SCRIPTS_DIR))

from release_lib import (  # noqa: E402  (must follow the sys.path bootstrap)
    Version,
    compare_versions,
    parse_version,
    read_version_file,
)

__all__ = [
    "BUMP_MAJOR",
    "BUMP_MINOR",
    "BUMP_NONE",
    "BUMP_PATCH",
    "ChangelogRenderError",
    "CommitLogEmptyError",
    "CommitLogReadError",
    "ParsedCommit",
    "ReleasePreparation",
    "ReleasePreparationError",
    "VersionDerivationError",
    "apply_bump",
    "classify_commits",
    "derive_bump",
    "main",
    "parse_commit",
    "prepare_release",
    "render_changelog_section",
    "render_pr_body",
    "split_commit_log",
]

LOGGER_NAME: Final[str] = "rytm_randomizer.release.prepare"
_LOGGER: Final[logging.Logger] = logging.getLogger(LOGGER_NAME)

BUMP_NONE: Final[str] = "none"
BUMP_PATCH: Final[str] = "patch"
BUMP_MINOR: Final[str] = "minor"
BUMP_MAJOR: Final[str] = "major"

#: Bump levels ordered weakest -> strongest. ``derive_bump`` reports the max.
_BUMP_RANK: Final[Mapping[str, int]] = MappingProxyType(
    {BUMP_NONE: 0, BUMP_PATCH: 1, BUMP_MINOR: 2, BUMP_MAJOR: 3}
)

#: Conventional-commit type -> bump level it implies (before ``!`` / footer).
_TYPE_BUMP: Final[Mapping[str, str]] = MappingProxyType(
    {
        "feat": BUMP_MINOR,
        "fix": BUMP_PATCH,
        "perf": BUMP_PATCH,
        "revert": BUMP_PATCH,
        "build": BUMP_NONE,
        "chore": BUMP_NONE,
        "ci": BUMP_NONE,
        "docs": BUMP_NONE,
        "refactor": BUMP_NONE,
        "style": BUMP_NONE,
        "test": BUMP_NONE,
    }
)

#: Changelog section heading per commit type, in emission order.
_SECTION_ORDER: Final[Sequence[tuple[str, str]]] = (
    ("feat", "Added"),
    ("fix", "Fixed"),
    ("perf", "Performance"),
    ("revert", "Reverted"),
    ("refactor", "Changed"),
    ("docs", "Documentation"),
    ("build", "Build"),
    ("ci", "CI"),
    ("test", "Tests"),
    ("chore", "Chores"),
    ("style", "Style"),
)

_UNCLASSIFIED_HEADING: Final[str] = "Other"

_SUBJECT_RE: Final[re.Pattern[str]] = re.compile(
    r"^(?P<type>[A-Za-z]+)"
    r"(?:\((?P<scope>[^()]*)\))?"
    r"(?P<breaking>!)?"
    r": *(?P<subject>.+?) *$"
)

_BREAKING_FOOTER_RE: Final[re.Pattern[str]] = re.compile(r"^BREAKING[ -]CHANGE *:", re.MULTILINE)

_PR_SUFFIX_RE: Final[re.Pattern[str]] = re.compile(r" *\(#(?P<number>\d+)\) *$")

DEFAULT_PR_BASE_URL: Final[str] = "https://github.com/buzzijose-hub/RytmRandomizer/pull"


# --------------------------------------------------------------------------
# Typed error taxonomy
# --------------------------------------------------------------------------


class ReleasePreparationError(Exception):
    """Root of the release-preparation error taxonomy.

    Every concrete subclass declares a stable dotted ``fingerprint`` so
    operators grep logs on one vocabulary shared with the metrics counter
    keys. ``detail`` is an already-sanitized, path-free description.
    """

    fingerprint: Final[str] = "release.prepare.error.unspecified"

    def __init__(self, detail: str) -> None:
        super().__init__(f"[{self.fingerprint}] {detail}")
        self.detail = detail


class CommitLogReadError(ReleasePreparationError):
    """The ``--log-file`` argument could not be read as UTF-8 text."""

    fingerprint: Final[str] = "release.prepare.log.read_failed"


class CommitLogEmptyError(ReleasePreparationError):
    """The commit log contained no commits at all."""

    fingerprint: Final[str] = "release.prepare.log.empty"


class VersionDerivationError(ReleasePreparationError):
    """The current version could not be read or the derived version regressed."""

    fingerprint: Final[str] = "release.prepare.version.invalid"


class ChangelogRenderError(ReleasePreparationError):
    """The changelog section could not be rendered from the classified commits."""

    fingerprint: Final[str] = "release.prepare.changelog.render_failed"


# --------------------------------------------------------------------------
# Metrics — an in-process counter surface, mirroring observability/metrics.py
# --------------------------------------------------------------------------


@dataclass
class ReleasePrepareMetrics:
    """Cumulative counters for the release-preparation boundary.

    Kept local to this script rather than added to
    ``rytm_randomizer/observability/metrics.py`` because the package metrics
    module is a *runtime* surface and this is build-time tooling; the package
    must not grow counters that no shipped code path can increment.
    """

    outcomes: Counter[str]
    errors_by_fingerprint: Counter[str]

    def record_outcome(self, outcome: str) -> None:
        """Record one terminal outcome (``derived`` or ``no_bump``)."""

        self.outcomes[outcome] += 1

    def record_error(self, fingerprint: str) -> None:
        """Record one categorized failure, keyed by its taxonomy fingerprint."""

        self.errors_by_fingerprint[fingerprint] += 1

    def format_summary(self) -> str:
        """Render a single-line, deterministic snapshot for structured logs."""

        outcomes = ",".join(f"{key}={self.outcomes[key]}" for key in sorted(self.outcomes))
        errors = ",".join(
            f"{key}={self.errors_by_fingerprint[key]}" for key in sorted(self.errors_by_fingerprint)
        )
        return f"ReleasePrepareMetrics(outcomes={outcomes or '-'}, errors={errors or '-'})"


_METRICS: ReleasePrepareMetrics = ReleasePrepareMetrics(
    outcomes=Counter(), errors_by_fingerprint=Counter()
)


def get_metrics() -> ReleasePrepareMetrics:
    """Return the module-level metrics singleton."""

    return _METRICS


def reset_metrics() -> None:
    """Clear every counter — test isolation hook."""

    _METRICS.outcomes.clear()
    _METRICS.errors_by_fingerprint.clear()


def _fail(error: ReleasePreparationError) -> ReleasePreparationError:
    """Record + log a taxonomy failure and hand the error back to be raised."""

    _METRICS.record_error(error.fingerprint)
    _LOGGER.error(
        "release preparation failed",
        extra={
            "fingerprint": error.fingerprint,
            "detail": error.detail,
            "metrics": _METRICS.format_summary(),
        },
    )
    return error


# --------------------------------------------------------------------------
# Commit parsing
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class ParsedCommit:
    """One classified commit from the log.

    ``conventional`` is ``False`` for a subject that does not match the
    ``type(scope)!: subject`` grammar; such a commit contributes no bump and
    lands under the ``Other`` changelog heading with its raw subject.
    """

    raw_subject: str
    commit_type: str | None
    scope: str | None
    subject: str
    breaking: bool
    pr_number: int | None
    conventional: bool

    @property
    def bump(self) -> str:
        """The SemVer bump this single commit implies."""

        if self.breaking:
            return BUMP_MAJOR
        if self.commit_type is None:
            return BUMP_NONE
        return _TYPE_BUMP.get(self.commit_type, BUMP_NONE)


def split_commit_log(commit_log: str) -> tuple[str, ...]:
    """Split a raw commit-log string into per-commit message blocks.

    Two separators are accepted so the caller can choose either
    ``git log --format=%B%x00`` (NUL-delimited, preserves blank lines inside a
    message body) or a simpler blank-line-delimited stream. NUL wins when
    present because it is unambiguous.
    """

    if "\x00" in commit_log:
        blocks = commit_log.split("\x00")
    else:
        blocks = re.split(r"\n[ \t]*\n", commit_log)
    return tuple(block.strip("\n") for block in blocks if block.strip())


def parse_commit(message: str) -> ParsedCommit:
    """Parse one commit message block into a :class:`ParsedCommit`.

    The first non-blank line is the subject; the remainder is scanned for a
    ``BREAKING CHANGE:`` (or ``BREAKING-CHANGE:``) footer.
    """

    lines = message.splitlines()
    subject_line = ""
    body_start = len(lines)
    for index, line in enumerate(lines):
        if line.strip():
            subject_line = line.strip()
            body_start = index + 1
            break
    body = "\n".join(lines[body_start:])
    has_breaking_footer = bool(_BREAKING_FOOTER_RE.search(body))

    pr_number: int | None = None
    pr_match = _PR_SUFFIX_RE.search(subject_line)
    stripped_subject = subject_line
    if pr_match is not None:
        pr_number = int(pr_match.group("number"))
        stripped_subject = subject_line[: pr_match.start()].rstrip()

    match = _SUBJECT_RE.match(stripped_subject)
    if match is None:
        return ParsedCommit(
            raw_subject=subject_line,
            commit_type=None,
            scope=None,
            subject=stripped_subject,
            breaking=has_breaking_footer,
            pr_number=pr_number,
            conventional=False,
        )

    commit_type = match.group("type").lower()
    scope_group = match.group("scope")
    scope = scope_group.strip() if scope_group is not None and scope_group.strip() else None
    return ParsedCommit(
        raw_subject=subject_line,
        commit_type=commit_type,
        scope=scope,
        subject=match.group("subject"),
        breaking=has_breaking_footer or match.group("breaking") is not None,
        pr_number=pr_number,
        conventional=True,
    )


def classify_commits(commit_log: str) -> tuple[ParsedCommit, ...]:
    """Split and parse a raw commit log into classified commits.

    Raises :class:`CommitLogEmptyError` when the log holds no commits — an
    empty range is a caller error at the release boundary, not a silent
    "no bump", because it usually means the tag range was computed wrong.
    """

    blocks = split_commit_log(commit_log)
    if not blocks:
        raise _fail(CommitLogEmptyError("commit log contained no commits"))
    return tuple(parse_commit(block) for block in blocks)


def derive_bump(commits: Sequence[ParsedCommit], *, floor: str = BUMP_PATCH) -> str:
    """Return the highest bump level implied by ``commits``, never below ``floor``.

    Spec §2 rule 4 states the derivation as "``BREAKING CHANGE:``/``!`` ⇒ MAJOR,
    ``feat:`` ⇒ MINOR, **else PATCH**" — a range that contains only ``docs:`` and
    ``chore:`` still cuts a patch release, because the spec's ``cut-release``
    path is invoked when the operator has already decided to ship. That is the
    default (``floor=BUMP_PATCH``).

    ``floor=BUMP_NONE`` selects the stricter reading, in which a range with no
    ``feat``/``fix``/``perf``/``revert`` and no breaking marker proposes no
    version change at all. It is reachable from the CLI via
    ``--no-bump-on-trivial`` so a caller can ask "is there anything
    release-worthy here?" without being told "yes, a patch" unconditionally.
    """

    level = floor
    for commit in commits:
        if _BUMP_RANK[commit.bump] > _BUMP_RANK[level]:
            level = commit.bump
    return level


def apply_bump(current: Version, bump: str) -> Version:
    """Apply ``bump`` to ``current`` and return the proposed next version.

    A pre-release version (``1.35.0-beta.1``) is *finalized* rather than
    incremented when the bump it already encodes is at least as strong as the
    derived bump: ``1.35.0-beta.1`` + ``minor`` becomes ``1.35.0``, because the
    minor bump is already baked into the pre-release. A stronger derived bump
    still moves the numbers (``1.35.0-beta.1`` + ``major`` → ``2.0.0``).
    """

    if bump == BUMP_NONE:
        return current
    # release_lib.Version.prerelease is `tuple[str, ...]` and defaults to `()`
    # for a stable release — it is NEVER None. Guarding on `is not None` here
    # was always true, so every bump took the prerelease-finalize branch and
    # apply_bump returned the CURRENT version unchanged: a `feat:` range
    # derived `minor` and proposed 1.34.0 instead of 1.35.0, i.e. a release
    # that silently does not bump. Guard on truthiness instead.
    if current.prerelease:
        already_encoded = _prerelease_encoded_bump(current)
        if _BUMP_RANK[bump] <= _BUMP_RANK[already_encoded]:
            return Version(
                major=current.major,
                minor=current.minor,
                patch=current.patch,
                prerelease=(),
            )
    if bump == BUMP_MAJOR:
        return Version(major=current.major + 1, minor=0, patch=0, prerelease=())
    if bump == BUMP_MINOR:
        return Version(major=current.major, minor=current.minor + 1, patch=0, prerelease=())
    return Version(major=current.major, minor=current.minor, patch=current.patch + 1, prerelease=())


def _prerelease_encoded_bump(current: Version) -> str:
    """Infer which bump a pre-release version already represents.

    ``X.0.0-rc`` encodes a major bump, ``X.Y.0-rc`` a minor bump, and anything
    else a patch bump. Pure numeric inspection — no history required.
    """

    if current.minor == 0 and current.patch == 0:
        return BUMP_MAJOR
    if current.patch == 0:
        return BUMP_MINOR
    return BUMP_PATCH


# --------------------------------------------------------------------------
# Rendering
# --------------------------------------------------------------------------


def _format_entry(commit: ParsedCommit, pr_base_url: str) -> str:
    """Render one changelog bullet, appending a PR link when one is present."""

    text = commit.subject if commit.conventional else commit.raw_subject
    if commit.scope is not None:
        text = f"**{commit.scope}**: {text}"
    if commit.breaking:
        text = f"**BREAKING** — {text}"
    if commit.pr_number is not None:
        text = f"{text} ([#{commit.pr_number}]({pr_base_url}/{commit.pr_number}))"
    return f"- {text}"


def render_changelog_section(
    version: Version,
    commits: Sequence[ParsedCommit],
    *,
    release_date: str,
    pr_base_url: str = DEFAULT_PR_BASE_URL,
) -> str:
    """Render the ``CHANGELOG.md`` section for ``version``.

    ``release_date`` is injected (never read from the wall clock) so the same
    inputs always render the same bytes.

    Raises :class:`ChangelogRenderError` when ``commits`` is empty — a section
    with no bullets would be committed as a silent regression in the release
    notes the operator reads before consenting to an update.
    """

    if not commits:
        raise _fail(ChangelogRenderError("cannot render a changelog section with no commits"))

    grouped: dict[str, list[ParsedCommit]] = {}
    for commit in commits:
        heading = _heading_for(commit)
        grouped.setdefault(heading, []).append(commit)

    lines: list[str] = [f"## [{version}] - {release_date}", ""]
    for heading in _ordered_headings(grouped):
        lines.append(f"### {heading}")
        lines.append("")
        lines.extend(_format_entry(commit, pr_base_url) for commit in grouped[heading])
        lines.append("")
    return "\n".join(lines).rstrip("\n") + "\n"


def _heading_for(commit: ParsedCommit) -> str:
    """Map a commit to its changelog heading."""

    for commit_type, heading in _SECTION_ORDER:
        if commit.commit_type == commit_type:
            return heading
    return _UNCLASSIFIED_HEADING


def _ordered_headings(grouped: Mapping[str, Sequence[ParsedCommit]]) -> tuple[str, ...]:
    """Return the populated headings in canonical emission order."""

    ordered: list[str] = []
    for _commit_type, heading in _SECTION_ORDER:
        if heading in grouped and heading not in ordered:
            ordered.append(heading)
    if _UNCLASSIFIED_HEADING in grouped:
        ordered.append(_UNCLASSIFIED_HEADING)
    return tuple(ordered)


def render_pr_body(preparation: ReleasePreparation) -> str:
    """Render the release-PR body for a completed derivation."""

    bump_note = (
        "No release-worthy commits in range; the version is unchanged."
        if preparation.bump == BUMP_NONE
        else f"Derived bump: **{preparation.bump}**."
    )
    breaking = [commit for commit in preparation.commits if commit.breaking]
    lines: list[str] = [
        f"# Release {preparation.next_version}",
        "",
        f"- Current version: `{preparation.current_version}`",
        f"- Proposed version: `{preparation.next_version}`",
        f"- Commits in range: {len(preparation.commits)}",
        f"- {bump_note}",
        "",
    ]
    if breaking:
        lines.extend(
            [
                "## Breaking changes",
                "",
                *(f"- {commit.subject or commit.raw_subject}" for commit in breaking),
                "",
            ]
        )
    lines.extend(
        [
            "## Changelog",
            "",
            preparation.changelog_section.rstrip("\n"),
            "",
            "## Applying this release",
            "",
            "This script proposes only. Run `scripts/sync_version.py` to write the",
            "`VERSION` file and its derivations, then tag the resulting commit.",
            "",
        ]
    )
    return "\n".join(lines)


# --------------------------------------------------------------------------
# Top-level derivation
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class ReleasePreparation:
    """The complete, side-effect-free proposal for the next release."""

    current_version: Version
    next_version: Version
    bump: str
    commits: tuple[ParsedCommit, ...]
    changelog_section: str

    @property
    def changed(self) -> bool:
        """Whether the derivation proposes a version change at all."""

        return self.bump != BUMP_NONE

    def to_json_object(self) -> dict[str, object]:
        """Render the machine-readable payload consumed by workflow steps."""

        return {
            "current_version": str(self.current_version),
            "next_version": str(self.next_version),
            "bump": self.bump,
            "changed": self.changed,
            "commit_count": len(self.commits),
            "breaking_count": sum(1 for commit in self.commits if commit.breaking),
            "unconventional_count": sum(1 for commit in self.commits if not commit.conventional),
            "changelog_section": self.changelog_section,
            "commits": [
                {
                    "type": commit.commit_type,
                    "scope": commit.scope,
                    "subject": commit.subject,
                    "breaking": commit.breaking,
                    "pr_number": commit.pr_number,
                    "conventional": commit.conventional,
                }
                for commit in self.commits
            ],
        }


def prepare_release(
    commit_log: str,
    *,
    current_version: Version,
    release_date: str,
    pr_base_url: str = DEFAULT_PR_BASE_URL,
    bump_floor: str = BUMP_PATCH,
) -> ReleasePreparation:
    """Derive the bump, next version, and changelog section. Writes nothing.

    ``bump_floor`` selects the spec §2 rule 4 default (``BUMP_PATCH`` — "else
    PATCH") or the stricter ``BUMP_NONE`` reading; see :func:`derive_bump`.

    Raises :class:`VersionDerivationError` when the proposed version does not
    strictly follow ``current_version`` for a non-empty bump — a guard against
    an ``apply_bump`` regression silently proposing a downgrade, which would
    make every already-updated client refuse the manifest.
    """

    commits = classify_commits(commit_log)
    bump = derive_bump(commits, floor=bump_floor)
    next_version = apply_bump(current_version, bump)
    if bump != BUMP_NONE and compare_versions(next_version, current_version) <= 0:
        raise _fail(
            VersionDerivationError(
                f"derived version {next_version} does not follow {current_version}"
            )
        )
    changelog_section = render_changelog_section(
        next_version, commits, release_date=release_date, pr_base_url=pr_base_url
    )
    _METRICS.record_outcome("derived" if bump != BUMP_NONE else "no_bump")
    _LOGGER.info(
        "release preparation derived",
        extra={
            "fingerprint": "release.prepare.derived",
            "bump": bump,
            "current_version": str(current_version),
            "next_version": str(next_version),
            "commit_count": len(commits),
            "metrics": _METRICS.format_summary(),
        },
    )
    return ReleasePreparation(
        current_version=current_version,
        next_version=next_version,
        bump=bump,
        commits=commits,
        changelog_section=changelog_section,
    )


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="prepare_release.py",
        description=(
            "Derive the next SemVer version, changelog section, and release-PR "
            "body from a conventional-commit log. Proposes only; never writes "
            "the VERSION file or any other file."
        ),
    )
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument(
        "--log-file",
        help="Path to a file holding the `git log <last-tag>..HEAD` output.",
    )
    source.add_argument(
        "--log-stdin",
        action="store_true",
        help="Read the commit log from standard input.",
    )
    parser.add_argument(
        "--date",
        required=True,
        help="Release date stamped into the changelog heading (YYYY-MM-DD). "
        "Injected rather than read from the clock so runs are reproducible.",
    )
    parser.add_argument(
        "--current-version",
        help="Override the current version instead of reading the VERSION file.",
    )
    parser.add_argument(
        "--repo-root",
        default=".",
        help="Directory holding the VERSION file (default: the current directory).",
    )
    parser.add_argument(
        "--pr-base-url",
        default=DEFAULT_PR_BASE_URL,
        help="Base URL used to build `(#NNN)` pull-request links.",
    )
    parser.add_argument(
        "--no-bump-on-trivial",
        action="store_true",
        help="Propose no version change when the range holds only trivial "
        "commits (docs/chore/ci/...). The default follows spec §2 rule 4 "
        "('else PATCH') and proposes a patch release for any non-empty range.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        dest="as_json",
        help="Emit the derivation as a single JSON object on stdout.",
    )
    parser.add_argument(
        "--pr-body",
        action="store_true",
        help="Emit the release-PR body instead of the changelog section.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the derivation and write nothing. This script never writes "
        "anything, so --dry-run only adds an explicit banner.",
    )
    return parser


def _read_commit_log(arguments: argparse.Namespace, stdin_text: str | None) -> str:
    if arguments.log_stdin:
        # Read the real stdin only when the caller did not inject text AND the
        # stdin source was actually selected; reading it unconditionally would
        # block (or raise, under pytest's capture) on the --log-file path.
        return sys.stdin.read() if stdin_text is None else stdin_text
    try:
        return Path(arguments.log_file).read_text(encoding="utf-8")
    except OSError as error:
        raise _fail(
            CommitLogReadError(
                f"could not read commit log from --log-file {arguments.log_file!r} "
                f"({type(error).__name__})"
            )
        ) from error
    except UnicodeDecodeError as error:
        raise _fail(
            CommitLogReadError(
                f"commit log at --log-file {arguments.log_file!r} is not valid UTF-8"
            )
        ) from error


def _resolve_current_version(arguments: argparse.Namespace) -> Version:
    if arguments.current_version is not None:
        try:
            return parse_version(arguments.current_version)
        except Exception as error:
            raise _fail(
                VersionDerivationError(
                    f"--current-version {arguments.current_version!r} is not valid SemVer"
                )
            ) from error
    try:
        return read_version_file(Path(arguments.repo_root))
    except Exception as error:
        raise _fail(
            VersionDerivationError(
                f"could not read the VERSION file under --repo-root "
                f"{arguments.repo_root!r} ({type(error).__name__})"
            )
        ) from error


def main(
    argv: Sequence[str] | None = None,
    *,
    stdin_text: str | None = None,
    stream: object | None = None,
) -> int:
    """CLI entry point. Returns a process exit code; writes nothing to disk."""

    out = sys.stdout if stream is None else stream
    parser = _build_parser()
    arguments = parser.parse_args(list(argv) if argv is not None else None)
    try:
        commit_log = _read_commit_log(arguments, stdin_text)
        current_version = _resolve_current_version(arguments)
        preparation = prepare_release(
            commit_log,
            current_version=current_version,
            release_date=arguments.date,
            pr_base_url=arguments.pr_base_url,
            bump_floor=BUMP_NONE if arguments.no_bump_on_trivial else BUMP_PATCH,
        )
    except ReleasePreparationError as error:
        print(f"error: {error}", file=sys.stderr)
        return 1

    if arguments.as_json:
        print(json.dumps(preparation.to_json_object(), indent=2, sort_keys=True), file=out)
        return 0
    if arguments.dry_run:
        print("dry-run: proposing only; no file is written by this script.", file=out)
    if arguments.pr_body:
        print(render_pr_body(preparation), file=out)
        return 0
    print(f"bump: {preparation.bump}", file=out)
    print(f"next_version: {preparation.next_version}", file=out)
    print("", file=out)
    print(preparation.changelog_section, file=out)
    return 0


if __name__ == "__main__":  # pragma: no cover - process entry point
    raise SystemExit(main())
