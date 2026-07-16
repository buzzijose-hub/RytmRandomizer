"""Passive natural-language mutation-intent packets for local AI review."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Final

from .provider import (
    LocalAiMessage,
    LocalAiValidationError,
    local_ai_message_to_dict,
    require_bool,
    require_int_range,
    require_string,
    require_string_list,
)

MUTATION_INTENT_VERSION: Final[str] = "local-ai-mutation-intent-v1"
DEFAULT_TARGET_DEVICE: Final[str] = "analog_rytm_mk2"
MUTATION_INTENT_SAFETY: Final[tuple[str, ...]] = (
    "passive mutation-intent packet",
    "staged suggestions only",
    "no MIDI sent",
    "no MIDI ports opened",
    "no runtime mutation executed",
)
MUTATION_INTENT_BLOCKED_ACTIONS: Final[tuple[str, ...]] = (
    "open MIDI output",
    "send MIDI",
    "write SysEx",
    "execute runtime mutation",
    "mutate connected hardware",
)

_MUTATION_REQUIRED: Final[list[str]] = [
    "intent_label",
    "target_device",
    "mutation_depth",
    "parameter_focus",
    "guardrails",
    "blocked_actions",
    "safety_notes",
    "staged_only",
]


@dataclass(frozen=True)
class StagedMutationIntent:
    """Validated passive mutation intent."""

    intent_label: str
    target_device: str
    mutation_depth: int
    parameter_focus: tuple[str, ...]
    guardrails: tuple[str, ...]
    blocked_actions: tuple[str, ...]
    safety_notes: tuple[str, ...]
    staged_only: bool


@dataclass(frozen=True)
class MutationIntentPacket:
    """Prompt packet for local natural-language mutation-intent extraction."""

    version: str
    source_text: str
    intent: StagedMutationIntent
    messages: tuple[LocalAiMessage, ...]
    schema: dict[str, object]
    safety: tuple[str, ...]


def build_mutation_intent_packet(
    text: str,
    *,
    target_device: str = DEFAULT_TARGET_DEVICE,
) -> MutationIntentPacket:
    """Build a deterministic staged mutation-intent packet."""

    source_text = require_string(text, label="text")
    device = require_string(target_device, label="target_device")
    intent = StagedMutationIntent(
        intent_label=_intent_label(source_text),
        target_device=device,
        mutation_depth=_mutation_depth(source_text),
        parameter_focus=_parameter_focus(source_text),
        guardrails=_guardrails(source_text),
        blocked_actions=MUTATION_INTENT_BLOCKED_ACTIONS,
        safety_notes=(
            "operator must review before any deterministic send-plan compiler",
            "AI output cannot arm hardware",
        ),
        staged_only=True,
    )
    messages = (
        LocalAiMessage(
            role="system",
            content=(
                "Extract a passive RytmRandomizer mutation intent. Return JSON only. "
                "Never include instructions to send MIDI, open hardware devices, or "
                "execute a runtime mutation."
            ),
        ),
        LocalAiMessage(
            role="user",
            content=(
                f"Target device: {device}\n"
                f"Operator request: {source_text}\n"
                "Return staged intent JSON matching the schema."
            ),
        ),
    )
    return MutationIntentPacket(
        version=MUTATION_INTENT_VERSION,
        source_text=source_text,
        intent=intent,
        messages=messages,
        schema=mutation_intent_schema(),
        safety=MUTATION_INTENT_SAFETY,
    )


def mutation_intent_schema() -> dict[str, object]:
    """Return the JSON schema expected from the local mutation-intent model."""

    return {
        "type": "object",
        "properties": {
            "intent_label": {"type": "string"},
            "target_device": {"type": "string"},
            "mutation_depth": {"type": "integer", "minimum": 1, "maximum": 4},
            "parameter_focus": {"type": "array", "items": {"type": "string"}},
            "guardrails": {"type": "array", "items": {"type": "string"}},
            "blocked_actions": {"type": "array", "items": {"type": "string"}},
            "safety_notes": {"type": "array", "items": {"type": "string"}},
            "staged_only": {"type": "boolean"},
        },
        "required": list(_MUTATION_REQUIRED),
    }


def mutation_intent_packet_to_dict(packet: MutationIntentPacket) -> dict[str, object]:
    """Return a JSON-ready packet payload."""

    return {
        "version": packet.version,
        "source_text": packet.source_text,
        "intent": staged_mutation_intent_to_dict(packet.intent),
        "messages": [local_ai_message_to_dict(message) for message in packet.messages],
        "schema": packet.schema,
        "safety": list(packet.safety),
    }


def validate_mutation_intent_payload(payload: dict[str, object]) -> StagedMutationIntent:
    """Validate a model-produced staged mutation intent."""

    staged_only = require_bool(payload.get("staged_only"), label="staged_only")
    if not staged_only:
        raise LocalAiValidationError("staged_only must be true")
    depth = require_int_range(
        payload.get("mutation_depth"),
        label="mutation_depth",
        minimum=1,
        maximum=4,
    )
    blocked_actions = require_string_list(payload.get("blocked_actions"), label="blocked_actions")
    for required_action in ("open MIDI output", "send MIDI"):
        if required_action not in blocked_actions:
            raise LocalAiValidationError(f"blocked_actions must include {required_action!r}")
    return StagedMutationIntent(
        intent_label=require_string(payload.get("intent_label"), label="intent_label"),
        target_device=require_string(payload.get("target_device"), label="target_device"),
        mutation_depth=depth,
        parameter_focus=require_string_list(
            payload.get("parameter_focus"),
            label="parameter_focus",
        ),
        guardrails=require_string_list(payload.get("guardrails"), label="guardrails"),
        blocked_actions=blocked_actions,
        safety_notes=require_string_list(payload.get("safety_notes"), label="safety_notes"),
        staged_only=True,
    )


def staged_mutation_intent_to_dict(intent: StagedMutationIntent) -> dict[str, object]:
    """Return a JSON-ready staged-intent payload."""

    return {
        "intent_label": intent.intent_label,
        "target_device": intent.target_device,
        "mutation_depth": intent.mutation_depth,
        "parameter_focus": list(intent.parameter_focus),
        "guardrails": list(intent.guardrails),
        "blocked_actions": list(intent.blocked_actions),
        "safety_notes": list(intent.safety_notes),
        "staged_only": intent.staged_only,
    }


def _intent_label(text: str) -> str:
    words = _intent_tokens(text)
    if "dark" in words or "darker" in words:
        return "darker staged mutation"
    if "bright" in words or "brighter" in words:
        return "brighter staged mutation"
    return "staged mutation"


def _mutation_depth(text: str) -> int:
    words = set(_intent_tokens(text))
    if {"wild", "aggressive", "extreme", "harder"} & words:
        return 3
    if {"subtle", "light", "slight", "gentle"} & words:
        return 1
    return 2


def _parameter_focus(text: str) -> tuple[str, ...]:
    words = set(_intent_tokens(text))
    focus: list[str] = []
    if {"dark", "darker", "filter", "lowpass"} & words:
        focus.append("filter_darkness")
    if {"noise", "noisy", "texture", "grain"} & words:
        focus.append("texture_noise")
    if {"bright", "brighter", "percussion", "hat", "metallic"} & words:
        focus.append("percussion_brightness")
    if {"movement", "motion", "lfo", "evolve"} & words:
        focus.append("modulation_motion")
    if {"low", "bass", "kick", "weight"} & words:
        focus.append("low_end_weight")
    return tuple(dict.fromkeys(focus or ["balanced_variation"]))


def _guardrails(text: str) -> tuple[str, ...]:
    words = set(_intent_tokens(text))
    guardrails = ["operator review before any send plan"]
    if {"kick", "stable", "stability"} & words:
        guardrails.append("kick_stability")
    if {"less", "reduce", "safer", "safe"} & words:
        guardrails.append("avoid_extreme_parameter_jumps")
    return tuple(dict.fromkeys(guardrails))


def _intent_tokens(text: str) -> tuple[str, ...]:
    return tuple(re.findall(r"[a-z0-9]+", text.lower()))


__all__ = [
    "DEFAULT_TARGET_DEVICE",
    "MUTATION_INTENT_BLOCKED_ACTIONS",
    "MUTATION_INTENT_SAFETY",
    "MUTATION_INTENT_VERSION",
    "MutationIntentPacket",
    "StagedMutationIntent",
    "build_mutation_intent_packet",
    "mutation_intent_packet_to_dict",
    "mutation_intent_schema",
    "staged_mutation_intent_to_dict",
    "validate_mutation_intent_payload",
]
