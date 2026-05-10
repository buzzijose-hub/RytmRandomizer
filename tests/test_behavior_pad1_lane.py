from pathlib import Path
import subprocess
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


SUPPORTED_PAD1_LANE_CASES = (
    (
        "BR",
        "rotate Pad 1 to the next profiled BD engine",
        "rotate_profiled_bd_engine",
        False,
        "",
        (
            "BR: rotate Pad 1 to the next profiled BD engine",
            "Read-only Pad 1 current-engine lane intent.",
            "Target pad: 1",
            "Lane: Pad 1 BD engine",
            "Lane action: rotate_profiled_bd_engine",
            "Current-engine dependency is recorded only.",
            "No prompt would run.",
            "No state would change.",
            "No command would dispatch.",
            "No command would execute.",
            "No lane state would mutate.",
            "No MIDI would be sent.",
            "No ports would be opened.",
            "No hardware would be required.",
        ),
    ),
    (
        "BM",
        "safely mutate the currently loaded Pad 1 BD engine",
        "safe_current_engine_mutation",
        True,
        "future_safe_mutation_depth",
        (
            "BM: safely mutate the currently loaded Pad 1 BD engine",
            "Read-only Pad 1 current-engine lane intent.",
            "Target pad: 1",
            "Lane: Pad 1 BD engine",
            "Lane action: safe_current_engine_mutation",
            "Current-engine dependency is recorded only.",
            "Future safe mutation depth is recorded only.",
            "No prompt would run.",
            "No state would change.",
            "No command would dispatch.",
            "No command would execute.",
            "No lane state would mutate.",
            "No MIDI would be sent.",
            "No ports would be opened.",
            "No hardware would be required.",
        ),
    ),
)

SUPPORTED_PAD1_BD_FM_CASES = (
    (
        "FT",
        "BD FM tone/FM discovery",
        "pad1-lane/bd-fm-discovery",
        "supported_pad1_bd_fm_discovery_intent",
        "bd_fm_tone_fm_discovery",
        "pad1_bd_fm_engine_profile",
        "future_bd_fm_discovery_depth",
        True,
        (
            "FT: BD FM tone/FM discovery",
            "Read-only Pad 1 BD FM discovery intent.",
            "Target pad: 1",
            "Lane: Pad 1 BD FM",
            "Lane action: bd_fm_tone_fm_discovery",
            "BD FM engine/profile dependency is recorded only.",
            "Future BD FM discovery depth is recorded only.",
            "No prompt would run.",
            "No state would change.",
            "No command would dispatch.",
            "No command would execute.",
            "No lane state would mutate.",
            "No MIDI would be sent.",
            "No ports would be opened.",
            "No hardware would be required.",
        ),
    ),
    (
        "FK",
        "BD FM kick/body discovery",
        "pad1-lane/bd-fm-discovery",
        "supported_pad1_bd_fm_discovery_intent",
        "bd_fm_kick_body_discovery",
        "pad1_bd_fm_engine_profile",
        "future_bd_fm_discovery_depth",
        True,
        (
            "FK: BD FM kick/body discovery",
            "Read-only Pad 1 BD FM discovery intent.",
            "Target pad: 1",
            "Lane: Pad 1 BD FM",
            "Lane action: bd_fm_kick_body_discovery",
            "BD FM engine/profile dependency is recorded only.",
            "Future BD FM discovery depth is recorded only.",
            "No prompt would run.",
            "No state would change.",
            "No command would dispatch.",
            "No command would execute.",
            "No lane state would mutate.",
            "No MIDI would be sent.",
            "No ports would be opened.",
            "No hardware would be required.",
        ),
    ),
    (
        "FG",
        "BD FM grit discovery",
        "pad1-lane/bd-fm-discovery",
        "supported_pad1_bd_fm_discovery_intent",
        "bd_fm_grit_discovery",
        "pad1_bd_fm_engine_profile",
        "future_bd_fm_discovery_depth",
        True,
        (
            "FG: BD FM grit discovery",
            "Read-only Pad 1 BD FM discovery intent.",
            "Target pad: 1",
            "Lane: Pad 1 BD FM",
            "Lane action: bd_fm_grit_discovery",
            "BD FM engine/profile dependency is recorded only.",
            "Future BD FM discovery depth is recorded only.",
            "No prompt would run.",
            "No state would change.",
            "No command would dispatch.",
            "No command would execute.",
            "No lane state would mutate.",
            "No MIDI would be sent.",
            "No ports would be opened.",
            "No hardware would be required.",
        ),
    ),
    (
        "FZ",
        "return Pad 1 BD FM to anchor",
        "pad1-lane/bd-fm-anchor-return",
        "supported_pad1_bd_fm_anchor_return_intent",
        "return_bd_fm_to_anchor",
        "pad1_bd_fm_anchor_state",
        "",
        False,
        (
            "FZ: return Pad 1 BD FM to anchor",
            "Read-only Pad 1 BD FM anchor-return intent.",
            "Target pad: 1",
            "Lane: Pad 1 BD FM",
            "Lane action: return_bd_fm_to_anchor",
            "BD FM anchor dependency is recorded only.",
            "No prompt would run.",
            "No state would change.",
            "No command would dispatch.",
            "No command would execute.",
            "No lane state would mutate.",
            "No MIDI would be sent.",
            "No ports would be opened.",
            "No hardware would be required.",
        ),
    ),
)

SUPPORTED_PAD1_BD_PLASTIC_CASES = (
    (
        "BP",
        "load Pad 1 BD Plastic profiled anchor",
        "pad1-lane/bd-plastic-anchor-load",
        "supported_pad1_bd_plastic_anchor_load_intent",
        "load_bd_plastic_profiled_anchor",
        "pad1_bd_plastic_profiled_anchor",
        "",
        False,
        (
            "BP: load Pad 1 BD Plastic profiled anchor",
            "Read-only Pad 1 BD Plastic lane intent.",
            "Target pad: 1",
            "Lane: Pad 1 BD Plastic",
            "Lane action: load_bd_plastic_profiled_anchor",
            "BD Plastic anchor/profile dependency is recorded only.",
            "No prompt would run.",
            "No state would change.",
            "No command would dispatch.",
            "No command would execute.",
            "No lane state would mutate.",
            "No MIDI would be sent.",
            "No ports would be opened.",
            "No hardware would be required.",
        ),
    ),
    (
        "PT",
        "BD Plastic tone/modulation discovery",
        "pad1-lane/bd-plastic-discovery",
        "supported_pad1_bd_plastic_discovery_intent",
        "bd_plastic_tone_modulation_discovery",
        "pad1_bd_plastic_engine_profile",
        "future_bd_plastic_discovery_depth",
        True,
        (
            "PT: BD Plastic tone/modulation discovery",
            "Read-only Pad 1 BD Plastic lane intent.",
            "Target pad: 1",
            "Lane: Pad 1 BD Plastic",
            "Lane action: bd_plastic_tone_modulation_discovery",
            "BD Plastic engine/profile dependency is recorded only.",
            "Future BD Plastic discovery depth is recorded only.",
            "No prompt would run.",
            "No state would change.",
            "No command would dispatch.",
            "No command would execute.",
            "No lane state would mutate.",
            "No MIDI would be sent.",
            "No ports would be opened.",
            "No hardware would be required.",
        ),
    ),
    (
        "PK",
        "BD Plastic kick/body discovery",
        "pad1-lane/bd-plastic-discovery",
        "supported_pad1_bd_plastic_discovery_intent",
        "bd_plastic_kick_body_discovery",
        "pad1_bd_plastic_engine_profile",
        "future_bd_plastic_discovery_depth",
        True,
        (
            "PK: BD Plastic kick/body discovery",
            "Read-only Pad 1 BD Plastic lane intent.",
            "Target pad: 1",
            "Lane: Pad 1 BD Plastic",
            "Lane action: bd_plastic_kick_body_discovery",
            "BD Plastic engine/profile dependency is recorded only.",
            "Future BD Plastic discovery depth is recorded only.",
            "No prompt would run.",
            "No state would change.",
            "No command would dispatch.",
            "No command would execute.",
            "No lane state would mutate.",
            "No MIDI would be sent.",
            "No ports would be opened.",
            "No hardware would be required.",
        ),
    ),
    (
        "PX",
        "BD Plastic rubber/experimental discovery",
        "pad1-lane/bd-plastic-discovery",
        "supported_pad1_bd_plastic_discovery_intent",
        "bd_plastic_rubber_experimental_discovery",
        "pad1_bd_plastic_engine_profile",
        "future_bd_plastic_discovery_depth",
        True,
        (
            "PX: BD Plastic rubber/experimental discovery",
            "Read-only Pad 1 BD Plastic lane intent.",
            "Target pad: 1",
            "Lane: Pad 1 BD Plastic",
            "Lane action: bd_plastic_rubber_experimental_discovery",
            "BD Plastic engine/profile dependency is recorded only.",
            "Future BD Plastic discovery depth is recorded only.",
            "No prompt would run.",
            "No state would change.",
            "No command would dispatch.",
            "No command would execute.",
            "No lane state would mutate.",
            "No MIDI would be sent.",
            "No ports would be opened.",
            "No hardware would be required.",
        ),
    ),
    (
        "PBH",
        "return Pad 1 BD Plastic to anchor",
        "pad1-lane/bd-plastic-anchor-return",
        "supported_pad1_bd_plastic_anchor_return_intent",
        "return_bd_plastic_to_anchor",
        "pad1_bd_plastic_anchor_state",
        "",
        False,
        (
            "PBH: return Pad 1 BD Plastic to anchor",
            "Read-only Pad 1 BD Plastic lane intent.",
            "Target pad: 1",
            "Lane: Pad 1 BD Plastic",
            "Lane action: return_bd_plastic_to_anchor",
            "BD Plastic anchor dependency is recorded only.",
            "No prompt would run.",
            "No state would change.",
            "No command would dispatch.",
            "No command would execute.",
            "No lane state would mutate.",
            "No MIDI would be sent.",
            "No ports would be opened.",
            "No hardware would be required.",
        ),
    ),
)

DEFERRED_PAD1_LANE_KEYS = (
    "BI",
    "ST",
    "SK",
    "SC",
    "SBH",
)

ALREADY_COVERED_PAD1_CONTEXT_KEYS = ("FM", "PD", "SM", "BH", "BC", "BS", "BF")


def run_cli(*args):
    return subprocess.run(
        [sys.executable, "-m", "rytm_randomizer.cli", *args],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def test_importing_behavior_pad1_lane_prints_nothing():
    result = subprocess.run(
        [sys.executable, "-c", "import rytm_randomizer.behavior_pad1_lane"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert result.stdout == ""
    assert result.stderr == ""


def test_br_and_bm_return_read_only_pad1_lane_intents():
    from rytm_randomizer.behavior_pad1_lane import evaluate_pad1_lane_behavior

    for (
        command_key,
        expected_label,
        expected_lane_action,
        expected_depth_required,
        expected_depth_dependency,
        expected_display,
    ) in SUPPORTED_PAD1_LANE_CASES:
        result = evaluate_pad1_lane_behavior(command_key)

        assert result.accepted is True
        assert result.command_key == command_key
        assert result.label == expected_label
        assert result.behavior_family == "pad1-lane/current-bd-engine"
        assert result.reason == "supported_pad1_current_engine_lane_intent"
        assert result.target_pad == 1
        assert result.lane == "Pad 1 BD engine"
        assert result.lane_action == expected_lane_action
        assert result.engine_dependency == "current_pad1_bd_engine_state"
        assert result.depth_dependency == expected_depth_dependency
        assert result.state_changed is False
        assert result.prompt_required is False
        assert result.dispatches_command is False
        assert result.executes_command is False
        assert result.mutates_lane_state is False
        assert result.sends_real_midi is False
        assert result.opens_ports is False
        assert result.hardware_required is False
        assert result.active_behavior is False
        assert result.display_lines == expected_display
        assert result.metadata["requires_depth_selection"] is expected_depth_required


def test_br_and_bm_metadata_contains_expected_passive_sources():
    from rytm_randomizer.behavior_pad1_lane import evaluate_pad1_lane_behavior

    expected = {
        "BR": {
            "source": "PAD1_COMMANDS",
            "source_command_type": "rotation",
            "source_command_scope": "pad_1",
            "source_v134_reference_command": True,
            "source_scaffold_only": True,
            "target_pad": 1,
            "lane": "pad_1_bd_engine",
            "lane_action": "rotate_profiled_bd_engine",
            "requires_current_engine_state": True,
            "requires_depth_selection": False,
        },
        "BM": {
            "source": "PAD1_COMMANDS",
            "source_command_type": "mutation",
            "source_command_scope": "pad_1",
            "source_v134_reference_command": True,
            "source_scaffold_only": True,
            "target_pad": 1,
            "lane": "pad_1_bd_engine",
            "lane_action": "safe_current_engine_mutation",
            "requires_current_engine_state": True,
            "requires_depth_selection": True,
        },
    }

    for command_key, expected_metadata in expected.items():
        result = evaluate_pad1_lane_behavior(command_key)

        for key, value in expected_metadata.items():
            assert result.metadata[key] == value
        assert result.metadata["mock_only"] is True
        assert result.metadata["sends_real_midi"] is False
        assert result.metadata["opens_ports"] is False
        assert result.metadata["hardware_required"] is False
        assert result.metadata["active_behavior"] is False
        assert result.metadata["mutates_runtime_state"] is False
        assert result.metadata["dispatches_command"] is False
        assert result.metadata["executes_command"] is False


def test_ft_fk_fg_and_fz_return_read_only_bd_fm_lane_intents():
    from rytm_randomizer.behavior_pad1_lane import evaluate_pad1_lane_behavior

    for (
        command_key,
        expected_label,
        expected_family,
        expected_reason,
        expected_lane_action,
        expected_engine_dependency,
        expected_depth_dependency,
        expected_depth_required,
        expected_display,
    ) in SUPPORTED_PAD1_BD_FM_CASES:
        result = evaluate_pad1_lane_behavior(command_key)

        assert result.accepted is True
        assert result.command_key == command_key
        assert result.label == expected_label
        assert result.behavior_family == expected_family
        assert result.reason == expected_reason
        assert result.target_pad == 1
        assert result.lane == "Pad 1 BD FM"
        assert result.lane_action == expected_lane_action
        assert result.engine_dependency == expected_engine_dependency
        assert result.depth_dependency == expected_depth_dependency
        assert result.state_changed is False
        assert result.prompt_required is False
        assert result.dispatches_command is False
        assert result.executes_command is False
        assert result.mutates_lane_state is False
        assert result.sends_real_midi is False
        assert result.opens_ports is False
        assert result.hardware_required is False
        assert result.active_behavior is False
        assert result.display_lines == expected_display
        assert result.metadata["requires_depth_selection"] is expected_depth_required


def test_ft_fk_fg_and_fz_metadata_contains_expected_passive_sources():
    from rytm_randomizer.behavior_pad1_lane import evaluate_pad1_lane_behavior

    expected = {
        "FT": {
            "source_command_type": "mutation",
            "lane_action": "bd_fm_tone_fm_discovery",
            "requires_bd_fm_engine_profile": True,
            "requires_bd_fm_anchor": False,
            "requires_depth_selection": True,
        },
        "FK": {
            "source_command_type": "mutation",
            "lane_action": "bd_fm_kick_body_discovery",
            "requires_bd_fm_engine_profile": True,
            "requires_bd_fm_anchor": False,
            "requires_depth_selection": True,
        },
        "FG": {
            "source_command_type": "mutation",
            "lane_action": "bd_fm_grit_discovery",
            "requires_bd_fm_engine_profile": True,
            "requires_bd_fm_anchor": False,
            "requires_depth_selection": True,
        },
        "FZ": {
            "source_command_type": "anchor_return",
            "lane_action": "return_bd_fm_to_anchor",
            "requires_bd_fm_engine_profile": False,
            "requires_bd_fm_anchor": True,
            "requires_depth_selection": False,
        },
    }

    for command_key, expected_metadata in expected.items():
        result = evaluate_pad1_lane_behavior(command_key)

        assert result.metadata["source"] == "PAD1_COMMANDS"
        assert result.metadata["source_command_scope"] == "pad_1"
        assert result.metadata["source_v134_reference_command"] is True
        assert result.metadata["source_scaffold_only"] is True
        assert result.metadata["target_pad"] == 1
        assert result.metadata["lane"] == "pad_1_bd_fm"
        for key, value in expected_metadata.items():
            assert result.metadata[key] == value
        assert result.metadata["mock_only"] is True
        assert result.metadata["sends_real_midi"] is False
        assert result.metadata["opens_ports"] is False
        assert result.metadata["hardware_required"] is False
        assert result.metadata["active_behavior"] is False
        assert result.metadata["mutates_runtime_state"] is False
        assert result.metadata["dispatches_command"] is False
        assert result.metadata["executes_command"] is False


def test_bp_pt_pk_px_and_pbh_return_read_only_bd_plastic_lane_intents():
    from rytm_randomizer.behavior_pad1_lane import evaluate_pad1_lane_behavior

    for (
        command_key,
        expected_label,
        expected_family,
        expected_reason,
        expected_lane_action,
        expected_engine_dependency,
        expected_depth_dependency,
        expected_depth_required,
        expected_display,
    ) in SUPPORTED_PAD1_BD_PLASTIC_CASES:
        result = evaluate_pad1_lane_behavior(command_key)

        assert result.accepted is True
        assert result.command_key == command_key
        assert result.label == expected_label
        assert result.behavior_family == expected_family
        assert result.reason == expected_reason
        assert result.target_pad == 1
        assert result.lane == "Pad 1 BD Plastic"
        assert result.lane_action == expected_lane_action
        assert result.engine_dependency == expected_engine_dependency
        assert result.depth_dependency == expected_depth_dependency
        assert result.state_changed is False
        assert result.prompt_required is False
        assert result.dispatches_command is False
        assert result.executes_command is False
        assert result.mutates_lane_state is False
        assert result.sends_real_midi is False
        assert result.opens_ports is False
        assert result.hardware_required is False
        assert result.active_behavior is False
        assert result.display_lines == expected_display
        assert result.metadata["requires_depth_selection"] is expected_depth_required


def test_bp_pt_pk_px_and_pbh_metadata_contains_expected_passive_sources():
    from rytm_randomizer.behavior_pad1_lane import evaluate_pad1_lane_behavior

    expected = {
        "BP": {
            "source_command_type": "load",
            "lane_action": "load_bd_plastic_profiled_anchor",
            "requires_bd_plastic_engine_profile": False,
            "requires_bd_plastic_anchor": True,
            "requires_depth_selection": False,
        },
        "PT": {
            "source_command_type": "mutation",
            "lane_action": "bd_plastic_tone_modulation_discovery",
            "requires_bd_plastic_engine_profile": True,
            "requires_bd_plastic_anchor": False,
            "requires_depth_selection": True,
        },
        "PK": {
            "source_command_type": "mutation",
            "lane_action": "bd_plastic_kick_body_discovery",
            "requires_bd_plastic_engine_profile": True,
            "requires_bd_plastic_anchor": False,
            "requires_depth_selection": True,
        },
        "PX": {
            "source_command_type": "mutation",
            "lane_action": "bd_plastic_rubber_experimental_discovery",
            "requires_bd_plastic_engine_profile": True,
            "requires_bd_plastic_anchor": False,
            "requires_depth_selection": True,
        },
        "PBH": {
            "source_command_type": "anchor_return",
            "lane_action": "return_bd_plastic_to_anchor",
            "requires_bd_plastic_engine_profile": False,
            "requires_bd_plastic_anchor": True,
            "requires_depth_selection": False,
        },
    }

    for command_key, expected_metadata in expected.items():
        result = evaluate_pad1_lane_behavior(command_key)

        assert result.metadata["source"] == "PAD1_COMMANDS"
        assert result.metadata["source_command_scope"] == "pad_1"
        assert result.metadata["source_v134_reference_command"] is True
        assert result.metadata["source_scaffold_only"] is True
        assert result.metadata["target_pad"] == 1
        assert result.metadata["lane"] == "pad_1_bd_plastic"
        for key, value in expected_metadata.items():
            assert result.metadata[key] == value
        assert result.metadata["mock_only"] is True
        assert result.metadata["sends_real_midi"] is False
        assert result.metadata["opens_ports"] is False
        assert result.metadata["hardware_required"] is False
        assert result.metadata["active_behavior"] is False
        assert result.metadata["mutates_runtime_state"] is False
        assert result.metadata["dispatches_command"] is False
        assert result.metadata["executes_command"] is False


def test_pad1_lane_metadata_is_copied_and_immutable():
    from rytm_randomizer.behavior_pad1_lane import Pad1LaneBehaviorResult

    metadata = {"source": "test"}
    result = Pad1LaneBehaviorResult(command_key="BR", metadata=metadata)

    metadata["source"] = "changed"

    assert result.metadata["source"] == "test"

    try:
        result.metadata["source"] = "mutated"
    except TypeError:
        pass
    else:
        raise AssertionError("metadata should be immutable")


def test_repeated_pad1_lane_evaluations_are_deterministic():
    from rytm_randomizer.behavior_pad1_lane import evaluate_pad1_lane_behavior

    assert evaluate_pad1_lane_behavior("BR") == evaluate_pad1_lane_behavior("BR")
    assert evaluate_pad1_lane_behavior("BM") == evaluate_pad1_lane_behavior("BM")
    assert evaluate_pad1_lane_behavior("FT") == evaluate_pad1_lane_behavior("FT")
    assert evaluate_pad1_lane_behavior("FK") == evaluate_pad1_lane_behavior("FK")
    assert evaluate_pad1_lane_behavior("FG") == evaluate_pad1_lane_behavior("FG")
    assert evaluate_pad1_lane_behavior("FZ") == evaluate_pad1_lane_behavior("FZ")
    assert evaluate_pad1_lane_behavior("BP") == evaluate_pad1_lane_behavior("BP")
    assert evaluate_pad1_lane_behavior("PT") == evaluate_pad1_lane_behavior("PT")
    assert evaluate_pad1_lane_behavior("PK") == evaluate_pad1_lane_behavior("PK")
    assert evaluate_pad1_lane_behavior("PX") == evaluate_pad1_lane_behavior("PX")
    assert evaluate_pad1_lane_behavior("PBH") == evaluate_pad1_lane_behavior("PBH")


def test_deferred_packet_5_pad1_lane_keys_fail_safely():
    from rytm_randomizer.behavior_pad1_lane import evaluate_pad1_lane_behavior

    for command_key in DEFERRED_PAD1_LANE_KEYS:
        result = evaluate_pad1_lane_behavior(command_key)

        assert result.accepted is False
        assert result.reason == "deferred_pad1_lane_command"
        assert result.display_lines == ()
        assert result.state_changed is False
        assert result.prompt_required is False
        assert result.dispatches_command is False
        assert result.executes_command is False
        assert result.mutates_lane_state is False
        assert result.sends_real_midi is False
        assert result.opens_ports is False
        assert result.hardware_required is False
        assert result.active_behavior is False
        assert result.metadata["source"] == "PAD1_COMMANDS"


def test_already_covered_pad1_context_keys_are_not_reimplemented():
    from rytm_randomizer.behavior_pad1_lane import evaluate_pad1_lane_behavior

    for command_key in ALREADY_COVERED_PAD1_CONTEXT_KEYS:
        result = evaluate_pad1_lane_behavior(command_key)

        assert result.accepted is False
        assert result.reason == "unsupported_pad1_lane_command"
        assert result.sends_real_midi is False
        assert result.opens_ports is False
        assert result.hardware_required is False
        assert result.active_behavior is False


def test_unknown_keys_fail_safely():
    from rytm_randomizer.behavior_pad1_lane import evaluate_pad1_lane_behavior

    result = evaluate_pad1_lane_behavior("DOES_NOT_EXIST")

    assert result.accepted is False
    assert result.reason == "unknown_command"
    assert result.display_lines == ()
    assert result.target_pad is None
    assert result.lane == ""
    assert result.lane_action == ""
    assert result.engine_dependency == ""
    assert result.depth_dependency == ""
    assert result.state_changed is False
    assert result.prompt_required is False
    assert result.dispatches_command is False
    assert result.executes_command is False
    assert result.mutates_lane_state is False
    assert result.sends_real_midi is False
    assert result.opens_ports is False
    assert result.hardware_required is False
    assert result.active_behavior is False


def test_packet_1_menu_utility_behavior_remains_unchanged():
    from rytm_randomizer.behavior_menu_utility import evaluate_menu_utility_behavior

    result = evaluate_menu_utility_behavior("BD")

    assert result.accepted is True
    assert result.label == "show BD engine tools"
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


def test_passive_cli_behavior_remains_unchanged():
    result = run_cli("inspect-command", "BR")

    assert result.returncode == 0
    assert "Command: BR" in result.stdout
    assert "Label: rotate Pad 1 to the next profiled BD engine" in result.stdout
    assert result.stderr == ""


def test_no_real_midi_library_is_imported():
    import rytm_randomizer.behavior_pad1_lane  # noqa: F401

    assert "mido" not in sys.modules
    assert "rtmidi" not in sys.modules


def test_no_package_metadata_files_are_introduced():
    for filename in ("pyproject.toml", "requirements.txt", "setup.py", "setup.cfg"):
        assert not (PROJECT_ROOT / filename).exists()


def test_behavior_pad1_lane_exposes_no_active_behavior_names():
    import rytm_randomizer.behavior_pad1_lane as behavior_pad1_lane

    exposed_names = set(dir(behavior_pad1_lane))

    assert "execute_command" not in exposed_names
    assert "send_command" not in exposed_names
    assert "hardware_test" not in exposed_names


def test_no_out_of_scope_support_is_exposed():
    import rytm_randomizer.behavior_pad1_lane as behavior_pad1_lane

    module_text = "\n".join(
        [
            behavior_pad1_lane.__doc__ or "",
            behavior_pad1_lane.evaluate_pad1_lane_behavior.__doc__ or "",
        ]
    )

    assert "Analog Four support" not in module_text
    assert "Pads 5-12 support" not in module_text


if __name__ == "__main__":
    test_importing_behavior_pad1_lane_prints_nothing()
    test_br_and_bm_return_read_only_pad1_lane_intents()
    test_br_and_bm_metadata_contains_expected_passive_sources()
    test_ft_fk_fg_and_fz_return_read_only_bd_fm_lane_intents()
    test_ft_fk_fg_and_fz_metadata_contains_expected_passive_sources()
    test_bp_pt_pk_px_and_pbh_return_read_only_bd_plastic_lane_intents()
    test_bp_pt_pk_px_and_pbh_metadata_contains_expected_passive_sources()
    test_pad1_lane_metadata_is_copied_and_immutable()
    test_repeated_pad1_lane_evaluations_are_deterministic()
    test_deferred_packet_5_pad1_lane_keys_fail_safely()
    test_already_covered_pad1_context_keys_are_not_reimplemented()
    test_unknown_keys_fail_safely()
    test_packet_1_menu_utility_behavior_remains_unchanged()
    test_packet_2_anchor_profile_behavior_remains_unchanged()
    test_passive_cli_behavior_remains_unchanged()
    test_no_real_midi_library_is_imported()
    test_no_package_metadata_files_are_introduced()
    test_behavior_pad1_lane_exposes_no_active_behavior_names()
    test_no_out_of_scope_support_is_exposed()
