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
    assert roles[0].key == "main_kick_foundation"
    assert roles[0].pad == 1
    assert "kick" in roles[0].desired_tags
    assert roles[4].key == "closed_hat_pulse"
    assert roles[8].key == "tonal_bell_accent"
    assert roles[-1].key == "wild_discovery_lane"


def test_metallic_reference_ranks_mapped_metallic_engines_first_by_default():
    from rytm_randomizer.essence.machine_catalog import rank_machines_for_role

    ranked = rank_machines_for_role(
        "metallic_motif",
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
        "metallic_motif",
        essence_tags=("metallic", "bell", "digital", "repetition"),
        include_unmapped=True,
    )

    keys = tuple(candidate.machine.key for candidate in ranked[:6])

    assert "bd_fm" in keys
    assert "sd_fm" in keys
    assert "sy_chip" in keys
    assert "dual_vco" in keys


def test_hat_role_can_include_machine_selectable_real_hat_engines():
    from rytm_randomizer.essence.machine_catalog import rank_machines_for_role

    ranked = rank_machines_for_role(
        "closed_hat_pulse",
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
