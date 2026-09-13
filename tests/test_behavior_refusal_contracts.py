"""Passive behavior contracts when known commands are outside a packet's scope."""

from collections.abc import Callable

import pytest

from rytm_randomizer.behavior import pad_lane, scene_group
from rytm_randomizer.behavior.selected_isolated_pad import (
    SelectedIsolatedPadBehaviorResult,
    evaluate_selected_isolated_pad_behavior,
)
from rytm_randomizer.behavior.selected_profile import (
    SelectedProfileBehaviorResult,
    evaluate_selected_profile_behavior,
)
from rytm_randomizer.behavior.undo_commit_state import (
    UndoCommitStateBehaviorResult,
    evaluate_undo_commit_state_behavior,
)

pytestmark = pytest.mark.fast


def test_default_behavior_metadata_is_empty_immutable_and_separate() -> None:
    first = SelectedProfileBehaviorResult(command_key="P")
    second = SelectedProfileBehaviorResult(command_key="M")

    assert first.metadata == second.metadata == {}
    assert first.metadata is not second.metadata
    with pytest.raises(TypeError):
        first.metadata["source"] = "changed"  # type: ignore[index]
    assert second.metadata == {}


@pytest.mark.parametrize(
    ("evaluate", "reason"),
    (
        (evaluate_selected_profile_behavior, "unsupported_packet_10_selected_profile_key"),
        (
            evaluate_selected_isolated_pad_behavior,
            "unsupported_packet_11_selected_isolated_pad_key",
        ),
        (evaluate_undo_commit_state_behavior, "unsupported_packet_9_undo_commit_state_key"),
    ),
)
def test_other_packet_command_is_refused_without_runtime_authority(
    evaluate: Callable[
        [str],
        SelectedProfileBehaviorResult
        | SelectedIsolatedPadBehaviorResult
        | UndoCommitStateBehaviorResult,
    ],
    reason: str,
) -> None:
    # BD is a known catalog command outside these three utility packets.
    result = evaluate("BD")

    assert result.command_key == "BD"
    assert result.accepted is False
    assert result.reason == reason
    assert result.metadata["source"] == "COMMANDS"
    assert result.display_lines == ()
    assert result.state_changed is False
    assert result.mutates_runtime_state is False
    assert result.executes_command is False
    assert result.opens_ports is False
    assert result.sends_real_midi is False


def test_withdrawn_pad_command_is_reported_as_deferred(monkeypatch: pytest.MonkeyPatch) -> None:
    assert pad_lane.evaluate_pad1_lane_behavior("BR").accepted is True

    # Exercise a real catalog key withdrawn from packet support. The test
    # restores both tables, and does not modify the shared command registry.
    monkeypatch.setattr(
        pad_lane,
        "_REGISTRY",
        {key: value for key, value in pad_lane._REGISTRY.items() if key != "BR"},
    )
    monkeypatch.setattr(pad_lane, "DEFERRED_PACKET_5_PAD1_LANE_KEYS", ("BR",))

    result = pad_lane.evaluate_pad1_lane_behavior("BR")

    assert result.accepted is False
    assert result.reason == "deferred_pad1_lane_command"
    assert result.metadata["source"] == "PAD1_COMMANDS"
    assert result.executes_command is False
    assert result.sends_real_midi is False
    assert result.opens_ports is False


@pytest.mark.parametrize(
    ("command", "accepted_table", "deferred_table", "reason"),
    (
        (
            "X",
            "PACKET_4B_GROUP_MUTATION_INTENT_KEYS",
            "DEFERRED_GROUP_MUTATION_KEYS",
            "deferred_group_mutation_command",
        ),
        (
            "Y",
            "PACKET_4C_LANE_AWARE_GROUP_MUTATION_INTENT_KEYS",
            "DEFERRED_LANE_AWARE_GROUP_MUTATION_KEYS",
            "deferred_lane_aware_group_mutation_command",
        ),
    ),
)
def test_withdrawn_group_commands_stay_passive_and_explain_deferral(
    monkeypatch: pytest.MonkeyPatch,
    command: str,
    accepted_table: str,
    deferred_table: str,
    reason: str,
) -> None:
    monkeypatch.setattr(scene_group, accepted_table, ())
    monkeypatch.setattr(scene_group, deferred_table, (command,))

    result = scene_group.evaluate_scene_group_behavior(command)

    assert result.command_key == command
    assert result.accepted is False
    assert result.reason == reason
    assert result.metadata["source"] == "GROUP_COMMANDS"
    assert result.executes_scene is False
    assert result.executes_group_mutation is False
    assert result.state_changed is False
    assert result.sends_real_midi is False
    assert result.opens_ports is False


def test_known_group_command_without_supported_packet_is_refused(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(scene_group, "PACKET_4D_GROUP_ANCHOR_INTENT_KEYS", ())

    result = scene_group.evaluate_scene_group_behavior("O")

    assert result.accepted is False
    assert result.reason == "unsupported_scene_group_command"
    assert result.metadata["source"] == "GROUP_COMMANDS"
    assert result.executes_scene is False
    assert result.executes_group_mutation is False
    assert result.state_changed is False
    assert result.sends_real_midi is False
    assert result.opens_ports is False
