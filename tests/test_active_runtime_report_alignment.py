from pathlib import Path
import importlib
import inspect
import subprocess
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def _source_keys(items):
    return tuple(item["source_key"] for item in items)


def _planning_input_by_key(items, key):
    return next(item for item in items if item["source_key"] == key)


def _unsupported_profile_by_key(profiles, key):
    return next(profile for profile in profiles if profile["profile_key"] == key)


def test_importing_alignment_report_dependencies_prints_nothing():
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "import rytm_randomizer.reports; "
            "import rytm_randomizer.reports",
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert result.stdout == ""
    assert result.stderr == ""


def test_runtime_and_active_reports_align_on_profile_2_candidate():
    from rytm_randomizer.reports import build_active_boundary_report
    from rytm_randomizer.reports import build_runtime_plan_report

    runtime_report = build_runtime_plan_report()
    active_report = build_active_boundary_report()

    runtime_profile_2 = _planning_input_by_key(
        runtime_report["supported_planning_inputs"],
        "2",
    )
    active_candidate = active_report["accepted_candidate"]

    assert runtime_profile_2["source_kind"] == "group_profile"
    assert runtime_profile_2["source_key"] == "2"
    assert runtime_profile_2["source_label"] == "group_profile:2"
    assert runtime_profile_2["status"] == "blocked"
    assert runtime_profile_2["reason_code"] == "execution_not_implemented"
    assert runtime_profile_2["supported"] is True
    assert runtime_profile_2["parked"] is False
    assert runtime_profile_2["would_execute"] is False

    assert active_candidate["source_kind"] == "group_profile"
    assert active_candidate["profile_key"] == "2"
    assert active_candidate["name"] == "My BD Hard"
    assert active_report["result_metadata"]["supported_candidate"] == "group_profile:2"
    assert active_report["result_metadata"]["boundary"] == "mock_active_boundary"


def test_profile_3_remains_runtime_supported_but_active_boundary_unsupported():
    from rytm_randomizer.reports import build_active_boundary_report
    from rytm_randomizer.reports import build_runtime_plan_report

    runtime_report = build_runtime_plan_report()
    active_report = build_active_boundary_report()

    assert _source_keys(runtime_report["supported_planning_inputs"]) == ("2", "3")

    runtime_profile_3 = _planning_input_by_key(
        runtime_report["supported_planning_inputs"],
        "3",
    )
    active_profile_3 = _unsupported_profile_by_key(
        active_report["unsupported_profiles"],
        "3",
    )

    assert runtime_profile_3["source_label"] == "group_profile:3"
    assert runtime_profile_3["reason_code"] == "execution_not_implemented"
    assert runtime_profile_3["supported"] is True
    assert runtime_profile_3["parked"] is False
    assert runtime_profile_3["would_execute"] is False

    assert active_profile_3["name"] == "My BD Classic"
    assert active_profile_3["reason"] == (
        "mock mapper/report scope only; not active-boundary supported"
    )
    assert "3" in tuple(
        profile["profile_key"] for profile in active_report["unsupported_profiles"]
    )


def test_profile_4_remains_parked_in_both_report_surfaces():
    from rytm_randomizer.reports import build_active_boundary_report
    from rytm_randomizer.reports import build_runtime_plan_report

    runtime_report = build_runtime_plan_report()
    active_report = build_active_boundary_report()

    assert _source_keys(runtime_report["parked_planning_inputs"]) == ("4",)

    runtime_profile_4 = _planning_input_by_key(
        runtime_report["parked_planning_inputs"],
        "4",
    )
    active_profile_4 = _unsupported_profile_by_key(
        active_report["unsupported_profiles"],
        "4",
    )

    assert runtime_profile_4["source_label"] == "group_profile:4"
    assert runtime_profile_4["reason_code"] == "profile_4_parked"
    assert runtime_profile_4["supported"] is False
    assert runtime_profile_4["parked"] is True
    assert runtime_profile_4["would_execute"] is False

    assert active_profile_4["name"] == "My BD Acoustic"
    assert active_profile_4["reason"] == "parked until separately approved"
    assert "4" in tuple(
        profile["profile_key"] for profile in active_report["unsupported_profiles"]
    )


def test_report_safety_boundaries_match_no_midi_no_ports_no_hardware():
    from rytm_randomizer.reports import build_active_boundary_report
    from rytm_randomizer.reports import build_runtime_plan_report

    runtime_report = build_runtime_plan_report()
    active_report = build_active_boundary_report()

    assert runtime_report["safety"] == {
        "would_execute": False,
        "mock_only": True,
        "sends_real_midi": False,
        "ports_allowed": False,
        "hardware_required": False,
    }
    assert runtime_report["runtime_execution"] == "absent"
    assert runtime_report["cli_execution_wiring"] == "absent"
    assert runtime_report["dispatch"] == "absent"
    assert runtime_report["real_midi"] == "absent"
    assert runtime_report["port_opening"] == "absent"
    assert runtime_report["hardware_required"] is False

    assert active_report["mock_only"] is True
    assert active_report["real_midi"] == "absent"
    assert active_report["port_opening"] == "absent"
    assert active_report["hardware_required"] is False
    assert active_report["active_cli_behavior"] == "absent"
    assert active_report["dispatch"] == "absent"
    assert active_report["command_execution"] == "absent"
    assert active_report["scene_execution"] == "absent"
    assert active_report["hardware_behavior"] == "absent"


def test_alignment_imports_no_real_midi_libraries():
    sys.modules.pop("rytm_randomizer.reports", None)
    sys.modules.pop("rytm_randomizer.reports", None)

    importlib.import_module("rytm_randomizer.reports")
    importlib.import_module("rytm_randomizer.reports")

    assert "mido" not in sys.modules
    assert "rtmidi" not in sys.modules


def test_alignment_report_surfaces_do_not_evaluate_active_boundary_requests():
    import rytm_randomizer.reports as active_report
    import rytm_randomizer.reports as runtime_report

    combined_source = "\n".join(
        (
            inspect.getsource(runtime_report),
            inspect.getsource(active_report),
        )
    )

    forbidden_fragments = (
        "evaluate_" + "mock_active_boundary",
        "Mock" + "MidiSender(",
        "Active" + "BoundaryRequest(",
        "execute_" + "command",
        "send_" + "command",
        "hardware_" + "test",
        "open_" + "port",
        "send_" + "midi",
    )

    for fragment in forbidden_fragments:
        assert fragment not in combined_source


def test_active_runtime_report_summaries_remain_consistent():
    from rytm_randomizer.reports import summarize_active_boundary_report
    from rytm_randomizer.reports import summarize_runtime_plan_report

    runtime_summary = summarize_runtime_plan_report()
    active_summary = summarize_active_boundary_report()

    assert runtime_summary["supported_count"] == 2
    assert runtime_summary["parked_count"] == 1
    assert runtime_summary["would_execute"] is False
    assert runtime_summary["mock_only"] is True
    assert runtime_summary["runtime_execution"] == "absent"

    assert active_summary["accepted_key"] == "2"
    assert active_summary["unsupported_keys"] == ("3", "4")
    assert active_summary["mock_only"] is True
    assert active_summary["active_cli_behavior"] == "absent"
    assert active_summary["hardware_required"] is False


if __name__ == "__main__":
    test_importing_alignment_report_dependencies_prints_nothing()
    test_runtime_and_active_reports_align_on_profile_2_candidate()
    test_profile_3_remains_runtime_supported_but_active_boundary_unsupported()
    test_profile_4_remains_parked_in_both_report_surfaces()
    test_report_safety_boundaries_match_no_midi_no_ports_no_hardware()
    test_alignment_imports_no_real_midi_libraries()
    test_alignment_report_surfaces_do_not_evaluate_active_boundary_requests()
    test_active_runtime_report_summaries_remain_consistent()
