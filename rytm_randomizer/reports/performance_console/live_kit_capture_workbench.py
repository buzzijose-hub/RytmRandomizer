"""Passive live-kit capture workbench payload for the performance console."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Final, cast

LIVE_KIT_CAPTURE_WORKBENCH_VERSION: Final[str] = "performance-console-live-kit-capture-workbench-v1"
LIVE_KIT_CAPTURE_WORKBENCH_ID: Final[str] = "live-kit-capture-workbench"
LIVE_KIT_CAPTURE_WORKBENCH_STATUS: Final[str] = "passive-ready"
LIVE_KIT_CAPTURE_WORKBENCH_PACKAGE_VERSION: Final[str] = "live-kit-capture-workbench-package-v1"
LIVE_KIT_CAPTURE_WORKBENCH_BLOCKED_ACTIONS: Final[tuple[str, ...]] = (
    "receive kit from Cockpit workbench",
    "stage captured-kit mutation from Cockpit workbench",
    "apply captured-kit package from Cockpit console",
    "export captured-kit package from passive Cockpit report",
    "send captured plan from Cockpit workbench",
)
LIVE_KIT_CAPTURE_WORKBENCH_SAFETY_LINES: Final[tuple[str, ...]] = (
    "live kit capture workbench is declarative only",
    "capture slots are review metadata only",
    "no package apply from passive Cockpit report",
    "no SysEx receive from passive Cockpit report",
    "no MIDI sending",
    "no port opening",
)


def _workbench_payload_text(payload: Mapping[str, object], key: str) -> str:
    value = payload.get(key)
    if isinstance(value, str):
        return value
    return ""


def _dict_sequence(value: object) -> tuple[Mapping[str, object], ...]:
    if not isinstance(value, list):
        return ()
    return tuple(item for item in value if isinstance(item, dict))


def build_live_kit_capture_workbench(
    live_kit_capture_panel: Mapping[str, object],
) -> dict[str, object]:
    """Return passive capture-slot/package metadata for the console."""

    launch_command = _workbench_payload_text(live_kit_capture_panel, "launch_command")
    source_panel_id = _workbench_payload_text(live_kit_capture_panel, "panel_id")
    replay_commands = [
        "python -m rytm_randomizer.cli live-gui-performance-console-report --json",
        "python -m rytm_randomizer.cli rytm-live-macro-hardware-rehearsal-report --json",
        launch_command,
    ]
    disabled_controls = [
        "Receive Kit",
        "Stage Mutation",
        "Apply Package",
        "Export Package",
        "Send Captured Plan",
    ]
    capture_slots = [
        {
            "slot_key": "current-live-kit",
            "label": "Current Live Kit",
            "slot_status": "review-ready",
            "operator_command": "kit",
            "stores": "captured 12-pad anchor values plus kit fingerprint",
            "source": "Analog Rytm KIT SysEx receive in armed shell",
            "safety_note": "Workbench shows the slot; Cockpit does not receive SysEx.",
        },
        {
            "slot_key": "candidate-variation",
            "label": "Candidate Variation",
            "slot_status": "staged-only",
            "operator_command": "randomize",
            "stores": "next mutation plan derived from captured anchor",
            "source": "snapshot shell mutation planner",
            "safety_note": "The candidate is staged for review before manual send.",
        },
        {
            "slot_key": "recovery-anchor",
            "label": "Recovery Anchor",
            "slot_status": "review-ready",
            "operator_command": "Z then send",
            "stores": "captured safe kit return path",
            "source": "captured anchor state",
            "safety_note": "Recovery stays explicit and operator-present.",
        },
        {
            "slot_key": "resnapshot-target",
            "label": "Resnapshot Target",
            "slot_status": "operator-only",
            "operator_command": "resnapshot",
            "stores": "future anchor after the operator loads or saves a kit",
            "source": "next KIT SysEx receive in armed shell",
            "safety_note": "The operator chooses when the anchor changes.",
        },
    ]
    anchor_checks = [
        {
            "check_key": "kit-sysex-received",
            "label": "KIT SysEx Received",
            "status": "review-ready",
            "evidence": "armed shell receives one Analog Rytm KIT SysEx frame",
        },
        {
            "check_key": "fingerprint-recorded",
            "label": "Fingerprint Recorded",
            "status": "review-ready",
            "evidence": "captured kit fingerprint is shown before mutation",
        },
        {
            "check_key": "twelve-pad-context",
            "label": "12-Pad Context",
            "status": "review-ready",
            "evidence": "all Rytm pads remain visible in the console packet",
        },
        {
            "check_key": "lane-policy-attached",
            "label": "Lane Policy Attached",
            "status": "review-ready",
            "evidence": ("pad 5/9/10/11 and pad 6-8 OXI lane rules are in the same packet"),
        },
        {
            "check_key": "recovery-command-visible",
            "label": "Recovery Command Visible",
            "status": "review-ready",
            "evidence": "home/send and Z/send are visible before performance pressure",
        },
    ]
    readiness_gates = [
        {
            "gate_key": "capture-current-kit",
            "label": "Capture Current Kit",
            "status": "review-ready",
            "operator_action": "kit",
            "cockpit_action_allowed": False,
            "blocked_action": "receive kit from Cockpit workbench",
        },
        {
            "gate_key": "review-current-deltas",
            "label": "Review Current Deltas",
            "status": "review-ready",
            "operator_action": "changes",
            "cockpit_action_allowed": False,
            "blocked_action": "run snapshot shell review from Cockpit workbench",
        },
        {
            "gate_key": "stage-candidate",
            "label": "Stage Candidate",
            "status": "review-ready",
            "operator_action": "randomize",
            "cockpit_action_allowed": False,
            "blocked_action": "stage captured-kit mutation from Cockpit workbench",
        },
        {
            "gate_key": "manual-fire",
            "label": "Manual Fire",
            "status": "operator-only",
            "operator_action": "go",
            "cockpit_action_allowed": False,
            "blocked_action": "send captured plan from Cockpit workbench",
        },
        {
            "gate_key": "recover-anchor",
            "label": "Recover Anchor",
            "status": "review-ready",
            "operator_action": "Z then send",
            "cockpit_action_allowed": False,
            "blocked_action": "send captured recovery from Cockpit workbench",
        },
        {
            "gate_key": "resnapshot-anchor",
            "label": "Resnapshot Anchor",
            "status": "operator-only",
            "operator_action": "resnapshot",
            "cockpit_action_allowed": False,
            "blocked_action": "receive replacement anchor from Cockpit workbench",
        },
    ]
    recovery_gates = [
        {
            "gate_key": "home-send",
            "label": "Home Macro Recovery",
            "operator_sequence": "home then send",
            "expected_result": "return staged plan to the captured home macro",
            "required_before_fire": True,
        },
        {
            "gate_key": "z-send",
            "label": "Captured Anchor Recovery",
            "operator_sequence": "Z then send",
            "expected_result": "restore the captured safe kit values",
            "required_before_fire": True,
        },
        {
            "gate_key": "reload-saved-kit",
            "label": "Reload Saved Kit",
            "operator_sequence": "stop sending and reload saved kit",
            "expected_result": "manual hardware fallback if a live idea goes too far",
            "required_before_fire": False,
        },
        {
            "gate_key": "resnapshot-before-next-run",
            "label": "Resnapshot Before Next Run",
            "operator_sequence": "resnapshot",
            "expected_result": "promote the current hardware kit as the next anchor",
            "required_before_fire": False,
        },
    ]
    return {
        "workbench_version": LIVE_KIT_CAPTURE_WORKBENCH_VERSION,
        "workbench_id": LIVE_KIT_CAPTURE_WORKBENCH_ID,
        "workbench_status": LIVE_KIT_CAPTURE_WORKBENCH_STATUS,
        "title": "Live Kit Capture Workbench",
        "summary": (
            "Passive package for capture slots, anchor verification, mutation readiness, "
            "recovery gates, and future package review."
        ),
        "source_panel_id": source_panel_id,
        "launch_command": launch_command,
        "capture_slots": capture_slots,
        "anchor_verification": {
            "anchor_key": "current-live-kit",
            "expected_kit_label": "operator-selected live Rytm kit",
            "fingerprint_source": "received-kit-sysex",
            "checks": anchor_checks,
        },
        "mutation_readiness": {
            "readiness_status": "operator-gated",
            "ready_gate_count": 4,
            "blocked_gate_count": 2,
            "gates": readiness_gates,
        },
        "recovery_gates": recovery_gates,
        "package_manifest": {
            "manifest_version": LIVE_KIT_CAPTURE_WORKBENCH_PACKAGE_VERSION,
            "manifest_id": "live-kit-capture-workbench-package",
            "source_panel_id": source_panel_id,
            "exports_files": False,
            "includes": [
                "capture_slots",
                "anchor_verification",
                "mutation_readiness",
                "recovery_gates",
                "blocked_actions",
                "safety_lines",
                "replay_commands",
            ],
            "disabled_controls": disabled_controls,
            "blocked_actions": list(LIVE_KIT_CAPTURE_WORKBENCH_BLOCKED_ACTIONS),
            "replay_commands": replay_commands,
        },
        "blocked_actions": list(LIVE_KIT_CAPTURE_WORKBENCH_BLOCKED_ACTIONS),
        "safety_lines": list(LIVE_KIT_CAPTURE_WORKBENCH_SAFETY_LINES),
        "replay_commands": replay_commands,
    }


def live_kit_capture_workbench_lines(workbench: Mapping[str, object]) -> list[str]:
    """Return deterministic passive report lines for the workbench payload."""

    anchor_verification = cast(
        Mapping[str, object],
        workbench["anchor_verification"],
    )
    mutation_readiness = cast(
        Mapping[str, object],
        workbench["mutation_readiness"],
    )
    package_manifest = cast(
        Mapping[str, object],
        workbench["package_manifest"],
    )
    lines = [
        "Live kit capture workbench:",
        f"- workbench status: {workbench['workbench_status']}",
        f"- source panel: {workbench['source_panel_id']}",
        f"- anchor fingerprint source: {anchor_verification['fingerprint_source']}",
        f"- mutation readiness: {mutation_readiness['readiness_status']}",
    ]
    for slot in _dict_sequence(workbench["capture_slots"]):
        lines.append(
            f"- capture slot: {slot['slot_key']} / "
            f"{slot['operator_command']} / {slot['slot_status']}"
        )
    for check in _dict_sequence(anchor_verification["checks"]):
        lines.append(f"- anchor check: {check['check_key']} / {check['status']}")
    for gate in _dict_sequence(mutation_readiness["gates"]):
        action_state = "enabled" if gate["cockpit_action_allowed"] else "blocked"
        lines.append(
            f"- readiness gate: {gate['gate_key']} / " f"{gate['operator_action']} / {action_state}"
        )
    for recovery_gate in _dict_sequence(workbench["recovery_gates"]):
        lines.append(
            f"- recovery gate: {recovery_gate['gate_key']} / "
            f"{recovery_gate['operator_sequence']}"
        )
    lines.append(
        f"- package manifest: {package_manifest['manifest_version']} / "
        f"exports={package_manifest['exports_files']}"
    )
    lines.extend(
        f"- workbench blocked: {action}" for action in cast(list[str], workbench["blocked_actions"])
    )
    lines.extend(
        f"- workbench safety: {line}" for line in cast(list[str], workbench["safety_lines"])
    )
    return lines
