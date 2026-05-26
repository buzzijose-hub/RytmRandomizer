"""Mock-only outbound Rytm channel matrix tests.

These tests prove the low-level CC sender can represent channels 0..11 without
opening real MIDI ports. They do not validate hardware receive behavior.
"""

from __future__ import annotations

from collections.abc import Callable

import pytest

pytestmark = pytest.mark.fast


def test_send_cc_records_track_channel_matrix_with_mock_sender(
    no_sleep: Callable[[float], None],
) -> None:
    from rytm_randomizer.midi_io import send_cc
    from rytm_randomizer.mock_midi import MockMidiSender

    for channel in range(12):
        sender = MockMidiSender()

        send_cc(sender, 17, 64, channel=channel, sleep=no_sleep)

        assert len(sender.messages) == 1
        message = sender.messages[0]
        assert message.type == "control_change"
        assert message.channel == channel
        assert message.control == 17
        assert message.value == 64


def test_send_cc_mock_channel_matrix_imports_no_real_midi_library(
    no_sleep: Callable[[float], None],
) -> None:
    import sys

    sys.modules.pop("mido", None)

    from rytm_randomizer.midi_io import send_cc
    from rytm_randomizer.mock_midi import MockMidiSender

    sender = MockMidiSender()
    send_cc(sender, 17, 64, channel=11, sleep=no_sleep)

    assert "mido" not in sys.modules
