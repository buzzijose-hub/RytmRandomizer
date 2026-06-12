"""WS-S7 tests: ``rytm_randomizer.cli_registry`` (CLI command registry).

The registry is the extension seam that lets the cli.py refactor
collapse each ``if args == [...]`` arm into a single ``register(...)``
call from a per-command module. These tests pin the public surface and
the immutability/duplicate-rejection guarantees the dispatcher relies on.

Test naming: ``test_<unit>_<behavior>_when_<condition>`` per Gate 8.
"""

from __future__ import annotations

import dataclasses
import json
import sys
from pathlib import Path
from types import MappingProxyType, SimpleNamespace

import pytest

# WS-M4: mark this module as fast-suite; pytest -m fast skips the 505
# warm-worker V1.34 parity fixtures and runs in <60s.
pytestmark = pytest.mark.fast

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


@pytest.fixture(autouse=True)
def _clean_registry():
    """Snapshot ``_COMMANDS`` around every test so registrations do not leak.

    The registry is a module-level dict; without this guard a test that
    registers a stub command would pollute every later test (and any
    other test module that imports ``cli_registry``).
    """

    from rytm_randomizer import cli_registry

    saved = dict(cli_registry._COMMANDS)
    cli_registry._COMMANDS.clear()
    try:
        yield
    finally:
        cli_registry._COMMANDS.clear()
        cli_registry._COMMANDS.update(saved)


# ---------------------------------------------------------------------------
# 1. Public surface
# ---------------------------------------------------------------------------


def test_cli_registry_module_exposes_expected_public_names() -> None:
    """Importing the module gives callers every documented symbol."""

    from rytm_randomizer import cli_registry

    for name in (
        "CliCommand",
        "register",
        "get",
        "all_commands",
        "default_error_formatter",
        "make_passive_report_command",
    ):
        assert hasattr(cli_registry, name), f"cli_registry missing {name!r}"


def test_registry_name_constant_is_final_str_cli() -> None:
    """Per Gate 12 the registry has a ``Final[str]`` name constant."""

    from rytm_randomizer import cli_registry

    assert cli_registry._REGISTRY_NAME == "cli"


# ---------------------------------------------------------------------------
# 2. CliCommand dataclass shape
# ---------------------------------------------------------------------------


def _stub_parser(argv):
    return {"argv": list(argv)}


def _stub_handler(**kwargs):
    return 0


def test_clicommand_is_frozen_dataclass_when_mutating_field() -> None:
    """Frozen so import-time registration cannot be silently rewritten."""

    from rytm_randomizer.cli_registry import CliCommand

    cmd = CliCommand(
        name="stub",
        summary="stub summary",
        args_parser=_stub_parser,
        handler=_stub_handler,
    )

    with pytest.raises(dataclasses.FrozenInstanceError):
        cmd.name = "renamed"  # type: ignore[misc]


def test_clicommand_error_formatter_defaults_to_none_when_omitted() -> None:
    from rytm_randomizer.cli_registry import CliCommand

    cmd = CliCommand(
        name="stub",
        summary="stub summary",
        args_parser=_stub_parser,
        handler=_stub_handler,
    )

    assert cmd.error_formatter is None


# ---------------------------------------------------------------------------
# 3. register / get / all_commands
# ---------------------------------------------------------------------------


def test_register_then_get_returns_the_same_clicommand() -> None:
    from rytm_randomizer.cli_registry import CliCommand, get, register

    cmd = CliCommand(
        name="stub",
        summary="stub summary",
        args_parser=_stub_parser,
        handler=_stub_handler,
    )

    register(cmd)

    assert get("stub") is cmd


def test_get_returns_none_when_command_is_unknown() -> None:
    """Dispatcher relies on ``None`` to fall through to USAGE/exit 2."""

    from rytm_randomizer.cli_registry import get

    assert get("definitely-not-a-command") is None


def test_register_raises_valueerror_when_name_already_taken() -> None:
    from rytm_randomizer.cli_registry import CliCommand, register

    cmd_a = CliCommand(
        name="dup",
        summary="first",
        args_parser=_stub_parser,
        handler=_stub_handler,
    )
    cmd_b = CliCommand(
        name="dup",
        summary="second",
        args_parser=_stub_parser,
        handler=_stub_handler,
    )

    register(cmd_a)

    with pytest.raises(ValueError, match="already registered"):
        register(cmd_b)


def test_all_commands_returns_mapping_proxy_view_when_called() -> None:
    """``all_commands()`` must be immutable from the caller's side."""

    from rytm_randomizer.cli_registry import CliCommand, all_commands, register

    register(
        CliCommand(
            name="stub",
            summary="stub summary",
            args_parser=_stub_parser,
            handler=_stub_handler,
        )
    )

    view = all_commands()

    assert isinstance(view, MappingProxyType)
    assert "stub" in view
    with pytest.raises(TypeError):
        view["should_fail"] = None  # type: ignore[index]


def test_all_commands_reflects_subsequent_registrations_when_added() -> None:
    """MappingProxy is a live view, not a snapshot."""

    from rytm_randomizer.cli_registry import CliCommand, all_commands, register

    view = all_commands()
    assert "late" not in view

    register(
        CliCommand(
            name="late",
            summary="registered after view",
            args_parser=_stub_parser,
            handler=_stub_handler,
        )
    )

    assert "late" in view


# ---------------------------------------------------------------------------
# 4. discovery helpers
# ---------------------------------------------------------------------------


def test_should_skip_matches_exact_prefix_and_dot_boundary() -> None:
    from rytm_randomizer.cli_registry import _should_skip

    assert _should_skip("rytm_randomizer.cli") is True
    assert _should_skip("rytm_randomizer.cli.submodule") is True
    assert _should_skip("rytm_randomizer.cli_registry") is True
    assert _should_skip("rytm_randomizer.cli_registry_extra") is False
    assert _should_skip("rytm_randomizer.reports.safe") is False


def test_discover_all_returns_without_walking_when_root_is_module(monkeypatch) -> None:
    from rytm_randomizer import cli_registry

    walked: list[object] = []

    monkeypatch.setattr(
        cli_registry.importlib,
        "import_module",
        lambda name: SimpleNamespace(__name__=name),
    )
    monkeypatch.setattr(
        cli_registry.pkgutil,
        "walk_packages",
        lambda package_path, prefix: walked.append((package_path, prefix)),
    )

    cli_registry.discover_all("plain_module")

    assert walked == []


def test_discover_all_imports_non_skipped_package_modules(monkeypatch) -> None:
    from rytm_randomizer import cli_registry

    imported: list[str] = []
    package = SimpleNamespace(__path__=("fake-path",))
    modules = (
        SimpleNamespace(name="rytm_randomizer.cli"),
        SimpleNamespace(name="rytm_randomizer.reports.safe"),
    )

    def fake_import_module(name: str) -> object:
        imported.append(name)
        return package if name == "rytm_randomizer" else SimpleNamespace(__name__=name)

    def fake_walk_packages(package_path: object, prefix: str) -> tuple[object, ...]:
        assert package_path == ("fake-path",)
        assert prefix == "rytm_randomizer."
        return modules

    monkeypatch.setattr(cli_registry.importlib, "import_module", fake_import_module)
    monkeypatch.setattr(cli_registry.pkgutil, "walk_packages", fake_walk_packages)

    cli_registry.discover_all()

    assert imported == ["rytm_randomizer", "rytm_randomizer.reports.safe"]


# ---------------------------------------------------------------------------
# 5. default_error_formatter
# ---------------------------------------------------------------------------


def test_default_error_formatter_returns_class_and_message_shape() -> None:
    from rytm_randomizer.cli_registry import default_error_formatter

    rendered = default_error_formatter(ValueError("bad input"))

    assert rendered == "Error: ValueError: bad input"


def test_default_error_formatter_handles_subclassed_exception_when_raised() -> None:
    from rytm_randomizer.cli_registry import default_error_formatter

    class _CustomError(RuntimeError):
        pass

    rendered = default_error_formatter(_CustomError("oh no"))

    assert rendered == "Error: _CustomError: oh no"


# ---------------------------------------------------------------------------
# 6. make_passive_report_command
# ---------------------------------------------------------------------------


def test_make_passive_report_command_writes_text_when_no_json_flag(capsys) -> None:
    from rytm_randomizer.cli_registry import make_passive_report_command

    command = make_passive_report_command(
        "demo-report",
        "demo passive report",
        format_lines=lambda: ("heading", "body"),
        build_payload=lambda: {"demo": True},
    )

    assert command.name == "demo-report"
    assert command.summary == "demo passive report"
    assert command.args_parser([]) == {"json_output": False}
    assert command.handler(**command.args_parser([])) == 0

    captured = capsys.readouterr()
    assert captured.out == "heading\nbody\n"
    assert captured.err == ""


def test_make_passive_report_command_writes_sorted_json_when_json_flag(capsys) -> None:
    from rytm_randomizer.cli_registry import make_passive_report_command

    command = make_passive_report_command(
        "demo-report",
        "demo passive report",
        format_lines=lambda: ("unused",),
        build_payload=lambda: {"z": 2, "a": {"nested": True}},
    )

    assert command.args_parser(["--json"]) == {"json_output": True}
    assert command.handler(**command.args_parser(["--json"])) == 0

    captured = capsys.readouterr()
    assert json.loads(captured.out) == {"a": {"nested": True}, "z": 2}
    assert captured.out.startswith('{\n  "a":')
    assert captured.out.endswith("\n")
    assert captured.err == ""


def test_make_passive_report_command_can_write_compact_json(capsys) -> None:
    from rytm_randomizer.cli_registry import make_passive_report_command

    command = make_passive_report_command(
        "compact-report",
        "compact passive report",
        format_lines=lambda: ("unused",),
        build_payload=lambda: {"z": 2, "a": True},
        json_indent=None,
    )

    assert command.handler(**command.args_parser(["--json"])) == 0

    captured = capsys.readouterr()
    assert captured.out == '{"a": true, "z": 2}\n'
    assert captured.err == ""


def test_make_passive_report_command_rejects_unexpected_args_and_formats_error() -> None:
    from rytm_randomizer.cli_registry import make_passive_report_command

    command = make_passive_report_command(
        "demo-report",
        "demo passive report",
        format_lines=lambda: ("unused",),
        build_payload=lambda: {"demo": True},
    )

    with pytest.raises(ValueError, match="demo-report accepts only optional --json"):
        command.args_parser(["--arm"])

    assert command.error_formatter is not None
    assert command.error_formatter(ValueError("demo-report accepts only optional --json")) == (
        "Error: demo-report accepts only optional --json"
    )


def test_make_passive_report_command_can_disable_json_flag(capsys) -> None:
    from rytm_randomizer.cli_registry import make_passive_report_command

    command = make_passive_report_command(
        "plain-report",
        "plain passive report",
        format_lines=lambda: ("plain",),
        json_flag=False,
    )

    assert command.args_parser([]) == {}
    assert command.handler() == 0
    with pytest.raises(ValueError, match="plain-report does not accept arguments"):
        command.args_parser(["--json"])

    captured = capsys.readouterr()
    assert captured.out == "plain\n"
    assert captured.err == ""


def test_make_passive_report_command_can_preserve_default_dispatch_error() -> None:
    from rytm_randomizer.cli_registry import make_passive_report_command

    command = make_passive_report_command(
        "legacy-report",
        "legacy passive report",
        format_lines=lambda: ("legacy",),
        json_flag=False,
        error_formatter=None,
    )

    assert command.error_formatter is None


def test_make_passive_report_command_rejects_json_without_payload() -> None:
    from rytm_randomizer.cli_registry import make_passive_report_command

    command = make_passive_report_command(
        "payloadless-report",
        "payloadless passive report",
        format_lines=lambda: ("payloadless",),
    )

    with pytest.raises(ValueError, match="payloadless-report does not provide JSON output"):
        command.handler(**command.args_parser(["--json"]))


# ---------------------------------------------------------------------------
# 7. Round-trip: register -> get -> parse -> handle returns exit code
# ---------------------------------------------------------------------------


def test_round_trip_register_parse_handle_propagates_exit_code() -> None:
    """Mirror the future cli.py dispatcher: parse argv, splat into handler."""

    from rytm_randomizer.cli_registry import CliCommand, get, register

    captured: dict[str, object] = {}

    def parser(argv):
        # Echo a single positional arg to prove parser output threads into the handler.
        return {"value": argv[0] if argv else None}

    def handler(*, value):
        captured["value"] = value
        return 7  # Distinctive non-zero so we know we got *this* handler.

    register(
        CliCommand(
            name="echo",
            summary="echo a single arg",
            args_parser=parser,
            handler=handler,
        )
    )

    cmd = get("echo")
    assert cmd is not None  # narrowing for type-checkers

    kwargs = cmd.args_parser(["hello"])
    exit_code = cmd.handler(**kwargs)

    assert kwargs == {"value": "hello"}
    assert exit_code == 7
    assert captured == {"value": "hello"}
