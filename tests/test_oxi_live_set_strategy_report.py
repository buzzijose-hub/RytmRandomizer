from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.fast

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_build_report_encodes_rig_roles_and_live_chapters() -> None:
    from rytm_randomizer.reports.oxi_live_set_strategy import (
        build_oxi_live_set_strategy_report,
        format_oxi_live_set_strategy_report,
    )

    report = build_oxi_live_set_strategy_report()
    text = "\n".join(format_oxi_live_set_strategy_report(report))

    assert report.title == "RytmRandomizer OXI live set strategy report"
    assert [role.name for role in report.rig_roles] == [
        "oxi-one",
        "analog-rytm-mkii",
        "analog-four-mkii",
    ]
    assert report.rig_roles[0].responsibility == "notes, triggers, mutes, pattern motion"
    assert report.rig_roles[1].responsibility == "captured-kit sound-design mutation"
    assert report.rig_roles[2].status == "review-only"
    assert [chapter.name for chapter in report.chapters] == [
        "capture-anchor",
        "establish-groove",
        "pressure-build",
        "peak-texture",
        "space-release",
        "transition-fill",
        "home-reset",
    ]
    assert report.chapters[0].rytm_command == "kit/resnapshot"
    assert report.chapters[1].macro_sequence == ("kit-core", "hard-groove")
    assert report.chapters[-1].recovery_action == "Z + send"
    assert "OXI live set strategy:" in text
    assert "Rytm acts as second performer" in text
    assert "Analog Four is review-only" in text


def test_pad_policy_keeps_jose_lane_discipline_without_excluding_pad_12() -> None:
    from rytm_randomizer.reports.oxi_live_set_strategy import (
        build_oxi_live_set_strategy_report,
    )

    report = build_oxi_live_set_strategy_report()
    by_group = {policy.name: policy for policy in report.pad_policies}

    reserved = by_group["reserved-src-fx"]
    assert reserved.pads == (5, 9, 10, 11)
    assert reserved.primary_lane == "SRC"
    assert reserved.filter_policy == "off"
    assert reserved.lfo_policy == "off"
    assert reserved.amp_policy == "overdrive/delay/reverb only"
    assert reserved.product_note == "common Jose live lane, not a product limitation"

    toms = by_group["tom-source-motion"]
    assert toms.pads == (6, 7, 8)
    assert toms.primary_lane == "SRC"
    assert toms.filter_policy == "light"
    assert toms.lfo_policy == "off"
    assert toms.amp_policy == "overdrive/delay/reverb only"

    pad_12 = by_group["pad-12-optional"]
    assert pad_12.pads == (12,)
    assert pad_12.primary_lane == "SRC/AMP FX"
    assert pad_12.product_note == "available for users who rely on Pad 12"


def test_json_payload_is_deterministic_and_explicitly_passive() -> None:
    from rytm_randomizer.reports.oxi_live_set_strategy import (
        build_oxi_live_set_strategy_payload,
    )

    first = build_oxi_live_set_strategy_payload()
    second = build_oxi_live_set_strategy_payload()

    assert json.dumps(first, sort_keys=True) == json.dumps(second, sort_keys=True)
    assert first["title"] == "RytmRandomizer OXI live set strategy report"
    assert first["safety"] == {
        "passive": True,
        "opens_ports": False,
        "sends_midi": False,
        "mutates_hardware": False,
        "requires_hardware": False,
        "a4_outbound": "blocked",
    }
    assert first["chapters"][2]["macro_sequence"] == ["hard-groove", "industrial"]
    assert first["pad_policies"][1]["pads"] == [6, 7, 8]
    assert first["next_hardware_validations"] == [
        "Rytm full-kit macro smoke test from a fresh current-kit capture",
        "A4 input-only soft-capture pass before any outbound macro promotion",
    ]


def test_hardware_validation_runway_keeps_a4_input_only_before_promotion() -> None:
    from rytm_randomizer.reports.oxi_live_set_strategy import (
        build_oxi_live_set_strategy_payload,
        build_oxi_live_set_strategy_report,
        format_oxi_live_set_strategy_report,
    )

    report = build_oxi_live_set_strategy_report()
    by_name = {step.name: step for step in report.hardware_validation_runway}

    assert tuple(by_name) == (
        "rytm-kit-core-smoke",
        "rytm-dual-vco-center-band",
        "a4-soft-capture",
        "a4-macro-dry-run",
    )
    kit_core = by_name["rytm-kit-core-smoke"]
    assert kit_core.device == "Analog Rytm MKII"
    assert kit_core.operator_path == "kit-core -> changes -> send -> go -> Z + send"
    assert kit_core.validation_mode == "operator-present armed Rytm shell"
    assert "no parameter changes staged" in kit_core.expected_evidence

    a4_capture = by_name["a4-soft-capture"]
    assert a4_capture.device == "Analog Four MKII"
    assert a4_capture.validation_mode == "input-only"
    assert a4_capture.safety_boundary == "opens A4 input only; no output and no MIDI send"

    payload = build_oxi_live_set_strategy_payload()
    assert payload["hardware_validation_runway"][2]["name"] == "a4-soft-capture"
    assert payload["hardware_validation_runway"][2]["validation_mode"] == "input-only"

    text = "\n".join(format_oxi_live_set_strategy_report(report))
    assert "Hardware validation runway:" in text
    assert "a4-soft-capture | Analog Four MKII | input-only" in text


def test_a4_promotion_criteria_keep_outbound_macros_blocked_until_evidence_exists() -> None:
    from rytm_randomizer.reports.oxi_live_set_strategy import (
        build_oxi_live_set_strategy_payload,
        build_oxi_live_set_strategy_report,
        format_oxi_live_set_strategy_report,
    )

    report = build_oxi_live_set_strategy_report()
    by_name = {criterion.name: criterion for criterion in report.promotion_criteria}

    assert tuple(by_name) == (
        "a4-input-label-coverage",
        "a4-macro-review",
        "a4-explicit-arm-gate",
        "a4-recovery-path",
    )
    label_coverage = by_name["a4-input-label-coverage"]
    assert label_coverage.device == "Analog Four MKII"
    assert label_coverage.current_status == "blocked"
    assert label_coverage.required_evidence == "known labels for moved controls on tracks 1-4"
    assert label_coverage.promotes_to == "A4 macro readiness review"

    arm_gate = by_name["a4-explicit-arm-gate"]
    assert arm_gate.required_evidence == "operator-confirmed --arm path with no unattended behavior"
    assert arm_gate.safety_note == "no A4 outbound macro send until this gate is satisfied"

    payload = build_oxi_live_set_strategy_payload()
    assert payload["promotion_criteria"][0]["name"] == "a4-input-label-coverage"
    assert payload["promotion_criteria"][2]["current_status"] == "blocked"

    text = "\n".join(format_oxi_live_set_strategy_report(report))
    assert "Promotion criteria:" in text
    assert "a4-explicit-arm-gate | Analog Four MKII | blocked" in text
    assert "no A4 outbound macro send until this gate is satisfied" in text


def test_cli_command_prints_text_json_and_rejects_unexpected_arguments() -> None:
    text_result = subprocess.run(
        [sys.executable, "-m", "rytm_randomizer.cli", "oxi-live-set-strategy-report"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    json_result = subprocess.run(
        [
            sys.executable,
            "-m",
            "rytm_randomizer.cli",
            "oxi-live-set-strategy-report",
            "--json",
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    bad_result = subprocess.run(
        [
            sys.executable,
            "-m",
            "rytm_randomizer.cli",
            "oxi-live-set-strategy-report",
            "--arm",
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert text_result.returncode == 0
    assert "RytmRandomizer OXI live set strategy report" in text_result.stdout
    assert "Pad policies:" in text_result.stdout
    assert text_result.stderr == ""

    assert json_result.returncode == 0
    assert json.loads(json_result.stdout)["chapters"][0]["name"] == "capture-anchor"
    assert json_result.stderr == ""

    assert bad_result.returncode == 2
    assert bad_result.stdout == ""
    assert "oxi-live-set-strategy-report usage: [--json]" in bad_result.stderr


def test_cli_parser_handler_and_error_formatter_cover_direct_paths(capsys) -> None:
    from rytm_randomizer.reports.oxi_live_set_strategy import (
        _format_oxi_live_set_strategy_error,
        _handle_oxi_live_set_strategy_report,
        _parse_oxi_live_set_strategy_args,
    )

    assert _parse_oxi_live_set_strategy_args([]) == {"json_output": False}
    assert _parse_oxi_live_set_strategy_args(["--json"]) == {"json_output": True}
    with pytest.raises(ValueError, match="oxi-live-set-strategy-report usage"):
        _parse_oxi_live_set_strategy_args(["--arm"])

    assert _handle_oxi_live_set_strategy_report(json_output=False) == 0
    text_result = capsys.readouterr()
    assert "RytmRandomizer OXI live set strategy report" in text_result.out
    assert text_result.err == ""

    assert _handle_oxi_live_set_strategy_report(json_output=True) == 0
    json_result = capsys.readouterr()
    assert json.loads(json_result.out)["title"] == "RytmRandomizer OXI live set strategy report"
    assert json_result.err == ""

    assert _format_oxi_live_set_strategy_error(ValueError("bad")) == "Error: bad"


def test_cli_command_imports_no_real_midi_modules() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import sys; "
                "from rytm_randomizer.cli import main; "
                "code = main(['oxi-live-set-strategy-report']); "
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
