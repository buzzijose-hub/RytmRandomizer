"""Tests for the passive Analog Four patch send-plan report."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from rytm_randomizer.guardrails.schema import Confidence, SourceType
from rytm_randomizer.style_analysis import FeatureReport

pytestmark = pytest.mark.fast

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _feature_report() -> FeatureReport:
    return FeatureReport(
        source_type=SourceType.SINGLE_TRACK,
        confidence=Confidence.HIGH,
        bpm=134.0,
        tempo_stability=0.9,
        kick_density=0.4,
        percussion_density=0.7,
        low_end_weight=0.35,
        spectral_brightness=0.62,
        texture_noise=0.3,
        energy_arc=(0.1, 0.2, 0.4, 0.6, 0.7, 0.6, 0.4, 0.2),
        content_hash="",
        derived_at="2026-07-03T12:00:00Z",
    )


def test_importing_patch_send_plan_report_prints_nothing() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "import rytm_randomizer.reports.analog_four_patch_send_plan",
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert result.stdout == ""
    assert result.stderr == ""


def test_patch_send_plan_report_text_shows_sendable_and_manual_rows() -> None:
    from rytm_randomizer.reports.analog_four_patch_send_plan import (
        build_analog_four_patch_send_plan_report_from_source,
        format_analog_four_patch_send_plan_report,
    )

    report = build_analog_four_patch_send_plan_report_from_source(
        "--description",
        "hypnotic metallic techno with bright sync stab and compact envelope",
        track=1,
        selected_candidate=1,
    )
    text = "\n".join(format_analog_four_patch_send_plan_report(report))

    assert text.startswith("RytmRandomizer passive Analog Four patch send plan\n")
    assert "Selected candidate: 1 / Closest reference" in text
    assert "Live dial path: partial-live-dial-ready" in text
    assert "Sendable events: 26 / 39 (67%)" in text
    assert "Transport messages: 34" in text
    assert "Sendable MIDI events:" in text
    assert "01 T1 ch0 CC69 OSC1 Level -> 96" in text
    assert "10 T1 ch0 NRPN 1:54 EnvA Env Shape -> 0" in text
    assert "Manual/front-panel rows:" in text
    assert "18 T1 EnvF Depth A" in text
    assert "paired CC LSB conversion not hardware-verified" in text
    assert (
        "16 T1 EnvF Gate Length | screen NOTE | skipped | physical A4 rehearsal "
        "disproved the inferred enum ordinal"
    ) in text
    assert (
        "25 T1 LFO1 Destination A | screen Filter1 Frequency | skipped | physical "
        "A4 rehearsal disproved the inferred enum ordinal"
    ) in text
    assert "- no MIDI port opened" in text
    assert "- no MIDI sent" in text


def test_patch_send_plan_report_builds_from_feature_report_directly() -> None:
    from rytm_randomizer.reports.analog_four_patch_send_plan import (
        build_analog_four_patch_send_plan_report,
    )

    report = build_analog_four_patch_send_plan_report(
        _feature_report(),
        source_label="description",
        source_value="manual feature report",
        track=2,
        selected_candidate=2,
    )

    assert report.source_label == "description"
    assert report.source_value == "manual feature report"
    assert report.plan.selected_track == 2
    assert report.plan.selected_label == "Brighter sync"


def test_patch_send_plan_report_audio_source_uses_audio_genome_inference(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from rytm_randomizer.reports import analog_four_patch_send_plan as report_module
    from rytm_randomizer.style_analysis import analog_four_patch_send_plan as send_plan_module
    from rytm_randomizer.style_analysis.analog_four_patch_genome import (
        build_analog_four_patch_genome,
    )

    observed_paths: list[Path] = []

    def _fake_build_audio_genome(path: Path, *, track: int) -> object:
        observed_paths.append(path)
        feature_report = _feature_report()
        return SimpleNamespace(
            feature_report=feature_report,
            genome=build_analog_four_patch_genome(feature_report, track=track),
        )

    monkeypatch.setattr(
        send_plan_module,
        "build_analog_four_audio_patch_genome_isolated",
        _fake_build_audio_genome,
    )

    report = report_module.build_analog_four_patch_send_plan_report_from_source(
        "--audio",
        "reference.wav",
        track=4,
        selected_candidate=3,
    )

    assert observed_paths == [Path("reference.wav")]
    assert report.source_label == "audio"
    assert report.plan.selected_track == 4
    assert report.plan.selected_label == "Noisy texture"


def test_patch_send_plan_report_rejects_unknown_source() -> None:
    from rytm_randomizer.reports.analog_four_patch_send_plan import (
        build_analog_four_patch_send_plan_report_from_source,
    )

    with pytest.raises(ValueError, match="source_flag must be"):
        build_analog_four_patch_send_plan_report_from_source(
            "--library",
            "reference-folder",
            track=1,
            selected_candidate=1,
        )


def test_patch_send_plan_report_json_includes_summary_and_events() -> None:
    from rytm_randomizer.reports.analog_four_patch_send_plan import (
        build_analog_four_patch_send_plan_payload,
        build_analog_four_patch_send_plan_report_from_source,
    )

    report = build_analog_four_patch_send_plan_report_from_source(
        "--description",
        "low end pressure with noisy metallic percussion",
        track=3,
        selected_candidate=2,
    )
    payload = build_analog_four_patch_send_plan_payload(report)

    assert payload["selected_candidate"] == 2
    assert payload["selected_track"] == 3
    assert payload["send_plan"]["summary"]["sendable_count"] > 0
    assert payload["send_plan"]["send_events"][0]["track"] == 3
    assert payload["send_plan"]["manual_events"]
    assert {event["skip_code"] for event in payload["send_plan"]["manual_events"]} == {
        "not-transport-ready",
        "paired-cc-unverified",
    }
    assert payload["safety"][0] == "passive read-only patch send plan"
    assert json.dumps(payload, sort_keys=True) == json.dumps(
        build_analog_four_patch_send_plan_payload(report),
        sort_keys=True,
    )


def test_patch_send_plan_report_private_transport_helper_covers_pending_nrpn() -> None:
    from rytm_randomizer.reports.analog_four_patch_send_plan import _transport_label
    from rytm_randomizer.style_analysis.analog_four_patch_send_plan import (
        AnalogFourPatchSendEvent,
    )

    event = AnalogFourPatchSendEvent(
        sequence=1,
        track=1,
        channel=0,
        parameter="Malformed NRPN",
        section="TEST",
        encoder="-",
        screen_value="1",
        midi_value=1,
        message_kind="nrpn",
        cc_msb=None,
        cc_lsb=None,
        nrpn_address=None,
        transport_status="nrpn-ready",
        dial_direction="set to 1",
        rationale="defensive row",
        confidence="test",
    )

    assert _transport_label(event) == "NRPN pending"


def test_patch_send_plan_cli_description_json_mode(capsys: pytest.CaptureFixture[str]) -> None:
    from rytm_randomizer.cli import main

    exit_code = main(
        [
            "analog-four-patch-send-plan-report",
            "--description",
            "dark rolling techno with narrow pulse and HP2 filter",
            "--track",
            "2",
            "--candidate",
            "1",
            "--json",
        ]
    )

    captured = capsys.readouterr()
    payload = json.loads(captured.out)

    assert exit_code == 0
    assert payload["selected_track"] == 2
    assert payload["selected_candidate"] == 1
    assert payload["send_plan"]["summary"]["transport_message_count"] == 34
    assert captured.err == ""


def test_patch_send_plan_cli_description_text_mode(capsys: pytest.CaptureFixture[str]) -> None:
    from rytm_randomizer.cli import main

    exit_code = main(
        [
            "analog-four-patch-send-plan-report",
            "--description",
            "dark rolling techno with narrow pulse and HP2 filter",
            "--track",
            "2",
            "--candidate",
            "1",
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 0
    assert "Sendable MIDI events:" in captured.out
    assert "Selected track: 2" in captured.out
    assert captured.err == ""


def test_patch_send_plan_cli_rejects_bad_arguments(capsys: pytest.CaptureFixture[str]) -> None:
    from rytm_randomizer.cli import main

    exit_code = main(["analog-four-patch-send-plan-report", "--track", "5"])

    captured = capsys.readouterr()

    assert exit_code == 2
    assert "requires exactly one source" in captured.err
    assert captured.out == ""


def test_patch_send_plan_cli_handler_formats_builder_errors(
    capsys: pytest.CaptureFixture[str],
) -> None:
    from rytm_randomizer.reports.analog_four_patch_send_plan import (
        _handle_analog_four_patch_send_plan_report,
    )

    exit_code = _handle_analog_four_patch_send_plan_report(
        "--library",
        "reference-folder",
        track=1,
        selected_candidate=1,
    )

    captured = capsys.readouterr()

    assert exit_code == 2
    assert "source_flag must be --description or --audio" in captured.err
    assert captured.out == ""


@pytest.mark.parametrize(
    "args, expected",
    [
        (["--description"], "--description requires a value"),
        (["--description", "x", "--track"], "--track requires a value"),
        (["--description", "x", "--candidate"], "--candidate requires a value"),
        (["--description", "x", "--candidate", "NaN"], "--candidate must be an integer"),
        (["--description", "x", "--track", "5"], "--track must be in 1..4"),
        (["--description", "x", "--unknown"], "unknown argument: --unknown"),
    ],
)
def test_patch_send_plan_cli_rejects_specific_bad_arguments(
    args: list[str],
    expected: str,
    capsys: pytest.CaptureFixture[str],
) -> None:
    from rytm_randomizer.cli import main

    exit_code = main(["analog-four-patch-send-plan-report", *args])

    captured = capsys.readouterr()

    assert exit_code == 2
    assert expected in captured.err
    assert captured.out == ""
