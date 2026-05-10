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
GROUP_MUTATION_INTENT_EXPECTATIONS = {
    "X": {
        "label": "balanced four-lane mutate full 4-pad group",
        "mode": "balanced_four_lane",
        "intensity": "balanced",
    },
    "D": {
        "label": "deeper four-lane mutation, Pads 2-4 pushed harder",
        "mode": "deeper_four_lane",
        "intensity": "deeper",
    },
    "I": {
        "label": "intense / controlled chaos four-lane mutation",
        "mode": "intense_controlled_chaos",
        "intensity": "intense",
    },
    "4": {
        "label": "harder / wild four-lane mutation",
        "mode": "harder_wild_four_lane",
        "intensity": "wild",
    },
}
LANE_AWARE_GROUP_MUTATION_INTENT_EXPECTATIONS = {
    "Y": {
        "label": "lane-aware SRC/morph mutation on all 4 group pads",
        "page": "src_morph",
        "mode": "lane_aware_src_morph",
    },
    "V": {
        "label": "lane-aware filter mutation on all 4 group pads",
        "page": "filter",
        "mode": "lane_aware_filter",
    },
    "N": {
        "label": "lane-aware grit mutation on all 4 group pads",
        "page": "grit",
        "mode": "lane_aware_grit",
    },
}
GROUP_ANCHOR_INTENT_EXPECTATIONS = {
    "O": {
        "label": "load full 4-pad group anchors",
        "command_type": "load",
        "anchor_action": "load_group_anchors",
        "reason": "supported_group_anchor_load_intent",
    },
    "Z": {
        "label": "return all 4 group pads to anchors",
        "command_type": "anchor_return",
        "anchor_action": "return_group_anchors",
        "reason": "supported_group_anchor_return_intent",
    },
}


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


def test_group_mutation_keys_return_read_only_intent_results():
    from rytm_randomizer.behavior_scene_group import evaluate_scene_group_behavior

    for command_key, expectation in GROUP_MUTATION_INTENT_EXPECTATIONS.items():
        result = evaluate_scene_group_behavior(command_key)

        assert result.accepted is True
        assert result.command_key == command_key
        assert result.behavior_family == "scene-group/group-mutation-intent"
        assert result.reason == "supported_group_mutation_intent"
        assert result.scene_scope == "four_pad_group"
        assert result.scene_name == ""
        assert result.scene_action == ""
        assert result.loads_anchors is False
        assert result.state_changed is False
        assert result.prompt_required is False
        assert result.executes_group_mutation is False
        assert result.executes_scene is False
        assert result.dispatches_command is False
        assert result.sends_real_midi is False
        assert result.opens_ports is False
        assert result.hardware_required is False
        assert result.active_behavior is False
        assert result.metadata["source"] == "GROUP_COMMANDS"
        assert result.metadata["source_group_command_label"] == expectation["label"]
        assert result.metadata["source_group_command_type"] == "mutation"
        assert result.metadata["source_group_command_scope"] == "four_pad_group"
        assert result.metadata["group_mutation_mode"] == expectation["mode"]
        assert result.metadata["mutation_intensity"] == expectation["intensity"]
        assert result.metadata["executes_group_mutation"] is False
        assert result.metadata["mutates_runtime_state"] is False
        assert result.display_lines[:4] == (
            f"{command_key}: {expectation['label']}",
            "Read-only group mutation intent.",
            f"Group mutation mode: {expectation['mode']}",
            "Group scope: four_pad_group",
        )
        assert "No group mutation would execute." in result.display_lines
        assert "No MIDI would be sent." in result.display_lines
        assert "No ports would be opened." in result.display_lines


def test_harder_wild_group_mutation_records_early_hardware_guardrail():
    from rytm_randomizer.behavior_scene_group import evaluate_scene_group_behavior

    result = evaluate_scene_group_behavior("4")

    assert result.accepted is True
    assert result.metadata["forbidden_early_hardware_scope"] is True
    assert "Early hardware scope: forbidden." in result.display_lines


def test_group_mutation_metadata_is_copied_and_immutable():
    from rytm_randomizer.behavior_scene_group import evaluate_scene_group_behavior
    from rytm_randomizer.commands import GROUP_COMMANDS

    result = evaluate_scene_group_behavior("X")
    original_label = GROUP_COMMANDS["X"]["label"]

    GROUP_COMMANDS["X"]["label"] = "changed"

    try:
        assert result.metadata["source_group_command_label"] == original_label

        try:
            result.metadata["source_group_command_label"] = "mutated"
        except TypeError:
            pass
        else:
            raise AssertionError("metadata should be immutable")
    finally:
        GROUP_COMMANDS["X"]["label"] = original_label


def test_repeated_group_mutation_evaluations_are_deterministic():
    from rytm_randomizer.behavior_scene_group import evaluate_scene_group_behavior

    for command_key in GROUP_MUTATION_INTENT_EXPECTATIONS:
        assert evaluate_scene_group_behavior(command_key) == (
            evaluate_scene_group_behavior(command_key)
        )


def test_lane_aware_group_mutation_keys_return_read_only_intent_results():
    from rytm_randomizer.behavior_scene_group import evaluate_scene_group_behavior

    for command_key, expectation in LANE_AWARE_GROUP_MUTATION_INTENT_EXPECTATIONS.items():
        result = evaluate_scene_group_behavior(command_key)

        assert result.accepted is True
        assert result.command_key == command_key
        assert result.behavior_family == (
            "scene-group/lane-aware-group-mutation-intent"
        )
        assert result.reason == "supported_lane_aware_group_mutation_intent"
        assert result.scene_scope == "four_pad_group"
        assert result.scene_name == ""
        assert result.scene_action == ""
        assert result.loads_anchors is False
        assert result.state_changed is False
        assert result.prompt_required is False
        assert result.executes_group_mutation is False
        assert result.executes_scene is False
        assert result.dispatches_command is False
        assert result.sends_real_midi is False
        assert result.opens_ports is False
        assert result.hardware_required is False
        assert result.active_behavior is False
        assert result.metadata["source"] == "GROUP_COMMANDS"
        assert result.metadata["source_group_command_label"] == expectation["label"]
        assert result.metadata["source_group_command_type"] == "mutation"
        assert result.metadata["source_group_command_scope"] == "four_pad_group"
        assert result.metadata["source_group_command_family"] == "lane_aware_page"
        assert result.metadata["lane_aware_page"] == expectation["page"]
        assert result.metadata["lane_aware_mutation_mode"] == expectation["mode"]
        assert result.metadata["executes_group_mutation"] is False
        assert result.metadata["mutates_runtime_state"] is False
        assert result.display_lines[:4] == (
            f"{command_key}: {expectation['label']}",
            "Read-only lane-aware group mutation intent.",
            f"Lane-aware page: {expectation['page']}",
            "Group scope: four_pad_group",
        )
        assert "No lane-aware group mutation would execute." in result.display_lines
        assert "No MIDI would be sent." in result.display_lines
        assert "No ports would be opened." in result.display_lines


def test_repeated_lane_aware_group_mutation_evaluations_are_deterministic():
    from rytm_randomizer.behavior_scene_group import evaluate_scene_group_behavior

    for command_key in LANE_AWARE_GROUP_MUTATION_INTENT_EXPECTATIONS:
        assert evaluate_scene_group_behavior(command_key) == (
            evaluate_scene_group_behavior(command_key)
        )


def test_group_anchor_keys_return_read_only_intent_results():
    from rytm_randomizer.behavior_scene_group import evaluate_scene_group_behavior

    for command_key, expectation in GROUP_ANCHOR_INTENT_EXPECTATIONS.items():
        result = evaluate_scene_group_behavior(command_key)

        assert result.accepted is True
        assert result.command_key == command_key
        assert result.behavior_family == "scene-group/group-anchor-intent"
        assert result.reason == expectation["reason"]
        assert result.scene_scope == "four_pad_group"
        assert result.scene_name == ""
        assert result.scene_action == ""
        assert result.loads_anchors is False
        assert result.state_changed is False
        assert result.prompt_required is False
        assert result.executes_scene is False
        assert result.executes_group_mutation is False
        assert result.dispatches_command is False
        assert result.sends_real_midi is False
        assert result.opens_ports is False
        assert result.hardware_required is False
        assert result.active_behavior is False
        assert result.metadata["source"] == "GROUP_COMMANDS"
        assert result.metadata["source_group_command_label"] == expectation["label"]
        assert result.metadata["source_group_command_type"] == expectation["command_type"]
        assert result.metadata["source_group_command_scope"] == "four_pad_group"
        assert result.metadata["anchor_action"] == expectation["anchor_action"]
        assert result.metadata["loads_anchors"] is False
        assert result.metadata["executes_group_anchor"] is False
        assert result.metadata["executes_group_mutation"] is False
        assert result.metadata["mutates_runtime_state"] is False
        assert result.display_lines == (
            f"{command_key}: {expectation['label']}",
            "Read-only group anchor intent.",
            f"Group anchor action: {expectation['anchor_action']}",
            "Group scope: four_pad_group",
            "No group anchor load or return would execute.",
            "No group mutation would execute.",
            "No scene would execute.",
            "No state would change.",
            "No command would dispatch.",
            "No MIDI would be sent.",
            "No ports would be opened.",
        )


def test_repeated_group_anchor_evaluations_are_deterministic():
    from rytm_randomizer.behavior_scene_group import evaluate_scene_group_behavior

    for command_key in GROUP_ANCHOR_INTENT_EXPECTATIONS:
        assert evaluate_scene_group_behavior(command_key) == (
            evaluate_scene_group_behavior(command_key)
        )


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
    test_group_mutation_keys_return_read_only_intent_results()
    test_harder_wild_group_mutation_records_early_hardware_guardrail()
    test_group_mutation_metadata_is_copied_and_immutable()
    test_repeated_group_mutation_evaluations_are_deterministic()
    test_lane_aware_group_mutation_keys_return_read_only_intent_results()
    test_repeated_lane_aware_group_mutation_evaluations_are_deterministic()
    test_group_anchor_keys_return_read_only_intent_results()
    test_repeated_group_anchor_evaluations_are_deterministic()
    test_packet_1_menu_utility_behavior_remains_unchanged()
    test_packet_2_anchor_profile_behavior_remains_unchanged()
    test_packet_3_mutation_depth_behavior_remains_unchanged()
    test_passive_cli_behavior_remains_unchanged()
    test_no_real_midi_library_is_imported()
    test_no_package_metadata_files_are_introduced()
    test_behavior_scene_group_exposes_no_active_behavior_names()
    test_no_out_of_scope_support_is_exposed()
