import importlib
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def test_importing_mock_runtime_active_bridge_report_prints_nothing():
    result = subprocess.run(
        [sys.executable, "-c", "import rytm_randomizer.reports"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert result.stdout == ""
    assert result.stderr == ""


def test_report_summarizes_bridge_contract_without_invoking_bridge():
    from rytm_randomizer.reports import build_mock_runtime_active_bridge_report

    report = build_mock_runtime_active_bridge_report()

    assert report["title"] == "RytmRandomizer Mock Runtime Active Bridge Report"
    assert report["mode"] == {
        "read_only": True,
        "mock_only": True,
        "metadata_only": True,
        "invokes_bridge": False,
        "constructs_sender": False,
        "emits_messages": False,
    }
    assert report["bridge"] == {
        "module": "rytm_randomizer.mock_runtime_active_bridge",
        "request_type": "RuntimeActiveBridgeRequest",
        "result_type": "RuntimeActiveBridgeResult",
        "evaluator": "evaluate_mock_runtime_active_bridge",
    }
    assert report["accepted_candidate"] == {
        "source_kind": "group_profile",
        "source_key": "2",
        "source_name": "My BD Hard",
        "target": "Pad 1 / BD Hard",
        "requires_armed": True,
        "requires_dry_run_confirmed": True,
        "sender": "MockMidiSender",
    }


def test_report_records_rejected_and_parked_scope():
    from rytm_randomizer.reports import build_mock_runtime_active_bridge_report

    report = build_mock_runtime_active_bridge_report()

    assert report["rejected_cases"] == (
        {
            "case": "missing_arming",
            "description": "missing arming fails safely",
            "emits_messages": False,
        },
        {
            "case": "missing_dry_run_confirmation",
            "description": "missing dry-run confirmation fails safely",
            "emits_messages": False,
        },
        {
            "case": "profile_3_bridge_rejected",
            "source_kind": "group_profile",
            "source_key": "3",
            "source_name": "My BD Classic",
            "emits_messages": False,
        },
        {
            "case": "unknown_key",
            "description": "unknown group profile keys fail safely",
            "emits_messages": False,
        },
        {
            "case": "unsupported_source_kind",
            "description": "unsupported source kinds fail safely",
            "emits_messages": False,
        },
        {
            "case": "invalid_request",
            "description": "invalid request fails before message emission",
            "emits_messages": False,
        },
        {
            "case": "invalid_sender",
            "description": "invalid sender fails before message emission",
            "emits_messages": False,
        },
    )
    assert report["parked_cases"] == (
        {
            "case": "profile_4_parked",
            "source_kind": "group_profile",
            "source_key": "4",
            "source_name": "My BD Acoustic",
            "emits_messages": False,
            "reason": "parked until separately approved",
        },
    )


def test_report_records_absent_runtime_and_hardware_boundaries():
    from rytm_randomizer.reports import build_mock_runtime_active_bridge_report

    report = build_mock_runtime_active_bridge_report()

    assert report["safety"] == {
        "real_midi": "absent",
        "port_opening": "absent",
        "hardware_required": False,
        "cli_execution_wiring": "absent",
        "runtime_execution": "absent",
        "dispatch": "absent",
        "active_behavior": "absent",
        "hardware_behavior": "absent",
    }


def test_report_summary_is_deterministic():
    from rytm_randomizer.reports import summarize_mock_runtime_active_bridge_report

    assert summarize_mock_runtime_active_bridge_report() == {
        "title": "RytmRandomizer Mock Runtime Active Bridge Report",
        "accepted_source_key": "2",
        "rejected_count": 7,
        "parked_count": 1,
        "read_only": True,
        "mock_only": True,
        "invokes_bridge": False,
        "constructs_sender": False,
        "emits_messages": False,
    }


def test_formatted_report_is_deterministic_and_human_readable():
    from rytm_randomizer.reports import format_mock_runtime_active_bridge_report

    first = format_mock_runtime_active_bridge_report()
    second = format_mock_runtime_active_bridge_report()

    assert first == second
    assert first == [
        "RytmRandomizer Mock Runtime Active Bridge Report",
        "Bridge Mode:",
        "- read_only: True",
        "- mock_only: True",
        "- metadata_only: True",
        "- invokes_bridge: False",
        "- constructs_sender: False",
        "- emits_messages: False",
        "Accepted Candidate:",
        "- group_profile:2 / My BD Hard -> Pad 1 / BD Hard",
        "- requires_armed: True",
        "- requires_dry_run_confirmed: True",
        "- sender: MockMidiSender",
        "Rejected Cases:",
        "- missing_arming: missing arming fails safely",
        "- missing_dry_run_confirmation: missing dry-run confirmation fails safely",
        "- group_profile:3 / My BD Classic: bridge rejected",
        "- unknown_key: unknown group profile keys fail safely",
        "- unsupported_source_kind: unsupported source kinds fail safely",
        "- invalid_request: invalid request fails before message emission",
        "- invalid_sender: invalid sender fails before message emission",
        "Parked Cases:",
        "- group_profile:4 / My BD Acoustic: parked until separately approved",
        "Safety:",
        "- real_midi: absent",
        "- port_opening: absent",
        "- hardware_required: False",
        "- cli_execution_wiring: absent",
        "- runtime_execution: absent",
        "- dispatch: absent",
        "- active_behavior: absent",
        "- hardware_behavior: absent",
        "Source: rytm_randomizer.mock_runtime_active_bridge",
        "In-memory only: True",
    ]


def test_returned_report_data_is_copied_and_mutation_safe():
    from rytm_randomizer.reports import build_mock_runtime_active_bridge_report

    report = build_mock_runtime_active_bridge_report()
    report["accepted_candidate"]["source_name"] = "MUTATED"
    report["rejected_cases"][0]["description"] = "MUTATED"
    report["source"]["bridge_module"] = "MUTATED"

    fresh_report = build_mock_runtime_active_bridge_report()

    assert fresh_report["accepted_candidate"]["source_name"] == "My BD Hard"
    assert fresh_report["rejected_cases"][0]["description"] == "missing arming fails safely"
    assert fresh_report["source"]["bridge_module"] == "rytm_randomizer.mock_runtime_active_bridge"


def test_report_import_does_not_import_or_invoke_bridge_or_sender():
    script = "\n".join(
        [
            "import sys",
            "sys.modules.pop('rytm_randomizer.reports', None)",
            "sys.modules.pop('rytm_randomizer.mock_runtime_active_bridge', None)",
            "sys.modules.pop('rytm_randomizer.mock_midi', None)",
            "import rytm_randomizer.reports as report",
            "report.build_mock_runtime_active_bridge_report()",
            "print('bridge_loaded=' + str('rytm_randomizer.mock_runtime_active_bridge' in sys.modules))",
            "print('mock_midi_loaded=' + str('rytm_randomizer.mock_midi' in sys.modules))",
        ]
    )
    result = subprocess.run(
        [sys.executable, "-c", script],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert result.stdout.splitlines() == [
        "bridge_loaded=False",
        "mock_midi_loaded=False",
    ]
    assert result.stderr == ""


def test_no_real_midi_library_is_imported():
    sys.modules.pop("rytm_randomizer.reports", None)
    importlib.import_module("rytm_randomizer.reports")

    assert "mido" not in sys.modules
    assert "rtmidi" not in sys.modules


def test_passive_cli_report_behavior_remains_unchanged():
    result = subprocess.run(
        [sys.executable, "-m", "rytm_randomizer.cli", "report"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert result.stderr == ""


def test_report_exposes_no_active_cli_command_names():
    import rytm_randomizer.reports as report

    exposed_names = set(dir(report))

    assert "execute_command" not in exposed_names
    assert "send_command" not in exposed_names
    assert "hardware_test" not in exposed_names
    assert "open_port" not in exposed_names
    assert "open_midi_port" not in exposed_names
    assert "send_midi" not in exposed_names
    assert "MidiPortProvider" not in exposed_names


def test_mock_runtime_active_bridge_report_exposes_explicit_public_api():
    import rytm_randomizer.reports as report

    # After the WS-P consolidation the per-report shim modules were removed
    # and the bridge-report public API moved onto the unified
    # ``rytm_randomizer.reports`` module. The Pad 4-style ``__all__``
    # equality check is therefore replaced with a subset assertion against
    # the consolidated module's public surface.
    bridge_report_public_names = {
        "ACCEPTED_CANDIDATE",
        "BRIDGE_SUMMARY",
        "PARKED_CASES",
        "REJECTED_CASES",
        "REPORT_MODE",
        "SAFETY_BOUNDARY",
        "build_mock_runtime_active_bridge_report",
        "format_mock_runtime_active_bridge_report",
        "summarize_mock_runtime_active_bridge_report",
    }
    exposed_names = set(dir(report))

    assert bridge_report_public_names.issubset(exposed_names)


if __name__ == "__main__":
    test_importing_mock_runtime_active_bridge_report_prints_nothing()
    test_report_summarizes_bridge_contract_without_invoking_bridge()
    test_report_records_rejected_and_parked_scope()
    test_report_records_absent_runtime_and_hardware_boundaries()
    test_report_summary_is_deterministic()
    test_formatted_report_is_deterministic_and_human_readable()
    test_returned_report_data_is_copied_and_mutation_safe()
    test_report_import_does_not_import_or_invoke_bridge_or_sender()
    test_no_real_midi_library_is_imported()
    test_passive_cli_report_behavior_remains_unchanged()
    test_report_exposes_no_active_cli_command_names()
    test_mock_runtime_active_bridge_report_exposes_explicit_public_api()
