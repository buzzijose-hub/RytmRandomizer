"""Passive Cockpit performance console packet for the future desktop UI."""

from __future__ import annotations

import hashlib
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Final, TypedDict, cast

from ..cli_registry import CliCommand, make_passive_report_command, register
from ..cockpit.data import History, HistoryEntry, PadState, Snapshot
from .analog_four_oxi_macro_readiness import (
    build_analog_four_oxi_macro_readiness_payload,
    build_analog_four_oxi_macro_readiness_report,
)
from .analog_four_oxi_macro_set_planner import (
    build_analog_four_oxi_macro_set_planner_payload,
    build_analog_four_oxi_macro_set_planner_report,
)
from .controller_brain_rehearsal import build_controller_brain_rehearsal_payload
from .formatter import SAFETY_SECTION_HEADER, PassiveReportHeader, passive_report_lines
from .live_gui_12_pad_surface_model import (
    build_live_gui_12_pad_surface_model,
    live_gui_12_pad_surface_model_payload,
)
from .live_gui_analyzer_panel_model import (
    build_live_gui_analyzer_panel_model,
    to_live_gui_analyzer_panel_model_json,
)
from .live_gui_command_queue_model import (
    build_live_gui_command_queue_model,
    to_live_gui_command_queue_model_json,
)
from .live_gui_device_inventory_model import (
    build_live_gui_device_inventory_model,
    live_gui_device_inventory_model_payload,
)
from .live_gui_performance_flow_model import (
    build_live_gui_performance_flow_model,
    live_gui_performance_flow_model_payload,
)
from .live_gui_safety_checklist_model import (
    build_live_gui_safety_checklist_model,
    to_live_gui_safety_checklist_model_json,
)
from .live_gui_snapshot_history_model import (
    build_live_gui_snapshot_history_model,
    to_live_gui_snapshot_history_model_json,
)
from .oxi_live_macro_catalog import (
    OxiLiveMacroCatalogReport,
    build_oxi_live_macro_catalog_report,
)
from .oxi_live_set_strategy import build_oxi_live_set_strategy_payload
from .performance_console.live_kit_capture_workbench import (
    build_live_kit_capture_workbench,
    live_kit_capture_workbench_lines,
)
from .performance_console.live_kit_package_audition import (
    build_live_kit_package_audition,
    live_kit_package_audition_lines,
)
from .rytm_live_macro_hardware_rehearsal import (
    build_rytm_live_macro_hardware_rehearsal_payload,
)
from .style_crate_rehearsal_deck import (
    build_style_crate_rehearsal_deck,
    to_style_crate_rehearsal_deck_json,
)

REPORT_TITLE: Final[str] = "RytmRandomizer passive Cockpit performance console model"
SOURCE_MODULE: Final[str] = "reports.live_gui_performance_console_model"
CONSOLE_VERSION: Final[str] = "live-gui-performance-console-v1"
CONSOLE_STATUS: Final[str] = "mock-safe"
HARDWARE_MODE: Final[str] = "passive"
MACRO_ACTION_DECK_VERSION: Final[str] = "performance-console-macro-action-deck-v1"
MACRO_ACTION_DECK_ID: Final[str] = "rytm-live-macro-actions"
MACRO_ACTION_DECK_STATUS: Final[str] = "passive-ready"
MACRO_ACTION_HARDWARE_STATE: Final[str] = "blocked"
MACRO_ACTION_BLOCKED_ACTIONS: Final[tuple[str, ...]] = (
    "fire macro from Cockpit console",
    "prepare hardware send from Cockpit macro action",
)
MACRO_ACTION_SAFETY_LINES: Final[tuple[str, ...]] = (
    "macro action cards are declarative only",
    "operators still use the armed snapshot shell for real sends",
    "all Cockpit macro fire controls stay disabled",
)
MACRO_ACTION_REPLAY_COMMANDS: Final[tuple[str, ...]] = (
    "python -m rytm_randomizer.cli oxi-live-macro-catalog-report",
    "python -m rytm_randomizer.cli live-gui-performance-flow-model-report --json",
)
REHEARSAL_BOARD_VERSION: Final[str] = "performance-console-rehearsal-board-v1"
REHEARSAL_BOARD_ID: Final[str] = "oxi-live-rehearsal-board"
REHEARSAL_BOARD_STATUS: Final[str] = "passive-ready"
REHEARSAL_BOARD_BLOCKED_ACTIONS: Final[tuple[str, ...]] = (
    "fire rehearsal cue from Cockpit console",
    "open MIDI port from rehearsal board",
    "send MIDI from rehearsal board",
    "promote A4 macro from rehearsal board",
)
REHEARSAL_BOARD_SAFETY_LINES: Final[tuple[str, ...]] = (
    "rehearsal board is declarative only",
    "launch command is shown for operator copy/review only",
    "real Rytm sends remain in the explicitly armed snapshot shell",
    "A4 outbound macro promotion remains blocked",
    "no MIDI sending",
)
CONTROLLER_BRAIN_PANEL_VERSION: Final[str] = "performance-console-controller-brain-panel-v1"
CONTROLLER_BRAIN_PANEL_ID: Final[str] = "controller-brain-rehearsal-panel"
LIVE_KIT_CAPTURE_PANEL_VERSION: Final[str] = "performance-console-live-kit-capture-panel-v1"
LIVE_KIT_CAPTURE_PANEL_ID: Final[str] = "live-kit-capture-panel"
LIVE_KIT_CAPTURE_PANEL_STATUS: Final[str] = "passive-ready"
LIVE_KIT_CAPTURE_BLOCKED_ACTIONS: Final[tuple[str, ...]] = (
    "receive kit from Cockpit console",
    "mutate captured kit from Cockpit console",
    "send captured plan from Cockpit console",
    "open Rytm SysEx input from passive Cockpit report",
)
LIVE_KIT_CAPTURE_SAFETY_LINES: Final[tuple[str, ...]] = (
    "live kit capture panel is declarative only",
    "no SysEx receive from passive Cockpit report",
    "operators still run the armed snapshot shell manually",
    "captured-anchor recovery remains explicit",
    "no MIDI sending",
    "no port opening",
)
A4_REVIEW_SURFACE_VERSION: Final[str] = "performance-console-a4-review-surface-v1"
A4_REVIEW_SURFACE_ID: Final[str] = "a4-oxi-macro-review-surface"
A4_REVIEW_SURFACE_STATUS: Final[str] = "review-only"
A4_REVIEW_EVENT_LIMIT: Final[int] = 4
A4_REVIEW_BLOCKED_ACTIONS: Final[tuple[str, ...]] = (
    "trigger A4 macro from Cockpit console",
    "open A4 output port from Cockpit console",
)
A4_REVIEW_SAFETY_LINES: Final[tuple[str, ...]] = (
    "A4 review surface is declarative only",
    "A4 validation commands are shown for operator review only",
    "no MIDI sending",
    "no port opening",
)
RYTM_LANE_POLICY_MATRIX_VERSION: Final[str] = "performance-console-rytm-lane-policy-matrix-v1"
RYTM_LANE_POLICY_MATRIX_ID: Final[str] = "rytm-oxi-lane-policy-matrix"
RYTM_LANE_POLICY_MATRIX_STATUS: Final[str] = "passive-ready"
RYTM_LANE_POLICY_BLOCKED_ACTIONS: Final[tuple[str, ...]] = (
    "dispatch Rytm lane policy from Cockpit console",
    "send Rytm lane policy from Cockpit console",
)
RYTM_LANE_POLICY_SAFETY_LINES: Final[tuple[str, ...]] = (
    "Rytm lane policy matrix is declarative only",
    "Cockpit shows macro policy before the armed snapshot shell applies anything",
    "no MIDI sending",
    "no port opening",
)
RYTM_LANE_POLICY_REPLAY_COMMANDS: Final[tuple[str, ...]] = (
    "python -m rytm_randomizer.cli oxi-live-macro-catalog-report",
)
_RYTM_LANE_POLICY_PAD_GROUPS: Final[tuple[dict[str, object], ...]] = (
    {
        "group_key": "reserved-src-fx",
        "pads": [5, 9, 10, 11],
        "summary": "SRC-first reserved percussion pads",
        "lane_policy": ("SRC primary; filter=off; lfo=off; AMP limited to overdrive/delay/reverb"),
        "operator_note": (
            "Pads 5, 9, 10, and 11 keep source movement as the main musical control."
        ),
    },
    {
        "group_key": "tom-source",
        "pads": [6, 7, 8],
        "summary": "tom/source movement pads",
        "lane_policy": (
            "SRC primary; filter=micro/light; lfo=off; AMP limited to overdrive/delay/reverb"
        ),
        "operator_note": (
            "Pads 6-8 can move harder on tom source controls while filter stays light."
        ),
    },
    {
        "group_key": "pad-12-supported",
        "pads": [12],
        "summary": "product-supported expansion pad",
        "lane_policy": "Pad 12 remains eligible for product users even when Jose does not use it.",
        "operator_note": "Keep Pad 12 visible as supported, but do not make it a live dependency.",
    },
)
REPLAY_COMMANDS: Final[tuple[str, ...]] = (
    "python -m rytm_randomizer.cli live-gui-performance-console-report",
    "python -m rytm_randomizer.cli live-gui-performance-console-report --json",
)
BASE_SAFETY_LINES: Final[tuple[str, ...]] = (
    "passive/read-only",
    "Cockpit performance console packet only",
    "composes passive report metadata only",
    "JSON/stdout only",
    "no GUI launch",
    "no file writing",
    "no command execution",
    "no MIDI sending",
    "no port opening",
    "no hardware mutation",
    "no hardware required",
)
_FIXED_CAPTURED_AT: Final[datetime] = datetime(2026, 6, 12, 12, 0, tzinfo=timezone.utc)
_HEADER: Final[PassiveReportHeader] = PassiveReportHeader(
    title=REPORT_TITLE,
    source_module=SOURCE_MODULE,
)


@dataclass(frozen=True)
class LiveGuiPerformanceConsoleModel:
    """One GUI-ready passive packet for the whole live performance console."""

    console_version: str
    source_module: str
    console_id: str
    session_label: str
    console_status: str
    hardware_mode: str
    device_inventory: dict[str, object]
    rytm_pad_surface: dict[str, object]
    rytm_lane_policy_matrix: dict[str, object]
    performance_flow: dict[str, object]
    macro_action_deck: dict[str, object]
    rehearsal_board: dict[str, object]
    controller_brain_panel: dict[str, object]
    live_kit_capture_panel: dict[str, object]
    live_kit_capture_workbench: dict[str, object]
    live_kit_package_audition: dict[str, object]
    analog_four_review_surface: dict[str, object]
    style_queue: dict[str, object]
    analyzer_panel: dict[str, object]
    snapshot_history: dict[str, object]
    command_queue: dict[str, object]
    safety_checklist: dict[str, object]
    blocked_actions: tuple[str, ...]
    safety_lines: tuple[str, ...]
    replay_commands: tuple[str, ...]


class LiveGuiPerformanceConsoleModelDict(TypedDict):
    """JSON-ready contract for :class:`LiveGuiPerformanceConsoleModel`."""

    console_version: str
    source_module: str
    console_id: str
    session_label: str
    console_status: str
    hardware_mode: str
    device_inventory: dict[str, object]
    rytm_pad_surface: dict[str, object]
    rytm_lane_policy_matrix: dict[str, object]
    performance_flow: dict[str, object]
    macro_action_deck: dict[str, object]
    rehearsal_board: dict[str, object]
    controller_brain_panel: dict[str, object]
    live_kit_capture_panel: dict[str, object]
    live_kit_capture_workbench: dict[str, object]
    live_kit_package_audition: dict[str, object]
    analog_four_review_surface: dict[str, object]
    style_queue: dict[str, object]
    analyzer_panel: dict[str, object]
    snapshot_history: dict[str, object]
    command_queue: dict[str, object]
    safety_checklist: dict[str, object]
    blocked_actions: tuple[str, ...]
    safety_lines: tuple[str, ...]
    replay_commands: tuple[str, ...]


def _nonblank(value: str, *, field: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field} must not be blank")
    return normalized


def _sample_pad_states(*, tune_offset: int) -> tuple[PadState, ...]:
    return tuple(
        PadState(
            pad_id=pad,
            machine=(
                "BD Hard"
                if pad == 1
                else (
                    "XT Classic"
                    if 6 <= pad <= 8
                    else (
                        "SY Raw"
                        if pad == 11
                        else "FX / utility" if pad == 12 else "Performance Pad"
                    )
                )
            ),
            params={
                "TUN": 64 + tune_offset,
                "DEC": 70,
                "LEV": 110,
            },
        )
        for pad in range(1, 13)
    )


def _console_history() -> History:
    snapshots = (
        Snapshot(
            snapshot_id="console-snap-01",
            device="analog_rytm_mk2",
            captured_at=_FIXED_CAPTURED_AT,
            pads=_sample_pad_states(tune_offset=0),
            scene_slot="A01",
            bpm=128.0,
        ),
        Snapshot(
            snapshot_id="console-snap-02",
            device="analog_rytm_mk2",
            captured_at=_FIXED_CAPTURED_AT,
            pads=_sample_pad_states(tune_offset=1),
            scene_slot="A01",
            bpm=128.0,
        ),
        Snapshot(
            snapshot_id="console-snap-03",
            device="analog_rytm_mk2",
            captured_at=_FIXED_CAPTURED_AT,
            pads=_sample_pad_states(tune_offset=2),
            scene_slot="A01",
            bpm=128.0,
        ),
    )
    return History(
        entries=(
            HistoryEntry(
                snapshot=snapshots[0],
                kind="auto",
                parent_id=None,
                via=None,
                label="Captured kit anchor",
            ),
            HistoryEntry(
                snapshot=snapshots[1],
                kind="auto",
                parent_id="console-snap-01",
                via="regen",
                label="Dark Hypnotic preview",
            ),
            HistoryEntry(
                snapshot=snapshots[2],
                kind="saved",
                parent_id="console-snap-02",
                via="send",
                label="Warehouse arc take",
            ),
        ),
        current_id="console-snap-03",
    )


def _unique_tuple(*groups: tuple[str, ...]) -> tuple[str, ...]:
    seen: set[str] = set()
    values: list[str] = []
    for group in groups:
        for value in group:
            if value not in seen:
                seen.add(value)
                values.append(value)
    return tuple(values)


def _tuple_from_payload(payload: dict[str, object], key: str) -> tuple[str, ...]:
    values = payload.get(key, ())
    if not isinstance(values, (list, tuple)):
        return ()
    return tuple(str(value) for value in values)


def _flow_lookup(catalog: OxiLiveMacroCatalogReport) -> dict[str, tuple[str, str]]:
    return {
        step.name: (step.send_policy, step.recovery_action)
        for step in catalog.performance_flow
        if step.name != "capture-anchor"
    }


def _macro_action_status(*, risk_label: str, macro_key: str) -> str:
    if macro_key == "home":
        return "recovery"
    if risk_label == "edge":
        return "review"
    return "staged"


def _macro_operator_hint(*, macro_key: str, recovery_action: str) -> str:
    if macro_key == "home":
        return "Type home in the armed shell, inspect changes, then send to restore the anchor."
    return (
        f"Type {macro_key} in the armed shell, inspect changes, send manually, "
        f"and recover with {recovery_action}."
    )


def _payload_list(payload: dict[str, object], key: str) -> list[object]:
    values = payload.get(key, ())
    if not isinstance(values, list):
        return []
    return values


def _payload_string(payload: dict[str, object], key: str) -> str:
    value = payload.get(key, "")
    if not isinstance(value, str):
        return ""
    return value


def _payload_dict(payload: dict[str, object], key: str) -> dict[str, object]:
    value = payload.get(key, {})
    if not isinstance(value, dict):
        return {}
    return value


def _payload_int(payload: dict[str, object], key: str) -> int:
    value = payload.get(key, 0)
    if not isinstance(value, int):
        return 0
    return value


def _first_payload_dict(values: list[object]) -> dict[str, object]:
    if not values:
        return {}
    first_value = values[0]
    if not isinstance(first_value, dict):
        return {}
    return first_value


def _a4_readiness_replay_command(
    *,
    macro_name: str,
    seed: int,
    intensity: int,
) -> str:
    return (
        "python -m rytm_randomizer.cli analog-four-oxi-macro-readiness-report "
        f"{macro_name} --seed {seed} --intensity {intensity} "
        f"--limit {A4_REVIEW_EVENT_LIMIT} --json"
    )


def _build_rehearsal_board() -> dict[str, object]:
    strategy = build_oxi_live_set_strategy_payload()
    rehearsal = build_rytm_live_macro_hardware_rehearsal_payload()
    return {
        "board_version": REHEARSAL_BOARD_VERSION,
        "board_id": REHEARSAL_BOARD_ID,
        "board_status": REHEARSAL_BOARD_STATUS,
        "title": "OXI Live Rehearsal Board",
        "launch_command": _payload_string(rehearsal, "launch_command"),
        "studio_workflow": _payload_list(rehearsal, "studio_workflow"),
        "chapters": _payload_list(strategy, "chapters"),
        "operator_cues": _payload_list(strategy, "operator_cues"),
        "pad_lane_checks": _payload_list(rehearsal, "pad_lane_checks"),
        "macro_checkpoints": _payload_list(rehearsal, "macros"),
        "hardware_validation_runway": _payload_list(strategy, "hardware_validation_runway"),
        "promotion_criteria": _payload_list(strategy, "promotion_criteria"),
        "recovery_checks": _payload_list(rehearsal, "recovery_checks"),
        "next_hardware_validations": _payload_list(strategy, "next_hardware_validations"),
        "replay_commands": _payload_list(strategy, "replay_commands"),
        "blocked_actions": list(REHEARSAL_BOARD_BLOCKED_ACTIONS),
        "safety_lines": list(REHEARSAL_BOARD_SAFETY_LINES),
    }


def _controller_template_page_cards(
    template_rows: list[object],
) -> list[dict[str, object]]:
    cards_by_key: dict[str, dict[str, object]] = {}
    slots_by_key: dict[str, list[int]] = {}
    for row_value in template_rows:
        if not isinstance(row_value, dict):
            continue

        page_key = _payload_string(row_value, "page_key")
        if not page_key:
            continue

        page_label = _payload_string(row_value, "page_label")
        page_index = _payload_int(row_value, "page_index")
        slot = _payload_int(row_value, "slot")
        if page_key not in cards_by_key:
            cards_by_key[page_key] = {
                "page_key": page_key,
                "page_label": page_label,
                "page_index": page_index,
                "row_count": 0,
                "first_slot": slot,
                "last_slot": slot,
            }
            slots_by_key[page_key] = []

        card = cards_by_key[page_key]
        row_count = card.get("row_count", 0)
        card["row_count"] = row_count + 1 if isinstance(row_count, int) else 1
        slots_by_key[page_key].append(slot)

    for page_key, slots in slots_by_key.items():
        card = cards_by_key[page_key]
        card["first_slot"] = min(slots)
        card["last_slot"] = max(slots)

    return sorted(
        cards_by_key.values(),
        key=lambda card: card["page_index"] if isinstance(card["page_index"], int) else 0,
    )


def _build_controller_brain_panel() -> dict[str, object]:
    payload = build_controller_brain_rehearsal_payload()
    source = _payload_dict(payload, "controller_brain_rehearsal")
    template_rows = _payload_list(source, "template_rows")
    gesture_outcomes = _payload_list(source, "gesture_outcomes")
    template_page_cards = _controller_template_page_cards(template_rows)
    return {
        "panel_version": CONTROLLER_BRAIN_PANEL_VERSION,
        "panel_id": CONTROLLER_BRAIN_PANEL_ID,
        "panel_status": _payload_string(source, "rehearsal_status"),
        "source_report": "controller-brain-rehearsal-report",
        "title": _payload_string(source, "title"),
        "profile_key": _payload_string(source, "profile_key"),
        "profile_label": _payload_string(source, "profile_label"),
        "controller_family": _payload_string(source, "controller_family"),
        "controller_layout": _payload_string(source, "controller_layout"),
        "scenario_key": _payload_string(source, "scenario_key"),
        "scenario_label": _payload_string(source, "scenario_label"),
        "scenario_summary": _payload_string(source, "scenario_summary"),
        "template_row_count": _payload_int(source, "template_row_count"),
        "template_rows": template_rows,
        "template_page_count": len(template_page_cards),
        "template_page_cards": template_page_cards,
        "gesture_count": len(gesture_outcomes),
        "gesture_outcomes": gesture_outcomes,
        "operator_notes": _payload_list(source, "operator_notes"),
        "blocked_actions": list(_tuple_from_payload(source, "blocked_active_actions")),
        "safety_lines": list(_tuple_from_payload(payload, "safety")),
        "replay_commands": _payload_list(source, "replay_commands"),
    }


def _build_live_kit_capture_panel(
    rehearsal_board: dict[str, object],
) -> dict[str, object]:
    launch_command = _payload_string(rehearsal_board, "launch_command")
    return {
        "panel_version": LIVE_KIT_CAPTURE_PANEL_VERSION,
        "panel_id": LIVE_KIT_CAPTURE_PANEL_ID,
        "panel_status": LIVE_KIT_CAPTURE_PANEL_STATUS,
        "title": "Live Kit Capture",
        "tagline": "Mutate the kit you are actually playing.",
        "source_report": "rytm-live-macro-hardware-rehearsal-report",
        "launch_command": launch_command,
        "workflow_steps": [
            {
                "step_key": "receive-kit-sysex",
                "label": "Receive Kit SysEx",
                "operator_command": "kit",
                "description": "Capture the currently loaded Analog Rytm kit before changing it.",
                "cockpit_state": "anchor captured from hardware",
                "safety_note": "Operator sends KIT SysEx in the armed shell; Cockpit stays passive.",
            },
            {
                "step_key": "review-captured-kit",
                "label": "Review Captured Kit",
                "operator_command": "changes",
                "description": "Inspect pad engines, pad locks, lane policy, and staged deltas.",
                "cockpit_state": "engine-aware review",
                "safety_note": "Review is local metadata until the armed shell sends.",
            },
            {
                "step_key": "mutate-captured-kit",
                "label": "Randomize Captured Kit",
                "operator_command": "randomize",
                "description": "Stage a musical mutation from the exact captured kit values.",
                "cockpit_state": "captured-kit mutation staged",
                "safety_note": "Mutation is planned from the anchor; no unattended hardware action.",
            },
            {
                "step_key": "go-send-next-variation",
                "label": "Go / Send Next Variation",
                "operator_command": "go",
                "description": "Generate and send the next operator-approved variation in the armed shell.",
                "cockpit_state": "manual fire path",
                "safety_note": "Only the explicitly armed shell is allowed to send MIDI.",
            },
            {
                "step_key": "recover-captured-anchor",
                "label": "Recover Captured Anchor",
                "operator_command": "Z then send",
                "description": "Return the Rytm to the captured safe kit state.",
                "cockpit_state": "captured-anchor recovery",
                "safety_note": "Recovery is visible before performance pressure starts.",
            },
            {
                "step_key": "resnapshot-new-anchor",
                "label": "Resnapshot New Anchor",
                "operator_command": "resnapshot",
                "description": "Promote a newly loaded or saved Rytm kit as the next mutation anchor.",
                "cockpit_state": "new live anchor ready",
                "safety_note": "The operator chooses when the anchor changes.",
            },
        ],
        "differentiators": [
            {
                "name": "live-kit-capture",
                "label": "Live kit capture",
                "summary": "Works from the kit loaded on the Rytm right now.",
                "controller_limit": "Fixed controller pages do not know the current kit.",
                "why_it_matters": "No need to rebuild the set around a prepared template.",
            },
            {
                "name": "engine-aware-current-kit-mutation",
                "label": "Engine-aware current-kit mutation",
                "summary": "Uses captured pad machines and values before proposing movement.",
                "controller_limit": "Raw CC mapping cannot tell if a knob is musical for this engine.",
                "why_it_matters": "The randomizer can respect live pad roles and guardrails.",
            },
            {
                "name": "captured-anchor-recovery",
                "label": "Captured-anchor recovery",
                "summary": "Keeps `home`/`send` and `Z`/`send` tied to the live captured kit.",
                "controller_limit": "Controller snapshots usually restore controller values only.",
                "why_it_matters": "The performer has a trusted escape hatch during a set.",
            },
            {
                "name": "twelve-pad-rytm-context",
                "label": "12-pad Rytm context",
                "summary": "Surfaces all 12 pads, pad policies, and supported expansion lanes.",
                "controller_limit": "A generic controller page does not model Rytm pad roles.",
                "why_it_matters": "Pad 12 remains product-supported while Jose-critical pads stay clear.",
            },
            {
                "name": "controller-complement",
                "label": "Controller complement",
                "summary": "Controller gestures can drive intent after kit capture defines the truth.",
                "controller_limit": "The controller is only the hand surface, not the kit brain.",
                "why_it_matters": "OXI/E16-style controls become safer because the app knows the anchor.",
            },
        ],
        "recovery_commands": ["home then send", "Z then send", "stop sending and reload saved kit"],
        "blocked_actions": list(LIVE_KIT_CAPTURE_BLOCKED_ACTIONS),
        "safety_lines": list(LIVE_KIT_CAPTURE_SAFETY_LINES),
        "replay_commands": [
            "python -m rytm_randomizer.cli rytm-live-macro-hardware-rehearsal-report --json",
            launch_command,
        ],
    }


def _build_analog_four_review_surface() -> dict[str, object]:
    set_plan = build_analog_four_oxi_macro_set_planner_report()
    set_payload = build_analog_four_oxi_macro_set_planner_payload(set_plan)
    up_next = _payload_list(set_payload, "up_next")
    current_step = _payload_dict(set_payload, "current_step")
    review_step = _first_payload_dict(up_next) or current_step
    macro_name = _payload_string(review_step, "macro_name")
    seed = _payload_int(review_step, "seed")
    intensity = _payload_int(review_step, "intensity")
    readiness = build_analog_four_oxi_macro_readiness_report(
        macro_name,
        seed=seed,
        intensity=intensity,
    )
    readiness_payload = build_analog_four_oxi_macro_readiness_payload(
        readiness,
        event_limit=A4_REVIEW_EVENT_LIMIT,
    )
    return {
        "surface_version": A4_REVIEW_SURFACE_VERSION,
        "surface_id": A4_REVIEW_SURFACE_ID,
        "surface_status": A4_REVIEW_SURFACE_STATUS,
        "title": "Analog Four Review Surface",
        "set_name": _payload_string(set_payload, "set_name"),
        "step_count": _payload_int(set_payload, "step_count"),
        "current_step": current_step,
        "up_next": up_next,
        "steps": _payload_list(set_payload, "steps"),
        "review_focus": {
            "macro_name": macro_name,
            "macro_label": _payload_string(review_step, "macro_label"),
            "seed": seed,
            "intensity": intensity,
            "energy": _payload_int(review_step, "energy"),
            "readiness": _payload_string(readiness_payload, "readiness"),
            "event_count": _payload_int(readiness_payload, "event_count"),
            "ready_count": _payload_int(readiness_payload, "ready_count"),
            "review_count": _payload_int(readiness_payload, "review_count"),
            "blocked_count": _payload_int(readiness_payload, "blocked_count"),
            "shown_count": _payload_int(readiness_payload, "shown_count"),
        },
        "readiness_events": _payload_list(readiness_payload, "events"),
        "preflight_command": _payload_string(readiness_payload, "preflight_command"),
        "validation_steps": _payload_list(readiness_payload, "validation_steps"),
        "recovery_notes": _payload_list(readiness_payload, "recovery_notes"),
        "promotion_gates": _payload_list(readiness_payload, "promotion_gates"),
        "replay_command": _payload_string(set_payload, "replay_command"),
        "readiness_replay_command": _a4_readiness_replay_command(
            macro_name=macro_name,
            seed=seed,
            intensity=intensity,
        ),
        "opens_ports": False,
        "sends_midi": False,
        "hardware_required": False,
        "blocked_actions": list(
            _unique_tuple(
                A4_REVIEW_BLOCKED_ACTIONS,
                _tuple_from_payload(set_payload, "blocked_active_actions"),
            )
        ),
        "safety_lines": list(
            _unique_tuple(
                A4_REVIEW_SAFETY_LINES,
                _tuple_from_payload(set_payload, "safety"),
                _tuple_from_payload(readiness_payload, "safety"),
            )
        ),
    }


def _build_macro_action_deck(
    *,
    current_macro_key: str,
    catalog: OxiLiveMacroCatalogReport | None = None,
) -> dict[str, object]:
    source = build_oxi_live_macro_catalog_report() if catalog is None else catalog
    flow_by_name = _flow_lookup(source)
    cards: list[dict[str, object]] = []
    for order, macro in enumerate(source.rytm_macros, start=1):
        send_policy, recovery_action = flow_by_name.get(
            macro.name,
            ("stage-review-send", macro.recovery_action),
        )
        cards.append(
            {
                "macro_key": macro.name,
                "order": order,
                "label": macro.label,
                "shell_command": macro.name,
                "send_policy": send_policy,
                "recovery_action": recovery_action,
                "risk_label": macro.risk_label,
                "affected_pads": list(macro.affected_pads),
                "pad_count": len(macro.affected_pads),
                "status": _macro_action_status(
                    risk_label=macro.risk_label,
                    macro_key=macro.name,
                ),
                "hardware_action_state": MACRO_ACTION_HARDWARE_STATE,
                "hardware_send_enabled": False,
                "dry_run_only": True,
                "operator_hint": _macro_operator_hint(
                    macro_key=macro.name,
                    recovery_action=recovery_action,
                ),
                "test_id": f"macro-action-{macro.name}",
            }
        )
    return {
        "deck_version": MACRO_ACTION_DECK_VERSION,
        "deck_id": MACRO_ACTION_DECK_ID,
        "deck_status": MACRO_ACTION_DECK_STATUS,
        "current_macro_key": current_macro_key,
        "cards": cards,
        "blocked_actions": list(MACRO_ACTION_BLOCKED_ACTIONS),
        "safety_lines": list(MACRO_ACTION_SAFETY_LINES),
        "replay_commands": list(MACRO_ACTION_REPLAY_COMMANDS),
    }


def _operator_family_name(family: str) -> str:
    return "overdrive" if family == "drive" else family


def _operator_family_allowlists(
    allowlists: Mapping[str, object],
) -> dict[str, list[str]]:
    operator_allowlists: dict[str, list[str]] = {}
    for section, families in allowlists.items():
        operator_families = cast(list[object], families)
        operator_allowlists[section] = sorted(
            _operator_family_name(str(family)) for family in operator_families
        )
    return operator_allowlists


def _operator_pad_policy_cards(
    pad_policies: Mapping[int, dict[str, object]],
) -> dict[str, dict[str, object]]:
    cards: dict[str, dict[str, object]] = {}
    for pad, policy in pad_policies.items():
        section_family_allowlists = cast(
            Mapping[str, object],
            policy["section_family_allowlists"],
        )
        cards[str(pad)] = {
            "amount": policy["amount"],
            "density": policy["density"],
            "bias": policy["bias"],
            "lane_policies": policy["lane_policies"],
            "section_family_allowlists": _operator_family_allowlists(section_family_allowlists),
        }
    return cards


def _lane_policy_summary(lane_policies: Mapping[str, str]) -> str:
    return ", ".join(f"{key}={lane_policies[key]}" for key in sorted(lane_policies)) or "none"


def _build_rytm_lane_policy_matrix(
    *,
    catalog: OxiLiveMacroCatalogReport,
) -> dict[str, object]:
    macro_rows: list[dict[str, object]] = []
    for order, macro in enumerate(catalog.rytm_macros, start=1):
        macro_rows.append(
            {
                "macro_key": macro.name,
                "order": order,
                "label": macro.label,
                "style_crate": macro.style_crate,
                "risk_label": macro.risk_label,
                "energy": macro.energy,
                "risk": macro.risk,
                "affected_pads": list(macro.affected_pads),
                "locked_pads": list(macro.locked_pads),
                "lane_policy_summary": _lane_policy_summary(macro.lane_policies),
                "pad_policy_cards": _operator_pad_policy_cards(macro.pad_policies),
                "recovery_action": macro.recovery_action,
                "summary": macro.summary,
            }
        )
    return {
        "matrix_version": RYTM_LANE_POLICY_MATRIX_VERSION,
        "matrix_id": RYTM_LANE_POLICY_MATRIX_ID,
        "matrix_status": RYTM_LANE_POLICY_MATRIX_STATUS,
        "source_report": "oxi-live-macro-catalog-report",
        "macro_count": len(macro_rows),
        "pad_groups": list(_RYTM_LANE_POLICY_PAD_GROUPS),
        "macro_rows": macro_rows,
        "blocked_actions": list(RYTM_LANE_POLICY_BLOCKED_ACTIONS),
        "safety_lines": list(RYTM_LANE_POLICY_SAFETY_LINES),
        "replay_commands": list(RYTM_LANE_POLICY_REPLAY_COMMANDS),
    }


def _console_id(
    *,
    session_label: str,
    device_inventory: dict[str, object],
    rytm_pad_surface: dict[str, object],
    rytm_lane_policy_matrix: dict[str, object],
    performance_flow: dict[str, object],
    macro_action_deck: dict[str, object],
    rehearsal_board: dict[str, object],
    controller_brain_panel: dict[str, object],
    live_kit_capture_panel: dict[str, object],
    live_kit_capture_workbench: dict[str, object],
    live_kit_package_audition: dict[str, object],
    analog_four_review_surface: dict[str, object],
    style_queue: dict[str, object],
    analyzer_panel: dict[str, object],
    snapshot_history: dict[str, object],
    command_queue: dict[str, object],
    safety_checklist: dict[str, object],
) -> str:
    payload = "|".join(
        (
            CONSOLE_VERSION,
            session_label,
            str(device_inventory.get("device_count", "")),
            str(rytm_pad_surface.get("pad_count", "")),
            str(rytm_lane_policy_matrix.get("matrix_id", "")),
            str(performance_flow.get("flow_id", "")),
            str(macro_action_deck.get("deck_id", "")),
            str(rehearsal_board.get("board_id", "")),
            str(controller_brain_panel.get("panel_id", "")),
            str(live_kit_capture_panel.get("panel_id", "")),
            str(live_kit_capture_workbench.get("workbench_id", "")),
            str(live_kit_package_audition.get("audition_id", "")),
            str(analog_four_review_surface.get("surface_id", "")),
            str(style_queue.get("deck_id", "")),
            str(analyzer_panel.get("panel_id", "")),
            str(snapshot_history.get("snapshot_history_id", "")),
            str(command_queue.get("command_queue_id", "")),
            str(safety_checklist.get("safety_checklist_id", "")),
        )
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def build_live_gui_performance_console_model(
    *,
    session_label: str = "Live Session",
) -> LiveGuiPerformanceConsoleModel:
    """Build a deterministic passive model for the full Cockpit performance console."""

    normalized_session_label = _nonblank(session_label, field="session_label")
    history = _console_history()
    device_inventory = live_gui_device_inventory_model_payload(
        build_live_gui_device_inventory_model()
    )
    rytm_pad_surface = live_gui_12_pad_surface_model_payload(build_live_gui_12_pad_surface_model())
    performance_flow = live_gui_performance_flow_model_payload(
        build_live_gui_performance_flow_model()
    )["live_gui_performance_flow_model"]
    macro_catalog = build_oxi_live_macro_catalog_report()
    macro_action_deck = _build_macro_action_deck(
        current_macro_key=str(performance_flow["current_step_key"]),
        catalog=macro_catalog,
    )
    rytm_lane_policy_matrix = _build_rytm_lane_policy_matrix(catalog=macro_catalog)
    rehearsal_board = _build_rehearsal_board()
    controller_brain_panel = _build_controller_brain_panel()
    live_kit_capture_panel = _build_live_kit_capture_panel(rehearsal_board)
    live_kit_capture_workbench = build_live_kit_capture_workbench(live_kit_capture_panel)
    live_kit_package_audition = build_live_kit_package_audition(live_kit_capture_workbench)
    analog_four_review_surface = _build_analog_four_review_surface()
    style_queue = to_style_crate_rehearsal_deck_json(build_style_crate_rehearsal_deck())[
        "style_crate_rehearsal_deck"
    ]
    analyzer_panel = to_live_gui_analyzer_panel_model_json(build_live_gui_analyzer_panel_model())[
        "live_gui_analyzer_panel"
    ]
    snapshot_history = to_live_gui_snapshot_history_model_json(
        build_live_gui_snapshot_history_model(
            history,
            session_label=normalized_session_label,
        )
    )["live_gui_snapshot_history_model"]
    command_queue = to_live_gui_command_queue_model_json(
        build_live_gui_command_queue_model(
            session_label=normalized_session_label,
            history=history,
        )
    )["live_gui_command_queue_model"]
    safety_checklist = to_live_gui_safety_checklist_model_json(
        build_live_gui_safety_checklist_model(session_label=normalized_session_label)
    )["live_gui_safety_checklist_model"]

    blocked_actions = _unique_tuple(
        tuple(performance_flow["blocked_actions"]),
        _tuple_from_payload(macro_action_deck, "blocked_actions"),
        _tuple_from_payload(rytm_lane_policy_matrix, "blocked_actions"),
        _tuple_from_payload(rehearsal_board, "blocked_actions"),
        _tuple_from_payload(controller_brain_panel, "blocked_actions"),
        _tuple_from_payload(live_kit_capture_panel, "blocked_actions"),
        _tuple_from_payload(live_kit_capture_workbench, "blocked_actions"),
        _tuple_from_payload(live_kit_package_audition, "blocked_actions"),
        _tuple_from_payload(analog_four_review_surface, "blocked_actions"),
        tuple(style_queue["blocked_actions"]),
        tuple(analyzer_panel["blocked_actions"]),
        tuple(snapshot_history["blocked_actions"]),
        tuple(command_queue["blocked_actions"]),
        tuple(safety_checklist["blocked_actions"]),
        _tuple_from_payload(device_inventory, "blocked_actions"),
        _tuple_from_payload(rytm_pad_surface, "blocked_actions"),
    )
    safety_lines = _unique_tuple(
        BASE_SAFETY_LINES,
        tuple(performance_flow["safety_lines"]),
        _tuple_from_payload(macro_action_deck, "safety_lines"),
        _tuple_from_payload(rytm_lane_policy_matrix, "safety_lines"),
        _tuple_from_payload(rehearsal_board, "safety_lines"),
        _tuple_from_payload(controller_brain_panel, "safety_lines"),
        _tuple_from_payload(live_kit_capture_panel, "safety_lines"),
        _tuple_from_payload(live_kit_capture_workbench, "safety_lines"),
        _tuple_from_payload(live_kit_package_audition, "safety_lines"),
        _tuple_from_payload(analog_four_review_surface, "safety_lines"),
        _tuple_from_payload(device_inventory, "safety"),
        _tuple_from_payload(rytm_pad_surface, "safety"),
    )

    return LiveGuiPerformanceConsoleModel(
        console_version=CONSOLE_VERSION,
        source_module=SOURCE_MODULE,
        console_id=_console_id(
            session_label=normalized_session_label,
            device_inventory=device_inventory,
            rytm_pad_surface=rytm_pad_surface,
            rytm_lane_policy_matrix=rytm_lane_policy_matrix,
            performance_flow=performance_flow,
            macro_action_deck=macro_action_deck,
            rehearsal_board=rehearsal_board,
            controller_brain_panel=controller_brain_panel,
            live_kit_capture_panel=live_kit_capture_panel,
            live_kit_capture_workbench=live_kit_capture_workbench,
            live_kit_package_audition=live_kit_package_audition,
            analog_four_review_surface=analog_four_review_surface,
            style_queue=style_queue,
            analyzer_panel=analyzer_panel,
            snapshot_history=snapshot_history,
            command_queue=command_queue,
            safety_checklist=safety_checklist,
        ),
        session_label=normalized_session_label,
        console_status=CONSOLE_STATUS,
        hardware_mode=HARDWARE_MODE,
        device_inventory=device_inventory,
        rytm_pad_surface=rytm_pad_surface,
        rytm_lane_policy_matrix=rytm_lane_policy_matrix,
        performance_flow=performance_flow,
        macro_action_deck=macro_action_deck,
        rehearsal_board=rehearsal_board,
        controller_brain_panel=controller_brain_panel,
        live_kit_capture_panel=live_kit_capture_panel,
        live_kit_capture_workbench=live_kit_capture_workbench,
        live_kit_package_audition=live_kit_package_audition,
        analog_four_review_surface=analog_four_review_surface,
        style_queue=style_queue,
        analyzer_panel=analyzer_panel,
        snapshot_history=snapshot_history,
        command_queue=command_queue,
        safety_checklist=safety_checklist,
        blocked_actions=blocked_actions,
        safety_lines=safety_lines,
        replay_commands=REPLAY_COMMANDS,
    )


def live_gui_performance_console_model_payload(
    model: LiveGuiPerformanceConsoleModel | None = None,
) -> dict[str, object]:
    """Return deterministic JSON-ready console metadata."""

    source = build_live_gui_performance_console_model() if model is None else model
    return {
        "live_gui_performance_console": {
            "console_version": source.console_version,
            "source_module": source.source_module,
            "console_id": source.console_id,
            "session_label": source.session_label,
            "console_status": source.console_status,
            "hardware_mode": source.hardware_mode,
            "device_inventory": source.device_inventory,
            "rytm_pad_surface": source.rytm_pad_surface,
            "rytm_lane_policy_matrix": source.rytm_lane_policy_matrix,
            "performance_flow": source.performance_flow,
            "macro_action_deck": source.macro_action_deck,
            "rehearsal_board": source.rehearsal_board,
            "controller_brain_panel": source.controller_brain_panel,
            "live_kit_capture_panel": source.live_kit_capture_panel,
            "live_kit_capture_workbench": source.live_kit_capture_workbench,
            "live_kit_package_audition": source.live_kit_package_audition,
            "analog_four_review_surface": source.analog_four_review_surface,
            "style_queue": source.style_queue,
            "analyzer_panel": source.analyzer_panel,
            "snapshot_history": source.snapshot_history,
            "command_queue": source.command_queue,
            "safety_checklist": source.safety_checklist,
            "blocked_actions": list(source.blocked_actions),
            "safety_lines": list(source.safety_lines),
            "replay_commands": list(source.replay_commands),
        },
        "safety": list(source.safety_lines),
    }


def _device_lines(model: LiveGuiPerformanceConsoleModel) -> list[str]:
    lines = ["Device rail:"]
    for card in model.device_inventory["cards"]:
        lines.append(
            f"- {card['device_id']} / {card['display_name']} / {card['track_count']} tracks"
        )
    return lines


def _rehearsal_board_lines(model: LiveGuiPerformanceConsoleModel) -> list[str]:
    board = model.rehearsal_board
    lines = [
        "Rehearsal board:",
        f"- status: {board['board_status']}",
        f"- chapters: {len(board['chapters'])}",
        f"- next hardware validations: {len(board['next_hardware_validations'])}",
        f"- launch: {board['launch_command']}",
    ]
    for lane in board["pad_lane_checks"]:
        lines.append(f"- pad lane: {lane['summary']}")
    for step in board["hardware_validation_runway"]:
        lines.append(
            f"- hardware validation: {step['name']} / "
            f"{step['device']} / {step['validation_mode']}"
        )
    return lines


def _controller_brain_panel_lines(model: LiveGuiPerformanceConsoleModel) -> list[str]:
    panel = model.controller_brain_panel
    lines = [
        "Controller brain panel:",
        f"- status: {panel['panel_status']}",
        f"- profile: {panel['profile_key']}",
        f"- scenario: {panel['scenario_key']}",
        f"- controller template rows: {panel['template_row_count']}",
        f"- controller pages: {panel['template_page_count']}",
        f"- controller gestures: {panel['gesture_count']}",
    ]
    for page_card in panel["template_page_cards"]:
        lines.append(
            f"- controller page: {page_card['page_key']} / "
            f"{page_card['row_count']} rows / slots "
            f"{page_card['first_slot']}-{page_card['last_slot']}"
        )
    for outcome in panel["gesture_outcomes"]:
        lines.append(
            f"- controller gesture: {outcome['assignment_key']} -> "
            f"{outcome['resolved_intent_key']}"
        )
    return lines


def _live_kit_capture_panel_lines(model: LiveGuiPerformanceConsoleModel) -> list[str]:
    panel = model.live_kit_capture_panel
    lines = [
        "Live kit capture:",
        f"- status: {panel['panel_status']}",
        f"- tagline: {panel['tagline']}",
        f"- launch: {panel['launch_command']}",
    ]
    for step in panel["workflow_steps"]:
        lines.append(f"- capture step: {step['step_key']} / {step['operator_command']}")
    for differentiator in panel["differentiators"]:
        lines.append(f"- differentiator: {differentiator['name']}")
    lines.extend(f"- recovery: {command}" for command in panel["recovery_commands"])
    return lines


def _analog_four_review_surface_lines(model: LiveGuiPerformanceConsoleModel) -> list[str]:
    surface = model.analog_four_review_surface
    review_focus = cast(dict[str, object], surface["review_focus"])
    lines = [
        "A4 review surface:",
        f"- status: {surface['surface_status']}",
        f"- set: {surface['set_name']}",
        f"- steps: {surface['step_count']}",
        (f"- review focus: {review_focus['macro_name']} / " f"{review_focus['readiness']}"),
        f"- shown readiness events: {review_focus['shown_count']}",
        f"- validation preflight: {surface['preflight_command']}",
        f"- readiness replay: {surface['readiness_replay_command']}",
    ]
    for step in surface["steps"]:
        lines.append(
            f"- A4 step: {step['order']} / {step['macro_name']} / "
            f"{step['readiness']} / events={step['event_count']}"
        )
    lines.extend(f"- blocked: {action}" for action in surface["blocked_actions"])
    lines.extend(f"- safety: {line}" for line in surface["safety_lines"])
    return lines


def _rytm_lane_policy_matrix_lines(model: LiveGuiPerformanceConsoleModel) -> list[str]:
    matrix = model.rytm_lane_policy_matrix
    lines = [
        "Rytm lane policy matrix:",
        f"- status: {matrix['matrix_status']}",
        f"- macros: {matrix['macro_count']}",
        f"- source: {matrix['source_report']}",
    ]
    for group in matrix["pad_groups"]:
        lines.append(
            f"- pad group: {group['group_key']} / pads "
            f"{', '.join(str(pad) for pad in group['pads'])}"
        )
    for row in matrix["macro_rows"]:
        lines.append(
            f"- macro policy: {row['macro_key']} / pads "
            f"{', '.join(str(pad) for pad in row['affected_pads'])}"
        )
    return lines


def _format_console_body(model: LiveGuiPerformanceConsoleModel) -> list[str]:
    current_flow_key = model.performance_flow["current_step_key"]
    a4_set_plan = model.performance_flow["analog_four_set_plan"]
    lines = [
        "Console summary:",
        f"- console id: {model.console_id}",
        f"- session: {model.session_label}",
        f"- status: {model.console_status}",
        f"- hardware mode: {model.hardware_mode}",
        *_device_lines(model),
        "Rytm pad surface:",
        f"- pads: {model.rytm_pad_surface['pad_count']}",
        f"- active V1.34 pads: {model.rytm_pad_surface['active_pad_count']}",
        f"- planned pads: {model.rytm_pad_surface['planned_pad_count']}",
        *_rytm_lane_policy_matrix_lines(model),
        "Performance flow:",
        f"- current: {current_flow_key}",
        f"- steps: {len(model.performance_flow['steps'])}",
        "Macro actions:",
        *[
            (
                f"- {card['macro_key']}: {card['shell_command']} / "
                f"{card['send_policy']} / {card['hardware_action_state']}"
            )
            for card in model.macro_action_deck["cards"]
        ],
        *_rehearsal_board_lines(model),
        *_controller_brain_panel_lines(model),
        *_live_kit_capture_panel_lines(model),
        *live_kit_capture_workbench_lines(model.live_kit_capture_workbench),
        *live_kit_package_audition_lines(model.live_kit_package_audition),
        *_analog_four_review_surface_lines(model),
        "A4 set plan:",
        f"- set: {a4_set_plan['set_name']}",
        f"- current macro: {a4_set_plan['current_macro']}",
        f"- up next: {', '.join(a4_set_plan['up_next_macros'])}",
        "Style queue and journal:",
        f"- crates: {len(model.style_queue['crate_cards'])}",
        f"- queued moves: {len(model.style_queue['queue_cards'])}",
        f"- journal entries: {len(model.style_queue['journal_cards'])}",
        "Analyzer panel:",
        f"- analyzer status: {model.analyzer_panel['panel_status']}",
        f"- analyzer mode: {model.analyzer_panel['panel_mode']}",
        f"- analyzer reference: {model.analyzer_panel['reference_label']}",
        (
            "- analyzer required actions: "
            f"{', '.join(model.analyzer_panel['required_actions']) or 'none'}"
        ),
        "Snapshot history:",
        f"- current: {model.snapshot_history['current_id']}",
        f"- entries: {model.snapshot_history['entry_count']}",
        "Command queue:",
        f"- status: {model.command_queue['queue_status']}",
        f"- queued commands: {len(model.command_queue['queued_commands'])}",
        "Safety checklist:",
        (
            f"- {model.safety_checklist['passed_count']} / "
            f"{model.safety_checklist['total_count']} passed"
        ),
        f"- arm gate: {model.safety_checklist['arm_gate']['state']}",
        "Blocked active actions:",
        *[f"- {action}" for action in model.blocked_actions],
        "Replay commands:",
        *[f"- {command}" for command in model.replay_commands],
        SAFETY_SECTION_HEADER,
        *[f"- {line}" for line in model.safety_lines],
    ]
    return lines


def format_live_gui_performance_console_model_report(
    model: LiveGuiPerformanceConsoleModel | None = None,
) -> list[str]:
    """Render the performance console packet as deterministic operator text."""

    source = build_live_gui_performance_console_model() if model is None else model
    return passive_report_lines(_HEADER, _format_console_body(source))


LIVE_GUI_PERFORMANCE_CONSOLE_CLI_COMMAND: Final[CliCommand] = make_passive_report_command(
    "live-gui-performance-console-report",
    "Print the passive Cockpit performance console model.",
    format_lines=format_live_gui_performance_console_model_report,
    build_payload=live_gui_performance_console_model_payload,
)

register(LIVE_GUI_PERFORMANCE_CONSOLE_CLI_COMMAND)


__all__ = [
    "BASE_SAFETY_LINES",
    "CONSOLE_STATUS",
    "CONSOLE_VERSION",
    "CONTROLLER_BRAIN_PANEL_ID",
    "CONTROLLER_BRAIN_PANEL_VERSION",
    "HARDWARE_MODE",
    "MACRO_ACTION_BLOCKED_ACTIONS",
    "MACRO_ACTION_DECK_STATUS",
    "MACRO_ACTION_DECK_VERSION",
    "MACRO_ACTION_HARDWARE_STATE",
    "MACRO_ACTION_REPLAY_COMMANDS",
    "MACRO_ACTION_SAFETY_LINES",
    "LIVE_GUI_PERFORMANCE_CONSOLE_CLI_COMMAND",
    "LiveGuiPerformanceConsoleModel",
    "LiveGuiPerformanceConsoleModelDict",
    "REPORT_TITLE",
    "REPLAY_COMMANDS",
    "REHEARSAL_BOARD_BLOCKED_ACTIONS",
    "REHEARSAL_BOARD_ID",
    "REHEARSAL_BOARD_SAFETY_LINES",
    "REHEARSAL_BOARD_STATUS",
    "REHEARSAL_BOARD_VERSION",
    "RYTM_LANE_POLICY_BLOCKED_ACTIONS",
    "RYTM_LANE_POLICY_MATRIX_ID",
    "RYTM_LANE_POLICY_MATRIX_STATUS",
    "RYTM_LANE_POLICY_MATRIX_VERSION",
    "RYTM_LANE_POLICY_REPLAY_COMMANDS",
    "RYTM_LANE_POLICY_SAFETY_LINES",
    "SOURCE_MODULE",
    "build_live_gui_performance_console_model",
    "format_live_gui_performance_console_model_report",
    "live_gui_performance_console_model_payload",
]
