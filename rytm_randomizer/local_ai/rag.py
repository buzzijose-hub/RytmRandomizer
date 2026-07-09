"""Deterministic docs/MIDI prompt packets for local AI assistants."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Final

from .provider import (
    LocalAiMessage,
    local_ai_message_to_dict,
    require_string,
    require_string_list,
)

DOCS_ASSISTANT_VERSION: Final[str] = "local-ai-docs-assistant-v1"
DOCS_ASSISTANT_SAFETY: Final[tuple[str, ...]] = (
    "passive docs/MIDI assistant",
    "no MIDI sent",
    "no MIDI ports opened",
    "no files written",
    "answers must cite provided source ids",
)

_DOCS_ASSISTANT_REQUIRED: Final[list[str]] = [
    "answer",
    "cited_sources",
    "safety_notes",
    "follow_up_actions",
]


@dataclass(frozen=True)
class SourceChunk:
    """One small source chunk included in a local RAG packet."""

    source_id: str
    title: str
    body: str
    keywords: tuple[str, ...]
    score: int = 0


@dataclass(frozen=True)
class DocsAssistantPacket:
    """Prompt packet for local docs/MIDI assistance."""

    version: str
    question: str
    chunks: tuple[SourceChunk, ...]
    messages: tuple[LocalAiMessage, ...]
    schema: dict[str, object]
    safety: tuple[str, ...]


@dataclass(frozen=True)
class DocsAssistantAnswer:
    """Validated model answer for docs/MIDI assistance."""

    answer: str
    cited_sources: tuple[str, ...]
    safety_notes: tuple[str, ...]
    follow_up_actions: tuple[str, ...]


_SOURCE_CHUNKS: Final[tuple[SourceChunk, ...]] = (
    SourceChunk(
        source_id="analog-four-midi-catalog",
        title="Analog Four MIDI catalog",
        body=(
            "Manual-backed Analog Four CC/NRPN rows live in "
            "rytm_randomizer.data.analog_four_midi and are surfaced through "
            "passive Analog Four reports before any live dial plan."
        ),
        keywords=("analog", "four", "a4", "midi", "cc", "nrpn", "filter", "catalog"),
    ),
    SourceChunk(
        source_id="patch-genome",
        title="Analog Four patch genome",
        body=(
            "The patch genome compiler turns FeatureReport data into four "
            "front-panel Analog Four single-sound candidates and stops at "
            "review metadata."
        ),
        keywords=("analog", "four", "patch", "genome", "dna", "candidate", "sound"),
    ),
    SourceChunk(
        source_id="passive-default",
        title="Passive default",
        body=(
            "The passive CLI must not open MIDI devices or send MIDI. Armed "
            "hardware paths live outside the report-only command surface."
        ),
        keywords=("passive", "safe", "safety", "midi", "send", "hardware", "armed"),
    ),
    SourceChunk(
        source_id="mutation-guardrails",
        title="Mutation guardrails",
        body=(
            "Mutation suggestions remain staged until deterministic code maps "
            "them to bounded parameter changes and an operator explicitly arms "
            "a hardware path."
        ),
        keywords=("mutation", "guardrails", "random", "staged", "depth", "bounded"),
    ),
)


def build_docs_assistant_packet(question: str, *, max_chunks: int = 3) -> DocsAssistantPacket:
    """Build a deterministic local RAG packet for ``question``."""

    normalized_question = require_string(question, label="question")
    ranked = _rank_chunks(normalized_question)[:max_chunks]
    messages = (
        LocalAiMessage(
            role="system",
            content=(
                "You are a passive RytmRandomizer docs/MIDI assistant. "
                "Answer only from the provided source chunks, cite source ids, "
                "and never suggest sending MIDI or opening hardware devices."
            ),
        ),
        LocalAiMessage(
            role="user",
            content=_context_prompt(normalized_question, ranked),
        ),
    )
    return DocsAssistantPacket(
        version=DOCS_ASSISTANT_VERSION,
        question=normalized_question,
        chunks=ranked,
        messages=messages,
        schema=docs_assistant_schema(),
        safety=DOCS_ASSISTANT_SAFETY,
    )


def docs_assistant_schema() -> dict[str, object]:
    """Return the JSON schema expected from the local docs assistant."""

    return {
        "type": "object",
        "properties": {
            "answer": {"type": "string"},
            "cited_sources": {"type": "array", "items": {"type": "string"}},
            "safety_notes": {"type": "array", "items": {"type": "string"}},
            "follow_up_actions": {"type": "array", "items": {"type": "string"}},
        },
        "required": list(_DOCS_ASSISTANT_REQUIRED),
    }


def docs_assistant_packet_to_dict(packet: DocsAssistantPacket) -> dict[str, object]:
    """Return a JSON-ready packet payload."""

    return {
        "version": packet.version,
        "question": packet.question,
        "chunks": [_source_chunk_to_dict(chunk) for chunk in packet.chunks],
        "messages": [local_ai_message_to_dict(message) for message in packet.messages],
        "schema": packet.schema,
        "safety": list(packet.safety),
    }


def validate_docs_answer_payload(payload: dict[str, object]) -> DocsAssistantAnswer:
    """Validate a docs assistant model payload."""

    return DocsAssistantAnswer(
        answer=require_string(payload.get("answer"), label="answer"),
        cited_sources=require_string_list(payload.get("cited_sources"), label="cited_sources"),
        safety_notes=require_string_list(payload.get("safety_notes"), label="safety_notes"),
        follow_up_actions=require_string_list(
            payload.get("follow_up_actions"),
            label="follow_up_actions",
        ),
    )


def docs_assistant_answer_to_dict(answer: DocsAssistantAnswer) -> dict[str, object]:
    """Return a JSON-ready validated answer payload."""

    return {
        "answer": answer.answer,
        "cited_sources": list(answer.cited_sources),
        "safety_notes": list(answer.safety_notes),
        "follow_up_actions": list(answer.follow_up_actions),
    }


def _rank_chunks(question: str) -> tuple[SourceChunk, ...]:
    terms = set(_tokens(question))
    ranked = tuple(
        sorted(
            (
                SourceChunk(
                    source_id=chunk.source_id,
                    title=chunk.title,
                    body=chunk.body,
                    keywords=chunk.keywords,
                    score=_score_chunk(chunk, terms),
                )
                for chunk in _SOURCE_CHUNKS
            ),
            key=lambda chunk: (-chunk.score, chunk.source_id),
        )
    )
    return ranked


def _score_chunk(chunk: SourceChunk, terms: set[str]) -> int:
    keyword_score = sum(3 for keyword in chunk.keywords if keyword in terms)
    title_terms = set(_tokens(chunk.title))
    body_terms = set(_tokens(chunk.body))
    return (
        keyword_score
        + sum(2 for term in terms if term in title_terms)
        + sum(1 for term in terms if term in body_terms)
    )


def _tokens(text: str) -> tuple[str, ...]:
    return tuple(re.findall(r"[a-z0-9]+", text.lower()))


def _context_prompt(question: str, chunks: tuple[SourceChunk, ...]) -> str:
    lines = [
        f"Question: {question}",
        "Source chunks:",
    ]
    for chunk in chunks:
        lines.append(f"[{chunk.source_id}] {chunk.title}: {chunk.body}")
    lines.append("Return only JSON matching the schema.")
    return "\n".join(lines)


def _source_chunk_to_dict(chunk: SourceChunk) -> dict[str, object]:
    return {
        "source_id": chunk.source_id,
        "title": chunk.title,
        "body": chunk.body,
        "keywords": list(chunk.keywords),
        "score": chunk.score,
    }


__all__ = [
    "DOCS_ASSISTANT_SAFETY",
    "DOCS_ASSISTANT_VERSION",
    "DocsAssistantAnswer",
    "DocsAssistantPacket",
    "SourceChunk",
    "build_docs_assistant_packet",
    "docs_assistant_answer_to_dict",
    "docs_assistant_packet_to_dict",
    "docs_assistant_schema",
    "validate_docs_answer_payload",
]
