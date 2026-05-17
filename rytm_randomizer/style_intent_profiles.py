"""Passive style-intent profiles for 12-pad kit planning.

This module translates broad genre/style language into essence tags. It does
not analyze audio, open MIDI ports, send MIDI, receive SysEx, write SysEx,
execute commands, or mutate hardware.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from .essence_plan_report import parse_discovery_value
from .essence_tag_adapter import ESSENCE_TAG_ORDER, derive_essence_tags_from_description
from .machine_catalog import MachineCandidate, build_essence_role_plan


@dataclass(frozen=True)
class StyleIntentProfile:
    """One broad style/genre intent profile."""

    key: str
    label: str
    aliases: tuple[str, ...]
    description: str
    essence_tags: tuple[str, ...]
    discovery_hint: float
    analog_rytm_note: str
    analog_four_note: str


@dataclass(frozen=True)
class StyleIntentRequest:
    """Resolved style prompt and planning settings."""

    prompt: str
    matched_profiles: tuple[StyleIntentProfile, ...]
    tags: tuple[str, ...]
    discovery: float


STYLE_INTENT_PROFILES: tuple[StyleIntentProfile, ...] = (
    StyleIntentProfile(
        key="broken_techno",
        label="Broken Techno",
        aliases=("broken techno", "broken", "broken beat techno"),
        description="Off-grid pressure, fractured motion, and rough percussion flow.",
        essence_tags=("driving", "repetition", "density", "noise", "raw", "motion", "groove"),
        discovery_hint=0.65,
        analog_rytm_note="Use motion and percussion lanes for fractured rhythmic pressure.",
        analog_four_note="Future A4 role: unstable tonal pulses and syncopated modulation.",
    ),
    StyleIntentProfile(
        key="dark_techno",
        label="Dark Techno",
        aliases=("dark techno", "dark", "deep dark techno"),
        description="Low, tense, noisy, and controlled.",
        essence_tags=("driving", "pressure", "repetition", "low", "deep", "noise", "tension"),
        discovery_hint=0.55,
        analog_rytm_note="Favor low-end weight, restrained brightness, and pressure lanes.",
        analog_four_note="Future A4 role: dark drones, tuned pressure, and controlled filter motion.",
    ),
    StyleIntentProfile(
        key="birmingham_techno",
        label="Birmingham Techno",
        aliases=("birmingham techno", "birmingham", "birmingham style techno"),
        description="Industrial metallic pressure with raw forward motion.",
        essence_tags=(
            "metallic",
            "driving",
            "pressure",
            "repetition",
            "density",
            "noise",
            "raw",
            "tension",
        ),
        discovery_hint=0.68,
        analog_rytm_note="Use metallic and pressure candidates while keeping the kick foundation hard.",
        analog_four_note="Future A4 role: cold FM-like stabs, drones, and abrasive modulation.",
    ),
    StyleIntentProfile(
        key="hardcore",
        label="Hardcore",
        aliases=("hardcore", "hard techno", "hardcore techno"),
        description="High-pressure, dense, bright, and forceful.",
        essence_tags=("driving", "pressure", "repetition", "density", "bright", "noise", "tension"),
        discovery_hint=0.78,
        analog_rytm_note="Push pressure and density while preserving a recoverable foundation.",
        analog_four_note="Future A4 role: aggressive sequences and clipped tonal accents.",
    ),
    StyleIntentProfile(
        key="schranz",
        label="Schranz",
        aliases=("schranz", "schranz techno"),
        description="Hard, distorted, dense, noisy, and relentlessly driving.",
        essence_tags=(
            "metallic",
            "driving",
            "pressure",
            "repetition",
            "density",
            "bright",
            "noise",
            "raw",
            "tension",
        ),
        discovery_hint=0.82,
        analog_rytm_note="Use dense pressure, grit, and metallic impact while preserving an escape path.",
        analog_four_note="Future A4 role: distorted sequences, hard sync motion, and aggressive stabs.",
    ),
    StyleIntentProfile(
        key="classic_detroit_techno",
        label="Classic Detroit Techno",
        aliases=("classic detroit techno", "detroit techno", "classic detroit"),
        description="Classic machine groove, Detroit bell/tonal flavor, and driving repetition.",
        essence_tags=("bell", "detroit", "driving", "repetition", "analog", "classic", "groove"),
        discovery_hint=0.45,
        analog_rytm_note="Favor groove, bell-like tonal accents, and usable classic machine pressure.",
        analog_four_note="Future A4 role: chord stabs, analog motifs, and melodic counter-motion.",
    ),
    StyleIntentProfile(
        key="driving_techno",
        label="Driving Techno",
        aliases=("driving techno", "driving", "rolling driving techno"),
        description="Forward repetition with low-end stability and pressure.",
        essence_tags=("driving", "pressure", "repetition", "low", "groove"),
        discovery_hint=0.50,
        analog_rytm_note="Keep the kick stable while secondary lanes add forward movement.",
        analog_four_note="Future A4 role: rolling basslines and locked melodic pressure.",
    ),
    StyleIntentProfile(
        key="peak_time_techno",
        label="Peak Time Techno",
        aliases=("peak time techno", "peak-time techno", "peak time", "big room techno"),
        description="Dense, bright, high-pressure, and performance-forward.",
        essence_tags=("driving", "pressure", "repetition", "density", "bright", "tension"),
        discovery_hint=0.72,
        analog_rytm_note="Use density and tension while keeping return-to-anchor safety obvious.",
        analog_four_note="Future A4 role: large hooks, risers, and bright tonal movement.",
    ),
)


def list_style_intent_profiles() -> tuple[StyleIntentProfile, ...]:
    """Return deterministic style-intent profiles."""

    return STYLE_INTENT_PROFILES


def match_style_intent_profiles(prompt: str) -> tuple[StyleIntentProfile, ...]:
    """Return style profiles whose aliases appear in the prompt."""

    normalized = _normalize_prompt(prompt)
    return tuple(
        profile
        for profile in STYLE_INTENT_PROFILES
        if any(_contains_alias(normalized, alias) for alias in profile.aliases)
    )


def derive_style_intent_tags(prompt: str) -> tuple[str, ...]:
    """Derive essence tags from style-intent profiles and free description text."""

    tags = set(derive_essence_tags_from_description(prompt))
    for profile in match_style_intent_profiles(prompt):
        tags.update(profile.essence_tags)
    return tuple(tag for tag in ESSENCE_TAG_ORDER if tag in tags)


def build_style_intent_request(
    prompt: str,
    *,
    discovery: float | None = None,
) -> StyleIntentRequest:
    """Resolve a style prompt into essence tags and a Discovery value."""

    if not isinstance(prompt, str):
        raise TypeError("style prompt must be a string")
    matched = match_style_intent_profiles(prompt)
    if discovery is None:
        discovery_value = _average_discovery_hint(matched)
    else:
        discovery_value = parse_discovery_value(str(discovery))
    return StyleIntentRequest(
        prompt=prompt,
        matched_profiles=matched,
        tags=derive_style_intent_tags(prompt),
        discovery=discovery_value,
    )


def format_style_intent_report(
    prompt: str,
    *,
    discovery: float | None = None,
) -> list[str]:
    """Format a deterministic passive style-intent kit report."""

    request = build_style_intent_request(prompt, discovery=discovery)
    role_plan = build_essence_role_plan(
        essence_tags=request.tags,
        discovery=request.discovery,
    )
    lines = [
        "RytmRandomizer passive Style Intent Report",
        f"Style prompt: {request.prompt}",
        f"Matched profiles: {_format_matched_profiles(request.matched_profiles)}",
        f"Essence tags: {_format_tags(request.tags)}",
        f"Discovery: {request.discovery:.2f}",
        "Analog Rytm: passive 12-pad essence plan preview",
        "Analog Four: future expansion target only; no current A4 mapping",
        "12-pad style kit plan:",
    ]
    for assignment in role_plan:
        candidate_text = ", ".join(
            _format_candidate(candidate) for candidate in assignment.candidates
        )
        lines.append(f"- Pad {assignment.pad} / {assignment.role.label}: {candidate_text}")
    lines.extend(
        [
            "Safety:",
            "- passive/read-only",
            "- no audio file analysis",
            "- no MIDI sending",
            "- no port opening",
            "- no command execution",
            "- no hardware mutation",
            "- no live SysEx receive",
            "- no SysEx writes",
            "- no Analog Four runtime support",
            "- no Pads 5-12 runtime mutation",
            "- no hardware required",
        ]
    )
    return lines


def format_style_intent_error(message: str) -> list[str]:
    """Format a deterministic passive style-intent error report."""

    return [
        "RytmRandomizer passive Style Intent Report",
        "Found: False",
        f"Message: {message}. No MIDI was sent. No command executed.",
        "Safety:",
        "- passive/read-only",
        "- no MIDI sending",
        "- no port opening",
        "- no command execution",
        "- no hardware mutation",
        "- no hardware required",
    ]


def _normalize_prompt(prompt: str) -> str:
    if not isinstance(prompt, str):
        raise TypeError("style prompt must be a string")
    return prompt.strip().lower()


def _contains_alias(prompt: str, alias: str) -> bool:
    escaped = re.escape(alias.lower())
    if " " in alias:
        return alias.lower() in prompt
    return re.search(rf"\b{escaped}\b", prompt) is not None


def _average_discovery_hint(profiles: tuple[StyleIntentProfile, ...]) -> float:
    if not profiles:
        return 0.50
    return round(sum(profile.discovery_hint for profile in profiles) / len(profiles), 2)


def _format_matched_profiles(profiles: tuple[StyleIntentProfile, ...]) -> str:
    return ", ".join(profile.label for profile in profiles) if profiles else "none"


def _format_tags(tags: tuple[str, ...]) -> str:
    return ", ".join(tags) if tags else "none"


def _format_candidate(candidate: MachineCandidate) -> str:
    marker = "mutable" if candidate.machine.support_status == "mutable_v134" else "future"
    return f"{candidate.machine.label} [{marker}]"


__all__ = [
    "StyleIntentProfile",
    "StyleIntentRequest",
    "build_style_intent_request",
    "derive_style_intent_tags",
    "format_style_intent_error",
    "format_style_intent_report",
    "list_style_intent_profiles",
    "match_style_intent_profiles",
]
