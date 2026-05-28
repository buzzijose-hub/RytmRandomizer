"""Passive style-crate rehearsal deck for future GUI crate browsing."""

from __future__ import annotations

import hashlib
import json
import sys
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from types import MappingProxyType
from typing import Final, TypedDict

from ..cli_registry import CliCommand, register
from ..data.style_crates import (
    DEFAULT_MUTATION_JOURNAL,
    DEFAULT_STYLE_QUEUE,
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

REPORT_TITLE: Final[str] = "RytmRandomizer passive style crate rehearsal deck"
SOURCE_MODULE: Final[str] = "reports.style_crate_rehearsal_deck"
STYLE_CRATE_REHEARSAL_DECK_VERSION: Final[str] = "style-crate-rehearsal-deck-v1"
SAFETY_LINES: Final[tuple[str, ...]] = (
    "passive/read-only",
    "GUI-ready rehearsal cards only",
    "uses existing Style Crates metadata only",
    "uses staged queue metadata only",
    "uses Mutation Journal replay metadata only",
    "JSON/stdout only",
    "no GUI launch",
    "no analyzer invocation",
    "no queue dispatch",
    "no journal persistence writes",
    "no command execution",
    "no MIDI sending",
    "no port opening",
    "no hardware mutation",
    "no hardware required",
)
BLOCKED_ACTIONS: Final[tuple[str, ...]] = (
    "fire queued style move",
    "dispatch crate move",
    "replay journal entry",
    "persist journal entry",
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
class StyleCrateRehearsalCrateCard:
    """One GUI-ready crate browser card."""

    crate_key: str
    crate_name: str
    summary: str
    tags: tuple[str, ...]
    move_count: int
    primary_move_key: str
    primary_move_name: str
    energy: int
    risk: int
    risk_status: str
    target_pads: tuple[int, ...]
    operator_action: str


class StyleCrateRehearsalCrateCardDict(TypedDict):
    """JSON-ready contract for :class:`StyleCrateRehearsalCrateCard`."""

    crate_key: str
    crate_name: str
    summary: str
    tags: list[str]
    move_count: int
    primary_move_key: str
    primary_move_name: str
    energy: int
    risk: int
    risk_status: str
    target_pads: list[int]
    operator_action: str


@dataclass(frozen=True)
class StyleCrateRehearsalQueueCard:
    """One staged queue move rendered as a passive rehearsal card."""

    queue_key: str
    order: int
    use_case: str
    chapter: str
    crate_key: str
    move_key: str
    move_name: str
    status: str
    mutation_amount_percent: int
    target_pads: tuple[int, ...]
    risk_status: str
    operator_action: str
    recovery_action: str
    dry_run_only: bool


class StyleCrateRehearsalQueueCardDict(TypedDict):
    """JSON-ready contract for :class:`StyleCrateRehearsalQueueCard`."""

    queue_key: str
    order: int
    use_case: str
    chapter: str
    crate_key: str
    move_key: str
    move_name: str
    status: str
    mutation_amount_percent: int
    target_pads: list[int]
    risk_status: str
    operator_action: str
    recovery_action: str
    dry_run_only: bool


@dataclass(frozen=True)
class StyleCrateRehearsalJournalCard:
    """One favorite mutation rendered as a passive replay card."""

    journal_key: str
    name: str
    tags: tuple[str, ...]
    replay_seed: str
    pads: tuple[int, ...]
    depth: str
    guardrail_mode: str
    risk_status: str
    value_summary: tuple[str, ...]
    operator_action: str


class StyleCrateRehearsalJournalCardDict(TypedDict):
    """JSON-ready contract for :class:`StyleCrateRehearsalJournalCard`."""

    journal_key: str
    name: str
    tags: list[str]
    replay_seed: str
    pads: list[int]
    depth: str
    guardrail_mode: str
    risk_status: str
    value_summary: list[str]
    operator_action: str


@dataclass(frozen=True)
class StyleCrateRehearsalDeck:
    """Passive GUI-ready crate, queue, and journal rehearsal packet."""

    deck_version: str
    deck_id: str
    deck_status: str
    crate_filter: str
    crates_by_key: Mapping[str, StyleCrate]
    crate_cards: tuple[StyleCrateRehearsalCrateCard, ...]
    queue_cards: tuple[StyleCrateRehearsalQueueCard, ...]
    journal_cards: tuple[StyleCrateRehearsalJournalCard, ...]
    safety_lines: tuple[str, ...]
    blocked_actions: tuple[str, ...]
    replay_commands: tuple[str, ...]


class StyleCrateRehearsalDeckDict(TypedDict):
    """JSON-ready contract for :class:`StyleCrateRehearsalDeck`."""

    deck_version: str
    deck_id: str
    deck_status: str
    crate_filter: str
    crate_cards: tuple[StyleCrateRehearsalCrateCardDict, ...]
    queue_cards: tuple[StyleCrateRehearsalQueueCardDict, ...]
    journal_cards: tuple[StyleCrateRehearsalJournalCardDict, ...]
    blocked_actions: list[str]
    replay_commands: list[str]


def _style_crate_rehearsal_crates_by_key() -> Mapping[str, StyleCrate]:
    return MappingProxyType(dict(STYLE_CRATES))


def _risk_status_for_move(move: StyleCrateMove) -> str:
    if move.risk <= 3:
        return "safe"
    if move.risk <= 6:
        return "review-ready"
    return "high-risk"


def _operator_action_for_risk(risk_status: str) -> str:
    if risk_status == "safe":
        return "Ready for passive preview; no hardware action available."
    if risk_status == "high-risk":
        return "Stage recovery first; keep this move in dry-run review."
    return "Review and dry-run before any future hardware arm."


def _risk_status_for_journal(entry: MutationJournalEntry) -> str:
    if entry.guardrail_mode == "live_safe":
        return "safe"
    if entry.guardrail_mode == "studio_wild":
        return "studio-only"
    return "explicit-opt-in"


def _move_for_queue(
    queued: StyleQueueMove, crates_by_key: Mapping[str, StyleCrate]
) -> StyleCrateMove:
    crate = crates_by_key[queued.crate_key]
    for move in crate.moves:
        if move.key == queued.move_key:
            return move
    raise KeyError(f"unknown move {queued.move_key!r} in crate {queued.crate_key!r}")


def _selected_crates(
    *,
    crate_key: str | None,
    crates_by_key: Mapping[str, StyleCrate],
) -> tuple[StyleCrate, ...]:
    if crate_key is None:
        return tuple(crates_by_key.values())
    normalized = crate_key.strip()
    if not normalized:
        raise ValueError("crate_key must not be blank")
    crate = crates_by_key.get(normalized)
    if crate is None:
        raise ValueError(f"unknown style crate: {normalized}")
    return (crate,)


def _crate_card(crate: StyleCrate) -> StyleCrateRehearsalCrateCard:
    primary = crate.moves[0]
    risk_status = _risk_status_for_move(primary)
    return StyleCrateRehearsalCrateCard(
        crate_key=crate.key,
        crate_name=crate.name,
        summary=crate.summary,
        tags=crate.tags,
        move_count=len(crate.moves),
        primary_move_key=primary.key,
        primary_move_name=primary.name,
        energy=primary.energy,
        risk=primary.risk,
        risk_status=risk_status,
        target_pads=primary.target_pads,
        operator_action=_operator_action_for_risk(risk_status),
    )


def _queue_card(
    queued: StyleQueueMove,
    *,
    crates_by_key: Mapping[str, StyleCrate],
) -> StyleCrateRehearsalQueueCard:
    move = _move_for_queue(queued, crates_by_key)
    risk_status = _risk_status_for_move(move)
    return StyleCrateRehearsalQueueCard(
        queue_key=queued.key,
        order=queued.order,
        use_case=queued.use_case,
        chapter=queued.chapter,
        crate_key=queued.crate_key,
        move_key=queued.move_key,
        move_name=move.name,
        status=queued.status,
        mutation_amount_percent=queued.mutation_amount_percent,
        target_pads=queued.target_pads,
        risk_status=risk_status,
        operator_action=_operator_action_for_risk(risk_status),
        recovery_action=move.recovery_action,
        dry_run_only=True,
    )


def _journal_card(entry: MutationJournalEntry) -> StyleCrateRehearsalJournalCard:
    risk_status = _risk_status_for_journal(entry)
    values = tuple(f"{key}={entry.values[key]}" for key in sorted(entry.values))
    if risk_status == "studio-only":
        operator_action = "Keep in studio review; do not arm as a Live Safe replay."
    elif risk_status == "safe":
        operator_action = "Can be reviewed as a passive replay seed."
    else:
        operator_action = "Requires explicit future opt-in before replay."
    return StyleCrateRehearsalJournalCard(
        journal_key=entry.key,
        name=entry.name,
        tags=entry.tags,
        replay_seed=entry.seed,
        pads=entry.pads,
        depth=entry.depth,
        guardrail_mode=entry.guardrail_mode,
        risk_status=risk_status,
        value_summary=values,
        operator_action=operator_action,
    )


def _style_crate_rehearsal_deck_id(
    *,
    crate_filter: str,
    queue_keys: Sequence[str],
    journal_keys: Sequence[str],
) -> str:
    digest = hashlib.sha256()
    digest.update(crate_filter.encode("utf-8"))
    for key in queue_keys:
        digest.update(b"\0")
        digest.update(key.encode("utf-8"))
    for key in journal_keys:
        digest.update(b"\0")
        digest.update(key.encode("utf-8"))
    return digest.hexdigest()[:16]


def _style_crate_rehearsal_replay_commands(crate_key: str | None) -> tuple[str, ...]:
    if crate_key is None:
        return (
            "python -m rytm_randomizer.cli style-crate-rehearsal-deck-report",
            "python -m rytm_randomizer.cli style-crate-rehearsal-deck-report --json",
        )
    return (
        f"python -m rytm_randomizer.cli style-crate-rehearsal-deck-report --crate {crate_key}",
        (
            "python -m rytm_randomizer.cli style-crate-rehearsal-deck-report "
            f"--crate {crate_key} --json"
        ),
    )


def build_style_crate_rehearsal_deck(
    *,
    crate_key: str | None = None,
) -> StyleCrateRehearsalDeck:
    """Build passive crate, queue, and journal cards for future GUI rehearsal."""

    crates_by_key = _style_crate_rehearsal_crates_by_key()
    crates = _selected_crates(crate_key=crate_key, crates_by_key=crates_by_key)
    selected_keys = {crate.key for crate in crates}
    queue_cards = tuple(
        _queue_card(queued, crates_by_key=crates_by_key)
        for queued in DEFAULT_STYLE_QUEUE
        if queued.crate_key in selected_keys
    )
    journal_entries = (
        DEFAULT_MUTATION_JOURNAL if crate_key is None or crate_key == "saved_accidents" else ()
    )
    journal_cards = tuple(_journal_card(entry) for entry in journal_entries)
    crate_filter = "all" if crate_key is None else crate_key
    return StyleCrateRehearsalDeck(
        deck_version=STYLE_CRATE_REHEARSAL_DECK_VERSION,
        deck_id=_style_crate_rehearsal_deck_id(
            crate_filter=crate_filter,
            queue_keys=tuple(card.queue_key for card in queue_cards),
            journal_keys=tuple(card.journal_key for card in journal_cards),
        ),
        deck_status="passive-ready",
        crate_filter=crate_filter,
        crates_by_key=crates_by_key,
        crate_cards=tuple(_crate_card(crate) for crate in crates),
        queue_cards=queue_cards,
        journal_cards=journal_cards,
        safety_lines=SAFETY_LINES,
        blocked_actions=BLOCKED_ACTIONS,
        replay_commands=_style_crate_rehearsal_replay_commands(crate_key),
    )


def _style_crate_rehearsal_pads_text(pads: Sequence[int]) -> str:
    return ", ".join(str(pad) for pad in pads)


def _style_crate_rehearsal_safety_lines() -> list[str]:
    return [SAFETY_SECTION_HEADER, *[f"- {line}" for line in SAFETY_LINES]]


def format_style_crate_rehearsal_deck(
    deck: StyleCrateRehearsalDeck | None = None,
) -> list[str]:
    """Return deterministic text for the passive style-crate rehearsal deck."""

    source = build_style_crate_rehearsal_deck() if deck is None else deck
    lines = [
        "Deck summary:",
        f"- Version: {source.deck_version}",
        f"- Deck ID: {source.deck_id}",
        f"- Status: {source.deck_status}",
        f"- Crate filter: {source.crate_filter}",
        f"- Crate cards: {len(source.crate_cards)}",
        f"- Queue rehearsal cards: {len(source.queue_cards)}",
        f"- Journal replay cards: {len(source.journal_cards)}",
        "Crate cards:",
    ]
    for card in source.crate_cards:
        lines.extend(
            [
                (
                    f"- {card.crate_key}: {card.crate_name} | risk={card.risk_status} | "
                    f"energy={card.energy}/10 | pads={_style_crate_rehearsal_pads_text(card.target_pads)}"
                ),
                f"  Primary move: {card.primary_move_key} -> {card.primary_move_name}",
                f"  Operator action: {card.operator_action}",
            ]
        )
    lines.append("Queue rehearsal cards:")
    for card in source.queue_cards:
        lines.extend(
            [
                (
                    f"{card.order}. {card.queue_key} -> {card.move_name} | "
                    f"{card.risk_status} | amount={card.mutation_amount_percent}%"
                ),
                f"   Chapter: {card.chapter} / {card.use_case} / status={card.status}",
                f"   Pads: {_style_crate_rehearsal_pads_text(card.target_pads)}",
                f"   Operator action: {card.operator_action}",
                f"   Recovery: {card.recovery_action}",
            ]
        )
    lines.append("Journal replay cards:")
    for card in source.journal_cards:
        lines.extend(
            [
                f"- {card.journal_key}: {card.name} | {card.risk_status}",
                f"  Seed: {card.replay_seed}",
                f"  Pads: {_style_crate_rehearsal_pads_text(card.pads)} | depth={card.depth}",
                f"  Values: {', '.join(card.value_summary)}",
                f"  Operator action: {card.operator_action}",
            ]
        )
    lines.extend(
        [
            "Blocked Actions:",
            *[f"- {action}" for action in source.blocked_actions],
            "Replay Commands:",
            *[f"- {command}" for command in source.replay_commands],
        ]
    )
    lines.extend(_style_crate_rehearsal_safety_lines())
    return passive_report_lines(_HEADER, lines)


def _crate_card_json(card: StyleCrateRehearsalCrateCard) -> StyleCrateRehearsalCrateCardDict:
    return {
        "crate_key": card.crate_key,
        "crate_name": card.crate_name,
        "summary": card.summary,
        "tags": list(card.tags),
        "move_count": card.move_count,
        "primary_move_key": card.primary_move_key,
        "primary_move_name": card.primary_move_name,
        "energy": card.energy,
        "risk": card.risk,
        "risk_status": card.risk_status,
        "target_pads": list(card.target_pads),
        "operator_action": card.operator_action,
    }


def _queue_card_json(card: StyleCrateRehearsalQueueCard) -> StyleCrateRehearsalQueueCardDict:
    return {
        "queue_key": card.queue_key,
        "order": card.order,
        "use_case": card.use_case,
        "chapter": card.chapter,
        "crate_key": card.crate_key,
        "move_key": card.move_key,
        "move_name": card.move_name,
        "status": card.status,
        "mutation_amount_percent": card.mutation_amount_percent,
        "target_pads": list(card.target_pads),
        "risk_status": card.risk_status,
        "operator_action": card.operator_action,
        "recovery_action": card.recovery_action,
        "dry_run_only": card.dry_run_only,
    }


def _journal_card_json(
    card: StyleCrateRehearsalJournalCard,
) -> StyleCrateRehearsalJournalCardDict:
    return {
        "journal_key": card.journal_key,
        "name": card.name,
        "tags": list(card.tags),
        "replay_seed": card.replay_seed,
        "pads": list(card.pads),
        "depth": card.depth,
        "guardrail_mode": card.guardrail_mode,
        "risk_status": card.risk_status,
        "value_summary": list(card.value_summary),
        "operator_action": card.operator_action,
    }


def to_style_crate_rehearsal_deck_json(
    deck: StyleCrateRehearsalDeck | None = None,
) -> dict[str, object]:
    """Return deterministic JSON-ready crate rehearsal deck metadata."""

    source = build_style_crate_rehearsal_deck() if deck is None else deck
    model: StyleCrateRehearsalDeckDict = {
        "deck_version": source.deck_version,
        "deck_id": source.deck_id,
        "deck_status": source.deck_status,
        "crate_filter": source.crate_filter,
        "crate_cards": tuple(_crate_card_json(card) for card in source.crate_cards),
        "queue_cards": tuple(_queue_card_json(card) for card in source.queue_cards),
        "journal_cards": tuple(_journal_card_json(card) for card in source.journal_cards),
        "blocked_actions": list(source.blocked_actions),
        "replay_commands": list(source.replay_commands),
    }
    return {
        "style_crate_rehearsal_deck": model,
        "safety": list(source.safety_lines),
    }


def _parse_style_crate_rehearsal_deck_args(argv: Sequence[str]) -> dict[str, object]:
    crate_key: str | None = None
    json_output = False
    index = 0
    while index < len(argv):
        arg = argv[index]
        if arg == "--json":
            json_output = True
            index += 1
            continue
        if arg == "--crate":
            if index + 1 >= len(argv):
                raise ValueError("--crate requires a style crate key")
            crate_key = argv[index + 1]
            index += 2
            continue
        raise ValueError(
            "style-crate-rehearsal-deck-report accepts optional --crate <key> and --json"
        )
    return {"crate_key": crate_key, "json_output": json_output}


def _handle_style_crate_rehearsal_deck_report(
    *,
    crate_key: str | None = None,
    json_output: bool = False,
) -> int:
    deck = build_style_crate_rehearsal_deck(crate_key=crate_key)
    if json_output:
        json.dump(to_style_crate_rehearsal_deck_json(deck), sys.stdout, sort_keys=True)
        sys.stdout.write("\n")
        return 0
    sys.stdout.write("\n".join(format_style_crate_rehearsal_deck(deck)))
    sys.stdout.write("\n")
    return 0


STYLE_CRATE_REHEARSAL_DECK_CLI_COMMAND: Final[CliCommand] = CliCommand(
    name="style-crate-rehearsal-deck-report",
    summary="Print the passive style crate rehearsal deck.",
    args_parser=_parse_style_crate_rehearsal_deck_args,
    handler=_handle_style_crate_rehearsal_deck_report,
)

register(STYLE_CRATE_REHEARSAL_DECK_CLI_COMMAND)

__all__ = [
    "BLOCKED_ACTIONS",
    "REPORT_TITLE",
    "SAFETY_LINES",
    "SOURCE_MODULE",
    "STYLE_CRATE_REHEARSAL_DECK_CLI_COMMAND",
    "STYLE_CRATE_REHEARSAL_DECK_VERSION",
    "StyleCrateRehearsalCrateCard",
    "StyleCrateRehearsalDeck",
    "StyleCrateRehearsalJournalCard",
    "StyleCrateRehearsalQueueCard",
    "build_style_crate_rehearsal_deck",
    "format_style_crate_rehearsal_deck",
    "to_style_crate_rehearsal_deck_json",
]
