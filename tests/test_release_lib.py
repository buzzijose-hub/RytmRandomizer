"""Tests for ``scripts/release_lib.py`` — the R1 release toolkit.

Three obligations, per the implementation plan:

1. **SemVer vectors** — precedence including prerelease ordering (semver.org
   §11) and build metadata excluded from precedence (§10).
2. **Every typed reason code** — each :class:`ViolationCode` a validator can
   emit has a test that provokes exactly it.
3. **100% branch coverage** on the module.
"""

from __future__ import annotations

import itertools
import json
import logging
import sys
from pathlib import Path
from typing import Any, Final

import pytest

PROJECT_ROOT: Final[Path] = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from release_lib import (  # noqa: E402
    ADVISORY_VIOLATION_CODES,
    ALLOWED_URL_PREFIX,
    MANIFEST_SCHEMA_VERSION,
    SUPPORTED_CHANNELS,
    SUPPORTED_TARGETS,
    ManifestViolation,
    ReleaseError,
    ReleaseMetrics,
    Version,
    ViolationCode,
    compare_versions,
    generate_manifest,
    get_metrics,
    is_valid_version,
    log_event,
    manifest_is_acceptable,
    parse_version,
    read_version_file,
    redact_path,
    validate_manifest,
    version_file_path,
)

pytestmark = pytest.mark.fast

_SHA: Final[str] = "a" * 40
_OTHER_SHA: Final[str] = "b" * 40
_RUN_URL: Final[str] = "https://github.com/o/r/actions/runs/1"


def _valid_manifest(**overrides: Any) -> dict[str, Any]:
    """A spec §4-shaped manifest that validates clean; ``overrides`` mutate it.

    The default platform URL is derived from the manifest's own ``version`` so
    that overriding the version keeps the document self-consistent. A manifest
    whose URL points at a *different* release than it declares ships the wrong
    binary with a signature that still verifies, and the validator refuses it —
    a hardcoded URL here made every version-overriding test trip that rule.
    """
    version = str(overrides.get("version", "1.35.1"))
    manifest: dict[str, Any] = {
        "schema_version": MANIFEST_SCHEMA_VERSION,
        "channel": "stable",
        "version": "1.35.1",
        "pub_date": "2026-09-14T00:00:00Z",
        "notes": "release notes",
        "hardware_revalidation": False,
        "rollout_percent": 100,
        "minimum_version": None,
        "build": {
            "source_sha": _SHA,
            "workflow_run_url": _RUN_URL,
            "builder_workflow_sha": _OTHER_SHA,
        },
        "platforms": {
            "darwin-aarch64": {
                "signature": "sig",
                "url": f"{ALLOWED_URL_PREFIX}o/r/releases/download/v{version}/a.tar.gz",
            }
        },
    }
    manifest.update(overrides)
    return manifest


def _codes(violations: tuple[ManifestViolation, ...]) -> set[str]:
    return {violation.code.value for violation in violations}


# ---------------------------------------------------------------------------
# SemVer parsing
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "text",
    [
        "0.0.0",
        "1.0.0",
        "1.34.0",
        "10.20.30",
        "1.0.0-beta.1",
        "1.0.0-alpha",
        "1.0.0-alpha.beta.1",
        "1.0.0-0.3.7",
        "1.0.0-x-y-z.--",
        "1.0.0+build.1",
        "1.0.0-beta.1+exp.sha.5114f85",
    ],
)
def test_parse_version_accepts_strict_semver(text: str) -> None:
    assert is_valid_version(text)
    assert str(parse_version(text)) == text


@pytest.mark.parametrize(
    "text",
    [
        "",
        "1",
        "1.0",
        "v1.0.0",  # a leading v is a tag name, not a version
        "1.0.0.0",
        "01.0.0",  # leading zeros are forbidden
        "1.00.0",
        "1.0.0-",
        "1.0.0-01",  # numeric prerelease identifiers may not have leading zeros
        "1.0.0+",
        "1.0.0 ",
        "1.0.0-beta_1",
    ],
)
def test_parse_version_rejects_non_semver(text: str) -> None:
    assert not is_valid_version(text)
    with pytest.raises(ReleaseError) as excinfo:
        parse_version(text)
    assert excinfo.value.code is ViolationCode.VERSION_MALFORMED


def test_version_is_keyword_constructible_and_frozen() -> None:
    version = Version(major=1, minor=34, patch=0)
    assert (version.major, version.minor, version.patch) == (1, 34, 0)
    assert version.prerelease == ()
    assert not version.is_prerelease
    with pytest.raises(AttributeError):
        version.major = 2  # type: ignore[misc]


def test_version_exposes_parsed_components() -> None:
    version = parse_version("2.3.4-beta.5+build.9")
    assert version == Version(major=2, minor=3, patch=4, prerelease=("beta", "5"))
    assert version.build == ("build", "9")
    assert version.is_prerelease


# ---------------------------------------------------------------------------
# SemVer precedence (semver.org §10 / §11)
# ---------------------------------------------------------------------------

#: semver.org §11's own worked example, in strictly ascending precedence.
_ASCENDING: Final[tuple[str, ...]] = (
    "1.0.0-alpha",
    "1.0.0-alpha.1",
    "1.0.0-alpha.beta",
    "1.0.0-beta",
    "1.0.0-beta.2",
    "1.0.0-beta.11",
    "1.0.0-rc.1",
    "1.0.0",
    "1.0.1",
    "1.1.0",
    "2.0.0",
)


def test_semver_precedence_chain_is_totally_ordered() -> None:
    for lower, higher in itertools.combinations(_ASCENDING, 2):
        assert compare_versions(lower, higher) == -1, f"{lower} should precede {higher}"
        assert compare_versions(higher, lower) == 1
        assert parse_version(lower) < parse_version(higher)
        assert parse_version(higher) > parse_version(lower)


def test_semver_numeric_identifiers_compare_numerically_not_lexically() -> None:
    # The classic trap: "11" sorts AFTER "2" numerically, before it lexically.
    assert compare_versions("1.0.0-beta.11", "1.0.0-beta.2") == 1


def test_semver_numeric_identifier_sorts_below_alphanumeric() -> None:
    assert compare_versions("1.0.0-1", "1.0.0-alpha") == -1


def test_semver_longer_prerelease_list_wins_when_prefix_equal() -> None:
    assert compare_versions("1.0.0-alpha", "1.0.0-alpha.1") == -1


def test_semver_prerelease_precedes_its_release() -> None:
    assert compare_versions("1.35.0-beta.1", "1.35.0") == -1
    assert compare_versions("1.35.0", "1.35.0-beta.1") == 1


@pytest.mark.parametrize(
    ("left", "right"),
    [
        ("1.0.0+build.1", "1.0.0+build.2"),
        ("1.0.0+a", "1.0.0"),
        ("1.0.0-beta.1+x", "1.0.0-beta.1+y"),
    ],
)
def test_build_metadata_is_excluded_from_precedence(left: str, right: str) -> None:
    """semver.org §10 — build metadata MUST be ignored when determining precedence."""
    assert compare_versions(left, right) == 0
    assert parse_version(left) == parse_version(right)
    assert hash(parse_version(left)) == hash(parse_version(right))
    assert not parse_version(left) < parse_version(right)


def test_equal_versions_compare_zero() -> None:
    assert compare_versions("1.2.3", "1.2.3") == 0
    assert compare_versions(parse_version("1.2.3"), "1.2.3") == 0
    assert compare_versions("1.2.3", parse_version("1.2.3")) == 0


def test_version_comparison_with_foreign_type_is_not_implemented() -> None:
    version = parse_version("1.0.0")
    assert version.__eq__("1.0.0") is NotImplemented
    assert version.__lt__("1.0.0") is NotImplemented
    assert version != "1.0.0"


def test_versions_are_hashable_and_sortable() -> None:
    parsed = [parse_version(text) for text in reversed(_ASCENDING)]
    assert [str(v) for v in sorted(parsed)] == list(_ASCENDING)
    assert len({parse_version(t) for t in _ASCENDING}) == len(_ASCENDING)


# ---------------------------------------------------------------------------
# VERSION file
# ---------------------------------------------------------------------------


def test_read_version_file_reads_the_repo_root_version() -> None:
    assert str(read_version_file()) == (PROJECT_ROOT / "VERSION").read_text().strip()


def test_version_file_path_defaults_to_the_repo_root() -> None:
    assert version_file_path() == PROJECT_ROOT / "VERSION"
    assert version_file_path(Path("/x")) == Path("/x/VERSION")


def test_read_version_file_missing(tmp_path: Path) -> None:
    with pytest.raises(ReleaseError) as excinfo:
        read_version_file(tmp_path)
    assert excinfo.value.code is ViolationCode.VERSION_FILE_MISSING


@pytest.mark.parametrize("content", ["", "\n", "   \n\n"])
def test_read_version_file_empty(tmp_path: Path, content: str) -> None:
    (tmp_path / "VERSION").write_text(content, encoding="utf-8")
    with pytest.raises(ReleaseError) as excinfo:
        read_version_file(tmp_path)
    assert excinfo.value.code is ViolationCode.VERSION_FILE_EMPTY


def test_read_version_file_multiline(tmp_path: Path) -> None:
    (tmp_path / "VERSION").write_text("1.0.0\n2.0.0\n", encoding="utf-8")
    with pytest.raises(ReleaseError) as excinfo:
        read_version_file(tmp_path)
    assert excinfo.value.code is ViolationCode.VERSION_FILE_MULTILINE


def test_read_version_file_not_semver(tmp_path: Path) -> None:
    (tmp_path / "VERSION").write_text("v1.0\n", encoding="utf-8")
    with pytest.raises(ReleaseError) as excinfo:
        read_version_file(tmp_path)
    assert excinfo.value.code is ViolationCode.VERSION_MALFORMED


def test_read_version_file_tolerates_surrounding_blank_lines(tmp_path: Path) -> None:
    (tmp_path / "VERSION").write_text("\n  1.34.0  \n\n", encoding="utf-8")
    assert str(read_version_file(tmp_path)) == "1.34.0"


# ---------------------------------------------------------------------------
# Observability helpers (Gate 7)
# ---------------------------------------------------------------------------


def test_redact_path_renders_repo_relative_and_never_absolute() -> None:
    rendered = redact_path(PROJECT_ROOT / "scripts" / "release_lib.py")
    assert rendered == "scripts/release_lib.py"
    assert not Path(rendered).is_absolute()


def test_redact_path_outside_the_repo_degrades_to_the_bare_name() -> None:
    rendered = redact_path(Path("/somewhere/else/secret/VERSION"))
    assert rendered == "VERSION"
    assert "secret" not in rendered


def test_release_error_message_includes_the_code() -> None:
    with_detail = ReleaseError(ViolationCode.VERSION_MALFORMED, "why")
    assert str(with_detail) == "release.version.malformed: why"
    assert with_detail.detail == "why"
    bare = ReleaseError(ViolationCode.VERSION_MALFORMED)
    assert str(bare) == "release.version.malformed"
    assert bare.detail == ""


def test_log_event_emits_one_structured_json_line(caplog: pytest.LogCaptureFixture) -> None:
    with caplog.at_level(logging.INFO, logger="rytm.release"):
        log_event("release.test", channel="beta", count=2)
    (record,) = [r for r in caplog.records if r.name == "rytm.release"]
    payload = json.loads(record.getMessage())
    assert payload == {"event": "release.test", "channel": "beta", "count": 2}


def test_log_event_serializes_non_json_values_without_raising(
    caplog: pytest.LogCaptureFixture,
) -> None:
    with caplog.at_level(logging.INFO, logger="rytm.release"):
        log_event("release.test", version=parse_version("1.0.0"))
    payload = json.loads(caplog.records[-1].getMessage())
    assert payload["version"] == "1.0.0"


def test_get_metrics_returns_the_process_wide_recorder() -> None:
    assert get_metrics() is get_metrics()


def test_release_metrics_counts_and_summarizes() -> None:
    metrics = ReleaseMetrics()
    metrics.record_version_parsed()
    metrics.record_manifest_generated()
    metrics.record_manifest_validated(())
    metrics.record_manifest_validated(
        (ManifestViolation(ViolationCode.MANIFEST_NOTES_INVALID, "notes"),)
    )
    metrics.record_manifest_validated(
        (ManifestViolation(ViolationCode.MANIFEST_NOTES_INVALID, "notes"),)
    )
    summary = metrics.format_summary()
    assert metrics.versions_parsed == 1
    assert metrics.manifests_validated == 3
    assert metrics.manifests_rejected == 2
    assert "release.manifest.notes_invalid=2" in summary
    assert "generated=1" in summary


def test_release_metrics_does_not_count_advisory_only_as_rejected() -> None:
    metrics = ReleaseMetrics()
    metrics.record_manifest_validated(
        (ManifestViolation(ViolationCode.MANIFEST_PROVENANCE_INVALID, "build"),)
    )
    assert metrics.manifests_rejected == 0
    assert metrics.manifests_validated == 1


def test_manifest_violation_renders_as_a_dict() -> None:
    violation = ManifestViolation(ViolationCode.MANIFEST_URL_NOT_PINNED, "platforms/x/url", "why")
    assert violation.as_dict() == {
        "code": "release.manifest.url_not_pinned",
        "pointer": "platforms/x/url",
        "message": "why",
        "advisory": False,
    }


def test_manifest_violation_defaults_are_empty_strings() -> None:
    violation = ManifestViolation(ViolationCode.MANIFEST_NOT_OBJECT)
    assert violation.pointer == ""
    assert violation.message == ""


# ---------------------------------------------------------------------------
# Manifest validation — the happy path and the spec's forward-compat rule
# ---------------------------------------------------------------------------


def test_valid_manifest_has_no_violations() -> None:
    assert validate_manifest(_valid_manifest()) == ()


def test_valid_manifest_is_acceptable() -> None:
    assert manifest_is_acceptable(validate_manifest(_valid_manifest()))


def test_expected_channel_matching_is_accepted() -> None:
    assert validate_manifest(_valid_manifest(), expected_channel="stable") == ()


def test_unknown_top_level_keys_are_ignored_for_forward_compatibility() -> None:
    """Spec §4: unknown top-level keys are ignored; ``schema_version`` gates."""
    manifest = _valid_manifest(future_field={"anything": 1}, another="x")
    assert validate_manifest(manifest) == ()


def test_optional_fields_may_be_absent() -> None:
    manifest = _valid_manifest()
    del manifest["rollout_percent"]
    del manifest["minimum_version"]
    del manifest["build"]
    assert validate_manifest(manifest) == ()


def test_all_supported_targets_validate() -> None:
    platforms = {
        target: {"signature": "s", "url": f"{ALLOWED_URL_PREFIX}o/r/releases/download/v1/a"}
        for target in SUPPORTED_TARGETS
    }
    assert validate_manifest(_valid_manifest(platforms=platforms)) == ()


@pytest.mark.parametrize("channel", SUPPORTED_CHANNELS)
def test_both_channels_validate(channel: str) -> None:
    version = "1.35.0-beta.1" if channel == "beta" else "1.35.0"
    manifest = _valid_manifest(channel=channel, version=version)
    assert validate_manifest(manifest, expected_channel=channel) == ()


# ---------------------------------------------------------------------------
# Manifest validation — one test per typed violation code
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("payload", ["a string", 7, None, ["a", "list"]])
def test_code_manifest_not_object(payload: object) -> None:
    violations = validate_manifest(payload)
    assert _codes(violations) == {ViolationCode.MANIFEST_NOT_OBJECT.value}


@pytest.mark.parametrize(
    "field",
    ["schema_version", "channel", "version", "pub_date", "notes", "hardware_revalidation"],
)
def test_code_manifest_missing_field(field: str) -> None:
    manifest = _valid_manifest()
    del manifest[field]
    violations = validate_manifest(manifest)
    assert ViolationCode.MANIFEST_MISSING_FIELD.value in _codes(violations)
    assert any(v.pointer == field for v in violations)


def test_code_manifest_missing_platforms() -> None:
    manifest = _valid_manifest()
    del manifest["platforms"]
    violations = validate_manifest(manifest)
    assert ViolationCode.MANIFEST_MISSING_FIELD.value in _codes(violations)
    assert ViolationCode.MANIFEST_PLATFORMS_INVALID.value in _codes(violations)


@pytest.mark.parametrize("value", [0, 2, "1", None, True])
def test_code_schema_version_invalid(value: object) -> None:
    violations = validate_manifest(_valid_manifest(schema_version=value))
    assert ViolationCode.MANIFEST_SCHEMA_VERSION_INVALID.value in _codes(violations)


@pytest.mark.parametrize("value", ["nightly", "", 1, None])
def test_code_channel_invalid(value: object) -> None:
    violations = validate_manifest(_valid_manifest(channel=value))
    assert ViolationCode.MANIFEST_CHANNEL_INVALID.value in _codes(violations)


def test_code_channel_mismatch() -> None:
    manifest = _valid_manifest(channel="beta", version="1.35.0-beta.1")
    violations = validate_manifest(manifest, expected_channel="stable")
    assert ViolationCode.MANIFEST_CHANNEL_MISMATCH.value in _codes(violations)


def test_invalid_channel_does_not_also_report_a_mismatch() -> None:
    violations = validate_manifest(_valid_manifest(channel="nightly"), expected_channel="stable")
    assert ViolationCode.MANIFEST_CHANNEL_MISMATCH.value not in _codes(violations)


@pytest.mark.parametrize("value", ["v1.0.0", "1.0", "", 3, None])
def test_code_version_invalid(value: object) -> None:
    violations = validate_manifest(_valid_manifest(version=value))
    assert ViolationCode.MANIFEST_VERSION_INVALID.value in _codes(violations)


def test_code_prerelease_on_stable() -> None:
    """Spec §2.5 — pre-release tags flow to the beta channel only."""
    violations = validate_manifest(_valid_manifest(channel="stable", version="1.35.0-beta.1"))
    assert ViolationCode.MANIFEST_PRERELEASE_ON_STABLE.value in _codes(violations)


def test_prerelease_on_beta_is_fine() -> None:
    manifest = _valid_manifest(channel="beta", version="1.35.0-beta.1")
    assert ViolationCode.MANIFEST_PRERELEASE_ON_STABLE.value not in _codes(
        validate_manifest(manifest)
    )


@pytest.mark.parametrize("value", [None, 5, ["notes"], {"a": 1}])
def test_code_notes_invalid(value: object) -> None:
    violations = validate_manifest(_valid_manifest(notes=value))
    assert ViolationCode.MANIFEST_NOTES_INVALID.value in _codes(violations)


@pytest.mark.parametrize(
    "value",
    ["2026-09-14", "2026-09-14T00:00:00", "2026-09-14T00:00:00+01:00", "", None, 0],
)
def test_code_pub_date_invalid(value: object) -> None:
    violations = validate_manifest(_valid_manifest(pub_date=value))
    assert ViolationCode.MANIFEST_PUB_DATE_INVALID.value in _codes(violations)


def test_pub_date_accepts_fractional_seconds() -> None:
    manifest = _valid_manifest(pub_date="2026-09-14T00:00:00.123456Z")
    assert ViolationCode.MANIFEST_PUB_DATE_INVALID.value not in _codes(validate_manifest(manifest))


@pytest.mark.parametrize("value", ["false", 0, 1, None])
def test_code_hardware_flag_invalid(value: object) -> None:
    violations = validate_manifest(_valid_manifest(hardware_revalidation=value))
    assert ViolationCode.MANIFEST_HARDWARE_FLAG_INVALID.value in _codes(violations)


@pytest.mark.parametrize("value", [-1, 101, "50", 1.5, None, True, False])
def test_code_rollout_invalid(value: object) -> None:
    violations = validate_manifest(_valid_manifest(rollout_percent=value))
    assert ViolationCode.MANIFEST_ROLLOUT_INVALID.value in _codes(violations)


@pytest.mark.parametrize("value", [0, 1, 50, 99, 100])
def test_rollout_boundaries_are_accepted(value: int) -> None:
    assert validate_manifest(_valid_manifest(rollout_percent=value)) == ()


@pytest.mark.parametrize("value", ["1.0", "v1.0.0", 1, ["1.0.0"]])
def test_code_minimum_version_invalid(value: object) -> None:
    violations = validate_manifest(_valid_manifest(minimum_version=value))
    assert ViolationCode.MANIFEST_MINIMUM_VERSION_INVALID.value in _codes(violations)


def test_minimum_version_is_advisory_only_and_may_exceed_the_release() -> None:
    """Spec §4: ``minimum_version`` is advisory-banner-only in v1 — never blocking."""
    manifest = _valid_manifest(version="1.35.1", minimum_version="9.9.9")
    assert validate_manifest(manifest) == ()


def test_minimum_version_null_means_no_floor() -> None:
    assert validate_manifest(_valid_manifest(minimum_version=None)) == ()


@pytest.mark.parametrize("value", ["", 7, ["x"], None])
def test_code_platforms_invalid(value: object) -> None:
    violations = validate_manifest(_valid_manifest(platforms=value))
    assert ViolationCode.MANIFEST_PLATFORMS_INVALID.value in _codes(violations)


def test_code_platforms_empty() -> None:
    violations = validate_manifest(_valid_manifest(platforms={}))
    assert ViolationCode.MANIFEST_PLATFORMS_EMPTY.value in _codes(violations)


def test_code_target_unknown() -> None:
    platforms = {
        "solaris-sparc": {
            "signature": "s",
            "url": f"{ALLOWED_URL_PREFIX}o/r/releases/download/v1.35.1/a.tar.gz",
        }
    }
    violations = validate_manifest(_valid_manifest(platforms=platforms))
    assert _codes(violations) == {ViolationCode.MANIFEST_TARGET_UNKNOWN.value}


@pytest.mark.parametrize("entry", ["a string", 7, None, ["x"]])
def test_code_target_entry_invalid(entry: object) -> None:
    violations = validate_manifest(_valid_manifest(platforms={"linux-x86_64": entry}))
    assert ViolationCode.MANIFEST_TARGET_ENTRY_INVALID.value in _codes(violations)


@pytest.mark.parametrize("signature", ["", None, 7])
def test_code_signature_missing(signature: object) -> None:
    platforms = {
        "linux-x86_64": {
            "signature": signature,
            "url": f"{ALLOWED_URL_PREFIX}o/r/releases/download/v1.35.1/a.tar.gz",
        }
    }
    violations = validate_manifest(_valid_manifest(platforms=platforms))
    assert ViolationCode.MANIFEST_SIGNATURE_MISSING.value in _codes(violations)


def test_code_signature_missing_when_key_absent() -> None:
    platforms = {
        "linux-x86_64": {"url": f"{ALLOWED_URL_PREFIX}o/r/releases/download/v1.35.1/a.tar.gz"}
    }
    violations = validate_manifest(_valid_manifest(platforms=platforms))
    assert _codes(violations) == {ViolationCode.MANIFEST_SIGNATURE_MISSING.value}


@pytest.mark.parametrize("url", ["", None, 7])
def test_code_url_missing(url: object) -> None:
    violations = validate_manifest(
        _valid_manifest(platforms={"linux-x86_64": {"signature": "s", "url": url}})
    )
    assert ViolationCode.MANIFEST_URL_MISSING.value in _codes(violations)


def test_code_url_missing_when_key_absent() -> None:
    violations = validate_manifest(_valid_manifest(platforms={"linux-x86_64": {"signature": "s"}}))
    assert _codes(violations) == {ViolationCode.MANIFEST_URL_MISSING.value}


@pytest.mark.parametrize(
    "url",
    [
        "http://github.com/o/r/releases/download/v1/a",  # plain http
        "https://evil.example.com/a.tar.gz",
        "https://raw.githubusercontent.com/o/r/a",
        "https://github.example.com/o/r/a",
    ],
)
def test_code_url_not_pinned(url: str) -> None:
    """Spec §4 — any host but the pinned GitHub releases host is refused."""
    violations = validate_manifest(
        _valid_manifest(platforms={"linux-x86_64": {"signature": "s", "url": url}})
    )
    assert _codes(violations) == {ViolationCode.MANIFEST_URL_NOT_PINNED.value}


def test_target_entry_extra_keys_are_tolerated() -> None:
    platforms = {
        "linux-x86_64": {
            "signature": "s",
            "url": f"{ALLOWED_URL_PREFIX}o/r/releases/download/v1.35.1/a.tar.gz",
            "future_field": 1,
        }
    }
    assert validate_manifest(_valid_manifest(platforms=platforms)) == ()


# ---------------------------------------------------------------------------
# Build provenance — reported, never blocking (spec §4)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("value", ["a string", 7, ["x"]])
def test_code_provenance_invalid_is_advisory(value: object) -> None:
    violations = validate_manifest(_valid_manifest(build=value))
    assert _codes(violations) == {ViolationCode.MANIFEST_PROVENANCE_INVALID.value}
    assert manifest_is_acceptable(violations), "provenance must never block an update"


@pytest.mark.parametrize(
    "field", sorted({"source_sha", "workflow_run_url", "builder_workflow_sha"})
)
def test_code_provenance_missing_field(field: str) -> None:
    build = _valid_manifest()["build"]
    del build[field]
    violations = validate_manifest(_valid_manifest(build=build))
    assert _codes(violations) == {ViolationCode.MANIFEST_PROVENANCE_MISSING_FIELD.value}
    assert manifest_is_acceptable(violations)


@pytest.mark.parametrize("field", ["source_sha", "builder_workflow_sha"])
@pytest.mark.parametrize("value", ["short", "A" * 40, "g" * 40, 7, None])
def test_code_provenance_sha_invalid(field: str, value: object) -> None:
    build = dict(_valid_manifest()["build"])
    build[field] = value
    violations = validate_manifest(_valid_manifest(build=build))
    assert _codes(violations) == {ViolationCode.MANIFEST_PROVENANCE_FIELD_INVALID.value}
    assert manifest_is_acceptable(violations)


@pytest.mark.parametrize("value", ["https://evil.example.com/runs/1", "", None, 7])
def test_code_provenance_run_url_invalid(value: object) -> None:
    build = dict(_valid_manifest()["build"])
    build["workflow_run_url"] = value
    violations = validate_manifest(_valid_manifest(build=build))
    assert _codes(violations) == {ViolationCode.MANIFEST_PROVENANCE_FIELD_INVALID.value}
    assert manifest_is_acceptable(violations)


def test_provenance_extra_keys_are_tolerated() -> None:
    build = dict(_valid_manifest()["build"])
    build["future_field"] = "x"
    assert validate_manifest(_valid_manifest(build=build)) == ()


def test_every_advisory_code_is_a_provenance_code() -> None:
    assert all("provenance" in code.value for code in ADVISORY_VIOLATION_CODES)


def test_manifest_is_acceptable_rejects_a_blocking_violation() -> None:
    blocking = (ManifestViolation(ViolationCode.MANIFEST_URL_NOT_PINNED, "p"),)
    advisory = (ManifestViolation(ViolationCode.MANIFEST_PROVENANCE_INVALID, "build"),)
    assert not manifest_is_acceptable(blocking)
    assert not manifest_is_acceptable(blocking + advisory)
    assert manifest_is_acceptable(advisory)
    assert manifest_is_acceptable(())


# ---------------------------------------------------------------------------
# Validation reports every problem in one pass
# ---------------------------------------------------------------------------


def test_validation_does_not_short_circuit() -> None:
    manifest = _valid_manifest(
        channel="nightly",
        version="v1",
        notes=None,
        pub_date="yesterday",
        hardware_revalidation="no",
        rollout_percent=101,
        platforms={},
    )
    codes = _codes(validate_manifest(manifest))
    assert codes >= {
        ViolationCode.MANIFEST_CHANNEL_INVALID.value,
        ViolationCode.MANIFEST_VERSION_INVALID.value,
        ViolationCode.MANIFEST_NOTES_INVALID.value,
        ViolationCode.MANIFEST_PUB_DATE_INVALID.value,
        ViolationCode.MANIFEST_HARDWARE_FLAG_INVALID.value,
        ViolationCode.MANIFEST_ROLLOUT_INVALID.value,
        ViolationCode.MANIFEST_PLATFORMS_EMPTY.value,
    }


def test_validation_logs_a_structured_verdict(caplog: pytest.LogCaptureFixture) -> None:
    with caplog.at_level(logging.INFO, logger="rytm.release"):
        validate_manifest(_valid_manifest())
    payload = json.loads(caplog.records[-1].getMessage())
    assert payload["event"] == "release.manifest.validated"
    assert payload["ok"] is True
    assert payload["violations"] == 0


def test_validation_logs_the_failing_codes(caplog: pytest.LogCaptureFixture) -> None:
    with caplog.at_level(logging.INFO, logger="rytm.release"):
        validate_manifest(_valid_manifest(notes=None))
    payload = json.loads(caplog.records[-1].getMessage())
    assert payload["ok"] is False
    assert payload["codes"] == [ViolationCode.MANIFEST_NOTES_INVALID.value]


def test_no_emitted_message_contains_an_absolute_path() -> None:
    """Gate 7 — emitted details are bounded and path-free."""
    manifest = _valid_manifest(
        version="/Users/someone/secret/1.0",
        notes=None,
        platforms={"linux-x86_64": {"signature": "s", "url": "file:///Users/someone/a.tar.gz"}},
    )
    for violation in validate_manifest(manifest):
        assert "/Users/" not in violation.message
        assert not violation.message.startswith("/")


# ---------------------------------------------------------------------------
# generate_manifest — the R1 generate-then-validate round trip
# ---------------------------------------------------------------------------


def _generate(**overrides: Any) -> dict[str, Any]:
    # Derive the artifact URL from the version under test so the generated
    # manifest is self-consistent; a URL naming a different release than the
    # manifest declares is refused (it would ship the wrong binary).
    version = str(overrides.get("version", "1.35.1"))
    kwargs: dict[str, Any] = {
        "channel": "stable",
        "version": "1.35.1",
        "pub_date": "2026-09-14T00:00:00Z",
        "notes": "notes",
        "platforms": {
            "linux-x86_64": {
                "signature": "s",
                "url": f"{ALLOWED_URL_PREFIX}o/r/releases/download/v{version}/a.tar.gz",
            }
        },
        "source_sha": _SHA,
        "workflow_run_url": _RUN_URL,
        "builder_workflow_sha": _OTHER_SHA,
    }
    kwargs.update(overrides)
    return generate_manifest(**kwargs)


def test_generate_manifest_produces_a_valid_spec_shaped_manifest() -> None:
    manifest = _generate()
    assert validate_manifest(manifest) == ()
    assert manifest["schema_version"] == MANIFEST_SCHEMA_VERSION
    assert manifest["build"] == {
        "source_sha": _SHA,
        "workflow_run_url": _RUN_URL,
        "builder_workflow_sha": _OTHER_SHA,
    }
    assert set(manifest) == {
        "schema_version",
        "channel",
        "version",
        "pub_date",
        "notes",
        "hardware_revalidation",
        "rollout_percent",
        "minimum_version",
        "build",
        "platforms",
    }


def test_generate_manifest_defaults_match_the_spec() -> None:
    manifest = _generate()
    assert manifest["hardware_revalidation"] is False
    assert manifest["rollout_percent"] == 100
    assert manifest["minimum_version"] is None


def test_generate_manifest_honours_explicit_gating_fields() -> None:
    manifest = _generate(hardware_revalidation=True, rollout_percent=10, minimum_version="1.0.0")
    assert manifest["hardware_revalidation"] is True
    assert manifest["rollout_percent"] == 10
    assert manifest["minimum_version"] == "1.0.0"


def test_generate_manifest_output_is_json_serializable() -> None:
    assert json.loads(json.dumps(_generate())) == _generate()


def test_generate_manifest_sorts_platform_keys_for_stable_diffs() -> None:
    platforms = {
        "windows-x86_64": {
            "signature": "s",
            "url": f"{ALLOWED_URL_PREFIX}o/r/releases/download/v1.35.1/w.tar.gz",
        },
        "darwin-aarch64": {
            "signature": "s",
            "url": f"{ALLOWED_URL_PREFIX}o/r/releases/download/v1.35.1/d.tar.gz",
        },
    }
    manifest = _generate(platforms=platforms)
    assert list(manifest["platforms"]) == ["darwin-aarch64", "windows-x86_64"]


def test_generate_manifest_copies_the_platform_entries() -> None:
    entry = {"signature": "s", "url": f"{ALLOWED_URL_PREFIX}o/r/releases/download/v1.35.1/a.tar.gz"}
    manifest = _generate(platforms={"linux-x86_64": entry})
    entry["signature"] = "mutated"
    assert manifest["platforms"]["linux-x86_64"]["signature"] == "s"


@pytest.mark.parametrize(
    ("overrides", "expected_code"),
    [
        ({"version": "not-a-version"}, ViolationCode.MANIFEST_VERSION_INVALID),
        ({"channel": "nightly"}, ViolationCode.MANIFEST_CHANNEL_INVALID),
        ({"pub_date": "yesterday"}, ViolationCode.MANIFEST_PUB_DATE_INVALID),
        ({"rollout_percent": 200}, ViolationCode.MANIFEST_ROLLOUT_INVALID),
        ({"platforms": {}}, ViolationCode.MANIFEST_PLATFORMS_EMPTY),
        (
            {"version": "1.35.0-beta.1", "channel": "stable"},
            ViolationCode.MANIFEST_PRERELEASE_ON_STABLE,
        ),
        (
            {"platforms": {"linux-x86_64": {"signature": "s", "url": "https://evil.example/a"}}},
            ViolationCode.MANIFEST_URL_NOT_PINNED,
        ),
    ],
)
def test_generate_manifest_refuses_invalid_input(
    overrides: dict[str, Any], expected_code: ViolationCode
) -> None:
    """The R1 round trip: the generator runs its own validator before returning."""
    with pytest.raises(ReleaseError) as excinfo:
        _generate(**overrides)
    assert excinfo.value.code is ViolationCode.GENERATE_PRODUCED_INVALID
    assert expected_code.value in excinfo.value.detail


def test_generate_manifest_refusal_detail_is_codes_only() -> None:
    with pytest.raises(ReleaseError) as excinfo:
        _generate(version="/Users/someone/secret")
    assert "/Users/" not in excinfo.value.detail
    assert excinfo.value.detail == ViolationCode.MANIFEST_VERSION_INVALID.value


def test_generate_manifest_refusal_is_logged(caplog: pytest.LogCaptureFixture) -> None:
    with caplog.at_level(logging.INFO, logger="rytm.release"):
        with pytest.raises(ReleaseError):
            _generate(version="nope")
    events = [json.loads(r.getMessage())["event"] for r in caplog.records]
    assert "release.manifest.generate_refused" in events


def test_generate_manifest_tolerates_advisory_provenance_defects(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """A malformed sha is reported, but must not stop the release train."""
    with caplog.at_level(logging.INFO, logger="rytm.release"):
        manifest = _generate(source_sha="not-a-sha")
    assert manifest["build"]["source_sha"] == "not-a-sha"
    events = [json.loads(r.getMessage())["event"] for r in caplog.records]
    assert "release.manifest.generate_advisory" in events
    assert "release.manifest.generated" in events


def test_generate_manifest_logs_success(caplog: pytest.LogCaptureFixture) -> None:
    with caplog.at_level(logging.INFO, logger="rytm.release"):
        _generate()
    payload = json.loads(caplog.records[-1].getMessage())
    assert payload["event"] == "release.manifest.generated"
    assert payload["version"] == "1.35.1"


def test_generate_manifest_round_trips_a_beta_prerelease() -> None:
    manifest = _generate(channel="beta", version="1.35.0-beta.1")
    assert validate_manifest(manifest, expected_channel="beta") == ()


def test_generated_manifest_channel_matches_the_expected_channel() -> None:
    """generate() validates against its own channel, so cross-wiring cannot slip."""
    manifest = _generate(channel="beta", version="1.35.0-beta.1")
    assert ViolationCode.MANIFEST_CHANNEL_MISMATCH.value in _codes(
        validate_manifest(manifest, expected_channel="stable")
    )
