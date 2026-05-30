"""Snapshot-grounded all-12-pad Analog Rytm performance shell.

This shell is the live-safe counterpart to the V1.34 four-pad command feel. It
anchors to a captured current-kit SysEx dump, mutates promoted CC-addressable
rows for all 12 pads, and sends only through an injected sender.
"""

from __future__ import annotations

import hashlib
import sys
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field, replace
from types import MappingProxyType
from typing import Final, Literal, TypeAlias

from ..data.analog_rytm_kit_layout import (
    RYTM_KIT_TRACK_SOUND_SIZE,
    RYTM_KIT_TRACKS_OFFSET,
    RYTM_SOUND_FIELD_BY_NRPN_LSB,
)
from ..data.analog_rytm_midi import (
    ANALOG_RYTM_VALIDATED_RUNTIME_CC,
    AnalogRytmCcMapping,
    get_machine_src_mappings,
)
from ..data.analog_rytm_style_recipes import AnalogRytmRenderedStyleEvent
from ..data.rytm_machine_catalog import RYTM_MACHINE_PROFILES, RytmMachineProfile
from ..devices.strategies import RytmKitSnapshot, rytm_snapshot_payload_fingerprint
from ..midi_io import Sender, send_cc
from .analog_rytm_12_pad_shell import classify_rytm_pad_role

InputFunc: TypeAlias = Callable[[str], str]
SnapshotDepth: TypeAlias = Literal["micro", "groove", "strong"]
SnapshotCommandKind: TypeAlias = Literal["scene", "zone"]
SnapshotZone: TypeAlias = Literal["full", "src", "filter", "grit"]
SnapshotSessionMode: TypeAlias = Literal["live", "studio"]
SnapshotSessionDepth: TypeAlias = Literal["gentle", "normal", "strong", "wild"]
SnapshotTunePolicy: TypeAlias = Literal["off", "micro", "normal", "wide"]
SnapshotLane: TypeAlias = Literal["tune", "noise", "fx", "filter", "amp", "lfo"]
SnapshotLanePolicy: TypeAlias = Literal["off", "micro", "normal", "wide"]
SnapshotRandomizerRole: TypeAlias = Literal[
    "kick",
    "snare",
    "tom",
    "hat",
    "cymbal",
    "synth",
    "noise",
    "perc",
]
SnapshotRandomizerAmount: TypeAlias = Literal["micro", "normal", "wide"]
SnapshotRandomizerDensity: TypeAlias = Literal[
    "off",
    "low",
    "medium",
    "high",
    "full",
]
SnapshotRandomizerBias: TypeAlias = Literal[
    "neutral",
    "darker",
    "brighter",
    "tighter",
    "looser",
    "grittier",
]
SelectorValueRange: TypeAlias = tuple[int, int]

_TRACK_COUNT: Final[int] = 12
_MACHINE_UNKNOWN: Final[str] = "unknown"
_CMD_PREVIEW: Final[str] = "preview"
_CMD_CHANGES: Final[str] = "changes"
_CMD_SEND: Final[str] = "send"
_CMD_AGAIN: Final[str] = "again"
_CMD_NEXT: Final[str] = "next"
_CMD_GO: Final[str] = "go"
_CMD_RANDOMIZE: Final[str] = "randomize"
_CMD_STATUS: Final[str] = "status"
_CMD_MODE: Final[str] = "mode"
_CMD_DEPTH: Final[str] = "depth"
_CMD_LOCK: Final[str] = "lock"
_CMD_UNLOCK: Final[str] = "unlock"
_CMD_PAD: Final[str] = "pad"
_CMD_PRESET: Final[str] = "preset"
_CMD_GUARDS: Final[str] = "guards"
_CMD_TUNE: Final[str] = "tune"
_CMD_LANE: Final[str] = "lane"
_CMD_UNDO: Final[str] = "u"
_CMD_RESET: Final[str] = "z"
_CMD_FRESH: Final[str] = "fresh"
_CMD_KIT: Final[str] = "kit"
_CMD_RESNAPSHOT: Final[str] = "resnapshot"
_CMD_DRUM_CORE: Final[str] = "drum-core"
_CMD_QUIT: Final[str] = "q"
_CMD_HELP: Final[str] = "help"
_CMD_S1A: Final[str] = "s1a"
_CMD_S3A: Final[str] = "s3a"
_CMD_S3B: Final[str] = "s3b"
_CMD_S4B: Final[str] = "s4b"
_CMD_FOUR: Final[str] = "4"
_CMD_Y: Final[str] = "y"
_CMD_V: Final[str] = "v"
_CMD_N: Final[str] = "n"
_DEPTH_MICRO: Final[SnapshotDepth] = "micro"
_DEPTH_GROOVE: Final[SnapshotDepth] = "groove"
_DEPTH_STRONG: Final[SnapshotDepth] = "strong"
_SESSION_MODE_LIVE: Final[SnapshotSessionMode] = "live"
_SESSION_MODE_STUDIO: Final[SnapshotSessionMode] = "studio"
_SESSION_DEPTH_GENTLE: Final[SnapshotSessionDepth] = "gentle"
_SESSION_DEPTH_NORMAL: Final[SnapshotSessionDepth] = "normal"
_SESSION_DEPTH_STRONG: Final[SnapshotSessionDepth] = "strong"
_SESSION_DEPTH_WILD: Final[SnapshotSessionDepth] = "wild"
_TUNE_POLICY_OFF: Final[SnapshotTunePolicy] = "off"
_TUNE_POLICY_MICRO: Final[SnapshotTunePolicy] = "micro"
_TUNE_POLICY_NORMAL: Final[SnapshotTunePolicy] = "normal"
_TUNE_POLICY_WIDE: Final[SnapshotTunePolicy] = "wide"
_LANE_TUNE: Final[SnapshotLane] = "tune"
_LANE_NOISE: Final[SnapshotLane] = "noise"
_LANE_FX: Final[SnapshotLane] = "fx"
_LANE_FILTER: Final[SnapshotLane] = "filter"
_LANE_AMP: Final[SnapshotLane] = "amp"
_LANE_LFO: Final[SnapshotLane] = "lfo"
_LANE_POLICY_OFF: Final[SnapshotLanePolicy] = "off"
_LANE_POLICY_MICRO: Final[SnapshotLanePolicy] = "micro"
_LANE_POLICY_NORMAL: Final[SnapshotLanePolicy] = "normal"
_LANE_POLICY_WIDE: Final[SnapshotLanePolicy] = "wide"
_RANDOMIZER_ROLE_KICK: Final[SnapshotRandomizerRole] = "kick"
_RANDOMIZER_ROLE_SNARE: Final[SnapshotRandomizerRole] = "snare"
_RANDOMIZER_ROLE_TOM: Final[SnapshotRandomizerRole] = "tom"
_RANDOMIZER_ROLE_HAT: Final[SnapshotRandomizerRole] = "hat"
_RANDOMIZER_ROLE_CYMBAL: Final[SnapshotRandomizerRole] = "cymbal"
_RANDOMIZER_ROLE_SYNTH: Final[SnapshotRandomizerRole] = "synth"
_RANDOMIZER_ROLE_NOISE: Final[SnapshotRandomizerRole] = "noise"
_RANDOMIZER_ROLE_PERC: Final[SnapshotRandomizerRole] = "perc"
_RANDOMIZER_AMOUNT_MICRO: Final[SnapshotRandomizerAmount] = "micro"
_RANDOMIZER_AMOUNT_NORMAL: Final[SnapshotRandomizerAmount] = "normal"
_RANDOMIZER_AMOUNT_WIDE: Final[SnapshotRandomizerAmount] = "wide"
_RANDOMIZER_DENSITY_OFF: Final[SnapshotRandomizerDensity] = "off"
_RANDOMIZER_DENSITY_LOW: Final[SnapshotRandomizerDensity] = "low"
_RANDOMIZER_DENSITY_MEDIUM: Final[SnapshotRandomizerDensity] = "medium"
_RANDOMIZER_DENSITY_HIGH: Final[SnapshotRandomizerDensity] = "high"
_RANDOMIZER_DENSITY_FULL: Final[SnapshotRandomizerDensity] = "full"
_RANDOMIZER_BIAS_NEUTRAL: Final[SnapshotRandomizerBias] = "neutral"
_RANDOMIZER_BIAS_DARKER: Final[SnapshotRandomizerBias] = "darker"
_RANDOMIZER_BIAS_BRIGHTER: Final[SnapshotRandomizerBias] = "brighter"
_RANDOMIZER_BIAS_TIGHTER: Final[SnapshotRandomizerBias] = "tighter"
_RANDOMIZER_BIAS_LOOSER: Final[SnapshotRandomizerBias] = "looser"
_RANDOMIZER_BIAS_GRITTIER: Final[SnapshotRandomizerBias] = "grittier"
_ZONE_FULL: Final[SnapshotZone] = "full"
_ZONE_SRC: Final[SnapshotZone] = "src"
_ZONE_FILTER: Final[SnapshotZone] = "filter"
_ZONE_GRIT: Final[SnapshotZone] = "grit"
_KIND_SCENE: Final[SnapshotCommandKind] = "scene"
_KIND_ZONE: Final[SnapshotCommandKind] = "zone"
_FILTER_SECTION: Final[str] = "FILTER"
_AMP_SECTION: Final[str] = "AMP"
_LFO_SECTION: Final[str] = "LFO"
_AMP_ATTACK_TIME: Final[str] = "Amp Attack Time"
_PAD_1_TUNE_WINDOW: Final[int] = 3
_LEVEL_PARAMETERS: Final[frozenset[str]] = frozenset({"Level", "Track Level", "Amp Volume"})
_GENERAL_SCOPES: Final[frozenset[str]] = frozenset({"filter", "amp", "lfo"})
_PROMOTED_SRC_MUTATION_STATUSES: Final[frozenset[str]] = frozenset(
    {"validated_runtime", "documented_only"}
)
_SNAPSHOT_OMITTED_MACHINE_SRC_ROWS: Final[frozenset[tuple[str, str]]] = frozenset(
    {("sy_raw", "Noise Level")}
)
_SNAPSHOT_PRESERVED_SELECTOR_ROWS: Final[frozenset[tuple[str, str]]] = frozenset(
    {("sy_raw", "Waveform 1"), ("sy_raw", "Waveform 2")}
)
_ZONE_LAYERING_HINT: Final[str] = (
    "zone commands layer on the current staged plan; "
    "use fresh first for anchor-only zone changes"
)

_MACHINE_PROFILE_BY_VALUE: Final[Mapping[int, RytmMachineProfile]] = MappingProxyType(
    {profile.machine_value: profile for profile in RYTM_MACHINE_PROFILES}
)
_DEPTH_ALIASES: Final[Mapping[str, SnapshotDepth]] = MappingProxyType(
    {
        _DEPTH_MICRO: _DEPTH_MICRO,
        "1": _DEPTH_MICRO,
        _DEPTH_GROOVE: _DEPTH_GROOVE,
        "2": _DEPTH_GROOVE,
        _DEPTH_STRONG: _DEPTH_STRONG,
        "3": _DEPTH_STRONG,
    }
)
_DEPTH_WINDOW: Final[Mapping[SnapshotDepth, int]] = MappingProxyType(
    {
        _DEPTH_MICRO: 3,
        _DEPTH_GROOVE: 8,
        _DEPTH_STRONG: 16,
    }
)
_SESSION_DEPTH_ORDER: Final[Mapping[SnapshotSessionDepth, int]] = MappingProxyType(
    {
        _SESSION_DEPTH_GENTLE: 0,
        _SESSION_DEPTH_NORMAL: 1,
        _SESSION_DEPTH_STRONG: 2,
        _SESSION_DEPTH_WILD: 3,
    }
)
_SNAPSHOT_DEPTH_TO_SESSION_DEPTH: Final[Mapping[SnapshotDepth, SnapshotSessionDepth]] = (
    MappingProxyType(
        {
            _DEPTH_MICRO: _SESSION_DEPTH_GENTLE,
            _DEPTH_GROOVE: _SESSION_DEPTH_NORMAL,
            _DEPTH_STRONG: _SESSION_DEPTH_STRONG,
        }
    )
)
_SESSION_DEPTH_ALIASES: Final[Mapping[str, SnapshotSessionDepth]] = MappingProxyType(
    {
        _SESSION_DEPTH_GENTLE: _SESSION_DEPTH_GENTLE,
        _SESSION_DEPTH_NORMAL: _SESSION_DEPTH_NORMAL,
        _SESSION_DEPTH_STRONG: _SESSION_DEPTH_STRONG,
        _SESSION_DEPTH_WILD: _SESSION_DEPTH_WILD,
        _DEPTH_MICRO: _SESSION_DEPTH_GENTLE,
        _DEPTH_GROOVE: _SESSION_DEPTH_NORMAL,
        "1": _SESSION_DEPTH_GENTLE,
        "2": _SESSION_DEPTH_NORMAL,
        "3": _SESSION_DEPTH_STRONG,
        "4": _SESSION_DEPTH_WILD,
    }
)
_SESSION_MODES: Final[frozenset[SnapshotSessionMode]] = frozenset(
    {_SESSION_MODE_LIVE, _SESSION_MODE_STUDIO}
)
_TUNE_POLICIES: Final[frozenset[SnapshotTunePolicy]] = frozenset(
    {
        _TUNE_POLICY_OFF,
        _TUNE_POLICY_MICRO,
        _TUNE_POLICY_NORMAL,
        _TUNE_POLICY_WIDE,
    }
)
_LANES: Final[tuple[SnapshotLane, ...]] = (
    _LANE_TUNE,
    _LANE_NOISE,
    _LANE_FX,
    _LANE_FILTER,
    _LANE_AMP,
    _LANE_LFO,
)
_LANE_POLICIES: Final[frozenset[SnapshotLanePolicy]] = frozenset(
    {
        _LANE_POLICY_OFF,
        _LANE_POLICY_MICRO,
        _LANE_POLICY_NORMAL,
        _LANE_POLICY_WIDE,
    }
)
_LIVE_LANE_POLICIES: Final[Mapping[SnapshotLane, SnapshotLanePolicy]] = MappingProxyType(
    {
        _LANE_TUNE: _LANE_POLICY_MICRO,
        _LANE_NOISE: _LANE_POLICY_NORMAL,
        _LANE_FX: _LANE_POLICY_MICRO,
        _LANE_FILTER: _LANE_POLICY_NORMAL,
        _LANE_AMP: _LANE_POLICY_NORMAL,
        _LANE_LFO: _LANE_POLICY_OFF,
    }
)
_STUDIO_LANE_POLICIES: Final[Mapping[SnapshotLane, SnapshotLanePolicy]] = MappingProxyType(
    {
        _LANE_TUNE: _LANE_POLICY_WIDE,
        _LANE_NOISE: _LANE_POLICY_WIDE,
        _LANE_FX: _LANE_POLICY_WIDE,
        _LANE_FILTER: _LANE_POLICY_WIDE,
        _LANE_AMP: _LANE_POLICY_WIDE,
        _LANE_LFO: _LANE_POLICY_WIDE,
    }
)
_TUNE_POLICY_MAX_STEPS: Final[Mapping[SnapshotTunePolicy, int]] = MappingProxyType(
    {
        _TUNE_POLICY_OFF: 0,
        _TUNE_POLICY_MICRO: 1,
        _TUNE_POLICY_NORMAL: 2,
        _TUNE_POLICY_WIDE: 4,
    }
)
_RANDOMIZER_ROLES: Final[frozenset[SnapshotRandomizerRole]] = frozenset(
    {
        _RANDOMIZER_ROLE_KICK,
        _RANDOMIZER_ROLE_SNARE,
        _RANDOMIZER_ROLE_TOM,
        _RANDOMIZER_ROLE_HAT,
        _RANDOMIZER_ROLE_CYMBAL,
        _RANDOMIZER_ROLE_SYNTH,
        _RANDOMIZER_ROLE_NOISE,
        _RANDOMIZER_ROLE_PERC,
    }
)
_RANDOMIZER_AMOUNTS: Final[frozenset[SnapshotRandomizerAmount]] = frozenset(
    {
        _RANDOMIZER_AMOUNT_MICRO,
        _RANDOMIZER_AMOUNT_NORMAL,
        _RANDOMIZER_AMOUNT_WIDE,
    }
)
_RANDOMIZER_DENSITIES: Final[frozenset[SnapshotRandomizerDensity]] = frozenset(
    {
        _RANDOMIZER_DENSITY_OFF,
        _RANDOMIZER_DENSITY_LOW,
        _RANDOMIZER_DENSITY_MEDIUM,
        _RANDOMIZER_DENSITY_HIGH,
        _RANDOMIZER_DENSITY_FULL,
    }
)
_RANDOMIZER_BIASES: Final[frozenset[SnapshotRandomizerBias]] = frozenset(
    {
        _RANDOMIZER_BIAS_NEUTRAL,
        _RANDOMIZER_BIAS_DARKER,
        _RANDOMIZER_BIAS_BRIGHTER,
        _RANDOMIZER_BIAS_TIGHTER,
        _RANDOMIZER_BIAS_LOOSER,
        _RANDOMIZER_BIAS_GRITTIER,
    }
)
_RANDOMIZER_AMOUNT_DEPTH: Final[Mapping[SnapshotRandomizerAmount, SnapshotSessionDepth]] = (
    MappingProxyType(
        {
            _RANDOMIZER_AMOUNT_MICRO: _SESSION_DEPTH_GENTLE,
            _RANDOMIZER_AMOUNT_NORMAL: _SESSION_DEPTH_NORMAL,
            _RANDOMIZER_AMOUNT_WIDE: _SESSION_DEPTH_STRONG,
        }
    )
)
_RANDOMIZER_DENSITY_PERCENT: Final[Mapping[SnapshotRandomizerDensity, int]] = MappingProxyType(
    {
        _RANDOMIZER_DENSITY_OFF: 0,
        _RANDOMIZER_DENSITY_LOW: 25,
        _RANDOMIZER_DENSITY_MEDIUM: 50,
        _RANDOMIZER_DENSITY_HIGH: 75,
        _RANDOMIZER_DENSITY_FULL: 100,
    }
)
_LANE_POLICY_SESSION_DEPTH: Final[Mapping[SnapshotLanePolicy, SnapshotSessionDepth]] = (
    MappingProxyType(
        {
            _LANE_POLICY_MICRO: _SESSION_DEPTH_GENTLE,
            _LANE_POLICY_NORMAL: _SESSION_DEPTH_NORMAL,
            _LANE_POLICY_WIDE: _SESSION_DEPTH_WILD,
        }
    )
)
_PRESET_LIVE: Final[str] = "live"
_PRESET_KICK_SAFE: Final[str] = "kick-safe"
_PRESET_ALL_GENTLE: Final[str] = "all-gentle"
_PRESET_STUDIO: Final[str] = "studio"
_GUARDS_RESET: Final[str] = "reset"
_LIVE_PAD_CAPS: Final[Mapping[int, SnapshotSessionDepth]] = MappingProxyType(
    {
        1: _SESSION_DEPTH_GENTLE,
        2: _SESSION_DEPTH_NORMAL,
        3: _SESSION_DEPTH_NORMAL,
        4: _SESSION_DEPTH_NORMAL,
        5: _SESSION_DEPTH_GENTLE,
        6: _SESSION_DEPTH_GENTLE,
        7: _SESSION_DEPTH_GENTLE,
        8: _SESSION_DEPTH_GENTLE,
        9: _SESSION_DEPTH_GENTLE,
        10: _SESSION_DEPTH_GENTLE,
        11: _SESSION_DEPTH_NORMAL,
        12: _SESSION_DEPTH_NORMAL,
    }
)
_STUDIO_PAD_CAPS: Final[Mapping[int, SnapshotSessionDepth]] = MappingProxyType(
    {
        1: _SESSION_DEPTH_STRONG,
        2: _SESSION_DEPTH_WILD,
        3: _SESSION_DEPTH_WILD,
        4: _SESSION_DEPTH_WILD,
        5: _SESSION_DEPTH_WILD,
        6: _SESSION_DEPTH_WILD,
        7: _SESSION_DEPTH_WILD,
        8: _SESSION_DEPTH_WILD,
        9: _SESSION_DEPTH_WILD,
        10: _SESSION_DEPTH_WILD,
        11: _SESSION_DEPTH_WILD,
        12: _SESSION_DEPTH_WILD,
    }
)
_SESSION_DEPTH_WINDOWS: Final[Mapping[SnapshotSessionMode, Mapping[SnapshotSessionDepth, int]]] = (
    MappingProxyType(
        {
            _SESSION_MODE_LIVE: MappingProxyType(
                {
                    _SESSION_DEPTH_GENTLE: 2,
                    _SESSION_DEPTH_NORMAL: 5,
                    _SESSION_DEPTH_STRONG: 8,
                    _SESSION_DEPTH_WILD: 12,
                }
            ),
            _SESSION_MODE_STUDIO: MappingProxyType(
                {
                    _SESSION_DEPTH_GENTLE: 3,
                    _SESSION_DEPTH_NORMAL: 8,
                    _SESSION_DEPTH_STRONG: 16,
                    _SESSION_DEPTH_WILD: 24,
                }
            ),
        }
    )
)


@dataclass(frozen=True)
class SnapshotShellCommand:
    """One old-feel live-safe snapshot shell command."""

    name: str
    label: str
    kind: SnapshotCommandKind
    zone: SnapshotZone
    depth: SnapshotDepth


@dataclass(frozen=True)
class SnapshotPadRandomizerContract:
    """Per-pad OXI-style musical randomizer guardrail contract."""

    role: SnapshotRandomizerRole
    amount: SnapshotRandomizerAmount
    density: SnapshotRandomizerDensity
    bias: SnapshotRandomizerBias


_RANDOMIZER_DEFAULT_CONTRACT_BY_ROLE: Final[
    Mapping[SnapshotRandomizerRole, SnapshotPadRandomizerContract]
] = MappingProxyType(
    {
        _RANDOMIZER_ROLE_KICK: SnapshotPadRandomizerContract(
            role=_RANDOMIZER_ROLE_KICK,
            amount=_RANDOMIZER_AMOUNT_MICRO,
            density=_RANDOMIZER_DENSITY_LOW,
            bias=_RANDOMIZER_BIAS_TIGHTER,
        ),
        _RANDOMIZER_ROLE_SNARE: SnapshotPadRandomizerContract(
            role=_RANDOMIZER_ROLE_SNARE,
            amount=_RANDOMIZER_AMOUNT_NORMAL,
            density=_RANDOMIZER_DENSITY_MEDIUM,
            bias=_RANDOMIZER_BIAS_NEUTRAL,
        ),
        _RANDOMIZER_ROLE_TOM: SnapshotPadRandomizerContract(
            role=_RANDOMIZER_ROLE_TOM,
            amount=_RANDOMIZER_AMOUNT_MICRO,
            density=_RANDOMIZER_DENSITY_MEDIUM,
            bias=_RANDOMIZER_BIAS_TIGHTER,
        ),
        _RANDOMIZER_ROLE_HAT: SnapshotPadRandomizerContract(
            role=_RANDOMIZER_ROLE_HAT,
            amount=_RANDOMIZER_AMOUNT_NORMAL,
            density=_RANDOMIZER_DENSITY_HIGH,
            bias=_RANDOMIZER_BIAS_BRIGHTER,
        ),
        _RANDOMIZER_ROLE_CYMBAL: SnapshotPadRandomizerContract(
            role=_RANDOMIZER_ROLE_CYMBAL,
            amount=_RANDOMIZER_AMOUNT_NORMAL,
            density=_RANDOMIZER_DENSITY_MEDIUM,
            bias=_RANDOMIZER_BIAS_BRIGHTER,
        ),
        _RANDOMIZER_ROLE_SYNTH: SnapshotPadRandomizerContract(
            role=_RANDOMIZER_ROLE_SYNTH,
            amount=_RANDOMIZER_AMOUNT_NORMAL,
            density=_RANDOMIZER_DENSITY_MEDIUM,
            bias=_RANDOMIZER_BIAS_NEUTRAL,
        ),
        _RANDOMIZER_ROLE_NOISE: SnapshotPadRandomizerContract(
            role=_RANDOMIZER_ROLE_NOISE,
            amount=_RANDOMIZER_AMOUNT_MICRO,
            density=_RANDOMIZER_DENSITY_LOW,
            bias=_RANDOMIZER_BIAS_NEUTRAL,
        ),
        _RANDOMIZER_ROLE_PERC: SnapshotPadRandomizerContract(
            role=_RANDOMIZER_ROLE_PERC,
            amount=_RANDOMIZER_AMOUNT_NORMAL,
            density=_RANDOMIZER_DENSITY_MEDIUM,
            bias=_RANDOMIZER_BIAS_NEUTRAL,
        ),
    }
)


@dataclass(frozen=True)
class RytmSnapshotShellAnchor:
    """Decoded current-kit anchor rows promoted for live-safe mutation."""

    kit_name: str
    fingerprint: str
    events: tuple[AnalogRytmRenderedStyleEvent, ...]
    events_by_pad: Mapping[int, tuple[AnalogRytmRenderedStyleEvent, ...]]


ResnapshotFunc: TypeAlias = Callable[[], RytmSnapshotShellAnchor | None]


@dataclass(frozen=True)
class SnapshotSessionGuardrails:
    """Session-only live/studio mutation guardrails."""

    mode: SnapshotSessionMode
    global_depth: SnapshotSessionDepth
    pad_overrides: Mapping[int, SnapshotSessionDepth]
    locked_pads: frozenset[int]
    live_pad_caps: Mapping[int, SnapshotSessionDepth]
    tune_policy: SnapshotTunePolicy
    lane_policies: Mapping[SnapshotLane, SnapshotLanePolicy]
    randomizer_overrides: Mapping[int, SnapshotPadRandomizerContract]


def default_snapshot_session_guardrails() -> SnapshotSessionGuardrails:
    """Return the default live performance guardrail profile."""

    return SnapshotSessionGuardrails(
        mode=_SESSION_MODE_LIVE,
        global_depth=_SESSION_DEPTH_NORMAL,
        pad_overrides=MappingProxyType({}),
        locked_pads=frozenset(),
        live_pad_caps=_LIVE_PAD_CAPS,
        tune_policy=_TUNE_POLICY_MICRO,
        lane_policies=_LIVE_LANE_POLICIES,
        randomizer_overrides=MappingProxyType({}),
    )


def _snapshot_session_guardrails(
    *,
    mode: SnapshotSessionMode,
    global_depth: SnapshotSessionDepth,
    pad_overrides: Mapping[int, SnapshotSessionDepth] | None = None,
    locked_pads: frozenset[int] = frozenset(),
    tune_policy: SnapshotTunePolicy | None = None,
    lane_policies: Mapping[SnapshotLane, SnapshotLanePolicy] | None = None,
    randomizer_overrides: Mapping[int, SnapshotPadRandomizerContract] | None = None,
) -> SnapshotSessionGuardrails:
    selected_tune_policy = tune_policy or _default_tune_policy_for_mode(mode)
    selected_lane_policies = lane_policies or _default_lane_policies_for_mode(mode)
    selected_lane_policies_dict = dict(selected_lane_policies)
    selected_lane_policies_dict[_LANE_TUNE] = selected_tune_policy
    return SnapshotSessionGuardrails(
        mode=mode,
        global_depth=global_depth,
        pad_overrides=MappingProxyType(dict(pad_overrides or {})),
        locked_pads=locked_pads,
        live_pad_caps=_LIVE_PAD_CAPS,
        tune_policy=selected_tune_policy,
        lane_policies=MappingProxyType(selected_lane_policies_dict),
        randomizer_overrides=MappingProxyType(dict(randomizer_overrides or {})),
    )


def _preset_guardrails(preset: str) -> SnapshotSessionGuardrails | None:
    if preset in {_PRESET_LIVE, _PRESET_ALL_GENTLE}:
        return _snapshot_session_guardrails(
            mode=_SESSION_MODE_LIVE,
            global_depth=_SESSION_DEPTH_GENTLE,
        )
    if preset == _PRESET_KICK_SAFE:
        return _snapshot_session_guardrails(
            mode=_SESSION_MODE_LIVE,
            global_depth=_SESSION_DEPTH_GENTLE,
            locked_pads=frozenset({1}),
        )
    if preset == _PRESET_STUDIO:
        return _snapshot_session_guardrails(
            mode=_SESSION_MODE_STUDIO,
            global_depth=_SESSION_DEPTH_WILD,
        )
    return None


@dataclass(frozen=True)
class RytmSnapshotShellState:
    """Current staged snapshot-shell plan."""

    anchor: RytmSnapshotShellAnchor
    mutation_name: str = "anchor"
    current_events: tuple[AnalogRytmRenderedStyleEvent, ...] = ()
    previous_events: tuple[AnalogRytmRenderedStyleEvent, ...] | None = None
    sent_message_count: int = 0
    last_command_name: str | None = None
    last_depth: SnapshotDepth | None = None
    mutation_generation: int = 0
    guardrails: SnapshotSessionGuardrails = field(
        default_factory=default_snapshot_session_guardrails
    )


SNAPSHOT_SHELL_COMMANDS: Final[Mapping[str, SnapshotShellCommand]] = MappingProxyType(
    {
        _CMD_S1A: SnapshotShellCommand(
            name=_CMD_S1A,
            label="Rolling Light",
            kind=_KIND_SCENE,
            zone=_ZONE_FULL,
            depth=_DEPTH_MICRO,
        ),
        _CMD_S3A: SnapshotShellCommand(
            name=_CMD_S3A,
            label="Intense Motion",
            kind=_KIND_SCENE,
            zone=_ZONE_FULL,
            depth=_DEPTH_GROOVE,
        ),
        _CMD_S3B: SnapshotShellCommand(
            name=_CMD_S3B,
            label="Intense Grit",
            kind=_KIND_SCENE,
            zone=_ZONE_GRIT,
            depth=_DEPTH_GROOVE,
        ),
        _CMD_S4B: SnapshotShellCommand(
            name=_CMD_S4B,
            label="Wild Maximum",
            kind=_KIND_SCENE,
            zone=_ZONE_FULL,
            depth=_DEPTH_STRONG,
        ),
        _CMD_FOUR: SnapshotShellCommand(
            name=_CMD_FOUR,
            label="Command 4",
            kind=_KIND_SCENE,
            zone=_ZONE_FULL,
            depth=_DEPTH_STRONG,
        ),
        _CMD_RANDOMIZE: SnapshotShellCommand(
            name=_CMD_RANDOMIZE,
            label="Randomize",
            kind=_KIND_SCENE,
            zone=_ZONE_FULL,
            depth=_DEPTH_STRONG,
        ),
        _CMD_Y: SnapshotShellCommand(
            name=_CMD_Y,
            label="SRC/Morph",
            kind=_KIND_ZONE,
            zone=_ZONE_SRC,
            depth=_DEPTH_MICRO,
        ),
        _CMD_V: SnapshotShellCommand(
            name=_CMD_V,
            label="Filter",
            kind=_KIND_ZONE,
            zone=_ZONE_FILTER,
            depth=_DEPTH_MICRO,
        ),
        _CMD_N: SnapshotShellCommand(
            name=_CMD_N,
            label="Grit",
            kind=_KIND_ZONE,
            zone=_ZONE_GRIT,
            depth=_DEPTH_MICRO,
        ),
    }
)


def _no_sleep(_seconds: float) -> None:
    return None


def _clamp_midi_value(value: int) -> int:
    return max(0, min(127, value))


def _valid_pad_number(value: str) -> int | None:
    try:
        pad = int(value)
    except ValueError:
        return None
    if 1 <= pad <= _TRACK_COUNT:
        return pad
    return None


def _pad_caps_for_mode(mode: SnapshotSessionMode) -> Mapping[int, SnapshotSessionDepth]:
    if mode == _SESSION_MODE_LIVE:
        return _LIVE_PAD_CAPS
    return _STUDIO_PAD_CAPS


def _default_tune_policy_for_mode(mode: SnapshotSessionMode) -> SnapshotTunePolicy:
    if mode == _SESSION_MODE_STUDIO:
        return _TUNE_POLICY_WIDE
    return _TUNE_POLICY_MICRO


def _default_lane_policies_for_mode(
    mode: SnapshotSessionMode,
) -> Mapping[SnapshotLane, SnapshotLanePolicy]:
    if mode == _SESSION_MODE_STUDIO:
        return _STUDIO_LANE_POLICIES
    return _LIVE_LANE_POLICIES


def _randomizer_role_for_machine(machine_key: str) -> SnapshotRandomizerRole:
    role = classify_rytm_pad_role(machine_key)
    if role == "kick":
        return _RANDOMIZER_ROLE_KICK
    if role == "snare":
        return _RANDOMIZER_ROLE_SNARE
    if role == "tom":
        return _RANDOMIZER_ROLE_TOM
    if role == "hat":
        return _RANDOMIZER_ROLE_HAT
    if role == "cymbal":
        return _RANDOMIZER_ROLE_CYMBAL
    if role == "synth":
        return _RANDOMIZER_ROLE_SYNTH
    if role == "utility":
        return _RANDOMIZER_ROLE_NOISE
    return _RANDOMIZER_ROLE_PERC


def _randomizer_default_contract_for_machine(
    machine_key: str,
) -> SnapshotPadRandomizerContract:
    return _RANDOMIZER_DEFAULT_CONTRACT_BY_ROLE[_randomizer_role_for_machine(machine_key)]


def _randomizer_default_contract_for_pad(
    anchor: RytmSnapshotShellAnchor,
    pad: int,
) -> SnapshotPadRandomizerContract:
    pad_events = anchor.events_by_pad[pad]
    if not pad_events:
        return _RANDOMIZER_DEFAULT_CONTRACT_BY_ROLE[_RANDOMIZER_ROLE_PERC]
    return _randomizer_default_contract_for_machine(pad_events[0].machine_key)


def _randomizer_contract_for_pad(
    anchor: RytmSnapshotShellAnchor,
    guardrails: SnapshotSessionGuardrails,
    pad: int,
) -> SnapshotPadRandomizerContract:
    override = guardrails.randomizer_overrides.get(pad)
    if override is not None:
        return override
    return _randomizer_default_contract_for_pad(anchor, pad)


def _randomizer_contracts_for_state(
    state: RytmSnapshotShellState,
) -> Mapping[int, SnapshotPadRandomizerContract]:
    return MappingProxyType(
        {
            pad: _randomizer_contract_for_pad(state.anchor, state.guardrails, pad)
            for pad in range(1, _TRACK_COUNT + 1)
        }
    )


def _min_session_depth(
    first: SnapshotSessionDepth,
    second: SnapshotSessionDepth,
) -> SnapshotSessionDepth:
    if _SESSION_DEPTH_ORDER[first] <= _SESSION_DEPTH_ORDER[second]:
        return first
    return second


def _effective_session_depth(
    *,
    pad: int,
    command_depth: SnapshotDepth,
    guardrails: SnapshotSessionGuardrails,
) -> SnapshotSessionDepth | None:
    if pad in guardrails.locked_pads:
        return None
    command_session_depth = _SNAPSHOT_DEPTH_TO_SESSION_DEPTH[command_depth]
    pad_override = guardrails.pad_overrides.get(pad)
    if pad_override is not None:
        return _min_session_depth(command_session_depth, pad_override)
    depth = _min_session_depth(command_session_depth, guardrails.global_depth)
    pad_cap = _pad_caps_for_mode(guardrails.mode)[pad]
    return _min_session_depth(depth, pad_cap)


def _session_depth_window(
    mode: SnapshotSessionMode,
    depth: SnapshotSessionDepth,
) -> int:
    return _SESSION_DEPTH_WINDOWS[mode][depth]


def _anchor_limited_value(anchor_value: int, proposed_value: int, window: int) -> int:
    low = max(0, anchor_value - window)
    high = min(127, anchor_value + window)
    return max(low, min(high, proposed_value))


def _value_limited_value(value: int, low: int, high: int) -> int:
    return max(low, min(high, _clamp_midi_value(value)))


def _selector_range_for_mapping(
    mapping: AnalogRytmCcMapping,
) -> SelectorValueRange | None:
    if mapping.value_kind != "selector":
        return None
    return mapping.value_min, mapping.value_max


def _selector_range_for_event(
    event: AnalogRytmRenderedStyleEvent,
) -> SelectorValueRange | None:
    if event.value_kind != "selector":
        return None
    return event.value_min, event.value_max


def _normalized_selector_value(value: int, selector_range: SelectorValueRange) -> int:
    low, high = selector_range
    if low <= value <= high:
        return value
    span = (high - low) + 1
    if span <= 1:
        return low
    return low + min(span - 1, (_clamp_midi_value(value) * span) // 128)


def _selector_mutated_value(
    anchor_value: int,
    delta: int,
    selector_range: SelectorValueRange,
    *,
    wrap: bool,
    single_step: bool,
) -> int:
    low, high = selector_range
    span = (high - low) + 1
    if span <= 1:
        return low
    normalized_anchor = _normalized_selector_value(anchor_value, selector_range)
    if single_step:
        delta = 1 if delta > 0 else -1 if delta < 0 else 0
    if not wrap:
        return max(low, min(high, normalized_anchor + delta))
    step = abs(delta) % span
    if step == 0:
        step = 1
    direction = 1 if delta >= 0 else -1
    return low + ((normalized_anchor - low + (direction * step)) % span)


def _wide_selector_discovery_value(
    event: AnalogRytmRenderedStyleEvent,
    command: SnapshotShellCommand,
    generation: int,
    selector_range: SelectorValueRange,
) -> int:
    low, high = selector_range
    span = (high - low) + 1
    if span <= 1:
        return low
    normalized_anchor = _normalized_selector_value(event.value, selector_range)
    payload = (
        f"selector|{command.name}|{generation}|{event.pad}|{event.machine_key}|"
        f"{event.section}|{event.parameter}|{event.value}"
    ).encode()
    value = int.from_bytes(hashlib.blake2s(payload, digest_size=2).digest(), "big")
    step = 1 + (value % (span - 1))
    return low + ((normalized_anchor - low + step) % span)


def _is_snapshot_omitted_mapping(mapping: AnalogRytmCcMapping) -> bool:
    return (
        mapping.machine_key is not None
        and (mapping.machine_key, mapping.parameter) in _SNAPSHOT_OMITTED_MACHINE_SRC_ROWS
    )


def _is_preserved_invalid_selector(
    mapping: AnalogRytmCcMapping,
    value: int,
    selector_range: SelectorValueRange | None,
) -> bool:
    if selector_range is None or mapping.machine_key is None:
        return False
    if (mapping.machine_key, mapping.parameter) not in _SNAPSHOT_PRESERVED_SELECTOR_ROWS:
        return False
    low, high = selector_range
    return not low <= value <= high


def _is_pad_1_foundation_protected_event(event: AnalogRytmRenderedStyleEvent) -> bool:
    if event.pad != 1:
        return False
    if event.section in {_FILTER_SECTION, _LFO_SECTION}:
        return True
    return event.section == _AMP_SECTION and event.parameter == _AMP_ATTACK_TIME


def _is_pad_1_tune_event(event: AnalogRytmRenderedStyleEvent) -> bool:
    return event.pad == 1 and event.source == "machine_src" and "tune" in event.parameter.casefold()


def _is_live_dual_vco_detune_guarded_event(event: AnalogRytmRenderedStyleEvent) -> bool:
    return (
        event.pad in {2, 3}
        and event.machine_key == "dual_vco"
        and event.parameter == "Osc 2 Detune"
    )


def _is_machine_source_tune_event(event: AnalogRytmRenderedStyleEvent) -> bool:
    return event.source == "machine_src" and "tune" in event.parameter.casefold()


def _lane_for_event(event: AnalogRytmRenderedStyleEvent) -> SnapshotLane | None:
    if _is_machine_source_tune_event(event):
        return _LANE_TUNE
    family = _parameter_family(event.parameter)
    if family == _LANE_NOISE:
        return _LANE_NOISE
    if family in {"delay", "reverb"}:
        return _LANE_FX
    if event.section == _FILTER_SECTION:
        return _LANE_FILTER
    if event.section == _AMP_SECTION:
        return _LANE_AMP
    if event.section == _LFO_SECTION:
        return _LANE_LFO
    return None


def _lane_limited_session_depth(
    event: AnalogRytmRenderedStyleEvent,
    session_depth: SnapshotSessionDepth,
    guardrails: SnapshotSessionGuardrails,
) -> SnapshotSessionDepth | None:
    lane = _lane_for_event(event)
    if lane is None:
        return session_depth
    policy = guardrails.lane_policies[lane]
    if policy == _LANE_POLICY_OFF:
        return None
    return _min_session_depth(session_depth, _LANE_POLICY_SESSION_DEPTH[policy])


def _is_snapshot_shell_event_active(
    event: AnalogRytmRenderedStyleEvent,
    guardrails: SnapshotSessionGuardrails,
) -> bool:
    if event.pad in guardrails.locked_pads:
        return False
    if _is_live_dual_vco_detune_guarded_event(event):
        return False
    if guardrails.tune_policy == _TUNE_POLICY_OFF and _is_machine_source_tune_event(event):
        return False
    lane = _lane_for_event(event)
    if lane is not None and guardrails.lane_policies[lane] == _LANE_POLICY_OFF:
        return False
    return not _is_pad_1_foundation_protected_event(event)


def _replace_pad_override(
    guardrails: SnapshotSessionGuardrails,
    pad: int,
    depth: SnapshotSessionDepth,
) -> SnapshotSessionGuardrails:
    pad_overrides = dict(guardrails.pad_overrides)
    pad_overrides[pad] = depth
    return replace(guardrails, pad_overrides=MappingProxyType(pad_overrides))


def _replace_lane_policy(
    guardrails: SnapshotSessionGuardrails,
    lane: SnapshotLane,
    policy: SnapshotLanePolicy,
) -> SnapshotSessionGuardrails:
    lane_policies = dict(guardrails.lane_policies)
    lane_policies[lane] = policy
    tune_policy = policy if lane == _LANE_TUNE else guardrails.tune_policy
    return replace(
        guardrails,
        lane_policies=MappingProxyType(lane_policies),
        tune_policy=tune_policy,
    )


def _replace_randomizer_override(
    guardrails: SnapshotSessionGuardrails,
    pad: int,
    contract: SnapshotPadRandomizerContract,
) -> SnapshotSessionGuardrails:
    overrides = dict(guardrails.randomizer_overrides)
    overrides[pad] = contract
    return replace(guardrails, randomizer_overrides=MappingProxyType(overrides))


def _rebase_randomizer_overrides_for_anchor(
    anchor: RytmSnapshotShellAnchor,
    guardrails: SnapshotSessionGuardrails,
) -> SnapshotSessionGuardrails:
    if not guardrails.randomizer_overrides:
        return guardrails

    overrides = {
        pad: replace(
            contract,
            role=_randomizer_default_contract_for_pad(anchor, pad).role,
        )
        for pad, contract in guardrails.randomizer_overrides.items()
    }
    return replace(guardrails, randomizer_overrides=MappingProxyType(overrides))


def _lock_pad(
    guardrails: SnapshotSessionGuardrails,
    pad: int,
) -> SnapshotSessionGuardrails:
    return replace(guardrails, locked_pads=frozenset((*guardrails.locked_pads, pad)))


def _unlock_pad(
    guardrails: SnapshotSessionGuardrails,
    pad: int,
) -> SnapshotSessionGuardrails:
    return replace(guardrails, locked_pads=frozenset(p for p in guardrails.locked_pads if p != pad))


def _reset_pad_to_anchor(
    anchor_events: Sequence[AnalogRytmRenderedStyleEvent],
    current_events: Sequence[AnalogRytmRenderedStyleEvent],
    pad: int,
) -> tuple[AnalogRytmRenderedStyleEvent, ...]:
    return tuple(
        anchor_event if current_event.pad == pad else current_event
        for anchor_event, current_event in zip(anchor_events, current_events, strict=True)
    )


def _reset_pads_to_anchor(
    anchor_events: Sequence[AnalogRytmRenderedStyleEvent],
    current_events: Sequence[AnalogRytmRenderedStyleEvent],
    pads: frozenset[int],
) -> tuple[AnalogRytmRenderedStyleEvent, ...]:
    if not pads:
        return tuple(current_events)
    return tuple(
        anchor_event if current_event.pad in pads else current_event
        for anchor_event, current_event in zip(anchor_events, current_events, strict=True)
    )


def _reset_tune_events_to_anchor(
    anchor_events: Sequence[AnalogRytmRenderedStyleEvent],
    current_events: Sequence[AnalogRytmRenderedStyleEvent],
) -> tuple[AnalogRytmRenderedStyleEvent, ...]:
    return tuple(
        anchor_event if _is_machine_source_tune_event(current_event) else current_event
        for anchor_event, current_event in zip(anchor_events, current_events, strict=True)
    )


def _reset_lane_events_to_anchor(
    anchor_events: Sequence[AnalogRytmRenderedStyleEvent],
    current_events: Sequence[AnalogRytmRenderedStyleEvent],
    lane: SnapshotLane,
) -> tuple[AnalogRytmRenderedStyleEvent, ...]:
    return tuple(
        anchor_event if _lane_for_event(current_event) == lane else current_event
        for anchor_event, current_event in zip(anchor_events, current_events, strict=True)
    )


def _events_by_pad(
    events: Sequence[AnalogRytmRenderedStyleEvent],
) -> Mapping[int, tuple[AnalogRytmRenderedStyleEvent, ...]]:
    return MappingProxyType(
        {pad: tuple(event for event in events if event.pad == pad) for pad in range(1, 13)}
    )


def _snapshot_profile(snapshot: RytmKitSnapshot, pad: int) -> RytmMachineProfile | None:
    fact = snapshot.machine_facts.facts_by_pad.get(pad)
    if fact is None:
        return None
    if fact.decoded_machine_value is not None:
        return _MACHINE_PROFILE_BY_VALUE.get(fact.decoded_machine_value)
    if fact.raw_machine_value >= 0:
        return _MACHINE_PROFILE_BY_VALUE.get(fact.raw_machine_value & 0x7F)
    return None


def _track_value(snapshot: RytmKitSnapshot, pad: int, nrpn_lsb: int) -> int | None:
    field = RYTM_SOUND_FIELD_BY_NRPN_LSB.get(nrpn_lsb)
    if field is None:
        return None
    offset = RYTM_KIT_TRACKS_OFFSET + (RYTM_KIT_TRACK_SOUND_SIZE * (pad - 1)) + field.sound_offset
    if offset >= len(snapshot.unpacked):
        return None
    return _clamp_midi_value(snapshot.unpacked[offset] & 0x7F)


def _is_promoted_general_mapping(mapping: AnalogRytmCcMapping) -> bool:
    return (
        mapping.machine_key is None
        and mapping.mutation_status == "validated_runtime"
        and mapping.scope in _GENERAL_SCOPES
        and mapping.nrpn_msb == 1
        and mapping.nrpn_lsb is not None
        and mapping.parameter not in _LEVEL_PARAMETERS
    )


def _is_promoted_src_mapping(mapping: AnalogRytmCcMapping) -> bool:
    return (
        mapping.mutation_status in _PROMOTED_SRC_MUTATION_STATUSES
        and mapping.scope == _ZONE_SRC
        and mapping.nrpn_msb == 1
        and mapping.nrpn_lsb is not None
        and mapping.parameter not in _LEVEL_PARAMETERS
    )


def _event_from_mapping(
    *,
    pad: int,
    profile: RytmMachineProfile | None,
    mapping: AnalogRytmCcMapping,
    value: int,
    source: Literal["machine_src", "manual"],
) -> AnalogRytmRenderedStyleEvent | None:
    if _is_snapshot_omitted_mapping(mapping):
        return None
    machine_key = profile.key if profile is not None else _MACHINE_UNKNOWN
    label = profile.label if profile is not None else _MACHINE_UNKNOWN
    selector_range = _selector_range_for_mapping(mapping)
    if _is_preserved_invalid_selector(mapping, value, selector_range):
        return None
    event_value = (
        _normalized_selector_value(value, selector_range)
        if selector_range is not None
        else _value_limited_value(value, mapping.value_min, mapping.value_max)
    )
    return AnalogRytmRenderedStyleEvent(
        pad=pad,
        channel=pad - 1,
        machine_key=machine_key,
        section=mapping.section,
        parameter=mapping.parameter,
        cc_msb=mapping.cc_msb,
        value=event_value,
        risk=mapping.risk,
        mutation_status=mapping.mutation_status,
        source=source,
        intent=f"snapshot anchor current {label}",
        value_min=mapping.value_min,
        value_max=mapping.value_max,
        value_kind=mapping.value_kind,
        value_orientation=mapping.value_orientation,
    )


def _general_anchor_events(
    snapshot: RytmKitSnapshot,
    pad: int,
    profile: RytmMachineProfile | None,
) -> tuple[AnalogRytmRenderedStyleEvent, ...]:
    events: list[AnalogRytmRenderedStyleEvent] = []
    for mapping in ANALOG_RYTM_VALIDATED_RUNTIME_CC:
        if not _is_promoted_general_mapping(mapping) or mapping.nrpn_lsb is None:
            continue
        value = _track_value(snapshot, pad, mapping.nrpn_lsb)
        if value is None:
            continue
        event = _event_from_mapping(
            pad=pad,
            profile=profile,
            mapping=mapping,
            value=value,
            source="manual",
        )
        if event is not None:
            events.append(event)
    return tuple(events)


def _src_anchor_events(
    snapshot: RytmKitSnapshot,
    pad: int,
    profile: RytmMachineProfile | None,
) -> tuple[AnalogRytmRenderedStyleEvent, ...]:
    if profile is None:
        return ()
    events: list[AnalogRytmRenderedStyleEvent] = []
    for mapping in get_machine_src_mappings(profile.key):
        if not _is_promoted_src_mapping(mapping) or mapping.nrpn_lsb is None:
            continue
        value = _track_value(snapshot, pad, mapping.nrpn_lsb)
        if value is None:
            continue
        event = _event_from_mapping(
            pad=pad,
            profile=profile,
            mapping=mapping,
            value=value,
            source="machine_src",
        )
        if event is not None:
            events.append(event)
    return tuple(events)


def build_snapshot_shell_anchor(snapshot: RytmKitSnapshot) -> RytmSnapshotShellAnchor:
    """Build the live-safe all-12-pad anchor from a decoded Rytm kit snapshot."""

    events: list[AnalogRytmRenderedStyleEvent] = []
    for pad in range(1, _TRACK_COUNT + 1):
        profile = _snapshot_profile(snapshot, pad)
        events.extend(_src_anchor_events(snapshot, pad, profile))
        events.extend(_general_anchor_events(snapshot, pad, profile))

    anchor_events = tuple(events)
    return RytmSnapshotShellAnchor(
        kit_name=snapshot.kit_name,
        fingerprint=rytm_snapshot_payload_fingerprint(snapshot),
        events=anchor_events,
        events_by_pad=_events_by_pad(anchor_events),
    )


def _parameter_family(parameter: str) -> str:
    name = parameter.casefold()
    if "frequency" in name or "tune" in name:
        return "pitch"
    if "decay" in name or "release" in name or "hold" in name:
        return "decay"
    if "overdrive" in name or "drive" in name or "dist" in name:
        return "drive"
    if "resonance" in name:
        return "resonance"
    if "noise" in name or "dust" in name:
        return "noise"
    if "attack" in name or "snap" in name or "transient" in name or "click" in name:
        return "transient"
    if "delay" in name:
        return "delay"
    if "reverb" in name:
        return "reverb"
    if "pan" in name:
        return "pan"
    if "lfo" in name or "speed" in name or "phase" in name or "waveform" in name:
        return "motion"
    return "general"


def _event_matches_zone(event: AnalogRytmRenderedStyleEvent, zone: SnapshotZone) -> bool:
    if zone == _ZONE_FULL:
        return True
    if zone == _ZONE_SRC:
        return event.source == "machine_src"
    if zone == _ZONE_FILTER:
        return event.section == _FILTER_SECTION
    if zone == _ZONE_GRIT:
        return _parameter_family(event.parameter) in {
            "drive",
            "noise",
            "resonance",
            "transient",
        }
    raise ValueError(f"unknown snapshot shell zone: {zone}")


def _base_delta(
    event: AnalogRytmRenderedStyleEvent,
    command: SnapshotShellCommand,
    window: int,
) -> int:
    role = classify_rytm_pad_role(event.machine_key)
    family = _parameter_family(event.parameter)

    if command.name == _CMD_S1A:
        if family == "decay":
            return max(1, window // 2)
        if family in {"delay", "reverb", "motion"}:
            return max(1, window // 3)
        if family == "pitch" and role in {"kick", "tom"}:
            return -1
        return 1

    if command.name == _CMD_S3A:
        if family in {"motion", "pitch", "decay"}:
            return window
        if family in {"delay", "reverb"}:
            return max(1, window // 2)
        return max(1, window // 3)

    if command.name == _CMD_S3B:
        if family in {"drive", "noise", "resonance", "transient"}:
            return window
        if family == "decay" and role in {"hat", "snare", "cymbal"}:
            return -max(1, window // 2)
        return max(1, window // 3)

    if command.name in {_CMD_S4B, _CMD_FOUR}:
        if family == "pitch" and role == "kick":
            return max(-3, -window // 4)
        if event.machine_key == "sy_raw" and event.parameter == "Osc 2 Detune":
            return max(2, window // 2)
        if family in {"drive", "noise", "resonance", "transient", "motion"}:
            return window
        if family in {"delay", "reverb", "decay"}:
            return max(1, window // 2)
        return max(1, window // 3)

    if command.zone == _ZONE_SRC:
        return window if family != "pitch" else max(1, window // 2)
    if command.zone == _ZONE_FILTER:
        return window
    if command.zone == _ZONE_GRIT:
        return window
    return max(1, window // 2)


def _generation_jitter(
    event: AnalogRytmRenderedStyleEvent,
    command: SnapshotShellCommand,
    window: int,
    generation: int,
) -> int:
    if generation <= 1:
        return 0
    span = max(1, window // 4)
    payload = (
        f"{command.name}|{window}|{generation}|{event.pad}|"
        f"{event.section}|{event.parameter}|{event.value}"
    ).encode()
    value = int.from_bytes(hashlib.blake2s(payload, digest_size=2).digest(), "big")
    return (value % ((span * 2) + 1)) - span


def _delta_with_generation_jitter(
    event: AnalogRytmRenderedStyleEvent,
    command: SnapshotShellCommand,
    window: int,
    generation: int,
) -> int:
    base_delta = _base_delta(event, command, window)
    jittered_delta = base_delta + _generation_jitter(event, command, window, generation)
    if base_delta > 0:
        return max(1, jittered_delta)
    if base_delta < 0:
        return min(-1, jittered_delta)
    if jittered_delta == 0:
        return 1
    return jittered_delta


def _randomizer_density_allows_event(
    event: AnalogRytmRenderedStyleEvent,
    command: SnapshotShellCommand,
    generation: int,
    density: SnapshotRandomizerDensity,
) -> bool:
    threshold = _RANDOMIZER_DENSITY_PERCENT[density]
    if threshold <= 0:
        return False
    if threshold >= 100:
        return True
    payload = (
        f"density|{command.name}|{generation}|{event.pad}|{event.section}|"
        f"{event.parameter}|{event.value}"
    ).encode()
    value = int.from_bytes(hashlib.blake2s(payload, digest_size=2).digest(), "big")
    return value % 100 < threshold


def _bias_adjusted_delta(
    event: AnalogRytmRenderedStyleEvent,
    delta: int,
    bias: SnapshotRandomizerBias,
) -> int:
    if delta == 0 or bias == _RANDOMIZER_BIAS_NEUTRAL:
        return delta
    magnitude = abs(delta)
    family = _parameter_family(event.parameter)
    parameter = event.parameter.casefold()
    is_filter_frequency = event.section == _FILTER_SECTION and "frequency" in parameter
    if bias == _RANDOMIZER_BIAS_BRIGHTER and is_filter_frequency:
        return magnitude
    if bias == _RANDOMIZER_BIAS_DARKER and is_filter_frequency:
        return -magnitude
    if bias == _RANDOMIZER_BIAS_TIGHTER and (
        family in {"decay", "delay", "reverb"} or "release" in parameter
    ):
        return -magnitude
    if bias == _RANDOMIZER_BIAS_LOOSER and (
        family in {"decay", "delay", "reverb"} or "release" in parameter
    ):
        return magnitude
    if bias == _RANDOMIZER_BIAS_GRITTIER and family in {
        "drive",
        "noise",
        "resonance",
        "transient",
    }:
        return magnitude
    return delta


def _tune_policy_delta(
    event: AnalogRytmRenderedStyleEvent,
    command: SnapshotShellCommand,
    window: int,
    generation: int,
    policy: SnapshotTunePolicy,
) -> int:
    max_step = min(window, _TUNE_POLICY_MAX_STEPS[policy])
    if max_step <= 0:
        return 0

    payload = (
        f"tune|{command.name}|{generation}|{event.pad}|{event.machine_key}|"
        f"{event.parameter}|{event.value}|{max_step}"
    ).encode()
    value = int.from_bytes(hashlib.blake2s(payload, digest_size=2).digest(), "big")
    magnitude = 1 + (value % max_step)
    direction = -1 if value & 0x8000 else 1
    if direction < 0 and event.value <= event.value_min:
        direction = 1
    if direction > 0 and event.value >= event.value_max:
        direction = -1
    if direction < 0:
        magnitude = min(magnitude, event.value - event.value_min)
    else:
        magnitude = min(magnitude, event.value_max - event.value)
    return direction * magnitude


def _mutate_snapshot_event(
    anchor_event: AnalogRytmRenderedStyleEvent,
    current_event: AnalogRytmRenderedStyleEvent,
    command: SnapshotShellCommand,
    depth: SnapshotDepth,
    generation: int,
    guardrails: SnapshotSessionGuardrails,
    randomizer_contract: SnapshotPadRandomizerContract | None = None,
) -> AnalogRytmRenderedStyleEvent:
    if _is_pad_1_foundation_protected_event(current_event):
        return anchor_event

    if _is_live_dual_vco_detune_guarded_event(current_event):
        return anchor_event

    if not _event_matches_zone(current_event, command.zone):
        return current_event

    session_depth = _effective_session_depth(
        pad=current_event.pad,
        command_depth=depth,
        guardrails=guardrails,
    )
    if session_depth is None:
        return current_event

    session_depth = _lane_limited_session_depth(current_event, session_depth, guardrails)
    if session_depth is None:
        return current_event

    if randomizer_contract is not None:
        if not _randomizer_density_allows_event(
            anchor_event,
            command,
            generation,
            randomizer_contract.density,
        ):
            return current_event
        amount_depth = _RANDOMIZER_AMOUNT_DEPTH[randomizer_contract.amount]
        session_depth = _min_session_depth(
            amount_depth,
            _pad_caps_for_mode(guardrails.mode)[current_event.pad],
        )
        session_depth = _lane_limited_session_depth(current_event, session_depth, guardrails)
        if session_depth is None:
            return current_event

    window = _session_depth_window(guardrails.mode, session_depth)
    if _is_machine_source_tune_event(current_event):
        delta = _tune_policy_delta(
            anchor_event,
            command,
            window,
            generation,
            guardrails.tune_policy,
        )
        if delta == 0:
            return current_event
        proposed_value = _value_limited_value(
            anchor_event.value + delta,
            anchor_event.value_min,
            anchor_event.value_max,
        )
        return replace(
            current_event,
            value=proposed_value,
            intent=f"{command.label} {session_depth}: {current_event.intent}",
        )

    delta = _delta_with_generation_jitter(anchor_event, command, window, generation)
    if randomizer_contract is not None:
        delta = _bias_adjusted_delta(anchor_event, delta, randomizer_contract.bias)
    selector_range = _selector_range_for_event(anchor_event)
    if selector_range is None:
        proposed_value = _clamp_midi_value(anchor_event.value + delta)
        proposed_value = _anchor_limited_value(anchor_event.value, proposed_value, window)
        if _is_pad_1_tune_event(current_event):
            proposed_value = _anchor_limited_value(
                anchor_event.value,
                proposed_value,
                _PAD_1_TUNE_WINDOW,
            )
        proposed_value = _value_limited_value(
            proposed_value,
            anchor_event.value_min,
            anchor_event.value_max,
        )
    else:
        event_lane = _lane_for_event(current_event)
        lane_policy = guardrails.lane_policies[event_lane] if event_lane is not None else None
        if (
            randomizer_contract is not None
            and randomizer_contract.amount == _RANDOMIZER_AMOUNT_WIDE
            and lane_policy != _LANE_POLICY_MICRO
        ):
            proposed_value = _wide_selector_discovery_value(
                anchor_event,
                command,
                generation,
                selector_range,
            )
        else:
            proposed_value = _selector_mutated_value(
                anchor_event.value,
                delta,
                selector_range,
                wrap=guardrails.mode == _SESSION_MODE_STUDIO and lane_policy != _LANE_POLICY_MICRO,
                single_step=guardrails.mode == _SESSION_MODE_LIVE
                or lane_policy == _LANE_POLICY_MICRO,
            )

    return replace(
        current_event,
        value=proposed_value,
        intent=f"{command.label} {session_depth}: {current_event.intent}",
    )


def mutate_snapshot_shell_events(
    anchor_events: Sequence[AnalogRytmRenderedStyleEvent],
    current_events: Sequence[AnalogRytmRenderedStyleEvent],
    command: SnapshotShellCommand,
    *,
    depth: SnapshotDepth | None = None,
    generation: int = 1,
    guardrails: SnapshotSessionGuardrails | None = None,
    randomizer_contracts: Mapping[int, SnapshotPadRandomizerContract] | None = None,
) -> tuple[AnalogRytmRenderedStyleEvent, ...]:
    """Return a live-safe mutation of current events around captured anchors."""

    selected_depth = depth or command.depth
    selected_guardrails = guardrails or default_snapshot_session_guardrails()
    return tuple(
        _mutate_snapshot_event(
            anchor_event,
            current_event,
            command,
            selected_depth,
            generation,
            selected_guardrails,
            None if randomizer_contracts is None else randomizer_contracts[anchor_event.pad],
        )
        for anchor_event, current_event in zip(anchor_events, current_events, strict=True)
    )


def send_snapshot_shell_events(
    out: Sender,
    events: Sequence[AnalogRytmRenderedStyleEvent],
    *,
    skip_sleep: bool,
) -> None:
    """Send snapshot shell events through an injected sender."""

    sleep = _no_sleep if skip_sleep else None
    for event in events:
        if sleep is None:
            send_cc(out, event.cc_msb, event.value, channel=event.channel)
        else:
            send_cc(out, event.cc_msb, event.value, channel=event.channel, sleep=sleep)


def _sendable_snapshot_shell_events(
    state: RytmSnapshotShellState,
) -> tuple[AnalogRytmRenderedStyleEvent, ...]:
    return tuple(
        event
        for event in state.current_events
        if _is_snapshot_shell_event_active(event, state.guardrails)
    )


def format_snapshot_shell_preview(state: RytmSnapshotShellState) -> str:
    """Format the current snapshot shell plan for operator review."""

    active_events = _sendable_snapshot_shell_events(state)
    events_by_pad = _events_by_pad(active_events)
    active_pads = [pad for pad, events in events_by_pad.items() if events]
    lines = [
        "RytmRandomizer snapshot shell preview",
        f"kit: {state.anchor.kit_name}",
        f"fingerprint: {state.anchor.fingerprint}",
        f"mutation: {state.mutation_name}",
        f"pads: {len(active_pads)}",
        f"event count: {len(active_events)}",
        f"sent messages: {state.sent_message_count}",
    ]
    for pad in active_pads:
        events = events_by_pad[pad]
        anchor_events = tuple(
            anchor_event
            for anchor_event in state.anchor.events_by_pad[pad]
            if _is_snapshot_shell_event_active(anchor_event, state.guardrails)
        )
        changed_count = sum(
            1
            for anchor_event, current_event in zip(anchor_events, events, strict=True)
            if anchor_event.value != current_event.value
        )
        lines.append(
            f"Pad {pad:02d} {events[0].machine_key} events:{len(events)} changed:{changed_count}"
        )
        if pad == 1 and changed_count:
            lines.append("Pad 01 changes:")
            for line in _changed_event_lines(anchor_events, events):
                lines.append(f"  {line}")
    return "\n".join(lines)


def _changed_event_lines(
    anchor_events: Sequence[AnalogRytmRenderedStyleEvent],
    current_events: Sequence[AnalogRytmRenderedStyleEvent],
) -> tuple[str, ...]:
    lines: list[str] = []
    for anchor_event, current_event in zip(anchor_events, current_events, strict=True):
        if anchor_event.value == current_event.value:
            continue
        lines.append(
            f"{current_event.section} {current_event.parameter}: "
            f"{anchor_event.value} -> {current_event.value}"
        )
    return tuple(lines)


def format_snapshot_shell_changes(state: RytmSnapshotShellState) -> str:
    """Format a full all-pad parameter delta log for the current plan."""

    events_by_pad = _events_by_pad(state.current_events)
    lines = [
        "RytmRandomizer snapshot shell changes",
        f"kit: {state.anchor.kit_name}",
        f"mutation: {state.mutation_name}",
    ]
    changed_total = 0
    for pad in range(1, _TRACK_COUNT + 1):
        events = events_by_pad[pad]
        if not events:
            continue
        changed = _changed_event_lines(state.anchor.events_by_pad[pad], events)
        changed_total += len(changed)
        for line in changed:
            if line.startswith(f"{events[0].machine_key} "):
                lines.append(f"Pad {pad:02d} {line}")
            else:
                lines.append(f"Pad {pad:02d} {events[0].machine_key} {line}")
    if changed_total == 0:
        lines.append("no parameter changes staged")
    return "\n".join(lines)


def _format_pad_list(pads: Sequence[int]) -> str:
    if not pads:
        return "none"
    return ", ".join(str(pad) for pad in pads)


def _format_pad_overrides(overrides: Mapping[int, SnapshotSessionDepth]) -> str:
    if not overrides:
        return "none"
    return ", ".join(f"{pad}={overrides[pad]}" for pad in sorted(overrides))


def _format_lane_policies(policies: Mapping[SnapshotLane, SnapshotLanePolicy]) -> str:
    return ", ".join(f"{lane}={policies[lane]}" for lane in _LANES)


def _format_randomizer_contract(contract: SnapshotPadRandomizerContract) -> str:
    return f"{contract.role}/{contract.amount}/{contract.density}/{contract.bias}"


def _format_randomizer_contracts(state: RytmSnapshotShellState) -> str:
    contracts = _randomizer_contracts_for_state(state)
    return ", ".join(
        f"{pad}={_format_randomizer_contract(contracts[pad])}" for pad in range(1, _TRACK_COUNT + 1)
    )


def _active_pad_overrides(
    guardrails: SnapshotSessionGuardrails,
) -> Mapping[int, SnapshotSessionDepth]:
    return MappingProxyType(
        {
            pad: depth
            for pad, depth in guardrails.pad_overrides.items()
            if pad not in guardrails.locked_pads
        }
    )


def _inactive_pad_overrides(
    guardrails: SnapshotSessionGuardrails,
) -> Mapping[int, SnapshotSessionDepth]:
    return MappingProxyType(
        {
            pad: depth
            for pad, depth in guardrails.pad_overrides.items()
            if pad in guardrails.locked_pads
        }
    )


def format_snapshot_shell_status(state: RytmSnapshotShellState) -> str:
    """Format the current session-only performance guardrails."""

    guardrails = state.guardrails
    active_events = sum(
        1 for event in state.current_events if _is_snapshot_shell_event_active(event, guardrails)
    )
    pad_caps = _pad_caps_for_mode(guardrails.mode)
    caps = ", ".join(f"{pad}={pad_caps[pad]}" for pad in range(1, _TRACK_COUNT + 1))
    return "\n".join(
        [
            "RytmRandomizer snapshot shell status",
            f"mode: {guardrails.mode}",
            f"global depth: {guardrails.global_depth}",
            f"tune lane: {guardrails.tune_policy}",
            f"lanes: {_format_lane_policies(guardrails.lane_policies)}",
            f"locked pads: {_format_pad_list(sorted(guardrails.locked_pads))}",
            f"active pad overrides: {_format_pad_overrides(_active_pad_overrides(guardrails))}",
            f"inactive pad overrides: {_format_pad_overrides(_inactive_pad_overrides(guardrails))}",
            f"default pad caps: {caps}",
            f"randomizer pads: {_format_randomizer_contracts(state)}",
            f"active event count: {active_events}",
        ]
    )


def _help_text() -> str:
    return "\n".join(
        [
            "RytmRandomizer snapshot shell commands",
            "S1A = Rolling Light",
            "S3A = Intense Motion",
            "S3B = Intense Grit",
            "S4B = Wild Maximum",
            "4   = harder / wild mutation",
            "Y   = SRC/morph mutation, choose depth",
            "V   = filter mutation, choose depth",
            "N   = grit mutation, choose depth",
            "Y/V/N zone commands layer on the current staged plan; use fresh first for anchor-only zone changes",
            "Z / fresh = return all 12 pads to captured anchor",
            "U   = undo previous staged plan",
            "preview / p = show current staged plan",
            "changes / c = show every staged parameter delta",
            "send / s    = send current staged plan",
            "again / next = repeat last mutation and make a new variation",
            "go = make the next variation and send it",
            "randomize / rand / r = OXI-style kit variation respecting pad contracts",
            "drum-core = lock Pad 1 and stage wide pads 2-4 drum discovery",
            "kit / resnapshot = receive a new live KIT SysEx anchor",
            "mode live|studio = choose session guardrail range",
            "depth gentle|normal|strong|wild = set global session depth",
            "tune off|micro|normal|wide = set source-page tune lane",
            "lane tune|noise|fx|filter|amp|lfo off|micro|normal|wide = set a sound-design lane",
            "lock N / unlock N = exclude or re-enable a pad this session",
            "pad N gentle|normal|strong|wild|off = set a pad override",
            "pad N role|amount|density|bias VALUE = set OXI-style randomizer guardrails",
            "pad N BIAS = shorthand for pad N bias BIAS",
            "preset live|kick-safe|all-gentle|studio = apply session guardrails",
            "guards reset = clear locks/overrides and restore default live guardrails",
            "status = show session guardrails",
            "Q   = quit",
        ]
    )


class AnalogRytmSnapshotShell:
    """Interactive all-12-pad shell anchored to a current-kit snapshot."""

    def __init__(
        self,
        anchor: RytmSnapshotShellAnchor,
        out: Sender,
        *,
        input_func: InputFunc | None = None,
        resnapshot_func: ResnapshotFunc | None = None,
        skip_sleep: bool = True,
    ) -> None:
        self.out = out
        self._input_func = input_func
        self._resnapshot_func = resnapshot_func
        self.skip_sleep = skip_sleep
        self.state = RytmSnapshotShellState(
            anchor=anchor,
            mutation_name="anchor",
            current_events=anchor.events,
            previous_events=None,
        )

    def _input(self, prompt: str) -> str:
        if self._input_func is not None:
            return self._input_func(prompt)

        import builtins  # noqa: PLC0415 - keep import-time behavior inert

        return builtins.input(prompt)

    def _write_line(self, text: str = "") -> None:
        sys.stdout.write(text)
        sys.stdout.write("\n")

    def _parse_pad(self, raw_pad: str) -> int | None:
        pad = _valid_pad_number(raw_pad)
        if pad is None:
            self._write_line(f"pad number must be 1-12: {raw_pad}")
            return None
        return pad

    def _set_mode(self, parts: Sequence[str]) -> None:
        if len(parts) != 2:
            self._write_line("usage: mode live|studio")
            return
        mode = parts[1]
        if mode not in _SESSION_MODES:
            self._write_line(f"unknown snapshot shell mode: {mode}")
            return
        self.state = replace(
            self.state,
            guardrails=replace(
                self.state.guardrails,
                mode=mode,
                tune_policy=_default_tune_policy_for_mode(mode),
                lane_policies=MappingProxyType(dict(_default_lane_policies_for_mode(mode))),
            ),
        )
        self._write_line(f"session mode: {mode}")

    def _set_global_depth(self, parts: Sequence[str]) -> None:
        if len(parts) != 2:
            self._write_line("usage: depth gentle|normal|strong|wild")
            return
        depth = _SESSION_DEPTH_ALIASES.get(parts[1])
        if depth is None:
            self._write_line(f"unknown snapshot shell session depth: {parts[1]}")
            return
        self.state = replace(
            self.state,
            guardrails=replace(self.state.guardrails, global_depth=depth),
        )
        self._write_line(f"global session depth: {depth}")

    def _set_tune_policy(self, parts: Sequence[str]) -> None:
        if len(parts) != 2:
            self._write_line("usage: tune off|micro|normal|wide")
            return
        policy = parts[1]
        if policy not in _TUNE_POLICIES:
            self._write_line(f"unknown snapshot shell tune lane: {policy}")
            return
        current_events = (
            _reset_tune_events_to_anchor(
                self.state.anchor.events,
                self.state.current_events,
            )
            if policy == _TUNE_POLICY_OFF
            else self.state.current_events
        )
        self.state = replace(
            self.state,
            guardrails=_replace_lane_policy(self.state.guardrails, _LANE_TUNE, policy),
            current_events=current_events,
        )
        self._write_line(f"tune lane: {policy}")

    def _set_lane_policy(self, parts: Sequence[str]) -> None:
        if len(parts) != 3:
            self._write_line("usage: lane tune|noise|fx|filter|amp|lfo off|micro|normal|wide")
            return
        lane = parts[1]
        if lane not in _LANES:
            self._write_line(f"unknown snapshot shell lane: {lane}")
            return
        policy = parts[2]
        if policy not in _LANE_POLICIES:
            self._write_line(f"unknown snapshot shell lane policy: {policy}")
            return
        current_events = (
            _reset_lane_events_to_anchor(
                self.state.anchor.events,
                self.state.current_events,
                lane,
            )
            if policy == _LANE_POLICY_OFF
            else self.state.current_events
        )
        self.state = replace(
            self.state,
            guardrails=_replace_lane_policy(self.state.guardrails, lane, policy),
            current_events=current_events,
        )
        self._write_line(f"lane {lane}: {policy}")

    def _set_lock(self, parts: Sequence[str], *, locked: bool) -> None:
        if len(parts) != 2:
            command = _CMD_LOCK if locked else _CMD_UNLOCK
            self._write_line(f"usage: {command} 1-12")
            return
        pad = self._parse_pad(parts[1])
        if pad is None:
            return
        guardrails = (
            _lock_pad(self.state.guardrails, pad)
            if locked
            else _unlock_pad(self.state.guardrails, pad)
        )
        current_events = (
            _reset_pad_to_anchor(self.state.anchor.events, self.state.current_events, pad)
            if locked
            else self.state.current_events
        )
        self.state = replace(self.state, guardrails=guardrails, current_events=current_events)
        status = "locked" if locked else "unlocked"
        self._write_line(f"pad {pad} {status}")

    def _set_pad_randomizer_policy(self, parts: Sequence[str]) -> None:
        pad = self._parse_pad(parts[1])
        if pad is None:
            return
        field = parts[2]
        value = parts[3]
        contract = _randomizer_contract_for_pad(self.state.anchor, self.state.guardrails, pad)
        if field == "role":
            if value == "auto":
                pad_events = self.state.anchor.events_by_pad[pad]
                role = (
                    _randomizer_role_for_machine(pad_events[0].machine_key)
                    if pad_events
                    else _RANDOMIZER_ROLE_PERC
                )
            elif value in _RANDOMIZER_ROLES:
                role = value
            else:
                self._write_line(f"unknown snapshot shell randomizer role: {value}")
                return
            contract = replace(contract, role=role)
        elif field == "amount":
            if value not in _RANDOMIZER_AMOUNTS:
                self._write_line(f"unknown snapshot shell randomizer amount: {value}")
                return
            contract = replace(contract, amount=value)
        elif field == "density":
            if value not in _RANDOMIZER_DENSITIES:
                if value in _RANDOMIZER_BIASES:
                    self._write_line(f"{value} is a bias; use: pad {pad} bias {value}")
                    return
                self._write_line(f"unknown snapshot shell randomizer density: {value}")
                return
            contract = replace(contract, density=value)
        elif field == "bias":
            if value not in _RANDOMIZER_BIASES:
                if value in _RANDOMIZER_DENSITIES:
                    self._write_line(f"{value} is a density; use: pad {pad} density {value}")
                    return
                self._write_line(f"unknown snapshot shell randomizer bias: {value}")
                return
            contract = replace(contract, bias=value)
        else:
            self._write_line("usage: pad 1-12 role|amount|density|bias VALUE")
            return
        self.state = replace(
            self.state,
            guardrails=_replace_randomizer_override(
                self.state.guardrails,
                pad,
                contract,
            ),
        )
        self._write_line(f"pad {pad} randomizer {field}: {value}")

    def _set_pad_policy(self, parts: Sequence[str]) -> None:
        if len(parts) == 4:
            self._set_pad_randomizer_policy(parts)
            return
        if len(parts) != 3:
            self._write_line(
                "usage: pad 1-12 gentle|normal|strong|wild|off "
                "or pad 1-12 role|amount|density|bias VALUE "
                "or pad 1-12 BIAS"
            )
            return
        pad = self._parse_pad(parts[1])
        if pad is None:
            return
        policy = parts[2]
        if policy in _RANDOMIZER_BIASES:
            self._set_pad_randomizer_policy(("pad", parts[1], "bias", policy))
            return
        if policy == "off":
            current_events = _reset_pad_to_anchor(
                self.state.anchor.events,
                self.state.current_events,
                pad,
            )
            self.state = replace(
                self.state,
                guardrails=_lock_pad(self.state.guardrails, pad),
                current_events=current_events,
            )
            self._write_line(f"pad {pad} locked")
            return
        depth = _SESSION_DEPTH_ALIASES.get(policy)
        if depth is None:
            self._write_line(f"unknown snapshot shell pad policy: {policy}")
            return
        guardrails = _replace_pad_override(
            _unlock_pad(self.state.guardrails, pad),
            pad,
            depth,
        )
        self.state = replace(self.state, guardrails=guardrails)
        self._write_line(f"pad {pad} depth override: {depth}")

    def _set_preset(self, parts: Sequence[str]) -> None:
        if len(parts) != 2:
            self._write_line("usage: preset live|kick-safe|all-gentle|studio")
            return
        preset = parts[1]
        guardrails = _preset_guardrails(preset)
        if guardrails is None:
            self._write_line(f"unknown snapshot shell preset: {preset}")
            return
        current_events = _reset_pads_to_anchor(
            self.state.anchor.events,
            self.state.current_events,
            guardrails.locked_pads,
        )
        self.state = replace(
            self.state,
            guardrails=guardrails,
            current_events=current_events,
        )
        self._write_line(f"preset applied: {preset}")

    def _reset_guards(self, parts: Sequence[str]) -> None:
        if len(parts) != 2 or parts[1] != _GUARDS_RESET:
            self._write_line("usage: guards reset")
            return
        self.state = replace(
            self.state,
            guardrails=default_snapshot_session_guardrails(),
        )
        self._write_line("session guardrails reset")

    def _read_depth(self, label: str) -> SnapshotDepth | None:
        try:
            raw = self._input(f"{label} depth (micro/groove/strong or 1/2/3): ")
        except (EOFError, KeyboardInterrupt, StopIteration, OSError):
            self._write_line("depth choice cancelled")
            return None
        depth = _DEPTH_ALIASES.get(raw.strip().casefold())
        if depth is None:
            self._write_line(f"unknown snapshot shell depth: {raw}")
            return None
        return depth

    def _apply_command(
        self,
        command: SnapshotShellCommand,
        *,
        depth_override: SnapshotDepth | None = None,
        label_suffix: str = "",
    ) -> None:
        depth = depth_override or command.depth
        if command.kind == _KIND_ZONE and depth_override is None:
            chosen_depth = self._read_depth(command.label)
            if chosen_depth is None:
                return
            depth = chosen_depth
        generation = self.state.mutation_generation + 1
        randomizer_contracts = (
            _randomizer_contracts_for_state(self.state) if command.name == _CMD_RANDOMIZE else None
        )
        current_events = (
            self.state.anchor.events
            if command.name == _CMD_RANDOMIZE
            else self.state.current_events
        )
        mutated = mutate_snapshot_shell_events(
            self.state.anchor.events,
            current_events,
            command,
            depth=depth,
            generation=generation,
            guardrails=self.state.guardrails,
            randomizer_contracts=randomizer_contracts,
        )
        label = command.label if command.kind == _KIND_SCENE else f"{command.label} {depth}"
        label = f"{label}{label_suffix}"
        self.state = replace(
            self.state,
            mutation_name=label,
            previous_events=self.state.current_events,
            current_events=mutated,
            last_command_name=command.name,
            last_depth=depth,
            mutation_generation=generation,
        )
        self._write_line(f"mutation applied: {label}")
        if command.kind == _KIND_ZONE:
            self._write_line(_ZONE_LAYERING_HINT)

    def _repeat_last_command(self) -> None:
        if self.state.last_command_name is None:
            self._write_line("nothing to repeat")
            return
        command = SNAPSHOT_SHELL_COMMANDS[self.state.last_command_name]
        depth = self.state.last_depth or command.depth
        self._apply_command(command, depth_override=depth, label_suffix=" again")

    def _go(self) -> None:
        if self.state.last_command_name is None:
            self._apply_command(SNAPSHOT_SHELL_COMMANDS[_CMD_FOUR])
        else:
            self._repeat_last_command()
        self._send()

    def _apply_drum_core_macro(self) -> None:
        self._write_line("macro applied: drum-core")
        self._set_preset(("preset", _PRESET_LIVE))
        self._set_lane_policy(("lane", _LANE_LFO, _LANE_POLICY_OFF))
        self._set_lane_policy(("lane", _LANE_FX, _LANE_POLICY_MICRO))
        self._set_lock(("lock", "1"), locked=True)
        for pad, bias in (
            (2, _RANDOMIZER_BIAS_LOOSER),
            (3, _RANDOMIZER_BIAS_GRITTIER),
            (4, _RANDOMIZER_BIAS_GRITTIER),
        ):
            raw_pad = str(pad)
            self._set_pad_randomizer_policy(("pad", raw_pad, "amount", _RANDOMIZER_AMOUNT_WIDE))
            self._set_pad_randomizer_policy(("pad", raw_pad, "density", _RANDOMIZER_DENSITY_FULL))
            self._set_pad_randomizer_policy(("pad", raw_pad, "bias", bias))
        self._apply_command(SNAPSHOT_SHELL_COMMANDS[_CMD_RANDOMIZE])

    def _resnapshot_anchor(self) -> None:
        if self._resnapshot_func is None:
            self._write_line(
                "live KIT resnapshot is unavailable in this shell; "
                "restart with --arm --rytm-live-snapshot-shell"
            )
            return
        anchor = self._resnapshot_func()
        if anchor is None:
            self._write_line("KIT resnapshot cancelled; keeping current anchor")
            return
        guardrails = _rebase_randomizer_overrides_for_anchor(anchor, self.state.guardrails)
        self.state = replace(
            self.state,
            anchor=anchor,
            guardrails=guardrails,
            mutation_name="anchor",
            current_events=anchor.events,
            previous_events=None,
            last_command_name=None,
            last_depth=None,
            mutation_generation=0,
        )
        self._write_line("replaced captured 12-pad anchor")
        self._write_line(f"kit: {anchor.kit_name}")
        self._write_line(f"fingerprint: {anchor.fingerprint}")

    def _preview(self) -> None:
        self._write_line(format_snapshot_shell_preview(self.state))

    def _changes(self) -> None:
        self._write_line(format_snapshot_shell_changes(self.state))

    def _status(self) -> None:
        self._write_line(format_snapshot_shell_status(self.state))

    def _send(self) -> None:
        sendable_events = _sendable_snapshot_shell_events(self.state)
        send_snapshot_shell_events(self.out, sendable_events, skip_sleep=self.skip_sleep)
        sent_count = self.state.sent_message_count + len(sendable_events)
        self.state = replace(self.state, sent_message_count=sent_count)
        self._write_line(f"sent current snapshot plan: {len(sendable_events)} message(s)")
        self._write_line(
            "send repeats current plan; type go for next variation+send, or type a mutation command/again/next"
        )

    def _undo(self) -> None:
        if self.state.previous_events is None:
            self._write_line("nothing to undo")
            return
        self.state = replace(
            self.state,
            mutation_name="undo",
            current_events=self.state.previous_events,
            previous_events=None,
        )
        self._write_line("restored previous snapshot plan")

    def _reset(self) -> None:
        self.state = replace(
            self.state,
            mutation_name="anchor",
            previous_events=self.state.current_events,
            current_events=self.state.anchor.events,
        )
        self._write_line("restored captured 12-pad anchor")

    def dispatch(self, raw_command: str) -> bool:
        """Dispatch one snapshot shell command. Return ``False`` only to exit."""

        command = raw_command.strip()
        if not command:
            return True
        normalized = command.casefold()
        parts = normalized.split()
        if normalized in {_CMD_QUIT, "quit", "exit"}:
            self._write_line("Exiting.")
            return False
        if normalized in {_CMD_HELP, "h", "?"}:
            self._write_line(_help_text())
            return True
        if normalized in {_CMD_PREVIEW, "p"}:
            self._preview()
            return True
        if normalized in {_CMD_CHANGES, "c"}:
            self._changes()
            return True
        if normalized in {_CMD_STATUS, "st"}:
            self._status()
            return True
        if normalized in {_CMD_SEND, "s"}:
            self._send()
            return True
        if normalized == _CMD_GO:
            self._go()
            return True
        if normalized in {_CMD_AGAIN, _CMD_NEXT}:
            self._repeat_last_command()
            return True
        if normalized in {"rand", "r"}:
            self._apply_command(SNAPSHOT_SHELL_COMMANDS[_CMD_RANDOMIZE])
            return True
        if normalized in {_CMD_DRUM_CORE, "drumcore"}:
            self._apply_drum_core_macro()
            return True
        if normalized == _CMD_UNDO:
            self._undo()
            return True
        if normalized in {_CMD_RESET, _CMD_FRESH}:
            self._reset()
            return True
        if normalized in {_CMD_KIT, _CMD_RESNAPSHOT}:
            self._resnapshot_anchor()
            return True
        if parts and parts[0] == _CMD_MODE:
            self._set_mode(parts)
            return True
        if parts and parts[0] == _CMD_DEPTH:
            self._set_global_depth(parts)
            return True
        if parts and parts[0] == _CMD_TUNE:
            self._set_tune_policy(parts)
            return True
        if parts and parts[0] == _CMD_LANE:
            self._set_lane_policy(parts)
            return True
        if parts and parts[0] == _CMD_LOCK:
            self._set_lock(parts, locked=True)
            return True
        if parts and parts[0] == _CMD_UNLOCK:
            self._set_lock(parts, locked=False)
            return True
        if parts and parts[0] == _CMD_PAD:
            self._set_pad_policy(parts)
            return True
        if parts and parts[0] == _CMD_PRESET:
            self._set_preset(parts)
            return True
        if parts and parts[0] == _CMD_GUARDS:
            self._reset_guards(parts)
            return True
        shell_command = SNAPSHOT_SHELL_COMMANDS.get(normalized)
        if shell_command is not None:
            self._apply_command(shell_command)
            return True
        self._write_line(f"unknown snapshot shell command: {command}")
        return True

    def run(self) -> int:
        """Run the interactive command loop."""

        self._write_line("RytmRandomizer snapshot shell")
        self._write_line(f"Loaded kit anchor: {self.state.anchor.kit_name}")
        self._write_line("Type help for commands.")
        try:
            while True:
                command = self._input("snapshot-12> ")
                if not self.dispatch(command):
                    return 0
        except (EOFError, KeyboardInterrupt, StopIteration):
            self._write_line("Exiting.")
            return 0


__all__ = [
    "AnalogRytmSnapshotShell",
    "ResnapshotFunc",
    "RytmSnapshotShellAnchor",
    "RytmSnapshotShellState",
    "SNAPSHOT_SHELL_COMMANDS",
    "SnapshotSessionGuardrails",
    "SnapshotShellCommand",
    "build_snapshot_shell_anchor",
    "default_snapshot_session_guardrails",
    "format_snapshot_shell_changes",
    "format_snapshot_shell_preview",
    "format_snapshot_shell_status",
    "mutate_snapshot_shell_events",
    "send_snapshot_shell_events",
]
