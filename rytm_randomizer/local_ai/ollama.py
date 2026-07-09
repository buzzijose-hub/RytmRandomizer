"""Ollama HTTP adapter for optional local structured-output calls."""

from __future__ import annotations

import http.client
import json
import os
import urllib.parse
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Final

from .provider import (
    LocalAiChatRequest,
    LocalAiEmbeddingResponse,
    LocalAiJsonResponse,
    LocalAiUnavailableError,
    LocalAiValidationError,
    local_ai_message_to_dict,
    parse_json_object,
    require_mapping,
    require_string,
)

DEFAULT_OLLAMA_HOST: Final[str] = "http://localhost:11434"
OLLAMA_HOST_ENV: Final[str] = "OLLAMA_HOST"
DEFAULT_TIMEOUT_SECONDS: Final[float] = 3.0

_Transport = Callable[[str, dict[str, object]], dict[str, object]]
_ALLOWED_HOST_SCHEMES: Final[tuple[str, ...]] = ("http", "https")


@dataclass(frozen=True)
class OllamaProvider:
    """Small stdlib-only adapter for Ollama's local HTTP API."""

    host: str = DEFAULT_OLLAMA_HOST
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS
    transport: _Transport | None = None

    @classmethod
    def from_env(cls) -> OllamaProvider:
        """Build a provider using ``OLLAMA_HOST`` when present."""

        return cls(host=os.environ.get(OLLAMA_HOST_ENV, DEFAULT_OLLAMA_HOST))

    def chat_json(self, request: LocalAiChatRequest) -> LocalAiJsonResponse:
        """Call ``/api/chat`` and parse the assistant message as JSON."""

        payload = {
            "model": request.model,
            "messages": [local_ai_message_to_dict(message) for message in request.messages],
            "stream": False,
            "format": dict(request.schema),
            "options": {"temperature": request.temperature},
        }
        raw = self._post_json("/api/chat", payload)
        message = require_mapping(raw.get("message"), label="message")
        content = require_string(message.get("content"), label="message.content")
        data = parse_json_object(content)
        model = require_string(raw.get("model", request.model), label="model")
        return LocalAiJsonResponse(
            workflow=request.workflow,
            model=model,
            data=data,
            raw_content=content,
            done_reason=str(raw.get("done_reason", "")),
            prompt_eval_count=_coerce_non_negative_int(raw.get("prompt_eval_count")),
            eval_count=_coerce_non_negative_int(raw.get("eval_count")),
        )

    def embed(self, *, model: str, inputs: Sequence[str]) -> LocalAiEmbeddingResponse:
        """Call ``/api/embed`` for one or more strings."""

        payload = {
            "model": model,
            "input": list(inputs),
        }
        raw = self._post_json("/api/embed", payload)
        embeddings = raw.get("embeddings")
        if not isinstance(embeddings, list):
            raise LocalAiValidationError("embeddings must be a list")
        rows: list[tuple[float, ...]] = []
        for row in embeddings:
            if not isinstance(row, list):
                raise LocalAiValidationError("embedding row must be a list")
            values: list[float] = []
            for value in row:
                if not isinstance(value, (int, float)) or isinstance(value, bool):
                    raise LocalAiValidationError("embedding value must be numeric")
                values.append(float(value))
            rows.append(tuple(values))
        return LocalAiEmbeddingResponse(model=model, embeddings=tuple(rows))

    def _post_json(self, endpoint: str, payload: dict[str, object]) -> dict[str, object]:
        transport = self.transport
        try:
            if transport is not None:
                return require_mapping(transport(endpoint, payload), label="ollama response")
            return self._http_post_json(endpoint, payload)
        except OSError as exc:
            raise LocalAiUnavailableError(str(exc)) from exc

    def _http_post_json(self, endpoint: str, payload: dict[str, object]) -> dict[str, object]:
        parsed_host = _parse_host(self.host)
        endpoint_path = endpoint if endpoint.startswith("/") else f"/{endpoint}"
        path = parsed_host.path.rstrip("/") + endpoint_path
        body = json.dumps(payload).encode("utf-8")
        connection_class = (
            http.client.HTTPSConnection
            if parsed_host.scheme == "https"
            else http.client.HTTPConnection
        )
        connection = connection_class(parsed_host.netloc, timeout=self.timeout_seconds)
        try:
            connection.request(
                "POST",
                path,
                body=body,
                headers={"Content-Type": "application/json"},
            )
            response = connection.getresponse()
            raw_body = response.read().decode("utf-8")
            if response.status >= 400:
                raise LocalAiUnavailableError(f"{response.status} {response.reason}")
        except http.client.HTTPException as exc:
            raise LocalAiUnavailableError(str(exc)) from exc
        finally:
            connection.close()
        try:
            parsed = json.loads(raw_body)
        except json.JSONDecodeError as exc:
            raise LocalAiValidationError("ollama response must be JSON") from exc
        return require_mapping(parsed, label="ollama response")


def _coerce_non_negative_int(value: object) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        return 0
    return max(0, value)


def _parse_host(host: str) -> urllib.parse.SplitResult:
    normalized_host = host if "://" in host else f"http://{host}"
    parsed_host = urllib.parse.urlsplit(normalized_host)
    if (
        parsed_host.scheme not in _ALLOWED_HOST_SCHEMES
        or not parsed_host.netloc
        or parsed_host.query
        or parsed_host.fragment
    ):
        raise LocalAiValidationError("ollama host must be an http or https URL")
    return parsed_host


__all__ = [
    "DEFAULT_OLLAMA_HOST",
    "DEFAULT_TIMEOUT_SECONDS",
    "OLLAMA_HOST_ENV",
    "OllamaProvider",
]
