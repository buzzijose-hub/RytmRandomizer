import json
import subprocess
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.fast

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_importing_analog_four_oxi_macro_report_prints_nothing():
    result = subprocess.run(
        [sys.executable, "-c", "import rytm_randomizer.reports.analog_four_oxi_macro_report"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert result.stdout == ""
    assert result.stderr == ""


def test_build_default_report_is_deterministic_and_four_track():
    from rytm_randomizer.reports.analog_four_oxi_macro_report import (
        build_analog_four_oxi_macro_report,
    )

    first = build_analog_four_oxi_macro_report(seed=11, intensity=5)
    second = build_analog_four_oxi_macro_report(seed=11, intensity=5)

    assert first == second
    assert first.macro_name == "hard-groove"
    assert first.track_count == 4
    assert first.event_count == len(first.events)
    assert first.mock_only is True
    assert first.hardware_required is False
    assert first.opens_ports is False
    assert first.sends_midi is False
    assert first.active_behavior is False
    assert {event.track for event in first.events} == {1, 2, 3, 4}
    assert all(0 <= event.value <= 127 for event in first.events)


def test_seed_changes_report_values_without_changing_shape():
    from rytm_randomizer.reports.analog_four_oxi_macro_report import (
        build_analog_four_oxi_macro_report,
    )

    first = build_analog_four_oxi_macro_report("dub-pressure", seed=4, intensity=6)
    second = build_analog_four_oxi_macro_report("dub-pressure", seed=5, intensity=6)

    assert first.macro_name == second.macro_name
    assert [event.parameter for event in first.events] == [
        event.parameter for event in second.events
    ]
    assert [event.value for event in first.events] != [event.value for event in second.events]


def test_report_rejects_unknown_macro_and_invalid_intensity():
    from rytm_randomizer.reports.analog_four_oxi_macro_report import (
        build_analog_four_oxi_macro_report,
    )

    with pytest.raises(ValueError, match="unknown Analog Four OXI macro"):
        build_analog_four_oxi_macro_report("ghost")

    with pytest.raises(ValueError, match="intensity must be between 0 and 7"):
        build_analog_four_oxi_macro_report(intensity=8)


def test_formatted_report_includes_safety_and_events():
    from rytm_randomizer.reports.analog_four_oxi_macro_report import (
        build_analog_four_oxi_macro_report,
        format_analog_four_oxi_macro_report,
    )

    report = build_analog_four_oxi_macro_report("industrial-transition", seed=2, intensity=7)
    output = "\n".join(format_analog_four_oxi_macro_report(report, include_events=True))

    assert output.startswith("RytmRandomizer passive Analog Four OXI macro report\n")
    assert "Macro: industrial-transition / Industrial Transition" in output
    assert "Tracks: 4" in output
    assert "Events:" in output
    assert "- Track 1" in output
    assert "- Track 4" in output
    assert "Safety:" in output
    assert "- passive/read-only" in output
    assert "- mock-only Analog Four OXI-style macro preview" in output
    assert "- no MIDI sending" in output
    assert "- no port opening" in output
    assert "- no hardware mutation" in output
    assert "Source: rytm_randomizer.reports.analog_four_oxi_macro_report" in output
    assert "In-memory only: True" in output


def test_json_report_is_deterministic_and_machine_readable():
    from rytm_randomizer.reports.analog_four_oxi_macro_report import (
        build_analog_four_oxi_macro_report,
        to_analog_four_oxi_macro_json,
    )

    report = build_analog_four_oxi_macro_report(seed=9, intensity=4)
    payload = to_analog_four_oxi_macro_json(report)
    encoded = json.dumps(payload, sort_keys=True)

    assert encoded == json.dumps(to_analog_four_oxi_macro_json(report), sort_keys=True)
    assert payload["macro_name"] == "hard-groove"
    assert payload["track_count"] == 4
    assert payload["mock_only"] is True
    assert payload["hardware_required"] is False
    assert payload["opens_ports"] is False
    assert payload["sends_midi"] is False
    assert payload["active_behavior"] is False
    assert payload["events"]
    assert payload["safety"]


def test_formatted_report_hides_events_by_default_and_can_truncate():
    from rytm_randomizer.reports.analog_four_oxi_macro_report import (
        build_analog_four_oxi_macro_report,
        format_analog_four_oxi_macro_report,
    )

    report = build_analog_four_oxi_macro_report("hard-groove", seed=7, intensity=4)

    hidden_output = "\n".join(format_analog_four_oxi_macro_report(report))
    assert "Shown events: 0" in hidden_output
    assert "Truncated events: 0" in hidden_output
    assert "- hidden; pass --events to show deterministic mock rows" in hidden_output

    truncated_output = "\n".join(
        format_analog_four_oxi_macro_report(
            report,
            include_events=True,
            event_limit=2,
        )
    )
    assert "Shown events: 2" in truncated_output
    assert f"Truncated events: {report.event_count - 2}" in truncated_output
    assert truncated_output.count("- Track ") == 2

    with pytest.raises(ValueError, match="event_limit must be >= 0"):
        format_analog_four_oxi_macro_report(
            report,
            include_events=True,
            event_limit=-1,
        )


def test_json_report_can_limit_events():
    from rytm_randomizer.reports.analog_four_oxi_macro_report import (
        build_analog_four_oxi_macro_report,
        to_analog_four_oxi_macro_json,
    )

    report = build_analog_four_oxi_macro_report("home", seed=1, intensity=3)

    payload = to_analog_four_oxi_macro_json(report, event_limit=3)

    assert payload["shown_count"] == 3
    assert payload["truncated_count"] == report.event_count - 3
    assert len(payload["events"]) == 3


def test_edge_event_paths_fail_safely(monkeypatch):
    import rytm_randomizer.reports.analog_four_oxi_macro_report as report_module
    from rytm_randomizer.data.analog_four_midi import AnalogFourCcMapping
    from rytm_randomizer.data.analog_four_oxi_macros import AnalogFourOxiMacroEventSpec
    from rytm_randomizer.reports.analog_four_oxi_macro_report import (
        _build_event,
        _event_value,
    )

    fixed_range_event = AnalogFourOxiMacroEventSpec(
        track=1,
        role="test",
        lane="fixed",
        parameter="OSC1 Level",
        value_min=42,
        value_max=42,
        intent="cover fixed ranges",
    )
    assert (
        _event_value(
            fixed_range_event,
            macro_name="home",
            seed=1,
            intensity=4,
            event_index=0,
        )
        == 42
    )

    nrpn_only_event = AnalogFourOxiMacroEventSpec(
        track=1,
        role="test",
        lane="nrpn-only",
        parameter="NRPN Only",
        value_min=0,
        value_max=127,
        intent="cover no-CC defensive path",
    )
    monkeypatch.setattr(
        report_module,
        "ANALOG_FOUR_SYNTH_TRACK_CC",
        {
            "NRPN Only": AnalogFourCcMapping(
                parameter="NRPN Only",
                section="TEST",
                encoder="A",
                cc_msb=None,
                cc_lsb=None,
                nrpn_msb=1,
                nrpn_lsb=1,
            )
        },
    )
    with pytest.raises(ValueError, match="has no CC MSB"):
        _build_event(
            nrpn_only_event,
            macro_name="home",
            seed=1,
            intensity=4,
            event_index=0,
        )


def test_cli_parser_accepts_options_and_rejects_bad_shapes():
    from rytm_randomizer.reports.analog_four_oxi_macro_report import (
        _parse_oxi_macro_cli_args,
    )

    parsed = _parse_oxi_macro_cli_args(
        [
            "home",
            "--events",
            "--json",
            "--seed",
            "4",
            "--intensity",
            "7",
            "--limit",
            "1",
        ]
    )

    assert parsed == {
        "macro_name": "home",
        "seed": 4,
        "intensity": 7,
        "include_events": True,
        "event_limit": 1,
        "json_output": True,
    }

    with pytest.raises(ValueError, match="analog-four-oxi-macro-report usage"):
        _parse_oxi_macro_cli_args(["--seed"])
    with pytest.raises(ValueError, match="--seed must be an integer"):
        _parse_oxi_macro_cli_args(["--seed", "abc"])
    with pytest.raises(ValueError, match="intensity must be between 0 and 7"):
        _parse_oxi_macro_cli_args(["--intensity", "8"])
    with pytest.raises(ValueError, match="--limit must be >= 0"):
        _parse_oxi_macro_cli_args(["--limit", "-1"])
    with pytest.raises(ValueError, match="analog-four-oxi-macro-report usage"):
        _parse_oxi_macro_cli_args(["--bogus"])
    with pytest.raises(ValueError, match="analog-four-oxi-macro-report usage"):
        _parse_oxi_macro_cli_args(["home", "hard-groove"])


def test_cli_handler_prints_text_json_and_errors(capsys):
    from rytm_randomizer.reports.analog_four_oxi_macro_report import (
        _format_oxi_macro_cli_error,
        _handle_oxi_macro_cli_report,
    )

    text_code = _handle_oxi_macro_cli_report(
        macro_name="home",
        seed=2,
        intensity=3,
        include_events=True,
        event_limit=1,
        json_output=False,
    )
    text_result = capsys.readouterr()
    assert text_code == 0
    assert "Macro: home / Home" in text_result.out
    assert "Shown events: 1" in text_result.out
    assert text_result.err == ""

    json_code = _handle_oxi_macro_cli_report(
        macro_name="home",
        seed=2,
        intensity=3,
        include_events=False,
        event_limit=1,
        json_output=True,
    )
    json_result = capsys.readouterr()
    assert json_code == 0
    assert json.loads(json_result.out)["shown_count"] == 1
    assert json_result.err == ""

    error_code = _handle_oxi_macro_cli_report(
        macro_name="ghost",
        seed=2,
        intensity=3,
        include_events=False,
        event_limit=1,
        json_output=False,
    )
    error_result = capsys.readouterr()
    assert error_code == 2
    assert error_result.out == ""
    assert "unknown Analog Four OXI macro" in error_result.err
    assert _format_oxi_macro_cli_error(ValueError("bad input")) == "Error: bad input"


def test_cli_command_imports_no_real_midi_modules():
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import sys; "
                "from rytm_randomizer.cli import main; "
                "code = main(['analog-four-oxi-macro-report']); "
                "print('RETURN', code); "
                "print('MIDO', 'mido' in sys.modules); "
                "print('RTMIDI', 'rtmidi' in sys.modules); "
                "print('REAL', 'rytm_randomizer.real_midi_adapter' in sys.modules); "
                "print('PROVIDER', 'rytm_randomizer.mido_provider' in sys.modules)"
            ),
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert "RETURN 0" in result.stdout
    assert "MIDO False" in result.stdout
    assert "RTMIDI False" in result.stdout
    assert "REAL False" in result.stdout
    assert "PROVIDER False" in result.stdout
    assert result.stderr == ""
