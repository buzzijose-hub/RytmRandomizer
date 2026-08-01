"""ReportSpec platform core — declarative passive-report specifications.

Wave 2b of the rival-program bundle. This module is the platform seam the
Wave 3 report-module migrations converge on: instead of every
``reports/*.py`` module hand-rolling its own line renderer, JSON payload
builder, and ``CliCommand`` wiring, a module declares one frozen
:class:`ReportSpec` and gets all three from the shared helpers here.

The module is leaf-passive (importing it opens no ports, sends no MIDI,
registers no CLI command) and composes ONLY the existing shared primitives:

* line rendering  -> ``reports.formatter.PassiveReportHeader`` +
  ``passive_report_lines`` + ``SAFETY_SECTION_HEADER`` (house grammar:
  title line, body lines, ``Safety:`` block, ``Source:`` /
  ``In-memory only: True`` footer),
* validation      -> ``reports.formatter.require_nonblank``,
* CLI wiring      -> ``cli_registry.make_passive_report_command``.

Public surface:

* ``ReportSection`` -- frozen (heading, rows) section record.
* ``ReportSpec`` -- frozen declarative description of one passive report.
* ``render_report_lines(spec)`` -- deterministic operator-facing lines in
  the house passive-report grammar.
* ``spec_payload(spec)`` -- the canonical JSON envelope (flat mapping with
  the trailing ``"safety": [...]`` list every existing payload builder
  emits).
* ``make_spec_command(spec, ...)`` -- a ``CliCommand`` for the spec,
  delegating to ``cli_registry.make_passive_report_command``.

No behavior change lands with this module: consumers migrate in Wave 3.
"""

from __future__ import annotations

from dataclasses import dataclass

from ..cli_registry import CliCommand, make_passive_report_command
from .formatter import (
    SAFETY_SECTION_HEADER,
    PassiveReportHeader,
    passive_report_lines,
    require_nonblank,
)


@dataclass(frozen=True)
class ReportSection:
    """One titled section of a passive report.

    ``heading`` is rendered as ``"{heading}:"``; each row is rendered as a
    ``"- {row}"`` bullet. An empty ``rows`` tuple renders the house
    ``"- none"`` placeholder (the ``Mismatch reasons:`` convention).
    """

    heading: str
    rows: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        require_nonblank(self.heading, "heading")


@dataclass(frozen=True)
class ReportSpec:
    """Declarative description of one passive text/JSON report.

    Attributes
    ----------
    title:
        The first emitted line (the report's operator-facing title).
    source_module:
        Short module suffix for the ``Source: rytm_randomizer.{module}``
        footer line (e.g. ``"reports.core"``).
    version:
        Spec/report version token, rendered as ``Version: {version}``.
    cli_name:
        The passive CLI subcommand token this spec is exposed under.
    summary:
        One-line description; doubles as the CLI command summary and the
        first body line of the rendered report.
    safety_lines:
        Bullet lines for the trailing ``Safety:`` block. An empty tuple
        renders just the ``Safety:`` header (matching
        ``formatter.safety_section_lines`` on an empty mapping).
    sections:
        Ordered titled sections rendered between the version line and the
        safety block.
    """

    title: str
    source_module: str
    version: str
    cli_name: str
    summary: str
    safety_lines: tuple[str, ...] = ()
    sections: tuple[ReportSection, ...] = ()

    def __post_init__(self) -> None:
        require_nonblank(self.title, "title")
        require_nonblank(self.source_module, "source_module")
        require_nonblank(self.version, "version")
        require_nonblank(self.cli_name, "cli_name")
        require_nonblank(self.summary, "summary")


def render_report_lines(spec: ReportSpec) -> list[str]:
    """Render ``spec`` as deterministic lines in the house passive grammar.

    Shape (mirroring e.g. ``reports.analog_four_baseline``): title line,
    summary, ``Version:`` line, one ``"{heading}:"`` + bullet block per
    section (``- none`` when a section has no rows), the ``Safety:`` block,
    then the standard ``Source:`` / ``In-memory only: True`` footer via
    :func:`reports.formatter.passive_report_lines`.
    """

    header = PassiveReportHeader(title=spec.title, source_module=spec.source_module)
    body: list[str] = [spec.summary, f"Version: {spec.version}"]
    for section in spec.sections:
        body.append(f"{section.heading}:")
        if section.rows:
            body.extend(f"- {row}" for row in section.rows)
        else:
            body.append("- none")
    body.append(SAFETY_SECTION_HEADER)
    body.extend(f"- {line}" for line in spec.safety_lines)
    return passive_report_lines(header, body)


def spec_payload(spec: ReportSpec) -> dict[str, object]:
    """Return the canonical JSON envelope for ``spec``.

    Flat mapping in the shape every existing ``build_*_payload`` /
    ``to_*_json`` builder emits, with the ``"safety": [...]`` list carrying
    ``spec.safety_lines`` and sections keyed by heading.
    """

    return {
        "title": spec.title,
        "source_module": spec.source_module,
        "version": spec.version,
        "cli_name": spec.cli_name,
        "summary": spec.summary,
        "sections": {section.heading: list(section.rows) for section in spec.sections},
        "safety": list(spec.safety_lines),
    }


def make_spec_command(
    spec: ReportSpec,
    *,
    json_flag: bool = True,
    json_indent: int | None = 2,
) -> CliCommand:
    """Return the passive ``CliCommand`` for ``spec``.

    Pure delegation to :func:`cli_registry.make_passive_report_command`
    with ``render_report_lines`` as the text path and ``spec_payload`` as
    the ``--json`` path. The caller decides whether/when to
    ``cli_registry.register`` the returned command; this module never
    registers anything at import time.
    """

    return make_passive_report_command(
        spec.cli_name,
        spec.summary,
        format_lines=lambda: render_report_lines(spec),
        build_payload=lambda: spec_payload(spec),
        json_flag=json_flag,
        json_indent=json_indent,
    )


__all__ = (
    "ReportSection",
    "ReportSpec",
    "make_spec_command",
    "render_report_lines",
    "spec_payload",
)
