"""Passive Ollama local-copilot report."""

from __future__ import annotations

import json
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Final

from ..cli_registry import CliCommand, register
from ..local_ai import LocalAiChatRequest, LocalAiProvider
from ..local_ai.mutation_intent import (
    MutationIntentPacket,
    build_mutation_intent_packet,
    mutation_intent_packet_to_dict,
    staged_mutation_intent_to_dict,
    validate_mutation_intent_payload,
)
from ..local_ai.ollama import OllamaProvider
from ..local_ai.provider import LocalAiError, LocalAiMessage, LocalAiUnavailableError
from ..local_ai.rag import (
    DocsAssistantPacket,
    build_docs_assistant_packet,
    docs_assistant_answer_to_dict,
    docs_assistant_packet_to_dict,
    validate_docs_answer_payload,
)
from ..style_analysis import extract_from_description
from ..style_analysis.analog_four_patch_codesigner import (
    AnalogFourPatchCodesignerPacket,
    analog_four_patch_codesigner_packet_to_dict,
    build_analog_four_patch_codesigner_packet,
    patch_codesigner_suggestion_to_dict,
    validate_patch_codesigner_payload,
)
from .formatter import SAFETY_SECTION_HEADER, PassiveReportHeader, passive_report_lines

REPORT_TITLE: Final[str] = "RytmRandomizer passive Ollama local copilot"
SOURCE_MODULE: Final[str] = "reports.ollama_local_copilot"
OLLAMA_LOCAL_COPILOT_VERSION: Final[str] = "ollama-local-copilot-report-v1"
DEFAULT_OLLAMA_MODEL: Final[str] = "llama3.2"
VALID_WORKFLOWS: Final[tuple[str, ...]] = ("docs", "mutation", "patch", "all")
SAFETY_LINES: Final[tuple[str, ...]] = (
    "passive local-AI copilot",
    "no MIDI sent",
    "no MIDI ports opened",
    "no hardware mutation",
    "no SysEx written",
    "Ollama calls are local and explicit",
)
USAGE: Final[str] = (
    "Usage: python -m rytm_randomizer.cli ollama-local-copilot-report "
    "--question <text> [--description <text>] [--workflow docs|mutation|patch|all] "
    "[--model <name>] [--ask-ollama] [--json]"
)
_HEADER: Final[PassiveReportHeader] = PassiveReportHeader(
    title=REPORT_TITLE,
    source_module=SOURCE_MODULE,
)


@dataclass(frozen=True)
class OllamaWorkflowResult:
    """Result for one optional local-model workflow."""

    workflow: str
    status: str
    model: str
    data: dict[str, object] | None
    error: str | None
    prompt_eval_count: int
    eval_count: int


@dataclass(frozen=True)
class OllamaLocalCopilotReport:
    """Operator-facing bundled local-copilot report."""

    version: str
    question: str
    description: str
    workflow: str
    model: str
    ask_ollama: bool
    docs_packet: DocsAssistantPacket | None
    mutation_packet: MutationIntentPacket | None
    patch_packet: AnalogFourPatchCodesignerPacket | None
    ollama_results: tuple[OllamaWorkflowResult, ...]
    safety: tuple[str, ...]


def build_ollama_local_copilot_report(
    *,
    question: str,
    description: str | None = None,
    workflow: str = "all",
    model: str = DEFAULT_OLLAMA_MODEL,
    ask_ollama: bool = False,
    provider: LocalAiProvider | None = None,
) -> OllamaLocalCopilotReport:
    """Build the bundled passive local-copilot report."""

    normalized_workflow = _normalize_workflow(workflow)
    normalized_question = _require_non_empty(question, "--question")
    normalized_description = _require_non_empty(description or question, "--description")
    normalized_model = _require_non_empty(model, "--model")
    docs_packet = (
        build_docs_assistant_packet(normalized_question)
        if normalized_workflow in ("docs", "all")
        else None
    )
    mutation_packet = (
        build_mutation_intent_packet(normalized_question)
        if normalized_workflow in ("mutation", "all")
        else None
    )
    patch_packet = (
        build_analog_four_patch_codesigner_packet(
            extract_from_description(normalized_description),
            description=normalized_description,
            track=1,
            selected_candidate=1,
        )
        if normalized_workflow in ("patch", "all")
        else None
    )
    results = (
        _call_ollama_packets(
            model=normalized_model,
            provider=provider or OllamaProvider.from_env(),
            docs_packet=docs_packet,
            mutation_packet=mutation_packet,
            patch_packet=patch_packet,
        )
        if ask_ollama
        else tuple(
            _skipped_result(workflow_name, model=normalized_model)
            for workflow_name in _requested_workflows(normalized_workflow)
        )
    )
    return OllamaLocalCopilotReport(
        version=OLLAMA_LOCAL_COPILOT_VERSION,
        question=normalized_question,
        description=normalized_description,
        workflow=normalized_workflow,
        model=normalized_model,
        ask_ollama=ask_ollama,
        docs_packet=docs_packet,
        mutation_packet=mutation_packet,
        patch_packet=patch_packet,
        ollama_results=results,
        safety=SAFETY_LINES,
    )


def build_ollama_local_copilot_payload(
    report: OllamaLocalCopilotReport,
) -> dict[str, object]:
    """Return a deterministic machine-readable local-copilot payload."""

    return {
        "version": report.version,
        "question": report.question,
        "description": report.description,
        "workflow": report.workflow,
        "model": report.model,
        "ollama": {
            "called": report.ask_ollama,
            "results": [_ollama_result_to_dict(result) for result in report.ollama_results],
        },
        "docs_packet": (
            docs_assistant_packet_to_dict(report.docs_packet)
            if report.docs_packet is not None
            else None
        ),
        "mutation_packet": (
            mutation_intent_packet_to_dict(report.mutation_packet)
            if report.mutation_packet is not None
            else None
        ),
        "patch_packet": (
            analog_four_patch_codesigner_packet_to_dict(report.patch_packet)
            if report.patch_packet is not None
            else None
        ),
        "safety": list(report.safety),
    }


def format_ollama_local_copilot_report(report: OllamaLocalCopilotReport) -> list[str]:
    """Return deterministic operator-facing report lines."""

    lines = [
        "Summary:",
        f"- Workflow: {report.workflow}",
        f"- Model: {report.model}",
        f"- Ollama call: {'requested' if report.ask_ollama else 'skipped'}",
        f"- Question: {report.question}",
    ]
    if report.docs_packet is not None:
        lines.extend(_docs_lines(report.docs_packet))
    if report.mutation_packet is not None:
        lines.extend(_mutation_lines(report.mutation_packet))
    if report.patch_packet is not None:
        lines.extend(_patch_lines(report.patch_packet))
    lines.append("Ollama results:")
    lines.extend(_ollama_result_line(result) for result in report.ollama_results)
    lines.append(SAFETY_SECTION_HEADER)
    lines.extend(f"- {line}" for line in report.safety)
    return passive_report_lines(_HEADER, lines)


def _call_ollama_packets(
    *,
    model: str,
    provider: LocalAiProvider,
    docs_packet: DocsAssistantPacket | None,
    mutation_packet: MutationIntentPacket | None,
    patch_packet: AnalogFourPatchCodesignerPacket | None,
) -> tuple[OllamaWorkflowResult, ...]:
    results: list[OllamaWorkflowResult] = []
    if docs_packet is not None:
        results.append(
            _call_one_workflow(
                workflow="docs",
                model=model,
                provider=provider,
                messages=docs_packet.messages,
                schema=docs_packet.schema,
                validator=lambda response: docs_assistant_answer_to_dict(
                    validate_docs_answer_payload(response.data)
                ),
            )
        )
    if mutation_packet is not None:
        results.append(
            _call_one_workflow(
                workflow="mutation",
                model=model,
                provider=provider,
                messages=mutation_packet.messages,
                schema=mutation_packet.schema,
                validator=lambda response: staged_mutation_intent_to_dict(
                    validate_mutation_intent_payload(response.data)
                ),
            )
        )
    if patch_packet is not None:
        results.append(
            _call_one_workflow(
                workflow="patch",
                model=model,
                provider=provider,
                messages=patch_packet.messages,
                schema=patch_packet.schema,
                validator=lambda response: patch_codesigner_suggestion_to_dict(
                    validate_patch_codesigner_payload(
                        response.data,
                        genome=patch_packet.genome,
                    )
                ),
            )
        )
    return tuple(results)


def _call_one_workflow(
    *,
    workflow: str,
    model: str,
    provider: LocalAiProvider,
    messages: tuple[LocalAiMessage, ...],
    schema: dict[str, object],
    validator,
) -> OllamaWorkflowResult:
    try:
        response = provider.chat_json(
            LocalAiChatRequest(
                workflow=workflow,
                model=model,
                messages=messages,
                schema=schema,
                temperature=0.0,
            )
        )
        validated = validator(response)
    except LocalAiError as exc:
        return OllamaWorkflowResult(
            workflow=workflow,
            status="unavailable" if isinstance(exc, LocalAiUnavailableError) else "invalid",
            model=model,
            data=None,
            error=str(exc),
            prompt_eval_count=0,
            eval_count=0,
        )
    return OllamaWorkflowResult(
        workflow=workflow,
        status="validated",
        model=response.model,
        data=validated,
        error=None,
        prompt_eval_count=response.prompt_eval_count,
        eval_count=response.eval_count,
    )


def _skipped_result(workflow: str, *, model: str) -> OllamaWorkflowResult:
    return OllamaWorkflowResult(
        workflow=workflow,
        status="skipped",
        model=model,
        data=None,
        error=None,
        prompt_eval_count=0,
        eval_count=0,
    )


def _requested_workflows(workflow: str) -> tuple[str, ...]:
    if workflow == "all":
        return ("docs", "mutation", "patch")
    return (workflow,)


def _docs_lines(packet: DocsAssistantPacket) -> list[str]:
    return [
        "Docs/MIDI assistant:",
        f"- Source chunk count: {len(packet.chunks)}",
        f"- Top source: {packet.chunks[0].source_id}",
        f"- Prompt messages: {len(packet.messages)}",
    ]


def _mutation_lines(packet: MutationIntentPacket) -> list[str]:
    return [
        "Mutation intent:",
        f"- Intent label: {packet.intent.intent_label}",
        f"- Target device: {packet.intent.target_device}",
        f"- Mutation depth: {packet.intent.mutation_depth}",
        f"- Parameter focus: {', '.join(packet.intent.parameter_focus)}",
        f"- Staged only: {packet.intent.staged_only}",
    ]


def _patch_lines(packet: AnalogFourPatchCodesignerPacket) -> list[str]:
    return [
        "Analog Four patch co-designer:",
        f"- Selected candidate: {packet.selected_candidate} / {packet.reference_candidate.label}",
        f"- Selected track: {packet.genome.selected_track}",
        f"- Ready for send: {packet.ready_for_send}",
        f"- Readiness reason: {packet.readiness_reason}",
    ]


def _ollama_result_line(result: OllamaWorkflowResult) -> str:
    suffix = f" ({result.error})" if result.error else ""
    return f"- {result.workflow}: {result.status}{suffix}"


def _ollama_result_to_dict(result: OllamaWorkflowResult) -> dict[str, object]:
    return {
        "workflow": result.workflow,
        "status": result.status,
        "model": result.model,
        "data": result.data,
        "error": result.error,
        "prompt_eval_count": result.prompt_eval_count,
        "eval_count": result.eval_count,
    }


def _normalize_workflow(workflow: str) -> str:
    normalized = workflow.strip().lower()
    if normalized not in VALID_WORKFLOWS:
        raise ValueError(f"workflow must be one of {', '.join(VALID_WORKFLOWS)}")
    return normalized


def _require_non_empty(value: str, option: str) -> str:
    normalized = str(value).strip()
    if not normalized:
        raise ValueError(f"{option} requires a non-empty value")
    return normalized


def _parse_ollama_local_copilot_args(argv: Sequence[str]) -> dict[str, object]:
    question = ""
    description: str | None = None
    workflow = "all"
    model = DEFAULT_OLLAMA_MODEL
    ask_ollama = False
    json_output = False
    index = 0
    while index < len(argv):
        option = argv[index]
        if option == "--json":
            json_output = True
            index += 1
            continue
        if option == "--ask-ollama":
            ask_ollama = True
            index += 1
            continue
        if option in ("--question", "--description", "--workflow", "--model"):
            if index + 1 >= len(argv):
                raise ValueError(f"{option} requires a value")
            value = argv[index + 1]
            if option == "--question":
                question = value
            elif option == "--description":
                description = value
            elif option == "--workflow":
                workflow = _normalize_workflow(value)
            else:
                model = _require_non_empty(value, option)
            index += 2
            continue
        raise ValueError(f"unknown argument: {option}")
    if not question.strip():
        raise ValueError("--question requires a value")
    return {
        "question": question,
        "description": description,
        "workflow": workflow,
        "model": model,
        "ask_ollama": ask_ollama,
        "json_output": json_output,
    }


def _format_ollama_local_copilot_error(exc: Exception) -> str:
    return f"{USAGE}\nError: {exc}"


def _handle_ollama_local_copilot_report(
    *,
    question: str,
    description: str | None,
    workflow: str,
    model: str,
    ask_ollama: bool,
    json_output: bool = False,
) -> int:
    try:
        report = build_ollama_local_copilot_report(
            question=question,
            description=description,
            workflow=workflow,
            model=model,
            ask_ollama=ask_ollama,
        )
    except (ValueError, TypeError) as exc:
        sys.stderr.write(f"{_format_ollama_local_copilot_error(exc)}\n")
        return 2

    if json_output:
        sys.stdout.write(
            json.dumps(
                build_ollama_local_copilot_payload(report),
                indent=2,
                sort_keys=True,
            )
        )
        sys.stdout.write("\n")
        return 0

    sys.stdout.write("\n".join(format_ollama_local_copilot_report(report)))
    sys.stdout.write("\n")
    return 0


OLLAMA_LOCAL_COPILOT_CLI_COMMAND: Final[CliCommand] = CliCommand(
    name="ollama-local-copilot-report",
    summary="Build passive local Ollama copilot packets for docs, mutation, and A4 patch DNA.",
    args_parser=_parse_ollama_local_copilot_args,
    handler=_handle_ollama_local_copilot_report,
    error_formatter=_format_ollama_local_copilot_error,
)

register(OLLAMA_LOCAL_COPILOT_CLI_COMMAND)

__all__ = [
    "DEFAULT_OLLAMA_MODEL",
    "OLLAMA_LOCAL_COPILOT_CLI_COMMAND",
    "OLLAMA_LOCAL_COPILOT_VERSION",
    "OllamaLocalCopilotReport",
    "OllamaWorkflowResult",
    "REPORT_TITLE",
    "SAFETY_LINES",
    "SOURCE_MODULE",
    "USAGE",
    "VALID_WORKFLOWS",
    "build_ollama_local_copilot_payload",
    "build_ollama_local_copilot_report",
    "format_ollama_local_copilot_report",
]
