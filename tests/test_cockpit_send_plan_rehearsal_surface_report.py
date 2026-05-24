from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from rytm_randomizer.cockpit.data import CockpitSendPlan, SendPlanPacket

pytestmark = pytest.mark.fast

PROJECT_ROOT = Path(__file__).resolve().parents[1]
FORBIDDEN_REAL_MIDI_AND_ADAPTER_MODULES = (
    "mido",
    "rtmidi",
    "pythonrtmidi",
    "rytm_randomizer.real_midi_adapter",
)


def _packet(pad_id: int = 1, parameter: str = "tun", value: int = 64) -> SendPlanPacket:
    return SendPlanPacket(
        pad_id=pad_id,
        parameter=parameter,
        channel=0,
        control=74,
        value=value,
    )


def _plan(
    *,
    ready: bool = True,
    readiness_reason: str = "ready",
    safety_status: str = "safe",
    packets: tuple[SendPlanPacket, ...] | None = None,
    locked_pad_ids: frozenset[int] = frozenset({4}),
    blocked_reasons: tuple[str, ...] = (),
) -> CockpitSendPlan:
    return CockpitSendPlan(
        plan_id="sendplan-abcdef0123456789",
        candidate_id="candidate-warehouse-1",
        source_snapshot_id="snapshot-warehouse-a01",
        profile_id="profile-jose-core-techno",
        ready=ready,
        readiness_reason=readiness_reason,  # type: ignore[arg-type]
        safety_status=safety_status,  # type: ignore[arg-type]
        packets=(
            packets
            if packets is not None
            else (
                _packet(pad_id=1, parameter="dec", value=91),
                _packet(pad_id=1, parameter="tun", value=70),
                _packet(pad_id=2, parameter="lev", value=110),
            )
        ),
        locked_pad_ids=locked_pad_ids,
        blocked_reasons=blocked_reasons,  # type: ignore[arg-type]
    )


def test_cockpit_send_plan_rehearsal_surface_builds_gui_ready_state() -> None:
    from rytm_randomizer.reports.cockpit_send_plan_operator_readiness import (
        build_cockpit_send_plan_operator_readiness_report,
    )
    from rytm_randomizer.reports.cockpit_send_plan_rehearsal_surface import (
        SEND_PLAN_REHEARSAL_SURFACE_VERSION,
        build_cockpit_send_plan_rehearsal_surface_from_readiness,
        format_cockpit_send_plan_rehearsal_surface_report,
        to_cockpit_send_plan_rehearsal_surface_json,
    )

    readiness = build_cockpit_send_plan_operator_readiness_report(
        _plan(),
        label="Warehouse readiness",
    )
    report = build_cockpit_send_plan_rehearsal_surface_from_readiness(
        readiness,
        surface_label="Warehouse send surface",
    )

    assert report.surface_version == SEND_PLAN_REHEARSAL_SURFACE_VERSION
    assert report.surface_id.startswith("send-plan-surface-")
    assert report.surface_label == "Warehouse send surface"
    assert report.surface_status == "ready"
    assert report.screen_state == "send-ready-review"
    assert report.send_control_state == "review-required"
    assert report.readiness_report_id == readiness.report_id
    assert report.primary_operator_action == (
        "SEND may be enabled after the operator reviews this prepared plan."
    )
    assert {panel.panel_key for panel in report.panels} >= {
        "summary",
        "pad-packets",
        "readiness-checks",
        "safety-locks",
    }
    assert report.panels[0].status == "ready"
    send_action = next(
        control for control in report.action_controls if control.action_key == "send"
    )
    assert send_action.control_state == "review-required"
    assert send_action.gate_status == "ready"
    assert send_action.enabled is False
    assert send_action.bound_state_key == "cockpit.sendPlan.send"
    assert any(binding.state_key == "cockpit.sendPlan.status" for binding in report.state_bindings)
    assert any(check.check_key == "assert-send-action-gated" for check in report.surface_checks)
    assert "no MIDI sending" in report.blocked_actions
    assert report.replay_commands[0].startswith(
        "python -m rytm_randomizer.cli cockpit-send-plan-rehearsal-surface-report "
    )

    lines = format_cockpit_send_plan_rehearsal_surface_report(report)
    text = "\n".join(lines)
    assert lines[0] == "RytmRandomizer passive cockpit send-plan rehearsal surface"
    assert "Cockpit send-plan rehearsal surface:" in lines
    assert "- Surface status: ready" in lines
    assert "- SEND control state: review-required" in lines
    assert "GUI panels:" in lines
    assert "- summary: Send plan summary" in lines
    assert "Action controls:" in lines
    assert "- send: SEND" in lines
    assert "Source: rytm_randomizer.reports.cockpit_send_plan_rehearsal_surface" in text

    payload = to_cockpit_send_plan_rehearsal_surface_json(report)
    surface = payload["cockpit_send_plan_rehearsal_surface"]
    assert surface["surface_id"] == report.surface_id
    assert surface["surface_status"] == "ready"
    assert surface["action_controls"][0]["enabled"] is False
    assert (
        payload["cockpit_send_plan_operator_readiness"]["send_plan_id"]
        == "sendplan-abcdef0123456789"
    )
    assert payload["safety"][0] == "passive/read-only"


def test_cockpit_send_plan_rehearsal_surface_explains_blocked_send() -> None:
    from rytm_randomizer.reports.cockpit_send_plan_rehearsal_surface import (
        build_cockpit_send_plan_rehearsal_surface_report,
        format_cockpit_send_plan_rehearsal_surface_report,
        to_cockpit_send_plan_rehearsal_surface_json,
    )

    report = build_cockpit_send_plan_rehearsal_surface_report(
        _plan(
            ready=False,
            readiness_reason="candidate_high_risk",
            safety_status="high_risk",
            packets=(_packet(pad_id=3, parameter="dist", value=127),),
            locked_pad_ids=frozenset({1, 2}),
            blocked_reasons=("candidate_high_risk",),
        ),
        surface_label="Blocked warehouse surface",
    )

    assert report.surface_status == "blocked"
    assert report.screen_state == "send-blocked-review"
    assert report.send_control_state == "disabled"
    assert report.primary_operator_action == (
        "Review the high-risk candidate, lower depth or regenerate, then prepare SEND again."
    )
    assert report.blocked_actions[0] == (
        "SEND remains disabled until prepare_send_plan returns a ready plan"
    )
    send_action = next(
        control for control in report.action_controls if control.action_key == "send"
    )
    assert send_action.gate_status == "blocked"
    assert send_action.control_state == "disabled"
    assert send_action.operator_action.startswith("Review the high-risk candidate")
    assert any(panel.status == "blocked" for panel in report.panels)

    text = "\n".join(format_cockpit_send_plan_rehearsal_surface_report(report))
    assert "- Surface status: blocked" in text
    assert "- Screen state: send-blocked-review" in text
    assert "SEND remains disabled" in text

    payload = to_cockpit_send_plan_rehearsal_surface_json(report)
    surface = payload["cockpit_send_plan_rehearsal_surface"]
    assert surface["surface_status"] == "blocked"
    assert surface["blocked_reasons"] == ["candidate_high_risk"]


def test_cockpit_send_plan_rehearsal_surface_cli_accepts_plan_and_readiness_json(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    from rytm_randomizer.cli import main
    from rytm_randomizer.reports.cockpit_send_plan_operator_readiness import (
        build_cockpit_send_plan_operator_readiness_report,
        to_cockpit_send_plan_operator_readiness_json,
    )
    from rytm_randomizer.reports.cockpit_send_plan_rehearsal_surface import (
        COCKPIT_SEND_PLAN_REHEARSAL_SURFACE_CLI_COMMAND,
    )

    plan_json = json.dumps(_plan().to_dict(), sort_keys=True)
    parsed = COCKPIT_SEND_PLAN_REHEARSAL_SURFACE_CLI_COMMAND.args_parser(
        ["--plan-json", plan_json, "--label", "Warehouse surface", "--json"]
    )
    assert parsed["surface_label"] == "Warehouse surface"
    assert parsed["json_output"] is True
    assert parsed["send_plan"].plan_id == "sendplan-abcdef0123456789"

    readiness_payload = to_cockpit_send_plan_operator_readiness_json(
        build_cockpit_send_plan_operator_readiness_report(
            _plan(),
            label="Warehouse readiness",
        )
    )
    readiness_json = json.dumps(readiness_payload, sort_keys=True)
    parsed_readiness = COCKPIT_SEND_PLAN_REHEARSAL_SURFACE_CLI_COMMAND.args_parser(
        ["--readiness-json", readiness_json]
    )
    assert parsed_readiness["readiness_report"].label == "Warehouse readiness"

    plan_path = tmp_path / "send-plan.json"
    plan_path.write_text(plan_json, encoding="utf-8")
    parsed_from_file = COCKPIT_SEND_PLAN_REHEARSAL_SURFACE_CLI_COMMAND.args_parser(
        ["--plan-file", str(plan_path)]
    )
    assert parsed_from_file["send_plan"].to_dict() == _plan().to_dict()

    readiness_path = tmp_path / "readiness.json"
    readiness_path.write_text(readiness_json, encoding="utf-8")
    parsed_readiness_file = COCKPIT_SEND_PLAN_REHEARSAL_SURFACE_CLI_COMMAND.args_parser(
        ["--readiness-file", str(readiness_path)]
    )
    assert parsed_readiness_file["readiness_report"].send_plan_id == ("sendplan-abcdef0123456789")

    rc = main(
        [
            "cockpit-send-plan-rehearsal-surface-report",
            "--plan-json",
            plan_json,
            "--label",
            "Warehouse surface",
            "--json",
        ]
    )
    captured = capsys.readouterr()
    assert rc == 0
    payload = json.loads(captured.out)
    assert payload["cockpit_send_plan_rehearsal_surface"]["surface_label"] == ("Warehouse surface")
    assert captured.err == ""

    rc = main(["cockpit-send-plan-rehearsal-surface-report", "--readiness-json", readiness_json])
    captured = capsys.readouterr()
    assert rc == 0
    assert "Cockpit send-plan rehearsal surface:" in captured.out
    assert "- Surface status: ready" in captured.out
    assert captured.err == ""


def test_cockpit_send_plan_rehearsal_surface_parser_and_handler_errors(
    capsys: pytest.CaptureFixture[str],
) -> None:
    from rytm_randomizer.reports.cockpit_send_plan_rehearsal_surface import (
        COCKPIT_SEND_PLAN_REHEARSAL_SURFACE_CLI_COMMAND,
    )

    plan_json = json.dumps(_plan().to_dict(), sort_keys=True)
    with pytest.raises(ValueError, match="surface_label must not be blank"):
        COCKPIT_SEND_PLAN_REHEARSAL_SURFACE_CLI_COMMAND.args_parser(
            ["--plan-json", plan_json, "--label", " "]
        )
    with pytest.raises(ValueError, match="provide exactly one"):
        COCKPIT_SEND_PLAN_REHEARSAL_SURFACE_CLI_COMMAND.args_parser(
            ["--plan-json", plan_json, "--readiness-json", "{}"]
        )
    with pytest.raises(ValueError, match="usage"):
        COCKPIT_SEND_PLAN_REHEARSAL_SURFACE_CLI_COMMAND.args_parser(
            ["--plan-json", plan_json, "--unknown"]
        )
    with pytest.raises(ValueError, match="plan JSON must decode to an object"):
        COCKPIT_SEND_PLAN_REHEARSAL_SURFACE_CLI_COMMAND.args_parser(["--plan-json", "[]"])
    with pytest.raises(ValueError, match="readiness JSON must decode to an object"):
        COCKPIT_SEND_PLAN_REHEARSAL_SURFACE_CLI_COMMAND.args_parser(["--readiness-json", "[]"])
    with pytest.raises(ValueError, match="readiness JSON must contain a readiness object"):
        COCKPIT_SEND_PLAN_REHEARSAL_SURFACE_CLI_COMMAND.args_parser(
            [
                "--readiness-json",
                json.dumps({"cockpit_send_plan_operator_readiness": []}),
            ]
        )
    with pytest.raises(ValueError, match="readiness JSON must include send_plan object"):
        COCKPIT_SEND_PLAN_REHEARSAL_SURFACE_CLI_COMMAND.args_parser(
            [
                "--readiness-json",
                json.dumps({"cockpit_send_plan_operator_readiness": {"label": "broken"}}),
            ]
        )

    rc = COCKPIT_SEND_PLAN_REHEARSAL_SURFACE_CLI_COMMAND.handler(
        send_plan="not-a-send-plan",
        readiness_report=None,
        surface_label="Warehouse surface",
        json_output=False,
    )
    captured = capsys.readouterr()
    assert rc == 2
    assert captured.out == ""
    assert "send_plan must be a CockpitSendPlan" in captured.err

    rc = COCKPIT_SEND_PLAN_REHEARSAL_SURFACE_CLI_COMMAND.handler(
        send_plan=None,
        readiness_report=object(),
        surface_label="Warehouse surface",
        json_output=False,
    )
    captured = capsys.readouterr()
    assert rc == 2
    assert captured.out == ""
    assert "readiness_report must be a CockpitSendPlanOperatorReadinessReport" in captured.err

    rc = COCKPIT_SEND_PLAN_REHEARSAL_SURFACE_CLI_COMMAND.handler(
        send_plan=_plan(),
        readiness_report=None,
        surface_label=object(),
        json_output=False,
    )
    captured = capsys.readouterr()
    assert rc == 2
    assert captured.out == ""
    assert "surface_label must be a string" in captured.err


def test_cockpit_send_plan_rehearsal_surface_help_and_passive_import_safety() -> None:
    from rytm_randomizer.help_text import resolve_help_text

    help_text = resolve_help_text("cockpit-send-plan-rehearsal-surface-report")
    assert help_text.startswith(
        "RytmRandomizer passive CLI: cockpit-send-plan-rehearsal-surface-report"
    )
    assert "send-plan rehearsal surface" in help_text
    assert "no MIDI sending" in help_text

    code = "\n".join(
        [
            "import sys",
            "import rytm_randomizer.reports.cockpit_send_plan_rehearsal_surface",
            f"forbidden = {FORBIDDEN_REAL_MIDI_AND_ADAPTER_MODULES!r}",
            "loaded = sorted(name for name in forbidden if name in sys.modules)",
            "if loaded:",
            "    print('\\n'.join(loaded))",
        ]
    )
    result = subprocess.run(
        [sys.executable, "-c", code],
        cwd=PROJECT_ROOT,
        text=True,
        capture_output=True,
        check=True,
    )
    assert result.stdout == ""
