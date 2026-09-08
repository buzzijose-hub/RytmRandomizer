"""Tests for ``scripts/validate_manifest.py`` — the manifest-validation CLI.

The CLI is deliberately thin (reuse contract R1/R5): every schema rule lives
in ``scripts/release_lib.py``, and this module owns only argument parsing,
file reading, exit codes, and step-summary rendering. These tests therefore
exercise exactly that surface, and **stub the validator** rather than
importing the real one.

Stubbing is not a shortcut here, it is the contract:

* ``release_lib.py`` is produced by a sibling agent (A1) and is not required
  for this CLI's own behaviour to be correct or testable. Testing against a
  stub is what proves the CLI carries no rules of its own — if a rule ever
  leaked in, one of these tests would start passing or failing for a reason
  the stub cannot explain.
* The rules themselves are covered by ``release_lib``'s own tests against the
  ``tests/fixtures/update_manifest/`` corpus.

What IS asserted against the real fixture corpus here is the *shape* of the
contract A5 owns: the canonical manifest parses, every invalid fixture is
named for a reason code, and the bucket vectors are arithmetically true.
"""

from __future__ import annotations

import base64
import hashlib
import importlib.util
import json
import re
import struct
import sys
from collections.abc import Iterator
from pathlib import Path
from types import ModuleType
from typing import Final

import pytest

# WS-M4: fast-suite member — no MIDI, no parity fixtures, pure file I/O.
pytestmark = pytest.mark.fast

PROJECT_ROOT: Final[Path] = Path(__file__).resolve().parents[1]
SCRIPTS_DIR: Final[Path] = PROJECT_ROOT / "scripts"
CLI_PATH: Final[Path] = SCRIPTS_DIR / "validate_manifest.py"
FIXTURE_DIR: Final[Path] = PROJECT_ROOT / "tests" / "fixtures" / "update_manifest"
CANONICAL_MANIFEST: Final[Path] = FIXTURE_DIR / "manifest.v1.json"
INVALID_DIR: Final[Path] = FIXTURE_DIR / "invalid"
BUCKET_VECTORS: Final[Path] = FIXTURE_DIR / "bucket_vectors.json"

#: The four normative platform targets (fixtures README § "Platform target
#: strings"). They are also the `<target>` component of the I6 ping asset
#: name, which is why they are asserted rather than merely documented.
PLATFORM_TARGETS: Final[frozenset[str]] = frozenset(
    {"darwin-aarch64", "darwin-x86_64", "windows-x86_64", "linux-x86_64"}
)


def _load_cli() -> ModuleType:
    """Import ``scripts/validate_manifest.py`` as a module.

    ``scripts/`` is not a package, so the module is loaded by path. A fresh
    module object per call keeps tests that monkeypatch its internals from
    leaking into each other.
    """

    spec = importlib.util.spec_from_file_location("_validate_manifest_under_test", CLI_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture()
def cli() -> ModuleType:
    """A freshly imported copy of the CLI module."""

    return _load_cli()


class _StubViolation:
    """Minimal stand-in for ``release_lib``'s violation dataclass."""

    def __init__(self, code: str, message: str) -> None:
        self.code = code
        self.message = message


@pytest.fixture()
def stub_release_lib(
    cli: ModuleType, monkeypatch: pytest.MonkeyPatch
) -> Iterator[list[list[_StubViolation]]]:
    """Replace the validator loader with a scripted stub.

    Yields a mutable queue of per-call results: the first validated document
    gets ``queue[0]``, the second ``queue[1]``, and so on. An empty list means
    "this manifest is clean". Leaving the queue empty means every document
    validates clean.
    """

    queue: list[list[_StubViolation]] = []
    call_index = {"n": 0}

    def fake_validator(document: object) -> list[_StubViolation]:
        index = call_index["n"]
        call_index["n"] += 1
        if index < len(queue):
            return queue[index]
        return []

    monkeypatch.setattr(cli, "_load_validator", lambda: fake_validator)
    yield queue


def _write(path: Path, document: object) -> Path:
    """Write ``document`` as JSON to ``path`` and return the path."""

    path.write_text(json.dumps(document), encoding="utf-8")
    return path


# ---------------------------------------------------------------------------
# Exit codes and the clean path.
# ---------------------------------------------------------------------------


def test_clean_manifest_exits_zero(
    cli: ModuleType,
    stub_release_lib: list[list[_StubViolation]],
    capsys: pytest.CaptureFixture[str],
) -> None:
    """A manifest with no violations exits 0 and reports PASS."""

    exit_code = cli.main([str(CANONICAL_MANIFEST)])

    assert exit_code == cli.EXIT_OK
    out = capsys.readouterr().out
    assert "**PASS**" in out
    assert "**FAIL**" not in out


def test_refused_manifest_exits_one_and_names_the_rule(
    cli: ModuleType,
    stub_release_lib: list[list[_StubViolation]],
    capsys: pytest.CaptureFixture[str],
) -> None:
    """A refused manifest exits 1 and prints the typed code, not a traceback."""

    stub_release_lib.append([_StubViolation("unknown_channel", "channel must be stable or beta")])

    exit_code = cli.main([str(CANONICAL_MANIFEST)])

    assert exit_code == cli.EXIT_REFUSED
    out = capsys.readouterr().out
    assert "**FAIL**" in out
    assert "`unknown_channel`" in out
    assert "channel must be stable or beta" in out


def test_multiple_manifests_are_all_reported_and_one_failure_refuses(
    cli: ModuleType,
    stub_release_lib: list[list[_StubViolation]],
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Every named manifest is validated; a single failure fails the run.

    ``manifest-validate.yml`` passes both channel files in one invocation, so
    a run that stopped at the first failure would hide a second broken
    channel until the operator fixed the first one.
    """

    second = _write(tmp_path / "beta.json", json.loads(CANONICAL_MANIFEST.read_text()))
    stub_release_lib.extend([[], [_StubViolation("version_not_semver", "version is not SemVer")]])

    exit_code = cli.main([str(CANONICAL_MANIFEST), str(second)])

    assert exit_code == cli.EXIT_REFUSED
    out = capsys.readouterr().out
    assert "**PASS**" in out
    assert "`version_not_semver`" in out


# ---------------------------------------------------------------------------
# Read / parse refusals — typed, never a raw exception string.
# ---------------------------------------------------------------------------


def test_missing_file_is_a_typed_refusal_not_a_crash(
    cli: ModuleType,
    stub_release_lib: list[list[_StubViolation]],
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """An unreadable path yields ``manifest_unreadable``, not an OSError."""

    exit_code = cli.main([str(tmp_path / "absent.json")])

    assert exit_code == cli.EXIT_REFUSED
    assert f"`{cli.CODE_UNREADABLE}`" in capsys.readouterr().out


def test_malformed_json_is_a_typed_refusal_locating_the_error(
    cli: ModuleType,
    stub_release_lib: list[list[_StubViolation]],
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Invalid JSON yields ``manifest_not_json`` with a line/column, no path."""

    broken = tmp_path / "broken.json"
    broken.write_text('{"schema_version": 1,,}', encoding="utf-8")

    exit_code = cli.main([str(broken)])

    assert exit_code == cli.EXIT_REFUSED
    out = capsys.readouterr().out
    assert f"`{cli.CODE_NOT_JSON}`" in out
    assert "line" in out and "column" in out


def test_non_object_root_is_a_typed_refusal(
    cli: ModuleType,
    stub_release_lib: list[list[_StubViolation]],
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """A JSON array (or scalar) at the root yields ``manifest_not_object``."""

    exit_code = cli.main([str(_write(tmp_path / "array.json", [1, 2, 3]))])

    assert exit_code == cli.EXIT_REFUSED
    assert f"`{cli.CODE_NOT_OBJECT}`" in capsys.readouterr().out


def test_absent_release_lib_is_an_invocation_error(
    cli: ModuleType,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Without the R1 toolkit the CLI exits 2 and says why.

    Exit 2 is distinct from exit 1 on purpose: "I could not run the rules"
    must never be reported to a workflow as "the manifest is fine".
    """

    def raise_import_error() -> object:
        raise ImportError("release_lib is absent")

    monkeypatch.setattr(cli, "_load_validator", raise_import_error)

    exit_code = cli.main([str(CANONICAL_MANIFEST)])

    assert exit_code == cli.EXIT_INVOCATION_ERROR
    assert "release_lib" in capsys.readouterr().err


def test_load_validator_reports_a_missing_release_lib(
    cli: ModuleType, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """``_load_validator`` raises ImportError when the sibling file is gone.

    Not FileNotFoundError: ``spec_from_file_location`` builds a spec for a
    path that does not exist and only fails inside ``exec_module``, so
    without the explicit existence check the caller would see an OSError
    from the import machinery instead of a named refusal.
    """

    monkeypatch.setattr(cli, "__file__", str(tmp_path / "validate_manifest.py"))

    with pytest.raises(ImportError, match="not present"):
        cli._load_validator()


def test_load_validator_reports_an_unloadable_spec(
    cli: ModuleType, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """A ``None`` spec (or loader) from importlib is an ImportError, not a crash.

    importlib types both as Optional. A stock loader never returns None for
    a real ``.py`` file, but letting a None through would surface as an
    AttributeError several frames from the cause.
    """

    (tmp_path / "release_lib.py").write_text("validate_manifest = None\n", encoding="utf-8")
    monkeypatch.setattr(cli, "__file__", str(tmp_path / "validate_manifest.py"))
    monkeypatch.setattr(cli.importlib.util, "spec_from_file_location", lambda *a, **k: None)

    with pytest.raises(ImportError, match="cannot load"):
        cli._load_validator()


def test_load_validator_reports_a_release_lib_without_the_symbol(
    cli: ModuleType, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """A release_lib missing ``validate_manifest`` is an ImportError, not None.

    Returning ``None`` here would surface as a ``TypeError: NoneType is not
    callable`` deep inside the run, which tells the operator nothing.
    """

    (tmp_path / "release_lib.py").write_text("VERSION = '1'\n", encoding="utf-8")
    monkeypatch.setattr(cli, "__file__", str(tmp_path / "validate_manifest.py"))

    with pytest.raises(ImportError, match="validate_manifest"):
        cli._load_validator()


def test_load_validator_returns_the_real_symbol_when_present(
    cli: ModuleType, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """The happy path loads by file path, with no ``sys.path`` mutation."""

    (tmp_path / "release_lib.py").write_text(
        "def validate_manifest(document):\n    return []\n", encoding="utf-8"
    )
    monkeypatch.setattr(cli, "__file__", str(tmp_path / "validate_manifest.py"))
    before = list(sys.path)

    validator = cli._load_validator()

    assert validator({}) == []
    assert sys.path == before


# ---------------------------------------------------------------------------
# Gate 7 hygiene: bounded, path-free output.
# ---------------------------------------------------------------------------


def test_emitted_output_contains_no_absolute_path(
    cli: ModuleType,
    stub_release_lib: list[list[_StubViolation]],
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """A manifest outside the repo is labelled by basename only.

    The report lands in a public CI step summary; the runner's directory
    layout is not the operator's business and differs per machine, which
    would make the same failure render differently every run.
    """

    outside = _write(tmp_path / "stable.json", json.loads(CANONICAL_MANIFEST.read_text()))

    cli.main([str(outside)])

    out = capsys.readouterr().out
    assert "stable.json" in out
    assert str(tmp_path) not in out


def test_repo_relative_paths_are_rendered_relative(cli: ModuleType) -> None:
    """A path inside the repo renders as a posix repo-relative label."""

    assert cli._display_path(CANONICAL_MANIFEST) == (
        "tests/fixtures/update_manifest/manifest.v1.json"
    )


def test_long_messages_are_truncated_with_an_elision_marker(cli: ModuleType) -> None:
    """An over-long violation message is capped, not echoed whole.

    Manifest content (URLs, base64 signatures) is partly attacker-shaped; an
    unbounded echo into a public step summary is a log-injection surface.
    """

    long_message = "x" * (cli.MAX_MESSAGE_CHARS + 50)

    bounded = cli._bound(long_message)

    assert len(bounded) == cli.MAX_MESSAGE_CHARS
    assert bounded.endswith("…")


def test_short_messages_are_passed_through_unchanged(cli: ModuleType) -> None:
    """A message at or under the cap is not modified."""

    assert cli._bound("short") == "short"


# ---------------------------------------------------------------------------
# Step summary.
# ---------------------------------------------------------------------------


def test_summary_flag_appends_to_the_github_step_summary(
    cli: ModuleType,
    stub_release_lib: list[list[_StubViolation]],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """``--summary`` writes the report where the Actions run page shows it."""

    summary = tmp_path / "summary.md"
    summary.write_text("pre-existing\n", encoding="utf-8")
    monkeypatch.setenv(cli.SUMMARY_ENV_VAR, str(summary))
    stub_release_lib.append([_StubViolation("platforms_empty", "platforms map is empty")])

    cli.main([str(CANONICAL_MANIFEST), "--summary"])

    written = summary.read_text(encoding="utf-8")
    assert written.startswith("pre-existing\n")
    assert "`platforms_empty`" in written


def test_summary_flag_is_a_noop_outside_actions(
    cli: ModuleType,
    stub_release_lib: list[list[_StubViolation]],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Without ``GITHUB_STEP_SUMMARY`` the flag writes nothing and does not fail."""

    monkeypatch.delenv(cli.SUMMARY_ENV_VAR, raising=False)

    assert cli.main([str(CANONICAL_MANIFEST), "--summary"]) == cli.EXIT_OK


def test_without_the_summary_flag_nothing_is_written(
    cli: ModuleType,
    stub_release_lib: list[list[_StubViolation]],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The summary file is untouched unless ``--summary`` is passed."""

    summary = tmp_path / "summary.md"
    summary.write_text("", encoding="utf-8")
    monkeypatch.setenv(cli.SUMMARY_ENV_VAR, str(summary))

    cli.main([str(CANONICAL_MANIFEST)])

    assert summary.read_text(encoding="utf-8") == ""


def test_argv_defaults_to_sys_argv(
    cli: ModuleType,
    stub_release_lib: list[list[_StubViolation]],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Calling ``main()`` with no argument reads ``sys.argv`` (the __main__ path)."""

    monkeypatch.setattr(sys, "argv", ["validate_manifest.py", str(CANONICAL_MANIFEST)])

    assert cli.main() == cli.EXIT_OK


def test_no_manifest_argument_is_a_usage_error(cli: ModuleType) -> None:
    """argparse enforces at least one path; the CLI never validates nothing."""

    with pytest.raises(SystemExit):
        cli.main([])


# ---------------------------------------------------------------------------
# Contract I3 — the fixture corpus itself (abstraction R2).
# ---------------------------------------------------------------------------


def test_canonical_manifest_matches_the_spec_field_set() -> None:
    """``manifest.v1.json`` carries exactly the spec §4 document fields.

    The spec's §4 example is the contract three languages read. A field
    quietly added or dropped here silently changes what the Rust serde
    round-trip and the e2e mock server agree on.
    """

    document = json.loads(CANONICAL_MANIFEST.read_text(encoding="utf-8"))

    assert set(document) == {
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
    assert document["schema_version"] == 1
    assert document["channel"] in {"stable", "beta"}
    # Spec §4 shows `minimum_version: null` — the advisory-only field in its
    # unset state, which is what a normal release emits.
    assert document["minimum_version"] is None
    assert set(document["build"]) == {
        "source_sha",
        "workflow_run_url",
        "builder_workflow_sha",
    }
    assert set(document["platforms"]) == set(PLATFORM_TARGETS)


def test_canonical_manifest_platform_entries_are_well_formed() -> None:
    """Every platform entry pins a github.com release-download URL for its tag.

    Host pinning plus the tag check is the whole reason a stolen or spoofed
    manifest cannot redirect a fleet at an attacker-controlled artifact, so
    the fixture must model a URL that actually satisfies it.
    """

    document = json.loads(CANONICAL_MANIFEST.read_text(encoding="utf-8"))
    version = document["version"]

    for target, entry in document["platforms"].items():
        assert set(entry) == {"signature", "url"}, target
        assert entry["url"].startswith("https://github.com/"), target
        assert f"/releases/download/v{version}/" in entry["url"], target
        # Signatures are base64; a fixture that is not decodable would let a
        # `platform_signature_not_base64` implementation pass by accident.
        base64.b64decode(entry["signature"], validate=True)


def test_every_invalid_fixture_is_a_single_field_mutation() -> None:
    """Each ``invalid/*.json`` differs from the canonical manifest minimally.

    Isolation is what makes the filename-is-the-code contract meaningful: a
    fixture violating two rules could legitimately be refused by either, so
    two implementations could disagree about which rule fired and both be
    "right".
    """

    canonical = json.loads(CANONICAL_MANIFEST.read_text(encoding="utf-8"))
    fixtures = sorted(INVALID_DIR.glob("*.json"))
    assert fixtures, "the invalid corpus must not be empty"

    for path in fixtures:
        document = json.loads(path.read_text(encoding="utf-8"))
        assert isinstance(document, dict), path.name
        differing = {
            key
            for key in set(canonical) | set(document)
            if canonical.get(key, object()) != document.get(key, object())
        }
        assert len(differing) == 1, f"{path.name} mutates {sorted(differing)}"


def test_invalid_fixture_names_are_snake_case_reason_codes() -> None:
    """Filenames are the typed reason codes, so they must look like codes."""

    for path in sorted(INVALID_DIR.glob("*.json")):
        assert re.fullmatch(r"[a-z][a-z0-9_]*", path.stem), path.name


def test_unknown_field_fixtures_live_where_the_spec_puts_them() -> None:
    """Spec §4's forward-compatibility rule decides where these fixtures live.

    "Unknown top-level keys are ignored (forward compatibility)" means there is
    no top-level unknown-key fixture at all — a deliberate absence, asserted so
    a future contributor "completing" the corpus cannot quietly invert the rule
    ``schema_version`` exists to provide.

    An unknown key inside a *platform entry* was originally filed as invalid on
    the theory that the entry shape is a security boundary. It is not: the same
    forward-compatibility reading applies (a v2 client adding ``sha256`` must
    not be refused by a v1 validator), and the security boundary is the URL
    host+path pin, which is enforced and separately fixtured. The fixture
    therefore lives under ``advisory/`` — reported, never blocking.
    """

    assert not (INVALID_DIR / "unknown_field.json").exists()
    assert not (INVALID_DIR / "platform_entry_unknown_field.json").exists()
    assert (INVALID_DIR.parent / "advisory" / "platform_entry_unknown_field.json").exists()


def test_no_missing_rollout_percent_fixture_exists() -> None:
    """Spec §4 says an absent ``rollout_percent`` means 100, so it is valid."""

    assert not (INVALID_DIR / "missing_rollout_percent.json").exists()
    assert (INVALID_DIR / "rollout_percent_out_of_range.json").exists()


# ---------------------------------------------------------------------------
# Contract I3 — bucket vectors (consumed by B-rust; a wrong number poisons it).
# ---------------------------------------------------------------------------


def _bucket(install_id: str) -> tuple[bytes, int, int]:
    """Return ``(prefix, u32_be, bucket)`` for ``install_id`` per spec §5."""

    prefix = hashlib.sha256(install_id.encode("utf-8")).digest()[:4]
    (value,) = struct.unpack(">I", prefix)
    return prefix, value, value % 100


def test_bucket_vectors_are_arithmetically_correct() -> None:
    """Recompute every pinned vector from the stated rule.

    The Rust implementation asserts against these exact numbers. If a vector
    were wrong, a correct Rust implementation would fail its own test suite
    and the obvious "fix" would be to break the Rust. Recomputing here keeps
    the fixture honest at its source.
    """

    data = json.loads(BUCKET_VECTORS.read_text(encoding="utf-8"))
    assert data["rule"]["prefix_endianness"] == "big"
    assert data["rule"]["modulus"] == 100

    for vector in data["vectors"]:
        prefix, value, bucket = _bucket(vector["install_id"])
        assert prefix.hex() == vector["sha256_prefix_hex"], vector["install_id"]
        assert value == vector["prefix_u32_be"], vector["install_id"]
        assert bucket == vector["bucket"], vector["install_id"]


def test_bucket_vector_eligibility_tables_use_strict_less_than() -> None:
    """``eligible == bucket < rollout_percent`` at every tabulated percentage.

    The `<` versus `<=` mistake is invisible except exactly at the install's
    own bucket, which is why each vector tabulates that boundary pair.
    """

    data = json.loads(BUCKET_VECTORS.read_text(encoding="utf-8"))

    for vector in data["vectors"]:
        bucket = vector["bucket"]
        for percent_text, expected in vector["eligible_at_rollout_percent"].items():
            assert (bucket < int(percent_text)) is expected, (
                vector["install_id"],
                percent_text,
            )


def test_bucket_boundary_cases_agree_with_the_per_vector_tables() -> None:
    """The pre-computed eligible-id sets match a recomputation from scratch."""

    data = json.loads(BUCKET_VECTORS.read_text(encoding="utf-8"))
    all_ids = [vector["install_id"] for vector in data["vectors"]]

    for case in data["boundary_cases"]:
        percent = case["rollout_percent"]
        expected = [install_id for install_id in all_ids if _bucket(install_id)[2] < percent]
        assert case["eligible_install_ids"] == expected, case["name"]


def test_bucket_rollout_steps_are_strict_supersets() -> None:
    """Nobody flaps out of a rollout as the percentage rises.

    This is the property that lets an operator step 10 → 50 → 100 without
    ever revoking an update from a machine that already qualified.
    """

    data = json.loads(BUCKET_VECTORS.read_text(encoding="utf-8"))
    cases = sorted(data["boundary_cases"], key=lambda case: case["rollout_percent"])

    for narrower, wider in zip(cases, cases[1:]):
        assert set(narrower["eligible_install_ids"]) <= set(wider["eligible_install_ids"]), (
            narrower["name"],
            wider["name"],
        )


# ---------------------------------------------------------------------------
# Contract I6 — ping-asset naming.
# ---------------------------------------------------------------------------


def test_fixture_readme_documents_every_platform_target_and_the_beacon_name() -> None:
    """The README beside the fixtures is the I6 contract's written half.

    B-rust builds the ping URL from these strings and C-snap parses release
    assets with them; the two agents never see each other's code, so the
    README has to actually contain the names they agree on.
    """

    readme = (FIXTURE_DIR / "README.md").read_text(encoding="utf-8")

    assert "beacon-<version>-<target>.txt" in readme
    for target in sorted(PLATFORM_TARGETS):
        assert target in readme, target
        assert f"beacon-1.35.1-{target}.txt" in readme, target
