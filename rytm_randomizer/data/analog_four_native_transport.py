"""Bounded A4 native/CC7 facts and descriptive evidence, never output authority."""

from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Final, Literal, TypedDict

A4_NATIVE_CC7_BINDINGS: Final[MappingProxyType[str, str]] = MappingProxyType(
    {
        "osc1_level": "OSC1 Level",
        "osc2_level": "OSC2 Level",
        "noise_sample_hold": "Noise S&H",
        "noise_level": "Noise Level",
        "sync_amount": "Sync Amount",
        "slide_time": "Slide Time",
        "vibrato_speed": "Vibrato Speed",
        "filter1_resonance": "Filter1 Resonance",
        "filter2_resonance": "Filter2 Resonance",
        "envf_attack": "EnvF Attack Time",
        "envf_decay": "EnvF Decay Time",
        "envf_sustain": "EnvF Sustain Level",
        "envf_release": "EnvF Release Time",
        "env2_attack": "Env2 Attack Time",
        "env2_decay": "Env2 Decay Time",
        "env2_sustain": "Env2 Sustain Level",
        "env2_release": "Env2 Release Time",
        "osc1_pw": "OSC1 Pulsewidth",
        "osc2_pw": "OSC2 Pulsewidth",
        "bend_depth": "Bend Amount",
        "filter1_overdrive": "Filter Overdrive",
        "filter1_env_depth": "Filter1 Envelope Amount",
        "filter2_env_depth": "Filter2 Envelope Amount",
        "lfo1_speed": "LFO1 Speed",
        "lfo2_speed": "LFO2 Speed",
    }
)


@dataclass(frozen=True)
class AnalogFourNativeTransportConflict:
    manual_name: str
    native_scale: str
    display_scale: str
    blocking_reason: str = "native_transport_scale_conflict"


A4_NATIVE_TRANSPORT_CONFLICTS: Final[MappingProxyType[str, AnalogFourNativeTransportConflict]] = (
    MappingProxyType(
        {
            "osc1_pwm_speed": AnalogFourNativeTransportConflict("OSC1 PWM Speed", "U7", "bipolar"),
            "osc2_pwm_speed": AnalogFourNativeTransportConflict("OSC2 PWM Speed", "U7", "bipolar"),
            "osc1_pwm_depth": AnalogFourNativeTransportConflict("OSC1 PWM Depth", "U7", "bipolar"),
            "osc2_pwm_depth": AnalogFourNativeTransportConflict("OSC2 PWM Depth", "U7", "bipolar"),
            "vibrato_depth": AnalogFourNativeTransportConflict("Vibrato Depth", "U7", "bipolar"),
            "noise_fade": AnalogFourNativeTransportConflict("Noise Fade", "BIPOLAR", "unipolar"),
        }
    )
)
A4_NATIVE_TRANSPORT_PAIRED_REASON: Final[str] = "paired_precision_requires_separate_transport"
A4_NATIVE_TRANSPORT_ENUM_REASON: Final[str] = "native_enum_transport_unverified"
A4_NATIVE_TRANSPORT_UNMAPPED_REASON: Final[str] = "native_cc7_mapping_unverified"
A4_NATIVE_TRANSPORT_CONTRACT_REASON: Final[str] = "native_cc7_contract_mismatch"
A4PermanentOutputBlocker = Literal[
    "a4_hardware_audition_validation_pending",
    "a4_live_transport_mapping_unverified",
    "persistent_kit_write_prohibited",
]
A4_NATIVE_TRANSPORT_OUTPUT_HOLDS: Final[tuple[A4PermanentOutputBlocker, ...]] = (
    "a4_hardware_audition_validation_pending",
    "a4_live_transport_mapping_unverified",
    "persistent_kit_write_prohibited",
)
A4_NATIVE_TRANSPORT_HOLDS: Final[tuple[str, ...]] = (
    *A4_NATIVE_TRANSPORT_OUTPUT_HOLDS,
    "channel_routing_unverified",
)
A4_NATIVE_TRANSPORT_SCHEMA_VERSION: Final[Literal["a4-native-transport-preview-v1"]] = (
    "a4-native-transport-preview-v1"
)


class AnalogFourNativeTransportChangeDict(TypedDict):
    track_id: int
    parameter: str
    before_native: int
    after_native: int
    cc_number: int | None
    before_cc7: int | None
    after_cc7: int | None
    roundtrip_exact: bool
    blockers: list[str]


@dataclass(frozen=True)
class AnalogFourNativeTransportChange:
    """Descriptive scalars only; no channel, MIDI event or executable packet."""

    track_id: int
    parameter: str
    before_native: int
    after_native: int
    cc_number: int | None
    before_cc7: int | None
    after_cc7: int | None
    roundtrip_exact: bool
    blockers: tuple[str, ...]

    def to_dict(self) -> AnalogFourNativeTransportChangeDict:
        return {
            "track_id": self.track_id,
            "parameter": self.parameter,
            "before_native": self.before_native,
            "after_native": self.after_native,
            "cc_number": self.cc_number,
            "before_cc7": self.before_cc7,
            "after_cc7": self.after_cc7,
            "roundtrip_exact": self.roundtrip_exact,
            "blockers": list(self.blockers),
        }


class AnalogFourNativeTransportPreviewDict(TypedDict):
    schema_version: Literal["a4-native-transport-preview-v1"]
    mapping_complete: bool
    changes: list[AnalogFourNativeTransportChangeDict]
    blocked_reasons: list[str]
    ready: Literal[False]
    output_authority: Literal["offline-review-only"]
    hardware_send_validated: Literal[False]
    channel_routing_verified: Literal[False]


@dataclass(frozen=True)
class AnalogFourNativeTransportPreview:
    """Constructing or replacing a review cannot grant hardware authority."""

    changes: tuple[AnalogFourNativeTransportChange, ...]
    schema_version: Literal["a4-native-transport-preview-v1"] = field(
        default=A4_NATIVE_TRANSPORT_SCHEMA_VERSION, init=False
    )
    mapping_complete: bool = field(init=False)
    blocked_reasons: tuple[str, ...] = field(init=False)
    ready: Literal[False] = field(default=False, init=False)
    output_authority: Literal["offline-review-only"] = field(
        default="offline-review-only", init=False
    )
    hardware_send_validated: Literal[False] = field(default=False, init=False)
    channel_routing_verified: Literal[False] = field(default=False, init=False)

    def __post_init__(self) -> None:
        if type(self.changes) is not tuple or not all(
            type(change) is AnalogFourNativeTransportChange for change in self.changes
        ):
            raise TypeError("changes must be a tuple of native transport change records")
        reasons = tuple(dict.fromkeys(reason for row in self.changes for reason in row.blockers))
        object.__setattr__(
            self,
            "mapping_complete",
            all(row.roundtrip_exact and not row.blockers for row in self.changes),
        )
        object.__setattr__(self, "blocked_reasons", (*A4_NATIVE_TRANSPORT_HOLDS, *reasons))

    def to_dict(self) -> AnalogFourNativeTransportPreviewDict:
        return {
            "schema_version": self.schema_version,
            "mapping_complete": self.mapping_complete,
            "changes": [change.to_dict() for change in self.changes],
            "blocked_reasons": list(self.blocked_reasons),
            "ready": self.ready,
            "output_authority": self.output_authority,
            "hardware_send_validated": self.hardware_send_validated,
            "channel_routing_verified": self.channel_routing_verified,
        }


__all__ = [
    "A4_NATIVE_CC7_BINDINGS",
    "A4_NATIVE_TRANSPORT_CONFLICTS",
    "A4_NATIVE_TRANSPORT_CONTRACT_REASON",
    "A4_NATIVE_TRANSPORT_ENUM_REASON",
    "A4_NATIVE_TRANSPORT_HOLDS",
    "A4_NATIVE_TRANSPORT_OUTPUT_HOLDS",
    "A4_NATIVE_TRANSPORT_PAIRED_REASON",
    "A4_NATIVE_TRANSPORT_SCHEMA_VERSION",
    "A4_NATIVE_TRANSPORT_UNMAPPED_REASON",
    "AnalogFourNativeTransportChange",
    "AnalogFourNativeTransportChangeDict",
    "AnalogFourNativeTransportConflict",
    "AnalogFourNativeTransportPreview",
    "AnalogFourNativeTransportPreviewDict",
]
