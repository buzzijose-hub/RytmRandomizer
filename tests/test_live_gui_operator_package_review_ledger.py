"""Tests for the passive operator package review ledger."""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.fast


def test_operator_package_review_ledger_summarizes_preview_mock_apply_and_receipt() -> None:
    from rytm_randomizer.reports.live_gui_performance_console_model import (
        build_live_gui_performance_console_model,
    )
    from rytm_randomizer.reports.performance_console.live_kit_operator_review_ledger import (
        build_live_kit_operator_review_ledger,
        live_kit_operator_review_ledger_lines,
    )

    operator_package = build_live_gui_performance_console_model().live_kit_operator_package

    ledger = build_live_kit_operator_review_ledger(operator_package)

    assert ledger["ledger_version"] == "performance-console-operator-package-review-ledger-v1"
    assert ledger["ledger_id"] == "operator-package-review-ledger:live-kit-operator-package"
    assert ledger["ledger_status"] == "passive-ready"
    assert ledger["operator_package_id"] == "live-kit-operator-package"
    assert ledger["review_stage_count"] == 3
    assert [stage["stage_key"] for stage in ledger["review_stages"]] == [
        "apply-preview",
        "mock-apply",
        "receipt-audit",
    ]
    assert ledger["step_count"] == 5
    assert ledger["step_rows"][0]["slot_key"] == "captured-base"
    assert ledger["step_rows"][0]["package_export_key"] == "operator-package-captured-base"
    assert ledger["step_rows"][0]["preview_status"] == "ready_for_mock_apply_preview"
    assert ledger["step_rows"][0]["mock_apply_status"] == "accepted_for_mock_apply"
    assert ledger["step_rows"][0]["receipt_status"] == "recorded_for_review"
    assert ledger["readiness_summary"] == {
        "mock_safe": True,
        "opened_midi_port": False,
        "sent_midi": False,
        "writes_files": False,
        "mutated_snapshot": False,
        "applied_send_plan": False,
        "events_emitted": False,
        "required_recovery_count": 3,
    }
    assert "send operator package from Cockpit console" in ledger["blocked_actions"]
    assert "no MIDI sending" in ledger["safety_lines"]
    assert ledger["replay_commands"] == [
        "python -m rytm_randomizer.cli live-gui-performance-console-report --json"
    ]

    lines = live_kit_operator_review_ledger_lines(ledger)
    assert "Operator package review ledger:" in lines
    assert "- ledger status: passive-ready" in lines
    assert "- review stage: apply-preview / preview_only / ready" in lines
    assert "- review stage: mock-apply / mock_apply_only / ready" in lines
    assert "- review stage: receipt-audit / passive_audit_only / ready" in lines
    assert "- step review: captured-base / operator-package-captured-base" in lines
    assert "- readiness: mock_safe=True / sent_midi=False / writes_files=False" in lines


def test_operator_package_review_ledger_tolerates_malformed_sequences() -> None:
    from rytm_randomizer.reports.performance_console.live_kit_operator_package import (
        build_live_kit_operator_package,
    )
    from rytm_randomizer.reports.performance_console.live_kit_operator_review_ledger import (
        build_live_kit_operator_review_ledger,
        live_kit_operator_review_ledger_lines,
    )

    operator_package = build_live_kit_operator_package(
        {"workbench_id": "workbench"},
        {"audition_id": "audition"},
    )
    operator_package["operator_steps"] = "ignore malformed steps"
    operator_package["slot_bindings"] = "ignore malformed bindings"
    operator_package["recovery_requirements"] = "ignore malformed requirements"
    operator_package["blocked_actions"] = "ignore malformed blocked actions"
    operator_package["safety_lines"] = "ignore malformed safety lines"

    ledger = build_live_kit_operator_review_ledger(operator_package)

    assert ledger["step_count"] == 0
    assert ledger["step_rows"] == []
    assert ledger["readiness_summary"]["required_recovery_count"] == 0
    assert ledger["blocked_actions"] == []
    assert ledger["safety_lines"] == []

    lines = live_kit_operator_review_ledger_lines(ledger)
    assert "- steps: 0" in lines
    assert not any(line.startswith("- step review:") for line in lines)
