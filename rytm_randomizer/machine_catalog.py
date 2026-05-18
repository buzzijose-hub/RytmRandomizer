"""Passive Analog Rytm machine catalog and essence-role matcher.

The catalog is planning metadata only. It does not import MIDI libraries, open
ports, send messages, request dumps, write SysEx, or mutate hardware.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

SupportStatus = Literal["mutable_v134", "machine_selectable", "needs_manual_mapping"]


@dataclass(frozen=True)
class MachineProfile:
    """Passive description of one Analog Rytm machine family."""

    key: str
    label: str
    family: str
    machine_value: int | None
    support_status: SupportStatus
    role_tags: tuple[str, ...]
    essence_tags: tuple[str, ...]
    character_tags: tuple[str, ...]


@dataclass(frozen=True)
class PadRole:
    """One 12-pad performance role for reference-driven kit planning."""

    pad: int
    key: str
    label: str
    desired_tags: tuple[str, ...]
    role_weight: int


@dataclass(frozen=True)
class MachineCandidate:
    """A ranked machine candidate for a pad role."""

    machine: MachineProfile
    score: float
    matched_tags: tuple[str, ...]


@dataclass(frozen=True)
class RoleAssignment:
    """Candidate machines for one 12-pad role assignment."""

    pad: int
    role: PadRole
    candidates: tuple[MachineCandidate, ...]


MACHINE_PROFILES: tuple[MachineProfile, ...] = (
    MachineProfile(
        key="bd_hard",
        label="BD Hard",
        family="bd",
        machine_value=0,
        support_status="mutable_v134",
        role_tags=("kick", "foundation", "low", "drive"),
        essence_tags=("driving", "pressure", "classic", "weight"),
        character_tags=("solid", "punchy", "stable"),
    ),
    MachineProfile(
        key="bd_classic",
        label="BD Classic",
        family="bd",
        machine_value=1,
        support_status="mutable_v134",
        role_tags=("kick", "secondary_low", "body", "percussion"),
        essence_tags=("classic", "round", "rolling", "groove"),
        character_tags=("warm", "round", "supporting"),
    ),
    MachineProfile(
        key="bd_sharp",
        label="BD Sharp",
        family="bd",
        machine_value=26,
        support_status="mutable_v134",
        role_tags=("kick", "attack", "accent", "click"),
        essence_tags=("sharp", "transient", "pressure", "driving"),
        character_tags=("tight", "pointed", "fast"),
    ),
    MachineProfile(
        key="bd_acoustic",
        label="BD Acoustic",
        family="bd",
        machine_value=30,
        support_status="mutable_v134",
        role_tags=("body", "accent", "pressure", "percussion"),
        essence_tags=("body", "thump", "organic", "push"),
        character_tags=("large", "soft_edge", "physical"),
    ),
    MachineProfile(
        key="bd_fm",
        label="BD FM",
        family="bd",
        machine_value=13,
        support_status="mutable_v134",
        role_tags=("kick", "metallic", "tonal", "accent"),
        essence_tags=("metallic", "bell", "detroit", "tension"),
        character_tags=("glassy", "electric", "ringing"),
    ),
    MachineProfile(
        key="bd_plastic",
        label="BD Plastic",
        family="bd",
        machine_value=21,
        support_status="mutable_v134",
        role_tags=("kick", "rubber", "experimental", "body"),
        essence_tags=("rubber", "modern", "synthetic", "bounce"),
        character_tags=("elastic", "odd", "rounded"),
    ),
    MachineProfile(
        key="bd_silky",
        label="BD Silky",
        family="bd",
        machine_value=22,
        support_status="mutable_v134",
        role_tags=("kick", "deep", "smooth", "foundation"),
        essence_tags=("deep", "smooth", "subtle", "low"),
        character_tags=("soft", "polished", "deep"),
    ),
    MachineProfile(
        key="sd_hard",
        label="SD Hard",
        family="sd",
        machine_value=2,
        support_status="mutable_v134",
        role_tags=("snare", "pressure", "accent", "transient"),
        essence_tags=("sharp", "pressure", "snap", "driving"),
        character_tags=("hard", "present", "cutting"),
    ),
    MachineProfile(
        key="sd_classic",
        label="SD Classic",
        family="sd",
        machine_value=3,
        support_status="mutable_v134",
        role_tags=("snare", "clap", "backbeat", "rolling"),
        essence_tags=("classic", "groove", "snap", "body"),
        character_tags=("familiar", "balanced", "usable"),
    ),
    MachineProfile(
        key="sd_fm",
        label="SD FM",
        family="sd",
        machine_value=14,
        support_status="mutable_v134",
        role_tags=("snare", "metallic", "accent", "noise"),
        essence_tags=("metallic", "bell", "electric", "tension"),
        character_tags=("bright", "ringing", "abrasive"),
    ),
    MachineProfile(
        key="sy_raw",
        label="SY Raw",
        family="sy",
        machine_value=32,
        support_status="mutable_v134",
        role_tags=("synth", "bass", "motion", "tonal", "texture"),
        essence_tags=("raw", "motion", "tension", "repetition"),
        character_tags=("wide", "animated", "synthetic"),
    ),
    MachineProfile(
        key="sy_chip",
        label="SY Chip",
        family="sy",
        machine_value=29,
        support_status="machine_selectable",
        role_tags=("synth", "digital", "metallic", "tonal", "motif"),
        essence_tags=("digital", "bell", "metallic", "repetition"),
        character_tags=("sharp", "pixel", "chirp"),
    ),
    MachineProfile(
        key="dual_vco",
        label="Dual VCO",
        family="sy",
        machine_value=28,
        support_status="machine_selectable",
        role_tags=("synth", "tonal", "bass", "tension", "motif"),
        essence_tags=("analog", "tuned", "tension", "drone"),
        character_tags=("thick", "alive", "pitched"),
    ),
    MachineProfile(
        key="sd_natural",
        label="SD Natural",
        family="sd",
        machine_value=23,
        support_status="machine_selectable",
        role_tags=("snare", "body", "organic", "accent"),
        essence_tags=("natural", "body", "groove", "pressure"),
        character_tags=("rounded", "physical", "supporting"),
    ),
    MachineProfile(
        key="sd_acoustic",
        label="SD Acoustic",
        family="sd",
        machine_value=31,
        support_status="machine_selectable",
        role_tags=("snare", "acoustic", "body", "accent"),
        essence_tags=("organic", "body", "snap", "classic"),
        character_tags=("wide", "human", "physical"),
    ),
    MachineProfile(
        key="rs_hard",
        label="RS Hard",
        family="rim",
        machine_value=4,
        support_status="machine_selectable",
        role_tags=("rim", "click", "accent", "texture", "transient"),
        essence_tags=("click", "transient", "repetition", "minimal", "pressure"),
        character_tags=("short", "dry", "hard"),
    ),
    MachineProfile(
        key="rs_classic",
        label="RS Classic",
        family="rim",
        machine_value=5,
        support_status="machine_selectable",
        role_tags=("rim", "click", "accent", "texture"),
        essence_tags=("click", "classic", "repetition", "minimal"),
        character_tags=("short", "dry", "precise"),
    ),
    MachineProfile(
        key="cp_classic",
        label="CP Classic",
        family="clap",
        machine_value=6,
        support_status="machine_selectable",
        role_tags=("clap", "snare", "accent", "noise", "width"),
        essence_tags=("snap", "width", "pressure", "classic"),
        character_tags=("wide", "noisy", "human"),
    ),
    MachineProfile(
        key="bt_classic",
        label="BT Classic",
        family="tom",
        machine_value=7,
        support_status="machine_selectable",
        role_tags=("body", "percussion", "rolling", "accent"),
        essence_tags=("body", "groove", "round", "classic"),
        character_tags=("round", "mid", "supporting"),
    ),
    MachineProfile(
        key="xt_classic",
        label="XT Classic",
        family="tom",
        machine_value=8,
        support_status="machine_selectable",
        role_tags=("body", "percussion", "rolling", "accent", "high"),
        essence_tags=("body", "groove", "bright", "classic"),
        character_tags=("tight", "mid", "supporting"),
    ),
    MachineProfile(
        key="ch_classic",
        label="CH Classic",
        family="hat",
        machine_value=9,
        support_status="machine_selectable",
        role_tags=("hat", "pulse", "high", "noise"),
        essence_tags=("density", "bright", "repetition", "air"),
        character_tags=("tight", "dry", "classic"),
    ),
    MachineProfile(
        key="ch_metallic",
        label="CH Metallic",
        family="hat",
        machine_value=17,
        support_status="machine_selectable",
        role_tags=("hat", "pulse", "high", "metallic", "noise"),
        essence_tags=("density", "bright", "metallic", "repetition"),
        character_tags=("sharp", "ringing", "tight"),
    ),
    MachineProfile(
        key="oh_classic",
        label="OH Classic",
        family="hat",
        machine_value=10,
        support_status="machine_selectable",
        role_tags=("hat", "noise", "lift", "high", "open"),
        essence_tags=("bright", "air", "wash", "repetition"),
        character_tags=("open", "shimmer", "classic"),
    ),
    MachineProfile(
        key="oh_metallic",
        label="OH Metallic",
        family="hat",
        machine_value=18,
        support_status="machine_selectable",
        role_tags=("hat", "noise", "lift", "high", "metallic", "open"),
        essence_tags=("bright", "metallic", "air", "tension"),
        character_tags=("open", "ringing", "shimmer"),
    ),
    MachineProfile(
        key="hh_basic",
        label="HH Basic",
        family="hat",
        machine_value=24,
        support_status="machine_selectable",
        role_tags=("hat", "pulse", "lift", "high", "noise"),
        essence_tags=("density", "bright", "repetition", "air"),
        character_tags=("basic", "usable", "tight"),
    ),
    MachineProfile(
        key="hh_lab",
        label="HH Lab",
        family="hat",
        machine_value=33,
        support_status="machine_selectable",
        role_tags=("hat", "pulse", "lift", "high", "experimental", "noise"),
        essence_tags=("density", "bright", "raw", "tension"),
        character_tags=("modern", "flexible", "edgy"),
    ),
    MachineProfile(
        key="cy_classic",
        label="CY Classic",
        family="cymbal",
        machine_value=11,
        support_status="machine_selectable",
        role_tags=("cymbal", "metallic", "noise", "accent", "high"),
        essence_tags=("metallic", "bright", "wash", "classic"),
        character_tags=("ringing", "splash", "wide"),
    ),
    MachineProfile(
        key="cy_metallic",
        label="CY Metallic",
        family="cymbal",
        machine_value=19,
        support_status="machine_selectable",
        role_tags=("cymbal", "metallic", "noise", "accent", "high"),
        essence_tags=("metallic", "bright", "wash", "tension"),
        character_tags=("ringing", "abrasive", "wide"),
    ),
    MachineProfile(
        key="cy_ride",
        label="CY Ride",
        family="cymbal",
        machine_value=25,
        support_status="machine_selectable",
        role_tags=("cymbal", "ride", "metallic", "pulse", "high"),
        essence_tags=("metallic", "repetition", "bright", "tension"),
        character_tags=("steady", "ringing", "wide"),
    ),
    MachineProfile(
        key="cb_classic",
        label="CB Classic",
        family="cowbell",
        machine_value=12,
        support_status="machine_selectable",
        role_tags=("bell", "metallic", "tonal", "accent"),
        essence_tags=("bell", "classic", "metallic", "repetition"),
        character_tags=("short", "pitched", "familiar"),
    ),
    MachineProfile(
        key="cb_metallic",
        label="CB Metallic",
        family="cowbell",
        machine_value=20,
        support_status="machine_selectable",
        role_tags=("bell", "metallic", "tonal", "accent"),
        essence_tags=("bell", "metallic", "tension", "bright"),
        character_tags=("ringing", "pitched", "sharp"),
    ),
    MachineProfile(
        key="ut_noise",
        label="UT Noise",
        family="utility",
        machine_value=15,
        support_status="machine_selectable",
        role_tags=("noise", "texture", "air", "experimental"),
        essence_tags=("noise", "raw", "density", "tension"),
        character_tags=("noisy", "wide", "unstable"),
    ),
    MachineProfile(
        key="ut_impulse",
        label="UT Impulse",
        family="utility",
        machine_value=16,
        support_status="machine_selectable",
        role_tags=("click", "transient", "accent", "experimental"),
        essence_tags=("click", "minimal", "repetition", "raw"),
        character_tags=("short", "dry", "sharp"),
    ),
    MachineProfile(
        key="rs_family",
        label="RS family",
        family="rim",
        machine_value=None,
        support_status="needs_manual_mapping",
        role_tags=("rim", "click", "accent", "texture"),
        essence_tags=("click", "transient", "repetition", "minimal"),
        character_tags=("short", "dry", "precise"),
    ),
    MachineProfile(
        key="cp_family",
        label="CP family",
        family="clap",
        machine_value=None,
        support_status="needs_manual_mapping",
        role_tags=("clap", "snare", "accent", "noise"),
        essence_tags=("snap", "width", "pressure", "classic"),
        character_tags=("wide", "noisy", "human"),
    ),
    MachineProfile(
        key="hat_family",
        label="CH/OH hat family",
        family="hat",
        machine_value=None,
        support_status="needs_manual_mapping",
        role_tags=("hat", "noise", "pulse", "lift", "high"),
        essence_tags=("density", "bright", "repetition", "air"),
        character_tags=("tight", "open", "shimmer"),
    ),
    MachineProfile(
        key="cymbal_family",
        label="CY/CB cymbal family",
        family="cymbal",
        machine_value=None,
        support_status="needs_manual_mapping",
        role_tags=("cymbal", "metallic", "noise", "accent", "high"),
        essence_tags=("metallic", "bright", "wash", "tension"),
        character_tags=("ringing", "splash", "wide"),
    ),
)


TWELVE_PAD_ROLES: tuple[PadRole, ...] = (
    PadRole(1, "main_kick_foundation", "Main kick foundation", ("kick", "foundation", "low"), 5),
    PadRole(
        2, "secondary_low_percussion", "Secondary low percussion", ("secondary_low", "body"), 4
    ),
    PadRole(3, "metallic_motif", "Metallic motif", ("metallic", "tonal", "motif"), 5),
    PadRole(4, "body_accent_hit", "Body/accent hit", ("body", "accent", "pressure"), 4),
    PadRole(5, "closed_hat_pulse", "Closed hat pulse", ("hat", "pulse", "high"), 4),
    PadRole(6, "open_hat_noise_lift", "Open hat / noise lift", ("hat", "noise", "lift"), 4),
    PadRole(7, "rim_click_texture", "Rim/click texture", ("rim", "click", "texture"), 3),
    PadRole(8, "snare_clap_pressure", "Snare/clap pressure", ("snare", "clap", "pressure"), 4),
    PadRole(9, "tonal_bell_accent", "Tonal bell accent", ("tonal", "bell", "metallic"), 5),
    PadRole(10, "rolling_percussion", "Rolling percussion", ("rolling", "percussion", "groove"), 3),
    PadRole(11, "atmosphere_noise_layer", "Atmosphere/noise layer", ("noise", "texture", "air"), 3),
    PadRole(12, "wild_discovery_lane", "Wild discovery lane", ("experimental", "tension"), 2),
)


def list_machine_profiles() -> tuple[MachineProfile, ...]:
    """Return all passive machine profiles."""

    return MACHINE_PROFILES


def get_machine_profile(key: str) -> MachineProfile:
    """Return a passive machine profile by key."""

    for profile in MACHINE_PROFILES:
        if profile.key == key:
            return profile
    raise KeyError(f"unknown machine profile: {key!r}")


def list_twelve_pad_roles() -> tuple[PadRole, ...]:
    """Return the reference-driven 12-pad role template."""

    return TWELVE_PAD_ROLES


def get_pad_role(key: str) -> PadRole:
    """Return a 12-pad role by key."""

    for role in TWELVE_PAD_ROLES:
        if role.key == key:
            return role
    raise KeyError(f"unknown pad role: {key!r}")


def rank_machines_for_role(
    role_key: str,
    *,
    essence_tags: tuple[str, ...] = (),
    include_unmapped: bool = False,
    include_machine_selectable: bool = False,
) -> tuple[MachineCandidate, ...]:
    """Rank machine candidates for a role and reference essence tags."""

    role = get_pad_role(role_key)
    candidates: list[MachineCandidate] = []
    essence = tuple(tag.lower() for tag in essence_tags)

    for machine in MACHINE_PROFILES:
        if not _include_machine(
            machine,
            include_unmapped=include_unmapped,
            include_machine_selectable=include_machine_selectable,
        ):
            continue

        matched = _matched_tags(role, machine, essence)
        score = _score_machine(role, machine, matched)
        if score <= 0:
            continue
        candidates.append(MachineCandidate(machine=machine, score=score, matched_tags=matched))

    return tuple(sorted(candidates, key=_candidate_sort_key))


def build_essence_role_plan(
    *,
    essence_tags: tuple[str, ...] = (),
    discovery: float = 0.0,
    candidates_per_role: int = 4,
    include_machine_selectable: bool = False,
    ensure_mutable_fallback: bool = True,
) -> tuple[RoleAssignment, ...]:
    """Build a passive 12-pad role plan from reference essence tags."""

    include_unmapped = discovery >= 0.75
    assignments: list[RoleAssignment] = []
    for role in TWELVE_PAD_ROLES:
        ranked = rank_machines_for_role(
            role.key,
            essence_tags=essence_tags,
            include_unmapped=include_unmapped,
            include_machine_selectable=include_machine_selectable,
        )
        candidates = _candidate_window(
            ranked,
            candidates_per_role=candidates_per_role,
            ensure_mutable_fallback=ensure_mutable_fallback,
        )
        assignments.append(RoleAssignment(pad=role.pad, role=role, candidates=candidates))
    return tuple(assignments)


def _matched_tags(
    role: PadRole,
    machine: MachineProfile,
    essence_tags: tuple[str, ...],
) -> tuple[str, ...]:
    machine_tags = set(machine.role_tags + machine.essence_tags + machine.character_tags)
    desired = set(role.desired_tags)
    essence = set(essence_tags)
    matched = sorted((desired | essence).intersection(machine_tags))
    return tuple(matched)


def _score_machine(role: PadRole, machine: MachineProfile, matched_tags: tuple[str, ...]) -> float:
    role_matches = set(role.desired_tags).intersection(machine.role_tags)
    score = float((len(role_matches) * role.role_weight) + len(matched_tags))
    if machine.support_status == "machine_selectable":
        score -= 0.75
    if machine.support_status == "needs_manual_mapping":
        score -= 2.0
    return score


def _candidate_sort_key(candidate: MachineCandidate) -> tuple[float, int, str]:
    return (
        -candidate.score,
        _support_sort_rank(candidate.machine.support_status),
        candidate.machine.key,
    )


def _include_machine(
    machine: MachineProfile,
    *,
    include_unmapped: bool,
    include_machine_selectable: bool,
) -> bool:
    if machine.support_status == "mutable_v134":
        return True
    if machine.support_status == "machine_selectable":
        return include_machine_selectable or include_unmapped
    return include_unmapped


def _support_sort_rank(support_status: SupportStatus) -> int:
    if support_status == "mutable_v134":
        return 0
    if support_status == "machine_selectable":
        return 1
    return 2


def _candidate_window(
    candidates: tuple[MachineCandidate, ...],
    *,
    candidates_per_role: int,
    ensure_mutable_fallback: bool,
) -> tuple[MachineCandidate, ...]:
    window = tuple(candidates[:candidates_per_role])
    if not ensure_mutable_fallback:
        return window
    if any(candidate.machine.support_status == "mutable_v134" for candidate in window):
        return window
    fallback = next(
        (
            candidate
            for candidate in candidates[candidates_per_role:]
            if candidate.machine.support_status == "mutable_v134"
        ),
        None,
    )
    if fallback is None:
        return window
    if not window:
        return (fallback,)
    return window[:-1] + (fallback,)
