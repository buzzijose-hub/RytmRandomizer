#!/usr/bin/env python3
"""Append one fleet check-in row to ``fleet-history.json`` (contract I5).

WHAT THIS MEASURES -- AND WHAT IT DOES NOT
==========================================

Spec §6 ("Fleet awareness -- GitHub-native, zero-opex") makes every release
upload a one-byte ping asset per OS target, named per contract I6::

    beacon-<version>-<target>.txt

A running client fires a fire-and-forget GET of the ping asset matching *its
own* running version and OS each time it performs a scheduled update check.
GitHub increments that asset's ``download_count``. This script reads those
counters through the Releases API and appends a dated row to
``fleet-history.json`` on the ``releases`` branch.

**The counters are CHECK-INS, not devices.** Three properties of the number
must never be lost in translation, and the dashboard (contract I5 consumer,
agent C-dash) is required to restate them next to every derived figure:

1. **Cumulative.** ``download_count`` is a lifetime total for the asset, not a
   per-interval rate. Only the *delta* between two consecutive snapshots
   describes an interval, and this script therefore never presents a raw
   count as activity.
2. **Inflated by repeat checks.** One device checking every 4 hours over a
   24-hour interval contributes ~6 check-ins (plus one per launch). Dividing
   an interval delta by the expected per-device cadence yields an *estimate*
   of devices; the raw delta is the ground truth and the estimate is derived.
   This script deliberately does **not** perform that division -- it records
   the measured counts and the cadence assumption, and leaves the estimation
   (clearly labelled as such) to the dashboard.
3. **Partial by construction.** Anything that is not a public asset GET is
   invisible: clients on a pre-beacon version, clients with
   ``RYTM_RAND_UPDATE_BEACON=off``, and clients with updates frozen entirely
   never appear. Counts are a lower bound on the fleet, never a census.
   Caches and proxies can also swallow a GET, pushing the number lower still.

Every row carries this meaning inline in its ``estimator`` block so a consumer
reading only the JSON -- with no access to this docstring -- cannot mistake a
check-in tally for a device count.

DELTA-ONLY WRITES
=================

A cron that commits an identical row every six hours produces four noise
commits a day and buries real movement. When the extracted counts are
byte-identical to the most recent row's counts *and* the channel manifests are
unchanged, this script writes nothing and exits 0 with a clear message. The
caller (``.github/workflows/fleet-snapshot.yml``) commits only when the file
actually changed.

OBSERVABILITY (Gate 7)
======================

Every boundary emits a structured single-line JSON log on stderr with a typed
code drawn from :data:`ERROR_CODES` / :data:`EVENT_CODES` -- never a raw
``str(err)`` passthrough and never a filesystem path. Paths are reported as
their basename only. A run summary of the in-process counters is written to
``$GITHUB_STEP_SUMMARY`` when that variable is set, so a red run is
self-explaining without opening the job log.

USAGE
=====

::

    python scripts/fleet_snapshot.py \\
        --repo buzzijose-hub/RytmRandomizer \\
        --history releases/fleet-history.json \\
        --stable-manifest releases/stable.json \\
        --beta-manifest releases/beta.json

``--releases-json PATH`` substitutes a local payload for the network fetch;
that is the only mode the test-suite ever uses.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.request
from collections import Counter
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Final

# ---------------------------------------------------------------------------
# Typed vocabularies (Gate 7). Closed sets -- a caller may only emit a code
# that appears here, which is what makes log/metric aggregation possible.
# ---------------------------------------------------------------------------

#: Terminal failure codes. Each maps 1:1 to a nonzero exit and a step-summary
#: line naming the failing rule.
ERROR_CODES: Final[frozenset[str]] = frozenset(
    {
        "fleet.releases.fetch_failed",
        "fleet.releases.malformed_payload",
        "fleet.history.malformed",
        "fleet.history.write_failed",
        "fleet.manifest.malformed",
    }
)

#: Non-fatal events. These describe work done or deliberately skipped.
EVENT_CODES: Final[frozenset[str]] = frozenset(
    {
        "fleet.snapshot.started",
        "fleet.snapshot.appended",
        "fleet.snapshot.unchanged",
        "fleet.release.skipped_draft",
        "fleet.release.no_beacon_assets",
        "fleet.asset.unparsable_name",
        "fleet.asset.invalid_count",
        "fleet.manifest.absent",
    }
)

#: Exit status for a terminal failure. 0 is success (including the
#: write-nothing "unchanged" path, which is a normal outcome, not a failure).
EXIT_FAILURE: Final[int] = 1

# ---------------------------------------------------------------------------
# Contract I6: beacon-<version>-<target>.txt
#
# ``version`` is a SemVer core with an optional pre-release (``1.36.0-beta.1``)
# and ``target`` is a Tauri target triple shorthand (``darwin-aarch64``). Both
# contain hyphens, so the split is anchored on the *target* being the final
# two hyphen-joined segments matching a known OS/arch shape rather than on a
# naive rsplit -- ``beacon-1.36.0-beta.1-darwin-aarch64.txt`` would otherwise
# parse its version as ``1.36.0-beta`` and its OS as ``1.darwin``.
# ---------------------------------------------------------------------------

_BEACON_ASSET_RE: Final[re.Pattern[str]] = re.compile(
    r"^beacon-(?P<version>.+)-(?P<os>darwin|windows|linux)-(?P<arch>[A-Za-z0-9_]+)\.txt$"
)

#: Cadence assumption recorded in every row so the dashboard's device estimate
#: is auditable against the release that produced the data (spec §0 D2:
#: launch + every 4 h while running).
EXPECTED_CHECKS_PER_DEVICE_PER_DAY: Final[int] = 6

#: The one sentence a consumer sees if it reads nothing else. Kept in the row
#: itself (not only in this file) because C-dash renders the row, not the
#: script.
ESTIMATOR_MEANING: Final[str] = (
    "counts are cumulative ping-asset check-ins, not devices: one device "
    "checks in about "
    f"{EXPECTED_CHECKS_PER_DEVICE_PER_DAY} times per day, so only the delta "
    "between consecutive snapshots describes an interval, and dividing that "
    "delta by the expected cadence yields an ESTIMATE of devices. Clients on "
    "pre-beacon versions, with RYTM_RAND_UPDATE_BEACON=off, or with updates "
    "frozen never appear, so every figure is a lower bound."
)

# The OS vocabulary lives in _BEACON_ASSET_RE's alternation and nowhere else:
# a second tuple listing the same three names would be a fork that could drift
# out of step with the pattern that actually does the matching. Contract I5's
# `counts` mapping is keyed by that OS segment alone -- the architecture half
# of the target triple is folded into the OS bucket by SUMMING (see
# `extract_counts`), since the row shape is `{version: {os: n}}`, not
# `{version: {target: n}}`. macOS ships two arches per release, so a
# last-write-wins assignment there would silently drop a whole population.


# ---------------------------------------------------------------------------
# Counters + structured logging
# ---------------------------------------------------------------------------


@dataclass
class SnapshotMetrics:
    """In-process counters for one snapshot run.

    Mirrors the shape of ``observability/metrics.MidiMetrics`` (bounded
    categorical keys, a ``format_summary`` for the operator surface) without
    importing the package: this script runs in a bare CI job that installs no
    project dependencies, so it must stay stdlib-only.
    """

    events_by_code: Counter[str] = field(default_factory=Counter)
    errors_by_code: Counter[str] = field(default_factory=Counter)
    releases_scanned: int = 0
    beacon_assets_read: int = 0
    versions_recorded: int = 0

    def record_event(self, code: str) -> None:
        """Count one non-fatal event. Unknown codes are a programming error."""

        if code not in EVENT_CODES:
            raise ValueError(f"unknown event code: {code!r}")
        self.events_by_code[code] += 1

    def record_error(self, code: str) -> None:
        """Count one terminal failure. Unknown codes are a programming error."""

        if code not in ERROR_CODES:
            raise ValueError(f"unknown error code: {code!r}")
        self.errors_by_code[code] += 1

    def format_summary(self) -> str:
        """Render a deterministic multi-line counter snapshot."""

        lines = [
            f"releases_scanned={self.releases_scanned}",
            f"beacon_assets_read={self.beacon_assets_read}",
            f"versions_recorded={self.versions_recorded}",
        ]
        for code, count in sorted(self.events_by_code.items()):
            lines.append(f"event {code}={count}")
        for code, count in sorted(self.errors_by_code.items()):
            lines.append(f"error {code}={count}")
        return "\n".join(lines)


class FleetSnapshotError(Exception):
    """A terminal snapshot failure carrying a typed code and bounded detail.

    ``detail`` is a mapping of short, already-sanitized scalars. Never put a
    raw exception string or a filesystem path in it -- use
    :func:`safe_path_label` for anything path-derived.
    """

    def __init__(self, code: str, detail: Mapping[str, str | int] | None = None) -> None:
        if code not in ERROR_CODES:
            raise ValueError(f"unknown error code: {code!r}")
        super().__init__(code)
        self.code: Final[str] = code
        self.detail: Final[Mapping[str, str | int]] = dict(detail or {})


def safe_path_label(path: Path) -> str:
    """Return a path's basename -- never its absolute location.

    Emitted details must not leak a runner's directory layout (Gate 7). The
    basename is enough to identify which of the four files a run was reading.
    """

    return path.name


def log_event(code: str, **detail: str | int) -> None:
    """Write one structured JSON line to stderr.

    stderr (not stdout) so the human-readable result on stdout stays clean and
    pipeable. Keys are sorted for deterministic, diffable output.
    """

    record = {"code": code, **detail}
    print(json.dumps(record, sort_keys=True), file=sys.stderr)


# ---------------------------------------------------------------------------
# Pure extraction
# ---------------------------------------------------------------------------


def parse_beacon_asset_name(name: str) -> tuple[str, str] | None:
    """Split a contract-I6 asset name into ``(version, os)``.

    Returns ``None`` for any asset that is not a beacon ping asset -- installer
    bundles, checksums, and anything whose OS segment is not a known target.
    That is the normal case for most assets on a release and is not an error.
    """

    match = _BEACON_ASSET_RE.match(name)
    if match is None:
        return None
    return match.group("version"), match.group("os")


def _coerce_count(raw: object) -> int | None:
    """Return a non-negative int download count, or ``None`` if unusable.

    ``bool`` is rejected explicitly: it is an ``int`` subclass and a payload
    carrying ``true`` where a count belongs is malformed, not a count of one.
    """

    if isinstance(raw, bool) or not isinstance(raw, int):
        return None
    if raw < 0:
        return None
    return raw


def extract_counts(
    releases: Sequence[object],
    metrics: SnapshotMetrics,
) -> dict[str, dict[str, int]]:
    """Build the I5 ``counts`` mapping from a Releases-API payload.

    Draft releases are skipped: their assets are not publicly downloadable, so
    any count on them is an artifact of maintainer traffic. Prereleases ARE
    included -- the beta channel is exactly the population a rollout wants to
    watch.

    Raises:
        FleetSnapshotError: ``fleet.releases.malformed_payload`` when a release
            entry or its asset list is not the shape the API documents.
    """

    counts: dict[str, dict[str, int]] = {}
    for release in releases:
        if not isinstance(release, Mapping):
            raise FleetSnapshotError(
                "fleet.releases.malformed_payload",
                {"reason": "release_entry_not_object"},
            )
        metrics.releases_scanned += 1
        if release.get("draft") is True:
            metrics.record_event("fleet.release.skipped_draft")
            log_event("fleet.release.skipped_draft", tag=str(release.get("tag_name", ""))[:64])
            continue

        assets = release.get("assets", [])
        if not isinstance(assets, list):
            raise FleetSnapshotError(
                "fleet.releases.malformed_payload",
                {"reason": "assets_not_list"},
            )

        matched_any = False
        for asset in assets:
            if not isinstance(asset, Mapping):
                raise FleetSnapshotError(
                    "fleet.releases.malformed_payload",
                    {"reason": "asset_entry_not_object"},
                )
            raw_name = asset.get("name")
            if not isinstance(raw_name, str):
                metrics.record_event("fleet.asset.unparsable_name")
                log_event("fleet.asset.unparsable_name", reason="name_not_string")
                continue
            parsed = parse_beacon_asset_name(raw_name)
            if parsed is None:
                continue
            version, os_key = parsed
            count = _coerce_count(asset.get("download_count"))
            if count is None:
                metrics.record_event("fleet.asset.invalid_count")
                log_event("fleet.asset.invalid_count", asset=raw_name[:96])
                continue
            matched_any = True
            metrics.beacon_assets_read += 1
            # SUM, never assign. A single OS ships multiple architectures
            # (spec §4 lists both `darwin-aarch64` and `darwin-x86_64`), and
            # contract I5 keys `counts` by OS alone. Assigning here would make
            # whichever arch the API happened to list last silently erase the
            # other -- on every real macOS release, that is the entire Apple
            # Silicon or entire Intel check-in population going missing with no
            # error. Summing is what "folded into the OS bucket" has to mean.
            per_os = counts.setdefault(version, {})
            per_os[os_key] = per_os.get(os_key, 0) + count

        if not matched_any:
            metrics.record_event("fleet.release.no_beacon_assets")
            log_event("fleet.release.no_beacon_assets", tag=str(release.get("tag_name", ""))[:64])

    metrics.versions_recorded = len(counts)
    return counts


def read_channel_manifest(
    path: Path | None,
    metrics: SnapshotMetrics,
) -> dict[str, object]:
    """Return the I5 ``{version, rollout_percent}`` pair for one channel.

    A channel that has never published is normal before the first release, so
    an absent file yields ``{"version": None, "rollout_percent": None}`` rather
    than failing the run. A file that exists but is not valid JSON, or whose
    two fields are the wrong type, IS a failure -- a silently-wrong rollout
    marker would mislabel the dashboard's adoption curve.

    Raises:
        FleetSnapshotError: ``fleet.manifest.malformed``.
    """

    if path is None or not path.exists():
        metrics.record_event("fleet.manifest.absent")
        log_event(
            "fleet.manifest.absent",
            file=safe_path_label(path) if path is not None else "unset",
        )
        return {"version": None, "rollout_percent": None}

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as err:
        raise FleetSnapshotError(
            "fleet.manifest.malformed",
            {"file": safe_path_label(path), "reason": type(err).__name__},
        ) from err

    if not isinstance(payload, Mapping):
        raise FleetSnapshotError(
            "fleet.manifest.malformed",
            {"file": safe_path_label(path), "reason": "not_object"},
        )

    version = payload.get("version")
    rollout = payload.get("rollout_percent")
    if not isinstance(version, str) or not version:
        raise FleetSnapshotError(
            "fleet.manifest.malformed",
            {"file": safe_path_label(path), "reason": "version_not_string"},
        )
    if isinstance(rollout, bool) or not isinstance(rollout, int) or not 0 <= rollout <= 100:
        raise FleetSnapshotError(
            "fleet.manifest.malformed",
            {"file": safe_path_label(path), "reason": "rollout_percent_invalid"},
        )
    return {"version": version, "rollout_percent": rollout}


def build_row(
    *,
    date: str,
    counts: Mapping[str, Mapping[str, int]],
    stable: Mapping[str, object],
    beta: Mapping[str, object],
) -> dict[str, object]:
    """Assemble one contract-I5 row.

    Contract I5 (FROZEN -- C-dash renders exactly this)::

        {date, counts: {version: {os: n}},
         stable: {version, rollout_percent},
         beta: {version, rollout_percent}}

    An ``estimator`` block is carried alongside the four frozen keys. It is
    additive metadata, not a change to the four required keys: a consumer that
    reads only the contract shape is unaffected, while a consumer that reads
    the whole row cannot miss what the counts actually mean.
    """

    return {
        "date": date,
        "counts": {
            version: dict(sorted(per_os.items())) for version, per_os in sorted(counts.items())
        },
        "stable": dict(stable),
        "beta": dict(beta),
        "estimator": {
            "unit": "cumulative_checkins",
            "expected_checks_per_device_per_day": EXPECTED_CHECKS_PER_DEVICE_PER_DAY,
            "meaning": ESTIMATOR_MEANING,
        },
    }


def load_history(path: Path) -> list[dict[str, object]]:
    """Read the existing history rows, or ``[]`` on a first-ever run.

    Raises:
        FleetSnapshotError: ``fleet.history.malformed`` when the file exists
            but is not a JSON list of objects. Appending to a corrupt history
            would compound the corruption, so the run stops instead.
    """

    if not path.exists():
        return []
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as err:
        raise FleetSnapshotError(
            "fleet.history.malformed",
            {"file": safe_path_label(path), "reason": type(err).__name__},
        ) from err
    if not isinstance(payload, list):
        raise FleetSnapshotError(
            "fleet.history.malformed",
            {"file": safe_path_label(path), "reason": "not_list"},
        )
    rows: list[dict[str, object]] = []
    for entry in payload:
        if not isinstance(entry, Mapping):
            raise FleetSnapshotError(
                "fleet.history.malformed",
                {"file": safe_path_label(path), "reason": "row_not_object"},
            )
        rows.append(dict(entry))
    return rows


def is_unchanged(previous: Mapping[str, object] | None, candidate: Mapping[str, object]) -> bool:
    """True when ``candidate`` carries no new information versus ``previous``.

    Compares the three *observed* fields -- counts and both channel pointers --
    and deliberately ignores ``date`` (which always differs) and ``estimator``
    (constant metadata). A first-ever run has no previous row and is therefore
    always a change.
    """

    if previous is None:
        return False
    return all(previous.get(key) == candidate.get(key) for key in ("counts", "stable", "beta"))


# ---------------------------------------------------------------------------
# I/O boundaries
# ---------------------------------------------------------------------------


def fetch_releases(repo: str, token: str | None) -> list[object]:
    """GET the Releases API for ``repo`` and return the decoded list.

    Uses the workflow's default ``GITHUB_TOKEN`` when present, which raises the
    API rate limit and is the only credential this script ever needs (the
    endpoint is public; the token is a courtesy, not an authorization).

    Raises:
        FleetSnapshotError: ``fleet.releases.fetch_failed`` for any transport
            or decode failure. The exception type name -- never the message --
            is carried as the detail, so a URL embedded in an error string can
            never reach the log.
    """

    url = f"https://api.github.com/repos/{repo}/releases?per_page=100"
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "rytm-randomizer-fleet-snapshot",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(url, headers=headers)  # noqa: S310 - https literal above
    try:
        with urllib.request.urlopen(request, timeout=30) as response:  # noqa: S310
            payload = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, OSError, ValueError) as err:
        raise FleetSnapshotError(
            "fleet.releases.fetch_failed",
            {"reason": type(err).__name__},
        ) from err
    if not isinstance(payload, list):
        raise FleetSnapshotError(
            "fleet.releases.malformed_payload",
            {"reason": "top_level_not_list"},
        )
    return payload


def load_releases_payload(path: Path) -> list[object]:
    """Read a Releases-API payload from disk instead of the network.

    Accepts either the bare API list or the fixture's ``{"releases": [...]}``
    envelope, so a fixture can carry explanatory keys alongside the data.

    Raises:
        FleetSnapshotError: ``fleet.releases.malformed_payload``.
    """

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as err:
        raise FleetSnapshotError(
            "fleet.releases.malformed_payload",
            {"file": safe_path_label(path), "reason": type(err).__name__},
        ) from err
    if isinstance(payload, list):
        return payload
    if isinstance(payload, Mapping):
        releases = payload.get("releases")
        if isinstance(releases, list):
            return releases
    raise FleetSnapshotError(
        "fleet.releases.malformed_payload",
        {"file": safe_path_label(path), "reason": "no_release_list"},
    )


def write_history(path: Path, rows: Sequence[Mapping[str, object]]) -> None:
    """Write the history file with a trailing newline and stable key order.

    Raises:
        FleetSnapshotError: ``fleet.history.write_failed``.
    """

    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(list(rows), indent=2) + "\n", encoding="utf-8")
    except OSError as err:
        raise FleetSnapshotError(
            "fleet.history.write_failed",
            {"file": safe_path_label(path), "reason": type(err).__name__},
        ) from err


def write_step_summary(lines: Iterable[str]) -> None:
    """Append ``lines`` to ``$GITHUB_STEP_SUMMARY`` when the runner set it.

    A failed cron run has no issue and no notification by design (spec §6 /
    plan A5.5) -- the red run plus this summary IS the alert, so the summary
    must always explain the outcome. Outside CI the variable is unset and this
    is a no-op.
    """

    target = os.environ.get("GITHUB_STEP_SUMMARY", "").strip()
    if not target:
        return
    try:
        with open(target, "a", encoding="utf-8") as handle:
            for line in lines:
                handle.write(line + "\n")
    except OSError:
        # A summary is diagnostics, never the job's result: failing the run
        # because the runner's summary file was unwritable would turn a
        # cosmetic problem into a false fleet-data outage.
        log_event("fleet.snapshot.started", summary_write="skipped")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    """Return the argument parser (separate so tests can introspect it)."""

    parser = argparse.ArgumentParser(
        description=(
            "Append one fleet check-in row to fleet-history.json. Counts are "
            "cumulative ping-asset check-ins, not devices."
        )
    )
    parser.add_argument(
        "--repo",
        default=os.environ.get("GITHUB_REPOSITORY", ""),
        help="owner/name of the repository to read releases from.",
    )
    parser.add_argument(
        "--history",
        type=Path,
        required=True,
        help="path to fleet-history.json (created if absent).",
    )
    parser.add_argument(
        "--stable-manifest",
        type=Path,
        default=None,
        help="path to stable.json; absent is treated as 'channel not published'.",
    )
    parser.add_argument(
        "--beta-manifest",
        type=Path,
        default=None,
        help="path to beta.json; absent is treated as 'channel not published'.",
    )
    parser.add_argument(
        "--releases-json",
        type=Path,
        default=None,
        help="read the Releases payload from this file instead of the network.",
    )
    parser.add_argument(
        "--now",
        default=None,
        help="ISO-8601 timestamp for the row's date (default: current UTC).",
    )
    return parser


def run(argv: Sequence[str] | None = None) -> int:
    """Execute one snapshot. Returns the process exit status."""

    args = build_parser().parse_args(argv)
    metrics = SnapshotMetrics()
    metrics.record_event("fleet.snapshot.started")
    log_event("fleet.snapshot.started", source="file" if args.releases_json else "api")

    try:
        if args.releases_json is not None:
            releases = load_releases_payload(args.releases_json)
        else:
            if not args.repo:
                raise FleetSnapshotError(
                    "fleet.releases.fetch_failed",
                    {"reason": "repo_not_configured"},
                )
            releases = fetch_releases(args.repo, os.environ.get("GITHUB_TOKEN"))

        counts = extract_counts(releases, metrics)
        stable = read_channel_manifest(args.stable_manifest, metrics)
        beta = read_channel_manifest(args.beta_manifest, metrics)
        history = load_history(args.history)

        date = args.now or datetime.now(timezone.utc).isoformat(timespec="seconds")
        row = build_row(date=date, counts=counts, stable=stable, beta=beta)
        previous = history[-1] if history else None

        if is_unchanged(previous, row):
            metrics.record_event("fleet.snapshot.unchanged")
            log_event("fleet.snapshot.unchanged", versions=len(counts))
            print(
                "fleet-snapshot: counts and channel pointers unchanged since the "
                "last row; wrote nothing (delta-only policy)."
            )
            write_step_summary(
                [
                    "### Fleet snapshot: unchanged",
                    "",
                    "No delta since the previous row, so no commit was made.",
                    "",
                    "```",
                    metrics.format_summary(),
                    "```",
                ]
            )
            return 0

        history.append(row)
        write_history(args.history, history)
        metrics.record_event("fleet.snapshot.appended")
        log_event("fleet.snapshot.appended", versions=len(counts), rows=len(history))
        print(
            f"fleet-snapshot: appended row {len(history)} covering "
            f"{len(counts)} version(s). Counts are cumulative check-ins, not devices."
        )
        write_step_summary(
            [
                "### Fleet snapshot: appended",
                "",
                f"Row {len(history)} covers {len(counts)} version(s).",
                "",
                f"> {ESTIMATOR_MEANING}",
                "",
                "```",
                metrics.format_summary(),
                "```",
            ]
        )
        return 0

    except FleetSnapshotError as err:
        metrics.record_error(err.code)
        log_event(err.code, **{str(k): v for k, v in err.detail.items()})
        detail = ", ".join(f"{key}={value}" for key, value in sorted(err.detail.items()))
        print(f"fleet-snapshot failed: {err.code} ({detail})", file=sys.stderr)
        write_step_summary(
            [
                "### Fleet snapshot: FAILED",
                "",
                f"Failing rule: `{err.code}`",
                "",
                f"Detail: `{detail}`",
                "",
                "```",
                metrics.format_summary(),
                "```",
            ]
        )
        return EXIT_FAILURE


def main() -> int:
    """Entry point: run one snapshot using ``sys.argv``."""

    return run()


# The module-level ``__main__`` guard is the only unreachable line in-process:
# coverage measures an imported module, where ``__name__`` is never
# ``"__main__"``. ``main()`` itself is covered by
# ``test_main_delegates_to_run``, so no production logic hides behind this.
if __name__ == "__main__":  # pragma: no cover - script entry point
    raise SystemExit(main())
