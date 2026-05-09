from pathlib import Path
import subprocess
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


SCENE_INTENT_KEYS = (
    "S0",
    "S1",
    "S1A",
    "S1B",
    "S2",
    "S2A",
    "S2B",
    "S3",
    "S3A",
    "S3B",
    "S4",
    "S4A",
    "S4B",
    "S5",
)
DEFERRED_GROUP_MUTATION_KEYS = ("X", "D", "I", "4")
DEFERRED_LANE_AWARE_GROUP_MUTATION_KEYS = ("Y", "V", "N")


def run_cli(*args):
    return subprocess.run(
        [sys.executable, "-m", "rytm_randomizer.cli", *args],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def test_importing_behavior_scene_group_prints_nothing():
    result = subprocess.run(
        [sys.executable, "-c", "import rytm_randomizer.behavior_scene_group"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert result.stdout == ""
    assert result.stderr == ""


def test_scene_intent_keys_return_read_only_results():
    from rytm_randomizer.behavior_scene_group import evaluate_scene_group_behavior

    for command_key in SCENE_INTENT_KEYS:
        result = evaluate_scene_group_behavior(command_key)

        assert result.accepted is True
        assert result.command_key == command_key
        assert result.behavior_family == "scene-group/scene-intent"
        assert result.reason == "supported_scene_intent"
        assert result.scene_scope == "four_pad_group"
        assert result.state_changed is False
        assert result.prompt_required is False
        assert result.dispatches_command is False
        assert result.executes_scene is False
        assert result.executes_group_mutation is False
        assert result.sends_real_midi is False
        assert result.opens_ports is False
        assert result.hardware_required is False
        assert result.active_behavior is False
        assert result.display_lines


def test_s0_returns_home_clean_scene_intent_without_anchor_loading():
    from rytm_randomizer.behavior_scene_group import evaluate_scene_group_behavior

    result = evaluate_scene_group_behavior("S0")

    assert result.accepted is True
    assert result.scene_name == "Home / Clean"
    assert result.scene_action == "home"
    assert result.loads_anchors is False
    assert result.display_lines == (
        "S0: Home / Clean",
        "Read-only scene intent.",
        "Scene action: home",
        "Scene scope: four_pad_group",
        "No scene would execute.",
        "No anchors would load.",
        "No state would change.",
        "No command would dispatch.",
        "No MIDI would be sent.",
        "No ports would be opened.",
    )
    assert result.metadata["source"] == "SCENE_COMMANDS"
    assert result.metadata["source_scene_name"] == "Home / Clean"
    assert result.metadata["source_scene_action"] == "home"
    assert result.metadata["source_scene_scope"] == "four_pad_group"
    assert result.metadata["loads_anchors"] is False
    assert result.metadata["executes_scene"] is False
    assert result.metadata["mutates_runtime_state"] is False


def test_s1a_returns_rolling_light_scene_intent_without_scene_execution():
    from rytm_randomizer.behavior_scene_group import evaluate_scene_group_behavior

    result = evaluate_scene_group_behavior("S1A")

    assert result.accepted is True
    assert result.scene_name == "Rolling Light"
    assert result.scene_action == "rolling_light"
    assert result.executes_scene is False
    assert result.state_changed is False
    assert result.metadata["source_scene_description"] == (
        "Lower-risk rolling movement for subtle live variation."
    )
    assert result.metadata["forbidden_early_hardware_scope"] is False


def test_s4b_returns_wild_maximum_scene_intent_with_early_hardware_guardrail():
    from rytm_randomizer.behavior_scene_group import evaluate_scene_group_behavior

    result = evaluate_scene_group_behavior("S4B")

    assert result.accepted is True
    assert result.scene_name == "Wild Maximum"
    assert result.scene_action == "wild_maximum"
    assert result.executes_scene is False
    assert result.state_changed is False
    assert result.metadata["forbidden_early_hardware_scope"] is True
    assert "Early hardware scope: forbidden." in result.display_lines


def test_s5_returns_back_to_clean_scene_intent_without_anchor_loading():
    from rytm_randomizer.behavior_scene_group import evaluate_scene_group_behavior

    result = evaluate_scene_group_behavior("S5")

    assert result.accepted is True
    assert result.scene_name == "Back to Clean"
    assert result.scene_action == "clean"
    assert result.loads_anchors is False
    assert result.executes_scene is False
    assert result.state_changed is False
    assert result.metadata["loads_anchors"] is False


def test_scene_group_metadata_is_copied_and_immutable():
    from rytm_randomizer.behavior_scene_group import SceneGroupBehaviorResult

    metadata = {"source": "test"}
    result = SceneGroupBehaviorResult(command_key="S0", metadata=metadata)

    metadata["source"] = "changed"

    assert result.metadata["source"] == "test"

    try:
        result.metadata["source"] = "mutated"
    except TypeError:
        pass
    else:
        raise AssertionError("metadata should be immutable")


def test_repeated_scene_group_evaluations_are_deterministic():
    from rytm_randomizer.behavior_scene_group import evaluate_scene_group_behavior

    for command_key in SCENE_INTENT_KEYS:
        assert evaluate_scene_group_behavior(command_key) == (
            evaluate_scene_group_behavior(command_key)
        )


def test_unknown_keys_fail_safely():
    from rytm_randomizer.behavior_scene_group import evaluate_scene_group_behavior

    result = evaluate_scene_group_behavior("DOES_NOT_EXIST")

    assert result.accepted is False
    assert result.reason == "unknown_command"
    assert result.display_lines == ()
    assert result.state_changed is False
    assert result.prompt_required is False
    assert result.dispatches_command is False
    assert result.executes_scene is False
    assert result.executes_group_mutation is False
    assert result.sends_real_midi is False
    assert result.opens_ports is False
    assert result.hardware_required is False
    assert result.active_behavior is False


def test_group_mutation_keys_remain_deferred_and_safe():
    from rytm_randomizer.behavior_scene_group import evaluate_scene_group_behavior

    for command_key in DEFERRED_GROUP_MUTATION_KEYS:
        result = evaluate_scene_group_behavior(command_key)

        assert result.accepted is False
        assert result.reason == "deferred_group_mutation_command"
        assert result.executes_group_mutation is False
        assert result.dispatches_command is False
        assert result.sends_real_midi is False
        assert result.opens_ports is False
        assert result.hardware_required is False
        assert result.active_behavior is False
        assert result.metadata["source"] == "GROUP_COMMANDS"


def test_lane_aware_group_mutation_keys_remain_deferred_and_safe():
    from rytm_randomizer.behavior_scene_group import evaluate_scene_group_behavior

    for command_key in DEFERRED_LANE_AWARE_GROUP_MUTATION_KEYS:
        result = evaluate_scene_group_behavior(command_key)

        assert result.accepted is False
        assert result.reason == "deferred_lane_aware_group_mutation_command"
        assert result.executes_group_mutation is False
        assert result.dispatches_command is False
        assert result.sends_real_midi is False
        assert result.opens_ports is False
        assert result.hardware_required is False
        assert result.active_behavior is False
        assert result.metadata["source"] == "GROUP_COMMANDS"


def test_packet_1_menu_utility_behavior_remains_unchanged():
    from rytm_randomizer.behavior_menu_utility import evaluate_menu_utility_behavior

    result = evaluate_menu_utility_behavior("SCN")

    assert result.accepted is True
    assert result.label == "show scene / preset tools"
    assert result.metadata["executes_scene"] is False
    assert result.sends_real_midi is False
    assert result.active_behavior is False


def test_packet_2_anchor_profile_behavior_remains_unchanged():
    from rytm_randomizer.behavior_anchor_profile import (
        evaluate_anchor_profile_behavior,
    )

    result = evaluate_anchor_profile_behavior("BH")

    assert result.accepted is True
    assert result.label == "load Pad 1 BD Hard anchor, primary default"
    assert result.profile_key == "2"
    assert result.machine_value == 0
    assert result.sends_real_midi is False
    assert result.active_behavior is False


def test_packet_3_mutation_depth_behavior_remains_unchanged():
    from rytm_randomizer.behavior_mutation_depth import (
        evaluate_mutation_depth_behavior,
    )

    result = evaluate_mutation_depth_behavior("PM")

    assert result.accepted is True
    assert result.behavior_family == "mutation-depth/selected-isolated-pad"
    assert result.sends_real_midi is False
    assert result.active_behavior is False


def test_passive_cli_behavior_remains_unchanged():
    result = run_cli("preview-scene", "S1A")

    assert result.returncode == 0
    assert "Scene: S1A" in result.stdout
    assert "No scene would execute." in result.stdout
    assert result.stderr == ""


def test_no_real_midi_library_is_imported():
    import rytm_randomizer.behavior_scene_group  # noqa: F401

    assert "mido" not in sys.modules
    assert "rtmidi" not in sys.modules


def test_no_package_metadata_files_are_introduced():
    for filename in ("pyproject.toml", "requirements.txt", "setup.py", "setup.cfg"):
        assert not (PROJECT_ROOT / filename).exists()


def test_behavior_scene_group_exposes_no_active_behavior_names():
    import rytm_randomizer.behavior_scene_group as behavior_scene_group

    exposed_names = set(dir(behavior_scene_group))

    assert "execute_command" not in exposed_names
    assert "send_command" not in exposed_names
    assert "hardware_test" not in exposed_names


def test_no_out_of_scope_support_is_exposed():
    import rytm_randomizer.behavior_scene_group as behavior_scene_group

    module_text = "\n".join(
        [
            behavior_scene_group.__doc__ or "",
            behavior_scene_group.evaluate_scene_group_behavior.__doc__ or "",
        ]
    )

    assert "Analog Four support" not in module_text
    assert "Pads 5-12 support" not in module_text


if __name__ == "__main__":
    test_importing_behavior_scene_group_prints_nothing()
    test_scene_intent_keys_return_read_only_results()
    test_s0_returns_home_clean_scene_intent_without_anchor_loading()
    test_s1a_returns_rolling_light_scene_intent_without_scene_execution()
    test_s4b_returns_wild_maximum_scene_intent_with_early_hardware_guardrail()
    test_s5_returns_back_to_clean_scene_intent_without_anchor_loading()
    test_scene_group_metadata_is_copied_and_immutable()
    test_repeated_scene_group_evaluations_are_deterministic()
    test_unknown_keys_fail_safely()
    test_group_mutation_keys_remain_deferred_and_safe()
    test_lane_aware_group_mutation_keys_remain_deferred_and_safe()
    test_packet_1_menu_utility_behavior_remains_unchanged()
    test_packet_2_anchor_profile_behavior_remains_unchanged()
    test_packet_3_mutation_depth_behavior_remains_unchanged()
    test_passive_cli_behavior_remains_unchanged()
    test_no_real_midi_library_is_imported()
    test_no_package_metadata_files_are_introduced()
    test_behavior_scene_group_exposes_no_active_behavior_names()
    test_no_out_of_scope_support_is_exposed()
