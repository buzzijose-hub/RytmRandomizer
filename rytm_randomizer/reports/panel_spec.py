"""PanelSpec vocabulary — schema-driven cockpit panels (rival-program).

The cockpit frontend renders every schema-driven panel from one generic
``PanelSpecDict`` contract instead of a bespoke React component per report.
This module is the Python source of truth for that contract: the sibling
TypeScript interfaces in ``desktop/web/src/types/live_gui_protocol.ts`` are
GENERATED from these TypedDicts by ``scripts/generate_live_gui_protocol_ts.py``
(pinned byte-for-byte by
``tests/architecture/test_live_gui_protocol_is_generated.py``).

The vocabulary mirrors the latent per-panel shape that grew inside
``reports/live_gui_performance_console_model.py``'s panel builders: a titled
surface with status badges, ordered sections (bullet rows, a small table, or
chips), the required/blocked action lists, and the trailing safety lines.

``panel_spec_from_report_spec`` bridges :class:`reports.core.ReportSpec` so a
single declarative spec feeds BOTH the markdown/text passive report (via
``reports.core.render_report_lines``) and the cockpit panel (via the generic
``PanelRenderer`` frontend component).

The module is leaf-passive: importing it opens no ports, sends no MIDI, and
registers no CLI command.
"""

from __future__ import annotations

from typing import Final, Literal, TypedDict

from .core import ReportSpec
from .formatter import require_nonblank

PANEL_SPEC_VERSION: Final[str] = "cockpit-panel-spec-v1"

#: The closed badge-tone vocabulary. Tones are rendered as icon + text in the
#: frontend (never hue alone) so color-blind operators read the same signal.
BADGE_TONES: Final[tuple[str, ...]] = ("ok", "warn", "risk", "neutral")

#: The closed section-kind vocabulary.
SECTION_KINDS: Final[tuple[str, ...]] = ("rows", "table", "chips")


class BadgeDict(TypedDict):
    """One status badge in a panel header (icon + text, never hue alone)."""

    label: str
    tone: Literal["ok", "warn", "risk", "neutral"]
    icon: str


class TableDict(TypedDict):
    """One small column-aligned table inside a panel section."""

    columns: list[str]
    rows: list[list[str]]


class PanelSectionDict(TypedDict):
    """One titled panel section: bullet rows, a table, or a chip row.

    Exactly one payload is populated per ``kind``; the unused payloads stay
    empty (``rows``/``chips``) or ``None`` (``table``) so the contract keeps a
    single flat JSON shape the generated TypeScript can type.
    """

    heading: str
    kind: Literal["rows", "table", "chips"]
    rows: list[str]
    table: TableDict | None
    chips: list[str]


class PanelSpecDict(TypedDict):
    """One generic, JSON-ready cockpit panel description."""

    panel_id: str
    title: str
    status_badges: list[BadgeDict]
    sections: list[PanelSectionDict]
    required_actions: list[str]
    blocked_actions: list[str]
    safety_lines: list[str]


def badge(
    label: str,
    *,
    tone: Literal["ok", "warn", "risk", "neutral"] = "neutral",
    icon: str = "",
) -> BadgeDict:
    """Return one validated :class:`BadgeDict`.

    ``icon`` may stay empty — the frontend substitutes the house glyph for
    the tone so every badge still reads as icon + text.
    """

    if tone not in BADGE_TONES:
        raise ValueError(f"tone must be one of {BADGE_TONES}, got {tone!r}")
    return {"label": require_nonblank(label, "label"), "tone": tone, "icon": icon}


def readiness_badges(ready: bool, reason: str) -> tuple[BadgeDict, ...]:
    """Return the one-badge readiness signal for a plan-shaped surface.

    A ready plan renders an ``ok`` "ready" badge; a not-ready plan renders a
    ``warn`` badge carrying ``reason``. Shared so preview panels (scope, morph,
    and future plan surfaces) do not each re-roll the same badge tuple — the
    icon+text tone contract is applied once here.
    """

    if ready:
        return (badge("ready", tone="ok", icon="✓"),)
    return (badge(reason, tone="warn", icon="!"),)


def rows_section(heading: str, rows: tuple[str, ...] = ()) -> PanelSectionDict:
    """Return a bullet-row section (the ``reports.core`` section shape)."""

    return {
        "heading": require_nonblank(heading, "heading"),
        "kind": "rows",
        "rows": list(rows),
        "table": None,
        "chips": [],
    }


def table_section(
    heading: str,
    *,
    columns: tuple[str, ...],
    rows: tuple[tuple[str, ...], ...] = (),
) -> PanelSectionDict:
    """Return a table section; every row must match the column count."""

    normalized_columns = [require_nonblank(column, "column") for column in columns]
    if not normalized_columns:
        raise ValueError("table_section requires at least one column")
    for row in rows:
        if len(row) != len(normalized_columns):
            raise ValueError(
                f"table row {row!r} has {len(row)} cells; "
                f"expected {len(normalized_columns)} (one per column)"
            )
    return {
        "heading": require_nonblank(heading, "heading"),
        "kind": "table",
        "rows": [],
        "table": {"columns": normalized_columns, "rows": [list(row) for row in rows]},
        "chips": [],
    }


def chips_section(heading: str, chips: tuple[str, ...] = ()) -> PanelSectionDict:
    """Return a chip-row section (compact keyword/command chips)."""

    return {
        "heading": require_nonblank(heading, "heading"),
        "kind": "chips",
        "rows": [],
        "table": None,
        "chips": list(chips),
    }


def panel_spec(
    panel_id: str,
    title: str,
    *,
    status_badges: tuple[BadgeDict, ...] = (),
    sections: tuple[PanelSectionDict, ...] = (),
    required_actions: tuple[str, ...] = (),
    blocked_actions: tuple[str, ...] = (),
    safety_lines: tuple[str, ...] = (),
) -> PanelSpecDict:
    """Return one validated :class:`PanelSpecDict`."""

    return {
        "panel_id": require_nonblank(panel_id, "panel_id"),
        "title": require_nonblank(title, "title"),
        "status_badges": list(status_badges),
        "sections": list(sections),
        "required_actions": list(required_actions),
        "blocked_actions": list(blocked_actions),
        "safety_lines": list(safety_lines),
    }


def panel_spec_from_report_spec(
    spec: ReportSpec,
    *,
    panel_id: str | None = None,
    status_badges: tuple[BadgeDict, ...] | None = None,
    required_actions: tuple[str, ...] = (),
    blocked_actions: tuple[str, ...] = (),
) -> PanelSpecDict:
    """Bridge a :class:`reports.core.ReportSpec` into a cockpit panel.

    One declarative spec then feeds BOTH surfaces: the passive text/JSON
    report (``reports.core.render_report_lines`` / ``spec_payload``) and the
    cockpit panel (the generic frontend ``PanelRenderer``). The mapping keeps
    the house grammar: the summary becomes the first section, each
    ``ReportSection`` becomes a bullet-row section, and the ``Safety:`` block
    becomes ``safety_lines``. The default badge carries the spec version with
    a neutral tone.
    """

    badges = (
        (badge(spec.version, tone="neutral", icon="i"),) if status_badges is None else status_badges
    )
    sections = (
        rows_section("Summary", (spec.summary,)),
        *(rows_section(section.heading, section.rows) for section in spec.sections),
    )
    return panel_spec(
        spec.cli_name if panel_id is None else panel_id,
        spec.title,
        status_badges=badges,
        sections=sections,
        required_actions=required_actions,
        blocked_actions=blocked_actions,
        safety_lines=spec.safety_lines,
    )


__all__ = (
    "BADGE_TONES",
    "PANEL_SPEC_VERSION",
    "SECTION_KINDS",
    "BadgeDict",
    "PanelSectionDict",
    "PanelSpecDict",
    "TableDict",
    "badge",
    "chips_section",
    "panel_spec",
    "panel_spec_from_report_spec",
    "readiness_badges",
    "rows_section",
    "table_section",
)
