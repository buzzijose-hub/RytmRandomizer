"""Immutable RAM-only studio intent, distinct from offline preparation reports.

No inbound plan parser exists: consumers must rebuild from canonical bytes and
current session observations before confirming an exact plan.
"""

from __future__ import annotations

import unicodedata
from dataclasses import dataclass, field
from typing import Final, Literal, TypedDict

from ...data.analog_four_saved_kit_layout import A4_KIT_SYNTH_TRACK_COUNT
from ...data.midi_transport import MIDI_MESSAGE_SETTLE_SECONDS
from ...guardrails.input_validation import require_int, require_text
from .send_plan import CockpitSendPlan

_MAX_OUTPUT_NAME: Final[int] = 256
_MAX_CHANNEL: Final[int] = 16
_CONTROL_CATEGORIES: Final[frozenset[str]] = frozenset({"Cc", "Cf", "Cs", "Zl", "Zp"})
A4_STUDIO_USB_FAMILY_NAME: Final[str] = "analog four"
A4_STUDIO_EXCLUDED_FAMILY_NAME: Final[str] = "rytm"


def is_a4_studio_usb_output_name(name: str) -> bool:
    """Conservatively require an OS-labelled A4 USB route, not physical proof.

    Generic DIN interfaces and contradictory Rytm names cannot qualify for this
    bounded trial. The operator still checks physical routing in the studio.
    """
    normalized = " ".join(name.casefold().split())
    return (
        A4_STUDIO_USB_FAMILY_NAME in normalized and A4_STUDIO_EXCLUDED_FAMILY_NAME not in normalized
    )


class A4StudioRoutingDict(TypedDict):
    output_port_name: str
    track_channels: list[int]


@dataclass(frozen=True)
class A4StudioRouting:
    """Exact output intent and four distinct user-facing channels (1..16)."""

    output_port_name: str
    track_channels: tuple[int, int, int, int]

    def __post_init__(self) -> None:
        name = require_text(self.output_port_name, "output_port_name", ValueError)
        if (
            not name.strip()
            or len(name) > _MAX_OUTPUT_NAME
            or any(unicodedata.category(character) in _CONTROL_CATEGORIES for character in name)
        ):
            raise ValueError("output_port_name must be bounded nonempty plain text")
        if (
            type(self.track_channels) is not tuple
            or len(self.track_channels) != A4_KIT_SYNTH_TRACK_COUNT
        ):
            raise ValueError("track_channels must be a four-channel tuple")
        for channel in self.track_channels:
            if not 1 <= require_int(channel, "track channel", ValueError) <= _MAX_CHANNEL:
                raise ValueError("track channels must be in 1..16")
        if len(set(self.track_channels)) != A4_KIT_SYNTH_TRACK_COUNT:
            raise ValueError("track channels must be distinct")

    def to_dict(self) -> A4StudioRoutingDict:
        return {
            "output_port_name": self.output_port_name,
            "track_channels": list(self.track_channels),
        }


class A4StudioAuditionPlanDict(TypedDict):
    bank_id: str
    bank_revision: int
    entry_id: str
    candidate_id: str | None
    session_generation: int
    routing: A4StudioRoutingDict
    send_plan: dict[str, object]
    plan_id: str
    ready: bool
    blocked_reasons: list[str]
    hardware_send_validated: Literal[False]
    persistent_write: Literal[False]
    output_authority: Literal["studio-ram-only-unqualified"]


@dataclass(frozen=True)
class A4StudioAuditionPlan:
    """Inert exact packets for an explicitly acknowledged, unqualified audition.

    Readiness is software preflight only, never a physical validation claim or
    a grant to open a port. The existing armed boundary remains mandatory.
    """

    bank_id: str
    bank_revision: int
    entry_id: str
    candidate_id: str | None
    session_generation: int
    routing: A4StudioRouting
    send_plan: CockpitSendPlan
    blocked_reasons: tuple[str, ...]
    hardware_send_validated: Literal[False] = field(default=False, init=False)
    persistent_write: Literal[False] = field(default=False, init=False)
    output_authority: Literal["studio-ram-only-unqualified"] = field(
        default="studio-ram-only-unqualified", init=False
    )

    def __post_init__(self) -> None:
        if type(self.blocked_reasons) is not tuple:
            raise TypeError("blocked_reasons must be an immutable tuple")
        if self.send_plan.ready == bool(self.blocked_reasons):
            raise ValueError("studio readiness must agree with its blocked reasons")
        if not self.send_plan.ready and self.send_plan.packets:
            raise ValueError("blocked studio plans must contain zero packets")

    @property
    def plan_id(self) -> str:
        return self.send_plan.plan_id

    @property
    def ready(self) -> bool:
        return self.send_plan.ready

    def to_dict(self) -> A4StudioAuditionPlanDict:
        return {
            "bank_id": self.bank_id,
            "bank_revision": self.bank_revision,
            "entry_id": self.entry_id,
            "candidate_id": self.candidate_id,
            "session_generation": self.session_generation,
            "routing": self.routing.to_dict(),
            "send_plan": self.send_plan.to_dict(),
            "plan_id": self.plan_id,
            "ready": self.ready,
            "blocked_reasons": list(self.blocked_reasons),
            "hardware_send_validated": self.hardware_send_validated,
            "persistent_write": self.persistent_write,
            "output_authority": self.output_authority,
        }


__all__ = [
    "MIDI_MESSAGE_SETTLE_SECONDS",
    "is_a4_studio_usb_output_name",
    "A4StudioAuditionPlan",
    "A4StudioAuditionPlanDict",
    "A4StudioRouting",
    "A4StudioRoutingDict",
]
