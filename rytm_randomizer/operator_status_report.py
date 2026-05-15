"""Read-only daily operator status report.

This module is passive and in-memory only. It summarizes existing project
status and collaborator intake readiness without querying GitHub, writing
files, opening MIDI ports, sending MIDI, dispatching commands, executing
active behavior, or touching hardware.
"""

from __future__ import annotations

from copy import deepcopy

from .collaborator_intake_readiness_report import (
    build_collaborator_intake_readiness_report,
    summarize_collaborator_intake_readiness_report,
)
from .project_status_report import (
    build_project_status_report,
    summarize_project_status_report,
)


OPERATOR_STATUS_SAFETY = {
    "real_midi": "absent",
    "mido": "absent",
    "port_opening": "absent",
    "midi_sending": "absent",
    "active_execution": "absent",
    "dispatch": "absent",
    "hardware_behavior": "absent",
    "hardware_required": False,
}

_MODE = {
    "passive": True,
    "daily_visibility": True,
    "implementation_intake_ready": True,
}

_OPERATOR_COMMANDS = {
    "project_status": "python -m rytm_randomizer.cli project-status-report --summary",
    "collaborator_intake_readiness": (
        "python -m rytm_randomizer.cli collaborator-intake-readiness-report"
    ),
    "collaborator_branch_watch": (
        "python -m rytm_randomizer.cli collaborator-branch-watch"
    ),
    "local_closeout": (
        "powershell -ExecutionPolicy Bypass -File .\\Scripts\\closeout_check.ps1"
    ),
    "v134_diff": "git diff -- rytm_hybrid_randomizer_v134.py",
    "git_status": "git status --short",
}

_NEXT_ACTIONS = (
    "wait for Eddie implementation branch or PR",
    "run collaborator implementation intake when branch or PR appears",
    "use local closeout for frequent feedback",
    "run manual GitHub Actions only at explicit review gates",
)

__all__ = [
    "OPERATOR_STATUS_SAFETY",
    "build_operator_status_report",
    "format_operator_status_report",
    "summarize_operator_status_report",
]


def build_operator_status_report():
    """Return copied, in-memory operator status data for daily visibility."""

    project_report = build_project_status_report()
    project_summary = summarize_project_status_report(project_report)
    intake_report = build_collaborator_intake_readiness_report()
    intake_summary = summarize_collaborator_intake_readiness_report(intake_report)
    actions_policy = intake_report["github_actions_policy"]

    report = {
        "title": "RytmRandomizer Operator Status Report",
        "mode": _MODE,
        "project": {
            "phase_name": project_summary["phase_name"],
            "creative_identity_candidate": (
                project_summary["creative_identity_candidate"]
            ),
            "passive_cli_command_count": (
                project_summary["passive_cli_command_count"]
            ),
            "v134_reference": project_summary["v134_reference"],
        },
        "collaborator_intake": {
            "status": intake_summary["status"],
            "implementation_branch_observed": intake_summary[
                "implementation_branch_observed"
            ],
            "implementation_pr_observed": intake_summary[
                "implementation_pr_observed"
            ],
            "direct_merge_allowed": intake_report["merge_policy"][
                "direct_merge_allowed"
            ],
        },
        "github_actions": {
            "status": actions_policy["status"],
            "daily_feedback": actions_policy["daily_feedback"],
            "automatic_pull_request_runs": actions_policy[
                "automatic_pull_request_runs"
            ],
            "automatic_push_runs": actions_policy["automatic_push_runs"],
            "automatic_release_tag_runs": actions_policy[
                "automatic_release_tag_runs"
            ],
            "no_pay_policy": actions_policy["no_pay_policy"],
        },
        "operator_commands": _OPERATOR_COMMANDS,
        "next_actions": _NEXT_ACTIONS,
        "safety": OPERATOR_STATUS_SAFETY,
        "source": {
            "project_status": "rytm_randomizer.project_status_report",
            "collaborator_intake_readiness": (
                "rytm_randomizer.collaborator_intake_readiness_report"
            ),
            "collaborator_branch_watch": (
                "rytm_randomizer.collaborator_branch_watch_report"
            ),
            "in_memory_only": True,
        },
    }
    return deepcopy(report)


def summarize_operator_status_report(report=None):
    """Return a compact copied operator status summary."""

    source_report = build_operator_status_report() if report is None else report
    return {
        "title": source_report["title"],
        "phase_name": source_report["project"]["phase_name"],
        "creative_identity_candidate": source_report["project"][
            "creative_identity_candidate"
        ],
        "passive_cli_command_count": source_report["project"][
            "passive_cli_command_count"
        ],
        "collaborator_intake_status": source_report["collaborator_intake"][
            "status"
        ],
        "implementation_branch_observed": source_report["collaborator_intake"][
            "implementation_branch_observed"
        ],
        "implementation_pr_observed": source_report["collaborator_intake"][
            "implementation_pr_observed"
        ],
        "github_actions": source_report["github_actions"]["status"],
        "daily_feedback": source_report["github_actions"]["daily_feedback"],
        "real_midi": source_report["safety"]["real_midi"],
        "active_execution": source_report["safety"]["active_execution"],
        "hardware_required": source_report["safety"]["hardware_required"],
        "next_recommended_action": source_report["next_actions"][0],
    }


def format_operator_status_report(report=None):
    """Return deterministic human-readable operator status report lines."""

    source_report = build_operator_status_report() if report is None else report
    lines = [source_report["title"], "Mode:"]

    for key, value in source_report["mode"].items():
        lines.append(f"- {key}: {value}")

    lines.append("Project:")
    for key, value in source_report["project"].items():
        lines.append(f"- {key}: {value}")

    lines.append("Collaborator Intake:")
    for key, value in source_report["collaborator_intake"].items():
        lines.append(f"- {key}: {value}")

    lines.append("GitHub Actions:")
    for key, value in source_report["github_actions"].items():
        lines.append(f"- {key}: {value}")

    lines.append("Operator Commands:")
    for key, value in source_report["operator_commands"].items():
        lines.append(f"- {key}: {value}")

    lines.append("Next Actions:")
    for action in source_report["next_actions"]:
        lines.append(f"- {action}")

    lines.append("Safety:")
    for key, value in source_report["safety"].items():
        lines.append(f"- {key}: {value}")

    lines.extend(
        [
            "Source:",
            f"- project_status: {source_report['source']['project_status']}",
            (
                "- collaborator_intake_readiness: "
                f"{source_report['source']['collaborator_intake_readiness']}"
            ),
            (
                "- collaborator_branch_watch: "
                f"{source_report['source']['collaborator_branch_watch']}"
            ),
            f"In-memory only: {source_report['source']['in_memory_only']}",
        ]
    )
    return lines
