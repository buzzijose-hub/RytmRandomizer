"""Passive GUI-facing cockpit model-export rehearsal surface.

This report is the operator's pre-flight check before clicking EXPORT in
the cockpit GUI. It answers "what would actually get written?" for a
``ProfileModel`` resolved from a ``ProfileRegistry``:

* the output ``.rymp`` file path that would be written,
* the format and model versions that would land in the binary header,
* the packed payload size and CRC32 of the rehearsal blob,
* whether the export would be signed and (if so) the size of the signed
  envelope and the key-id label,
* and the GUI surface contract (panels, state bindings, action controls,
  acceptance checks, blocked actions, replay command) that mirrors PR
  #104's send-plan rehearsal surface shape so a single GUI consumer
  pattern can ingest both surfaces.

The report is **strictly passive** in the sense the cockpit means by that
word: no I/O writes, no port opens, no sidecar connection, no GUI launch,
no MIDI sending, no irreversible action of any kind. It is *not* "imports
nothing from ``cockpit.export``" — the rehearsal deliberately calls
:func:`~rytm_randomizer.cockpit.export.pack_profile_model` (pure compute:
MessagePack-encode plus CRC32) and
:func:`~rytm_randomizer.cockpit.export.signed_envelope_overhead_bytes`
(an analytic formula derived from the wire layout) so the rehearsal can
report the exact would-write size without having to invoke the signer or
the writer. Both calls have no side effects.

The Phase 3 keystore is not yet available; the ``--key-id`` option
therefore travels as a metadata label only — actual key lookup is
deferred to Phase 3.5.
"""

from __future__ import annotations

import hashlib
import json
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Final, Literal

from ..cli_registry import CliCommand, register
from ..cockpit.data import ProfileModel
from ..cockpit.export import (
    FORMAT_VERSION,
    SIGNATURE_ALGO_HMAC_SHA256,
    pack_profile_model,
    signed_envelope_overhead_bytes,
)
from ..cockpit.export.model_format import compute_crc
from ..cockpit.profiles import ProfileRegistry, default_profiles_dir
from .formatter import (
    SAFETY_SECTION_HEADER,
    PassiveReportHeader,
    passive_report_lines,
    powershell_literal_arg,
)
from .live_gui_common import format_cli_error as _format_cli_error
from .live_gui_common import pop_option_value, status_severity

REPORT_TITLE: Final[str] = "RytmRandomizer passive cockpit export rehearsal surface"
SOURCE_MODULE: Final[str] = "reports.cockpit_export_rehearsal"
EXPORT_REHEARSAL_SURFACE_VERSION: Final[str] = "cockpit-export-rehearsal-surface-v1"
_DEFAULT_SURFACE_LABEL: Final[str] = "Cockpit export rehearsal surface"
_COMMAND_NAME: Final[str] = "cockpit-export-rehearsal-report"
_OUTPUT_EXTENSION: Final[str] = ".rymp"
_DEFAULT_OUTPUT_DIR: Final[Path] = Path("~/.rytm-randomizer/exports")

SAFETY_LINES: Final[tuple[str, ...]] = (
    "passive/read-only",
    "GUI-facing export rehearsal metadata only",
    "consumes ProfileModel registry + pack_profile_model only",
    "action controls are declarative and disabled",
    "state bindings are declarative metadata only",
    "does not write any file",
    "does not invoke the signer or verifier",
    "does not invoke the export writer",
    "does not connect to cockpit sidecar",
    "does not open a WebSocket",
    "does not launch GUI",
    "does not launch app",
    "does not dispatch GUI actions",
    "does not mutate GUI state stores",
    "JSON/stdout only",
    "path options are read-only inputs",
    "no MIDI sending",
    "no port opening",
    "no hardware mutation",
    "no hardware required",
)

_HEADER: Final[PassiveReportHeader] = PassiveReportHeader(
    title=REPORT_TITLE,
    source_module=SOURCE_MODULE,
)
_USAGE: Final[str] = (
    "cockpit-export-rehearsal-report usage: "
    "--profile-id <id> --profiles-dir <path> "
    "[--key-id <label>] [--unsigned] [--output <path>] [--json]"
)

SurfaceStatus = Literal["ready", "blocked"]
ScreenState = Literal["export-ready-review", "review-required", "disabled"]
SendControlState = Literal["ready", "disabled", "review-required"]


@dataclass(frozen=True)
class CockpitExportRehearsalPanel:
    """One GUI-facing panel for export rehearsal."""

    panel_key: str
    label: str
    status: str
    severity: str
    source_key: str
    summary: str
    value_text: str
    passive: bool


@dataclass(frozen=True)
class CockpitExportRehearsalStateBinding:
    """One future GUI state binding for export rehearsal."""

    state_key: str
    source_json_key: str
    label: str
    value: str
    required: bool
    passive: bool


@dataclass(frozen=True)
class CockpitExportRehearsalActionControl:
    """One disabled future GUI action control."""

    action_key: str
    label: str
    control_state: str
    gate_status: str
    enabled: bool
    bound_state_key: str
    blocked_reason: str
    operator_action: str
    passive: bool


@dataclass(frozen=True)
class CockpitExportRehearsalSurfaceCheck:
    """One passive acceptance check for the rehearsal surface."""

    check_key: str
    label: str
    status: str
    severity: str
    source_id: str
    message: str
    operator_action: str
    passive: bool


@dataclass(frozen=True)
class CockpitExportRehearsalSurfaceReport:
    """Passive GUI-ready state describing one rehearsed model export."""

    surface_version: str
    surface_id: str
    surface_label: str
    profile_id: str
    profile_name: str
    profile_kind: str
    model_version: str
    format_version: int
    output_path: str
    payload_size: int
    payload_crc_hex: str
    signed: bool
    key_id: str | None
    signed_size: int | None
    surface_status: SurfaceStatus
    screen_state: ScreenState
    send_control_state: SendControlState
    primary_operator_action: str
    panels: tuple[CockpitExportRehearsalPanel, ...]
    state_bindings: tuple[CockpitExportRehearsalStateBinding, ...]
    action_controls: tuple[CockpitExportRehearsalActionControl, ...]
    surface_checks: tuple[CockpitExportRehearsalSurfaceCheck, ...]
    blocked_actions: tuple[str, ...]
    blocked_reasons: tuple[str, ...]
    replay_command: str


# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------


def _normalize_nonblank(value: str, *, field: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field} must not be blank")
    return normalized


def _default_output_path(profile_id: str, model_version: str) -> Path:
    return _DEFAULT_OUTPUT_DIR.expanduser() / f"{profile_id}-v{model_version}{_OUTPUT_EXTENSION}"


def _surface_id(
    *,
    profile_id: str,
    model_version: str,
    output_path: str,
    payload_crc_hex: str,
    signed: bool,
    key_id: str | None,
    surface_label: str,
) -> str:
    payload = "|".join(
        (
            EXPORT_REHEARSAL_SURFACE_VERSION,
            profile_id,
            model_version,
            output_path,
            payload_crc_hex,
            "signed" if signed else "unsigned",
            key_id or "",
            surface_label,
        )
    )
    return f"export-surface-{hashlib.sha256(payload.encode('utf-8')).hexdigest()[:16]}"


# ---------------------------------------------------------------------------
# Panels / bindings / controls / checks builders
# ---------------------------------------------------------------------------


def _panel(
    *,
    panel_key: str,
    label: str,
    status: str,
    source_key: str,
    summary: str,
    value_text: str,
) -> CockpitExportRehearsalPanel:
    return CockpitExportRehearsalPanel(
        panel_key=panel_key,
        label=label,
        status=status,
        severity=status_severity(status),
        source_key=source_key,
        summary=summary,
        value_text=value_text,
        passive=True,
    )


def _panels(
    *,
    profile: ProfileModel,
    output_path: str,
    payload_size: int,
    payload_crc_hex: str,
    signed: bool,
    key_id: str | None,
    signed_size: int | None,
    surface_status: SurfaceStatus,
    blocked_reasons: tuple[str, ...],
) -> tuple[CockpitExportRehearsalPanel, ...]:
    signing_status = "ready" if signed else "ready"
    signing_summary = (
        f"signed envelope: {signed_size} bytes (key {key_id})"
        if signed
        else "unsigned export (no key-id provided)"
    )
    signing_value_text = (
        f"key_id={key_id} signed_size={signed_size}"
        if signed
        else "key_id=<none> signed_size=<n/a>"
    )
    payload_panel_status = "ready" if payload_size > 0 else "blocked"
    blocked_text = ", ".join(blocked_reasons) or "none"
    return (
        _panel(
            panel_key="summary",
            label="Export summary",
            status=surface_status,
            source_key="cockpit_export_rehearsal",
            summary=(f"{profile.profile_id} v{profile.model_version} is {surface_status}"),
            value_text=(
                f"profile_kind={profile.kind} signed={signed} " f"blocked_reasons={blocked_text}"
            ),
        ),
        _panel(
            panel_key="output-path",
            label="Output path",
            status="ready",
            source_key="output_path",
            summary="Would-write file path",
            value_text=output_path,
        ),
        _panel(
            panel_key="payload",
            label="Packed payload",
            status=payload_panel_status,
            source_key="pack_profile_model",
            summary=f"{payload_size} bytes packed",
            value_text=f"crc32=0x{payload_crc_hex} format_version={FORMAT_VERSION}",
        ),
        _panel(
            panel_key="signing",
            label="Signing status",
            status=signing_status,
            source_key="signing",
            summary=signing_summary,
            value_text=signing_value_text,
        ),
        _panel(
            panel_key="safety-locks",
            label="Passive safety locks",
            status="ready",
            source_key="blocked_actions",
            summary="Export action remains disabled in this rehearsal",
            value_text=("no writer, no signer, no verifier, no sidecar, no MIDI"),
        ),
    )


def _binding(
    *,
    state_key: str,
    source_json_key: str,
    label: str,
    value: str,
) -> CockpitExportRehearsalStateBinding:
    return CockpitExportRehearsalStateBinding(
        state_key=state_key,
        source_json_key=source_json_key,
        label=label,
        value=value,
        required=True,
        passive=True,
    )


def _state_bindings(
    *,
    profile: ProfileModel,
    output_path: str,
    payload_size: int,
    payload_crc_hex: str,
    signed: bool,
    key_id: str | None,
    signed_size: int | None,
    surface_status: SurfaceStatus,
    screen_state: ScreenState,
    send_control_state: SendControlState,
) -> tuple[CockpitExportRehearsalStateBinding, ...]:
    return (
        _binding(
            state_key="cockpit.export.status",
            source_json_key="cockpit_export_rehearsal.surface_status",
            label="Export rehearsal status",
            value=surface_status,
        ),
        _binding(
            state_key="cockpit.export.screenState",
            source_json_key="cockpit_export_rehearsal.screen_state",
            label="Screen state",
            value=screen_state,
        ),
        _binding(
            state_key="cockpit.export.send",
            source_json_key="cockpit_export_rehearsal.send_control_state",
            label="EXPORT control state",
            value=send_control_state,
        ),
        _binding(
            state_key="cockpit.export.profileId",
            source_json_key="cockpit_export_rehearsal.profile_id",
            label="Profile id",
            value=profile.profile_id,
        ),
        _binding(
            state_key="cockpit.export.modelVersion",
            source_json_key="cockpit_export_rehearsal.model_version",
            label="Model version",
            value=profile.model_version,
        ),
        _binding(
            state_key="cockpit.export.outputPath",
            source_json_key="cockpit_export_rehearsal.output_path",
            label="Output path",
            value=output_path,
        ),
        _binding(
            state_key="cockpit.export.payloadSize",
            source_json_key="cockpit_export_rehearsal.payload_size",
            label="Payload size",
            value=str(payload_size),
        ),
        _binding(
            state_key="cockpit.export.payloadCrcHex",
            source_json_key="cockpit_export_rehearsal.payload_crc_hex",
            label="Payload CRC32 (hex)",
            value=payload_crc_hex,
        ),
        _binding(
            state_key="cockpit.export.signed",
            source_json_key="cockpit_export_rehearsal.signed",
            label="Signed",
            value=str(signed),
        ),
        _binding(
            state_key="cockpit.export.keyId",
            source_json_key="cockpit_export_rehearsal.key_id",
            label="Key id",
            value=key_id or "none",
        ),
        _binding(
            state_key="cockpit.export.signedSize",
            source_json_key="cockpit_export_rehearsal.signed_size",
            label="Signed envelope size",
            value="none" if signed_size is None else str(signed_size),
        ),
    )


def _action_controls(
    *,
    surface_status: SurfaceStatus,
    send_control_state: SendControlState,
    primary_operator_action: str,
) -> tuple[CockpitExportRehearsalActionControl, ...]:
    return (
        CockpitExportRehearsalActionControl(
            action_key="export",
            label="EXPORT",
            control_state=send_control_state,
            gate_status=surface_status,
            enabled=False,
            bound_state_key="cockpit.export.send",
            blocked_reason="passive report; EXPORT requires the armed cockpit runtime",
            operator_action=primary_operator_action,
            passive=True,
        ),
        CockpitExportRehearsalActionControl(
            action_key="sign",
            label="SIGN",
            control_state="sidecar-required",
            gate_status="ready",
            enabled=False,
            bound_state_key="cockpit.export.signed",
            blocked_reason="passive report does not call the signer",
            operator_action="Use the armed cockpit sidecar to invoke the signer.",
            passive=True,
        ),
        CockpitExportRehearsalActionControl(
            action_key="review-rehearsal",
            label="REVIEW",
            control_state="display-only",
            gate_status="ready",
            enabled=False,
            bound_state_key="cockpit.export.outputPath",
            blocked_reason="passive metadata only; no GUI action dispatch",
            operator_action="Review the displayed output path, payload size, and CRC.",
            passive=True,
        ),
    )


def _surface_check(
    *,
    check_key: str,
    label: str,
    status: str,
    source_id: str,
    message: str,
    operator_action: str,
) -> CockpitExportRehearsalSurfaceCheck:
    return CockpitExportRehearsalSurfaceCheck(
        check_key=check_key,
        label=label,
        status=status,
        severity=status_severity(status),
        source_id=source_id,
        message=message,
        operator_action=operator_action,
        passive=True,
    )


def _surface_checks(
    *,
    profile: ProfileModel,
    output_path: str,
    payload_size: int,
    surface_status: SurfaceStatus,
    panels: tuple[CockpitExportRehearsalPanel, ...],
    state_bindings: tuple[CockpitExportRehearsalStateBinding, ...],
    action_controls: tuple[CockpitExportRehearsalActionControl, ...],
    blocked_reasons: tuple[str, ...],
) -> tuple[CockpitExportRehearsalSurfaceCheck, ...]:
    export_control = action_controls[0]
    parent_status = "ready" if Path(output_path).expanduser().parent.exists() else ("review-needed")
    parent_message = (
        f"Output parent directory exists: {Path(output_path).expanduser().parent}"
        if parent_status == "ready"
        else (
            "Output parent directory does not exist; the export CLI would create it: "
            f"{Path(output_path).expanduser().parent}"
        )
    )
    blocked_text = ", ".join(blocked_reasons) or "none"
    return (
        _surface_check(
            check_key="assert-profile-resolved",
            label="Profile resolved",
            status=surface_status,
            source_id=profile.profile_id,
            message=(
                f"Profile {profile.profile_id} v{profile.model_version} loaded from registry."
            ),
            operator_action="Inspect the profile id and model version before exporting.",
        ),
        _surface_check(
            check_key="assert-payload-packed",
            label="Payload packed",
            status="ready" if payload_size > 0 else "blocked",
            source_id=profile.profile_id,
            message=f"pack_profile_model produced {payload_size} bytes.",
            operator_action="Confirm payload size matches profile expectations.",
        ),
        _surface_check(
            check_key="assert-output-parent-exists",
            label="Output parent directory",
            status=parent_status,
            source_id=output_path,
            message=parent_message,
            operator_action=("The active export CLI will create the parent directory when armed."),
        ),
        _surface_check(
            check_key="assert-panel-coverage",
            label="GUI panel coverage",
            status="ready" if panels else "blocked",
            source_id=profile.profile_id,
            message=f"{len(panels)} GUI-facing panels are available.",
            operator_action=("Keep panels display-only until the armed GUI runtime consumes them."),
        ),
        _surface_check(
            check_key="assert-state-binding-coverage",
            label="GUI state binding coverage",
            status="ready" if state_bindings else "blocked",
            source_id=profile.profile_id,
            message=(f"{len(state_bindings)} declarative state bindings are available."),
            operator_action="Do not mutate GUI stores from passive CLI reports.",
        ),
        _surface_check(
            check_key="assert-export-action-gated",
            label="EXPORT action gate",
            status=export_control.gate_status,
            source_id=profile.profile_id,
            message=(
                f"EXPORT control is {export_control.control_state} and disabled " "in this report."
            ),
            operator_action=export_control.operator_action,
        ),
        _surface_check(
            check_key="assert-blocked-reasons",
            label="Blocked reasons",
            status="blocked" if blocked_reasons else "ready",
            source_id=profile.profile_id,
            message=f"Blocked reasons: {blocked_text}.",
            operator_action=("Resolve the listed reasons before clicking EXPORT in the cockpit."),
        ),
        _surface_check(
            check_key="assert-passive-boundary",
            label="Passive boundary",
            status="ready",
            source_id=profile.profile_id,
            message="Rehearsal surface emits metadata only.",
            operator_action=(
                "Do not launch GUI, open ports, connect sidecar, send MIDI, "
                "or write files from this report."
            ),
        ),
    )


def _blocked_actions(*, surface_status: SurfaceStatus) -> tuple[str, ...]:
    actions: list[str] = []
    if surface_status == "blocked":
        actions.append("EXPORT remains disabled until the cockpit resolves the listed blockers")
    actions.extend(
        (
            "no .rymp file write",
            "no signer invocation",
            "no verifier invocation",
            "no export writer invocation",
            "no cockpit sidecar connection",
            "no WebSocket opening",
            "no GUI launch",
            "no app launch",
            "no GUI action dispatch",
            "no GUI state-store mutation",
        )
    )
    return tuple(actions)


def _replay_command(
    *,
    profile_id: str,
    profiles_dir: Path,
    output_path: str,
    signed: bool,
    key_id: str | None,
    json_output: bool,
) -> str:
    pieces: list[str] = [
        f"python -m rytm_randomizer.cli {_COMMAND_NAME}",
        "--profile-id",
        powershell_literal_arg(profile_id),
        "--profiles-dir",
        powershell_literal_arg(str(profiles_dir)),
        "--output",
        powershell_literal_arg(output_path),
    ]
    if signed and key_id is not None:
        pieces.extend(("--key-id", powershell_literal_arg(key_id)))
    else:
        pieces.append("--unsigned")
    if json_output:
        pieces.append("--json")
    return " ".join(pieces)


def _resolve_profile(profile_id: str, profiles_dir: Path) -> ProfileModel:
    registry = ProfileRegistry(profiles_dir)
    profile = registry.get(profile_id)
    if profile is None:
        raise ValueError(f"profile {profile_id!r} not found in registry at {profiles_dir}")
    return profile


def _resolve_signing(*, key_id: str | None, unsigned: bool) -> tuple[bool, str | None]:
    if unsigned and key_id is not None:
        raise ValueError("--unsigned and --key-id are mutually exclusive")
    if key_id is not None:
        return True, _normalize_nonblank(key_id, field="key_id")
    return False, None


def _compute_payload(profile: ProfileModel) -> tuple[bytes, str]:
    payload = pack_profile_model(profile)
    crc = compute_crc(payload)
    return payload, f"{crc:08x}"


def _resolve_output_path(
    *,
    profile: ProfileModel,
    explicit_output: Path | None,
) -> str:
    if explicit_output is not None:
        return str(explicit_output)
    return str(_default_output_path(profile.profile_id, profile.model_version))


def _signed_size(payload_size: int, *, key_id: str) -> int:
    """Return the exact would-write size of a signed envelope.

    Composes the analytic
    :func:`~rytm_randomizer.cockpit.export.signed_envelope_overhead_bytes`
    with the rehearsal's already-computed ``payload_size`` so the report
    surfaces the same byte count the real
    :func:`~rytm_randomizer.cockpit.export.pack_signed` would later emit
    — no estimate, no upper-bound padding, no guessing.
    """

    overhead = signed_envelope_overhead_bytes(
        algo=SIGNATURE_ALGO_HMAC_SHA256,
        key_id=key_id,
    )
    return payload_size + overhead


def _surface_status_and_screen(
    *,
    blocked_reasons: tuple[str, ...],
) -> tuple[SurfaceStatus, ScreenState, SendControlState]:
    if blocked_reasons:
        return "blocked", "disabled", "disabled"
    return "ready", "export-ready-review", "ready"


def _primary_operator_action(
    *,
    surface_status: SurfaceStatus,
    signed: bool,
) -> str:
    if surface_status == "blocked":
        return "Resolve the listed blocked reasons before re-running the export rehearsal."
    if signed:
        return (
            "Review the would-write path and signed envelope size, then click "
            "EXPORT in the cockpit GUI."
        )
    return (
        "Review the would-write path and packed payload size, then click EXPORT "
        "in the cockpit GUI."
    )


# ---------------------------------------------------------------------------
# Builder
# ---------------------------------------------------------------------------


def build_cockpit_export_rehearsal_report(
    *,
    profile_id: str,
    profiles_dir: Path,
    key_id: str | None = None,
    unsigned: bool = False,
    output_path: Path | None = None,
    surface_label: str = _DEFAULT_SURFACE_LABEL,
    json_output: bool = False,
    additional_blocked_reasons: tuple[str, ...] = (),
) -> CockpitExportRehearsalSurfaceReport:
    """Build the passive cockpit model-export rehearsal surface.

    ``additional_blocked_reasons`` is a testing/integration seam for the
    Phase 3.5 keystore wrapper (and tests): callers that detect a missing
    signing key, an unreadable keystore, or any future export-blocker can
    pass the reason strings here and the rehearsal surface will switch to
    the ``blocked`` shape (status, screen state, send control, panels, and
    blocked actions) without raising.
    """

    normalized_label = _normalize_nonblank(surface_label, field="surface_label")
    signed, resolved_key_id = _resolve_signing(key_id=key_id, unsigned=unsigned)
    profile = _resolve_profile(profile_id, profiles_dir)
    payload, payload_crc_hex = _compute_payload(profile)
    payload_size = len(payload)
    signed_size = (
        _signed_size(payload_size, key_id=resolved_key_id)
        if signed and resolved_key_id is not None
        else None
    )
    resolved_output_path = _resolve_output_path(
        profile=profile,
        explicit_output=output_path,
    )

    blocked_reasons: tuple[str, ...] = tuple(additional_blocked_reasons)
    surface_status, screen_state, send_control_state = _surface_status_and_screen(
        blocked_reasons=blocked_reasons,
    )
    primary_operator_action = _primary_operator_action(
        surface_status=surface_status,
        signed=signed,
    )

    panels = _panels(
        profile=profile,
        output_path=resolved_output_path,
        payload_size=payload_size,
        payload_crc_hex=payload_crc_hex,
        signed=signed,
        key_id=resolved_key_id,
        signed_size=signed_size,
        surface_status=surface_status,
        blocked_reasons=blocked_reasons,
    )
    state_bindings = _state_bindings(
        profile=profile,
        output_path=resolved_output_path,
        payload_size=payload_size,
        payload_crc_hex=payload_crc_hex,
        signed=signed,
        key_id=resolved_key_id,
        signed_size=signed_size,
        surface_status=surface_status,
        screen_state=screen_state,
        send_control_state=send_control_state,
    )
    action_controls = _action_controls(
        surface_status=surface_status,
        send_control_state=send_control_state,
        primary_operator_action=primary_operator_action,
    )
    checks = _surface_checks(
        profile=profile,
        output_path=resolved_output_path,
        payload_size=payload_size,
        surface_status=surface_status,
        panels=panels,
        state_bindings=state_bindings,
        action_controls=action_controls,
        blocked_reasons=blocked_reasons,
    )
    blocked_actions = _blocked_actions(surface_status=surface_status)
    replay_command = _replay_command(
        profile_id=profile.profile_id,
        profiles_dir=profiles_dir,
        output_path=resolved_output_path,
        signed=signed,
        key_id=resolved_key_id,
        json_output=json_output,
    )

    return CockpitExportRehearsalSurfaceReport(
        surface_version=EXPORT_REHEARSAL_SURFACE_VERSION,
        surface_id=_surface_id(
            profile_id=profile.profile_id,
            model_version=profile.model_version,
            output_path=resolved_output_path,
            payload_crc_hex=payload_crc_hex,
            signed=signed,
            key_id=resolved_key_id,
            surface_label=normalized_label,
        ),
        surface_label=normalized_label,
        profile_id=profile.profile_id,
        profile_name=profile.name,
        profile_kind=profile.kind,
        model_version=profile.model_version,
        format_version=FORMAT_VERSION,
        output_path=resolved_output_path,
        payload_size=payload_size,
        payload_crc_hex=payload_crc_hex,
        signed=signed,
        key_id=resolved_key_id,
        signed_size=signed_size,
        surface_status=surface_status,
        screen_state=screen_state,
        send_control_state=send_control_state,
        primary_operator_action=primary_operator_action,
        panels=panels,
        state_bindings=state_bindings,
        action_controls=action_controls,
        surface_checks=checks,
        blocked_actions=blocked_actions,
        blocked_reasons=blocked_reasons,
        replay_command=replay_command,
    )


# ---------------------------------------------------------------------------
# JSON / text formatters
# ---------------------------------------------------------------------------


def _panel_json(panel: CockpitExportRehearsalPanel) -> dict[str, object]:
    return {
        "panel_key": panel.panel_key,
        "label": panel.label,
        "status": panel.status,
        "severity": panel.severity,
        "source_key": panel.source_key,
        "summary": panel.summary,
        "value_text": panel.value_text,
        "passive": panel.passive,
    }


def _binding_json(binding: CockpitExportRehearsalStateBinding) -> dict[str, object]:
    return {
        "state_key": binding.state_key,
        "source_json_key": binding.source_json_key,
        "label": binding.label,
        "value": binding.value,
        "required": binding.required,
        "passive": binding.passive,
    }


def _action_control_json(
    control: CockpitExportRehearsalActionControl,
) -> dict[str, object]:
    return {
        "action_key": control.action_key,
        "label": control.label,
        "control_state": control.control_state,
        "gate_status": control.gate_status,
        "enabled": control.enabled,
        "bound_state_key": control.bound_state_key,
        "blocked_reason": control.blocked_reason,
        "operator_action": control.operator_action,
        "passive": control.passive,
    }


def _surface_check_json(
    check: CockpitExportRehearsalSurfaceCheck,
) -> dict[str, object]:
    return {
        "check_key": check.check_key,
        "label": check.label,
        "status": check.status,
        "severity": check.severity,
        "source_id": check.source_id,
        "message": check.message,
        "operator_action": check.operator_action,
        "passive": check.passive,
    }


def to_cockpit_export_rehearsal_json(
    report: CockpitExportRehearsalSurfaceReport,
) -> dict[str, object]:
    """Return deterministic JSON for a passive export rehearsal surface."""

    return {
        "cockpit_export_rehearsal": {
            "surface_version": report.surface_version,
            "surface_id": report.surface_id,
            "surface_label": report.surface_label,
            "surface_status": report.surface_status,
            "screen_state": report.screen_state,
            "send_control_state": report.send_control_state,
            "primary_operator_action": report.primary_operator_action,
            "profile_id": report.profile_id,
            "profile_name": report.profile_name,
            "profile_kind": report.profile_kind,
            "model_version": report.model_version,
            "format_version": report.format_version,
            "output_path": report.output_path,
            "payload_size": report.payload_size,
            "payload_crc_hex": report.payload_crc_hex,
            "signed": report.signed,
            "key_id": report.key_id,
            "signed_size": report.signed_size,
            "blocked_reasons": list(report.blocked_reasons),
            "panels": [_panel_json(panel) for panel in report.panels],
            "state_bindings": [_binding_json(binding) for binding in report.state_bindings],
            "action_controls": [
                _action_control_json(control) for control in report.action_controls
            ],
            "surface_checks": [_surface_check_json(check) for check in report.surface_checks],
            "blocked_actions": list(report.blocked_actions),
            "replay_command": report.replay_command,
        },
        "safety": list(SAFETY_LINES),
    }


def _panel_lines(panel: CockpitExportRehearsalPanel) -> list[str]:
    return [
        f"- {panel.panel_key}: {panel.label}",
        f"  Status: {panel.status}",
        f"  Severity: {panel.severity}",
        f"  Source: {panel.source_key}",
        f"  Summary: {panel.summary}",
        f"  Value: {panel.value_text}",
        f"  Passive: {panel.passive}",
    ]


def _binding_lines(binding: CockpitExportRehearsalStateBinding) -> list[str]:
    return [
        f"- {binding.state_key}: {binding.label}",
        f"  Source JSON: {binding.source_json_key}",
        f"  Value: {binding.value}",
        f"  Required: {binding.required}",
        f"  Passive: {binding.passive}",
    ]


def _action_control_lines(control: CockpitExportRehearsalActionControl) -> list[str]:
    return [
        f"- {control.action_key}: {control.label}",
        f"  Control state: {control.control_state}",
        f"  Gate status: {control.gate_status}",
        f"  Enabled: {control.enabled}",
        f"  Bound state: {control.bound_state_key}",
        f"  Blocked reason: {control.blocked_reason}",
        f"  Operator action: {control.operator_action}",
        f"  Passive: {control.passive}",
    ]


def _surface_check_lines(check: CockpitExportRehearsalSurfaceCheck) -> list[str]:
    return [
        f"- {check.check_key}: {check.label}",
        f"  Status: {check.status}",
        f"  Severity: {check.severity}",
        f"  Source id: {check.source_id}",
        f"  Message: {check.message}",
        f"  Operator action: {check.operator_action}",
        f"  Passive: {check.passive}",
    ]


def format_cockpit_export_rehearsal_report(
    report: CockpitExportRehearsalSurfaceReport,
) -> list[str]:
    """Format a passive cockpit export rehearsal surface."""

    signed_size_text = "n/a" if report.signed_size is None else str(report.signed_size)
    key_id_text = report.key_id or "none"
    blocked_reasons_text = ", ".join(report.blocked_reasons) or "none"
    lines = [
        "Cockpit export rehearsal surface:",
        f"- Surface id: {report.surface_id}",
        f"- Surface label: {report.surface_label}",
        f"- Surface status: {report.surface_status}",
        f"- Screen state: {report.screen_state}",
        f"- EXPORT control state: {report.send_control_state}",
        f"- Primary operator action: {report.primary_operator_action}",
        f"- Profile id: {report.profile_id}",
        f"- Profile name: {report.profile_name}",
        f"- Profile kind: {report.profile_kind}",
        f"- Model version: {report.model_version}",
        f"- Format version: {report.format_version}",
        f"- Output path: {report.output_path}",
        f"- Payload size: {report.payload_size}",
        f"- Payload CRC32: 0x{report.payload_crc_hex}",
        f"- Signed: {report.signed}",
        f"- Key id: {key_id_text}",
        f"- Signed envelope size: {signed_size_text}",
        f"- Blocked reasons: {blocked_reasons_text}",
        "GUI panels:",
    ]
    for panel in report.panels:
        lines.extend(_panel_lines(panel))
    lines.append("State bindings:")
    for binding in report.state_bindings:
        lines.extend(_binding_lines(binding))
    lines.append("Action controls:")
    for control in report.action_controls:
        lines.extend(_action_control_lines(control))
    lines.append("Surface checks:")
    for check in report.surface_checks:
        lines.extend(_surface_check_lines(check))
    lines.extend(
        [
            "Blocked active actions:",
            *[f"- {action}" for action in report.blocked_actions],
            "Replayable passive command:",
            f"- {report.replay_command}",
            SAFETY_SECTION_HEADER,
            *[f"- {line}" for line in SAFETY_LINES],
        ]
    )
    return passive_report_lines(_HEADER, lines)


# ---------------------------------------------------------------------------
# CLI argument parser + handler
# ---------------------------------------------------------------------------


def _pop_option_value(remaining: list[str]) -> str:
    return pop_option_value(remaining, usage=_USAGE)


def parse_cockpit_export_rehearsal_cli_args(
    argv: Sequence[str],
) -> dict[str, object]:
    """Parse passive cockpit export rehearsal CLI args."""

    profile_id: str | None = None
    profiles_dir: Path | None = None
    key_id: str | None = None
    unsigned = False
    output_path: Path | None = None
    surface_label = _DEFAULT_SURFACE_LABEL
    json_output = False
    remaining = list(argv)
    while remaining:
        option = remaining.pop(0)
        if option == "--json":
            json_output = True
        elif option == "--unsigned":
            unsigned = True
        elif option == "--profile-id":
            profile_id = _normalize_nonblank(
                _pop_option_value(remaining),
                field="profile_id",
            )
        elif option == "--profiles-dir":
            profiles_dir = Path(_pop_option_value(remaining))
        elif option == "--key-id":
            key_id = _normalize_nonblank(
                _pop_option_value(remaining),
                field="key_id",
            )
        elif option == "--output":
            output_path = Path(_pop_option_value(remaining))
        elif option == "--label":
            surface_label = _normalize_nonblank(
                _pop_option_value(remaining),
                field="surface_label",
            )
        else:
            raise ValueError(_USAGE)
    if profile_id is None:
        raise ValueError("--profile-id is required")
    if profiles_dir is None:
        # Mirror the default the cockpit uses at runtime so the rehearsal
        # CLI matches what the operator would see in the GUI by default.
        profiles_dir = default_profiles_dir()
    if unsigned and key_id is not None:
        raise ValueError("--unsigned and --key-id are mutually exclusive")
    return {
        "profile_id": profile_id,
        "profiles_dir": profiles_dir,
        "key_id": key_id,
        "unsigned": unsigned,
        "output_path": output_path,
        "surface_label": surface_label,
        "json_output": json_output,
    }


def _handle_cli_report(
    *,
    profile_id: object,
    profiles_dir: object,
    key_id: object = None,
    unsigned: object = False,
    output_path: object = None,
    surface_label: object = _DEFAULT_SURFACE_LABEL,
    json_output: object = False,
) -> int:
    try:
        if not isinstance(profile_id, str):
            raise TypeError("profile_id must be a string")
        if not isinstance(profiles_dir, Path):
            raise TypeError("profiles_dir must be a Path")
        if key_id is not None and not isinstance(key_id, str):
            raise TypeError("key_id must be a string when provided")
        if not isinstance(unsigned, bool):
            raise TypeError("unsigned must be a bool")
        if output_path is not None and not isinstance(output_path, Path):
            raise TypeError("output_path must be a Path when provided")
        if not isinstance(surface_label, str):
            raise TypeError("surface_label must be a string")
        report = build_cockpit_export_rehearsal_report(
            profile_id=profile_id,
            profiles_dir=profiles_dir,
            key_id=key_id,
            unsigned=unsigned,
            output_path=output_path,
            surface_label=surface_label,
            json_output=bool(json_output),
        )
        if json_output is True:
            sys.stdout.write(
                json.dumps(
                    to_cockpit_export_rehearsal_json(report),
                    indent=2,
                    sort_keys=True,
                )
            )
            sys.stdout.write("\n")
            return 0
        lines = format_cockpit_export_rehearsal_report(report)
    except (OSError, ValueError, RuntimeError, NotImplementedError, TypeError, KeyError) as exc:
        sys.stderr.write(f"Error: {exc}\n")
        return 2
    for line in lines:
        sys.stdout.write(f"{line}\n")
    return 0


COCKPIT_EXPORT_REHEARSAL_CLI_COMMAND: Final[CliCommand] = CliCommand(
    name=_COMMAND_NAME,
    summary="Build passive GUI-facing cockpit model-export rehearsal state.",
    args_parser=parse_cockpit_export_rehearsal_cli_args,
    handler=_handle_cli_report,
    error_formatter=_format_cli_error,
)

register(COCKPIT_EXPORT_REHEARSAL_CLI_COMMAND)

__all__ = [
    "COCKPIT_EXPORT_REHEARSAL_CLI_COMMAND",
    "EXPORT_REHEARSAL_SURFACE_VERSION",
    "REPORT_TITLE",
    "SAFETY_LINES",
    "SOURCE_MODULE",
    "CockpitExportRehearsalActionControl",
    "CockpitExportRehearsalPanel",
    "CockpitExportRehearsalStateBinding",
    "CockpitExportRehearsalSurfaceCheck",
    "CockpitExportRehearsalSurfaceReport",
    "build_cockpit_export_rehearsal_report",
    "format_cockpit_export_rehearsal_report",
    "parse_cockpit_export_rehearsal_cli_args",
    "to_cockpit_export_rehearsal_json",
]
