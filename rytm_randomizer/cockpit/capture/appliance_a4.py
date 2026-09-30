"""Exact saved-state A4 appliance projection through the existing field codec.

Integer native words retain sub-display precision during offline previews.
This module never renders or sends MIDI, changes a retained capture, or promotes
saved state to unsaved working-memory authority.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from ...data.analog_four_kit_fields import (
    A4_NATIVE_FIELD_DOMAINS,
    A4NativeEncoding,
    format_a4_native_number,
)
from ...data.analog_four_saved_kit_layout import A4_SNAPSHOT_LAYOUT_SAVED_KIT
from ...devices import A4Kit, A4Sound, AnalogFourKitSnapshot
from ..data import PadState, Snapshot, new_ulid, require_int
from ..data.stage import ANALOG_FOUR_DEVICE_ID
from .appliance_capabilities import ApplianceParameterCapability, parameter_capabilities
from .service import KitCaptureResult, decode_kit_capture_frame


@dataclass(frozen=True)
class A4ApplianceFieldEncoding:
    """Offline integer domain and exact display projection for one field."""

    parameter_id: str
    field: str
    encoding: A4NativeEncoding
    raw_minimum: int
    raw_maximum: int
    display_scale: int = 1
    display_offset: int = 0
    categorical: bool = False
    legal_values: tuple[tuple[int, str], ...] = ()
    offline_mutable: bool = True
    blockers: tuple[str, ...] = ()

    def validate_raw(self, value: object) -> int:
        raw = require_int(value, "A4 projected native value")
        if not self.raw_minimum <= raw <= self.raw_maximum:
            raise ValueError("A4 projected native value is outside its supported domain")
        if self.legal_values and raw not in {value for value, _ in self.legal_values}:
            raise ValueError("A4 projected selector value is not a legal enum choice")
        return raw

    def format_display(self, value: object) -> str:
        """Format exactly using integer arithmetic, independent of Decimal context."""

        raw = self.validate_raw(value)
        for enum_value, label in self.legal_values:
            if raw == enum_value:
                return label
        return format_a4_native_number(raw, scale=self.display_scale, offset=self.display_offset)

    def read(self, sound: A4Sound) -> int:
        """Use the public typed field accessors, never hand-read offsets."""

        if self.encoding == "q8.8":
            raw = sound.get_fixed_8_8_raw(self.field)
        elif self.encoding == "q8.7":
            raw = sound.get_mod_depth_raw(self.field)
        elif self.encoding == "pitch_word":
            raw = sound.get_oscillator_pitch_raw(1 if self.field.startswith("osc1") else 2)
        elif self.encoding == "fine_component":
            raw = sound.get_oscillator_fine(1 if self.field.startswith("osc1") else 2)
        elif self.encoding == "bipolar":
            raw = sound.get_bipolar(self.field)
        else:
            raw = sound.get_u7(self.field)
        return self.validate_raw(raw)

    def to_dict(self) -> dict[str, object]:
        return {
            "parameter_id": self.parameter_id,
            "field": self.field,
            "encoding": self.encoding,
            "raw_minimum": self.raw_minimum,
            "raw_maximum": self.raw_maximum,
            "display_scale": self.display_scale,
            "display_offset": self.display_offset,
            "categorical": self.categorical,
            "legal_values": [
                {"value": value, "label": label} for value, label in self.legal_values
            ],
            "offline_mutable": self.offline_mutable,
            "blockers": list(self.blockers),
            "baseline_coverage": "saved_state_only",
            "live_send_supported": False,
            "hardware_restore_supported": False,
        }


def _encoding_for_row(row: ApplianceParameterCapability) -> A4ApplianceFieldEncoding | None:
    if not row.native_fields:
        return None
    field = row.native_fields[0]
    domain = row.legal_domain
    facts = A4_NATIVE_FIELD_DOMAINS[field]

    def bound(screen_value: str | None, fallback: int) -> int:
        if screen_value is None:
            return fallback
        # Exact canonical display bounds, including field-specific calibration
        # limits, become native integers without Decimal context arithmetic.
        numerator, denominator = Decimal(screen_value).as_integer_ratio()
        return numerator * facts.display_scale // denominator + facts.display_offset

    minimum = bound(domain.minimum, facts.value_minimum)
    maximum = bound(domain.maximum, facts.value_maximum)
    mutable = domain.authority != "unknown" and facts.offline_mutable
    blockers: tuple[str, ...] = (
        ("shared_pitch_component_requires_pair_edit",)
        if not facts.offline_mutable
        else () if mutable else ("legal_values_unproven",)
    )
    return A4ApplianceFieldEncoding(
        row.parameter_id,
        field,
        facts.encoding,
        minimum,
        maximum,
        facts.display_scale,
        facts.display_offset,
        row.categorical,
        domain.legal_values,
        mutable,
        blockers,
    )


def appliance_a4_parameter_encodings() -> tuple[A4ApplianceFieldEncoding, ...]:
    """Return mapped-field metadata; documented-only MIDI rows are absent."""

    return tuple(
        encoding
        for row in parameter_capabilities(ANALOG_FOUR_DEVICE_ID)
        if (encoding := _encoding_for_row(row)) is not None
    )


def appliance_a4_parameter_encoding(parameter_id: str) -> A4ApplianceFieldEncoding | None:
    """Resolve an exact mapped A4 parameter identity, without fuzzy fallback."""

    for encoding in appliance_a4_parameter_encodings():
        if encoding.parameter_id == parameter_id:
            return encoding
    return None


def appliance_snapshot_from_a4_capture(result: KitCaptureResult) -> Snapshot:
    """Project verified saved-KIT values for all four tracks without authority.

    Re-decode the retained canonical frame and compare the exact native object
    so a caller cannot relabel or swap the source using only a trusted-looking
    checksum flag. Unknown/invalid mapped value domains refuse projection.
    """

    if result.device_id != ANALOG_FOUR_DEVICE_ID:
        raise ValueError("appliance A4 projection requires an Analog Four capture")
    if not result.round_trip_verified:
        raise ValueError("appliance A4 capture must have exact codec round-trip verification")
    if not isinstance(result.snapshot, AnalogFourKitSnapshot):
        raise TypeError("appliance A4 capture must retain an AnalogFourKitSnapshot")
    if result.snapshot.snapshot_layout != A4_SNAPSHOT_LAYOUT_SAVED_KIT:
        raise ValueError("appliance A4 projection requires the canonical saved-KIT layout")
    canonical = decode_kit_capture_frame(ANALOG_FOUR_DEVICE_ID, result.frame)
    if (
        not isinstance(canonical.snapshot, AnalogFourKitSnapshot)
        or canonical.fingerprint != result.fingerprint
        or canonical.snapshot.unpacked != result.snapshot.unpacked
    ):
        raise ValueError("appliance A4 capture does not match its retained canonical frame")
    kit = A4Kit.from_bytes(canonical.snapshot.unpacked)
    encodings = appliance_a4_parameter_encodings()
    return Snapshot(
        new_ulid(),
        ANALOG_FOUR_DEVICE_ID,
        result.captured_at,
        tuple(
            PadState(
                track + 1,
                "A4 CAPTURED SAVED KIT",
                {encoding.parameter_id: encoding.read(kit.sound(track)) for encoding in encodings},
            )
            for track in range(4)
        ),
        None,
        None,
    )


__all__ = [
    "A4ApplianceFieldEncoding",
    "appliance_a4_parameter_encoding",
    "appliance_a4_parameter_encodings",
    "appliance_snapshot_from_a4_capture",
]
