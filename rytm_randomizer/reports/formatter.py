"""Passive-report rendering primitives.

WS-S4 extraction (per docs/SIMPLIFICATION_PLAN.md). This module is leaf-passive:
importing it opens no ports, sends no MIDI, performs no state transitions, and
makes no guardrail decisions. Per Gate 7 (docs/PLAN_REQUIREMENTS.md), the
module has no logger or @trace adoption -- text rendering is not a
decision-shaped operation.

Public surface:

* ``SAFETY_SECTION_HEADER`` -- the canonical "Safety:" literal that opens a
  safety-bullets block.
* ``PASSIVE_FOOTER_SOURCE_TEMPLATE`` -- the "Source: rytm_randomizer.{module}"
  trailer template; callers format with their own short module name.
* ``PASSIVE_FOOTER_MEMORY_LINE`` -- the "In-memory only: True" trailer literal.
* ``PASSIVE_FOOTER`` -- the aggregated 2-tuple of the two trailer templates,
  exposed for convenience and immutable-by-construction (tuple).
* ``PassiveReportHeader`` -- frozen dataclass describing a passive report's
  header (title + optional source module + memory-line toggle).
* ``safety_section_lines(safety)`` -- render a Safety: section as
  ``[header, "- key: value", ...]`` preserving the mapping's insertion order.
* ``passive_footer_lines(source_module, *, include_memory_line=True)`` -- render
  the 1-or-2-line trailer.
* ``render_passive_report(header, body_lines)`` -- join header + body + footer
  into a single newline-separated string.
* ``passive_report_lines(header, body_lines)`` -- list-returning sibling of
  ``render_passive_report``.

Per Gate 12, every module-level constant is annotated ``Final``.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import Final

SAFETY_SECTION_HEADER: Final[str] = "Safety:"

# The two-line trailer used by mock_mapper / runtime_plan /
# mock_runtime_active_bridge / registry format_*_report() functions.
# ``{module}`` is filled in by callers.
PASSIVE_FOOTER_SOURCE_TEMPLATE: Final[str] = "Source: rytm_randomizer.{module}"
PASSIVE_FOOTER_MEMORY_LINE: Final[str] = "In-memory only: True"

# Aggregated PASSIVE_FOOTER tuple the SIMPLIFICATION_PLAN names. Immutable by
# construction (tuple). The first element holds the unformatted source
# template; callers usually go through ``passive_footer_lines`` to apply the
# module name in one call.
PASSIVE_FOOTER: Final[tuple[str, str]] = (
    PASSIVE_FOOTER_SOURCE_TEMPLATE,
    PASSIVE_FOOTER_MEMORY_LINE,
)


@dataclass(frozen=True)
class PassiveReportHeader:
    """Header metadata for a passive report.

    ``title`` is the first emitted line. ``source_module`` is the short suffix
    that fills the ``PASSIVE_FOOTER_SOURCE_TEMPLATE`` placeholder; when
    ``None`` the report emits no trailer. ``include_memory_line`` toggles
    emission of the "In-memory only: True" trailer line; defaults to True.
    """

    title: str
    source_module: str | None = None
    include_memory_line: bool = True


def safety_section_lines(safety: Mapping[str, object]) -> list[str]:
    """Render a Safety: section as a header + one ``- key: value`` per item.

    Iteration order is the mapping's native order (Python 3.7+ insertion
    order). Today's callers in ``reports.format_anchor_profile_report`` and
    ``project_status_report.format_project_status_report`` iterate
    ``source_report["safety"].items()`` with the same ordering guarantee, so
    this helper produces byte-identical output.

    An empty mapping yields just the header line.
    """

    rendered: list[str] = [SAFETY_SECTION_HEADER]
    for key, value in safety.items():
        rendered.append(f"- {key}: {value}")
    return rendered


def passive_footer_lines(source_module: str, *, include_memory_line: bool = True) -> list[str]:
    """Render the trailing 1-or-2-line ``Source: ... / In-memory only: True`` footer."""

    lines: list[str] = [PASSIVE_FOOTER_SOURCE_TEMPLATE.format(module=source_module)]
    if include_memory_line:
        lines.append(PASSIVE_FOOTER_MEMORY_LINE)
    return lines


def passive_report_lines(
    header: PassiveReportHeader,
    body_lines: Iterable[str],
) -> list[str]:
    """List-returning sibling of :func:`render_passive_report`.

    Header line first, then body lines as-given, then (if
    ``header.source_module`` is set) the standard 1-or-2-line passive footer.
    """

    lines: list[str] = [header.title, *body_lines]
    if header.source_module is not None:
        lines.extend(
            passive_footer_lines(
                header.source_module,
                include_memory_line=header.include_memory_line,
            )
        )
    return lines


def render_passive_report(
    header: PassiveReportHeader,
    body_lines: Iterable[str],
) -> str:
    """Join header + body + footer into a deterministic newline-separated string."""

    return "\n".join(passive_report_lines(header, body_lines))


__all__ = [
    "PASSIVE_FOOTER",
    "PASSIVE_FOOTER_MEMORY_LINE",
    "PASSIVE_FOOTER_SOURCE_TEMPLATE",
    "PassiveReportHeader",
    "SAFETY_SECTION_HEADER",
    "passive_footer_lines",
    "passive_report_lines",
    "render_passive_report",
    "safety_section_lines",
]
