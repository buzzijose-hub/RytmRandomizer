"""Provider boundary and validation helpers for local AI workflows."""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import ClassVar, Protocol

from ..observability.errors import BoundaryError


class LocalAiError(BoundaryError):
    """Base class for local AI provider failures."""

    fingerprint: ClassVar[str] = "local_ai.error.unspecified"


class LocalAiUnavailableError(LocalAiError):
    """Raised when a local provider cannot be reached."""

    fingerprint: ClassVar[str] = "local_ai.provider.unavailable"


class LocalAiValidationError(LocalAiError, ValueError):
    """Raised when local AI input or output fails validation."""

    fingerprint: ClassVar[str] = "local_ai.validation.failed"


@dataclass(frozen=True)
class LocalAiMessage:
    """One chat message passed to a local model provider."""

    role: str
    content: str


@dataclass(frozen=True)
class LocalAiChatRequest:
    """Structured-output chat request for a local model provider."""

    workflow: str
    model: str
    messages: tuple[LocalAiMessage, ...]
    schema: Mapping[str, object]
    temperature: float = 0.0


@dataclass(frozen=True)
class LocalAiJsonResponse:
    """Validated JSON-object response from a local model provider."""

    workflow: str
    model: str
    data: dict[str, object]
    raw_content: str
    done_reason: str
    prompt_eval_count: int
    eval_count: int


@dataclass(frozen=True)
class LocalAiEmbeddingResponse:
    """Embedding response from a local model provider."""

    model: str
    embeddings: tuple[tuple[float, ...], ...]


class LocalAiProvider(Protocol):
    """Protocol for optional local AI providers."""

    def chat_json(self, request: LocalAiChatRequest) -> LocalAiJsonResponse:
        """Return a validated JSON response for ``request``."""

    def embed(self, *, model: str, inputs: Sequence[str]) -> LocalAiEmbeddingResponse:
        """Return embeddings for ``inputs``."""


def local_ai_message_to_dict(message: LocalAiMessage) -> dict[str, str]:
    """Return Ollama/OpenAI-compatible message JSON."""

    return {
        "role": message.role,
        "content": message.content,
    }


def parse_json_object(raw_content: str) -> dict[str, object]:
    """Parse ``raw_content`` as a JSON object."""

    try:
        parsed = json.loads(raw_content)
    except json.JSONDecodeError as exc:
        raise LocalAiValidationError(f"model content is not valid JSON: {exc}") from exc
    if not isinstance(parsed, dict):
        raise LocalAiValidationError("model content must be a JSON object")
    return dict(parsed)


def require_mapping(value: object, *, label: str) -> dict[str, object]:
    """Return ``value`` as a plain mapping or raise a validation error."""

    if not isinstance(value, Mapping):
        raise LocalAiValidationError(f"{label} must be a JSON object")
    return dict(value)


def require_string(value: object, *, label: str, allow_empty: bool = False) -> str:
    """Return ``value`` as a string with optional non-empty validation."""

    if not isinstance(value, str):
        raise LocalAiValidationError(f"{label} must be a string")
    normalized = value.strip()
    if not allow_empty and not normalized:
        raise LocalAiValidationError(f"{label} must be a non-empty string")
    return normalized


def require_bool(value: object, *, label: str) -> bool:
    """Return ``value`` as a bool."""

    if not isinstance(value, bool):
        raise LocalAiValidationError(f"{label} must be a boolean")
    return value


def require_int_range(value: object, *, label: str, minimum: int, maximum: int) -> int:
    """Return ``value`` as an integer inside ``minimum..maximum``."""

    if not isinstance(value, int) or isinstance(value, bool):
        raise LocalAiValidationError(f"{label} must be an integer")
    if value < minimum or value > maximum:
        raise LocalAiValidationError(f"{label} must be in {minimum}..{maximum}")
    return value


def require_string_list(
    value: object,
    *,
    label: str,
    allow_empty: bool = False,
) -> tuple[str, ...]:
    """Return ``value`` as a tuple of non-empty strings."""

    if not isinstance(value, list):
        raise LocalAiValidationError(f"{label} must be a list")
    items = tuple(require_string(item, label=f"{label} item") for item in value)
    if not allow_empty and not items:
        raise LocalAiValidationError(f"{label} must contain at least one item")
    return items


def require_mapping_list(value: object, *, label: str) -> tuple[dict[str, object], ...]:
    """Return ``value`` as a tuple of plain mappings."""

    if not isinstance(value, list):
        raise LocalAiValidationError(f"{label} must be a list")
    return tuple(require_mapping(item, label=f"{label} item") for item in value)


__all__ = [
    "LocalAiChatRequest",
    "LocalAiEmbeddingResponse",
    "LocalAiError",
    "LocalAiJsonResponse",
    "LocalAiMessage",
    "LocalAiProvider",
    "LocalAiUnavailableError",
    "LocalAiValidationError",
    "local_ai_message_to_dict",
    "parse_json_object",
    "require_bool",
    "require_int_range",
    "require_mapping",
    "require_mapping_list",
    "require_string",
    "require_string_list",
]
