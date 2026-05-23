"""Passive live GUI implementation bridge for future desktop surfaces."""

from __future__ import annotations

import hashlib
import json
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Final

from ..cli_registry import CliCommand, register
from ..style_analysis.feature_report import FeatureReport
from .formatter import (
    SAFETY_SECTION_HEADER,
    PassiveReportHeader,
    passive_report_lines,
    powershell_literal_arg,
)
from .live_gui_test_harness_readiness import (
    StylePerformanceArcLiveGuiTestHarnessReadinessReport,
    build_style_performance_arc_live_gui_test_harness_readiness_report,
    parse_style_performance_arc_live_gui_test_harness_readiness_cli_args,
    to_style_performance_arc_live_gui_test_harness_readiness_json,
)

REPORT_TITLE: Final[str] = (
    "RytmRandomizer passive style performance arc live GUI implementation bridge"
)
SOURCE_MODULE: Final[str] = "reports.live_gui_implementation_bridge"
BRIDGE_VERSION: Final[str] = "live-gui-implementation-bridge-v1"
SAFETY_LINES: Final[tuple[str, ...]] = (
    "passive/read-only",
    "Passive GUI implementation bridge metadata only",
    "consumes live GUI test-harness readiness metadata only",
    "view-model packets are declarative metadata only",
    "component mounts are declarative metadata only",
    "fixture bundles are declarative metadata only",
    "implementation gates are advisory metadata only",
    "future desktop GUI only",
    "future audio analyzer comparison only",
    "JSON/stdout only",
    "path options are read-only inputs",
    "no GUI launch",
    "no GUI renderer start",
    "no renderer execution",
    "no GUI event dispatch",
    "no GUI controller dispatch",
    "no GUI state-store mutation",
    "no GUI test runner execution",
    "no bundler or dev-server launch",
    "no command execution",
    "no file writing",
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
_DEFAULT_BRIDGE_LABEL: Final[str] = "Live GUI implementation bridge"
_USAGE: Final[str] = (
    "style-performance-arc-live-gui-implementation-bridge-report usage: "
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
    "[--bridge-label <text>] [--json]"
)


@dataclass(frozen=True)
class StylePerformanceArcLiveGuiImplementationViewModelPacket:
    """One future-GUI view-model packet sourced from the passive chain."""

    packet_key: str
    order: int
    packet_kind: str
    source_id: str
    json_key: str
    component_hint: str
    status: str
    passive: bool


@dataclass(frozen=True)
class StylePerformanceArcLiveGuiImplementationComponentMount:
    """One disabled future component mount descriptor."""

    component_key: str
    order: int
    region_key: str
    component_type: str
    source_packet_key: str
    test_id: str
    mount_enabled: bool
    blocked_reason: str
    operator_action: str


@dataclass(frozen=True)
class StylePerformanceArcLiveGuiImplementationFixtureBundle:
    """One passive future-GUI fixture bundle descriptor."""

    bundle_key: str
    order: int
    fixture_kind: str
    source_packet_key: str
    source_id: str
    json_path: str
    target_scope: str
    passive: bool


@dataclass(frozen=True)
class StylePerformanceArcLiveGuiImplementationGate:
    """One implementation bridge gate for future GUI work."""

    key: str
    label: str
    status: str
    severity: str
    source_id: str
    message: str
    operator_action: str
    passive: bool


@dataclass(frozen=True)
class StylePerformanceArcLiveGuiImplementationBridgeReport:
    """Passive implementation bridge composed from test-harness readiness."""

    test_harness_readiness: StylePerformanceArcLiveGuiTestHarnessReadinessReport
    bridge_version: str
    bridge_id: str
    bridge_label: str
    bridge_status: str
    view_model_summary: str
    component_mount_summary: str
    fixture_bundle_summary: str
    view_model_packets: tuple[
        StylePerformanceArcLiveGuiImplementationViewModelPacket,
        ...,
    ]
    component_mounts: tuple[
        StylePerformanceArcLiveGuiImplementationComponentMount,
        ...,
    ]
    fixture_bundles: tuple[
        StylePerformanceArcLiveGuiImplementationFixtureBundle,
        ...,
    ]
    implementation_gates: tuple[StylePerformanceArcLiveGuiImplementationGate, ...]
    blocked_actions: tuple[str, ...]
    replay_commands: tuple[str, ...]

    @property
    def readiness_id(self) -> str:
        """Return upstream test-harness readiness id."""

        return self.test_harness_readiness.readiness_id

    @property
    def contract_id(self) -> str:
        """Return upstream test-harness contract id."""

        return self.test_harness_readiness.contract_id

    @property
    def selected_arc_key(self) -> str:
        """Return selected performance arc key."""

        return self.test_harness_readiness.selected_arc_key

    @property
    def selected_arc_name(self) -> str:
        """Return selected performance arc name."""

        return self.test_harness_readiness.selected_arc_name

    @property
    def scope(self) -> str:
        """Return selected machine scope."""

        return self.test_harness_readiness.scope


def _normalize_nonblank(value: str, *, field: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field} must not be blank")
    return normalized


def _status_severity(status: str) -> str:
    if status == "blocked":
        return "critical"
    if status == "review-needed":
        return "warning"
    return "info"


def _bridge_id(
    readiness: StylePerformanceArcLiveGuiTestHarnessReadinessReport,
    *,
    bridge_label: str,
    bridge_status: str,
) -> str:
    payload = "|".join(
        (
            BRIDGE_VERSION,
            readiness.readiness_id,
            readiness.contract_id,
            readiness.selected_arc_key,
            readiness.scope,
            bridge_label,
            bridge_status,
        )
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def _view_model_packet(
    *,
    packet_key: str,
    order: int,
    packet_kind: str,
    source_id: str,
    json_key: str,
    component_hint: str,
    status: str,
) -> StylePerformanceArcLiveGuiImplementationViewModelPacket:
    return StylePerformanceArcLiveGuiImplementationViewModelPacket(
        packet_key=packet_key,
        order=order,
        packet_kind=packet_kind,
        source_id=source_id,
        json_key=json_key,
        component_hint=component_hint,
        status=status,
        passive=True,
    )


def _view_model_packets(
    readiness: StylePerformanceArcLiveGuiTestHarnessReadinessReport,
) -> tuple[StylePerformanceArcLiveGuiImplementationViewModelPacket, ...]:
    contract = readiness.test_harness_contract
    validation = contract.playback_validation
    return (
        _view_model_packet(
            packet_key="sidecar-session",
            order=1,
            packet_kind="source-packet",
            source_id=validation.screen_contract_id,
            json_key="live_gui_sidecar_session",
            component_hint="sidecar shell and cue context",
            status=readiness.readiness_status,
        ),
        _view_model_packet(
            packet_key="screen-contract",
            order=2,
            packet_kind="layout-contract",
            source_id=validation.screen_contract_id,
            json_key="live_gui_screen_contract",
            component_hint="regions and component state",
            status=readiness.readiness_status,
        ),
        _view_model_packet(
            packet_key="render-tree",
            order=3,
            packet_kind="render-tree",
            source_id=validation.render_tree_id,
            json_key="live_gui_render_tree",
            component_hint="render nodes and test ids",
            status=readiness.readiness_status,
        ),
        _view_model_packet(
            packet_key="analyzer-frame",
            order=4,
            packet_kind="analyzer-frame",
            source_id=readiness.frame_id,
            json_key="live_gui_analyzer_frame",
            component_hint="overlay meters and frame assertions",
            status=readiness.readiness_status,
        ),
        _view_model_packet(
            packet_key="controller-state",
            order=5,
            packet_kind="controller-state",
            source_id=readiness.controller_id,
            json_key="live_gui_controller_state",
            component_hint="allowed and blocked control rows",
            status=readiness.readiness_status,
        ),
        _view_model_packet(
            packet_key="test-harness-readiness",
            order=6,
            packet_kind="readiness",
            source_id=readiness.readiness_id,
            json_key="live_gui_test_harness_readiness",
            component_hint="readiness gates and rehearsal steps",
            status=readiness.readiness_status,
        ),
    )


def _component_mount(
    *,
    component_key: str,
    order: int,
    region_key: str,
    component_type: str,
    source_packet_key: str,
    test_id: str,
    operator_action: str,
) -> StylePerformanceArcLiveGuiImplementationComponentMount:
    return StylePerformanceArcLiveGuiImplementationComponentMount(
        component_key=component_key,
        order=order,
        region_key=region_key,
        component_type=component_type,
        source_packet_key=source_packet_key,
        test_id=test_id,
        mount_enabled=False,
        blocked_reason="future GUI implementation only; no renderer is launched",
        operator_action=operator_action,
    )


def _component_mounts() -> tuple[StylePerformanceArcLiveGuiImplementationComponentMount, ...]:
    return (
        _component_mount(
            component_key="current-cue-panel",
            order=1,
            region_key="primary",
            component_type="cue-status",
            source_packet_key="screen-contract",
            test_id="rr-current-cue-panel",
            operator_action="bind current cue, primary action, and alert rows",
        ),
        _component_mount(
            component_key="machine-panels",
            order=2,
            region_key="machine-grid",
            component_type="machine-summary",
            source_packet_key="sidecar-session",
            test_id="rr-machine-panels",
            operator_action="bind Rytm/A4 machine status panels from sidecar rows",
        ),
        _component_mount(
            component_key="analyzer-overlay",
            order=3,
            region_key="analyzer",
            component_type="meter-overlay",
            source_packet_key="analyzer-frame",
            test_id="rr-analyzer-overlay",
            operator_action="bind analyzer overlay meters and frame assertions",
        ),
        _component_mount(
            component_key="capture-review-panel",
            order=4,
            region_key="capture",
            component_type="capture-review",
            source_packet_key="sidecar-session",
            test_id="rr-capture-review-panel",
            operator_action="bind selected take and hold/repeat/go decisions",
        ),
        _component_mount(
            component_key="controller-actions",
            order=5,
            region_key="controls",
            component_type="action-bar",
            source_packet_key="controller-state",
            test_id="rr-controller-actions",
            operator_action="bind disabled controls and queued safe actions",
        ),
        _component_mount(
            component_key="test-harness-panel",
            order=6,
            region_key="validation",
            component_type="harness-readiness",
            source_packet_key="test-harness-readiness",
            test_id="rr-test-harness-panel",
            operator_action="bind readiness gates, checks, and rehearsal steps",
        ),
    )


def _fixture_bundle(
    *,
    bundle_key: str,
    order: int,
    fixture_kind: str,
    source_packet_key: str,
    source_id: str,
    json_path: str,
    target_scope: str,
) -> StylePerformanceArcLiveGuiImplementationFixtureBundle:
    return StylePerformanceArcLiveGuiImplementationFixtureBundle(
        bundle_key=bundle_key,
        order=order,
        fixture_kind=fixture_kind,
        source_packet_key=source_packet_key,
        source_id=source_id,
        json_path=json_path,
        target_scope=target_scope,
        passive=True,
    )


def _fixture_bundles(
    readiness: StylePerformanceArcLiveGuiTestHarnessReadinessReport,
) -> tuple[StylePerformanceArcLiveGuiImplementationFixtureBundle, ...]:
    validation = readiness.test_harness_contract.playback_validation
    return (
        _fixture_bundle(
            bundle_key="fixture-sidecar-session-json",
            order=1,
            fixture_kind="view-model-json",
            source_packet_key="sidecar-session",
            source_id=validation.screen_contract_id,
            json_path="$.live_gui_sidecar_session",
            target_scope="desktop sidecar shell",
        ),
        _fixture_bundle(
            bundle_key="fixture-render-tree-json",
            order=2,
            fixture_kind="render-tree-json",
            source_packet_key="render-tree",
            source_id=validation.render_tree_id,
            json_path="$.live_gui_render_tree",
            target_scope="deterministic render-node tests",
        ),
        _fixture_bundle(
            bundle_key="fixture-controller-state-json",
            order=3,
            fixture_kind="controller-state-json",
            source_packet_key="controller-state",
            source_id=readiness.controller_id,
            json_path="$.live_gui_controller_state",
            target_scope="action reducer/controller tests",
        ),
        _fixture_bundle(
            bundle_key="fixture-test-harness-readiness-json",
            order=4,
            fixture_kind="readiness-json",
            source_packet_key="test-harness-readiness",
            source_id=readiness.readiness_id,
            json_path="$.live_gui_test_harness_readiness",
            target_scope="future GUI harness readiness tests",
        ),
    )


def _gate(
    *,
    key: str,
    label: str,
    status: str,
    source_id: str,
    message: str,
    operator_action: str,
) -> StylePerformanceArcLiveGuiImplementationGate:
    return StylePerformanceArcLiveGuiImplementationGate(
        key=key,
        label=label,
        status=status,
        severity=_status_severity(status),
        source_id=source_id,
        message=message,
        operator_action=operator_action,
        passive=True,
    )


def _coverage_status(count: int) -> str:
    if count <= 0:
        return "blocked"
    return "ready"


def _replay_status(replay_commands: tuple[str, ...]) -> str:
    if replay_commands and replay_commands[0].startswith(
        "python -m rytm_randomizer.cli "
        "style-performance-arc-live-gui-implementation-bridge-report"
    ):
        return "ready"
    return "review-needed"


def _implementation_gates(
    readiness: StylePerformanceArcLiveGuiTestHarnessReadinessReport,
    *,
    view_model_packets: tuple[StylePerformanceArcLiveGuiImplementationViewModelPacket, ...],
    component_mounts: tuple[StylePerformanceArcLiveGuiImplementationComponentMount, ...],
    fixture_bundles: tuple[StylePerformanceArcLiveGuiImplementationFixtureBundle, ...],
    replay_commands: tuple[str, ...],
) -> tuple[StylePerformanceArcLiveGuiImplementationGate, ...]:
    readiness_status = readiness.readiness_status
    return (
        _gate(
            key="readiness-status",
            label="Test-harness readiness status",
            status=readiness_status,
            source_id=readiness.readiness_id,
            message=f"Upstream readiness is {readiness_status}.",
            operator_action="hold GUI implementation if upstream readiness is blocked",
        ),
        _gate(
            key="view-model-coverage",
            label="View-model packet coverage",
            status=_coverage_status(len(view_model_packets)),
            source_id=readiness.readiness_id,
            message=f"{len(view_model_packets)} view-model packets are available.",
            operator_action="bind packets to future GUI view-model fixtures",
        ),
        _gate(
            key="component-mount-coverage",
            label="Component mount coverage",
            status=_coverage_status(len(component_mounts)),
            source_id=readiness.readiness_id,
            message=f"{len(component_mounts)} component mounts are available.",
            operator_action="map disabled component mounts before enabling UI runtime",
        ),
        _gate(
            key="fixture-bundle-coverage",
            label="Fixture bundle coverage",
            status=_coverage_status(len(fixture_bundles)),
            source_id=readiness.readiness_id,
            message=f"{len(fixture_bundles)} fixture bundles are available.",
            operator_action="wire deterministic fixtures before launching a GUI runner",
        ),
        _gate(
            key="replay-command",
            label="Bridge replay command",
            status=_replay_status(replay_commands),
            source_id=readiness.readiness_id,
            message=(
                "Bridge replay command is available."
                if replay_commands
                else "Bridge replay command is missing."
            ),
            operator_action="review command wiring before promoting to a GUI task",
        ),
        _gate(
            key="passive-boundary",
            label="Passive boundary",
            status="ready",
            source_id=readiness.readiness_id,
            message="Bridge emits metadata only.",
            operator_action="do not launch GUI, renderer, audio analysis, or MIDI hardware",
        ),
    )


def _bridge_status(
    readiness: StylePerformanceArcLiveGuiTestHarnessReadinessReport,
    gates: tuple[StylePerformanceArcLiveGuiImplementationGate, ...],
) -> str:
    if readiness.readiness_status == "blocked":
        return "blocked"
    if any(gate.status == "blocked" for gate in gates):
        return "blocked"
    if readiness.readiness_status == "review-needed":
        return "review-needed"
    if any(gate.status == "review-needed" for gate in gates):
        return "review-needed"
    return "ready"


def _blocked_actions(bridge_status: str) -> tuple[str, ...]:
    actions: list[str] = [
        "no GUI launch",
        "no GUI renderer start",
        "no renderer execution",
        "no GUI event dispatch",
        "no GUI controller dispatch",
        "no GUI state-store mutation",
        "no GUI test runner execution",
        "no bundler or dev-server launch",
        "no command execution",
        "no file writing",
        "no audio recording",
        "no audio streaming",
        "no audio read/compare execution",
        "no real MIDI rendering",
        "no MIDI sending",
        "no port opening",
        "no hardware mutation",
    ]
    if bridge_status != "ready":
        actions.insert(0, "hold GUI implementation bridge until readiness is clear")
    return tuple(actions)


def _replace_replay_command(
    command: str,
    *,
    bridge_label: str,
) -> str | None:
    source = "style-performance-arc-live-gui-test-harness-readiness-report"
    target = "style-performance-arc-live-gui-implementation-bridge-report"
    if source not in command:
        return None
    return (
        command.replace(source, target, 1)
        + f" --bridge-label {powershell_literal_arg(bridge_label)}"
    )


def _replay_commands(
    readiness: StylePerformanceArcLiveGuiTestHarnessReadinessReport,
    *,
    bridge_label: str,
) -> tuple[str, ...]:
    if not readiness.replay_commands:
        return ()
    bridge_command = _replace_replay_command(
        readiness.replay_commands[0],
        bridge_label=bridge_label,
    )
    if bridge_command is None:
        return readiness.replay_commands
    return (bridge_command, *readiness.replay_commands)


def build_style_performance_arc_live_gui_implementation_bridge_from_readiness(
    readiness: StylePerformanceArcLiveGuiTestHarnessReadinessReport,
    *,
    bridge_label: str = _DEFAULT_BRIDGE_LABEL,
) -> StylePerformanceArcLiveGuiImplementationBridgeReport:
    """Build one passive GUI implementation bridge from readiness metadata."""

    normalized_label = _normalize_nonblank(bridge_label, field="bridge_label")
    view_model_packets = _view_model_packets(readiness)
    component_mounts = _component_mounts()
    fixture_bundles = _fixture_bundles(readiness)
    replay_commands = _replay_commands(readiness, bridge_label=normalized_label)
    provisional_gates = _implementation_gates(
        readiness,
        view_model_packets=view_model_packets,
        component_mounts=component_mounts,
        fixture_bundles=fixture_bundles,
        replay_commands=replay_commands,
    )
    bridge_status = _bridge_status(readiness, provisional_gates)
    return StylePerformanceArcLiveGuiImplementationBridgeReport(
        test_harness_readiness=readiness,
        bridge_version=BRIDGE_VERSION,
        bridge_id=_bridge_id(
            readiness,
            bridge_label=normalized_label,
            bridge_status=bridge_status,
        ),
        bridge_label=normalized_label,
        bridge_status=bridge_status,
        view_model_summary=f"{len(view_model_packets)} view-model packets ready for GUI binding",
        component_mount_summary=f"{len(component_mounts)} component mounts held disabled",
        fixture_bundle_summary=f"{len(fixture_bundles)} fixture bundles ready for future harnesses",
        view_model_packets=view_model_packets,
        component_mounts=component_mounts,
        fixture_bundles=fixture_bundles,
        implementation_gates=provisional_gates,
        blocked_actions=_blocked_actions(bridge_status),
        replay_commands=replay_commands,
    )


def build_style_performance_arc_live_gui_implementation_bridge_report(
    *,
    description: str | None = None,
    feature_report: FeatureReport | None = None,
    audio_path: Path | None = None,
    library_path: Path | None = None,
    capture_description: str | None = None,
    capture_feature_report: FeatureReport | None = None,
    capture_audio_path: Path | None = None,
    capture_library_path: Path | None = None,
    rytm_sysex_path: Path | None = None,
    analog_four_sysex_path: Path | None = None,
    scope: str | None = None,
    selection_rank: int | None = None,
    total_minutes: int | None = None,
    segment_minutes: int | None = None,
    discovery_start: int | None = None,
    discovery_end: int | None = None,
    cue_number: int = 1,
    lookahead_count: int = 2,
    match_limit: int = 3,
    take_count: int = 2,
    slot_key: str = "capture-001",
    queue_label: str = "Live GUI capture queue",
    capture_prefix: str = "rehearsal",
    sidecar_label: str = "Live GUI sidecar session",
    screen_label: str = "Live GUI screen contract",
    layout_key: str = "operator-cockpit",
    viewport: str = "desktop",
    render_target: str = "desktop-sidecar",
    density: str = "standard",
    overlay_label: str = "Live GUI analyzer overlay",
    frame_label: str = "Live GUI analyzer frame",
    interaction_label: str = "Live GUI interaction script",
    reducer_label: str = "Live GUI action reducer",
    controller_label: str = "Live GUI controller state",
    playback_label: str = "Live GUI playback transcript",
    validation_label: str = "Live GUI playback validation matrix",
    harness_label: str = "Live GUI test-harness contract",
    readiness_label: str = "Live GUI test-harness readiness",
    bridge_label: str = _DEFAULT_BRIDGE_LABEL,
) -> StylePerformanceArcLiveGuiImplementationBridgeReport:
    """Build a passive GUI implementation bridge from normal report inputs."""

    readiness = build_style_performance_arc_live_gui_test_harness_readiness_report(
        description=description,
        feature_report=feature_report,
        audio_path=audio_path,
        library_path=library_path,
        capture_description=capture_description,
        capture_feature_report=capture_feature_report,
        capture_audio_path=capture_audio_path,
        capture_library_path=capture_library_path,
        rytm_sysex_path=rytm_sysex_path,
        analog_four_sysex_path=analog_four_sysex_path,
        scope=scope,
        selection_rank=selection_rank,
        total_minutes=total_minutes,
        segment_minutes=segment_minutes,
        discovery_start=discovery_start,
        discovery_end=discovery_end,
        cue_number=cue_number,
        lookahead_count=lookahead_count,
        match_limit=match_limit,
        take_count=take_count,
        slot_key=slot_key,
        queue_label=queue_label,
        capture_prefix=capture_prefix,
        sidecar_label=sidecar_label,
        screen_label=screen_label,
        layout_key=layout_key,
        viewport=viewport,
        render_target=render_target,
        density=density,
        overlay_label=overlay_label,
        frame_label=frame_label,
        interaction_label=interaction_label,
        reducer_label=reducer_label,
        controller_label=controller_label,
        playback_label=playback_label,
        validation_label=validation_label,
        harness_label=harness_label,
        readiness_label=readiness_label,
    )
    return build_style_performance_arc_live_gui_implementation_bridge_from_readiness(
        readiness,
        bridge_label=bridge_label,
    )


def _packet_json(
    packet: StylePerformanceArcLiveGuiImplementationViewModelPacket,
) -> dict[str, object]:
    return {
        "packet_key": packet.packet_key,
        "order": packet.order,
        "packet_kind": packet.packet_kind,
        "source_id": packet.source_id,
        "json_key": packet.json_key,
        "component_hint": packet.component_hint,
        "status": packet.status,
        "passive": packet.passive,
    }


def _mount_json(mount: StylePerformanceArcLiveGuiImplementationComponentMount) -> dict[str, object]:
    return {
        "component_key": mount.component_key,
        "order": mount.order,
        "region_key": mount.region_key,
        "component_type": mount.component_type,
        "source_packet_key": mount.source_packet_key,
        "test_id": mount.test_id,
        "mount_enabled": mount.mount_enabled,
        "blocked_reason": mount.blocked_reason,
        "operator_action": mount.operator_action,
    }


def _fixture_json(
    bundle: StylePerformanceArcLiveGuiImplementationFixtureBundle,
) -> dict[str, object]:
    return {
        "bundle_key": bundle.bundle_key,
        "order": bundle.order,
        "fixture_kind": bundle.fixture_kind,
        "source_packet_key": bundle.source_packet_key,
        "source_id": bundle.source_id,
        "json_path": bundle.json_path,
        "target_scope": bundle.target_scope,
        "passive": bundle.passive,
    }


def _gate_json(gate: StylePerformanceArcLiveGuiImplementationGate) -> dict[str, object]:
    return {
        "key": gate.key,
        "label": gate.label,
        "status": gate.status,
        "severity": gate.severity,
        "source_id": gate.source_id,
        "message": gate.message,
        "operator_action": gate.operator_action,
        "passive": gate.passive,
    }


def to_style_performance_arc_live_gui_implementation_bridge_json(
    report: StylePerformanceArcLiveGuiImplementationBridgeReport,
) -> dict[str, object]:
    """Return deterministic JSON for a passive GUI implementation bridge."""

    readiness_json = to_style_performance_arc_live_gui_test_harness_readiness_json(
        report.test_harness_readiness
    )
    return {
        "live_gui_implementation_bridge": {
            "bridge_version": report.bridge_version,
            "bridge_id": report.bridge_id,
            "bridge_label": report.bridge_label,
            "bridge_status": report.bridge_status,
            "readiness_id": report.readiness_id,
            "contract_id": report.contract_id,
            "selected_arc_key": report.selected_arc_key,
            "selected_arc_name": report.selected_arc_name,
            "scope": report.scope,
            "view_model_summary": report.view_model_summary,
            "component_mount_summary": report.component_mount_summary,
            "fixture_bundle_summary": report.fixture_bundle_summary,
            "view_model_packets": [_packet_json(packet) for packet in report.view_model_packets],
            "component_mounts": [_mount_json(mount) for mount in report.component_mounts],
            "fixture_bundles": [_fixture_json(bundle) for bundle in report.fixture_bundles],
            "implementation_gates": [_gate_json(gate) for gate in report.implementation_gates],
            "blocked_actions": list(report.blocked_actions),
            "replay_commands": list(report.replay_commands),
        },
        **readiness_json,
        "safety": list(SAFETY_LINES),
    }


def _packet_lines(packet: StylePerformanceArcLiveGuiImplementationViewModelPacket) -> list[str]:
    return [
        f"- {packet.order}. {packet.packet_key} ({packet.packet_kind})",
        f"  Source id: {packet.source_id}",
        f"  JSON key: {packet.json_key}",
        f"  Component hint: {packet.component_hint}",
        f"  Status: {packet.status}",
        f"  Passive: {packet.passive}",
    ]


def _mount_lines(mount: StylePerformanceArcLiveGuiImplementationComponentMount) -> list[str]:
    return [
        f"- {mount.order}. {mount.component_key} ({mount.component_type})",
        f"  Region: {mount.region_key}",
        f"  Source packet: {mount.source_packet_key}",
        f"  Test id: {mount.test_id}",
        f"  Mount enabled: {mount.mount_enabled}",
        f"  Blocked reason: {mount.blocked_reason}",
        f"  Operator action: {mount.operator_action}",
    ]


def _fixture_lines(bundle: StylePerformanceArcLiveGuiImplementationFixtureBundle) -> list[str]:
    return [
        f"- {bundle.order}. {bundle.bundle_key} ({bundle.fixture_kind})",
        f"  Source packet: {bundle.source_packet_key}",
        f"  Source id: {bundle.source_id}",
        f"  JSON path: {bundle.json_path}",
        f"  Target scope: {bundle.target_scope}",
        f"  Passive: {bundle.passive}",
    ]


def _gate_lines(gate: StylePerformanceArcLiveGuiImplementationGate) -> list[str]:
    return [
        f"- {gate.key}: {gate.label}",
        f"  Status: {gate.status}",
        f"  Severity: {gate.severity}",
        f"  Source id: {gate.source_id}",
        f"  Message: {gate.message}",
        f"  Operator action: {gate.operator_action}",
        f"  Passive: {gate.passive}",
    ]


def format_style_performance_arc_live_gui_implementation_bridge_report(
    report: StylePerformanceArcLiveGuiImplementationBridgeReport,
) -> list[str]:
    """Format a passive GUI implementation bridge report."""

    lines = [
        "Live GUI implementation bridge summary:",
        f"- Bridge id: {report.bridge_id}",
        f"- Bridge label: {report.bridge_label}",
        f"- Bridge status: {report.bridge_status}",
        f"- Readiness id: {report.readiness_id}",
        f"- Contract id: {report.contract_id}",
        f"- Selected arc: {report.selected_arc_name} ({report.selected_arc_key})",
        f"- Scope: {report.scope}",
        f"- View-model summary: {report.view_model_summary}",
        f"- Component mount summary: {report.component_mount_summary}",
        f"- Fixture bundle summary: {report.fixture_bundle_summary}",
        "View-model packets:",
    ]
    for packet in report.view_model_packets:
        lines.extend(_packet_lines(packet))
    lines.append("Component mounts:")
    for mount in report.component_mounts:
        lines.extend(_mount_lines(mount))
    lines.append("Fixture bundles:")
    for bundle in report.fixture_bundles:
        lines.extend(_fixture_lines(bundle))
    lines.append("Implementation gates:")
    for gate in report.implementation_gates:
        lines.extend(_gate_lines(gate))
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
    if not remaining:
        raise ValueError(_USAGE)
    return remaining.pop(0)


def parse_style_performance_arc_live_gui_implementation_bridge_cli_args(
    argv: Sequence[str],
) -> dict[str, object]:
    """Parse implementation bridge CLI args for passive report composition."""

    bridge_label = _DEFAULT_BRIDGE_LABEL
    readiness_args: list[str] = []
    remaining = list(argv)
    while remaining:
        option = remaining.pop(0)
        if option == "--bridge-label":
            bridge_label = _normalize_nonblank(
                _pop_option_value(remaining),
                field="bridge_label",
            )
        else:
            readiness_args.append(option)
            if option != "--json":
                readiness_args.append(_pop_option_value(remaining))
    parsed = parse_style_performance_arc_live_gui_test_harness_readiness_cli_args(readiness_args)
    parsed["bridge_label"] = bridge_label
    return parsed


def _handle_cli_report(
    *,
    description: str | None,
    audio_path: Path | None,
    library_path: Path | None,
    capture_description: str | None,
    capture_audio_path: Path | None,
    capture_library_path: Path | None,
    rytm_sysex_path: Path | None,
    analog_four_sysex_path: Path | None,
    scope: str | None,
    selection_rank: int | None,
    total_minutes: int | None,
    segment_minutes: int | None,
    discovery_start: int | None,
    discovery_end: int | None,
    cue_number: int,
    lookahead_count: int,
    match_limit: int,
    take_count: int,
    slot_key: str,
    queue_label: str,
    capture_prefix: str,
    sidecar_label: str,
    screen_label: str,
    layout_key: str,
    viewport: str,
    render_target: str,
    density: str,
    overlay_label: str,
    frame_label: str,
    interaction_label: str,
    reducer_label: str,
    controller_label: str,
    playback_label: str,
    validation_label: str,
    harness_label: str,
    readiness_label: str,
    bridge_label: str,
    json_output: bool,
) -> int:
    try:
        report = build_style_performance_arc_live_gui_implementation_bridge_report(
            description=description,
            audio_path=audio_path,
            library_path=library_path,
            capture_description=capture_description,
            capture_audio_path=capture_audio_path,
            capture_library_path=capture_library_path,
            rytm_sysex_path=rytm_sysex_path,
            analog_four_sysex_path=analog_four_sysex_path,
            scope=scope,
            selection_rank=selection_rank,
            total_minutes=total_minutes,
            segment_minutes=segment_minutes,
            discovery_start=discovery_start,
            discovery_end=discovery_end,
            cue_number=cue_number,
            lookahead_count=lookahead_count,
            match_limit=match_limit,
            take_count=take_count,
            slot_key=slot_key,
            queue_label=queue_label,
            capture_prefix=capture_prefix,
            sidecar_label=sidecar_label,
            screen_label=screen_label,
            layout_key=layout_key,
            viewport=viewport,
            render_target=render_target,
            density=density,
            overlay_label=overlay_label,
            frame_label=frame_label,
            interaction_label=interaction_label,
            reducer_label=reducer_label,
            controller_label=controller_label,
            playback_label=playback_label,
            validation_label=validation_label,
            harness_label=harness_label,
            readiness_label=readiness_label,
            bridge_label=bridge_label,
        )
        if json_output:
            sys.stdout.write(
                json.dumps(
                    to_style_performance_arc_live_gui_implementation_bridge_json(report),
                    indent=2,
                    sort_keys=True,
                )
            )
            sys.stdout.write("\n")
            return 0
        lines = format_style_performance_arc_live_gui_implementation_bridge_report(report)
    except (OSError, ValueError, RuntimeError, NotImplementedError, TypeError, KeyError) as exc:
        sys.stderr.write(f"Error: {exc}\n")
        return 2
    for line in lines:
        sys.stdout.write(f"{line}\n")
    return 0


def _format_cli_error(exc: Exception) -> str:
    return f"Error: {exc}"


STYLE_PERFORMANCE_ARC_LIVE_GUI_IMPLEMENTATION_BRIDGE_CLI_COMMAND: Final[CliCommand] = CliCommand(
    name="style-performance-arc-live-gui-implementation-bridge-report",
    summary="Compose passive GUI readiness into future implementation wiring metadata.",
    args_parser=parse_style_performance_arc_live_gui_implementation_bridge_cli_args,
    handler=_handle_cli_report,
    error_formatter=_format_cli_error,
)

register(STYLE_PERFORMANCE_ARC_LIVE_GUI_IMPLEMENTATION_BRIDGE_CLI_COMMAND)

__all__ = [
    "BRIDGE_VERSION",
    "REPORT_TITLE",
    "SAFETY_LINES",
    "SOURCE_MODULE",
    "STYLE_PERFORMANCE_ARC_LIVE_GUI_IMPLEMENTATION_BRIDGE_CLI_COMMAND",
    "StylePerformanceArcLiveGuiImplementationBridgeReport",
    "StylePerformanceArcLiveGuiImplementationComponentMount",
    "StylePerformanceArcLiveGuiImplementationFixtureBundle",
    "StylePerformanceArcLiveGuiImplementationGate",
    "StylePerformanceArcLiveGuiImplementationViewModelPacket",
    "build_style_performance_arc_live_gui_implementation_bridge_from_readiness",
    "build_style_performance_arc_live_gui_implementation_bridge_report",
    "format_style_performance_arc_live_gui_implementation_bridge_report",
    "parse_style_performance_arc_live_gui_implementation_bridge_cli_args",
    "to_style_performance_arc_live_gui_implementation_bridge_json",
]
