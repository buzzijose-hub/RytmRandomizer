"""Working-RAM evidence cannot become saved-source or rehearsal authority."""

from __future__ import annotations

from dataclasses import replace
from datetime import timedelta
from hashlib import sha256
from pathlib import Path

import pytest

from rytm_randomizer.cockpit.capture import ANALOG_FOUR_DEVICE_ID, decode_kit_capture_frame
from rytm_randomizer.cockpit.show_bank.forge import (
    analog_four_capture_semantic_fingerprint,
    capture_reference,
)
from rytm_randomizer.cockpit.show_bank.store import validate_show_bank_capture_frame
from rytm_randomizer.observability.errors import DataError

from .conftest import build_show_bank_harness

pytestmark = pytest.mark.fast


def _working_capture(indexed):
    frame = bytearray(indexed.frame)
    frame[6] = 0x58
    actual = decode_kit_capture_frame(ANALOG_FOUR_DEVICE_ID, bytes(frame))
    assert actual.fingerprint == indexed.fingerprint
    assert actual.snapshot_layout == "working_kit"
    # Even misleading caller metadata cannot conceal the authoritative frame kind.
    return replace(actual, captured_at=indexed.captured_at, snapshot_layout="saved_kit")


def _files(root: Path) -> dict[str, bytes]:
    return {
        str(path.relative_to(root)): path.read_bytes() for path in root.rglob("*") if path.is_file()
    }


def test_working_capture_cannot_be_adopted_or_imported_as_an_indexed_source(tmp_path: Path) -> None:
    harness = build_show_bank_harness(tmp_path)
    workspace = harness.workspace
    bank = workspace.bank(harness.bank_id)
    working = _working_capture(harness.analog_four)
    before = _files(harness.store.root)
    with pytest.raises(ValueError, match="passive evidence"):
        capture_reference(working, hardware_slot=21, snapshot_id=None)
    with pytest.raises(ValueError, match="passive evidence"):
        workspace.adopt_sources(
            harness.bank_id,
            bank.revision,
            captures={**harness.captures, ANALOG_FOUR_DEVICE_ID: working},
            rytm_fingerprint=harness.rytm.fingerprint,
            analog_four_fingerprint=working.fingerprint,
            rytm_slot=20,
            analog_four_slot=21,
        )
    original = bank.entry(harness.entry_id).analog_four_source
    claimed = replace(
        original,
        sysex=replace(
            original.sysex,
            frame_sha256=sha256(working.frame).hexdigest(),
            frame_bytes=len(working.frame),
        ),
    )
    with pytest.raises(DataError) as failure:
        validate_show_bank_capture_frame(claimed, working.frame)
    assert failure.value.context["category"] == "framing"
    assert _files(harness.store.root) == before
    assert workspace.bank(harness.bank_id) == bank


def test_working_capture_cannot_verify_a_fully_locked_favorite_or_preflight(tmp_path: Path) -> None:
    harness = build_show_bank_harness(tmp_path)
    workspace = harness.workspace
    (candidate,) = workspace.generate_candidates(
        harness.bank_id,
        harness.entry_id,
        workspace.bank(harness.bank_id).revision,
        profile=harness.profile,
        depth_preset="small",
        depth=0,
        seed=91,
        candidate_count=1,
        rytm_targets=(),
        rytm_locks=tuple(range(1, 13)),
        analog_four_targets=(),
        analog_four_locks=(1, 2, 3, 4),
    )
    assert candidate.analog_four_candidate.values == ()
    workspace.mark_favorite(
        harness.bank_id,
        harness.entry_id,
        candidate.candidate_id,
        workspace.bank(harness.bank_id).revision,
    )
    for device in ("analog_rytm_mk2", "analog_four_mk2"):
        workspace.attest_saved(
            harness.bank_id,
            harness.entry_id,
            workspace.bank(harness.bank_id).revision,
            device_id=device,
            hardware_slot=64,
        )
    harness.clock.current += timedelta(minutes=2)
    indexed = {
        device: replace(capture, captured_at=harness.clock.current - timedelta(minutes=1))
        for device, capture in harness.captures.items()
    }
    working = _working_capture(indexed[ANALOG_FOUR_DEVICE_ID])
    before = _files(harness.store.root)
    bank = workspace.bank(harness.bank_id)
    with pytest.raises(ValueError, match="passive evidence"):
        analog_four_capture_semantic_fingerprint(working, candidate.analog_four_candidate)
    with pytest.raises(ValueError, match="passive evidence"):
        workspace.verify_recaptures(
            harness.bank_id,
            harness.entry_id,
            bank.revision,
            captures={**indexed, ANALOG_FOUR_DEVICE_ID: working},
        )
    assert workspace.bank(harness.bank_id) == bank
    assert _files(harness.store.root) == before
    verified = workspace.verify_recaptures(
        harness.bank_id, harness.entry_id, bank.revision, captures=indexed
    )
    assert verified.status == "verified"
    harness.clock.current += timedelta(minutes=2)
    fresh = {
        device: replace(capture, captured_at=harness.clock.current - timedelta(minutes=1))
        for device, capture in indexed.items()
    }
    bank = workspace.bank(harness.bank_id)
    before = _files(harness.store.root)
    with pytest.raises(ValueError, match="passive evidence"):
        workspace.run_preflight(
            harness.bank_id,
            harness.entry_id,
            bank.revision,
            captures={
                **fresh,
                ANALOG_FOUR_DEVICE_ID: _working_capture(fresh[ANALOG_FOUR_DEVICE_ID]),
            },
        )
    assert workspace.bank(harness.bank_id) == bank
    assert _files(harness.store.root) == before
