"""Local executable adapter for optional structured-output model calls."""

from __future__ import annotations

import os
import shlex
import subprocess
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Final

from .provider import (
    LocalAiChatRequest,
    LocalAiJsonResponse,
    LocalAiUnavailableError,
    LocalAiValidationError,
    parse_json_object,
)

LOCAL_MODEL_COMMAND_ENV: Final[str] = "LOCAL_MODEL_COMMAND"
DEFAULT_LOCAL_MODEL: Final[str] = "local-model"
DEFAULT_TIMEOUT_SECONDS: Final[float] = 30.0


@dataclass(frozen=True)
class LocalModelProcessResult:
    """Captured result from a local model executable."""

    stdout: str
    stderr: str
    returncode: int


_Runner = Callable[[Sequence[str], str, float], LocalModelProcessResult]


@dataclass(frozen=True)
class LocalModelCommandProvider:
    """Run a configured local model executable and parse JSON stdout."""

    command_template: str | None = None
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS
    runner: _Runner | None = None

    @classmethod
    def from_env(cls) -> LocalModelCommandProvider:
        """Build a provider from ``LOCAL_MODEL_COMMAND`` when configured."""

        command = os.environ.get(LOCAL_MODEL_COMMAND_ENV)
        return cls(command_template=command.strip() if command else None)

    def chat_json(self, request: LocalAiChatRequest) -> LocalAiJsonResponse:
        """Run the local command for ``request`` and parse JSON stdout."""

        command_template = _require_command_template(self.command_template)
        prompt = build_local_model_prompt(request)
        args, stdin = _render_command(command_template, model=request.model, prompt=prompt)
        result = self._run(args, stdin)
        if result.returncode != 0:
            reason = result.stderr.strip() or f"exit code {result.returncode}"
            raise LocalAiUnavailableError(f"local model command failed: {reason}")
        content = result.stdout.strip()
        data = parse_json_object(content)
        return LocalAiJsonResponse(
            workflow=request.workflow,
            model=request.model,
            data=data,
            raw_content=content,
            done_reason="local-command",
            prompt_eval_count=0,
            eval_count=0,
        )

    def _run(self, args: Sequence[str], stdin: str) -> LocalModelProcessResult:
        runner = self.runner
        if runner is not None:
            return runner(tuple(args), stdin, self.timeout_seconds)
        try:
            completed = subprocess.run(  # noqa: S603 - explicit LOCAL_MODEL_COMMAND.
                list(args),
                input=stdin,
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            raise LocalAiUnavailableError("local model command timed out") from exc
        except OSError as exc:
            raise LocalAiUnavailableError(str(exc)) from exc
        return LocalModelProcessResult(
            stdout=completed.stdout,
            stderr=completed.stderr,
            returncode=completed.returncode,
        )


def build_local_model_prompt(request: LocalAiChatRequest) -> str:
    """Return a deterministic prompt for a local structured-output model."""

    messages = "\n".join(
        f"{message.role.upper()}: {message.content}" for message in request.messages
    )
    return "\n".join(
        (
            "Return exactly one JSON object for the requested workflow.",
            "Do not include markdown fences, commentary, or extra text.",
            f"Workflow: {request.workflow}",
            f"Temperature: {request.temperature:.2f}",
            "JSON schema:",
            _schema_to_json(request.schema),
            "Conversation:",
            messages,
        )
    )


def _schema_to_json(schema: object) -> str:
    import json

    return json.dumps(schema, sort_keys=True, separators=(",", ":"))


def _require_command_template(command_template: str | None) -> str:
    if command_template is None:
        raise LocalAiUnavailableError(f"{LOCAL_MODEL_COMMAND_ENV} is not configured")
    return command_template


def _render_command(
    command_template: str,
    *,
    model: str,
    prompt: str,
) -> tuple[tuple[str, ...], str]:
    tokens = shlex.split(command_template, posix=os.name != "nt")
    if not tokens:
        raise LocalAiValidationError(f"{LOCAL_MODEL_COMMAND_ENV} must not be empty")
    rendered: list[str] = []
    used_prompt_placeholder = False
    for token in tokens:
        if "{prompt}" in token:
            used_prompt_placeholder = True
        rendered.append(token.replace("{model}", model).replace("{prompt}", prompt))
    stdin = "" if used_prompt_placeholder else prompt
    return tuple(rendered), stdin


__all__ = [
    "DEFAULT_LOCAL_MODEL",
    "DEFAULT_TIMEOUT_SECONDS",
    "LOCAL_MODEL_COMMAND_ENV",
    "LocalModelCommandProvider",
    "LocalModelProcessResult",
    "build_local_model_prompt",
]
