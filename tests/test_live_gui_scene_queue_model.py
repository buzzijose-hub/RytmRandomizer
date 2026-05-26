"""Tests for the passive live GUI scene queue model."""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.fast


def test_scene_queue_model_exposes_all_v134_scenes_and_risk_states() -> None:
    from rytm_randomizer.data import SCENE_PRESETS
    from rytm_randomizer.reports.live_gui_scene_queue_model import (
        build_live_gui_scene_queue_model,
    )

    model = build_live_gui_scene_queue_model()

    assert model.model_version == "live-gui-scene-queue-model-v1"
    assert tuple(card.scene_key.lower() for card in model.scene_cards) == tuple(SCENE_PRESETS)
    assert len(model.scene_cards) == 14
    home = model.scene_cards[0]
    assert home.scene_key == "S0"
    assert home.status == "safe"
    assert home.mutation_depth_percent == 15
    assert home.affected_pads == (1, 2, 3, 4)
    wild = next(card for card in model.scene_cards if card.scene_key == "S4B")
    assert wild.label == "Wild Maximum"
    assert wild.status == "high-risk"
    assert wild.mutation_depth_percent == 85
    assert wild.affected_pads == (1, 2, 3, 4)
    assert wild.depth_tokens == ("strong",)


def test_scene_queue_model_builds_preview_queue_and_passive_payload() -> None:
    from rytm_randomizer.reports.live_gui_scene_queue_model import (
        build_live_gui_scene_queue_model,
        live_gui_scene_queue_model_payload,
    )

    model = build_live_gui_scene_queue_model(queue_keys=("s1", "s1a", "s2", "s3", "s4"))

    assert tuple(item.scene_key for item in model.preview_queue) == (
        "S1",
        "S1A",
        "S2",
        "S3",
        "S4",
    )
    assert model.preview_queue[0].queue_position == "current"
    assert model.preview_queue[1].queue_position == "up-next-1"
    assert model.preview_queue[-1].estimated_duration_seconds == 32
    assert model.preview_queue[-1].status == "high-risk"
    assert model.queue_status == "review-needed"
    assert model.blocked_actions == (
        "open_midi_port",
        "send_midi",
        "arm_hardware",
        "execute_scene",
    )

    payload = live_gui_scene_queue_model_payload(model)
    scene_payload = payload["live_gui_scene_queue_model"]
    assert scene_payload["queue_status"] == "review-needed"
    assert scene_payload["scene_count"] == 14
    assert scene_payload["preview_queue"][0]["scene_key"] == "S1"
    assert scene_payload["scene_cards"][-1]["scene_key"] == "S5"
    assert scene_payload["safety_lines"][0] == "passive/read-only"
    assert scene_payload["blocked_actions"] == list(model.blocked_actions)

    ready_model = build_live_gui_scene_queue_model(queue_keys=("s1", "s1a"))
    assert ready_model.queue_status == "ready"


def test_scene_queue_model_supports_future_scene_presets() -> None:
    from rytm_randomizer.reports.live_gui_scene_queue_model import (
        build_live_gui_scene_queue_model,
    )

    model = build_live_gui_scene_queue_model(
        scene_presets={
            "s9": {
                "name": "Future Hold",
                "description": "Unknown future scene for GUI review.",
                "action": "future_hold",
            }
        },
        intensity_plans={},
        queue_keys=("missing", "s9"),
    )

    card = model.scene_cards[0]
    assert card.scene_key == "S9"
    assert card.status == "review-needed"
    assert card.affected_pads == ()
    assert card.mutation_depth_percent == 0
    assert card.operator_hint == "Review future_hold before enabling scene execution."
    assert model.preview_queue[0].status == "review-needed"
    assert model.queue_status == "review-needed"

    from rytm_randomizer.reports.live_gui_scene_queue_model import (
        format_live_gui_scene_queue_model_report,
    )

    assert "- S9 Future Hold: depth 0%, pads none, status review-needed" in "\n".join(
        format_live_gui_scene_queue_model_report(model)
    )


def test_scene_queue_model_report_is_operator_readable_and_passive() -> None:
    from rytm_randomizer.reports.live_gui_scene_queue_model import (
        build_live_gui_scene_queue_model,
        format_live_gui_scene_queue_model_report,
    )

    lines = format_live_gui_scene_queue_model_report(build_live_gui_scene_queue_model())
    text = "\n".join(lines)

    assert lines[0] == "RytmRandomizer passive live GUI scene queue model"
    assert "Scene rail:" in text
    assert "- S4B Wild Maximum: depth 85%, pads 1/2/3/4, status high-risk" in text
    assert "Live preview queue:" in text
    assert "- current: S1 Rolling, ~16s, status armed" in text
    assert "no MIDI sending" in text
    assert "no port opening" in text
