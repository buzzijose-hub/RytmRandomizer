"""Passive Cockpit performance console packet for the future desktop UI."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Final, TypedDict

from ..cli_registry import CliCommand, make_passive_report_command, register
from ..cockpit.data import History, HistoryEntry, PadState, Snapshot
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
    performance_flow: dict[str, object]
    macro_action_deck: dict[str, object]
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
    performance_flow: dict[str, object]
    macro_action_deck: dict[str, object]
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
                "style_crate": macro.style_crate,
                "energy": macro.energy,
                "risk": macro.risk,
                "tags": list(macro.tags),
                "shell_command": macro.name,
                "send_policy": send_policy,
                "recovery_action": recovery_action,
                "risk_label": macro.risk_label,
                "affected_pads": list(macro.affected_pads),
                "locked_pads": list(macro.locked_pads),
                "lane_policies": dict(macro.lane_policies),
                "pad_policies": {str(pad): policy for pad, policy in macro.pad_policies.items()},
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


def _console_id(
    *,
    session_label: str,
    device_inventory: dict[str, object],
    rytm_pad_surface: dict[str, object],
    performance_flow: dict[str, object],
    macro_action_deck: dict[str, object],
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
            str(performance_flow.get("flow_id", "")),
            str(macro_action_deck.get("deck_id", "")),
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
    macro_action_deck = _build_macro_action_deck(
        current_macro_key=str(performance_flow["current_step_key"])
    )
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
            performance_flow=performance_flow,
            macro_action_deck=macro_action_deck,
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
        performance_flow=performance_flow,
        macro_action_deck=macro_action_deck,
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
            "performance_flow": source.performance_flow,
            "macro_action_deck": source.macro_action_deck,
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
    "SOURCE_MODULE",
    "build_live_gui_performance_console_model",
    "format_live_gui_performance_console_model_report",
    "live_gui_performance_console_model_payload",
]
