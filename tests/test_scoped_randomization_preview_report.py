"""Branch-complete tests for the scoped-randomization preview report/panel."""

from __future__ import annotations

import pytest

from rytm_randomizer.behavior import scope
from rytm_randomizer.reports import scoped_randomization_preview as srp
from rytm_randomizer.reports.core import render_report_lines, spec_payload

pytestmark = pytest.mark.fast


def test_demo_plan_is_ready_and_deterministic() -> None:
    plan = srp.build_demo_scope_plan()
    assert plan.ready is True
    assert plan.total_changed > 0
    assert plan == srp.build_demo_scope_plan()


def test_report_spec_shape() -> None:
    spec = srp.build_scope_report_spec()
    assert spec.cli_name == srp.CLI_NAME == "scoped-randomization-preview"
    assert spec.source_module == srp.SOURCE_MODULE
    assert spec.version == srp.REPORT_VERSION
    headings = [section.heading for section in spec.sections]
    assert headings == ["Mask", "Per-track deltas"]


def test_report_lines_render() -> None:
    lines = render_report_lines(srp.build_scope_report_spec())
    text = "\n".join(lines)
    assert srp.REPORT_TITLE in text
    assert "Per-track deltas:" in text
    assert "ready: True (ready)" in text
    assert "In-memory only: True" in text
    # Both a positive (+) and a negative (-) delta appear in the demo.
    assert any("(+" in line for line in lines)
    assert any("(-" in line for line in lines)


def test_report_payload_json_shape() -> None:
    payload = spec_payload(srp.build_scope_report_spec())
    assert payload["cli_name"] == "scoped-randomization-preview"
    assert "Mask" in payload["sections"]
    assert payload["safety"] == list(srp.SAFETY_LINES)


def test_panel_spec_shape() -> None:
    panel = srp.build_scope_panel_spec()
    assert panel["panel_id"] == srp.PANEL_ID
    assert panel["title"] == srp.REPORT_TITLE
    # version badge + ready badge
    tones = [b["tone"] for b in panel["status_badges"]]
    assert "neutral" in tones and "ok" in tones
    section_kinds = {s["heading"]: s["kind"] for s in panel["sections"]}
    assert section_kinds["Mask"] == "rows"
    assert section_kinds["Parameter deltas"] == "table"
    assert panel["safety_lines"] == list(srp.SAFETY_LINES)


def test_panel_delta_table_columns_and_signs() -> None:
    panel = srp.build_scope_panel_spec()
    table = next(s for s in panel["sections"] if s["heading"] == "Parameter deltas")
    assert table["table"]["columns"] == ["Pad", "Group", "Param", "Anchor", "Planned", "Delta"]
    signs = [row[-1] for row in table["table"]["rows"]]
    assert any(s.startswith("+") for s in signs)
    assert any(s.startswith("-") for s in signs)


def test_not_ready_badge_and_text_when_plan_empty(monkeypatch: pytest.MonkeyPatch) -> None:
    empty = scope.ScopePlan(
        depth=0.0,
        mask=scope.ScopeMask(tracks=frozenset(), groups=frozenset()),
        track_plans=(),
        ready=False,
        readiness_reason="no tracks selected",
    )
    monkeypatch.setattr(srp, "build_demo_scope_plan", lambda: empty)
    panel = srp.build_scope_panel_spec()
    warn = [b for b in panel["status_badges"] if b["tone"] == "warn"]
    assert warn and warn[0]["label"] == "no tracks selected"
    spec = srp.build_scope_report_spec()
    text = "\n".join(render_report_lines(spec))
    assert "ready: False (no tracks selected)" in text


def test_cli_command_registered() -> None:
    from rytm_randomizer import cli_registry

    assert srp.SCOPED_RANDOMIZATION_PREVIEW_CLI_COMMAND.name == "scoped-randomization-preview"
    # Importing the module registers it.
    assert cli_registry.get("scoped-randomization-preview") is not None
