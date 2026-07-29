"""Tests for the PanelSpec vocabulary (``rytm_randomizer/reports/panel_spec.py``).

Pins the JSON shapes the generated TypeScript interfaces mirror
(``desktop/web/src/types/live_gui_protocol.ts``) and the
``panel_spec_from_report_spec`` bridge that lets one ``ReportSpec`` feed both
the passive text report and the cockpit panel.
"""

from __future__ import annotations

import json
from typing import Literal, cast

import pytest

from rytm_randomizer.reports.core import ReportSection, ReportSpec
from rytm_randomizer.reports.panel_spec import (
    BADGE_TONES,
    PANEL_SPEC_VERSION,
    SECTION_KINDS,
    badge,
    chips_section,
    panel_spec,
    panel_spec_from_report_spec,
    rows_section,
    table_section,
)

pytestmark = pytest.mark.fast

_BadgeTone = Literal["ok", "warn", "risk", "neutral"]


def _demo_report_spec() -> ReportSpec:
    return ReportSpec(
        title="RytmRandomizer panel platform demo",
        source_module="reports.panel_spec",
        version="v1",
        cli_name="panel-platform-demo-report",
        summary="Demonstrate the PanelSpec bridge.",
        safety_lines=("passive/read-only", "no MIDI sending"),
        sections=(
            ReportSection(heading="Alpha", rows=("row one", "row two")),
            ReportSection(heading="Empty"),
        ),
    )


# ---------------------------------------------------------------------------
# Vocabulary constants
# ---------------------------------------------------------------------------


def test_vocabulary_constants_are_closed() -> None:
    assert PANEL_SPEC_VERSION == "cockpit-panel-spec-v1"
    assert BADGE_TONES == ("ok", "warn", "risk", "neutral")
    assert SECTION_KINDS == ("rows", "table", "chips")


# ---------------------------------------------------------------------------
# badge
# ---------------------------------------------------------------------------


def test_badge_defaults_to_neutral_tone_with_empty_icon() -> None:
    assert badge("  passive  ") == {"label": "passive", "tone": "neutral", "icon": ""}


def test_badge_accepts_every_documented_tone() -> None:
    for tone in BADGE_TONES:
        built = badge("state", tone=cast(_BadgeTone, tone), icon="+")
        assert built == {"label": "state", "tone": tone, "icon": "+"}


def test_badge_rejects_unknown_tone() -> None:
    with pytest.raises(ValueError, match="tone must be one of"):
        badge("state", tone=cast(_BadgeTone, "loud"))


def test_badge_rejects_blank_label() -> None:
    with pytest.raises(ValueError, match="label must not be blank"):
        badge("   ")


# ---------------------------------------------------------------------------
# Sections
# ---------------------------------------------------------------------------


def test_rows_section_shape_and_default() -> None:
    assert rows_section("Alpha", ("one", "two")) == {
        "heading": "Alpha",
        "kind": "rows",
        "rows": ["one", "two"],
        "table": None,
        "chips": [],
    }
    assert rows_section("Empty")["rows"] == []


def test_rows_section_rejects_blank_heading() -> None:
    with pytest.raises(ValueError, match="heading must not be blank"):
        rows_section("  ")


def test_table_section_shape_and_default() -> None:
    assert table_section(
        "Spectrum",
        columns=("Band", "Level"),
        rows=(("Low", "0%"), ("High", "50%")),
    ) == {
        "heading": "Spectrum",
        "kind": "table",
        "rows": [],
        "table": {
            "columns": ["Band", "Level"],
            "rows": [["Low", "0%"], ["High", "50%"]],
        },
        "chips": [],
    }
    assert table_section("Bare", columns=("Only",))["table"] == {
        "columns": ["Only"],
        "rows": [],
    }


def test_table_section_rejects_empty_columns() -> None:
    with pytest.raises(ValueError, match="at least one column"):
        table_section("Spectrum", columns=())


def test_table_section_rejects_blank_column() -> None:
    with pytest.raises(ValueError, match="column must not be blank"):
        table_section("Spectrum", columns=("Band", " "))


def test_table_section_rejects_ragged_row() -> None:
    with pytest.raises(ValueError, match="expected 2"):
        table_section("Spectrum", columns=("Band", "Level"), rows=(("Low",),))


def test_table_section_rejects_blank_heading() -> None:
    with pytest.raises(ValueError, match="heading must not be blank"):
        table_section("  ", columns=("Band",))


def test_chips_section_shape_and_default() -> None:
    assert chips_section("Controls", ("preview", "dry-run")) == {
        "heading": "Controls",
        "kind": "chips",
        "rows": [],
        "table": None,
        "chips": ["preview", "dry-run"],
    }
    assert chips_section("Empty")["chips"] == []


def test_chips_section_rejects_blank_heading() -> None:
    with pytest.raises(ValueError, match="heading must not be blank"):
        chips_section("")


# ---------------------------------------------------------------------------
# panel_spec
# ---------------------------------------------------------------------------


def test_panel_spec_full_shape() -> None:
    spec = panel_spec(
        "analyzer",
        "Analyzer (Post-Mutation Preview)",
        status_badges=(badge("empty", tone="warn"),),
        sections=(rows_section("Reference", ("No reference loaded",)),),
        required_actions=("load-reference",),
        blocked_actions=("send-midi",),
        safety_lines=("passive",),
    )
    assert spec == {
        "panel_id": "analyzer",
        "title": "Analyzer (Post-Mutation Preview)",
        "status_badges": [{"label": "empty", "tone": "warn", "icon": ""}],
        "sections": [
            {
                "heading": "Reference",
                "kind": "rows",
                "rows": ["No reference loaded"],
                "table": None,
                "chips": [],
            }
        ],
        "required_actions": ["load-reference"],
        "blocked_actions": ["send-midi"],
        "safety_lines": ["passive"],
    }


def test_panel_spec_defaults_are_empty_lists() -> None:
    spec = panel_spec("bare", "Bare Panel")
    assert spec == {
        "panel_id": "bare",
        "title": "Bare Panel",
        "status_badges": [],
        "sections": [],
        "required_actions": [],
        "blocked_actions": [],
        "safety_lines": [],
    }


def test_panel_spec_rejects_blank_identity_fields() -> None:
    with pytest.raises(ValueError, match="panel_id must not be blank"):
        panel_spec(" ", "Title")
    with pytest.raises(ValueError, match="title must not be blank"):
        panel_spec("panel", " ")


def test_panel_spec_is_json_serializable() -> None:
    json.dumps(
        panel_spec(
            "roundtrip",
            "Roundtrip",
            sections=(
                table_section("T", columns=("A",), rows=(("1",),)),
                chips_section("C", ("x",)),
            ),
        ),
        sort_keys=True,
    )


# ---------------------------------------------------------------------------
# panel_spec_from_report_spec — one spec, both surfaces
# ---------------------------------------------------------------------------


def test_panel_spec_from_report_spec_defaults() -> None:
    assert panel_spec_from_report_spec(_demo_report_spec()) == {
        "panel_id": "panel-platform-demo-report",
        "title": "RytmRandomizer panel platform demo",
        "status_badges": [{"label": "v1", "tone": "neutral", "icon": "i"}],
        "sections": [
            {
                "heading": "Summary",
                "kind": "rows",
                "rows": ["Demonstrate the PanelSpec bridge."],
                "table": None,
                "chips": [],
            },
            {
                "heading": "Alpha",
                "kind": "rows",
                "rows": ["row one", "row two"],
                "table": None,
                "chips": [],
            },
            {
                "heading": "Empty",
                "kind": "rows",
                "rows": [],
                "table": None,
                "chips": [],
            },
        ],
        "required_actions": [],
        "blocked_actions": [],
        "safety_lines": ["passive/read-only", "no MIDI sending"],
    }


def test_panel_spec_from_report_spec_overrides() -> None:
    built = panel_spec_from_report_spec(
        _demo_report_spec(),
        panel_id="custom-panel",
        status_badges=(badge("ready", tone="ok", icon="+"),),
        required_actions=("review",),
        blocked_actions=("send-midi",),
    )
    assert built["panel_id"] == "custom-panel"
    assert built["status_badges"] == [{"label": "ready", "tone": "ok", "icon": "+"}]
    assert built["required_actions"] == ["review"]
    assert built["blocked_actions"] == ["send-midi"]


def test_panel_spec_from_report_spec_shares_section_content_with_report_lines() -> None:
    # The same ReportSpec feeds both surfaces: every section heading and row
    # rendered into the passive report also lands in the panel sections.
    from rytm_randomizer.reports.core import render_report_lines

    spec = _demo_report_spec()
    lines = render_report_lines(spec)
    panel = panel_spec_from_report_spec(spec)
    for section in spec.sections:
        assert f"{section.heading}:" in lines
        panel_rows = [
            built["rows"] for built in panel["sections"] if built["heading"] == section.heading
        ]
        assert panel_rows == [list(section.rows)]
    assert panel["safety_lines"] == list(spec.safety_lines)
