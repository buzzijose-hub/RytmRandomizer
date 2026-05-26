from __future__ import annotations

import json

import pytest

from rytm_randomizer import cli

pytestmark = pytest.mark.fast


def test_reference_style_blueprint_report_cli_description(capsys) -> None:
    exit_code = cli.main(
        [
            "reference-style-blueprint-report",
            "--description",
            "rolling metallic techno with heavy low end and sparse industrial percussion",
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 0
    assert "RytmRandomizer passive reference-style blueprint report" in captured.out
    assert "Analog Rytm pads: 12" in captured.out
    assert "Analog Four tracks: 4" in captured.out
    assert "BD Hard / low-end anchor" in captured.out
    assert "SY Raw / metallic texture" in captured.out
    assert "sub bass movement" in captured.out
    assert "no MIDI port opened" in captured.out
    assert captured.err == ""


def test_reference_style_blueprint_report_cli_json(capsys) -> None:
    exit_code = cli.main(
        [
            "reference-style-blueprint-report",
            "--description",
            "hypnotic industrial reference",
            "--json",
        ]
    )

    captured = capsys.readouterr()
    payload = json.loads(captured.out)

    assert exit_code == 0
    assert payload["readiness"] == "mock_safe_low_confidence"
    assert len(payload["rytm_pads"]) == 12
    assert len(payload["analog_four_tracks"]) == 4
    assert payload["safety"][1] == "no MIDI port opened"
    assert captured.err == ""


def test_reference_style_blueprint_report_cli_requires_one_source(capsys) -> None:
    exit_code = cli.main(["reference-style-blueprint-report"])

    captured = capsys.readouterr()

    assert exit_code == 2
    assert "requires exactly one source" in captured.err
    assert captured.out == ""


def test_reference_style_blueprint_report_cli_help(capsys) -> None:
    exit_code = cli.main(["reference-style-blueprint-report", "--help"])

    captured = capsys.readouterr()

    assert exit_code == 0
    assert "reference-style-blueprint-report" in captured.out
    assert "--description <text>" in captured.out
    assert "--audio <path>" in captured.out
    assert "--json" in captured.out
    assert "no MIDI sending" in captured.out
