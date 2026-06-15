from __future__ import annotations

import json

import pytest

pytestmark = pytest.mark.fast


def test_controller_mapping_report_text_mentions_pages_and_safety() -> None:
    from rytm_randomizer.reports.controller_mapping_profile_catalog import (
        build_controller_mapping_profile_report,
        format_controller_mapping_profile_report,
    )

    report = build_controller_mapping_profile_report()
    text = "\n".join(format_controller_mapping_profile_report(report))

    assert report.title == "RytmRandomizer passive controller brain mapping report"
    assert "Controller profile: generic-16-encoder-performance" in text
    assert "Page 1: Global Brain" in text
    assert "Page 4: Rytm Pads 9-12" in text
    assert "open MIDI controller input" in text
    assert "Source: rytm_randomizer.reports.controller_mapping_profile_catalog" in text


def test_controller_mapping_report_json_is_deterministic() -> None:
    from rytm_randomizer.reports.controller_mapping_profile_catalog import (
        build_controller_mapping_profile_payload,
    )

    payload = build_controller_mapping_profile_payload()
    encoded = json.dumps(payload, sort_keys=True)

    assert encoded == json.dumps(build_controller_mapping_profile_payload(), sort_keys=True)
    assert payload["profile_key"] == "generic-16-encoder-performance"
    assert len(payload["pages"]) == 7
    assert payload["pages"][0]["controls"][0]["intent_key"] == "global.preview_depth"
    assert payload["pages"][3]["controls"][-1]["target_scope"] == "rytm_pad_12"
    assert payload["safety"]["sends_midi"] is False
    assert payload["safety"]["opens_ports"] is False
    assert payload["blocked_active_actions"]


def test_controller_mapping_report_has_no_raw_midi_controller_fields() -> None:
    from rytm_randomizer.reports.controller_mapping_profile_catalog import (
        build_controller_mapping_profile_payload,
    )

    payload = build_controller_mapping_profile_payload()

    controls = [control for page in payload["pages"] for control in page["controls"]]
    forbidden_keys = {"midi_cc", "cc", "channel", "port", "controller_port"}
    assert all(forbidden_keys.isdisjoint(control) for control in controls)
    assert {control["target_device"] for control in controls} >= {
        "analog_rytm_mk2",
        "analog_four_mk2",
        "style_queue",
        "snapshot_recovery",
    }


def test_controller_mapping_report_cli_supports_text_and_json(capsys) -> None:
    from rytm_randomizer.reports.controller_mapping_profile_catalog import (
        CONTROLLER_MAPPING_PROFILE_CATALOG_CLI_COMMAND,
    )

    assert CONTROLLER_MAPPING_PROFILE_CATALOG_CLI_COMMAND.args_parser([]) == {"json_output": False}
    assert CONTROLLER_MAPPING_PROFILE_CATALOG_CLI_COMMAND.args_parser(["--json"]) == {
        "json_output": True
    }
    with pytest.raises(ValueError, match="accepts only optional --json"):
        CONTROLLER_MAPPING_PROFILE_CATALOG_CLI_COMMAND.args_parser(["extra"])

    assert CONTROLLER_MAPPING_PROFILE_CATALOG_CLI_COMMAND.handler() == 0
    text_output = capsys.readouterr().out
    assert "RytmRandomizer passive controller brain mapping report" in text_output

    assert CONTROLLER_MAPPING_PROFILE_CATALOG_CLI_COMMAND.handler(json_output=True) == 0
    json_output = capsys.readouterr().out
    assert json.loads(json_output)["profile_key"] == "generic-16-encoder-performance"
