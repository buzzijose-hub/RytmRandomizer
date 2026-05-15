"""Read-only pad-lane behavior helpers backed by a single command registry.

This module collapses the former per-pad ``behavior_pad1_lane`` ..
``behavior_pad4_lane`` modules into one data-driven ``PadLaneCommand``
registry. It models deterministic pad-lane intent for Pads 1-4 without prompt
loops, dispatching commands, opening ports, sending MIDI, or touching
hardware.

The four historical modules each grew their own copy-pasted descriptor tables
(Pad 1) or near-identical hand-written result functions (Pads 2-4). Every one
of those values is a static fact about a pad command, so they all live here in
a single ``{command_key: PadLaneCommand}`` mapping. The per-pad public function
names are re-implemented as thin filters/formatters over this registry and are
re-exported by thin ``behavior_padN_lane`` shim modules for backward
compatibility.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType

from .commands import COMMANDS, PAD1_COMMANDS, PAD2_COMMANDS, PAD3_COMMANDS, PAD4_COMMANDS


# --------------------------------------------------------------------------
# Frozen descriptor for a single pad-lane command.
# --------------------------------------------------------------------------
@dataclass(frozen=True)
class PadLaneCommand:
    """Immutable static descriptor for one Pad 1-4 lane command.

    Captures the fields that were previously spread across Pad 1's 14 parallel
    dicts and Pads 2/3/4's hand-written ``_accepted_*_result`` functions.
    """

    command_key: str
    pad: int
    source: str
    behavior_family: str
    reason: str
    lane: str
    lane_action: str
    intent_line: str
    dependency_line: str
    # Pad 1 specific descriptor fields (empty/neutral for Pads 2-4).
    engine_dependency: str = ""
    depth_dependency: str = ""
    requires_depth_selection: bool = False
    lane_metadata: str = ""
    state_lane_family: str = ""
    state_intent_kind: str = ""
    # Pads 2-4 result fields (empty/neutral for Pad 1).
    intent_kind: str = ""
    anchor_concept: str = ""
    mode_concept: str = ""
    # Extra display lines that follow the dependency line, plus extra metadata.
    extra_display_lines: tuple[str, ...] = ()
    extra_metadata: Mapping[str, object] = field(default_factory=lambda: MappingProxyType({}))

    def __post_init__(self) -> None:
        object.__setattr__(self, "extra_display_lines", tuple(self.extra_display_lines))
        object.__setattr__(self, "extra_metadata", MappingProxyType(dict(self.extra_metadata)))


# --------------------------------------------------------------------------
# Per-pad result dataclasses (byte-identical to the historical modules).
# --------------------------------------------------------------------------
@dataclass(frozen=True)
class Pad1LaneBehaviorResult:
    """Immutable read-only result for Packet 5 Pad 1 lane behavior."""

    command_key: str
    label: str = ""
    behavior_family: str = "pad1-lane/current-bd-engine"
    accepted: bool = False
    reason: str = "not_evaluated"
    target_pad: int | None = None
    lane: str = ""
    lane_action: str = ""
    engine_dependency: str = ""
    depth_dependency: str = ""
    display_lines: tuple[str, ...] = ()
    state_changed: bool = False
    prompt_required: bool = False
    dispatches_command: bool = False
    executes_command: bool = False
    mutates_lane_state: bool = False
    sends_real_midi: bool = False
    opens_ports: bool = False
    hardware_required: bool = False
    active_behavior: bool = False
    metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "display_lines", tuple(self.display_lines))
        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))


@dataclass(frozen=True)
class Pad1LaneStateDescriptor:
    """Immutable static descriptor for read-only Pad 1 lane context."""

    source_key: str
    supported: bool = False
    reason: str = "unknown_command"
    target_pad: int | None = None
    lane_family: str = ""
    lane_action: str = ""
    intent_kind: str = ""
    requires_current_engine: bool = False
    requires_anchor: bool = False
    requires_profiled_engine: bool = False
    anchor_key: str = ""
    return_key: str = ""
    discovery_depth: str = ""
    mutation_depth: str = ""
    metadata_only: bool = True
    executes: bool = False
    sends_midi: bool = False
    opens_ports: bool = False
    hardware_required: bool = False
    notes: tuple[str, ...] = ()
    metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "notes", tuple(self.notes))
        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))


@dataclass(frozen=True)
class Pad2LaneBehaviorResult:
    """Immutable read-only result for Packet 6 Pad 2 lane behavior."""

    command_key: str
    label: str = ""
    behavior_family: str = "pad2-lane/bd-classic-home-anchor"
    accepted: bool = False
    reason: str = "not_evaluated"
    target_pad: int | None = None
    lane: str = ""
    lane_action: str = ""
    intent_kind: str = ""
    anchor_concept: str = ""
    display_lines: tuple[str, ...] = ()
    state_changed: bool = False
    prompt_required: bool = False
    dispatches_command: bool = False
    executes_command: bool = False
    mutates_lane_state: bool = False
    sends_real_midi: bool = False
    opens_ports: bool = False
    hardware_required: bool = False
    active_behavior: bool = False
    metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "display_lines", tuple(self.display_lines))
        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))


@dataclass(frozen=True)
class Pad3LaneBehaviorResult:
    """Immutable read-only result for Packet 7 Pad 3 lane behavior."""

    command_key: str
    label: str = ""
    behavior_family: str = "pad3-lane/sy-raw-mid-bass-home-anchor"
    accepted: bool = False
    reason: str = "not_evaluated"
    target_pad: int | None = None
    lane: str = ""
    lane_action: str = ""
    intent_kind: str = ""
    anchor_concept: str = ""
    mode_concept: str = ""
    display_lines: tuple[str, ...] = ()
    state_changed: bool = False
    prompt_required: bool = False
    dispatches_command: bool = False
    executes_command: bool = False
    mutates_lane_state: bool = False
    sends_real_midi: bool = False
    opens_ports: bool = False
    hardware_required: bool = False
    active_behavior: bool = False
    metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "display_lines", tuple(self.display_lines))
        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))


@dataclass(frozen=True)
class Pad4LaneBehaviorResult:
    """Immutable read-only result for Packet 8 Pad 4 lane behavior."""

    command_key: str
    label: str = ""
    behavior_family: str = "pad4-lane/bd-acoustic-body-accent-home-anchor"
    accepted: bool = False
    reason: str = "not_evaluated"
    target_pad: int | None = None
    lane: str = ""
    lane_action: str = ""
    intent_kind: str = ""
    anchor_concept: str = ""
    display_lines: tuple[str, ...] = ()
    state_changed: bool = False
    prompt_required: bool = False
    dispatches_command: bool = False
    executes_command: bool = False
    mutates_lane_state: bool = False
    sends_real_midi: bool = False
    opens_ports: bool = False
    hardware_required: bool = False
    active_behavior: bool = False
    metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "display_lines", tuple(self.display_lines))
        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))


# --------------------------------------------------------------------------
# Packet key tuples (preserved verbatim from the historical modules).
# --------------------------------------------------------------------------
PACKET_5A_PAD1_CURRENT_ENGINE_KEYS = ("BR", "BM")
PACKET_5B_PAD1_BD_FM_KEYS = ("FT", "FK", "FG", "FZ")
PACKET_5C_PAD1_BD_PLASTIC_KEYS = ("BP", "PT", "PK", "PX", "PBH")
PACKET_5D_PAD1_BD_SILKY_KEYS = ("BI", "ST", "SK", "SC", "SBH")
PACKET_5E_PAD1_BD_ACOUSTIC_KEYS = ("BA",)
DEFERRED_PACKET_5_PAD1_LANE_KEYS = ()

PACKET_6A_PAD2_LANE_KEYS = ("P2B",)
PACKET_6B_PAD2_LANE_KEYS = ("P2H",)
PACKET_6C_PAD2_LANE_KEYS = ("P2C",)
PACKET_6D_PAD2_LANE_KEYS = ("P2F",)
PACKET_6E_PAD2_LANE_KEYS = ("P2T",)
PACKET_6F_PAD2_LANE_KEYS = ("P2P",)
PACKET_6G_PAD2_LANE_KEYS = ("P2G",)
PACKET_6H_PAD2_LANE_KEYS = ("P2R",)
PACKET_6I_PAD2_LANE_KEYS = ("P2X",)
PACKET_6J_PAD2_LANE_KEYS = ("P2Z",)
DEFERRED_PACKET_6_PAD2_LANE_KEYS = ("P2M",)

PACKET_7A_PAD3_LANE_KEYS = ("P3A",)
PACKET_7B_PAD3_LANE_KEYS = ("SA",)
PACKET_7C_PAD3_LANE_KEYS = ("SL",)
PACKET_7D_PAD3_LANE_KEYS = ("SB",)
PACKET_7E_PAD3_LANE_KEYS = ("SX",)
PACKET_7F_PAD3_LANE_KEYS = ("SW",)
PACKET_7G_PAD3_LANE_KEYS = ("P3R",)
PACKET_7H_PAD3_LANE_KEYS = ("P3X",)
DEFERRED_PACKET_7_PAD3_LANE_KEYS = ("P3M",)

PACKET_8A_PAD4_LANE_KEYS = ("P4A",)
PACKET_8B_PAD4_LANE_KEYS = ("P4R",)
PACKET_8C_PAD4_LANE_KEYS = ("P4X",)
DEFERRED_PACKET_8_PAD4_LANE_KEYS = ("P4M",)

PAD1_LANE_KEYS = (
    PACKET_5A_PAD1_CURRENT_ENGINE_KEYS
    + PACKET_5B_PAD1_BD_FM_KEYS
    + PACKET_5C_PAD1_BD_PLASTIC_KEYS
    + PACKET_5D_PAD1_BD_SILKY_KEYS
    + PACKET_5E_PAD1_BD_ACOUSTIC_KEYS
)


# --------------------------------------------------------------------------
# The single command registry.
#
# This registry holds pad-lane *descriptor* facts (lane families, depth
# dependencies, intent/dependency lines) — the same static facts the four
# historical behavior_padN_lane modules expressed as parallel dicts /
# hand-written result functions. This is a distinct data domain from
# rytm_randomizer.data (param maps / scenes / profiles), so it is kept
# self-contained here rather than sourced from that layer.
# --------------------------------------------------------------------------
def _pad1(
    command_key: str,
    behavior_family: str,
    reason: str,
    lane: str,
    lane_action: str,
    intent_line: str,
    dependency_line: str,
    engine_dependency: str,
    depth_dependency: str,
    requires_depth_selection: bool,
    lane_metadata: str,
    state_lane_family: str,
    state_intent_kind: str,
    extra_display_lines: tuple[str, ...] = (),
    extra_metadata: Mapping[str, object] | None = None,
) -> PadLaneCommand:
    return PadLaneCommand(
        command_key=command_key,
        pad=1,
        source="PAD1_COMMANDS",
        behavior_family=behavior_family,
        reason=reason,
        lane=lane,
        lane_action=lane_action,
        intent_line=intent_line,
        dependency_line=dependency_line,
        engine_dependency=engine_dependency,
        depth_dependency=depth_dependency,
        requires_depth_selection=requires_depth_selection,
        lane_metadata=lane_metadata,
        state_lane_family=state_lane_family,
        state_intent_kind=state_intent_kind,
        extra_display_lines=extra_display_lines,
        extra_metadata=extra_metadata or {},
    )


_PAD1_INTENT_CURRENT = "Read-only Pad 1 current-engine lane intent."
_PAD1_INTENT_FM_DISCOVERY = "Read-only Pad 1 BD FM discovery intent."
_PAD1_INTENT_FM_ANCHOR = "Read-only Pad 1 BD FM anchor-return intent."
_PAD1_INTENT_PLASTIC = "Read-only Pad 1 BD Plastic lane intent."
_PAD1_INTENT_SILKY = "Read-only Pad 1 BD Silky lane intent."
_PAD1_INTENT_ACOUSTIC = "Read-only Pad 1 BD Acoustic anchor intent."

_DEP_FM_DISCOVERY = ("Future BD FM discovery depth is recorded only.",)
_DEP_PLASTIC_DISCOVERY = ("Future BD Plastic discovery depth is recorded only.",)
_DEP_SILKY_DISCOVERY = ("Future BD Silky discovery depth is recorded only.",)
_DEP_SAFE_MUTATION = ("Future safe mutation depth is recorded only.",)


_REGISTRY: dict[str, PadLaneCommand] = {}


def _register(*commands: PadLaneCommand) -> None:
    for command in commands:
        _REGISTRY[command.command_key] = command


# --- Pad 1 -----------------------------------------------------------------
_register(
    _pad1(
        "BR",
        "pad1-lane/current-bd-engine",
        "supported_pad1_current_engine_lane_intent",
        "Pad 1 BD engine",
        "rotate_profiled_bd_engine",
        _PAD1_INTENT_CURRENT,
        "Current-engine dependency is recorded only.",
        "current_pad1_bd_engine_state",
        "",
        False,
        "pad_1_bd_engine",
        "current_bd_engine",
        "rotation",
    ),
    _pad1(
        "BM",
        "pad1-lane/current-bd-engine",
        "supported_pad1_current_engine_lane_intent",
        "Pad 1 BD engine",
        "safe_current_engine_mutation",
        _PAD1_INTENT_CURRENT,
        "Current-engine dependency is recorded only.",
        "current_pad1_bd_engine_state",
        "future_safe_mutation_depth",
        True,
        "pad_1_bd_engine",
        "current_bd_engine",
        "mutation",
        extra_display_lines=_DEP_SAFE_MUTATION,
    ),
    _pad1(
        "FT",
        "pad1-lane/bd-fm-discovery",
        "supported_pad1_bd_fm_discovery_intent",
        "Pad 1 BD FM",
        "bd_fm_tone_fm_discovery",
        _PAD1_INTENT_FM_DISCOVERY,
        "BD FM engine/profile dependency is recorded only.",
        "pad1_bd_fm_engine_profile",
        "future_bd_fm_discovery_depth",
        True,
        "pad_1_bd_fm",
        "bd_fm",
        "discovery",
        extra_display_lines=_DEP_FM_DISCOVERY,
        extra_metadata={
            "requires_current_engine_state": False,
            "requires_bd_fm_engine_profile": True,
            "requires_bd_fm_anchor": False,
        },
    ),
    _pad1(
        "FK",
        "pad1-lane/bd-fm-discovery",
        "supported_pad1_bd_fm_discovery_intent",
        "Pad 1 BD FM",
        "bd_fm_kick_body_discovery",
        _PAD1_INTENT_FM_DISCOVERY,
        "BD FM engine/profile dependency is recorded only.",
        "pad1_bd_fm_engine_profile",
        "future_bd_fm_discovery_depth",
        True,
        "pad_1_bd_fm",
        "bd_fm",
        "discovery",
        extra_display_lines=_DEP_FM_DISCOVERY,
        extra_metadata={
            "requires_current_engine_state": False,
            "requires_bd_fm_engine_profile": True,
            "requires_bd_fm_anchor": False,
        },
    ),
    _pad1(
        "FG",
        "pad1-lane/bd-fm-discovery",
        "supported_pad1_bd_fm_discovery_intent",
        "Pad 1 BD FM",
        "bd_fm_grit_discovery",
        _PAD1_INTENT_FM_DISCOVERY,
        "BD FM engine/profile dependency is recorded only.",
        "pad1_bd_fm_engine_profile",
        "future_bd_fm_discovery_depth",
        True,
        "pad_1_bd_fm",
        "bd_fm",
        "discovery",
        extra_display_lines=_DEP_FM_DISCOVERY,
        extra_metadata={
            "requires_current_engine_state": False,
            "requires_bd_fm_engine_profile": True,
            "requires_bd_fm_anchor": False,
        },
    ),
    _pad1(
        "FZ",
        "pad1-lane/bd-fm-anchor-return",
        "supported_pad1_bd_fm_anchor_return_intent",
        "Pad 1 BD FM",
        "return_bd_fm_to_anchor",
        _PAD1_INTENT_FM_ANCHOR,
        "BD FM anchor dependency is recorded only.",
        "pad1_bd_fm_anchor_state",
        "",
        False,
        "pad_1_bd_fm",
        "bd_fm",
        "anchor_return",
        extra_metadata={
            "requires_current_engine_state": False,
            "requires_bd_fm_engine_profile": False,
            "requires_bd_fm_anchor": True,
        },
    ),
    _pad1(
        "BP",
        "pad1-lane/bd-plastic-anchor-load",
        "supported_pad1_bd_plastic_anchor_load_intent",
        "Pad 1 BD Plastic",
        "load_bd_plastic_profiled_anchor",
        _PAD1_INTENT_PLASTIC,
        "BD Plastic anchor/profile dependency is recorded only.",
        "pad1_bd_plastic_profiled_anchor",
        "",
        False,
        "pad_1_bd_plastic",
        "bd_plastic",
        "anchor_load",
        extra_metadata={
            "requires_current_engine_state": False,
            "requires_bd_plastic_engine_profile": False,
            "requires_bd_plastic_anchor": True,
        },
    ),
    _pad1(
        "PT",
        "pad1-lane/bd-plastic-discovery",
        "supported_pad1_bd_plastic_discovery_intent",
        "Pad 1 BD Plastic",
        "bd_plastic_tone_modulation_discovery",
        _PAD1_INTENT_PLASTIC,
        "BD Plastic engine/profile dependency is recorded only.",
        "pad1_bd_plastic_engine_profile",
        "future_bd_plastic_discovery_depth",
        True,
        "pad_1_bd_plastic",
        "bd_plastic",
        "discovery",
        extra_display_lines=_DEP_PLASTIC_DISCOVERY,
        extra_metadata={
            "requires_current_engine_state": False,
            "requires_bd_plastic_engine_profile": True,
            "requires_bd_plastic_anchor": False,
        },
    ),
    _pad1(
        "PK",
        "pad1-lane/bd-plastic-discovery",
        "supported_pad1_bd_plastic_discovery_intent",
        "Pad 1 BD Plastic",
        "bd_plastic_kick_body_discovery",
        _PAD1_INTENT_PLASTIC,
        "BD Plastic engine/profile dependency is recorded only.",
        "pad1_bd_plastic_engine_profile",
        "future_bd_plastic_discovery_depth",
        True,
        "pad_1_bd_plastic",
        "bd_plastic",
        "discovery",
        extra_display_lines=_DEP_PLASTIC_DISCOVERY,
        extra_metadata={
            "requires_current_engine_state": False,
            "requires_bd_plastic_engine_profile": True,
            "requires_bd_plastic_anchor": False,
        },
    ),
    _pad1(
        "PX",
        "pad1-lane/bd-plastic-discovery",
        "supported_pad1_bd_plastic_discovery_intent",
        "Pad 1 BD Plastic",
        "bd_plastic_rubber_experimental_discovery",
        _PAD1_INTENT_PLASTIC,
        "BD Plastic engine/profile dependency is recorded only.",
        "pad1_bd_plastic_engine_profile",
        "future_bd_plastic_discovery_depth",
        True,
        "pad_1_bd_plastic",
        "bd_plastic",
        "discovery",
        extra_display_lines=_DEP_PLASTIC_DISCOVERY,
        extra_metadata={
            "requires_current_engine_state": False,
            "requires_bd_plastic_engine_profile": True,
            "requires_bd_plastic_anchor": False,
        },
    ),
    _pad1(
        "PBH",
        "pad1-lane/bd-plastic-anchor-return",
        "supported_pad1_bd_plastic_anchor_return_intent",
        "Pad 1 BD Plastic",
        "return_bd_plastic_to_anchor",
        _PAD1_INTENT_PLASTIC,
        "BD Plastic anchor dependency is recorded only.",
        "pad1_bd_plastic_anchor_state",
        "",
        False,
        "pad_1_bd_plastic",
        "bd_plastic",
        "anchor_return",
        extra_metadata={
            "requires_current_engine_state": False,
            "requires_bd_plastic_engine_profile": False,
            "requires_bd_plastic_anchor": True,
        },
    ),
    _pad1(
        "BI",
        "pad1-lane/bd-silky-anchor-load",
        "supported_pad1_bd_silky_anchor_load_intent",
        "Pad 1 BD Silky",
        "load_bd_silky_profiled_anchor",
        _PAD1_INTENT_SILKY,
        "BD Silky anchor/profile dependency is recorded only.",
        "pad1_bd_silky_profiled_anchor",
        "",
        False,
        "pad_1_bd_silky",
        "bd_silky",
        "anchor_load",
        extra_metadata={
            "requires_current_engine_state": False,
            "requires_bd_silky_engine_profile": False,
            "requires_bd_silky_anchor": True,
        },
    ),
    _pad1(
        "ST",
        "pad1-lane/bd-silky-discovery",
        "supported_pad1_bd_silky_discovery_intent",
        "Pad 1 BD Silky",
        "bd_silky_smooth_tone_discovery",
        _PAD1_INTENT_SILKY,
        "BD Silky engine/profile dependency is recorded only.",
        "pad1_bd_silky_engine_profile",
        "future_bd_silky_discovery_depth",
        True,
        "pad_1_bd_silky",
        "bd_silky",
        "discovery",
        extra_display_lines=_DEP_SILKY_DISCOVERY,
        extra_metadata={
            "requires_current_engine_state": False,
            "requires_bd_silky_engine_profile": True,
            "requires_bd_silky_anchor": False,
        },
    ),
    _pad1(
        "SK",
        "pad1-lane/bd-silky-discovery",
        "supported_pad1_bd_silky_discovery_intent",
        "Pad 1 BD Silky",
        "bd_silky_kick_body_discovery",
        _PAD1_INTENT_SILKY,
        "BD Silky engine/profile dependency is recorded only.",
        "pad1_bd_silky_engine_profile",
        "future_bd_silky_discovery_depth",
        True,
        "pad_1_bd_silky",
        "bd_silky",
        "discovery",
        extra_display_lines=_DEP_SILKY_DISCOVERY,
        extra_metadata={
            "requires_current_engine_state": False,
            "requires_bd_silky_engine_profile": True,
            "requires_bd_silky_anchor": False,
        },
    ),
    _pad1(
        "SC",
        "pad1-lane/bd-silky-discovery",
        "supported_pad1_bd_silky_discovery_intent",
        "Pad 1 BD Silky",
        "bd_silky_click_dust_discovery",
        _PAD1_INTENT_SILKY,
        "BD Silky engine/profile dependency is recorded only.",
        "pad1_bd_silky_engine_profile",
        "future_bd_silky_discovery_depth",
        True,
        "pad_1_bd_silky",
        "bd_silky",
        "discovery",
        extra_display_lines=_DEP_SILKY_DISCOVERY,
        extra_metadata={
            "requires_current_engine_state": False,
            "requires_bd_silky_engine_profile": True,
            "requires_bd_silky_anchor": False,
        },
    ),
    _pad1(
        "SBH",
        "pad1-lane/bd-silky-anchor-return",
        "supported_pad1_bd_silky_anchor_return_intent",
        "Pad 1 BD Silky",
        "return_bd_silky_to_anchor",
        _PAD1_INTENT_SILKY,
        "BD Silky anchor dependency is recorded only.",
        "pad1_bd_silky_anchor_state",
        "",
        False,
        "pad_1_bd_silky",
        "bd_silky",
        "anchor_return",
        extra_metadata={
            "requires_current_engine_state": False,
            "requires_bd_silky_engine_profile": False,
            "requires_bd_silky_anchor": True,
        },
    ),
    _pad1(
        "BA",
        "pad1-lane/bd-acoustic-anchor-load",
        "supported_pad1_bd_acoustic_anchor_load_intent",
        "Pad 1 BD Acoustic",
        "load_bd_acoustic_anchor",
        _PAD1_INTENT_ACOUSTIC,
        "BD Acoustic anchor dependency is recorded only.",
        "pad1_bd_acoustic_anchor_state",
        "",
        False,
        "pad_1_bd_acoustic",
        "bd_acoustic",
        "anchor_load",
        extra_display_lines=("Group profile 4 is not used by this Pad 1 command.",),
        extra_metadata={
            "lane_family": "bd_acoustic",
            "requires_current_engine_state": False,
            "requires_bd_acoustic_anchor": True,
            "requires_group_profile_4": False,
            "requires_pad_4": False,
        },
    ),
)


def _padn(
    command_key: str,
    pad: int,
    source: str,
    behavior_family: str,
    reason: str,
    lane: str,
    lane_action: str,
    intent_line: str,
    dependency_line: str,
    intent_kind: str,
    anchor_concept: str = "",
    mode_concept: str = "",
    extra_display_lines: tuple[str, ...] = (),
    extra_metadata: Mapping[str, object] | None = None,
) -> PadLaneCommand:
    return PadLaneCommand(
        command_key=command_key,
        pad=pad,
        source=source,
        behavior_family=behavior_family,
        reason=reason,
        lane=lane,
        lane_action=lane_action,
        intent_line=intent_line,
        dependency_line=dependency_line,
        intent_kind=intent_kind,
        anchor_concept=anchor_concept,
        mode_concept=mode_concept,
        extra_display_lines=extra_display_lines,
        extra_metadata=extra_metadata or {},
    )


# --- Pad 2 -----------------------------------------------------------------
_PAD2_LANE = "Pad 2 secondary lane"
_register(
    _padn(
        "P2B",
        2,
        "PAD2_COMMANDS",
        "pad2-lane/bd-classic-home-anchor",
        "supported_pad2_bd_classic_home_anchor_intent",
        _PAD2_LANE,
        "load_pad2_bd_classic_home_anchor",
        "Read-only Pad 2 BD Classic home anchor intent.",
        "Pad 2 BD Classic home anchor dependency is recorded only.",
        "anchor_load",
        anchor_concept="Pad 2 BD Classic home anchor",
    ),
    _padn(
        "P2H",
        2,
        "PAD2_COMMANDS",
        "pad2-lane/sd-hard-anchor",
        "supported_pad2_sd_hard_anchor_intent",
        _PAD2_LANE,
        "load_pad2_sd_hard_anchor",
        "Read-only Pad 2 SD Hard anchor intent.",
        "Pad 2 SD Hard anchor dependency is recorded only.",
        "anchor_load",
        anchor_concept="Pad 2 SD Hard anchor",
    ),
    _padn(
        "P2C",
        2,
        "PAD2_COMMANDS",
        "pad2-lane/sd-classic-anchor",
        "supported_pad2_sd_classic_anchor_intent",
        _PAD2_LANE,
        "load_pad2_sd_classic_anchor",
        "Read-only Pad 2 SD Classic anchor intent.",
        "Pad 2 SD Classic anchor dependency is recorded only.",
        "anchor_load",
        anchor_concept="Pad 2 SD Classic anchor",
    ),
    _padn(
        "P2F",
        2,
        "PAD2_COMMANDS",
        "pad2-lane/sd-fm-anchor",
        "supported_pad2_sd_fm_anchor_intent",
        _PAD2_LANE,
        "load_pad2_sd_fm_anchor",
        "Read-only Pad 2 SD FM anchor intent.",
        "Pad 2 SD FM anchor dependency is recorded only.",
        "anchor_load",
        anchor_concept="Pad 2 SD FM anchor",
    ),
    _padn(
        "P2T",
        2,
        "PAD2_COMMANDS",
        "pad2-lane/tone-snap-discovery",
        "supported_pad2_tone_snap_discovery_intent",
        _PAD2_LANE,
        "describe_pad2_tone_snap_discovery_intent",
        "Read-only Pad 2 tone/snap discovery intent.",
        "Discovery concept: Pad 2 tone/snap discovery",
        "discovery_intent",
        extra_metadata={"discovery_concept": "Pad 2 tone/snap discovery"},
    ),
    _padn(
        "P2P",
        2,
        "PAD2_COMMANDS",
        "pad2-lane/pressure-body-discovery",
        "supported_pad2_pressure_body_discovery_intent",
        _PAD2_LANE,
        "describe_pad2_pressure_body_discovery_intent",
        "Read-only Pad 2 pressure/body discovery intent.",
        "Discovery concept: Pad 2 pressure/body discovery",
        "discovery_intent",
        extra_metadata={"discovery_concept": "Pad 2 pressure/body discovery"},
    ),
    _padn(
        "P2G",
        2,
        "PAD2_COMMANDS",
        "pad2-lane/grit-noise-discovery",
        "supported_pad2_grit_noise_discovery_intent",
        _PAD2_LANE,
        "describe_pad2_grit_noise_discovery_intent",
        "Read-only Pad 2 grit/noise discovery intent.",
        "Discovery concept: Pad 2 grit/noise discovery",
        "discovery_intent",
        extra_metadata={"discovery_concept": "Pad 2 grit/noise discovery"},
    ),
    _padn(
        "P2R",
        2,
        "PAD2_COMMANDS",
        "pad2-lane/profile-rotation",
        "supported_pad2_profile_rotation_intent",
        _PAD2_LANE,
        "describe_pad2_profile_rotation_intent",
        "Read-only Pad 2 profile rotation intent.",
        "Rotation concept: Pad 2 profiled secondary-lane engine rotation",
        "rotation_intent",
        extra_metadata={"rotation_concept": "Pad 2 profiled secondary-lane engine rotation"},
    ),
    _padn(
        "P2X",
        2,
        "PAD2_COMMANDS",
        "pad2-lane/current-profile-safe-mutation",
        "supported_pad2_current_profile_safe_mutation_intent",
        _PAD2_LANE,
        "describe_pad2_current_profile_safe_mutation_intent",
        "Read-only Pad 2 current-profile safe mutation intent.",
        "Mutation concept: Pad 2 current-profile safe mutation",
        "mutation_intent",
        extra_display_lines=("Selected-profile dependency is recorded only.",),
        extra_metadata={
            "mutation_concept": "Pad 2 current-profile safe mutation",
            "selected_profile_dependency": "current_pad2_profile_state",
        },
    ),
    _padn(
        "P2Z",
        2,
        "PAD2_COMMANDS",
        "pad2-lane/current-profile-anchor-return",
        "supported_pad2_current_profile_anchor_return_intent",
        _PAD2_LANE,
        "describe_pad2_current_profile_anchor_return_intent",
        "Read-only Pad 2 current-profile anchor return intent.",
        "Anchor return concept: Pad 2 current-profile anchor return",
        "anchor_return_intent",
        anchor_concept="Pad 2 current-profile anchor return",
        extra_display_lines=("Selected-profile dependency is recorded only.",),
        extra_metadata={
            "anchor_return_concept": "Pad 2 current-profile anchor return",
            "selected_profile_dependency": "current_pad2_profile_state",
        },
    ),
)


# --- Pad 3 -----------------------------------------------------------------
_PAD3_LANE = "Pad 3 SY Raw lane"
_register(
    _padn(
        "P3A",
        3,
        "PAD3_COMMANDS",
        "pad3-lane/sy-raw-mid-bass-home-anchor",
        "supported_pad3_sy_raw_mid_bass_home_anchor_intent",
        _PAD3_LANE,
        "return_pad3_sy_raw_mid_bass_home_anchor",
        "Read-only Pad 3 SY Raw Mid Bass home anchor intent.",
        "Pad 3 SY Raw Mid Bass home anchor dependency is recorded only.",
        "anchor_return",
        anchor_concept="Pad 3 SY Raw Mid Bass home anchor",
    ),
    _padn(
        "SA",
        3,
        "PAD3_COMMANDS",
        "pad3-lane/sy-raw-anchor-return",
        "supported_pad3_sy_raw_anchor_return_intent",
        _PAD3_LANE,
        "return_pad3_sy_raw_anchor",
        "Read-only Pad 3 SY Raw anchor return intent.",
        "Pad 3 SY Raw anchor dependency is recorded only.",
        "anchor_return",
        anchor_concept="Pad 3 SY Raw anchor",
    ),
    _padn(
        "SL",
        3,
        "PAD3_COMMANDS",
        "pad3-lane/sy-raw-lp1-bassline-mode",
        "supported_pad3_sy_raw_lp1_bassline_mode_intent",
        _PAD3_LANE,
        "load_pad3_sy_raw_lp1_bassline_mode",
        "Read-only Pad 3 SY Raw LP1 bassline mode-load intent.",
        "Pad 3 SY Raw LP1 bassline mode dependency is recorded only.",
        "mode_load",
        mode_concept="Pad 3 SY Raw LP1 bassline mode",
        extra_metadata={"mode_concept": "Pad 3 SY Raw LP1 bassline mode"},
    ),
    _padn(
        "SB",
        3,
        "PAD3_COMMANDS",
        "pad3-lane/sy-raw-bandpass-mid-bass-mode",
        "supported_pad3_sy_raw_bandpass_mid_bass_mode_intent",
        _PAD3_LANE,
        "load_pad3_sy_raw_bandpass_mid_bass_mode",
        "Read-only Pad 3 SY Raw Bandpass mid-bass mode-load intent.",
        "Pad 3 SY Raw Bandpass mid-bass mode dependency is recorded only.",
        "mode_load",
        mode_concept="Pad 3 SY Raw Bandpass mid-bass mode",
        extra_metadata={"mode_concept": "Pad 3 SY Raw Bandpass mid-bass mode"},
    ),
    _padn(
        "SX",
        3,
        "PAD3_COMMANDS",
        "pad3-lane/sy-raw-sci-fi-motion-accent-mode",
        "supported_pad3_sy_raw_sci_fi_motion_accent_mode_intent",
        _PAD3_LANE,
        "load_pad3_sy_raw_sci_fi_motion_accent_mode",
        "Read-only Pad 3 SY Raw sci-fi motion accent mode-load intent.",
        "Pad 3 SY Raw sci-fi motion accent mode dependency is recorded only.",
        "mode_load",
        mode_concept="Pad 3 SY Raw sci-fi motion accent mode",
        extra_metadata={"mode_concept": "Pad 3 SY Raw sci-fi motion accent mode"},
    ),
    _padn(
        "SW",
        3,
        "PAD3_COMMANDS",
        "pad3-lane/sy-raw-wave-balance-discovery",
        "supported_pad3_sy_raw_wave_balance_discovery_intent",
        _PAD3_LANE,
        "describe_pad3_sy_raw_wave_balance_discovery_intent",
        "Read-only Pad 3 SY Raw Wave + Balance discovery intent.",
        "Discovery concept: Pad 3 SY Raw Wave + Balance discovery",
        "discovery",
        extra_metadata={"discovery_concept": "Pad 3 SY Raw Wave + Balance discovery"},
    ),
    _padn(
        "P3R",
        3,
        "PAD3_COMMANDS",
        "pad3-lane/sy-raw-mode-rotation",
        "supported_pad3_sy_raw_mode_rotation_intent",
        _PAD3_LANE,
        "describe_pad3_sy_raw_mode_rotation_intent",
        "Read-only Pad 3 SY Raw behavior mode rotation intent.",
        "Rotation concept: Pad 3 SY Raw behavior mode rotation",
        "rotation",
        extra_metadata={"rotation_concept": "Pad 3 SY Raw behavior mode rotation"},
    ),
    _padn(
        "P3X",
        3,
        "PAD3_COMMANDS",
        "pad3-lane/sy-raw-current-mode-safe-mutation",
        "supported_pad3_sy_raw_current_mode_safe_mutation_intent",
        _PAD3_LANE,
        "describe_pad3_sy_raw_current_mode_safe_mutation_intent",
        "Read-only Pad 3 SY Raw current mode safe mutation intent.",
        "Mutation concept: Pad 3 SY Raw current mode safe mutation",
        "mutation",
        extra_metadata={"mutation_concept": "Pad 3 SY Raw current mode safe mutation"},
    ),
)


# --- Pad 4 -----------------------------------------------------------------
_PAD4_LANE = "Pad 4 BD Acoustic lane"
_register(
    _padn(
        "P4A",
        4,
        "PAD4_COMMANDS",
        "pad4-lane/bd-acoustic-body-accent-home-anchor",
        "supported_pad4_bd_acoustic_home_anchor_intent",
        _PAD4_LANE,
        "return_pad4_bd_acoustic_body_accent_home_anchor",
        "Read-only Pad 4 BD Acoustic body/accent home anchor intent.",
        "Pad 4 BD Acoustic body/accent home anchor dependency is recorded only.",
        "anchor_return",
        anchor_concept="Pad 4 BD Acoustic body/accent home anchor",
    ),
    _padn(
        "P4R",
        4,
        "PAD4_COMMANDS",
        "pad4-lane/bd-acoustic-mode-rotation",
        "supported_pad4_bd_acoustic_mode_rotation_intent",
        _PAD4_LANE,
        "describe_pad4_bd_acoustic_mode_rotation_intent",
        "Read-only Pad 4 BD Acoustic behavior mode rotation intent.",
        "Rotation concept: Pad 4 BD Acoustic behavior mode rotation",
        "rotation",
        extra_metadata={"rotation_concept": "Pad 4 BD Acoustic behavior mode rotation"},
    ),
    _padn(
        "P4X",
        4,
        "PAD4_COMMANDS",
        "pad4-lane/bd-acoustic-current-mode-safe-mutation",
        "supported_pad4_bd_acoustic_current_mode_safe_mutation_intent",
        _PAD4_LANE,
        "describe_pad4_bd_acoustic_current_mode_safe_mutation_intent",
        "Read-only Pad 4 BD Acoustic current mode safe mutation intent.",
        "Mutation concept: Pad 4 BD Acoustic current mode safe mutation",
        "mutation",
        extra_metadata={"mutation_concept": "Pad 4 BD Acoustic current mode safe mutation"},
    ),
)


PAD_LANE_REGISTRY: Mapping[str, PadLaneCommand] = MappingProxyType(_REGISTRY)

_SOURCE_COMMANDS = {
    "PAD1_COMMANDS": PAD1_COMMANDS,
    "PAD2_COMMANDS": PAD2_COMMANDS,
    "PAD3_COMMANDS": PAD3_COMMANDS,
    "PAD4_COMMANDS": PAD4_COMMANDS,
}

_NO_PROMPT_TAIL = (
    "No prompt would run.",
    "No state would change.",
    "No command would dispatch.",
    "No command would execute.",
    "No lane state would mutate.",
    "No MIDI would be sent.",
    "No ports would be opened.",
    "No hardware would be required.",
)


# --------------------------------------------------------------------------
# Pad 1 public API (thin formatters over the registry).
# --------------------------------------------------------------------------
def _pad1_accepted_metadata(command: PadLaneCommand) -> dict[str, object]:
    command_metadata = PAD1_COMMANDS[command.command_key]
    metadata: dict[str, object] = {
        "source": "PAD1_COMMANDS",
        "source_command_type": command_metadata["type"],
        "source_command_scope": command_metadata["scope"],
        "source_v134_reference_command": command_metadata["v134_reference_command"],
        "source_scaffold_only": command_metadata["scaffold_only"],
        "target_pad": command.pad,
        "lane": command.lane_metadata,
        "lane_action": command.lane_action,
        "requires_current_engine_state": True,
        "requires_depth_selection": command.requires_depth_selection,
        "mock_only": True,
        "sends_real_midi": False,
        "opens_ports": False,
        "hardware_required": False,
        "active_behavior": False,
        "mutates_runtime_state": False,
        "dispatches_command": False,
        "executes_command": False,
    }
    metadata.update(dict(command.extra_metadata))
    return metadata


def _pad1_accepted_result(command: PadLaneCommand) -> Pad1LaneBehaviorResult:
    command_metadata = PAD1_COMMANDS[command.command_key]
    label = command_metadata["label"]

    display_lines = (
        f"{command.command_key}: {label}",
        command.intent_line,
        f"Target pad: {command.pad}",
        f"Lane: {command.lane}",
        f"Lane action: {command.lane_action}",
        command.dependency_line,
        *command.extra_display_lines,
        *_NO_PROMPT_TAIL,
    )

    return Pad1LaneBehaviorResult(
        command_key=command.command_key,
        label=label,
        accepted=True,
        behavior_family=command.behavior_family,
        reason=command.reason,
        target_pad=command.pad,
        lane=command.lane,
        lane_action=command.lane_action,
        engine_dependency=command.engine_dependency,
        depth_dependency=command.depth_dependency,
        display_lines=display_lines,
        metadata=_pad1_accepted_metadata(command),
    )


def _safe_failure_metadata(source: str) -> dict[str, object]:
    return {
        "source": source,
        "mock_only": True,
        "sends_real_midi": False,
        "opens_ports": False,
        "hardware_required": False,
        "active_behavior": False,
        "mutates_runtime_state": False,
        "dispatches_command": False,
        "executes_command": False,
    }


def _safe_state_metadata(source: str) -> dict[str, object]:
    metadata = _safe_failure_metadata(source)
    metadata.update(
        {
            "metadata_only": True,
            "executes": False,
            "mutates_runtime_state": False,
            "dispatches_command": False,
        }
    )
    return metadata


def evaluate_pad1_lane_behavior(command_key) -> Pad1LaneBehaviorResult:
    """Return a passive Packet 5 Pad 1 lane behavior result."""

    key = str(command_key)
    command = _REGISTRY.get(key)

    if command is not None and command.pad == 1:
        return _pad1_accepted_result(command)

    if key in DEFERRED_PACKET_5_PAD1_LANE_KEYS:
        return Pad1LaneBehaviorResult(
            command_key=key,
            accepted=False,
            reason="deferred_pad1_lane_command",
            metadata=_safe_failure_metadata("PAD1_COMMANDS"),
        )

    if key in COMMANDS:
        return Pad1LaneBehaviorResult(
            command_key=key,
            accepted=False,
            reason="unsupported_pad1_lane_command",
            metadata=_safe_failure_metadata("COMMANDS"),
        )

    return Pad1LaneBehaviorResult(
        command_key=key,
        accepted=False,
        reason="unknown_command",
        metadata=_safe_failure_metadata("unknown"),
    )


def _pad1_accepted_state_descriptor(
    command: PadLaneCommand,
) -> Pad1LaneStateDescriptor:
    behavior = evaluate_pad1_lane_behavior(command.command_key)
    intent_kind = command.state_intent_kind
    lane_family = command.state_lane_family
    depth_dependency = command.depth_dependency
    discovery_depth = depth_dependency if intent_kind == "discovery" else ""
    mutation_depth = depth_dependency if intent_kind == "mutation" else ""
    requires_anchor = intent_kind in ("anchor_load", "anchor_return")
    requires_profiled_engine = intent_kind == "discovery"
    anchor_key = command.command_key if requires_anchor else ""
    return_key = command.command_key if intent_kind == "anchor_return" else ""
    requires_current_engine = command.command_key in PACKET_5A_PAD1_CURRENT_ENGINE_KEYS

    metadata = dict(behavior.metadata)
    metadata.update(
        {
            "source_key": command.command_key,
            "lane_family": lane_family,
            "intent_kind": intent_kind,
            "requires_current_engine": requires_current_engine,
            "requires_anchor": requires_anchor,
            "requires_profiled_engine": requires_profiled_engine,
            "anchor_key": anchor_key,
            "return_key": return_key,
            "discovery_depth": discovery_depth,
            "mutation_depth": mutation_depth,
            "metadata_only": True,
            "executes": False,
            "sends_real_midi": False,
            "opens_ports": False,
            "hardware_required": False,
            "mutates_runtime_state": False,
            "dispatches_command": False,
        }
    )

    return Pad1LaneStateDescriptor(
        source_key=command.command_key,
        supported=True,
        reason=behavior.reason,
        target_pad=behavior.target_pad,
        lane_family=lane_family,
        lane_action=behavior.lane_action,
        intent_kind=intent_kind,
        requires_current_engine=requires_current_engine,
        requires_anchor=requires_anchor,
        requires_profiled_engine=requires_profiled_engine,
        anchor_key=anchor_key,
        return_key=return_key,
        discovery_depth=discovery_depth,
        mutation_depth=mutation_depth,
        metadata_only=True,
        executes=False,
        sends_midi=False,
        opens_ports=False,
        hardware_required=False,
        notes=behavior.display_lines,
        metadata=metadata,
    )


def describe_pad1_lane_state(command_key) -> Pad1LaneStateDescriptor:
    """Return a static read-only Pad 1 lane-state descriptor."""

    key = str(command_key)
    command = _REGISTRY.get(key)

    if command is not None and command.pad == 1:
        return _pad1_accepted_state_descriptor(command)

    if key in COMMANDS:
        return Pad1LaneStateDescriptor(
            source_key=key,
            supported=False,
            reason="unsupported_pad1_lane_command",
            metadata=_safe_state_metadata("COMMANDS"),
        )

    return Pad1LaneStateDescriptor(
        source_key=key,
        supported=False,
        reason="unknown_command",
        metadata=_safe_state_metadata("unknown"),
    )


# --------------------------------------------------------------------------
# Shared Pad 2-4 formatter.
# --------------------------------------------------------------------------
def _padn_accepted_result(command: PadLaneCommand, result_cls):
    source_commands = _SOURCE_COMMANDS[command.source]
    command_metadata = source_commands[command.command_key]
    label = command_metadata["label"]
    lane_metadata_value = f"pad_{command.pad}_" + (
        "secondary_lane"
        if command.pad == 2
        else "sy_raw_lane" if command.pad == 3 else "bd_acoustic_lane"
    )

    result_metadata: dict[str, object] = {
        "source": command.source,
        "command_type": command_metadata["type"],
        "target_pad": command_metadata["pad"],
        "lane": lane_metadata_value,
        "behavior_family": command.behavior_family,
        "lane_action": command.lane_action,
        "intent_kind": command.intent_kind,
    }
    if command.anchor_concept:
        result_metadata["anchor_concept"] = command.anchor_concept
    result_metadata.update(dict(command.extra_metadata))
    result_metadata.update(
        {
            "mock_only": True,
            "sends_real_midi": False,
            "opens_ports": False,
            "hardware_required": False,
            "active_behavior": False,
            "mutates_runtime_state": False,
            "dispatches_command": False,
        }
    )

    display_lines = (
        f"{command.command_key}: {label}",
        command.intent_line,
        f"Target pad: {command.pad}",
        f"Lane: {command.lane}",
        f"Lane action: {command.lane_action}",
        command.dependency_line,
        *command.extra_display_lines,
        *_NO_PROMPT_TAIL,
    )

    kwargs: dict[str, object] = {
        "command_key": command.command_key,
        "label": label,
        "behavior_family": command.behavior_family,
        "accepted": True,
        "reason": command.reason,
        "target_pad": command.pad,
        "lane": command.lane,
        "lane_action": command.lane_action,
        "intent_kind": command.intent_kind,
        "anchor_concept": command.anchor_concept,
        "display_lines": display_lines,
        "metadata": result_metadata,
    }
    if result_cls is Pad3LaneBehaviorResult:
        kwargs["mode_concept"] = command.mode_concept
    return result_cls(**kwargs)


# --------------------------------------------------------------------------
# Pad 2 public API.
# --------------------------------------------------------------------------
def evaluate_pad2_lane_behavior(command_key) -> Pad2LaneBehaviorResult:
    """Return a passive Packet 6 behavior result for a Pad 2 command key."""

    key = str(command_key)
    command = _REGISTRY.get(key)

    if command is not None and command.pad == 2:
        return _padn_accepted_result(command, Pad2LaneBehaviorResult)

    if key in COMMANDS:
        return Pad2LaneBehaviorResult(
            command_key=key,
            accepted=False,
            reason="unsupported_pad2_lane_command",
            metadata={
                "source": "COMMANDS",
                "mock_only": True,
                "sends_real_midi": False,
                "opens_ports": False,
                "hardware_required": False,
                "active_behavior": False,
            },
        )

    return Pad2LaneBehaviorResult(
        command_key=key,
        accepted=False,
        reason="unknown_command",
        metadata={
            "source": "unknown",
            "mock_only": True,
            "sends_real_midi": False,
        },
    )


# --------------------------------------------------------------------------
# Pad 3 public API.
# --------------------------------------------------------------------------
def evaluate_pad3_lane_behavior(command_key) -> Pad3LaneBehaviorResult:
    """Return a passive Packet 7 behavior result for a Pad 3 command key."""

    key = str(command_key)
    command = _REGISTRY.get(key)

    if command is not None and command.pad == 3:
        return _padn_accepted_result(command, Pad3LaneBehaviorResult)

    if key in COMMANDS:
        return Pad3LaneBehaviorResult(
            command_key=key,
            accepted=False,
            reason="unsupported_packet_7_pad3_lane_key",
            metadata={
                "source": "COMMANDS",
                "mock_only": True,
                "sends_real_midi": False,
                "opens_ports": False,
                "hardware_required": False,
                "active_behavior": False,
            },
        )

    return Pad3LaneBehaviorResult(
        command_key=key,
        accepted=False,
        reason="unknown_command",
        metadata={
            "source": "unknown",
            "mock_only": True,
            "sends_real_midi": False,
        },
    )


# --------------------------------------------------------------------------
# Pad 4 public API.
# --------------------------------------------------------------------------
def evaluate_pad4_lane_behavior(command_key) -> Pad4LaneBehaviorResult:
    """Return a passive Packet 8 behavior result for a Pad 4 command key."""

    key = str(command_key)
    command = _REGISTRY.get(key)

    if command is not None and command.pad == 4:
        return _padn_accepted_result(command, Pad4LaneBehaviorResult)

    if key in COMMANDS:
        return Pad4LaneBehaviorResult(
            command_key=key,
            accepted=False,
            reason="unsupported_packet_8_pad4_lane_key",
            metadata={
                "source": "COMMANDS",
                "mock_only": True,
                "sends_real_midi": False,
                "opens_ports": False,
                "hardware_required": False,
                "active_behavior": False,
                "mutates_runtime_state": False,
                "dispatches_command": False,
            },
        )

    return Pad4LaneBehaviorResult(
        command_key=key,
        accepted=False,
        reason="unknown_command",
        metadata={
            "source": "unknown",
            "mock_only": True,
            "sends_real_midi": False,
        },
    )


__all__ = [
    "PadLaneCommand",
    "PAD_LANE_REGISTRY",
    "PAD1_LANE_KEYS",
    "DEFERRED_PACKET_5_PAD1_LANE_KEYS",
    "PACKET_5A_PAD1_CURRENT_ENGINE_KEYS",
    "PACKET_5B_PAD1_BD_FM_KEYS",
    "PACKET_5C_PAD1_BD_PLASTIC_KEYS",
    "PACKET_5D_PAD1_BD_SILKY_KEYS",
    "PACKET_5E_PAD1_BD_ACOUSTIC_KEYS",
    "DEFERRED_PACKET_6_PAD2_LANE_KEYS",
    "PACKET_6A_PAD2_LANE_KEYS",
    "PACKET_6B_PAD2_LANE_KEYS",
    "PACKET_6C_PAD2_LANE_KEYS",
    "PACKET_6D_PAD2_LANE_KEYS",
    "PACKET_6E_PAD2_LANE_KEYS",
    "PACKET_6F_PAD2_LANE_KEYS",
    "PACKET_6G_PAD2_LANE_KEYS",
    "PACKET_6H_PAD2_LANE_KEYS",
    "PACKET_6I_PAD2_LANE_KEYS",
    "PACKET_6J_PAD2_LANE_KEYS",
    "DEFERRED_PACKET_7_PAD3_LANE_KEYS",
    "PACKET_7A_PAD3_LANE_KEYS",
    "PACKET_7B_PAD3_LANE_KEYS",
    "PACKET_7C_PAD3_LANE_KEYS",
    "PACKET_7D_PAD3_LANE_KEYS",
    "PACKET_7E_PAD3_LANE_KEYS",
    "PACKET_7F_PAD3_LANE_KEYS",
    "PACKET_7G_PAD3_LANE_KEYS",
    "PACKET_7H_PAD3_LANE_KEYS",
    "DEFERRED_PACKET_8_PAD4_LANE_KEYS",
    "PACKET_8A_PAD4_LANE_KEYS",
    "PACKET_8B_PAD4_LANE_KEYS",
    "PACKET_8C_PAD4_LANE_KEYS",
    "Pad1LaneBehaviorResult",
    "Pad1LaneStateDescriptor",
    "Pad2LaneBehaviorResult",
    "Pad3LaneBehaviorResult",
    "Pad4LaneBehaviorResult",
    "describe_pad1_lane_state",
    "evaluate_pad1_lane_behavior",
    "evaluate_pad2_lane_behavior",
    "evaluate_pad3_lane_behavior",
    "evaluate_pad4_lane_behavior",
]
