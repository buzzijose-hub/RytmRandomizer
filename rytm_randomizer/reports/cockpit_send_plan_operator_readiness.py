"""Passive cockpit send-plan operator-readiness report."""

from __future__ import annotations

import hashlib
import json
import sys
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Final

from ..cli_registry import CliCommand, register
from ..cockpit.data import CockpitSendPlan, ReadinessReason
from ._passive_section import (
    PassiveJsonField,
    PassiveLineField,
    passive_dataclass_json,
    passive_section_lines,
)
from .formatter import (
    SAFETY_SECTION_HEADER,
    PassiveReportHeader,
    passive_report_lines,
    powershell_literal_arg,
)
from .live_gui_common import format_cli_error as _format_cli_error
from .live_gui_common import pop_option_value, status_severity

REPORT_TITLE: Final[str] = "RytmRandomizer passive cockpit send-plan operator readiness"
SOURCE_MODULE: Final[str] = "reports.cockpit_send_plan_operator_readiness"
SEND_PLAN_OPERATOR_READINESS_VERSION: Final[str] = "cockpit-send-plan-operator-readiness-v1"
_DEFAULT_LABEL: Final[str] = "Cockpit send-plan operator readiness"
_COMMAND_NAME: Final[str] = "cockpit-send-plan-readiness-report"
SAFETY_LINES: Final[tuple[str, ...]] = (
    "passive/read-only",
    "CockpitSendPlan metadata only",
    "operator readiness explanation only",
    "uses prepared inert packet rows only",
    "does not prepare a new plan",
    "does not apply a plan",
    "does not connect to cockpit sidecar",
    "does not open a WebSocket",
    "does not launch GUI",
    "does not launch app",
    "JSON/stdout only",
    "path options are read-only inputs",
    "no MIDI sending",
    "no port opening",
    "no hardware mutation",
    "no hardware required",
)
_HEADER: Final[PassiveReportHeader] = PassiveReportHeader(
    title=REPORT_TITLE,
    source_module=SOURCE_MODULE,
)
_USAGE: Final[str] = (
    "cockpit-send-plan-readiness-report usage: "
    "(--plan-json <json>|--plan-file <path>) [--label <text>] [--json]"
)
_PAD_SUMMARY_JSON_FIELDS: Final[tuple[PassiveJsonField, ...]] = (
    PassiveJsonField("pad_id", "pad_id"),
    PassiveJsonField("packet_count", "packet_count"),
    PassiveJsonField("parameter_summary", "parameter_summary"),
)
_READINESS_CHECK_JSON_FIELDS: Final[tuple[PassiveJsonField, ...]] = (
    PassiveJsonField("check_key", "check_key"),
    PassiveJsonField("label", "label"),
    PassiveJsonField("status", "status"),
    PassiveJsonField("severity", "severity"),
    PassiveJsonField("message", "message"),
    PassiveJsonField("operator_action", "operator_action"),
    PassiveJsonField("passive", "passive"),
)
_READINESS_CHECK_LINE_FIELDS: Final[tuple[PassiveLineField, ...]] = (
    PassiveLineField("Status", "status"),
    PassiveLineField("Severity", "severity"),
    PassiveLineField("Message", "message"),
    PassiveLineField("Operator action", "operator_action"),
    PassiveLineField("Passive", "passive"),
)


@dataclass(frozen=True)
class CockpitSendPlanPadSummary:
    """Operator-facing summary for one pad's prepared packet rows."""

    pad_id: int
    packet_count: int
    parameter_summary: str


@dataclass(frozen=True)
class CockpitSendPlanReadinessCheck:
    """One send-plan readiness check for operator review."""

    check_key: str
    label: str
    status: str
    severity: str
    message: str
    operator_action: str
    passive: bool


@dataclass(frozen=True)
class CockpitSendPlanOperatorReadinessReport:
    """Passive operator-readiness explanation for one prepared send plan."""

    send_plan: CockpitSendPlan
    report_version: str
    report_id: str
    label: str
    status: str
    severity: str
    operator_next_action: str
    locked_pad_summary: str
    pad_summaries: tuple[CockpitSendPlanPadSummary, ...]
    readiness_checks: tuple[CockpitSendPlanReadinessCheck, ...]
    blocked_actions: tuple[str, ...]
    replay_commands: tuple[str, ...]

    @property
    def send_plan_id(self) -> str:
        """Return the upstream prepared send-plan id."""

        return self.send_plan.plan_id

    @property
    def candidate_id(self) -> str:
        """Return the mutation candidate id attached to the plan."""

        return self.send_plan.candidate_id

    @property
    def source_snapshot_id(self) -> str:
        """Return the source snapshot id attached to the plan."""

        return self.send_plan.source_snapshot_id

    @property
    def profile_id(self) -> str:
        """Return the profile id attached to the plan."""

        return self.send_plan.profile_id

    @property
    def readiness_reason(self) -> ReadinessReason:
        """Return the primary readiness reason."""

        return self.send_plan.readiness_reason

    @property
    def blocked_reasons(self) -> tuple[ReadinessReason, ...]:
        """Return all blocked reasons carried by the plan."""

        return self.send_plan.blocked_reasons


def _normalize_nonblank(value: str, *, field: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field} must not be blank")
    return normalized


def _report_id(send_plan: CockpitSendPlan, label: str) -> str:
    payload = {
        "label": label,
        "send_plan": send_plan.to_dict(),
        "version": SEND_PLAN_OPERATOR_READINESS_VERSION,
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return f"send-plan-readiness-{hashlib.sha256(encoded).hexdigest()[:16]}"


def _locked_pad_summary(send_plan: CockpitSendPlan) -> str:
    if not send_plan.locked_pad_ids:
        return "none"
    return ", ".join(str(pad_id) for pad_id in sorted(send_plan.locked_pad_ids))


def _pad_summaries(send_plan: CockpitSendPlan) -> tuple[CockpitSendPlanPadSummary, ...]:
    by_pad: dict[int, list[str]] = {}
    for packet in send_plan.packets:
        by_pad.setdefault(packet.pad_id, []).append(
            f"{packet.parameter}={packet.value} cc{packet.control} ch{packet.channel}"
        )
    return tuple(
        CockpitSendPlanPadSummary(
            pad_id=pad_id,
            packet_count=len(parameters),
            parameter_summary="; ".join(parameters),
        )
        for pad_id, parameters in sorted(by_pad.items())
    )


def _operator_next_action(send_plan: CockpitSendPlan) -> str:
    if send_plan.ready:
        return "SEND may be enabled after the operator reviews this prepared plan."
    if "candidate_high_risk" in send_plan.blocked_reasons:
        return "Review the high-risk candidate, lower depth or regenerate, then prepare SEND again."
    if "profile_mismatch" in send_plan.blocked_reasons:
        return "Select the matching profile, regenerate the preview if needed, then prepare SEND again."
    if "source_snapshot_mismatch" in send_plan.blocked_reasons:
        return "Reload or refresh the current snapshot, then prepare SEND again."
    if "no_sendable_changes" in send_plan.blocked_reasons:
        return (
            "Unlock at least one changed pad or stage a candidate with sendable parameter changes."
        )
    return "Prepare SEND again after resolving the blocked readiness reason."  # pragma: no cover


def _check(
    *,
    check_key: str,
    label: str,
    status: str,
    message: str,
    operator_action: str,
) -> CockpitSendPlanReadinessCheck:
    return CockpitSendPlanReadinessCheck(
        check_key=check_key,
        label=label,
        status=status,
        severity=status_severity(status),
        message=message,
        operator_action=operator_action,
        passive=True,
    )


def _reason_status(send_plan: CockpitSendPlan, reason: ReadinessReason) -> str:
    if send_plan.ready:
        return "ready"
    return "blocked" if reason in send_plan.blocked_reasons else "ready"


def _readiness_checks(send_plan: CockpitSendPlan) -> tuple[CockpitSendPlanReadinessCheck, ...]:
    ready_status = "ready" if send_plan.ready else "blocked"
    checks = [
        _check(
            check_key="send-plan-ready",
            label="Prepared send plan is ready",
            status=ready_status,
            message=(
                "Prepared plan can gate SEND."
                if send_plan.ready
                else "Prepared plan blocks SEND until readiness reasons clear."
            ),
            operator_action=_operator_next_action(send_plan),
        ),
        _check(
            check_key="candidate_high_risk",
            label="Candidate risk guard",
            status=_reason_status(send_plan, "candidate_high_risk"),
            message=(
                "Candidate is high risk."
                if "candidate_high_risk" in send_plan.blocked_reasons
                else "Candidate risk does not block this plan."
            ),
            operator_action="Lower depth, regenerate, or keep SEND disabled for high-risk plans.",
        ),
        _check(
            check_key="profile_mismatch",
            label="Profile identity guard",
            status=_reason_status(send_plan, "profile_mismatch"),
            message=(
                "Plan profile does not match the active profile."
                if "profile_mismatch" in send_plan.blocked_reasons
                else "Plan profile matches the prepared candidate."
            ),
            operator_action="Select the matching profile before preparing SEND.",
        ),
        _check(
            check_key="source_snapshot_mismatch",
            label="Snapshot identity guard",
            status=_reason_status(send_plan, "source_snapshot_mismatch"),
            message=(
                "Plan source snapshot is stale."
                if "source_snapshot_mismatch" in send_plan.blocked_reasons
                else "Plan source snapshot matches the prepared candidate."
            ),
            operator_action="Refresh the snapshot before preparing SEND.",
        ),
        _check(
            check_key="no_sendable_changes",
            label="Sendable packet guard",
            status=_reason_status(send_plan, "no_sendable_changes"),
            message=(
                "No prepared packet rows remain after locks."
                if "no_sendable_changes" in send_plan.blocked_reasons
                else "Prepared packet rows are available for operator review."
            ),
            operator_action="Unlock a changed pad or stage a candidate with sendable changes.",
        ),
    ]
    return tuple(checks)


def _blocked_actions(send_plan: CockpitSendPlan) -> tuple[str, ...]:
    actions = [
        "no MIDI sending",
        "no port opening",
        "no hardware mutation",
        "no cockpit sidecar connection",
        "no GUI launch",
    ]
    if not send_plan.ready:
        actions.insert(0, "SEND remains disabled until prepare_send_plan returns a ready plan")
    return tuple(actions)


def _replay_command(send_plan: CockpitSendPlan, label: str) -> str:
    plan_json = json.dumps(send_plan.to_dict(), sort_keys=True, separators=(",", ":"))
    return (
        f"python -m rytm_randomizer.cli {_COMMAND_NAME} "
        f"--plan-json {powershell_literal_arg(plan_json)} "
        f"--label {powershell_literal_arg(label)}"
    )


def build_cockpit_send_plan_operator_readiness_report(
    send_plan: CockpitSendPlan,
    *,
    label: str = _DEFAULT_LABEL,
) -> CockpitSendPlanOperatorReadinessReport:
    """Build passive operator-readiness metadata for a prepared cockpit send plan."""

    normalized_label = _normalize_nonblank(label, field="label")
    status = "ready" if send_plan.ready else "blocked"
    return CockpitSendPlanOperatorReadinessReport(
        send_plan=send_plan,
        report_version=SEND_PLAN_OPERATOR_READINESS_VERSION,
        report_id=_report_id(send_plan, normalized_label),
        label=normalized_label,
        status=status,
        severity=status_severity(status),
        operator_next_action=_operator_next_action(send_plan),
        locked_pad_summary=_locked_pad_summary(send_plan),
        pad_summaries=_pad_summaries(send_plan),
        readiness_checks=_readiness_checks(send_plan),
        blocked_actions=_blocked_actions(send_plan),
        replay_commands=(_replay_command(send_plan, normalized_label),),
    )


def _pad_summary_json(summary: CockpitSendPlanPadSummary) -> dict[str, object]:
    return passive_dataclass_json(summary, _PAD_SUMMARY_JSON_FIELDS)


def _readiness_check_json(check: CockpitSendPlanReadinessCheck) -> dict[str, object]:
    return passive_dataclass_json(check, _READINESS_CHECK_JSON_FIELDS)


def to_cockpit_send_plan_operator_readiness_json(
    report: CockpitSendPlanOperatorReadinessReport,
) -> dict[str, object]:
    """Return deterministic JSON for passive send-plan operator readiness."""

    return {
        "cockpit_send_plan_operator_readiness": {
            "report_version": report.report_version,
            "report_id": report.report_id,
            "label": report.label,
            "status": report.status,
            "severity": report.severity,
            "operator_next_action": report.operator_next_action,
            "send_plan_id": report.send_plan_id,
            "candidate_id": report.candidate_id,
            "source_snapshot_id": report.source_snapshot_id,
            "profile_id": report.profile_id,
            "readiness_reason": report.readiness_reason,
            "blocked_reasons": list(report.blocked_reasons),
            "safety_status": report.send_plan.safety_status,
            "estimated_midi_msgs": len(report.send_plan.packets),
            "pad_count": len({packet.pad_id for packet in report.send_plan.packets}),
            "locked_pad_summary": report.locked_pad_summary,
            "pad_summaries": [_pad_summary_json(summary) for summary in report.pad_summaries],
            "readiness_checks": [_readiness_check_json(check) for check in report.readiness_checks],
            "blocked_actions": list(report.blocked_actions),
            "replay_commands": list(report.replay_commands),
            "send_plan": report.send_plan.to_dict(),
        },
        "safety": list(SAFETY_LINES),
    }


def _pad_summary_lines(summary: CockpitSendPlanPadSummary) -> list[str]:
    return [f"- Pad {summary.pad_id}: {summary.packet_count} packets | {summary.parameter_summary}"]


def _readiness_check_lines(check: CockpitSendPlanReadinessCheck) -> list[str]:
    return passive_section_lines(
        f"- {check.check_key}: {check.label}",
        check,
        _READINESS_CHECK_LINE_FIELDS,
    )


def format_cockpit_send_plan_operator_readiness_report(
    report: CockpitSendPlanOperatorReadinessReport,
) -> list[str]:
    """Format a passive send-plan operator-readiness report."""

    lines = [
        "Cockpit send-plan operator readiness:",
        f"- Report id: {report.report_id}",
        f"- Label: {report.label}",
        f"- Status: {report.status}",
        f"- Severity: {report.severity}",
        f"- Operator next action: {report.operator_next_action}",
        f"- Send plan id: {report.send_plan_id}",
        f"- Candidate id: {report.candidate_id}",
        f"- Source snapshot id: {report.source_snapshot_id}",
        f"- Profile id: {report.profile_id}",
        f"- Readiness reason: {report.readiness_reason}",
        f"- Blocked reasons: {', '.join(report.blocked_reasons) or 'none'}",
        f"- Safety status: {report.send_plan.safety_status}",
        f"- Estimated MIDI messages: {len(report.send_plan.packets)}",
        f"- Pad count: {len({packet.pad_id for packet in report.send_plan.packets})}",
        f"- Locked pads: {report.locked_pad_summary}",
        "Pad packet summaries:",
    ]
    if report.pad_summaries:
        for summary in report.pad_summaries:
            lines.extend(_pad_summary_lines(summary))
    else:
        lines.append("- none")
    lines.append("Readiness checks:")
    for check in report.readiness_checks:
        lines.extend(_readiness_check_lines(check))
    lines.extend(
        [
            "Blocked active actions:",
            *[f"- {action}" for action in report.blocked_actions],
            "Replayable passive commands:",
            *[f"- {command}" for command in report.replay_commands],
            SAFETY_SECTION_HEADER,
            *[f"- {line}" for line in SAFETY_LINES],
        ]
    )
    return passive_report_lines(_HEADER, lines)


def _pop_option_value(remaining: list[str]) -> str:
    return pop_option_value(remaining, usage=_USAGE)


def _send_plan_from_json(value: str) -> CockpitSendPlan:
    decoded = json.loads(value)
    if not isinstance(decoded, Mapping):
        raise ValueError("plan JSON must decode to an object")
    return CockpitSendPlan.from_dict(decoded)


def _send_plan_from_file(path: Path) -> CockpitSendPlan:
    return _send_plan_from_json(path.read_text(encoding="utf-8"))


def parse_cockpit_send_plan_operator_readiness_cli_args(
    argv: Sequence[str],
) -> dict[str, object]:
    """Parse passive cockpit send-plan readiness report CLI args."""

    plan_json: str | None = None
    plan_file: Path | None = None
    label = _DEFAULT_LABEL
    json_output = False
    remaining = list(argv)
    while remaining:
        option = remaining.pop(0)
        if option == "--json":
            json_output = True
        elif option == "--plan-json":
            plan_json = _pop_option_value(remaining)
        elif option == "--plan-file":
            plan_file = Path(_pop_option_value(remaining))
        elif option == "--label":
            label = _normalize_nonblank(_pop_option_value(remaining), field="label")
        else:
            raise ValueError(_USAGE)
    if (plan_json is None) == (plan_file is None):
        raise ValueError("provide exactly one of --plan-json or --plan-file")
    send_plan = (
        _send_plan_from_json(plan_json)
        if plan_json is not None
        else _send_plan_from_file(plan_file if plan_file is not None else Path())
    )
    return {
        "send_plan": send_plan,
        "label": label,
        "json_output": json_output,
    }


def _handle_cli_report(**options: object) -> int:
    json_output = options.pop("json_output", False)
    send_plan = options.pop("send_plan")
    label = options.pop("label", _DEFAULT_LABEL)
    try:
        if not isinstance(send_plan, CockpitSendPlan):
            raise TypeError("send_plan must be a CockpitSendPlan")
        if not isinstance(label, str):
            raise TypeError("label must be a string")
        report = build_cockpit_send_plan_operator_readiness_report(
            send_plan,
            label=label,
        )
        if json_output is True:
            sys.stdout.write(
                json.dumps(
                    to_cockpit_send_plan_operator_readiness_json(report),
                    indent=2,
                    sort_keys=True,
                )
            )
            sys.stdout.write("\n")
            return 0
        lines = format_cockpit_send_plan_operator_readiness_report(report)
    except (OSError, ValueError, RuntimeError, NotImplementedError, TypeError, KeyError) as exc:
        sys.stderr.write(f"Error: {exc}\n")
        return 2
    for line in lines:
        sys.stdout.write(f"{line}\n")
    return 0


COCKPIT_SEND_PLAN_OPERATOR_READINESS_CLI_COMMAND: Final[CliCommand] = CliCommand(
    name=_COMMAND_NAME,
    summary="Explain prepared cockpit send-plan readiness for operator review.",
    args_parser=parse_cockpit_send_plan_operator_readiness_cli_args,
    handler=_handle_cli_report,
    error_formatter=_format_cli_error,
)

register(COCKPIT_SEND_PLAN_OPERATOR_READINESS_CLI_COMMAND)

__all__ = [
    "COCKPIT_SEND_PLAN_OPERATOR_READINESS_CLI_COMMAND",
    "REPORT_TITLE",
    "SAFETY_LINES",
    "SEND_PLAN_OPERATOR_READINESS_VERSION",
    "SOURCE_MODULE",
    "CockpitSendPlanOperatorReadinessReport",
    "CockpitSendPlanPadSummary",
    "CockpitSendPlanReadinessCheck",
    "build_cockpit_send_plan_operator_readiness_report",
    "format_cockpit_send_plan_operator_readiness_report",
    "parse_cockpit_send_plan_operator_readiness_cli_args",
    "to_cockpit_send_plan_operator_readiness_json",
]
