"""Tests for the ReportSpec platform core (Wave 2b, rival-program bundle).

Covers ``rytm_randomizer/reports/core.py`` plus the additive shared helpers
it rides on: ``reports.formatter.fingerprint_id`` /
``reports.formatter.require_nonblank`` and the registry-level promotions
``cli_registry.pop_option_value`` / ``cli_registry.format_cli_error``.

The helper tests pin behavior against the same inputs/outputs as the local
copies they will replace in Wave 3 (the dominant recipes frozen in
``tests/architecture/test_report_module_shape.py``), and against
``reports.live_gui_common`` for the verbatim registry promotions.
"""

from __future__ import annotations

import hashlib
import json

import pytest

from rytm_randomizer import cli_registry
from rytm_randomizer.reports import live_gui_common
from rytm_randomizer.reports.core import (
    ReportSection,
    ReportSpec,
    make_spec_command,
    render_report_lines,
    spec_payload,
)
from rytm_randomizer.reports.formatter import fingerprint_id, require_nonblank

pytestmark = pytest.mark.fast


def _demo_spec() -> ReportSpec:
    return ReportSpec(
        title="RytmRandomizer spec platform demo",
        source_module="reports.core",
        version="v1",
        cli_name="spec-platform-demo-report",
        summary="Demonstrate the ReportSpec house grammar.",
        safety_lines=("passive/read-only", "no MIDI sending"),
        sections=(
            ReportSection(heading="Alpha", rows=("row one", "row two")),
            ReportSection(heading="Empty"),
        ),
    )


# ---------------------------------------------------------------------------
# ReportSpec / ReportSection validation
# ---------------------------------------------------------------------------


def test_report_section_blank_heading_rejected() -> None:
    with pytest.raises(ValueError, match="heading must not be blank"):
        ReportSection(heading="   ")


def test_report_section_defaults_to_no_rows() -> None:
    assert ReportSection(heading="Alpha").rows == ()


@pytest.mark.parametrize(
    "field",
    ["title", "source_module", "version", "cli_name", "summary"],
)
def test_report_spec_blank_identity_fields_rejected(field: str) -> None:
    kwargs: dict[str, str] = {
        "title": "t",
        "source_module": "reports.core",
        "version": "v1",
        "cli_name": "c",
        "summary": "s",
    }
    kwargs[field] = "  "
    with pytest.raises(ValueError, match=f"{field} must not be blank"):
        ReportSpec(**kwargs)


def test_report_spec_is_frozen() -> None:
    spec = _demo_spec()
    with pytest.raises(AttributeError):
        spec.title = "other"  # type: ignore[misc]


# ---------------------------------------------------------------------------
# render_report_lines — house grammar
# ---------------------------------------------------------------------------


def test_render_report_lines_matches_house_grammar_exactly() -> None:
    assert render_report_lines(_demo_spec()) == [
        "RytmRandomizer spec platform demo",
        "Demonstrate the ReportSpec house grammar.",
        "Version: v1",
        "Alpha:",
        "- row one",
        "- row two",
        "Empty:",
        "- none",
        "Safety:",
        "- passive/read-only",
        "- no MIDI sending",
        "Source: rytm_randomizer.reports.core",
        "In-memory only: True",
    ]


def test_render_report_lines_without_sections_or_safety() -> None:
    spec = ReportSpec(
        title="Bare report",
        source_module="reports.core",
        version="v2",
        cli_name="bare-report",
        summary="No sections, no safety bullets.",
    )
    assert render_report_lines(spec) == [
        "Bare report",
        "No sections, no safety bullets.",
        "Version: v2",
        "Safety:",
        "Source: rytm_randomizer.reports.core",
        "In-memory only: True",
    ]


# ---------------------------------------------------------------------------
# spec_payload — canonical JSON envelope
# ---------------------------------------------------------------------------


def test_spec_payload_envelope() -> None:
    assert spec_payload(_demo_spec()) == {
        "title": "RytmRandomizer spec platform demo",
        "source_module": "reports.core",
        "version": "v1",
        "cli_name": "spec-platform-demo-report",
        "summary": "Demonstrate the ReportSpec house grammar.",
        "sections": {
            "Alpha": ["row one", "row two"],
            "Empty": [],
        },
        "safety": ["passive/read-only", "no MIDI sending"],
    }


def test_spec_payload_is_json_serializable() -> None:
    json.dumps(spec_payload(_demo_spec()), sort_keys=True)


# ---------------------------------------------------------------------------
# make_spec_command — delegation to make_passive_report_command
# ---------------------------------------------------------------------------


def test_make_spec_command_identity_and_parsing() -> None:
    command = make_spec_command(_demo_spec())
    assert command.name == "spec-platform-demo-report"
    assert command.summary == "Demonstrate the ReportSpec house grammar."
    assert command.args_parser([]) == {"json_output": False}
    assert command.args_parser(["--json"]) == {"json_output": True}
    with pytest.raises(ValueError, match="accepts only optional --json"):
        command.args_parser(["--bogus"])


def test_make_spec_command_text_output(capsys: pytest.CaptureFixture[str]) -> None:
    command = make_spec_command(_demo_spec())
    assert command.handler(**command.args_parser([])) == 0
    captured = capsys.readouterr()
    assert captured.out == "\n".join(render_report_lines(_demo_spec())) + "\n"


def test_make_spec_command_json_output(capsys: pytest.CaptureFixture[str]) -> None:
    command = make_spec_command(_demo_spec())
    assert command.handler(**command.args_parser(["--json"])) == 0
    captured = capsys.readouterr()
    expected = json.dumps(spec_payload(_demo_spec()), indent=2, sort_keys=True)
    assert captured.out == expected + "\n"


def test_make_spec_command_json_indent_none(capsys: pytest.CaptureFixture[str]) -> None:
    command = make_spec_command(_demo_spec(), json_indent=None)
    assert command.handler(json_output=True) == 0
    captured = capsys.readouterr()
    expected = json.dumps(spec_payload(_demo_spec()), indent=None, sort_keys=True)
    assert captured.out == expected + "\n"


def test_make_spec_command_without_json_flag() -> None:
    command = make_spec_command(_demo_spec(), json_flag=False)
    assert command.args_parser([]) == {}
    with pytest.raises(ValueError, match="does not accept arguments"):
        command.args_parser(["--json"])


def test_make_spec_command_error_formatter_is_passive_default() -> None:
    command = make_spec_command(_demo_spec())
    assert command.error_formatter is not None
    assert command.error_formatter(ValueError("boom")) == "Error: boom"


# ---------------------------------------------------------------------------
# formatter.fingerprint_id — pinned to the dominant local recipe
# ---------------------------------------------------------------------------


def test_fingerprint_id_matches_dominant_local_recipe() -> None:
    # The dominant local builder shape (e.g. live_gui_render_tree,
    # live_gui_capture_queue, live_gui_action_reducer):
    #   payload = "|".join(parts)
    #   hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]
    parts = ("render-tree-v1", "screen-a", "ready", "desktop", "compact")
    expected = hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()[:16]
    assert fingerprint_id(*parts) == expected


def test_fingerprint_id_single_and_zero_parts() -> None:
    assert fingerprint_id("solo") == hashlib.sha256(b"solo").hexdigest()[:16]
    assert fingerprint_id() == hashlib.sha256(b"").hexdigest()[:16]


def test_fingerprint_id_is_16_lowercase_hex_and_deterministic() -> None:
    value = fingerprint_id("a", "b")
    assert len(value) == 16
    assert value == value.lower()
    assert set(value) <= set("0123456789abcdef")
    assert value == fingerprint_id("a", "b")
    assert value != fingerprint_id("a", "c")


# ---------------------------------------------------------------------------
# formatter.require_nonblank — pinned to the dominant local validator
# ---------------------------------------------------------------------------


def test_require_nonblank_returns_stripped_value() -> None:
    assert require_nonblank("  kit-core  ", "label") == "kit-core"
    assert require_nonblank("plain", "label") == "plain"


@pytest.mark.parametrize("blank", ["", "   ", "\t\n"])
def test_require_nonblank_rejects_blank_with_house_message(blank: str) -> None:
    with pytest.raises(ValueError) as excinfo:
        require_nonblank(blank, "label")
    # Byte-identical to the local validators it replaces, e.g.
    # live_gui_render_tree._normalize_nonblank:
    #   raise ValueError(f"{field} must not be blank")
    assert str(excinfo.value) == "label must not be blank"


# ---------------------------------------------------------------------------
# cli_registry promotions — verbatim parity with reports.live_gui_common
# ---------------------------------------------------------------------------


def test_format_cli_error_matches_live_gui_common() -> None:
    exc = ValueError("bad option --pad")
    assert cli_registry.format_cli_error(exc) == "Error: bad option --pad"
    assert cli_registry.format_cli_error(exc) == live_gui_common.format_cli_error(exc)


def test_pop_option_value_pops_next_token() -> None:
    remaining = ["7", "--json"]
    assert cli_registry.pop_option_value(remaining, usage="usage text") == "7"
    assert remaining == ["--json"]


def test_pop_option_value_raises_usage_when_exhausted() -> None:
    with pytest.raises(ValueError, match="^usage text$"):
        cli_registry.pop_option_value([], usage="usage text")


def test_pop_option_value_matches_live_gui_common() -> None:
    promoted = cli_registry.pop_option_value(["x"], usage="u")
    legacy = live_gui_common.pop_option_value(["x"], usage="u")
    assert promoted == legacy
    with pytest.raises(ValueError) as promoted_exc:
        cli_registry.pop_option_value([], usage="the usage line")
    with pytest.raises(ValueError) as legacy_exc:
        live_gui_common.pop_option_value([], usage="the usage line")
    assert str(promoted_exc.value) == str(legacy_exc.value)
