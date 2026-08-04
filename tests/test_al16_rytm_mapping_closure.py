from __future__ import annotations

import json
from pathlib import Path
from typing import cast

import pytest

from conftest import ANALOG_RYTM_SAVED_KIT_TEST_HEADER
from rytm_randomizer.cockpit.export import al16_rytm_mapping_closure as mapping_closure
from rytm_randomizer.cockpit.export.al16_rytm_mapping_closure import (
    analyze_mapping_capture,
    analyze_mapping_capture_files,
    build_mapping_closure_plan,
    candidate_location_for_path,
    load_mapping_gap_paths,
    render_mapping_capture_report,
)
from rytm_randomizer.data.analog_rytm_kit_layout import RYTM_KIT_RAW_SIZE
from rytm_randomizer.devices.strategies.analog_rytm_saved_kit_codec import (
    AnalogRytmSavedKitCodecError,
    encode_analog_rytm_saved_kit_frame,
)

pytestmark = pytest.mark.fast

_REPO_ROOT = Path(__file__).resolve().parents[1]
_RECIPE_PATH = _REPO_ROOT / "specs" / "al16" / "AL02_LOCK_RYTM.yaml"
_GAP_PATHS = (
    "destination_slot",
    "tracks.1.machine",
    "tracks.1.source.dec",
    "tracks.1.source.hld",
    "tracks.1.source.swd",
    "tracks.1.source.swt",
    "tracks.1.source.trn",
    "tracks.1.source.tun",
    "tracks.1.source.wav",
    "tracks.1.amp.vol",
    "tracks.3.machine",
    "tracks.3.amp.vol",
    "tracks.6.source.decay",
    "tracks.6.source.target_note",
    "tracks.6.amp.vol",
    "tracks.9.machine",
    "tracks.9.source.decay",
    "tracks.9.amp.vol",
)


def _recipe() -> dict[str, object]:
    parsed = cast(object, json.loads(_RECIPE_PATH.read_text(encoding="utf-8")))
    assert isinstance(parsed, dict)
    return cast(dict[str, object], parsed)


def _frame(raw: bytes) -> bytes:
    return encode_analog_rytm_saved_kit_frame(
        ANALOG_RYTM_SAVED_KIT_TEST_HEADER,
        raw,
    )


def test_closure_plan_covers_all_eighteen_gaps_in_two_sessions() -> None:
    plan = build_mapping_closure_plan(_GAP_PATHS)

    assert plan.manual_sessions_required == 2
    assert {group.evidence_class: len(group.semantic_paths) for group in plan.groups} == {
        "machine_selection": 3,
        "machine_source": 9,
        "amp_volume": 4,
        "machine_tuning": 1,
        "destination_slot": 1,
    }
    assert len(plan.covered_paths) == 18
    assert set(plan.covered_paths) == set(_GAP_PATHS)


def test_closure_plan_rejects_duplicate_and_unknown_paths() -> None:
    with pytest.raises(ValueError, match="must be unique"):
        build_mapping_closure_plan(("destination_slot", "destination_slot"))
    with pytest.raises(ValueError, match="unsupported AL16 mapping-gap path"):
        build_mapping_closure_plan(("tracks.1.filter.frq",))


def test_closure_plan_defensive_coverage_invariant(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        mapping_closure,
        "_GROUP_ORDER",
        ("machine_selection", "machine_selection"),
    )

    with pytest.raises(ValueError, match="did not cover every path exactly once"):
        build_mapping_closure_plan(("tracks.1.machine",))


def test_candidate_location_rejects_invalid_track_paths_and_recipe_shapes() -> None:
    with pytest.raises(ValueError, match="invalid AL16 track semantic path"):
        candidate_location_for_path("tracks.X.source.dec", _recipe())
    with pytest.raises(ValueError, match="pad must be in 1..12"):
        candidate_location_for_path("tracks.13.machine", _recipe())
    with pytest.raises(ValueError, match="pad must be in 1..12"):
        mapping_closure._mapping_evidence_track_offset(0, 0)
    with pytest.raises(ValueError, match="tracks must be a mapping"):
        candidate_location_for_path("tracks.1.source.dec", {})
    with pytest.raises(ValueError, match="keys must be numeric strings"):
        candidate_location_for_path("tracks.1.source.dec", {"tracks": {"one": {}}})
    with pytest.raises(ValueError, match="track 1 must be a mapping"):
        candidate_location_for_path("tracks.1.source.dec", {"tracks": {"1": "bad"}})
    with pytest.raises(ValueError, match="machine must be a string"):
        candidate_location_for_path(
            "tracks.1.source.dec",
            {"tracks": {"1": {"machine": 1}}},
        )


def test_candidate_location_reports_unresolved_machine_and_source_fields() -> None:
    missing_machine = candidate_location_for_path(
        "tracks.1.source.dec",
        {"tracks": {"1": {}}},
    )
    unknown_alias = candidate_location_for_path(
        "tracks.1.source.unknown",
        {"tracks": {"1": {"machine": "bd_classic"}}},
    )
    unknown_machine = candidate_location_for_path(
        "tracks.1.source.dec",
        {"tracks": {"1": {"machine": "not_a_machine"}}},
    )
    unsupported_parameter = candidate_location_for_path(
        "tracks.3.source.hld",
        {"tracks": {"3": {"machine": "rs_classic"}}},
    )

    assert missing_machine.status == "unresolved_recipe_machine"
    assert unknown_alias.status == "unresolved_machine_parameter"
    assert unknown_machine.status == "unresolved_recipe_machine"
    assert unsupported_parameter.status == "unresolved_machine_parameter"


@pytest.mark.parametrize(
    ("manifest", "message"),
    [
        ({}, "must be a non-empty list"),
        ({"critical_mapping_gaps": ["bad"]}, "gap 0 must be a mapping"),
        (
            {"critical_mapping_gaps": [{"semantic_path": ""}]},
            "gap 0 semantic_path must be a string",
        ),
    ],
)
def test_mapping_gap_loader_rejects_malformed_entries(
    manifest: dict[str, object],
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        load_mapping_gap_paths(manifest)


def test_candidate_locations_use_existing_catalog_and_keep_ambiguity_unresolved() -> None:
    recipe = _recipe()
    machine = candidate_location_for_path("tracks.1.machine", recipe)
    bd_decay = candidate_location_for_path("tracks.1.source.dec", recipe)
    xt_tune = candidate_location_for_path("tracks.6.source.target_note", recipe)
    amp_volume = candidate_location_for_path("tracks.3.amp.vol", recipe)
    ambiguous_hat = candidate_location_for_path("tracks.9.source.decay", recipe)
    destination = candidate_location_for_path("destination_slot", recipe)

    assert machine.status == "candidate_location"
    assert bd_decay.status == "candidate_location"
    assert "bd_classic Decay NRPN 1:2" in bd_decay.source
    assert xt_tune.status == "candidate_location"
    assert "xt_classic Tune NRPN 1:1" in xt_tune.source
    assert amp_volume.status == "candidate_location"
    assert "Amp Volume NRPN 1:31" in amp_volume.source
    assert ambiguous_hat.status == "unresolved_recipe_machine"
    assert ambiguous_hat.unpacked_offset is None
    assert "ch_basic" in ambiguous_hat.source
    assert destination.status == "destination_header_proof_required"


def test_offline_capture_analyzer_reports_candidates_without_promoting_them() -> None:
    recipe = _recipe()
    paths = (
        "destination_slot",
        "tracks.1.machine",
        "tracks.1.source.dec",
        "tracks.3.amp.vol",
        "tracks.6.source.target_note",
        "tracks.9.source.decay",
    )
    configured = bytearray(RYTM_KIT_RAW_SIZE)
    for semantic_path, value in (
        ("tracks.1.machine", 1),
        ("tracks.1.source.dec", 53),
        ("tracks.3.amp.vol", 56),
        ("tracks.6.source.target_note", 41),
    ):
        location = candidate_location_for_path(semantic_path, recipe)
        assert location.unpacked_offset is not None
        configured[location.unpacked_offset] = value
    configured[10] = 99

    report = analyze_mapping_capture(
        reference_frame=_frame(bytes(RYTM_KIT_RAW_SIZE)),
        configured_frame=_frame(bytes(configured)),
        recipe=recipe,
        semantic_paths=paths,
    )
    statuses = {
        observation.semantic_path: observation.status
        for observation in report.candidate_observations
    }

    assert report.promotion_status == "review_required"
    assert statuses == {
        "destination_slot": "not_located",
        "tracks.1.machine": "candidate_changed",
        "tracks.1.source.dec": "candidate_changed",
        "tracks.3.amp.vol": "candidate_changed",
        "tracks.6.source.target_note": "candidate_changed",
        "tracks.9.source.decay": "not_located",
    }
    assert report.other_changed_unpacked_offsets == (10,)
    assert report.changed_header_indices == ()


def test_offline_capture_analyzer_reports_unchanged_candidates() -> None:
    frame = _frame(bytes(RYTM_KIT_RAW_SIZE))

    report = analyze_mapping_capture(
        reference_frame=frame,
        configured_frame=frame,
        recipe=_recipe(),
        semantic_paths=("tracks.1.source.dec",),
    )

    assert report.candidate_observations[0].status == "candidate_unchanged"
    assert report.changed_unpacked_offsets == ()


def test_file_analyzer_and_renderer_are_deterministic(tmp_path: Path) -> None:
    frame = _frame(bytes(RYTM_KIT_RAW_SIZE))
    reference_path = tmp_path / "reference.syx"
    configured_path = tmp_path / "configured.syx"
    reference_path.write_bytes(frame)
    configured_path.write_bytes(frame)

    first = analyze_mapping_capture_files(
        reference_path=reference_path,
        configured_path=configured_path,
        recipe=_recipe(),
        semantic_paths=("tracks.1.machine",),
    )
    second = analyze_mapping_capture_files(
        reference_path=reference_path,
        configured_path=configured_path,
        recipe=_recipe(),
        semantic_paths=("tracks.1.machine",),
    )

    assert first == second
    assert render_mapping_capture_report(first) == render_mapping_capture_report(second)
    assert '"promotion_status": "review_required"' in render_mapping_capture_report(first)


def test_capture_analyzer_rejects_invalid_saved_kit_frames() -> None:
    valid = _frame(bytes(RYTM_KIT_RAW_SIZE))

    with pytest.raises(AnalogRytmSavedKitCodecError, match="frame length"):
        analyze_mapping_capture(
            reference_frame=valid[:-1],
            configured_frame=valid,
            recipe=_recipe(),
            semantic_paths=("tracks.1.machine",),
        )
