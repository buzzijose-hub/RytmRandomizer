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
    assert "Live performance flow:" in text
    assert "capture-anchor | command=kit/resnapshot | send=receive-only" in text
    assert "home | command=home | send=restore-anchor" in text
    assert "Analog Four runway: candidate-only" in text
    assert "blocked active actions: A4 outbound macro send" in text


def test_oxi_live_macro_catalog_report_includes_performance_flow_contract() -> None:
    from rytm_randomizer.reports.oxi_live_macro_catalog import (
        build_oxi_live_macro_catalog_report,
    )

    report = build_oxi_live_macro_catalog_report()

    assert [step.command for step in report.performance_flow] == [
        "kit/resnapshot",
        "kit-core",
        "hard-groove",
        "industrial",
        "dub-pressure",
        "transition",
        "home",
    ]
    assert report.performance_flow[0].intent == "Capture the current Rytm kit as the safe anchor."
    assert report.performance_flow[-1].send_policy == "restore-anchor"
    assert report.performance_flow[-1].recovery_action == "captured-anchor"


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
    assert payload["performance_flow"][0] == {
        "order": 1,
        "name": "capture-anchor",
        "command": "kit/resnapshot",
        "send_policy": "receive-only",
        "recovery_action": "captured-anchor",
        "intent": "Capture the current Rytm kit as the safe anchor.",
    }
    assert payload["performance_flow"][-1]["name"] == "home"
    assert payload["performance_flow"][-1]["send_policy"] == "restore-anchor"
    assert payload["analog_four"]["status"] == "candidate-only"
    assert payload["blocked_active_actions"] == ["A4 outbound macro send"]


def test_oxi_live_macro_catalog_exposes_gui_ready_macro_policies() -> None:
    from rytm_randomizer.reports.oxi_live_macro_catalog import (
        build_oxi_live_macro_catalog_payload,
        build_oxi_live_macro_catalog_report,
        format_oxi_live_macro_catalog_report,
    )

    report = build_oxi_live_macro_catalog_report()
    payload = build_oxi_live_macro_catalog_payload()
    text = "\n".join(format_oxi_live_macro_catalog_report(report))

    kit_core = report.rytm_macros[0]
    assert kit_core.locked_pads == (1,)
    assert kit_core.lane_policies == {"fx": "micro", "lfo": "off"}
    assert kit_core.pad_policies[5] == {
        "amount": "normal",
        "density": "high",
        "bias": None,
        "lane_policies": {"filter": "off", "lfo": "off"},
        "section_family_allowlists": {"AMP": ["delay", "drive", "reverb"]},
    }
    assert kit_core.pad_policies[6]["lane_policies"] == {
        "filter": "micro",
        "lfo": "off",
    }
    assert kit_core.pad_policies[6]["section_family_allowlists"] == {
        "AMP": ["delay", "drive", "reverb"]
    }

    hard_groove = payload["rytm_macros"][1]
    assert hard_groove["locked_pads"] == [1]
    assert hard_groove["lane_policies"] == {"fx": "micro", "lfo": "off"}
    assert hard_groove["pad_policies"]["12"] == {
        "amount": "normal",
        "density": "medium",
        "bias": "neutral",
        "lane_policies": {},
        "section_family_allowlists": {"AMP": ["delay", "drive", "reverb"]},
    }
    assert "locked pads: 1" in text
    assert "global lanes: fx=micro, lfo=off" in text
    assert "pad 5: amount=normal, density=high, lanes=filter=off/lfo=off" in text


def test_oxi_live_macro_catalog_cli_command_rejects_args_and_writes_report(
    capsys,
) -> None:
    from rytm_randomizer.reports.oxi_live_macro_catalog import (
        OXI_LIVE_MACRO_CATALOG_CLI_COMMAND,
    )

    assert OXI_LIVE_MACRO_CATALOG_CLI_COMMAND.args_parser([]) == {}
    with pytest.raises(ValueError, match="does not accept arguments"):
        OXI_LIVE_MACRO_CATALOG_CLI_COMMAND.args_parser(["extra"])

    assert OXI_LIVE_MACRO_CATALOG_CLI_COMMAND.handler() == 0
    captured = capsys.readouterr()
    assert "RytmRandomizer OXI live macro catalog" in captured.out
    assert "A4 outbound macro send" in captured.out


def test_passive_report_cli_commands_reject_unexpected_arguments() -> None:
    from rytm_randomizer.reports import (
        ACTIVE_BOUNDARY_REPORT_CLI_COMMAND,
        MOCK_MAPPER_REPORT_CLI_COMMAND,
        RUNTIME_PLAN_REPORT_CLI_COMMAND,
    )

    for command in (
        MOCK_MAPPER_REPORT_CLI_COMMAND,
        RUNTIME_PLAN_REPORT_CLI_COMMAND,
        ACTIVE_BOUNDARY_REPORT_CLI_COMMAND,
    ):
        assert command.args_parser([]) == {}
        with pytest.raises(ValueError, match="does not accept arguments"):
            command.args_parser(["unexpected"])
