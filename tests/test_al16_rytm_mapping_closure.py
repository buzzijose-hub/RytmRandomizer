from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import cast

import pytest

from conftest import AL16_RYTM_MAPPING_GAP_PATHS, ANALOG_RYTM_SAVED_KIT_TEST_HEADER
from rytm_randomizer.cockpit.export import al16_rytm_mapping_closure as mapping_closure
from rytm_randomizer.cockpit.export.al16_rytm_kit import deterministic_recipe_identifier
from rytm_randomizer.cockpit.export.al16_rytm_mapping_closure import (
    CandidateLocation,
    MappingEvidenceProvenance,
    MappingGapRequest,
    analyze_mapping_capture,
    analyze_mapping_capture_files,
    build_mapping_closure_plan,
    candidate_location_for_path,
    load_mapping_gap_paths,
    load_mapping_gap_requests,
    render_mapping_capture_report,
)
from rytm_randomizer.data.analog_rytm_kit_layout import (
    RYTM_KIT_RAW_SIZE,
    analog_rytm_track_sound_offset,
)
from rytm_randomizer.data.analog_rytm_midi import AnalogRytmCcMapping
from rytm_randomizer.devices.strategies.analog_rytm_saved_kit_codec import (
    AnalogRytmSavedKitCodecError,
    encode_analog_rytm_saved_kit_frame,
)

pytestmark = pytest.mark.fast

_REPO_ROOT = Path(__file__).resolve().parents[1]
_RECIPE_PATH = _REPO_ROOT / "specs" / "al16" / "AL02_LOCK_RYTM.yaml"
_EXPECTED_GAP_LOCATIONS = {
    "destination_slot": (
        "destination_header_proof_required",
        None,
        None,
        "separate user-selected scratch-slot header proof",
    ),
    "tracks.1.machine": (
        "candidate_location",
        170,
        1,
        "existing decoded-kit machine-type candidate offset; adjacent flag validity still requires review",
    ),
    "tracks.1.source.dec": (
        "candidate_location",
        78,
        1,
        "manual-backed bd_classic Decay NRPN 1:2 plus candidate saved-kit sound offset 0x0020",
    ),
    "tracks.1.source.hld": (
        "candidate_location",
        80,
        1,
        "manual-backed bd_classic Hold NRPN 1:3 plus candidate saved-kit sound offset 0x0022",
    ),
    "tracks.1.source.swd": (
        "candidate_location",
        84,
        1,
        "manual-backed bd_classic Sweep Depth NRPN 1:5 plus candidate saved-kit sound offset 0x0026",
    ),
    "tracks.1.source.swt": (
        "candidate_location",
        82,
        1,
        "manual-backed bd_classic Sweep Time NRPN 1:4 plus candidate saved-kit sound offset 0x0024",
    ),
    "tracks.1.source.trn": (
        "candidate_location",
        88,
        1,
        "manual-backed bd_classic Transient Tick NRPN 1:7 plus candidate saved-kit sound offset 0x002A",
    ),
    "tracks.1.source.tun": (
        "candidate_location",
        76,
        1,
        "manual-backed bd_classic Tune NRPN 1:1 plus candidate saved-kit sound offset 0x001E",
    ),
    "tracks.1.source.wav": (
        "candidate_location",
        86,
        1,
        "manual-backed bd_classic Waveform NRPN 1:6 plus candidate saved-kit sound offset 0x0028",
    ),
    "tracks.1.amp.vol": (
        "candidate_location",
        136,
        1,
        "manual-backed Amp Volume NRPN 1:31 plus candidate saved-kit sound offset 0x005A",
    ),
    "tracks.3.machine": (
        "candidate_location",
        494,
        1,
        "existing decoded-kit machine-type candidate offset; adjacent flag validity still requires review",
    ),
    "tracks.3.amp.vol": (
        "candidate_location",
        460,
        1,
        "manual-backed Amp Volume NRPN 1:31 plus candidate saved-kit sound offset 0x005A",
    ),
    "tracks.6.source.decay": (
        "candidate_location",
        888,
        1,
        "manual-backed xt_classic Decay NRPN 1:2 plus candidate saved-kit sound offset 0x0020",
    ),
    "tracks.6.source.target_note": (
        "candidate_location",
        886,
        1,
        "manual-backed xt_classic Tune NRPN 1:1 plus candidate saved-kit sound offset 0x001E",
    ),
    "tracks.6.amp.vol": (
        "candidate_location",
        946,
        1,
        "manual-backed Amp Volume NRPN 1:31 plus candidate saved-kit sound offset 0x005A",
    ),
    "tracks.9.machine": (
        "candidate_location",
        1466,
        1,
        "existing decoded-kit machine-type candidate offset; adjacent flag validity still requires review",
    ),
    "tracks.9.source.decay": (
        "unresolved_recipe_machine",
        None,
        None,
        "recipe selects unknown machine ch_basic",
    ),
    "tracks.9.amp.vol": (
        "candidate_location",
        1432,
        1,
        "manual-backed Amp Volume NRPN 1:31 plus candidate saved-kit sound offset 0x005A",
    ),
}


def _recipe() -> dict[str, object]:
    parsed = cast(object, json.loads(_RECIPE_PATH.read_text(encoding="utf-8")))
    assert isinstance(parsed, dict)
    return cast(dict[str, object], parsed)


def _frame(raw: bytes) -> bytes:
    return encode_analog_rytm_saved_kit_frame(
        ANALOG_RYTM_SAVED_KIT_TEST_HEADER,
        raw,
    )


def _provenance() -> MappingEvidenceProvenance:
    return MappingEvidenceProvenance(
        recipe_artifact="recipe.yaml",
        recipe_sha256="recipe-sha256",
        gap_manifest_artifact="manifest.json",
        gap_manifest_sha256="manifest-sha256",
        deterministic_recipe_identifier="recipe-id",
        manifest_reference_sha256="reference-sha256",
    )


def _requested_manifest_value(semantic_path: str) -> object:
    values: dict[str, object] = {
        "destination_slot": 127,
        "tracks.1.machine": "BD Classic",
        "tracks.1.source.dec": 53,
    }
    return values.get(semantic_path, f"requested:{semantic_path}")


def _requests(semantic_paths: tuple[str, ...]) -> tuple[MappingGapRequest, ...]:
    return tuple(
        MappingGapRequest(
            semantic_path=semantic_path,
            requested_semantic_value=str(_requested_manifest_value(semantic_path)),
        )
        for semantic_path in semantic_paths
    )


def _write_bound_inputs(
    tmp_path: Path,
    *,
    reference_frame: bytes,
    configured_frame: bytes,
    semantic_paths: tuple[str, ...],
) -> tuple[Path, Path, Path, Path]:
    recipe_payload = _RECIPE_PATH.read_bytes()
    recipe = _recipe()
    reference_path = tmp_path / "reference.syx"
    configured_path = tmp_path / "configured.syx"
    recipe_path = tmp_path / "recipe.yaml"
    manifest_path = tmp_path / "manifest.json"
    reference_path.write_bytes(reference_frame)
    configured_path.write_bytes(configured_frame)
    recipe_path.write_bytes(recipe_payload)
    manifest_path.write_text(
        json.dumps(
            {
                "critical_mapping_gaps": [{"semantic_path": path} for path in semantic_paths],
                "semantic_field_audits": [
                    {
                        "semantic_path": path,
                        "requested_semantic_value": _requested_manifest_value(path),
                        "verification_status": "critical_mapping_gap",
                    }
                    for path in semantic_paths
                ],
                "deterministic_recipe_identifier": deterministic_recipe_identifier(recipe),
                "recipe_sha256": hashlib.sha256(recipe_payload).hexdigest(),
                "reference_sha256": hashlib.sha256(reference_frame).hexdigest(),
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    return reference_path, configured_path, recipe_path, manifest_path


def test_closure_plan_covers_all_eighteen_gaps_in_two_sessions() -> None:
    plan = build_mapping_closure_plan(AL16_RYTM_MAPPING_GAP_PATHS)

    assert plan.manual_sessions_required == 2
    assert {group.evidence_class: len(group.semantic_paths) for group in plan.groups} == {
        "machine_selection": 3,
        "machine_source": 9,
        "amp_volume": 4,
        "machine_tuning": 1,
        "destination_slot": 1,
    }
    assert len(plan.covered_paths) == 18
    assert set(plan.covered_paths) == set(AL16_RYTM_MAPPING_GAP_PATHS)


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
    with pytest.raises(ValueError, match=r"pad must be in \[1, 12\]"):
        analog_rytm_track_sound_offset(0, 0)
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


def test_source_location_fails_closed_for_broken_canonical_mapping(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def raise_missing_mapping(_machine: str, _parameter: str) -> AnalogRytmCcMapping | None:
        raise ValueError("broken canonical table")

    monkeypatch.setattr(mapping_closure, "cockpit_parameter_mapping", raise_missing_mapping)

    location = candidate_location_for_path("tracks.1.source.dec", _recipe())

    assert location.status == "unresolved_machine_parameter"
    assert location.unpacked_offset is None


def test_source_location_fails_closed_without_saved_kit_layout(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    mapping = AnalogRytmCcMapping(
        section="SYNTH",
        parameter="Decay",
        cc_msb=0,
        cc_lsb=None,
        nrpn_msb=1,
        nrpn_lsb=999,
        scope="track",
        risk="low",
        mutation_status="documented_only",
    )
    monkeypatch.setattr(mapping_closure, "cockpit_parameter_mapping", lambda *_args: mapping)

    location = candidate_location_for_path("tracks.1.source.dec", _recipe())

    assert location.status == "unresolved_machine_parameter"
    assert "no approved saved-kit layout" in location.source


def test_amp_volume_requires_canonical_mapping(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(mapping_closure, "cockpit_parameter_mapping", lambda *_args: None)

    with pytest.raises(ValueError, match="canonical Amp Volume mapping is unavailable"):
        candidate_location_for_path("tracks.3.amp.vol", _recipe())


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


def test_mapping_gap_loader_preserves_manifest_authoritative_scalar_values() -> None:
    paths = (
        "destination_slot",
        "tracks.1.machine",
        "tracks.1.source.dec",
        "tracks.1.source.hld",
        "tracks.1.source.swd",
    )
    requested_values: tuple[object, ...] = (127, "BD Classic", True, None, 32.5)
    manifest = {
        "critical_mapping_gaps": [{"semantic_path": path} for path in paths],
        "semantic_field_audits": [
            {
                "semantic_path": path,
                "requested_semantic_value": value,
                "verification_status": "critical_mapping_gap",
            }
            for path, value in zip(paths, requested_values, strict=True)
        ]
        + [
            {
                "semantic_path": "tracks.1.filter.frq",
                "requested_semantic_value": 25,
                "verification_status": "verified",
            }
        ],
    }

    requests = load_mapping_gap_requests(manifest)

    assert requests == (
        MappingGapRequest("destination_slot", "127"),
        MappingGapRequest("tracks.1.machine", "BD Classic"),
        MappingGapRequest("tracks.1.source.dec", "true"),
        MappingGapRequest("tracks.1.source.hld", "null"),
        MappingGapRequest("tracks.1.source.swd", "32.5"),
    )
    assert load_mapping_gap_paths(manifest) == paths


@pytest.mark.parametrize(
    ("audits", "message"),
    [
        (None, "semantic_field_audits must be a non-empty list"),
        (["bad"], "semantic field audit 0 must be a mapping"),
        (
            [
                {
                    "semantic_path": "",
                    "requested_semantic_value": 53,
                    "verification_status": "critical_mapping_gap",
                }
            ],
            "semantic field audit 0 semantic_path must be a string",
        ),
        (
            [
                {
                    "semantic_path": "tracks.1.source.dec",
                    "verification_status": "critical_mapping_gap",
                }
            ],
            "must include requested_semantic_value",
        ),
        (
            [
                {
                    "semantic_path": "tracks.1.source.dec",
                    "requested_semantic_value": 53,
                    "verification_status": "critical_mapping_gap",
                },
                {
                    "semantic_path": "tracks.1.source.dec",
                    "requested_semantic_value": 54,
                    "verification_status": "critical_mapping_gap",
                },
            ],
            "duplicate critical mapping-gap audit",
        ),
        (
            [
                {
                    "semantic_path": "tracks.1.source.dec",
                    "requested_semantic_value": [53],
                    "verification_status": "critical_mapping_gap",
                }
            ],
            "must be a JSON scalar",
        ),
        (
            [
                {
                    "semantic_path": "tracks.1.source.dec",
                    "requested_semantic_value": float("nan"),
                    "verification_status": "critical_mapping_gap",
                }
            ],
            "must be a finite JSON scalar",
        ),
    ],
)
def test_mapping_gap_request_loader_rejects_malformed_audits(
    audits: object,
    message: str,
) -> None:
    manifest = {
        "critical_mapping_gaps": [{"semantic_path": "tracks.1.source.dec"}],
        "semantic_field_audits": audits,
    }

    with pytest.raises(ValueError, match=message):
        load_mapping_gap_requests(manifest)


def test_mapping_gap_request_loader_requires_an_audit_for_every_gap() -> None:
    manifest = {
        "critical_mapping_gaps": [{"semantic_path": "tracks.1.source.dec"}],
        "semantic_field_audits": [
            {
                "semantic_path": "tracks.1.source.hld",
                "requested_semantic_value": 42,
                "verification_status": "critical_mapping_gap",
            }
        ],
    }

    with pytest.raises(ValueError, match="no critical mapping-gap audit"):
        load_mapping_gap_requests(manifest)


def test_real_al02_manifest_preserves_requested_decay_value() -> None:
    manifest_path = _REPO_ROOT / "output" / "al16" / "AL02_LOCK_RYTM_manifest.json"
    manifest = cast(
        dict[str, object],
        json.loads(manifest_path.read_text(encoding="utf-8")),
    )

    requests = {
        request.semantic_path: request.requested_semantic_value
        for request in load_mapping_gap_requests(manifest)
    }

    assert requests["tracks.1.source.dec"] == "53"
    assert requests["tracks.1.machine"] == "BD Classic"


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


def test_all_gap_locations_match_explicit_review_oracle() -> None:
    recipe = _recipe()

    actual = {}
    for path in AL16_RYTM_MAPPING_GAP_PATHS:
        location = candidate_location_for_path(path, recipe)
        actual[path] = (
            location.status,
            location.unpacked_offset,
            location.width,
            location.source,
        )

    assert actual == _EXPECTED_GAP_LOCATIONS


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
    for unpacked_offset, value in (
        (170, 1),
        (78, 53),
        (460, 56),
        (886, 41),
    ):
        configured[unpacked_offset] = value
    configured[10] = 99

    report = analyze_mapping_capture(
        reference_frame=_frame(bytes(RYTM_KIT_RAW_SIZE)),
        configured_frame=_frame(bytes(configured)),
        recipe=recipe,
        requests=_requests(paths),
        provenance=_provenance(),
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
    assert report.mapping_gap_count == 6
    assert report.candidate_changed_count == 4
    assert report.unresolved_location_count == 2
    assert {
        observation.semantic_path: observation.requested_semantic_value
        for observation in report.candidate_observations
    } == {
        "destination_slot": "127",
        "tracks.1.machine": "BD Classic",
        "tracks.1.source.dec": "53",
        "tracks.3.amp.vol": "requested:tracks.3.amp.vol",
        "tracks.6.source.target_note": "requested:tracks.6.source.target_note",
        "tracks.9.source.decay": "requested:tracks.9.source.decay",
    }
    assert {
        observation.semantic_path: observation.location.unpacked_offset
        for observation in report.candidate_observations
    } == {
        "destination_slot": None,
        "tracks.1.machine": 170,
        "tracks.1.source.dec": 78,
        "tracks.3.amp.vol": 460,
        "tracks.6.source.target_note": 886,
        "tracks.9.source.decay": None,
    }


def test_offline_capture_analyzer_reports_unchanged_candidates() -> None:
    frame = _frame(bytes(RYTM_KIT_RAW_SIZE))

    report = analyze_mapping_capture(
        reference_frame=frame,
        configured_frame=frame,
        recipe=_recipe(),
        requests=_requests(("tracks.1.source.dec",)),
        provenance=_provenance(),
    )

    assert report.candidate_observations[0].status == "candidate_unchanged"
    assert report.changed_unpacked_offsets == ()


def test_file_analyzer_and_renderer_are_deterministic(tmp_path: Path) -> None:
    frame = _frame(bytes(RYTM_KIT_RAW_SIZE))
    reference_path, configured_path, recipe_path, manifest_path = _write_bound_inputs(
        tmp_path,
        reference_frame=frame,
        configured_frame=frame,
        semantic_paths=("tracks.1.machine",),
    )

    first = analyze_mapping_capture_files(
        reference_path=reference_path,
        configured_path=configured_path,
        recipe_path=recipe_path,
        gap_manifest_path=manifest_path,
    )
    second = analyze_mapping_capture_files(
        reference_path=reference_path,
        configured_path=configured_path,
        recipe_path=recipe_path,
        gap_manifest_path=manifest_path,
    )

    assert first == second
    assert render_mapping_capture_report(first) == render_mapping_capture_report(second)
    rendered = render_mapping_capture_report(first)
    assert '"schema_version": 1' in rendered
    assert '"promotion_status": "review_required"' in rendered
    assert '"requested_semantic_value": "BD Classic"' in rendered
    assert '"recipe_artifact": "recipe.yaml"' in rendered
    assert f'"recipe_sha256": "{hashlib.sha256(recipe_path.read_bytes()).hexdigest()}"' in rendered


def test_file_analyzer_rejects_recipe_and_reference_identity_drift(tmp_path: Path) -> None:
    frame = _frame(bytes(RYTM_KIT_RAW_SIZE))
    reference_path, configured_path, recipe_path, manifest_path = _write_bound_inputs(
        tmp_path,
        reference_frame=frame,
        configured_frame=frame,
        semantic_paths=("tracks.1.machine",),
    )
    recipe_path.write_text('{"tracks": {}}', encoding="utf-8")

    with pytest.raises(ValueError, match="recipe does not match"):
        analyze_mapping_capture_files(
            reference_path=reference_path,
            configured_path=configured_path,
            recipe_path=recipe_path,
            gap_manifest_path=manifest_path,
        )

    recipe_path.write_bytes(_RECIPE_PATH.read_bytes())
    reference_path.write_bytes(_frame(bytes([1]) + bytes(RYTM_KIT_RAW_SIZE - 1)))
    with pytest.raises(ValueError, match="reference does not match"):
        analyze_mapping_capture_files(
            reference_path=reference_path,
            configured_path=configured_path,
            recipe_path=recipe_path,
            gap_manifest_path=manifest_path,
        )


@pytest.mark.parametrize(
    ("manifest_payload", "message"),
    [
        (b"{", "must be valid UTF-8 JSON"),
        (b"[]", "must be a JSON object"),
    ],
)
def test_file_analyzer_rejects_malformed_manifest_documents(
    tmp_path: Path,
    manifest_payload: bytes,
    message: str,
) -> None:
    frame = _frame(bytes(RYTM_KIT_RAW_SIZE))
    reference_path, configured_path, recipe_path, manifest_path = _write_bound_inputs(
        tmp_path,
        reference_frame=frame,
        configured_frame=frame,
        semantic_paths=("tracks.1.machine",),
    )
    manifest_path.write_bytes(manifest_payload)

    with pytest.raises(ValueError, match=message):
        analyze_mapping_capture_files(
            reference_path=reference_path,
            configured_path=configured_path,
            recipe_path=recipe_path,
            gap_manifest_path=manifest_path,
        )


@pytest.mark.parametrize(
    ("manifest_update", "message"),
    [
        (
            {"deterministic_recipe_identifier": "wrong-recipe"},
            "deterministic recipe identifier does not match",
        ),
        ({"recipe_sha256": None}, "recipe_sha256 must be a string"),
    ],
)
def test_file_analyzer_rejects_invalid_manifest_identity_fields(
    tmp_path: Path,
    manifest_update: dict[str, object],
    message: str,
) -> None:
    frame = _frame(bytes(RYTM_KIT_RAW_SIZE))
    reference_path, configured_path, recipe_path, manifest_path = _write_bound_inputs(
        tmp_path,
        reference_frame=frame,
        configured_frame=frame,
        semantic_paths=("tracks.1.machine",),
    )
    manifest = cast(dict[str, object], json.loads(manifest_path.read_text(encoding="utf-8")))
    manifest.update(manifest_update)
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    with pytest.raises(ValueError, match=message):
        analyze_mapping_capture_files(
            reference_path=reference_path,
            configured_path=configured_path,
            recipe_path=recipe_path,
            gap_manifest_path=manifest_path,
        )


def test_destination_slot_proof_reports_exact_header_byte() -> None:
    reference_header = ANALOG_RYTM_SAVED_KIT_TEST_HEADER
    configured_header = reference_header[:-1] + bytes((7,))
    raw = bytes(RYTM_KIT_RAW_SIZE)

    report = analyze_mapping_capture(
        reference_frame=encode_analog_rytm_saved_kit_frame(reference_header, raw),
        configured_frame=encode_analog_rytm_saved_kit_frame(configured_header, raw),
        recipe=_recipe(),
        requests=_requests(("destination_slot",)),
        provenance=_provenance(),
    )

    assert report.changed_header_indices == (8,)
    assert report.reference_header[8] == 0
    assert report.configured_header[8] == 7
    assert report.changed_unpacked_offsets == ()


def test_capture_analyzer_rejects_candidate_locations_beyond_saved_kit_bounds(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    frame = _frame(bytes(RYTM_KIT_RAW_SIZE))
    monkeypatch.setattr(
        mapping_closure,
        "candidate_location_for_path",
        lambda semantic_path, _recipe_value: CandidateLocation(
            semantic_path=semantic_path,
            unpacked_offset=RYTM_KIT_RAW_SIZE,
            width=1,
            status="candidate_location",
            source="test-only out-of-bounds location",
        ),
    )

    with pytest.raises(ValueError, match="exceeds decoded saved-kit bounds"):
        analyze_mapping_capture(
            reference_frame=frame,
            configured_frame=frame,
            recipe=_recipe(),
            requests=_requests(("tracks.1.source.dec",)),
            provenance=_provenance(),
        )


def test_capture_analyzer_rejects_invalid_saved_kit_frames() -> None:
    valid = _frame(bytes(RYTM_KIT_RAW_SIZE))

    with pytest.raises(AnalogRytmSavedKitCodecError, match="frame length"):
        analyze_mapping_capture(
            reference_frame=valid[:-1],
            configured_frame=valid,
            recipe=_recipe(),
            requests=_requests(("tracks.1.machine",)),
            provenance=_provenance(),
        )
