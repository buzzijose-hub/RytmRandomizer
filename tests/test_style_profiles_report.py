import pytest

from rytm_randomizer.data.style_profiles import STYLE_PROFILES
from rytm_randomizer.reports.style_profiles import (
    INSPECT_STYLE_PROFILE_CLI_COMMAND,
    LIST_STYLE_PROFILES_CLI_COMMAND,
    SEARCH_STYLE_PROFILES_CLI_COMMAND,
    STYLE_PROFILE_REPORT_CLI_COMMAND,
    StyleProfileCatalogReport,
    build_style_profile_catalog_report,
    format_style_profile_inspection,
    format_style_profile_list,
    format_style_profile_report,
    format_style_profile_search,
)

pytestmark = pytest.mark.fast


def test_style_profile_catalog_report_is_detached_from_source_mapping():
    report = build_style_profile_catalog_report()

    assert isinstance(report, StyleProfileCatalogReport)
    assert report.profile_count == len(STYLE_PROFILES)
    assert report.profiles_by_key == STYLE_PROFILES

    with pytest.raises(TypeError):
        report.profiles_by_key["new_profile"] = STYLE_PROFILES["detroit_minimal"]


def test_style_profile_report_help_resolves_in_process_with_safety_lines():
    from rytm_randomizer.help_text import resolve_help_text

    output = resolve_help_text("style-profile-report")

    assert "RytmRandomizer passive CLI: style-profile-report" in output
    assert "Prints the passive style-profile catalog for techno design intent." in output
    assert "  no MIDI sending" in output
    assert "  no port opening" in output


def test_style_profile_catalog_report_formatter_accepts_explicit_report():
    report = StyleProfileCatalogReport(
        profile_count=len(STYLE_PROFILES),
        profiles_by_key={"detroit_minimal": STYLE_PROFILES["detroit_minimal"]},
    )

    lines = format_style_profile_report(report)

    assert lines[0] == "RytmRandomizer passive style profile report"
    assert "- Profiles: " + str(len(STYLE_PROFILES)) in lines
    assert "detroit_minimal: Detroit Minimal" in lines
    assert all(line != "birmingham_pressure: Birmingham Pressure" for line in lines)
    assert "- no MIDI sending" in lines


def test_style_profile_list_formatter_is_sorted_and_passive():
    lines = format_style_profile_list()
    item_lines = [line for line in lines if line.startswith("- ") and ": " in line]

    assert lines[0] == "RytmRandomizer passive style profile list"
    assert lines.count("Items:") == 1
    assert item_lines == sorted(item_lines)
    assert any(line.startswith("- hardgroove_percussive:") for line in item_lines)
    assert "- no hardware mutation" in lines


def test_style_profile_inspection_is_case_insensitive_and_safe():
    lines = format_style_profile_inspection("BIRMINGHAM_PRESSURE")

    assert lines[0] == "RytmRandomizer passive style profile inspection"
    assert "Key: birmingham_pressure" in lines
    assert "Found: True" in lines
    assert "Name: Birmingham Pressure" in lines
    assert "Analog Four focus:" in lines
    assert "Analyzer hooks:" in lines
    assert "- no command execution" in lines


def test_style_profile_inspection_unknown_key_reports_no_send_path():
    lines = format_style_profile_inspection("ghost_style")

    assert "Key: ghost_style" in lines
    assert "Found: False" in lines
    assert "Message: Style profile not found. No MIDI was sent. No command executed." in lines
    assert "- no MIDI sending" in lines


def test_style_profile_search_matches_metadata_and_handles_empty_result():
    matching_lines = format_style_profile_search("hardgroove")
    missing_lines = format_style_profile_search("not-a-style")

    assert "Query: hardgroove" in matching_lines
    assert "Match count: 1" in matching_lines
    assert any(line.startswith("- hardgroove_percussive:") for line in matching_lines)
    assert "Query: not-a-style" in missing_lines
    assert "Match count: 0" in missing_lines
    assert "- no matches found. No MIDI was sent. No command executed." in missing_lines


def test_style_profile_cli_command_parsers_accept_expected_arguments():
    assert STYLE_PROFILE_REPORT_CLI_COMMAND.args_parser([]) == {}
    assert LIST_STYLE_PROFILES_CLI_COMMAND.args_parser([]) == {}
    assert INSPECT_STYLE_PROFILE_CLI_COMMAND.args_parser(["detroit_minimal"]) == {
        "key": "detroit_minimal"
    }
    assert SEARCH_STYLE_PROFILES_CLI_COMMAND.args_parser(["dark"]) == {"query": "dark"}


@pytest.mark.parametrize(
    ("command", "argv", "message"),
    [
        (
            STYLE_PROFILE_REPORT_CLI_COMMAND,
            ["extra"],
            "style-profile-report does not accept arguments",
        ),
        (
            LIST_STYLE_PROFILES_CLI_COMMAND,
            ["extra"],
            "list-style-profiles does not accept arguments",
        ),
        (INSPECT_STYLE_PROFILE_CLI_COMMAND, [], "command requires exactly one key"),
        (
            INSPECT_STYLE_PROFILE_CLI_COMMAND,
            ["one", "two"],
            "command requires exactly one key",
        ),
        (SEARCH_STYLE_PROFILES_CLI_COMMAND, [], "command requires exactly one query"),
        (
            SEARCH_STYLE_PROFILES_CLI_COMMAND,
            ["one", "two"],
            "command requires exactly one query",
        ),
    ],
)
def test_style_profile_cli_command_parsers_reject_bad_arguments(command, argv, message):
    with pytest.raises(ValueError, match=message):
        command.args_parser(argv)


@pytest.mark.parametrize(
    "command",
    [
        STYLE_PROFILE_REPORT_CLI_COMMAND,
        LIST_STYLE_PROFILES_CLI_COMMAND,
        SEARCH_STYLE_PROFILES_CLI_COMMAND,
    ],
)
def test_style_profile_cli_command_handlers_write_stdout(command, capsys):
    kwargs = command.args_parser(["dark"] if command is SEARCH_STYLE_PROFILES_CLI_COMMAND else [])

    assert command.handler(**kwargs) == 0
    captured = capsys.readouterr()

    assert "RytmRandomizer passive style profile" in captured.out
    assert "- no MIDI sending" in captured.out
    assert captured.err == ""


def test_style_profile_inspect_handler_routes_known_key_to_stdout(capsys):
    kwargs = INSPECT_STYLE_PROFILE_CLI_COMMAND.args_parser(["detroit_minimal"])

    assert INSPECT_STYLE_PROFILE_CLI_COMMAND.handler(**kwargs) == 0
    captured = capsys.readouterr()

    assert "Found: True" in captured.out
    assert "Name: Detroit Minimal" in captured.out
    assert captured.err == ""


def test_style_profile_inspect_handler_routes_unknown_key_to_stderr(capsys):
    kwargs = INSPECT_STYLE_PROFILE_CLI_COMMAND.args_parser(["ghost_style"])

    assert INSPECT_STYLE_PROFILE_CLI_COMMAND.handler(**kwargs) == 1
    captured = capsys.readouterr()

    assert captured.out == ""
    assert "Found: False" in captured.err
    assert "No MIDI was sent" in captured.err
