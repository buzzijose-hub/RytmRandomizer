"""Read-only collaborator implementation intake readiness report.

This module is passive and in-memory only. It records the current wait-state
for Eddie's implementation branch without querying GitHub, opening ports,
sending MIDI, executing commands, or touching hardware.
"""

from __future__ import annotations

from copy import deepcopy


COLLABORATOR_INTAKE_READINESS_BOUNDARY = {
    "real_midi": "absent",
    "mido": "absent",
    "port_opening": "absent",
    "midi_sending": "absent",
    "active_execution": "absent",
    "dispatch": "absent",
    "hardware_behavior": "absent",
    "hardware_required": False,
    "v134_reference": "untouched",
}

_CURRENT_PULL_REQUEST = {
    "number": 2,
    "title": "Execute Eddie review plan foundation",
    "branch": "codex/execute-eddie-plan",
    "base": "modularize-v1.34",
    "draft": True,
}

_OBSERVED_PULL_REQUESTS = (
    {
        "number": 1,
        "title": "Add code review findings and parallel execution plan",
        "author": "edward-rosado",
        "branch": "docs/review-and-execution-plan",
        "base": "modularize-v1.34",
        "role": "review_plan_source",
        "implementation_branch": False,
    },
    {
        "number": 2,
        "title": "Execute Eddie review plan foundation",
        "author": "buzzijose-hub",
        "branch": "codex/execute-eddie-plan",
        "base": "modularize-v1.34",
        "role": "draft_foundation_branch",
        "implementation_branch": False,
    },
)

_OBSERVED_REMOTE_BRANCHES = (
    "modularize-v1.34",
    "docs/review-and-execution-plan",
    "codex/execute-eddie-plan",
)

_REQUIRED_INTAKE_FIELDS = (
    "branch_name",
    "commit_hash",
    "base_branch",
    "test_result",
    "v134_status",
    "midi_ports_active_hardware_status",
)

_MERGE_POLICY = {
    "intake_before_review": True,
    "intake_before_merge": True,
    "direct_merge_allowed": False,
    "pr1_is_implementation": False,
    "implementation_branch_observed": False,
    "implementation_pr_observed": False,
}

_GITHUB_ACTIONS_POLICY = {
    "status": "manual_only",
    "daily_feedback": "local_closeout",
    "automatic_pull_request_runs": False,
    "automatic_push_runs": False,
    "automatic_release_tag_runs": False,
    "manual_gate_required_for_collaborator_intake": True,
    "no_pay_policy": True,
}

__all__ = [
    "COLLABORATOR_INTAKE_READINESS_BOUNDARY",
    "build_collaborator_intake_readiness_report",
    "format_collaborator_intake_readiness_report",
    "summarize_collaborator_intake_readiness_report",
]


def build_collaborator_intake_readiness_report():
    """Return copied, in-memory data about collaborator intake readiness."""

    report = {
        "title": "RytmRandomizer Collaborator Intake Readiness Report",
        "status": "waiting_for_implementation_branch",
        "current_branch": "codex/execute-eddie-plan",
        "current_pull_request": _CURRENT_PULL_REQUEST,
        "observed_pull_requests": _OBSERVED_PULL_REQUESTS,
        "observed_remote_branches": _OBSERVED_REMOTE_BRANCHES,
        "required_intake_fields": _REQUIRED_INTAKE_FIELDS,
        "merge_policy": _MERGE_POLICY,
        "github_actions_policy": _GITHUB_ACTIONS_POLICY,
        "safety": COLLABORATOR_INTAKE_READINESS_BOUNDARY,
        "source": {
            "checkpoint_path": (
                "Docs/COLLABORATOR_IMPLEMENTATION_WAIT_STATE_CHECKPOINT.md"
            ),
            "intake_protocol_path": (
                "Docs/COLLABORATOR_IMPLEMENTATION_BRANCH_INTAKE_PROTOCOL.md"
            ),
            "in_memory_only": True,
        },
    }
    return deepcopy(report)


def summarize_collaborator_intake_readiness_report(report=None):
    """Return a compact copied summary of collaborator intake readiness."""

    source_report = (
        build_collaborator_intake_readiness_report()
        if report is None
        else report
    )
    merge_policy = source_report["merge_policy"]
    actions_policy = source_report["github_actions_policy"]
    safety = source_report["safety"]

    return {
        "title": source_report["title"],
        "status": source_report["status"],
        "observed_pull_request_count": len(source_report["observed_pull_requests"]),
        "observed_remote_branch_count": len(source_report["observed_remote_branches"]),
        "implementation_branch_observed": merge_policy[
            "implementation_branch_observed"
        ],
        "implementation_pr_observed": merge_policy["implementation_pr_observed"],
        "direct_merge_allowed": merge_policy["direct_merge_allowed"],
        "github_actions": actions_policy["status"],
        "daily_feedback": actions_policy["daily_feedback"],
        "real_midi": safety["real_midi"],
        "active_execution": safety["active_execution"],
        "hardware_required": safety["hardware_required"],
    }


def _pull_request_line(pull_request):
    return (
        f"- #{pull_request['number']} {pull_request['author']} "
        f"{pull_request['branch']} -> {pull_request['base']} "
        f"({pull_request['role']}, implementation_branch: "
        f"{pull_request['implementation_branch']})"
    )


def format_collaborator_intake_readiness_report(report=None):
    """Return deterministic collaborator intake readiness report lines."""

    source_report = (
        build_collaborator_intake_readiness_report()
        if report is None
        else report
    )
    current_pr = source_report["current_pull_request"]

    lines = [
        source_report["title"],
        "Current State:",
        f"- status: {source_report['status']}",
        f"- current_branch: {source_report['current_branch']}",
        f"- current_pr: #{current_pr['number']} {current_pr['title']}",
        "Observed Pull Requests:",
    ]

    for pull_request in source_report["observed_pull_requests"]:
        lines.append(_pull_request_line(pull_request))

    lines.append("Observed Remote Branches:")
    for branch in source_report["observed_remote_branches"]:
        lines.append(f"- {branch}")

    lines.append("Required Intake Fields:")
    for field in source_report["required_intake_fields"]:
        lines.append(f"- {field}")

    lines.append("Merge Policy:")
    for key, value in source_report["merge_policy"].items():
        lines.append(f"- {key}: {value}")

    lines.append("GitHub Actions Policy:")
    for key, value in source_report["github_actions_policy"].items():
        lines.append(f"- {key}: {value}")

    lines.append("Safety:")
    for key, value in source_report["safety"].items():
        lines.append(f"- {key}: {value}")

    lines.extend(
        [
            f"Source: {source_report['source']['checkpoint_path']}",
            f"In-memory only: {source_report['source']['in_memory_only']}",
        ]
    )
    return lines
