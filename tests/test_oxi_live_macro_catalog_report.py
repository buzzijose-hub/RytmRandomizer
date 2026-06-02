from __future__ import annotations

import pytest

pytestmark = pytest.mark.fast


def test_oxi_live_macro_catalog_report_lists_rytm_macros_and_a4_candidate_state() -> None:
    from rytm_randomizer.reports.oxi_live_macro_catalog import (
        build_oxi_live_macro_catalog_report,
        format_oxi_live_macro_catalog_report,
    )

    report = build_oxi_live_macro_catalog_report()
    text = "\n".join(format_oxi_live_macro_catalog_report(report))

    assert report.title == "RytmRandomizer OXI live macro catalog"
    assert [card.name for card in report.rytm_macros] == [
        "kit-core",
        "hard-groove",
        "industrial",
        "dub-pressure",
        "transition",
        "home",
    ]
    assert "Rytm macros:" in text
    assert "hard-groove | live-safe | recovery=home" in text
    assert "Analog Four runway: candidate-only" in text
    assert "blocked active actions: A4 outbound macro send" in text


def test_oxi_live_macro_catalog_json_is_deterministic() -> None:
    from rytm_randomizer.reports.oxi_live_macro_catalog import (
        build_oxi_live_macro_catalog_payload,
    )

    payload = build_oxi_live_macro_catalog_payload()

    assert payload["title"] == "RytmRandomizer OXI live macro catalog"
    assert payload["rytm_macros"][0]["name"] == "kit-core"
    assert payload["rytm_macros"][1]["affected_pads"] == [
        2,
        3,
        4,
        5,
        6,
        7,
        8,
        9,
        10,
        11,
        12,
    ]
    assert payload["analog_four"]["status"] == "candidate-only"
    assert payload["blocked_active_actions"] == ["A4 outbound macro send"]
