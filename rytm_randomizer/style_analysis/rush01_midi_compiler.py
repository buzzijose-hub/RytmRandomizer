"""Pure RUSH01 semantic-spec to documented MIDI event-plan compiler."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from types import MappingProxyType
from typing import Final, Literal, TypeAlias, cast

from ..data.analog_four_display import (
    ANALOG_FOUR_PARAMETER_DISPLAY,
    signed_screen_to_a4_midi,
)
from ..data.analog_four_midi import (
    ANALOG_FOUR_MANUAL_CC,
    ANALOG_FOUR_SYNTH_TRACK_NRPN,
    AnalogFourCcMapping,
)
from ..data.analog_rytm_midi import (
    ANALOG_RYTM_CC_BY_SECTION_AND_PARAMETER,
    AnalogRytmCcMapping,
    get_machine_src_mappings,
)
from ..data.plans import FILTER_TYPE_NAMES
from ..data.rush01_midi import (
    RUSH01_A4_BINDINGS,
    RUSH01_A4_TRACK_ORDER,
    RUSH01_RYTM_AMP_BINDINGS,
    RUSH01_RYTM_FILTER_BINDINGS,
    RUSH01_RYTM_TRACK_ORDER,
    Rush01ConversionKind,
    Rush01RytmCommonBinding,
)
from ..data.rytm_machine_catalog import (
    RYTM_MACHINE_PROFILES,
    RytmMachineProfile,
    is_machine_allowed_on_pad,
)

Rush01Device: TypeAlias = Literal["rytm", "a4"]
Rush01FieldStatus: TypeAlias = Literal[
    "ready",
    "preserve_reference",
    "manual_setup_required",
    "learn_required",
    "invalid_spec_field",
]
Rush01MessageType: TypeAlias = Literal["CC", "CC14", "NRPN"]
MidiByteMessage: TypeAlias = tuple[int, int, int]

RUSH01_PLAN_VERSION: Final[str] = "rush01-device-assisted-midi-plan-v1"
RUSH01_DEVICE_RYTM: Final[Rush01Device] = "rytm"
RUSH01_DEVICE_A4: Final[Rush01Device] = "a4"

STATUS_READY: Final[Rush01FieldStatus] = "ready"
STATUS_PRESERVE_REFERENCE: Final[Rush01FieldStatus] = "preserve_reference"
STATUS_MANUAL_SETUP_REQUIRED: Final[Rush01FieldStatus] = "manual_setup_required"
STATUS_LEARN_REQUIRED: Final[Rush01FieldStatus] = "learn_required"
STATUS_INVALID_SPEC_FIELD: Final[Rush01FieldStatus] = "invalid_spec_field"

MESSAGE_CC: Final[Rush01MessageType] = "CC"
MESSAGE_CC14: Final[Rush01MessageType] = "CC14"
MESSAGE_NRPN: Final[Rush01MessageType] = "NRPN"

_STATUS_ORDER: Final[tuple[Rush01FieldStatus, ...]] = (
    STATUS_READY,
    STATUS_PRESERVE_REFERENCE,
    STATUS_MANUAL_SETUP_REQUIRED,
    STATUS_LEARN_REQUIRED,
    STATUS_INVALID_SPEC_FIELD,
)
_MIDI_CC_STATUS: Final[int] = 0xB0
_MIDI_CHANNEL_MIN: Final[int] = 0
_MIDI_CHANNEL_MAX: Final[int] = 15
_MIDI_DATA_MIN: Final[int] = 0
_MIDI_DATA_MAX: Final[int] = 127
_MIDI_14BIT_MAX: Final[int] = 0x3FFF
_MIDI_NON_CHANNEL_MODE_CONTROL_MAX: Final[int] = 119
_RYTM_MODEL: Final[str] = "Analog Rytm MKII"
_A4_MODEL: Final[str] = "Analog Four MKII"
_SAFETY: Final[tuple[str, ...]] = (
    "dry-run by default",
    "one device per plan",
    "control-change messages only",
    "no Program Change",
    "no transport",
    "no SysEx",
    "no kit save",
    "no project messages",
    "no MIDI sent during compilation",
)


@dataclass(frozen=True)
class Rush01DeviceConfig:
    """Validated exact output port and user-facing 1-based track channels."""

    device: Rush01Device
    output_port: str
    track_channels: Mapping[str, int]

    def __post_init__(self) -> None:
        object.__setattr__(self, "track_channels", MappingProxyType(dict(self.track_channels)))


@dataclass(frozen=True)
class Rush01MidiField:
    """One semantic field and its compiled or deliberately refused MIDI action."""

    sequence: int
    device: Rush01Device
    track: str | None
    semantic_path: str
    requested_value: object
    normalized_midi_value: int | None
    message_type: Rush01MessageType | None
    channel: int | None
    user_channel: int | None
    controller: int | None
    controller_lsb: int | None
    nrpn_address: tuple[int, int] | None
    ordered_midi_bytes: tuple[MidiByteMessage, ...] | None
    mapping_evidence: str
    status: Rush01FieldStatus
    reason: str
    configuration_issue: str | None = None


@dataclass(frozen=True)
class Rush01MidiPlanSummary:
    """Deterministic status and transport totals for one compiled plan."""

    total_fields: int
    ready_fields: int
    preserve_reference_fields: int
    manual_setup_fields: int
    learn_required_fields: int
    invalid_spec_fields: int
    configured_ready_fields: int
    transport_message_count: int


@dataclass(frozen=True)
class Rush01MidiPlan:
    """One device's complete passive RUSH01 MIDI compilation result."""

    version: str
    device: Rush01Device
    device_model: str
    spec_name: str
    output_port: str | None
    fields: tuple[Rush01MidiField, ...]
    summary: Rush01MidiPlanSummary
    configuration_ready: bool
    dry_run: bool
    midi_sent: bool
    track_filter: str | None
    parameter_filter: str | None
    safety: tuple[str, ...]


def user_channel_to_midi(channel: int) -> int:
    """Convert a user-facing MIDI channel in ``1..16`` to ``0..15``."""

    if isinstance(channel, bool) or not isinstance(channel, int) or not 1 <= channel <= 16:
        raise ValueError("MIDI track channel must be an integer in 1..16")
    return channel - 1


def encode_cc_message(channel: int, controller: int, value: int) -> tuple[MidiByteMessage, ...]:
    """Encode one ordinary control-change message."""

    _validate_midi_channel(channel)
    _validate_midi_data(controller, label="controller")
    _validate_midi_data(value, label="value")
    return ((_MIDI_CC_STATUS | channel, controller, value),)


def encode_cc14_messages(
    channel: int,
    controller_msb: int,
    controller_lsb: int,
    value_14bit: int,
) -> tuple[MidiByteMessage, ...]:
    """Encode a high-resolution CC pair in MSB then LSB order."""

    _validate_midi_channel(channel)
    _validate_midi_data(controller_msb, label="controller_msb")
    _validate_midi_data(controller_lsb, label="controller_lsb")
    if isinstance(value_14bit, bool) or not isinstance(value_14bit, int):
        raise ValueError("value_14bit must be an integer in 0..16383")
    if not 0 <= value_14bit <= _MIDI_14BIT_MAX:
        raise ValueError("value_14bit must be an integer in 0..16383")
    return (
        (_MIDI_CC_STATUS | channel, controller_msb, (value_14bit >> 7) & 0x7F),
        (_MIDI_CC_STATUS | channel, controller_lsb, value_14bit & 0x7F),
    )


def encode_nrpn_messages(
    channel: int,
    nrpn_msb: int,
    nrpn_lsb: int,
    value_msb: int,
    *,
    value_lsb: int | None = None,
) -> tuple[MidiByteMessage, ...]:
    """Encode NRPN select then Data Entry MSB and optional LSB messages."""

    _validate_midi_channel(channel)
    for label, value in (
        ("nrpn_msb", nrpn_msb),
        ("nrpn_lsb", nrpn_lsb),
        ("value_msb", value_msb),
    ):
        _validate_midi_data(value, label=label)
    messages: tuple[MidiByteMessage, ...] = (
        (_MIDI_CC_STATUS | channel, 99, nrpn_msb),
        (_MIDI_CC_STATUS | channel, 98, nrpn_lsb),
        (_MIDI_CC_STATUS | channel, 6, value_msb),
    )
    if value_lsb is None:
        return messages
    _validate_midi_data(value_lsb, label="value_lsb")
    return messages + ((_MIDI_CC_STATUS | channel, 38, value_lsb),)


def parse_rush01_device_config(payload: object, device: str) -> Rush01DeviceConfig:
    """Validate one device section from the explicit YAML channel config."""

    normalized_device = _validated_device(device)
    root = _require_mapping(payload, path="config")
    section = _require_mapping(root.get(normalized_device), path=f"config.{normalized_device}")
    output_port = section.get("output_port")
    if not isinstance(output_port, str) or not output_port.strip():
        raise ValueError(f"config.{normalized_device}.output_port must be an exact port name")
    if _is_unfilled_config_value(output_port):
        raise ValueError(f"config.{normalized_device}.output_port still contains a placeholder")

    track_values = _require_mapping(
        section.get("tracks"), path=f"config.{normalized_device}.tracks"
    )
    expected_tracks = _track_order(normalized_device)
    channels: dict[str, int] = {}
    for track in expected_tracks:
        if track not in track_values:
            raise ValueError(f"config.{normalized_device}.tracks.{track} is required")
        raw_channel = track_values[track]
        if isinstance(raw_channel, str) and _is_unfilled_config_value(raw_channel):
            raise ValueError(
                f"config.{normalized_device}.tracks.{track} still contains a placeholder"
            )
        if isinstance(raw_channel, bool) or not isinstance(raw_channel, int):
            raise ValueError(f"config.{normalized_device}.tracks.{track} must be in 1..16")
        user_channel_to_midi(raw_channel)
        channels[track] = raw_channel

    extras = sorted(set(track_values) - set(expected_tracks))
    if extras:
        raise ValueError(
            f"config.{normalized_device}.tracks has unsupported track(s): {', '.join(extras)}"
        )
    return Rush01DeviceConfig(
        device=normalized_device,
        output_port=output_port,
        track_channels=channels,
    )


def compile_rush01_midi_plan(
    device: str,
    spec: object,
    *,
    config: Rush01DeviceConfig | None = None,
    track: str | None = None,
    parameter: str | None = None,
) -> Rush01MidiPlan:
    """Compile one RUSH01 device plan without opening or sending MIDI."""

    normalized_device = _validated_device(device)
    if config is not None and config.device != normalized_device:
        raise ValueError("config device does not match selected device")
    spec_root = _require_mapping(spec, path="spec")
    _validate_spec_device(spec_root, normalized_device)
    normalized_track = _validated_track_filter(normalized_device, track)
    if parameter is not None and not parameter.strip():
        raise ValueError("parameter filter must not be empty")

    channels = config.track_channels if config is not None else None
    if normalized_device == RUSH01_DEVICE_RYTM:
        fields = _compile_rytm_fields(spec_root, channels=channels)
    else:
        fields = _compile_a4_fields(spec_root, channels=channels)
    fields = _filter_and_resequence_fields(
        fields,
        track=normalized_track,
        parameter=parameter,
    )
    if not fields:
        raise ValueError("track/parameter filters matched no RUSH01 semantic fields")

    summary = _summarize(fields)
    configuration_ready = (
        config is not None
        and summary.ready_fields == summary.configured_ready_fields
        and summary.ready_fields > 0
    )
    plan = Rush01MidiPlan(
        version=RUSH01_PLAN_VERSION,
        device=normalized_device,
        device_model=_RYTM_MODEL if normalized_device == RUSH01_DEVICE_RYTM else _A4_MODEL,
        spec_name=_required_string(spec_root, "spec_name", path="spec.spec_name"),
        output_port=config.output_port if config is not None else None,
        fields=fields,
        summary=summary,
        configuration_ready=configuration_ready,
        dry_run=True,
        midi_sent=False,
        track_filter=normalized_track,
        parameter_filter=parameter,
        safety=_SAFETY,
    )
    validate_rush01_plan_safety(plan)
    return plan


def rush01_midi_plan_to_dict(plan: Rush01MidiPlan) -> dict[str, object]:
    """Return a stable JSON-ready representation of one plan."""

    if not isinstance(plan, Rush01MidiPlan):
        raise TypeError("plan must be a Rush01MidiPlan")
    return {
        "version": plan.version,
        "device": plan.device,
        "device_model": plan.device_model,
        "spec_name": plan.spec_name,
        "output_port": plan.output_port,
        "configuration_ready": plan.configuration_ready,
        "dry_run": plan.dry_run,
        "midi_sent": plan.midi_sent,
        "track_filter": plan.track_filter,
        "parameter_filter": plan.parameter_filter,
        "summary": {
            "total_fields": plan.summary.total_fields,
            "ready_fields": plan.summary.ready_fields,
            "preserve_reference_fields": plan.summary.preserve_reference_fields,
            "manual_setup_fields": plan.summary.manual_setup_fields,
            "learn_required_fields": plan.summary.learn_required_fields,
            "invalid_spec_fields": plan.summary.invalid_spec_fields,
            "configured_ready_fields": plan.summary.configured_ready_fields,
            "transport_message_count": plan.summary.transport_message_count,
        },
        "fields": [_field_to_dict(field) for field in plan.fields],
        "manual_setup_checklist": [
            field.semantic_path
            for field in plan.fields
            if field.status == STATUS_MANUAL_SETUP_REQUIRED
        ],
        "learn_required_fields": [
            field.semantic_path for field in plan.fields if field.status == STATUS_LEARN_REQUIRED
        ],
        "invalid_spec_fields": [
            field.semantic_path
            for field in plan.fields
            if field.status == STATUS_INVALID_SPEC_FIELD
        ],
        "safety": list(plan.safety),
    }


def validate_rush01_plan_safety(plan: Rush01MidiPlan) -> None:
    """Reject any compiled packet outside the allowed CC-only transport surface."""

    if plan.midi_sent:
        raise ValueError("compiled RUSH01 plans must record midi_sent=false")
    for field in plan.fields:
        if field.message_type not in (None, MESSAGE_CC, MESSAGE_CC14, MESSAGE_NRPN):
            raise ValueError(f"unsupported MIDI message type: {field.message_type}")
        if field.ordered_midi_bytes is None:
            continue
        for message in field.ordered_midi_bytes:
            if len(message) != 3:
                raise ValueError("compiled MIDI message must contain exactly three bytes")
            status, controller, value = message
            if status & 0xF0 != _MIDI_CC_STATUS:
                raise ValueError("only MIDI control-change messages are allowed")
            if not 0 <= controller <= _MIDI_NON_CHANNEL_MODE_CONTROL_MAX:
                raise ValueError("MIDI channel-mode and system messages are forbidden")
            if not 0 <= value <= _MIDI_DATA_MAX:
                raise ValueError("MIDI data bytes must be in 0..127")


def _compile_rytm_fields(
    spec: Mapping[str, object],
    *,
    channels: Mapping[str, int] | None,
) -> tuple[Rush01MidiField, ...]:
    tracks = _require_mapping(spec.get("tracks"), path="spec.tracks")
    track_levels = _require_mapping(spec.get("track_levels"), path="spec.track_levels")
    build_policy = _require_mapping(spec.get("build_policy"), path="spec.build_policy")
    fields: list[Rush01MidiField] = [
        _manual_field(
            device=RUSH01_DEVICE_RYTM,
            track=None,
            path="build_policy.kit_name",
            requested=build_policy.get("kit_name"),
            reason="kit naming remains a front-panel step; the compiler never saves a kit",
        )
    ]
    for pad, track in enumerate(RUSH01_RYTM_TRACK_ORDER, start=1):
        track_spec = _require_mapping(tracks.get(track), path=f"spec.tracks.{track}")
        channel, user_channel = _channel_for(track, channels)
        machine = _require_mapping(track_spec.get("machine"), path=f"spec.tracks.{track}.machine")
        machine_name = _required_string(machine, "name", path=f"spec.tracks.{track}.machine.name")
        profile = _rytm_machine_profile_by_label(machine_name)
        if not is_machine_allowed_on_pad(pad, profile.key):
            fields.append(
                _status_field(
                    device=RUSH01_DEVICE_RYTM,
                    track=track,
                    path=f"tracks.{track}.machine",
                    requested=machine_name,
                    status=STATUS_INVALID_SPEC_FIELD,
                    reason=f"{machine_name} is unsupported on Rytm pad {pad}",
                    channel=channel,
                    user_channel=user_channel,
                    evidence="repository Rytm pad capability catalog",
                )
            )
        else:
            fields.append(
                _compile_rytm_machine_field(
                    track=track,
                    machine=machine,
                    machine_name=machine_name,
                    machine_value=profile.machine_value,
                    channel=channel,
                    user_channel=user_channel,
                )
            )

        level_mapping = ANALOG_RYTM_CC_BY_SECTION_AND_PARAMETER[("COMMON", "Track Level")]
        fields.append(
            _compile_rytm_mapping_field(
                track=track,
                path=f"track_levels.{track}",
                requested=track_levels.get(track),
                mapping=level_mapping,
                channel=channel,
                user_channel=user_channel,
            )
        )
        source_spec = _require_mapping(track_spec.get("synth"), path=f"spec.tracks.{track}.synth")
        source_mappings = get_machine_src_mappings(profile.key)
        known_source_parameters = {mapping.parameter for mapping in source_mappings}
        for mapping in source_mappings:
            if mapping.parameter not in source_spec:
                continue
            fields.append(
                _compile_rytm_mapping_field(
                    track=track,
                    path=f"tracks.{track}.synth.{mapping.parameter}",
                    requested=source_spec[mapping.parameter],
                    mapping=mapping,
                    channel=channel,
                    user_channel=user_channel,
                )
            )
        for unknown in sorted(set(source_spec) - known_source_parameters):
            fields.append(
                _status_field(
                    device=RUSH01_DEVICE_RYTM,
                    track=track,
                    path=f"tracks.{track}.synth.{unknown}",
                    requested=source_spec[unknown],
                    status=STATUS_INVALID_SPEC_FIELD,
                    reason=f"{unknown} is not a documented {machine_name} source parameter",
                    channel=channel,
                    user_channel=user_channel,
                    evidence="machine-specific Analog Rytm source catalog",
                )
            )

        sample = _require_mapping(track_spec.get("sample"), path=f"spec.tracks.{track}.sample")
        sample_mapping = ANALOG_RYTM_CC_BY_SECTION_AND_PARAMETER[("SAMPLE", "Sample Level")]
        sample_level = sample.get("level")
        if sample_level == 0:
            fields.append(
                _compile_rytm_mapping_field(
                    track=track,
                    path=f"tracks.{track}.sample.level",
                    requested=sample_level,
                    mapping=sample_mapping,
                    channel=channel,
                    user_channel=user_channel,
                )
            )
        else:
            fields.append(
                _status_field(
                    device=RUSH01_DEVICE_RYTM,
                    track=track,
                    path=f"tracks.{track}.sample.level",
                    requested=sample_level,
                    status=STATUS_INVALID_SPEC_FIELD,
                    reason="RUSH01 phase one requires every sample playback level to be zero",
                    channel=channel,
                    user_channel=user_channel,
                    evidence="explicit RUSH01 no-external-sample policy",
                    message_type=_message_type_for(
                        sample_mapping.cc_msb,
                        sample_mapping.cc_lsb,
                        _rytm_nrpn_address(sample_mapping),
                    ),
                    controller=sample_mapping.cc_msb,
                    controller_lsb=sample_mapping.cc_lsb,
                    nrpn_address=_rytm_nrpn_address(sample_mapping),
                )
            )
        if sample.get("dependency") != "none":
            fields.append(
                _status_field(
                    device=RUSH01_DEVICE_RYTM,
                    track=track,
                    path=f"tracks.{track}.sample.dependency",
                    requested=sample.get("dependency"),
                    status=STATUS_INVALID_SPEC_FIELD,
                    reason="RUSH01 phase one permits no external sample dependency",
                    channel=channel,
                    user_channel=user_channel,
                    evidence="explicit RUSH01 no-external-sample policy",
                )
            )
        fields.extend(
            _compile_rytm_common_section(
                track=track,
                section_spec=_require_mapping(
                    track_spec.get("filter"), path=f"spec.tracks.{track}.filter"
                ),
                section_path="filter",
                bindings=RUSH01_RYTM_FILTER_BINDINGS,
                channel=channel,
                user_channel=user_channel,
            )
        )
        fields.extend(
            _compile_rytm_common_section(
                track=track,
                section_spec=_require_mapping(
                    track_spec.get("amp"), path=f"spec.tracks.{track}.amp"
                ),
                section_path="amp",
                bindings=RUSH01_RYTM_AMP_BINDINGS,
                channel=channel,
                user_channel=user_channel,
            )
        )
    return tuple(replace(field, sequence=index) for index, field in enumerate(fields, start=1))


def _compile_rytm_machine_field(
    *,
    track: str,
    machine: Mapping[str, object],
    machine_name: str,
    machine_value: int,
    channel: int | None,
    user_channel: int | None,
) -> Rush01MidiField:
    path = f"tracks.{track}.machine"
    selection = machine.get("selection")
    if selection == STATUS_MANUAL_SETUP_REQUIRED:
        return _manual_field(
            device=RUSH01_DEVICE_RYTM,
            track=track,
            path=path,
            requested=machine_name,
            reason=(
                f"select {machine_name} manually before applying source controls; "
                "the specification forbids candidate-only tom machine IDs"
            ),
            channel=channel,
            user_channel=user_channel,
        )
    if selection == STATUS_PRESERVE_REFERENCE:
        return _status_field(
            device=RUSH01_DEVICE_RYTM,
            track=track,
            path=path,
            requested=machine_name,
            status=STATUS_PRESERVE_REFERENCE,
            reason="machine selection explicitly preserves the active-kit value",
            channel=channel,
            user_channel=user_channel,
            evidence="corrected RUSH01 semantic specification",
        )
    if selection != "catalog_verified":
        return _status_field(
            device=RUSH01_DEVICE_RYTM,
            track=track,
            path=path,
            requested=machine_name,
            status=STATUS_INVALID_SPEC_FIELD,
            reason="machine.selection must be catalog_verified, preserve_reference, or manual_setup_required",
            channel=channel,
            user_channel=user_channel,
            evidence="RUSH01 machine-selection policy",
        )
    mapping = ANALOG_RYTM_CC_BY_SECTION_AND_PARAMETER[("COMMON", "Track Machine Type")]
    return _ready_field_from_address(
        device=RUSH01_DEVICE_RYTM,
        track=track,
        path=path,
        requested=machine_name,
        normalized=machine_value,
        cc_msb=mapping.cc_msb,
        cc_lsb=mapping.cc_lsb,
        nrpn_address=_rytm_nrpn_address(mapping),
        channel=channel,
        user_channel=user_channel,
        evidence=(
            f"repository Rytm machine catalog: {machine_name}=CC15 value {machine_value}; "
            "manual-backed Track Machine Type mapping"
        ),
    )


def _compile_rytm_mapping_field(
    *,
    track: str,
    path: str,
    requested: object,
    mapping: AnalogRytmCcMapping,
    channel: int | None,
    user_channel: int | None,
) -> Rush01MidiField:
    evidence = (
        f"manual-backed Analog Rytm {mapping.section}/{mapping.parameter}: "
        f"CC{mapping.cc_msb}, NRPN {mapping.nrpn_msb}:{mapping.nrpn_lsb}"
    )
    if mapping.parameter == "Filter Mode":
        normalized, status, reason = _validated_rytm_filter_mode(requested)
    elif mapping.value_kind == "selector":
        normalized, status, reason = _validated_typed_selector(requested, mapping=mapping)
    else:
        normalized, status, reason = _validated_direct_7bit(requested)
    if status != STATUS_READY or normalized is None:
        return _status_field(
            device=RUSH01_DEVICE_RYTM,
            track=track,
            path=path,
            requested=requested,
            status=status,
            reason=reason,
            channel=channel,
            user_channel=user_channel,
            evidence=evidence,
            message_type=_message_type_for(
                mapping.cc_msb, mapping.cc_lsb, _rytm_nrpn_address(mapping)
            ),
            controller=mapping.cc_msb,
            controller_lsb=mapping.cc_lsb,
            nrpn_address=_rytm_nrpn_address(mapping),
        )
    return _ready_field_from_address(
        device=RUSH01_DEVICE_RYTM,
        track=track,
        path=path,
        requested=requested,
        normalized=normalized,
        cc_msb=mapping.cc_msb,
        cc_lsb=mapping.cc_lsb,
        nrpn_address=_rytm_nrpn_address(mapping),
        channel=channel,
        user_channel=user_channel,
        evidence=evidence,
    )


def _compile_rytm_common_section(
    *,
    track: str,
    section_spec: Mapping[str, object],
    section_path: str,
    bindings: Sequence[Rush01RytmCommonBinding],
    channel: int | None,
    user_channel: int | None,
) -> tuple[Rush01MidiField, ...]:
    fields: list[Rush01MidiField] = []
    known_keys: set[str] = set()
    for candidate in bindings:
        spec_key = candidate.spec_key
        section = candidate.section
        parameter = candidate.parameter
        known_keys.add(spec_key)
        mapping = ANALOG_RYTM_CC_BY_SECTION_AND_PARAMETER[(section, parameter)]
        fields.append(
            _compile_rytm_mapping_field(
                track=track,
                path=f"tracks.{track}.{section_path}.{spec_key}",
                requested=section_spec.get(spec_key),
                mapping=mapping,
                channel=channel,
                user_channel=user_channel,
            )
        )
    for unknown in sorted(set(section_spec) - known_keys):
        fields.append(
            _status_field(
                device=RUSH01_DEVICE_RYTM,
                track=track,
                path=f"tracks.{track}.{section_path}.{unknown}",
                requested=section_spec[unknown],
                status=STATUS_INVALID_SPEC_FIELD,
                reason=f"unsupported Rytm {section_path} specification field",
                channel=channel,
                user_channel=user_channel,
                evidence="RUSH01 fixed-section binding table",
            )
        )
    return tuple(fields)


def _compile_a4_fields(
    spec: Mapping[str, object],
    *,
    channels: Mapping[str, int] | None,
) -> tuple[Rush01MidiField, ...]:
    tracks = _require_mapping(spec.get("tracks"), path="spec.tracks")
    track_levels = _require_mapping(spec.get("track_levels"), path="spec.track_levels")
    build_policy = _require_mapping(spec.get("build_policy"), path="spec.build_policy")
    fields: list[Rush01MidiField] = [
        _manual_field(
            device=RUSH01_DEVICE_A4,
            track=None,
            path="build_policy.kit_name",
            requested=build_policy.get("kit_name"),
            reason="kit naming remains a front-panel step; the compiler never saves a kit",
        )
    ]
    track_level_mapping = ANALOG_FOUR_MANUAL_CC["Track Level"]
    for track in RUSH01_A4_TRACK_ORDER:
        track_spec = _require_mapping(tracks.get(track), path=f"spec.tracks.{track}")
        channel, user_channel = _channel_for(track, channels)
        fields.append(
            _compile_a4_mapping_field(
                track=track,
                path=f"track_levels.{track}",
                requested=track_levels.get(track),
                mapping=track_level_mapping,
                conversion="direct_7bit",
                channel=channel,
                user_channel=user_channel,
            )
        )
        binding_keys_by_section: dict[str, set[str]] = {}
        for binding in RUSH01_A4_BINDINGS:
            binding_keys_by_section.setdefault(binding.section_key, set()).add(binding.field_key)
            section = _require_mapping(
                track_spec.get(binding.section_key),
                path=f"spec.tracks.{track}.{binding.section_key}",
            )
            mapping = (
                ANALOG_FOUR_SYNTH_TRACK_NRPN.get(binding.parameter)
                if binding.parameter is not None
                else None
            )
            fields.append(
                _compile_a4_mapping_field(
                    track=track,
                    path=f"tracks.{track}.{binding.section_key}.{binding.field_key}",
                    requested=section.get(binding.field_key),
                    mapping=mapping,
                    conversion=binding.conversion,
                    channel=channel,
                    user_channel=user_channel,
                )
            )
        for section_key, known_keys in binding_keys_by_section.items():
            section = _require_mapping(
                track_spec.get(section_key), path=f"spec.tracks.{track}.{section_key}"
            )
            for unknown in sorted(set(section) - known_keys):
                fields.append(
                    _status_field(
                        device=RUSH01_DEVICE_A4,
                        track=track,
                        path=f"tracks.{track}.{section_key}.{unknown}",
                        requested=section[unknown],
                        status=STATUS_INVALID_SPEC_FIELD,
                        reason="unsupported Analog Four specification field",
                        channel=channel,
                        user_channel=user_channel,
                        evidence="RUSH01 A4 semantic binding table",
                    )
                )
    return tuple(replace(field, sequence=index) for index, field in enumerate(fields, start=1))


def _compile_a4_mapping_field(
    *,
    track: str,
    path: str,
    requested: object,
    mapping: AnalogFourCcMapping | None,
    conversion: Rush01ConversionKind,
    channel: int | None,
    user_channel: int | None,
) -> Rush01MidiField:
    normalized, status, reason = _convert_a4_value(
        requested,
        mapping=mapping,
        conversion=conversion,
    )
    evidence = _a4_mapping_evidence(mapping, conversion=conversion)
    cc_msb = mapping.cc_msb if mapping is not None else None
    cc_lsb = mapping.cc_lsb if mapping is not None else None
    nrpn_address = _a4_nrpn_address(mapping)
    if status != STATUS_READY or normalized is None:
        return _status_field(
            device=RUSH01_DEVICE_A4,
            track=track,
            path=path,
            requested=requested,
            status=status,
            reason=reason,
            channel=channel,
            user_channel=user_channel,
            evidence=evidence,
            message_type=_message_type_for(cc_msb, cc_lsb, nrpn_address),
            controller=cc_msb,
            controller_lsb=cc_lsb,
            nrpn_address=nrpn_address,
        )
    return _ready_field_from_address(
        device=RUSH01_DEVICE_A4,
        track=track,
        path=path,
        requested=requested,
        normalized=normalized,
        cc_msb=cc_msb,
        cc_lsb=cc_lsb,
        nrpn_address=nrpn_address,
        channel=channel,
        user_channel=user_channel,
        evidence=evidence,
    )


def _convert_a4_value(
    requested: object,
    *,
    mapping: AnalogFourCcMapping | None,
    conversion: Rush01ConversionKind,
) -> tuple[int | None, Rush01FieldStatus, str]:
    if requested == STATUS_PRESERVE_REFERENCE:
        return None, STATUS_PRESERVE_REFERENCE, "field explicitly preserves the active-kit value"
    if conversion == "direct_7bit":
        return _validated_direct_7bit(requested)
    if conversion == "bipolar_7bit":
        if isinstance(requested, bool) or not isinstance(requested, int):
            return None, STATUS_INVALID_SPEC_FIELD, "bipolar display value must be an integer"
        try:
            return (
                signed_screen_to_a4_midi(requested),
                STATUS_READY,
                "repository signed Analog Four display converter",
            )
        except ValueError as exc:
            return None, STATUS_INVALID_SPEC_FIELD, str(exc)
    if conversion == "verified_enum":
        if mapping is None or not isinstance(requested, str):
            return None, STATUS_LEARN_REQUIRED, "typed enum label has no verified raw MIDI value"
        display = ANALOG_FOUR_PARAMETER_DISPLAY[mapping.parameter]
        raw_value = display.value_for_label(requested)
        if raw_value is None or not display.transport_ready:
            return None, STATUS_LEARN_REQUIRED, "typed enum label is absent from the verified table"
        return raw_value, STATUS_READY, "repository Analog Four typed enum table"
    if conversion == "unverified_high_resolution":
        return (
            None,
            STATUS_LEARN_REQUIRED,
            "high-resolution display-to-MIDI conversion is not positively verified",
        )
    if conversion == "unverified_boolean":
        return None, STATUS_LEARN_REQUIRED, "boolean raw MIDI representation is not verified"
    if conversion == "unverified_enum":
        return None, STATUS_LEARN_REQUIRED, "typed enum raw MIDI table is not verified"
    if conversion == "unverified_conversion":
        return None, STATUS_LEARN_REQUIRED, "display-to-MIDI conversion is not verified"
    return None, STATUS_LEARN_REQUIRED, "no documented MIDI address is present in the repository"


def _validated_rytm_filter_mode(
    requested: object,
) -> tuple[int | None, Rush01FieldStatus, str]:
    value = _require_mapping_or_none(requested)
    if value is None:
        return None, STATUS_INVALID_SPEC_FIELD, "Filter Mode must provide typed name and id"
    name = value.get("name")
    raw_id = value.get("id")
    if not isinstance(name, str) or isinstance(raw_id, bool) or not isinstance(raw_id, int):
        return None, STATUS_INVALID_SPEC_FIELD, "Filter Mode must provide typed name and id"
    if FILTER_TYPE_NAMES.get(raw_id) != name:
        return None, STATUS_INVALID_SPEC_FIELD, "Filter Mode name and id disagree"
    return raw_id, STATUS_READY, "repository Filter Mode enum table"


def _validated_typed_selector(
    requested: object,
    *,
    mapping: AnalogRytmCcMapping,
) -> tuple[int | None, Rush01FieldStatus, str]:
    value = _require_mapping_or_none(requested)
    if value is None:
        return (
            None,
            STATUS_LEARN_REQUIRED,
            f"{mapping.parameter} requires a typed enum with verified raw MIDI",
        )
    if value.get("type") != "enum":
        return None, STATUS_INVALID_SPEC_FIELD, f"{mapping.parameter} must declare type: enum"
    if value.get("requested") == STATUS_PRESERVE_REFERENCE:
        return (
            None,
            STATUS_PRESERVE_REFERENCE,
            "typed enum explicitly preserves the active-kit value",
        )
    raw_midi = value.get("raw_midi")
    if raw_midi == STATUS_LEARN_REQUIRED:
        return None, STATUS_LEARN_REQUIRED, "typed enum raw MIDI value requires calibration"
    if isinstance(raw_midi, bool) or not isinstance(raw_midi, int):
        return None, STATUS_LEARN_REQUIRED, "typed enum raw MIDI value is not supplied"
    if not mapping.value_min <= raw_midi <= mapping.value_max:
        return (
            None,
            STATUS_INVALID_SPEC_FIELD,
            f"typed enum raw MIDI value must be in {mapping.value_min}..{mapping.value_max}",
        )
    return raw_midi, STATUS_READY, "typed raw MIDI enum supplied explicitly by the specification"


def _validated_direct_7bit(
    requested: object,
) -> tuple[int | None, Rush01FieldStatus, str]:
    if requested == STATUS_PRESERVE_REFERENCE:
        return None, STATUS_PRESERVE_REFERENCE, "field explicitly preserves the active-kit value"
    if isinstance(requested, bool) or not isinstance(requested, int):
        return None, STATUS_INVALID_SPEC_FIELD, "direct MIDI value must be an integer in 0..127"
    if not _MIDI_DATA_MIN <= requested <= _MIDI_DATA_MAX:
        return None, STATUS_INVALID_SPEC_FIELD, "direct MIDI value must be an integer in 0..127"
    return requested, STATUS_READY, "direct unambiguous 7-bit MIDI value"


def _ready_field_from_address(
    *,
    device: Rush01Device,
    track: str,
    path: str,
    requested: object,
    normalized: int,
    cc_msb: int | None,
    cc_lsb: int | None,
    nrpn_address: tuple[int, int] | None,
    channel: int | None,
    user_channel: int | None,
    evidence: str,
) -> Rush01MidiField:
    message_type = _message_type_for(cc_msb, cc_lsb, nrpn_address)
    if message_type is None:
        return _status_field(
            device=device,
            track=track,
            path=path,
            requested=requested,
            status=STATUS_LEARN_REQUIRED,
            reason="no documented MIDI address is available",
            channel=channel,
            user_channel=user_channel,
            evidence=evidence,
        )
    messages: tuple[MidiByteMessage, ...] | None = None
    configuration_issue: str | None = None
    if channel is None:
        configuration_issue = "track channel must be configured before byte encoding"
    elif message_type == MESSAGE_CC:
        messages = encode_cc_message(channel, cast(int, cc_msb), normalized)
    elif message_type == MESSAGE_CC14:
        messages = encode_cc14_messages(
            channel,
            cast(int, cc_msb),
            cast(int, cc_lsb),
            normalized,
        )
    else:
        address = cast(tuple[int, int], nrpn_address)
        messages = encode_nrpn_messages(
            channel,
            address[0],
            address[1],
            normalized,
        )
    return Rush01MidiField(
        sequence=0,
        device=device,
        track=track,
        semantic_path=path,
        requested_value=requested,
        normalized_midi_value=normalized,
        message_type=message_type,
        channel=channel,
        user_channel=user_channel,
        controller=cc_msb,
        controller_lsb=cc_lsb,
        nrpn_address=nrpn_address,
        ordered_midi_bytes=messages,
        mapping_evidence=evidence,
        status=STATUS_READY,
        reason="ready for dry-run MIDI plan",
        configuration_issue=configuration_issue,
    )


def _status_field(
    *,
    device: Rush01Device,
    track: str | None,
    path: str,
    requested: object,
    status: Rush01FieldStatus,
    reason: str,
    channel: int | None,
    user_channel: int | None,
    evidence: str,
    message_type: Rush01MessageType | None = None,
    controller: int | None = None,
    controller_lsb: int | None = None,
    nrpn_address: tuple[int, int] | None = None,
) -> Rush01MidiField:
    return Rush01MidiField(
        sequence=0,
        device=device,
        track=track,
        semantic_path=path,
        requested_value=requested,
        normalized_midi_value=None,
        message_type=message_type,
        channel=channel,
        user_channel=user_channel,
        controller=controller,
        controller_lsb=controller_lsb,
        nrpn_address=nrpn_address,
        ordered_midi_bytes=None,
        mapping_evidence=evidence,
        status=status,
        reason=reason,
    )


def _manual_field(
    *,
    device: Rush01Device,
    track: str | None,
    path: str,
    requested: object,
    reason: str,
    channel: int | None = None,
    user_channel: int | None = None,
) -> Rush01MidiField:
    return _status_field(
        device=device,
        track=track,
        path=path,
        requested=requested,
        status=STATUS_MANUAL_SETUP_REQUIRED,
        reason=reason,
        channel=channel,
        user_channel=user_channel,
        evidence="explicit RUSH01 manual-setup policy",
    )


def _message_type_for(
    cc_msb: int | None,
    cc_lsb: int | None,
    nrpn_address: tuple[int, int] | None,
) -> Rush01MessageType | None:
    if cc_msb is not None and cc_lsb is not None:
        return MESSAGE_CC14
    if cc_msb is not None:
        return MESSAGE_CC
    if nrpn_address is not None:
        return MESSAGE_NRPN
    return None


def _a4_mapping_evidence(
    mapping: AnalogFourCcMapping | None,
    *,
    conversion: Rush01ConversionKind,
) -> str:
    if mapping is None:
        return f"no Analog Four manual mapping; conversion policy={conversion}"
    nrpn = _a4_nrpn_address(mapping)
    return (
        f"manual-backed Analog Four {mapping.section}/{mapping.parameter}: "
        f"CC={mapping.cc_msb}, CC-LSB={mapping.cc_lsb}, NRPN={nrpn}; "
        f"conversion policy={conversion}"
    )


def _a4_nrpn_address(mapping: AnalogFourCcMapping | None) -> tuple[int, int] | None:
    if mapping is None or mapping.nrpn_msb is None or mapping.nrpn_lsb is None:
        return None
    return (mapping.nrpn_msb, mapping.nrpn_lsb)


def _rytm_nrpn_address(mapping: AnalogRytmCcMapping) -> tuple[int, int] | None:
    if mapping.nrpn_msb is None or mapping.nrpn_lsb is None:
        return None
    return (mapping.nrpn_msb, mapping.nrpn_lsb)


def _rytm_machine_profile_by_label(label: str) -> RytmMachineProfile:
    for profile in RYTM_MACHINE_PROFILES:
        if profile.label == label:
            return profile
    raise ValueError(f"unknown Rytm machine name: {label}")


def _filter_and_resequence_fields(
    fields: Sequence[Rush01MidiField],
    *,
    track: str | None,
    parameter: str | None,
) -> tuple[Rush01MidiField, ...]:
    selected = tuple(
        field
        for field in fields
        if (track is None or field.track == track)
        and (parameter is None or field.semantic_path == parameter)
    )
    return tuple(replace(field, sequence=index) for index, field in enumerate(selected, start=1))


def _summarize(fields: Sequence[Rush01MidiField]) -> Rush01MidiPlanSummary:
    counts = {
        status: sum(1 for field in fields if field.status == status) for status in _STATUS_ORDER
    }
    return Rush01MidiPlanSummary(
        total_fields=len(fields),
        ready_fields=counts[STATUS_READY],
        preserve_reference_fields=counts[STATUS_PRESERVE_REFERENCE],
        manual_setup_fields=counts[STATUS_MANUAL_SETUP_REQUIRED],
        learn_required_fields=counts[STATUS_LEARN_REQUIRED],
        invalid_spec_fields=counts[STATUS_INVALID_SPEC_FIELD],
        configured_ready_fields=sum(
            1
            for field in fields
            if field.status == STATUS_READY and field.ordered_midi_bytes is not None
        ),
        transport_message_count=sum(
            len(field.ordered_midi_bytes or ()) for field in fields if field.status == STATUS_READY
        ),
    )


def _field_to_dict(field: Rush01MidiField) -> dict[str, object]:
    return {
        "sequence": field.sequence,
        "device": field.device,
        "track": field.track,
        "semantic_path": field.semantic_path,
        "requested_value": _json_value(field.requested_value),
        "normalized_midi_value": field.normalized_midi_value,
        "message_type": field.message_type,
        "channel": field.channel,
        "user_channel": field.user_channel,
        "controller": field.controller,
        "controller_lsb": field.controller_lsb,
        "nrpn_address": list(field.nrpn_address) if field.nrpn_address is not None else None,
        "ordered_midi_bytes": (
            [list(message) for message in field.ordered_midi_bytes]
            if field.ordered_midi_bytes is not None
            else None
        ),
        "mapping_evidence": field.mapping_evidence,
        "status": field.status,
        "reason": field.reason,
        "configuration_issue": field.configuration_issue,
    }


def _json_value(value: object) -> object:
    if isinstance(value, Mapping):
        return {str(key): _json_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_value(item) for item in value]
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    return str(value)


def _channel_for(
    track: str,
    channels: Mapping[str, int] | None,
) -> tuple[int | None, int | None]:
    if channels is None:
        return None, None
    if track not in channels:
        raise ValueError(f"configured channel is missing for track {track}")
    user_channel = channels[track]
    return user_channel_to_midi(user_channel), user_channel


def _validated_device(device: str) -> Rush01Device:
    if device == RUSH01_DEVICE_RYTM:
        return RUSH01_DEVICE_RYTM
    if device == RUSH01_DEVICE_A4:
        return RUSH01_DEVICE_A4
    raise ValueError("device must be exactly one of: rytm, a4")


def _is_unfilled_config_value(value: str) -> bool:
    return "replace" in value.casefold()


def _track_order(device: Rush01Device) -> tuple[str, ...]:
    return RUSH01_RYTM_TRACK_ORDER if device == RUSH01_DEVICE_RYTM else RUSH01_A4_TRACK_ORDER


def _validated_track_filter(device: Rush01Device, track: str | None) -> str | None:
    if track is None:
        return None
    if track not in _track_order(device):
        raise ValueError(f"track must be one of: {', '.join(_track_order(device))}")
    return track


def _validate_spec_device(spec: Mapping[str, object], device: Rush01Device) -> None:
    device_spec = _require_mapping(spec.get("device"), path="spec.device")
    model = device_spec.get("model")
    expected = _RYTM_MODEL if device == RUSH01_DEVICE_RYTM else _A4_MODEL
    if model != expected:
        raise ValueError(f"selected {device} device does not match specification model {model!r}")


def _required_string(mapping: Mapping[str, object], key: str, *, path: str) -> str:
    value = mapping.get(key)
    if not isinstance(value, str) or not value:
        raise ValueError(f"{path} must be a non-empty string")
    return value


def _require_mapping(value: object, *, path: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{path} must be a mapping")
    normalized: dict[str, object] = {}
    for key, item in value.items():
        if not isinstance(key, str):
            raise ValueError(f"{path} keys must be strings")
        normalized[key] = item
    return MappingProxyType(normalized)


def _require_mapping_or_none(value: object) -> Mapping[str, object] | None:
    if not isinstance(value, Mapping):
        return None
    normalized: dict[str, object] = {}
    for key, item in value.items():
        if not isinstance(key, str):
            return None
        normalized[key] = item
    return MappingProxyType(normalized)


def _validate_midi_channel(channel: int) -> None:
    if isinstance(channel, bool) or not isinstance(channel, int):
        raise ValueError("MIDI channel must be an integer in 0..15")
    if not _MIDI_CHANNEL_MIN <= channel <= _MIDI_CHANNEL_MAX:
        raise ValueError("MIDI channel must be an integer in 0..15")


def _validate_midi_data(value: int, *, label: str) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 127:
        raise ValueError(f"{label} must be an integer in 0..127")


__all__ = [
    "MESSAGE_CC",
    "MESSAGE_CC14",
    "MESSAGE_NRPN",
    "RUSH01_DEVICE_A4",
    "RUSH01_DEVICE_RYTM",
    "RUSH01_PLAN_VERSION",
    "STATUS_INVALID_SPEC_FIELD",
    "STATUS_LEARN_REQUIRED",
    "STATUS_MANUAL_SETUP_REQUIRED",
    "STATUS_PRESERVE_REFERENCE",
    "STATUS_READY",
    "MidiByteMessage",
    "Rush01DeviceConfig",
    "Rush01FieldStatus",
    "Rush01MessageType",
    "Rush01MidiField",
    "Rush01MidiPlan",
    "Rush01MidiPlanSummary",
    "compile_rush01_midi_plan",
    "encode_cc14_messages",
    "encode_cc_message",
    "encode_nrpn_messages",
    "parse_rush01_device_config",
    "rush01_midi_plan_to_dict",
    "user_channel_to_midi",
    "validate_rush01_plan_safety",
]
