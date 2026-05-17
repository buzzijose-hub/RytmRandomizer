import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_importing_analog_four_reference_is_passive_and_silent():
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import sys; "
                "import rytm_randomizer.analog_four_reference; "
                "assert 'mido' not in sys.modules; "
                "assert 'rtmidi' not in sys.modules"
            ),
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert result.stdout == ""
    assert result.stderr == ""


def test_reference_source_records_midi_guide_attribution():
    from rytm_randomizer.analog_four_reference import get_analog_four_reference_source

    source = get_analog_four_reference_source()

    assert source.device == "Elektron Analog Four MKII"
    assert source.url == "https://midi.guide/d/elektron/analog-four-mkii/"
    assert source.csv_history_url.endswith("Elektron/Analog%20Four%20MKII.csv")
    assert source.license == "Creative Commons Attribution Share Alike 4.0 International"
    assert source.last_update == "2026-03-26"
    assert source.parameter_count == 230


def test_track_roles_cover_four_a4_tracks_without_runtime_claims():
    from rytm_randomizer.analog_four_reference import list_analog_four_track_roles

    roles = list_analog_four_track_roles()

    assert tuple(role.track for role in roles) == (1, 2, 3, 4)
    assert tuple(role.key for role in roles) == (
        "bass_low_anchor",
        "stab_sequence_pressure",
        "drone_pad_atmosphere",
        "noise_fx_transition",
    )
    assert all(role.validation_status == "planning_only" for role in roles)


def test_reference_known_parameter_groups_capture_first_mutation_surface():
    from rytm_randomizer.analog_four_reference import list_analog_four_parameter_groups

    groups = {group.key: group for group in list_analog_four_parameter_groups()}

    assert groups["track_level"].parameters[0].name == "Track: Level"
    assert groups["track_level"].parameters[0].cc_msb == 95
    assert groups["track_level"].parameters[0].nrpn == (1, 100)

    osc_levels = {param.name: param for param in groups["oscillator_levels"].parameters}
    assert osc_levels["OSC1: Level"].cc_msb == 69
    assert osc_levels["OSC1: Level"].nrpn == (1, 4)
    assert osc_levels["OSC2: Level"].cc_msb == 78
    assert osc_levels["OSC2: Level"].nrpn == (1, 24)

    filter_params = {param.name: param for param in groups["filter_pressure"].parameters}
    assert filter_params["Filter 1: Frequency"].cc_msb == 18
    assert filter_params["Filter 1: Frequency"].cc_lsb == 50
    assert filter_params["Filter 1: Frequency"].nrpn == (1, 40)
    assert filter_params["Filter 2: Frequency"].cc_msb == 19
    assert filter_params["Filter 2: Frequency"].cc_lsb == 51
    assert filter_params["Filter 2: Frequency"].nrpn == (1, 45)

    assert groups["amp_envelope"].parameters[0].name == "Amp Env: Attack"
    assert groups["amp_envelope"].parameters[0].cc_msb == 104
    assert groups["lfo_motion"].parameters[0].name == "LFO1: Speed"
    assert groups["lfo_motion"].parameters[0].cc_msb == 116
    assert all(group.validation_status == "reference_known_mock_only" for group in groups.values())


def test_format_analog_four_reference_report_is_passive_and_actionable():
    from rytm_randomizer.analog_four_reference import format_analog_four_reference_report

    report = format_analog_four_reference_report()

    assert report[0] == "RytmRandomizer passive Analog Four MKII Reference Report"
    assert "Source: https://midi.guide/d/elektron/analog-four-mkii/" in report
    assert "Parameter count: 230" in report
    assert "License: Creative Commons Attribution Share Alike 4.0 International" in report
    assert "Track roles:" in report
    assert "- Track 1 / Bass / low tonal anchor: planning_only" in report
    assert "Reference-known starter groups:" in report
    assert any(line.startswith("- filter_pressure:") for line in report)
    assert "Blocked until next slices:" in report
    assert "- real Analog Four MIDI sending" in report
    assert "- no MIDI sending" in report
    assert "- no port opening" in report
