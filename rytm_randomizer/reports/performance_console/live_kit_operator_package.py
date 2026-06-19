"""Passive live-kit operator package payload for the performance console."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Final, TypedDict, cast

from .payload_helpers import dict_sequence

LIVE_KIT_OPERATOR_PACKAGE_VERSION: Final[str] = "performance-console-live-kit-operator-package-v1"
LIVE_KIT_OPERATOR_PACKAGE_ID: Final[str] = "live-kit-operator-package"
LIVE_KIT_OPERATOR_PACKAGE_STATUS: Final[str] = "passive-ready"
LIVE_KIT_OPERATOR_PACKAGE_BLOCKED_ACTIONS: Final[tuple[str, ...]] = (
    "generate operator package from Cockpit console",
    "send operator package from Cockpit console",
    "write operator package file from passive report",
    "commit operator journal from passive report",
    "open MIDI port from operator package",
)
LIVE_KIT_OPERATOR_PACKAGE_SAFETY_LINES: Final[tuple[str, ...]] = (
    "live kit operator package is declarative only",
    "operator steps are browser-local rehearsal metadata",
    "local export preview does not write files",
    "journal commit remains preview-only",
    "no MIDI sending",
    "no port opening",
)


class LiveKitOperatorPackageManifest(TypedDict):
    """Passive operator package manifest summary."""

    manifest_version: str
    package_kind: str
    package_id: str
    source_audition_id: str
    source_workbench_id: str
    source_package_manifest_version: str
    slot_count: int
    queue_count: int
    recovery_count: int
    journal_preview_count: int
    exports_files: bool
    includes: list[str]


class LiveKitOperatorPackageStep(TypedDict):
    """One operator-facing local package step."""

    step_key: str
    label: str
    slot_key: str
    queue_status: str
    local_action: str
    operator_command: str
    cockpit_binding: str
    stage_target: str
    recovery_command: str
    safety_status: str


class LiveKitOperatorPackageSlotBinding(TypedDict):
    """Browser-local binding for an audition slot."""

    slot_key: str
    style_crate: str
    crate_key: str
    queue_key: str
    depth_percent: int
    journal_seed: str
    package_export_key: str
    value_source: str
    action_preview: str


class LiveKitOperatorPackageRecoveryRequirement(TypedDict):
    """Recovery requirement surfaced before any future hardware promotion."""

    requirement_key: str
    label: str
    command: str
    required_before_send: bool
    evidence: str


class LiveKitOperatorPackageJournalCommitPreview(TypedDict):
    """Journal commit preview metadata that does not write from passive mode."""

    name: str
    seed: str
    tags: list[str]
    pads: list[int]
    depth: str
    guardrail_mode: str
    value_summary: str
    notes: str
    replay_policy: str
    commit_status: str
    write_policy: str


class LiveKitOperatorPackageLocalExportPreview(TypedDict):
    """Local browser export preview for the operator package lane."""

    export_kind: str
    export_status: str
    writes_files: bool
    extra_fields: list[str]
    source_audition_id: str
    selected_slot_policy: str


class LiveKitOperatorPackagePayload(TypedDict):
    """JSON-ready passive live-kit operator package contract."""

    operator_package_version: str
    operator_package_id: str
    operator_package_status: str
    title: str
    summary: str
    source_audition_id: str
    source_workbench_id: str
    source_package_manifest_version: str
    package_manifest: LiveKitOperatorPackageManifest
    operator_steps: list[LiveKitOperatorPackageStep]
    slot_bindings: list[LiveKitOperatorPackageSlotBinding]
    recovery_requirements: list[LiveKitOperatorPackageRecoveryRequirement]
    journal_commit_preview: LiveKitOperatorPackageJournalCommitPreview
    local_export_preview: LiveKitOperatorPackageLocalExportPreview
    disabled_controls: list[str]
    blocked_actions: list[str]
    safety_lines: list[str]
    replay_commands: list[str]


def _payload_text(payload: Mapping[str, object], key: str) -> str:
    value = payload.get(key)
    if isinstance(value, str):
        return value
    return ""


def _operator_payload_int(payload: Mapping[str, object], key: str) -> int:
    value = payload.get(key)
    if isinstance(value, int):
        return value
    return 0


def _operator_payload_dict(payload: Mapping[str, object], key: str) -> Mapping[str, object]:
    value = payload.get(key)
    if isinstance(value, dict):
        return value
    return {}


def _payload_text_list(payload: Mapping[str, object], key: str) -> list[str]:
    value = payload.get(key)
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, str)]


def _payload_int_list(payload: Mapping[str, object], key: str) -> list[int]:
    value = payload.get(key)
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, int)]


def _key_from_label(label: str) -> str:
    normalized = label.lower().strip()
    chars: list[str] = []
    previous_dash = False
    for char in normalized:
        if char.isalnum():
            chars.append(char)
            previous_dash = False
            continue
        if previous_dash:
            continue
        chars.append("-")
        previous_dash = True
    return "".join(chars).strip("-")


def _queue_by_key(audition: Mapping[str, object]) -> dict[str, Mapping[str, object]]:
    rows: dict[str, Mapping[str, object]] = {}
    for row in dict_sequence(audition.get("audition_queue", [])):
        queue_key = _payload_text(row, "queue_key")
        if queue_key:
            rows[queue_key] = row
    return rows


def _operator_local_action(slot_key: str, queue_status: str) -> str:
    if slot_key == "captured-base":
        return "review-captured-anchor"
    if queue_status == "recovery":
        return "stage-recovery"
    return "stage-local-set-plan"


def _cockpit_binding(local_action: str) -> str:
    if local_action == "review-captured-anchor":
        return "Review Captured Anchor"
    if local_action == "stage-recovery":
        return "Stage Recovery Operator Package"
    return "Stage Local Operator Package"


def _operator_command(
    *,
    slot: Mapping[str, object],
    queue_item: Mapping[str, object],
) -> str:
    queue_command = _payload_text(queue_item, "fire_command")
    if queue_command:
        return queue_command
    sequence = _payload_text_list(slot, "operator_sequence")
    if sequence:
        return sequence[-1]
    return ""


def _build_operator_steps(
    *,
    audition: Mapping[str, object],
) -> list[LiveKitOperatorPackageStep]:
    queue_rows = _queue_by_key(audition)
    steps: list[LiveKitOperatorPackageStep] = []
    for slot in dict_sequence(audition.get("audition_slots", [])):
        slot_key = _payload_text(slot, "slot_key")
        label = _payload_text(slot, "label")
        if not slot_key or not label:
            continue
        queue_item = queue_rows.get(slot_key, {})
        queue_status = _payload_text(queue_item, "queue_status") or "reference"
        local_action = _operator_local_action(slot_key, queue_status)
        steps.append(
            {
                "step_key": f"operator-step-{slot_key}",
                "label": label,
                "slot_key": slot_key,
                "queue_status": queue_status,
                "local_action": local_action,
                "operator_command": _operator_command(slot=slot, queue_item=queue_item),
                "cockpit_binding": _cockpit_binding(local_action),
                "stage_target": queue_status if queue_status != "reference" else "anchor",
                "recovery_command": _payload_text(slot, "recovery_command"),
                "safety_status": "browser-local-only",
            }
        )
    return steps


def _slot_bindings(
    *,
    audition: Mapping[str, object],
) -> list[LiveKitOperatorPackageSlotBinding]:
    queue_rows = _queue_by_key(audition)
    bindings: list[LiveKitOperatorPackageSlotBinding] = []
    for slot in dict_sequence(audition.get("audition_slots", [])):
        slot_key = _payload_text(slot, "slot_key")
        style_crate = _payload_text(slot, "style_crate")
        if not slot_key or not style_crate:
            continue
        queue_item = queue_rows.get(slot_key, {})
        energy = _operator_payload_int(slot, "energy")
        bindings.append(
            {
                "slot_key": slot_key,
                "style_crate": style_crate,
                "crate_key": _key_from_label(style_crate),
                "queue_key": _payload_text(queue_item, "queue_key"),
                "depth_percent": min(max(energy * 10, 10), 90),
                "journal_seed": _payload_text(slot, "seed"),
                "package_export_key": f"operator-package-{slot_key}",
                "value_source": "captured-kit-audition-slot",
                "action_preview": "browser-local-stage",
            }
        )
    return bindings


def _recovery_requirements(
    *,
    audition: Mapping[str, object],
) -> list[LiveKitOperatorPackageRecoveryRequirement]:
    seen: set[str] = set()
    requirements: list[LiveKitOperatorPackageRecoveryRequirement] = []
    for slot in dict_sequence(audition.get("audition_slots", [])):
        command = _payload_text(slot, "recovery_command")
        if not command:
            continue
        requirement_key = _key_from_label(command)
        if requirement_key in seen:
            continue
        seen.add(requirement_key)
        requirements.append(
            {
                "requirement_key": requirement_key,
                "label": f"Recovery: {command}",
                "command": command,
                "required_before_send": True,
                "evidence": f"{_payload_text(slot, 'slot_key')} exposes recovery before staging",
            }
        )
    return requirements


def _journal_commit_preview(
    *,
    audition: Mapping[str, object],
) -> LiveKitOperatorPackageJournalCommitPreview:
    journal = _operator_payload_dict(audition, "journal_preview")
    return {
        "name": _payload_text(journal, "name"),
        "seed": _payload_text(journal, "seed"),
        "tags": _payload_text_list(journal, "tags"),
        "pads": _payload_int_list(journal, "pads"),
        "depth": _payload_text(journal, "depth"),
        "guardrail_mode": _payload_text(journal, "guardrail_mode"),
        "value_summary": _payload_text(journal, "value_summary"),
        "notes": _payload_text(journal, "notes"),
        "replay_policy": _payload_text(journal, "replay_policy"),
        "commit_status": "preview-only",
        "write_policy": "blocked-from-passive-console",
    }


def build_live_kit_operator_package(
    live_kit_capture_workbench: Mapping[str, object],
    live_kit_package_audition: Mapping[str, object],
) -> LiveKitOperatorPackagePayload:
    """Return passive operator package metadata for the captured-kit audition lane."""

    source_workbench_id = _payload_text(live_kit_capture_workbench, "workbench_id")
    source_audition_id = _payload_text(live_kit_package_audition, "audition_id")
    source_manifest_version = _payload_text(
        live_kit_package_audition,
        "source_package_manifest_version",
    )
    operator_steps = _build_operator_steps(audition=live_kit_package_audition)
    slot_bindings = _slot_bindings(audition=live_kit_package_audition)
    recovery_requirements = _recovery_requirements(audition=live_kit_package_audition)
    journal_commit_preview = _journal_commit_preview(audition=live_kit_package_audition)
    replay_commands = [
        "python -m rytm_randomizer.cli live-gui-performance-console-report --json",
        "python -m rytm_randomizer.cli oxi-live-macro-catalog-report",
        _payload_text(live_kit_capture_workbench, "launch_command"),
    ]
    payload: LiveKitOperatorPackagePayload = {
        "operator_package_version": LIVE_KIT_OPERATOR_PACKAGE_VERSION,
        "operator_package_id": LIVE_KIT_OPERATOR_PACKAGE_ID,
        "operator_package_status": LIVE_KIT_OPERATOR_PACKAGE_STATUS,
        "title": "Live Kit Operator Package",
        "summary": (
            "Browser-local package lane that turns captured-kit audition slots into "
            "reviewable operator steps, recovery checks, journal previews, and local exports."
        ),
        "source_audition_id": source_audition_id,
        "source_workbench_id": source_workbench_id,
        "source_package_manifest_version": source_manifest_version,
        "package_manifest": {
            "manifest_version": "live-kit-operator-package-manifest-v1",
            "package_kind": "rytmrandomizer.live-kit.operator-package",
            "package_id": LIVE_KIT_OPERATOR_PACKAGE_ID,
            "source_audition_id": source_audition_id,
            "source_workbench_id": source_workbench_id,
            "source_package_manifest_version": source_manifest_version,
            "slot_count": len(slot_bindings),
            "queue_count": len(dict_sequence(live_kit_package_audition.get("audition_queue", []))),
            "recovery_count": len(recovery_requirements),
            "journal_preview_count": 1 if journal_commit_preview["seed"] else 0,
            "exports_files": False,
            "includes": [
                "audition_slots",
                "audition_queue",
                "operator_steps",
                "slot_bindings",
                "recovery_requirements",
                "journal_commit_preview",
                "local_export_preview",
                "blocked_actions",
            ],
        },
        "operator_steps": operator_steps,
        "slot_bindings": slot_bindings,
        "recovery_requirements": recovery_requirements,
        "journal_commit_preview": journal_commit_preview,
        "local_export_preview": {
            "export_kind": "rytmrandomizer.cockpit.local-rehearsal-package",
            "export_status": "browser-local-only",
            "writes_files": False,
            "extra_fields": ["auditionSource", "operatorPackage"],
            "source_audition_id": source_audition_id,
            "selected_slot_policy": "operator-selected-local-slot",
        },
        "disabled_controls": [
            "Stage Operator Package",
            "Commit Operator Journal",
            "Write Operator Package",
            "Send Operator Package",
            "Open MIDI Port",
        ],
        "blocked_actions": list(LIVE_KIT_OPERATOR_PACKAGE_BLOCKED_ACTIONS),
        "safety_lines": list(LIVE_KIT_OPERATOR_PACKAGE_SAFETY_LINES),
        "replay_commands": replay_commands,
    }
    return payload


def live_kit_operator_package_lines(operator_package: Mapping[str, object]) -> list[str]:
    """Return deterministic passive report lines for the operator package payload."""

    manifest = cast(Mapping[str, object], operator_package["package_manifest"])
    local_export_preview = cast(Mapping[str, object], operator_package["local_export_preview"])
    journal_commit_preview = cast(
        Mapping[str, object],
        operator_package["journal_commit_preview"],
    )
    lines = [
        "Live kit operator package:",
        f"- operator package status: {operator_package['operator_package_status']}",
        f"- source audition: {operator_package['source_audition_id']}",
        f"- source workbench: {operator_package['source_workbench_id']}",
        f"- package kind: {manifest['package_kind']}",
        f"- operator steps: {len(dict_sequence(operator_package['operator_steps']))}",
        f"- slot bindings: {len(dict_sequence(operator_package['slot_bindings']))}",
        f"- recovery requirements: {len(dict_sequence(operator_package['recovery_requirements']))}",
    ]
    for step in dict_sequence(operator_package["operator_steps"]):
        lines.append(
            f"- operator step: {step['slot_key']} / {step['local_action']} / "
            f"{step['operator_command']}"
        )
    for binding in dict_sequence(operator_package["slot_bindings"]):
        lines.append(f"- slot binding: {binding['slot_key']} / {binding['package_export_key']}")
    for requirement in dict_sequence(operator_package["recovery_requirements"]):
        lines.append(
            f"- recovery requirement: {requirement['requirement_key']} / "
            f"{requirement['command']}"
        )
    lines.append(
        f"- journal commit preview: {journal_commit_preview['name']} / "
        f"{journal_commit_preview['commit_status']}"
    )
    lines.append(
        f"- local export preview: {local_export_preview['export_status']} / "
        f"writes={local_export_preview['writes_files']}"
    )
    lines.extend(
        f"- operator package disabled control: {control}"
        for control in cast(list[str], operator_package["disabled_controls"])
    )
    lines.extend(
        f"- operator package blocked: {action}"
        for action in cast(list[str], operator_package["blocked_actions"])
    )
    lines.extend(
        f"- operator package safety: {line}"
        for line in cast(list[str], operator_package["safety_lines"])
    )
    return lines
