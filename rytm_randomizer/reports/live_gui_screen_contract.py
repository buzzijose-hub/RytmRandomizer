"""Passive live GUI screen contract packet for sidecar rehearsal state."""

from __future__ import annotations

import hashlib
import json
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Final

from ..cli_registry import CliCommand, register
from ..data.live_gui_contracts import LIVE_GUI_SCREEN_COMPONENT_SPECS
from ..style_analysis.feature_report import FeatureReport
from .dual_machine_style_kit_selection import normalize_selection_scope
from .formatter import (
    SAFETY_SECTION_HEADER,
    PassiveReportHeader,
    passive_report_lines,
    powershell_literal_arg,
)
from .live_gui_common import format_cli_error as _format_cli_error
from .live_gui_common import pop_option_value
from .live_gui_sidecar_session import (
    StylePerformanceArcLiveGuiSidecarSessionReport,
    build_style_performance_arc_live_gui_sidecar_session_report,
    to_style_performance_arc_live_gui_sidecar_session_json,
)

REPORT_TITLE: Final[str] = "RytmRandomizer passive style performance arc live GUI screen contract"
SOURCE_MODULE: Final[str] = "reports.live_gui_screen_contract"
GUI_SCREEN_CONTRACT_VERSION: Final[str] = "live-gui-screen-contract-v1"
SAFETY_LINES: Final[tuple[str, ...]] = (
    "passive/read-only",
    "Passive GUI screen contract only",
    "composes live GUI sidecar session only",
    "deterministic GUI layout state only",
    "screen components are metadata only",
    "interaction controls are disabled metadata only",
    "future desktop GUI only",
    "future audio analyzer comparison only",
    "JSON/stdout only",
    "path options are read-only inputs",
    "no GUI launch",
    "no file writing",
    "no audio recording",
    "no real MIDI rendering",
    "no MIDI sending",
    "no port opening",
    "no command execution",
    "no hardware mutation",
    "no hardware required",
)
_HEADER: Final[PassiveReportHeader] = PassiveReportHeader(
    title=REPORT_TITLE,
    source_module=SOURCE_MODULE,
)
_DEFAULT_CUE_NUMBER: Final[int] = 1
_DEFAULT_LOOKAHEAD_COUNT: Final[int] = 1
_DEFAULT_MATCH_LIMIT: Final[int] = 3
_DEFAULT_TAKE_COUNT: Final[int] = 2
_DEFAULT_QUEUE_LABEL: Final[str] = "Live GUI capture queue"
_DEFAULT_CAPTURE_PREFIX: Final[str] = "rehearsal"
_DEFAULT_SLOT_KEY: Final[str] = "capture-001"
_DEFAULT_SIDECAR_LABEL: Final[str] = "Live GUI sidecar session"
_DEFAULT_SCREEN_LABEL: Final[str] = "Live GUI screen contract"
_DEFAULT_LAYOUT_KEY: Final[str] = "operator-cockpit"
_DEFAULT_VIEWPORT: Final[str] = "desktop"
_VIEWPORTS: Final[tuple[str, ...]] = ("desktop", "tablet", "compact")
_USAGE: Final[str] = (
    "style-performance-arc-live-gui-screen-contract-report usage: "
    "(--description <text>|--audio <path>|--library <dir>) "
    "(--capture-description <text>|--capture-audio <path>|--capture-library <dir>) "
    "[--rytm <syx-path>] [--analog-four <syx-path>] "
    "[--scope dual|rytm-only|analog-four-only|a4-only] "
    "[--rank N] [--total-minutes N] [--segment-minutes N] "
    "[--discovery-start N] [--discovery-end N] "
    "[--cue N] [--lookahead N] [--matches N] "
    "[--takes N] [--slot capture-001] "
    "[--label <text>] [--capture-prefix <text>] "
    "[--sidecar-label <text>] [--screen-label <text>] "
    "[--layout <key>] [--viewport desktop|tablet|compact] [--json]"
)
_CLI_OPTIONS: Final[tuple[str, ...]] = (
    "--description",
    "--audio",
    "--library",
    "--capture-description",
    "--capture-audio",
    "--capture-library",
    "--rytm",
    "--analog-four",
    "--scope",
    "--rank",
    "--total-minutes",
    "--segment-minutes",
    "--discovery-start",
    "--discovery-end",
    "--cue",
    "--lookahead",
    "--matches",
    "--takes",
    "--slot",
    "--label",
    "--capture-prefix",
    "--sidecar-label",
    "--screen-label",
    "--layout",
    "--viewport",
    "--json",
)


@dataclass(frozen=True)
class StylePerformanceArcLiveGuiScreenAction:
    """One passive primary screen action descriptor."""

    key: str
    label: str
    status: str
    enabled: bool
    reason: str
    operator_action: str


@dataclass(frozen=True)
class StylePerformanceArcLiveGuiScreenAlert:
    """One GUI banner alert descriptor."""

    key: str
    severity: str
    label: str
    message: str
    source: str


@dataclass(frozen=True)
class StylePerformanceArcLiveGuiScreenRegion:
    """One deterministic screen layout region."""

    key: str
    label: str
    role: str
    order: int
    source: str
    component_keys: tuple[str, ...]


@dataclass(frozen=True)
class StylePerformanceArcLiveGuiScreenComponent:
    """One deterministic GUI component state row."""

    key: str
    region_key: str
    component_type: str
    label: str
    status: str
    value: str
    enabled: bool
    source: str
    operator_action: str


@dataclass(frozen=True)
class StylePerformanceArcLiveGuiScreenTableRow:
    """One analyzer/capture table row for future GUI rendering."""

    key: str
    row_type: str
    label: str
    status: str
    selected: bool
    cells: tuple[str, ...]
    operator_action: str


@dataclass(frozen=True)
class StylePerformanceArcLiveGuiScreenContractReport:
    """Passive GUI screen contract composed from a sidecar session."""

    sidecar_session: StylePerformanceArcLiveGuiSidecarSessionReport
    screen_version: str
    screen_id: str
    screen_label: str
    screen_status: str
    layout_key: str
    viewport: str
    current_cue_label: str
    next_cue_labels: tuple[str, ...]
    primary_action: StylePerformanceArcLiveGuiScreenAction
    alerts: tuple[StylePerformanceArcLiveGuiScreenAlert, ...]
    regions: tuple[StylePerformanceArcLiveGuiScreenRegion, ...]
    components: tuple[StylePerformanceArcLiveGuiScreenComponent, ...]
    table_rows: tuple[StylePerformanceArcLiveGuiScreenTableRow, ...]
    interaction_controls: tuple[StylePerformanceArcLiveGuiScreenComponent, ...]
    blocked_actions: tuple[str, ...]
    replay_commands: tuple[str, ...]

    @property
    def sidecar_session_id(self) -> str:
        """Return upstream sidecar session id."""

        return self.sidecar_session.sidecar_id

    @property
    def selected_arc_key(self) -> str:
        """Return selected arc key."""

        return self.sidecar_session.selected_arc_key

    @property
    def selected_arc_name(self) -> str:
        """Return selected arc name."""

        return self.sidecar_session.selected_arc_name

    @property
    def scope(self) -> str:
        """Return selected machine scope."""

        return self.sidecar_session.scope


def _source_count(
    *,
    description: str | None,
    feature_report: FeatureReport | None,
    audio_path: Path | None,
    library_path: Path | None,
) -> int:
    return sum(
        (
            description is not None,
            feature_report is not None,
            audio_path is not None,
            library_path is not None,
        )
    )


def _capture_source_count(
    *,
    capture_description: str | None,
    capture_feature_report: FeatureReport | None,
    capture_audio_path: Path | None,
    capture_library_path: Path | None,
) -> int:
    return _source_count(
        description=capture_description,
        feature_report=capture_feature_report,
        audio_path=capture_audio_path,
        library_path=capture_library_path,
    )


def _normalize_nonblank(value: str, *, field: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field} must not be blank")
    return normalized


def _normalize_viewport(value: str) -> str:
    normalized = _normalize_nonblank(value, field="viewport")
    if normalized not in _VIEWPORTS:
        raise ValueError("viewport must be desktop, tablet, or compact")
    return normalized


def _screen_id(
    sidecar: StylePerformanceArcLiveGuiSidecarSessionReport,
    *,
    screen_label: str,
    layout_key: str,
    viewport: str,
) -> str:
    payload = "|".join(
        (
            GUI_SCREEN_CONTRACT_VERSION,
            sidecar.sidecar_id,
            sidecar.capture_review_id,
            screen_label,
            layout_key,
            viewport,
            sidecar.sidecar_status,
        )
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def _next_cue_labels(
    sidecar: StylePerformanceArcLiveGuiSidecarSessionReport,
) -> tuple[str, ...]:
    return sidecar.next_cue_labels or ("No lookahead cue queued",)


def _primary_action(
    sidecar: StylePerformanceArcLiveGuiSidecarSessionReport,
) -> StylePerformanceArcLiveGuiScreenAction:
    if sidecar.sidecar_status == "ready":
        label = "Show GO"
    elif sidecar.sidecar_status == "needs-repeat":
        label = "Repeat take"
    else:
        label = "Hold workflow"
    return StylePerformanceArcLiveGuiScreenAction(
        key="primary-action",
        label=label,
        status=sidecar.sidecar_status,
        enabled=False,
        reason="Passive screen contract labels the action; active controls remain disabled.",
        operator_action=sidecar.next_operator_action,
    )


def _alerts(
    sidecar: StylePerformanceArcLiveGuiSidecarSessionReport,
) -> tuple[StylePerformanceArcLiveGuiScreenAlert, ...]:
    if sidecar.sidecar_status == "ready":
        return ()
    if sidecar.sidecar_status == "needs-repeat":
        return (
            StylePerformanceArcLiveGuiScreenAlert(
                key="repeat-take",
                severity="warning",
                label="Repeat take",
                message=sidecar.next_operator_action,
                source="live_gui_sidecar_session.sidecar_status",
            ),
        )
    return (
        StylePerformanceArcLiveGuiScreenAlert(
            key="hold-workflow",
            severity="critical",
            label="Hold workflow",
            message=sidecar.next_operator_action,
            source="live_gui_sidecar_session.sidecar_status",
        ),
    )


def _base_components(
    sidecar: StylePerformanceArcLiveGuiSidecarSessionReport,
    *,
    next_cues: tuple[str, ...],
    primary_action: StylePerformanceArcLiveGuiScreenAction,
) -> tuple[StylePerformanceArcLiveGuiScreenComponent, ...]:
    status_values = {
        "sidecar_status": sidecar.sidecar_status,
        "queued": "queued",
    }
    value_values = {
        "selected_arc": f"{sidecar.selected_arc_key} / {sidecar.selected_arc_name}",
        "sidecar_status": sidecar.sidecar_status,
        "current_cue_label": sidecar.current_cue_label,
        "next_cue_labels": ", ".join(next_cues),
    }
    components = [
        *(
            StylePerformanceArcLiveGuiScreenComponent(
                key=spec.key,
                region_key=spec.region_key,
                component_type=spec.component_type,
                label=spec.label,
                status=status_values[spec.status_source],
                value=value_values[spec.value_source],
                enabled=False,
                source=spec.source,
                operator_action=spec.operator_action,
            )
            for spec in LIVE_GUI_SCREEN_COMPONENT_SPECS
        ),
        StylePerformanceArcLiveGuiScreenComponent(
            key=primary_action.key,
            region_key="cue-strip",
            component_type="button-disabled",
            label=primary_action.label,
            status=primary_action.status,
            value=primary_action.reason,
            enabled=primary_action.enabled,
            source="live_gui_sidecar_session.next_operator_action",
            operator_action=primary_action.operator_action,
        ),
    ]
    components.extend(
        StylePerformanceArcLiveGuiScreenComponent(
            key=f"panel-{panel.key}",
            region_key="machine-panels" if panel.key == "machines" else "header",
            component_type="panel",
            label=panel.label,
            status=panel.status,
            value=panel.source,
            enabled=False,
            source=panel.source,
            operator_action=panel.operator_action,
        )
        for panel in sidecar.panels
    )
    return tuple(components)


def _table_rows(
    sidecar: StylePerformanceArcLiveGuiSidecarSessionReport,
) -> tuple[StylePerformanceArcLiveGuiScreenTableRow, ...]:
    rows: list[StylePerformanceArcLiveGuiScreenTableRow] = []
    rows.extend(
        StylePerformanceArcLiveGuiScreenTableRow(
            key=f"analyzer-{row.key}",
            row_type="analyzer",
            label=row.label,
            status=row.status,
            selected=False,
            cells=(
                row.target_value,
                row.captured_value,
                row.delta,
                row.decision,
            ),
            operator_action=row.operator_action,
        )
        for row in sidecar.analyzer_rows
    )
    rows.extend(
        StylePerformanceArcLiveGuiScreenTableRow(
            key=f"capture-{row.slot_key}",
            row_type="capture",
            label=row.capture_label,
            status=row.status,
            selected=row.selected,
            cells=(
                row.slot_key,
                row.decision,
                row.suggested_filename,
                "; ".join(row.hold_reasons) if row.hold_reasons else "no hold reasons",
            ),
            operator_action=row.operator_action,
        )
        for row in sidecar.capture_rows
    )
    if not sidecar.analyzer_rows:
        rows.append(
            StylePerformanceArcLiveGuiScreenTableRow(
                key="empty-analyzer",
                row_type="empty",
                label="Analyzer table empty",
                status="empty",
                selected=False,
                cells=("No analyzer rows available",),
                operator_action="Keep analyzer table visible with an empty-state row.",
            )
        )
    if not sidecar.capture_rows:
        rows.append(
            StylePerformanceArcLiveGuiScreenTableRow(
                key="empty-capture",
                row_type="empty",
                label="Capture table empty",
                status="empty",
                selected=False,
                cells=("No capture rows available",),
                operator_action="Keep capture table visible with an empty-state row.",
            )
        )
    return tuple(rows)


def _table_components(
    rows: Sequence[StylePerformanceArcLiveGuiScreenTableRow],
) -> tuple[StylePerformanceArcLiveGuiScreenComponent, ...]:
    return tuple(
        StylePerformanceArcLiveGuiScreenComponent(
            key=row.key,
            region_key=(
                "analyzer-table"
                if row.key.startswith(("analyzer-", "empty-analyzer"))
                else "capture-table"
            ),
            component_type="table-row",
            label=row.label,
            status=row.status,
            value=" | ".join(row.cells),
            enabled=False,
            source=f"live_gui_screen_contract.{row.row_type}_rows",
            operator_action=row.operator_action,
        )
        for row in rows
    )


def _disabled_control_components(
    sidecar: StylePerformanceArcLiveGuiSidecarSessionReport,
) -> tuple[StylePerformanceArcLiveGuiScreenComponent, ...]:
    return tuple(
        StylePerformanceArcLiveGuiScreenComponent(
            key=f"disabled-{control.key}",
            region_key="safety-bar",
            component_type="disabled-control",
            label=control.label,
            status="disabled",
            value=control.reason,
            enabled=control.enabled,
            source="live_gui_sidecar_session.disabled_controls",
            operator_action="Keep this control disabled in passive rehearsal screens.",
        )
        for control in sidecar.disabled_controls
    )


def _component_keys_by_region(
    components: Sequence[StylePerformanceArcLiveGuiScreenComponent],
) -> dict[str, tuple[str, ...]]:
    region_keys = ("header", "cue-strip", "machine-panels", "analyzer-table", "capture-table")
    grouped: dict[str, tuple[str, ...]] = {}
    for region_key in region_keys:
        grouped[region_key] = tuple(
            component.key for component in components if component.region_key == region_key
        )
    grouped["safety-bar"] = tuple(
        component.key for component in components if component.region_key == "safety-bar"
    )
    return grouped


def _regions(
    components: Sequence[StylePerformanceArcLiveGuiScreenComponent],
) -> tuple[StylePerformanceArcLiveGuiScreenRegion, ...]:
    grouped = _component_keys_by_region(components)
    return (
        StylePerformanceArcLiveGuiScreenRegion(
            key="header",
            label="Header",
            role="summary",
            order=1,
            source="live_gui_sidecar_session.summary",
            component_keys=grouped["header"],
        ),
        StylePerformanceArcLiveGuiScreenRegion(
            key="cue-strip",
            label="Cue strip",
            role="cue",
            order=2,
            source="live_gui_sidecar_session.cues",
            component_keys=grouped["cue-strip"],
        ),
        StylePerformanceArcLiveGuiScreenRegion(
            key="machine-panels",
            label="Machine panels",
            role="machine-status",
            order=3,
            source="live_gui_sidecar_session.panels",
            component_keys=grouped["machine-panels"],
        ),
        StylePerformanceArcLiveGuiScreenRegion(
            key="analyzer-table",
            label="Analyzer table",
            role="analysis",
            order=4,
            source="live_gui_sidecar_session.analyzer_rows",
            component_keys=grouped["analyzer-table"],
        ),
        StylePerformanceArcLiveGuiScreenRegion(
            key="capture-table",
            label="Capture table",
            role="capture",
            order=5,
            source="live_gui_sidecar_session.capture_rows",
            component_keys=grouped["capture-table"],
        ),
        StylePerformanceArcLiveGuiScreenRegion(
            key="safety-bar",
            label="Safety bar",
            role="safety",
            order=6,
            source="live_gui_sidecar_session.disabled_controls",
            component_keys=grouped["safety-bar"],
        ),
    )


def _blocked_actions(
    sidecar: StylePerformanceArcLiveGuiSidecarSessionReport,
) -> tuple[str, ...]:
    actions = (
        *sidecar.blocked_actions,
        "no GUI screen launch",
        "no GUI-triggered MIDI sends",
        "no GUI-triggered port opening",
        "no automatic audio recording",
        "no automatic hardware arming",
        "no automatic kit mutation",
        "no MIDI sending",
        "no port opening",
    )
    return tuple(dict.fromkeys(actions))


def _replay_command(
    sidecar: StylePerformanceArcLiveGuiSidecarSessionReport,
    *,
    screen_label: str,
    layout_key: str,
    viewport: str,
) -> str:
    fallback_command = (
        "python -m rytm_randomizer.cli " "style-performance-arc-live-gui-screen-contract-report"
    )
    if sidecar.replay_commands:
        sidecar_command = sidecar.replay_commands[0]
        command = sidecar_command.replace(
            "style-performance-arc-live-gui-sidecar-session-report",
            "style-performance-arc-live-gui-screen-contract-report",
            1,
        )
        if command == sidecar_command:
            command = fallback_command
    else:
        command = fallback_command
    return (
        f"{command} "
        f"--screen-label {powershell_literal_arg(screen_label)} "
        f"--layout {powershell_literal_arg(layout_key)} "
        f"--viewport {powershell_literal_arg(viewport)}"
    )


def build_style_performance_arc_live_gui_screen_contract_from_sidecar_session(
    sidecar_session: StylePerformanceArcLiveGuiSidecarSessionReport,
    *,
    screen_label: str = _DEFAULT_SCREEN_LABEL,
    layout_key: str = _DEFAULT_LAYOUT_KEY,
    viewport: str = _DEFAULT_VIEWPORT,
) -> StylePerformanceArcLiveGuiScreenContractReport:
    """Build one passive GUI screen contract from a sidecar session."""

    normalized_label = _normalize_nonblank(screen_label, field="screen_label")
    normalized_layout = _normalize_nonblank(layout_key, field="layout_key")
    normalized_viewport = _normalize_viewport(viewport)
    next_cues = _next_cue_labels(sidecar_session)
    primary = _primary_action(sidecar_session)
    rows = _table_rows(sidecar_session)
    disabled_controls = _disabled_control_components(sidecar_session)
    components = (
        *_base_components(sidecar_session, next_cues=next_cues, primary_action=primary),
        *_table_components(rows),
        *disabled_controls,
    )
    return StylePerformanceArcLiveGuiScreenContractReport(
        sidecar_session=sidecar_session,
        screen_version=GUI_SCREEN_CONTRACT_VERSION,
        screen_id=_screen_id(
            sidecar_session,
            screen_label=normalized_label,
            layout_key=normalized_layout,
            viewport=normalized_viewport,
        ),
        screen_label=normalized_label,
        screen_status=sidecar_session.sidecar_status,
        layout_key=normalized_layout,
        viewport=normalized_viewport,
        current_cue_label=sidecar_session.current_cue_label,
        next_cue_labels=next_cues,
        primary_action=primary,
        alerts=_alerts(sidecar_session),
        regions=_regions(components),
        components=components,
        table_rows=rows,
        interaction_controls=(
            tuple(
                component
                for component in components
                if component.component_type.endswith("control")
            )
            + tuple(component for component in components if component.key == primary.key)
        ),
        blocked_actions=_blocked_actions(sidecar_session),
        replay_commands=(
            _replay_command(
                sidecar_session,
                screen_label=normalized_label,
                layout_key=normalized_layout,
                viewport=normalized_viewport,
            ),
            *sidecar_session.replay_commands,
        ),
    )


def build_style_performance_arc_live_gui_screen_contract_report(
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
    cue_number: int = _DEFAULT_CUE_NUMBER,
    lookahead_count: int = _DEFAULT_LOOKAHEAD_COUNT,
    match_limit: int = _DEFAULT_MATCH_LIMIT,
    take_count: int = _DEFAULT_TAKE_COUNT,
    slot_key: str = _DEFAULT_SLOT_KEY,
    queue_label: str = _DEFAULT_QUEUE_LABEL,
    capture_prefix: str = _DEFAULT_CAPTURE_PREFIX,
    sidecar_label: str = _DEFAULT_SIDECAR_LABEL,
    screen_label: str = _DEFAULT_SCREEN_LABEL,
    layout_key: str = _DEFAULT_LAYOUT_KEY,
    viewport: str = _DEFAULT_VIEWPORT,
) -> StylePerformanceArcLiveGuiScreenContractReport:
    """Build a passive GUI screen contract from source evidence."""

    if (
        _source_count(
            description=description,
            feature_report=feature_report,
            audio_path=audio_path,
            library_path=library_path,
        )
        != 1
    ):
        raise ValueError("live GUI screen contract report requires exactly one reference source")
    if description is not None and not description.strip():
        raise ValueError("description must include reference evidence")
    if (
        _capture_source_count(
            capture_description=capture_description,
            capture_feature_report=capture_feature_report,
            capture_audio_path=capture_audio_path,
            capture_library_path=capture_library_path,
        )
        != 1
    ):
        raise ValueError(
            "live GUI screen contract report requires exactly one captured evidence source"
        )
    sidecar = build_style_performance_arc_live_gui_sidecar_session_report(
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
    )
    return build_style_performance_arc_live_gui_screen_contract_from_sidecar_session(
        sidecar,
        screen_label=screen_label,
        layout_key=layout_key,
        viewport=viewport,
    )


def _action_json(action: StylePerformanceArcLiveGuiScreenAction) -> dict[str, object]:
    return {
        "key": action.key,
        "label": action.label,
        "status": action.status,
        "enabled": action.enabled,
        "reason": action.reason,
        "operator_action": action.operator_action,
    }


def _alert_json(alert: StylePerformanceArcLiveGuiScreenAlert) -> dict[str, object]:
    return {
        "key": alert.key,
        "severity": alert.severity,
        "label": alert.label,
        "message": alert.message,
        "source": alert.source,
    }


def _region_json(region: StylePerformanceArcLiveGuiScreenRegion) -> dict[str, object]:
    return {
        "key": region.key,
        "label": region.label,
        "role": region.role,
        "order": region.order,
        "source": region.source,
        "component_keys": list(region.component_keys),
    }


def _component_json(
    component: StylePerformanceArcLiveGuiScreenComponent,
) -> dict[str, object]:
    return {
        "key": component.key,
        "region_key": component.region_key,
        "component_type": component.component_type,
        "label": component.label,
        "status": component.status,
        "value": component.value,
        "enabled": component.enabled,
        "source": component.source,
        "operator_action": component.operator_action,
    }


def _table_row_json(row: StylePerformanceArcLiveGuiScreenTableRow) -> dict[str, object]:
    return {
        "key": row.key,
        "row_type": row.row_type,
        "label": row.label,
        "status": row.status,
        "selected": row.selected,
        "cells": list(row.cells),
        "operator_action": row.operator_action,
    }


def to_style_performance_arc_live_gui_screen_contract_json(
    report: StylePerformanceArcLiveGuiScreenContractReport,
) -> dict[str, object]:
    """Return deterministic JSON-ready live GUI screen contract payload."""

    sidecar_json = to_style_performance_arc_live_gui_sidecar_session_json(report.sidecar_session)
    return {
        "live_gui_screen_contract": {
            "screen_version": report.screen_version,
            "screen_id": report.screen_id,
            "screen_label": report.screen_label,
            "screen_status": report.screen_status,
            "layout_key": report.layout_key,
            "viewport": report.viewport,
            "selected_arc_key": report.selected_arc_key,
            "selected_arc_name": report.selected_arc_name,
            "scope": report.scope,
            "sidecar_session_id": report.sidecar_session_id,
            "capture_review_id": report.sidecar_session.capture_review_id,
            "current_cue_label": report.current_cue_label,
            "next_cue_labels": list(report.next_cue_labels),
            "primary_action": _action_json(report.primary_action),
            "alerts": [_alert_json(alert) for alert in report.alerts],
            "regions": [_region_json(region) for region in report.regions],
            "components": [_component_json(component) for component in report.components],
            "table_rows": [_table_row_json(row) for row in report.table_rows],
            "interaction_controls": [
                _component_json(component) for component in report.interaction_controls
            ],
            "blocked_actions": list(report.blocked_actions),
            "replay_commands": list(report.replay_commands),
        },
        "live_gui_sidecar_session": sidecar_json["live_gui_sidecar_session"],
        "live_gui_capture_review": sidecar_json["live_gui_capture_review"],
        "live_gui_capture_queue": sidecar_json["live_gui_capture_queue"],
        "live_gui_rehearsal_session": sidecar_json["live_gui_rehearsal_session"],
        "live_gui_analyzer_readiness": sidecar_json["live_gui_analyzer_readiness"],
        "live_analyzer_targets": sidecar_json["live_analyzer_targets"],
        "live_analyzer_handoff": sidecar_json["live_analyzer_handoff"],
        "live_control_surface": sidecar_json["live_control_surface"],
        "live_readiness": sidecar_json["live_readiness"],
        "live_state_packet": sidecar_json["live_state_packet"],
        "live_command_deck": sidecar_json["live_command_deck"],
        "reference_match": sidecar_json["reference_match"],
        "safety": list(SAFETY_LINES),
    }


def _action_lines(action: StylePerformanceArcLiveGuiScreenAction) -> list[str]:
    state = "enabled" if action.enabled else "disabled"
    return [
        f"- {action.key} / {action.label}: {action.status} / {state}",
        f"  Reason: {action.reason}",
        f"  Action: {action.operator_action}",
    ]


def _alert_lines(alert: StylePerformanceArcLiveGuiScreenAlert) -> list[str]:
    return [
        f"- {alert.key} / {alert.label}: {alert.severity}",
        f"  Message: {alert.message}",
        f"  Source: {alert.source}",
    ]


def _region_lines(region: StylePerformanceArcLiveGuiScreenRegion) -> list[str]:
    return [
        f"- {region.order}. {region.key} / {region.label}: {region.role}",
        f"  Source: {region.source}",
        f"  Components: {', '.join(region.component_keys) or 'none'}",
    ]


def _component_lines(component: StylePerformanceArcLiveGuiScreenComponent) -> list[str]:
    state = "enabled" if component.enabled else "disabled"
    return [
        (
            f"- {component.key} / {component.label}: {component.component_type} / "
            f"{component.status} / {state}"
        ),
        f"  Region: {component.region_key}",
        f"  Value: {component.value}",
        f"  Action: {component.operator_action}",
    ]


def _table_row_lines(row: StylePerformanceArcLiveGuiScreenTableRow) -> list[str]:
    selected = "selected" if row.selected else "available"
    return [
        f"- {row.key} / {row.label}: {row.row_type} / {row.status} / {selected}",
        f"  Cells: {' | '.join(row.cells)}",
        f"  Action: {row.operator_action}",
    ]


def format_style_performance_arc_live_gui_screen_contract_report(
    report: StylePerformanceArcLiveGuiScreenContractReport,
) -> list[str]:
    """Return deterministic passive live GUI screen contract lines."""

    lines = [
        "Live GUI screen contract summary:",
        f"- Screen version: {report.screen_version}",
        f"- Screen id: {report.screen_id}",
        f"- Screen label: {report.screen_label}",
        f"- Screen status: {report.screen_status}",
        f"- Layout: {report.layout_key}",
        f"- Viewport: {report.viewport}",
        f"- Selected arc: {report.selected_arc_key} / {report.selected_arc_name}",
        f"- Scope: {report.scope}",
        f"- Sidecar session id: {report.sidecar_session_id}",
        f"- Capture review id: {report.sidecar_session.capture_review_id}",
        f"- Current cue: {report.current_cue_label}",
        f"- Next cues: {', '.join(report.next_cue_labels)}",
        "Primary passive action:",
        *_action_lines(report.primary_action),
        "Screen alerts:",
    ]
    if report.alerts:
        for alert in report.alerts:
            lines.extend(_alert_lines(alert))
    else:
        lines.append("- none")
    lines.append("Screen regions:")
    for region in report.regions:
        lines.extend(_region_lines(region))
    lines.append("Screen components:")
    for component in report.components:
        lines.extend(_component_lines(component))
    lines.append("Screen table rows:")
    for row in report.table_rows:
        lines.extend(_table_row_lines(row))
    lines.append("Interaction contract:")
    for component in report.interaction_controls:
        lines.extend(_component_lines(component))
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


def _parse_nonnegative_int(value: str, *, option: str) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise ValueError(f"{option} must be an integer") from exc
    if parsed < 0:
        raise ValueError(f"{option} must be >= 0")
    return parsed


def _parse_positive_int(value: str, *, option: str) -> int:
    parsed = _parse_nonnegative_int(value, option=option)
    if parsed < 1:
        raise ValueError(f"{option} must be >= 1")
    return parsed


def _pop_option_value(remaining: list[str]) -> str:
    return pop_option_value(remaining, usage=_USAGE)


def _parse_cli_args(argv: Sequence[str]) -> dict[str, object]:
    description: str | None = None
    audio_path: Path | None = None
    library_path: Path | None = None
    capture_description: str | None = None
    capture_audio_path: Path | None = None
    capture_library_path: Path | None = None
    rytm_sysex_path: Path | None = None
    analog_four_sysex_path: Path | None = None
    scope: str | None = None
    selection_rank: int | None = None
    total_minutes: int | None = None
    segment_minutes: int | None = None
    discovery_start: int | None = None
    discovery_end: int | None = None
    cue_number = _DEFAULT_CUE_NUMBER
    lookahead_count = _DEFAULT_LOOKAHEAD_COUNT
    match_limit = _DEFAULT_MATCH_LIMIT
    take_count = _DEFAULT_TAKE_COUNT
    slot_key = _DEFAULT_SLOT_KEY
    queue_label = _DEFAULT_QUEUE_LABEL
    capture_prefix = _DEFAULT_CAPTURE_PREFIX
    sidecar_label = _DEFAULT_SIDECAR_LABEL
    screen_label = _DEFAULT_SCREEN_LABEL
    layout_key = _DEFAULT_LAYOUT_KEY
    viewport = _DEFAULT_VIEWPORT
    json_output = False
    remaining = list(argv)
    while remaining:
        option = remaining.pop(0)
        if option == "--json":
            json_output = True
            continue
        if option not in _CLI_OPTIONS:
            raise ValueError(_USAGE)
        value = _pop_option_value(remaining)
        if option == "--description":
            description = value
        elif option == "--audio":
            audio_path = Path(value)
        elif option == "--library":
            library_path = Path(value)
        elif option == "--capture-description":
            capture_description = value
        elif option == "--capture-audio":
            capture_audio_path = Path(value)
        elif option == "--capture-library":
            capture_library_path = Path(value)
        elif option == "--rytm":
            rytm_sysex_path = Path(value)
        elif option == "--analog-four":
            analog_four_sysex_path = Path(value)
        elif option == "--scope":
            scope = normalize_selection_scope(value)
        elif option == "--rank":
            selection_rank = _parse_positive_int(value, option=option)
        elif option == "--total-minutes":
            total_minutes = _parse_positive_int(value, option=option)
        elif option == "--segment-minutes":
            segment_minutes = _parse_positive_int(value, option=option)
        elif option == "--discovery-start":
            discovery_start = _parse_nonnegative_int(value, option=option)
        elif option == "--discovery-end":
            discovery_end = _parse_nonnegative_int(value, option=option)
        elif option == "--cue":
            cue_number = _parse_positive_int(value, option=option)
        elif option == "--lookahead":
            lookahead_count = _parse_nonnegative_int(value, option=option)
        elif option == "--matches":
            match_limit = _parse_positive_int(value, option=option)
        elif option == "--takes":
            take_count = _parse_positive_int(value, option=option)
        elif option == "--slot":
            slot_key = _normalize_nonblank(value, field="slot")
        elif option == "--label":
            queue_label = _normalize_nonblank(value, field="label")
        elif option == "--capture-prefix":
            capture_prefix = _normalize_nonblank(value, field="capture_prefix")
        elif option == "--sidecar-label":
            sidecar_label = _normalize_nonblank(value, field="sidecar_label")
        elif option == "--screen-label":
            screen_label = _normalize_nonblank(value, field="screen_label")
        elif option == "--layout":
            layout_key = _normalize_nonblank(value, field="layout_key")
        else:
            viewport = _normalize_viewport(value)

    if description is not None and not description.strip():
        raise ValueError("description must include reference evidence")
    if capture_description is not None and not capture_description.strip():
        raise ValueError("capture description must include measured evidence")
    if (
        _source_count(
            description=description,
            feature_report=None,
            audio_path=audio_path,
            library_path=library_path,
        )
        != 1
    ):
        raise ValueError(_USAGE)
    if (
        _capture_source_count(
            capture_description=capture_description,
            capture_feature_report=None,
            capture_audio_path=capture_audio_path,
            capture_library_path=capture_library_path,
        )
        != 1
    ):
        raise ValueError(
            "live GUI screen contract report requires exactly one captured evidence source"
        )

    return {
        "description": description,
        "audio_path": audio_path,
        "library_path": library_path,
        "capture_description": capture_description,
        "capture_audio_path": capture_audio_path,
        "capture_library_path": capture_library_path,
        "rytm_sysex_path": rytm_sysex_path,
        "analog_four_sysex_path": analog_four_sysex_path,
        "scope": scope,
        "selection_rank": selection_rank,
        "total_minutes": total_minutes,
        "segment_minutes": segment_minutes,
        "discovery_start": discovery_start,
        "discovery_end": discovery_end,
        "cue_number": cue_number,
        "lookahead_count": lookahead_count,
        "match_limit": match_limit,
        "take_count": take_count,
        "slot_key": slot_key,
        "queue_label": queue_label,
        "capture_prefix": capture_prefix,
        "sidecar_label": sidecar_label,
        "screen_label": screen_label,
        "layout_key": layout_key,
        "viewport": viewport,
        "json_output": json_output,
    }


def parse_style_performance_arc_live_gui_screen_contract_cli_args(
    argv: Sequence[str],
) -> dict[str, object]:
    """Return parsed CLI args for screen-contract-compatible report commands."""

    return _parse_cli_args(argv)


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
    json_output: bool,
) -> int:
    try:
        report = build_style_performance_arc_live_gui_screen_contract_report(
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
        )
        if json_output:
            sys.stdout.write(
                json.dumps(
                    to_style_performance_arc_live_gui_screen_contract_json(report),
                    indent=2,
                    sort_keys=True,
                )
            )
            sys.stdout.write("\n")
            return 0
        lines = format_style_performance_arc_live_gui_screen_contract_report(report)
    except (OSError, ValueError, RuntimeError, NotImplementedError, TypeError, KeyError) as exc:
        sys.stderr.write(f"Error: {exc}\n")
        return 2
    sys.stdout.write("\n".join(lines))
    sys.stdout.write("\n")
    return 0


STYLE_PERFORMANCE_ARC_LIVE_GUI_SCREEN_CONTRACT_CLI_COMMAND: Final[CliCommand] = CliCommand(
    name="style-performance-arc-live-gui-screen-contract-report",
    summary="Compose passive sidecar state into a deterministic GUI screen contract.",
    args_parser=_parse_cli_args,
    handler=_handle_cli_report,
    error_formatter=_format_cli_error,
)

register(STYLE_PERFORMANCE_ARC_LIVE_GUI_SCREEN_CONTRACT_CLI_COMMAND)

__all__ = [
    "GUI_SCREEN_CONTRACT_VERSION",
    "REPORT_TITLE",
    "SAFETY_LINES",
    "SOURCE_MODULE",
    "STYLE_PERFORMANCE_ARC_LIVE_GUI_SCREEN_CONTRACT_CLI_COMMAND",
    "StylePerformanceArcLiveGuiScreenAction",
    "StylePerformanceArcLiveGuiScreenAlert",
    "StylePerformanceArcLiveGuiScreenComponent",
    "StylePerformanceArcLiveGuiScreenContractReport",
    "StylePerformanceArcLiveGuiScreenRegion",
    "StylePerformanceArcLiveGuiScreenTableRow",
    "build_style_performance_arc_live_gui_screen_contract_from_sidecar_session",
    "build_style_performance_arc_live_gui_screen_contract_report",
    "format_style_performance_arc_live_gui_screen_contract_report",
    "parse_style_performance_arc_live_gui_screen_contract_cli_args",
    "to_style_performance_arc_live_gui_screen_contract_json",
]
