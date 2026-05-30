"""Declarative live-GUI contract facts for passive report builders."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final


@dataclass(frozen=True)
class LiveGuiScreenComponentSpec:
    """Static component metadata for the live GUI screen contract."""

    key: str
    region_key: str
    component_type: str
    label: str
    status_source: str
    value_source: str
    source: str
    operator_action: str


@dataclass(frozen=True)
class LiveGuiDesktopViewportSpec:
    """Static viewport metadata for future desktop surfaces."""

    viewport_key: str
    width_px: int
    height_px: int
    density_mode: str


@dataclass(frozen=True)
class LiveGuiDesktopRegionSpec:
    """Static desktop layout-region metadata."""

    region_key: str
    order: int
    label: str
    role: str
    source_component_key: str
    grid_area: str
    min_width_px: int
    min_height_px: int


@dataclass(frozen=True)
class LiveGuiDesktopMountRegionSpec:
    """Static bridge-mount to desktop-region mapping."""

    component_key: str
    region_key: str


@dataclass(frozen=True)
class LiveGuiDesktopStyleTokenSpec:
    """Static desktop style-token metadata."""

    token_key: str
    label: str
    token_type: str
    value_hint: str


LIVE_GUI_SCREEN_COMPONENT_SPECS: Final[tuple[LiveGuiScreenComponentSpec, ...]] = (
    LiveGuiScreenComponentSpec(
        key="selected-arc",
        region_key="header",
        component_type="badge",
        label="Selected arc",
        status_source="sidecar_status",
        value_source="selected_arc",
        source="live_gui_sidecar_session.selected_arc",
        operator_action="Display the selected performance arc and scope.",
    ),
    LiveGuiScreenComponentSpec(
        key="sidecar-status",
        region_key="header",
        component_type="status",
        label="Sidecar status",
        status_source="sidecar_status",
        value_source="sidecar_status",
        source="live_gui_sidecar_session.sidecar_status",
        operator_action="Display the passive sidecar state badge.",
    ),
    LiveGuiScreenComponentSpec(
        key="current-cue",
        region_key="cue-strip",
        component_type="cue",
        label="Current cue",
        status_source="sidecar_status",
        value_source="current_cue_label",
        source="live_gui_sidecar_session.current_cue_label",
        operator_action="Display the cue currently being rehearsed.",
    ),
    LiveGuiScreenComponentSpec(
        key="next-cues",
        region_key="cue-strip",
        component_type="lookahead",
        label="Next cues",
        status_source="queued",
        value_source="next_cue_labels",
        source="live_gui_sidecar_session.next_cue_labels",
        operator_action="Display passive lookahead cue labels.",
    ),
)

LIVE_GUI_DESKTOP_VIEWPORT_SPECS: Final[tuple[LiveGuiDesktopViewportSpec, ...]] = (
    LiveGuiDesktopViewportSpec("desktop", 1440, 900, "requested"),
    LiveGuiDesktopViewportSpec("tablet", 1024, 768, "requested"),
    LiveGuiDesktopViewportSpec("compact", 768, 1024, "compact"),
)

LIVE_GUI_DESKTOP_REGION_SPECS: Final[tuple[LiveGuiDesktopRegionSpec, ...]] = (
    LiveGuiDesktopRegionSpec(
        "region-current-cue",
        1,
        "Current cue",
        "main",
        "current-cue-panel",
        "cue",
        420,
        240,
    ),
    LiveGuiDesktopRegionSpec(
        "region-machine-grid",
        2,
        "Machines",
        "status-grid",
        "machine-panels",
        "machines",
        520,
        240,
    ),
    LiveGuiDesktopRegionSpec(
        "region-analyzer",
        3,
        "Analyzer",
        "meter-stack",
        "analyzer-overlay",
        "analyzer",
        420,
        220,
    ),
    LiveGuiDesktopRegionSpec(
        "region-capture-review",
        4,
        "Capture review",
        "review-table",
        "capture-review-panel",
        "capture",
        520,
        220,
    ),
    LiveGuiDesktopRegionSpec(
        "region-controls",
        5,
        "Controls",
        "action-bar",
        "controller-actions",
        "controls",
        420,
        120,
    ),
    LiveGuiDesktopRegionSpec(
        "region-harness",
        6,
        "Harness",
        "validation",
        "test-harness-panel",
        "harness",
        520,
        160,
    ),
)

LIVE_GUI_DESKTOP_MOUNT_REGION_SPECS: Final[tuple[LiveGuiDesktopMountRegionSpec, ...]] = (
    LiveGuiDesktopMountRegionSpec("current-cue-panel", "region-current-cue"),
    LiveGuiDesktopMountRegionSpec("machine-panels", "region-machine-grid"),
    LiveGuiDesktopMountRegionSpec("analyzer-overlay", "region-analyzer"),
    LiveGuiDesktopMountRegionSpec("capture-review-panel", "region-capture-review"),
    LiveGuiDesktopMountRegionSpec("controller-actions", "region-controls"),
    LiveGuiDesktopMountRegionSpec("test-harness-panel", "region-harness"),
)

LIVE_GUI_DESKTOP_APP_STYLE_TOKEN_SPECS: Final[tuple[LiveGuiDesktopStyleTokenSpec, ...]] = (
    LiveGuiDesktopStyleTokenSpec(
        "token-surface",
        "Surface",
        "color",
        "operator dark neutral surface",
    ),
    LiveGuiDesktopStyleTokenSpec("token-panel", "Panel", "color", "low-glare machine panel"),
    LiveGuiDesktopStyleTokenSpec(
        "token-warning",
        "Warning",
        "color",
        "high-contrast hold/repeat warning",
    ),
    LiveGuiDesktopStyleTokenSpec(
        "token-disabled",
        "Disabled",
        "state",
        "disabled active-control affordance",
    ),
)
