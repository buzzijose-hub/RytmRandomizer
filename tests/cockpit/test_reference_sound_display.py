"""Operator labels must not mutate exact native identities or v1 replay records."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import replace
from pathlib import Path
from threading import Event

import pytest
from cockpit.conftest import make_reference_pcm

from rytm_randomizer.cockpit.export.reference_sound_candidates import (
    ReferenceSoundControl,
    list_reference_sound_controls,
    render_reference_sound_candidates,
    render_refined_reference_sound_candidate,
)
from rytm_randomizer.cockpit.export.reference_sound_display import (
    reference_sound_operator_control,
    reference_sound_operator_session,
)
from rytm_randomizer.cockpit.export.reference_sound_session import ReferenceSoundWorkspace
from rytm_randomizer.devices.strategies.analog_four_saved_kit_codec import (
    decode_analog_four_saved_kit_payload,
    encode_analog_four_saved_kit_payload,
)
from rytm_randomizer.observability.errors import BoundaryError

pytestmark = pytest.mark.fast


def _label_test_source(native: int, *, working: bool = False) -> bytes:
    original = (
        Path(__file__).parents[1] / "fixtures/native_representation/a4_init_retained.syx"
    ).read_bytes()
    source = decode_analog_four_saved_kit_payload(original[1:-1], require_trailer=True)
    body = bytearray(source.unpacked)
    body[128:130] = native.to_bytes(2, "big")
    header = bytearray(source.prefix)
    header[5] = 0x58 if working else 0x52
    encoded = encode_analog_four_saved_kit_payload(bytes(header), bytes(body))
    return b"\xf0" + encoded.payload + b"\xf7"


@pytest.mark.parametrize("native", [32513, 32766])
def test_larger_legal_f1_sources_keep_legacy_preservation_reason_and_favorite_replay(
    reference_sound_workspace: ReferenceSoundWorkspace, native: int
) -> None:
    workspace = reference_sound_workspace
    source = _label_test_source(native)
    imported = workspace.import_reference(make_reference_pcm(), "Legacy protected F1")
    retained = workspace.commit(
        workspace.generate(
            imported["session_id"],
            source_frame=source,
            device_id="analog_four_mk2",
            target=1,
            parameters=("filter1_frequency",),
            locks=(),
            strength=0.5,
            cancel=Event(),
        )
    )
    candidate = retained["candidates"][0]
    assert (
        "filter1_frequency preserved: source_value_outside_established_domain."
        in candidate["limitations"]
    )
    assert candidate["changes"] == []
    selected = workspace.select(retained["session_id"], candidate["candidate_id"], favorite=True)
    restarted = ReferenceSoundWorkspace(workspace.store, analyzer=workspace.analyzer)
    assert restarted.reopen(retained["session_id"]) == selected
    assert restarted.candidate(retained["session_id"], candidate["candidate_id"]).frame == source
    exported = restarted.export_patch(retained["session_id"], candidate["candidate_id"], 18)
    assert (
        decode_analog_four_saved_kit_payload(exported[1:-1], require_trailer=True).unpacked
        == decode_analog_four_saved_kit_payload(source[1:-1], require_trailer=True).unpacked
    )
    assert workspace.reopen(retained["session_id"]) == selected


def test_working_source_inspection_is_read_only_and_generation_refuses_before_analysis(
    reference_sound_workspace: ReferenceSoundWorkspace, audio_patch_dna_analysis, monkeypatch
) -> None:
    workspace = reference_sound_workspace
    source = _label_test_source(16257, working=True)
    controls = list_reference_sound_controls(source, "analog_four_mk2", 1)
    assert all(not control.mutable for control in controls)
    assert all("working_kit_freshness_unverified" in control.reasons for control in controls)
    imported = workspace.import_reference(make_reference_pcm(), "Working inspection")
    before = {
        path.name: path.read_bytes()
        for path in workspace.store.directory.iterdir()
        if path.is_file()
    }

    def forbidden_analysis(*args):
        pytest.fail("read-only source must be refused before audio analysis")

    monkeypatch.setattr(workspace, "analyzer", forbidden_analysis)
    calls = (
        lambda: workspace.generate(
            imported["session_id"],
            source_frame=source,
            device_id="analog_four_mk2",
            target=1,
            parameters=(),
            locks=(),
            strength=0,
            cancel=Event(),
        ),
        lambda: render_reference_sound_candidates(
            source, "analog_four_mk2", 1, audio_patch_dna_analysis, (), (), 0
        ),
        lambda: render_refined_reference_sound_candidate(
            source, "analog_four_mk2", 1, audio_patch_dna_analysis, (), (), 0
        ),
    )
    for call in calls:
        with pytest.raises(BoundaryError) as failure:
            call()
        assert failure.value.context["error_code"] == "working_kit_read_only"
        assert "indexed" in str(failure.value)
    assert {
        path.name: path.read_bytes()
        for path in workspace.store.directory.iterdir()
        if path.is_file()
    } == before
    assert workspace.reopen(imported["session_id"]) == imported


@pytest.mark.parametrize(
    "native,label,wire,lost",
    [(1, "0.00", 0, 1), (2, "0.00", 1, 0), (3, "0.01", 1, 1), (32766, "127.99", 16383, 0)],
)
def test_operator_control_separates_colliding_labels_from_exact_words_and_wire_loss(
    native: int, label: str, wire: int, lost: int
) -> None:
    control = ReferenceSoundControl(
        "filter1_frequency", native, "legacy exact coordinate", "q8.8", None, (128, 129), ()
    )
    before = control.to_dict()
    result = reference_sound_operator_control(control)
    assert result.keys() == before.keys()
    assert result["source_value"] == native
    assert result["source_display"] == label
    assert f"NRPN14={wire}" in result["units"]
    assert f"lost native bit={lost}" in result["units"]
    assert result["send_supported"] is False
    assert control.to_dict() == before
    other = replace(control, parameter="filter2_frequency")
    assert reference_sound_operator_control(other) == other.to_dict()


def test_operator_session_view_preserves_stored_labels_favorites_and_exact_restart_replay(
    reference_sound_workspace: ReferenceSoundWorkspace,
    reference_sound_source: tuple[bytes, str, int, tuple[str, ...]],
) -> None:
    workspace = reference_sound_workspace
    frame, device, target, parameters = reference_sound_source
    imported = workspace.import_reference(make_reference_pcm(), "Legacy representation proof")
    retained = workspace.commit(
        workspace.generate(
            imported["session_id"],
            source_frame=frame,
            device_id=device,
            target=target,
            parameters=parameters,
            locks=(),
            strength=0.5,
            cancel=Event(),
        )
    )
    selected = retained["candidates"][0]
    retained = workspace.select(retained["session_id"], selected["candidate_id"], favorite=True)
    original = deepcopy(retained)
    before = workspace.candidate(retained["session_id"], selected["candidate_id"]).frame
    view = reference_sound_operator_session(retained)
    assert view.keys() == original.keys()
    assert view["session_id"] == original["session_id"]
    assert view["favorites"] == original["favorites"]
    for observed, saved in zip(view["candidates"], original["candidates"], strict=True):
        assert observed["candidate_id"] == saved["candidate_id"]
        assert observed["source_sha256"] == saved["source_sha256"]
        assert observed["frame_sha256"] == saved["frame_sha256"]
        for actual, old in zip(observed["changes"], saved["changes"], strict=True):
            assert actual["source_value"] == old["source_value"]
            assert actual["rendered_value"] == old["rendered_value"]
            assert actual["offsets"] == old["offsets"]
            if actual["parameter"] == "filter1_frequency":
                hundredths = actual["rendered_value"] * 100 // 256
                assert actual["rendered_display"] == f"{hundredths // 100}.{hundredths % 100:02d}"
                assert "output unverified" in actual["units"]
            else:
                assert actual == old
    assert retained == original
    restarted = ReferenceSoundWorkspace(workspace.store, analyzer=workspace.analyzer)
    assert restarted.reopen(retained["session_id"]) == original
    assert restarted.candidate(retained["session_id"], selected["candidate_id"]).frame == before
