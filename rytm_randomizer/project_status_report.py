"""Read-only project status report summary.

This module is passive and in-memory only. It reports current project status
without opening ports, sending MIDI, wiring active execution, dispatching
commands, mutating runtime state, writing files, or touching hardware.
"""

from __future__ import annotations

from copy import deepcopy
import json


PASSIVE_CLI_COMMANDS = (
    "report",
    "project-status-report",
    "mock-mapper-report",
    "runtime-plan-report",
    "active-boundary-report",
    "mock-runtime-active-bridge-report",
    "anchor-profile-report",
    "behavior-parity-report",
    "collaborator-intake-readiness-report",
    "collaborator-branch-watch",
    "operator-status-report",
    "list-commands",
    "list-scenes",
    "list-group-profiles",
    "search-commands",
    "search-scenes",
    "search-group-profiles",
    "inspect-command",
    "inspect-scene",
    "inspect-group-profile",
    "preview-command",
    "preview-scene",
    "preview-group-profile",
)

PROJECT_PHASE = {
    "name": "Passive/Mock Runtime Visibility Phase",
    "technical_name": "RytmRandomizer",
    "creative_identity_candidate": "KitForge",
    "repository_name": "RytmRandomizer",
    "package_name": "rytm_randomizer",
}

CLOSEOUT_STATUS = {
    "closeout_contract": "present",
    "failure_propagation": "guarded",
    "closeout_script": "Scripts/closeout_check.ps1",
}

PUBLIC_API_HARDENING_STATUS = {
    "status": "checkpointed",
    "module_count": 5,
    "exports_documented": True,
    "modules": (
        "rytm_randomizer.active_boundary",
        "rytm_randomizer.active_boundary_report",
        "rytm_randomizer.runtime_plan",
        "rytm_randomizer.runtime_plan_report",
        "rytm_randomizer.mock_runtime_active_bridge_report",
    ),
    "real_midi": "absent",
    "port_opening": "absent",
    "active_behavior": "absent",
}

COLLABORATOR_REVIEW_INTAKE_STATUS = {
    "status": "checkpointed",
    "collaborator": "Eddie",
    "review_source": "external_ai_assisted_review",
    "findings_received": False,
    "required_format": "text_or_markdown",
    "implementation_policy": "verify_before_implementing",
    "triage_categories": (
        "valid_and_urgent",
        "valid_but_later",
        "already_handled",
        "needs_more_evidence",
        "not_applicable",
        "conflicts_with_safety_constraints",
        "conflicts_with_project_direction",
    ),
    "real_midi": "absent",
    "port_opening": "absent",
    "active_behavior": "absent",
    "hardware_behavior": "absent",
    "package_metadata_changes": "requires_explicit_approval",
}

COLLABORATOR_REVIEW_TRIAGE_TEMPLATE_STATUS = {
    "status": "accepted",
    "template_path": "Docs/COLLABORATOR_REVIEW_TRIAGE_TEMPLATE.md",
    "review_gate_path": "Docs/COLLABORATOR_REVIEW_TRIAGE_TEMPLATE_REVIEW.md",
    "findings_recorded": False,
    "requires_text_or_markdown": True,
    "screenshot_only_sufficient": False,
    "implementation_policy": "triage_before_implementing",
    "real_midi": "absent",
    "port_opening": "absent",
    "active_behavior": "absent",
    "hardware_behavior": "absent",
    "package_metadata_changes": "requires_explicit_approval",
}

COLLABORATOR_IMPLEMENTATION_BRANCH_INTAKE_STATUS = {
    "status": "waiting_for_branch",
    "collaborator": "Eddie",
    "request_packet_path": "Docs/EDDIE_IMPLEMENTATION_REVIEW_REQUEST_PACKET.md",
    "intake_protocol_path": (
        "Docs/COLLABORATOR_IMPLEMENTATION_BRANCH_INTAKE_PROTOCOL.md"
    ),
    "implementation_branch_observed": False,
    "implementation_pr_observed": False,
    "required_info": (
        "branch_name",
        "commit_hash",
        "base_branch",
        "test_result",
        "v134_status",
        "midi_ports_active_hardware_status",
    ),
    "merge_policy": "intake_before_merge",
    "direct_merge_allowed": False,
    "real_midi": "absent",
    "port_opening": "absent",
    "active_behavior": "absent",
    "hardware_behavior": "absent",
}

GITHUB_ACTIONS_MANUAL_GATE_STATUS = {
    "status": "manual_only",
    "policy": "gated_pipeline_only",
    "daily_feedback": "local_closeout",
    "default_test_workflow": ".github/workflows/test.yml",
    "full_matrix_workflow": ".github/workflows/test-full-matrix.yml",
    "release_workflow": ".github/workflows/release.yml",
    "codeql_workflow": ".github/workflows/codeql.yml",
    "automatic_pull_request_runs": False,
    "automatic_push_runs": False,
    "automatic_release_tag_runs": False,
    "manual_gate_required_for_pr_readiness": True,
    "manual_gate_required_for_major_merge": True,
    "manual_gate_required_for_collaborator_intake": True,
    "actions_minute_policy": "spend_only_on_explicit_gate",
    "no_pay_policy": True,
    "real_midi": "absent",
    "port_opening": "absent",
    "active_behavior": "absent",
    "hardware_behavior": "absent",
}

PROJECT_STATUS_SAFETY = {
    "real_midi": "absent",
    "port_opening": "absent",
    "active_execution": "absent",
    "dispatch": "absent",
    "command_execution": "absent",
    "hardware_required": False,
    "hardware_behavior": "absent",
    "analog_four_support": "absent",
    "pads_5_12_support": "absent",
    "v134_reference": "import_safe_wrapped",
    "package_metadata": "declared",
}

PROJECT_STATUS_CHECKS = (
    ("safety.real_midi", "absent"),
    ("safety.port_opening", "absent"),
    ("safety.active_execution", "absent"),
    ("safety.command_execution", "absent"),
    ("safety.dispatch", "absent"),
    ("safety.hardware_required", False),
    ("safety.v134_reference", "import_safe_wrapped"),
    ("safety.package_metadata", "declared"),
    ("runtime_plan.runtime_execution", "absent"),
    ("active_boundary.active_cli_behavior", "absent"),
    ("mock_runtime_active_bridge.emits_messages", False),
    ("public_api_hardening.status", "checkpointed"),
    ("public_api_hardening.exports_documented", True),
    ("public_api_hardening.real_midi", "absent"),
    ("public_api_hardening.port_opening", "absent"),
    ("public_api_hardening.active_behavior", "absent"),
    ("collaborator_review_intake.status", "checkpointed"),
    ("collaborator_review_intake.findings_received", False),
    ("collaborator_review_intake.implementation_policy", "verify_before_implementing"),
    ("collaborator_review_intake.real_midi", "absent"),
    ("collaborator_review_intake.port_opening", "absent"),
    ("collaborator_review_intake.active_behavior", "absent"),
    ("collaborator_review_intake.hardware_behavior", "absent"),
    ("collaborator_review_triage_template.status", "accepted"),
    ("collaborator_review_triage_template.findings_recorded", False),
    ("collaborator_review_triage_template.screenshot_only_sufficient", False),
    (
        "collaborator_review_triage_template.implementation_policy",
        "triage_before_implementing",
    ),
    ("collaborator_review_triage_template.real_midi", "absent"),
    ("collaborator_review_triage_template.port_opening", "absent"),
    ("collaborator_review_triage_template.active_behavior", "absent"),
    ("collaborator_review_triage_template.hardware_behavior", "absent"),
    ("collaborator_implementation_branch_intake.status", "waiting_for_branch"),
    (
        "collaborator_implementation_branch_intake.implementation_branch_observed",
        False,
    ),
    (
        "collaborator_implementation_branch_intake.implementation_pr_observed",
        False,
    ),
    (
        "collaborator_implementation_branch_intake.merge_policy",
        "intake_before_merge",
    ),
    ("collaborator_implementation_branch_intake.direct_merge_allowed", False),
    ("collaborator_implementation_branch_intake.real_midi", "absent"),
    ("collaborator_implementation_branch_intake.port_opening", "absent"),
    ("collaborator_implementation_branch_intake.active_behavior", "absent"),
    ("collaborator_implementation_branch_intake.hardware_behavior", "absent"),
    ("github_actions_manual_gate.status", "manual_only"),
    ("github_actions_manual_gate.automatic_pull_request_runs", False),
    ("github_actions_manual_gate.automatic_push_runs", False),
    ("github_actions_manual_gate.automatic_release_tag_runs", False),
    ("github_actions_manual_gate.no_pay_policy", True),
    ("github_actions_manual_gate.real_midi", "absent"),
    ("github_actions_manual_gate.port_opening", "absent"),
    ("github_actions_manual_gate.active_behavior", "absent"),
    ("github_actions_manual_gate.hardware_behavior", "absent"),
    ("source.in_memory_only", True),
    ("source.writes_files", False),
    ("closeout.failure_propagation", "guarded"),
)


def _get_nested_value(data, path):
    current = data
    for part in path.split("."):
        current = current[part]
    return current


def build_project_status_report():
    """Return copied, in-memory data about the current project status."""

    from .active_boundary_report import summarize_active_boundary_report
    from .behavior_parity_coverage_report import (
        summarize_behavior_parity_coverage_report,
    )
    from .mock_runtime_active_bridge_report import (
        summarize_mock_runtime_active_bridge_report,
    )
    from .runtime_plan_report import summarize_runtime_plan_report

    report = {
        "title": "RytmRandomizer Project Status Report",
        "phase": PROJECT_PHASE,
        "passive_cli_commands": PASSIVE_CLI_COMMANDS,
        "behavior_parity": summarize_behavior_parity_coverage_report(),
        "runtime_plan": summarize_runtime_plan_report(),
        "active_boundary": summarize_active_boundary_report(),
        "mock_runtime_active_bridge": summarize_mock_runtime_active_bridge_report(),
        "public_api_hardening": PUBLIC_API_HARDENING_STATUS,
        "collaborator_review_intake": COLLABORATOR_REVIEW_INTAKE_STATUS,
        "collaborator_review_triage_template": (
            COLLABORATOR_REVIEW_TRIAGE_TEMPLATE_STATUS
        ),
        "collaborator_implementation_branch_intake": (
            COLLABORATOR_IMPLEMENTATION_BRANCH_INTAKE_STATUS
        ),
        "github_actions_manual_gate": GITHUB_ACTIONS_MANUAL_GATE_STATUS,
        "closeout": CLOSEOUT_STATUS,
        "safety": PROJECT_STATUS_SAFETY,
        "source": {
            "in_memory_only": True,
            "writes_files": False,
            "report_module": "rytm_randomizer.project_status_report",
        },
    }
    return deepcopy(report)


def check_project_status_report(report=None):
    """Return deterministic safety check results for project status data."""

    source_report = build_project_status_report() if report is None else report
    checked = {}
    failures = []

    for path, expected in PROJECT_STATUS_CHECKS:
        actual = _get_nested_value(source_report, path)
        checked[path] = actual
        if actual != expected:
            failures.append({"path": path, "expected": expected, "actual": actual})

    return {
        "title": "RytmRandomizer Project Status Check",
        "ok": not failures,
        "failure_count": len(failures),
        "failures": failures,
        "checked": checked,
    }


def summarize_project_status_report(report=None):
    """Return a compact copied summary of the project status report."""

    source_report = build_project_status_report() if report is None else report
    return {
        "title": source_report["title"],
        "phase_name": source_report["phase"]["name"],
        "creative_identity_candidate": source_report["phase"][
            "creative_identity_candidate"
        ],
        "passive_cli_command_count": len(source_report["passive_cli_commands"]),
        "accepted_packet_count": source_report["behavior_parity"][
            "accepted_packet_count"
        ],
        "pad_lane_command_count": source_report["behavior_parity"][
            "pad_lane_command_count"
        ],
        "runtime_supported_count": source_report["runtime_plan"]["supported_count"],
        "active_boundary_candidate": source_report["active_boundary"][
            "supported_candidate"
        ],
        "mock_bridge_candidate": source_report["mock_runtime_active_bridge"][
            "accepted_source_key"
        ],
        "public_api_hardening": source_report["public_api_hardening"]["status"],
        "public_api_module_count": source_report["public_api_hardening"][
            "module_count"
        ],
        "collaborator_review_intake": source_report["collaborator_review_intake"][
            "status"
        ],
        "external_review_findings_received": source_report[
            "collaborator_review_intake"
        ]["findings_received"],
        "collaborator_review_triage_template": source_report[
            "collaborator_review_triage_template"
        ]["status"],
        "collaborator_implementation_branch_intake": source_report[
            "collaborator_implementation_branch_intake"
        ]["status"],
        "external_implementation_branch_observed": source_report[
            "collaborator_implementation_branch_intake"
        ]["implementation_branch_observed"],
        "external_implementation_pr_observed": source_report[
            "collaborator_implementation_branch_intake"
        ]["implementation_pr_observed"],
        "github_actions_manual_gate": source_report["github_actions_manual_gate"][
            "status"
        ],
        "github_actions_auto_pr_runs": source_report["github_actions_manual_gate"][
            "automatic_pull_request_runs"
        ],
        "github_actions_no_pay_policy": source_report["github_actions_manual_gate"][
            "no_pay_policy"
        ],
        "real_midi": source_report["safety"]["real_midi"],
        "port_opening": source_report["safety"]["port_opening"],
        "active_execution": source_report["safety"]["active_execution"],
        "hardware_required": source_report["safety"]["hardware_required"],
        "v134_reference": source_report["safety"]["v134_reference"],
    }


def format_project_status_summary(report=None):
    """Return deterministic compact project status summary lines."""

    summary = summarize_project_status_report(report)
    return [
        "RytmRandomizer Project Status Summary",
        f"- phase_name: {summary['phase_name']}",
        f"- creative_identity_candidate: {summary['creative_identity_candidate']}",
        f"- passive_cli_command_count: {summary['passive_cli_command_count']}",
        f"- accepted_packet_count: {summary['accepted_packet_count']}",
        f"- pad_lane_command_count: {summary['pad_lane_command_count']}",
        f"- runtime_supported_count: {summary['runtime_supported_count']}",
        f"- active_boundary_candidate: {summary['active_boundary_candidate']}",
        f"- mock_bridge_candidate: {summary['mock_bridge_candidate']}",
        f"- public_api_hardening: {summary['public_api_hardening']}",
        f"- public_api_module_count: {summary['public_api_module_count']}",
        f"- collaborator_review_intake: {summary['collaborator_review_intake']}",
        (
            "- external_review_findings_received: "
            f"{summary['external_review_findings_received']}"
        ),
        (
            "- collaborator_review_triage_template: "
            f"{summary['collaborator_review_triage_template']}"
        ),
        (
            "- collaborator_implementation_branch_intake: "
            f"{summary['collaborator_implementation_branch_intake']}"
        ),
        (
            "- external_implementation_branch_observed: "
            f"{summary['external_implementation_branch_observed']}"
        ),
        (
            "- external_implementation_pr_observed: "
            f"{summary['external_implementation_pr_observed']}"
        ),
        f"- github_actions_manual_gate: {summary['github_actions_manual_gate']}",
        f"- github_actions_auto_pr_runs: {summary['github_actions_auto_pr_runs']}",
        (
            "- github_actions_no_pay_policy: "
            f"{summary['github_actions_no_pay_policy']}"
        ),
        f"- real_midi: {summary['real_midi']}",
        f"- port_opening: {summary['port_opening']}",
        f"- active_execution: {summary['active_execution']}",
        f"- hardware_required: {summary['hardware_required']}",
        f"- v134_reference: {summary['v134_reference']}",
    ]


def format_project_status_check(report=None):
    """Return deterministic project status safety check lines."""

    check = check_project_status_report(report)
    lines = [
        check["title"],
        f"- ok: {check['ok']}",
        f"- failure_count: {check['failure_count']}",
    ]

    for path, _expected in PROJECT_STATUS_CHECKS:
        lines.append(f"- {path}: {check['checked'][path]}")

    if check["failures"]:
        lines.append("Failures:")
        for failure in check["failures"]:
            lines.append(
                "- "
                f"{failure['path']}: expected {failure['expected']}, "
                f"actual {failure['actual']}"
            )

    return lines


def format_project_status_report(report=None):
    """Return deterministic human-readable project status report lines."""

    source_report = build_project_status_report() if report is None else report
    phase = source_report["phase"]
    behavior = source_report["behavior_parity"]
    runtime = source_report["runtime_plan"]
    active = source_report["active_boundary"]
    bridge = source_report["mock_runtime_active_bridge"]
    api = source_report["public_api_hardening"]
    collaborator = source_report["collaborator_review_intake"]
    triage_template = source_report["collaborator_review_triage_template"]
    implementation_intake = source_report["collaborator_implementation_branch_intake"]
    actions_gate = source_report["github_actions_manual_gate"]

    lines = [
        source_report["title"],
        "Phase:",
        f"- name: {phase['name']}",
        f"- technical_name: {phase['technical_name']}",
        f"- creative_identity_candidate: {phase['creative_identity_candidate']}",
        "Passive CLI Visibility:",
    ]

    for command in source_report["passive_cli_commands"]:
        lines.append(f"- {command}")

    lines.extend(
        [
            "Behavior Parity:",
            f"- accepted_packet_count: {behavior['accepted_packet_count']}",
            (
                "- selected_isolated_pad_packet_count: "
                f"{behavior['selected_isolated_pad_packet_count']}"
            ),
            f"- pad_lane_packet_count: {behavior['pad_lane_packet_count']}",
            f"- pad_lane_command_count: {behavior['pad_lane_command_count']}",
            (
                "- runtime_adjacent_safe_failure_count: "
                f"{behavior['runtime_adjacent_safe_failure_count']}"
            ),
            f"- parked_scope_count: {behavior['parked_scope_count']}",
            "Runtime Plan:",
            f"- supported_count: {runtime['supported_count']}",
            f"- parked_count: {runtime['parked_count']}",
            f"- unsupported_count: {runtime['unsupported_count']}",
            f"- runtime_execution: {runtime['runtime_execution']}",
            "Active Boundary:",
            f"- supported_candidate: {active['supported_candidate']}",
            f"- unsupported_keys: {', '.join(active['unsupported_keys'])}",
            f"- active_cli_behavior: {active['active_cli_behavior']}",
            "Mock Runtime Active Bridge:",
            f"- accepted_source_key: {bridge['accepted_source_key']}",
            f"- rejected_count: {bridge['rejected_count']}",
            f"- parked_count: {bridge['parked_count']}",
            f"- emits_messages: {bridge['emits_messages']}",
            "Public API Hardening:",
            f"- status: {api['status']}",
            f"- module_count: {api['module_count']}",
            f"- exports_documented: {api['exports_documented']}",
            "- modules: " + ", ".join(api["modules"]),
            f"- real_midi: {api['real_midi']}",
            f"- port_opening: {api['port_opening']}",
            f"- active_behavior: {api['active_behavior']}",
            "Collaborator Review Intake:",
            f"- status: {collaborator['status']}",
            f"- collaborator: {collaborator['collaborator']}",
            f"- review_source: {collaborator['review_source']}",
            f"- findings_received: {collaborator['findings_received']}",
            f"- required_format: {collaborator['required_format']}",
            f"- implementation_policy: {collaborator['implementation_policy']}",
            "- triage_categories: "
            + ", ".join(collaborator["triage_categories"]),
            f"- real_midi: {collaborator['real_midi']}",
            f"- port_opening: {collaborator['port_opening']}",
            f"- active_behavior: {collaborator['active_behavior']}",
            f"- hardware_behavior: {collaborator['hardware_behavior']}",
            (
                "- package_metadata_changes: "
                f"{collaborator['package_metadata_changes']}"
            ),
            "Collaborator Review Triage Template:",
            f"- status: {triage_template['status']}",
            f"- template_path: {triage_template['template_path']}",
            f"- review_gate_path: {triage_template['review_gate_path']}",
            f"- findings_recorded: {triage_template['findings_recorded']}",
            (
                "- requires_text_or_markdown: "
                f"{triage_template['requires_text_or_markdown']}"
            ),
            (
                "- screenshot_only_sufficient: "
                f"{triage_template['screenshot_only_sufficient']}"
            ),
            f"- implementation_policy: {triage_template['implementation_policy']}",
            f"- real_midi: {triage_template['real_midi']}",
            f"- port_opening: {triage_template['port_opening']}",
            f"- active_behavior: {triage_template['active_behavior']}",
            f"- hardware_behavior: {triage_template['hardware_behavior']}",
            (
                "- package_metadata_changes: "
                f"{triage_template['package_metadata_changes']}"
            ),
            "Collaborator Implementation Branch Intake:",
            f"- status: {implementation_intake['status']}",
            f"- collaborator: {implementation_intake['collaborator']}",
            f"- request_packet_path: {implementation_intake['request_packet_path']}",
            f"- intake_protocol_path: {implementation_intake['intake_protocol_path']}",
            (
                "- implementation_branch_observed: "
                f"{implementation_intake['implementation_branch_observed']}"
            ),
            (
                "- implementation_pr_observed: "
                f"{implementation_intake['implementation_pr_observed']}"
            ),
            "- required_info: " + ", ".join(implementation_intake["required_info"]),
            f"- merge_policy: {implementation_intake['merge_policy']}",
            f"- direct_merge_allowed: {implementation_intake['direct_merge_allowed']}",
            f"- real_midi: {implementation_intake['real_midi']}",
            f"- port_opening: {implementation_intake['port_opening']}",
            f"- active_behavior: {implementation_intake['active_behavior']}",
            f"- hardware_behavior: {implementation_intake['hardware_behavior']}",
            "GitHub Actions Manual Gate:",
            f"- status: {actions_gate['status']}",
            f"- policy: {actions_gate['policy']}",
            f"- daily_feedback: {actions_gate['daily_feedback']}",
            f"- default_test_workflow: {actions_gate['default_test_workflow']}",
            f"- full_matrix_workflow: {actions_gate['full_matrix_workflow']}",
            f"- release_workflow: {actions_gate['release_workflow']}",
            f"- codeql_workflow: {actions_gate['codeql_workflow']}",
            (
                "- automatic_pull_request_runs: "
                f"{actions_gate['automatic_pull_request_runs']}"
            ),
            f"- automatic_push_runs: {actions_gate['automatic_push_runs']}",
            (
                "- automatic_release_tag_runs: "
                f"{actions_gate['automatic_release_tag_runs']}"
            ),
            (
                "- manual_gate_required_for_pr_readiness: "
                f"{actions_gate['manual_gate_required_for_pr_readiness']}"
            ),
            (
                "- manual_gate_required_for_major_merge: "
                f"{actions_gate['manual_gate_required_for_major_merge']}"
            ),
            (
                "- manual_gate_required_for_collaborator_intake: "
                f"{actions_gate['manual_gate_required_for_collaborator_intake']}"
            ),
            f"- actions_minute_policy: {actions_gate['actions_minute_policy']}",
            f"- no_pay_policy: {actions_gate['no_pay_policy']}",
            f"- real_midi: {actions_gate['real_midi']}",
            f"- port_opening: {actions_gate['port_opening']}",
            f"- active_behavior: {actions_gate['active_behavior']}",
            f"- hardware_behavior: {actions_gate['hardware_behavior']}",
            "Closeout:",
        ]
    )

    for key, value in source_report["closeout"].items():
        lines.append(f"- {key}: {value}")

    lines.append("Safety:")
    for key, value in source_report["safety"].items():
        lines.append(f"- {key}: {value}")

    lines.extend(
        [
            "Source:",
            f"- in_memory_only: {source_report['source']['in_memory_only']}",
            f"- writes_files: {source_report['source']['writes_files']}",
        ]
    )
    return lines


def format_project_status_report_json(report=None):
    """Return deterministic JSON for the copied project status report."""

    source_report = build_project_status_report() if report is None else report
    return json.dumps(deepcopy(source_report), indent=2, sort_keys=True)
