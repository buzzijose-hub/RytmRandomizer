"""Passive scoped-randomization preview report (ScopeMask + depth macro).

Surfaces the deterministic :mod:`rytm_randomizer.behavior.scope` plan as BOTH
a passive text/JSON CLI report (via the ReportSpec platform) and a cockpit
panel (via ``panel_spec_from_report_spec``). The report renders a canonical
demonstration preview — a fixed mask + depth over the built-in V1.34 profile
registry — so the zero-argument command is deterministic and golden-capturable.

Passive: importing this module opens no ports, sends no MIDI, and the rendered
plan is preview-only. An operator arms-and-sends through the existing
``senders`` ArmedApply seam; this module never reaches it.
"""

from __future__ import annotations

from typing import Final

from ..behavior.scope import (
    ScopeMask,
    ScopePlan,
    TrackScope,
    build_track_scope,
    plan_scope,
)
from ..cli_registry import CliCommand, register
from .core import ReportSection, ReportSpec, make_spec_command
from .panel_spec import (
    PanelSectionDict,
    PanelSpecDict,
    badge,
    panel_spec,
    readiness_badges,
    rows_section,
    table_section,
)

REPORT_TITLE: Final[str] = "RytmRandomizer scoped-randomization preview"
SOURCE_MODULE: Final[str] = "reports.scoped_randomization_preview"
REPORT_VERSION: Final[str] = "scope-preview-v1"
CLI_NAME: Final[str] = "scoped-randomization-preview"
PANEL_ID: Final[str] = "scoped-randomization"

SAFETY_LINES: Final[tuple[str, ...]] = (
    "passive/read-only",
    "preview plan only",
    "no MIDI sending",
    "no port opening",
    "arm-and-send via the senders ArmedApply seam",
    "no hardware required",
)

# The canonical demonstration preview: two contrasting kicks under a mid-depth
# sweep of the src + filter groups. Fixed so the zero-arg report is byte-stable.
_DEMO_TRACKS: Final[tuple[tuple[int, str], ...]] = ((1, "1"), (2, "6"))
_DEMO_GROUPS: Final[frozenset[str]] = frozenset({"src", "filter"})
_DEMO_DEPTH: Final[float] = 0.5


def build_demo_scope_plan() -> ScopePlan:
    """Return the deterministic canonical scoped-randomization demo plan."""

    scopes: list[TrackScope] = [
        build_track_scope(track, profile_key) for track, profile_key in _DEMO_TRACKS
    ]
    mask = ScopeMask(
        tracks=frozenset(track for track, _ in _DEMO_TRACKS),
        groups=_DEMO_GROUPS,
    )
    return plan_scope(scopes, mask, _DEMO_DEPTH)


def _delta_section(plan: ScopePlan) -> ReportSection:
    rows: list[str] = []
    for track_plan in plan.track_plans:
        rows.append(
            f"Pad {track_plan.track} ({track_plan.profile_name}): "
            f"{track_plan.changed_count} params moved"
        )
        for delta in track_plan.deltas:
            sign = "+" if delta.delta >= 0 else ""
            rows.append(
                f"  {delta.group}/{delta.name}: {delta.anchor} -> "
                f"{delta.planned} ({sign}{delta.delta})"
            )
    return ReportSection(heading="Per-track deltas", rows=tuple(rows))


def build_scope_report_spec() -> ReportSpec:
    """Return the :class:`ReportSpec` for the canonical scope demo plan."""

    plan = build_demo_scope_plan()
    mask_row = (
        f"depth {plan.depth:.2f}; groups {sorted(plan.mask.groups)}; "
        f"tracks {sorted(plan.mask.tracks)}"
    )
    summary_section = ReportSection(
        heading="Mask",
        rows=(
            mask_row,
            f"ready: {plan.ready} ({plan.readiness_reason})",
            f"total params moved: {plan.total_changed}",
        ),
    )
    return ReportSpec(
        title=REPORT_TITLE,
        source_module=SOURCE_MODULE,
        version=REPORT_VERSION,
        cli_name=CLI_NAME,
        summary="Deterministic ScopeMask + depth-macro randomization preview (passive).",
        safety_lines=SAFETY_LINES,
        sections=(summary_section, _delta_section(plan)),
    )


def _delta_table_section(plan: ScopePlan) -> PanelSectionDict:
    rows: list[tuple[str, ...]] = []
    for track_plan in plan.track_plans:
        for delta in track_plan.deltas:
            sign = "+" if delta.delta >= 0 else ""
            rows.append(
                (
                    f"Pad {track_plan.track}",
                    delta.group,
                    delta.name,
                    str(delta.anchor),
                    str(delta.planned),
                    f"{sign}{delta.delta}",
                )
            )
    return table_section(
        "Parameter deltas",
        columns=("Pad", "Group", "Param", "Anchor", "Planned", "Delta"),
        rows=tuple(rows),
    )


def build_scope_panel_spec() -> PanelSpecDict:
    """Return the cockpit :class:`PanelSpecDict` for the canonical scope demo.

    A bespoke interactive mask-grid + depth slider lives in the frontend
    (``scopedRandomizationPanelSpec.ts``); this Python builder feeds the
    passive display-only panel and pins the shared vocabulary the frontend
    recomputes against.
    """

    plan = build_demo_scope_plan()
    mask_section = rows_section(
        "Mask",
        (
            f"depth {plan.depth:.2f}",
            f"groups: {', '.join(sorted(plan.mask.groups))}",
            f"tracks: {', '.join(str(track) for track in sorted(plan.mask.tracks))}",
            f"total params moved: {plan.total_changed}",
        ),
    )
    return panel_spec(
        PANEL_ID,
        REPORT_TITLE,
        status_badges=(
            badge(REPORT_VERSION, tone="neutral", icon="i"),
            *readiness_badges(plan.ready, plan.readiness_reason),
        ),
        sections=(mask_section, _delta_table_section(plan)),
        safety_lines=SAFETY_LINES,
    )


SCOPED_RANDOMIZATION_PREVIEW_CLI_COMMAND: Final[CliCommand] = make_spec_command(
    build_scope_report_spec()
)

register(SCOPED_RANDOMIZATION_PREVIEW_CLI_COMMAND)


__all__ = [
    "CLI_NAME",
    "PANEL_ID",
    "REPORT_TITLE",
    "REPORT_VERSION",
    "SAFETY_LINES",
    "SCOPED_RANDOMIZATION_PREVIEW_CLI_COMMAND",
    "SOURCE_MODULE",
    "build_demo_scope_plan",
    "build_scope_panel_spec",
    "build_scope_report_spec",
]
