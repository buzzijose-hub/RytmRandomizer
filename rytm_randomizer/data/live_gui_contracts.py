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
