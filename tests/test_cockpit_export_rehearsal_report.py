"""Tests for the passive cockpit export rehearsal report (WS-D)."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.fast

PROJECT_ROOT = Path(__file__).resolve().parents[1]
FORBIDDEN_REAL_MIDI_AND_ADAPTER_MODULES = (
    "mido",
    "rtmidi",
    "pythonrtmidi",
    "rytm_randomizer.real_midi_adapter",
)
FORBIDDEN_EXPORT_SIDE_EFFECT_MODULES = (
    "rytm_randomizer.cockpit.export.signing",
    "rytm_randomizer.cockpit.export.verifier",
    "rytm_randomizer.cockpit.export.writer",
    "rytm_randomizer.cockpit.export.cli",
)


def _scene_profiles_dir(tmp_path: Path) -> Path:
    """Return a profiles dir containing no user profiles (forces built-in resolution)."""

    profiles_dir = tmp_path / "profiles"
    (profiles_dir / "user").mkdir(parents=True)
    return profiles_dir


def _builtin_profile_id() -> str:
    # Built-in scene id is deterministic per builtin.py: "scene-<name>".
    return "scene-industrial"


# ---------------------------------------------------------------------------
# Surface shape — ready (signed and unsigned)
# ---------------------------------------------------------------------------


def test_cockpit_export_rehearsal_builds_unsigned_ready_surface(tmp_path: Path) -> None:
    from rytm_randomizer.reports.cockpit_export_rehearsal import (
        EXPORT_REHEARSAL_SURFACE_VERSION,
        build_cockpit_export_rehearsal_report,
        format_cockpit_export_rehearsal_report,
        to_cockpit_export_rehearsal_json,
    )

    profiles_dir = _scene_profiles_dir(tmp_path)
    report = build_cockpit_export_rehearsal_report(
        profile_id=_builtin_profile_id(),
        profiles_dir=profiles_dir,
        unsigned=True,
        surface_label="Warehouse export surface",
    )

    assert report.surface_version == EXPORT_REHEARSAL_SURFACE_VERSION
    assert report.surface_id.startswith("export-surface-")
    assert report.surface_label == "Warehouse export surface"
    assert report.surface_status == "ready"
    assert report.screen_state == "export-ready-review"
    assert report.send_control_state == "ready"
    assert report.profile_id == _builtin_profile_id()
    assert report.profile_kind == "scene"
    assert report.signed is False
    assert report.key_id is None
    assert report.signed_size is None
    assert report.payload_size > 0
    assert len(report.payload_crc_hex) == 8
    assert int(report.payload_crc_hex, 16) >= 0
    assert report.output_path.endswith(f"{_builtin_profile_id()}-v{report.model_version}.rymp")
    assert {panel.panel_key for panel in report.panels} >= {
        "summary",
        "output-path",
        "payload",
        "signing",
        "safety-locks",
    }
    export_action = next(
        control for control in report.action_controls if control.action_key == "export"
    )
    assert export_action.control_state == "ready"
    assert export_action.gate_status == "ready"
    assert export_action.enabled is False
    assert export_action.bound_state_key == "cockpit.export.send"
    assert any(binding.state_key == "cockpit.export.status" for binding in report.state_bindings)
    assert any(check.check_key == "assert-export-action-gated" for check in report.surface_checks)
    assert "no .rymp file write" in report.blocked_actions
    assert "no signer invocation" in report.blocked_actions
    assert report.replay_command.startswith(
        "python -m rytm_randomizer.cli cockpit-export-rehearsal-report "
    )
    assert "--unsigned" in report.replay_command
    assert "--key-id" not in report.replay_command

    lines = format_cockpit_export_rehearsal_report(report)
    text = "\n".join(lines)
    assert lines[0] == "RytmRandomizer passive cockpit export rehearsal surface"
    assert "Cockpit export rehearsal surface:" in lines
    assert "- Surface status: ready" in lines
    assert "- EXPORT control state: ready" in lines
    assert "- Signed: False" in lines
    assert "- Key id: none" in lines
    assert "GUI panels:" in lines
    assert "- summary: Export summary" in lines
    assert "Action controls:" in lines
    assert "- export: EXPORT" in lines
    assert "Source: rytm_randomizer.reports.cockpit_export_rehearsal" in text

    payload = to_cockpit_export_rehearsal_json(report)
    surface = payload["cockpit_export_rehearsal"]
    assert surface["surface_id"] == report.surface_id
    assert surface["surface_status"] == "ready"
    assert surface["signed"] is False
    assert surface["key_id"] is None
    assert surface["signed_size"] is None
    assert surface["payload_size"] == report.payload_size
    assert surface["payload_crc_hex"] == report.payload_crc_hex
    assert surface["action_controls"][0]["enabled"] is False
    assert payload["safety"][0] == "passive/read-only"
    # JSON is deterministic.
    text_a = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    text_b = json.dumps(
        to_cockpit_export_rehearsal_json(
            build_cockpit_export_rehearsal_report(
                profile_id=_builtin_profile_id(),
                profiles_dir=profiles_dir,
                unsigned=True,
                surface_label="Warehouse export surface",
            )
        ),
        sort_keys=True,
        separators=(",", ":"),
    )
    assert text_a == text_b


def test_cockpit_export_rehearsal_builds_signed_ready_surface_with_key_id(
    tmp_path: Path,
) -> None:
    from rytm_randomizer.reports.cockpit_export_rehearsal import (
        build_cockpit_export_rehearsal_report,
        format_cockpit_export_rehearsal_report,
        to_cockpit_export_rehearsal_json,
    )

    profiles_dir = _scene_profiles_dir(tmp_path)
    report = build_cockpit_export_rehearsal_report(
        profile_id="scene-hypnotic",
        profiles_dir=profiles_dir,
        key_id="prod-ed25519-2026-05",
        surface_label="Signed warehouse export",
    )

    assert report.signed is True
    assert report.key_id == "prod-ed25519-2026-05"
    assert report.signed_size is not None
    assert report.signed_size > report.payload_size
    assert "signed=True" in report.panels[0].value_text
    assert "key prod-ed25519-2026-05" in report.panels[3].summary
    assert "key_id=prod-ed25519-2026-05" in report.panels[3].value_text
    assert "click EXPORT" in report.primary_operator_action
    assert "signed envelope size" in (
        report.primary_operator_action
        + " "
        + "\n".join(
            line for binding in report.state_bindings for line in (binding.label, binding.value)
        )
    ) or "Signed envelope size" in "\n".join(binding.label for binding in report.state_bindings)
    assert "--key-id" in report.replay_command
    assert "--unsigned" not in report.replay_command

    text = "\n".join(format_cockpit_export_rehearsal_report(report))
    assert "- Signed: True" in text
    assert "- Key id: prod-ed25519-2026-05" in text
    assert f"- Signed envelope size: {report.signed_size}" in text

    payload = to_cockpit_export_rehearsal_json(report)
    surface = payload["cockpit_export_rehearsal"]
    assert surface["signed"] is True
    assert surface["key_id"] == "prod-ed25519-2026-05"
    assert surface["signed_size"] == report.signed_size


def test_cockpit_export_rehearsal_default_output_path_uses_profile_id_and_model_version(
    tmp_path: Path,
) -> None:
    from rytm_randomizer.reports.cockpit_export_rehearsal import (
        build_cockpit_export_rehearsal_report,
    )

    profiles_dir = _scene_profiles_dir(tmp_path)
    report = build_cockpit_export_rehearsal_report(
        profile_id="scene-industrial",
        profiles_dir=profiles_dir,
        unsigned=True,
    )

    # Default output path mirrors the spec template.
    assert report.output_path.endswith(f"scene-industrial-v{report.model_version}.rymp")


def test_cockpit_export_rehearsal_explicit_output_path_is_honored(tmp_path: Path) -> None:
    from rytm_randomizer.reports.cockpit_export_rehearsal import (
        build_cockpit_export_rehearsal_report,
    )

    profiles_dir = _scene_profiles_dir(tmp_path)
    explicit = tmp_path / "exports" / "scene.rymp"
    report = build_cockpit_export_rehearsal_report(
        profile_id="scene-industrial",
        profiles_dir=profiles_dir,
        unsigned=True,
        output_path=explicit,
    )

    assert report.output_path == str(explicit)
    parent_check = next(
        check for check in report.surface_checks if check.check_key == "assert-output-parent-exists"
    )
    # Parent does not exist by default; check should signal review-needed.
    assert parent_check.status == "review-needed"
    assert "does not exist" in parent_check.message


def test_cockpit_export_rehearsal_existing_output_parent_marks_check_ready(
    tmp_path: Path,
) -> None:
    from rytm_randomizer.reports.cockpit_export_rehearsal import (
        build_cockpit_export_rehearsal_report,
    )

    profiles_dir = _scene_profiles_dir(tmp_path)
    parent = tmp_path / "exports"
    parent.mkdir()
    explicit = parent / "scene.rymp"
    report = build_cockpit_export_rehearsal_report(
        profile_id="scene-industrial",
        profiles_dir=profiles_dir,
        unsigned=True,
        output_path=explicit,
    )

    parent_check = next(
        check for check in report.surface_checks if check.check_key == "assert-output-parent-exists"
    )
    assert parent_check.status == "ready"
    assert "Output parent directory exists" in parent_check.message


# ---------------------------------------------------------------------------
# Blocked surface
# ---------------------------------------------------------------------------


def test_cockpit_export_rehearsal_blocked_when_additional_blockers_provided(
    tmp_path: Path,
) -> None:
    """Phase 3.5 testing seam: caller-injected blocked reasons switch the surface."""

    from rytm_randomizer.reports.cockpit_export_rehearsal import (
        build_cockpit_export_rehearsal_report,
        format_cockpit_export_rehearsal_report,
        to_cockpit_export_rehearsal_json,
    )

    profiles_dir = _scene_profiles_dir(tmp_path)
    report = build_cockpit_export_rehearsal_report(
        profile_id="scene-industrial",
        profiles_dir=profiles_dir,
        key_id="missing-key-2026",
        additional_blocked_reasons=("keystore_unavailable",),
    )

    assert report.surface_status == "blocked"
    assert report.screen_state == "disabled"
    assert report.send_control_state == "disabled"
    assert report.blocked_reasons == ("keystore_unavailable",)
    assert "Resolve the listed blocked reasons" in report.primary_operator_action
    assert (
        report.blocked_actions[0]
        == "EXPORT remains disabled until the cockpit resolves the listed blockers"
    )
    blocked_check = next(
        check for check in report.surface_checks if check.check_key == "assert-blocked-reasons"
    )
    assert blocked_check.status == "blocked"
    assert "keystore_unavailable" in blocked_check.message

    text = "\n".join(format_cockpit_export_rehearsal_report(report))
    assert "- Surface status: blocked" in text
    assert "- Screen state: disabled" in text
    assert "- EXPORT control state: disabled" in text
    assert "- Blocked reasons: keystore_unavailable" in text
    assert "EXPORT remains disabled" in text

    payload = to_cockpit_export_rehearsal_json(report)
    surface = payload["cockpit_export_rehearsal"]
    assert surface["surface_status"] == "blocked"
    assert surface["blocked_reasons"] == ["keystore_unavailable"]


# ---------------------------------------------------------------------------
# Errors / validation
# ---------------------------------------------------------------------------


def test_cockpit_export_rehearsal_rejects_missing_profile(tmp_path: Path) -> None:
    from rytm_randomizer.reports.cockpit_export_rehearsal import (
        build_cockpit_export_rehearsal_report,
    )

    profiles_dir = _scene_profiles_dir(tmp_path)
    with pytest.raises(ValueError, match="not found in registry"):
        build_cockpit_export_rehearsal_report(
            profile_id="profile-does-not-exist",
            profiles_dir=profiles_dir,
            unsigned=True,
        )


def test_cockpit_export_rehearsal_rejects_blank_surface_label(tmp_path: Path) -> None:
    from rytm_randomizer.reports.cockpit_export_rehearsal import (
        build_cockpit_export_rehearsal_report,
    )

    profiles_dir = _scene_profiles_dir(tmp_path)
    with pytest.raises(ValueError, match="surface_label must not be blank"):
        build_cockpit_export_rehearsal_report(
            profile_id="scene-industrial",
            profiles_dir=profiles_dir,
            unsigned=True,
            surface_label="   ",
        )


def test_cockpit_export_rehearsal_rejects_mutually_exclusive_signing_flags(
    tmp_path: Path,
) -> None:
    from rytm_randomizer.reports.cockpit_export_rehearsal import (
        build_cockpit_export_rehearsal_report,
    )

    profiles_dir = _scene_profiles_dir(tmp_path)
    with pytest.raises(ValueError, match="mutually exclusive"):
        build_cockpit_export_rehearsal_report(
            profile_id="scene-industrial",
            profiles_dir=profiles_dir,
            key_id="some-key",
            unsigned=True,
        )


def test_cockpit_export_rehearsal_rejects_blank_key_id(tmp_path: Path) -> None:
    from rytm_randomizer.reports.cockpit_export_rehearsal import (
        build_cockpit_export_rehearsal_report,
    )

    profiles_dir = _scene_profiles_dir(tmp_path)
    with pytest.raises(ValueError, match="key_id must not be blank"):
        build_cockpit_export_rehearsal_report(
            profile_id="scene-industrial",
            profiles_dir=profiles_dir,
            key_id="   ",
        )


# ---------------------------------------------------------------------------
# CLI parser + handler
# ---------------------------------------------------------------------------


def test_cockpit_export_rehearsal_cli_parser_round_trips_all_options(
    tmp_path: Path,
) -> None:
    from rytm_randomizer.reports.cockpit_export_rehearsal import (
        COCKPIT_EXPORT_REHEARSAL_CLI_COMMAND,
    )

    profiles_dir = _scene_profiles_dir(tmp_path)
    output_path = tmp_path / "exports" / "scene.rymp"
    parsed = COCKPIT_EXPORT_REHEARSAL_CLI_COMMAND.args_parser(
        [
            "--profile-id",
            "scene-industrial",
            "--profiles-dir",
            str(profiles_dir),
            "--key-id",
            "prod-ed25519-2026-05",
            "--output",
            str(output_path),
            "--label",
            "Warehouse export",
            "--json",
        ]
    )
    assert parsed["profile_id"] == "scene-industrial"
    assert parsed["profiles_dir"] == profiles_dir
    assert parsed["key_id"] == "prod-ed25519-2026-05"
    assert parsed["unsigned"] is False
    assert parsed["output_path"] == output_path
    assert parsed["surface_label"] == "Warehouse export"
    assert parsed["json_output"] is True


def test_cockpit_export_rehearsal_cli_parser_defaults_profiles_dir(
    tmp_path: Path,
) -> None:
    from rytm_randomizer.cockpit.profiles import default_profiles_dir
    from rytm_randomizer.reports.cockpit_export_rehearsal import (
        COCKPIT_EXPORT_REHEARSAL_CLI_COMMAND,
    )

    parsed = COCKPIT_EXPORT_REHEARSAL_CLI_COMMAND.args_parser(
        ["--profile-id", "scene-industrial", "--unsigned"]
    )
    assert parsed["profiles_dir"] == default_profiles_dir()
    assert parsed["unsigned"] is True


def test_cockpit_export_rehearsal_cli_parser_errors(tmp_path: Path) -> None:
    from rytm_randomizer.reports.cockpit_export_rehearsal import (
        COCKPIT_EXPORT_REHEARSAL_CLI_COMMAND,
    )

    profiles_dir = _scene_profiles_dir(tmp_path)
    with pytest.raises(ValueError, match="usage"):
        COCKPIT_EXPORT_REHEARSAL_CLI_COMMAND.args_parser(
            ["--profile-id", "scene-industrial", "--unknown"]
        )
    with pytest.raises(ValueError, match="--profile-id is required"):
        COCKPIT_EXPORT_REHEARSAL_CLI_COMMAND.args_parser(["--profiles-dir", str(profiles_dir)])
    with pytest.raises(ValueError, match="profile_id must not be blank"):
        COCKPIT_EXPORT_REHEARSAL_CLI_COMMAND.args_parser(
            ["--profile-id", "   ", "--profiles-dir", str(profiles_dir)]
        )
    with pytest.raises(ValueError, match="surface_label must not be blank"):
        COCKPIT_EXPORT_REHEARSAL_CLI_COMMAND.args_parser(
            [
                "--profile-id",
                "scene-industrial",
                "--profiles-dir",
                str(profiles_dir),
                "--label",
                " ",
            ]
        )
    with pytest.raises(ValueError, match="key_id must not be blank"):
        COCKPIT_EXPORT_REHEARSAL_CLI_COMMAND.args_parser(
            [
                "--profile-id",
                "scene-industrial",
                "--profiles-dir",
                str(profiles_dir),
                "--key-id",
                " ",
            ]
        )
    with pytest.raises(ValueError, match="mutually exclusive"):
        COCKPIT_EXPORT_REHEARSAL_CLI_COMMAND.args_parser(
            [
                "--profile-id",
                "scene-industrial",
                "--profiles-dir",
                str(profiles_dir),
                "--unsigned",
                "--key-id",
                "k1",
            ]
        )
    with pytest.raises(ValueError, match="usage"):
        # Missing value for the option triggers the pop_option_value path.
        COCKPIT_EXPORT_REHEARSAL_CLI_COMMAND.args_parser(["--profile-id"])
    with pytest.raises(ValueError, match="usage"):
        COCKPIT_EXPORT_REHEARSAL_CLI_COMMAND.args_parser(["--profiles-dir"])
    with pytest.raises(ValueError, match="usage"):
        COCKPIT_EXPORT_REHEARSAL_CLI_COMMAND.args_parser(["--output"])


def test_cockpit_export_rehearsal_cli_handler_emits_text_and_json(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    from rytm_randomizer.cli import main

    profiles_dir = _scene_profiles_dir(tmp_path)

    rc = main(
        [
            "cockpit-export-rehearsal-report",
            "--profile-id",
            "scene-industrial",
            "--profiles-dir",
            str(profiles_dir),
            "--unsigned",
            "--label",
            "Warehouse export",
            "--json",
        ]
    )
    captured = capsys.readouterr()
    assert rc == 0
    payload = json.loads(captured.out)
    surface = payload["cockpit_export_rehearsal"]
    assert surface["surface_label"] == "Warehouse export"
    assert surface["signed"] is False
    assert captured.err == ""

    rc = main(
        [
            "cockpit-export-rehearsal-report",
            "--profile-id",
            "scene-hypnotic",
            "--profiles-dir",
            str(profiles_dir),
            "--key-id",
            "prod-ed25519",
        ]
    )
    captured = capsys.readouterr()
    assert rc == 0
    assert "Cockpit export rehearsal surface:" in captured.out
    assert "- Surface status: ready" in captured.out
    assert "- Signed: True" in captured.out
    assert captured.err == ""


def test_cockpit_export_rehearsal_cli_handler_type_validation(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    from rytm_randomizer.reports.cockpit_export_rehearsal import (
        COCKPIT_EXPORT_REHEARSAL_CLI_COMMAND,
    )

    profiles_dir = _scene_profiles_dir(tmp_path)

    rc = COCKPIT_EXPORT_REHEARSAL_CLI_COMMAND.handler(
        profile_id=12345,
        profiles_dir=profiles_dir,
    )
    captured = capsys.readouterr()
    assert rc == 2
    assert captured.out == ""
    assert "profile_id must be a string" in captured.err

    rc = COCKPIT_EXPORT_REHEARSAL_CLI_COMMAND.handler(
        profile_id="scene-industrial",
        profiles_dir="not-a-path",
    )
    captured = capsys.readouterr()
    assert rc == 2
    assert "profiles_dir must be a Path" in captured.err

    rc = COCKPIT_EXPORT_REHEARSAL_CLI_COMMAND.handler(
        profile_id="scene-industrial",
        profiles_dir=profiles_dir,
        key_id=42,
    )
    captured = capsys.readouterr()
    assert rc == 2
    assert "key_id must be a string when provided" in captured.err

    rc = COCKPIT_EXPORT_REHEARSAL_CLI_COMMAND.handler(
        profile_id="scene-industrial",
        profiles_dir=profiles_dir,
        unsigned="yes",
    )
    captured = capsys.readouterr()
    assert rc == 2
    assert "unsigned must be a bool" in captured.err

    rc = COCKPIT_EXPORT_REHEARSAL_CLI_COMMAND.handler(
        profile_id="scene-industrial",
        profiles_dir=profiles_dir,
        unsigned=True,
        output_path="/some/string/path",
    )
    captured = capsys.readouterr()
    assert rc == 2
    assert "output_path must be a Path when provided" in captured.err

    rc = COCKPIT_EXPORT_REHEARSAL_CLI_COMMAND.handler(
        profile_id="scene-industrial",
        profiles_dir=profiles_dir,
        unsigned=True,
        surface_label=object(),
    )
    captured = capsys.readouterr()
    assert rc == 2
    assert "surface_label must be a string" in captured.err

    # Surface ValueError from build (missing profile) goes through the handler.
    rc = COCKPIT_EXPORT_REHEARSAL_CLI_COMMAND.handler(
        profile_id="profile-not-found",
        profiles_dir=profiles_dir,
        unsigned=True,
    )
    captured = capsys.readouterr()
    assert rc == 2
    assert "not found in registry" in captured.err


# ---------------------------------------------------------------------------
# Passive import safety + help text
# ---------------------------------------------------------------------------


def test_cockpit_export_rehearsal_help_text_resolves() -> None:
    from rytm_randomizer.help_text import resolve_help_text

    help_text = resolve_help_text("cockpit-export-rehearsal-report")
    assert help_text.startswith("RytmRandomizer passive CLI: cockpit-export-rehearsal-report")
    assert "model-export rehearsal" in help_text
    assert "no MIDI sending" in help_text
    assert "does not invoke the signer or writer" in help_text


def test_cockpit_export_rehearsal_import_does_not_pull_real_midi() -> None:
    code = "\n".join(
        [
            "import sys",
            "import rytm_randomizer.reports.cockpit_export_rehearsal",
            f"forbidden = {FORBIDDEN_REAL_MIDI_AND_ADAPTER_MODULES!r}",
            "loaded = sorted(name for name in forbidden if name in sys.modules)",
            "if loaded:",
            "    print('\\n'.join(loaded))",
        ]
    )
    result = subprocess.run(
        [sys.executable, "-c", code],
        cwd=PROJECT_ROOT,
        text=True,
        capture_output=True,
        check=True,
    )
    assert result.stdout == ""


def test_cockpit_export_rehearsal_import_does_not_pull_export_side_effect_modules() -> None:
    code = "\n".join(
        [
            "import sys",
            "import rytm_randomizer.reports.cockpit_export_rehearsal",
            f"forbidden = {FORBIDDEN_EXPORT_SIDE_EFFECT_MODULES!r}",
            "loaded = sorted(name for name in forbidden if name in sys.modules)",
            "if loaded:",
            "    print('\\n'.join(loaded))",
        ]
    )
    result = subprocess.run(
        [sys.executable, "-c", code],
        cwd=PROJECT_ROOT,
        text=True,
        capture_output=True,
        check=True,
    )
    assert result.stdout == ""
