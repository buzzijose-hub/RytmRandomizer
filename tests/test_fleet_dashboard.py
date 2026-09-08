"""Contract and render checks for the static fleet dashboard.

The dashboard (``dashboard/index.html``) is a single self-contained page served
from GitHub Pages on the ``releases`` branch. It has no build step, no backend,
and no external dependency of any kind: the only network call it may ever make
is a same-directory fetch of ``fleet-history.json`` (interface contract I5).

That "no build step" property is exactly what makes it easy to break silently.
Nothing compiles it, nothing type-checks it, and a CDN ``<script src=...>``
smuggled in during a later edit would look fine on a developer laptop and blank
the page for every reader behind a restrictive network. These tests are the
gate.

Two layers:

1. **Source contract** (pure Python ``html.parser``): the page is
   self-contained, states the estimator caveat in reader-visible prose, mounts
   its three sections, and derives its series from the data rather than
   hardcoding any version string.
2. **Behavioural render**: the page's own rendering module is extracted and
   executed under ``node`` against
   ``tests/fixtures/fleet/synthetic_history.json``; the produced markup is then
   parsed and asserted against the fixture. This is what proves every fixture
   version is referenced, that promote markers land where ``rollout_percent``
   or the target version changed, that estimates are accompanied by raw counts,
   and that an empty history degrades to "no data yet" instead of a broken
   chart or a JS error.

``node`` is a hard requirement for layer 2 rather than a skip: the repo's
frontend toolchain already depends on it (``desktop/web``, Playwright), and a
silently-skipping render check is not a gate. If it is genuinely absent the
tests fail loudly and say why.

Estimator semantics under test (spec ``2026-08-03-autoupdate-distribution.md``
sections 6 and 6.1): ``counts`` are GitHub's cumulative release-asset
``download_count`` values, so the page differences consecutive snapshots and
divides the per-interval check-ins by the expected checks per device per
interval (gate D2 cadence: launch plus every 4 hours, i.e. 6 per device per
day). A history of N snapshots therefore yields N-1 chartable intervals.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
from html.parser import HTMLParser
from pathlib import Path
from typing import Final

import pytest

pytestmark = pytest.mark.fast

_REPO_ROOT: Final[Path] = Path(__file__).resolve().parent.parent
_DASHBOARD_HTML: Final[Path] = _REPO_ROOT / "dashboard" / "index.html"
_DASHBOARD_README: Final[Path] = _REPO_ROOT / "dashboard" / "README.md"
_SYNTHETIC_HISTORY: Final[Path] = (
    _REPO_ROOT / "tests" / "fixtures" / "fleet" / "synthetic_history.json"
)

#: Expected check-ins per device per day, from the gate D2 cadence
#: (launch + every 4 h while running). The page must agree with this.
_EXPECTED_CHECKS_PER_DEVICE_PER_DAY: Final[int] = 6

#: Section ids the page must mount its three renders into.
_REQUIRED_SECTION_IDS: Final[tuple[str, ...]] = (
    "composition-body",
    "adoption-body",
    "promotions-body",
)

#: Phrases the estimator caveat must state in prose a reader will actually see.
#: Together these are the honest description the spec requires on the page:
#: what is measured, that it is cumulative and differenced, that the device
#: figure is derived, and that it is not a unique-device count.
_CAVEAT_PHRASES: Final[tuple[str, ...]] = (
    "check-in",
    "cumulative",
    "estimate, not a count",
    "not a count of unique devices",
)

#: Attributes that can pull in a third-party resource. ``src``/``href`` on a
#: local relative path is fine; an absolute or protocol-relative URL is not.
_URL_ATTRS: Final[tuple[str, ...]] = ("src", "href", "srcset", "data", "poster")

_ABSOLUTE_URL: Final[re.Pattern[str]] = re.compile(r"^(?:[a-z][a-z0-9+.-]*:)?//", re.IGNORECASE)

_VOID_ELEMENTS: Final[frozenset[str]] = frozenset(
    {"meta", "link", "br", "hr", "img", "input", "source", "area", "base", "col", "embed", "wbr"}
)


class _Collector(HTMLParser):
    """Collect the parts of an HTML document these tests assert against."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.ids: set[str] = set()
        self.external_urls: list[str] = []
        self.script_srcs: list[str] = []
        self.text_by_id: dict[str, str] = {}
        self.attrs_by_tag: dict[str, list[dict[str, str]]] = {}
        self._open_ids: list[str | None] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        mapping = {key: (value or "") for key, value in attrs}
        self.attrs_by_tag.setdefault(tag, []).append(mapping)

        element_id = mapping.get("id")
        if element_id:
            self.ids.add(element_id)

        for attr in _URL_ATTRS:
            value = mapping.get(attr, "").strip()
            if value and _ABSOLUTE_URL.match(value):
                self.external_urls.append(value)
        if tag == "script" and mapping.get("src"):
            self.script_srcs.append(mapping["src"])

        # Void elements never close, so they must not push a capture frame.
        if tag in _VOID_ELEMENTS:
            return
        self._open_ids.append(element_id)
        if element_id:
            self.text_by_id.setdefault(element_id, "")

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        # Self-closing form: record attributes without opening a frame.
        mapping = {key: (value or "") for key, value in attrs}
        self.attrs_by_tag.setdefault(tag, []).append(mapping)
        element_id = mapping.get("id")
        if element_id:
            self.ids.add(element_id)
        for attr in _URL_ATTRS:
            value = mapping.get(attr, "").strip()
            if value and _ABSOLUTE_URL.match(value):
                self.external_urls.append(value)

    def handle_endtag(self, tag: str) -> None:
        if self._open_ids:
            self._open_ids.pop()

    def handle_data(self, data: str) -> None:
        for element_id in self._open_ids:
            if element_id:
                self.text_by_id[element_id] = self.text_by_id.get(element_id, "") + data


def _parse(markup: str) -> _Collector:
    collector = _Collector()
    collector.feed(markup)
    collector.close()
    return collector


def _normalize(text: str) -> str:
    return " ".join(text.split()).lower()


def _attrs_with(collector: _Collector, tag: str, key: str) -> list[dict[str, str]]:
    return [attrs for attrs in collector.attrs_by_tag.get(tag, []) if key in attrs]


@pytest.fixture(scope="module")
def page_source() -> str:
    return _DASHBOARD_HTML.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def page(page_source: str) -> _Collector:
    return _parse(page_source)


@pytest.fixture(scope="module")
def synthetic_history() -> list[dict[str, object]]:
    loaded = json.loads(_SYNTHETIC_HISTORY.read_text(encoding="utf-8"))
    assert isinstance(loaded, list)
    return loaded


# ---------------------------------------------------------------------------
# Layer 1 -- source contract.
# ---------------------------------------------------------------------------


def test_dashboard_page_exists_and_is_html(page_source: str) -> None:
    assert page_source.lstrip().lower().startswith("<!doctype html>")
    assert "<title>" in page_source


def test_dashboard_loads_nothing_external(page: _Collector) -> None:
    """No CDN, no font host, no analytics -- the page must render standalone."""
    assert page.script_srcs == [], f"external script tags: {page.script_srcs}"
    assert page.external_urls == [], f"absolute URLs in markup: {page.external_urls}"


def test_dashboard_only_fetches_the_sibling_history_file(page_source: str) -> None:
    fetched = re.findall(r"fetch\(\s*([\"'])(.*?)\1", page_source)
    assert [target for _, target in fetched] == ["fleet-history.json"]
    assert "XMLHttpRequest" not in page_source
    assert "importScripts" not in page_source
    assert "EventSource" not in page_source


def test_dashboard_mounts_the_three_sections(page: _Collector) -> None:
    for section_id in _REQUIRED_SECTION_IDS:
        assert section_id in page.ids, f"missing mount point #{section_id}"


def test_estimator_caveat_is_reader_visible_prose(page: _Collector) -> None:
    """Requirement: say what the number means where a reader will see it."""
    assert "estimator-caveat" in page.ids
    caveat = _normalize(page.text_by_id["estimator-caveat"])
    for phrase in _CAVEAT_PHRASES:
        assert phrase in caveat, f"caveat is missing {phrase!r}: {caveat}"
    # It must be body prose, not a comment the reader never sees.
    assert "<!--" not in page.text_by_id["estimator-caveat"]


def test_estimator_formula_is_stated_on_the_page(page: _Collector) -> None:
    """The divisor is the whole estimator; the page must spell it out."""
    assert "estimator-formula" in page.ids
    formula = _normalize(page.text_by_id["estimator-formula"])
    assert "estimated devices" in formula
    assert "check-ins" in formula
    assert "per device" in formula


def test_page_agrees_with_the_d2_cadence(page_source: str) -> None:
    """The stated cadence and the estimator divisor must be the same number."""
    assert "every 4 hours" in page_source
    match = re.search(
        r"EXPECTED_CHECKS_PER_DEVICE_PER_DAY\s*=\s*24\s*/\s*CHECK_INTERVAL_HOURS", page_source
    )
    assert match is not None, "the divisor must be derived from the check interval"
    interval = re.search(r"CHECK_INTERVAL_HOURS\s*=\s*(\d+)", page_source)
    assert interval is not None
    assert 24 // int(interval.group(1)) == _EXPECTED_CHECKS_PER_DEVICE_PER_DAY


def test_page_hardcodes_no_version_string(page_source: str) -> None:
    """Series must be derived from the data, never enumerated in the page."""
    script_only = "\n".join(re.findall(r"<script>(.*?)</script>", page_source, flags=re.DOTALL))
    assert script_only, "expected an inline <script> block"
    assert re.search(r"\b\d+\.\d+\.\d+\b", script_only) is None, (
        "the dashboard script contains a literal SemVer string; versions must "
        "come from fleet-history.json"
    )


def test_page_declares_an_empty_state(page_source: str) -> None:
    assert "No data yet." in page_source


def test_series_are_not_encoded_by_colour_alone(page_source: str) -> None:
    """A11y: every series carries a dash pattern and a glyph, not just a hue."""
    assert "stroke-dasharray" in page_source
    assert "GLYPHS" in page_source
    assert 'aria-label="Estimated devices per version over time' in page_source
    assert 'aria-label="Estimated devices per version in the latest interval' in page_source


def test_theme_tokens_are_defined_for_light_and_dark(page_source: str) -> None:
    assert "color-scheme: light dark" in page_source
    assert "prefers-color-scheme: dark" in page_source
    # Every series colour must have both a light and a dark definition.
    light, dark = page_source.split("prefers-color-scheme: dark", 1)
    for index in range(1, 7):
        token = f"--s{index}:"
        assert token in light, f"{token} missing from the light palette"
        assert token in dark, f"{token} missing from the dark palette"


def test_dashboard_readme_documents_the_page() -> None:
    readme = _DASHBOARD_README.read_text(encoding="utf-8")
    assert "fleet-history.json" in readme
    assert "releases" in readme
    assert "check-in" in readme.lower()
    assert "estimate" in readme.lower()


# ---------------------------------------------------------------------------
# Fixture contract -- the synthetic I5 history the render layer runs against.
# ---------------------------------------------------------------------------


def test_synthetic_history_matches_the_i5_shape(
    synthetic_history: list[dict[str, object]],
) -> None:
    assert synthetic_history, "the synthetic history must not be empty"
    for entry in synthetic_history:
        assert set(entry) == {"date", "counts", "stable", "beta"}
        assert isinstance(entry["date"], str)
        counts = entry["counts"]
        assert isinstance(counts, dict) and counts
        for version, per_os in counts.items():
            assert isinstance(version, str)
            assert isinstance(per_os, dict) and per_os
            for os_name, number in per_os.items():
                assert isinstance(os_name, str)
                assert isinstance(number, int) and number >= 0
        for channel in ("stable", "beta"):
            channel_entry = entry[channel]
            assert isinstance(channel_entry, dict)
            assert set(channel_entry) == {"version", "rollout_percent"}
            assert isinstance(channel_entry["version"], str)
            assert isinstance(channel_entry["rollout_percent"], int)
            assert 0 <= channel_entry["rollout_percent"] <= 100


def test_synthetic_history_counts_are_cumulative(
    synthetic_history: list[dict[str, object]],
) -> None:
    """``counts`` mirrors GitHub's ``download_count``: it never decreases.

    If the fixture were per-interval instead, it would silently validate the
    wrong estimator -- the page would look right against data no real snapshot
    could produce.
    """
    previous: dict[tuple[str, str], int] = {}
    for entry in synthetic_history:
        counts = entry["counts"]
        assert isinstance(counts, dict)
        date = entry["date"]
        for version, per_os in counts.items():
            assert isinstance(per_os, dict)
            for os_name, value in per_os.items():
                key = (version, os_name)
                assert isinstance(value, int)
                assert value >= previous.get(key, 0), f"{date}: {key} went backwards"
                previous[key] = value


def test_synthetic_history_exercises_both_promotion_kinds(
    synthetic_history: list[dict[str, object]],
) -> None:
    """The fixture must drive a version promotion AND a percent bump."""
    version_changes = 0
    percent_bumps = 0
    for channel in ("stable", "beta"):
        previous: dict[str, object] | None = None
        for entry in synthetic_history:
            current = entry[channel]
            assert isinstance(current, dict)
            if previous is not None:
                if previous["version"] != current["version"]:
                    version_changes += 1
                elif previous["rollout_percent"] != current["rollout_percent"]:
                    percent_bumps += 1
            previous = current
    assert version_changes >= 1, "fixture needs a channel version promotion"
    assert percent_bumps >= 1, "fixture needs a rollout_percent bump"


def test_synthetic_history_spans_several_versions_and_all_targets(
    synthetic_history: list[dict[str, object]],
) -> None:
    versions: set[str] = set()
    oses: set[str] = set()
    for entry in synthetic_history:
        counts = entry["counts"]
        assert isinstance(counts, dict)
        versions.update(counts)
        for per_os in counts.values():
            assert isinstance(per_os, dict)
            oses.update(per_os)
    assert len(versions) >= 3, "the adoption curve needs several overlapping series"
    assert {"darwin-aarch64", "windows-x86_64", "linux-x86_64"} <= oses


# ---------------------------------------------------------------------------
# Layer 2 -- behavioural render through the page's own script.
# ---------------------------------------------------------------------------

_NODE: Final[str | None] = shutil.which("node")


def _extract_module(page_source: str) -> str:
    blocks = re.findall(r"<script>(.*?)</script>", page_source, flags=re.DOTALL)
    assert len(blocks) == 1, "expected exactly one inline script block"
    return blocks[0]


def _render(tmp_path: Path, page_source: str, history: object) -> dict[str, str]:
    """Execute the page's rendering module under node and return its markup."""
    assert _NODE is not None, (
        "node is required for the dashboard render check; it is part of this "
        "repo's frontend toolchain (desktop/web, Playwright). Install node or "
        "run this suite where it is available -- skipping would leave the "
        "dashboard's only behavioural gate unenforced."
    )
    module_path = tmp_path / "fleet_dashboard.js"
    module_path.write_text(_extract_module(page_source), encoding="utf-8")
    driver_path = tmp_path / "driver.js"
    driver_path.write_text(
        "const api = require('./fleet_dashboard.js');\n"
        "const history = JSON.parse(process.argv[2]);\n"
        "process.stdout.write(JSON.stringify(api.renderAll(history)));\n",
        encoding="utf-8",
    )
    completed = subprocess.run(
        [_NODE, str(driver_path), json.dumps(history)],
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    rendered = json.loads(completed.stdout)
    assert set(rendered) == {"composition", "adoption", "promotions"}
    return rendered


def _expected_intervals(history: list[dict[str, object]]) -> list[dict[str, object]]:
    """Mirror of the page's delta logic, written independently in Python.

    Re-deriving the arithmetic here rather than importing the page's own
    numbers is the point: if the page's estimator changes, these assertions
    must be updated deliberately.
    """
    intervals: list[dict[str, object]] = []
    for index in range(1, len(history)):
        previous = history[index - 1]
        current = history[index]
        previous_counts = previous["counts"]
        current_counts = current["counts"]
        assert isinstance(previous_counts, dict) and isinstance(current_counts, dict)
        deltas: dict[str, dict[str, int]] = {}
        for version, per_os in current_counts.items():
            assert isinstance(per_os, dict)
            before = previous_counts.get(version, {})
            assert isinstance(before, dict)
            deltas[version] = {
                os_name: max(0, value - before.get(os_name, 0)) for os_name, value in per_os.items()
            }
        intervals.append({"date": current["date"], "check_ins": deltas})
    return intervals


@pytest.fixture(scope="module")
def rendered(
    tmp_path_factory: pytest.TempPathFactory,
    page_source: str,
    synthetic_history: list[dict[str, object]],
) -> dict[str, str]:
    return _render(tmp_path_factory.mktemp("fleet"), page_source, synthetic_history)


def test_render_references_every_version_in_the_fixture(
    rendered: dict[str, str],
    synthetic_history: list[dict[str, object]],
) -> None:
    versions: set[str] = set()
    for entry in synthetic_history:
        counts = entry["counts"]
        assert isinstance(counts, dict)
        versions.update(counts)

    chart = _parse(rendered["adoption"])
    legend_versions = {attrs["data-version"] for attrs in _attrs_with(chart, "li", "data-version")}
    assert legend_versions == versions

    series_versions = {
        attrs["data-version"] for attrs in _attrs_with(chart, "polyline", "data-version")
    }
    assert series_versions == versions


def test_render_stacks_current_composition_by_os(
    rendered: dict[str, str],
    synthetic_history: list[dict[str, object]],
) -> None:
    """Spec 6.1 item 1: stacked bars, version x OS, from the latest delta."""
    intervals = _expected_intervals(synthetic_history)
    latest = intervals[-1]
    check_ins = latest["check_ins"]
    assert isinstance(check_ins, dict)
    expected_versions = {
        version for version, per_os in check_ins.items() if sum(per_os.values()) > 0
    }
    assert expected_versions, "the last interval must have movement to chart"

    chart = _parse(rendered["composition"])

    bar_versions = {attrs["data-version"] for attrs in _attrs_with(chart, "g", "data-version")}
    assert bar_versions == expected_versions

    # Each bar is stacked: one <rect> per OS that actually moved.
    segments: dict[str, set[str]] = {}
    for attrs in _attrs_with(chart, "rect", "data-os"):
        segments.setdefault(attrs["data-version"], set()).add(attrs["data-os"])
    for version in expected_versions:
        per_os = check_ins[version]
        assert isinstance(per_os, dict)
        expected_oses = {name for name, value in per_os.items() if value > 0}
        assert segments.get(version) == expected_oses, f"stack mismatch for {version}"

    # And the segment widths carry the raw counts they were derived from.
    for attrs in _attrs_with(chart, "rect", "data-check-ins"):
        version = attrs["data-version"]
        per_os = check_ins[version]
        assert isinstance(per_os, dict)
        assert int(attrs["data-check-ins"]) == per_os[attrs["data-os"]]


def test_composition_shows_raw_check_ins_beside_every_estimate(
    rendered: dict[str, str],
    synthetic_history: list[dict[str, object]],
) -> None:
    """Spec 6.1: "the page always shows the measured number next to the derived one"."""
    intervals = _expected_intervals(synthetic_history)
    check_ins = intervals[-1]["check_ins"]
    assert isinstance(check_ins, dict)

    chart = _parse(rendered["composition"])
    bars = {attrs["data-version"]: attrs for attrs in _attrs_with(chart, "g", "data-version")}
    assert bars, "expected per-version bar groups"

    for version, attrs in bars.items():
        per_os = check_ins[version]
        assert isinstance(per_os, dict)
        raw = sum(per_os.values())
        assert int(attrs["data-check-ins"]) == raw, f"{version} raw total mismatch"

        # The estimate is the raw count divided by the interval's expected
        # checks per device. The fixture's snapshots are one day apart.
        expected = raw / _EXPECTED_CHECKS_PER_DEVICE_PER_DAY
        assert abs(float(attrs["data-devices"]) - expected) < 0.05, (
            f"{version}: {attrs['data-devices']} is not {raw} / "
            f"{_EXPECTED_CHECKS_PER_DEVICE_PER_DAY}"
        )

    # The table repeats both numbers in text, headed so a reader can tell
    # which column is which.
    assert "Est. devices" in rendered["composition"]
    assert "Raw check-ins" in rendered["composition"]


def test_render_emits_a_promote_marker_for_every_channel_change(
    rendered: dict[str, str],
    synthetic_history: list[dict[str, object]],
) -> None:
    expected: set[tuple[str, str, str, int]] = set()
    for channel in ("stable", "beta"):
        previous: dict[str, object] | None = None
        for entry in synthetic_history:
            current = entry[channel]
            assert isinstance(current, dict)
            if previous is not None and previous != current:
                date = entry["date"]
                version = current["version"]
                percent = current["rollout_percent"]
                assert isinstance(date, str)
                assert isinstance(version, str) and isinstance(percent, int)
                expected.add((channel, date, version, percent))
            previous = current
    assert expected, "fixture must contain promotions"

    chart = _parse(rendered["adoption"])
    markers = {
        (
            attrs["data-channel"],
            attrs["data-date"],
            attrs["data-version"],
            int(attrs["data-rollout-percent"]),
        )
        for attrs in chart.attrs_by_tag.get("g", [])
        if attrs.get("class") == "promote-marker"
    }
    assert markers == expected

    log = _parse(rendered["promotions"])
    log_rows = {
        (
            attrs["data-channel"],
            attrs["data-date"],
            attrs["data-version"],
            int(attrs["data-rollout-percent"]),
        )
        for attrs in _attrs_with(log, "tr", "data-channel")
    }
    assert log_rows == expected


def test_render_labels_a_percent_bump_distinctly_from_a_version_promotion(
    rendered: dict[str, str],
) -> None:
    text = rendered["adoption"]
    assert "→" in text
    assert "% →" in text, "a rollout_percent bump must read as a percent transition"


def test_adoption_points_are_estimates_not_raw_counts(
    rendered: dict[str, str],
    synthetic_history: list[dict[str, object]],
) -> None:
    """The y axis is devices; its top tick must match the peak estimate."""
    intervals = _expected_intervals(synthetic_history)
    peak_raw = 0
    for interval in intervals:
        check_ins = interval["check_ins"]
        assert isinstance(check_ins, dict)
        for per_os in check_ins.values():
            total = sum(per_os.values())
            peak_raw = max(peak_raw, total)
    peak_devices = peak_raw / _EXPECTED_CHECKS_PER_DEVICE_PER_DAY

    assert "devices" in rendered["adoption"]
    axis_labels = [float(value) for value in re.findall(r">(\d+\.\d)</text>", rendered["adoption"])]
    assert axis_labels, "expected numeric y-axis ticks"
    assert (
        abs(max(axis_labels) - peak_devices) < 0.15
    ), f"top tick {max(axis_labels)} should be the peak estimate {peak_devices}"


def test_empty_history_renders_no_data_not_a_broken_chart(tmp_path: Path, page_source: str) -> None:
    rendered = _render(tmp_path, page_source, [])
    for key, markup in rendered.items():
        assert "No data yet." in markup, f"{key} lost its empty state"
        assert "<svg" not in markup, f"{key} drew a chart with no data"


@pytest.mark.parametrize(
    "malformed",
    [
        pytest.param({}, id="object-not-array"),
        pytest.param("nope", id="string"),
        pytest.param(None, id="null"),
        pytest.param([None, 3, "x"], id="junk-entries"),
        pytest.param([{"date": "2026-09-01"}], id="entry-missing-counts"),
        pytest.param([{"counts": {}}], id="entry-missing-date"),
        pytest.param(
            [{"date": "2026-09-01", "counts": {"x": "not-an-object"}}],
            id="counts-value-not-object",
        ),
    ],
)
def test_malformed_history_degrades_to_the_empty_state(
    tmp_path: Path, page_source: str, malformed: object
) -> None:
    rendered = _render(tmp_path, page_source, malformed)
    assert "No data yet." in rendered["composition"]
    assert "No data yet." in rendered["adoption"]


def test_single_snapshot_cannot_be_charted_and_says_so(
    tmp_path: Path, page_source: str, synthetic_history: list[dict[str, object]]
) -> None:
    """One cumulative reading carries no rate information.

    Charting it would present "every check-in since the counter started" as if
    it were one interval's traffic, inflating the fleet by however long the
    release has been out. The honest render is the empty state.
    """
    rendered = _render(tmp_path, page_source, synthetic_history[:1])
    assert "No data yet." in rendered["composition"]
    assert "No data yet." in rendered["adoption"]
    assert "No data yet." in rendered["promotions"], "one snapshot cannot hold a promotion"


def test_two_snapshots_produce_exactly_one_interval(
    tmp_path: Path, page_source: str, synthetic_history: list[dict[str, object]]
) -> None:
    rendered = _render(tmp_path, page_source, synthetic_history[:2])
    assert "<svg" in rendered["adoption"]
    assert "NaN" not in rendered["adoption"]
    chart = _parse(rendered["adoption"])
    for attrs in _attrs_with(chart, "polyline", "points"):
        assert len(attrs["points"].split()) == 1, "two snapshots is one plotted point"


def test_flat_counters_estimate_zero_devices_without_dividing_by_zero(
    tmp_path: Path, page_source: str
) -> None:
    """Cumulative counters that stop moving mean nobody checked in."""
    history = [
        {
            "date": "2026-09-01",
            "counts": {"9.9.9": {"linux-x86_64": 120}},
            "stable": {"version": "9.9.9", "rollout_percent": 0},
            "beta": {"version": "9.9.9", "rollout_percent": 0},
        },
        {
            "date": "2026-09-02",
            "counts": {"9.9.9": {"linux-x86_64": 120}},
            "stable": {"version": "9.9.9", "rollout_percent": 0},
            "beta": {"version": "9.9.9", "rollout_percent": 0},
        },
    ]
    rendered = _render(tmp_path, page_source, history)
    assert "NaN" not in rendered["adoption"]
    assert "Infinity" not in rendered["adoption"]
    # Zero movement in the only interval: nothing to compose.
    assert "No data yet." in rendered["composition"]


def test_a_counter_reset_is_clamped_and_disclosed(tmp_path: Path, page_source: str) -> None:
    """A re-cut release replaces its assets and the counter drops.

    A negative delta must not plot as a phantom dip, and the reader must be
    told it happened rather than left to wonder.
    """
    history = [
        {
            "date": "2026-09-01",
            "counts": {"9.9.9": {"linux-x86_64": 600}},
            "stable": {"version": "9.9.9", "rollout_percent": 100},
            "beta": {"version": "9.9.9", "rollout_percent": 100},
        },
        {
            "date": "2026-09-02",
            "counts": {"9.9.9": {"linux-x86_64": 12}},
            "stable": {"version": "9.9.9", "rollout_percent": 100},
            "beta": {"version": "9.9.9", "rollout_percent": 100},
        },
    ]
    rendered = _render(tmp_path, page_source, history)

    # The drop is clamped, never plotted as a negative.
    for markup in rendered.values():
        raw_counts = re.findall(r'data-check-ins="([^"]*)"', markup)
        assert all(int(value) >= 0 for value in raw_counts), f"negative delta plotted: {raw_counts}"

    # And it is disclosed to the reader in both charts.
    for key in ("composition", "adoption"):
        chart = _parse(rendered[key])
        anomalies = _attrs_with(chart, "p", "data-anomaly-count")
        assert anomalies, f"{key}: a counter reset must be disclosed on the page"
        assert int(anomalies[0]["data-anomaly-count"]) == 1
        assert "re-cut" in rendered[key]
        assert "9.9.9" in rendered[key], f"{key}: the note must name the affected version"


def test_history_is_sorted_by_date_before_rendering(
    tmp_path: Path, page_source: str, synthetic_history: list[dict[str, object]]
) -> None:
    shuffled = list(reversed(synthetic_history))
    from_shuffled = _render(tmp_path, page_source, shuffled)
    from_ordered = _render(tmp_path, page_source, synthetic_history)
    assert from_shuffled == from_ordered


def test_uneven_snapshot_spacing_scales_the_divisor(tmp_path: Path, page_source: str) -> None:
    """A missed cron run must not read as a doubled fleet.

    Two intervals with identical check-in counts but different lengths must
    produce different device estimates -- the four-day gap is four days of
    expected check-ins, not one.
    """
    history = [
        {
            "date": "2026-09-01",
            "counts": {"9.9.9": {"linux-x86_64": 0}},
            "stable": {"version": "9.9.9", "rollout_percent": 100},
            "beta": {"version": "9.9.9", "rollout_percent": 100},
        },
        {
            "date": "2026-09-02",
            "counts": {"9.9.9": {"linux-x86_64": 120}},
            "stable": {"version": "9.9.9", "rollout_percent": 100},
            "beta": {"version": "9.9.9", "rollout_percent": 100},
        },
        {
            "date": "2026-09-06",
            "counts": {"9.9.9": {"linux-x86_64": 240}},
            "stable": {"version": "9.9.9", "rollout_percent": 100},
            "beta": {"version": "9.9.9", "rollout_percent": 100},
        },
    ]
    rendered = _render(tmp_path, page_source, history)
    chart = _parse(rendered["composition"])
    bars = _attrs_with(chart, "g", "data-devices")
    assert len(bars) == 1
    # 120 check-ins over 4 days = 120 / (4 * 6) = 5 devices, not 20.
    assert abs(float(bars[0]["data-devices"]) - 5.0) < 0.05


def test_render_escapes_untrusted_strings(tmp_path: Path, page_source: str) -> None:
    payload = "<img src=x onerror=1>"
    history = [
        {
            "date": "2026-09-01",
            "counts": {payload: {"linux-x86_64": 0}},
            "stable": {"version": payload, "rollout_percent": 100},
            "beta": {"version": payload, "rollout_percent": 100},
        },
        {
            "date": "2026-09-02",
            "counts": {payload: {"linux-x86_64": 60}},
            "stable": {"version": payload, "rollout_percent": 100},
            "beta": {"version": payload, "rollout_percent": 100},
        },
    ]
    rendered = _render(tmp_path, page_source, history)
    for key, markup in rendered.items():
        assert "<img" not in markup, f"{key} emitted an unescaped tag"
    assert "&lt;img" in rendered["composition"]


def test_render_produces_parseable_markup_for_every_section(
    rendered: dict[str, str],
) -> None:
    """Each fragment must parse cleanly -- a malformed chart is a broken page."""
    for key, markup in rendered.items():
        collector = _parse(markup)
        assert collector.external_urls == [], f"{key} pulled in an external URL"
        assert collector.script_srcs == [], f"{key} injected a script tag"
