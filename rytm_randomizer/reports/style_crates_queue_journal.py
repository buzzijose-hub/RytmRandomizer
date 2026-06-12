"""Passive Style Crates, Queue, and Mutation Journal report."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from types import MappingProxyType
from typing import Final

from ..cli_registry import CliCommand, make_passive_report_command, register
from ..data.style_crates import (
    DANGER_MODES,
    DEFAULT_MUTATION_JOURNAL,
    DEFAULT_STYLE_QUEUE,
    FUTURE_DANGER_MODE_LABELS,
    STYLE_CRATES,
    MutationJournalEntry,
    StyleCrate,
    StyleCrateMove,
    StyleQueueMove,
)
from .formatter import (
    SAFETY_SECTION_HEADER,
    PassiveReportHeader,
    passive_report_lines,
)

REPORT_TITLE: Final[str] = "RytmRandomizer passive style crates queue journal report"
SOURCE_MODULE: Final[str] = "reports.style_crates_queue_journal"
STYLE_CRATES_QUEUE_JOURNAL_VERSION: Final[str] = "style-crates-queue-journal-v1"
SAFETY_LINES: Final[tuple[str, ...]] = (
    "passive/read-only",
    "metadata only",
    "mock-first planning only",
    "queue entries are declarative only",
    "journal entries are replay metadata only",
    "reference analyzer is not implemented in this passive MVP",
    "JSON/stdout only",
    "no audio analyzer invocation",
    "no GUI launch",
    "no queue dispatch",
    "no journal persistence writes",
    "no command execution",
    "no MIDI sending",
    "no port opening",
    "no hardware mutation",
    "no hardware required",
)
BLOCKED_ACTIONS: Final[tuple[str, ...]] = (
    "dispatch queued move",
    "fire staged move",
    "save journal entry to disk",
    "run reference-track analyzer",
    "open MIDI port",
    "send MIDI",
    "mutate hardware",
    "launch GUI",
)
_HEADER: Final[PassiveReportHeader] = PassiveReportHeader(
    title=REPORT_TITLE,
    source_module=SOURCE_MODULE,
)


@dataclass(frozen=True)
class StyleCratesQueueJournalReport:
    """Passive crate/queue/journal packet for future GUI and CLI consumers."""

    report_version: str
    crate_count: int
    move_count: int
    queue_move_count: int
    journal_entry_count: int
    crates_by_key: Mapping[str, StyleCrate]
    queue: tuple[StyleQueueMove, ...]
    journal: tuple[MutationJournalEntry, ...]
    future_danger_modes: tuple[str, ...]
    reference_analyzer_status: str
    safety_lines: tuple[str, ...]
    blocked_actions: tuple[str, ...]
    replay_commands: tuple[str, ...]


def _style_crates_join(values: Sequence[str]) -> str:
    return ", ".join(values)


def _pads_text(pads: Sequence[int]) -> str:
    return ", ".join(str(pad) for pad in pads)


def _move_by_key(crate: StyleCrate, move_key: str) -> StyleCrateMove:
    for move in crate.moves:
        if move.key == move_key:
            return move
    raise KeyError(f"unknown move {move_key!r} in crate {crate.key!r}")


def _crates_by_key() -> Mapping[str, StyleCrate]:
    return MappingProxyType(dict(STYLE_CRATES))


def build_style_crates_queue_journal_report() -> StyleCratesQueueJournalReport:
    """Return passive Style Crates, queue, and journal metadata."""

    crates_by_key = _crates_by_key()
    move_count = sum(len(crate.moves) for crate in crates_by_key.values())
    return StyleCratesQueueJournalReport(
        report_version=STYLE_CRATES_QUEUE_JOURNAL_VERSION,
        crate_count=len(crates_by_key),
        move_count=move_count,
        queue_move_count=len(DEFAULT_STYLE_QUEUE),
        journal_entry_count=len(DEFAULT_MUTATION_JOURNAL),
        crates_by_key=crates_by_key,
        queue=DEFAULT_STYLE_QUEUE,
        journal=DEFAULT_MUTATION_JOURNAL,
        future_danger_modes=tuple(FUTURE_DANGER_MODE_LABELS[mode] for mode in DANGER_MODES),
        reference_analyzer_status="future: not implemented in passive MVP",
        safety_lines=SAFETY_LINES,
        blocked_actions=BLOCKED_ACTIONS,
        replay_commands=(
            "python -m rytm_randomizer.cli style-crates-queue-journal-report",
            "python -m rytm_randomizer.cli style-crates-queue-journal-report --json",
        ),
    )


def _style_crates_safety_lines() -> list[str]:
    return [SAFETY_SECTION_HEADER, *[f"- {line}" for line in SAFETY_LINES]]


def _crate_lines(report: StyleCratesQueueJournalReport) -> list[str]:
    lines = ["Style Crates:"]
    for key in report.crates_by_key:
        crate = report.crates_by_key[key]
        lines.extend(
            [
                f"{crate.key}: {crate.name} ({len(crate.moves)} move(s))",
                f"  Tags: {_style_crates_join(crate.tags)}",
                f"  Summary: {crate.summary}",
                "  Moves:",
            ]
        )
        for move in crate.moves:
            lines.extend(
                [
                    (
                        f"    - {move.key}: {move.name} | energy {move.energy}/10 | "
                        f"risk {move.risk}/10 | pads {_pads_text(move.target_pads)} | "
                        f"mode {move.mode}"
                    ),
                    f"      Recovery: {move.recovery_action}",
                    f"      Notes: {move.notes}",
                ]
            )
    return lines


def _queue_lines(report: StyleCratesQueueJournalReport) -> list[str]:
    lines = ["Staged Queue:"]
    for queued in report.queue:
        crate = report.crates_by_key[queued.crate_key]
        move = _move_by_key(crate, queued.move_key)
        lines.extend(
            [
                (
                    f"{queued.order}. {queued.use_case} / {queued.chapter} / "
                    f"{queued.crate_key}.{queued.move_key} -> {move.name}"
                ),
                (
                    f"   status={queued.status}, amount={queued.mutation_amount_percent}%, "
                    f"pads={_pads_text(queued.target_pads)}"
                ),
                f"   note={queued.operator_note}",
            ]
        )
    return lines


def _journal_lines(report: StyleCratesQueueJournalReport) -> list[str]:
    lines = ["Mutation Journal:"]
    for entry in report.journal:
        values = ", ".join(f"{key}={entry.values[key]}" for key in sorted(entry.values))
        lines.extend(
            [
                f"- {entry.key}: {entry.name}",
                f"  Tags: {_style_crates_join(entry.tags)}",
                f"  Seed: {entry.seed}",
                (
                    f"  Pads: {_pads_text(entry.pads)} | depth={entry.depth} | "
                    f"guardrail={entry.guardrail_mode}"
                ),
                f"  Values: {values}",
                f"  Notes: {entry.notes}",
            ]
        )
    return lines


def format_style_crates_queue_journal_report(
    report: StyleCratesQueueJournalReport | None = None,
) -> list[str]:
    """Return deterministic text for the passive crate/queue/journal report."""

    source_report = build_style_crates_queue_journal_report() if report is None else report
    lines = [
        "Summary:",
        f"- Version: {source_report.report_version}",
        f"- Crates: {source_report.crate_count}",
        f"- Moves: {source_report.move_count}",
        f"- Staged queue moves: {source_report.queue_move_count}",
        f"- Journal entries: {source_report.journal_entry_count}",
        f"- Reference analyzer: {source_report.reference_analyzer_status}",
    ]
    lines.extend(_crate_lines(source_report))
    lines.extend(_queue_lines(source_report))
    lines.extend(_journal_lines(source_report))
    lines.extend(
        [
            "Future Danger Modes:",
            *[f"- {mode}" for mode in source_report.future_danger_modes],
            "Blocked Actions:",
            *[f"- {action}" for action in source_report.blocked_actions],
            "Replay Commands:",
            *[f"- {command}" for command in source_report.replay_commands],
        ]
    )
    lines.extend(_style_crates_safety_lines())
    return passive_report_lines(_HEADER, lines)


def _move_json(move: StyleCrateMove) -> dict[str, object]:
    return {
        "key": move.key,
        "name": move.name,
        "summary": move.summary,
        "energy": move.energy,
        "risk": move.risk,
        "tags": list(move.tags),
        "target_pads": list(move.target_pads),
        "mode": move.mode,
        "recovery_action": move.recovery_action,
        "notes": move.notes,
    }


def _crate_json(crate: StyleCrate) -> dict[str, object]:
    return {
        "key": crate.key,
        "name": crate.name,
        "summary": crate.summary,
        "tags": list(crate.tags),
        "moves": [_move_json(move) for move in crate.moves],
    }


def _queue_json(queued: StyleQueueMove) -> dict[str, object]:
    return {
        "key": queued.key,
        "use_case": queued.use_case,
        "chapter": queued.chapter,
        "order": queued.order,
        "crate_key": queued.crate_key,
        "move_key": queued.move_key,
        "status": queued.status,
        "mutation_amount_percent": queued.mutation_amount_percent,
        "target_pads": list(queued.target_pads),
        "operator_note": queued.operator_note,
    }


def _journal_json(entry: MutationJournalEntry) -> dict[str, object]:
    return {
        "key": entry.key,
        "name": entry.name,
        "tags": list(entry.tags),
        "seed": entry.seed,
        "pads": list(entry.pads),
        "values": dict(entry.values),
        "depth": entry.depth,
        "guardrail_mode": entry.guardrail_mode,
        "notes": entry.notes,
    }


def to_style_crates_queue_journal_json(
    report: StyleCratesQueueJournalReport | None = None,
) -> dict[str, object]:
    """Return deterministic JSON-ready crate/queue/journal metadata."""

    source_report = build_style_crates_queue_journal_report() if report is None else report
    return {
        "style_crates_queue_journal": {
            "report_version": source_report.report_version,
            "crate_count": source_report.crate_count,
            "move_count": source_report.move_count,
            "queue_move_count": source_report.queue_move_count,
            "journal_entry_count": source_report.journal_entry_count,
            "crates": [
                _crate_json(source_report.crates_by_key[key]) for key in source_report.crates_by_key
            ],
            "queue": [_queue_json(queued) for queued in source_report.queue],
            "journal": [_journal_json(entry) for entry in source_report.journal],
            "future_danger_modes": list(source_report.future_danger_modes),
            "reference_analyzer_status": source_report.reference_analyzer_status,
            "blocked_actions": list(source_report.blocked_actions),
            "replay_commands": list(source_report.replay_commands),
        },
        "safety": list(source_report.safety_lines),
    }


STYLE_CRATES_QUEUE_JOURNAL_CLI_COMMAND: Final[CliCommand] = make_passive_report_command(
    "style-crates-queue-journal-report",
    "Print the passive Style Crates, Queue, and Mutation Journal report.",
    format_lines=lambda: format_style_crates_queue_journal_report(
        build_style_crates_queue_journal_report()
    ),
    build_payload=lambda: to_style_crates_queue_journal_json(
        build_style_crates_queue_journal_report()
    ),
    json_indent=None,
)

register(STYLE_CRATES_QUEUE_JOURNAL_CLI_COMMAND)

__all__ = [
    "BLOCKED_ACTIONS",
    "REPORT_TITLE",
    "SAFETY_LINES",
    "SOURCE_MODULE",
    "STYLE_CRATES_QUEUE_JOURNAL_CLI_COMMAND",
    "STYLE_CRATES_QUEUE_JOURNAL_VERSION",
    "StyleCratesQueueJournalReport",
    "build_style_crates_queue_journal_report",
    "format_style_crates_queue_journal_report",
    "to_style_crates_queue_journal_json",
]
