import subprocess
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.fast

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_importing_machine_catalog_is_passive_and_silent():
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import sys; "
                "import rytm_randomizer.essence.machine_catalog; "
                "assert 'mido' not in sys.modules; "
                "assert 'rtmidi' not in sys.modules"
            ),
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert result.stdout == ""
    assert result.stderr == ""


def test_catalog_tracks_v134_mutable_machines_and_selectable_inventory():
    from rytm_randomizer.essence.machine_catalog import get_machine_profile, list_machine_profiles

    profiles = list_machine_profiles()

    assert len(profiles) >= 32
    assert get_machine_profile("bd_hard").machine_value == 0
    assert get_machine_profile("bd_hard").support_status == "mutable_v134"
    assert get_machine_profile("bd_fm").machine_value == 13
    assert get_machine_profile("sd_fm").machine_value == 14
    assert get_machine_profile("sy_raw").machine_value == 32

    sy_chip = get_machine_profile("sy_chip")
    dual_vco = get_machine_profile("dual_vco")
    assert sy_chip.machine_value == 29
    assert sy_chip.support_status == "machine_selectable"
    assert dual_vco.machine_value == 28
    assert dual_vco.support_status == "machine_selectable"

    ch_classic = get_machine_profile("ch_classic")
    hh_lab = get_machine_profile("hh_lab")
    assert ch_classic.machine_value == 9
    assert ch_classic.support_status == "machine_selectable"
    assert hh_lab.machine_value == 33
    assert hh_lab.support_status == "machine_selectable"


def test_twelve_pad_role_template_covers_performance_lanes():
    from rytm_randomizer.essence.machine_catalog import list_twelve_pad_roles

    roles = list_twelve_pad_roles()

    assert tuple(role.pad for role in roles) == tuple(range(1, 13))
    assert roles[0].key == "bd_track_bass_drum"
    assert roles[0].pad == 1
    assert "kick" in roles[0].desired_tags
    assert roles[4].key == "bt_track_bass_tom"
    assert roles[8].key == "ch_track_closed_hihat"
    assert roles[9].key == "oh_track_open_hihat"
    assert roles[-1].key == "cb_track_cowbell"


def test_rytm_os172_pad_capabilities_match_manual_machine_table():
    from rytm_randomizer.essence.machine_catalog import (
        get_rytm_pad_capability,
        is_machine_allowed_on_pad,
        list_rytm_pad_capabilities,
    )

    capabilities = list_rytm_pad_capabilities()

    assert tuple(capability.pad for capability in capabilities) == tuple(range(1, 13))
    assert get_rytm_pad_capability(1).track_code == "BD"
    assert get_rytm_pad_capability(10).track_code == "OH"
    assert get_rytm_pad_capability(10).label == "Open Hihat"

    assert set(get_rytm_pad_capability(1).allowed_machine_keys) >= {
        "bd_hard",
        "bd_classic",
        "bd_fm",
        "bd_plastic",
        "bd_silky",
        "bd_sharp",
        "bd_acoustic",
        "sd_hard",
        "sd_classic",
        "sd_fm",
        "sd_natural",
        "sd_acoustic",
        "dual_vco",
        "sy_chip",
        "sy_raw",
        "ut_noise",
        "ut_impulse",
    }
    assert get_rytm_pad_capability(5).allowed_machine_keys == (
        "bt_classic",
        "ut_noise",
        "ut_impulse",
    )
    assert get_rytm_pad_capability(6).allowed_machine_keys == (
        "xt_classic",
        "ut_noise",
        "ut_impulse",
    )
    assert get_rytm_pad_capability(7).allowed_machine_keys == (
        "xt_classic",
        "ut_noise",
        "ut_impulse",
    )
    assert get_rytm_pad_capability(8).allowed_machine_keys == (
        "xt_classic",
        "ut_noise",
        "ut_impulse",
    )
    assert set(get_rytm_pad_capability(9).allowed_machine_keys) == {
        "ch_classic",
        "ch_metallic",
        "hh_basic",
        "hh_lab",
        "oh_classic",
        "oh_metallic",
        "ut_noise",
        "ut_impulse",
    }
    assert set(get_rytm_pad_capability(10).allowed_machine_keys) == {
        "oh_classic",
        "oh_metallic",
        "hh_basic",
        "hh_lab",
        "ch_classic",
        "ch_metallic",
        "ut_noise",
        "ut_impulse",
    }
    assert set(get_rytm_pad_capability(11).allowed_machine_keys) == {
        "cy_classic",
        "cy_metallic",
        "cy_ride",
        "cb_classic",
        "cb_metallic",
        "ut_noise",
        "ut_impulse",
    }
    assert set(get_rytm_pad_capability(12).allowed_machine_keys) == {
        "cb_classic",
        "cb_metallic",
        "cy_classic",
        "cy_metallic",
        "cy_ride",
        "ut_noise",
        "ut_impulse",
    }

    assert is_machine_allowed_on_pad(10, "oh_metallic")
    assert is_machine_allowed_on_pad(10, "ch_classic")
    assert not is_machine_allowed_on_pad(10, "xt_classic")
    assert is_machine_allowed_on_pad(6, "xt_classic")
    assert not is_machine_allowed_on_pad(6, "ch_classic")


def test_metallic_reference_ranks_mapped_metallic_engines_first_by_default():
    from rytm_randomizer.essence.machine_catalog import rank_machines_for_role

    ranked = rank_machines_for_role(
        "rs_track_rim_shot",
        essence_tags=("metallic", "bell", "repetition", "detroit"),
    )

    keys = tuple(candidate.machine.key for candidate in ranked[:4])

    assert "bd_fm" in keys
    assert "sd_fm" in keys
    assert "sy_chip" not in keys
    assert all(candidate.machine.support_status == "mutable_v134" for candidate in ranked[:4])


def test_metallic_reference_can_include_future_engines_as_inventory_candidates():
    from rytm_randomizer.essence.machine_catalog import rank_machines_for_role

    ranked = rank_machines_for_role(
        "rs_track_rim_shot",
        essence_tags=("metallic", "bell", "digital", "repetition"),
        include_unmapped=True,
    )

    keys = tuple(candidate.machine.key for candidate in ranked[:6])

    assert "bd_fm" in keys
    assert "sy_chip" in keys
    assert "rs_hard" in keys
    assert "rs_classic" in keys


def test_hat_role_can_include_machine_selectable_real_hat_engines():
    from rytm_randomizer.essence.machine_catalog import rank_machines_for_role

    ranked = rank_machines_for_role(
        "ch_track_closed_hihat",
        essence_tags=("bright", "repetition", "density"),
        include_machine_selectable=True,
    )

    keys = tuple(candidate.machine.key for candidate in ranked[:4])

    assert keys[:2] == ("ch_classic", "ch_metallic")
    assert "hh_basic" in keys
    assert all(candidate.machine.machine_value is not None for candidate in ranked[:4])


def test_reference_discovery_slider_expands_role_plan_candidates():
    from rytm_randomizer.essence.machine_catalog import build_essence_role_plan

    reference_plan = build_essence_role_plan(
        essence_tags=("metallic", "bell", "driving", "repetition"),
        discovery=0.0,
    )
    discovery_plan = build_essence_role_plan(
        essence_tags=("metallic", "bell", "driving", "repetition"),
        discovery=1.0,
    )

    assert len(reference_plan) == 12
    assert len(discovery_plan) == 12
    assert all(assignment.pad == index for index, assignment in enumerate(reference_plan, start=1))
    assert all(
        candidate.machine.support_status == "mutable_v134"
        for assignment in reference_plan
        for candidate in assignment.candidates
    )
    assert any(
        candidate.machine.support_status == "machine_selectable"
        for assignment in discovery_plan
        for candidate in assignment.candidates
    )
