import importlib
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


def test_importing_runtime_plan_report_prints_nothing():
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


def test_report_summarizes_runtime_plan_inputs():
    from rytm_randomizer.reports import build_runtime_plan_report

    report = build_runtime_plan_report()

    assert report["title"] == "RytmRandomizer Runtime Plan Report"
    assert report["mode"] == {
        "mock_only": True,
        "metadata_only": True,
        "blocked_by_default": True,
    }
    assert report["supported_planning_inputs"] == (
        {
            "source_kind": "group_profile",
            "source_key": "2",
            "target": "Pad 1 / My BD Hard",
            "source_label": "group_profile:2",
            "status": "blocked",
            "reason": "execution not implemented",
            "reason_code": "execution_not_implemented",
            "supported": True,
            "parked": False,
            "would_execute": False,
            "mock_only": True,
            "sends_real_midi": False,
            "ports_allowed": False,
            "hardware_required": False,
        },
        {
            "source_kind": "group_profile",
            "source_key": "3",
            "target": "Pad 2 / My BD Classic",
            "source_label": "group_profile:3",
            "status": "blocked",
            "reason": "execution not implemented",
            "reason_code": "execution_not_implemented",
            "supported": True,
            "parked": False,
            "would_execute": False,
            "mock_only": True,
            "sends_real_midi": False,
            "ports_allowed": False,
            "hardware_required": False,
        },
    )
    assert report["parked_planning_inputs"] == (
        {
            "source_kind": "group_profile",
            "source_key": "4",
            "target": "Pad 1 / My BD Acoustic",
            "source_label": "group_profile:4",
            "status": "blocked",
            "reason": "profile 4 parked",
            "reason_code": "profile_4_parked",
            "supported": False,
            "parked": True,
            "would_execute": False,
            "mock_only": True,
            "sends_real_midi": False,
            "ports_allowed": False,
            "hardware_required": False,
        },
    )
    assert report["unsupported_planning_inputs"] == (
        {
            "source_kind": "group_profile",
            "source_key": "unknown",
            "target": "unknown",
            "source_label": "group_profile:unknown",
            "status": "blocked",
            "reason": "unsupported key",
            "reason_code": "unsupported_key",
            "supported": False,
            "parked": False,
            "would_execute": False,
            "mock_only": True,
            "sends_real_midi": False,
            "ports_allowed": False,
            "hardware_required": False,
        },
        {
            "source_kind": "scene",
            "source_key": "S1A",
            "target": "Rolling Light",
            "source_label": "scene:S1A",
            "status": "blocked",
            "reason": "unsupported source kind",
            "reason_code": "unsupported_source_kind",
            "supported": False,
            "parked": False,
            "would_execute": False,
            "mock_only": True,
            "sends_real_midi": False,
            "ports_allowed": False,
            "hardware_required": False,
        },
    )


def test_report_records_read_only_runtime_boundaries():
    from rytm_randomizer.reports import build_runtime_plan_report

    report = build_runtime_plan_report()

    assert report["safety"] == {
        "would_execute": False,
        "mock_only": True,
        "sends_real_midi": False,
        "ports_allowed": False,
        "hardware_required": False,
    }
    assert report["runtime_execution"] == "absent"
    assert report["cli_execution_wiring"] == "absent"
    assert report["dispatch"] == "absent"
    assert report["command_execution"] == "absent"
    assert report["scene_execution"] == "absent"
    assert report["real_midi"] == "absent"
    assert report["port_opening"] == "absent"
    assert report["hardware_required"] is False


def test_report_summary_is_deterministic():
    from rytm_randomizer.reports import summarize_runtime_plan_report

    assert summarize_runtime_plan_report() == {
        "title": "RytmRandomizer Runtime Plan Report",
        "supported_count": 2,
        "parked_count": 1,
        "unsupported_count": 2,
        "reason_codes": (
            "execution_not_implemented",
            "unsupported_key",
            "unsupported_source_kind",
            "profile_4_parked",
            "missing_arming",
        ),
        "would_execute": False,
        "mock_only": True,
        "runtime_execution": "absent",
    }


def test_formatted_report_is_deterministic_and_human_readable():
    from rytm_randomizer.reports import format_runtime_plan_report

    first = format_runtime_plan_report()
    second = format_runtime_plan_report()

    assert first == second
    assert first == [
        "RytmRandomizer Runtime Plan Report",
        "Runtime Plan Mode:",
        "- mock_only: True",
        "- metadata_only: True",
        "- blocked_by_default: True",
        "Supported Planning Inputs:",
        "- group_profile:2 -> Pad 1 / My BD Hard (execution_not_implemented)",
        "- group_profile:3 -> Pad 2 / My BD Classic (execution_not_implemented)",
        "Parked Planning Inputs:",
        "- group_profile:4 -> Pad 1 / My BD Acoustic (profile_4_parked)",
        "Unsupported Planning Inputs:",
        "- group_profile:unknown -> unknown (unsupported_key)",
        "- scene:S1A -> Rolling Light (unsupported_source_kind)",
        "Runtime Plan Safety:",
        "- would_execute: False",
        "- mock_only: True",
        "- sends_real_midi: False",
        "- ports_allowed: False",
        "- hardware_required: False",
        "- runtime_execution: absent",
        "- cli_execution_wiring: absent",
        "- dispatch: absent",
        "Source: rytm_randomizer.runtime_plan",
        "In-memory only: True",
    ]


def test_returned_report_data_is_copied_and_mutation_safe():
    from rytm_randomizer.reports import build_runtime_plan_report

    report = build_runtime_plan_report()
    report["supported_planning_inputs"][0]["target"] = "MUTATED"
    report["source"]["runtime_plan_module"] = "MUTATED"

    fresh_report = build_runtime_plan_report()

    assert fresh_report["supported_planning_inputs"][0]["target"] == "Pad 1 / My BD Hard"
    assert fresh_report["source"]["runtime_plan_module"] == "rytm_randomizer.runtime_plan"


def test_no_real_midi_library_is_imported():
    sys.modules.pop("rytm_randomizer.reports", None)
    importlib.import_module("rytm_randomizer.reports")

    assert "mido" not in sys.modules
    assert "rtmidi" not in sys.modules


def test_runtime_plan_report_exposes_no_active_behavior_names():
    import rytm_randomizer.reports as report

    exposed_names = set(dir(report))

    assert "execute_command" not in exposed_names
    assert "send_command" not in exposed_names
    assert "hardware_test" not in exposed_names
    assert "open_port" not in exposed_names
    assert "open_midi_port" not in exposed_names
    assert "send_midi" not in exposed_names


def test_runtime_plan_report_exposes_explicit_public_api():
    import rytm_randomizer.reports as report

    # After the WS-P consolidation the per-report shim modules were removed
    # and the runtime-plan report public API moved onto the unified
    # ``rytm_randomizer.reports`` module. The Pad 4-style ``__all__``
    # equality check is therefore replaced with a subset assertion against
    # the consolidated module's public surface.
    runtime_plan_public_names = {
        "PARKED_REPORT_INPUTS",
        "RUNTIME_PLAN_REPORT_BOUNDARY",
        "SUPPORTED_REPORT_INPUTS",
        "UNSUPPORTED_REPORT_INPUTS",
        "build_runtime_plan_report",
        "format_runtime_plan_report",
        "summarize_runtime_plan_report",
    }
    exposed_names = set(dir(report))

    assert runtime_plan_public_names.issubset(exposed_names)


if __name__ == "__main__":
    test_importing_runtime_plan_report_prints_nothing()
    test_report_summarizes_runtime_plan_inputs()
    test_report_records_read_only_runtime_boundaries()
    test_report_summary_is_deterministic()
    test_formatted_report_is_deterministic_and_human_readable()
    test_returned_report_data_is_copied_and_mutation_safe()
    test_no_real_midi_library_is_imported()
    test_runtime_plan_report_exposes_no_active_behavior_names()
    test_runtime_plan_report_exposes_explicit_public_api()
