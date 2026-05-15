from pathlib import Path
import importlib
import subprocess
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def test_importing_collaborator_intake_readiness_report_prints_nothing():
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "import rytm_randomizer.collaborator_intake_readiness_report",
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert result.stdout == ""
    assert result.stderr == ""


def test_report_records_waiting_state_and_observed_github_context():
    from rytm_randomizer.collaborator_intake_readiness_report import (
        build_collaborator_intake_readiness_report,
    )

    report = build_collaborator_intake_readiness_report()

    assert report["title"] == "RytmRandomizer Collaborator Intake Readiness Report"
    assert report["status"] == "waiting_for_implementation_branch"
    assert report["current_branch"] == "codex/execute-eddie-plan"
    assert report["current_pull_request"] == {
        "number": 2,
        "title": "Execute Eddie review plan foundation",
        "branch": "codex/execute-eddie-plan",
        "base": "modularize-v1.34",
        "draft": True,
    }
    assert report["observed_pull_requests"] == (
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
    assert report["observed_remote_branches"] == (
        "modularize-v1.34",
        "docs/review-and-execution-plan",
        "codex/execute-eddie-plan",
    )


def test_report_records_required_intake_and_merge_policy():
    from rytm_randomizer.collaborator_intake_readiness_report import (
        build_collaborator_intake_readiness_report,
    )

    report = build_collaborator_intake_readiness_report()

    assert report["required_intake_fields"] == (
        "branch_name",
        "commit_hash",
        "base_branch",
        "test_result",
        "v134_status",
        "midi_ports_active_hardware_status",
    )
    assert report["merge_policy"] == {
        "intake_before_review": True,
        "intake_before_merge": True,
        "direct_merge_allowed": False,
        "pr1_is_implementation": False,
        "implementation_branch_observed": False,
        "implementation_pr_observed": False,
    }


def test_report_records_manual_actions_and_safety_boundaries():
    from rytm_randomizer.collaborator_intake_readiness_report import (
        build_collaborator_intake_readiness_report,
    )

    report = build_collaborator_intake_readiness_report()

    assert report["github_actions_policy"] == {
        "status": "manual_only",
        "daily_feedback": "local_closeout",
        "automatic_pull_request_runs": False,
        "automatic_push_runs": False,
        "automatic_release_tag_runs": False,
        "manual_gate_required_for_collaborator_intake": True,
        "no_pay_policy": True,
    }
    assert report["safety"] == {
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


def test_summary_is_deterministic():
    from rytm_randomizer.collaborator_intake_readiness_report import (
        summarize_collaborator_intake_readiness_report,
    )

    assert summarize_collaborator_intake_readiness_report() == {
        "title": "RytmRandomizer Collaborator Intake Readiness Report",
        "status": "waiting_for_implementation_branch",
        "observed_pull_request_count": 2,
        "observed_remote_branch_count": 3,
        "implementation_branch_observed": False,
        "implementation_pr_observed": False,
        "direct_merge_allowed": False,
        "github_actions": "manual_only",
        "daily_feedback": "local_closeout",
        "real_midi": "absent",
        "active_execution": "absent",
        "hardware_required": False,
    }


def test_formatted_report_is_deterministic_and_human_readable():
    from rytm_randomizer.collaborator_intake_readiness_report import (
        format_collaborator_intake_readiness_report,
    )

    first = format_collaborator_intake_readiness_report()
    second = format_collaborator_intake_readiness_report()

    assert first == second
    assert first == [
        "RytmRandomizer Collaborator Intake Readiness Report",
        "Current State:",
        "- status: waiting_for_implementation_branch",
        "- current_branch: codex/execute-eddie-plan",
        "- current_pr: #2 Execute Eddie review plan foundation",
        "Observed Pull Requests:",
        "- #1 edward-rosado docs/review-and-execution-plan -> modularize-v1.34 (review_plan_source, implementation_branch: False)",
        "- #2 buzzijose-hub codex/execute-eddie-plan -> modularize-v1.34 (draft_foundation_branch, implementation_branch: False)",
        "Observed Remote Branches:",
        "- modularize-v1.34",
        "- docs/review-and-execution-plan",
        "- codex/execute-eddie-plan",
        "Required Intake Fields:",
        "- branch_name",
        "- commit_hash",
        "- base_branch",
        "- test_result",
        "- v134_status",
        "- midi_ports_active_hardware_status",
        "Merge Policy:",
        "- intake_before_review: True",
        "- intake_before_merge: True",
        "- direct_merge_allowed: False",
        "- pr1_is_implementation: False",
        "- implementation_branch_observed: False",
        "- implementation_pr_observed: False",
        "GitHub Actions Policy:",
        "- status: manual_only",
        "- daily_feedback: local_closeout",
        "- automatic_pull_request_runs: False",
        "- automatic_push_runs: False",
        "- automatic_release_tag_runs: False",
        "- manual_gate_required_for_collaborator_intake: True",
        "- no_pay_policy: True",
        "Safety:",
        "- real_midi: absent",
        "- mido: absent",
        "- port_opening: absent",
        "- midi_sending: absent",
        "- active_execution: absent",
        "- dispatch: absent",
        "- hardware_behavior: absent",
        "- hardware_required: False",
        "- v134_reference: untouched",
        "Source: Docs/COLLABORATOR_IMPLEMENTATION_WAIT_STATE_CHECKPOINT.md",
        "In-memory only: True",
    ]


def test_returned_report_data_is_copied_and_mutation_safe():
    from rytm_randomizer.collaborator_intake_readiness_report import (
        build_collaborator_intake_readiness_report,
    )

    report = build_collaborator_intake_readiness_report()
    report["observed_pull_requests"][0]["role"] = "MUTATED"
    report["github_actions_policy"]["status"] = "MUTATED"
    report["source"]["checkpoint_path"] = "MUTATED"

    fresh_report = build_collaborator_intake_readiness_report()

    assert fresh_report["observed_pull_requests"][0]["role"] == "review_plan_source"
    assert fresh_report["github_actions_policy"]["status"] == "manual_only"
    assert (
        fresh_report["source"]["checkpoint_path"]
        == "Docs/COLLABORATOR_IMPLEMENTATION_WAIT_STATE_CHECKPOINT.md"
    )


def test_no_real_midi_library_is_imported():
    sys.modules.pop("rytm_randomizer.collaborator_intake_readiness_report", None)
    importlib.import_module("rytm_randomizer.collaborator_intake_readiness_report")

    assert "mido" not in sys.modules
    assert "rtmidi" not in sys.modules


def test_report_exposes_no_active_behavior_names():
    import rytm_randomizer.collaborator_intake_readiness_report as report

    exposed_names = set(dir(report))

    assert "execute_command" not in exposed_names
    assert "send_command" not in exposed_names
    assert "hardware_test" not in exposed_names
    assert "open_port" not in exposed_names
    assert "open_midi_port" not in exposed_names
    assert "send_midi" not in exposed_names


def test_report_exposes_explicit_public_api():
    import rytm_randomizer.collaborator_intake_readiness_report as report

    assert report.__all__ == [
        "COLLABORATOR_INTAKE_READINESS_BOUNDARY",
        "build_collaborator_intake_readiness_report",
        "format_collaborator_intake_readiness_report",
        "summarize_collaborator_intake_readiness_report",
    ]


if __name__ == "__main__":
    test_importing_collaborator_intake_readiness_report_prints_nothing()
    test_report_records_waiting_state_and_observed_github_context()
    test_report_records_required_intake_and_merge_policy()
    test_report_records_manual_actions_and_safety_boundaries()
    test_summary_is_deterministic()
    test_formatted_report_is_deterministic_and_human_readable()
    test_returned_report_data_is_copied_and_mutation_safe()
    test_no_real_midi_library_is_imported()
    test_report_exposes_no_active_behavior_names()
    test_report_exposes_explicit_public_api()
