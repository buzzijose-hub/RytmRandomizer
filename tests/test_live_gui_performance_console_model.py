"""Tests for the passive Cockpit performance console packet."""

from __future__ import annotations

import json
import sys

import pytest

pytestmark = pytest.mark.fast

FORBIDDEN_REAL_MIDI_AND_ADAPTER_MODULES = (
    "mido",
    "rtmidi",
    "pythonrtmidi",
    "rytm_randomizer.real_midi_adapter",
)


def test_performance_console_model_composes_live_cockpit_sections() -> None:
    from rytm_randomizer.reports.live_gui_performance_console_model import (
        build_live_gui_performance_console_model,
    )

    model = build_live_gui_performance_console_model(session_label="Warehouse arc")

    assert model.console_version == "live-gui-performance-console-v1"
    assert model.source_module == "reports.live_gui_performance_console_model"
    assert len(model.console_id) == 16
    assert model.session_label == "Warehouse arc"
    assert model.console_status == "mock-safe"
    assert model.hardware_mode == "passive"

    assert model.device_inventory["device_count"] == 2
    device_ids = [card["device_id"] for card in model.device_inventory["cards"]]
    assert device_ids == ["analog_rytm_mk2", "analog_four_mk2"]

    assert model.rytm_pad_surface["pad_count"] == 12
    assert len(model.rytm_pad_surface["cards"]) == 12
    assert model.rytm_pad_surface["cards"][0]["pad"] == 1
    assert model.rytm_pad_surface["cards"][-1]["pad"] == 12

    assert model.performance_flow["flow_id"] == "oxi-rytm-a4-performance-flow"
    assert model.performance_flow["analog_four_set_plan"]["set_name"] == "warehouse-arc"
    assert model.performance_flow["analog_four_set_plan"]["current_macro"] == "home"
    assert model.performance_flow["steps"][1]["key"] == "kit-core"

    rytm_lane_policy_matrix = model.rytm_lane_policy_matrix
    assert (
        rytm_lane_policy_matrix["matrix_version"]
        == "performance-console-rytm-lane-policy-matrix-v1"
    )
    assert rytm_lane_policy_matrix["matrix_status"] == "passive-ready"
    assert rytm_lane_policy_matrix["source_report"] == "oxi-live-macro-catalog-report"
    assert rytm_lane_policy_matrix["macro_count"] >= 6
    assert rytm_lane_policy_matrix["pad_groups"][0]["pads"] == [5, 9, 10, 11]
    assert "SRC-first" in rytm_lane_policy_matrix["pad_groups"][0]["summary"]
    assert "filter=off" in rytm_lane_policy_matrix["pad_groups"][0]["lane_policy"]
    assert rytm_lane_policy_matrix["pad_groups"][1]["pads"] == [6, 7, 8]
    assert "tom/source" in rytm_lane_policy_matrix["pad_groups"][1]["summary"]
    assert rytm_lane_policy_matrix["pad_groups"][2]["pads"] == [12]
    hard_groove_row = rytm_lane_policy_matrix["macro_rows"][1]
    assert hard_groove_row["macro_key"] == "hard-groove"
    assert hard_groove_row["style_crate"] == "Hard Groove"
    assert hard_groove_row["pad_policy_cards"]["5"]["lane_policies"]["filter"] == "off"
    assert hard_groove_row["pad_policy_cards"]["5"]["lane_policies"]["lfo"] == "off"
    assert hard_groove_row["pad_policy_cards"]["5"]["section_family_allowlists"]["AMP"] == [
        "delay",
        "overdrive",
        "reverb",
    ]
    assert hard_groove_row["pad_policy_cards"]["6"]["lane_policies"]["filter"] == "micro"
    assert hard_groove_row["pad_policy_cards"]["6"]["lane_policies"]["lfo"] == "off"
    assert "no MIDI sending" in rytm_lane_policy_matrix["safety_lines"]
    assert (
        "dispatch Rytm lane policy from Cockpit console"
        in rytm_lane_policy_matrix["blocked_actions"]
    )

    a4_review_surface = model.analog_four_review_surface
    assert a4_review_surface["surface_version"] == "performance-console-a4-review-surface-v1"
    assert a4_review_surface["surface_status"] == "review-only"
    assert a4_review_surface["set_name"] == "warehouse-arc"
    assert a4_review_surface["current_step"]["macro_name"] == "home"
    assert [step["macro_name"] for step in a4_review_surface["steps"]] == [
        "home",
        "hard-groove",
        "dub-pressure",
        "industrial-transition",
        "home",
    ]
    assert a4_review_surface["review_focus"]["macro_name"] == "hard-groove"
    assert a4_review_surface["review_focus"]["readiness"] == "review-ready"
    assert a4_review_surface["readiness_events"][0]["status"] == "cc-ready"
    assert (
        a4_review_surface["preflight_command"]
        == "python -m rytm_randomizer.app --arm --a4-soft-capture"
    )
    assert "Run the input-only A4 soft capture first." in a4_review_surface["validation_steps"]
    assert (
        "At least one operator-present validation pass is clean"
        in a4_review_surface["promotion_gates"]
    )
    assert "A4 full macro SEND" in a4_review_surface["blocked_actions"]
    assert "A4 unattended macro playback" in a4_review_surface["blocked_actions"]
    assert "A4 full macro SEND remains blocked" in a4_review_surface["safety_lines"]
    assert a4_review_surface["replay_command"].startswith(
        "python -m rytm_randomizer.cli analog-four-oxi-macro-set-planner-report"
    )
    assert a4_review_surface["readiness_replay_command"].startswith(
        "python -m rytm_randomizer.cli analog-four-oxi-macro-readiness-report hard-groove"
    )

    rehearsal_board = model.rehearsal_board
    assert rehearsal_board["board_version"] == "performance-console-rehearsal-board-v1"
    assert rehearsal_board["board_status"] == "passive-ready"
    assert rehearsal_board["launch_command"].startswith(
        "python -m rytm_randomizer.app --arm --rytm-live-snapshot-shell"
    )
    assert [chapter["name"] for chapter in rehearsal_board["chapters"]][:3] == [
        "capture-anchor",
        "establish-groove",
        "pressure-build",
    ]
    assert rehearsal_board["operator_cues"][1]["rytm_stage_command"] == "macro hard-groove"
    assert rehearsal_board["pad_lane_checks"][0]["pads"] == [5, 9, 10, 11]
    assert "SRC stays important" in rehearsal_board["pad_lane_checks"][0]["summary"]
    assert rehearsal_board["hardware_validation_runway"][2]["name"] == "a4-soft-capture"
    assert rehearsal_board["promotion_criteria"][0]["name"] == "a4-input-label-coverage"
    assert "fire rehearsal cue from Cockpit console" in rehearsal_board["blocked_actions"]
    assert "no MIDI sending" in rehearsal_board["safety_lines"]
    assert rehearsal_board["replay_commands"][0]["name"] == "read-strategy"

    controller_brain_panel = model.controller_brain_panel
    assert (
        controller_brain_panel["panel_version"] == "performance-console-controller-brain-panel-v1"
    )
    assert controller_brain_panel["panel_status"] == "passive-ready"
    assert controller_brain_panel["source_report"] == "controller-brain-rehearsal-report"
    assert controller_brain_panel["profile_key"] == "generic-16-encoder-performance"
    assert controller_brain_panel["scenario_key"] == "warehouse-controller-brain-rehearsal"
    assert controller_brain_panel["template_row_count"] == 112
    assert controller_brain_panel["template_page_count"] == 7
    assert controller_brain_panel["gesture_count"] == 9
    assert controller_brain_panel["template_page_cards"][0]["page_key"] == "global-brain"
    assert controller_brain_panel["template_page_cards"][0]["row_count"] == 16
    assert {
        outcome["resolved_intent_key"] for outcome in controller_brain_panel["gesture_outcomes"]
    } >= {
        "global.preview_depth",
        "rytm.pad5.source_amount",
        "rytm.pad6.source_amount",
        "rytm.pad12.source_amount",
        "a4.track1.macro_depth",
        "queue.next_1",
        "snapshot.panic_home",
    }
    assert "MIDI learn or raw CC capture" in controller_brain_panel["blocked_actions"]
    assert "no MIDI controller input" in controller_brain_panel["safety_lines"]

    live_kit_capture_panel = model.live_kit_capture_panel
    assert (
        live_kit_capture_panel["panel_version"] == "performance-console-live-kit-capture-panel-v1"
    )
    assert live_kit_capture_panel["panel_status"] == "passive-ready"
    assert live_kit_capture_panel["tagline"] == "Mutate the kit you are actually playing."
    assert live_kit_capture_panel["source_report"] == "rytm-live-macro-hardware-rehearsal-report"
    assert live_kit_capture_panel["launch_command"].startswith(
        "python -m rytm_randomizer.app --arm --rytm-live-snapshot-shell"
    )
    assert [step["step_key"] for step in live_kit_capture_panel["workflow_steps"]] == [
        "receive-kit-sysex",
        "review-captured-kit",
        "mutate-captured-kit",
        "go-send-next-variation",
        "recover-captured-anchor",
        "resnapshot-new-anchor",
    ]
    assert live_kit_capture_panel["workflow_steps"][0]["operator_command"] == "kit"
    assert live_kit_capture_panel["workflow_steps"][2]["operator_command"] == "randomize"
    assert live_kit_capture_panel["workflow_steps"][3]["operator_command"] == "go"
    assert live_kit_capture_panel["differentiators"][0]["name"] == "live-kit-capture"
    assert (
        live_kit_capture_panel["differentiators"][1]["name"] == "engine-aware-current-kit-mutation"
    )
    assert "Z then send" in live_kit_capture_panel["recovery_commands"]
    assert "receive kit from Cockpit console" in live_kit_capture_panel["blocked_actions"]
    assert "no SysEx receive from passive Cockpit report" in live_kit_capture_panel["safety_lines"]

    live_kit_capture_workbench = model.live_kit_capture_workbench
    assert (
        live_kit_capture_workbench["workbench_version"]
        == "performance-console-live-kit-capture-workbench-v1"
    )
    assert live_kit_capture_workbench["workbench_status"] == "passive-ready"
    assert live_kit_capture_workbench["source_panel_id"] == "live-kit-capture-panel"
    assert live_kit_capture_workbench["title"] == "Live Kit Capture Workbench"
    assert [slot["slot_key"] for slot in live_kit_capture_workbench["capture_slots"]] == [
        "current-live-kit",
        "candidate-variation",
        "recovery-anchor",
        "resnapshot-target",
    ]
    assert live_kit_capture_workbench["capture_slots"][0]["operator_command"] == "kit"
    assert live_kit_capture_workbench["capture_slots"][1]["operator_command"] == "randomize"
    assert live_kit_capture_workbench["capture_slots"][2]["operator_command"] == "Z then send"
    assert live_kit_capture_workbench["capture_slots"][3]["operator_command"] == "resnapshot"

    anchor_verification = live_kit_capture_workbench["anchor_verification"]
    assert anchor_verification["fingerprint_source"] == "received-kit-sysex"
    assert anchor_verification["expected_kit_label"] == "operator-selected live Rytm kit"
    assert [check["check_key"] for check in anchor_verification["checks"]] == [
        "kit-sysex-received",
        "fingerprint-recorded",
        "twelve-pad-context",
        "lane-policy-attached",
        "recovery-command-visible",
    ]
    assert {check["status"] for check in anchor_verification["checks"]} == {"review-ready"}

    mutation_readiness = live_kit_capture_workbench["mutation_readiness"]
    assert mutation_readiness["readiness_status"] == "operator-gated"
    assert mutation_readiness["ready_gate_count"] == 4
    assert mutation_readiness["blocked_gate_count"] == 2
    assert [gate["gate_key"] for gate in mutation_readiness["gates"]] == [
        "capture-current-kit",
        "review-current-deltas",
        "stage-candidate",
        "manual-fire",
        "recover-anchor",
        "resnapshot-anchor",
    ]
    assert mutation_readiness["gates"][3]["cockpit_action_allowed"] is False
    assert mutation_readiness["gates"][3]["operator_action"] == "go"

    assert [gate["gate_key"] for gate in live_kit_capture_workbench["recovery_gates"]] == [
        "home-send",
        "z-send",
        "reload-saved-kit",
        "resnapshot-before-next-run",
    ]
    assert live_kit_capture_workbench["recovery_gates"][1]["operator_sequence"] == "Z then send"
    package_manifest = live_kit_capture_workbench["package_manifest"]
    assert package_manifest["manifest_version"] == "live-kit-capture-workbench-package-v1"
    assert package_manifest["exports_files"] is False
    assert "capture_slots" in package_manifest["includes"]
    assert "Send Captured Plan" in package_manifest["disabled_controls"]
    assert "apply captured-kit package from Cockpit console" in package_manifest["blocked_actions"]
    assert (
        "apply captured-kit package from Cockpit console"
        in live_kit_capture_workbench["blocked_actions"]
    )
    assert (
        "no package apply from passive Cockpit report" in live_kit_capture_workbench["safety_lines"]
    )

    macro_deck = model.macro_action_deck
    assert macro_deck["deck_status"] == "passive-ready"
    assert macro_deck["current_macro_key"] == "capture-anchor"
    assert [card["macro_key"] for card in macro_deck["cards"]] == [
        "kit-core",
        "hard-groove",
        "industrial",
        "dub-pressure",
        "transition",
        "home",
    ]
    assert macro_deck["cards"][0]["shell_command"] == "kit-core"
    assert macro_deck["cards"][0]["send_policy"] == "stage-review-send"
    assert macro_deck["cards"][0]["hardware_send_enabled"] is False
    assert macro_deck["cards"][1]["affected_pads"] == [
        2,
        3,
        4,
        5,
        6,
        7,
        8,
        9,
        10,
        11,
        12,
    ]
    assert macro_deck["cards"][-1]["recovery_action"] == "captured-anchor"
    assert "fire macro from Cockpit console" in macro_deck["blocked_actions"]

    assert model.style_queue["deck_status"] == "passive-ready"
    assert len(model.style_queue["crate_cards"]) >= 7
    assert len(model.style_queue["queue_cards"]) >= 3
    assert len(model.style_queue["journal_cards"]) >= 1

    analyzer_panel = model.analyzer_panel
    assert analyzer_panel["panel_model_version"] == "live-gui-analyzer-panel-model-v1"
    assert analyzer_panel["panel_status"] == "empty"
    assert analyzer_panel["panel_mode"] == "split"
    assert analyzer_panel["reference_label"] == "No reference loaded"
    assert analyzer_panel["required_actions"] == ["load-reference"]
    assert analyzer_panel["controls"]["preview"]["enabled"] is False

    assert model.snapshot_history["session_label"] == "Warehouse arc"
    assert model.snapshot_history["entry_count"] == 3
    assert model.snapshot_history["current_id"] == "console-snap-03"
    assert model.command_queue["session_label"] == "Warehouse arc"
    assert model.command_queue["last_actions"][0]["snapshot_id"] == "console-snap-03"
    assert model.safety_checklist["checklist_status"] == "passed"
    assert model.safety_checklist["arm_gate"]["enabled"] is False

    assert "open_midi_port_without_arm" in model.blocked_actions
    assert "a4_outbound_macro_send" in model.blocked_actions
    assert "record-audio" in model.blocked_actions
    assert "fire rehearsal cue from Cockpit console" in model.blocked_actions
    assert "apply captured-kit package from Cockpit console" in model.blocked_actions
    assert "dispatch queued command from model" in model.blocked_actions
    assert "send MIDI from snapshot history" in model.blocked_actions
    assert "no MIDI sending" in model.safety_lines
    assert "no port opening" in model.safety_lines
    assert "no hardware mutation" in model.safety_lines
    assert model.replay_commands == (
        "python -m rytm_randomizer.cli live-gui-performance-console-report",
        "python -m rytm_randomizer.cli live-gui-performance-console-report --json",
    )


def test_live_kit_capture_workbench_tolerates_incomplete_source_panel() -> None:
    from rytm_randomizer.reports.performance_console.live_kit_capture_workbench import (
        build_live_kit_capture_workbench,
    )

    workbench = build_live_kit_capture_workbench({"panel_id": 123})

    assert workbench["source_panel_id"] == ""
    assert workbench["launch_command"] == ""
    assert workbench["replay_commands"][-1] == ""
    assert workbench["package_manifest"]["source_panel_id"] == ""


def test_live_kit_capture_workbench_lines_ignore_malformed_sequences() -> None:
    from rytm_randomizer.reports.performance_console.live_kit_capture_workbench import (
        build_live_kit_capture_workbench,
        live_kit_capture_workbench_lines,
    )

    workbench = build_live_kit_capture_workbench(
        {
            "panel_id": "live-kit-capture-panel",
            "launch_command": "python -m rytm_randomizer.app --arm --rytm-live-snapshot-shell",
        }
    )
    workbench["capture_slots"] = [
        {
            "slot_key": "kept-slot",
            "operator_command": "kit",
            "slot_status": "review-ready",
        },
        "ignore-me",
    ]
    anchor_verification = dict(workbench["anchor_verification"])
    anchor_verification["checks"] = "ignore malformed checks"
    workbench["anchor_verification"] = anchor_verification
    mutation_readiness = dict(workbench["mutation_readiness"])
    mutation_readiness["gates"] = "ignore malformed readiness gates"
    workbench["mutation_readiness"] = mutation_readiness
    workbench["recovery_gates"] = "ignore malformed recovery gates"

    lines = live_kit_capture_workbench_lines(workbench)

    assert "- capture slot: kept-slot / kit / review-ready" in lines
    assert not any(line.startswith("- anchor check:") for line in lines)
    assert not any(line.startswith("- readiness gate:") for line in lines)
    assert not any(line.startswith("- recovery gate:") for line in lines)


def test_live_kit_package_audition_tolerates_incomplete_workbench() -> None:
    from rytm_randomizer.reports.performance_console.live_kit_package_audition import (
        build_live_kit_package_audition,
    )

    audition = build_live_kit_package_audition({"workbench_id": 123})

    assert audition["source_workbench_id"] == ""
    assert audition["source_package_manifest_version"] == ""
    assert audition["replay_commands"][-1] == ""
    assert audition["audition_summary"]["slot_count"] == 5
    assert audition["package_checks"][0]["status"] == "review-only"


def test_live_kit_package_audition_lines_ignore_malformed_sequences() -> None:
    from rytm_randomizer.reports.performance_console.live_kit_package_audition import (
        build_live_kit_package_audition,
        live_kit_package_audition_lines,
    )

    audition = build_live_kit_package_audition(
        {
            "workbench_id": "live-kit-capture-workbench",
            "launch_command": "python -m rytm_randomizer.app --arm --rytm-live-snapshot-shell",
            "package_manifest": {
                "manifest_version": "live-kit-capture-workbench-package-v1",
            },
        }
    )
    audition["audition_slots"] = "ignore malformed slots"
    audition["audition_queue"] = "ignore malformed queue"
    audition["package_checks"] = "ignore malformed checks"

    lines = live_kit_package_audition_lines(audition)

    assert "- audition status: passive-ready" in lines
    assert not any(line.startswith("- audition slot:") for line in lines)
    assert not any(line.startswith("- package check:") for line in lines)


def test_performance_console_model_rejects_blank_session_label() -> None:
    from rytm_randomizer.reports.live_gui_performance_console_model import (
        build_live_gui_performance_console_model,
    )

    with pytest.raises(ValueError, match="session_label must not be blank"):
        build_live_gui_performance_console_model(session_label="   ")


def test_performance_console_model_ignores_malformed_optional_payload_sequences(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from rytm_randomizer.reports import live_gui_performance_console_model as report

    monkeypatch.setattr(
        report,
        "live_gui_device_inventory_model_payload",
        lambda _source: {
            "device_count": 2,
            "blocked_actions": "not-a-sequence",
            "safety": "not-a-sequence",
        },
    )

    model = report.build_live_gui_performance_console_model()

    assert "not-a-sequence" not in model.blocked_actions
    assert "not-a-sequence" not in model.safety_lines


def test_performance_console_payload_helpers_ignore_malformed_values() -> None:
    from rytm_randomizer.reports import live_gui_performance_console_model as report

    assert report._payload_list({"value": "not-a-list"}, "value") == []
    assert report._payload_string({"value": 123}, "value") == ""
    assert report._payload_dict({"value": "not-a-dict"}, "value") == {}
    assert report._payload_int({"value": "not-an-int"}, "value") == 0
    assert report._first_payload_dict([]) == {}
    assert report._first_payload_dict(["not-a-dict"]) == {}


def test_controller_template_page_cards_skip_invalid_rows_and_blank_pages() -> None:
    from rytm_randomizer.reports.live_gui_performance_console_model import (
        _controller_template_page_cards,
    )

    cards = _controller_template_page_cards(
        [
            "not a template row",
            {"page_key": "", "page_label": "Blank", "page_index": 99, "slot": 1},
            {
                "page_key": "valid-page",
                "page_label": "Valid Page",
                "page_index": 2,
                "slot": 7,
            },
            {
                "page_key": "valid-page",
                "page_label": "Valid Page",
                "page_index": 2,
                "slot": 9,
            },
        ]
    )

    assert cards == [
        {
            "page_key": "valid-page",
            "page_label": "Valid Page",
            "page_index": 2,
            "row_count": 2,
            "first_slot": 7,
            "last_slot": 9,
        }
    ]


def test_performance_console_payload_is_json_safe_and_passive() -> None:
    before_modules = set(sys.modules)

    from rytm_randomizer.reports.live_gui_performance_console_model import (
        live_gui_performance_console_model_payload,
    )

    payload = live_gui_performance_console_model_payload()
    json.dumps(payload, sort_keys=True)

    model = payload["live_gui_performance_console"]
    assert model["console_version"] == "live-gui-performance-console-v1"
    assert model["device_inventory"]["cards"][1]["device_id"] == "analog_four_mk2"
    assert model["rytm_pad_surface"]["pad_count"] == 12
    assert model["macro_action_deck"]["cards"][1]["macro_key"] == "hard-groove"
    assert model["macro_action_deck"]["cards"][1]["shell_command"] == "hard-groove"
    assert model["rytm_lane_policy_matrix"]["pad_groups"][0]["pads"] == [5, 9, 10, 11]
    assert model["rytm_lane_policy_matrix"]["macro_rows"][1]["macro_key"] == "hard-groove"
    assert model["rehearsal_board"]["chapters"][1]["name"] == "establish-groove"
    assert model["rehearsal_board"]["pad_lane_checks"][1]["pads"] == [6, 7, 8]
    assert model["rehearsal_board"]["hardware_validation_runway"][2]["name"] == "a4-soft-capture"
    assert model["controller_brain_panel"]["template_row_count"] == 112
    assert (
        model["controller_brain_panel"]["gesture_outcomes"][-1]["resolved_intent_key"]
        == "snapshot.panic_home"
    )
    assert model["live_kit_capture_panel"]["tagline"] == (
        "Mutate the kit you are actually playing."
    )
    assert model["live_kit_capture_panel"]["workflow_steps"][0]["step_key"] == ("receive-kit-sysex")
    assert model["live_kit_capture_panel"]["differentiators"][-1]["name"] == (
        "controller-complement"
    )
    assert model["live_kit_capture_workbench"]["capture_slots"][0]["slot_key"] == (
        "current-live-kit"
    )
    assert model["live_kit_capture_workbench"]["mutation_readiness"]["readiness_status"] == (
        "operator-gated"
    )
    assert model["live_kit_capture_workbench"]["package_manifest"]["exports_files"] is False
    audition = model["live_kit_package_audition"]
    assert audition["audition_status"] == "passive-ready"
    assert audition["source_workbench_id"] == "live-kit-capture-workbench"
    assert audition["source_package_manifest_version"] == "live-kit-capture-workbench-package-v1"
    assert audition["audition_summary"]["slot_count"] == 5
    assert audition["audition_summary"]["queue_count"] == 4
    assert audition["audition_slots"][0]["slot_key"] == "captured-base"
    assert audition["audition_slots"][1]["style_crate"] == "Hard Groove"
    assert audition["audition_slots"][2]["operator_sequence"] == [
        "randomize",
        "changes",
        "go",
    ]
    assert audition["audition_queue"][0]["queue_status"] == "current"
    assert audition["package_checks"][-1]["check_key"] == "journal-preview-only"
    assert audition["journal_preview"]["seed"] == "live-kit-audition-0001"
    assert "Send Variation" in audition["disabled_controls"]
    assert "send audition variation from Cockpit console" in audition["blocked_actions"]
    assert model["analog_four_review_surface"]["review_focus"]["macro_name"] == "hard-groove"
    assert model["analog_four_review_surface"]["readiness_events"][0]["status"] == "cc-ready"
    assert model["performance_flow"]["analog_four_set_plan"]["step_count"] == 5
    assert model["analyzer_panel"]["panel_status"] == "empty"
    assert model["analyzer_panel"]["required_actions"] == ["load-reference"]
    assert model["snapshot_history"]["entries"][0]["snapshot_id"] == "console-snap-01"
    assert payload["safety"][0] == "passive/read-only"

    imported_modules = set(sys.modules) - before_modules
    assert not (set(FORBIDDEN_REAL_MIDI_AND_ADAPTER_MODULES) & imported_modules)


def test_performance_console_report_is_operator_readable() -> None:
    from rytm_randomizer.reports.live_gui_performance_console_model import (
        build_live_gui_performance_console_model,
        format_live_gui_performance_console_model_report,
    )

    lines = format_live_gui_performance_console_model_report(
        build_live_gui_performance_console_model(session_label="Warehouse arc")
    )
    text = "\n".join(lines)

    assert lines[0] == "RytmRandomizer passive Cockpit performance console model"
    assert "Console summary:" in lines
    assert "- session: Warehouse arc" in lines
    assert "- status: mock-safe" in lines
    assert "Device rail:" in lines
    assert "- analog_rytm_mk2 / Elektron Analog Rytm MKII / 12 tracks" in lines
    assert "- analog_four_mk2 / Elektron Analog Four MKII / 4 tracks" in lines
    assert "Rytm pad surface:" in lines
    assert "- pads: 12" in lines
    assert "Rytm lane policy matrix:" in lines
    assert "- pad group: reserved-src-fx / pads 5, 9, 10, 11" in lines
    assert "- macro policy: hard-groove / pads 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12" in lines
    assert "Performance flow:" in lines
    assert "- current: capture-anchor" in lines
    assert "Macro actions:" in lines
    assert "- hard-groove: hard-groove / stage-review-send / blocked" in lines
    assert "Rehearsal board:" in lines
    assert "- chapters: 7" in lines
    assert "- next hardware validations: 2" in lines
    assert (
        "- launch: python -m rytm_randomizer.app --arm --rytm-live-snapshot-shell --confirm-rytm-snapshot-shell-send"
        in lines
    )
    assert "- pad lane: Pads 5, 9, 10, 11: SRC stays important" in lines
    assert "- hardware validation: a4-soft-capture / Analog Four MKII / input-only" in lines
    assert "Controller brain panel:" in lines
    assert "- controller template rows: 112" in lines
    assert "- controller gesture: snapshot-recovery-journal:16 -> snapshot.panic_home" in lines
    assert "Live kit capture:" in lines
    assert "- tagline: Mutate the kit you are actually playing." in lines
    assert "- capture step: receive-kit-sysex / kit" in lines
    assert "- differentiator: live-kit-capture" in lines
    assert "- recovery: Z then send" in lines
    assert "Live kit capture workbench:" in lines
    assert "- workbench status: passive-ready" in lines
    assert "- capture slot: current-live-kit / kit / review-ready" in lines
    assert "- anchor check: twelve-pad-context / review-ready" in lines
    assert "- readiness gate: manual-fire / go / blocked" in lines
    assert "- recovery gate: z-send / Z then send" in lines
    assert "- package manifest: live-kit-capture-workbench-package-v1 / exports=False" in lines
    assert "Live kit package audition:" in lines
    assert "- audition status: passive-ready" in lines
    assert "- audition slot: hard-groove-lift / Hard Groove / review-only" in lines
    assert "- audition queue: industrial-pressure / up-next / go" in lines
    assert "- package check: recovery-visible-before-fire / review-only" in lines
    assert "- journal preview: Captured Kit Audition 0001 / live-kit-audition-0001" in lines
    assert "- audition disabled control: Send Variation" in lines
    assert "A4 review surface:" in lines
    assert "- set: warehouse-arc" in lines
    assert "- review focus: hard-groove / review-ready" in lines
    assert "- validation preflight: python -m rytm_randomizer.app --arm --a4-soft-capture" in lines
    assert "- blocked: A4 full macro SEND" in lines
    assert "- safety: A4 full macro SEND remains blocked" in lines
    assert "A4 set plan:" in lines
    assert "- set: warehouse-arc" in lines
    assert "Style queue and journal:" in lines
    assert "Analyzer panel:" in lines
    assert "- analyzer status: empty" in lines
    assert "- analyzer required actions: load-reference" in lines
    assert "Snapshot history:" in lines
    assert "- current: console-snap-03" in lines
    assert "Command queue:" in lines
    assert "Safety checklist:" in lines
    assert "Blocked active actions:" in lines
    assert "Safety:" in text
    assert "no MIDI sending" in text


def test_performance_console_cli_text_and_json_modes(capsys: pytest.CaptureFixture[str]) -> None:
    from rytm_randomizer.cli import main

    assert main(["live-gui-performance-console-report"]) == 0
    text_output = capsys.readouterr().out
    assert "RytmRandomizer passive Cockpit performance console model" in text_output
    assert "A4 set plan:" in text_output
    assert "no MIDI sending" in text_output

    assert main(["live-gui-performance-console-report", "--json"]) == 0
    json_output = capsys.readouterr().out
    payload = json.loads(json_output)
    model = payload["live_gui_performance_console"]
    assert model["console_status"] == "mock-safe"
    assert model["device_inventory"]["device_count"] == 2
    assert model["analyzer_panel"]["panel_mode"] == "split"
    assert model["rytm_lane_policy_matrix"]["matrix_status"] == "passive-ready"
    assert model["controller_brain_panel"]["panel_status"] == "passive-ready"
    assert model["live_kit_capture_panel"]["panel_status"] == "passive-ready"
    assert model["live_kit_capture_workbench"]["workbench_status"] == "passive-ready"
    assert model["live_kit_package_audition"]["audition_status"] == "passive-ready"
    assert model["analog_four_review_surface"]["surface_status"] == "review-only"
    assert model["performance_flow"]["analog_four_set_plan"]["set_name"] == "warehouse-arc"


def test_performance_console_cli_rejects_unknown_args(
    capsys: pytest.CaptureFixture[str],
) -> None:
    from rytm_randomizer.cli import main

    assert main(["live-gui-performance-console-report", "--arm"]) == 2
    captured = capsys.readouterr()

    assert captured.out == ""
    assert "live-gui-performance-console-report accepts only optional --json" in captured.err
