"""Passive operator package review ledger for the performance console."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Final, TypedDict, cast

from .payload_helpers import dict_sequence, payload_int, payload_text, payload_text_list

LIVE_KIT_OPERATOR_REVIEW_LEDGER_VERSION: Final[str] = (
    "performance-console-operator-package-review-ledger-v1"
)
LIVE_KIT_OPERATOR_REVIEW_LEDGER_STATUS: Final[str] = "passive-ready"
LIVE_KIT_OPERATOR_REVIEW_LEDGER_REPLAY_COMMANDS: Final[tuple[str, ...]] = (
    "python -m rytm_randomizer.cli live-gui-performance-console-report --json",
)


class LiveKitOperatorReviewLedgerStage(TypedDict):
    """One passive review stage in the operator package ledger."""

    stage_key: str
    label: str
    policy: str
    status: str
    summary: str
    opened_midi_port: bool
    sent_midi: bool
    writes_files: bool
    mutates_snapshot: bool
    applies_send_plan: bool


class LiveKitOperatorReviewLedgerStep(TypedDict):
    """One operator package step normalized for review."""

    order: int
    step_key: str
    label: str
    slot_key: str
    package_export_key: str
    queue_status: str
    local_action: str
    operator_command: str
    recovery_command: str
    depth_percent: int
    preview_status: str
    mock_apply_status: str
    receipt_status: str


class LiveKitOperatorReviewLedgerReadinessSummary(TypedDict):
    """Passive side-effect summary for the review ledger."""

    mock_safe: bool
    opened_midi_port: bool
    sent_midi: bool
    writes_files: bool
    mutated_snapshot: bool
    applied_send_plan: bool
    events_emitted: bool
    required_recovery_count: int


class LiveKitOperatorReviewLedgerPayload(TypedDict):
    """JSON-ready passive operator package review ledger contract."""

    ledger_version: str
    ledger_id: str
    ledger_status: str
    title: str
    operator_package_id: str
    source_audition_id: str
    source_workbench_id: str
    review_stage_count: int
    step_count: int
    review_stages: list[LiveKitOperatorReviewLedgerStage]
    step_rows: list[LiveKitOperatorReviewLedgerStep]
    readiness_summary: LiveKitOperatorReviewLedgerReadinessSummary
    blocked_actions: list[str]
    safety_lines: list[str]
    replay_commands: list[str]


def _review_stages() -> list[LiveKitOperatorReviewLedgerStage]:
    return [
        {
            "stage_key": "apply-preview",
            "label": "Apply Preview",
            "policy": "preview_only",
            "status": "ready",
            "summary": "Review selected operator steps and blocked actions before mock apply.",
            "opened_midi_port": False,
            "sent_midi": False,
            "writes_files": False,
            "mutates_snapshot": False,
            "applies_send_plan": False,
        },
        {
            "stage_key": "mock-apply",
            "label": "Mock Apply",
            "policy": "mock_apply_only",
            "status": "ready",
            "summary": "Accept browser-local rehearsal intent without touching hardware.",
            "opened_midi_port": False,
            "sent_midi": False,
            "writes_files": False,
            "mutates_snapshot": False,
            "applies_send_plan": False,
        },
        {
            "stage_key": "receipt-audit",
            "label": "Receipt Audit",
            "policy": "passive_audit_only",
            "status": "ready",
            "summary": "Record review evidence for the passive report and operator handoff.",
            "opened_midi_port": False,
            "sent_midi": False,
            "writes_files": False,
            "mutates_snapshot": False,
            "applies_send_plan": False,
        },
    ]


def _slot_bindings_by_key(
    operator_package: Mapping[str, object],
) -> dict[str, Mapping[str, object]]:
    bindings: dict[str, Mapping[str, object]] = {}
    for binding in dict_sequence(operator_package.get("slot_bindings", [])):
        slot_key = payload_text(binding, "slot_key")
        if slot_key:
            bindings[slot_key] = binding
    return bindings


def _step_rows(
    operator_package: Mapping[str, object],
) -> list[LiveKitOperatorReviewLedgerStep]:
    bindings = _slot_bindings_by_key(operator_package)
    rows: list[LiveKitOperatorReviewLedgerStep] = []
    for order, step in enumerate(
        dict_sequence(operator_package.get("operator_steps", [])), start=1
    ):
        slot_key = payload_text(step, "slot_key")
        binding = bindings.get(slot_key, {})
        package_export_key = payload_text(binding, "package_export_key")
        if not package_export_key and slot_key:
            package_export_key = f"operator-package-{slot_key}"
        rows.append(
            {
                "order": order,
                "step_key": payload_text(step, "step_key"),
                "label": payload_text(step, "label"),
                "slot_key": slot_key,
                "package_export_key": package_export_key,
                "queue_status": payload_text(step, "queue_status"),
                "local_action": payload_text(step, "local_action"),
                "operator_command": payload_text(step, "operator_command"),
                "recovery_command": payload_text(step, "recovery_command"),
                "depth_percent": payload_int(binding, "depth_percent"),
                "preview_status": "ready_for_mock_apply_preview",
                "mock_apply_status": "accepted_for_mock_apply",
                "receipt_status": "recorded_for_review",
            }
        )
    return rows


def build_live_kit_operator_review_ledger(
    operator_package: Mapping[str, object],
) -> LiveKitOperatorReviewLedgerPayload:
    """Return a passive review ledger for the operator package payload."""

    operator_package_id = payload_text(operator_package, "operator_package_id")
    review_stages = _review_stages()
    step_rows = _step_rows(operator_package)
    recovery_count = len(dict_sequence(operator_package.get("recovery_requirements", [])))
    return {
        "ledger_version": LIVE_KIT_OPERATOR_REVIEW_LEDGER_VERSION,
        "ledger_id": f"operator-package-review-ledger:{operator_package_id}",
        "ledger_status": LIVE_KIT_OPERATOR_REVIEW_LEDGER_STATUS,
        "title": "Operator Package Review Ledger",
        "operator_package_id": operator_package_id,
        "source_audition_id": payload_text(operator_package, "source_audition_id"),
        "source_workbench_id": payload_text(operator_package, "source_workbench_id"),
        "review_stage_count": len(review_stages),
        "step_count": len(step_rows),
        "review_stages": review_stages,
        "step_rows": step_rows,
        "readiness_summary": {
            "mock_safe": True,
            "opened_midi_port": False,
            "sent_midi": False,
            "writes_files": False,
            "mutated_snapshot": False,
            "applied_send_plan": False,
            "events_emitted": False,
            "required_recovery_count": recovery_count,
        },
        "blocked_actions": payload_text_list(operator_package, "blocked_actions"),
        "safety_lines": payload_text_list(operator_package, "safety_lines"),
        "replay_commands": list(LIVE_KIT_OPERATOR_REVIEW_LEDGER_REPLAY_COMMANDS),
    }


def live_kit_operator_review_ledger_lines(
    ledger: Mapping[str, object],
) -> list[str]:
    """Return deterministic passive report lines for the review ledger."""

    readiness = cast(Mapping[str, object], ledger["readiness_summary"])
    lines = [
        "Operator package review ledger:",
        f"- ledger status: {ledger['ledger_status']}",
        f"- operator package: {ledger['operator_package_id']}",
        f"- review stages: {ledger['review_stage_count']}",
        f"- steps: {ledger['step_count']}",
    ]
    for stage in dict_sequence(ledger.get("review_stages", [])):
        lines.append(
            f"- review stage: {stage['stage_key']} / {stage['policy']} / {stage['status']}"
        )
    for row in dict_sequence(ledger.get("step_rows", [])):
        lines.append(f"- step review: {row['slot_key']} / {row['package_export_key']}")
    lines.append(
        f"- readiness: mock_safe={readiness['mock_safe']} / "
        f"sent_midi={readiness['sent_midi']} / writes_files={readiness['writes_files']}"
    )
    lines.extend(
        f"- ledger blocked: {action}" for action in payload_text_list(ledger, "blocked_actions")
    )
    lines.extend(f"- ledger safety: {line}" for line in payload_text_list(ledger, "safety_lines"))
    return lines


__all__ = [
    "LIVE_KIT_OPERATOR_REVIEW_LEDGER_REPLAY_COMMANDS",
    "LIVE_KIT_OPERATOR_REVIEW_LEDGER_STATUS",
    "LIVE_KIT_OPERATOR_REVIEW_LEDGER_VERSION",
    "LiveKitOperatorReviewLedgerPayload",
    "LiveKitOperatorReviewLedgerReadinessSummary",
    "LiveKitOperatorReviewLedgerStage",
    "LiveKitOperatorReviewLedgerStep",
    "build_live_kit_operator_review_ledger",
    "live_kit_operator_review_ledger_lines",
]
