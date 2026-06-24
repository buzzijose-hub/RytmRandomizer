from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.fast

PROJECT_ROOT = Path(__file__).resolve().parents[1]
FORBIDDEN_REAL_MIDI_AND_ADAPTER_MODULES = (
    "mido",
    "rtmidi",
    "pythonrtmidi",
    "rytm_randomizer.real_midi_adapter",
)


def test_controller_brain_operator_package_binds_gestures_to_operator_slots() -> None:
    from rytm_randomizer.reports.controller_brain_operator_package import (
        build_controller_brain_operator_package_payload,
        build_controller_brain_operator_package_report,
        format_controller_brain_operator_package_report,
    )

    report = build_controller_brain_operator_package_report()

    assert report.ledger_version == "controller-brain-operator-package-ledger-v1"
    assert report.ledger_status == "passive-ready"
    assert report.source_controller_report == "controller-brain-rehearsal-report"
    assert report.source_operator_package == "live-kit-operator-package"
    assert report.controller_profile_key == "generic-16-encoder-performance"
    assert report.operator_package_id == "live-kit-operator-package"
    assert report.gesture_binding_count == 9
    assert len(report.gesture_bindings) == 9

    bindings_by_intent = {binding.intent_key: binding for binding in report.gesture_bindings}
    assert bindings_by_intent["global.preview_depth"].operator_target == (
        "operator-package.depth-review"
    )
    assert bindings_by_intent["macro.industrial"].slot_key == "industrial-pressure"
    assert bindings_by_intent["macro.industrial"].package_export_key == (
        "operator-package-industrial-pressure"
    )
    assert bindings_by_intent["rytm.pad5.source_amount"].operator_target == (
        "operator-package.pad-lane-review"
    )
    assert bindings_by_intent["rytm.pad5.source_amount"].slot_key == "hard-groove-lift"
    assert bindings_by_intent["rytm.pad6.source_amount"].operator_target == (
        "operator-package.pad-lane-review"
    )
    assert bindings_by_intent["rytm.pad12.source_amount"].operator_target == (
        "operator-package.pad-lane-review"
    )
    assert bindings_by_intent["a4.track1.macro_depth"].operator_target == (
        "operator-package.a4-review-only"
    )
    assert bindings_by_intent["crate.dark_hypnotic"].operator_target == (
        "operator-package.crate-review"
    )
    assert bindings_by_intent["queue.next_1"].operator_target == "operator-package.queue-stage"
    assert bindings_by_intent["snapshot.panic_home"].slot_key == "recovery-return"

    assert report.readiness.opened_controller_input is False
    assert report.readiness.captured_raw_cc is False
    assert report.readiness.dispatched_websocket is False
    assert report.readiness.opened_midi_port is False
    assert report.readiness.sent_midi is False
    assert report.readiness.wrote_files is False
    assert report.readiness.mutated_snapshot is False
    assert report.readiness.armed_hardware is False
    assert report.readiness.status == "mock-safe"
    assert report.readiness.ready_for_cockpit_preview is True
    assert report.readiness.ready_for_hardware_send is False

    assert "open MIDI controller input" in report.blocked_actions
    assert "dispatch Cockpit WebSocket commands" in report.blocked_actions
    assert "send operator package from Cockpit console" in report.blocked_actions
    assert "write operator package file from passive report" in report.blocked_actions
    assert "no MIDI controller input" in report.safety_lines
    assert "no MIDI sending" in report.safety_lines
    assert "no WebSocket command dispatch" in report.safety_lines
    assert "no file writing" in report.safety_lines
    assert "python -m rytm_randomizer.cli controller-brain-operator-package-report --json" in (
        report.replay_commands
    )

    lines = format_controller_brain_operator_package_report(report)
    text = "\n".join(lines)
    assert lines[0] == "RytmRandomizer passive controller brain operator package ledger"
    assert "Controller gestures bound: 9" in lines
    assert "Operator slots: 5" in lines
    assert "macro.industrial -> operator-package.slot-selection" in text
    assert "rytm.pad5.source_amount -> operator-package.pad-lane-review" in text
    assert "snapshot.panic_home -> operator-package.recovery" in text
    assert "Ready for hardware send: False" in text
    assert "Source: rytm_randomizer.reports.controller_brain_operator_package" in text

    payload = build_controller_brain_operator_package_payload()
    model = payload["controller_brain_operator_package_ledger"]
    assert model["ledger_version"] == "controller-brain-operator-package-ledger-v1"
    assert model["gesture_binding_count"] == 9
    assert model["operator_slot_count"] == 5
    assert model["gesture_bindings"][0]["intent_key"] == "global.preview_depth"
    assert model["gesture_bindings"][1]["slot_key"] == "industrial-pressure"
    assert model["readiness"]["sent_midi"] is False
    assert model["readiness"]["ready_for_hardware_send"] is False
    assert payload["safety"][0] == "passive/read-only"

    forbidden_keys = {"midi_cc", "cc", "channel", "port", "controller_port"}
    assert all(forbidden_keys.isdisjoint(binding) for binding in model["gesture_bindings"])


def test_controller_brain_operator_package_cli_supports_text_json_and_no_hardware_imports(
    capsys: pytest.CaptureFixture[str],
) -> None:
    from rytm_randomizer.cli import main
    from rytm_randomizer.reports.controller_brain_operator_package import (
        CONTROLLER_BRAIN_OPERATOR_PACKAGE_CLI_COMMAND,
    )

    assert CONTROLLER_BRAIN_OPERATOR_PACKAGE_CLI_COMMAND.args_parser([]) == {"json_output": False}
    assert CONTROLLER_BRAIN_OPERATOR_PACKAGE_CLI_COMMAND.args_parser(["--json"]) == {
        "json_output": True
    }
    with pytest.raises(ValueError, match="accepts only optional --json"):
        CONTROLLER_BRAIN_OPERATOR_PACKAGE_CLI_COMMAND.args_parser(["extra"])

    assert main(["controller-brain-operator-package-report"]) == 0
    captured = capsys.readouterr()
    assert "RytmRandomizer passive controller brain operator package ledger" in captured.out
    assert "no MIDI sending" in captured.out
    assert captured.err == ""

    assert main(["controller-brain-operator-package-report", "--json"]) == 0
    captured_json = capsys.readouterr()
    assert captured_json.err == ""
    model = json.loads(captured_json.out)["controller_brain_operator_package_ledger"]
    assert model["ledger_status"] == "passive-ready"
    assert model["gesture_bindings"][-1]["intent_key"] == "snapshot.panic_home"

    forbidden_modules = repr(FORBIDDEN_REAL_MIDI_AND_ADAPTER_MODULES)
    code = f"""
import sys
from rytm_randomizer import cli

exit_code = cli.main(["controller-brain-operator-package-report", "--json"])
assert exit_code == 0, exit_code
for module_name in {forbidden_modules}:
    assert module_name not in sys.modules, module_name
"""
    passive_result = subprocess.run(
        [sys.executable, "-c", code],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert passive_result.returncode == 0, passive_result.stderr


def test_controller_brain_operator_package_help_mentions_passive_contract() -> None:
    from rytm_randomizer.help_text import resolve_help_text

    help_text = resolve_help_text("controller-brain-operator-package-report")

    assert help_text.startswith(
        "RytmRandomizer passive CLI: controller-brain-operator-package-report"
    )
    assert "operator package" in help_text
    assert "no MIDI controller input" in help_text
    assert "no WebSocket command dispatch" in help_text
    assert "no MIDI sending" in help_text
