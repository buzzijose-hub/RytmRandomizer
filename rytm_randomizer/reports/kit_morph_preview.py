"""Passive kit-morph preview report (source -> target interpolation).

Surfaces the deterministic :mod:`rytm_randomizer.behavior.morph` plan as BOTH
a passive text/JSON CLI report (via the ReportSpec platform) and a cockpit
panel (via the shared PanelSpec vocabulary). The report renders a canonical
demonstration preview — a fixed source/target pair at a fixed amount over the
built-in V1.34 profile registry — so the zero-argument command is
deterministic and golden-capturable.

Passive: importing this module opens no ports and sends no MIDI.

**Preview only — not sendable today.** The rendered
:class:`~rytm_randomizer.behavior.morph.MorphPlan` is an audit artefact, NOT
a device plan: it is not a ``RytmMutationPlan``, it is not compiled into one,
and no code path can hand it to the ``senders`` ArmedApply seam. The report
must not advertise arm-and-send as an available next step.
"""

from __future__ import annotations

from typing import Final

from ..behavior.morph import (
    MorphPlan,
    MorphTrack,
    build_morph_track,
    plan_morph,
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

REPORT_TITLE: Final[str] = "RytmRandomizer kit-morph preview"
SOURCE_MODULE: Final[str] = "reports.kit_morph_preview"
REPORT_VERSION: Final[str] = "morph-preview-v1"
CLI_NAME: Final[str] = "kit-morph-preview"
PANEL_ID: Final[str] = "kit-morph"

SAFETY_LINES: Final[tuple[str, ...]] = (
    "passive/read-only",
    "preview plan only",
    "no MIDI sending",
    "no port opening",
    # NOT "arm-and-send via the senders ArmedApply seam": a MorphPlan is not
    # a device plan and cannot be transmitted. Advertising a send path that
    # does not exist is the defect this line replaced.
    "not a device plan - cannot be sent to hardware",
    "no hardware required",
)

# The canonical demonstration preview: morph a sharp kick toward a classic kick
# at the midpoint over the src + filter groups. Fixed so the report is stable.
_DEMO_TRACKS: Final[tuple[tuple[int, str, str], ...]] = ((1, "1", "3"),)
_DEMO_GROUPS: Final[frozenset[str]] = frozenset({"src", "filter"})
_DEMO_AMOUNT: Final[float] = 0.5


def build_demo_morph_plan() -> MorphPlan:
    """Return the deterministic canonical kit-morph demo plan."""

    tracks: list[MorphTrack] = [
        build_morph_track(track, source_key, target_key)
        for track, source_key, target_key in _DEMO_TRACKS
    ]
    return plan_morph(tracks, _DEMO_GROUPS, _DEMO_AMOUNT)


def _interp_section(plan: MorphPlan) -> ReportSection:
    rows: list[str] = []
    for track_plan in plan.track_plans:
        rows.append(
            f"Pad {track_plan.track} ({track_plan.source_name} -> "
            f"{track_plan.target_name}): {track_plan.moved_count} params moved"
        )
        for param in track_plan.params:
            kind = "discrete" if param.discrete else "linear"
            rows.append(
                f"  {param.group}/{param.name} [{kind}]: "
                f"{param.source} -> {param.target} = {param.interpolated}"
            )
        if track_plan.unmatched:
            rows.append(f"  unmatched (not morphed): {', '.join(track_plan.unmatched)}")
    return ReportSection(heading="Per-track interpolation", rows=tuple(rows))


def build_morph_report_spec() -> ReportSpec:
    """Return the :class:`ReportSpec` for the canonical morph demo plan."""

    plan = build_demo_morph_plan()
    summary_section = ReportSection(
        heading="Morph",
        rows=(
            f"amount {plan.amount:.2f}; groups {sorted(plan.groups)}",
            f"ready: {plan.ready} ({plan.readiness_reason})",
            f"total params moved: {plan.total_moved}",
        ),
    )
    return ReportSpec(
        title=REPORT_TITLE,
        source_module=SOURCE_MODULE,
        version=REPORT_VERSION,
        cli_name=CLI_NAME,
        summary="Deterministic source->target kit-morph interpolation preview (passive).",
        safety_lines=SAFETY_LINES,
        sections=(summary_section, _interp_section(plan)),
    )


def _interp_table_section(plan: MorphPlan) -> PanelSectionDict:
    rows: list[tuple[str, ...]] = []
    for track_plan in plan.track_plans:
        for param in track_plan.params:
            kind = "discrete" if param.discrete else "linear"
            rows.append(
                (
                    f"Pad {track_plan.track}",
                    param.group,
                    param.name,
                    kind,
                    str(param.source),
                    str(param.target),
                    str(param.interpolated),
                )
            )
    return table_section(
        "Interpolation",
        columns=("Pad", "Group", "Param", "Kind", "Source", "Target", "Interp"),
        rows=tuple(rows),
    )


def build_morph_panel_spec() -> PanelSpecDict:
    """Return the cockpit :class:`PanelSpecDict` for the canonical morph demo.

    A bespoke interactive morph-amount slider strip lives in the frontend
    (``kitMorphPanelSpec.ts``); this Python builder feeds the passive
    display-only panel and pins the shared vocabulary the frontend recomputes
    against.
    """

    plan = build_demo_morph_plan()
    morph_section = rows_section(
        "Morph",
        (
            f"amount {plan.amount:.2f}",
            f"groups: {', '.join(sorted(plan.groups))}",
            f"total params moved: {plan.total_moved}",
        ),
    )
    return panel_spec(
        PANEL_ID,
        REPORT_TITLE,
        status_badges=(
            badge(REPORT_VERSION, tone="neutral", icon="i"),
            *readiness_badges(plan.ready, plan.readiness_reason),
        ),
        sections=(morph_section, _interp_table_section(plan)),
        safety_lines=SAFETY_LINES,
    )


KIT_MORPH_PREVIEW_CLI_COMMAND: Final[CliCommand] = make_spec_command(build_morph_report_spec())

register(KIT_MORPH_PREVIEW_CLI_COMMAND)


__all__ = [
    "CLI_NAME",
    "KIT_MORPH_PREVIEW_CLI_COMMAND",
    "PANEL_ID",
    "REPORT_TITLE",
    "REPORT_VERSION",
    "SAFETY_LINES",
    "SOURCE_MODULE",
    "build_demo_morph_plan",
    "build_morph_panel_spec",
    "build_morph_report_spec",
]
