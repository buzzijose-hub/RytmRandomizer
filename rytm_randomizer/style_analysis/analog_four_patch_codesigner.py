"""Passive Analog Four patch co-designer prompt packets."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

from ..local_ai import LocalAiMessage, local_ai_message_to_dict
from ..local_ai.provider import (
    LocalAiValidationError,
    require_bool,
    require_int_range,
    require_mapping_list,
    require_string,
    require_string_list,
)
from .analog_four_patch_genome import (
    AnalogFourPatchCandidate,
    AnalogFourPatchGenome,
    analog_four_patch_candidate_to_dict,
    analog_four_patch_genome_to_dict,
    build_analog_four_patch_genome,
)
from .feature_report import FeatureReport

ANALOG_FOUR_PATCH_CODESIGNER_VERSION: Final[str] = "analog-four-patch-codesigner-v1"
ANALOG_FOUR_PATCH_CODESIGNER_SAFETY: Final[tuple[str, ...]] = (
    "passive A4 patch co-designer",
    "staged review metadata only",
    "no MIDI sent",
    "no MIDI ports opened",
    "no send plan compiled",
    "no SysEx written",
)
ANALOG_FOUR_PATCH_CODESIGNER_READINESS_REASON: Final[str] = (
    "ollama suggestions are staged review metadata only"
)

_CODESIGNER_REQUIRED: Final[list[str]] = [
    "summary",
    "selected_candidate",
    "audition_notes",
    "parameter_edits",
    "safety_notes",
    "staged_only",
]


@dataclass(frozen=True)
class PatchParameterEdit:
    """One staged parameter edit suggested by the co-designer."""

    parameter: str
    direction: str
    reason: str


@dataclass(frozen=True)
class PatchCodesignerSuggestion:
    """Validated co-designer suggestion."""

    summary: str
    selected_candidate: int
    audition_notes: tuple[str, ...]
    parameter_edits: tuple[PatchParameterEdit, ...]
    safety_notes: tuple[str, ...]
    staged_only: bool


@dataclass(frozen=True)
class AnalogFourPatchCodesignerPacket:
    """Passive prompt packet for A4 patch co-design."""

    version: str
    description: str
    selected_candidate: int
    genome: AnalogFourPatchGenome
    reference_candidate: AnalogFourPatchCandidate
    messages: tuple[LocalAiMessage, ...]
    schema: dict[str, object]
    safety: tuple[str, ...]
    ready_for_send: bool
    readiness_reason: str


def build_analog_four_patch_codesigner_packet(
    report: FeatureReport,
    *,
    description: str,
    track: int = 1,
    selected_candidate: int = 1,
) -> AnalogFourPatchCodesignerPacket:
    """Build a passive local-AI co-designer packet from a feature report."""

    source_description = require_string(description, label="description")
    genome = build_analog_four_patch_genome(report, track=track)
    if selected_candidate < 1 or selected_candidate > genome.candidate_count:
        raise ValueError(f"selected_candidate must be in 1..{genome.candidate_count}")
    reference_candidate = genome.candidates[selected_candidate - 1]
    messages = (
        LocalAiMessage(
            role="system",
            content=(
                "You are a passive Analog Four patch co-designer. Suggest staged "
                "review notes only. Do not produce MIDI send instructions, SysEx, "
                "or hardware actions."
            ),
        ),
        LocalAiMessage(
            role="user",
            content=_codesigner_prompt(source_description, genome, reference_candidate),
        ),
    )
    return AnalogFourPatchCodesignerPacket(
        version=ANALOG_FOUR_PATCH_CODESIGNER_VERSION,
        description=source_description,
        selected_candidate=selected_candidate,
        genome=genome,
        reference_candidate=reference_candidate,
        messages=messages,
        schema=analog_four_patch_codesigner_schema(),
        safety=ANALOG_FOUR_PATCH_CODESIGNER_SAFETY,
        ready_for_send=False,
        readiness_reason=ANALOG_FOUR_PATCH_CODESIGNER_READINESS_REASON,
    )


def analog_four_patch_codesigner_schema() -> dict[str, object]:
    """Return the JSON schema expected from the patch co-designer."""

    return {
        "type": "object",
        "properties": {
            "summary": {"type": "string"},
            "selected_candidate": {"type": "integer", "minimum": 1, "maximum": 4},
            "audition_notes": {"type": "array", "items": {"type": "string"}},
            "parameter_edits": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "parameter": {"type": "string"},
                        "direction": {"type": "string"},
                        "reason": {"type": "string"},
                    },
                    "required": ["parameter", "direction", "reason"],
                },
            },
            "safety_notes": {"type": "array", "items": {"type": "string"}},
            "staged_only": {"type": "boolean"},
        },
        "required": list(_CODESIGNER_REQUIRED),
    }


def analog_four_patch_codesigner_packet_to_dict(
    packet: AnalogFourPatchCodesignerPacket,
) -> dict[str, object]:
    """Return a JSON-ready packet payload."""

    return {
        "version": packet.version,
        "description": packet.description,
        "selected_candidate": packet.selected_candidate,
        "genome": analog_four_patch_genome_to_dict(packet.genome),
        "reference_candidate": analog_four_patch_candidate_to_dict(packet.reference_candidate),
        "messages": [local_ai_message_to_dict(message) for message in packet.messages],
        "schema": packet.schema,
        "safety": list(packet.safety),
        "ready_for_send": packet.ready_for_send,
        "readiness_reason": packet.readiness_reason,
    }


def validate_patch_codesigner_payload(
    payload: dict[str, object],
    *,
    genome: AnalogFourPatchGenome,
) -> PatchCodesignerSuggestion:
    """Validate a model-produced patch co-designer suggestion."""

    staged_only = require_bool(payload.get("staged_only"), label="staged_only")
    if not staged_only:
        raise LocalAiValidationError("staged_only must be true")
    selected_candidate = require_int_range(
        payload.get("selected_candidate"),
        label="selected_candidate",
        minimum=1,
        maximum=genome.candidate_count,
    )
    valid_parameters = {
        gene.value.parameter for candidate in genome.candidates for gene in candidate.genes
    }
    edits = tuple(
        _validate_parameter_edit(edit, valid_parameters=valid_parameters)
        for edit in require_mapping_list(payload.get("parameter_edits"), label="parameter_edits")
    )
    return PatchCodesignerSuggestion(
        summary=require_string(payload.get("summary"), label="summary"),
        selected_candidate=selected_candidate,
        audition_notes=require_string_list(payload.get("audition_notes"), label="audition_notes"),
        parameter_edits=edits,
        safety_notes=require_string_list(payload.get("safety_notes"), label="safety_notes"),
        staged_only=True,
    )


def patch_codesigner_suggestion_to_dict(
    suggestion: PatchCodesignerSuggestion,
) -> dict[str, object]:
    """Return a JSON-ready co-designer suggestion payload."""

    return {
        "summary": suggestion.summary,
        "selected_candidate": suggestion.selected_candidate,
        "audition_notes": list(suggestion.audition_notes),
        "parameter_edits": [
            {
                "parameter": edit.parameter,
                "direction": edit.direction,
                "reason": edit.reason,
            }
            for edit in suggestion.parameter_edits
        ],
        "safety_notes": list(suggestion.safety_notes),
        "staged_only": suggestion.staged_only,
    }


def _validate_parameter_edit(
    payload: dict[str, object],
    *,
    valid_parameters: set[str],
) -> PatchParameterEdit:
    parameter = require_string(payload.get("parameter"), label="parameter")
    if parameter not in valid_parameters:
        raise LocalAiValidationError(f"parameter {parameter!r} is not in the patch genome")
    return PatchParameterEdit(
        parameter=parameter,
        direction=require_string(payload.get("direction"), label="direction"),
        reason=require_string(payload.get("reason"), label="reason"),
    )


def _codesigner_prompt(
    description: str,
    genome: AnalogFourPatchGenome,
    candidate: AnalogFourPatchCandidate,
) -> str:
    lines = [
        f"Reference description: {description}",
        f"Selected track: {genome.selected_track}",
        f"Selected candidate: {candidate.column} / {candidate.label}",
        "Patch DNA:",
    ]
    for gene in candidate.genes:
        value = gene.value
        lines.append(
            f"- {value.parameter}: screen {value.screen_value}; "
            f"transport {value.transport_status}; rationale {gene.rationale}"
        )
    lines.append("Return staged co-design JSON matching the schema.")
    return "\n".join(lines)


__all__ = [
    "ANALOG_FOUR_PATCH_CODESIGNER_READINESS_REASON",
    "ANALOG_FOUR_PATCH_CODESIGNER_SAFETY",
    "ANALOG_FOUR_PATCH_CODESIGNER_VERSION",
    "AnalogFourPatchCodesignerPacket",
    "PatchCodesignerSuggestion",
    "PatchParameterEdit",
    "analog_four_patch_codesigner_packet_to_dict",
    "analog_four_patch_codesigner_schema",
    "build_analog_four_patch_codesigner_packet",
    "patch_codesigner_suggestion_to_dict",
    "validate_patch_codesigner_payload",
]
