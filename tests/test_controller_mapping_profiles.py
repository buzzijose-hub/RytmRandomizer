from __future__ import annotations

import pytest

pytestmark = pytest.mark.fast


def test_default_controller_profile_has_16_slot_pages() -> None:
    from rytm_randomizer.data.controller_mapping_profiles import (
        CONTROLLER_ENCODER_COUNT,
        CONTROLLER_MAPPING_PROFILES,
        DEFAULT_CONTROLLER_MAPPING_PROFILE,
    )

    profile = CONTROLLER_MAPPING_PROFILES[DEFAULT_CONTROLLER_MAPPING_PROFILE]

    assert CONTROLLER_ENCODER_COUNT == 16
    assert profile.controller_family == "generic-16-encoder"
    assert [page.key for page in profile.pages] == [
        "global-brain",
        "rytm-pads-1-4",
        "rytm-pads-5-8",
        "rytm-pads-9-12",
        "analog-four-tracks",
        "style-crates-queue",
        "snapshot-recovery-journal",
    ]
    for page in profile.pages:
        assert [control.slot for control in page.controls] == list(range(1, 17))


def test_controller_profile_is_intent_based_and_device_aware() -> None:
    from rytm_randomizer.data.controller_mapping_profiles import (
        CONTROLLER_MAPPING_PROFILES,
        DEFAULT_CONTROLLER_MAPPING_PROFILE,
    )

    profile = CONTROLLER_MAPPING_PROFILES[DEFAULT_CONTROLLER_MAPPING_PROFILE]
    controls = [control for page in profile.pages for control in page.controls]

    assert {control.target_device for control in controls} >= {
        "analog_rytm_mk2",
        "analog_four_mk2",
        "style_queue",
        "snapshot_recovery",
    }
    assert {control.target_scope for control in controls} >= {
        "rytm_pad_6",
        "rytm_pad_12",
        "a4_track_1",
        "queue",
        "journal",
    }
    assert all(control.intent_key for control in controls)
    assert all("cc" not in control.action.lower() for control in controls)
    assert any(control.intent_key == "rytm.pad6.source_amount" for control in controls)
    assert any(control.intent_key == "a4.track1.macro_depth" for control in controls)


def test_controller_profile_blocks_active_hardware_actions() -> None:
    from rytm_randomizer.data.controller_mapping_profiles import (
        CONTROLLER_MAPPING_PROFILES,
        DEFAULT_CONTROLLER_MAPPING_PROFILE,
    )

    profile = CONTROLLER_MAPPING_PROFILES[DEFAULT_CONTROLLER_MAPPING_PROFILE]

    assert "open MIDI controller input" in profile.blocked_active_actions
    assert "send hardware MIDI" in profile.blocked_active_actions
    assert "dispatch Cockpit WebSocket commands" in profile.blocked_active_actions
    assert profile.safety_summary == (
        "passive mapping only; translates controller gestures into reviewed "
        "RytmRandomizer intent, not active MIDI sends"
    )


def test_controller_profile_export_constants_are_reexported() -> None:
    import rytm_randomizer.data as data

    assert data.CONTROLLER_ENCODER_COUNT == 16
    assert data.DEFAULT_CONTROLLER_MAPPING_PROFILE == "generic-16-encoder-performance"
    assert "CONTROLLER_MAPPING_PROFILES" in data.__all__


def test_controller_page_builder_rejects_wrong_control_count() -> None:
    from rytm_randomizer.data import controller_mapping_profiles as profiles

    with pytest.raises(ValueError, match="must define 16 controls"):
        profiles._page("bad", "Bad", "Missing controls", ())


def test_controller_page_builder_rejects_non_sequential_slots() -> None:
    from rytm_randomizer.data import controller_mapping_profiles as profiles

    controls = tuple(
        profiles.ControllerMappingControlSpec(
            slot=slot,
            label=f"Control {slot}",
            target_device="style_queue",
            target_scope="global",
            intent_key=f"test.{slot}",
            action="adjust_test",
            lane="test",
            safety_tier="passive",
            recovery_action="recover_anchor",
            notes="Test control.",
        )
        for slot in (*range(1, 16), 20)
    )

    with pytest.raises(ValueError, match="slots must be 1-16"):
        profiles._page("bad", "Bad", "Bad slots", controls)
