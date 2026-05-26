"""Passive live-GUI device inventory model from the registered Device catalog."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import Final, TypeAlias

from ..devices import Device, all_devices
from .formatter import SAFETY_SECTION_HEADER, PassiveReportHeader, passive_report_lines

REPORT_TITLE: Final[str] = "RytmRandomizer passive live GUI device inventory model"
SOURCE_MODULE: Final[str] = "reports.live_gui_device_inventory_model"
DEVICE_INVENTORY_MODEL_VERSION: Final[str] = "live_gui_device_inventory_v1"
SAFETY_LINES: Final[tuple[str, ...]] = (
    "passive/read-only",
    "in-memory only",
    "device registry metadata only",
    "no MIDI sending",
    "no port opening",
    "no command execution",
    "no hardware mutation",
)
BLOCKED_ACTIONS: Final[tuple[str, ...]] = (
    "open_midi_port",
    "arm_hardware",
    "send_midi",
    "write_sysex",
    "mutate_hardware",
)
CAPABILITY_BADGES: Final[tuple[str, ...]] = (
    "snapshot_decode",
    "mutation_plan",
    "mock_render",
    "guarded_send",
)
_DEVICE_ORDER_BY_ID: Final[Mapping[str, int]] = MappingProxyType(
    {
        "analog_rytm_mk2": 0,
        "analog_four_mk2": 1,
    }
)
_HEADER: Final[PassiveReportHeader] = PassiveReportHeader(
    title=REPORT_TITLE,
    source_module=SOURCE_MODULE,
)

DeviceInventoryScalar: TypeAlias = str | int | bool
DeviceInventoryCardPayload: TypeAlias = dict[
    str,
    DeviceInventoryScalar | tuple[str, ...],
]
DeviceInventoryPayload: TypeAlias = dict[
    str,
    DeviceInventoryScalar | tuple[str, ...] | tuple[DeviceInventoryCardPayload, ...],
]


@dataclass(frozen=True)
class LiveGuiDeviceInventoryCard:
    """GUI-ready passive state for one registered Elektron device."""

    device_id: str
    display_name: str
    order: int
    track_count: int
    default_midi_channel_label: str
    sysex_manufacturer_id_hex: str
    role_summary: str
    port_state: str
    hardware_state: str
    mock_state: str
    can_open_port: bool
    can_arm_hardware: bool
    capability_badges: tuple[str, ...]
    passive: bool


@dataclass(frozen=True)
class LiveGuiDeviceInventoryModel:
    """Passive device-inventory state for a future live GUI device rail."""

    model_version: str
    device_count: int
    cards_by_device_id: Mapping[str, LiveGuiDeviceInventoryCard]
    blocked_actions: tuple[str, ...]
    safety: tuple[str, ...]


def _live_gui_device_inventory_order(device_id: str) -> int:
    return _DEVICE_ORDER_BY_ID.get(device_id, len(_DEVICE_ORDER_BY_ID))


def _live_gui_device_inventory_role_summary(device: Device) -> str:
    if device.track_count == 12:
        return "12-pad drum and sample performance surface"
    if device.track_count == 4:
        return "4-track synth performance surface"
    return f"{device.track_count}-track Elektron performance surface"


def _manufacturer_id_hex(device: Device) -> str:
    return " ".join(f"{byte:02x}" for byte in device.sysex_manufacturer_id)


def _live_gui_device_inventory_card(device: Device) -> LiveGuiDeviceInventoryCard:
    return LiveGuiDeviceInventoryCard(
        device_id=device.device_id,
        display_name=device.display_name,
        order=_live_gui_device_inventory_order(device.device_id),
        track_count=device.track_count,
        default_midi_channel_label=str(device.default_midi_channel + 1),
        sysex_manufacturer_id_hex=_manufacturer_id_hex(device),
        role_summary=_live_gui_device_inventory_role_summary(device),
        port_state="not_open",
        hardware_state="locked",
        mock_state="mock_safe",
        can_open_port=False,
        can_arm_hardware=False,
        capability_badges=CAPABILITY_BADGES,
        passive=True,
    )


def build_live_gui_device_inventory_model() -> LiveGuiDeviceInventoryModel:
    """Return passive GUI device inventory from the registered Device catalog."""

    cards = tuple(
        _live_gui_device_inventory_card(device)
        for _device_id, device in sorted(
            all_devices().items(),
            key=lambda item: (_live_gui_device_inventory_order(item[0]), item[0]),
        )
    )
    cards_by_device_id = {card.device_id: card for card in cards}
    return LiveGuiDeviceInventoryModel(
        model_version=DEVICE_INVENTORY_MODEL_VERSION,
        device_count=len(cards),
        cards_by_device_id=MappingProxyType(cards_by_device_id),
        blocked_actions=BLOCKED_ACTIONS,
        safety=SAFETY_LINES,
    )


def _live_gui_device_inventory_card_payload(
    card: LiveGuiDeviceInventoryCard,
) -> DeviceInventoryCardPayload:
    return {
        "device_id": card.device_id,
        "display_name": card.display_name,
        "order": card.order,
        "track_count": card.track_count,
        "default_midi_channel_label": card.default_midi_channel_label,
        "sysex_manufacturer_id_hex": card.sysex_manufacturer_id_hex,
        "role_summary": card.role_summary,
        "port_state": card.port_state,
        "hardware_state": card.hardware_state,
        "mock_state": card.mock_state,
        "can_open_port": card.can_open_port,
        "can_arm_hardware": card.can_arm_hardware,
        "capability_badges": card.capability_badges,
        "passive": card.passive,
    }


def live_gui_device_inventory_model_payload(
    model: LiveGuiDeviceInventoryModel | None = None,
) -> DeviceInventoryPayload:
    """Return a deterministic JSON-shaped payload without hardware side effects."""

    source_model = build_live_gui_device_inventory_model() if model is None else model
    cards = tuple(
        _live_gui_device_inventory_card_payload(source_model.cards_by_device_id[device_id])
        for device_id in source_model.cards_by_device_id
    )
    return {
        "model_version": source_model.model_version,
        "device_count": source_model.device_count,
        "cards": cards,
        "blocked_actions": source_model.blocked_actions,
        "safety": source_model.safety,
    }


def _live_gui_device_inventory_body_lines(
    model: LiveGuiDeviceInventoryModel,
) -> list[str]:
    lines = [
        "Summary:",
        f"- Model version: {model.model_version}",
        f"- Devices: {model.device_count}",
        "Devices:",
    ]

    for device_id in model.cards_by_device_id:
        card = model.cards_by_device_id[device_id]
        lines.extend(
            [
                f"Device {card.device_id} / {card.display_name}:",
                f"  Tracks: {card.track_count}",
                f"  Role: {card.role_summary}",
                f"  Default MIDI channel: {card.default_midi_channel_label}",
                f"  Manufacturer ID: {card.sysex_manufacturer_id_hex}",
                f"  MIDI port: {card.port_state}",
                f"  Hardware: {card.hardware_state}",
                f"  Mock state: {card.mock_state}",
                f"  Capabilities: {', '.join(card.capability_badges)}",
            ]
        )

    lines.append("Blocked actions:")
    lines.extend(f"- {action}" for action in model.blocked_actions)
    lines.append(SAFETY_SECTION_HEADER)
    lines.extend(f"- {line}" for line in model.safety)
    return lines


def format_live_gui_device_inventory_model_report(
    model: LiveGuiDeviceInventoryModel | None = None,
) -> list[str]:
    """Return deterministic lines for the passive live-GUI device inventory."""

    source_model = build_live_gui_device_inventory_model() if model is None else model
    return passive_report_lines(_HEADER, _live_gui_device_inventory_body_lines(source_model))


__all__ = [
    "BLOCKED_ACTIONS",
    "CAPABILITY_BADGES",
    "DEVICE_INVENTORY_MODEL_VERSION",
    "LiveGuiDeviceInventoryCard",
    "LiveGuiDeviceInventoryModel",
    "REPORT_TITLE",
    "SAFETY_LINES",
    "SOURCE_MODULE",
    "build_live_gui_device_inventory_model",
    "format_live_gui_device_inventory_model_report",
    "live_gui_device_inventory_model_payload",
]
