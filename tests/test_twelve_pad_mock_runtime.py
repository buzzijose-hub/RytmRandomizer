import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def run_cli(*args):
    return subprocess.run(
        [sys.executable, "-m", "rytm_randomizer.cli", *args],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def test_importing_twelve_pad_mock_runtime_is_passive_and_silent():
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import sys; "
                "import rytm_randomizer.twelve_pad_mock_runtime; "
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


def test_birmingham_dark_techno_mock_plan_covers_all_12_pads_with_mapped_engines():
    from rytm_randomizer.twelve_pad_mock_runtime import build_twelve_pad_mock_runtime_plan

    plan = build_twelve_pad_mock_runtime_plan("Birmingham dark techno")

    assert plan.style_prompt == "Birmingham dark techno"
    assert plan.discovery == 0.61
    assert plan.planned_pad_count == 12
    assert plan.blocked_pad_count == 0
    assert tuple(pad.pad for pad in plan.pads) == tuple(range(1, 13))
    assert tuple(pad.midi_channel for pad in plan.pads) == tuple(range(1, 13))
    assert tuple(pad.wire_channel for pad in plan.pads) == tuple(range(12))
    assert {pad.selection_status for pad in plan.pads} == {"planned"}
    assert plan.pads[0].selected_machine_label == "BD Hard"
    assert plan.pads[0].machine_value == 0
    assert plan.pads[2].role_label == "Metallic motif"
    assert plan.pads[2].selected_machine_label == "BD FM"
    assert plan.pads[11].role_label == "Wild discovery lane"


def test_schranz_mock_plan_falls_back_from_future_preference_to_mapped_engines():
    from rytm_randomizer.twelve_pad_mock_runtime import build_twelve_pad_mock_runtime_plan

    plan = build_twelve_pad_mock_runtime_plan("schranz")

    assert plan.discovery == 0.82
    assert plan.planned_pad_count == 12
    assert plan.blocked_pad_count == 0
    assert plan.fallback_pad_count >= 4

    pad3 = plan.pads[2]
    assert pad3.role_label == "Metallic motif"
    assert pad3.preferred_machine_label == "SY Chip"
    assert pad3.selected_machine_label == "BD FM"
    assert pad3.selection_status == "mapped_fallback"
    assert pad3.selection_reason == "preferred_future_machine_needs_manual_mapping"


def test_mock_sender_captures_machine_and_anchor_messages_with_pad_metadata():
    from rytm_randomizer.twelve_pad_mock_runtime import (
        build_twelve_pad_mock_runtime_plan,
        capture_twelve_pad_mock_messages,
    )

    plan = build_twelve_pad_mock_runtime_plan("Birmingham dark techno", discovery=0.35)
    sender = capture_twelve_pad_mock_messages(plan)
    messages = sender.sent_messages

    assert len(messages) == plan.message_count
    assert len(messages) > 250
    assert messages[0].channel == 0
    assert messages[0].control == 15
    assert messages[0].value == 0
    assert messages[0].metadata["pad"] == 1
    assert messages[0].metadata["midi_channel"] == 1
    assert messages[0].metadata["message_role"] == "machine"
    assert messages[1].metadata["message_role"] == "anchor_param"
    assert messages[1].metadata["parameter"] == "SRC Tune"
    assert messages[-1].metadata["pad"] == 12
    assert messages[-1].metadata["midi_channel"] == 12


def test_format_twelve_pad_mock_runtime_report_includes_safety_and_stream():
    from rytm_randomizer.twelve_pad_mock_runtime import (
        build_twelve_pad_mock_runtime_plan,
        format_twelve_pad_mock_runtime_report,
    )

    plan = build_twelve_pad_mock_runtime_plan("Birmingham dark techno", discovery=0.35)
    report = format_twelve_pad_mock_runtime_report(plan)

    assert report[0] == "RytmRandomizer passive Twelve Pad Mock Runtime Report"
    assert "Style prompt: Birmingham dark techno" in report
    assert "Pad counts: planned 12 / blocked 0 / fallback 0" in report
    assert any(
        line.startswith("- Pad 12 / MIDI channel 12 / Wild discovery lane: BD Hard")
        for line in report
    )
    assert any(line == "- Pad 1 ch 1 wire 0 machine: CC15 -> 0" for line in report)
    assert any(line.startswith("- Pad 12 ch 12 wire 11") for line in report)
    assert "- mock sender only" in report
    assert "- no MIDI sending" in report
    assert "- no port opening" in report


def test_twelve_pad_mock_runtime_report_cli_accepts_style_prompt():
    result = run_cli(
        "twelve-pad-mock-runtime-report",
        "--style",
        "Birmingham dark techno",
    )

    assert result.returncode == 0
    assert "RytmRandomizer passive Twelve Pad Mock Runtime Report" in result.stdout
    assert "Style prompt: Birmingham dark techno" in result.stdout
    assert "Pad counts: planned 12 / blocked 0 / fallback 0" in result.stdout
    assert "Mock sender captured:" in result.stdout
    assert "Pad 12 / MIDI channel 12 / Wild discovery lane: BD Hard" in result.stdout
    assert "- no MIDI sending" in result.stdout
    assert result.stderr == ""


def test_twelve_pad_mock_runtime_report_cli_discovery_override():
    result = run_cli(
        "twelve-pad-mock-runtime-report",
        "--style",
        "schranz",
        "--discovery",
        "0.82",
    )

    assert result.returncode == 0
    assert "Style prompt: schranz" in result.stdout
    assert "Discovery: 0.82" in result.stdout
    assert "Pad counts: planned 12 / blocked 0 / fallback" in result.stdout
    assert "preferred SY Chip [future] -> selected BD FM [mutable]" in result.stdout
    assert result.stderr == ""
