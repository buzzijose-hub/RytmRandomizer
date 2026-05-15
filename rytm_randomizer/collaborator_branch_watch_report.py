"""Read-only collaborator branch watch report.

This module is passive and in-memory only. It records the last known
collaborator branch/PR watch state and the local commands an operator can run
to refresh that state. It does not query GitHub, check out branches, merge
branches, trigger GitHub Actions, open MIDI ports, send MIDI, execute active
behavior, or touch hardware.
"""

from __future__ import annotations

from copy import deepcopy


COLLABORATOR_BRANCH_WATCH_SAFETY = {
    "github_mutation": "absent",
    "branch_checkout": "absent",
    "branch_merge": "absent",
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

_OBSERVED_REMOTE_BRANCHES = (
    "modularize-v1.34",
    "docs/review-and-execution-plan",
    "codex/execute-eddie-plan",
)

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

_WATCH_RULES = {
    "expected_collaborator": "Eddie",
    "expected_github_owner": "edward-rosado",
    "implementation_branch_observed": False,
    "implementation_pr_observed": False,
    "direct_merge_allowed": False,
    "intake_required_before_review": True,
    "intake_required_before_merge": True,
}

_REFRESH_COMMANDS = {
    "remote_branches": "git ls-remote --heads origin",
    "pull_requests": (
        "gh pr list --repo buzzijose-hub/RytmRandomizer --state all "
        "--limit 20 --json number,title,headRefName,baseRefName,state,"
        "isDraft,updatedAt,url"
    ),
    "local_status": "git status --short",
    "v134_diff": "git diff -- rytm_hybrid_randomizer_v134.py",
}

_GITHUB_ACTIONS_POLICY = {
    "status": "manual_only",
    "automatic_pull_request_runs": False,
    "automatic_push_runs": False,
    "automatic_release_tag_runs": False,
    "report_triggers_actions": False,
    "no_pay_policy": True,
}

_NEXT_ACTIONS = (
    "wait for Eddie implementation branch or PR",
    "run collaborator implementation intake when branch or PR appears",
    "keep GitHub Actions manual-only unless explicitly triggered",
    "do not merge collaborator work before intake review",
)

__all__ = [
    "COLLABORATOR_BRANCH_WATCH_SAFETY",
    "build_collaborator_branch_watch_report",
    "format_collaborator_branch_watch_report",
    "summarize_collaborator_branch_watch_report",
]


def build_collaborator_branch_watch_report():
    """Return copied, in-memory collaborator branch watch data."""

    report = {
        "title": "RytmRandomizer Collaborator Branch Watch Report",
        "status": "waiting_for_external_implementation_branch",
        "current_branch": "codex/execute-eddie-plan",
        "current_pull_request": _CURRENT_PULL_REQUEST,
        "observed_remote_branches": _OBSERVED_REMOTE_BRANCHES,
        "observed_pull_requests": _OBSERVED_PULL_REQUESTS,
        "watch_rules": _WATCH_RULES,
        "refresh_commands": _REFRESH_COMMANDS,
        "github_actions_policy": _GITHUB_ACTIONS_POLICY,
        "next_actions": _NEXT_ACTIONS,
        "safety": COLLABORATOR_BRANCH_WATCH_SAFETY,
        "source": {
            "intake_protocol_path": (
                "Docs/COLLABORATOR_IMPLEMENTATION_BRANCH_INTAKE_PROTOCOL.md"
            ),
            "in_memory_only": True,
        },
    }
    return deepcopy(report)


def summarize_collaborator_branch_watch_report(report=None):
    """Return a compact copied collaborator branch watch summary."""

    source_report = (
        build_collaborator_branch_watch_report() if report is None else report
    )
    watch_rules = source_report["watch_rules"]
    actions_policy = source_report["github_actions_policy"]
    safety = source_report["safety"]

    return {
        "title": source_report["title"],
        "status": source_report["status"],
        "observed_remote_branch_count": len(
            source_report["observed_remote_branches"]
        ),
        "observed_pull_request_count": len(source_report["observed_pull_requests"]),
        "implementation_branch_observed": watch_rules[
            "implementation_branch_observed"
        ],
        "implementation_pr_observed": watch_rules["implementation_pr_observed"],
        "direct_merge_allowed": watch_rules["direct_merge_allowed"],
        "github_actions": actions_policy["status"],
        "report_triggers_actions": actions_policy["report_triggers_actions"],
        "real_midi": safety["real_midi"],
        "active_execution": safety["active_execution"],
        "hardware_required": safety["hardware_required"],
        "next_recommended_action": source_report["next_actions"][0],
    }


def _pull_request_line(pull_request):
    return (
        f"- #{pull_request['number']} {pull_request['author']} "
        f"{pull_request['branch']} -> {pull_request['base']} "
        f"({pull_request['role']}, implementation_branch: "
        f"{pull_request['implementation_branch']})"
    )


def format_collaborator_branch_watch_report(report=None):
    """Return deterministic collaborator branch watch report lines."""

    source_report = (
        build_collaborator_branch_watch_report() if report is None else report
    )
    current_pr = source_report["current_pull_request"]

    lines = [
        source_report["title"],
        "Current State:",
        f"- status: {source_report['status']}",
        f"- current_branch: {source_report['current_branch']}",
        f"- current_pr: #{current_pr['number']} {current_pr['title']}",
        "Observed Remote Branches:",
    ]

    for branch in source_report["observed_remote_branches"]:
        lines.append(f"- {branch}")

    lines.append("Observed Pull Requests:")
    for pull_request in source_report["observed_pull_requests"]:
        lines.append(_pull_request_line(pull_request))

    lines.append("Watch Rules:")
    for key, value in source_report["watch_rules"].items():
        lines.append(f"- {key}: {value}")

    lines.append("Refresh Commands:")
    for key, value in source_report["refresh_commands"].items():
        lines.append(f"- {key}: {value}")

    lines.append("GitHub Actions Policy:")
    for key, value in source_report["github_actions_policy"].items():
        lines.append(f"- {key}: {value}")

    lines.append("Next Actions:")
    for action in source_report["next_actions"]:
        lines.append(f"- {action}")

    lines.append("Safety:")
    for key, value in source_report["safety"].items():
        lines.append(f"- {key}: {value}")

    lines.extend(
        [
            f"Source: {source_report['source']['intake_protocol_path']}",
            f"In-memory only: {source_report['source']['in_memory_only']}",
        ]
    )
    return lines
