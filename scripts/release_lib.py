"""Release toolkit — the single home for version + update-manifest logic (R1).

This module is the ``R1`` abstraction named in
``docs/superpowers/plans/2026-09-07-autoupdate-implementation.md``. It is a
**library, not a CLI**: every release-adjacent script and workflow step
(``sync_version.py``, ``prepare_release.py``, ``validate_manifest.py``,
``release.yml`` verify-tag, ``promote.yml``, ``manifest-validate.yml``) imports
from here rather than re-deriving SemVer comparison or manifest rules. SemVer
logic exists exactly once in Python; a renamed-symbol fork elsewhere is a
Gate 17 violation.

It has **no third-party dependencies** — stdlib only — so a workflow step can
``python -c "import release_lib"`` before any ``pip install`` has run.

Frozen public API (the import surface other agents code against)
----------------------------------------------------------------

* :class:`Version` — frozen, keyword-constructible
  (``major`` / ``minor`` / ``patch`` / ``prerelease``) strict SemVer value.
* :func:`parse_version` / :func:`compare_versions` — parse and three-way
  compare, implementing semver.org §11 prerelease precedence with build
  metadata excluded from precedence (§10).
* :func:`read_version_file` — the one reader of the repo-root ``VERSION``.
* :func:`validate_manifest` — returns a tuple of typed
  :class:`ManifestViolation` values (``.code`` / ``.message``).
* :func:`generate_manifest` — builds a spec §4 channel manifest and runs
  :func:`validate_manifest` on its own output **before returning**, so a
  caller can never obtain a manifest this module's own gate would refuse.

Manifest rules implemented here are spec §4 verbatim, including the two that
are easy to get backwards:

* **Unknown top-level keys are ignored**, not rejected — §4 makes that the
  forward-compatibility hinge, with ``schema_version`` gating interpretation.
* **``build`` is informational provenance.** Its shape is checked when
  present, but a client "must not refuse an update over provenance fields",
  so a malformed ``build`` block is reported at advisory severity and never
  makes an otherwise-valid manifest unacceptable.

Observability (Gate 7)
----------------------

Boundaries emit structured single-line records through :func:`log_event` (a
JSON object on the ``rytm.release`` logger) and counters through
:class:`ReleaseMetrics`. Nothing here formats a raw exception into emitted
text: a failure becomes a :class:`ManifestViolation` with a
:class:`ViolationCode`, or a :class:`ReleaseError` carrying one. No emitted
detail ever contains an absolute filesystem path — see :func:`redact_path`.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import re
import sys
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from enum import Enum
from functools import total_ordering
from pathlib import Path
from typing import Final

__all__ = [
    "ADVISORY_VIOLATION_CODES",
    "ALLOWED_URL_PREFIX",
    "MANIFEST_SCHEMA_VERSION",
    "PLACEHOLDER_VERSION",
    "RELEASE_DOWNLOAD_PATH_SEGMENT",
    "SUPPORTED_CHANNELS",
    "SUPPORTED_TARGETS",
    "ManifestViolation",
    "ReleaseError",
    "ReleaseMetrics",
    "Version",
    "ViolationCode",
    "compare_versions",
    "generate_manifest",
    "get_metrics",
    "is_valid_version",
    "log_event",
    "manifest_is_acceptable",
    "parse_version",
    "read_version_file",
    "redact_path",
    "version_file_path",
]

PROJECT_ROOT: Final[Path] = Path(__file__).resolve().parents[1]

#: Schema version stamped into every generated manifest (spec §4). Clients pin
#: what they accept; bumping this is a deliberate, reviewed migration.
MANIFEST_SCHEMA_VERSION: Final[int] = 1

#: The two release channels (spec §3). Prereleases flow to ``beta`` only.
SUPPORTED_CHANNELS: Final[tuple[str, ...]] = ("stable", "beta")

#: Platform keys the Tauri updater consumes (spec §4). A manifest may omit a
#: target (a partial rollout), but may not invent one.
SUPPORTED_TARGETS: Final[tuple[str, ...]] = (
    "darwin-aarch64",
    "darwin-x86_64",
    "windows-x86_64",
    "linux-x86_64",
)

#: Artifact URLs are host-pinned (spec §4: "any other host is refused").
ALLOWED_URL_PREFIX: Final[str] = "https://github.com/"

#: ...AND path-pinned. Spec §4 requires
#: ``https://github.com/<owner>/<repo>/releases/download/<tag>/<file>``.
#: Pinning only the host accepts any attacker-controlled path on github.com —
#: e.g. ``https://github.com/attacker/pages-site/evil.app.tar.gz`` or a
#: ``/raw/main/`` blob. The Rust client enforces this segment
#: (``update_policy.rs`` RELEASE_DOWNLOAD_PATH_SEGMENT); a Python validator
#: that does not would sign off on manifests the client must refuse, leaving
#: the two consumers of this schema on different security boundaries.
RELEASE_DOWNLOAD_PATH_SEGMENT: Final[str] = "/releases/download/"

#: A ``/releases/download/v<semver>/`` tag segment, when the URL carries one.
_URL_RELEASE_TAG_RE: Final[re.Pattern[str]] = re.compile(
    r"/releases/download/v(\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?)/"
)


def _release_tag_in_url(url: str) -> str | None:
    """The SemVer tag a release-download URL encodes, if it encodes one.

    Spec §4 requires the ``/releases/download/`` path but does not mandate a
    version segment, so a URL without a SemVer-shaped tag is legal and simply
    unverifiable here.
    """
    match = _URL_RELEASE_TAG_RE.search(url)
    return match.group(1) if match else None


#: The sentinel version a never-published channel seed carries. Never newer
#: than any running build, so a client reads it as "no update available".
PLACEHOLDER_VERSION: Final[str] = "0.0.0"

#: A platform entry carries exactly these keys — the shape is closed.
_ALLOWED_TARGET_FIELDS: Final[frozenset[str]] = frozenset({"url", "signature"})

#: Base64 (standard alphabet, optional padding).
_BASE64_RE: Final[re.Pattern[str]] = re.compile(r"[A-Za-z0-9+/]+={0,2}")

_LOGGER: Final[logging.Logger] = logging.getLogger("rytm.release")


class ViolationCode(str, Enum):
    """Closed vocabulary of release-toolkit failure reasons.

    Every validation failure and every :class:`ReleaseError` names one of
    these. Callers branch on the code; :attr:`ManifestViolation.message` is a
    short human note for logs and step summaries only, and never carries an
    absolute path.
    """

    # Version-level
    VERSION_MALFORMED = "release.version.malformed"
    VERSION_FILE_MISSING = "release.version.file_missing"
    VERSION_FILE_EMPTY = "release.version.file_empty"
    VERSION_FILE_MULTILINE = "release.version.file_multiline"

    # Manifest envelope
    MANIFEST_NOT_OBJECT = "release.manifest.not_object"
    MANIFEST_MISSING_FIELD = "release.manifest.missing_field"
    MANIFEST_SCHEMA_VERSION_INVALID = "release.manifest.schema_version_invalid"

    # Manifest field-level
    MANIFEST_VERSION_INVALID = "release.manifest.version_invalid"
    MANIFEST_NOTES_INVALID = "release.manifest.notes_invalid"
    MANIFEST_PUB_DATE_INVALID = "release.manifest.pub_date_invalid"
    MANIFEST_HARDWARE_FLAG_INVALID = "release.manifest.hardware_flag_invalid"
    MANIFEST_ROLLOUT_INVALID = "release.manifest.rollout_invalid"
    MANIFEST_MINIMUM_VERSION_INVALID = "release.manifest.minimum_version_invalid"
    MANIFEST_CHANNEL_INVALID = "release.manifest.channel_invalid"
    MANIFEST_CHANNEL_MISMATCH = "release.manifest.channel_mismatch"
    MANIFEST_PRERELEASE_ON_STABLE = "release.manifest.prerelease_on_stable"

    # Platforms block
    MANIFEST_PLATFORMS_INVALID = "release.manifest.platforms_invalid"
    MANIFEST_PLATFORMS_EMPTY = "release.manifest.platforms_empty"
    MANIFEST_TARGET_UNKNOWN = "release.manifest.target_unknown"
    MANIFEST_TARGET_ENTRY_INVALID = "release.manifest.target_entry_invalid"
    MANIFEST_SIGNATURE_MISSING = "release.manifest.signature_missing"
    MANIFEST_URL_MISSING = "release.manifest.url_missing"
    MANIFEST_URL_NOT_PINNED = "release.manifest.url_not_pinned"
    MANIFEST_URL_VERSION_MISMATCH = "release.manifest.url_version_mismatch"
    MANIFEST_SIGNATURE_NOT_BASE64 = "release.manifest.signature_not_base64"
    MANIFEST_PLATFORM_UNKNOWN_FIELD = "release.manifest.platform_unknown_field"
    MANIFEST_MINIMUM_VERSION_EXCEEDS_VERSION = "release.manifest.minimum_version_exceeds_version"

    # Build-provenance block — advisory only (spec §4: a client "must not
    # refuse an update over provenance fields").
    MANIFEST_PROVENANCE_INVALID = "release.manifest.provenance_invalid"
    MANIFEST_PROVENANCE_MISSING_FIELD = "release.manifest.provenance_missing_field"
    MANIFEST_PROVENANCE_FIELD_INVALID = "release.manifest.provenance_field_invalid"

    # Generator self-check
    GENERATE_PRODUCED_INVALID = "release.generate.produced_invalid"


#: Violation codes that are reported but do NOT make a manifest unacceptable.
#:
#: Spec §4: ``build`` is informational provenance, "never validated for update
#: eligibility — a client must not refuse an update over provenance fields".
#: Reporting them keeps the pipeline honest (a release whose provenance is
#: malformed is a real bug worth a red step summary) without letting a
#: cosmetic provenance defect block a shipped update.
ADVISORY_VIOLATION_CODES: Final[frozenset[ViolationCode]] = frozenset(
    {
        ViolationCode.MANIFEST_PROVENANCE_MISSING_FIELD,
        ViolationCode.MANIFEST_PROVENANCE_FIELD_INVALID,
        ViolationCode.MANIFEST_PROVENANCE_INVALID,
    }
)


@dataclass(frozen=True, slots=True)
class ManifestViolation:
    """One typed reason a manifest is unacceptable (or advisory-flagged).

    ``code`` is the closed-vocabulary contract callers branch on. ``pointer``
    is a JSON-pointer-ish path into the manifest
    (``platforms/darwin-aarch64/url``) so a workflow step summary can name the
    failing field. ``message`` is a short log-only note that never embeds an
    absolute filesystem path or a raw exception string.
    """

    code: ViolationCode
    pointer: str = ""
    message: str = ""

    @property
    def is_advisory(self) -> bool:
        """Whether this violation is reported but does not reject the manifest."""
        return self.code in ADVISORY_VIOLATION_CODES

    def as_dict(self) -> dict[str, object]:
        """Render as a JSON-serializable record (for step summaries / logs)."""
        return {
            "code": self.code.value,
            "pointer": self.pointer,
            "message": self.message,
            "advisory": self.is_advisory,
        }


class ReleaseError(Exception):
    """Raised for a release-toolkit failure that is not a manifest violation.

    Always carries a :class:`ViolationCode`; callers branch on ``code`` rather
    than parsing the message.
    """

    def __init__(self, code: ViolationCode, detail: str = "") -> None:
        super().__init__(f"{code.value}: {detail}" if detail else code.value)
        self.code: Final[ViolationCode] = code
        self.detail: Final[str] = detail


def redact_path(path: Path) -> str:
    """Render ``path`` relative to the repo root, never as an absolute path.

    Emitted details and log records must not leak a developer's or a CI
    runner's home directory (Gate 7). A path outside the repo degrades to its
    bare name.
    """
    try:
        return path.resolve().relative_to(PROJECT_ROOT).as_posix()
    except ValueError:
        return path.name


def log_event(event: str, /, **fields: object) -> None:
    """Emit one structured single-line JSON record on the ``rytm.release`` logger."""
    payload: dict[str, object] = {"event": event}
    payload.update(fields)
    _LOGGER.info(json.dumps(payload, sort_keys=True, default=str))


@dataclass(slots=True)
class ReleaseMetrics:
    """In-process counters for the release boundary (Gate 7).

    Deliberately local to the release toolkit:
    ``rytm_randomizer.observability.metrics.MidiMetrics`` is the runtime
    MIDI-hot-path recorder with a fixed ``record_*`` vocabulary and no release
    concepts, and ``scripts/`` sits outside the package. Reusing it would mean
    widening a hot-path type for build tooling.
    """

    versions_parsed: int = 0
    manifests_validated: int = 0
    manifests_rejected: int = 0
    manifests_generated: int = 0
    violations_by_code: dict[str, int] = field(default_factory=dict)

    def record_version_parsed(self) -> None:
        self.versions_parsed += 1

    def record_manifest_validated(self, violations: Sequence[ManifestViolation]) -> None:
        self.manifests_validated += 1
        if any(not violation.is_advisory for violation in violations):
            self.manifests_rejected += 1
        for violation in violations:
            key = violation.code.value
            self.violations_by_code[key] = self.violations_by_code.get(key, 0) + 1

    def record_manifest_generated(self) -> None:
        self.manifests_generated += 1

    def format_summary(self) -> str:
        """One-line human summary, mirroring ``MidiMetrics.format_summary``."""
        codes = ", ".join(
            f"{code}={count}" for code, count in sorted(self.violations_by_code.items())
        )
        return (
            f"release: parsed={self.versions_parsed} "
            f"validated={self.manifests_validated} "
            f"rejected={self.manifests_rejected} "
            f"generated={self.manifests_generated} "
            f"violations=[{codes}]"
        )


_METRICS: Final[ReleaseMetrics] = ReleaseMetrics()


def get_metrics() -> ReleaseMetrics:
    """Return the process-wide release metrics recorder."""
    return _METRICS


# ---------------------------------------------------------------------------
# SemVer (spec §2)
# ---------------------------------------------------------------------------

# semver.org's official recommended pattern, with named groups.
_SEMVER_RE: Final[re.Pattern[str]] = re.compile(
    r"^(?P<major>0|[1-9]\d*)"
    r"\.(?P<minor>0|[1-9]\d*)"
    r"\.(?P<patch>0|[1-9]\d*)"
    r"(?:-(?P<prerelease>"
    r"(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)"
    r"(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*"
    r"))?"
    r"(?:\+(?P<build>[0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?$"
)

_NUMERIC_IDENTIFIER_RE: Final[re.Pattern[str]] = re.compile(r"^(?:0|[1-9]\d*)$")


@total_ordering
@dataclass(frozen=True, slots=True)
class Version:
    """A strict SemVer 2.0.0 version with standard precedence.

    Keyword-constructible with ``major`` / ``minor`` / ``patch`` /
    ``prerelease`` (the frozen consumer-facing shape); ``build`` is parsed and
    preserved but **excluded from precedence** per semver.org §10, so two
    versions differing only in build metadata compare equal.

    Ordering follows semver.org §11: numeric core first, then prerelease rules
    — a prerelease sorts *before* its release; identifiers compare numerically
    when both are numeric and ASCII-lexically otherwise; numeric sorts below
    alphanumeric; and when all shared identifiers are equal the longer list
    wins.
    """

    major: int
    minor: int
    patch: int
    prerelease: tuple[str, ...] = ()
    build: tuple[str, ...] = ()

    @classmethod
    def parse(cls, text: str) -> Version:
        """Parse a strict SemVer string (see :func:`parse_version`)."""
        match = _SEMVER_RE.match(text)
        if match is None:
            raise ReleaseError(ViolationCode.VERSION_MALFORMED, f"not strict SemVer: {text!r}")
        prerelease_raw = match.group("prerelease")
        build_raw = match.group("build")
        _METRICS.record_version_parsed()
        return cls(
            major=int(match.group("major")),
            minor=int(match.group("minor")),
            patch=int(match.group("patch")),
            prerelease=tuple(prerelease_raw.split(".")) if prerelease_raw else (),
            build=tuple(build_raw.split(".")) if build_raw else (),
        )

    @property
    def is_prerelease(self) -> bool:
        """Whether this version carries prerelease identifiers (beta channel only)."""
        return bool(self.prerelease)

    def __str__(self) -> str:
        core = f"{self.major}.{self.minor}.{self.patch}"
        if self.prerelease:
            core = f"{core}-{'.'.join(self.prerelease)}"
        if self.build:
            core = f"{core}+{'.'.join(self.build)}"
        return core

    def _core(self) -> tuple[int, int, int]:
        return (self.major, self.minor, self.patch)

    def __eq__(self, other: object) -> bool:
        """Equality by precedence — build metadata is ignored (semver.org §10)."""
        if not isinstance(other, Version):
            return NotImplemented
        return self._core() == other._core() and self.prerelease == other.prerelease

    def __hash__(self) -> int:
        return hash((self._core(), self.prerelease))

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, Version):
            return NotImplemented
        if self._core() != other._core():
            return self._core() < other._core()
        return _prerelease_lt(self.prerelease, other.prerelease)


def _prerelease_lt(left: tuple[str, ...], right: tuple[str, ...]) -> bool:
    """Return whether prerelease list ``left`` sorts before ``right`` (§11)."""
    if not left:
        # No prerelease: either equal (both empty) or the higher precedence.
        return False
    if not right:
        # A version WITH a prerelease has lower precedence than one without.
        return True
    for left_id, right_id in zip(left, right):
        if left_id == right_id:
            continue
        left_numeric = _NUMERIC_IDENTIFIER_RE.match(left_id) is not None
        right_numeric = _NUMERIC_IDENTIFIER_RE.match(right_id) is not None
        if left_numeric and right_numeric:
            return int(left_id) < int(right_id)
        if left_numeric != right_numeric:
            # Numeric identifiers always have lower precedence than
            # alphanumeric ones.
            return left_numeric
        return left_id < right_id
    # All shared identifiers equal: the shorter list has lower precedence.
    return len(left) < len(right)


def parse_version(text: str) -> Version:
    """Parse a strict SemVer string into a :class:`Version`.

    Raises :class:`ReleaseError` with
    :attr:`ViolationCode.VERSION_MALFORMED` on anything the official
    semver.org pattern rejects — including a leading ``v``, leading zeros in a
    numeric component, and two-component versions.
    """
    return Version.parse(text)


def is_valid_version(text: str) -> bool:
    """Return whether ``text`` is a strict SemVer string (never raises)."""
    return _SEMVER_RE.match(text) is not None


def compare_versions(left: Version | str, right: Version | str) -> int:
    """Three-way compare by SemVer precedence: ``-1`` / ``0`` / ``1``.

    Accepts either parsed :class:`Version` values or raw strings (parsed on
    the way in). Build metadata is ignored, so ``1.0.0+a`` and ``1.0.0+b``
    compare equal (semver.org §10).
    """
    left_version = left if isinstance(left, Version) else parse_version(left)
    right_version = right if isinstance(right, Version) else parse_version(right)
    if left_version == right_version:
        return 0
    return -1 if left_version < right_version else 1


# ---------------------------------------------------------------------------
# VERSION file (spec §2.1)
# ---------------------------------------------------------------------------


def version_file_path(project_root: Path | None = None) -> Path:
    """Return the path of the canonical repo-root ``VERSION`` file."""
    return (project_root or PROJECT_ROOT) / "VERSION"


def read_version_file(project_root: Path | None = None) -> Version:
    """Read and parse the repo-root ``VERSION`` file — the one canonical read.

    Raises :class:`ReleaseError` with a typed code when the file is missing,
    empty, carries more than one non-empty line, or is not strict SemVer.
    """
    path = version_file_path(project_root)
    if not path.is_file():
        raise ReleaseError(ViolationCode.VERSION_FILE_MISSING, redact_path(path))
    raw = path.read_text(encoding="utf-8")
    lines = [line for line in raw.splitlines() if line.strip()]
    if not lines:
        raise ReleaseError(ViolationCode.VERSION_FILE_EMPTY, redact_path(path))
    if len(lines) > 1:
        raise ReleaseError(
            ViolationCode.VERSION_FILE_MULTILINE,
            f"{redact_path(path)} has {len(lines)} non-empty lines",
        )
    return parse_version(lines[0].strip())


# ---------------------------------------------------------------------------
# Update manifest (spec §4)
# ---------------------------------------------------------------------------

#: Fields spec §4 requires in every v1 manifest. Note that UNKNOWN top-level
#: keys are deliberately NOT an error — §4 makes ignoring them the
#: forward-compatibility hinge, gated by ``schema_version``.
_MANIFEST_REQUIRED_FIELDS: Final[frozenset[str]] = frozenset(
    {
        "schema_version",
        "channel",
        "version",
        "pub_date",
        "notes",
        "hardware_revalidation",
        "platforms",
    }
)

#: ``build`` provenance sub-fields (spec §4). Advisory — see
#: :data:`ADVISORY_VIOLATION_CODES`.
_PROVENANCE_REQUIRED_FIELDS: Final[frozenset[str]] = frozenset(
    {"source_sha", "workflow_run_url", "builder_workflow_sha"}
)

#: RFC-3339 UTC instant, as emitted by the release workflow.
_RFC3339_UTC_RE: Final[re.Pattern[str]] = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z$"
)

_GIT_SHA_RE: Final[re.Pattern[str]] = re.compile(r"^[0-9a-f]{40}$")


def _validate_envelope(manifest: Mapping[str, object]) -> list[ManifestViolation]:
    """Check required fields are present. Unknown keys are ignored (spec §4)."""
    return [
        ManifestViolation(ViolationCode.MANIFEST_MISSING_FIELD, missing, "required field absent")
        for missing in sorted(_MANIFEST_REQUIRED_FIELDS - set(manifest))
    ]


def _validate_scalars(
    manifest: Mapping[str, object], expected_channel: str | None
) -> list[ManifestViolation]:
    violations: list[ManifestViolation] = []

    schema_version = manifest.get("schema_version")
    # `bool` is an `int` subclass, so a JSON `true` would otherwise satisfy
    # `== 1` and be read as schema version 1.
    if isinstance(schema_version, bool) or schema_version != MANIFEST_SCHEMA_VERSION:
        violations.append(
            ManifestViolation(
                ViolationCode.MANIFEST_SCHEMA_VERSION_INVALID,
                "schema_version",
                f"expected {MANIFEST_SCHEMA_VERSION}",
            )
        )

    channel = manifest.get("channel")
    channel_ok = isinstance(channel, str) and channel in SUPPORTED_CHANNELS
    if not channel_ok:
        violations.append(
            ManifestViolation(
                ViolationCode.MANIFEST_CHANNEL_INVALID,
                "channel",
                f"expected one of {list(SUPPORTED_CHANNELS)}",
            )
        )
    elif expected_channel is not None and channel != expected_channel:
        violations.append(
            ManifestViolation(
                ViolationCode.MANIFEST_CHANNEL_MISMATCH,
                "channel",
                "manifest channel does not match the file being written",
            )
        )

    version = manifest.get("version")
    version_parsed: Version | None = None
    if not isinstance(version, str) or not is_valid_version(version):
        violations.append(
            ManifestViolation(
                ViolationCode.MANIFEST_VERSION_INVALID, "version", "not strict SemVer"
            )
        )
    else:
        version_parsed = parse_version(version)
        # Spec §2.5: pre-release tags flow to the beta channel only.
        if version_parsed.is_prerelease and channel == "stable":
            violations.append(
                ManifestViolation(
                    ViolationCode.MANIFEST_PRERELEASE_ON_STABLE,
                    "version",
                    "a prerelease version may only ship on the beta channel",
                )
            )

    if not isinstance(manifest.get("notes"), str):
        violations.append(
            ManifestViolation(ViolationCode.MANIFEST_NOTES_INVALID, "notes", "expected a string")
        )

    pub_date = manifest.get("pub_date")
    if not isinstance(pub_date, str) or _RFC3339_UTC_RE.match(pub_date) is None:
        violations.append(
            ManifestViolation(
                ViolationCode.MANIFEST_PUB_DATE_INVALID, "pub_date", "expected RFC-3339 UTC"
            )
        )

    if not isinstance(manifest.get("hardware_revalidation"), bool):
        violations.append(
            ManifestViolation(
                ViolationCode.MANIFEST_HARDWARE_FLAG_INVALID,
                "hardware_revalidation",
                "expected a bool",
            )
        )

    violations.extend(_validate_rollout(manifest))
    violations.extend(_validate_minimum_version(manifest))
    return violations


def _validate_rollout(manifest: Mapping[str, object]) -> list[ManifestViolation]:
    """Validate ``rollout_percent`` (spec §4: integer 0-100; missing ⇒ 100)."""
    if "rollout_percent" not in manifest:
        return []
    rollout = manifest["rollout_percent"]
    # bool is an int subclass; `true` is not a rollout percentage.
    if isinstance(rollout, bool) or not isinstance(rollout, int) or not 0 <= rollout <= 100:
        return [
            ManifestViolation(
                ViolationCode.MANIFEST_ROLLOUT_INVALID,
                "rollout_percent",
                "expected an int in 0..100",
            )
        ]
    return []


def _validate_minimum_version(manifest: Mapping[str, object]) -> list[ManifestViolation]:
    """Validate the advisory ``minimum_version`` field (spec §4).

    Advisory-banner-only in v1: the client shows a banner and never blocks.
    ``null`` (or absent) means "no floor". Only the shape is checked here —
    making a floor *blocking* is explicitly a future decision, not a hotfix.
    """
    minimum = manifest.get("minimum_version")
    if minimum is None:
        return []
    if not isinstance(minimum, str) or not is_valid_version(minimum):
        return [
            ManifestViolation(
                ViolationCode.MANIFEST_MINIMUM_VERSION_INVALID,
                "minimum_version",
                "expected null or strict SemVer",
            )
        ]
    return []


def _validate_platforms(
    manifest: Mapping[str, object], *, version: str | None = None
) -> list[ManifestViolation]:
    platforms = manifest.get("platforms")
    if not isinstance(platforms, Mapping):
        return [
            ManifestViolation(
                ViolationCode.MANIFEST_PLATFORMS_INVALID, "platforms", "expected an object"
            )
        ]
    if not platforms:
        if manifest.get("placeholder") is True and manifest.get("version") == PLACEHOLDER_VERSION:
            # A channel that has never published. Spec §4: a client acts only
            # when `version` is NEWER than what it runs, so the 0.0.0 sentinel
            # already reads as "no update available" — which is exactly what
            # the first fetch from a fresh `releases` branch must mean, not an
            # error. The exemption requires BOTH the explicit flag and the
            # sentinel version, so a real manifest can never claim it.
            return []
        return [
            ManifestViolation(
                ViolationCode.MANIFEST_PLATFORMS_EMPTY,
                "platforms",
                "at least one target required",
            )
        ]

    violations: list[ManifestViolation] = []
    for target in sorted(platforms):
        pointer = f"platforms/{target}"
        if target not in SUPPORTED_TARGETS:
            violations.append(
                ManifestViolation(
                    ViolationCode.MANIFEST_TARGET_UNKNOWN,
                    pointer,
                    f"expected one of {list(SUPPORTED_TARGETS)}",
                )
            )
            continue
        violations.extend(_validate_target_entry(platforms[target], pointer, version=version))
    return violations


def _validate_target_entry(
    entry: object, pointer: str, *, version: str | None = None
) -> list[ManifestViolation]:
    if not isinstance(entry, Mapping):
        return [
            ManifestViolation(
                ViolationCode.MANIFEST_TARGET_ENTRY_INVALID, pointer, "expected an object"
            )
        ]

    violations: list[ManifestViolation] = []
    signature = entry.get("signature")
    if not isinstance(signature, str) or not signature:
        violations.append(
            ManifestViolation(
                ViolationCode.MANIFEST_SIGNATURE_MISSING,
                f"{pointer}/signature",
                "expected a non-empty updater signature",
            )
        )
    elif not _BASE64_RE.fullmatch(signature):
        # The Tauri updater refuses a non-base64 signature at install time.
        # Catching it here means the pipeline never publishes a manifest whose
        # artifacts no client can install.
        violations.append(
            ManifestViolation(
                ViolationCode.MANIFEST_SIGNATURE_NOT_BASE64,
                f"{pointer}/signature",
                "expected a base64 updater signature",
            )
        )

    url = entry.get("url")
    if not isinstance(url, str) or not url:
        violations.append(
            ManifestViolation(
                ViolationCode.MANIFEST_URL_MISSING, f"{pointer}/url", "expected a non-empty URL"
            )
        )
    elif not url.startswith(ALLOWED_URL_PREFIX):
        violations.append(
            ManifestViolation(
                ViolationCode.MANIFEST_URL_NOT_PINNED,
                f"{pointer}/url",
                "artifact host must be the pinned GitHub releases host",
            )
        )
    elif RELEASE_DOWNLOAD_PATH_SEGMENT not in url:
        violations.append(
            ManifestViolation(
                ViolationCode.MANIFEST_URL_NOT_PINNED,
                f"{pointer}/url",
                "artifact path must be a GitHub releases download path",
            )
        )
    elif (
        version is not None
        and (_url_tag := _release_tag_in_url(url)) is not None
        and _url_tag != version
    ):
        # A URL pointing at a DIFFERENT release than the manifest declares ships
        # the wrong binary to everyone on the channel — and the signature would
        # still verify, because it signs that other artifact.
        violations.append(
            ManifestViolation(
                ViolationCode.MANIFEST_URL_VERSION_MISMATCH,
                f"{pointer}/url",
                f"artifact URL does not point at the v{version} release",
            )
        )
    return violations


def _validate_build(manifest: Mapping[str, object]) -> list[ManifestViolation]:
    """Validate the ``build`` provenance block — advisory only (spec §4).

    ``build`` is "informational provenance (never validated for update
    eligibility — a client must not refuse an update over provenance
    fields)". Every code emitted here is in :data:`ADVISORY_VIOLATION_CODES`,
    so a malformed block is *reported* (the pipeline should notice) but never
    makes a manifest unacceptable.
    """
    if "build" not in manifest:
        return []
    build = manifest["build"]
    if not isinstance(build, Mapping):
        return [
            ManifestViolation(
                ViolationCode.MANIFEST_PROVENANCE_INVALID, "build", "expected an object"
            )
        ]

    violations: list[ManifestViolation] = [
        ManifestViolation(
            ViolationCode.MANIFEST_PROVENANCE_MISSING_FIELD,
            f"build/{missing}",
            "required provenance field absent",
        )
        for missing in sorted(_PROVENANCE_REQUIRED_FIELDS - set(build))
    ]

    for sha_field in ("source_sha", "builder_workflow_sha"):
        if sha_field not in build:
            continue
        value = build[sha_field]
        if not isinstance(value, str) or _GIT_SHA_RE.match(value) is None:
            violations.append(
                ManifestViolation(
                    ViolationCode.MANIFEST_PROVENANCE_FIELD_INVALID,
                    f"build/{sha_field}",
                    "expected a 40-char lowercase git sha",
                )
            )

    if "workflow_run_url" in build:
        run_url = build["workflow_run_url"]
        if not isinstance(run_url, str) or not run_url.startswith(ALLOWED_URL_PREFIX):
            violations.append(
                ManifestViolation(
                    ViolationCode.MANIFEST_PROVENANCE_FIELD_INVALID,
                    "build/workflow_run_url",
                    "expected a pinned GitHub URL",
                )
            )
    return violations


def validate_manifest(
    manifest: object, *, expected_channel: str | None = None
) -> tuple[ManifestViolation, ...]:
    """Validate a channel manifest; return every violation found.

    Returns an empty tuple when the manifest is fully clean. Never raises for
    manifest content — a malformed manifest is data, and every rejection is a
    typed :class:`ManifestViolation`. Pass ``expected_channel`` at a site that
    knows which file it is writing (``stable.json`` / ``beta.json``) so a
    cross-wired manifest is caught.

    Validation does not short-circuit at the envelope: field checks still run
    on whatever is present, so one pass reports every problem. Some returned
    violations are advisory (see :data:`ADVISORY_VIOLATION_CODES`) — use
    :func:`manifest_is_acceptable` for the ship / no-ship verdict.
    """
    if not isinstance(manifest, Mapping):
        violations = (
            ManifestViolation(ViolationCode.MANIFEST_NOT_OBJECT, "", "expected a JSON object"),
        )
        _METRICS.record_manifest_validated(violations)
        log_event("release.manifest.validated", ok=False, violations=1)
        return violations

    declared_version = manifest.get("version")
    version_for_urls = declared_version if isinstance(declared_version, str) else None

    found: list[ManifestViolation] = []
    found.extend(_validate_envelope(manifest))
    found.extend(_validate_scalars(manifest, expected_channel))
    found.extend(_validate_platforms(manifest, version=version_for_urls))
    found.extend(_validate_build(manifest))
    result = tuple(found)
    _METRICS.record_manifest_validated(result)
    log_event(
        "release.manifest.validated",
        ok=manifest_is_acceptable(result),
        violations=len(result),
        codes=sorted({violation.code.value for violation in result}),
    )
    return result


def manifest_is_acceptable(violations: Sequence[ManifestViolation]) -> bool:
    """Whether ``violations`` permit shipping — i.e. none is blocking.

    Advisory provenance violations (spec §4) are reported but do not block.
    """
    return not any(not violation.is_advisory for violation in violations)


def generate_manifest(
    *,
    channel: str,
    version: str,
    pub_date: str,
    notes: str,
    platforms: Mapping[str, Mapping[str, str]],
    source_sha: str,
    workflow_run_url: str,
    builder_workflow_sha: str,
    hardware_revalidation: bool = False,
    rollout_percent: int = 100,
    minimum_version: str | None = None,
) -> dict[str, object]:
    """Build a spec §4 channel manifest and validate it before returning.

    The generator round-trips its own :func:`validate_manifest` in-process
    (the R1 requirement), so no caller can obtain a manifest this module's own
    gate would refuse — the pipeline cannot publish something
    ``manifest-validate.yml`` would then reject.

    Raises :class:`ReleaseError` with
    :attr:`ViolationCode.GENERATE_PRODUCED_INVALID` when the inputs would
    produce a manifest with any *blocking* violation; the offending codes are
    in ``detail`` (codes only — no absolute paths, no caller data echoed
    back). Advisory provenance defects are logged, not raised, mirroring the
    client's own must-not-refuse rule.
    """
    manifest: dict[str, object] = {
        "schema_version": MANIFEST_SCHEMA_VERSION,
        "channel": channel,
        "version": version,
        "pub_date": pub_date,
        "notes": notes,
        "hardware_revalidation": hardware_revalidation,
        "rollout_percent": rollout_percent,
        "minimum_version": minimum_version,
        "build": {
            "source_sha": source_sha,
            "workflow_run_url": workflow_run_url,
            "builder_workflow_sha": builder_workflow_sha,
        },
        "platforms": {target: dict(entry) for target, entry in sorted(platforms.items())},
    }

    violations = validate_manifest(manifest, expected_channel=channel)
    if not manifest_is_acceptable(violations):
        codes = ",".join(sorted({v.code.value for v in violations if not v.is_advisory}))
        log_event("release.manifest.generate_refused", channel=channel, codes=codes)
        raise ReleaseError(ViolationCode.GENERATE_PRODUCED_INVALID, codes)
    if violations:
        log_event(
            "release.manifest.generate_advisory",
            channel=channel,
            codes=sorted({v.code.value for v in violations}),
        )

    _METRICS.record_manifest_generated()
    log_event("release.manifest.generated", channel=channel, version=version)
    return manifest


# ---------------------------------------------------------------------------
# Command-line entry point
# ---------------------------------------------------------------------------
#
# `release.yml` and `promote.yml` both invoke this file as a script:
#
#     python scripts/release_lib.py generate --channel beta --version X --output F
#
# Without a __main__ block that invocation executes the module body, prints
# nothing, writes nothing, and EXITS 0 — the workflow step reports success
# having produced no manifest, and the failure only surfaces one step later
# as "manifest could not be read", pointing the operator at the wrong cause.
# `tests/architecture/test_workflow_script_invocations_resolve.py` now pins
# every such call site to a real entry point.
#
# The CLI stays thin (reuse contract R5): it parses arguments, derives the
# build-provenance fields from the CI environment, and delegates to
# `generate_manifest`, which validates its own output before returning.


def _artifact_url(*, repository: str, version: str, target: str) -> str:
    """The spec §4 release-download URL for one platform artifact."""
    return (
        f"{ALLOWED_URL_PREFIX}{repository}"
        f"{RELEASE_DOWNLOAD_PATH_SEGMENT}v{version}/"
        f"RytmRandomizer-{version}-{target}.tar.gz"
    )


def _platforms_from_env(*, repository: str, version: str) -> dict[str, dict[str, str]]:
    """Build the per-target platform table.

    Signatures come from the environment (the signing step writes one
    ``RYTM_SIGNATURE_<TARGET>`` per artifact). A target with no signature is
    omitted rather than emitted unsigned: `validate_manifest` refuses an
    unsigned entry, so omitting keeps the failure honest and specific.
    """
    platforms: dict[str, dict[str, str]] = {}
    for target in SUPPORTED_TARGETS:
        env_key = "RYTM_SIGNATURE_" + target.replace("-", "_").upper()
        signature = os.environ.get(env_key, "").strip()
        if not signature:
            continue
        platforms[target] = {
            "url": _artifact_url(repository=repository, version=version, target=target),
            "signature": signature,
        }
    return platforms


def _build_generate_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="release_lib.py",
        description="Release toolkit CLI (manifest generation).",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    gen = sub.add_parser("generate", help="Generate a validated channel manifest.")
    gen.add_argument("--channel", required=True, choices=sorted(SUPPORTED_CHANNELS))
    gen.add_argument("--version", required=True)
    gen.add_argument("--output", required=True, type=Path)
    gen.add_argument("--rollout-percent", type=int, default=100)
    gen.add_argument("--notes", default="")
    gen.add_argument("--minimum-version", default=None)
    gen.add_argument(
        "--pub-date",
        default=None,
        help="RFC3339 timestamp. Defaults to $RYTM_PUB_DATE (injected, never read "
        "from the wall clock, so a run is reproducible).",
    )
    return gen.parent if False else parser  # parser owns the subcommand


def main(argv: Sequence[str] | None = None) -> int:
    """Thin CLI over :func:`generate_manifest`. Non-zero on any refusal."""
    args = _build_generate_parser().parse_args(argv)

    repository = os.environ.get("GITHUB_REPOSITORY", "").strip()
    if not repository:
        print(
            "error: GITHUB_REPOSITORY is unset; the artifact URLs are built from it.",
            file=sys.stderr,
        )
        return 2

    pub_date = args.pub_date or os.environ.get("RYTM_PUB_DATE", "").strip()
    if not pub_date:
        print(
            "error: no publication date. Pass --pub-date or set RYTM_PUB_DATE; "
            "it is never read from the wall clock so a rerun is reproducible.",
            file=sys.stderr,
        )
        return 2

    platforms = _platforms_from_env(repository=repository, version=args.version)
    if not platforms:
        print(
            "error: no signed platform artifacts found. The signing step sets one "
            "RYTM_SIGNATURE_<TARGET> per artifact; with none set there is nothing "
            "to publish and an empty manifest would be refused anyway.",
            file=sys.stderr,
        )
        return 2

    try:
        manifest = generate_manifest(
            channel=args.channel,
            version=args.version,
            pub_date=pub_date,
            notes=args.notes,
            platforms=platforms,
            source_sha=os.environ.get("GITHUB_SHA", ""),
            workflow_run_url=(
                f"{ALLOWED_URL_PREFIX}{repository}/actions/runs/"
                f"{os.environ.get('GITHUB_RUN_ID', '')}"
            ),
            builder_workflow_sha=os.environ.get("GITHUB_WORKFLOW_SHA", "")
            or os.environ.get("GITHUB_SHA", ""),
            rollout_percent=args.rollout_percent,
            minimum_version=args.minimum_version,
        )
    except ReleaseError as error:
        print(f"error: manifest refused by its own validator: {error}", file=sys.stderr)
        return 1

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {args.output} ({args.channel} {args.version})")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
