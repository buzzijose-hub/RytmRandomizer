"""Current code must replay immutable sessions created by actual e30cc84c code.

These fixtures are synthetic software witnesses, never hardware authority.
No current generator creates the expected sessions or rewrites the goldens.
"""

from __future__ import annotations

import json
import shutil
from collections.abc import Iterator
from pathlib import Path
from threading import Event
from typing import Final, NoReturn

import pytest

from rytm_randomizer.cockpit.export.reference_sound_candidates import list_reference_sound_controls
from rytm_randomizer.cockpit.export.reference_sound_display import (
    reference_sound_operator_control,
    reference_sound_operator_session,
)
from rytm_randomizer.cockpit.export.reference_sound_session import ReferenceSoundWorkspace
from rytm_randomizer.cockpit.export.reference_sound_store import (
    REFERENCE_SOUND_SCHEMA,
    ReferenceSoundStore,
    reference_sound_digest,
    reference_sound_json,
)
from rytm_randomizer.devices import get_analog_four_native_field_capability
from rytm_randomizer.devices.strategies.analog_four_saved_kit_codec import (
    decode_analog_four_saved_kit_payload,
    encode_analog_four_saved_kit_payload,
)

pytestmark = [pytest.mark.fast, pytest.mark.usefixtures("offline_hardware_denied")]

_FIXTURES: Final[Path] = Path(__file__).parents[1] / "fixtures/native_representation"
_SOURCE_COMMIT: Final[str] = "e30cc84cbb9c745654632f71ac827e05007ce320"
_ORIGINAL_SHA: Final[str] = "50c753f3a2acd73ca77e2930e9b9658ea62bbe51f7cb9f7644e6f8ff2689cc5e"
_PROVENANCE_SHA: Final[dict[str, str]] = {
    "mutable_16257": "3f25512081e48e67475782586688671e09fe5007beae70b15dba5febb0123606",
    "protected_32513": "6e8c03d0e0e64e1bb47ac74dc49c6933b9ac659e59c576f5879629e8ea1e49f5",
}


def _files(directory: Path) -> dict[str, bytes]:
    return {
        path.relative_to(directory).as_posix(): path.read_bytes()
        for path in directory.rglob("*")
        if path.is_file() and path.name != ".sound-publication.lock"
    }


def _forbidden_analysis(_path: Path, _cancel: Event) -> NoReturn:
    pytest.fail("An old retained session must replay without an analyzer or audio worker")


@pytest.fixture(params=tuple(_PROVENANCE_SHA))
def legacy_session(request: pytest.FixtureRequest, tmp_path: Path) -> Iterator[tuple]:
    directory = _FIXTURES / f"legacy_v1_e30_{request.param}"
    receipt_bytes = (directory / "provenance.json").read_bytes()
    assert reference_sound_digest(receipt_bytes) == _PROVENANCE_SHA[request.param]
    receipt = json.loads(receipt_bytes)
    assert receipt["source_commit"] == _SOURCE_COMMIT
    assert receipt["physical_validation"] is receipt["hardware_authority"] is False
    assert receipt["all_loaded_application_modules_verified_against_git"] == 147
    actual = {
        name: reference_sound_digest(value)
        for name, value in _files(directory).items()
        if name not in ("provenance.json", "README.md")
    }
    assert actual == receipt["artifact_sha256"]
    assert receipt["original_source"] == {"file": "a4_init_retained.syx", "sha256": _ORIGINAL_SHA}
    assert (
        reference_sound_digest((_FIXTURES / "a4_init_retained.syx").read_bytes()) == _ORIGINAL_SHA
    )
    assert receipt["target"] == 1 and receipt["response_kind"] == 0x52
    assert receipt["parameters"] == ["filter1_frequency"]
    assert receipt["locks"] == [] and receipt["strength"] == 0.5
    assert len(receipt["candidate_ids"]) == len(set(receipt["candidate_ids"])) == 8
    frozen = _files(directory)
    store = ReferenceSoundStore(tmp_path / "copied-old-store")
    shutil.copytree(directory / "store", store.directory)
    manifest = json.loads(
        (directory / "store" / f"{receipt['session_id']}.sound.json").read_bytes()
    )
    manifest.pop("content_sha256")
    workspace = ReferenceSoundWorkspace(store, analyzer=_forbidden_analysis)
    yield directory, receipt, manifest, workspace
    assert _files(directory) == frozen


def test_prechange_sessions_reopen_exact_candidates_without_analysis_or_rewrites(
    legacy_session: tuple,
) -> None:
    directory, receipt, expected, workspace = legacy_session
    before = _files(workspace.store.directory)
    reopened = workspace.reopen(receipt["session_id"])
    assert expected["schema_version"] == 1
    assert reopened == {**expected, "schema_version": REFERENCE_SOUND_SCHEMA}
    assert reopened["selected_candidate_id"] == receipt["favorite_candidate_id"]
    assert reopened["favorites"] == [receipt["favorite_candidate_id"]]
    assert [candidate["candidate_id"] for candidate in reopened["candidates"]] == receipt[
        "candidate_ids"
    ]
    for saved in expected["candidates"]:
        candidate = workspace.candidate(receipt["session_id"], saved["candidate_id"])
        assert reference_sound_json(candidate.to_dict()) == reference_sound_json(saved)
        assert (
            candidate.frame == (directory / "store" / f"{saved['frame_sha256']}.syx").read_bytes()
        )
        assert candidate.source_sha256 == receipt["source_sha256"]
        assert candidate.output_authority == "local-file-only"
        assert candidate.hardware_send_validated is False
        if receipt["source_native"] == 32513:
            assert saved["changes"] == []
            assert (
                "filter1_frequency preserved: source_value_outside_established_domain."
                in saved["limitations"]
            )
            assert saved["frame_sha256"] == receipt["source_sha256"]
        else:
            for change in saved["changes"]:
                assert change["source_value"] == 16257
                assert change["source_display"] == "63.50390625"
                assert change["offsets"] == [128, 129]
    assert _files(workspace.store.directory) == before


def test_prechange_selection_favorites_and_all_scratch_exports_preserve_exact_bytes(
    legacy_session: tuple,
) -> None:
    directory, receipt, expected, workspace = legacy_session
    before = _files(workspace.store.directory)
    session_id = receipt["session_id"]
    first, second = receipt["candidate_ids"][:2]
    current = {**expected, "schema_version": REFERENCE_SOUND_SCHEMA}
    assert workspace.select(session_id, first, favorite=True) == current
    changed = workspace.select(session_id, second, favorite=True)
    assert changed["selected_candidate_id"] == second
    assert changed["favorites"] == sorted((first, second))
    workspace.select(session_id, second, favorite=False)
    assert workspace.select(session_id, first) == current
    for candidate_id in receipt["candidate_ids"]:
        exported = workspace.export_patch(session_id, candidate_id, receipt["export_slot"])
        assert exported == (directory / "exports" / f"{candidate_id}.syx").read_bytes()
        decoded = decode_analog_four_saved_kit_payload(exported[1:-1], require_trailer=True)
        assert decoded.prefix[5] == 0x52 and decoded.prefix[-1] == 18
        assert (
            encode_analog_four_saved_kit_payload(decoded.prefix, decoded.unpacked).payload
            == exported[1:-1]
        )
        candidate = workspace.candidate(session_id, candidate_id)
        assert (
            decoded.unpacked
            == decode_analog_four_saved_kit_payload(
                candidate.frame[1:-1], require_trailer=True
            ).unpacked
        )
    manifest_name = f"{session_id}.sound.json"
    migrated = {**current, "content_sha256": reference_sound_digest(reference_sound_json(current))}
    assert _files(workspace.store.directory) == {
        **before,
        manifest_name: reference_sound_json(migrated),
    }


def test_prechange_native_scope_and_display_projection_keep_legacy_replay_separate(
    legacy_session: tuple,
) -> None:
    directory, receipt, expected, workspace = legacy_session
    source = (directory / "store" / f"{receipt['source_sha256']}.syx").read_bytes()
    cell = (
        get_analog_four_native_field_capability()
        .read_native_fields(source)
        .value("filter1_frequency", 1)
    )
    control = next(
        item
        for item in list_reference_sound_controls(source, "analog_four_mk2", 1)
        if item.parameter == "filter1_frequency"
    )
    current = json.loads(reference_sound_json(control.to_dict()))
    # Legal passive recognition of the protected value is additive; its old
    # unavailable display is not a persisted candidate label or mutation grant.
    for key in receipt["source_control"]:
        if key != "source_display":
            assert current[key] == receipt["source_control"][key]
    assert cell.encoded_native == receipt["source_native"]
    if receipt["source_native"] == 16257:
        assert cell.mutable is True and cell.domain is not None
        assert (cell.domain.minimum, cell.domain.maximum, cell.domain.quantum) == (0, 32512, 1)
        assert cell.screen_value == receipt["source_control"]["source_display"] == "63.50390625"
        assert cell.protection_reason is None
    else:
        assert cell.mutable is False and cell.domain is None
        assert receipt["source_control"]["source_display"] is None
        assert cell.protection_reason == "source_value_outside_established_domain"
    projected = reference_sound_operator_control(control)
    assert projected["source_value"] == receipt["source_native"]
    assert projected["source_display"] == (
        "63.50" if receipt["source_native"] == 16257 else "127.00"
    )
    assert projected["send_supported"] is False
    view = reference_sound_operator_session(workspace.reopen(receipt["session_id"]))
    assert view["favorites"] == expected["favorites"]
    assert [item["candidate_id"] for item in view["candidates"]] == receipt["candidate_ids"]
    for shown, saved in zip(view["candidates"], expected["candidates"], strict=True):
        assert shown["frame_sha256"] == saved["frame_sha256"]
        assert shown["limitations"] == saved["limitations"]
        for displayed, old in zip(shown["changes"], saved["changes"], strict=True):
            assert displayed["source_value"] == old["source_value"]
            assert displayed["rendered_value"] == old["rendered_value"]
            assert displayed["source_display"] == "63.50"
            assert old["source_display"] == "63.50390625"
    assert workspace.reopen(receipt["session_id"]) == {
        **expected,
        "schema_version": REFERENCE_SOUND_SCHEMA,
    }
