from pathlib import Path
import importlib
import subprocess
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def test_importing_operator_status_report_prints_nothing():
    result = subprocess.run(
        [sys.executable, "-c", "import rytm_randomizer.operator_status_report"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert result.stdout == ""
    assert result.stderr == ""


def test_report_summarizes_daily_operator_state():
    from rytm_randomizer.operator_status_report import build_operator_status_report

    report = build_operator_status_report()

    assert report["title"] == "RytmRandomizer Operator Status Report"
    assert report["mode"] == {
        "passive": True,
        "daily_visibility": True,
        "implementation_intake_ready": True,
    }
    assert report["project"] == {
        "phase_name": "Passive/Mock Runtime Visibility Phase",
        "creative_identity_candidate": "KitForge",
        "passive_cli_command_count": 23,
        "v134_reference": "import_safe_wrapped",
    }
    assert report["collaborator_intake"] == {
        "status": "waiting_for_implementation_branch",
        "implementation_branch_observed": False,
        "implementation_pr_observed": False,
        "direct_merge_allowed": False,
    }
    assert report["github_actions"] == {
        "status": "manual_only",
        "daily_feedback": "local_closeout",
        "automatic_pull_request_runs": False,
        "automatic_push_runs": False,
        "automatic_release_tag_runs": False,
        "no_pay_policy": True,
    }


def test_report_records_operator_commands_and_next_actions():
    from rytm_randomizer.operator_status_report import build_operator_status_report

    report = build_operator_status_report()

    assert report["operator_commands"] == {
        "project_status": (
            "python -m rytm_randomizer.cli project-status-report --summary"
        ),
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
    assert report["next_actions"] == (
        "wait for Eddie implementation branch or PR",
        "run collaborator implementation intake when branch or PR appears",
        "use local closeout for frequent feedback",
        "run manual GitHub Actions only at explicit review gates",
    )


def test_report_records_safety_boundaries():
    from rytm_randomizer.operator_status_report import build_operator_status_report

    report = build_operator_status_report()

    assert report["safety"] == {
        "real_midi": "absent",
        "mido": "absent",
        "port_opening": "absent",
        "midi_sending": "absent",
        "active_execution": "absent",
        "dispatch": "absent",
        "hardware_behavior": "absent",
        "hardware_required": False,
    }


def test_summary_is_deterministic():
    from rytm_randomizer.operator_status_report import summarize_operator_status_report

    assert summarize_operator_status_report() == {
        "title": "RytmRandomizer Operator Status Report",
        "phase_name": "Passive/Mock Runtime Visibility Phase",
        "creative_identity_candidate": "KitForge",
        "passive_cli_command_count": 23,
        "collaborator_intake_status": "waiting_for_implementation_branch",
        "implementation_branch_observed": False,
        "implementation_pr_observed": False,
        "github_actions": "manual_only",
        "daily_feedback": "local_closeout",
        "real_midi": "absent",
        "active_execution": "absent",
        "hardware_required": False,
        "next_recommended_action": "wait for Eddie implementation branch or PR",
    }


def test_formatted_report_is_deterministic_and_human_readable():
    from rytm_randomizer.operator_status_report import format_operator_status_report

    first = format_operator_status_report()
    second = format_operator_status_report()

    assert first == second
    assert first == [
        "RytmRandomizer Operator Status Report",
        "Mode:",
        "- passive: True",
        "- daily_visibility: True",
        "- implementation_intake_ready: True",
        "Project:",
        "- phase_name: Passive/Mock Runtime Visibility Phase",
        "- creative_identity_candidate: KitForge",
        "- passive_cli_command_count: 23",
        "- v134_reference: import_safe_wrapped",
        "Collaborator Intake:",
        "- status: waiting_for_implementation_branch",
        "- implementation_branch_observed: False",
        "- implementation_pr_observed: False",
        "- direct_merge_allowed: False",
        "GitHub Actions:",
        "- status: manual_only",
        "- daily_feedback: local_closeout",
        "- automatic_pull_request_runs: False",
        "- automatic_push_runs: False",
        "- automatic_release_tag_runs: False",
        "- no_pay_policy: True",
        "Operator Commands:",
        (
            "- project_status: "
            "python -m rytm_randomizer.cli project-status-report --summary"
        ),
        (
            "- collaborator_intake_readiness: "
            "python -m rytm_randomizer.cli collaborator-intake-readiness-report"
        ),
        (
            "- collaborator_branch_watch: "
            "python -m rytm_randomizer.cli collaborator-branch-watch"
        ),
        (
            "- local_closeout: "
            "powershell -ExecutionPolicy Bypass -File .\\Scripts\\closeout_check.ps1"
        ),
        "- v134_diff: git diff -- rytm_hybrid_randomizer_v134.py",
        "- git_status: git status --short",
        "Next Actions:",
        "- wait for Eddie implementation branch or PR",
        "- run collaborator implementation intake when branch or PR appears",
        "- use local closeout for frequent feedback",
        "- run manual GitHub Actions only at explicit review gates",
        "Safety:",
        "- real_midi: absent",
        "- mido: absent",
        "- port_opening: absent",
        "- midi_sending: absent",
        "- active_execution: absent",
        "- dispatch: absent",
        "- hardware_behavior: absent",
        "- hardware_required: False",
        "Source:",
        "- project_status: rytm_randomizer.project_status_report",
        (
            "- collaborator_intake_readiness: "
            "rytm_randomizer.collaborator_intake_readiness_report"
        ),
        (
            "- collaborator_branch_watch: "
            "rytm_randomizer.collaborator_branch_watch_report"
        ),
        "In-memory only: True",
    ]


def test_returned_report_data_is_copied_and_mutation_safe():
    from rytm_randomizer.operator_status_report import build_operator_status_report

    report = build_operator_status_report()
    report["project"]["phase_name"] = "MUTATED"
    report["collaborator_intake"]["status"] = "MUTATED"
    report["github_actions"]["status"] = "MUTATED"

    fresh_report = build_operator_status_report()

    assert fresh_report["project"]["phase_name"] == (
        "Passive/Mock Runtime Visibility Phase"
    )
    assert (
        fresh_report["collaborator_intake"]["status"]
        == "waiting_for_implementation_branch"
    )
    assert fresh_report["github_actions"]["status"] == "manual_only"


def test_no_real_midi_library_is_imported():
    sys.modules.pop("rytm_randomizer.operator_status_report", None)
    importlib.import_module("rytm_randomizer.operator_status_report")

    assert "mido" not in sys.modules
    assert "rtmidi" not in sys.modules


def test_report_exposes_no_active_behavior_names():
    import rytm_randomizer.operator_status_report as report

    exposed_names = set(dir(report))

    assert "execute_command" not in exposed_names
    assert "send_command" not in exposed_names
    assert "hardware_test" not in exposed_names
    assert "open_port" not in exposed_names
    assert "open_midi_port" not in exposed_names
    assert "send_midi" not in exposed_names


def test_report_exposes_explicit_public_api():
    import rytm_randomizer.operator_status_report as report

    assert report.__all__ == [
        "OPERATOR_STATUS_SAFETY",
        "build_operator_status_report",
        "format_operator_status_report",
        "summarize_operator_status_report",
    ]


if __name__ == "__main__":
    test_importing_operator_status_report_prints_nothing()
    test_report_summarizes_daily_operator_state()
    test_report_records_operator_commands_and_next_actions()
    test_report_records_safety_boundaries()
    test_summary_is_deterministic()
    test_formatted_report_is_deterministic_and_human_readable()
    test_returned_report_data_is_copied_and_mutation_safe()
    test_no_real_midi_library_is_imported()
    test_report_exposes_no_active_behavior_names()
    test_report_exposes_explicit_public_api()
