"""Passive Style Crates, Queue, and Mutation Journal seed data.

This module is pure data. It opens no MIDI ports, sends no MIDI, imports no
hardware adapters, and performs no analyzer work. The records here are the
first passive vocabulary for browsing mutation moves, staging future moves,
and saving favorite mutation results.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import Final, Literal

DangerMode = Literal[
    "live_safe",
    "studio_wild",
    "chaos",
    "one_shot_blast",
    "evolve_mode",
]
MoveMode = Literal["scene", "mutation", "transition", "recovery", "journal"]
QueueUseCase = Literal["set_story", "live_scratchpad"]
QueueMoveStatus = Literal["staged", "scratchpad", "skipped", "fired", "saved"]

DANGER_MODES: Final[tuple[DangerMode, ...]] = (
    "live_safe",
    "studio_wild",
    "chaos",
    "one_shot_blast",
    "evolve_mode",
)
FUTURE_DANGER_MODE_LABELS: Final[Mapping[DangerMode, str]] = MappingProxyType(
    {
        "live_safe": "Live Safe",
        "studio_wild": "Studio Wild",
        "chaos": "Chaos",
        "one_shot_blast": "One-Shot Blast",
        "evolve_mode": "Evolve Mode",
    }
)
_VALID_PADS: Final[range] = range(1, 13)


@dataclass(frozen=True)
class StyleCrateMove:
    """One passive mutation direction inside a crate."""

    key: str
    name: str
    summary: str
    energy: int
    risk: int
    tags: tuple[str, ...]
    target_pads: tuple[int, ...]
    mode: MoveMode
    recovery_action: str
    notes: str


@dataclass(frozen=True)
class StyleCrate:
    """Genre/vibe folder of passive mutation moves."""

    key: str
    name: str
    summary: str
    tags: tuple[str, ...]
    moves: tuple[StyleCrateMove, ...]


@dataclass(frozen=True)
class StyleQueueMove:
    """One staged move in the passive set-story or live-scratchpad queue."""

    key: str
    use_case: QueueUseCase
    chapter: str
    order: int
    crate_key: str
    move_key: str
    status: QueueMoveStatus
    mutation_amount_percent: int
    target_pads: tuple[int, ...]
    operator_note: str


@dataclass(frozen=True)
class MutationJournalEntry:
    """Favorite mutation result metadata for later replay or variation."""

    key: str
    name: str
    tags: tuple[str, ...]
    seed: str
    pads: tuple[int, ...]
    values: Mapping[str, int]
    depth: str
    guardrail_mode: DangerMode
    notes: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "values", MappingProxyType(dict(self.values)))


def _move(
    *,
    key: str,
    name: str,
    summary: str,
    energy: int,
    risk: int,
    tags: tuple[str, ...],
    target_pads: tuple[int, ...],
    mode: MoveMode,
    recovery_action: str,
    notes: str,
) -> StyleCrateMove:
    return StyleCrateMove(
        key=key,
        name=name,
        summary=summary,
        energy=energy,
        risk=risk,
        tags=tags,
        target_pads=target_pads,
        mode=mode,
        recovery_action=recovery_action,
        notes=notes,
    )


_STYLE_CRATE_ITEMS: Final[tuple[StyleCrate, ...]] = (
    StyleCrate(
        key="dark_hypnotic",
        name="Dark Hypnotic",
        summary="Low-light tunnel pressure with slow motion and protected kick weight.",
        tags=("dark", "hypnotic", "tunnel", "low_end"),
        moves=(
            _move(
                key="shadow_filter_pressure",
                name="Shadow Filter Pressure",
                summary="Lean into dark filter motion while the kick stays stable.",
                energy=5,
                risk=3,
                tags=("filter", "tunnel", "slow_motion"),
                target_pads=(1, 3, 11),
                mode="mutation",
                recovery_action="return to Live Safe anchors or Back to Clean",
                notes="Good first darkening move before heavier pressure.",
            ),
        ),
    ),
    StyleCrate(
        key="peak_time",
        name="Peak Time",
        summary="High-energy warehouse drive with guarded chaos and hard transient focus.",
        tags=("peak", "warehouse", "drive", "energy"),
        moves=(
            _move(
                key="warehouse_lift",
                name="Warehouse Lift",
                summary="Raise movement and transient pressure without freeing the kick.",
                energy=9,
                risk=6,
                tags=("lift", "drive", "transient"),
                target_pads=(1, 2, 3, 4, 9, 11),
                mode="scene",
                recovery_action="stage a transition reset or queue Back to Clean",
                notes="Intended as a visible set-story lift, not an unattended loop.",
            ),
        ),
    ),
    StyleCrate(
        key="hard_groove",
        name="Hard Groove",
        summary="Rolling percussion density with push, swing, and dry machine funk.",
        tags=("hardgroove", "rolling", "percussion", "funk"),
        moves=(
            _move(
                key="rolling_perc_push",
                name="Rolling Perc Push",
                summary="Push hats, rims, and supporting percussion around a fixed low end.",
                energy=7,
                risk=4,
                tags=("groove", "hats", "percussion"),
                target_pads=(2, 3, 5, 6, 7, 9),
                mode="mutation",
                recovery_action="mute dense lanes or return percussion pads to journaled baseline",
                notes="Useful for studio 12-pad work once Pads 5-12 are promoted.",
            ),
        ),
    ),
    StyleCrate(
        key="dub_pressure",
        name="Dub Pressure",
        summary="Space, delay pressure, sub weight, and restrained movement.",
        tags=("dub", "space", "delay", "low_end"),
        moves=(
            _move(
                key="sub_space_bloom",
                name="Sub Space Bloom",
                summary="Widen space and low-end perception without increasing density.",
                energy=4,
                risk=3,
                tags=("space", "sub", "reverb"),
                target_pads=(1, 3, 12),
                mode="mutation",
                recovery_action="cut delay/reverb sends and return filter to Live Safe",
                notes="Reference-analyzer future can suggest this from low brightness and high space.",
            ),
        ),
    ),
    StyleCrate(
        key="industrial_broken",
        name="Industrial/Broken",
        summary="Broken-grid impact, metallic grit, and unstable machine pressure.",
        tags=("industrial", "broken", "metallic", "grit"),
        moves=(
            _move(
                key="broken_metal_stress",
                name="Broken Metal Stress",
                summary="Add metallic bite and broken accents while keeping a recovery cue ready.",
                energy=8,
                risk=7,
                tags=("metallic", "stress", "accent"),
                target_pads=(3, 4, 8, 10, 11),
                mode="mutation",
                recovery_action="skip queued move or fire a transition reset before arming hardware",
                notes="High-risk live move; safer as a studio exploration until proven.",
            ),
        ),
    ),
    StyleCrate(
        key="deep_minimal",
        name="Deep Minimal",
        summary="Sparse, patient, low-risk motion for long-form hypnotic sections.",
        tags=("deep", "minimal", "sparse", "patient"),
        moves=(
            _move(
                key="micro_motion_hold",
                name="Micro Motion Hold",
                summary="Small parameter drift that preserves repetition and negative space.",
                energy=3,
                risk=2,
                tags=("micro", "space", "hold"),
                target_pads=(1, 2, 3),
                mode="mutation",
                recovery_action="hold current state; no urgent recovery expected",
                notes="Designed for Evolve Mode later, but passive-only now.",
            ),
        ),
    ),
    StyleCrate(
        key="chaos_fills",
        name="Chaos Fills",
        summary="Explicit opt-in fills and accents for brief release moments.",
        tags=("chaos", "fills", "release", "accent"),
        moves=(
            _move(
                key="one_bar_flash",
                name="One-Bar Flash",
                summary="A short burst concept for future one-shot mutation behavior.",
                energy=10,
                risk=9,
                tags=("one_shot", "fill", "maximum"),
                target_pads=(2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12),
                mode="transition",
                recovery_action="One-Shot Blast must auto-stop and queue Back to Clean",
                notes="Documentation-only until the one-shot hardware contract is approved.",
            ),
        ),
    ),
    StyleCrate(
        key="transitions",
        name="Transitions",
        summary="Moves for leaving, entering, or resetting a section.",
        tags=("transition", "reset", "handoff", "chapter"),
        moves=(
            _move(
                key="back_to_clean_handoff",
                name="Back To Clean Handoff",
                summary="Prepare a clean recovery lane after a high-risk section.",
                energy=2,
                risk=1,
                tags=("recovery", "clean", "handoff"),
                target_pads=(1, 2, 3, 4),
                mode="recovery",
                recovery_action="already a recovery move; verify anchors before any SEND",
                notes="Should remain available near every high-risk queue entry.",
            ),
        ),
    ),
    StyleCrate(
        key="saved_accidents",
        name="Saved Accidents",
        summary="Favorite accidents worth replaying, varying, or re-crating.",
        tags=("journal", "favorite", "accident", "replay"),
        moves=(
            _move(
                key="journaled_pressure_rattle",
                name="Journaled Pressure Rattle",
                summary="A saved accident pattern promoted into a browsable move.",
                energy=6,
                risk=5,
                tags=("saved", "rattle", "variation"),
                target_pads=(3, 9, 11),
                mode="journal",
                recovery_action="load the journal seed's Live Safe baseline first",
                notes="Represents the bridge from journal entry to future crate move.",
            ),
        ),
    ),
)


def _validate_nonblank(value: str, *, field: str) -> None:
    if not value.strip():
        raise ValueError(f"{field} must not be blank")


def _validate_pads(key: str, pads: tuple[int, ...]) -> None:
    if not pads:
        raise ValueError(f"{key} requires at least one target pad")
    invalid = tuple(pad for pad in pads if pad not in _VALID_PADS)
    if invalid:
        raise ValueError(f"{key} has invalid 1-12 pad(s): {invalid}")


def _validate_score(key: str, *, field: str, value: int) -> None:
    if not 1 <= value <= 10:
        raise ValueError(f"{key} {field} must be in 1..10")


def _validated_crates(crates: tuple[StyleCrate, ...]) -> Mapping[str, StyleCrate]:
    keys: set[str] = set()
    for crate in crates:
        _validate_nonblank(crate.key, field="crate key")
        _validate_nonblank(crate.name, field=f"{crate.key} name")
        if crate.key in keys:
            raise ValueError(f"duplicate style crate key: {crate.key}")
        keys.add(crate.key)
        move_keys: set[str] = set()
        for move in crate.moves:
            _validate_nonblank(move.key, field=f"{crate.key} move key")
            if move.key in move_keys:
                raise ValueError(f"duplicate move key in {crate.key}: {move.key}")
            move_keys.add(move.key)
            _validate_score(move.key, field="energy", value=move.energy)
            _validate_score(move.key, field="risk", value=move.risk)
            _validate_pads(move.key, move.target_pads)
            _validate_nonblank(move.recovery_action, field=f"{move.key} recovery_action")
            _validate_nonblank(move.notes, field=f"{move.key} notes")
    return MappingProxyType({crate.key: crate for crate in crates})


STYLE_CRATES: Final[Mapping[str, StyleCrate]] = _validated_crates(_STYLE_CRATE_ITEMS)

_DEFAULT_STYLE_QUEUE_ITEMS: Final[tuple[StyleQueueMove, ...]] = (
    StyleQueueMove(
        key="queue-opening-shadow",
        use_case="set_story",
        chapter="opening tunnel",
        order=1,
        crate_key="dark_hypnotic",
        move_key="shadow_filter_pressure",
        status="staged",
        mutation_amount_percent=28,
        target_pads=(1, 3, 11),
        operator_note="Start with a low-risk darkening move and listen before adding density.",
    ),
    StyleQueueMove(
        key="queue-groove-pressure",
        use_case="set_story",
        chapter="pressure lift",
        order=2,
        crate_key="hard_groove",
        move_key="rolling_perc_push",
        status="staged",
        mutation_amount_percent=45,
        target_pads=(2, 3, 5, 6, 7, 9),
        operator_note="Use as the first 12-pad studio-work target once support is promoted.",
    ),
    StyleQueueMove(
        key="queue-peak-metal",
        use_case="set_story",
        chapter="peak stress",
        order=3,
        crate_key="industrial_broken",
        move_key="broken_metal_stress",
        status="staged",
        mutation_amount_percent=64,
        target_pads=(3, 4, 8, 10, 11),
        operator_note="Keep Back To Clean staged before this is ever armed.",
    ),
    StyleQueueMove(
        key="queue-scratchpad-clean",
        use_case="live_scratchpad",
        chapter="scratchpad recovery",
        order=4,
        crate_key="transitions",
        move_key="back_to_clean_handoff",
        status="scratchpad",
        mutation_amount_percent=0,
        target_pads=(1, 2, 3, 4),
        operator_note="Manual recovery candidate; passive queue does not fire it.",
    ),
)

_DEFAULT_MUTATION_JOURNAL_ITEMS: Final[tuple[MutationJournalEntry, ...]] = (
    MutationJournalEntry(
        key="warehouse_accident_01",
        name="Warehouse Accident 01",
        tags=("warehouse", "accident", "hypnotic", "keeper"),
        seed="style-journal-warehouse-0001",
        pads=(1, 3, 11),
        values={
            "pad_1_filter_frequency": 26,
            "pad_3_lfo_depth": 92,
            "pad_11_noise_level": 7,
        },
        depth="groove",
        guardrail_mode="live_safe",
        notes="Useful metallic motion that stayed controlled after returning to clean.",
    ),
    MutationJournalEntry(
        key="broken_fill_seed_02",
        name="Broken Fill Seed 02",
        tags=("industrial", "fill", "one_shot", "review"),
        seed="style-journal-broken-0002",
        pads=(4, 8, 10, 11),
        values={
            "pad_4_decay": 87,
            "pad_8_accent_pressure": 72,
            "pad_10_hat_density": 64,
            "pad_11_drive": 81,
        },
        depth="strong",
        guardrail_mode="studio_wild",
        notes="Save for studio exploration; too risky for Live Safe without a reset cue.",
    ),
)


def _validated_queue(queue: tuple[StyleQueueMove, ...]) -> tuple[StyleQueueMove, ...]:
    for queued in queue:
        _validate_nonblank(queued.key, field="queue key")
        if queued.order < 1:
            raise ValueError(f"{queued.key} order must be >= 1")
        if queued.crate_key not in STYLE_CRATES:
            raise ValueError(f"{queued.key} references unknown crate {queued.crate_key}")
        crate = STYLE_CRATES[queued.crate_key]
        if all(move.key != queued.move_key for move in crate.moves):
            raise ValueError(f"{queued.key} references unknown move {queued.move_key}")
        if not 0 <= queued.mutation_amount_percent <= 100:
            raise ValueError(f"{queued.key} mutation_amount_percent must be in 0..100")
        _validate_pads(queued.key, queued.target_pads)
    return queue


def _validated_journal(
    entries: tuple[MutationJournalEntry, ...],
) -> tuple[MutationJournalEntry, ...]:
    for entry in entries:
        _validate_nonblank(entry.key, field="journal key")
        _validate_nonblank(entry.seed, field=f"{entry.key} seed")
        _validate_pads(entry.key, entry.pads)
        if entry.guardrail_mode not in DANGER_MODES:
            raise ValueError(f"{entry.key} guardrail_mode must be a known danger mode")
    return entries


DEFAULT_STYLE_QUEUE: Final[tuple[StyleQueueMove, ...]] = _validated_queue(
    _DEFAULT_STYLE_QUEUE_ITEMS
)
DEFAULT_MUTATION_JOURNAL: Final[tuple[MutationJournalEntry, ...]] = _validated_journal(
    _DEFAULT_MUTATION_JOURNAL_ITEMS
)

__all__ = [
    "DEFAULT_MUTATION_JOURNAL",
    "DEFAULT_STYLE_QUEUE",
    "DANGER_MODES",
    "FUTURE_DANGER_MODE_LABELS",
    "DangerMode",
    "MoveMode",
    "MutationJournalEntry",
    "QueueMoveStatus",
    "QueueUseCase",
    "STYLE_CRATES",
    "StyleCrate",
    "StyleCrateMove",
    "StyleQueueMove",
]
