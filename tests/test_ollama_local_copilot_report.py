"""Tests for the passive Ollama local-copilot report."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from rytm_randomizer.local_ai.provider import (
    LocalAiChatRequest,
    LocalAiJsonResponse,
    LocalAiUnavailableError,
)

pytestmark = pytest.mark.fast

PROJECT_ROOT = Path(__file__).resolve().parents[1]


class _FakeProvider:
    def __init__(self) -> None:
        self.requests: list[LocalAiChatRequest] = []

    def chat_json(self, request: LocalAiChatRequest) -> LocalAiJsonResponse:
        self.requests.append(request)
        if request.workflow == "docs":
            data: dict[str, object] = {
                "answer": "Use the passive MIDI catalog first.",
                "cited_sources": ["analog-four-midi-catalog"],
                "safety_notes": ["staged only"],
                "follow_up_actions": ["inspect dry-run packet"],
            }
        elif request.workflow == "mutation":
            data = {
                "intent_label": "darker stable groove",
                "target_device": "analog_rytm_mk2",
                "mutation_depth": 2,
                "parameter_focus": ["filter_darkness"],
                "guardrails": ["keep kick stable"],
                "blocked_actions": ["open MIDI output", "send MIDI"],
                "safety_notes": ["operator review required"],
                "staged_only": True,
            }
        else:
            data = {
                "summary": "Keep the closest candidate and trim overdrive.",
                "selected_candidate": 1,
                "audition_notes": ["A/B by ear before compiling any send plan"],
                "parameter_edits": [
                    {
                        "parameter": "Filter Overdrive",
                        "direction": "decrease",
                        "reason": "smooths the top edge",
                    }
                ],
                "safety_notes": ["staged review only"],
                "staged_only": True,
            }
        return LocalAiJsonResponse(
            workflow=request.workflow,
            model=request.model,
            data=data,
            raw_content=json.dumps(data),
            done_reason="stop",
            prompt_eval_count=10,
            eval_count=5,
        )


class _UnavailableProvider:
    def chat_json(self, request: LocalAiChatRequest) -> LocalAiJsonResponse:
        raise LocalAiUnavailableError("ollama offline")


def test_importing_ollama_local_copilot_report_prints_nothing() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "import rytm_randomizer.reports.ollama_local_copilot",
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert result.stdout == ""
    assert result.stderr == ""


def test_ollama_local_copilot_report_text_includes_all_three_workflows() -> None:
    from rytm_randomizer.reports.ollama_local_copilot import (
        build_ollama_local_copilot_report,
        format_ollama_local_copilot_report,
    )

    report = build_ollama_local_copilot_report(
        question="How can I make a darker hardware-safe groove?",
        description="dark rolling techno with metallic A4 stab",
        workflow="all",
        model="llama3.2",
        ask_ollama=False,
    )
    text = "\n".join(format_ollama_local_copilot_report(report))

    assert text.startswith("RytmRandomizer passive Ollama local copilot\n")
    assert "Docs/MIDI assistant:" in text
    assert "Mutation intent:" in text
    assert "Analog Four patch co-designer:" in text
    assert "- Ollama call: skipped" in text
    assert "- no MIDI sent" in text
    assert "Source: rytm_randomizer.reports.ollama_local_copilot" in text


@pytest.mark.parametrize(
    ("workflow", "included", "excluded"),
    [
        (
            "docs",
            "Docs/MIDI assistant:",
            ("Mutation intent:", "Analog Four patch co-designer:"),
        ),
        (
            "mutation",
            "Mutation intent:",
            ("Docs/MIDI assistant:", "Analog Four patch co-designer:"),
        ),
        (
            "patch",
            "Analog Four patch co-designer:",
            ("Docs/MIDI assistant:", "Mutation intent:"),
        ),
    ],
)
def test_ollama_local_copilot_report_text_matches_requested_workflow(
    workflow: str,
    included: str,
    excluded: tuple[str, ...],
) -> None:
    from rytm_randomizer.reports.ollama_local_copilot import (
        build_ollama_local_copilot_report,
        format_ollama_local_copilot_report,
    )

    report = build_ollama_local_copilot_report(
        question="How can I stage this safely?",
        description="bright metallic stab",
        workflow=workflow,
        ask_ollama=False,
    )
    text = "\n".join(format_ollama_local_copilot_report(report))

    assert included in text
    for heading in excluded:
        assert heading not in text


def test_ollama_local_copilot_report_json_is_deterministic() -> None:
    from rytm_randomizer.reports.ollama_local_copilot import (
        build_ollama_local_copilot_payload,
        build_ollama_local_copilot_report,
    )

    report = build_ollama_local_copilot_report(
        question="Which MIDI facts matter?",
        description="bright stab",
        workflow="docs",
        model="llama3.2",
        ask_ollama=False,
    )
    payload = build_ollama_local_copilot_payload(report)

    assert payload["workflow"] == "docs"
    assert payload["ollama"]["called"] is False
    assert payload["docs_packet"]["version"] == "local-ai-docs-assistant-v1"
    assert json.dumps(payload, sort_keys=True) == json.dumps(
        build_ollama_local_copilot_payload(report),
        sort_keys=True,
    )


def test_ollama_local_copilot_report_can_call_injected_provider() -> None:
    from rytm_randomizer.reports.ollama_local_copilot import build_ollama_local_copilot_report

    provider = _FakeProvider()

    report = build_ollama_local_copilot_report(
        question="Make this safer and darker",
        description="dark rolling techno with bright stab",
        workflow="all",
        model="llama3.2",
        ask_ollama=True,
        provider=provider,
    )

    assert [request.workflow for request in provider.requests] == ["docs", "mutation", "patch"]
    assert tuple(result.status for result in report.ollama_results) == (
        "validated",
        "validated",
        "validated",
    )
    assert report.ollama_results[0].data["answer"] == "Use the passive MIDI catalog first."


@pytest.mark.parametrize(
    ("workflow", "expected_requests"),
    [
        ("mutation", ["mutation"]),
        ("patch", ["patch"]),
    ],
)
def test_ollama_local_copilot_report_calls_single_requested_workflow(
    workflow: str,
    expected_requests: list[str],
) -> None:
    from rytm_randomizer.reports.ollama_local_copilot import build_ollama_local_copilot_report

    provider = _FakeProvider()

    report = build_ollama_local_copilot_report(
        question="Make this safer and darker",
        description="dark rolling techno with bright stab",
        workflow=workflow,
        model="llama3.2",
        ask_ollama=True,
        provider=provider,
    )

    assert [request.workflow for request in provider.requests] == expected_requests
    assert tuple(result.workflow for result in report.ollama_results) == tuple(expected_requests)
    assert tuple(result.status for result in report.ollama_results) == ("validated",)


def test_ollama_local_copilot_report_records_unavailable_provider() -> None:
    from rytm_randomizer.reports.ollama_local_copilot import build_ollama_local_copilot_report

    report = build_ollama_local_copilot_report(
        question="Can Ollama answer?",
        workflow="docs",
        ask_ollama=True,
        provider=_UnavailableProvider(),
    )

    assert len(report.ollama_results) == 1
    assert report.ollama_results[0].status == "unavailable"
    assert report.ollama_results[0].error == "ollama offline"


def test_ollama_local_copilot_cli_json_mode(capsys: pytest.CaptureFixture[str]) -> None:
    from rytm_randomizer.cli import main

    exit_code = main(
        [
            "ollama-local-copilot-report",
            "--question",
            "How do I keep this safe?",
            "--description",
            "dark rolling techno",
            "--workflow",
            "mutation",
            "--json",
        ]
    )

    captured = capsys.readouterr()
    payload = json.loads(captured.out)

    assert exit_code == 0
    assert payload["workflow"] == "mutation"
    assert payload["mutation_packet"]["intent"]["staged_only"] is True
    assert payload["ollama"]["called"] is False
    assert captured.err == ""


def test_ollama_local_copilot_cli_text_mode(capsys: pytest.CaptureFixture[str]) -> None:
    from rytm_randomizer.cli import main

    exit_code = main(
        [
            "ollama-local-copilot-report",
            "--question",
            "How do I keep this safe?",
            "--workflow",
            "docs",
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 0
    assert "RytmRandomizer passive Ollama local copilot" in captured.out
    assert "Docs/MIDI assistant:" in captured.out
    assert captured.err == ""


def test_ollama_local_copilot_cli_rejects_bad_arguments(
    capsys: pytest.CaptureFixture[str],
) -> None:
    from rytm_randomizer.cli import main

    exit_code = main(["ollama-local-copilot-report", "--workflow", "wrong"])

    captured = capsys.readouterr()

    assert exit_code == 2
    assert "workflow must be one of" in captured.err
    assert captured.out == ""


@pytest.mark.parametrize(
    ("args", "message"),
    [
        (["--question", "hello", "--model"], "--model requires a value"),
        (["--question", "hello", "--description"], "--description requires a value"),
        (["--question", "hello", "--unknown"], "unknown argument"),
        (["--workflow", "docs"], "--question requires a value"),
    ],
)
def test_parse_ollama_local_copilot_args_rejects_bad_shapes(
    args: list[str],
    message: str,
) -> None:
    from rytm_randomizer.reports.ollama_local_copilot import OLLAMA_LOCAL_COPILOT_CLI_COMMAND

    with pytest.raises(ValueError, match=message):
        OLLAMA_LOCAL_COPILOT_CLI_COMMAND.args_parser(args)


def test_parse_ollama_local_copilot_args_accepts_model_and_ask_flag() -> None:
    from rytm_randomizer.reports.ollama_local_copilot import OLLAMA_LOCAL_COPILOT_CLI_COMMAND

    parsed = OLLAMA_LOCAL_COPILOT_CLI_COMMAND.args_parser(
        [
            "--question",
            "How do I stage this?",
            "--model",
            "mistral",
            "--ask-ollama",
            "--json",
        ]
    )

    assert parsed["model"] == "mistral"
    assert parsed["ask_ollama"] is True
    assert parsed["json_output"] is True


def test_ollama_local_copilot_handler_formats_build_errors(
    capsys: pytest.CaptureFixture[str],
) -> None:
    from rytm_randomizer.reports.ollama_local_copilot import (
        _handle_ollama_local_copilot_report,
    )

    exit_code = _handle_ollama_local_copilot_report(
        question=" ",
        description=None,
        workflow="docs",
        model="llama3.2",
        ask_ollama=False,
    )

    captured = capsys.readouterr()

    assert exit_code == 2
    assert "--question requires a non-empty value" in captured.err
    assert captured.out == ""
