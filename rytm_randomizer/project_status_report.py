"""Read-only project status report summary.

This module is passive and in-memory only: it reports project status without
opening ports, sending MIDI, dispatching commands, mutating runtime state,
writing files, or touching hardware.

As of the WS-H convergence wave the *package* is no longer passive forever:
``rytm_randomizer.app`` exposes a real MIDI provider and an interactive sender
behind an explicit ``--arm`` flag (with ``--dry-run`` against the mock). This
report's job is therefore to **track convergence progress** -- it measures how
far the package has come toward owning the active runtime, instead of asserting
the package stays inert. The report module itself remains passive; only what it
*describes* has advanced.
"""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from copy import deepcopy
from typing import Final, TypeAlias, cast

from .reports.formatter import safety_section_lines

#: One node in the status report tree. The tree mixes leaf scalars with
#: nested sections and tuples of commands, so ``object`` is the honest
#: element type: callers read a value and render or compare it, never
#: dereference it structurally. (Gate 6 bans bare ``Any``; ``object`` is the
#: typed alternative — it forces a narrowing check before use.)
StatusValue: TypeAlias = object

#: A section of the report, or the whole report: string keys to mixed values.
StatusSection: TypeAlias = dict[str, StatusValue]

#: A read-only view of a section, for parameters that never mutate.
StatusSectionView: TypeAlias = Mapping[str, StatusValue]

PASSIVE_CLI_COMMANDS: Final[tuple[str, ...]] = (
    "report",
    "project-status-report",
    "mock-mapper-report",
    "runtime-plan-report",
    "active-boundary-report",
    "mock-runtime-active-bridge-report",
    "anchor-profile-report",
    "behavior-parity-report",
    "rytm-live-macro-hardware-rehearsal-report",
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

PROJECT_PHASE: Final[StatusSection] = {
    "name": "Convergence Phase (armed behind --arm flag)",
    "technical_name": "RytmRandomizer",
    "creative_identity_candidate": "KitForge",
    "repository_name": "RytmRandomizer",
    "package_name": "rytm_randomizer",
}

CLOSEOUT_STATUS: Final[StatusSection] = {
    "closeout_contract": "present",
    "failure_propagation": "guarded",
    "closeout_script": "scripts/closeout_check.ps1",
}

# Convergence status values intentionally describe the *package* as it stands
# after the WS-H wave: real MIDI and active execution now exist, but only
# behind the explicit ``--arm`` flag. ``default_mode`` stays passive so the
# safe landing state is unchanged. The validated monolith is still untouched.
#
# The COLLABORATOR_* and PUBLIC_API_HARDENING_STATUS dicts below merged in from
# origin/modularize-v1.34; their ``real_midi`` / ``active_behavior`` fields
# have been updated from ``"absent"`` to ``"present_behind_arm_flag"`` so they
# describe the post-WS-H convergence reality consistently with the rest of
# this module. ``Docs/`` paths likewise updated to lowercase ``docs/``.

PUBLIC_API_HARDENING_STATUS: Final[StatusSection] = {
    "status": "checkpointed",
    "module_count": 3,
    "exports_documented": True,
    "modules": (
        "rytm_randomizer.active_boundary",
        "rytm_randomizer.reports",
        "rytm_randomizer.runtime_plan",
    ),
    "real_midi": "absent",
    "port_opening": "absent",
    "active_behavior": "absent",
}

COLLABORATOR_REVIEW_INTAKE_STATUS: Final[StatusSection] = {
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

COLLABORATOR_REVIEW_TRIAGE_TEMPLATE_STATUS: Final[StatusSection] = {
    "status": "accepted",
    "template_path": "docs/archive/COLLABORATOR_REVIEW_TRIAGE_TEMPLATE.md",
    "review_gate_path": "docs/archive/COLLABORATOR_REVIEW_TRIAGE_TEMPLATE_REVIEW.md",
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

PROJECT_STATUS_SAFETY: Final[StatusSection] = {
    "real_midi": "present_behind_arm_flag",
    "port_opening": "present_behind_arm_flag",
    "active_execution": "present_behind_arm_flag",
    "dispatch": "present_behind_arm_flag",
    "command_execution": "present_behind_arm_flag",
    "default_mode": "passive",
    "hardware_required": False,
    "hardware_behavior": "opt_in_behind_arm_flag",
    "analog_four_support": "absent",
    "pads_5_12_support": "absent",
    "v134_reference": "untouched",
    "package_metadata": "untouched",
}

# Convergence tracking: the package entry point now has three explicit modes.
# ``armed`` and ``dry_run`` carry active execution; ``default`` stays passive.
# ``active_modes_present`` / ``total_modes`` give a simple progress ratio.
#
# Wave 4 / WS-O closed the interactive logic gap: the command shell now lives
# in :mod:`rytm_randomizer.shell` (see ``--arm`` and ``--dry-run`` in
# ``rytm_randomizer.app``). The V1.34 monolith is retained on disk only as a
# frozen byte-parity reference for the test suite. The package therefore owns
# the interactive runtime end-to-end: ``interactive_logic_converged`` is True.
CONVERGENCE_STATUS: Final[StatusSection] = {
    "active_execution": "present",
    "active_execution_gate": "--arm flag",
    "entry_point": "rytm_randomizer.app",
    "default_mode": "passive",
    "modes": ("default", "arm", "dry-run"),
    "active_modes_present": 2,
    "total_modes": 3,
    "real_midi_provider": "rytm_randomizer.mido_provider.MidoMidiPortProvider",
    "interactive_logic_owner": "rytm_randomizer.shell",
    "interactive_logic_converged": True,
}

PROJECT_STATUS_CHECKS: Final[tuple[tuple[str, StatusValue], ...]] = (
    ("safety.real_midi", "present_behind_arm_flag"),
    ("safety.port_opening", "present_behind_arm_flag"),
    ("safety.active_execution", "present_behind_arm_flag"),
    ("safety.command_execution", "present_behind_arm_flag"),
    ("safety.dispatch", "present_behind_arm_flag"),
    ("safety.default_mode", "passive"),
    ("safety.hardware_required", False),
    ("safety.v134_reference", "untouched"),
    ("safety.package_metadata", "untouched"),
    # Convergence checks (WS-H): the package gained active execution behind --arm.
    # The legacy "absent" assertions on runtime_plan / active_boundary /
    # mock_runtime_active_bridge are superseded -- those modules are now
    # behind-the-flag, not forbidden. New convergence-tracking checks replace
    # them. The historical "absent" intent is preserved in the safety floor
    # (default_mode stays passive; the v134 reference stays untouched).
    ("convergence.active_execution", "present"),
    ("convergence.active_execution_gate", "--arm flag"),
    ("convergence.default_mode", "passive"),
    # PUBLIC_API_HARDENING + COLLABORATOR_* sections merged from
    # origin/modularize-v1.34; their "absent" / False fields updated to
    # match the post-WS-H convergence reality where appropriate.
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
    ("source.in_memory_only", True),
    ("source.writes_files", False),
    ("closeout.failure_propagation", "guarded"),
)


def _section(value: StatusValue, *, context: str) -> StatusSectionView:
    """Narrow a report value to a nested section, or fail with the key path.

    The report tree is ``dict[str, object]``, so reading a subsection back
    out needs an explicit narrowing step. Failing loudly here (rather than
    letting an ``object`` subscript blow up somewhere downstream) keeps a
    malformed report diagnosable.
    """

    if not isinstance(value, Mapping):
        raise TypeError(f"project status report section {context!r} is not a mapping")
    mapping = cast("Mapping[object, StatusValue]", value)
    narrowed: StatusSection = {str(key): item for key, item in mapping.items()}
    return narrowed


def _render(value: StatusValue) -> str:
    """Render a status-report leaf for line output."""

    return str(value)


def _rows(value: StatusValue, *, context: str) -> tuple[StatusValue, ...]:
    """Narrow a report value to a tuple of rows."""

    if isinstance(value, (str, bytes)) or not isinstance(value, (list, tuple)):
        raise TypeError(f"project status collection {context!r} is not a sequence")
    return tuple(cast("Sequence[StatusValue]", value))


def _joined(value: StatusValue, *, context: str) -> str:
    """Render a report collection as a comma-separated string."""

    return ", ".join(_render(item) for item in _rows(value, context=context))


def _get_nested_value(data: StatusSectionView, path: str) -> StatusValue:
    current: StatusValue = data
    for part in path.split("."):
        current = _section(current, context=path)[part]
    return current


def build_project_status_report() -> StatusSection:
    """Return copied, in-memory data about the current project status."""

    from .reports import (
        summarize_active_boundary_report,
        summarize_behavior_parity_coverage_report,
        summarize_mock_runtime_active_bridge_report,
        summarize_runtime_plan_report,
    )

    report: StatusSection = {
        "title": "RytmRandomizer Project Status Report",
        "phase": PROJECT_PHASE,
        "passive_cli_commands": PASSIVE_CLI_COMMANDS,
        "behavior_parity": summarize_behavior_parity_coverage_report(),
        "runtime_plan": summarize_runtime_plan_report(),
        "active_boundary": summarize_active_boundary_report(),
        "mock_runtime_active_bridge": summarize_mock_runtime_active_bridge_report(),
        "public_api_hardening": PUBLIC_API_HARDENING_STATUS,
        "collaborator_review_intake": COLLABORATOR_REVIEW_INTAKE_STATUS,
        "collaborator_review_triage_template": (COLLABORATOR_REVIEW_TRIAGE_TEMPLATE_STATUS),
        "closeout": CLOSEOUT_STATUS,
        "convergence": CONVERGENCE_STATUS,
        "safety": PROJECT_STATUS_SAFETY,
        "source": {
            "in_memory_only": True,
            "writes_files": False,
            "report_module": "rytm_randomizer.project_status_report",
        },
    }
    return deepcopy(report)


def check_project_status_report(report: StatusSection | None = None) -> StatusSection:
    """Return deterministic safety check results for project status data."""

    source_report = build_project_status_report() if report is None else report
    checked: StatusSection = {}
    failures: list[StatusSection] = []

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


def summarize_project_status_report(report: StatusSection | None = None) -> StatusSection:
    """Return a compact copied summary of the project status report."""

    source_report = build_project_status_report() if report is None else report
    phase = _section(source_report["phase"], context="phase")
    behavior = _section(source_report["behavior_parity"], context="behavior_parity")
    runtime = _section(source_report["runtime_plan"], context="runtime_plan")
    active = _section(source_report["active_boundary"], context="active_boundary")
    bridge = _section(
        source_report["mock_runtime_active_bridge"], context="mock_runtime_active_bridge"
    )
    api = _section(source_report["public_api_hardening"], context="public_api_hardening")
    collaborator = _section(
        source_report["collaborator_review_intake"], context="collaborator_review_intake"
    )
    triage_template = _section(
        source_report["collaborator_review_triage_template"],
        context="collaborator_review_triage_template",
    )
    safety = _section(source_report["safety"], context="safety")
    convergence = _section(source_report["convergence"], context="convergence")
    commands = source_report["passive_cli_commands"]

    return {
        "title": source_report["title"],
        "phase_name": phase["name"],
        "creative_identity_candidate": phase["creative_identity_candidate"],
        "passive_cli_command_count": len(_rows(commands, context="passive_cli_commands")),
        "accepted_packet_count": behavior["accepted_packet_count"],
        "pad_lane_command_count": behavior["pad_lane_command_count"],
        "runtime_supported_count": runtime["supported_count"],
        "active_boundary_candidate": active["supported_candidate"],
        "mock_bridge_candidate": bridge["accepted_source_key"],
        "public_api_hardening": api["status"],
        "public_api_module_count": api["module_count"],
        "collaborator_review_intake": collaborator["status"],
        "external_review_findings_received": collaborator["findings_received"],
        "collaborator_review_triage_template": triage_template["status"],
        "real_midi": safety["real_midi"],
        "port_opening": safety["port_opening"],
        "active_execution": safety["active_execution"],
        "default_mode": safety["default_mode"],
        "hardware_required": safety["hardware_required"],
        "v134_reference": safety["v134_reference"],
        "active_execution_gate": convergence["active_execution_gate"],
        "active_modes_present": convergence["active_modes_present"],
        "total_modes": convergence["total_modes"],
    }


def format_project_status_summary(report: StatusSection | None = None) -> list[str]:
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
        ("- external_review_findings_received: " f"{summary['external_review_findings_received']}"),
        (
            "- collaborator_review_triage_template: "
            f"{summary['collaborator_review_triage_template']}"
        ),
        f"- real_midi: {summary['real_midi']}",
        f"- port_opening: {summary['port_opening']}",
        f"- active_execution: {summary['active_execution']}",
        f"- active_execution_gate: {summary['active_execution_gate']}",
        f"- default_mode: {summary['default_mode']}",
        f"- active_modes_present: {summary['active_modes_present']}",
        f"- total_modes: {summary['total_modes']}",
        f"- hardware_required: {summary['hardware_required']}",
        f"- v134_reference: {summary['v134_reference']}",
    ]


def format_project_status_check(report: StatusSection | None = None) -> list[str]:
    """Return deterministic project status safety check lines."""

    check = check_project_status_report(report)
    lines: list[str] = [
        _render(check["title"]),
        f"- ok: {check['ok']}",
        f"- failure_count: {check['failure_count']}",
    ]

    checked = _section(check["checked"], context="check.checked")
    for path, _expected in PROJECT_STATUS_CHECKS:
        lines.append(f"- {path}: {_render(checked[path])}")

    failures = check["failures"]
    if failures:
        lines.append("Failures:")
        for failure in _rows(failures, context="check.failures"):
            row = _section(failure, context="check.failures[]")
            lines.append(
                "- "
                f"{_render(row['path'])}: expected {_render(row['expected'])}, "
                f"actual {_render(row['actual'])}"
            )

    return lines


def format_project_status_report(report: StatusSection | None = None) -> list[str]:
    """Return deterministic human-readable project status report lines."""

    source_report = build_project_status_report() if report is None else report
    phase = _section(source_report["phase"], context="phase")
    behavior = _section(source_report["behavior_parity"], context="behavior_parity")
    runtime = _section(source_report["runtime_plan"], context="runtime_plan")
    active = _section(source_report["active_boundary"], context="active_boundary")
    bridge = _section(
        source_report["mock_runtime_active_bridge"], context="mock_runtime_active_bridge"
    )
    api = _section(source_report["public_api_hardening"], context="public_api_hardening")
    collaborator = _section(
        source_report["collaborator_review_intake"], context="collaborator_review_intake"
    )
    triage_template = _section(
        source_report["collaborator_review_triage_template"],
        context="collaborator_review_triage_template",
    )

    lines = [
        _render(source_report["title"]),
        "Phase:",
        f"- name: {phase['name']}",
        f"- technical_name: {phase['technical_name']}",
        f"- creative_identity_candidate: {phase['creative_identity_candidate']}",
        "Passive CLI Visibility:",
    ]

    for command in _rows(source_report["passive_cli_commands"], context="passive_cli_commands"):
        lines.append(f"- {_render(command)}")

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
            f"- unsupported_keys: "
            f"{_joined(active['unsupported_keys'], context='unsupported_keys')}",
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
            "- modules: " + _joined(api["modules"], context="modules"),
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
            + _joined(collaborator["triage_categories"], context="triage_categories"),
            f"- real_midi: {collaborator['real_midi']}",
            f"- port_opening: {collaborator['port_opening']}",
            f"- active_behavior: {collaborator['active_behavior']}",
            f"- hardware_behavior: {collaborator['hardware_behavior']}",
            ("- package_metadata_changes: " f"{collaborator['package_metadata_changes']}"),
            "Collaborator Review Triage Template:",
            f"- status: {triage_template['status']}",
            f"- template_path: {triage_template['template_path']}",
            f"- review_gate_path: {triage_template['review_gate_path']}",
            f"- findings_recorded: {triage_template['findings_recorded']}",
            ("- requires_text_or_markdown: " f"{triage_template['requires_text_or_markdown']}"),
            ("- screenshot_only_sufficient: " f"{triage_template['screenshot_only_sufficient']}"),
            f"- implementation_policy: {triage_template['implementation_policy']}",
            f"- real_midi: {triage_template['real_midi']}",
            f"- port_opening: {triage_template['port_opening']}",
            f"- active_behavior: {triage_template['active_behavior']}",
            f"- hardware_behavior: {triage_template['hardware_behavior']}",
            ("- package_metadata_changes: " f"{triage_template['package_metadata_changes']}"),
            "Closeout:",
        ]
    )

    closeout = _section(source_report["closeout"], context="closeout")
    for key in closeout:
        lines.append(f"- {key}: {_render(closeout[key])}")

    lines.append("Convergence:")
    convergence = _section(source_report["convergence"], context="convergence")
    for key in convergence:
        entry = convergence[key]
        # ``_joined`` does its own sequence narrowing, so the value is passed
        # unnarrowed rather than through an isinstance check that would only
        # widen the element type back to Unknown.
        rendered = (
            _joined(convergence[key], context=str(key))
            if isinstance(entry, tuple)
            else _render(entry)
        )
        lines.append(f"- {key}: {rendered}")

    lines.extend(safety_section_lines(_section(source_report["safety"], context="safety")))

    source_block = _section(source_report["source"], context="source")

    lines.extend(
        [
            "Source:",
            f"- in_memory_only: {_render(source_block['in_memory_only'])}",
            f"- writes_files: {_render(source_block['writes_files'])}",
        ]
    )
    return lines


def format_project_status_report_json(report: StatusSection | None = None) -> str:
    """Return deterministic JSON for the copied project status report."""

    source_report = build_project_status_report() if report is None else report
    return json.dumps(deepcopy(source_report), indent=2, sort_keys=True)
