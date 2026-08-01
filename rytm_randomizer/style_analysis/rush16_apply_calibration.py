"""Passive model for guarded RUSH16 active-kit apply calibration."""

from __future__ import annotations

import json
import re
from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from hashlib import sha256
from pathlib import Path
from types import MappingProxyType
from typing import Final, Literal, TypeAlias, cast

from ..data import RYTM_MACHINE_PROFILES
from ..devices.strategies import ANALOG_FOUR_KIT_CODEC, ANALOG_RYTM_KIT_CODEC
from .rush01_midi_compiler import (
    MESSAGE_CC,
    MESSAGE_CC14,
    MESSAGE_NRPN,
    RUSH01_DEVICE_A4,
    RUSH01_DEVICE_RYTM,
    STATUS_INVALID_SPEC_FIELD,
    STATUS_LEARN_REQUIRED,
    STATUS_MANUAL_SETUP_REQUIRED,
    STATUS_PRESERVE_REFERENCE,
    STATUS_READY,
    VALUE_DOMAIN_7BIT,
    VALUE_DOMAIN_14BIT,
    MidiByteMessage,
    Rush01Device,
    Rush01DeviceConfig,
    Rush01MessageType,
    Rush01MidiField,
    Rush01MidiPlan,
    Rush01MidiPlanSummary,
    Rush01ValueDomain,
    compile_rush01_midi_plan,
    encode_cc14_messages,
    encode_cc_message,
    encode_nrpn_messages,
    user_channel_to_midi,
    validate_rush01_plan_safety,
)
from .rush16_anchor_audition import rush16_hardware_blockers, rush16_value_at_path

CalibrationKind: TypeAlias = Literal[
    "selector", "boolean", "bipolar", "continuous", "high_resolution", "machine"
]
PromotionMode: TypeAlias = Literal["lookup", "affine", "unsupported"]
CalibrationEvidenceKind: TypeAlias = Literal[
    "display_discovery", "display_repeat", "saved_kit_differential"
]

RUSH16_CALIBRATION_VERSION: Final[str] = "rush16-apply-calibration-v3"
_LEGACY_PROMOTION_CHECKPOINT_VERSION: Final[str] = "rush16-apply-calibration-v2"
_PROMOTION_CHECKPOINT_VERSIONS: Final[frozenset[str]] = frozenset(
    {_LEGACY_PROMOTION_CHECKPOINT_VERSION, RUSH16_CALIBRATION_VERSION}
)
_RYTM_MACHINE_CC: Final[int] = 15
_PROBE_7BIT: Final[tuple[int, ...]] = (0, 1, 64, 96, 127)
_PROBE_BIPOLAR: Final[tuple[int, ...]] = (0, 63, 64, 65, 127)
_PROBE_14BIT: Final[tuple[int, ...]] = (0, 1, 8191, 8192, 12345, 16383)
_PROBE_BOOLEAN: Final[tuple[int, ...]] = (0, 127)
_A4_COARSE_TUNE_PROBES: Final[tuple[int, ...]] = (63, 64, 65, 75, 76, 77, 82, 83, 84)
_A4_FINE_TUNE_PROBES: Final[tuple[int, ...]] = (56, 57, 58, 59, 63, 64, 65)
_AFFINE_INFERENCE_KINDS: Final[frozenset[CalibrationKind]] = frozenset(
    {"bipolar", "continuous", "high_resolution"}
)


@dataclass(frozen=True)
class Rush16CalibrationAddress:
    """One positively documented MIDI address used for a probe."""

    message_type: Rush01MessageType
    value_domain: Rush01ValueDomain
    controller: int | None = None
    controller_lsb: int | None = None
    nrpn_address: tuple[int, int] | None = None


@dataclass(frozen=True)
class Rush16CalibrationWitness:
    """One track/address observation used to confirm a converter family."""

    role: str
    spec_filename: str
    semantic_path: str
    track: str
    address: Rush16CalibrationAddress


@dataclass(frozen=True)
class Rush16CalibrationTarget:
    """One blocked anchor value a promoted converter must encode exactly."""

    spec_filename: str
    semantic_path: str
    requested_value: object
    requested_fingerprint: str


@dataclass(frozen=True)
class Rush16CalibrationFamily:
    """One reusable converter family and its complete probe contract."""

    family_id: str
    device: Rush01Device
    label: str
    converter_kind: CalibrationKind
    promotion_mode: PromotionMode
    path_pattern: str
    candidates: tuple[int, ...]
    witnesses: tuple[Rush16CalibrationWitness, ...]
    evidence_source: str
    supported: bool
    targets: tuple[Rush16CalibrationTarget, ...] = ()


@dataclass(frozen=True)
class Rush16CalibrationStep:
    """One outbound candidate and the exact packets previewed to the operator."""

    step_id: str
    sequence: int
    family_id: str
    witness_role: str
    spec_filename: str
    semantic_path: str
    track: str
    raw_value: int
    value_domain: Rush01ValueDomain
    context_messages: tuple[MidiByteMessage, ...]
    candidate_messages: tuple[MidiByteMessage, ...]

    @property
    def ordered_messages(self) -> tuple[MidiByteMessage, ...]:
        return self.context_messages + self.candidate_messages


@dataclass(frozen=True)
class Rush16CalibrationPlan:
    """Complete deterministic observation plan for one device."""

    version: str
    device: Rush01Device
    output_port: str
    input_port: str
    families: tuple[Rush16CalibrationFamily, ...]
    steps: tuple[Rush16CalibrationStep, ...]
    blocker_counts_before: Mapping[str, int]
    filter2_resonance_evidence: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "blocker_counts_before",
            MappingProxyType(dict(self.blocker_counts_before)),
        )


@dataclass(frozen=True)
class Rush16CalibrationProgress:
    """Checkpoint-derived operator progress."""

    families_complete: int
    families_remaining: int
    observations_complete: int
    observations_remaining: int
    next_family_id: str | None
    next_family_observations_remaining: int
    deferred_large_selector_families: int
    blocker_counts_before: Mapping[str, int]
    blocker_counts_after: Mapping[str, int]

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "blocker_counts_before",
            MappingProxyType(dict(self.blocker_counts_before)),
        )
        object.__setattr__(
            self,
            "blocker_counts_after",
            MappingProxyType(dict(self.blocker_counts_after)),
        )


@dataclass(frozen=True)
class _FamilyTemplate:
    family_id: str
    device: Rush01Device
    label: str
    converter_kind: CalibrationKind
    promotion_mode: PromotionMode
    path_pattern: str
    candidates: tuple[int, ...]
    witnesses: tuple[Rush16CalibrationWitness, ...]
    evidence_source: str
    supported: bool = True


def _address_cc(controller: int) -> Rush16CalibrationAddress:
    return Rush16CalibrationAddress(MESSAGE_CC, VALUE_DOMAIN_7BIT, controller=controller)


def _address_cc14(controller: int, controller_lsb: int) -> Rush16CalibrationAddress:
    return Rush16CalibrationAddress(
        MESSAGE_CC14,
        VALUE_DOMAIN_14BIT,
        controller=controller,
        controller_lsb=controller_lsb,
    )


def _address_nrpn(lsb: int) -> Rush16CalibrationAddress:
    return Rush16CalibrationAddress(
        MESSAGE_NRPN,
        VALUE_DOMAIN_7BIT,
        nrpn_address=(1, lsb),
    )


def _witness(
    role: str,
    spec_filename: str,
    semantic_path: str,
    track: str,
    address: Rush16CalibrationAddress,
) -> Rush16CalibrationWitness:
    return Rush16CalibrationWitness(role, spec_filename, semantic_path, track, address)


_RYTM_COMMON_SPEC: Final[str] = "01_DRY_AUTHORITY_RYTM.yaml"
_RYTM_RAW_SPEC: Final[str] = "16_SIGNATURE_APEX_RYTM.yaml"
_RYTM_CHIP_SPEC: Final[str] = "08_METAL_LOCK_RYTM.yaml"
_A4_SPEC: Final[str] = "01_DRY_AUTHORITY_A4.yaml"


def _repeat_witnesses(
    spec_filename: str,
    semantic_path: str,
    track: str,
    address: Rush16CalibrationAddress,
) -> tuple[Rush16CalibrationWitness, ...]:
    return (
        _witness("primary", spec_filename, semantic_path, track, address),
        _witness("repeat", spec_filename, semantic_path, track, address),
    )


_FAMILY_TEMPLATES: Final[tuple[_FamilyTemplate, ...]] = (
    _FamilyTemplate(
        "rytm_bd_sharp_waveform",
        RUSH01_DEVICE_RYTM,
        "BD Sharp waveform",
        "selector",
        "lookup",
        r"^tracks\.BD\.synth\.Waveform$",
        tuple(range(12)),
        _repeat_witnesses(_RYTM_COMMON_SPEC, "tracks.BD.synth.Waveform", "BD", _address_cc(23)),
        "Analog Rytm catalog: BD Sharp Waveform CC23 / NRPN 1:7, selector 0..11",
    ),
    _FamilyTemplate(
        "rytm_ch_osc_reset",
        RUSH01_DEVICE_RYTM,
        "CH oscillator reset",
        "boolean",
        "lookup",
        r"^tracks\.CH\.synth\.Osc Reset$",
        _PROBE_BOOLEAN,
        _repeat_witnesses(_RYTM_COMMON_SPEC, "tracks.CH.synth.Osc Reset", "CH", _address_cc(21)),
        "Analog Rytm catalog: HH Basic Osc Reset CC21 / NRPN 1:5, 7-bit boolean endpoints",
    ),
    _FamilyTemplate(
        "rytm_cy_cymbal_type",
        RUSH01_DEVICE_RYTM,
        "CY Ride cymbal type",
        "selector",
        "lookup",
        r"^tracks\.CY\.synth\.Cymbal Type$",
        tuple(range(4)),
        _repeat_witnesses(_RYTM_COMMON_SPEC, "tracks.CY.synth.Cymbal Type", "CY", _address_cc(20)),
        "Analog Rytm catalog: CY Ride Cymbal Type CC20 / NRPN 1:4, selector 0..3",
    ),
    _FamilyTemplate(
        "rytm_xt_classic_machine",
        RUSH01_DEVICE_RYTM,
        "XT Classic machine selection",
        "machine",
        "lookup",
        r"^tracks\.(LT|MT|HT)\.machine$",
        (8,),
        tuple(
            _witness(
                f"{track.lower()}_track",
                _RYTM_COMMON_SPEC,
                f"tracks.{track}.machine",
                track,
                _address_cc(_RYTM_MACHINE_CC),
            )
            for track in ("LT", "MT", "HT")
        ),
        "Rytm machine catalog XT Classic=8; manual-backed Track Machine Type CC15 / NRPN 1:103",
    ),
    _FamilyTemplate(
        "rytm_sy_raw_waveform_1",
        RUSH01_DEVICE_RYTM,
        "SY Raw waveform 1",
        "selector",
        "lookup",
        r"^tracks\.SD\.synth\.Waveform 1$",
        tuple(range(7)),
        _repeat_witnesses(_RYTM_RAW_SPEC, "tracks.SD.synth.Waveform 1", "SD", _address_cc(21)),
        "Analog Rytm catalog: SY Raw Waveform 1 CC21 / NRPN 1:5, selector 0..6",
    ),
    _FamilyTemplate(
        "rytm_sy_raw_waveform_2",
        RUSH01_DEVICE_RYTM,
        "SY Raw waveform 2",
        "selector",
        "lookup",
        r"^tracks\.SD\.synth\.Waveform 2$",
        (0, 1),
        _repeat_witnesses(_RYTM_RAW_SPEC, "tracks.SD.synth.Waveform 2", "SD", _address_cc(22)),
        "Analog Rytm catalog: SY Raw Waveform 2 CC22 / NRPN 1:6, selector 0..1",
    ),
    _FamilyTemplate(
        "rytm_sy_chip_waveform",
        RUSH01_DEVICE_RYTM,
        "SY Chip waveform",
        "selector",
        "lookup",
        r"^tracks\.SD\.synth\.Waveform$",
        _PROBE_7BIT,
        _repeat_witnesses(_RYTM_CHIP_SPEC, "tracks.SD.synth.Waveform", "SD", _address_cc(19)),
        "Analog Rytm catalog: SY Chip Waveform CC19 / NRPN 1:3, documented 7-bit domain",
    ),
)


def _a4_pair(
    path_one: str,
    path_two: str,
    address_one: Rush16CalibrationAddress,
    address_two: Rush16CalibrationAddress,
) -> tuple[Rush16CalibrationWitness, ...]:
    return (
        _witness("representative_t1", _A4_SPEC, path_one, "T1", address_one),
        _witness("confirmation_t2", _A4_SPEC, path_two, "T2", address_two),
    )


_A4_FAMILY_TEMPLATES: Final[tuple[_FamilyTemplate, ...]] = (
    _FamilyTemplate(
        "a4_oscillator_coarse_tune",
        RUSH01_DEVICE_A4,
        "oscillator coarse tune",
        "bipolar",
        "lookup",
        r"^tracks\.T[1-4]\.oscillator_[12]\.coarse_tune_semitones$",
        _A4_COARSE_TUNE_PROBES,
        _a4_pair(
            "tracks.T1.oscillator_1.coarse_tune_semitones",
            "tracks.T2.oscillator_2.coarse_tune_semitones",
            _address_cc(16),
            _address_cc(17),
        ),
        "Analog Four hardware evidence: OSC1 coarse tune is CC16 and OSC2 coarse tune is CC17; "
        "the companion CCs control a separate fine-tune display value",
    ),
    _FamilyTemplate(
        "a4_oscillator_fine_tune",
        RUSH01_DEVICE_A4,
        "oscillator fine tune",
        "bipolar",
        "lookup",
        r"^tracks\.T[1-4]\.oscillator_[12]\.fine_tune_cents$",
        _A4_FINE_TUNE_PROBES,
        _a4_pair(
            "tracks.T1.oscillator_1.fine_tune_cents",
            "tracks.T2.oscillator_2.fine_tune_cents",
            _address_cc(48),
            _address_cc(49),
        ),
        "Analog Four hardware evidence: OSC1 fine tune is CC48 and OSC2 fine tune is CC49; "
        "the companion CCs control a separate coarse-tune display value",
    ),
    _FamilyTemplate(
        "a4_linear_detune",
        RUSH01_DEVICE_A4,
        "linear detune",
        "bipolar",
        "affine",
        r"^tracks\.T[1-4]\.oscillator_[12]\.linear_detune_hz$",
        _PROBE_BIPOLAR,
        _a4_pair(
            "tracks.T1.oscillator_1.linear_detune_hz",
            "tracks.T2.oscillator_2.linear_detune_hz",
            _address_nrpn(2),
            _address_nrpn(22),
        ),
        "Analog Four manual-backed OSC1 Detune NRPN 1:2 and OSC2 Detune NRPN 1:22",
    ),
    _FamilyTemplate(
        "a4_keytracking",
        RUSH01_DEVICE_A4,
        "keytracking",
        "boolean",
        "lookup",
        r"^tracks\.T[1-4]\.oscillator_[12]\.keytrack$",
        _PROBE_BOOLEAN,
        _a4_pair(
            "tracks.T1.oscillator_1.keytrack",
            "tracks.T2.oscillator_2.keytrack",
            _address_nrpn(3),
            _address_nrpn(23),
        ),
        "Analog Four manual-backed OSC1 Keytracking NRPN 1:3 and OSC2 Keytracking NRPN 1:23",
    ),
    _FamilyTemplate(
        "a4_oscillator_waveform",
        RUSH01_DEVICE_A4,
        "oscillator waveform",
        "selector",
        "lookup",
        r"^tracks\.T[1-4]\.oscillator_[12]\.waveform$",
        tuple(range(128)),
        _a4_pair(
            "tracks.T1.oscillator_1.waveform",
            "tracks.T2.oscillator_2.waveform",
            _address_cc(70),
            _address_cc(79),
        ),
        "Analog Four manual-backed OSC1 Waveform CC70 and OSC2 Waveform CC79; raw enum table unverified",
    ),
    _FamilyTemplate(
        "a4_sub_oscillator",
        RUSH01_DEVICE_A4,
        "sub oscillator",
        "selector",
        "lookup",
        r"^tracks\.T[1-4]\.oscillator_[12]\.sub_oscillator$",
        tuple(range(128)),
        _a4_pair(
            "tracks.T1.oscillator_1.sub_oscillator",
            "tracks.T2.oscillator_2.sub_oscillator",
            _address_cc(71),
            _address_cc(80),
        ),
        "Analog Four manual-backed OSC1 Sub Oscillator CC71 and OSC2 Sub Oscillator CC80; raw enum table unverified",
    ),
    _FamilyTemplate(
        "a4_pulse_width",
        RUSH01_DEVICE_A4,
        "pulse width",
        "bipolar",
        "affine",
        r"^tracks\.T[1-4]\.oscillator_[12]\.pulse_width$",
        _PROBE_BIPOLAR,
        _a4_pair(
            "tracks.T1.oscillator_1.pulse_width",
            "tracks.T2.oscillator_2.pulse_width",
            _address_cc(72),
            _address_cc(81),
        ),
        "Analog Four manual-backed OSC1 Pulse Width CC72 and OSC2 Pulse Width CC81",
    ),
    _FamilyTemplate(
        "a4_osc1_am",
        RUSH01_DEVICE_A4,
        "OSC1 AM",
        "boolean",
        "lookup",
        r"^tracks\.T[1-4]\.oscillator_common\.osc1_am$",
        _PROBE_BOOLEAN,
        _a4_pair(
            "tracks.T1.oscillator_common.osc1_am",
            "tracks.T2.oscillator_common.osc1_am",
            _address_nrpn(30),
            _address_nrpn(30),
        ),
        "Analog Four manual-backed OSC1 AM NRPN 1:30",
    ),
    _FamilyTemplate(
        "a4_osc2_am",
        RUSH01_DEVICE_A4,
        "OSC2 AM",
        "boolean",
        "lookup",
        r"^tracks\.T[1-4]\.oscillator_common\.osc2_am$",
        _PROBE_BOOLEAN,
        _a4_pair(
            "tracks.T1.oscillator_common.osc2_am",
            "tracks.T2.oscillator_common.osc2_am",
            _address_nrpn(35),
            _address_nrpn(35),
        ),
        "Analog Four manual-backed OSC2 AM NRPN 1:35",
    ),
    _FamilyTemplate(
        "a4_oscillator_retrigger",
        RUSH01_DEVICE_A4,
        "oscillator retrigger",
        "boolean",
        "lookup",
        r"^tracks\.T[1-4]\.oscillator_common\.oscillator_retrigger$",
        _PROBE_BOOLEAN,
        _a4_pair(
            "tracks.T1.oscillator_common.oscillator_retrigger",
            "tracks.T2.oscillator_common.oscillator_retrigger",
            _address_nrpn(36),
            _address_nrpn(36),
        ),
        "Analog Four manual-backed Oscillator Retrigger NRPN 1:36",
    ),
    _FamilyTemplate(
        "a4_sync_mode",
        RUSH01_DEVICE_A4,
        "sync mode",
        "selector",
        "lookup",
        r"^tracks\.T[1-4]\.oscillator_common\.sync_mode$",
        tuple(range(128)),
        _a4_pair(
            "tracks.T1.oscillator_common.sync_mode",
            "tracks.T2.oscillator_common.sync_mode",
            _address_nrpn(31),
            _address_nrpn(31),
        ),
        "Analog Four manual-backed Sync Mode NRPN 1:31; raw enum table unverified",
    ),
    _FamilyTemplate(
        "a4_noise_color",
        RUSH01_DEVICE_A4,
        "noise color",
        "bipolar",
        "unsupported",
        r"^tracks\.T[1-4]\.noise\.color$",
        (),
        (),
        "No documented Noise Color MIDI address exists in the repository",
        False,
    ),
    _FamilyTemplate(
        "a4_filter_1_frequency",
        RUSH01_DEVICE_A4,
        "Filter 1 frequency",
        "high_resolution",
        "affine",
        r"^tracks\.T[1-4]\.filter_1\.frequency$",
        _PROBE_14BIT,
        _a4_pair(
            "tracks.T1.filter_1.frequency",
            "tracks.T2.filter_1.frequency",
            _address_cc14(18, 50),
            _address_cc14(18, 50),
        ),
        "Analog Four manual-backed Filter 1 Frequency CC18/50 NRPN 1:40",
    ),
    _FamilyTemplate(
        "a4_filter_2_frequency",
        RUSH01_DEVICE_A4,
        "Filter 2 frequency",
        "high_resolution",
        "affine",
        r"^tracks\.T[1-4]\.filter_2\.frequency$",
        _PROBE_14BIT,
        _a4_pair(
            "tracks.T1.filter_2.frequency",
            "tracks.T2.filter_2.frequency",
            _address_cc14(19, 51),
            _address_cc14(19, 51),
        ),
        "Analog Four manual-backed Filter 2 Frequency CC19/51 NRPN 1:45",
    ),
    _FamilyTemplate(
        "a4_filter_envelope_depth",
        RUSH01_DEVICE_A4,
        "filter-envelope depth",
        "bipolar",
        "affine",
        r"^tracks\.T[1-4]\.filter_1\.envelope_depth$",
        _PROBE_BIPOLAR,
        _a4_pair(
            "tracks.T1.filter_1.envelope_depth",
            "tracks.T2.filter_1.envelope_depth",
            _address_cc(102),
            _address_cc(102),
        ),
        "Analog Four manual-backed Filter 1 Envelope Amount CC102 NRPN 1:44",
    ),
    _FamilyTemplate(
        "a4_filter_2_type",
        RUSH01_DEVICE_A4,
        "Filter 2 type",
        "selector",
        "lookup",
        r"^tracks\.T[1-4]\.filter_2\.type$",
        tuple(range(7)),
        _a4_pair(
            "tracks.T1.filter_2.type",
            "tracks.T2.filter_2.type",
            _address_nrpn(47),
            _address_nrpn(47),
        ),
        "Analog Four manual-backed Filter 2 Type NRPN 1:47; display table documents raw 0..6",
    ),
    _FamilyTemplate(
        "a4_amp_envelope_shape",
        RUSH01_DEVICE_A4,
        "amp-envelope shape",
        "selector",
        "lookup",
        r"^tracks\.T[1-4]\.amp\.envelope_shape$",
        tuple(range(3)),
        _a4_pair(
            "tracks.T1.amp.envelope_shape",
            "tracks.T2.amp.envelope_shape",
            _address_nrpn(54),
            _address_nrpn(54),
        ),
        "Analog Four manual-backed Amp Envelope Shape NRPN 1:54; display table documents raw 0..2",
    ),
    _FamilyTemplate(
        "a4_filter_envelope_shape",
        RUSH01_DEVICE_A4,
        "filter-envelope shape",
        "selector",
        "lookup",
        r"^tracks\.T[1-4]\.filter_envelope\.envelope_shape$",
        tuple(range(3)),
        _a4_pair(
            "tracks.T1.filter_envelope.envelope_shape",
            "tracks.T2.filter_envelope.envelope_shape",
            _address_nrpn(64),
            _address_nrpn(64),
        ),
        "Analog Four manual-backed Filter Envelope Shape NRPN 1:64; display table documents raw 0..2",
    ),
)


def build_rush16_calibration_plan(
    device: str,
    specs: Mapping[str, object],
    *,
    config: Rush01DeviceConfig,
) -> Rush16CalibrationPlan:
    """Build all required probes without opening a MIDI backend or port."""

    if device not in {RUSH01_DEVICE_RYTM, RUSH01_DEVICE_A4}:
        raise ValueError("RUSH16 calibration device must be rytm or a4")
    normalized_device = cast(Rush01Device, device)
    if config.device != normalized_device:
        raise ValueError("RUSH16 calibration config device does not match")
    if config.input_port is None:
        raise ValueError(f"config.{device}.input_port is required for calibration KIT captures")
    device_specs = {
        name: spec for name, spec in specs.items() if _spec_device(spec) == normalized_device
    }
    if len(device_specs) != 4:
        raise ValueError(f"RUSH16 calibration requires four {device} anchor specs")

    blocker_counts: dict[str, int] = {}
    blocker_targets: list[Rush16CalibrationTarget] = []
    for filename, spec in sorted(device_specs.items()):
        plan = compile_rush01_midi_plan(normalized_device, spec, config=config)
        blockers = rush16_hardware_blockers(spec, plan)
        blocker_counts[filename] = len(blockers)
        for path in blockers:
            requested = _target_requested_value(path, rush16_value_at_path(spec, path))
            blocker_targets.append(
                Rush16CalibrationTarget(
                    spec_filename=filename,
                    semantic_path=path,
                    requested_value=requested,
                    requested_fingerprint=_fingerprint(requested),
                )
            )

    templates = tuple(
        template
        for template in _FAMILY_TEMPLATES + _A4_FAMILY_TEMPLATES
        if template.device == normalized_device
    )
    families: list[Rush16CalibrationFamily] = []
    matched: set[tuple[str, str]] = set()
    for template in templates:
        targets = tuple(
            target
            for target in blocker_targets
            if re.fullmatch(template.path_pattern, target.semantic_path)
        )
        matched.update((target.spec_filename, target.semantic_path) for target in targets)
        families.append(
            Rush16CalibrationFamily(
                family_id=template.family_id,
                device=template.device,
                label=template.label,
                converter_kind=template.converter_kind,
                promotion_mode=template.promotion_mode,
                path_pattern=template.path_pattern,
                candidates=template.candidates,
                witnesses=template.witnesses,
                evidence_source=template.evidence_source,
                supported=template.supported,
                targets=targets,
            )
        )
    unmatched = tuple(
        target
        for target in blocker_targets
        if (target.spec_filename, target.semantic_path) not in matched
    )
    if unmatched:
        raise ValueError(
            "RUSH16 calibration has no family for: "
            + ", ".join(f"{target.spec_filename}:{target.semantic_path}" for target in unmatched)
        )
    _validate_distinct_family_witness_addresses(families)

    steps: list[Rush16CalibrationStep] = []
    for family in families:
        if not family.supported or not family.targets:
            continue
        for witness in family.witnesses:
            if witness.spec_filename not in device_specs:
                raise ValueError(f"missing RUSH16 witness spec: {witness.spec_filename}")
            channel = _midi_channel(config, witness.track)
            context = _machine_context_messages(
                normalized_device,
                device_specs[witness.spec_filename],
                witness,
                channel,
                family.family_id,
            )
            for raw_value in family.candidates:
                candidate = _encode_address(witness.address, channel, raw_value)
                sequence = len(steps) + 1
                steps.append(
                    Rush16CalibrationStep(
                        step_id=f"{family.family_id}:{witness.role}:{raw_value}",
                        sequence=sequence,
                        family_id=family.family_id,
                        witness_role=witness.role,
                        spec_filename=witness.spec_filename,
                        semantic_path=witness.semantic_path,
                        track=witness.track,
                        raw_value=raw_value,
                        value_domain=witness.address.value_domain,
                        context_messages=context,
                        candidate_messages=candidate,
                    )
                )

    return Rush16CalibrationPlan(
        version=RUSH16_CALIBRATION_VERSION,
        device=normalized_device,
        output_port=config.output_port,
        input_port=config.input_port,
        families=tuple(families),
        steps=tuple(steps),
        blocker_counts_before=blocker_counts,
        filter2_resonance_evidence=(
            "PR #214 hardware-validated Filter 2 Resonance writer is reused when integrated; "
            "it is not an apply blocker and has no calibration probes in this plan."
        ),
    )


def build_rush16_calibration_catalog(
    device: str,
    specs: Mapping[str, object],
) -> dict[str, object]:
    """Build an unconfigured family catalog with null ports and no packets."""

    if device not in {RUSH01_DEVICE_RYTM, RUSH01_DEVICE_A4}:
        raise ValueError("RUSH16 calibration device must be rytm or a4")
    normalized_device = cast(Rush01Device, device)
    device_specs = {
        name: spec for name, spec in specs.items() if _spec_device(spec) == normalized_device
    }
    if len(device_specs) != 4:
        raise ValueError(f"RUSH16 calibration requires four {device} anchor specs")
    blockers: dict[str, int] = {}
    targets: list[Rush16CalibrationTarget] = []
    for filename, spec in sorted(device_specs.items()):
        plan = compile_rush01_midi_plan(normalized_device, spec)
        paths = rush16_hardware_blockers(spec, plan)
        blockers[filename] = len(paths)
        for path in paths:
            requested = _target_requested_value(path, rush16_value_at_path(spec, path))
            targets.append(
                Rush16CalibrationTarget(
                    spec_filename=filename,
                    semantic_path=path,
                    requested_value=requested,
                    requested_fingerprint=_fingerprint(requested),
                )
            )
    templates = tuple(
        template
        for template in _FAMILY_TEMPLATES + _A4_FAMILY_TEMPLATES
        if template.device == normalized_device
    )
    matched: set[tuple[str, str]] = set()
    families: list[dict[str, object]] = []
    for template in templates:
        family_targets = tuple(
            target
            for target in targets
            if re.fullmatch(template.path_pattern, target.semantic_path)
        )
        matched.update((target.spec_filename, target.semantic_path) for target in family_targets)
        families.append(
            {
                "family_id": template.family_id,
                "label": template.label,
                "converter_kind": template.converter_kind,
                "promotion_mode": template.promotion_mode,
                "supported": template.supported,
                "evidence_source": template.evidence_source,
                "candidates": list(template.candidates),
                "required_observations": len(template.candidates) * len(template.witnesses),
                "witnesses": [_witness_to_dict(witness) for witness in template.witnesses],
                "targets": [_target_to_dict(target) for target in family_targets],
            }
        )
    unmatched = tuple(
        target for target in targets if (target.spec_filename, target.semantic_path) not in matched
    )
    if unmatched:
        raise ValueError(
            "RUSH16 calibration has no family for: "
            + ", ".join(f"{target.spec_filename}:{target.semantic_path}" for target in unmatched)
        )
    return {
        "version": RUSH16_CALIBRATION_VERSION,
        "device": normalized_device,
        "output_port": None,
        "input_port": None,
        "channels": None,
        "configuration_ready": False,
        "blocker_counts_before": blockers,
        "families": families,
        "required_observations": sum(
            int(family["required_observations"])
            for family in families
            if family["supported"] and family["targets"]
        ),
        "filter2_resonance_evidence": (
            "PR #214 hardware-validated Filter 2 Resonance writer is reused when integrated; "
            "it is not an apply blocker and has no calibration probes in this catalog."
        ),
        "safety": {
            "passive_catalog": True,
            "midi_backend_opened": False,
            "midi_port_opened": False,
            "midi_or_sysex_transmitted": False,
        },
    }


def rush16_calibration_plan_to_dict(plan: Rush16CalibrationPlan) -> dict[str, object]:
    """Return a stable JSON-ready plan representation."""

    return {
        "version": plan.version,
        "device": plan.device,
        "output_port": plan.output_port,
        "input_port": plan.input_port,
        "blocker_counts_before": dict(plan.blocker_counts_before),
        "filter2_resonance_evidence": plan.filter2_resonance_evidence,
        "families": [
            {
                "family_id": family.family_id,
                "label": family.label,
                "converter_kind": family.converter_kind,
                "promotion_mode": family.promotion_mode,
                "supported": family.supported,
                "evidence_source": family.evidence_source,
                "candidates": list(family.candidates),
                "required_observations": len(family.candidates) * len(family.witnesses),
                "witnesses": [_witness_to_dict(witness) for witness in family.witnesses],
                "targets": [_target_to_dict(target) for target in family.targets],
            }
            for family in plan.families
        ],
        "steps": [_step_to_dict(step) for step in plan.steps],
        "safety": {
            "app_arm_required": True,
            "one_candidate_per_invocation": True,
            "manual_sound_parameter_entry": False,
            "outbound_message_types": ["CC"],
            "program_change": False,
            "transport": False,
            "realtime": False,
            "sysex_output": False,
            "save_pattern_song_project": False,
        },
    }


def rush16_calibration_plan_sha256(plan: Rush16CalibrationPlan) -> str:
    """Hash the exact configured calibration plan for checkpoint binding."""

    return sha256(_canonical_json(rush16_calibration_plan_to_dict(plan))).hexdigest()


def load_or_create_rush16_checkpoint(
    path: Path,
    plan: Rush16CalibrationPlan,
    *,
    hardware_unit: str,
    disposable_target: str,
) -> dict[str, object]:
    """Load one matching checkpoint or create a new local-only session."""

    if not hardware_unit.strip():
        raise ValueError("RUSH16 calibration hardware unit identifier is required")
    if not disposable_target.strip():
        raise ValueError("RUSH16 calibration disposable target is required")
    plan_sha = rush16_calibration_plan_sha256(plan)
    if path.exists():
        payload = json.loads(path.read_text(encoding="utf-8"))
        checkpoint = _mapping(payload, "checkpoint")
        expected = {
            "version": RUSH16_CALIBRATION_VERSION,
            "device": plan.device,
            "plan_sha256": plan_sha,
            "hardware_unit": hardware_unit,
            "disposable_target": disposable_target,
        }
        for key, value in expected.items():
            if checkpoint.get(key) != value:
                raise ValueError(f"RUSH16 checkpoint {key} does not match this session")
        observations = tuple(
            _mapping(row, "checkpoint observation")
            for row in _require_object_sequence(
                checkpoint.get("observations"), "checkpoint.observations"
            )
        )
        _require_object_sequence(checkpoint.get("promotions"), "checkpoint.promotions")
        normalized = dict(checkpoint)
        normalized["promotions"] = _derive_promotions(plan, observations)
        return normalized
    now = datetime.now(UTC).isoformat()
    return {
        "version": RUSH16_CALIBRATION_VERSION,
        "device": plan.device,
        "plan_sha256": plan_sha,
        "hardware_unit": hardware_unit,
        "disposable_target": disposable_target,
        "created_at_utc": now,
        "updated_at_utc": now,
        "observations": [],
        "promotions": [],
    }


def next_rush16_calibration_step(
    plan: Rush16CalibrationPlan,
    checkpoint: Mapping[str, object],
) -> Rush16CalibrationStep | None:
    """Return the next useful step, avoiding redundant A4 certification cycles."""

    observations = tuple(
        _mapping(row, "observation")
        for row in _require_object_sequence(
            checkpoint.get("observations"), "checkpoint.observations"
        )
    )
    observed = {str(row.get("step_id")) for row in observations if _observation_completes_step(row)}
    promoted = {
        str(_mapping(row, "promotion").get("family_id"))
        for row in _require_object_sequence(checkpoint.get("promotions"), "checkpoint.promotions")
    }
    promoted.update(str(row.get("family_id")) for row in _derive_promotions(plan, observations))
    family_order = {family.family_id: index for index, family in enumerate(plan.families)}
    candidate_order = {
        (family.family_id, raw): index
        for family in plan.families
        for index, raw in enumerate(family.candidates)
    }
    witness_order = {
        (family.family_id, witness.role): index
        for family in plan.families
        for index, witness in enumerate(family.witnesses)
    }
    remaining = tuple(
        step
        for step in plan.steps
        if step.step_id not in observed and step.family_id not in promoted
    )
    if plan.device != RUSH01_DEVICE_A4:
        return min(
            remaining,
            key=lambda step: (
                family_order[step.family_id],
                candidate_order[(step.family_id, step.raw_value)],
                witness_order[(step.family_id, step.witness_role)],
                step.sequence,
            ),
            default=None,
        )

    active_families = tuple(
        family
        for family in plan.families
        if family.supported and family.targets and family.witnesses
    )
    ordered_families = (
        tuple(
            sorted(
                active_families,
                key=lambda family: (
                    (
                        0
                        if any(row.get("family_id") == family.family_id for row in observations)
                        else 1
                    ),
                    _a4_family_remaining_step_count(
                        plan,
                        family,
                        tuple(
                            row for row in observations if row.get("family_id") == family.family_id
                        ),
                    ),
                    family_order[family.family_id],
                ),
            )
        )
        if observations
        else active_families
    )
    for family in ordered_families:
        if family.family_id in promoted or not family.supported or not family.targets:
            continue
        family_rows = tuple(row for row in observations if row.get("family_id") == family.family_id)
        target_raws = _adaptive_target_raws(family, family_rows)
        affine_confirmation = _affine_confirmation_raw(family, family_rows)
        if _supports_affine_inference(family):
            certification_raws = [affine_confirmation] if affine_confirmation is not None else []
        else:
            certification_raws = list(dict.fromkeys(target_raws.values()))
        for raw in certification_raws:
            for witness in family.witnesses:
                step = next(
                    (
                        candidate
                        for candidate in plan.steps
                        if candidate.family_id == family.family_id
                        and candidate.raw_value == raw
                        and candidate.witness_role == witness.role
                    ),
                    None,
                )
                if step is not None and not _step_has_saved_kit_evidence(family_rows, step):
                    return step

        discovery_raws: list[int] = []
        if family.converter_kind in {"selector", "boolean"}:
            for raw in tuple(certification_raws):
                discovery_raws.extend(_neighboring_candidates(family, raw))

        primary_role = family.witnesses[0].role
        for raw in discovery_raws:
            step = next(
                (
                    candidate
                    for candidate in plan.steps
                    if candidate.family_id == family.family_id
                    and candidate.raw_value == raw
                    and candidate.witness_role == primary_role
                ),
                None,
            )
            if step is not None and not _step_has_any_evidence(family_rows, step):
                return step

        # Unknown mappings are discovered on one representative route. Other routes are
        # certified only for useful target values, never for every rejected candidate.
        for raw in _discovery_candidate_order(family):
            primary = next(
                (
                    step
                    for step in plan.steps
                    if step.family_id == family.family_id
                    and step.raw_value == raw
                    and step.witness_role == primary_role
                ),
                None,
            )
            if primary is not None and not _step_has_any_evidence(family_rows, primary):
                return primary
    return None


def rush16_calibration_step_requires_saved_kit(
    plan: Rush16CalibrationPlan,
    checkpoint: Mapping[str, object],
    step: Rush16CalibrationStep,
) -> bool:
    """Return whether this candidate must receive full saved-KIT certification."""

    if plan.device != RUSH01_DEVICE_A4:
        return True
    family = _family_by_id(plan, step.family_id)
    rows = tuple(
        _mapping(row, "observation")
        for row in _require_object_sequence(
            checkpoint.get("observations"), "checkpoint.observations"
        )
        if _mapping(row, "observation").get("family_id") == step.family_id
    )
    affine_confirmation = _affine_confirmation_raw(family, rows)
    if _supports_affine_inference(family):
        required = {affine_confirmation} if affine_confirmation is not None else set()
    else:
        required = set(_adaptive_target_raws(family, rows).values())
    return step.raw_value in required


def _step_has_any_evidence(
    rows: Sequence[Mapping[str, object]],
    step: Rush16CalibrationStep,
) -> bool:
    return any(row.get("step_id") == step.step_id for row in rows)


def _step_has_saved_kit_evidence(
    rows: Sequence[Mapping[str, object]],
    step: Rush16CalibrationStep,
) -> bool:
    return any(
        row.get("step_id") == step.step_id and _row_has_saved_payload_change(row) for row in rows
    )


def _observation_completes_step(row: Mapping[str, object]) -> bool:
    if row.get("evidence_kind") != "display_discovery":
        return True
    approvals = _require_object_sequence(row.get("approved_requested_values"), "approved values")
    return not approvals


def _adaptive_target_raws(
    family: Rush16CalibrationFamily,
    rows: Sequence[Mapping[str, object]],
) -> dict[str, int]:
    approved: dict[str, int] = {}
    for row in rows:
        raw = row.get("raw_value")
        if not isinstance(raw, int):
            continue
        for value in _require_object_sequence(
            row.get("approved_requested_values"), "approved values"
        ):
            approved[_fingerprint(value)] = raw
    if family.converter_kind not in {"bipolar", "continuous", "high_resolution"}:
        return approved
    return {**_predict_affine_target_raws(family, rows), **approved}


def _predict_affine_target_raws(
    family: Rush16CalibrationFamily,
    rows: Sequence[Mapping[str, object]],
) -> dict[str, int]:
    fit = _affine_fit(family, rows)
    if fit is None or not _affine_cross_track_confirmed(family, rows):
        return {}
    slope, intercept = fit
    maximum = 127 if family.witnesses[0].address.value_domain == VALUE_DOMAIN_7BIT else 16383
    result: dict[str, int] = {}
    for target in family.targets:
        value = rush16_effective_requested_value(target.requested_value)
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            continue
        raw = round((float(value) - intercept) / slope)
        if 0 <= raw <= maximum and abs((slope * raw + intercept) - float(value)) <= 1e-6:
            result[_fingerprint(value)] = raw
    return result


def _supports_affine_inference(family: Rush16CalibrationFamily) -> bool:
    return family.promotion_mode in {"lookup", "affine"} and (
        family.converter_kind in _AFFINE_INFERENCE_KINDS
    )


def _affine_fit(
    family: Rush16CalibrationFamily,
    rows: Sequence[Mapping[str, object]],
) -> tuple[float, float] | None:
    primary_role = family.witnesses[0].role
    points: dict[int, float] = {}
    for row in rows:
        if row.get("witness_role") != primary_role:
            continue
        raw = row.get("raw_value")
        display = row.get("display_value")
        if (
            isinstance(raw, int)
            and not isinstance(display, bool)
            and isinstance(display, (int, float))
        ):
            numeric = float(display)
            if raw in points and points[raw] != numeric:
                return None
            points[raw] = numeric
    if len(points) < 3:
        return None
    low_raw, high_raw = min(points), max(points)
    if low_raw == high_raw or points[low_raw] == points[high_raw]:
        return None
    slope = (points[high_raw] - points[low_raw]) / (high_raw - low_raw)
    intercept = points[low_raw] - slope * low_raw
    if abs(slope) < 1e-12 or any(
        abs((slope * raw + intercept) - display) > 1e-6 for raw, display in points.items()
    ):
        return None
    return slope, intercept


def _neighboring_candidates(family: Rush16CalibrationFamily, raw: int) -> tuple[int, ...]:
    if raw not in family.candidates:
        return ()
    index = family.candidates.index(raw)
    return tuple(
        family.candidates[candidate_index]
        for candidate_index in (index - 1, index + 1)
        if 0 <= candidate_index < len(family.candidates)
    )


def _discovery_candidate_order(family: Rush16CalibrationFamily) -> tuple[int, ...]:
    if family.converter_kind != "selector" or len(family.candidates) <= 16:
        return family.candidates
    candidates = family.candidates
    ordered_indices = [0, len(candidates) - 1]
    intervals = [(1, len(candidates) - 2)]
    while intervals:
        low, high = intervals.pop(0)
        if low > high:
            continue
        middle = (low + high) // 2
        ordered_indices.append(middle)
        intervals.extend(((low, middle - 1), (middle + 1, high)))
    return tuple(candidates[index] for index in ordered_indices)


def _affine_confirmation_raw(
    family: Rush16CalibrationFamily,
    rows: Sequence[Mapping[str, object]],
) -> int | None:
    if not _supports_affine_inference(family) or _affine_fit(family, rows) is None:
        return None
    primary_role = family.witnesses[0].role
    primary_raws = sorted(
        {
            int(row["raw_value"])
            for row in rows
            if row.get("witness_role") == primary_role and isinstance(row.get("raw_value"), int)
        }
    )
    for raw in primary_raws:
        if _raw_has_matching_saved_affine_evidence(family, rows, raw):
            return None
    if primary_raws:
        return primary_raws[0]
    return None


def _raw_has_matching_saved_affine_evidence(
    family: Rush16CalibrationFamily,
    rows: Sequence[Mapping[str, object]],
    raw: int,
) -> bool:
    matching = tuple(row for row in rows if row.get("raw_value") == raw)
    roles = {witness.role for witness in family.witnesses}
    if {str(row.get("witness_role")) for row in matching} != roles:
        return False
    displays = {_fingerprint(row.get("display_value")) for row in matching}
    if len(displays) != 1:
        return False
    return _raw_has_saved_kit_evidence_for_all_locations(family, matching, raw)


def validate_rush16_calibration_baseline_continuity(
    checkpoint: Mapping[str, object],
    baseline: bytes,
) -> None:
    """Require the baseline to match the last accepted saved KIT state."""

    observations = _require_object_sequence(
        checkpoint.get("observations"), "checkpoint.observations"
    )
    if not observations:
        return
    previous = next(
        (
            _mapping(row, "checkpoint observation")
            for row in reversed(observations)
            if isinstance(_mapping(row, "checkpoint observation").get("differential"), Mapping)
        ),
        None,
    )
    if previous is None:
        raise ValueError("RUSH16 checkpoint has no saved KIT differential for baseline continuity")
    differential = _mapping(previous.get("differential"), "last saved KIT differential")
    expected = differential.get("changed_sha256")
    if not isinstance(expected, str):
        raise ValueError("last RUSH16 observation is missing its changed KIT SHA-256")
    actual = sha256(baseline).hexdigest()
    if actual != expected:
        raise ValueError(
            "RUSH16 baseline KIT does not match the last accepted saved calibration state; "
            f"expected sha256={expected}, captured sha256={actual}. Restore the last accepted "
            "saved state before retrying; no candidate MIDI was sent"
        )


def accept_rush16_calibration_observation(
    plan: Rush16CalibrationPlan,
    checkpoint: Mapping[str, object],
    *,
    step: Rush16CalibrationStep,
    display_value: object,
    approved_requested_values: Sequence[object],
    differential: Mapping[str, object] | None,
    evidence_reference_step_id: str | None = None,
    observation_evidence_kind: CalibrationEvidenceKind | None = None,
) -> dict[str, object]:
    """Checkpoint one accepted display/capture observation and derive promotions."""

    expected = next_rush16_calibration_step(plan, checkpoint)
    if expected is None or expected.step_id != step.step_id:
        raise ValueError("RUSH16 calibration observation is not the next checkpoint step")
    family = _family_by_id(plan, step.family_id)
    observations = [
        dict(_mapping(row, "observation"))
        for row in _require_object_sequence(
            checkpoint.get("observations"), "checkpoint.observations"
        )
    ]
    allowed = {
        _fingerprint(rush16_effective_requested_value(target.requested_value))
        for target in family.targets
    }
    approvals = tuple(
        value
        for index, value in enumerate(approved_requested_values)
        if _fingerprint(value)
        not in {_fingerprint(previous) for previous in approved_requested_values[:index]}
    )
    if any(_fingerprint(value) not in allowed for value in approvals):
        raise ValueError("approved value is not requested by this calibration family")
    unpacked_offsets: tuple[int, ...]
    if observation_evidence_kind == "display_discovery":
        if differential is not None or evidence_reference_step_id is not None:
            raise ValueError("RUSH16 display discovery cannot include saved-KIT evidence")
        unpacked_offsets = ()
        evidence_kind = "display_discovery"
    elif differential is None:
        if observation_evidence_kind not in (None, "display_repeat"):
            raise ValueError("RUSH16 observation evidence kind does not match its payload")
        _validate_display_repeat_evidence(
            family,
            observations,
            step=step,
            display_value=display_value,
            approvals=approvals,
            evidence_reference_step_id=evidence_reference_step_id,
        )
        unpacked_offsets = ()
        evidence_kind = "display_repeat"
    else:
        if observation_evidence_kind not in (None, "saved_kit_differential"):
            raise ValueError("RUSH16 observation evidence kind does not match its payload")
        if evidence_reference_step_id is not None:
            raise ValueError("saved KIT differential evidence cannot reference another step")
        unpacked_offsets = _validate_observation_differential(differential)
        evidence_kind = "saved_kit_differential"

    updated = dict(checkpoint)
    approved_fingerprints = {_fingerprint(value) for value in approvals}
    if approved_fingerprints and any(
        row.get("family_id") == step.family_id
        and row.get("raw_value") != step.raw_value
        and approved_fingerprints
        & {
            _fingerprint(value)
            for value in _require_object_sequence(
                row.get("approved_requested_values"), "approved values"
            )
        }
        for row in observations
    ):
        raise ValueError("RUSH16 requested value is already approved for a different raw candidate")
    distinct_display_for_role = any(
        row.get("family_id") == step.family_id
        and row.get("witness_role") == step.witness_role
        and row.get("raw_value") != step.raw_value
        and _fingerprint(row.get("display_value")) != _fingerprint(display_value)
        for row in observations
    )
    step_witness = next(
        witness for witness in family.witnesses if witness.role == step.witness_role
    )
    equivalent_roles = {
        witness.role
        for witness in family.witnesses
        if _same_witness_location(witness, step_witness)
    }
    equivalent_location_has_saved_evidence = any(
        row.get("witness_role") in equivalent_roles and _row_has_saved_payload_change(row)
        for row in observations
    )
    if (
        evidence_kind != "display_discovery"
        and not unpacked_offsets
        and distinct_display_for_role
        and not equivalent_location_has_saved_evidence
    ):
        raise ValueError(
            "RUSH16 changed KIT contains no payload differential for a distinct displayed "
            "candidate; save the disposable active KIT before the changed capture"
        )
    observations.append(
        {
            "step_id": step.step_id,
            "family_id": step.family_id,
            "witness_role": step.witness_role,
            "spec_filename": step.spec_filename,
            "semantic_path": step.semantic_path,
            "track": step.track,
            "raw_value": step.raw_value,
            "value_domain": step.value_domain,
            "display_value": display_value,
            "approved_requested_values": list(approvals),
            "ordered_midi_bytes": [list(packet) for packet in step.ordered_messages],
            "evidence_kind": evidence_kind,
            "evidence_reference_step_id": evidence_reference_step_id,
            "differential": dict(differential) if differential is not None else None,
            "accepted_at_utc": datetime.now(UTC).isoformat(),
        }
    )
    updated["observations"] = observations
    updated["promotions"] = _derive_promotions(plan, observations)
    updated["updated_at_utc"] = datetime.now(UTC).isoformat()
    return updated


def rush16_steps_share_witness_location(
    plan: Rush16CalibrationPlan,
    left: Rush16CalibrationStep,
    right: Rush16CalibrationStep,
) -> bool:
    """Return whether two same-candidate steps probe one saved KIT location."""

    if left.family_id != right.family_id or left.raw_value != right.raw_value:
        return False
    family = _family_by_id(plan, left.family_id)
    left_witness = next(
        witness for witness in family.witnesses if witness.role == left.witness_role
    )
    right_witness = next(
        witness for witness in family.witnesses if witness.role == right.witness_role
    )
    return _same_witness_location(left_witness, right_witness)


def write_rush16_checkpoint(path: Path, checkpoint: Mapping[str, object]) -> None:
    """Atomically write a local calibration checkpoint after acceptance."""

    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    try:
        temporary.write_text(
            json.dumps(dict(checkpoint), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        temporary.replace(path)
    finally:
        if temporary.exists():
            temporary.unlink()


def analyze_rush16_kit_differential(
    device: str,
    baseline: bytes,
    changed: bytes,
) -> dict[str, object]:
    """Validate two hardware KIT frames and report every changed location."""

    if len(baseline) != len(changed):
        raise ValueError("RUSH16 differential frames must have equal lengths")
    codec = ANALOG_RYTM_KIT_CODEC if device == RUSH01_DEVICE_RYTM else ANALOG_FOUR_KIT_CODEC
    baseline_decoded = codec.decode_frame(baseline)
    changed_decoded = codec.decode_frame(changed)
    if codec.encode_frame(baseline_decoded) != baseline:
        raise ValueError("RUSH16 calibration baseline KIT is not round-trip stable")
    if codec.encode_frame(changed_decoded) != changed:
        raise ValueError("RUSH16 calibration changed KIT is not round-trip stable")
    header_size = codec.spec.header_size_without_f0
    packed_frame_start = 1 + header_size
    trailer_start = len(baseline) - 5
    return {
        "baseline_sha256": sha256(baseline).hexdigest(),
        "changed_sha256": sha256(changed).hexdigest(),
        "baseline_round_trip_identical": True,
        "changed_round_trip_identical": True,
        "frame_offsets": _changed_offsets(baseline, changed),
        "header_offsets": _changed_offsets(
            baseline_decoded.header,
            changed_decoded.header,
            offset=1,
        ),
        "packed_offsets": _changed_offsets(
            baseline_decoded.packed,
            changed_decoded.packed,
        ),
        "packed_frame_offsets": _changed_offsets(
            baseline_decoded.packed,
            changed_decoded.packed,
            offset=packed_frame_start,
        ),
        "unpacked_offsets": _changed_offsets(
            baseline_decoded.unpacked,
            changed_decoded.unpacked,
        ),
        "integrity_frame_offsets": [
            offset
            for offset in _changed_offsets(baseline, changed)
            if trailer_start <= offset < len(baseline) - 1
        ],
    }


def apply_rush16_calibration_promotions(
    plan: Rush01MidiPlan,
    *,
    spec_filename: str,
    checkpoint: Mapping[str, object],
) -> Rush01MidiPlan:
    """Overlay only exact requested-value promotions onto a compiled plan."""

    checkpoint_version = checkpoint.get("version")
    if checkpoint_version not in _PROMOTION_CHECKPOINT_VERSIONS:
        raise ValueError("RUSH16 promotion checkpoint version is invalid")
    if checkpoint.get("device") != plan.device:
        raise ValueError("RUSH16 promotion checkpoint device does not match plan")
    promotions = [
        _mapping(row, "promotion")
        for row in _require_object_sequence(checkpoint.get("promotions"), "checkpoint.promotions")
    ]
    by_path = {
        str(target["semantic_path"]): (promotion, target)
        for promotion in promotions
        for target in _require_object_sequence(promotion.get("targets"), "promotion.targets")
        if isinstance(target, Mapping) and target.get("spec_filename") == spec_filename
    }
    fields: list[Rush01MidiField] = []
    for field in plan.fields:
        promoted = by_path.get(field.semantic_path)
        if promoted is None:
            fields.append(field)
            continue
        promotion, target = promoted
        if target.get("requested_fingerprint") != _fingerprint(field.requested_value):
            raise ValueError(f"stale RUSH16 promotion for {field.semantic_path}")
        raw_value = target.get("raw_value")
        domain = target.get("value_domain")
        if isinstance(raw_value, bool) or not isinstance(raw_value, int):
            raise ValueError("RUSH16 promotion raw value must be an integer")
        if domain not in {VALUE_DOMAIN_7BIT, VALUE_DOMAIN_14BIT}:
            raise ValueError("RUSH16 promotion value domain is invalid")
        if field.channel is None:
            raise ValueError(
                f"RUSH16 promoted field has no configured channel: {field.semantic_path}"
            )
        address = _promotion_address(
            checkpoint_version=cast(str, checkpoint_version),
            target=target,
            field=field,
        )
        if address.value_domain != domain:
            raise ValueError("RUSH16 promotion address value domain is inconsistent")
        packets = _encode_address(address, field.channel, raw_value)
        fields.append(
            replace(
                field,
                normalized_midi_value=raw_value,
                normalized_value_domain=cast(Rush01ValueDomain, domain),
                message_type=address.message_type,
                controller=address.controller,
                controller_lsb=address.controller_lsb,
                nrpn_address=address.nrpn_address,
                ordered_midi_bytes=packets,
                mapping_evidence=(
                    f"RUSH16 hardware calibration {promotion.get('family_id')}; "
                    f"checkpoint={checkpoint.get('plan_sha256')}; "
                    f"evidence={promotion.get('evidence_sha256')}"
                ),
                status=STATUS_READY,
                reason="requested value encoded by repeated hardware calibration evidence",
                configuration_issue=None,
            )
        )
    field_tuple = tuple(fields)
    summary = _summarize_promoted_fields(field_tuple)
    promoted_plan = replace(
        plan,
        fields=field_tuple,
        summary=summary,
        configuration_ready=(
            summary.ready_fields > 0 and summary.ready_fields == summary.configured_ready_fields
        ),
    )
    validate_rush01_plan_safety(promoted_plan)
    return promoted_plan


def _promotion_address(
    *,
    checkpoint_version: str,
    target: Mapping[str, object],
    field: Rush01MidiField,
) -> Rush16CalibrationAddress:
    if checkpoint_version == RUSH16_CALIBRATION_VERSION:
        return _address_from_dict(_mapping(target.get("address"), "promotion target address"))
    if "address" in target:
        raise ValueError("legacy RUSH16 promotion target must not supply an address")
    if field.message_type == MESSAGE_CC and field.controller is not None:
        return _address_cc(field.controller)
    if (
        field.message_type == MESSAGE_CC14
        and field.controller is not None
        and field.controller_lsb is not None
    ):
        return _address_cc14(field.controller, field.controller_lsb)
    if field.message_type == MESSAGE_NRPN and field.nrpn_address is not None:
        return Rush16CalibrationAddress(
            MESSAGE_NRPN,
            VALUE_DOMAIN_7BIT,
            nrpn_address=field.nrpn_address,
        )
    raise ValueError(
        f"legacy RUSH16 promotion has no unique documented address: {field.semantic_path}"
    )


def rush16_calibration_progress(
    plan: Rush16CalibrationPlan,
    checkpoint: Mapping[str, object],
) -> Rush16CalibrationProgress:
    """Summarize family, observation, and anchor blocker progress."""

    observations = _require_object_sequence(
        checkpoint.get("observations"), "checkpoint.observations"
    )
    observation_rows = tuple(row for row in observations if isinstance(row, Mapping))
    promotions = _derive_promotions(plan, observation_rows)
    promoted_ids = {str(row.get("family_id")) for row in promotions}
    supported = tuple(family for family in plan.families if family.supported and family.targets)
    complete = sum(family.family_id in promoted_ids for family in supported)
    completed_step_ids = {
        str(row.get("step_id"))
        for row in observations
        if isinstance(row, Mapping) and _observation_completes_step(row)
    }
    remaining_steps = _adaptive_remaining_step_count(
        plan,
        observation_rows,
        promoted_ids,
        completed_step_ids,
    )
    promoted_targets = Counter(
        str(target.get("spec_filename"))
        for promotion in promotions
        for target in _require_object_sequence(promotion.get("targets"), "promotion.targets")
        if isinstance(target, Mapping)
    )
    after = {
        filename: max(0, count - promoted_targets.get(filename, 0))
        for filename, count in plan.blocker_counts_before.items()
    }
    next_step = next_rush16_calibration_step(plan, checkpoint)
    next_family_id = next_step.family_id if next_step is not None else None
    next_family_remaining = 0
    if next_family_id is not None:
        next_family = _family_by_id(plan, next_family_id)
        next_family_rows = tuple(
            row for row in observation_rows if row.get("family_id") == next_family_id
        )
        if plan.device == RUSH01_DEVICE_A4:
            next_family_remaining = _a4_family_remaining_step_count(
                plan, next_family, next_family_rows
            )
        else:
            next_family_remaining = sum(
                step.family_id == next_family_id and step.step_id not in completed_step_ids
                for step in plan.steps
            )
    return Rush16CalibrationProgress(
        families_complete=complete,
        families_remaining=len(supported) - complete,
        observations_complete=len(observations),
        observations_remaining=remaining_steps,
        next_family_id=next_family_id,
        next_family_observations_remaining=next_family_remaining,
        deferred_large_selector_families=sum(
            family.family_id not in promoted_ids
            and family.supported
            and bool(family.targets)
            and family.converter_kind == "selector"
            and len(family.candidates) > 16
            for family in plan.families
        ),
        blocker_counts_before=plan.blocker_counts_before,
        blocker_counts_after=after,
    )


def _adaptive_remaining_step_count(
    plan: Rush16CalibrationPlan,
    observations: Sequence[Mapping[str, object]],
    promoted_ids: set[str],
    completed_step_ids: set[str],
) -> int:
    if plan.device != RUSH01_DEVICE_A4:
        return sum(
            step.family_id not in promoted_ids and step.step_id not in completed_step_ids
            for step in plan.steps
        )
    return sum(
        _a4_family_remaining_step_count(
            plan,
            family,
            tuple(row for row in observations if row.get("family_id") == family.family_id),
        )
        for family in plan.families
        if family.family_id not in promoted_ids and family.supported and family.targets
    )


def _a4_family_remaining_step_count(
    plan: Rush16CalibrationPlan,
    family: Rush16CalibrationFamily,
    rows: Sequence[Mapping[str, object]],
) -> int:
    if not family.witnesses:
        return 0
    target_raws = _adaptive_target_raws(family, rows)
    affine_confirmation = _affine_confirmation_raw(family, rows)
    if _supports_affine_inference(family):
        required_raws = {affine_confirmation} if affine_confirmation is not None else set()
    else:
        required_raws = set(target_raws.values())
    representative_raws: set[int] = set()
    requested = {
        _fingerprint(rush16_effective_requested_value(target.requested_value))
        for target in family.targets
    }
    if set(target_raws) != requested and (
        not _supports_affine_inference(family) or _affine_fit(family, rows) is None
    ):
        representative_raws.update(family.candidates)
    if family.converter_kind in {"selector", "boolean"}:
        for raw in required_raws:
            representative_raws.update(_neighboring_candidates(family, raw))
    primary_role = family.witnesses[0].role
    return sum(
        step.raw_value in required_raws and not _step_has_saved_kit_evidence(rows, step)
        for step in plan.steps
        if step.family_id == family.family_id
    ) + sum(
        step.raw_value in representative_raws
        and step.raw_value not in required_raws
        and step.witness_role == primary_role
        and not _step_has_any_evidence(rows, step)
        for step in plan.steps
        if step.family_id == family.family_id
    )


def _derive_promotions(
    plan: Rush16CalibrationPlan,
    observations: Sequence[Mapping[str, object]],
) -> list[dict[str, object]]:
    promotions: list[dict[str, object]] = []
    for family in plan.families:
        family_rows = [row for row in observations if row.get("family_id") == family.family_id]
        if not _family_has_saved_kit_evidence(family, family_rows):
            continue
        target_raw: dict[str, int] = {}
        effective_promotion_mode = family.promotion_mode
        if family.promotion_mode == "lookup":
            target_raw = _lookup_target_raw(family, family_rows)
            if len(target_raw) != len(
                {_fingerprint(target.requested_value) for target in family.targets}
            ) and _supports_affine_inference(family):
                target_raw = _affine_target_raw(family, family_rows)
                effective_promotion_mode = "affine"
        elif family.promotion_mode == "affine":
            target_raw = _affine_target_raw(family, family_rows)
        if len(target_raw) != len(
            {_fingerprint(target.requested_value) for target in family.targets}
        ):
            continue
        evidence_sha = sha256(_canonical_json(family_rows)).hexdigest()
        promotions.append(
            {
                "family_id": family.family_id,
                "converter_kind": family.converter_kind,
                "promotion_mode": effective_promotion_mode,
                "evidence_source": family.evidence_source,
                "evidence_sha256": evidence_sha,
                "observations": len(family_rows),
                "targets": [
                    {
                        **_target_to_dict(target),
                        "raw_value": target_raw[_fingerprint(target.requested_value)],
                        "value_domain": _address_for_target(
                            family, target.semantic_path
                        ).value_domain,
                        "address": _address_to_dict(
                            _address_for_target(family, target.semantic_path)
                        ),
                    }
                    for target in family.targets
                ],
            }
        )
    return promotions


def _validate_display_repeat_evidence(
    family: Rush16CalibrationFamily,
    observations: Sequence[Mapping[str, object]],
    *,
    step: Rush16CalibrationStep,
    display_value: object,
    approvals: Sequence[object],
    evidence_reference_step_id: str | None,
) -> None:
    if evidence_reference_step_id is None:
        raise ValueError("RUSH16 display repeat requires an evidence reference step")
    if approvals:
        raise ValueError("RUSH16 display repeat cannot add semantic approvals")
    if not observations:
        raise ValueError("RUSH16 display repeat requires a preceding saved KIT observation")
    reference = observations[-1]
    if reference.get("step_id") != evidence_reference_step_id:
        raise ValueError("RUSH16 display repeat must reference the immediately preceding step")
    if reference.get("family_id") != step.family_id or reference.get("raw_value") != step.raw_value:
        raise ValueError("RUSH16 display repeat must reference the same family and raw candidate")
    reference_role = reference.get("witness_role")
    if not isinstance(reference_role, str):
        raise ValueError("RUSH16 display repeat reference has no witness role")
    reference_witness = next(
        witness for witness in family.witnesses if witness.role == reference_role
    )
    step_witness = next(
        witness for witness in family.witnesses if witness.role == step.witness_role
    )
    if not _same_witness_location(reference_witness, step_witness):
        raise ValueError("RUSH16 display repeat cannot replace cross-track saved KIT evidence")
    if _fingerprint(reference.get("display_value")) != _fingerprint(display_value):
        raise ValueError("RUSH16 repeated display does not match the primary observation")
    reference_differential = reference.get("differential")
    if not isinstance(reference_differential, Mapping):
        raise ValueError("RUSH16 display repeat reference has no saved KIT differential")
    _validate_observation_differential(reference_differential)


def _validate_observation_differential(differential: Mapping[str, object]) -> tuple[int, ...]:
    if (
        differential.get("baseline_round_trip_identical") is not True
        or differential.get("changed_round_trip_identical") is not True
    ):
        raise ValueError("RUSH16 calibration differential requires stable KIT round trips")
    baseline_sha = differential.get("baseline_sha256")
    changed_sha = differential.get("changed_sha256")
    if not isinstance(baseline_sha, str) or not isinstance(changed_sha, str):
        raise ValueError("RUSH16 calibration differential requires KIT SHA-256 values")
    offsets = {
        key: _validated_offsets(differential.get(key), key)
        for key in (
            "frame_offsets",
            "header_offsets",
            "packed_offsets",
            "packed_frame_offsets",
            "unpacked_offsets",
            "integrity_frame_offsets",
        )
    }
    if offsets["header_offsets"]:
        raise ValueError("RUSH16 calibration differential changed KIT header bytes")
    unpacked_offsets = offsets["unpacked_offsets"]
    if bool(unpacked_offsets) != (baseline_sha != changed_sha):
        raise ValueError("RUSH16 calibration differential hash/payload evidence is inconsistent")
    if unpacked_offsets and (
        not offsets["frame_offsets"]
        or not offsets["packed_offsets"]
        or not offsets["packed_frame_offsets"]
    ):
        raise ValueError("RUSH16 calibration differential is missing packed payload evidence")
    if not unpacked_offsets and any(offsets.values()):
        raise ValueError("RUSH16 calibration no-op differential contains changed byte offsets")
    return unpacked_offsets


def _validated_offsets(value: object, key: str) -> tuple[int, ...]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        raise ValueError(f"RUSH16 calibration differential {key} must be a sequence")
    if any(
        isinstance(offset, bool) or not isinstance(offset, int) or offset < 0 for offset in value
    ):
        raise ValueError(f"RUSH16 calibration differential {key} contains an invalid offset")
    return tuple(cast(Sequence[int], value))


def _family_has_saved_kit_evidence(
    family: Rush16CalibrationFamily,
    rows: Sequence[Mapping[str, object]],
) -> bool:
    changed_roles = {
        str(row.get("witness_role")) for row in rows if _row_has_saved_payload_change(row)
    }
    evidence_groups = {
        frozenset(
            candidate.role
            for candidate in family.witnesses
            if _same_witness_location(candidate, witness)
        )
        for witness in family.witnesses
    }
    return all(bool(group & changed_roles) for group in evidence_groups)


def _row_has_saved_payload_change(row: Mapping[str, object]) -> bool:
    differential = row.get("differential")
    return isinstance(differential, Mapping) and bool(differential.get("unpacked_offsets"))


def _same_witness_location(
    left: Rush16CalibrationWitness,
    right: Rush16CalibrationWitness,
) -> bool:
    return (
        left.spec_filename,
        left.semantic_path,
        left.track,
        left.address,
    ) == (
        right.spec_filename,
        right.semantic_path,
        right.track,
        right.address,
    )


def _lookup_target_raw(
    family: Rush16CalibrationFamily,
    rows: Sequence[Mapping[str, object]],
) -> dict[str, int]:
    roles = {witness.role for witness in family.witnesses}
    if (
        family.device != RUSH01_DEVICE_A4
        and family.converter_kind == "boolean"
        and any(
            {str(row.get("witness_role")) for row in rows if row.get("raw_value") == candidate}
            != roles
            for candidate in family.candidates
        )
    ):
        return {}
    result: dict[str, int] = {}
    for target in family.targets:
        effective = rush16_effective_requested_value(target.requested_value)
        fingerprint = _fingerprint(effective)
        candidates: dict[int, set[str]] = {}
        displays: dict[int, set[str]] = {}
        approved_raws: set[int] = set()
        for row in rows:
            approvals = _require_object_sequence(
                row.get("approved_requested_values"), "approved values"
            )
            raw = row.get("raw_value")
            role = row.get("witness_role")
            if isinstance(raw, int) and isinstance(role, str):
                candidates.setdefault(raw, set()).add(role)
                displays.setdefault(raw, set()).add(_fingerprint(row.get("display_value")))
                if fingerprint in {_fingerprint(value) for value in approvals}:
                    approved_raws.add(raw)
        matching = [
            raw
            for raw, observed_roles in candidates.items()
            if raw in approved_raws
            and observed_roles == roles
            and len(displays.get(raw, set())) == 1
            and (
                family.device != RUSH01_DEVICE_A4
                or _raw_has_saved_kit_evidence_for_all_locations(family, rows, raw)
            )
        ]
        if len(matching) != 1:
            continue
        raw = matching[0]
        neighbor_roles = roles if family.device != RUSH01_DEVICE_A4 else None
        if family.converter_kind in {
            "selector",
            "boolean",
        } and not _selector_neighbors_observed(family, rows, raw, neighbor_roles):
            continue
        result[_fingerprint(target.requested_value)] = raw
    return result


def _selector_neighbors_observed(
    family: Rush16CalibrationFamily,
    rows: Sequence[Mapping[str, object]],
    raw: int,
    roles: set[str] | None = None,
) -> bool:
    candidate_index = family.candidates.index(raw)
    neighboring = tuple(
        family.candidates[index]
        for index in (candidate_index - 1, candidate_index + 1)
        if 0 <= index < len(family.candidates)
    )
    if not neighboring:
        return True
    target_display = {
        _fingerprint(row.get("display_value")) for row in rows if row.get("raw_value") == raw
    }
    if roles is not None:
        return all(
            {str(row.get("witness_role")) for row in rows if row.get("raw_value") == neighbor}
            == roles
            and {
                _fingerprint(row.get("display_value"))
                for row in rows
                if row.get("raw_value") == neighbor
            }
            != target_display
            for neighbor in neighboring
        )
    primary_role = family.witnesses[0].role
    return all(
        any(
            row.get("witness_role") == primary_role and row.get("raw_value") == neighbor
            for row in rows
        )
        and {
            _fingerprint(row.get("display_value"))
            for row in rows
            if row.get("raw_value") == neighbor and row.get("witness_role") == primary_role
        }
        != target_display
        for neighbor in neighboring
    )


def _affine_target_raw(
    family: Rush16CalibrationFamily,
    rows: Sequence[Mapping[str, object]],
) -> dict[str, int]:
    predicted = _predict_affine_target_raws(family, rows)
    result: dict[str, int] = {}
    for target in family.targets:
        value = rush16_effective_requested_value(target.requested_value)
        fingerprint = _fingerprint(value)
        raw = predicted.get(fingerprint)
        if raw is None:
            continue
        result[_fingerprint(target.requested_value)] = raw
    return result


def _affine_cross_track_confirmed(
    family: Rush16CalibrationFamily,
    rows: Sequence[Mapping[str, object]],
) -> bool:
    for raw in family.candidates:
        if _raw_has_matching_saved_affine_evidence(family, rows, raw):
            return True
    return False


def _raw_has_saved_kit_evidence_for_all_locations(
    family: Rush16CalibrationFamily,
    rows: Sequence[Mapping[str, object]],
    raw: int,
) -> bool:
    evidence_groups = {
        frozenset(
            candidate.role
            for candidate in family.witnesses
            if _same_witness_location(candidate, witness)
        )
        for witness in family.witnesses
    }
    return all(
        any(
            row.get("raw_value") == raw
            and row.get("witness_role") in group
            and _row_has_saved_payload_change(row)
            for row in rows
        )
        for group in evidence_groups
    )


def _encode_address(
    address: Rush16CalibrationAddress,
    channel: int,
    raw_value: int,
) -> tuple[MidiByteMessage, ...]:
    if address.message_type == MESSAGE_CC:
        if address.controller is None:
            raise ValueError("CC calibration address requires a controller")
        return encode_cc_message(channel, address.controller, raw_value)
    if address.message_type == MESSAGE_CC14:
        if address.controller is None or address.controller_lsb is None:
            raise ValueError("CC14 calibration address requires MSB and LSB controllers")
        return encode_cc14_messages(
            channel,
            address.controller,
            address.controller_lsb,
            raw_value,
        )
    if address.nrpn_address is None:
        raise ValueError("NRPN calibration address requires an address")
    return encode_nrpn_messages(channel, *address.nrpn_address, raw_value)


def _validate_distinct_family_witness_addresses(
    families: Sequence[Rush16CalibrationFamily],
) -> None:
    routes: dict[tuple[str, Rush16CalibrationAddress], tuple[str, str]] = {}
    for family in families:
        if not family.supported or not family.targets:
            continue
        for witness in family.witnesses:
            route = (witness.track, witness.address)
            previous = routes.get(route)
            current = (family.family_id, witness.semantic_path)
            if previous is not None and previous[0] != family.family_id:
                raise ValueError(
                    "RUSH16 calibration families share one outbound address: "
                    f"{previous[0]}:{previous[1]} and {current[0]}:{current[1]}"
                )
            routes[route] = current


def _address_for_target(
    family: Rush16CalibrationFamily,
    semantic_path: str,
) -> Rush16CalibrationAddress:
    relative_path = _track_relative_semantic_path(semantic_path)
    matches = {
        witness.address
        for witness in family.witnesses
        if _track_relative_semantic_path(witness.semantic_path) == relative_path
    }
    if not matches:
        matches = {witness.address for witness in family.witnesses}
    if len(matches) != 1:
        raise ValueError(f"RUSH16 target has no unique calibrated address: {semantic_path}")
    return matches.pop()


def _track_relative_semantic_path(semantic_path: str) -> str:
    parts = semantic_path.split(".", 2)
    if len(parts) != 3 or parts[0] != "tracks" or not parts[1]:
        raise ValueError(f"RUSH16 semantic path has no track prefix: {semantic_path}")
    return parts[2]


def rush16_calibration_display_label(
    plan: Rush16CalibrationPlan,
    step: Rush16CalibrationStep,
) -> str:
    """Name the exact front-panel value the operator must transcribe."""

    family = _family_by_id(plan, step.family_id)
    if family.family_id == "a4_oscillator_coarse_tune":
        return "coarse-tune semitone value (first pitch value)"
    if family.family_id == "a4_oscillator_fine_tune":
        return "fine-tune value (second pitch value)"
    return f"{family.label} value"


def _machine_context_messages(
    device: Rush01Device,
    spec: object,
    witness: Rush16CalibrationWitness,
    channel: int,
    family_id: str,
) -> tuple[MidiByteMessage, ...]:
    if device != RUSH01_DEVICE_RYTM or family_id == "rytm_xt_classic_machine":
        return ()
    machine = rush16_value_at_path(spec, f"tracks.{witness.track}.machine")
    if not isinstance(machine, Mapping) or not isinstance(machine.get("name"), str):
        raise ValueError(f"RUSH16 witness has no machine context: {witness.semantic_path}")
    label = machine["name"]
    values = [profile.machine_value for profile in RYTM_MACHINE_PROFILES if profile.label == label]
    if len(values) != 1:
        raise ValueError(f"RUSH16 witness machine is absent from catalog: {label}")
    return encode_cc_message(channel, _RYTM_MACHINE_CC, values[0])


def _midi_channel(config: Rush01DeviceConfig, track: str) -> int:
    user_channel = config.track_channels.get(track)
    if user_channel is None:
        raise ValueError(f"RUSH16 calibration has no channel for track {track}")
    return user_channel_to_midi(user_channel)


def _summarize_promoted_fields(fields: Sequence[Rush01MidiField]) -> Rush01MidiPlanSummary:
    counts = Counter(field.status for field in fields)
    return Rush01MidiPlanSummary(
        total_fields=len(fields),
        ready_fields=counts[STATUS_READY],
        preserve_reference_fields=counts[STATUS_PRESERVE_REFERENCE],
        manual_setup_fields=counts[STATUS_MANUAL_SETUP_REQUIRED],
        learn_required_fields=counts[STATUS_LEARN_REQUIRED],
        invalid_spec_fields=counts[STATUS_INVALID_SPEC_FIELD],
        configured_ready_fields=sum(
            field.status == STATUS_READY
            and field.channel is not None
            and field.ordered_midi_bytes is not None
            for field in fields
        ),
        transport_message_count=sum(
            len(field.ordered_midi_bytes or ()) for field in fields if field.status == STATUS_READY
        ),
    )


def _family_by_id(plan: Rush16CalibrationPlan, family_id: str) -> Rush16CalibrationFamily:
    matches = tuple(family for family in plan.families if family.family_id == family_id)
    if len(matches) != 1:
        raise ValueError(f"unknown RUSH16 calibration family: {family_id}")
    return matches[0]


def _spec_device(spec: object) -> str:
    root = _mapping(spec, "spec")
    rush16 = _mapping(root.get("rush16"), "spec.rush16")
    device = rush16.get("device")
    if device not in {RUSH01_DEVICE_RYTM, RUSH01_DEVICE_A4}:
        raise ValueError("RUSH16 spec device is invalid")
    return cast(str, device)


def rush16_effective_requested_value(value: object) -> object:
    """Return the operator-facing semantic value from a typed request wrapper."""

    if isinstance(value, Mapping) and "requested" in value:
        return value["requested"]
    return value


def _target_requested_value(path: str, value: object) -> object:
    if path.endswith(".machine") and isinstance(value, Mapping):
        name = value.get("name")
        if isinstance(name, str):
            return name
    return value


def _fingerprint(value: object) -> str:
    return sha256(_canonical_json(value)).hexdigest()


def _canonical_json(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _mapping(value: object, path: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{path} must be a mapping")
    return cast(Mapping[str, object], value)


def _require_object_sequence(value: object, path: str) -> Sequence[object]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        raise ValueError(f"{path} must be a sequence")
    return cast(Sequence[object], value)


def _changed_offsets(before: bytes, after: bytes, *, offset: int = 0) -> list[int]:
    if len(before) != len(after):
        raise ValueError("RUSH16 differential frames must have equal lengths")
    return [
        offset + index for index, (left, right) in enumerate(zip(before, after)) if left != right
    ]


def _witness_to_dict(witness: Rush16CalibrationWitness) -> dict[str, object]:
    return {
        "role": witness.role,
        "spec_filename": witness.spec_filename,
        "semantic_path": witness.semantic_path,
        "track": witness.track,
        "address": _address_to_dict(witness.address),
    }


def _address_to_dict(address: Rush16CalibrationAddress) -> dict[str, object]:
    return {
        "message_type": address.message_type,
        "value_domain": address.value_domain,
        "controller": address.controller,
        "controller_lsb": address.controller_lsb,
        "nrpn_address": (list(address.nrpn_address) if address.nrpn_address is not None else None),
    }


def _address_from_dict(payload: Mapping[str, object]) -> Rush16CalibrationAddress:
    message_type = payload.get("message_type")
    value_domain = payload.get("value_domain")
    if message_type not in {MESSAGE_CC, MESSAGE_CC14, MESSAGE_NRPN}:
        raise ValueError("RUSH16 promotion address message type is invalid")
    if value_domain not in {VALUE_DOMAIN_7BIT, VALUE_DOMAIN_14BIT}:
        raise ValueError("RUSH16 promotion address value domain is invalid")
    controller = payload.get("controller")
    controller_lsb = payload.get("controller_lsb")
    if controller is not None and (isinstance(controller, bool) or not isinstance(controller, int)):
        raise ValueError("RUSH16 promotion address controller is invalid")
    if controller_lsb is not None and (
        isinstance(controller_lsb, bool) or not isinstance(controller_lsb, int)
    ):
        raise ValueError("RUSH16 promotion address LSB controller is invalid")
    raw_nrpn = payload.get("nrpn_address")
    nrpn_address: tuple[int, int] | None = None
    if raw_nrpn is not None:
        values = _require_object_sequence(raw_nrpn, "promotion target address.nrpn_address")
        if len(values) != 2 or any(
            isinstance(value, bool) or not isinstance(value, int) for value in values
        ):
            raise ValueError("RUSH16 promotion address NRPN is invalid")
        nrpn_address = (cast(int, values[0]), cast(int, values[1]))
    return Rush16CalibrationAddress(
        message_type=cast(Rush01MessageType, message_type),
        value_domain=cast(Rush01ValueDomain, value_domain),
        controller=cast(int | None, controller),
        controller_lsb=cast(int | None, controller_lsb),
        nrpn_address=nrpn_address,
    )


def _target_to_dict(target: Rush16CalibrationTarget) -> dict[str, object]:
    return {
        "spec_filename": target.spec_filename,
        "semantic_path": target.semantic_path,
        "requested_value": target.requested_value,
        "requested_fingerprint": target.requested_fingerprint,
    }


def _step_to_dict(step: Rush16CalibrationStep) -> dict[str, object]:
    return {
        "step_id": step.step_id,
        "sequence": step.sequence,
        "family_id": step.family_id,
        "witness_role": step.witness_role,
        "spec_filename": step.spec_filename,
        "semantic_path": step.semantic_path,
        "track": step.track,
        "raw_value": step.raw_value,
        "value_domain": step.value_domain,
        "context_messages": [list(packet) for packet in step.context_messages],
        "candidate_messages": [list(packet) for packet in step.candidate_messages],
        "ordered_messages": [list(packet) for packet in step.ordered_messages],
    }


__all__ = [
    "RUSH16_CALIBRATION_VERSION",
    "Rush16CalibrationAddress",
    "Rush16CalibrationFamily",
    "Rush16CalibrationPlan",
    "Rush16CalibrationProgress",
    "Rush16CalibrationStep",
    "Rush16CalibrationTarget",
    "Rush16CalibrationWitness",
    "accept_rush16_calibration_observation",
    "analyze_rush16_kit_differential",
    "apply_rush16_calibration_promotions",
    "build_rush16_calibration_catalog",
    "build_rush16_calibration_plan",
    "load_or_create_rush16_checkpoint",
    "next_rush16_calibration_step",
    "rush16_calibration_plan_sha256",
    "rush16_calibration_plan_to_dict",
    "rush16_calibration_display_label",
    "rush16_calibration_progress",
    "rush16_calibration_step_requires_saved_kit",
    "rush16_effective_requested_value",
    "rush16_steps_share_witness_location",
    "validate_rush16_calibration_baseline_continuity",
    "write_rush16_checkpoint",
]
