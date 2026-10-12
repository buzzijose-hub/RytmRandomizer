"""Operator labels must not mutate exact native identities or v1 replay records."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import replace
from threading import Event

import pytest
from cockpit.conftest import make_reference_pcm

from rytm_randomizer.cockpit.export.reference_sound_candidates import ReferenceSoundControl
from rytm_randomizer.cockpit.export.reference_sound_display import (
    reference_sound_operator_control,
    reference_sound_operator_session,
)
from rytm_randomizer.cockpit.export.reference_sound_session import ReferenceSoundWorkspace

pytestmark = pytest.mark.fast


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
