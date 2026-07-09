"""Tests for the import-safe local AI provider boundary."""

from __future__ import annotations

import json
import subprocess

import pytest

pytestmark = pytest.mark.fast


def _docs_request():
    from rytm_randomizer.local_ai import LocalAiChatRequest, LocalAiMessage

    return LocalAiChatRequest(
        workflow="docs",
        model="local-doc-model",
        messages=(LocalAiMessage(role="user", content="Which CC controls filter?"),),
        schema={
            "type": "object",
            "required": ["answer", "cited_sources", "safety_notes", "follow_up_actions"],
        },
        temperature=0.0,
    )


def test_local_model_provider_runs_configured_command_with_prompt_on_stdin() -> None:
    from rytm_randomizer.local_ai.local_model import (
        LocalModelCommandProvider,
        LocalModelProcessResult,
    )

    observed: list[tuple[tuple[str, ...], str, float]] = []

    def _runner(
        args: tuple[str, ...],
        stdin: str,
        timeout: float,
    ) -> LocalModelProcessResult:
        observed.append((args, stdin, timeout))
        return LocalModelProcessResult(
            stdout=json.dumps(
                {
                    "answer": "Use the passive catalog first.",
                    "cited_sources": ["analog-four-midi"],
                    "safety_notes": ["staged only"],
                    "follow_up_actions": ["open dry-run report"],
                }
            ),
            stderr="",
            returncode=0,
        )

    provider = LocalModelCommandProvider(
        command_template="local-model-runner --model {model}",
        timeout_seconds=4.5,
        runner=_runner,
    )

    response = provider.chat_json(_docs_request())

    assert len(observed) == 1
    args, stdin, timeout = observed[0]
    assert args == ("local-model-runner", "--model", "local-doc-model")
    assert "Return exactly one JSON object" in stdin
    assert '"required":["answer","cited_sources","safety_notes","follow_up_actions"]' in stdin
    assert "USER: Which CC controls filter?" in stdin
    assert timeout == 4.5
    assert response.workflow == "docs"
    assert response.model == "local-doc-model"
    assert response.data["answer"] == "Use the passive catalog first."
    assert response.done_reason == "local-command"
    assert response.prompt_eval_count == 0
    assert response.eval_count == 0


def test_local_model_provider_supports_prompt_placeholder() -> None:
    from rytm_randomizer.local_ai.local_model import (
        LocalModelCommandProvider,
        LocalModelProcessResult,
    )

    observed: list[tuple[tuple[str, ...], str]] = []

    def _runner(
        args: tuple[str, ...],
        stdin: str,
        timeout: float,
    ) -> LocalModelProcessResult:
        observed.append((args, stdin))
        return LocalModelProcessResult(
            stdout=json.dumps(
                {
                    "answer": "Inline prompt accepted.",
                    "cited_sources": ["source"],
                    "safety_notes": ["safe"],
                    "follow_up_actions": ["review"],
                }
            ),
            stderr="",
            returncode=0,
        )

    provider = LocalModelCommandProvider(
        command_template="runner --prompt {prompt} --model {model}",
        runner=_runner,
    )

    response = provider.chat_json(_docs_request())

    args, stdin = observed[0]
    assert args[0:2] == ("runner", "--prompt")
    assert "Conversation:" in args[2]
    assert args[-2:] == ("--model", "local-doc-model")
    assert stdin == ""
    assert response.data["answer"] == "Inline prompt accepted."


def test_local_model_provider_from_env_uses_command(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from rytm_randomizer.local_ai.local_model import (
        LOCAL_MODEL_COMMAND_ENV,
        LocalModelCommandProvider,
    )

    monkeypatch.setenv(LOCAL_MODEL_COMMAND_ENV, "runner --model {model}")

    assert LocalModelCommandProvider.from_env().command_template == "runner --model {model}"


def test_local_model_provider_requires_command() -> None:
    from rytm_randomizer.local_ai.local_model import LocalModelCommandProvider
    from rytm_randomizer.local_ai.provider import LocalAiUnavailableError

    provider = LocalModelCommandProvider()

    with pytest.raises(LocalAiUnavailableError, match="LOCAL_MODEL_COMMAND"):
        provider.chat_json(_docs_request())


def test_local_model_provider_rejects_empty_command_tokens() -> None:
    from rytm_randomizer.local_ai.local_model import LocalModelCommandProvider
    from rytm_randomizer.local_ai.provider import LocalAiValidationError

    provider = LocalModelCommandProvider(command_template="   ")

    with pytest.raises(LocalAiValidationError, match="must not be empty"):
        provider.chat_json(_docs_request())


def test_local_model_provider_wraps_process_failure() -> None:
    from rytm_randomizer.local_ai.local_model import (
        LocalModelCommandProvider,
        LocalModelProcessResult,
    )
    from rytm_randomizer.local_ai.provider import LocalAiUnavailableError

    def _runner(
        args: tuple[str, ...],
        stdin: str,
        timeout: float,
    ) -> LocalModelProcessResult:
        return LocalModelProcessResult(stdout="", stderr="model failed", returncode=2)

    provider = LocalModelCommandProvider(command_template="runner", runner=_runner)

    with pytest.raises(LocalAiUnavailableError, match="model failed"):
        provider.chat_json(_docs_request())


def test_local_model_provider_rejects_non_json_stdout() -> None:
    from rytm_randomizer.local_ai.local_model import (
        LocalModelCommandProvider,
        LocalModelProcessResult,
    )
    from rytm_randomizer.local_ai.provider import LocalAiValidationError

    def _runner(
        args: tuple[str, ...],
        stdin: str,
        timeout: float,
    ) -> LocalModelProcessResult:
        return LocalModelProcessResult(stdout="not json", stderr="", returncode=0)

    provider = LocalModelCommandProvider(command_template="runner", runner=_runner)

    with pytest.raises(LocalAiValidationError, match="valid JSON"):
        provider.chat_json(_docs_request())


def test_local_model_provider_default_runner_invokes_subprocess(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from rytm_randomizer.local_ai.local_model import LocalModelCommandProvider

    class _Completed:
        stdout = json.dumps(
            {
                "answer": "Subprocess answer.",
                "cited_sources": ["source"],
                "safety_notes": ["safe"],
                "follow_up_actions": ["review"],
            }
        )
        stderr = ""
        returncode = 0

    observed: list[tuple[list[str], dict[str, object]]] = []

    def _run(args: list[str], **kwargs) -> _Completed:
        observed.append((args, kwargs))
        return _Completed()

    monkeypatch.setattr(subprocess, "run", _run)

    provider = LocalModelCommandProvider(command_template="runner", timeout_seconds=2.0)
    response = provider.chat_json(_docs_request())

    assert len(observed) == 1
    args, kwargs = observed[0]
    assert args == ["runner"]
    assert isinstance(kwargs["input"], str)
    assert kwargs["capture_output"] is True
    assert kwargs["text"] is True
    assert kwargs["timeout"] == 2.0
    assert kwargs["check"] is False
    assert response.data["answer"] == "Subprocess answer."


def test_local_model_provider_default_runner_wraps_timeout(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from rytm_randomizer.local_ai.local_model import LocalModelCommandProvider
    from rytm_randomizer.local_ai.provider import LocalAiUnavailableError

    def _run(args: list[str], **kwargs):
        raise subprocess.TimeoutExpired(cmd="runner", timeout=1.0)

    monkeypatch.setattr(subprocess, "run", _run)

    provider = LocalModelCommandProvider(command_template="runner", timeout_seconds=1.0)

    with pytest.raises(LocalAiUnavailableError, match="timed out"):
        provider.chat_json(_docs_request())


def test_local_model_provider_default_runner_wraps_os_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from rytm_randomizer.local_ai.local_model import LocalModelCommandProvider
    from rytm_randomizer.local_ai.provider import LocalAiUnavailableError

    def _run(args: list[str], **kwargs):
        raise OSError("missing executable")

    monkeypatch.setattr(subprocess, "run", _run)

    provider = LocalModelCommandProvider(command_template="runner")

    with pytest.raises(LocalAiUnavailableError, match="missing executable"):
        provider.chat_json(_docs_request())


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
    with pytest.raises(LocalAiValidationError, match="must be a JSON object"):
        parse_json_object("[]")
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
