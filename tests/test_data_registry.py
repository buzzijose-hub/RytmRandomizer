from __future__ import annotations

import importlib
import sys


def test_data_package_imports_without_side_effects(capsys):
    sys.modules.pop("rytm_randomizer.data", None)

    importlib.import_module("rytm_randomizer.data")

    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == ""
    assert "mido" not in sys.modules
    assert "rtmidi" not in sys.modules


def test_shared_data_exports_existing_passive_metadata():
    from rytm_randomizer import constants, profiles, scenes
    from rytm_randomizer.data import constants as data_constants
    from rytm_randomizer.data import profiles as data_profiles
    from rytm_randomizer.data import scenes as data_scenes

    assert constants.MACHINE_CC == data_constants.MACHINE_CC
    assert constants.SUPPORTED_PADS == data_constants.SUPPORTED_PADS
    assert profiles.GROUP_PROFILE_METADATA == data_profiles.GROUP_PROFILE_METADATA
    assert profiles.GROUP_LAYOUT == data_profiles.GROUP_LAYOUT
    assert scenes.SCENE_COMMANDS == data_scenes.SCENE_COMMANDS


def test_shared_data_keeps_active_behavior_absent():
    import rytm_randomizer.data as data

    exposed_names = set(dir(data))

    assert "execute_command" not in exposed_names
    assert "send_command" not in exposed_names
    assert "hardware_test" not in exposed_names
    assert "open_port" not in exposed_names
    assert "send_midi" not in exposed_names
