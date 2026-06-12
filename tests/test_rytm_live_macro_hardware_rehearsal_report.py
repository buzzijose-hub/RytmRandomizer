from __future__ import annotations

import json

import pytest

pytestmark = pytest.mark.fast


def test_rytm_live_macro_hardware_rehearsal_report_lists_operator_workflow() -> None:
    from rytm_randomizer.reports.rytm_live_macro_hardware_rehearsal import (
        build_rytm_live_macro_hardware_rehearsal_report,
        format_rytm_live_macro_hardware_rehearsal_report,
    )

    report = build_rytm_live_macro_hardware_rehearsal_report()
    text = "\n".join(format_rytm_live_macro_hardware_rehearsal_report(report))

    assert report.title == "RytmRandomizer passive Rytm live macro hardware rehearsal"
    assert report.launch_command == (
        "python -m rytm_randomizer.app --arm --rytm-live-snapshot-shell "
        "--confirm-rytm-snapshot-shell-send"
    )
    assert [macro.name for macro in report.macros] == [
        "kit-core",
        "hard-groove",
        "industrial",
        "dub-pressure",
        "transition",
        "home",
    ]
    assert "Studio workflow:" in text
    assert "- Capture the current Rytm kit with KIT SysEx before changing anything." in text
    assert "- Run `changes` before `send` or `go`." in text
    assert "Pad lane checks:" in text
    assert "Pads 5, 9, 10, 11: SRC stays important" in text
    assert "Pads 6-8: tom/source movement" in text
    assert "Recovery checks:" in text
    assert "- `home` then `send` returns to the captured safe kit." in text
    assert "Safety:" in text
    assert "- passive/read-only report" in text


def test_rytm_live_macro_hardware_rehearsal_report_json_is_deterministic() -> None:
    from rytm_randomizer.reports.rytm_live_macro_hardware_rehearsal import (
        build_rytm_live_macro_hardware_rehearsal_payload,
    )

    payload = build_rytm_live_macro_hardware_rehearsal_payload()

    assert payload["title"] == "RytmRandomizer passive Rytm live macro hardware rehearsal"
    assert payload["launch_command"].startswith("python -m rytm_randomizer.app --arm")
    assert payload["macros"][0]["name"] == "kit-core"
    assert payload["macros"][0]["checkpoints"] == [
        "capture anchor first",
        "run changes before send",
        "listen for musicality",
        "recover with home",
    ]
    assert payload["macros"][-1]["name"] == "home"
    assert payload["pad_lane_checks"][0]["pads"] == [5, 9, 10, 11]
    assert payload["pad_lane_checks"][1]["pads"] == [6, 7, 8]
    assert payload["safety"] == [
        "passive/read-only report",
        "does not open MIDI ports",
        "does not send MIDI",
        "operator must run the armed shell manually",
    ]
    assert json.dumps(payload, sort_keys=True) == json.dumps(
        build_rytm_live_macro_hardware_rehearsal_payload(),
        sort_keys=True,
    )


def test_rytm_live_macro_hardware_rehearsal_cli_supports_json_and_text(
    capsys: pytest.CaptureFixture[str],
) -> None:
    from rytm_randomizer.reports.rytm_live_macro_hardware_rehearsal import (
        RYTM_LIVE_MACRO_HARDWARE_REHEARSAL_CLI_COMMAND,
    )

    assert RYTM_LIVE_MACRO_HARDWARE_REHEARSAL_CLI_COMMAND.args_parser([]) == {"json_output": False}
    assert RYTM_LIVE_MACRO_HARDWARE_REHEARSAL_CLI_COMMAND.args_parser(["--json"]) == {
        "json_output": True
    }
    with pytest.raises(ValueError, match="accepts only optional --json"):
        RYTM_LIVE_MACRO_HARDWARE_REHEARSAL_CLI_COMMAND.args_parser(["extra"])

    assert RYTM_LIVE_MACRO_HARDWARE_REHEARSAL_CLI_COMMAND.handler() == 0
    text = capsys.readouterr().out
    assert "RytmRandomizer passive Rytm live macro hardware rehearsal" in text
    assert "kit-core | live-safe | recovery=home" in text

    assert RYTM_LIVE_MACRO_HARDWARE_REHEARSAL_CLI_COMMAND.handler(json_output=True) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["macros"][1]["name"] == "hard-groove"
