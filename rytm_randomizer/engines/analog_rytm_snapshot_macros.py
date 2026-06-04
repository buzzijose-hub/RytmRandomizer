"""Passive macro definitions for the all-12-pad Rytm snapshot shell."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Final, Literal, TypeAlias

MacroMode: TypeAlias = Literal["live", "studio"]
MacroLane: TypeAlias = Literal["tune", "noise", "fx", "filter", "amp", "lfo"]
MacroLanePolicy: TypeAlias = Literal["off", "micro", "normal", "wide"]
MacroAmount: TypeAlias = Literal["micro", "normal", "wide"]
MacroDensity: TypeAlias = Literal["off", "low", "medium", "high", "full"]
MacroBias: TypeAlias = Literal[
    "neutral",
    "darker",
    "brighter",
    "tighter",
    "looser",
    "grittier",
]
MacroRiskLabel: TypeAlias = Literal["live-safe", "edge", "studio", "blocked"]


@dataclass(frozen=True)
class SnapshotMacroPadPolicy:
    """Pad-level randomizer policy overrides for one live macro."""

    amount: MacroAmount | None = None
    density: MacroDensity | None = None
    bias: MacroBias | None = None
    lane_policies: Mapping[MacroLane, MacroLanePolicy] = field(
        default_factory=lambda: MappingProxyType({})
    )
    section_family_allowlists: Mapping[str, frozenset[str]] = field(
        default_factory=lambda: MappingProxyType({})
    )


@dataclass(frozen=True)
class SnapshotLiveMacroSpec:
    """Passive, GUI-ready definition for one snapshot-shell live macro."""

    name: str
    label: str
    mode: MacroMode
    lane_policies: Mapping[MacroLane, MacroLanePolicy]
    locked_pads: frozenset[int]
    pad_policies: Mapping[int, SnapshotMacroPadPolicy]
    recovery_action: str
    risk_label: MacroRiskLabel
    summary: str


_AMP_FX_FAMILIES: Final[frozenset[str]] = frozenset({"delay", "drive", "reverb"})
_BASE_LIVE_LANES: Final[Mapping[MacroLane, MacroLanePolicy]] = MappingProxyType(
    {"lfo": "off", "fx": "micro"}
)
_DUB_PRESSURE_LANES: Final[Mapping[MacroLane, MacroLanePolicy]] = MappingProxyType(
    {"lfo": "off", "fx": "normal"}
)
_TRANSITION_LANES: Final[Mapping[MacroLane, MacroLanePolicy]] = MappingProxyType(
    {"lfo": "micro", "fx": "normal"}
)
_RESERVED_PAD_LANES: Final[Mapping[MacroLane, MacroLanePolicy]] = MappingProxyType(
    {"filter": "off", "lfo": "off"}
)
_TOM_PAD_LANES: Final[Mapping[MacroLane, MacroLanePolicy]] = MappingProxyType(
    {"filter": "micro", "lfo": "off"}
)


def _allowlists(*, amp_fx_only: bool) -> Mapping[str, frozenset[str]]:
    if not amp_fx_only:
        return MappingProxyType({})
    return MappingProxyType({"AMP": _AMP_FX_FAMILIES})


def _pad_policy(
    *,
    amount: MacroAmount | None = None,
    density: MacroDensity | None = None,
    bias: MacroBias | None = None,
    lanes: Mapping[MacroLane, MacroLanePolicy] | None = None,
    amp_fx_only: bool = False,
) -> SnapshotMacroPadPolicy:
    return SnapshotMacroPadPolicy(
        amount=amount,
        density=density,
        bias=bias,
        lane_policies=MappingProxyType(dict(lanes or {})),
        section_family_allowlists=_allowlists(amp_fx_only=amp_fx_only),
    )


def _macro(
    *,
    name: str,
    label: str,
    lane_policies: Mapping[MacroLane, MacroLanePolicy],
    pad_policies: Mapping[int, SnapshotMacroPadPolicy],
    risk_label: MacroRiskLabel,
    summary: str,
) -> SnapshotLiveMacroSpec:
    return SnapshotLiveMacroSpec(
        name=name,
        label=label,
        mode="live",
        lane_policies=MappingProxyType(dict(lane_policies)),
        locked_pads=frozenset({1}),
        pad_policies=MappingProxyType(dict(pad_policies)),
        recovery_action="home",
        risk_label=risk_label,
        summary=summary,
    )


def _reserved_pad_policy(
    *,
    amount: MacroAmount,
    density: MacroDensity,
    bias: MacroBias | None = None,
) -> SnapshotMacroPadPolicy:
    return _pad_policy(
        amount=amount,
        density=density,
        bias=bias,
        lanes=_RESERVED_PAD_LANES,
        amp_fx_only=True,
    )


def _tom_pad_policy(
    *,
    amount: MacroAmount,
    density: MacroDensity,
    bias: MacroBias,
) -> SnapshotMacroPadPolicy:
    return _pad_policy(
        amount=amount,
        density=density,
        bias=bias,
        lanes=_TOM_PAD_LANES,
        amp_fx_only=True,
    )


SNAPSHOT_LIVE_MACROS: Final[Mapping[str, SnapshotLiveMacroSpec]] = MappingProxyType(
    {
        "kit-core": _macro(
            name="kit-core",
            label="Kit Core",
            lane_policies=_BASE_LIVE_LANES,
            risk_label="live-safe",
            summary="Full-kit live-safe discovery with Jose's pad 5-11 lane discipline.",
            pad_policies={
                2: _pad_policy(amount="wide", density="full", bias="looser"),
                3: _pad_policy(amount="wide", density="full", bias="grittier"),
                4: _pad_policy(amount="wide", density="full", bias="grittier"),
                5: _reserved_pad_policy(amount="normal", density="high"),
                6: _tom_pad_policy(amount="wide", density="full", bias="tighter"),
                7: _tom_pad_policy(amount="wide", density="full", bias="tighter"),
                8: _tom_pad_policy(amount="wide", density="full", bias="tighter"),
                9: _reserved_pad_policy(amount="normal", density="high"),
                10: _reserved_pad_policy(amount="normal", density="high"),
                11: _reserved_pad_policy(amount="normal", density="high"),
            },
        ),
        "hard-groove": _macro(
            name="hard-groove",
            label="Hard Groove",
            lane_policies=_BASE_LIVE_LANES,
            risk_label="live-safe",
            summary="Dry pressure macro for OXI patterns that already carry the groove.",
            pad_policies={
                2: _pad_policy(amount="normal", density="high", bias="tighter"),
                3: _pad_policy(amount="normal", density="high", bias="tighter"),
                4: _pad_policy(amount="normal", density="high", bias="grittier"),
                5: _reserved_pad_policy(
                    amount="normal",
                    density="high",
                    bias="tighter",
                ),
                6: _tom_pad_policy(amount="wide", density="full", bias="tighter"),
                7: _tom_pad_policy(amount="wide", density="full", bias="tighter"),
                8: _tom_pad_policy(amount="wide", density="full", bias="tighter"),
                9: _reserved_pad_policy(
                    amount="normal",
                    density="high",
                    bias="brighter",
                ),
                10: _reserved_pad_policy(
                    amount="normal",
                    density="high",
                    bias="brighter",
                ),
                11: _reserved_pad_policy(
                    amount="normal",
                    density="high",
                    bias="brighter",
                ),
                12: _pad_policy(
                    amount="normal",
                    density="medium",
                    bias="neutral",
                    amp_fx_only=True,
                ),
            },
        ),
        "industrial": _macro(
            name="industrial",
            label="Industrial",
            lane_policies=_BASE_LIVE_LANES,
            risk_label="edge",
            summary="Metallic pressure and controlled grit without releasing the kick anchor.",
            pad_policies={
                2: _pad_policy(amount="wide", density="full", bias="grittier"),
                3: _pad_policy(amount="wide", density="full", bias="grittier"),
                4: _pad_policy(amount="wide", density="full", bias="grittier"),
                5: _reserved_pad_policy(
                    amount="normal",
                    density="high",
                    bias="grittier",
                ),
                6: _tom_pad_policy(amount="wide", density="full", bias="grittier"),
                7: _tom_pad_policy(amount="wide", density="full", bias="grittier"),
                8: _tom_pad_policy(amount="wide", density="full", bias="grittier"),
                9: _reserved_pad_policy(
                    amount="normal",
                    density="high",
                    bias="brighter",
                ),
                10: _reserved_pad_policy(
                    amount="normal",
                    density="high",
                    bias="brighter",
                ),
                11: _reserved_pad_policy(
                    amount="normal",
                    density="high",
                    bias="grittier",
                ),
                12: _pad_policy(
                    amount="wide",
                    density="high",
                    bias="grittier",
                    amp_fx_only=True,
                ),
            },
        ),
        "dub-pressure": _macro(
            name="dub-pressure",
            label="Dub Pressure",
            lane_policies=_DUB_PRESSURE_LANES,
            risk_label="live-safe",
            summary="Darker pressure with more delay/reverb influence and small filter motion.",
            pad_policies={
                2: _pad_policy(amount="normal", density="medium", bias="darker"),
                3: _pad_policy(amount="normal", density="medium", bias="looser"),
                4: _pad_policy(amount="normal", density="medium", bias="darker"),
                5: _reserved_pad_policy(
                    amount="normal",
                    density="medium",
                    bias="darker",
                ),
                6: _tom_pad_policy(amount="normal", density="high", bias="looser"),
                7: _tom_pad_policy(amount="normal", density="high", bias="looser"),
                8: _tom_pad_policy(amount="normal", density="high", bias="looser"),
                9: _reserved_pad_policy(
                    amount="micro",
                    density="medium",
                    bias="darker",
                ),
                10: _reserved_pad_policy(
                    amount="micro",
                    density="medium",
                    bias="darker",
                ),
                11: _reserved_pad_policy(
                    amount="micro",
                    density="medium",
                    bias="darker",
                ),
                12: _pad_policy(
                    amount="normal",
                    density="medium",
                    bias="darker",
                    amp_fx_only=True,
                ),
            },
        ),
        "transition": _macro(
            name="transition",
            label="Transition",
            lane_policies=_TRANSITION_LANES,
            risk_label="edge",
            summary="Set-section movement with obvious recovery through home.",
            pad_policies={
                2: _pad_policy(amount="wide", density="full", bias="looser"),
                3: _pad_policy(amount="wide", density="full", bias="grittier"),
                4: _pad_policy(amount="wide", density="full", bias="looser"),
                5: _reserved_pad_policy(
                    amount="normal",
                    density="high",
                    bias="brighter",
                ),
                6: _tom_pad_policy(amount="wide", density="high", bias="looser"),
                7: _tom_pad_policy(amount="wide", density="high", bias="looser"),
                8: _tom_pad_policy(amount="wide", density="high", bias="looser"),
                9: _reserved_pad_policy(
                    amount="normal",
                    density="high",
                    bias="brighter",
                ),
                10: _reserved_pad_policy(
                    amount="normal",
                    density="high",
                    bias="brighter",
                ),
                11: _reserved_pad_policy(
                    amount="normal",
                    density="high",
                    bias="brighter",
                ),
                12: _pad_policy(
                    amount="wide",
                    density="medium",
                    bias="looser",
                    amp_fx_only=True,
                ),
            },
        ),
        "home": SnapshotLiveMacroSpec(
            name="home",
            label="Home",
            mode="live",
            lane_policies=MappingProxyType({}),
            locked_pads=frozenset(),
            pad_policies=MappingProxyType({}),
            recovery_action="home",
            risk_label="live-safe",
            summary="Return the current staged plan to the captured anchor.",
        ),
    }
)


__all__ = (
    "MacroAmount",
    "MacroBias",
    "MacroDensity",
    "MacroLane",
    "MacroLanePolicy",
    "MacroMode",
    "MacroRiskLabel",
    "SNAPSHOT_LIVE_MACROS",
    "SnapshotLiveMacroSpec",
    "SnapshotMacroPadPolicy",
)
