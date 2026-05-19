import importlib
import json
import subprocess
import sys
from pathlib import Path

import pytest

# WS-M4: mark this module as fast-suite; pytest -m fast skips the 505
# warm-worker V1.34 parity fixtures and runs in <60s.
pytestmark = pytest.mark.fast

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def test_importing_project_status_report_prints_nothing():
    result = subprocess.run(
        [sys.executable, "-c", "import rytm_randomizer.project_status_report"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert result.stdout == ""
    assert result.stderr == ""


def test_project_status_report_summarizes_current_project_state():
    from rytm_randomizer.project_status_report import build_project_status_report

    report = build_project_status_report()

    assert report["title"] == "RytmRandomizer Project Status Report"
    assert report["phase"] == {
        "name": "Convergence Phase (armed behind --arm flag)",
        "technical_name": "RytmRandomizer",
        "creative_identity_candidate": "KitForge",
        "repository_name": "RytmRandomizer",
        "package_name": "rytm_randomizer",
    }
    assert report["behavior_parity"]["accepted_packet_count"] == 12
    assert report["behavior_parity"]["pad_lane_packet_count"] == 4
    assert report["behavior_parity"]["pad_lane_command_count"] == 38
    assert report["runtime_plan"]["supported_count"] == 2
    assert report["runtime_plan"]["parked_count"] == 1
    assert report["active_boundary"]["supported_candidate"] == "group_profile:2"
    assert report["mock_runtime_active_bridge"]["accepted_source_key"] == "2"
    assert report["closeout"] == {
        "closeout_contract": "present",
        "failure_propagation": "guarded",
        "closeout_script": "Scripts/closeout_check.ps1",
    }


def test_project_status_report_records_passive_cli_visibility():
    from rytm_randomizer.project_status_report import build_project_status_report

    report = build_project_status_report()

    assert report["passive_cli_commands"] == (
        "report",
        "project-status-report",
        "mock-mapper-report",
        "runtime-plan-report",
        "active-boundary-report",
        "mock-runtime-active-bridge-report",
        "anchor-profile-report",
        "behavior-parity-report",
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


def test_project_status_report_tracks_convergence_behind_arm_flag():
    from rytm_randomizer.project_status_report import build_project_status_report

    report = build_project_status_report()

    # Active execution now EXISTS in the package -- but only behind --arm.
    # The default landing mode stays passive, and the validated monolith is
    # still untouched. This report tracks that progress instead of forbidding
    # it.
    assert report["safety"] == {
        "real_midi": "present_behind_arm_flag",
        "port_opening": "present_behind_arm_flag",
        "active_execution": "present_behind_arm_flag",
        "dispatch": "present_behind_arm_flag",
        "command_execution": "present_behind_arm_flag",
        "default_mode": "passive",
        "hardware_required": False,
        "hardware_behavior": "opt_in_behind_arm_flag",
        "analog_four_support": "present_behind_arm_flag",
        "pads_5_12_support": "present_behind_arm_flag",
        "v134_reference": "untouched",
        "package_metadata": "untouched",
    }

    assert report["convergence"] == {
        "active_execution": "present",
        "active_execution_gate": "--arm flag",
        "entry_point": "rytm_randomizer.app",
        "default_mode": "passive",
        "modes": ("default", "arm", "dry-run"),
        "active_modes_present": 2,
        "total_modes": 3,
        "real_midi_provider": ("rytm_randomizer.mido_provider.MidoMidiPortProvider"),
        "interactive_logic_owner": "rytm_randomizer.shell",
        "interactive_logic_converged": True,
    }


def test_project_status_report_records_first_hardware_validation_pass():
    from rytm_randomizer.project_status_report import build_project_status_report

    report = build_project_status_report()

    assert report["hardware_validation"] == {
        "status": "first_end_user_pass",
        "date": "2026-05-15",
        "validated_device": "Elektron Analog Rytm MKII",
        "operator": "Jose Buzzi",
        "collaborator": "Eddie",
        "installer_wheel": "rytm_randomizer-1.34.0-py3-none-any.whl",
        "dry_run": "passed",
        "arm_port_open": "passed",
        "audible_scene_mutation": "confirmed_by_operator",
        "anchor_return": "confirmed_by_operator",
        "guardrails": (
            "profile_prompt_rejected_scn_without_midi",
            "scn_command_menu_no_midi",
            "bare_depth_digit_no_midi",
        ),
        "canonical_scene_flow": ("S1A", "S3A", "S3B", "S4B", "S5", "Z"),
        "analog_four_support": "not_in_first_pass",
        "pads_5_12_support": "not_in_first_pass",
    }


def test_project_status_report_records_current_runtime_validation_status():
    from rytm_randomizer.project_status_report import build_project_status_report

    report = build_project_status_report()

    assert report["current_runtime_validation"] == {
        "status": "dual_machine_lane_gate_ready",
        "date": "2026-05-19",
        "analog_four_support": "operator_smoke_confirmed",
        "pads_5_12_support": "operator_smoke_confirmed",
        "dual_machine_lane_validation_guide": "software_ready",
        "all_lane_validation_guide": "software_ready",
        "pr37_required_checks": "passed",
        "next_hardware_scope": "lane_scoped_manual_validation",
    }


def test_project_status_report_records_public_api_hardening_checkpoint():
    from rytm_randomizer.project_status_report import build_project_status_report

    report = build_project_status_report()

    assert report["public_api_hardening"] == {
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


def test_project_status_report_records_collaborator_review_intake_checkpoint():
    from rytm_randomizer.project_status_report import build_project_status_report

    report = build_project_status_report()

    assert report["collaborator_review_intake"] == {
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


def test_project_status_report_records_collaborator_review_triage_template():
    from rytm_randomizer.project_status_report import build_project_status_report

    report = build_project_status_report()

    assert report["collaborator_review_triage_template"] == {
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


def test_project_status_summary_is_deterministic():
    from rytm_randomizer.project_status_report import summarize_project_status_report

    assert summarize_project_status_report() == {
        "title": "RytmRandomizer Project Status Report",
        "phase_name": "Convergence Phase (armed behind --arm flag)",
        "creative_identity_candidate": "KitForge",
        "passive_cli_command_count": 20,
        "accepted_packet_count": 12,
        "pad_lane_command_count": 38,
        "runtime_supported_count": 2,
        "active_boundary_candidate": "group_profile:2",
        "mock_bridge_candidate": "2",
        "real_midi": "present_behind_arm_flag",
        "port_opening": "present_behind_arm_flag",
        "active_execution": "present_behind_arm_flag",
        "default_mode": "passive",
        "public_api_hardening": "checkpointed",
        "public_api_module_count": 3,
        "collaborator_review_intake": "checkpointed",
        "external_review_findings_received": False,
        "collaborator_review_triage_template": "accepted",
        "hardware_required": False,
        "hardware_validation": "first_end_user_pass",
        "current_runtime_validation": "dual_machine_lane_gate_ready",
        "analog_four_support": "present_behind_arm_flag",
        "pads_5_12_support": "present_behind_arm_flag",
        "pr37_required_checks": "passed",
        "v134_reference": "untouched",
        "active_execution_gate": "--arm flag",
        "active_modes_present": 2,
        "total_modes": 3,
    }


def test_project_status_summary_lines_are_deterministic():
    from rytm_randomizer.project_status_report import format_project_status_summary

    first = format_project_status_summary()
    second = format_project_status_summary()

    assert first == second
    assert first == [
        "RytmRandomizer Project Status Summary",
        "- phase_name: Convergence Phase (armed behind --arm flag)",
        "- creative_identity_candidate: KitForge",
        "- passive_cli_command_count: 20",
        "- accepted_packet_count: 12",
        "- pad_lane_command_count: 38",
        "- runtime_supported_count: 2",
        "- active_boundary_candidate: group_profile:2",
        "- mock_bridge_candidate: 2",
        "- public_api_hardening: checkpointed",
        "- public_api_module_count: 3",
        "- collaborator_review_intake: checkpointed",
        "- external_review_findings_received: False",
        "- collaborator_review_triage_template: accepted",
        "- real_midi: present_behind_arm_flag",
        "- port_opening: present_behind_arm_flag",
        "- active_execution: present_behind_arm_flag",
        "- active_execution_gate: --arm flag",
        "- default_mode: passive",
        "- active_modes_present: 2",
        "- total_modes: 3",
        "- hardware_required: False",
        "- hardware_validation: first_end_user_pass",
        "- current_runtime_validation: dual_machine_lane_gate_ready",
        "- analog_four_support: present_behind_arm_flag",
        "- pads_5_12_support: present_behind_arm_flag",
        "- pr37_required_checks: passed",
        "- v134_reference: untouched",
    ]


def test_project_status_check_passes_for_current_report():
    from rytm_randomizer.project_status_report import check_project_status_report

    check = check_project_status_report()

    assert check == {
        "title": "RytmRandomizer Project Status Check",
        "ok": True,
        "failure_count": 0,
        "failures": [],
        "checked": {
            "safety.real_midi": "present_behind_arm_flag",
            "safety.port_opening": "present_behind_arm_flag",
            "safety.active_execution": "present_behind_arm_flag",
            "safety.command_execution": "present_behind_arm_flag",
            "safety.dispatch": "present_behind_arm_flag",
            "safety.default_mode": "passive",
            "safety.hardware_required": False,
            "safety.analog_four_support": "present_behind_arm_flag",
            "safety.pads_5_12_support": "present_behind_arm_flag",
            "hardware_validation.status": "first_end_user_pass",
            "hardware_validation.dry_run": "passed",
            "hardware_validation.arm_port_open": "passed",
            "hardware_validation.audible_scene_mutation": "confirmed_by_operator",
            "hardware_validation.anchor_return": "confirmed_by_operator",
            "current_runtime_validation.status": "dual_machine_lane_gate_ready",
            "current_runtime_validation.analog_four_support": "operator_smoke_confirmed",
            "current_runtime_validation.pads_5_12_support": "operator_smoke_confirmed",
            "current_runtime_validation.pr37_required_checks": "passed",
            "safety.v134_reference": "untouched",
            "safety.package_metadata": "untouched",
            "convergence.active_execution": "present",
            "convergence.active_execution_gate": "--arm flag",
            "convergence.default_mode": "passive",
            "public_api_hardening.status": "checkpointed",
            "public_api_hardening.exports_documented": True,
            "public_api_hardening.real_midi": "absent",
            "public_api_hardening.port_opening": "absent",
            "public_api_hardening.active_behavior": "absent",
            "collaborator_review_intake.status": "checkpointed",
            "collaborator_review_intake.findings_received": False,
            "collaborator_review_intake.implementation_policy": ("verify_before_implementing"),
            "collaborator_review_intake.real_midi": "absent",
            "collaborator_review_intake.port_opening": "absent",
            "collaborator_review_intake.active_behavior": "absent",
            "collaborator_review_intake.hardware_behavior": "absent",
            "collaborator_review_triage_template.status": "accepted",
            "collaborator_review_triage_template.findings_recorded": False,
            "collaborator_review_triage_template.screenshot_only_sufficient": False,
            "collaborator_review_triage_template.implementation_policy": (
                "triage_before_implementing"
            ),
            "collaborator_review_triage_template.real_midi": "absent",
            "collaborator_review_triage_template.port_opening": "absent",
            "collaborator_review_triage_template.active_behavior": "absent",
            "collaborator_review_triage_template.hardware_behavior": "absent",
            "source.in_memory_only": True,
            "source.writes_files": False,
            "closeout.failure_propagation": "guarded",
        },
    }


def test_project_status_check_fails_for_mutated_unsafe_report():
    from rytm_randomizer.project_status_report import (
        build_project_status_report,
        check_project_status_report,
    )

    report = build_project_status_report()
    # Convergence invariants the check still guards: the default landing mode
    # must stay passive, and the report must not write files.
    report["safety"]["default_mode"] = "armed"
    report["source"]["writes_files"] = True

    check = check_project_status_report(report)

    assert check["ok"] is False
    assert check["failure_count"] == 2
    assert check["failures"] == [
        {
            "path": "safety.default_mode",
            "expected": "passive",
            "actual": "armed",
        },
        {
            "path": "source.writes_files",
            "expected": False,
            "actual": True,
        },
    ]


def test_project_status_check_lines_are_deterministic():
    from rytm_randomizer.project_status_report import format_project_status_check

    first = format_project_status_check()
    second = format_project_status_check()

    assert first == second
    assert first == [
        "RytmRandomizer Project Status Check",
        "- ok: True",
        "- failure_count: 0",
        "- safety.real_midi: present_behind_arm_flag",
        "- safety.port_opening: present_behind_arm_flag",
        "- safety.active_execution: present_behind_arm_flag",
        "- safety.command_execution: present_behind_arm_flag",
        "- safety.dispatch: present_behind_arm_flag",
        "- safety.default_mode: passive",
        "- safety.hardware_required: False",
        "- safety.analog_four_support: present_behind_arm_flag",
        "- safety.pads_5_12_support: present_behind_arm_flag",
        "- hardware_validation.status: first_end_user_pass",
        "- hardware_validation.dry_run: passed",
        "- hardware_validation.arm_port_open: passed",
        "- hardware_validation.audible_scene_mutation: confirmed_by_operator",
        "- hardware_validation.anchor_return: confirmed_by_operator",
        "- current_runtime_validation.status: dual_machine_lane_gate_ready",
        "- current_runtime_validation.analog_four_support: operator_smoke_confirmed",
        "- current_runtime_validation.pads_5_12_support: operator_smoke_confirmed",
        "- current_runtime_validation.pr37_required_checks: passed",
        "- safety.v134_reference: untouched",
        "- safety.package_metadata: untouched",
        "- convergence.active_execution: present",
        "- convergence.active_execution_gate: --arm flag",
        "- convergence.default_mode: passive",
        "- public_api_hardening.status: checkpointed",
        "- public_api_hardening.exports_documented: True",
        "- public_api_hardening.real_midi: absent",
        "- public_api_hardening.port_opening: absent",
        "- public_api_hardening.active_behavior: absent",
        "- collaborator_review_intake.status: checkpointed",
        "- collaborator_review_intake.findings_received: False",
        "- collaborator_review_intake.implementation_policy: verify_before_implementing",
        "- collaborator_review_intake.real_midi: absent",
        "- collaborator_review_intake.port_opening: absent",
        "- collaborator_review_intake.active_behavior: absent",
        "- collaborator_review_intake.hardware_behavior: absent",
        "- collaborator_review_triage_template.status: accepted",
        "- collaborator_review_triage_template.findings_recorded: False",
        "- collaborator_review_triage_template.screenshot_only_sufficient: False",
        "- collaborator_review_triage_template.implementation_policy: triage_before_implementing",
        "- collaborator_review_triage_template.real_midi: absent",
        "- collaborator_review_triage_template.port_opening: absent",
        "- collaborator_review_triage_template.active_behavior: absent",
        "- collaborator_review_triage_template.hardware_behavior: absent",
        "- source.in_memory_only: True",
        "- source.writes_files: False",
        "- closeout.failure_propagation: guarded",
    ]


def test_formatted_project_status_report_is_deterministic():
    from rytm_randomizer.project_status_report import format_project_status_report

    first = format_project_status_report()
    second = format_project_status_report()

    assert first == second
    assert first == [
        "RytmRandomizer Project Status Report",
        "Phase:",
        "- name: Convergence Phase (armed behind --arm flag)",
        "- technical_name: RytmRandomizer",
        "- creative_identity_candidate: KitForge",
        "Passive CLI Visibility:",
        "- report",
        "- project-status-report",
        "- mock-mapper-report",
        "- runtime-plan-report",
        "- active-boundary-report",
        "- mock-runtime-active-bridge-report",
        "- anchor-profile-report",
        "- behavior-parity-report",
        "- list-commands",
        "- list-scenes",
        "- list-group-profiles",
        "- search-commands",
        "- search-scenes",
        "- search-group-profiles",
        "- inspect-command",
        "- inspect-scene",
        "- inspect-group-profile",
        "- preview-command",
        "- preview-scene",
        "- preview-group-profile",
        "Behavior Parity:",
        "- accepted_packet_count: 12",
        "- selected_isolated_pad_packet_count: 2",
        "- pad_lane_packet_count: 4",
        "- pad_lane_command_count: 38",
        "- runtime_adjacent_safe_failure_count: 3",
        "- parked_scope_count: 2",
        "Runtime Plan:",
        "- supported_count: 2",
        "- parked_count: 1",
        "- unsupported_count: 2",
        "- runtime_execution: absent",
        "Active Boundary:",
        "- supported_candidate: group_profile:2",
        "- unsupported_keys: 3, 4",
        "- active_cli_behavior: absent",
        "Mock Runtime Active Bridge:",
        "- accepted_source_key: 2",
        "- rejected_count: 7",
        "- parked_count: 1",
        "- emits_messages: False",
        "Public API Hardening:",
        "- status: checkpointed",
        "- module_count: 3",
        "- exports_documented: True",
        (
            "- modules: rytm_randomizer.active_boundary, "
            "rytm_randomizer.reports, "
            "rytm_randomizer.runtime_plan"
        ),
        "- real_midi: absent",
        "- port_opening: absent",
        "- active_behavior: absent",
        "Collaborator Review Intake:",
        "- status: checkpointed",
        "- collaborator: Eddie",
        "- review_source: external_ai_assisted_review",
        "- findings_received: False",
        "- required_format: text_or_markdown",
        "- implementation_policy: verify_before_implementing",
        (
            "- triage_categories: valid_and_urgent, valid_but_later, "
            "already_handled, needs_more_evidence, not_applicable, "
            "conflicts_with_safety_constraints, conflicts_with_project_direction"
        ),
        "- real_midi: absent",
        "- port_opening: absent",
        "- active_behavior: absent",
        "- hardware_behavior: absent",
        "- package_metadata_changes: requires_explicit_approval",
        "Collaborator Review Triage Template:",
        "- status: accepted",
        "- template_path: docs/archive/COLLABORATOR_REVIEW_TRIAGE_TEMPLATE.md",
        "- review_gate_path: docs/archive/COLLABORATOR_REVIEW_TRIAGE_TEMPLATE_REVIEW.md",
        "- findings_recorded: False",
        "- requires_text_or_markdown: True",
        "- screenshot_only_sufficient: False",
        "- implementation_policy: triage_before_implementing",
        "- real_midi: absent",
        "- port_opening: absent",
        "- active_behavior: absent",
        "- hardware_behavior: absent",
        "- package_metadata_changes: requires_explicit_approval",
        "Closeout:",
        "- closeout_contract: present",
        "- failure_propagation: guarded",
        "- closeout_script: Scripts/closeout_check.ps1",
        "Convergence:",
        "- active_execution: present",
        "- active_execution_gate: --arm flag",
        "- entry_point: rytm_randomizer.app",
        "- default_mode: passive",
        "- modes: default, arm, dry-run",
        "- active_modes_present: 2",
        "- total_modes: 3",
        "- real_midi_provider: " "rytm_randomizer.mido_provider.MidoMidiPortProvider",
        "- interactive_logic_owner: rytm_randomizer.shell",
        "- interactive_logic_converged: True",
        "Hardware Validation:",
        "- status: first_end_user_pass",
        "- date: 2026-05-15",
        "- validated_device: Elektron Analog Rytm MKII",
        "- operator: Jose Buzzi",
        "- collaborator: Eddie",
        "- installer_wheel: rytm_randomizer-1.34.0-py3-none-any.whl",
        "- dry_run: passed",
        "- arm_port_open: passed",
        "- audible_scene_mutation: confirmed_by_operator",
        "- anchor_return: confirmed_by_operator",
        (
            "- guardrails: profile_prompt_rejected_scn_without_midi, "
            "scn_command_menu_no_midi, bare_depth_digit_no_midi"
        ),
        "- canonical_scene_flow: S1A, S3A, S3B, S4B, S5, Z",
        "- analog_four_support: not_in_first_pass",
        "- pads_5_12_support: not_in_first_pass",
        "Current Runtime Validation:",
        "- status: dual_machine_lane_gate_ready",
        "- date: 2026-05-19",
        "- analog_four_support: operator_smoke_confirmed",
        "- pads_5_12_support: operator_smoke_confirmed",
        "- dual_machine_lane_validation_guide: software_ready",
        "- all_lane_validation_guide: software_ready",
        "- pr37_required_checks: passed",
        "- next_hardware_scope: lane_scoped_manual_validation",
        "Safety:",
        "- real_midi: present_behind_arm_flag",
        "- port_opening: present_behind_arm_flag",
        "- active_execution: present_behind_arm_flag",
        "- dispatch: present_behind_arm_flag",
        "- command_execution: present_behind_arm_flag",
        "- default_mode: passive",
        "- hardware_required: False",
        "- hardware_behavior: opt_in_behind_arm_flag",
        "- analog_four_support: present_behind_arm_flag",
        "- pads_5_12_support: present_behind_arm_flag",
        "- v134_reference: untouched",
        "- package_metadata: untouched",
        "Source:",
        "- in_memory_only: True",
        "- writes_files: False",
    ]


def test_project_status_report_json_is_deterministic_and_parseable():
    from rytm_randomizer.project_status_report import format_project_status_report_json

    first = format_project_status_report_json()
    second = format_project_status_report_json()

    assert first == second
    parsed = json.loads(first)
    assert parsed["title"] == "RytmRandomizer Project Status Report"
    assert parsed["phase"]["name"] == "Convergence Phase (armed behind --arm flag)"
    assert parsed["phase"]["creative_identity_candidate"] == "KitForge"
    assert parsed["behavior_parity"]["accepted_packet_count"] == 12
    assert parsed["runtime_plan"]["runtime_execution"] == "absent"
    assert parsed["active_boundary"]["active_cli_behavior"] == "absent"
    assert parsed["mock_runtime_active_bridge"]["emits_messages"] is False
    assert parsed["safety"]["real_midi"] == "present_behind_arm_flag"
    assert parsed["safety"]["default_mode"] == "passive"
    assert parsed["public_api_hardening"]["status"] == "checkpointed"
    assert parsed["public_api_hardening"]["module_count"] == 3
    assert parsed["public_api_hardening"]["exports_documented"] is True
    assert parsed["collaborator_review_intake"]["status"] == "checkpointed"
    assert parsed["collaborator_review_intake"]["findings_received"] is False
    assert parsed["collaborator_review_triage_template"]["status"] == "accepted"
    assert parsed["collaborator_review_triage_template"]["findings_recorded"] is False
    assert parsed["hardware_validation"]["status"] == "first_end_user_pass"
    assert parsed["hardware_validation"]["audible_scene_mutation"] == "confirmed_by_operator"
    assert parsed["current_runtime_validation"]["status"] == "dual_machine_lane_gate_ready"
    assert parsed["current_runtime_validation"]["analog_four_support"] == (
        "operator_smoke_confirmed"
    )
    assert parsed["current_runtime_validation"]["pads_5_12_support"] == ("operator_smoke_confirmed")
    assert parsed["safety"]["hardware_required"] is False
    assert parsed["safety"]["analog_four_support"] == "present_behind_arm_flag"
    assert parsed["safety"]["pads_5_12_support"] == "present_behind_arm_flag"
    assert parsed["convergence"]["active_execution"] == "present"
    assert parsed["convergence"]["active_execution_gate"] == "--arm flag"
    assert parsed["convergence"]["default_mode"] == "passive"
    assert parsed["source"]["in_memory_only"] is True
    assert parsed["source"]["writes_files"] is False


def test_returned_project_status_report_is_copied_and_mutation_safe():
    from rytm_randomizer.project_status_report import build_project_status_report

    report = build_project_status_report()
    report["phase"]["name"] = "MUTATED"
    report["behavior_parity"]["accepted_packet_count"] = 0
    report["passive_cli_commands"] = ()
    report["public_api_hardening"]["status"] = "MUTATED"
    report["collaborator_review_intake"]["status"] = "MUTATED"
    report["collaborator_review_triage_template"]["status"] = "MUTATED"
    report["current_runtime_validation"]["status"] = "MUTATED"

    fresh_report = build_project_status_report()

    assert fresh_report["phase"]["name"] == "Convergence Phase (armed behind --arm flag)"
    assert fresh_report["behavior_parity"]["accepted_packet_count"] == 12
    assert "project-status-report" in fresh_report["passive_cli_commands"]
    assert fresh_report["public_api_hardening"]["status"] == "checkpointed"
    assert fresh_report["collaborator_review_intake"]["status"] == "checkpointed"
    assert fresh_report["collaborator_review_triage_template"]["status"] == "accepted"
    assert fresh_report["current_runtime_validation"]["status"] == "dual_machine_lane_gate_ready"


def test_project_status_report_imports_no_real_midi_libraries():
    sys.modules.pop("rytm_randomizer.project_status_report", None)
    importlib.import_module("rytm_randomizer.project_status_report")

    assert "mido" not in sys.modules
    assert "rtmidi" not in sys.modules


def test_project_status_report_exposes_no_active_cli_command_names():
    import rytm_randomizer.project_status_report as report

    exposed_names = set(dir(report))

    assert "execute_command" not in exposed_names
    assert "send_command" not in exposed_names
    assert "hardware_test" not in exposed_names
    assert "open_port" not in exposed_names
    assert "open_midi_port" not in exposed_names
    assert "send_midi" not in exposed_names


if __name__ == "__main__":
    test_importing_project_status_report_prints_nothing()
    test_project_status_report_summarizes_current_project_state()
    test_project_status_report_records_passive_cli_visibility()
    test_project_status_report_tracks_convergence_behind_arm_flag()
    test_project_status_report_records_current_runtime_validation_status()
    test_project_status_report_records_public_api_hardening_checkpoint()
    test_project_status_report_records_collaborator_review_intake_checkpoint()
    test_project_status_report_records_collaborator_review_triage_template()
    test_project_status_summary_is_deterministic()
    test_project_status_summary_lines_are_deterministic()
    test_project_status_check_passes_for_current_report()
    test_project_status_check_fails_for_mutated_unsafe_report()
    test_project_status_check_lines_are_deterministic()
    test_formatted_project_status_report_is_deterministic()
    test_project_status_report_json_is_deterministic_and_parseable()
    test_returned_project_status_report_is_copied_and_mutation_safe()
    test_project_status_report_imports_no_real_midi_libraries()
    test_project_status_report_exposes_no_active_cli_command_names()
