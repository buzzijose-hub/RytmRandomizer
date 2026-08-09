"""Behavior tests for the operator-console PowerShell formatting helpers."""

from __future__ import annotations

import pytest

from rytm_randomizer.behavior.operator_console import (
    powershell_command,
    powershell_literal_arg,
)

pytestmark = pytest.mark.fast


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("candidate-1.wav", "candidate-1.wav"),
        ("Jose's A4", "'Jose''s A4'"),
        (r"C:\music\kits,drafts\manifest.json", r"'C:\music\kits,drafts\manifest.json'"),
        ("@splat", "'@splat'"),
        ("user@host", "user@host"),
        ("", "''"),
    ],
)
def test_literal_arg_quotes_exactly_the_unsafe_values(value: str, expected: str) -> None:
    assert powershell_literal_arg(value) == expected


def test_literal_arg_always_quote_forces_quoting_of_safe_values() -> None:
    assert powershell_literal_arg("safe-value", always_quote=True) == "'safe-value'"


def test_command_invokes_head_through_the_call_operator_always_quoted() -> None:
    # A quoted string at command position is just an expression in
    # PowerShell; the `&` call operator plus an always-quoted executable is
    # what makes the line runnable regardless of the interpreter path shape.
    rendered = powershell_command(["python", "-m", "rytm_randomizer.app", "--dry-run"])
    assert rendered == "& 'python' -m rytm_randomizer.app --dry-run"


def test_command_quotes_only_the_arguments_that_need_it() -> None:
    rendered = powershell_command(
        ["C:/py/python.exe", "--a4-output-port", "Elektron Analog Four MKII 2"]
    )
    assert rendered == "& 'C:/py/python.exe' --a4-output-port 'Elektron Analog Four MKII 2'"


def test_command_neutralizes_injection_shaped_arguments() -> None:
    rendered = powershell_command(["tool", "evil'; Remove-Item -Recurse C:\\ ;'x"])
    assert rendered == "& 'tool' 'evil''; Remove-Item -Recurse C:\\ ;''x'"


def test_command_renders_empty_argv_as_bare_call_operator() -> None:
    assert powershell_command([]) == "& "
