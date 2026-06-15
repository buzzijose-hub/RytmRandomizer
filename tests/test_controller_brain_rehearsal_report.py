from __future__ import annotations

import json
import subprocess
import sys
from dataclasses import replace
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


def test_controller_brain_rehearsal_resolves_mapping_profile_to_template_rows() -> None:
    from rytm_randomizer.reports.controller_brain_rehearsal import (
        build_controller_brain_rehearsal_payload,
        build_controller_brain_rehearsal_report,
        format_controller_brain_rehearsal_report,
    )

    report = build_controller_brain_rehearsal_report()

    assert report.rehearsal_version == "controller-brain-rehearsal-v1"
    assert report.rehearsal_status == "passive-ready"
    assert report.profile_key == "generic-16-encoder-performance"
    assert report.template_row_count == 112
    assert len(report.template_rows) == 112
    assert report.template_rows[0].assignment_key == "global-brain:01"
    assert report.template_rows[0].intent_key == "global.preview_depth"
    assert report.template_rows[-1].assignment_key == "snapshot-recovery-journal:16"
    assert report.template_rows[-1].intent_key == "snapshot.panic_home"
    assert len(report.gesture_outcomes) == len(report.scenario.gestures)
    assert {outcome.resolved_intent_key for outcome in report.gesture_outcomes} >= {
        "global.preview_depth",
        "macro.industrial",
        "rytm.pad5.source_amount",
        "rytm.pad6.source_amount",
        "rytm.pad12.source_amount",
        "a4.track1.macro_depth",
        "crate.dark_hypnotic",
        "queue.next_1",
        "snapshot.panic_home",
    }
    assert all(outcome.status == "passive-intent-staged" for outcome in report.gesture_outcomes)
    assert "open MIDI controller input" in report.blocked_actions
    assert "MIDI learn or raw CC capture" in report.blocked_actions
    assert "dispatch Cockpit WebSocket commands" in report.blocked_actions
    assert "send hardware MIDI" in report.blocked_actions
    assert "no MIDI sending" in report.safety_lines
    assert "no port opening" in report.safety_lines

    lines = format_controller_brain_rehearsal_report(report)
    text = "\n".join(lines)
    assert lines[0] == "RytmRandomizer passive controller brain rehearsal report"
    assert "Controller template rows: 112" in lines
    assert "Gesture outcomes:" in lines
    assert "global-brain:01 -> global.preview_depth" in text
    assert "rytm-pads-5-8:01 -> rytm.pad5.source_amount" in text
    assert "Source: rytm_randomizer.reports.controller_brain_rehearsal" in text

    payload = build_controller_brain_rehearsal_payload()
    model = payload["controller_brain_rehearsal"]
    assert model["rehearsal_version"] == "controller-brain-rehearsal-v1"
    assert model["template_row_count"] == 112
    assert model["template_rows"][0]["assignment_key"] == "global-brain:01"
    assert model["gesture_outcomes"][0]["resolved_intent_key"] == "global.preview_depth"
    assert payload["safety"][0] == "passive/read-only"

    forbidden_keys = {"midi_cc", "cc", "channel", "port", "controller_port"}
    assert all(forbidden_keys.isdisjoint(row) for row in model["template_rows"])
    assert all(forbidden_keys.isdisjoint(row) for row in model["gesture_outcomes"])


def test_controller_brain_rehearsal_cli_supports_text_json_and_no_hardware_imports(
    capsys: pytest.CaptureFixture[str],
) -> None:
    from rytm_randomizer.cli import main
    from rytm_randomizer.reports.controller_brain_rehearsal import (
        CONTROLLER_BRAIN_REHEARSAL_CLI_COMMAND,
    )

    assert CONTROLLER_BRAIN_REHEARSAL_CLI_COMMAND.args_parser([]) == {"json_output": False}
    assert CONTROLLER_BRAIN_REHEARSAL_CLI_COMMAND.args_parser(["--json"]) == {"json_output": True}
    with pytest.raises(ValueError, match="accepts only optional --json"):
        CONTROLLER_BRAIN_REHEARSAL_CLI_COMMAND.args_parser(["extra"])

    assert main(["controller-brain-rehearsal-report"]) == 0
    captured = capsys.readouterr()
    assert "RytmRandomizer passive controller brain rehearsal report" in captured.out
    assert "no MIDI sending" in captured.out
    assert captured.err == ""

    assert main(["controller-brain-rehearsal-report", "--json"]) == 0
    captured_json = capsys.readouterr()
    assert captured_json.err == ""
    model = json.loads(captured_json.out)["controller_brain_rehearsal"]
    assert model["rehearsal_status"] == "passive-ready"
    assert model["gesture_outcomes"][-1]["resolved_intent_key"] == "snapshot.panic_home"

    forbidden_modules = repr(FORBIDDEN_REAL_MIDI_AND_ADAPTER_MODULES)
    code = f"""
import json
import sys
from rytm_randomizer import cli

exit_code = cli.main(["controller-brain-rehearsal-report", "--json"])
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


def test_controller_brain_rehearsal_rejects_unknown_scenario_and_bad_gesture() -> None:
    from rytm_randomizer.data.controller_rehearsal_scenarios import (
        CONTROLLER_REHEARSAL_SCENARIOS,
    )
    from rytm_randomizer.reports import controller_brain_rehearsal as report_module
    from rytm_randomizer.reports.controller_brain_rehearsal import (
        build_controller_brain_rehearsal_report,
    )

    with pytest.raises(ValueError, match="unknown controller rehearsal scenario"):
        build_controller_brain_rehearsal_report("missing-scenario")

    scenario = CONTROLLER_REHEARSAL_SCENARIOS["warehouse-controller-brain-rehearsal"]
    bad_page = replace(
        scenario,
        gestures=(replace(scenario.gestures[0], page_key="missing-page"),),
    )
    with pytest.raises(ValueError, match="unknown controller page"):
        report_module._gesture_outcomes(
            bad_page, report_module._template_rows(scenario.profile_key)
        )

    bad_slot = replace(
        scenario,
        gestures=(replace(scenario.gestures[0], slot=99),),
    )
    with pytest.raises(ValueError, match="unknown controller slot"):
        report_module._gesture_outcomes(
            bad_slot, report_module._template_rows(scenario.profile_key)
        )


def test_controller_brain_rehearsal_help_mentions_passive_contract() -> None:
    from rytm_randomizer.help_text import resolve_help_text

    help_text = resolve_help_text("controller-brain-rehearsal-report")

    assert help_text.startswith("RytmRandomizer passive CLI: controller-brain-rehearsal-report")
    assert "controller-template rows" in help_text
    assert "no MIDI controller input" in help_text
    assert "no MIDI sending" in help_text
