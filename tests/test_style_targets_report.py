import pytest

from rytm_randomizer.data.style_profiles import STYLE_PROFILES

pytestmark = pytest.mark.fast


def test_style_target_vectors_cover_every_style_profile():
    from rytm_randomizer.data.style_targets import STYLE_TARGET_VECTORS

    assert set(STYLE_TARGET_VECTORS) == set(STYLE_PROFILES)


def test_style_target_vector_axes_are_stable_and_bounded():
    from rytm_randomizer.data.style_targets import (
        STYLE_TARGET_VECTOR_AXES,
        STYLE_TARGET_VECTORS,
    )

    assert STYLE_TARGET_VECTOR_AXES == (
        "low_end_weight",
        "transient_density",
        "attack_sharpness",
        "decay_tail",
        "darkness",
        "metallicity",
        "noise_grit",
        "drive_pressure",
        "space_depth",
        "motion_amount",
        "repetition_hypnosis",
        "percussive_density",
        "tonal_center_weight",
        "industrial_edge",
        "minimal_restraint",
        "warehouse_intensity",
    )

    for key, vector in STYLE_TARGET_VECTORS.items():
        assert vector.key == key
        mapping = vector.as_mapping()
        assert tuple(mapping) == STYLE_TARGET_VECTOR_AXES
        for axis in STYLE_TARGET_VECTOR_AXES:
            assert 0 <= mapping[axis] <= 100


def test_style_target_vectors_encode_expected_musical_intent():
    from rytm_randomizer.data.style_targets import STYLE_TARGET_VECTORS

    birmingham = STYLE_TARGET_VECTORS["birmingham_pressure"]
    detroit = STYLE_TARGET_VECTORS["detroit_minimal"]
    industrial = STYLE_TARGET_VECTORS["industrial_dark"]
    hardgroove = STYLE_TARGET_VECTORS["hardgroove_percussive"]
    jose_core = STYLE_TARGET_VECTORS["jose_core_techno"]

    assert birmingham.drive_pressure >= 85
    assert industrial.noise_grit == 100
    assert hardgroove.percussive_density >= 85
    assert detroit.minimal_restraint >= 85
    assert detroit.space_depth < industrial.space_depth
    assert jose_core.drive_pressure >= 90
    assert jose_core.repetition_hypnosis >= 90
    assert jose_core.darkness >= 80
    assert jose_core.metallicity >= 75
    assert jose_core.industrial_edge >= 85
    assert jose_core.warehouse_intensity >= 90


def test_style_target_catalog_report_is_detached_from_source_mapping():
    from rytm_randomizer.data.style_targets import STYLE_TARGET_VECTORS
    from rytm_randomizer.reports.style_targets import (
        StyleTargetCatalogReport,
        build_style_target_catalog_report,
    )

    report = build_style_target_catalog_report()

    assert isinstance(report, StyleTargetCatalogReport)
    assert report.target_count == len(STYLE_TARGET_VECTORS)
    assert report.targets_by_key == STYLE_TARGET_VECTORS

    with pytest.raises(TypeError):
        report.targets_by_key["new_target"] = STYLE_TARGET_VECTORS["detroit_minimal"]


def test_style_target_report_formatter_is_sorted_and_passive():
    from rytm_randomizer.reports.style_targets import format_style_target_report

    lines = format_style_target_report()
    item_lines = [line for line in lines if line.startswith("- ") and ": " in line]

    assert lines[0] == "RytmRandomizer passive style target vector report"
    assert "- Purpose: numeric style intent for future snapshot mutation planning" in lines
    assert item_lines == sorted(item_lines)
    assert any(line.startswith("- birmingham_pressure:") for line in item_lines)
    assert "- no MIDI sending" in lines
    assert "- no hardware mutation" in lines


def test_style_target_inspection_is_case_insensitive_and_safe():
    from rytm_randomizer.reports.style_targets import format_style_target_inspection

    lines = format_style_target_inspection("INDUSTRIAL_DARK")

    assert lines[0] == "RytmRandomizer passive style target vector inspection"
    assert "Key: industrial_dark" in lines
    assert "Found: True" in lines
    assert "darkness: 100" in lines
    assert "noise_grit: 100" in lines
    assert "- no command execution" in lines


def test_style_target_inspection_unknown_key_reports_no_send_path():
    from rytm_randomizer.reports.style_targets import format_style_target_inspection

    lines = format_style_target_inspection("ghost_style")

    assert "Key: ghost_style" in lines
    assert "Found: False" in lines
    assert "Message: Style target not found. No MIDI was sent. No command executed." in lines
    assert "- no MIDI sending" in lines


def test_style_target_cli_command_parsers_accept_expected_arguments():
    from rytm_randomizer.reports.style_targets import (
        INSPECT_STYLE_TARGET_CLI_COMMAND,
        STYLE_TARGET_REPORT_CLI_COMMAND,
    )

    assert STYLE_TARGET_REPORT_CLI_COMMAND.args_parser([]) == {}
    assert INSPECT_STYLE_TARGET_CLI_COMMAND.args_parser(["detroit_minimal"]) == {
        "key": "detroit_minimal"
    }


@pytest.mark.parametrize(
    ("command_name", "argv", "message"),
    [
        ("STYLE_TARGET_REPORT_CLI_COMMAND", ["extra"], "command takes no arguments"),
        ("INSPECT_STYLE_TARGET_CLI_COMMAND", [], "command requires exactly one key"),
        (
            "INSPECT_STYLE_TARGET_CLI_COMMAND",
            ["one", "two"],
            "command requires exactly one key",
        ),
    ],
)
def test_style_target_cli_command_parsers_reject_bad_arguments(
    command_name,
    argv,
    message,
):
    import rytm_randomizer.reports.style_targets as style_targets

    command = getattr(style_targets, command_name)
    with pytest.raises(ValueError, match=message):
        command.args_parser(argv)


def test_style_target_report_handler_writes_stdout(capsys):
    from rytm_randomizer.reports.style_targets import STYLE_TARGET_REPORT_CLI_COMMAND

    assert STYLE_TARGET_REPORT_CLI_COMMAND.handler() == 0
    captured = capsys.readouterr()

    assert "RytmRandomizer passive style target vector report" in captured.out
    assert "- no MIDI sending" in captured.out
    assert captured.err == ""


def test_style_target_inspect_handler_routes_known_key_to_stdout(capsys):
    from rytm_randomizer.reports.style_targets import INSPECT_STYLE_TARGET_CLI_COMMAND

    kwargs = INSPECT_STYLE_TARGET_CLI_COMMAND.args_parser(["detroit_minimal"])

    assert INSPECT_STYLE_TARGET_CLI_COMMAND.handler(**kwargs) == 0
    captured = capsys.readouterr()

    assert "Found: True" in captured.out
    assert "minimal_restraint:" in captured.out
    assert captured.err == ""


def test_style_target_inspect_handler_routes_unknown_key_to_stderr(capsys):
    from rytm_randomizer.reports.style_targets import INSPECT_STYLE_TARGET_CLI_COMMAND

    kwargs = INSPECT_STYLE_TARGET_CLI_COMMAND.args_parser(["ghost_style"])

    assert INSPECT_STYLE_TARGET_CLI_COMMAND.handler(**kwargs) == 1
    captured = capsys.readouterr()

    assert captured.out == ""
    assert "Found: False" in captured.err
    assert "No MIDI was sent" in captured.err
