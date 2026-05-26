"""Passive live-GUI model for the Analog Rytm 12-pad surface."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import Final, Literal, TypeAlias, TypedDict

from ..data.rytm_machine_catalog import (
    MACHINE_SELECTABLE,
    MUTABLE_V134,
    RYTM_PAD_CAPABILITIES,
    RytmMachineProfile,
    allowed_machine_profiles_for_pad,
)
from .formatter import SAFETY_SECTION_HEADER, PassiveReportHeader, passive_report_lines

REPORT_TITLE: Final[str] = "RytmRandomizer passive live GUI 12-pad surface model"
SOURCE_MODULE: Final[str] = "reports.live_gui_12_pad_surface_model"
SURFACE_MODEL_VERSION: Final[str] = "live_gui_12_pad_surface_v1"
ACTIVE_V134_PADS: Final[frozenset[int]] = frozenset({1, 2, 3, 4})
PRIMARY_MACHINE_LIMIT: Final[int] = 4
PLANNED_LOCK_REASON: Final[str] = "awaiting V1.34-compatible mutation routing for pads 5-12"
SAFETY_LINES: Final[tuple[str, ...]] = (
    "passive/read-only",
    "in-memory only",
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
_HEADER: Final[PassiveReportHeader] = PassiveReportHeader(
    title=REPORT_TITLE,
    source_module=SOURCE_MODULE,
)

SurfaceState: TypeAlias = Literal["active_v134", "planned_expansion"]
SurfaceScalar: TypeAlias = str | int | bool
PadCardPayload: TypeAlias = dict[str, SurfaceScalar | tuple[str, ...]]
SurfacePayload: TypeAlias = dict[
    str,
    SurfaceScalar | tuple[str, ...] | tuple[PadCardPayload, ...],
]


@dataclass(frozen=True)
class LiveGuiRytmPadSurfaceCard:
    """GUI-ready passive state for one 1-based Analog Rytm pad."""

    pad: int
    track_code: str
    label: str
    surface_state: SurfaceState
    ui_enabled: bool
    ui_locked: bool
    lock_reason: str
    default_role: str
    default_machine_label: str
    legal_machine_count: int
    snapshot_mutable_machine_count: int
    selectable_only_machine_count: int
    primary_machine_labels: tuple[str, ...]


class LiveGuiRytmPadSurfaceCardDict(TypedDict):
    """JSON-ready contract for :class:`LiveGuiRytmPadSurfaceCard`."""

    pad: int
    track_code: str
    label: str
    surface_state: SurfaceState
    ui_enabled: bool
    ui_locked: bool
    lock_reason: str
    default_role: str
    default_machine_label: str
    legal_machine_count: int
    snapshot_mutable_machine_count: int
    selectable_only_machine_count: int
    primary_machine_labels: tuple[str, ...]


@dataclass(frozen=True)
class LiveGuiRytmTwelvePadSurfaceModel:
    """Passive model the cockpit can consume before the 12-pad UI is wired."""

    model_version: str
    pad_count: int
    active_pad_count: int
    planned_pad_count: int
    cards_by_pad: Mapping[int, LiveGuiRytmPadSurfaceCard]
    blocked_actions: tuple[str, ...]
    safety: tuple[str, ...]


class LiveGuiRytmTwelvePadSurfaceModelDict(TypedDict):
    """JSON-ready contract for :class:`LiveGuiRytmTwelvePadSurfaceModel`."""

    model_version: str
    pad_count: int
    active_pad_count: int
    planned_pad_count: int
    cards_by_pad: Mapping[int, LiveGuiRytmPadSurfaceCardDict]
    blocked_actions: tuple[str, ...]
    safety: tuple[str, ...]


def _default_role(profiles: tuple[RytmMachineProfile, ...]) -> str:
    return profiles[0].role_tags[0]


def _card_state(pad: int) -> SurfaceState:
    if pad in ACTIVE_V134_PADS:
        return "active_v134"
    return "planned_expansion"


def _primary_machine_labels(profiles: tuple[RytmMachineProfile, ...]) -> tuple[str, ...]:
    return tuple(profile.label for profile in profiles[:PRIMARY_MACHINE_LIMIT])


def _count_status(profiles: tuple[RytmMachineProfile, ...], status: str) -> int:
    return sum(1 for profile in profiles if profile.support_status == status)


def _pad_surface_card(
    pad: int,
    track_code: str,
    label: str,
) -> LiveGuiRytmPadSurfaceCard:
    profiles = allowed_machine_profiles_for_pad(pad)
    surface_state = _card_state(pad)
    ui_enabled = surface_state == "active_v134"
    return LiveGuiRytmPadSurfaceCard(
        pad=pad,
        track_code=track_code,
        label=label,
        surface_state=surface_state,
        ui_enabled=ui_enabled,
        ui_locked=not ui_enabled,
        lock_reason="" if ui_enabled else PLANNED_LOCK_REASON,
        default_role=_default_role(profiles),
        default_machine_label=profiles[0].label,
        legal_machine_count=len(profiles),
        snapshot_mutable_machine_count=_count_status(profiles, MUTABLE_V134),
        selectable_only_machine_count=_count_status(profiles, MACHINE_SELECTABLE),
        primary_machine_labels=_primary_machine_labels(profiles),
    )


def build_live_gui_12_pad_surface_model() -> LiveGuiRytmTwelvePadSurfaceModel:
    """Return passive 12-pad surface metadata for a future live GUI."""

    cards_by_pad: dict[int, LiveGuiRytmPadSurfaceCard] = {}
    active_count = 0

    for capability in RYTM_PAD_CAPABILITIES:
        card = _pad_surface_card(capability.pad, capability.track_code, capability.label)
        cards_by_pad[capability.pad] = card
        if card.surface_state == "active_v134":
            active_count += 1

    return LiveGuiRytmTwelvePadSurfaceModel(
        model_version=SURFACE_MODEL_VERSION,
        pad_count=len(RYTM_PAD_CAPABILITIES),
        active_pad_count=active_count,
        planned_pad_count=len(RYTM_PAD_CAPABILITIES) - active_count,
        cards_by_pad=MappingProxyType(cards_by_pad),
        blocked_actions=BLOCKED_ACTIONS,
        safety=SAFETY_LINES,
    )


def _card_payload(card: LiveGuiRytmPadSurfaceCard) -> PadCardPayload:
    return {
        "pad": card.pad,
        "track_code": card.track_code,
        "label": card.label,
        "surface_state": card.surface_state,
        "ui_enabled": card.ui_enabled,
        "ui_locked": card.ui_locked,
        "lock_reason": card.lock_reason,
        "default_role": card.default_role,
        "default_machine_label": card.default_machine_label,
        "legal_machine_count": card.legal_machine_count,
        "snapshot_mutable_machine_count": card.snapshot_mutable_machine_count,
        "selectable_only_machine_count": card.selectable_only_machine_count,
        "primary_machine_labels": card.primary_machine_labels,
    }


def live_gui_12_pad_surface_model_payload(
    model: LiveGuiRytmTwelvePadSurfaceModel | None = None,
) -> SurfacePayload:
    """Return a deterministic JSON-shaped payload without hardware side effects."""

    source_model = build_live_gui_12_pad_surface_model() if model is None else model
    cards = tuple(
        _card_payload(source_model.cards_by_pad[pad]) for pad in source_model.cards_by_pad
    )
    return {
        "model_version": source_model.model_version,
        "pad_count": source_model.pad_count,
        "active_pad_count": source_model.active_pad_count,
        "planned_pad_count": source_model.planned_pad_count,
        "cards": cards,
        "blocked_actions": source_model.blocked_actions,
        "safety": source_model.safety,
    }


def _live_gui_12_pad_surface_body_lines(
    model: LiveGuiRytmTwelvePadSurfaceModel,
) -> list[str]:
    lines = [
        "Summary:",
        f"- Model version: {model.model_version}",
        f"- Pads: {model.pad_count}",
        f"- Active V1.34 pads: {model.active_pad_count}",
        f"- Planned/locked pads: {model.planned_pad_count}",
        "Pads:",
    ]

    for pad in sorted(model.cards_by_pad):
        card = model.cards_by_pad[pad]
        lines.extend(
            [
                f"Pad {card.pad} / {card.track_code} / {card.label}:",
                f"  Surface state: {card.surface_state}",
                f"  UI enabled: {card.ui_enabled}",
                f"  UI locked: {card.ui_locked}",
                f"  Lock reason: {card.lock_reason or 'none'}",
                f"  Default role: {card.default_role}",
                f"  Default machine: {card.default_machine_label}",
                f"  Legal machines: {card.legal_machine_count}",
                f"  Snapshot-mutable machines: {card.snapshot_mutable_machine_count}",
                f"  Selectable-only machines: {card.selectable_only_machine_count}",
                f"  Primary machines: {', '.join(card.primary_machine_labels)}",
            ]
        )

    lines.append("Blocked actions:")
    lines.extend(f"- {action}" for action in model.blocked_actions)
    lines.append(SAFETY_SECTION_HEADER)
    lines.extend(f"- {line}" for line in model.safety)
    return lines


def format_live_gui_12_pad_surface_model_report(
    model: LiveGuiRytmTwelvePadSurfaceModel | None = None,
) -> list[str]:
    """Return deterministic lines for the passive 12-pad live-GUI surface model."""

    source_model = build_live_gui_12_pad_surface_model() if model is None else model
    return passive_report_lines(_HEADER, _live_gui_12_pad_surface_body_lines(source_model))


__all__ = [
    "ACTIVE_V134_PADS",
    "BLOCKED_ACTIONS",
    "LiveGuiRytmPadSurfaceCard",
    "LiveGuiRytmPadSurfaceCardDict",
    "LiveGuiRytmTwelvePadSurfaceModel",
    "LiveGuiRytmTwelvePadSurfaceModelDict",
    "PLANNED_LOCK_REASON",
    "REPORT_TITLE",
    "SAFETY_LINES",
    "SOURCE_MODULE",
    "SURFACE_MODEL_VERSION",
    "build_live_gui_12_pad_surface_model",
    "format_live_gui_12_pad_surface_model_report",
    "live_gui_12_pad_surface_model_payload",
]
