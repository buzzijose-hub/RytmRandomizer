"""Passive live GUI scene rail and preview-queue model."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Final

from ..data import INTENSITY_PLANS, SCENE_PRESETS

REPORT_TITLE: Final[str] = "RytmRandomizer passive live GUI scene queue model"
SOURCE_MODULE: Final[str] = "reports.live_gui_scene_queue_model"
SCENE_QUEUE_MODEL_VERSION: Final[str] = "live-gui-scene-queue-model-v1"
SAFETY_LINES: Final[tuple[str, ...]] = (
    "passive/read-only",
    "GUI scene rail model only",
    "live preview queue metadata only",
    "scene execution remains blocked",
    "dry-run message estimates only",
    "JSON/stdout only",
    "no GUI launch",
    "no file writing",
    "no real MIDI rendering",
    "no MIDI sending",
    "no port opening",
    "no hardware mutation",
    "no hardware required",
)
BLOCKED_ACTIONS: Final[tuple[str, ...]] = (
    "open_midi_port",
    "send_midi",
    "arm_hardware",
    "execute_scene",
)
DEFAULT_QUEUE_KEYS: Final[tuple[str, ...]] = ("s1", "s1a", "s2", "s3", "s4")
_DEPTH_PERCENT: Final[dict[str, int]] = {
    "micro": 15,
    "groove": 42,
    "strong": 68,
}
_DEPTH_RANK: Final[dict[str, int]] = {
    "micro": 1,
    "groove": 2,
    "strong": 3,
}

ScenePresetMap = Mapping[str, Mapping[str, str]]
IntensityPlanMap = Mapping[str, Mapping[int, Sequence[tuple[str, str]]]]


@dataclass(frozen=True)
class LiveGuiSceneCard:
    """One GUI-ready scene rail card."""

    scene_key: str
    order: int
    label: str
    description: str
    action: str
    affected_pads: tuple[int, ...]
    zone_tokens: tuple[str, ...]
    depth_tokens: tuple[str, ...]
    mutation_depth_percent: int
    dry_run_message_count: int
    status: str
    operator_hint: str
    passive: bool


@dataclass(frozen=True)
class LiveGuiScenePreviewQueueItem:
    """One GUI-ready live preview queue item."""

    scene_key: str
    queue_index: int
    queue_position: str
    label: str
    status: str
    estimated_duration_seconds: int
    mutation_depth_percent: int
    affected_pads: tuple[int, ...]
    dry_run_message_count: int
    passive: bool


@dataclass(frozen=True)
class LiveGuiSceneQueueModel:
    """Passive scene rail and preview queue packet for future GUI consumers."""

    model_version: str
    source_module: str
    scene_count: int
    queue_status: str
    scene_cards: tuple[LiveGuiSceneCard, ...]
    preview_queue: tuple[LiveGuiScenePreviewQueueItem, ...]
    safety_lines: tuple[str, ...]
    blocked_actions: tuple[str, ...]


def _live_gui_scene_plan(
    action: str,
    *,
    intensity_plans: IntensityPlanMap,
) -> Mapping[int, Sequence[tuple[str, str]]]:
    return intensity_plans.get(action, {})


def _live_gui_scene_depth_tokens(
    plan: Mapping[int, Sequence[tuple[str, str]]],
) -> tuple[str, ...]:
    tokens = {depth for pad_plan in plan.values() for _zone, depth in pad_plan}
    if not tokens:
        return ()
    highest_rank = max(_DEPTH_RANK.get(token, 0) for token in tokens)
    return tuple(sorted(token for token in tokens if _DEPTH_RANK.get(token, 0) == highest_rank))


def _live_gui_scene_zone_tokens(
    plan: Mapping[int, Sequence[tuple[str, str]]],
) -> tuple[str, ...]:
    tokens = {zone for pad_plan in plan.values() for zone, _depth in pad_plan}
    return tuple(sorted(tokens))


def _live_gui_scene_depth_percent(
    *,
    action: str,
    depth_tokens: Sequence[str],
) -> int:
    if action in {"harder", "wild_controlled", "wild_maximum"}:
        return 85
    if depth_tokens:
        return max(_DEPTH_PERCENT.get(token, 0) for token in depth_tokens)
    if action in {"home", "clean"}:
        return 15
    return 0


def _live_gui_scene_status(*, action: str, depth_percent: int) -> str:
    if action in {"home", "clean"}:
        return "safe"
    if depth_percent >= 68:
        return "high-risk"
    if depth_percent > 0:
        return "armed"
    return "review-needed"


def _live_gui_scene_operator_hint(*, action: str, status: str) -> str:
    if action in {"home", "clean"}:
        return "Anchor/reset scene is safe for passive review."
    if status == "high-risk":
        return "High-risk scene requires dry run and explicit hardware arm later."
    if status == "review-needed":
        return f"Review {action} before enabling scene execution."
    return "Dry-run scene preview is ready for operator review."


def _live_gui_scene_affected_pads(
    *,
    action: str,
    plan: Mapping[int, Sequence[tuple[str, str]]],
) -> tuple[int, ...]:
    if plan:
        return tuple(sorted(plan))
    if action in {"home", "clean"}:
        return (1, 2, 3, 4)
    return ()


def _live_gui_scene_dry_run_count(
    *,
    affected_pads: Sequence[int],
    plan: Mapping[int, Sequence[tuple[str, str]]],
    action: str,
) -> int:
    if action in {"home", "clean"}:
        return 18
    operation_count = sum(len(pad_plan) for pad_plan in plan.values())
    return operation_count * 7 + len(affected_pads) * 2


def _live_gui_scene_card(
    scene_key: str,
    order: int,
    preset: Mapping[str, str],
    *,
    intensity_plans: IntensityPlanMap,
) -> LiveGuiSceneCard:
    action = preset["action"]
    plan = _live_gui_scene_plan(action, intensity_plans=intensity_plans)
    depth_tokens = _live_gui_scene_depth_tokens(plan)
    zone_tokens = _live_gui_scene_zone_tokens(plan)
    depth_percent = _live_gui_scene_depth_percent(
        action=action,
        depth_tokens=depth_tokens,
    )
    status = _live_gui_scene_status(action=action, depth_percent=depth_percent)
    affected_pads = _live_gui_scene_affected_pads(action=action, plan=plan)
    dry_run_count = _live_gui_scene_dry_run_count(
        affected_pads=affected_pads,
        plan=plan,
        action=action,
    )
    return LiveGuiSceneCard(
        scene_key=scene_key.upper(),
        order=order,
        label=preset["name"],
        description=preset["description"],
        action=action,
        affected_pads=affected_pads,
        zone_tokens=zone_tokens,
        depth_tokens=depth_tokens,
        mutation_depth_percent=depth_percent,
        dry_run_message_count=dry_run_count,
        status=status,
        operator_hint=_live_gui_scene_operator_hint(action=action, status=status),
        passive=True,
    )


def _live_gui_scene_queue_position(index: int) -> str:
    if index == 1:
        return "current"
    return f"up-next-{index - 1}"


def _live_gui_scene_estimated_duration(card: LiveGuiSceneCard) -> int:
    if card.status == "review-needed":
        return 0
    if card.status == "high-risk":
        return 32
    return 16


def _live_gui_scene_queue_status(
    queue_items: Sequence[LiveGuiScenePreviewQueueItem],
) -> str:
    statuses = {item.status for item in queue_items}
    if "high-risk" in statuses:
        return "review-needed"
    if "review-needed" in statuses:
        return "review-needed"
    return "ready"


def _live_gui_scene_preview_queue(
    scene_cards: Sequence[LiveGuiSceneCard],
    *,
    queue_keys: Sequence[str],
) -> tuple[LiveGuiScenePreviewQueueItem, ...]:
    by_key = {card.scene_key.lower(): card for card in scene_cards}
    items: list[LiveGuiScenePreviewQueueItem] = []
    for raw_key in queue_keys:
        card = by_key.get(raw_key.lower())
        if card is None:
            continue
        index = len(items) + 1
        items.append(
            LiveGuiScenePreviewQueueItem(
                scene_key=card.scene_key,
                queue_index=index,
                queue_position=_live_gui_scene_queue_position(index),
                label=card.label,
                status=card.status,
                estimated_duration_seconds=_live_gui_scene_estimated_duration(card),
                mutation_depth_percent=card.mutation_depth_percent,
                affected_pads=card.affected_pads,
                dry_run_message_count=card.dry_run_message_count,
                passive=True,
            )
        )
    return tuple(items)


def build_live_gui_scene_queue_model(
    *,
    scene_presets: ScenePresetMap = SCENE_PRESETS,
    intensity_plans: IntensityPlanMap = INTENSITY_PLANS,
    queue_keys: Sequence[str] = DEFAULT_QUEUE_KEYS,
) -> LiveGuiSceneQueueModel:
    """Build a passive GUI-ready scene rail and preview queue model."""

    scene_cards = tuple(
        _live_gui_scene_card(
            scene_key,
            order,
            preset,
            intensity_plans=intensity_plans,
        )
        for order, (scene_key, preset) in enumerate(scene_presets.items(), start=1)
    )
    preview_queue = _live_gui_scene_preview_queue(scene_cards, queue_keys=queue_keys)
    return LiveGuiSceneQueueModel(
        model_version=SCENE_QUEUE_MODEL_VERSION,
        source_module=SOURCE_MODULE,
        scene_count=len(scene_cards),
        queue_status=_live_gui_scene_queue_status(preview_queue),
        scene_cards=scene_cards,
        preview_queue=preview_queue,
        safety_lines=SAFETY_LINES,
        blocked_actions=BLOCKED_ACTIONS,
    )


def _live_gui_scene_card_payload(card: LiveGuiSceneCard) -> dict[str, object]:
    return {
        "scene_key": card.scene_key,
        "order": card.order,
        "label": card.label,
        "description": card.description,
        "action": card.action,
        "affected_pads": list(card.affected_pads),
        "zone_tokens": list(card.zone_tokens),
        "depth_tokens": list(card.depth_tokens),
        "mutation_depth_percent": card.mutation_depth_percent,
        "dry_run_message_count": card.dry_run_message_count,
        "status": card.status,
        "operator_hint": card.operator_hint,
        "passive": card.passive,
    }


def _live_gui_scene_queue_item_payload(
    item: LiveGuiScenePreviewQueueItem,
) -> dict[str, object]:
    return {
        "scene_key": item.scene_key,
        "queue_index": item.queue_index,
        "queue_position": item.queue_position,
        "label": item.label,
        "status": item.status,
        "estimated_duration_seconds": item.estimated_duration_seconds,
        "mutation_depth_percent": item.mutation_depth_percent,
        "affected_pads": list(item.affected_pads),
        "dry_run_message_count": item.dry_run_message_count,
        "passive": item.passive,
    }


def live_gui_scene_queue_model_payload(
    model: LiveGuiSceneQueueModel,
) -> dict[str, object]:
    """Return deterministic JSON-ready scene queue model payload."""

    return {
        "live_gui_scene_queue_model": {
            "model_version": model.model_version,
            "source_module": model.source_module,
            "scene_count": model.scene_count,
            "queue_status": model.queue_status,
            "scene_cards": [_live_gui_scene_card_payload(card) for card in model.scene_cards],
            "preview_queue": [
                _live_gui_scene_queue_item_payload(item) for item in model.preview_queue
            ],
            "safety_lines": list(model.safety_lines),
            "blocked_actions": list(model.blocked_actions),
        }
    }


def _live_gui_scene_pad_label(pads: Sequence[int]) -> str:
    if not pads:
        return "none"
    return "/".join(str(pad) for pad in pads)


def _live_gui_scene_queue_body_lines(
    model: LiveGuiSceneQueueModel,
) -> tuple[str, ...]:
    lines: list[str] = [
        REPORT_TITLE,
        "",
        "Scene rail:",
    ]
    for card in model.scene_cards:
        lines.append(
            f"- {card.scene_key} {card.label}: depth "
            f"{card.mutation_depth_percent}%, pads "
            f"{_live_gui_scene_pad_label(card.affected_pads)}, status {card.status}"
        )
    lines.extend(("", "Live preview queue:"))
    for item in model.preview_queue:
        lines.append(
            f"- {item.queue_position}: {item.scene_key} {item.label}, "
            f"~{item.estimated_duration_seconds}s, status {item.status}"
        )
    lines.extend(("", "Passive safety:"))
    lines.extend(f"- {line}" for line in model.safety_lines)
    lines.extend(("", "Blocked actions:"))
    lines.extend(f"- {action}" for action in model.blocked_actions)
    return tuple(lines)


def format_live_gui_scene_queue_model_report(
    model: LiveGuiSceneQueueModel,
) -> tuple[str, ...]:
    """Return deterministic operator-readable scene queue model lines."""

    return _live_gui_scene_queue_body_lines(model)


__all__ = [
    "LiveGuiSceneCard",
    "LiveGuiScenePreviewQueueItem",
    "LiveGuiSceneQueueModel",
    "build_live_gui_scene_queue_model",
    "format_live_gui_scene_queue_model_report",
    "live_gui_scene_queue_model_payload",
]
