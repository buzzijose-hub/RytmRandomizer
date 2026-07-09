"""Tests for the import-safe local AI provider boundary."""

from __future__ import annotations

import http.client
import json

import pytest

pytestmark = pytest.mark.fast


def test_ollama_provider_posts_chat_json_schema_with_stream_disabled() -> None:
    from rytm_randomizer.local_ai import LocalAiChatRequest, LocalAiMessage
    from rytm_randomizer.local_ai.ollama import OllamaProvider

    observed: list[tuple[str, dict[str, object]]] = []

    def _transport(endpoint: str, payload: dict[str, object]) -> dict[str, object]:
        observed.append((endpoint, payload))
        return {
            "model": "llama3.2",
            "message": {
                "role": "assistant",
                "content": json.dumps(
                    {
                        "answer": "Use the passive catalog first.",
                        "cited_sources": ["analog-four-midi"],
                        "safety_notes": ["staged only"],
                        "follow_up_actions": ["open dry-run report"],
                    }
                ),
            },
            "done_reason": "stop",
            "prompt_eval_count": 12,
            "eval_count": 7,
        }

    provider = OllamaProvider(host="http://ollama.test", transport=_transport)
    request = LocalAiChatRequest(
        workflow="docs",
        model="llama3.2",
        messages=(LocalAiMessage(role="user", content="Which CC controls filter?"),),
        schema={
            "type": "object",
            "required": ["answer", "cited_sources", "safety_notes", "follow_up_actions"],
        },
        temperature=0.0,
    )

    response = provider.chat_json(request)

    assert observed == [
        (
            "/api/chat",
            {
                "model": "llama3.2",
                "messages": [{"role": "user", "content": "Which CC controls filter?"}],
                "stream": False,
                "format": request.schema,
                "options": {"temperature": 0.0},
            },
        )
    ]
    assert response.workflow == "docs"
    assert response.model == "llama3.2"
    assert response.data["answer"] == "Use the passive catalog first."
    assert response.prompt_eval_count == 12
    assert response.eval_count == 7


def test_ollama_provider_posts_embedding_batches() -> None:
    from rytm_randomizer.local_ai.ollama import OllamaProvider

    observed: list[tuple[str, dict[str, object]]] = []

    def _transport(endpoint: str, payload: dict[str, object]) -> dict[str, object]:
        observed.append((endpoint, payload))
        return {"embeddings": [[1.0, 0.0], [0.0, 1.0]]}

    provider = OllamaProvider(host="http://ollama.test", transport=_transport)

    response = provider.embed(model="embeddinggemma", inputs=("Filter CC", "Patch DNA"))

    assert observed == [
        (
            "/api/embed",
            {
                "model": "embeddinggemma",
                "input": ["Filter CC", "Patch DNA"],
            },
        )
    ]
    assert response.model == "embeddinggemma"
    assert response.embeddings == ((1.0, 0.0), (0.0, 1.0))


def test_ollama_provider_from_env_uses_ollama_host(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from rytm_randomizer.local_ai.ollama import OLLAMA_HOST_ENV, OllamaProvider

    monkeypatch.setenv(OLLAMA_HOST_ENV, "https://ollama.local/api")

    assert OllamaProvider.from_env().host == "https://ollama.local/api"


def test_chat_json_rejects_non_object_model_content() -> None:
    from rytm_randomizer.local_ai import LocalAiChatRequest, LocalAiMessage
    from rytm_randomizer.local_ai.ollama import OllamaProvider
    from rytm_randomizer.local_ai.provider import LocalAiValidationError

    def _transport(endpoint: str, payload: dict[str, object]) -> dict[str, object]:
        return {
            "model": "llama3.2",
            "message": {"role": "assistant", "content": "[]"},
        }

    provider = OllamaProvider(host="http://ollama.test", transport=_transport)
    request = LocalAiChatRequest(
        workflow="docs",
        model="llama3.2",
        messages=(LocalAiMessage(role="user", content="hello"),),
        schema={"type": "object"},
    )

    with pytest.raises(LocalAiValidationError, match="JSON object"):
        provider.chat_json(request)


def test_chat_json_wraps_transport_failures_as_unavailable() -> None:
    from rytm_randomizer.local_ai import LocalAiChatRequest, LocalAiMessage
    from rytm_randomizer.local_ai.ollama import OllamaProvider
    from rytm_randomizer.local_ai.provider import LocalAiUnavailableError

    def _transport(endpoint: str, payload: dict[str, object]) -> dict[str, object]:
        raise OSError("connection refused")

    provider = OllamaProvider(host="http://ollama.test", transport=_transport)
    request = LocalAiChatRequest(
        workflow="docs",
        model="llama3.2",
        messages=(LocalAiMessage(role="user", content="hello"),),
        schema={"type": "object"},
    )

    with pytest.raises(LocalAiUnavailableError, match="connection refused"):
        provider.chat_json(request)


def test_ollama_provider_http_client_path_posts_json(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from rytm_randomizer.local_ai import LocalAiChatRequest, LocalAiMessage
    from rytm_randomizer.local_ai.ollama import OllamaProvider

    class _FakeResponse:
        status = 200
        reason = "OK"

        def read(self) -> bytes:
            return json.dumps(
                {
                    "model": "llama3.2",
                    "message": {
                        "content": json.dumps(
                            {
                                "answer": "Local answer",
                                "cited_sources": ["source"],
                                "safety_notes": ["safe"],
                                "follow_up_actions": ["review"],
                            }
                        )
                    },
                }
            ).encode("utf-8")

    class _FakeConnection:
        instances: list[_FakeConnection] = []

        def __init__(self, host: str, timeout: float) -> None:
            self.host = host
            self.timeout = timeout
            self.request_args: tuple[str, str, bytes, dict[str, str]] | None = None
            self.closed = False
            _FakeConnection.instances.append(self)

        def request(
            self,
            method: str,
            path: str,
            *,
            body: bytes,
            headers: dict[str, str],
        ) -> None:
            self.request_args = (method, path, body, headers)

        def getresponse(self) -> _FakeResponse:
            return _FakeResponse()

        def close(self) -> None:
            self.closed = True

    monkeypatch.setattr(http.client, "HTTPConnection", _FakeConnection)

    provider = OllamaProvider(host="localhost:11434", timeout_seconds=1.5)
    response = provider.chat_json(
        LocalAiChatRequest(
            workflow="docs",
            model="llama3.2",
            messages=(LocalAiMessage(role="user", content="hello"),),
            schema={"type": "object"},
        )
    )

    connection = _FakeConnection.instances[0]
    assert connection.host == "localhost:11434"
    assert connection.timeout == 1.5
    assert connection.closed is True
    assert connection.request_args is not None
    method, path, body, headers = connection.request_args
    assert method == "POST"
    assert path == "/api/chat"
    assert headers == {"Content-Type": "application/json"}
    assert json.loads(body)["stream"] is False
    assert response.data["answer"] == "Local answer"


@pytest.mark.parametrize(
    ("response_payload", "message"),
    [
        ({"embeddings": "not rows"}, "embeddings must be a list"),
        ({"embeddings": [{"bad": "row"}]}, "embedding row must be a list"),
        ({"embeddings": [[True]]}, "embedding value must be numeric"),
    ],
)
def test_ollama_provider_rejects_malformed_embedding_payloads(
    response_payload: dict[str, object],
    message: str,
) -> None:
    from rytm_randomizer.local_ai.ollama import OllamaProvider
    from rytm_randomizer.local_ai.provider import LocalAiValidationError

    def _transport(endpoint: str, payload: dict[str, object]) -> dict[str, object]:
        return response_payload

    provider = OllamaProvider(transport=_transport)

    with pytest.raises(LocalAiValidationError, match=message):
        provider.embed(model="embeddinggemma", inputs=("one",))


def test_ollama_provider_rejects_invalid_hosts() -> None:
    from rytm_randomizer.local_ai.ollama import OllamaProvider
    from rytm_randomizer.local_ai.provider import LocalAiValidationError

    provider = OllamaProvider(host="file:///tmp/ollama.sock")

    with pytest.raises(LocalAiValidationError, match="http or https"):
        provider.embed(model="embeddinggemma", inputs=("one",))


def test_ollama_provider_classifies_http_errors(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from rytm_randomizer.local_ai.ollama import OllamaProvider
    from rytm_randomizer.local_ai.provider import LocalAiUnavailableError

    class _FakeConnection:
        def __init__(self, host: str, timeout: float) -> None:
            pass

        def request(
            self,
            method: str,
            path: str,
            *,
            body: bytes,
            headers: dict[str, str],
        ) -> None:
            raise http.client.HTTPException("broken socket")

        def close(self) -> None:
            pass

    monkeypatch.setattr(http.client, "HTTPConnection", _FakeConnection)

    provider = OllamaProvider(host="http://localhost:11434")

    with pytest.raises(LocalAiUnavailableError, match="broken socket"):
        provider.embed(model="embeddinggemma", inputs=("one",))


def test_ollama_provider_classifies_http_status_errors(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from rytm_randomizer.local_ai.ollama import OllamaProvider
    from rytm_randomizer.local_ai.provider import LocalAiUnavailableError

    class _FakeResponse:
        status = 503
        reason = "Service Unavailable"

        def read(self) -> bytes:
            return b"{}"

    class _FakeConnection:
        def __init__(self, host: str, timeout: float) -> None:
            pass

        def request(
            self,
            method: str,
            path: str,
            *,
            body: bytes,
            headers: dict[str, str],
        ) -> None:
            pass

        def getresponse(self) -> _FakeResponse:
            return _FakeResponse()

        def close(self) -> None:
            pass

    monkeypatch.setattr(http.client, "HTTPConnection", _FakeConnection)

    provider = OllamaProvider(host="http://localhost:11434")

    with pytest.raises(LocalAiUnavailableError, match="503 Service Unavailable"):
        provider.embed(model="embeddinggemma", inputs=("one",))


def test_ollama_provider_rejects_non_json_http_response(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from rytm_randomizer.local_ai.ollama import OllamaProvider
    from rytm_randomizer.local_ai.provider import LocalAiValidationError

    class _FakeResponse:
        status = 200
        reason = "OK"

        def read(self) -> bytes:
            return b"{"

    class _FakeConnection:
        def __init__(self, host: str, timeout: float) -> None:
            pass

        def request(
            self,
            method: str,
            path: str,
            *,
            body: bytes,
            headers: dict[str, str],
        ) -> None:
            pass

        def getresponse(self) -> _FakeResponse:
            return _FakeResponse()

        def close(self) -> None:
            pass

    monkeypatch.setattr(http.client, "HTTPConnection", _FakeConnection)

    provider = OllamaProvider(host="http://localhost:11434")

    with pytest.raises(LocalAiValidationError, match="ollama response must be JSON"):
        provider.embed(model="embeddinggemma", inputs=("one",))


def test_provider_validation_helpers_cover_rejection_branches() -> None:
    from rytm_randomizer.local_ai.provider import (
        LocalAiValidationError,
        parse_json_object,
        require_bool,
        require_int_range,
        require_mapping,
        require_mapping_list,
        require_string,
        require_string_list,
    )

    assert require_string("", label="optional", allow_empty=True) == ""
    assert require_bool(True, label="flag") is True
    assert require_int_range(2, label="depth", minimum=1, maximum=4) == 2
    assert require_mapping({"ok": True}, label="object") == {"ok": True}
    assert require_mapping_list([{"ok": True}], label="rows") == ({"ok": True},)
    assert require_string_list(["x"], label="items") == ("x",)

    with pytest.raises(LocalAiValidationError, match="valid JSON"):
        parse_json_object("{")
    with pytest.raises(LocalAiValidationError, match="must be a string"):
        require_string(4, label="name")
    with pytest.raises(LocalAiValidationError, match="must be a non-empty string"):
        require_string("", label="name")
    with pytest.raises(LocalAiValidationError, match="must be a boolean"):
        require_bool("true", label="flag")
    with pytest.raises(LocalAiValidationError, match="must be an integer"):
        require_int_range(True, label="depth", minimum=1, maximum=4)
    with pytest.raises(LocalAiValidationError, match="must be in"):
        require_int_range(9, label="depth", minimum=1, maximum=4)
    with pytest.raises(LocalAiValidationError, match="must be a JSON object"):
        require_mapping([], label="object")
    with pytest.raises(LocalAiValidationError, match="must be a list"):
        require_mapping_list({}, label="rows")
    with pytest.raises(LocalAiValidationError, match="must be a list"):
        require_string_list({}, label="items")
    with pytest.raises(LocalAiValidationError, match="must contain"):
        require_string_list([], label="items")
