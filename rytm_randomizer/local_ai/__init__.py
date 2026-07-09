"""Import-safe local AI helpers for passive operator copilot workflows."""

from __future__ import annotations

from .provider import (
    LocalAiChatRequest,
    LocalAiEmbeddingResponse,
    LocalAiError,
    LocalAiJsonResponse,
    LocalAiMessage,
    LocalAiProvider,
    LocalAiUnavailableError,
    LocalAiValidationError,
    local_ai_message_to_dict,
    parse_json_object,
)

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
]
