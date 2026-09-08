"""Tests for the fleet check-in snapshot script (contract I5).

Nothing here touches the network. Every release payload comes from
``tests/fixtures/fleet/releases_api_payload.json`` or an inline literal, and
the one test that covers the HTTP boundary monkeypatches ``urlopen`` -- so a
CI runner with no egress still gets full branch coverage of the fetch path.

Cases required by the C-snap work package, each named below:

* first-ever run (no history file) -> ``test_first_run_*``
* a delta                          -> ``test_second_run_with_changed_counts_appends``
* a no-delta run                   -> ``test_unchanged_run_writes_nothing``
* a malformed API payload          -> ``test_malformed_*``
* a missing beacon asset           -> ``test_release_without_beacon_assets_*``
* version in the API, absent from
  history                          -> ``test_new_version_appears_only_in_the_new_row``
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType
from typing import Any, Final

import pytest

pytestmark = pytest.mark.fast

_REPO_ROOT: Final[Path] = Path(__file__).resolve().parents[1]
_SCRIPT: Final[Path] = _REPO_ROOT / "scripts" / "fleet_snapshot.py"
_FIXTURE_DIR: Final[Path] = _REPO_ROOT / "tests" / "fixtures" / "fleet"
_RELEASES_FIXTURE: Final[Path] = _FIXTURE_DIR / "releases_api_payload.json"
_STABLE_FIXTURE: Final[Path] = _FIXTURE_DIR / "stable.json"
_BETA_FIXTURE: Final[Path] = _FIXTURE_DIR / "beta.json"


def _load_script_module() -> ModuleType:
    """Import ``scripts/fleet_snapshot.py`` by path.

    The module is registered in ``sys.modules`` *before* execution because
    ``@dataclass`` resolves ``cls.__module__`` through that table while the
    class body is being processed; an unregistered module makes the decorator
    raise ``AttributeError`` on ``NoneType``.
    """

    spec = importlib.util.spec_from_file_location("fleet_snapshot", _SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


fleet_snapshot = _load_script_module()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _run(
    tmp_path: Path,
    *,
    releases: Path | None = _RELEASES_FIXTURE,
    stable: Path | None = _STABLE_FIXTURE,
    beta: Path | None = _BETA_FIXTURE,
    history: Path | None = None,
    now: str | None = "2026-09-07T00:00:00+00:00",
    repo: str | None = None,
) -> tuple[int, Path]:
    """Invoke ``run()`` with fixture inputs; return ``(exit_code, history)``."""

    history_path = history if history is not None else tmp_path / "fleet-history.json"
    argv: list[str] = ["--history", str(history_path)]
    if releases is not None:
        argv += ["--releases-json", str(releases)]
    if stable is not None:
        argv += ["--stable-manifest", str(stable)]
    if beta is not None:
        argv += ["--beta-manifest", str(beta)]
    if now is not None:
        argv += ["--now", now]
    if repo is not None:
        argv += ["--repo", repo]
    return fleet_snapshot.run(argv), history_path


def _rows(path: Path) -> list[dict[str, Any]]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_releases(tmp_path: Path, payload: object, name: str = "releases.json") -> Path:
    path = tmp_path / name
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


# ---------------------------------------------------------------------------
# Contract I5 row shape
# ---------------------------------------------------------------------------


def test_first_run_creates_history_with_one_contract_i5_row(tmp_path: Path) -> None:
    """A first-ever run (no history file) writes exactly one row."""

    code, history = _run(tmp_path)

    assert code == 0
    rows = _rows(history)
    assert len(rows) == 1
    row = rows[0]
    # Contract I5 is FROZEN: these four keys, spelled exactly so.
    assert {"date", "counts", "stable", "beta"} <= set(row)
    assert row["date"] == "2026-09-07T00:00:00+00:00"
    assert row["stable"] == {"version": "1.35.0", "rollout_percent": 50}
    assert row["beta"] == {"version": "1.36.0-beta.1", "rollout_percent": 100}


def test_first_run_counts_are_per_version_per_os(tmp_path: Path) -> None:
    """``counts`` is ``{version: {os: n}}`` -- the beacon assets, only."""

    _, history = _run(tmp_path)
    counts = _rows(history)[0]["counts"]

    assert counts == {
        "1.34.2": {"darwin": 118, "linux": 26},
        # darwin == 42 (aarch64) + 8 (x86_64): see the summing test below.
        "1.35.0": {"darwin": 50, "linux": 5, "windows": 17},
        "1.36.0-beta.1": {"darwin": 4},
    }
    # The installer bundles on v1.35.0 (a .dmg at 9 and a .nsis.zip at 3) are
    # real downloads but not check-ins; folding them in would inflate the
    # fleet figure with one-off installs.
    assert 9 not in counts["1.35.0"].values()
    assert 3 not in counts["1.35.0"].values()


def test_two_arches_of_one_os_sum_into_a_single_bucket(tmp_path: Path) -> None:
    """Contract I5 keys ``counts`` by OS, so per-arch beacons must SUM.

    Every real macOS release ships both ``darwin-aarch64`` and
    ``darwin-x86_64`` ping assets (spec §4 lists both platforms). Because the
    frozen row shape is ``{version: {os: n}}`` and not
    ``{version: {target: n}}``, assigning instead of accumulating would make
    whichever arch the Releases API listed last erase the other -- losing an
    entire Apple Silicon or Intel check-in population on every snapshot, with
    no error anywhere. The single-arch fixtures cannot catch that, so this
    pins it directly.
    """

    payload = _write_releases(
        tmp_path,
        [
            {
                "tag_name": "v2.0.0",
                "draft": False,
                "prerelease": False,
                "assets": [
                    {"name": "beacon-2.0.0-darwin-aarch64.txt", "download_count": 30},
                    {"name": "beacon-2.0.0-darwin-x86_64.txt", "download_count": 12},
                    {"name": "beacon-2.0.0-linux-x86_64.txt", "download_count": 4},
                ],
            }
        ],
    )

    _, history = _run(tmp_path, releases=payload)
    assert _rows(history)[0]["counts"] == {"2.0.0": {"darwin": 42, "linux": 4}}


def test_draft_release_counts_are_excluded(tmp_path: Path) -> None:
    """A draft release's assets are not public, so its count is maintainer noise."""

    _, history = _run(tmp_path)
    assert "1.37.0" not in _rows(history)[0]["counts"]


def test_prerelease_counts_are_included(tmp_path: Path) -> None:
    """The beta channel is exactly the population a rollout wants to watch."""

    _, history = _run(tmp_path)
    assert _rows(history)[0]["counts"]["1.36.0-beta.1"] == {"darwin": 4}


# ---------------------------------------------------------------------------
# Honest estimation (the row must not read as a device count)
# ---------------------------------------------------------------------------


def test_row_carries_the_estimator_meaning_inline(tmp_path: Path) -> None:
    """A consumer reading only the JSON cannot mistake check-ins for devices."""

    _, history = _run(tmp_path)
    estimator = _rows(history)[0]["estimator"]

    assert estimator["unit"] == "cumulative_checkins"
    assert estimator["expected_checks_per_device_per_day"] == 6
    meaning = estimator["meaning"]
    assert "not devices" in meaning
    assert "ESTIMATE" in meaning
    assert "lower bound" in meaning


def test_script_header_states_the_estimator_meaning() -> None:
    """The file header is the second place the caveat must live."""

    header = _SCRIPT.read_text(encoding="utf-8")[:6000]
    assert "CHECK-INS, not devices" in header
    assert "Cumulative" in header
    assert "Inflated by repeat checks" in header


def test_success_stdout_repeats_the_caveat(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """The human-facing line never presents a count as a device tally."""

    _run(tmp_path)
    assert "cumulative check-ins, not devices" in capsys.readouterr().out


# ---------------------------------------------------------------------------
# Delta-only behaviour
# ---------------------------------------------------------------------------


def test_unchanged_run_writes_nothing(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Identical counts + channel pointers => no write, exit 0, clear message."""

    _, history = _run(tmp_path, now="2026-09-07T00:00:00+00:00")
    first = history.read_bytes()

    code, _ = _run(tmp_path, history=history, now="2026-09-07T06:00:00+00:00")

    assert code == 0
    assert history.read_bytes() == first, "a no-delta run must not touch the file"
    out = capsys.readouterr().out
    assert "unchanged" in out
    assert "delta-only" in out


def test_second_run_with_changed_counts_appends(tmp_path: Path) -> None:
    """A real count delta appends a second row and keeps the first."""

    _, history = _run(tmp_path, now="2026-09-07T00:00:00+00:00")

    bumped = json.loads(_RELEASES_FIXTURE.read_text(encoding="utf-8"))
    # One more aarch64 check-in. The darwin bucket is the SUM of both macOS
    # arches, so the recorded figure moves 50 -> 51, not 42 -> 43.
    bumped["releases"][0]["assets"][0]["download_count"] += 1
    later = _write_releases(tmp_path, bumped, "bumped.json")

    code, _ = _run(tmp_path, releases=later, history=history, now="2026-09-07T06:00:00+00:00")

    assert code == 0
    rows = _rows(history)
    assert len(rows) == 2
    assert rows[0]["counts"]["1.35.0"]["darwin"] == 50
    assert rows[1]["counts"]["1.35.0"]["darwin"] == 51


def test_rollout_percent_change_alone_is_a_delta(tmp_path: Path) -> None:
    """A promote (10 -> 50) must land a row even with flat counts.

    The dashboard's adoption curve draws its promote markers from these
    fields; dropping the row because the counts had not moved yet would erase
    the marker for the interval where the promote actually happened.
    """

    _, history = _run(tmp_path, now="2026-09-07T00:00:00+00:00")

    promoted = tmp_path / "stable-promoted.json"
    manifest = json.loads(_STABLE_FIXTURE.read_text(encoding="utf-8"))
    manifest["rollout_percent"] = 100
    promoted.write_text(json.dumps(manifest), encoding="utf-8")

    code, _ = _run(tmp_path, stable=promoted, history=history, now="2026-09-07T06:00:00+00:00")

    assert code == 0
    rows = _rows(history)
    assert len(rows) == 2
    assert rows[1]["stable"]["rollout_percent"] == 100


def test_new_version_appears_only_in_the_new_row(tmp_path: Path) -> None:
    """A version present in the API but absent from history is added, not backfilled."""

    _, history = _run(tmp_path, now="2026-09-07T00:00:00+00:00")
    assert "1.38.0" not in _rows(history)[0]["counts"]

    payload = json.loads(_RELEASES_FIXTURE.read_text(encoding="utf-8"))
    payload["releases"].append(
        {
            "tag_name": "v1.38.0",
            "draft": False,
            "prerelease": False,
            "assets": [{"name": "beacon-1.38.0-linux-x86_64.txt", "download_count": 7}],
        }
    )
    later = _write_releases(tmp_path, payload, "with-new-version.json")

    code, _ = _run(tmp_path, releases=later, history=history, now="2026-09-07T06:00:00+00:00")

    assert code == 0
    rows = _rows(history)
    assert len(rows) == 2
    assert "1.38.0" not in rows[0]["counts"], "history rows are immutable"
    assert rows[1]["counts"]["1.38.0"] == {"linux": 7}


def test_is_unchanged_ignores_date_and_estimator() -> None:
    """Only the three observed fields decide the delta."""

    base = fleet_snapshot.build_row(
        date="2026-09-07T00:00:00+00:00",
        counts={"1.0.0": {"linux": 1}},
        stable={"version": "1.0.0", "rollout_percent": 100},
        beta={"version": None, "rollout_percent": None},
    )
    later = fleet_snapshot.build_row(
        date="2026-09-08T00:00:00+00:00",
        counts={"1.0.0": {"linux": 1}},
        stable={"version": "1.0.0", "rollout_percent": 100},
        beta={"version": None, "rollout_percent": None},
    )
    assert fleet_snapshot.is_unchanged(base, later) is True
    assert fleet_snapshot.is_unchanged(None, later) is False


# ---------------------------------------------------------------------------
# Missing beacon assets
# ---------------------------------------------------------------------------


def test_release_without_beacon_assets_is_recorded_as_an_event(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """v1.33.0 in the fixture ships no beacon; the run succeeds and says so."""

    code, history = _run(tmp_path)

    assert code == 0
    assert "1.33.0" not in _rows(history)[0]["counts"]
    assert "fleet.release.no_beacon_assets" in capsys.readouterr().err


def test_release_with_no_assets_key_at_all(tmp_path: Path) -> None:
    """A release object with no ``assets`` key defaults to empty, not a crash."""

    payload = [{"tag_name": "v1.0.0", "draft": False}]
    releases = _write_releases(tmp_path, payload)

    code, history = _run(tmp_path, releases=releases, stable=None, beta=None)

    assert code == 0
    assert _rows(history)[0]["counts"] == {}


def test_asset_with_a_non_string_name_is_skipped(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    payload = [
        {
            "tag_name": "v1.0.0",
            "draft": False,
            "assets": [
                {"name": 17, "download_count": 3},
                {"name": "beacon-1.0.0-linux-x86_64.txt", "download_count": 3},
            ],
        }
    ]
    releases = _write_releases(tmp_path, payload)

    code, history = _run(tmp_path, releases=releases, stable=None, beta=None)

    assert code == 0
    assert _rows(history)[0]["counts"] == {"1.0.0": {"linux": 3}}
    assert "fleet.asset.unparsable_name" in capsys.readouterr().err


@pytest.mark.parametrize("bad_count", [True, "12", None, -1, 3.5])
def test_asset_with_an_unusable_download_count_is_skipped(
    tmp_path: Path, bad_count: object, capsys: pytest.CaptureFixture[str]
) -> None:
    """``true`` must not read as 1, and a negative count is nonsense."""

    payload = [
        {
            "tag_name": "v1.0.0",
            "draft": False,
            "assets": [{"name": "beacon-1.0.0-linux-x86_64.txt", "download_count": bad_count}],
        }
    ]
    releases = _write_releases(tmp_path, payload)

    code, history = _run(tmp_path, releases=releases, stable=None, beta=None)

    assert code == 0
    assert _rows(history)[0]["counts"] == {}
    assert "fleet.asset.invalid_count" in capsys.readouterr().err


def test_asset_with_a_zero_download_count_is_kept(tmp_path: Path) -> None:
    """Zero is a real measurement (asset published, nobody has checked in yet)."""

    payload = [
        {
            "tag_name": "v1.0.0",
            "draft": False,
            "assets": [{"name": "beacon-1.0.0-linux-x86_64.txt", "download_count": 0}],
        }
    ]
    releases = _write_releases(tmp_path, payload)

    _, history = _run(tmp_path, releases=releases, stable=None, beta=None)
    assert _rows(history)[0]["counts"] == {"1.0.0": {"linux": 0}}


# ---------------------------------------------------------------------------
# Contract I6 asset-name parsing
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        ("beacon-1.35.0-darwin-aarch64.txt", ("1.35.0", "darwin")),
        ("beacon-1.35.0-windows-x86_64.txt", ("1.35.0", "windows")),
        ("beacon-1.35.0-linux-x86_64.txt", ("1.35.0", "linux")),
        # The hyphenated pre-release is the case a naive rsplit gets wrong.
        ("beacon-1.36.0-beta.1-darwin-aarch64.txt", ("1.36.0-beta.1", "darwin")),
    ],
)
def test_parse_beacon_asset_name_accepts_contract_i6(name: str, expected: tuple[str, str]) -> None:
    assert fleet_snapshot.parse_beacon_asset_name(name) == expected


@pytest.mark.parametrize(
    "name",
    [
        "RytmRandomizer_1.35.0_aarch64.dmg",
        "beacon-1.35.0-darwin-aarch64.txt.sig",
        "beacon-1.35.0-solaris-sparc.txt",
        "beacon-darwin-aarch64.txt",
        "beacon.txt",
        "",
    ],
)
def test_parse_beacon_asset_name_rejects_non_beacons(name: str) -> None:
    assert fleet_snapshot.parse_beacon_asset_name(name) is None


# ---------------------------------------------------------------------------
# Malformed payloads
# ---------------------------------------------------------------------------


def test_malformed_releases_json_is_a_typed_failure(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    bad = tmp_path / "bad.json"
    bad.write_text("{not json", encoding="utf-8")

    code, _ = _run(tmp_path, releases=bad, stable=None, beta=None)

    assert code == 1
    err = capsys.readouterr().err
    assert "fleet.releases.malformed_payload" in err


@pytest.mark.parametrize(
    "payload",
    [
        {"unexpected": "shape"},
        # An envelope whose `releases` key exists but is the wrong type is the
        # likeliest hand-edit mistake in a fixture, and must not be mistaken
        # for an empty fleet.
        {"releases": {"v1.0.0": 3}},
        {"releases": "v1.0.0"},
        42,
        "a bare string",
    ],
    ids=["no_releases_key", "releases_is_object", "releases_is_string", "int", "str"],
)
def test_malformed_releases_payload_without_a_list(tmp_path: Path, payload: object) -> None:
    releases = _write_releases(tmp_path, payload)
    code, _ = _run(tmp_path, releases=releases, stable=None, beta=None)
    assert code == 1


def test_malformed_releases_payload_missing_file(tmp_path: Path) -> None:
    code, _ = _run(tmp_path, releases=tmp_path / "absent.json", stable=None, beta=None)
    assert code == 1


@pytest.mark.parametrize(
    "payload",
    [
        ["not-an-object"],
        [{"tag_name": "v1", "draft": False, "assets": "not-a-list"}],
        [{"tag_name": "v1", "draft": False, "assets": ["not-an-object"]}],
    ],
    ids=["release_not_object", "assets_not_list", "asset_not_object"],
)
def test_malformed_release_entries_fail_with_a_typed_code(
    tmp_path: Path, payload: object, capsys: pytest.CaptureFixture[str]
) -> None:
    releases = _write_releases(tmp_path, payload)
    code, _ = _run(tmp_path, releases=releases, stable=None, beta=None)
    assert code == 1
    assert "fleet.releases.malformed_payload" in capsys.readouterr().err


def test_bare_api_list_payload_is_accepted(tmp_path: Path) -> None:
    """The real API returns a bare list; the fixture wraps it. Both work."""

    payload = [
        {
            "tag_name": "v2.0.0",
            "draft": False,
            "assets": [{"name": "beacon-2.0.0-darwin-aarch64.txt", "download_count": 11}],
        }
    ]
    releases = _write_releases(tmp_path, payload)

    _, history = _run(tmp_path, releases=releases, stable=None, beta=None)
    assert _rows(history)[0]["counts"] == {"2.0.0": {"darwin": 11}}


# ---------------------------------------------------------------------------
# Channel manifests
# ---------------------------------------------------------------------------


def test_absent_channel_manifest_is_not_an_error(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Before the first release neither channel has published anything."""

    code, history = _run(tmp_path, stable=tmp_path / "nope.json", beta=None)

    assert code == 0
    row = _rows(history)[0]
    assert row["stable"] == {"version": None, "rollout_percent": None}
    assert row["beta"] == {"version": None, "rollout_percent": None}
    assert "fleet.manifest.absent" in capsys.readouterr().err


@pytest.mark.parametrize(
    "content",
    [
        "{not json",
        '["a", "list"]',
        '{"rollout_percent": 50}',
        '{"version": "", "rollout_percent": 50}',
        '{"version": 5, "rollout_percent": 50}',
        '{"version": "1.0.0"}',
        '{"version": "1.0.0", "rollout_percent": true}',
        '{"version": "1.0.0", "rollout_percent": "50"}',
        '{"version": "1.0.0", "rollout_percent": 101}',
        '{"version": "1.0.0", "rollout_percent": -1}',
    ],
)
def test_malformed_channel_manifest_fails_with_a_typed_code(
    tmp_path: Path, content: str, capsys: pytest.CaptureFixture[str]
) -> None:
    manifest = tmp_path / "stable.json"
    manifest.write_text(content, encoding="utf-8")

    code, _ = _run(tmp_path, stable=manifest, beta=None)

    assert code == 1
    assert "fleet.manifest.malformed" in capsys.readouterr().err


def test_unreadable_channel_manifest_is_a_typed_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """An OSError on read is a malformed-manifest failure, not a traceback."""

    manifest = tmp_path / "stable.json"
    manifest.write_text("{}", encoding="utf-8")

    def _boom(*_args: object, **_kwargs: object) -> str:
        raise OSError("denied")

    monkeypatch.setattr(Path, "read_text", _boom)
    metrics = fleet_snapshot.SnapshotMetrics()
    with pytest.raises(fleet_snapshot.FleetSnapshotError) as excinfo:
        fleet_snapshot.read_channel_manifest(manifest, metrics)
    assert excinfo.value.code == "fleet.manifest.malformed"


# ---------------------------------------------------------------------------
# History file failures
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "content",
    ["{not json", '{"rows": []}', '["not-an-object"]'],
    ids=["undecodable", "not_list", "row_not_object"],
)
def test_malformed_history_fails_rather_than_compounding_corruption(
    tmp_path: Path, content: str, capsys: pytest.CaptureFixture[str]
) -> None:
    history = tmp_path / "fleet-history.json"
    history.write_text(content, encoding="utf-8")

    code, _ = _run(tmp_path, history=history)

    assert code == 1
    assert "fleet.history.malformed" in capsys.readouterr().err


def test_unreadable_history_is_a_typed_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    history = tmp_path / "fleet-history.json"
    history.write_text("[]", encoding="utf-8")

    def _boom(*_args: object, **_kwargs: object) -> str:
        raise OSError("denied")

    monkeypatch.setattr(Path, "read_text", _boom)
    with pytest.raises(fleet_snapshot.FleetSnapshotError) as excinfo:
        fleet_snapshot.load_history(history)
    assert excinfo.value.code == "fleet.history.malformed"


def test_history_write_failure_is_a_typed_code(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    def _boom(*_args: object, **_kwargs: object) -> int:
        raise OSError("read-only filesystem")

    monkeypatch.setattr(Path, "write_text", _boom)

    code, _ = _run(tmp_path)

    assert code == 1
    assert "fleet.history.write_failed" in capsys.readouterr().err


def test_write_history_creates_missing_parent_directories(tmp_path: Path) -> None:
    target = tmp_path / "nested" / "deeper" / "fleet-history.json"
    fleet_snapshot.write_history(target, [{"date": "x"}])
    assert json.loads(target.read_text(encoding="utf-8")) == [{"date": "x"}]
    assert target.read_text(encoding="utf-8").endswith("\n")


# ---------------------------------------------------------------------------
# Network boundary (monkeypatched -- never a real request)
# ---------------------------------------------------------------------------


class _FakeResponse:
    def __init__(self, body: bytes) -> None:
        self._body = body

    def read(self) -> bytes:
        return self._body

    def __enter__(self) -> _FakeResponse:
        return self

    def __exit__(self, *_exc: object) -> bool:
        return False


def test_fetch_releases_uses_the_token_when_present(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, Any] = {}

    def _fake_urlopen(request: Any, timeout: int = 0) -> _FakeResponse:
        captured["url"] = request.full_url
        captured["headers"] = dict(request.header_items())
        captured["timeout"] = timeout
        return _FakeResponse(b'[{"tag_name": "v1.0.0"}]')

    monkeypatch.setattr(fleet_snapshot.urllib.request, "urlopen", _fake_urlopen)

    result = fleet_snapshot.fetch_releases("owner/repo", "tok")

    assert result == [{"tag_name": "v1.0.0"}]
    assert captured["url"].startswith("https://api.github.com/repos/owner/repo/releases")
    assert captured["headers"]["Authorization"] == "Bearer tok"
    assert captured["timeout"] == 30


def test_fetch_releases_omits_authorization_without_a_token(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, Any] = {}

    def _fake_urlopen(request: Any, timeout: int = 0) -> _FakeResponse:
        captured["headers"] = dict(request.header_items())
        return _FakeResponse(b"[]")

    monkeypatch.setattr(fleet_snapshot.urllib.request, "urlopen", _fake_urlopen)

    assert fleet_snapshot.fetch_releases("owner/repo", None) == []
    assert "Authorization" not in captured["headers"]


def test_fetch_releases_transport_failure_is_typed_and_leaks_no_url(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def _fake_urlopen(*_args: object, **_kwargs: object) -> _FakeResponse:
        raise fleet_snapshot.urllib.error.URLError("https://api.github.com/secret-path")

    monkeypatch.setattr(fleet_snapshot.urllib.request, "urlopen", _fake_urlopen)

    with pytest.raises(fleet_snapshot.FleetSnapshotError) as excinfo:
        fleet_snapshot.fetch_releases("owner/repo", None)

    assert excinfo.value.code == "fleet.releases.fetch_failed"
    # Only the exception TYPE is carried -- never the message, which here
    # embeds a URL.
    assert excinfo.value.detail == {"reason": "URLError"}


def test_fetch_releases_non_list_body_is_typed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        fleet_snapshot.urllib.request,
        "urlopen",
        lambda *_a, **_k: _FakeResponse(b'{"message": "Not Found"}'),
    )
    with pytest.raises(fleet_snapshot.FleetSnapshotError) as excinfo:
        fleet_snapshot.fetch_releases("owner/repo", None)
    assert excinfo.value.code == "fleet.releases.malformed_payload"


def test_run_uses_the_network_path_when_no_local_payload_is_given(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        fleet_snapshot.urllib.request,
        "urlopen",
        lambda *_a, **_k: _FakeResponse(
            b'[{"tag_name": "v3.0.0", "draft": false, "assets": '
            b'[{"name": "beacon-3.0.0-linux-x86_64.txt", "download_count": 2}]}]'
        ),
    )
    monkeypatch.setenv("GITHUB_TOKEN", "tok")

    code, history = _run(tmp_path, releases=None, stable=None, beta=None, repo="owner/repo")

    assert code == 0
    assert _rows(history)[0]["counts"] == {"3.0.0": {"linux": 2}}


def test_run_refuses_the_network_path_without_a_repo(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.delenv("GITHUB_REPOSITORY", raising=False)

    code, _ = _run(tmp_path, releases=None, stable=None, beta=None, repo="")

    assert code == 1
    assert "repo_not_configured" in capsys.readouterr().err


def test_parser_defaults_repo_from_the_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GITHUB_REPOSITORY", "owner/from-env")
    module = _load_script_module()
    args = module.build_parser().parse_args(["--history", "h.json"])
    assert args.repo == "owner/from-env"


def test_default_date_is_used_when_now_is_omitted(tmp_path: Path) -> None:
    code, history = _run(tmp_path, now=None)
    assert code == 0
    date = _rows(history)[0]["date"]
    assert date.endswith("+00:00")


# ---------------------------------------------------------------------------
# Observability surface
# ---------------------------------------------------------------------------


def test_step_summary_records_the_appended_row(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    summary = tmp_path / "summary.md"
    monkeypatch.setenv("GITHUB_STEP_SUMMARY", str(summary))

    _run(tmp_path)

    text = summary.read_text(encoding="utf-8")
    assert "Fleet snapshot: appended" in text
    assert "not devices" in text
    assert "versions_recorded=3" in text


def test_step_summary_records_the_unchanged_outcome(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _, history = _run(tmp_path, now="2026-09-07T00:00:00+00:00")
    summary = tmp_path / "summary.md"
    monkeypatch.setenv("GITHUB_STEP_SUMMARY", str(summary))

    _run(tmp_path, history=history, now="2026-09-07T06:00:00+00:00")

    assert "Fleet snapshot: unchanged" in summary.read_text(encoding="utf-8")


def test_step_summary_names_the_failing_rule(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A red run + its summary IS the alert -- so the summary must explain."""

    bad = tmp_path / "bad.json"
    bad.write_text("{not json", encoding="utf-8")
    summary = tmp_path / "summary.md"
    monkeypatch.setenv("GITHUB_STEP_SUMMARY", str(summary))

    _run(tmp_path, releases=bad, stable=None, beta=None)

    text = summary.read_text(encoding="utf-8")
    assert "Fleet snapshot: FAILED" in text
    assert "fleet.releases.malformed_payload" in text


def test_step_summary_is_a_noop_when_unset(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("GITHUB_STEP_SUMMARY", raising=False)
    fleet_snapshot.write_step_summary(["ignored"])
    monkeypatch.setenv("GITHUB_STEP_SUMMARY", "   ")
    fleet_snapshot.write_step_summary(["ignored"])


def test_step_summary_write_failure_never_fails_the_run(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """A cosmetic summary problem must not masquerade as a fleet-data outage."""

    monkeypatch.setenv("GITHUB_STEP_SUMMARY", str(tmp_path / "no-such-dir" / "s.md"))

    fleet_snapshot.write_step_summary(["line"])

    assert "summary_write" in capsys.readouterr().err


def test_emitted_details_never_carry_an_absolute_path(tmp_path: Path) -> None:
    """Gate 7: no runner directory layout in any emitted detail."""

    nested = tmp_path / "deep" / "nested"
    nested.mkdir(parents=True)
    manifest = nested / "stable.json"
    manifest.write_text("{not json", encoding="utf-8")

    metrics = fleet_snapshot.SnapshotMetrics()
    with pytest.raises(fleet_snapshot.FleetSnapshotError) as excinfo:
        fleet_snapshot.read_channel_manifest(manifest, metrics)

    assert excinfo.value.detail["file"] == "stable.json"
    assert str(tmp_path) not in json.dumps(dict(excinfo.value.detail))


def test_safe_path_label_returns_only_the_basename() -> None:
    assert fleet_snapshot.safe_path_label(Path("/a/b/c/fleet-history.json")) == (
        "fleet-history.json"
    )


def test_metrics_reject_codes_outside_the_closed_vocabularies() -> None:
    metrics = fleet_snapshot.SnapshotMetrics()
    with pytest.raises(ValueError, match="unknown event code"):
        metrics.record_event("fleet.invented.code")
    with pytest.raises(ValueError, match="unknown error code"):
        metrics.record_error("fleet.invented.code")


def test_error_constructor_rejects_an_unknown_code() -> None:
    with pytest.raises(ValueError, match="unknown error code"):
        fleet_snapshot.FleetSnapshotError("not.a.real.code")


def test_error_detail_defaults_to_empty() -> None:
    err = fleet_snapshot.FleetSnapshotError("fleet.history.malformed")
    assert err.detail == {}


def test_format_summary_lists_events_and_errors() -> None:
    metrics = fleet_snapshot.SnapshotMetrics()
    metrics.record_event("fleet.snapshot.started")
    metrics.record_error("fleet.history.malformed")
    summary = metrics.format_summary()
    assert "event fleet.snapshot.started=1" in summary
    assert "error fleet.history.malformed=1" in summary


def test_the_two_code_vocabularies_are_disjoint() -> None:
    """A code is either an event or a failure -- never ambiguously both."""

    assert not (fleet_snapshot.ERROR_CODES & fleet_snapshot.EVENT_CODES)


def test_log_event_emits_sorted_json_on_stderr(capsys: pytest.CaptureFixture[str]) -> None:
    fleet_snapshot.log_event("fleet.snapshot.started", zebra=1, alpha="a")
    line = capsys.readouterr().err.strip()
    assert json.loads(line) == {"code": "fleet.snapshot.started", "alpha": "a", "zebra": 1}
    assert line.index('"alpha"') < line.index('"code"') < line.index('"zebra"')


# ---------------------------------------------------------------------------
# Workflow invariants
# ---------------------------------------------------------------------------


def test_workflow_parses_and_declares_least_privilege() -> None:
    yaml = pytest.importorskip("yaml")
    path = _REPO_ROOT / ".github" / "workflows" / "fleet-snapshot.yml"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))

    # PyYAML parses the bare `on:` key as the boolean True.
    triggers = data[True]
    assert triggers["schedule"] == [{"cron": "0 */6 * * *"}]
    assert "workflow_dispatch" in triggers

    assert data["permissions"] == {"contents": "write"}

    job = data["jobs"]["snapshot"]
    steps = job["steps"]
    assert any(step.get("with", {}).get("ref") == "releases" for step in steps)
    # A push must only ever target the data branch.
    push_steps = [s for s in steps if "git push" in str(s.get("run", ""))]
    assert push_steps and all("HEAD:releases" in s["run"] for s in push_steps)


def test_workflow_never_opens_an_issue_on_failure() -> None:
    """A red run + step summary is the alert; an auto-filed issue is noise.

    Asserted against the parsed structure, not the raw text, so the prose
    comment that *explains* the absent scope cannot satisfy or break the check.
    """

    yaml = pytest.importorskip("yaml")
    path = _REPO_ROOT / ".github" / "workflows" / "fleet-snapshot.yml"
    text = path.read_text(encoding="utf-8")
    data = yaml.safe_load(text)

    # No token scope that could file anything, at the workflow or job level.
    assert "issues" not in data["permissions"]
    for job in data["jobs"].values():
        assert "issues" not in (job.get("permissions") or {})

    # No step reaches for the issues API by another route.
    for job in data["jobs"].values():
        for step in job["steps"]:
            body = f"{step.get('uses', '')} {step.get('run', '')}"
            assert "create-issue" not in body
            assert "issues" not in body

    assert "GITHUB_STEP_SUMMARY" in text


def _commit_step_run_body(*, strip_comments: bool = False) -> str:
    """Return the one committing step's ``run:`` body.

    ``strip_comments`` drops ``#`` lines so an assertion about command
    *ordering* cannot be satisfied (or defeated) by prose that happens to
    quote the command it is explaining.
    """

    yaml = pytest.importorskip("yaml")
    path = _REPO_ROOT / ".github" / "workflows" / "fleet-snapshot.yml"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    bodies = [
        str(step.get("run", ""))
        for step in data["jobs"]["snapshot"]["steps"]
        if "git commit" in str(step.get("run", ""))
    ]
    assert len(bodies) == 1, "expected exactly one committing step"
    body = bodies[0]
    if strip_comments:
        body = "\n".join(line for line in body.splitlines() if not line.lstrip().startswith("#"))
    return body


def test_workflow_commit_step_is_delta_guarded() -> None:
    """The commit is skipped when nothing changed -- no daily no-op stream."""

    body = _commit_step_run_body()
    assert "--quiet" in body
    assert "exit 0" in body


def test_workflow_delta_guard_sees_a_first_run_untracked_file() -> None:
    """The guard must stage before diffing, or the first row is lost forever.

    On the first-ever run ``fleet-history.json`` does not exist on the
    ``releases`` branch, so the script creates it UNTRACKED. ``git diff`` does
    not report untracked files, so a bare ``git diff --quiet -- <file>`` guard
    reports "no delta", skips the commit, and silently drops the first row --
    and every later run repeats the same drop. Staging first and consulting
    the index (``git diff --cached --quiet``) sees additions and modifications
    alike. This test pins the property, not one spelling of it.
    """

    body = _commit_step_run_body(strip_comments=True)
    assert "git add fleet-history.json" in body
    assert "git diff --cached --quiet" in body

    add_at = body.index("git add fleet-history.json")
    diff_at = body.index("git diff --cached --quiet")
    assert add_at < diff_at, "must stage before consulting the index"

    # The untracked-blind spelling must not be what gates the commit.
    assert "git diff --quiet -- fleet-history.json" not in body


def test_main_delegates_to_run(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """``main()`` is a thin argv shim over ``run()`` and carries no logic."""

    history = tmp_path / "fleet-history.json"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "fleet_snapshot.py",
            "--history",
            str(history),
            "--releases-json",
            str(_RELEASES_FIXTURE),
            "--now",
            "2026-09-07T00:00:00+00:00",
        ],
    )

    assert fleet_snapshot.main() == 0
    capsys.readouterr()
    assert len(_rows(history)) == 1


def test_the_channel_manifest_fixtures_pass_the_real_validator() -> None:
    """These stand in for manifests the pipeline actually publishes.

    ``fleet_snapshot`` only reads ``version`` and ``rollout_percent``, so a
    malformed fixture would not fail its own tests — it would simply encode a
    document that can never exist on the ``releases`` branch, and the snapshot
    would be verified against a fiction. Running them through the same
    ``release_lib.validate_manifest`` the release and promote workflows use is
    the cross-component contract (R2): one schema, every consumer.
    """
    import importlib.util
    import sys

    root = Path(__file__).resolve().parents[1]
    spec = importlib.util.spec_from_file_location(
        "release_lib", root / "scripts" / "release_lib.py"
    )
    assert spec is not None and spec.loader is not None
    release_lib = sys.modules.get("release_lib")
    if release_lib is None:
        release_lib = importlib.util.module_from_spec(spec)
        sys.modules["release_lib"] = release_lib
        spec.loader.exec_module(release_lib)

    for channel in ("stable", "beta"):
        payload = json.loads(
            (root / "tests" / "fixtures" / "fleet" / f"{channel}.json").read_text(encoding="utf-8")
        )
        violations = release_lib.validate_manifest(payload, expected_channel=channel)
        blocking = [v.code.value for v in violations if not v.is_advisory]
        assert release_lib.manifest_is_acceptable(
            violations
        ), f"fleet fixture {channel}.json would be refused by the pipeline: {blocking}"
