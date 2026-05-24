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


def test_cockpit_send_plan_operator_readiness_builds_report_and_json() -> None:
    from rytm_randomizer.reports.cockpit_send_plan_operator_readiness import (
        SEND_PLAN_OPERATOR_READINESS_VERSION,
        build_cockpit_send_plan_operator_readiness_report,
        format_cockpit_send_plan_operator_readiness_report,
        to_cockpit_send_plan_operator_readiness_json,
    )

    send_plan = _plan()
    report = build_cockpit_send_plan_operator_readiness_report(
        send_plan,
        label="Warehouse send preflight",
    )

    assert report.report_version == SEND_PLAN_OPERATOR_READINESS_VERSION
    assert report.report_id.startswith("send-plan-readiness-")
    assert report.label == "Warehouse send preflight"
    assert report.send_plan_id == send_plan.plan_id
    assert report.status == "ready"
    assert report.severity == "info"
    assert report.operator_next_action == (
        "SEND may be enabled after the operator reviews this prepared plan."
    )
    assert report.pad_summaries[0].pad_id == 1
    assert report.pad_summaries[0].packet_count == 2
    assert report.pad_summaries[0].parameter_summary == "dec=91 cc74 ch0; tun=70 cc74 ch0"
    assert report.locked_pad_summary == "4"
    assert "no MIDI sending" in report.blocked_actions
    assert report.replay_commands[0].startswith(
        "python -m rytm_randomizer.cli cockpit-send-plan-readiness-report --plan-json "
    )

    lines = format_cockpit_send_plan_operator_readiness_report(report)
    text = "\n".join(lines)
    assert lines[0] == "RytmRandomizer passive cockpit send-plan operator readiness"
    assert "Cockpit send-plan operator readiness:" in lines
    assert "- Status: ready" in lines
    assert (
        "- Operator next action: SEND may be enabled after the operator reviews this prepared plan."
    )
    assert "Pad packet summaries:" in lines
    assert "- Pad 1: 2 packets | dec=91 cc74 ch0; tun=70 cc74 ch0" in lines
    assert "- no MIDI sending" in lines
    assert "- no port opening" in lines
    assert "Source: rytm_randomizer.reports.cockpit_send_plan_operator_readiness" in text

    payload = to_cockpit_send_plan_operator_readiness_json(report)
    readiness = payload["cockpit_send_plan_operator_readiness"]
    assert readiness["report_id"] == report.report_id
    assert readiness["status"] == "ready"
    assert readiness["pad_summaries"][0]["parameter_summary"] == (
        "dec=91 cc74 ch0; tun=70 cc74 ch0"
    )
    assert readiness["send_plan"]["estimated_midi_msgs"] == 3
    assert payload["safety"][0] == "passive/read-only"


def test_cockpit_send_plan_operator_readiness_explains_blocked_plans() -> None:
    from rytm_randomizer.reports.cockpit_send_plan_operator_readiness import (
        build_cockpit_send_plan_operator_readiness_report,
        format_cockpit_send_plan_operator_readiness_report,
        to_cockpit_send_plan_operator_readiness_json,
    )

    send_plan = _plan(
        ready=False,
        readiness_reason="candidate_high_risk",
        safety_status="high_risk",
        packets=(_packet(pad_id=3, parameter="dist", value=127),),
        locked_pad_ids=frozenset({1, 2}),
        blocked_reasons=("candidate_high_risk",),
    )
    report = build_cockpit_send_plan_operator_readiness_report(send_plan)

    assert report.status == "blocked"
    assert report.severity == "critical"
    assert report.operator_next_action == (
        "Review the high-risk candidate, lower depth or regenerate, then prepare SEND again."
    )
    assert report.locked_pad_summary == "1, 2"
    assert any(check.status == "blocked" for check in report.readiness_checks)
    assert "SEND remains disabled until prepare_send_plan returns a ready plan" in (
        report.blocked_actions
    )

    lines = format_cockpit_send_plan_operator_readiness_report(report)
    assert "- Status: blocked" in lines
    assert "- Readiness reason: candidate_high_risk" in lines
    assert "Readiness checks:" in lines
    assert any("candidate_high_risk" in line for line in lines)

    payload = to_cockpit_send_plan_operator_readiness_json(report)
    readiness = payload["cockpit_send_plan_operator_readiness"]
    assert readiness["status"] == "blocked"
    assert readiness["blocked_reasons"] == ["candidate_high_risk"]


def test_cockpit_send_plan_operator_readiness_cli_parses_json_and_files(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    from rytm_randomizer.cli import main
    from rytm_randomizer.reports.cockpit_send_plan_operator_readiness import (
        COCKPIT_SEND_PLAN_OPERATOR_READINESS_CLI_COMMAND,
    )

    plan_json = json.dumps(_plan().to_dict(), sort_keys=True)
    parsed = COCKPIT_SEND_PLAN_OPERATOR_READINESS_CLI_COMMAND.args_parser(
        ["--plan-json", plan_json, "--label", "Warehouse send preflight", "--json"]
    )
    assert parsed["label"] == "Warehouse send preflight"
    assert parsed["json_output"] is True
    assert parsed["send_plan"].plan_id == "sendplan-abcdef0123456789"

    plan_path = tmp_path / "send-plan.json"
    plan_path.write_text(plan_json, encoding="utf-8")
    parsed_from_file = COCKPIT_SEND_PLAN_OPERATOR_READINESS_CLI_COMMAND.args_parser(
        ["--plan-file", str(plan_path)]
    )
    assert parsed_from_file["send_plan"].to_dict() == _plan().to_dict()

    with pytest.raises(ValueError, match="usage"):
        COCKPIT_SEND_PLAN_OPERATOR_READINESS_CLI_COMMAND.args_parser(["--label"])
    with pytest.raises(ValueError, match="exactly one"):
        COCKPIT_SEND_PLAN_OPERATOR_READINESS_CLI_COMMAND.args_parser(
            ["--plan-json", plan_json, "--plan-file", str(plan_path)]
        )

    rc = main(
        [
            "cockpit-send-plan-readiness-report",
            "--plan-json",
            plan_json,
            "--label",
            "Warehouse send preflight",
            "--json",
        ]
    )
    captured = capsys.readouterr()
    assert rc == 0
    payload = json.loads(captured.out)
    assert payload["cockpit_send_plan_operator_readiness"]["label"] == ("Warehouse send preflight")
    assert captured.err == ""

    rc = main(["cockpit-send-plan-readiness-report", "--plan-json", plan_json])
    captured = capsys.readouterr()
    assert rc == 0
    assert "Cockpit send-plan operator readiness:" in captured.out
    assert "- Status: ready" in captured.out
    assert captured.err == ""


@pytest.mark.parametrize(
    ("readiness_reason", "blocked_reasons", "expected_next_action"),
    [
        (
            "profile_mismatch",
            ("profile_mismatch",),
            "Select the matching profile, regenerate the preview if needed, then prepare SEND again.",
        ),
        (
            "source_snapshot_mismatch",
            ("source_snapshot_mismatch",),
            "Reload or refresh the current snapshot, then prepare SEND again.",
        ),
        (
            "no_sendable_changes",
            ("no_sendable_changes",),
            "Unlock at least one changed pad or stage a candidate with sendable parameter changes.",
        ),
    ],
)
def test_cockpit_send_plan_operator_readiness_operator_actions_cover_blockers(
    readiness_reason: str,
    blocked_reasons: tuple[str, ...],
    expected_next_action: str,
) -> None:
    from rytm_randomizer.reports.cockpit_send_plan_operator_readiness import (
        build_cockpit_send_plan_operator_readiness_report,
        format_cockpit_send_plan_operator_readiness_report,
    )

    send_plan = _plan(
        ready=False,
        readiness_reason=readiness_reason,
        safety_status="safe",
        packets=(),
        locked_pad_ids=frozenset(),
        blocked_reasons=blocked_reasons,
    )
    report = build_cockpit_send_plan_operator_readiness_report(send_plan)

    assert report.operator_next_action == expected_next_action
    assert report.locked_pad_summary == "none"
    assert report.pad_summaries == ()
    assert "- none" in format_cockpit_send_plan_operator_readiness_report(report)


def test_cockpit_send_plan_operator_readiness_parser_and_handler_errors(
    capsys: pytest.CaptureFixture[str],
) -> None:
    from rytm_randomizer.reports.cockpit_send_plan_operator_readiness import (
        COCKPIT_SEND_PLAN_OPERATOR_READINESS_CLI_COMMAND,
    )

    plan_json = json.dumps(_plan().to_dict(), sort_keys=True)
    with pytest.raises(ValueError, match="label must not be blank"):
        COCKPIT_SEND_PLAN_OPERATOR_READINESS_CLI_COMMAND.args_parser(
            ["--plan-json", plan_json, "--label", " "]
        )
    with pytest.raises(ValueError, match="usage"):
        COCKPIT_SEND_PLAN_OPERATOR_READINESS_CLI_COMMAND.args_parser(
            ["--plan-json", plan_json, "--unknown"]
        )
    with pytest.raises(ValueError, match="plan JSON must decode to an object"):
        COCKPIT_SEND_PLAN_OPERATOR_READINESS_CLI_COMMAND.args_parser(["--plan-json", "[]"])

    rc = COCKPIT_SEND_PLAN_OPERATOR_READINESS_CLI_COMMAND.handler(
        send_plan="not-a-send-plan",
        label="Warehouse send preflight",
        json_output=False,
    )
    captured = capsys.readouterr()
    assert rc == 2
    assert captured.out == ""
    assert "send_plan must be a CockpitSendPlan" in captured.err

    rc = COCKPIT_SEND_PLAN_OPERATOR_READINESS_CLI_COMMAND.handler(
        send_plan=_plan(),
        label=object(),
        json_output=False,
    )
    captured = capsys.readouterr()
    assert rc == 2
    assert captured.out == ""
    assert "label must be a string" in captured.err


def test_cockpit_send_plan_operator_readiness_help_and_passive_import_safety() -> None:
    from rytm_randomizer.help_text import resolve_help_text

    help_text = resolve_help_text("cockpit-send-plan-readiness-report")
    assert help_text.startswith("RytmRandomizer passive CLI: cockpit-send-plan-readiness-report")
    assert "send-plan operator readiness" in help_text
    assert "no MIDI sending" in help_text

    code = "\n".join(
        [
            "import sys",
            "import rytm_randomizer.reports.cockpit_send_plan_operator_readiness",
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
