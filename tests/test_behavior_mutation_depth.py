import subprocess
import sys
from pathlib import Path

import pytest

# WS-M4: mark this module as fast-suite; pytest -m fast skips the 505
# warm-worker V1.34 parity fixtures and runs in <60s.
pytestmark = pytest.mark.fast

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


GUARDED_DEPTH_KEYS = ("1", "2", "3")
LEGACY_SINGLE_PROFILE_MUTATION_CASES = (
    (
        "M1",
        "Legacy single-profile full micro mutation",
        "micro",
    ),
    (
        "M2",
        "Legacy single-profile full groove mutation",
        "groove",
    ),
    (
        "M3",
        "Legacy single-profile full strong mutation",
        "strong",
    ),
)
CURRENT_PROFILE_PAGE_MUTATION_CASES = (
    (
        "S",
        "SRC-only mutation, choose depth",
        "src",
    ),
    (
        "F",
        "Filter-only mutation, choose depth",
        "filter",
    ),
    (
        "A",
        "Amp-only mutation, choose depth",
        "amp",
    ),
    (
        "G",
        "Grit-only mutation, choose depth",
        "grit",
    ),
    (
        "K",
        "Kick body mutation, choose depth",
        "kick_body",
    ),
)
SELECTED_ISOLATED_PAD_MUTATION_CASES = (
    (
        "PM",
        "mutate selected isolated pad only using its group default zone/depth",
        "full",
        False,
        True,
    ),
    (
        "PS",
        "mutate selected isolated pad SRC only, choose depth",
        "src",
        True,
        False,
    ),
    (
        "PF",
        "mutate selected isolated pad Filter only, choose depth",
        "filter",
        True,
        False,
    ),
    (
        "PA",
        "mutate selected isolated pad Amp only, choose depth",
        "amp",
        True,
        False,
    ),
    (
        "PL",
        "mutate selected isolated pad LFO only, choose depth",
        "lfo",
        True,
        False,
    ),
    (
        "PO",
        "mutate selected isolated pad Morph only, choose depth",
        "morph",
        True,
        False,
    ),
    (
        "PB",
        "mutate selected isolated pad Body only, choose depth",
        "body",
        True,
        False,
    ),
    (
        "PG",
        "mutate selected isolated pad Grit only, choose depth",
        "grit",
        True,
        False,
    ),
)
DEFERRED_PACKET_3_KEYS = ()
PACKET_3D_KEYS = (
    "PM",
    "PS",
    "PF",
    "PA",
    "PL",
    "PO",
    "PB",
    "PG",
)


def run_cli(*args):
    return subprocess.run(
        [sys.executable, "-m", "rytm_randomizer.cli", *args],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def test_importing_behavior_mutation_depth_prints_nothing():
    result = subprocess.run(
        [sys.executable, "-c", "import rytm_randomizer.behavior.mutation_depth"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert result.stdout == ""
    assert result.stderr == ""


def test_guarded_numeric_inputs_return_read_only_results():
    from rytm_randomizer.behavior.mutation_depth import evaluate_mutation_depth_behavior

    for command_key in GUARDED_DEPTH_KEYS:
        result = evaluate_mutation_depth_behavior(command_key)

        assert result.accepted is True
        assert result.command_key == command_key
        assert result.behavior_family == "mutation-depth/guarded-input"
        assert result.depth_value == int(command_key)
        assert result.guarded_input is True
        assert result.requires_depth_prompt_context is True
        assert result.prompt_available is False
        assert result.state_changed is False
        assert result.prompt_required is False
        assert result.dispatches_command is False
        assert result.executes_command is False
        assert result.sends_real_midi is False
        assert result.opens_ports is False
        assert result.hardware_required is False
        assert result.active_behavior is False
        assert result.display_lines


def test_guarded_numeric_input_1_has_expected_display_and_metadata():
    from rytm_randomizer.behavior.mutation_depth import evaluate_mutation_depth_behavior

    result = evaluate_mutation_depth_behavior("1")

    assert result.accepted is True
    assert result.label == "guarded depth input 1, requires lane/mode prefix"
    assert result.reason == "supported_guarded_depth_input"
    assert result.display_lines == (
        "1: guarded depth input 1, requires lane/mode prefix",
        "Read-only guarded numeric input intent.",
        "Depth value: 1",
        "Bare main-prompt use remains guarded.",
        "Valid only inside a future depth prompt context.",
        "No active depth prompt exists now.",
        "No prompt would run.",
        "No state would change.",
        "No command would dispatch.",
        "No command would execute.",
        "No MIDI would be sent.",
        "No ports would be opened.",
    )
    assert result.metadata["source"] == "MAIN_PROMPT_DEPTH_GUARDRAIL"
    assert result.metadata["source_command_type"] == "guarded_depth"
    assert result.metadata["depth_prompt_context"] == (
        "Use a command that asks for depth before entering 1, 2, or 3."
    )
    assert result.metadata["mock_only"] is True
    assert result.metadata["sends_real_midi"] is False
    assert result.metadata["opens_ports"] is False
    assert result.metadata["hardware_required"] is False
    assert result.metadata["active_behavior"] is False
    assert result.metadata["mutates_runtime_state"] is False


def test_repeated_mutation_depth_evaluations_are_deterministic():
    from rytm_randomizer.behavior.mutation_depth import evaluate_mutation_depth_behavior

    for command_key in GUARDED_DEPTH_KEYS:
        assert evaluate_mutation_depth_behavior(command_key) == (
            evaluate_mutation_depth_behavior(command_key)
        )


def test_legacy_single_profile_mutations_return_read_only_results():
    from rytm_randomizer.behavior.mutation_depth import evaluate_mutation_depth_behavior

    for command_key, expected_label, expected_depth in LEGACY_SINGLE_PROFILE_MUTATION_CASES:
        result = evaluate_mutation_depth_behavior(command_key)

        assert result.accepted is True
        assert result.command_key == command_key
        assert result.label == expected_label
        assert result.behavior_family == "mutation-depth/legacy-single-profile"
        assert result.reason == "supported_legacy_single_profile_mutation_intent"
        assert result.mutation_area == "full"
        assert result.mutation_depth == expected_depth
        assert result.scope == "selected_profile"
        assert result.uses_selected_profile is True
        assert result.depth_value is None
        assert result.guarded_input is False
        assert result.requires_depth_prompt_context is False
        assert result.prompt_available is False
        assert result.state_changed is False
        assert result.prompt_required is False
        assert result.dispatches_command is False
        assert result.executes_command is False
        assert result.sends_real_midi is False
        assert result.opens_ports is False
        assert result.hardware_required is False
        assert result.active_behavior is False
        assert result.display_lines


def test_legacy_single_profile_mutation_m1_has_expected_display_and_metadata():
    from rytm_randomizer.behavior.mutation_depth import evaluate_mutation_depth_behavior

    result = evaluate_mutation_depth_behavior("M1")

    assert result.accepted is True
    assert result.display_lines == (
        "M1: Legacy single-profile full micro mutation",
        "Read-only legacy single-profile mutation intent.",
        "Mutation area: full",
        "Mutation depth: micro",
        "Selected-profile dependency is recorded only.",
        "No selected-profile state exists in this helper.",
        "No prompt would run.",
        "No state would change.",
        "No command would dispatch.",
        "No command would execute.",
        "No MIDI would be sent.",
        "No ports would be opened.",
    )
    assert result.metadata["source"] == "LEGACY_SINGLE_PROFILE_MUTATION_COMMANDS"
    assert result.metadata["source_command_type"] == "mutation"
    assert result.metadata["command_family"] == "legacy_single_profile_mutation"
    assert result.metadata["mutation_area"] == "full"
    assert result.metadata["mutation_depth"] == "micro"
    assert result.metadata["scope"] == "selected_profile"
    assert result.metadata["uses_selected_profile"] is True
    assert result.metadata["mock_only"] is True
    assert result.metadata["sends_real_midi"] is False
    assert result.metadata["opens_ports"] is False
    assert result.metadata["hardware_required"] is False
    assert result.metadata["active_behavior"] is False
    assert result.metadata["mutates_runtime_state"] is False


def test_repeated_legacy_single_profile_mutation_evaluations_are_deterministic():
    from rytm_randomizer.behavior.mutation_depth import evaluate_mutation_depth_behavior

    for command_key, _expected_label, _expected_depth in LEGACY_SINGLE_PROFILE_MUTATION_CASES:
        assert evaluate_mutation_depth_behavior(command_key) == (
            evaluate_mutation_depth_behavior(command_key)
        )


def test_current_profile_page_mutations_return_read_only_results():
    from rytm_randomizer.behavior.mutation_depth import evaluate_mutation_depth_behavior

    for command_key, expected_label, expected_area in CURRENT_PROFILE_PAGE_MUTATION_CASES:
        result = evaluate_mutation_depth_behavior(command_key)

        assert result.accepted is True
        assert result.command_key == command_key
        assert result.label == expected_label
        assert result.behavior_family == "mutation-depth/current-profile-page"
        assert result.reason == "supported_current_profile_page_mutation_intent"
        assert result.mutation_area == expected_area
        assert result.mutation_depth == ""
        assert result.scope == "current_profile"
        assert result.uses_selected_profile is False
        assert result.depth_value is None
        assert result.guarded_input is False
        assert result.requires_depth_prompt_context is True
        assert result.prompt_available is False
        assert result.state_changed is False
        assert result.prompt_required is True
        assert result.dispatches_command is False
        assert result.executes_command is False
        assert result.sends_real_midi is False
        assert result.opens_ports is False
        assert result.hardware_required is False
        assert result.active_behavior is False
        assert result.display_lines


def test_current_profile_page_mutation_s_has_expected_display_and_metadata():
    from rytm_randomizer.behavior.mutation_depth import evaluate_mutation_depth_behavior

    result = evaluate_mutation_depth_behavior("S")

    assert result.accepted is True
    assert result.display_lines == (
        "S: SRC-only mutation, choose depth",
        "Read-only current-profile page mutation intent.",
        "Mutation area: src",
        "Current-profile dependency is recorded only.",
        "Future depth selection is required.",
        "No active depth prompt exists now.",
        "No current-profile state exists in this helper.",
        "No prompt would run.",
        "No state would change.",
        "No command would dispatch.",
        "No command would execute.",
        "No MIDI would be sent.",
        "No ports would be opened.",
    )
    assert result.metadata["source"] == "CURRENT_PROFILE_PAGE_MUTATION_COMMANDS"
    assert result.metadata["source_command_type"] == "mutation"
    assert result.metadata["command_family"] == "generic_current_profile_page_mutation"
    assert result.metadata["mutation_area"] == "src"
    assert result.metadata["requires_depth_selection"] is True
    assert result.metadata["scope"] == "current_profile"
    assert result.metadata["mock_only"] is True
    assert result.metadata["sends_real_midi"] is False
    assert result.metadata["opens_ports"] is False
    assert result.metadata["hardware_required"] is False
    assert result.metadata["active_behavior"] is False
    assert result.metadata["mutates_runtime_state"] is False


def test_repeated_current_profile_page_mutation_evaluations_are_deterministic():
    from rytm_randomizer.behavior.mutation_depth import evaluate_mutation_depth_behavior

    for command_key, _expected_label, _expected_area in CURRENT_PROFILE_PAGE_MUTATION_CASES:
        assert evaluate_mutation_depth_behavior(command_key) == (
            evaluate_mutation_depth_behavior(command_key)
        )


def test_selected_isolated_pad_mutations_return_read_only_results():
    from rytm_randomizer.behavior.mutation_depth import evaluate_mutation_depth_behavior

    for (
        command_key,
        expected_label,
        expected_area,
        requires_depth,
        uses_group_default,
    ) in SELECTED_ISOLATED_PAD_MUTATION_CASES:
        result = evaluate_mutation_depth_behavior(command_key)

        assert result.accepted is True
        assert result.command_key == command_key
        assert result.label == expected_label
        assert result.behavior_family == "mutation-depth/selected-isolated-pad"
        assert result.reason == "supported_selected_isolated_pad_mutation_intent"
        assert result.mutation_area == expected_area
        assert result.mutation_depth == ""
        assert result.scope == "selected_isolated_pad"
        assert result.uses_selected_profile is False
        assert result.depth_value is None
        assert result.guarded_input is False
        assert result.requires_depth_prompt_context is requires_depth
        assert result.prompt_available is False
        assert result.state_changed is False
        assert result.prompt_required is requires_depth
        assert result.dispatches_command is False
        assert result.executes_command is False
        assert result.sends_real_midi is False
        assert result.opens_ports is False
        assert result.hardware_required is False
        assert result.active_behavior is False
        assert result.metadata["uses_group_default_zone_depth"] is uses_group_default
        assert result.display_lines


def test_selected_isolated_pad_mutation_pm_has_expected_display_and_metadata():
    from rytm_randomizer.behavior.mutation_depth import evaluate_mutation_depth_behavior

    result = evaluate_mutation_depth_behavior("PM")

    assert result.accepted is True
    assert result.display_lines == (
        "PM: mutate selected isolated pad only using its group default zone/depth",
        "Read-only selected isolated pad mutation intent.",
        "Mutation area: full",
        "Selected-isolated-pad dependency is recorded only.",
        "Uses group default zone/depth.",
        "No selected-isolated-pad state exists in this helper.",
        "No active depth prompt exists now.",
        "No prompt would run.",
        "No state would change.",
        "No command would dispatch.",
        "No command would execute.",
        "No MIDI would be sent.",
        "No ports would be opened.",
    )
    assert result.metadata["source"] == "ISOLATED_PAD_MUTATION_COMMANDS"
    assert result.metadata["source_command_type"] == "mutation"
    assert result.metadata["command_family"] == "isolated_pad_mutation"
    assert result.metadata["mutation_area"] == "full"
    assert result.metadata["uses_group_default_zone_depth"] is True
    assert result.metadata["requires_depth_selection"] is False
    assert result.metadata["scope"] == "selected_isolated_pad"
    assert result.metadata["mock_only"] is True
    assert result.metadata["sends_real_midi"] is False
    assert result.metadata["opens_ports"] is False
    assert result.metadata["hardware_required"] is False
    assert result.metadata["active_behavior"] is False
    assert result.metadata["mutates_runtime_state"] is False


def test_selected_isolated_pad_mutation_ps_has_expected_display_and_metadata():
    from rytm_randomizer.behavior.mutation_depth import evaluate_mutation_depth_behavior

    result = evaluate_mutation_depth_behavior("PS")

    assert result.accepted is True
    assert result.display_lines == (
        "PS: mutate selected isolated pad SRC only, choose depth",
        "Read-only selected isolated pad mutation intent.",
        "Mutation area: src",
        "Selected-isolated-pad dependency is recorded only.",
        "Future depth selection is required.",
        "No active depth prompt exists now.",
        "No selected-isolated-pad state exists in this helper.",
        "No prompt would run.",
        "No state would change.",
        "No command would dispatch.",
        "No command would execute.",
        "No MIDI would be sent.",
        "No ports would be opened.",
    )
    assert result.metadata["source"] == "ISOLATED_PAD_MUTATION_COMMANDS"
    assert result.metadata["source_command_type"] == "mutation"
    assert result.metadata["command_family"] == "isolated_pad_mutation"
    assert result.metadata["mutation_area"] == "src"
    assert result.metadata["uses_group_default_zone_depth"] is False
    assert result.metadata["requires_depth_selection"] is True
    assert result.metadata["scope"] == "selected_isolated_pad"
    assert result.metadata["mock_only"] is True
    assert result.metadata["sends_real_midi"] is False
    assert result.metadata["opens_ports"] is False
    assert result.metadata["hardware_required"] is False
    assert result.metadata["active_behavior"] is False
    assert result.metadata["mutates_runtime_state"] is False


def test_repeated_selected_isolated_pad_mutation_evaluations_are_deterministic():
    from rytm_randomizer.behavior.mutation_depth import evaluate_mutation_depth_behavior

    for (
        command_key,
        _label,
        _area,
        _requires_depth,
        _uses_default,
    ) in SELECTED_ISOLATED_PAD_MUTATION_CASES:
        assert evaluate_mutation_depth_behavior(command_key) == (
            evaluate_mutation_depth_behavior(command_key)
        )


def test_packet_3d_keys_are_no_longer_deferred():
    from rytm_randomizer.behavior.mutation_depth import DEFERRED_PACKET_3_MUTATION_DEPTH_KEYS

    assert not set(PACKET_3D_KEYS).intersection(DEFERRED_PACKET_3_MUTATION_DEPTH_KEYS)


def test_mutation_depth_metadata_is_copied_and_immutable():
    from rytm_randomizer.behavior.mutation_depth import MutationDepthBehaviorResult

    metadata = {"source": "test"}
    result = MutationDepthBehaviorResult(command_key="1", metadata=metadata)

    metadata["source"] = "changed"

    assert result.metadata["source"] == "test"

    try:
        result.metadata["source"] = "mutated"
    except TypeError:
        pass
    else:
        raise AssertionError("metadata should be immutable")


def test_unknown_keys_fail_safely():
    from rytm_randomizer.behavior.mutation_depth import evaluate_mutation_depth_behavior

    result = evaluate_mutation_depth_behavior("DOES_NOT_EXIST")

    assert result.accepted is False
    assert result.reason == "unknown_command"
    assert result.display_lines == ()
    assert result.depth_value is None
    assert result.guarded_input is False
    assert result.requires_depth_prompt_context is False
    assert result.prompt_available is False
    assert result.state_changed is False
    assert result.prompt_required is False
    assert result.dispatches_command is False
    assert result.executes_command is False
    assert result.sends_real_midi is False
    assert result.opens_ports is False
    assert result.hardware_required is False
    assert result.active_behavior is False


def test_deferred_packet_3_keys_fail_safely():
    from rytm_randomizer.behavior.mutation_depth import evaluate_mutation_depth_behavior

    for command_key in DEFERRED_PACKET_3_KEYS:
        result = evaluate_mutation_depth_behavior(command_key)

        assert result.accepted is False
        assert result.reason == "deferred_mutation_depth_command"
        assert result.sends_real_midi is False
        assert result.opens_ports is False
        assert result.hardware_required is False
        assert result.active_behavior is False
        assert result.metadata["source"] == "COMMANDS"


def test_packet_1_menu_utility_behavior_remains_unchanged():
    from rytm_randomizer.behavior.menu_utility import evaluate_menu_utility_behavior

    result = evaluate_menu_utility_behavior("BD")

    assert result.accepted is True
    assert result.label == "show BD engine tools"
    assert result.sends_real_midi is False
    assert result.active_behavior is False


def test_packet_2_anchor_profile_behavior_remains_unchanged():
    from rytm_randomizer.behavior.anchor_profile import evaluate_anchor_profile_behavior

    result = evaluate_anchor_profile_behavior("BH")

    assert result.accepted is True
    assert result.label == "load Pad 1 BD Hard anchor, primary default"
    assert result.profile_key == "2"
    assert result.machine_value == 0
    assert result.sends_real_midi is False
    assert result.active_behavior is False


def test_passive_cli_behavior_remains_unchanged():
    result = run_cli("inspect-command", "1")

    assert result.returncode == 0
    assert "Command: 1" in result.stdout
    assert "Label: guarded depth input 1, requires lane/mode prefix" in result.stdout
    assert result.stderr == ""


def test_no_real_midi_library_is_imported():
    import rytm_randomizer.behavior.mutation_depth  # noqa: F401

    assert "mido" not in sys.modules
    assert "rtmidi" not in sys.modules


def test_packaging_uses_pyproject_not_legacy_setup():
    # WS-A introduced PEP 621 packaging. The project ships pyproject.toml as the
    # single source of packaging truth; legacy setup.py / setup.cfg must not be used.
    assert (PROJECT_ROOT / "pyproject.toml").exists()
    for legacy in ("setup.py", "setup.cfg"):
        assert not (PROJECT_ROOT / legacy).exists()


def test_behavior_mutation_depth_exposes_no_active_behavior_names():
    import rytm_randomizer.behavior.mutation_depth as behavior_mutation_depth

    exposed_names = set(dir(behavior_mutation_depth))

    assert "execute_command" not in exposed_names
    assert "send_command" not in exposed_names
    assert "hardware_test" not in exposed_names


def test_no_out_of_scope_support_is_exposed():
    import rytm_randomizer.behavior.mutation_depth as behavior_mutation_depth

    module_text = "\n".join(
        [
            behavior_mutation_depth.__doc__ or "",
            behavior_mutation_depth.evaluate_mutation_depth_behavior.__doc__ or "",
        ]
    )

    assert "Analog Four support" not in module_text
    assert "Pads 5-12 support" not in module_text


if __name__ == "__main__":
    test_importing_behavior_mutation_depth_prints_nothing()
    test_guarded_numeric_inputs_return_read_only_results()
    test_guarded_numeric_input_1_has_expected_display_and_metadata()
    test_repeated_mutation_depth_evaluations_are_deterministic()
    test_legacy_single_profile_mutations_return_read_only_results()
    test_legacy_single_profile_mutation_m1_has_expected_display_and_metadata()
    test_repeated_legacy_single_profile_mutation_evaluations_are_deterministic()
    test_current_profile_page_mutations_return_read_only_results()
    test_current_profile_page_mutation_s_has_expected_display_and_metadata()
    test_repeated_current_profile_page_mutation_evaluations_are_deterministic()
    test_selected_isolated_pad_mutations_return_read_only_results()
    test_selected_isolated_pad_mutation_pm_has_expected_display_and_metadata()
    test_selected_isolated_pad_mutation_ps_has_expected_display_and_metadata()
    test_repeated_selected_isolated_pad_mutation_evaluations_are_deterministic()
    test_packet_3d_keys_are_no_longer_deferred()
    test_mutation_depth_metadata_is_copied_and_immutable()
    test_unknown_keys_fail_safely()
    test_deferred_packet_3_keys_fail_safely()
    test_packet_1_menu_utility_behavior_remains_unchanged()
    test_packet_2_anchor_profile_behavior_remains_unchanged()
    test_passive_cli_behavior_remains_unchanged()
    test_no_real_midi_library_is_imported()
    test_packaging_uses_pyproject_not_legacy_setup()
    test_behavior_mutation_depth_exposes_no_active_behavior_names()
    test_no_out_of_scope_support_is_exposed()
