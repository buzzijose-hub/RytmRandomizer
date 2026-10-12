"""Pure, source-preserving reference-sound candidates for Rytm and A4 KITs."""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import asdict, dataclass, field, fields, replace
from typing import Literal, cast

from ...data.analog_four_audio_inference import ANALOG_FOUR_AUDIO_INFERENCE_BY_PARAMETER
from ...data.analog_four_kit_fields import parse_a4_fixed_8_8
from ...data.analog_rytm_kit_fields import RYTM_SOUND_U7_FIELDS
from ...data.analog_rytm_kit_layout import (
    RYTM_KIT_SYSEX_HEADER_SIZE_WITHOUT_F0,
    RYTM_SOUND_FIELD_BY_NRPN_LSB,
    analog_rytm_track_sound_offset,
)
from ...data.analog_rytm_midi import ANALOG_RYTM_CC_BY_SECTION_AND_PARAMETER
from ...data.reference_sound_candidates import (
    A4_REFERENCE_INFERENCE_BINDINGS,
    REFERENCE_SOUND_LIMITATIONS,
    RYTM_REFERENCE_FEATURE_TERMS,
)
from ...data.rytm_machine_catalog import RYTM_MACHINE_PROFILES, is_machine_allowed_on_pad
from ...devices import (
    AnalogFourNativeDomain,
    AnalogFourNativeEncoding,
    AnalogFourNativeMutation,
    RytmKit,
    encode_bipolar,
    get_analog_four_native_field_capability,
    resolve_saved_kit_capture_capability,
)
from ...snapshot.mutation_scope import registered_mutation_ids
from ...style_analysis.analog_four_patch_inference import (
    build_analog_four_inference_feature_values,
    evaluate_analog_four_inference_spec,
)
from ...style_analysis.audio_patch_dna import build_audio_patch_dna_workspace
from ...style_analysis.extractor import (
    AudioFeatureAnalysis,
    AudioSynthesisFeatures,
    audio_synthesis_features_to_dict,
)
from ...style_analysis.runtime_types import require_runtime_type
from ..data.stage import ANALOG_FOUR_DEVICE_ID, ANALOG_RYTM_DEVICE_ID


@dataclass(frozen=True)
class ReferenceSoundControl:
    """Exact source native cell, plus truthful reference-inference eligibility."""

    parameter: str
    source_value: int
    source_display: str | None
    units: str
    domain: AnalogFourNativeDomain | None
    offsets: tuple[int, ...]
    reasons: tuple[str, ...]

    @property
    def mutable(self) -> bool:
        return not self.reasons and self.domain is not None

    def to_dict(self) -> dict[str, object]:
        """Return JSON-compatible control metadata without raw source bytes."""
        return {
            **asdict(self),
            "mutable": self.mutable,
            "output_authority": "local-file-only",
            "send_supported": False,
        }


@dataclass(frozen=True)
class ReferenceSoundChange:
    """One actual change, including unblended intent and exact encoded readback."""

    parameter: str
    source_value: int
    proposed_value: int
    rendered_value: int
    source_display: str | None
    proposed_display: str
    rendered_display: str | None
    units: str
    rationale: str
    offsets: tuple[int, ...]

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class ReferenceSoundCandidate:
    """Inert local bytes and an exact native-byte isolation proof."""

    candidate_id: str
    direction: str
    label: str
    device_id: str
    target: int
    source_sha256: str
    frame_bytes: bytes
    changes: tuple[ReferenceSoundChange, ...]
    limitations: tuple[str, ...]
    intended_unpacked_offsets: tuple[int, ...]
    changed_unpacked_offsets: tuple[int, ...]
    changed_wire_offsets: tuple[int, ...]
    audio_features: AudioSynthesisFeatures
    output_authority: Literal["local-file-only"] = field(default="local-file-only", init=False)
    hardware_send_validated: Literal[False] = field(default=False, init=False)
    roundtrip_redecoded: Literal[True] = field(default=True, init=False)

    @property
    def frame(self) -> bytes:
        return self.frame_bytes

    @property
    def features(self) -> AudioSynthesisFeatures:
        return self.audio_features

    def to_dict(self) -> dict[str, object]:
        """Return inspectable metadata; the caller owns persistence of frame bytes."""
        return {
            "candidate_id": self.candidate_id,
            "direction": self.direction,
            "label": self.label,
            "device_id": self.device_id,
            "target": self.target,
            "source_sha256": self.source_sha256,
            "frame_sha256": hashlib.sha256(self.frame).hexdigest(),
            "frame_size": len(self.frame),
            "changes": [change.to_dict() for change in self.changes],
            "limitations": self.limitations,
            "intended_unpacked_offsets": self.intended_unpacked_offsets,
            "changed_unpacked_offsets": self.changed_unpacked_offsets,
            "changed_wire_offsets": self.changed_wire_offsets,
            "features": audio_synthesis_features_to_dict(self.features),
            "output_authority": self.output_authority,
            "hardware_send_validated": False,
            "roundtrip_redecoded": True,
        }


def _validate_source(source_frame: bytes, device_id: str, target: int) -> bytes:
    if type(source_frame) is not bytes:
        raise TypeError("source_frame must be immutable bytes")
    if device_id not in (ANALOG_RYTM_DEVICE_ID, ANALOG_FOUR_DEVICE_ID):
        raise ValueError("unsupported reference-sound device")
    if type(target) is not int or target not in registered_mutation_ids(device_id):
        raise ValueError("target must be a strict device pad/track integer")
    codec = resolve_saved_kit_capture_capability(device_id).capability
    decoded = codec.decode_saved_kit_capture(source_frame)
    if codec.encode_saved_kit_capture(decoded) != source_frame:
        raise ValueError("source KIT must round-trip byte-identically")
    return decoded.unpacked


def _rytm_reference_controls(unpacked: bytes, target: int) -> tuple[ReferenceSoundControl, ...]:
    sound = RytmKit.from_bytes(unpacked).sound(target - 1)
    machine = int(sound.machine)
    profile = next((p for p in RYTM_MACHINE_PROFILES if p.machine_value == machine), None)
    if profile is None or not is_machine_allowed_on_pad(target, profile.key):
        raise ValueError("source Rytm machine is unknown or incompatible with selected pad")
    by_offset = {value.sound_offset: nrpn for nrpn, value in RYTM_SOUND_FIELD_BY_NRPN_LSB.items()}
    by_nrpn = {m.nrpn_lsb: m for m in ANALOG_RYTM_CC_BY_SECTION_AND_PARAMETER.values()}
    controls: list[ReferenceSoundControl] = []
    for parameter, offset in RYTM_SOUND_U7_FIELDS.items():
        raw = sound.get_u7(parameter)
        domain = AnalogFourNativeDomain(0, 127)
        mapping = by_nrpn.get(by_offset.get(offset))
        reasons: list[str] = []
        if parameter not in RYTM_REFERENCE_FEATURE_TERMS:
            reasons.append("audio_trait_unexpressible_or_unmapped")
        if mapping is None or mapping.mutation_status in ("locked_default", "forbidden"):
            reasons.append("mandatory_parameter_protection")
        if raw > domain.maximum:
            reasons.append("source_value_outside_verified_domain")
        controls.append(
            ReferenceSoundControl(
                parameter,
                raw,
                str(raw),
                "native u7 coarse; companion byte retained",
                domain,
                (analog_rytm_track_sound_offset(target, offset),),
                tuple(reasons),
            )
        )
    return tuple(controls)


def list_reference_sound_controls(
    source_frame: bytes, device_id: str, target: int
) -> tuple[ReferenceSoundControl, ...]:
    """List source-bound controls without I/O or live eligibility grants."""
    unpacked = _validate_source(source_frame, device_id, target)
    if device_id == ANALOG_RYTM_DEVICE_ID:
        return _rytm_reference_controls(unpacked, target)
    native = get_analog_four_native_field_capability().read_native_fields(source_frame)
    controls: list[ReferenceSoundControl] = []
    for cell in native.values:
        if cell.track != target:
            continue
        reasons: list[str] = []
        if not cell.mutable or not cell.metadata.evidence:
            reasons.append(cell.protection_reason or "native_source_or_evidence_unavailable")
        if cell.parameter not in A4_REFERENCE_INFERENCE_BINDINGS:
            reasons.append("audio_trait_unexpressible_or_unmapped")
        controls.append(
            ReferenceSoundControl(
                cell.parameter,
                cell.encoded_native,
                cell.screen_value,
                cell.metadata.native_encoding.value,
                cell.domain,
                cell.unpacked_offsets,
                tuple(reasons),
            )
        )
    return tuple(controls)


def _validate_reference_request(
    analysis: AudioFeatureAnalysis,
    parameters: tuple[str, ...],
    locks: tuple[str, ...],
    strength: float,
    controls: tuple[ReferenceSoundControl, ...],
) -> None:
    checked = require_runtime_type(
        analysis, AudioFeatureAnalysis, "analysis must be AudioFeatureAnalysis"
    )
    if type(strength) not in (int, float) or not math.isfinite(strength) or not 0 <= strength <= 1:
        raise ValueError("strength must be finite in 0..1")
    features = require_runtime_type(
        checked.synthesis_features,
        AudioSynthesisFeatures,
        "analysis requires measured AudioSynthesisFeatures",
    )
    for descriptor in fields(features):
        if descriptor.name == "audio_sha256":
            continue
        value = getattr(features, descriptor.name)
        if type(value) not in (float, int) or not math.isfinite(value) or not 0 <= value <= 1:
            raise ValueError("audio synthesis features must be finite normalized measurements")
    known = {control.parameter for control in controls}
    for selection in (parameters, locks):
        if type(selection) is not tuple or any(type(key) is not str for key in selection):
            raise TypeError("parameters and locks must be tuples of canonical field keys")
        if len(set(selection)) != len(selection) or not set(selection).issubset(known):
            raise ValueError("duplicate, unknown or foreign reference-sound parameter")


def _proposal(
    control: ReferenceSoundControl,
    features: AudioSynthesisFeatures,
    device_id: str,
) -> tuple[int, str, str]:
    if device_id == ANALOG_RYTM_DEVICE_ID:
        terms = RYTM_REFERENCE_FEATURE_TERMS[control.parameter]
        raw = round(127 * sum(getattr(features, name) * weight for name, weight in terms))
        equation = " + ".join(f"{weight:g}*{name}" for name, weight in terms)
        return raw, str(raw), f"Normalized native-u7 intent: round(127*({equation})); not Hz/ms."
    parameter = A4_REFERENCE_INFERENCE_BINDINGS[control.parameter]
    spec = ANALOG_FOUR_AUDIO_INFERENCE_BY_PARAMETER[parameter]
    feature_values = build_analog_four_inference_feature_values(features, column=1)
    screen = str(evaluate_analog_four_inference_spec(spec, feature_values))
    native = get_analog_four_native_field_capability().native_fields()
    encoding = next(item.native_encoding for item in native if item.parameter == control.parameter)
    if encoding is AnalogFourNativeEncoding.Q8_8:
        raw = parse_a4_fixed_8_8(screen)
    elif encoding is AnalogFourNativeEncoding.BIPOLAR:
        raw = encode_bipolar(int(screen))
    else:
        raw = int(screen)
    return (
        raw,
        screen,
        f"Existing measured-audio A4 inference for {parameter}; native conversion only, not acoustic equivalence.",
    )


def _verify_diff(
    source_frame: bytes, frame: bytes, device_id: str, intended: tuple[int, ...]
) -> tuple[tuple[int, ...], tuple[int, ...]]:
    codec = resolve_saved_kit_capture_capability(device_id).capability
    source = codec.decode_saved_kit_capture(source_frame)
    after = codec.decode_saved_kit_capture(frame)
    if after.header != source.header or codec.encode_saved_kit_capture(after) != frame:
        raise ValueError("candidate failed exact header-preserving round trip")
    changed = tuple(
        i
        for i, pair in enumerate(zip(source.unpacked, after.unpacked, strict=True))
        if pair[0] != pair[1]
    )
    if not set(changed).issubset(intended):
        raise ValueError("candidate changed bytes outside selected native controls")
    wire = tuple(
        i for i, pair in enumerate(zip(source_frame, frame, strict=True)) if pair[0] != pair[1]
    )
    if device_id == ANALOG_RYTM_DEVICE_ID:
        approved: set[int] = set()
        for offset in intended:
            group, member = divmod(offset, 7)
            mask = 1 + RYTM_KIT_SYSEX_HEADER_SIZE_WITHOUT_F0 + group * 8
            approved.update((mask, mask + member + 1))
        if intended:
            approved.update((len(frame) - 5, len(frame) - 4))
        if not set(wire).issubset(approved):
            raise ValueError("candidate changed wire bytes outside approved footprint")
    return changed, wire


def _render(  # noqa: PLR0913 - pure request plus selected direction and source controls
    source_frame: bytes,
    device_id: str,
    target: int,
    features: AudioSynthesisFeatures,
    controls: tuple[ReferenceSoundControl, ...],
    parameters: tuple[str, ...],
    locks: tuple[str, ...],
    strength: float,
    direction: str,
    label: str,
    audio_sha256: str,
) -> ReferenceSoundCandidate:
    mutations: list[AnalogFourNativeMutation] = []
    pending: list[tuple[ReferenceSoundControl, int, str, str, int]] = []
    limitations = list(REFERENCE_SOUND_LIMITATIONS)
    for control in controls:
        if control.parameter not in parameters:
            continue
        if control.parameter in locks or not control.mutable:
            reasons = ("parameter_locked",) if control.parameter in locks else control.reasons
            limitations.append(f"{control.parameter} preserved: {', '.join(reasons)}.")
            continue
        domain = cast(AnalogFourNativeDomain, control.domain)
        proposed, display, rationale = _proposal(control, features, device_id)
        source_index = domain.index_of(control.source_value)
        proposed_index = domain.index_of(proposed)
        raw = domain.value_at(round(source_index + strength * (proposed_index - source_index)))
        if raw != control.source_value:
            mutations.append(AnalogFourNativeMutation(control.parameter, target, raw))
            pending.append((control, proposed, display, rationale, raw))
    if device_id == ANALOG_FOUR_DEVICE_ID:
        rendered = get_analog_four_native_field_capability().render_native_fields(
            source_frame, mutations
        )
        frame, intended = rendered.framed_sysex, rendered.intended_unpacked_offsets
    else:
        codec = resolve_saved_kit_capture_capability(device_id).capability
        source = codec.decode_saved_kit_capture(source_frame)
        kit = RytmKit.from_bytes(source.unpacked)
        sound = kit.sound(target - 1)
        for mutation in mutations:
            sound.set_u7(mutation.parameter, mutation.encoded_native, clear_lsb=False)
        kit.replace_sound(target - 1, sound)
        frame = codec.encode_saved_kit_capture(replace(source, unpacked=kit.to_bytes()))
        intended = tuple(sorted(offset for item in pending for offset in item[0].offsets))
        limitations.append(
            "Rytm machine SRC/tuning and AL16 multi-pad recipe policies are not applied."
        )
    changed, wire = _verify_diff(source_frame, frame, device_id, intended)
    after = {
        control.parameter: control
        for control in list_reference_sound_controls(frame, device_id, target)
    }
    changes: list[ReferenceSoundChange] = []
    for control, proposed, display, rationale, raw in pending:
        readback = after[control.parameter]
        if readback.source_value != raw:
            raise ValueError("candidate native readback disagrees with requested value")
        changes.append(
            ReferenceSoundChange(
                control.parameter,
                control.source_value,
                proposed,
                raw,
                control.source_display,
                display,
                readback.source_display,
                control.units,
                rationale,
                control.offsets,
            )
        )
    if not changes:
        limitations.append(
            "No expressible unlocked selected value changed; candidate is an exact source clone."
        )
    source_hash = hashlib.sha256(source_frame).hexdigest()
    identity = json.dumps(
        (
            source_hash,
            hashlib.sha256(frame).hexdigest(),
            audio_sha256,
            device_id,
            target,
            direction,
            parameters,
            locks,
            strength,
            tuple(getattr(features, f.name) for f in fields(features)),
        ),
        separators=(",", ":"),
    )
    return ReferenceSoundCandidate(
        hashlib.sha256(identity.encode("ascii")).hexdigest(),
        direction,
        label,
        device_id,
        target,
        source_hash,
        frame,
        tuple(changes),
        tuple(limitations),
        intended,
        changed,
        wire,
        features,
    )


def render_reference_sound_candidates(  # noqa: PLR0913 - explicit immutable request
    source_frame: bytes,
    device_id: str,
    target: int,
    analysis: AudioFeatureAnalysis,
    parameters: tuple[str, ...],
    locks: tuple[str, ...],
    strength: float = 1.0,
) -> tuple[ReferenceSoundCandidate, ...]:
    """Render the eight existing DNA directions against exactly one saved sound."""
    controls = list_reference_sound_controls(source_frame, device_id, target)
    _validate_reference_request(analysis, parameters, locks, strength, controls)
    workspace = build_audio_patch_dna_workspace(
        analysis, track=target if device_id == ANALOG_FOUR_DEVICE_ID else 1
    )
    return tuple(
        _render(
            source_frame,
            device_id,
            target,
            candidate.audio_features,
            controls,
            parameters,
            locks,
            strength,
            candidate.key,
            candidate.label,
            analysis.audio_sha256,
        )
        for candidate in workspace.candidates
    )


def render_refined_reference_sound_candidate(  # noqa: PLR0913 - same explicit request
    source_frame: bytes,
    device_id: str,
    target: int,
    analysis: AudioFeatureAnalysis,
    parameters: tuple[str, ...],
    locks: tuple[str, ...],
    strength: float = 1.0,
) -> ReferenceSoundCandidate:
    """Render one already-refined measurement without reapplying DNA transforms."""
    controls = list_reference_sound_controls(source_frame, device_id, target)
    _validate_reference_request(analysis, parameters, locks, strength, controls)
    return _render(
        source_frame,
        device_id,
        target,
        analysis.synthesis_features,
        controls,
        parameters,
        locks,
        strength,
        "refined",
        "Refined",
        analysis.audio_sha256,
    )


__all__ = [
    "ReferenceSoundCandidate",
    "ReferenceSoundChange",
    "ReferenceSoundControl",
    "list_reference_sound_controls",
    "render_reference_sound_candidates",
    "render_refined_reference_sound_candidate",
]
