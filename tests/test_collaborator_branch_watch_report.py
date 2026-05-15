from pathlib import Path
import importlib
import subprocess
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def test_importing_collaborator_branch_watch_report_prints_nothing():
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "import rytm_randomizer.collaborator_branch_watch_report",
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert result.stdout == ""
    assert result.stderr == ""


def test_report_records_current_branch_watch_snapshot():
    from rytm_randomizer.collaborator_branch_watch_report import (
        build_collaborator_branch_watch_report,
    )

    report = build_collaborator_branch_watch_report()

    assert report["title"] == "RytmRandomizer Collaborator Branch Watch Report"
    assert report["status"] == "waiting_for_external_implementation_branch"
    assert report["current_branch"] == "codex/execute-eddie-plan"
    assert report["current_pull_request"] == {
        "number": 2,
        "title": "Execute Eddie review plan foundation",
        "branch": "codex/execute-eddie-plan",
        "base": "modularize-v1.34",
        "draft": True,
    }
    assert report["observed_remote_branches"] == (
        "modularize-v1.34",
        "docs/review-and-execution-plan",
        "codex/execute-eddie-plan",
    )
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


def test_report_records_watch_rules_and_local_refresh_commands():
    from rytm_randomizer.collaborator_branch_watch_report import (
        build_collaborator_branch_watch_report,
    )

    report = build_collaborator_branch_watch_report()

    assert report["watch_rules"] == {
        "expected_collaborator": "Eddie",
        "expected_github_owner": "edward-rosado",
        "implementation_branch_observed": False,
        "implementation_pr_observed": False,
        "direct_merge_allowed": False,
        "intake_required_before_review": True,
        "intake_required_before_merge": True,
    }
    assert report["refresh_commands"] == {
        "remote_branches": "git ls-remote --heads origin",
        "pull_requests": (
            "gh pr list --repo buzzijose-hub/RytmRandomizer --state all "
            "--limit 20 --json number,title,headRefName,baseRefName,state,"
            "isDraft,updatedAt,url"
        ),
        "local_status": "git status --short",
        "v134_diff": "git diff -- rytm_hybrid_randomizer_v134.py",
    }


def test_report_records_manual_actions_policy_and_safety_boundaries():
    from rytm_randomizer.collaborator_branch_watch_report import (
        build_collaborator_branch_watch_report,
    )

    report = build_collaborator_branch_watch_report()

    assert report["github_actions_policy"] == {
        "status": "manual_only",
        "automatic_pull_request_runs": False,
        "automatic_push_runs": False,
        "automatic_release_tag_runs": False,
        "report_triggers_actions": False,
        "no_pay_policy": True,
    }
    assert report["safety"] == {
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


def test_summary_is_deterministic():
    from rytm_randomizer.collaborator_branch_watch_report import (
        summarize_collaborator_branch_watch_report,
    )

    assert summarize_collaborator_branch_watch_report() == {
        "title": "RytmRandomizer Collaborator Branch Watch Report",
        "status": "waiting_for_external_implementation_branch",
        "observed_remote_branch_count": 3,
        "observed_pull_request_count": 2,
        "implementation_branch_observed": False,
        "implementation_pr_observed": False,
        "direct_merge_allowed": False,
        "github_actions": "manual_only",
        "report_triggers_actions": False,
        "real_midi": "absent",
        "active_execution": "absent",
        "hardware_required": False,
        "next_recommended_action": "wait for Eddie implementation branch or PR",
    }


def test_formatted_report_is_deterministic_and_human_readable():
    from rytm_randomizer.collaborator_branch_watch_report import (
        format_collaborator_branch_watch_report,
    )

    first = format_collaborator_branch_watch_report()
    second = format_collaborator_branch_watch_report()

    assert first == second
    assert first == [
        "RytmRandomizer Collaborator Branch Watch Report",
        "Current State:",
        "- status: waiting_for_external_implementation_branch",
        "- current_branch: codex/execute-eddie-plan",
        "- current_pr: #2 Execute Eddie review plan foundation",
        "Observed Remote Branches:",
        "- modularize-v1.34",
        "- docs/review-and-execution-plan",
        "- codex/execute-eddie-plan",
        "Observed Pull Requests:",
        "- #1 edward-rosado docs/review-and-execution-plan -> modularize-v1.34 (review_plan_source, implementation_branch: False)",
        "- #2 buzzijose-hub codex/execute-eddie-plan -> modularize-v1.34 (draft_foundation_branch, implementation_branch: False)",
        "Watch Rules:",
        "- expected_collaborator: Eddie",
        "- expected_github_owner: edward-rosado",
        "- implementation_branch_observed: False",
        "- implementation_pr_observed: False",
        "- direct_merge_allowed: False",
        "- intake_required_before_review: True",
        "- intake_required_before_merge: True",
        "Refresh Commands:",
        "- remote_branches: git ls-remote --heads origin",
        "- pull_requests: gh pr list --repo buzzijose-hub/RytmRandomizer --state all --limit 20 --json number,title,headRefName,baseRefName,state,isDraft,updatedAt,url",
        "- local_status: git status --short",
        "- v134_diff: git diff -- rytm_hybrid_randomizer_v134.py",
        "GitHub Actions Policy:",
        "- status: manual_only",
        "- automatic_pull_request_runs: False",
        "- automatic_push_runs: False",
        "- automatic_release_tag_runs: False",
        "- report_triggers_actions: False",
        "- no_pay_policy: True",
        "Next Actions:",
        "- wait for Eddie implementation branch or PR",
        "- run collaborator implementation intake when branch or PR appears",
        "- keep GitHub Actions manual-only unless explicitly triggered",
        "- do not merge collaborator work before intake review",
        "Safety:",
        "- github_mutation: absent",
        "- branch_checkout: absent",
        "- branch_merge: absent",
        "- real_midi: absent",
        "- mido: absent",
        "- port_opening: absent",
        "- midi_sending: absent",
        "- active_execution: absent",
        "- dispatch: absent",
        "- hardware_behavior: absent",
        "- hardware_required: False",
        "- v134_reference: untouched",
        "Source: Docs/COLLABORATOR_IMPLEMENTATION_BRANCH_INTAKE_PROTOCOL.md",
        "In-memory only: True",
    ]


def test_returned_report_data_is_copied_and_mutation_safe():
    from rytm_randomizer.collaborator_branch_watch_report import (
        build_collaborator_branch_watch_report,
    )

    report = build_collaborator_branch_watch_report()
    report["observed_remote_branches"] += ("MUTATED",)
    report["watch_rules"]["implementation_branch_observed"] = True
    report["safety"]["real_midi"] = "MUTATED"

    fresh_report = build_collaborator_branch_watch_report()

    assert fresh_report["observed_remote_branches"] == (
        "modularize-v1.34",
        "docs/review-and-execution-plan",
        "codex/execute-eddie-plan",
    )
    assert fresh_report["watch_rules"]["implementation_branch_observed"] is False
    assert fresh_report["safety"]["real_midi"] == "absent"


def test_no_real_midi_library_is_imported():
    sys.modules.pop("rytm_randomizer.collaborator_branch_watch_report", None)
    importlib.import_module("rytm_randomizer.collaborator_branch_watch_report")

    assert "mido" not in sys.modules
    assert "rtmidi" not in sys.modules


def test_report_exposes_no_active_behavior_names():
    import rytm_randomizer.collaborator_branch_watch_report as report

    exposed_names = set(dir(report))

    assert "execute_command" not in exposed_names
    assert "send_command" not in exposed_names
    assert "hardware_test" not in exposed_names
    assert "open_port" not in exposed_names
    assert "open_midi_port" not in exposed_names
    assert "send_midi" not in exposed_names
    assert "merge_branch" not in exposed_names
    assert "trigger_actions" not in exposed_names


def test_report_exposes_explicit_public_api():
    import rytm_randomizer.collaborator_branch_watch_report as report

    assert report.__all__ == [
        "COLLABORATOR_BRANCH_WATCH_SAFETY",
        "build_collaborator_branch_watch_report",
        "format_collaborator_branch_watch_report",
        "summarize_collaborator_branch_watch_report",
    ]


if __name__ == "__main__":
    test_importing_collaborator_branch_watch_report_prints_nothing()
    test_report_records_current_branch_watch_snapshot()
    test_report_records_watch_rules_and_local_refresh_commands()
    test_report_records_manual_actions_policy_and_safety_boundaries()
    test_summary_is_deterministic()
    test_formatted_report_is_deterministic_and_human_readable()
    test_returned_report_data_is_copied_and_mutation_safe()
    test_no_real_midi_library_is_imported()
    test_report_exposes_no_active_behavior_names()
    test_report_exposes_explicit_public_api()
