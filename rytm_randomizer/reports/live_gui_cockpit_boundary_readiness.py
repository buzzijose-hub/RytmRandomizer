"""Passive live GUI cockpit boundary-readiness report."""

from __future__ import annotations

import hashlib
import json
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Final

from ..cli_registry import CliCommand, register
from .formatter import (
    SAFETY_SECTION_HEADER,
    PassiveReportHeader,
    passive_report_lines,
)
from .live_gui_common import format_cli_error as _format_cli_error
from .live_gui_common import pop_option_value, replace_replay_command, status_severity
from .live_gui_desktop_render_harness import (
    StylePerformanceArcLiveGuiDesktopRenderHarnessReport,
    build_style_performance_arc_live_gui_desktop_render_harness_report,
    parse_style_performance_arc_live_gui_desktop_render_harness_cli_args,
    to_style_performance_arc_live_gui_desktop_render_harness_json,
)

REPORT_TITLE: Final[str] = (
    "RytmRandomizer passive style performance arc live GUI cockpit boundary readiness"
)
SOURCE_MODULE: Final[str] = "reports.live_gui_cockpit_boundary_readiness"
BOUNDARY_READINESS_VERSION: Final[str] = "live-gui-cockpit-boundary-readiness-v1"
_DEFAULT_BOUNDARY_LABEL: Final[str] = "Live GUI cockpit boundary readiness"
_DEFAULT_HARDWARE_ENTRYPOINT: Final[str] = "python -m rytm_randomizer.app --arm"
_DEFAULT_PASSIVE_ENTRYPOINT: Final[str] = "python -m rytm_randomizer.cli"
_DEFAULT_WS_PORT_ENV: Final[str] = "RYTM_RAND_WS_PORT"
SAFETY_LINES: Final[tuple[str, ...]] = (
    "passive/read-only",
    "Passive GUI cockpit boundary-readiness metadata only",
    "consumes live GUI desktop render-harness metadata only",
    "active hardware remains app --arm only",
    "passive CLI remains python -m rytm_randomizer.cli only",
    "Rytm 12-pad scope is explicit",
    "Analog Four 4-track scope is explicit",
    "future cockpit sidecar only",
    "future Tauri/web shell only",
    "future audio analyzer comparison only",
    "JSON/stdout only",
    "path options are read-only inputs",
    "no cockpit hardware entrypoint",
    "no GUI launch",
    "no app launch",
    "no component mount",
    "no Electron launch",
    "no Tauri launch",
    "no webview launch",
    "no GUI renderer start",
    "no GUI event dispatch",
    "no GUI controller dispatch",
    "no GUI state-store mutation",
    "no browser automation execution",
    "no screenshot capture",
    "no bundler launch",
    "no dev-server launch",
    "no command execution",
    "no build execution",
    "no file writing",
    "no fixture file writing",
    "no component file writing",
    "no audio recording",
    "no audio streaming",
    "no audio read/compare execution",
    "no real MIDI rendering",
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
    "style-performance-arc-live-gui-cockpit-boundary-readiness-report usage: "
    "(--description <text>|--audio <path>|--library <dir>) "
    "(--capture-description <text>|--capture-audio <path>|--capture-library <dir>) "
    "[--rytm <syx-path>] [--analog-four <syx-path>] "
    "[--scope dual|rytm-only|analog-four-only|a4-only] "
    "[--rank N] [--total-minutes N] [--segment-minutes N] "
    "[--discovery-start N] [--discovery-end N] "
    "[--cue N] [--lookahead N] [--matches N] [--takes N] "
    "[--slot capture-001] [--label <text>] [--capture-prefix <text>] "
    "[--sidecar-label <text>] [--screen-label <text>] "
    "[--layout <key>] [--viewport desktop|tablet|compact] "
    "[--render-target desktop-sidecar|test-harness|operator-dashboard] "
    "[--density standard|compact] [--overlay-label <text>] "
    "[--frame-label <text>] [--interaction-label <text>] "
    "[--reducer-label <text>] [--controller-label <text>] "
    "[--playback-label <text>] [--validation-label <text>] "
    "[--harness-label <text>] [--readiness-label <text>] "
    "[--bridge-label <text>] [--blueprint-label <text>] "
    "[--desktop-shell operator-dashboard|desktop-sidecar|test-harness] "
    "[--app-plan-label <text>] "
    "[--framework-target desktop-python|web-desktop|test-harness] "
    "[--component-contract-label <text>] [--selector-prefix <text>] "
    "[--view-model-label <text>] [--state-prefix <text>] "
    "[--render-contract-label <text>] "
    "[--render-harness-label <text>] [--runner-label <text>] "
    "[--boundary-label <text>] [--hardware-entrypoint <command>] "
    "[--passive-entrypoint <command>] [--ws-port-env <name>] [--json]"
)


@dataclass(frozen=True)
class StylePerformanceArcLiveGuiCockpitBoundaryCheck:
    """One passive cockpit boundary assertion."""

    check_key: str
    label: str
    status: str
    severity: str
    source_id: str
    message: str
    operator_action: str
    passive: bool


@dataclass(frozen=True)
class StylePerformanceArcLiveGuiCockpitDeviceScopeCheck:
    """One passive device scope assertion for future cockpit surfaces."""

    device_key: str
    label: str
    required_lanes: int
    available_lanes: int
    lane_label: str
    scope_status: str
    severity: str
    operator_action: str
    passive: bool


@dataclass(frozen=True)
class StylePerformanceArcLiveGuiCockpitToolchainGuardrail:
    """One passive future cockpit toolchain guardrail."""

    guardrail_key: str
    label: str
    required_artifact: str
    docs_target: str
    status: str
    severity: str
    operator_action: str
    passive: bool


@dataclass(frozen=True)
class StylePerformanceArcLiveGuiCockpitBoundaryReadinessReport:
    """Passive cockpit boundary-readiness metadata."""

    render_harness: StylePerformanceArcLiveGuiDesktopRenderHarnessReport
    boundary_readiness_version: str
    boundary_readiness_id: str
    boundary_label: str
    boundary_status: str
    hardware_entrypoint: str
    passive_entrypoint: str
    ws_port_env: str
    device_scope_summary: str
    env_var_summary: str
    toolchain_summary: str
    device_scope_checks: tuple[StylePerformanceArcLiveGuiCockpitDeviceScopeCheck, ...]
    toolchain_guardrails: tuple[StylePerformanceArcLiveGuiCockpitToolchainGuardrail, ...]
    boundary_checks: tuple[StylePerformanceArcLiveGuiCockpitBoundaryCheck, ...]
    blocked_actions: tuple[str, ...]
    replay_commands: tuple[str, ...]

    @property
    def render_harness_id(self) -> str:
        """Return upstream desktop render-harness id."""

        return self.render_harness.render_harness_id

    @property
    def render_contract_id(self) -> str:
        """Return upstream desktop render-contract id."""

        return self.render_harness.render_contract_id

    @property
    def view_model_id(self) -> str:
        """Return upstream desktop view-model id."""

        return self.render_harness.view_model_id

    @property
    def selected_arc_key(self) -> str:
        """Return selected performance arc key."""

        return self.render_harness.selected_arc_key

    @property
    def selected_arc_name(self) -> str:
        """Return selected performance arc name."""

        return self.render_harness.selected_arc_name

    @property
    def scope(self) -> str:
        """Return selected machine scope."""

        return self.render_harness.scope


def _normalize_nonblank(value: str, *, field: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field} must not be blank")
    return normalized


def _status_from_boolean(value: bool, *, blocked: bool = False) -> str:
    if value:
        return "ready"
    if blocked:
        return "blocked"
    return "review-needed"


def _boundary_check(
    *,
    check_key: str,
    label: str,
    status: str,
    source_id: str,
    message: str,
    operator_action: str,
) -> StylePerformanceArcLiveGuiCockpitBoundaryCheck:
    return StylePerformanceArcLiveGuiCockpitBoundaryCheck(
        check_key=check_key,
        label=label,
        status=status,
        severity=status_severity(status),
        source_id=source_id,
        message=message,
        operator_action=operator_action,
        passive=True,
    )


def _render_harness_status_for_check(
    render_harness: StylePerformanceArcLiveGuiDesktopRenderHarnessReport,
) -> str:
    if render_harness.render_harness_status == "blocked":
        return "blocked"
    if render_harness.render_harness_status == "review-needed":
        return "review-needed"
    return "ready"


def _active_entrypoint_status(hardware_entrypoint: str) -> str:
    return _status_from_boolean(
        hardware_entrypoint == _DEFAULT_HARDWARE_ENTRYPOINT,
        blocked=True,
    )


def _no_cockpit_hardware_status(hardware_entrypoint: str) -> str:
    return _status_from_boolean("cockpit" not in hardware_entrypoint.lower(), blocked=True)


def _passive_entrypoint_status(passive_entrypoint: str) -> str:
    return _status_from_boolean(passive_entrypoint == _DEFAULT_PASSIVE_ENTRYPOINT)


def _replay_status(replay_commands: tuple[str, ...]) -> str:
    if not replay_commands:
        return "review-needed"
    if not replay_commands[0].startswith(
        "python -m rytm_randomizer.cli "
        "style-performance-arc-live-gui-cockpit-boundary-readiness-report"
    ):
        return "review-needed"
    return "ready"


def _boundary_checks(
    render_harness: StylePerformanceArcLiveGuiDesktopRenderHarnessReport,
    *,
    hardware_entrypoint: str,
    passive_entrypoint: str,
    ws_port_env: str,
    replay_commands: tuple[str, ...],
) -> tuple[StylePerformanceArcLiveGuiCockpitBoundaryCheck, ...]:
    return (
        _boundary_check(
            check_key="desktop-render-harness-status",
            label="Desktop render-harness status",
            status=_render_harness_status_for_check(render_harness),
            source_id=render_harness.render_harness_id,
            message=f"Desktop render-harness status is {render_harness.render_harness_status}.",
            operator_action="resolve desktop render-harness blockers before cockpit work",
        ),
        _boundary_check(
            check_key="active-hardware-entrypoint",
            label="Active hardware entrypoint",
            status=_active_entrypoint_status(hardware_entrypoint),
            source_id=render_harness.render_harness_id,
            message=(
                "Active hardware remains app --arm only via " f"{_DEFAULT_HARDWARE_ENTRYPOINT}."
            ),
            operator_action="keep armed hardware sends behind the existing app boundary",
        ),
        _boundary_check(
            check_key="no-cockpit-hardware-entrypoint",
            label="No cockpit hardware entrypoint",
            status=_no_cockpit_hardware_status(hardware_entrypoint),
            source_id=render_harness.render_harness_id,
            message="The future cockpit must not introduce its own armed hardware module.",
            operator_action="route future cockpit actions through existing active boundary",
        ),
        _boundary_check(
            check_key="passive-cli-entrypoint",
            label="Passive CLI entrypoint",
            status=_passive_entrypoint_status(passive_entrypoint),
            source_id=render_harness.render_harness_id,
            message=f"Passive cockpit reports remain under {passive_entrypoint}.",
            operator_action="do not open MIDI ports from passive CLI commands",
        ),
        _boundary_check(
            check_key="ws-port-env-docs",
            label="WebSocket port environment variable docs",
            status=_status_from_boolean(bool(ws_port_env.strip())),
            source_id=render_harness.render_harness_id,
            message=(
                f"{ws_port_env or _DEFAULT_WS_PORT_ENV} must be documented in "
                "CONTRIBUTING.md, docs/LOCAL_DEV_TOOLING_NOTES.md, and future "
                "COCKPIT_QUICKSTART.md."
            ),
            operator_action="keep future sidecar env vars documented at all operator surfaces",
        ),
        _boundary_check(
            check_key="replay-command",
            label="Cockpit boundary replay command",
            status=_replay_status(replay_commands),
            source_id=render_harness.render_harness_id,
            message=(
                "Cockpit boundary replay command is available."
                if replay_commands
                else "Cockpit boundary replay command is missing."
            ),
            operator_action="review command wiring before cockpit implementation",
        ),
        _boundary_check(
            check_key="passive-boundary",
            label="Passive boundary",
            status="ready",
            source_id=render_harness.render_harness_id,
            message="Cockpit boundary readiness emits metadata only.",
            operator_action="do not launch GUI, Tauri, audio analysis, or MIDI hardware",
        ),
    )


def _included_lanes(scope: str, *, device_key: str, required_lanes: int) -> int:
    if device_key == "analog-rytm-mkii" and scope in {"dual", "rytm-only"}:
        return required_lanes
    if device_key == "analog-four-mkii" and scope in {"dual", "analog-four-only", "a4-only"}:
        return required_lanes
    return 0


def _device_scope_check(
    *,
    device_key: str,
    label: str,
    required_lanes: int,
    available_lanes: int,
    lane_label: str,
    operator_action: str,
) -> StylePerformanceArcLiveGuiCockpitDeviceScopeCheck:
    status = _status_from_boolean(available_lanes >= required_lanes)
    return StylePerformanceArcLiveGuiCockpitDeviceScopeCheck(
        device_key=device_key,
        label=label,
        required_lanes=required_lanes,
        available_lanes=available_lanes,
        lane_label=lane_label,
        scope_status=status,
        severity=status_severity(status),
        operator_action=operator_action,
        passive=True,
    )


def _device_scope_checks(
    render_harness: StylePerformanceArcLiveGuiDesktopRenderHarnessReport,
) -> tuple[StylePerformanceArcLiveGuiCockpitDeviceScopeCheck, ...]:
    scope = render_harness.scope
    return (
        _device_scope_check(
            device_key="analog-rytm-mkii",
            label="Analog Rytm MKII",
            required_lanes=12,
            available_lanes=_included_lanes(
                scope,
                device_key="analog-rytm-mkii",
                required_lanes=12,
            ),
            lane_label="pads",
            operator_action="keep future cockpit Rytm surfaces aware of pads 1-12",
        ),
        _device_scope_check(
            device_key="analog-four-mkii",
            label="Analog Four MKII",
            required_lanes=4,
            available_lanes=_included_lanes(
                scope,
                device_key="analog-four-mkii",
                required_lanes=4,
            ),
            lane_label="tracks",
            operator_action="keep future cockpit Analog Four surfaces aware of tracks 1-4",
        ),
    )


def _toolchain_guardrail(
    *,
    guardrail_key: str,
    label: str,
    required_artifact: str,
    docs_target: str,
    status: str,
    operator_action: str,
) -> StylePerformanceArcLiveGuiCockpitToolchainGuardrail:
    return StylePerformanceArcLiveGuiCockpitToolchainGuardrail(
        guardrail_key=guardrail_key,
        label=label,
        required_artifact=required_artifact,
        docs_target=docs_target,
        status=status,
        severity=status_severity(status),
        operator_action=operator_action,
        passive=True,
    )


def _toolchain_guardrails(
    *,
    ws_port_env: str,
) -> tuple[StylePerformanceArcLiveGuiCockpitToolchainGuardrail, ...]:
    return (
        _toolchain_guardrail(
            guardrail_key="python-sidecar-websocket-port",
            label="Python sidecar WebSocket port",
            required_artifact=ws_port_env,
            docs_target="CONTRIBUTING.md; docs/LOCAL_DEV_TOOLING_NOTES.md",
            status=_status_from_boolean(bool(ws_port_env.strip())),
            operator_action="document the sidecar port before enabling a server",
        ),
        _toolchain_guardrail(
            guardrail_key="tauri-web-lockfiles",
            label="Tauri/web lockfiles",
            required_artifact="Cargo.lock; package-lock.json or pnpm-lock.yaml",
            docs_target="future cockpit implementation PR",
            status="review-needed",
            operator_action="add lockfiles and CI cache rules with the implementation",
        ),
        _toolchain_guardrail(
            guardrail_key="optional-cockpit-dependencies",
            label="Optional cockpit dependencies",
            required_artifact="optional extras or documented setup path",
            docs_target="docs/LOCAL_DEV_TOOLING_NOTES.md",
            status="review-needed",
            operator_action="keep CLI install path independent of desktop GUI dependencies",
        ),
    )


def _boundary_status(
    render_harness: StylePerformanceArcLiveGuiDesktopRenderHarnessReport,
    checks: tuple[StylePerformanceArcLiveGuiCockpitBoundaryCheck, ...],
) -> str:
    if render_harness.render_harness_status == "blocked":
        return "blocked"
    if any(check.status == "blocked" for check in checks):
        return "blocked"
    if render_harness.render_harness_status == "review-needed":
        return "review-needed"
    if any(check.status == "review-needed" for check in checks):
        return "review-needed"
    return "ready"


def _blocked_actions(
    render_harness: StylePerformanceArcLiveGuiDesktopRenderHarnessReport,
    boundary_status: str,
) -> tuple[str, ...]:
    actions: list[str] = [
        "no cockpit hardware entrypoint",
        "no GUI launch",
        "no app launch",
        "no component mount",
        "no Electron launch",
        "no Tauri launch",
        "no webview launch",
        "no GUI renderer start",
        "no GUI event dispatch",
        "no GUI controller dispatch",
        "no GUI state-store mutation",
        "no browser automation execution",
        "no screenshot capture",
        "no bundler launch",
        "no dev-server launch",
        "no command execution",
        "no build execution",
        "no file writing",
        "no fixture file writing",
        "no component file writing",
        "no audio recording",
        "no audio streaming",
        "no audio read/compare execution",
        "no real MIDI rendering",
        "no MIDI sending",
        "no port opening",
        "no hardware mutation",
    ]
    for action in render_harness.blocked_actions:
        if action not in actions:
            actions.append(action)
    if boundary_status != "ready":
        actions.insert(0, "hold cockpit work until desktop render harness is clear")
    return tuple(actions)


def _boundary_readiness_id(
    render_harness: StylePerformanceArcLiveGuiDesktopRenderHarnessReport,
    *,
    boundary_label: str,
    boundary_status: str,
    hardware_entrypoint: str,
    passive_entrypoint: str,
    ws_port_env: str,
) -> str:
    payload = "|".join(
        (
            BOUNDARY_READINESS_VERSION,
            render_harness.render_harness_id,
            render_harness.render_contract_id,
            render_harness.view_model_id,
            render_harness.selected_arc_key,
            render_harness.scope,
            boundary_label,
            boundary_status,
            hardware_entrypoint,
            passive_entrypoint,
            ws_port_env,
        )
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def _replace_replay_command(
    command: str,
    *,
    boundary_label: str,
    hardware_entrypoint: str,
    passive_entrypoint: str,
    ws_port_env: str,
) -> str | None:
    return replace_replay_command(
        command,
        source_command="style-performance-arc-live-gui-desktop-render-harness-report",
        target_command="style-performance-arc-live-gui-cockpit-boundary-readiness-report",
        extra_options=(
            ("--boundary-label", boundary_label),
            ("--hardware-entrypoint", hardware_entrypoint),
            ("--passive-entrypoint", passive_entrypoint),
            ("--ws-port-env", ws_port_env),
        ),
    )


def _replay_commands(
    render_harness: StylePerformanceArcLiveGuiDesktopRenderHarnessReport,
    *,
    boundary_label: str,
    hardware_entrypoint: str,
    passive_entrypoint: str,
    ws_port_env: str,
) -> tuple[str, ...]:
    if not render_harness.replay_commands:
        return ()
    boundary_command = _replace_replay_command(
        render_harness.replay_commands[0],
        boundary_label=boundary_label,
        hardware_entrypoint=hardware_entrypoint,
        passive_entrypoint=passive_entrypoint,
        ws_port_env=ws_port_env,
    )
    if boundary_command is None:
        return render_harness.replay_commands
    return (boundary_command, *render_harness.replay_commands)


def build_style_performance_arc_live_gui_cockpit_boundary_readiness_from_render_harness(
    render_harness: StylePerformanceArcLiveGuiDesktopRenderHarnessReport,
    *,
    boundary_label: str = _DEFAULT_BOUNDARY_LABEL,
    hardware_entrypoint: str = _DEFAULT_HARDWARE_ENTRYPOINT,
    passive_entrypoint: str = _DEFAULT_PASSIVE_ENTRYPOINT,
    ws_port_env: str = _DEFAULT_WS_PORT_ENV,
) -> StylePerformanceArcLiveGuiCockpitBoundaryReadinessReport:
    """Build passive cockpit boundary-readiness metadata from a render harness."""

    normalized_boundary_label = _normalize_nonblank(
        boundary_label,
        field="boundary_label",
    )
    normalized_hardware_entrypoint = _normalize_nonblank(
        hardware_entrypoint,
        field="hardware_entrypoint",
    )
    normalized_passive_entrypoint = _normalize_nonblank(
        passive_entrypoint,
        field="passive_entrypoint",
    )
    normalized_ws_port_env = ws_port_env.strip()
    replay_commands = _replay_commands(
        render_harness,
        boundary_label=normalized_boundary_label,
        hardware_entrypoint=normalized_hardware_entrypoint,
        passive_entrypoint=normalized_passive_entrypoint,
        ws_port_env=normalized_ws_port_env,
    )
    boundary_checks = _boundary_checks(
        render_harness,
        hardware_entrypoint=normalized_hardware_entrypoint,
        passive_entrypoint=normalized_passive_entrypoint,
        ws_port_env=normalized_ws_port_env,
        replay_commands=replay_commands,
    )
    boundary_status = _boundary_status(render_harness, boundary_checks)
    return StylePerformanceArcLiveGuiCockpitBoundaryReadinessReport(
        render_harness=render_harness,
        boundary_readiness_version=BOUNDARY_READINESS_VERSION,
        boundary_readiness_id=_boundary_readiness_id(
            render_harness,
            boundary_label=normalized_boundary_label,
            boundary_status=boundary_status,
            hardware_entrypoint=normalized_hardware_entrypoint,
            passive_entrypoint=normalized_passive_entrypoint,
            ws_port_env=normalized_ws_port_env,
        ),
        boundary_label=normalized_boundary_label,
        boundary_status=boundary_status,
        hardware_entrypoint=normalized_hardware_entrypoint,
        passive_entrypoint=normalized_passive_entrypoint,
        ws_port_env=normalized_ws_port_env,
        device_scope_summary=(
            "Rytm 12-pad and Analog Four 4-track scope is explicit for future cockpit work."
        ),
        env_var_summary=(
            f"{normalized_ws_port_env or _DEFAULT_WS_PORT_ENV} documentation targets "
            "CONTRIBUTING.md, docs/LOCAL_DEV_TOOLING_NOTES.md, and future "
            "COCKPIT_QUICKSTART.md."
        ),
        toolchain_summary="Future cockpit toolchain remains optional and lockfile-governed.",
        device_scope_checks=_device_scope_checks(render_harness),
        toolchain_guardrails=_toolchain_guardrails(ws_port_env=normalized_ws_port_env),
        boundary_checks=boundary_checks,
        blocked_actions=_blocked_actions(render_harness, boundary_status),
        replay_commands=replay_commands,
    )


def build_style_performance_arc_live_gui_cockpit_boundary_readiness_report(
    **options: object,
) -> StylePerformanceArcLiveGuiCockpitBoundaryReadinessReport:
    """Build one passive cockpit boundary-readiness report."""

    boundary_label = str(options.pop("boundary_label", _DEFAULT_BOUNDARY_LABEL))
    hardware_entrypoint = str(options.pop("hardware_entrypoint", _DEFAULT_HARDWARE_ENTRYPOINT))
    passive_entrypoint = str(options.pop("passive_entrypoint", _DEFAULT_PASSIVE_ENTRYPOINT))
    ws_port_env = str(options.pop("ws_port_env", _DEFAULT_WS_PORT_ENV))
    render_harness = build_style_performance_arc_live_gui_desktop_render_harness_report(**options)
    return build_style_performance_arc_live_gui_cockpit_boundary_readiness_from_render_harness(
        render_harness,
        boundary_label=boundary_label,
        hardware_entrypoint=hardware_entrypoint,
        passive_entrypoint=passive_entrypoint,
        ws_port_env=ws_port_env,
    )


def _device_scope_json(
    scope: StylePerformanceArcLiveGuiCockpitDeviceScopeCheck,
) -> dict[str, object]:
    return {
        "device_key": scope.device_key,
        "label": scope.label,
        "required_lanes": scope.required_lanes,
        "available_lanes": scope.available_lanes,
        "lane_label": scope.lane_label,
        "scope_status": scope.scope_status,
        "severity": scope.severity,
        "operator_action": scope.operator_action,
        "passive": scope.passive,
    }


def _toolchain_guardrail_json(
    guardrail: StylePerformanceArcLiveGuiCockpitToolchainGuardrail,
) -> dict[str, object]:
    return {
        "guardrail_key": guardrail.guardrail_key,
        "label": guardrail.label,
        "required_artifact": guardrail.required_artifact,
        "docs_target": guardrail.docs_target,
        "status": guardrail.status,
        "severity": guardrail.severity,
        "operator_action": guardrail.operator_action,
        "passive": guardrail.passive,
    }


def _boundary_check_json(
    check: StylePerformanceArcLiveGuiCockpitBoundaryCheck,
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


def to_style_performance_arc_live_gui_cockpit_boundary_readiness_json(
    report: StylePerformanceArcLiveGuiCockpitBoundaryReadinessReport,
) -> dict[str, object]:
    """Return deterministic JSON for passive cockpit boundary readiness."""

    render_harness_json = to_style_performance_arc_live_gui_desktop_render_harness_json(
        report.render_harness
    )
    return {
        "live_gui_cockpit_boundary_readiness": {
            "boundary_readiness_version": report.boundary_readiness_version,
            "boundary_readiness_id": report.boundary_readiness_id,
            "boundary_label": report.boundary_label,
            "boundary_status": report.boundary_status,
            "hardware_entrypoint": report.hardware_entrypoint,
            "passive_entrypoint": report.passive_entrypoint,
            "ws_port_env": report.ws_port_env,
            "render_harness_id": report.render_harness_id,
            "render_contract_id": report.render_contract_id,
            "view_model_id": report.view_model_id,
            "selected_arc_key": report.selected_arc_key,
            "selected_arc_name": report.selected_arc_name,
            "scope": report.scope,
            "device_scope_summary": report.device_scope_summary,
            "env_var_summary": report.env_var_summary,
            "toolchain_summary": report.toolchain_summary,
            "device_scope_checks": [
                _device_scope_json(scope) for scope in report.device_scope_checks
            ],
            "toolchain_guardrails": [
                _toolchain_guardrail_json(guardrail) for guardrail in report.toolchain_guardrails
            ],
            "boundary_checks": [_boundary_check_json(check) for check in report.boundary_checks],
            "blocked_actions": list(report.blocked_actions),
            "replay_commands": list(report.replay_commands),
        },
        **render_harness_json,
        "safety": list(SAFETY_LINES),
    }


def _device_scope_lines(scope: StylePerformanceArcLiveGuiCockpitDeviceScopeCheck) -> list[str]:
    return [
        f"- {scope.device_key}: {scope.label}",
        f"  Required {scope.lane_label}: {scope.required_lanes}",
        f"  Available {scope.lane_label}: {scope.available_lanes}",
        f"  Status: {scope.scope_status}",
        f"  Severity: {scope.severity}",
        f"  Operator action: {scope.operator_action}",
        f"  Passive: {scope.passive}",
    ]


def _toolchain_guardrail_lines(
    guardrail: StylePerformanceArcLiveGuiCockpitToolchainGuardrail,
) -> list[str]:
    return [
        f"- {guardrail.guardrail_key}: {guardrail.label}",
        f"  Required artifact: {guardrail.required_artifact}",
        f"  Docs target: {guardrail.docs_target}",
        f"  Status: {guardrail.status}",
        f"  Severity: {guardrail.severity}",
        f"  Operator action: {guardrail.operator_action}",
        f"  Passive: {guardrail.passive}",
    ]


def _boundary_check_lines(check: StylePerformanceArcLiveGuiCockpitBoundaryCheck) -> list[str]:
    return [
        f"- {check.check_key}: {check.label}",
        f"  Status: {check.status}",
        f"  Severity: {check.severity}",
        f"  Source id: {check.source_id}",
        f"  Message: {check.message}",
        f"  Operator action: {check.operator_action}",
        f"  Passive: {check.passive}",
    ]


def format_style_performance_arc_live_gui_cockpit_boundary_readiness_report(
    report: StylePerformanceArcLiveGuiCockpitBoundaryReadinessReport,
) -> list[str]:
    """Format a passive cockpit boundary-readiness report."""

    lines = [
        "Live GUI cockpit boundary readiness summary:",
        f"- Boundary readiness id: {report.boundary_readiness_id}",
        f"- Boundary label: {report.boundary_label}",
        f"- Boundary status: {report.boundary_status}",
        f"- Hardware entrypoint: {report.hardware_entrypoint}",
        f"- Passive entrypoint: {report.passive_entrypoint}",
        f"- WebSocket port env: {report.ws_port_env or _DEFAULT_WS_PORT_ENV}",
        f"- Render harness id: {report.render_harness_id}",
        f"- Render contract id: {report.render_contract_id}",
        f"- View model id: {report.view_model_id}",
        f"- Selected arc: {report.selected_arc_name} ({report.selected_arc_key})",
        f"- Scope: {report.scope}",
        f"- Device scope summary: {report.device_scope_summary}",
        f"- Env var summary: {report.env_var_summary}",
        f"- Toolchain summary: {report.toolchain_summary}",
        "Device scope checks:",
    ]
    for scope in report.device_scope_checks:
        lines.extend(_device_scope_lines(scope))
    lines.append("Toolchain guardrails:")
    for guardrail in report.toolchain_guardrails:
        lines.extend(_toolchain_guardrail_lines(guardrail))
    lines.append("Boundary checks:")
    for check in report.boundary_checks:
        lines.extend(_boundary_check_lines(check))
    lines.extend(
        [
            "Blocked active actions:",
            *[f"- {action}" for action in report.blocked_actions],
            "Replayable passive commands:",
            *[f"- {command}" for command in report.replay_commands],
            SAFETY_SECTION_HEADER,
            *[f"- {line}" for line in SAFETY_LINES],
        ]
    )
    return passive_report_lines(_HEADER, lines)


def _pop_option_value(remaining: list[str]) -> str:
    return pop_option_value(remaining, usage=_USAGE)


def parse_style_performance_arc_live_gui_cockpit_boundary_readiness_cli_args(
    argv: Sequence[str],
) -> dict[str, object]:
    """Parse cockpit boundary-readiness CLI args for passive report composition."""

    boundary_label = _DEFAULT_BOUNDARY_LABEL
    hardware_entrypoint = _DEFAULT_HARDWARE_ENTRYPOINT
    passive_entrypoint = _DEFAULT_PASSIVE_ENTRYPOINT
    ws_port_env = _DEFAULT_WS_PORT_ENV
    render_harness_args: list[str] = []
    remaining = list(argv)
    while remaining:
        option = remaining.pop(0)
        if option == "--boundary-label":
            boundary_label = _normalize_nonblank(
                _pop_option_value(remaining),
                field="boundary_label",
            )
        elif option == "--hardware-entrypoint":
            hardware_entrypoint = _normalize_nonblank(
                _pop_option_value(remaining),
                field="hardware_entrypoint",
            )
        elif option == "--passive-entrypoint":
            passive_entrypoint = _normalize_nonblank(
                _pop_option_value(remaining),
                field="passive_entrypoint",
            )
        elif option == "--ws-port-env":
            ws_port_env = _pop_option_value(remaining).strip()
        else:
            render_harness_args.append(option)
            if option != "--json":
                render_harness_args.append(_pop_option_value(remaining))
    parsed = parse_style_performance_arc_live_gui_desktop_render_harness_cli_args(
        render_harness_args
    )
    parsed["boundary_label"] = boundary_label
    parsed["hardware_entrypoint"] = hardware_entrypoint
    parsed["passive_entrypoint"] = passive_entrypoint
    parsed["ws_port_env"] = ws_port_env
    return parsed


def _handle_cli_report(**options: object) -> int:
    json_output = options.pop("json_output", False)
    try:
        report = build_style_performance_arc_live_gui_cockpit_boundary_readiness_report(**options)
        if json_output is True:
            sys.stdout.write(
                json.dumps(
                    to_style_performance_arc_live_gui_cockpit_boundary_readiness_json(report),
                    indent=2,
                    sort_keys=True,
                )
            )
            sys.stdout.write("\n")
            return 0
        lines = format_style_performance_arc_live_gui_cockpit_boundary_readiness_report(report)
    except (OSError, ValueError, RuntimeError, NotImplementedError, TypeError, KeyError) as exc:
        sys.stderr.write(f"Error: {exc}\n")
        return 2
    for line in lines:
        sys.stdout.write(f"{line}\n")
    return 0


STYLE_PERFORMANCE_ARC_LIVE_GUI_COCKPIT_BOUNDARY_READINESS_CLI_COMMAND: Final[CliCommand] = (
    CliCommand(
        name="style-performance-arc-live-gui-cockpit-boundary-readiness-report",
        summary=(
            "Compose passive GUI desktop render harnesses into cockpit boundary-readiness "
            "metadata."
        ),
        args_parser=parse_style_performance_arc_live_gui_cockpit_boundary_readiness_cli_args,
        handler=_handle_cli_report,
        error_formatter=_format_cli_error,
    )
)

register(STYLE_PERFORMANCE_ARC_LIVE_GUI_COCKPIT_BOUNDARY_READINESS_CLI_COMMAND)

__all__ = [
    "BOUNDARY_READINESS_VERSION",
    "REPORT_TITLE",
    "SAFETY_LINES",
    "SOURCE_MODULE",
    "STYLE_PERFORMANCE_ARC_LIVE_GUI_COCKPIT_BOUNDARY_READINESS_CLI_COMMAND",
    "StylePerformanceArcLiveGuiCockpitBoundaryCheck",
    "StylePerformanceArcLiveGuiCockpitBoundaryReadinessReport",
    "StylePerformanceArcLiveGuiCockpitDeviceScopeCheck",
    "StylePerformanceArcLiveGuiCockpitToolchainGuardrail",
    "_boundary_checks",
    "_boundary_status",
    "build_style_performance_arc_live_gui_cockpit_boundary_readiness_from_render_harness",
    "build_style_performance_arc_live_gui_cockpit_boundary_readiness_report",
    "format_style_performance_arc_live_gui_cockpit_boundary_readiness_report",
    "parse_style_performance_arc_live_gui_cockpit_boundary_readiness_cli_args",
    "to_style_performance_arc_live_gui_cockpit_boundary_readiness_json",
]
