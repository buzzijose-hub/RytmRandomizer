"""Real-codec helpers for Show Kit Forge capture-boundary tests."""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime

from rytm_randomizer.cockpit.capture import (
    ANALOG_RYTM_DEVICE_ID,
    KitCaptureResult,
    cockpit_snapshot_from_rytm_capture,
    decode_kit_capture_frame,
)
from rytm_randomizer.cockpit.data.mutation_candidate import MutationCandidate
from rytm_randomizer.cockpit.data.rytm_parameter_map import cockpit_parameter_mapping
from rytm_randomizer.data.analog_rytm_kit_layout import (
    RYTM_SOUND_FIELD_BY_NRPN_LSB,
    analog_rytm_track_sound_offset,
)
from rytm_randomizer.devices.strategies.analog_rytm_saved_kit_codec import (
    decode_analog_rytm_saved_kit_frame,
    encode_analog_rytm_saved_kit_frame,
)


def capture_matching_rytm_candidate(
    source: KitCaptureResult,
    candidate: MutationCandidate,
    *,
    captured_at: datetime,
) -> KitCaptureResult:
    """Render one candidate into a valid saved-KIT frame, then publicly decode it."""

    source_snapshot = cockpit_snapshot_from_rytm_capture(source)
    source_pads = {pad.pad_id: pad for pad in source_snapshot.pads}
    decoded = decode_analog_rytm_saved_kit_frame(source.frame)
    rendered = bytearray(decoded.unpacked)

    for delta in candidate.pad_deltas:
        machine = source_pads[delta.pad_id].machine
        for parameter, value in delta.proposed_params.items():
            mapping = cockpit_parameter_mapping(machine, parameter)
            if mapping is None or mapping.nrpn_lsb is None:
                raise AssertionError(
                    f"candidate parameter lost its saved-KIT mapping: {machine}:{parameter}"
                )
            field = RYTM_SOUND_FIELD_BY_NRPN_LSB.get(mapping.nrpn_lsb)
            if field is None:
                raise AssertionError(
                    f"candidate parameter lost its native offset: {machine}:{parameter}"
                )
            rendered[analog_rytm_track_sound_offset(delta.pad_id, field.sound_offset)] = value

    frame = encode_analog_rytm_saved_kit_frame(decoded.header, bytes(rendered))
    return replace(
        decode_kit_capture_frame(ANALOG_RYTM_DEVICE_ID, frame),
        captured_at=captured_at,
    )


__all__ = ["capture_matching_rytm_candidate"]
