"""Branch-complete tests for the kit-morph preview report/panel."""

from __future__ import annotations

import pytest

from rytm_randomizer.behavior import morph
from rytm_randomizer.reports import kit_morph_preview as kmp
from rytm_randomizer.reports.core import render_report_lines, spec_payload

pytestmark = pytest.mark.fast


def test_demo_plan_is_ready_and_deterministic() -> None:
    plan = kmp.build_demo_morph_plan()
    assert plan.ready is True
    assert plan.total_moved > 0
    assert plan == kmp.build_demo_morph_plan()


def test_report_spec_shape() -> None:
    spec = kmp.build_morph_report_spec()
    assert spec.cli_name == kmp.CLI_NAME == "kit-morph-preview"
    assert spec.source_module == kmp.SOURCE_MODULE
    headings = [section.heading for section in spec.sections]
    assert headings == ["Morph", "Per-track interpolation"]


def test_report_lines_render_with_linear_and_unmatched() -> None:
    lines = render_report_lines(kmp.build_morph_report_spec())
    text = "\n".join(lines)
    assert kmp.REPORT_TITLE in text
    assert "Per-track interpolation:" in text
    assert "[linear]" in text
    # The demo (sharp -> classic, src+filter) leaves SRC Hold Time unmatched.
    assert "unmatched (not morphed):" in text


def test_report_payload_json_shape() -> None:
    payload = spec_payload(kmp.build_morph_report_spec())
    assert payload["cli_name"] == "kit-morph-preview"
    assert "Morph" in payload["sections"]
    assert payload["safety"] == list(kmp.SAFETY_LINES)


def test_panel_spec_shape() -> None:
    panel = kmp.build_morph_panel_spec()
    assert panel["panel_id"] == kmp.PANEL_ID
    section_kinds = {s["heading"]: s["kind"] for s in panel["sections"]}
    assert section_kinds["Morph"] == "rows"
    assert section_kinds["Interpolation"] == "table"
    table = next(s for s in panel["sections"] if s["heading"] == "Interpolation")
    assert table["table"]["columns"] == [
        "Pad",
        "Group",
        "Param",
        "Kind",
        "Source",
        "Target",
        "Interp",
    ]


def test_panel_table_includes_linear_kind() -> None:
    panel = kmp.build_morph_panel_spec()
    table = next(s for s in panel["sections"] if s["heading"] == "Interpolation")
    kinds = {row[3] for row in table["table"]["rows"]}
    assert "linear" in kinds


def test_discrete_kind_rendered(monkeypatch: pytest.MonkeyPatch) -> None:
    # Force a plan whose only param is a discrete selector so the "discrete"
    # kind label branch is exercised in both the report and panel renderers.
    track = morph.MorphTrack(
        track=1,
        source_name="S",
        target_name="T",
        source={"SRC Waveform": 0},
        target={"SRC Waveform": 3},
        groups={"osc": ("SRC Waveform",)},
    )
    plan = morph.plan_morph([track], frozenset({"osc"}), 0.5)
    monkeypatch.setattr(kmp, "build_demo_morph_plan", lambda: plan)
    report_text = "\n".join(render_report_lines(kmp.build_morph_report_spec()))
    assert "[discrete]" in report_text
    panel = kmp.build_morph_panel_spec()
    table = next(s for s in panel["sections"] if s["heading"] == "Interpolation")
    assert any(row[3] == "discrete" for row in table["table"]["rows"])


def test_not_ready_badge_when_plan_empty(monkeypatch: pytest.MonkeyPatch) -> None:
    empty = morph.MorphPlan(
        amount=0.0,
        groups=frozenset(),
        track_plans=(),
        ready=False,
        readiness_reason="no parameter groups selected",
    )
    monkeypatch.setattr(kmp, "build_demo_morph_plan", lambda: empty)
    panel = kmp.build_morph_panel_spec()
    warn = [b for b in panel["status_badges"] if b["tone"] == "warn"]
    assert warn and warn[0]["label"] == "no parameter groups selected"


def test_cli_command_registered() -> None:
    from rytm_randomizer import cli_registry

    assert kmp.KIT_MORPH_PREVIEW_CLI_COMMAND.name == "kit-morph-preview"
    assert cli_registry.get("kit-morph-preview") is not None
