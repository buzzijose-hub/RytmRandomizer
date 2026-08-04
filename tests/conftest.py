"""Shared test fixtures -- Gate 11 single source of truth.

Per docs/PLAN_REQUIREMENTS.md Gate 11, fixtures used in >1 test file live
here. ``RecordingOut`` / ``_FakeMessage`` / ``_install_fake_mido`` / ``_no_sleep``
were previously duplicated across ``tests/test_engines_pad{1..4}.py``,
``tests/test_group_runner.py``, ``tests/test_scene_runner.py``,
``tests/test_midi_io.py``, ``tests/test_randomization.py`` (~260 LOC of
copy-paste). This module replaces the canonical, byte-identical copies.

Two files keep NEAR-identical local copies of ``_FakeMessage`` (different
ctor signature) and are explicitly allow-listed:

* ``tests/test_guardrails_e2e.py``
* ``tests/test_midi_io.py``

``tests/test_mido_provider.py`` keeps its own ``_install_fake_mido`` with a
different signature.

Pytest auto-discovery: this file is at ``tests/conftest.py`` so every test
file under ``tests/`` automatically sees the fixtures named below
(``recording_out`` / ``fake_mido_session`` / ``no_sleep``). Classes
``RecordingOut`` and ``_FakeMessage`` are also exported at module scope so
tests that need to construct one mid-body can ``from conftest import
RecordingOut`` directly (pytest's prepend-import-mode puts ``tests/`` on
sys.path).
"""

from __future__ import annotations

import io
import logging
import sys
import types
from collections.abc import Iterator
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable

import pytest

if TYPE_CHECKING:
    from rytm_randomizer.devices.strategies.analog_four_saved_kit_writer import (
        AnalogFourSavedKitMutation,
    )
    from rytm_randomizer.style_analysis import FeatureReport


def analog_four_reference_feature_report(*, derived_at: str) -> FeatureReport:
    """Build the canonical 134-BPM feature report used across A4 tests."""

    from rytm_randomizer.guardrails.schema import Confidence, SourceType
    from rytm_randomizer.style_analysis import FeatureReport

    return FeatureReport(
        source_type=SourceType.SINGLE_TRACK,
        confidence=Confidence.HIGH,
        bpm=134.0,
        tempo_stability=0.91,
        kick_density=0.48,
        percussion_density=0.78,
        low_end_weight=0.42,
        spectral_brightness=0.63,
        texture_noise=0.34,
        energy_arc=(0.18, 0.34, 0.48, 0.72, 0.84, 0.78, 0.61, 0.4),
        content_hash="",
        derived_at=derived_at,
    )


def analog_four_saved_kit_mutation(
    track: int = 1,
    screen_value: str = "64",
    parameter: str = "Filter2 Resonance",
) -> AnalogFourSavedKitMutation:
    """Build one shared saved-kit mutation record for A4 tests."""

    from rytm_randomizer.devices.strategies.analog_four_saved_kit_writer import (
        AnalogFourSavedKitMutation,
    )

    return AnalogFourSavedKitMutation(
        parameter=parameter,
        track=track,
        screen_value=screen_value,
    )


ANALOG_RYTM_SAVED_KIT_TEST_HEADER = bytes((0x00, 0x20, 0x3C, 0x07, 0x00, 0x52, 0x01, 0x01, 0x00))


def analog_rytm_saved_kit_test_raw() -> bytes:
    """Build the deterministic unpacked Rytm body shared by codec tests."""

    from rytm_randomizer.data.analog_rytm_kit_layout import RYTM_KIT_RAW_SIZE

    return bytes(((index * 37) + 193) & 0xFF for index in range(RYTM_KIT_RAW_SIZE))


@pytest.fixture
def isolated_observability() -> Iterator[None]:
    """Reset A4 metrics and restore package logging after observability tests."""

    from rytm_randomizer.observability.logging import (
        PACKAGE_LOGGER_NAME,
        configure_logging,
    )
    from rytm_randomizer.observability.metrics import reset_metrics

    package_logger = logging.getLogger(PACKAGE_LOGGER_NAME)
    reset_metrics()
    configure_logging(stream=io.StringIO())
    try:
        yield
    finally:
        for handler in list(package_logger.handlers):
            package_logger.removeHandler(handler)
            handler.close()
        package_logger.addHandler(logging.NullHandler())
        package_logger.setLevel(logging.NOTSET)
        package_logger.propagate = False
        reset_metrics()


class _FakeMessage:
    """Records the same fields a ``mido.Message`` would expose.

    Verbatim from the pre-WS-M4 ``tests/test_engines_pad1.py:62-83`` definition.
    Two attribute spellings (``type`` and ``message_type``) are kept because
    different test files reach for different names; both point at the same
    string. Prefer ``type`` in new tests.

    ``__eq__`` compares (type, channel, control, value) — the four fields
    every engine test compares on. This matches the original per-test-file
    ``_FakeMessage`` behavior byte-identically so parity tests stay green
    after the conftest migration.
    """

    def __init__(self, message_type: str, **kwargs: Any) -> None:
        self.type = message_type
        self.message_type = message_type
        for name, value in kwargs.items():
            setattr(self, name, value)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, _FakeMessage):
            return NotImplemented
        return (
            self.type,
            getattr(self, "channel", None),
            getattr(self, "control", None),
            getattr(self, "value", None),
        ) == (
            other.type,
            getattr(other, "channel", None),
            getattr(other, "control", None),
            getattr(other, "value", None),
        )

    def __hash__(self) -> int:
        return hash(
            (
                self.type,
                getattr(self, "channel", None),
                getattr(self, "control", None),
                getattr(self, "value", None),
            )
        )

    def __repr__(self) -> str:  # pragma: no cover - debugging aid only
        return (
            f"_FakeMessage({self.type!r}, "
            f"channel={getattr(self, 'channel', None)}, "
            f"control={getattr(self, 'control', None)}, "
            f"value={getattr(self, 'value', None)})"
        )


class RecordingOut:
    """Minimal stand-in for a mido output port; records sent messages.

    Verbatim from the pre-WS-M4 ``tests/test_engines_pad1.py:95-102`` definition.
    """

    def __init__(self) -> None:
        self.sent: list[object] = []

    def send(self, message: object) -> None:
        self.sent.append(message)


def _install_fake_mido() -> types.ModuleType:
    """Install an inert fake ``mido`` so ``send_cc`` builds no real message.

    Module-level helper (not a fixture) so legacy call-site usage in
    ``tests/test_engines_pad{1..4}.py`` and friends continues to work
    after WS-M4 dedupe.

    .. warning::

        LEGACY COMPATIBILITY ONLY. This helper modifies ``sys.modules``
        in place and does **not** restore the prior ``mido`` entry on
        teardown. Tests that call it directly leak the fake into every
        subsequent test in the same pytest worker. **Prefer the
        :func:`fake_mido_session` pytest fixture below** -- it installs
        the same fake but restores ``sys.modules`` on test exit.

        This helper exists only because removing it would require a
        sweep of the ~5 remaining call sites in ``test_engines_pad*.py``
        and the existing ``_restore_sys_modules`` autouse fixtures in
        those files happen to clean up the leak by side effect. New
        tests should not add new calls; flagged as a follow-up sweep
        in the WS-M4 plan.
    """

    fake = types.ModuleType("mido")
    fake.Message = _FakeMessage  # type: ignore[attr-defined]
    sys.modules["mido"] = fake
    return fake


def _no_sleep(_seconds: float) -> None:
    """A no-op sleep substitute matching the engines' ``SleepFunc`` signature.

    Module-level helper so legacy positional usage (``sleep=_no_sleep``)
    continues to work after WS-M4 dedupe. New tests should prefer the
    ``no_sleep`` pytest fixture.
    """
    return None


def pack_elektron_7bit(unpacked: bytes) -> bytes:
    """Delegate shared fixtures to the production Elektron packer."""

    from rytm_randomizer.snapshot import pack_elektron_7bit as pack

    return pack(unpacked)


def analog_four_saved_kit_frame(
    *,
    name: bytes = b"KIT 1",
    unpacked_overrides: dict[int, int] | None = None,
    unpacked_size: int | None = None,
) -> bytes:
    """Build a framed A4 saved-kit fixture using the observed hardware layout."""

    from rytm_randomizer.devices.strategies.analog_four_offset_manifest import (
        A4_CHECKSUM_PACKED_OFFSET,
        A4_FAMILY_BYTE,
        A4_KIT_NAME_LENGTH,
        A4_KIT_NAME_OFFSET,
        A4_KIT_OBJECT_BYTE,
        A4_SAVED_KIT_UNPACKED_SIZE,
    )
    from rytm_randomizer.snapshot.envelope import ELEKTRON_MFR_ID

    unpacked = bytearray(A4_SAVED_KIT_UNPACKED_SIZE if unpacked_size is None else unpacked_size)
    unpacked[0:4] = bytes([A4_KIT_OBJECT_BYTE, 0x01, 0x01, 0x00])
    unpacked[A4_KIT_NAME_OFFSET : A4_KIT_NAME_OFFSET + A4_KIT_NAME_LENGTH] = name[
        :A4_KIT_NAME_LENGTH
    ].ljust(A4_KIT_NAME_LENGTH, b"\x00")
    for offset, value in (unpacked_overrides or {}).items():
        unpacked[offset] = value

    packed = pack_elektron_7bit(bytes(unpacked))
    checksum = sum(packed[A4_CHECKSUM_PACKED_OFFSET:]) & 0x3FFF
    trailer = bytes(
        [
            (checksum >> 7) & 0x7F,
            checksum & 0x7F,
            (len(packed) >> 7) & 0x7F,
            len(packed) & 0x7F,
        ]
    )
    payload = ELEKTRON_MFR_ID + bytes([A4_FAMILY_BYTE]) + packed + trailer
    return bytes([0xF0]) + payload + bytes([0xF7])


def rytm_real_layout_kit_payload(name: bytes = b"KIT 1") -> bytes:
    """Build a packed Rytm kit body matching the observed hardware dump layout."""

    from rytm_randomizer.data.analog_rytm_kit_layout import (
        RYTM_KIT_DUMP_ID,
        RYTM_KIT_RAW_SIZE,
        RYTM_KIT_TRACK_MACHINE_VALUE_OFFSET,
        RYTM_KIT_TRACK_SOUND_SIZE,
        RYTM_KIT_TRACKS_OFFSET,
        RYTM_SOUND_FIELD_BY_NRPN_LSB,
        RYTM_SYSEX_PRODUCT_ID,
    )

    raw = bytearray(bytes([0x00] * RYTM_KIT_RAW_SIZE))
    raw[0:4] = bytes([0x00, 0x00, 0x00, 0x06])
    raw[4:20] = name.ljust(16, b"\x00")
    machine_values = {
        1: 0,
        2: 2,
        3: 4,
        4: 6,
        5: 7,
        6: 30,
        7: 0,
        8: 0,
        9: 9,
        10: 10,
        11: 11,
        12: 12,
    }
    for pad, value in machine_values.items():
        track_offset = RYTM_KIT_TRACKS_OFFSET + (RYTM_KIT_TRACK_SOUND_SIZE * (pad - 1))
        raw[RYTM_KIT_TRACK_MACHINE_VALUE_OFFSET + (RYTM_KIT_TRACK_SOUND_SIZE * (pad - 1))] = value
        raw[track_offset + RYTM_SOUND_FIELD_BY_NRPN_LSB[1].sound_offset] = 40 + pad
        raw[track_offset + RYTM_SOUND_FIELD_BY_NRPN_LSB[2].sound_offset] = 50 + pad
        raw[track_offset + RYTM_SOUND_FIELD_BY_NRPN_LSB[20].sound_offset] = 24 + pad
        raw[track_offset + RYTM_SOUND_FIELD_BY_NRPN_LSB[27].sound_offset] = 18 + pad
    packed = pack_elektron_7bit(bytes(raw))
    checksum = sum(packed) & 0x3FFF
    size = (len(packed) + 5) & 0x3FFF
    trailer = bytes(
        [
            (checksum >> 7) & 0x7F,
            checksum & 0x7F,
            (size >> 7) & 0x7F,
            size & 0x7F,
        ]
    )
    return (
        bytes(
            [
                0x00,
                0x20,
                0x3C,
                RYTM_SYSEX_PRODUCT_ID,
                0x00,
                RYTM_KIT_DUMP_ID,
                0x01,
                0x01,
                0x00,
            ]
        )
        + packed
        + trailer
    )


def elektron_syx_message(payload: bytes) -> bytes:
    """Wrap one payload in a SysEx start/end frame for passive fixture banks."""

    return bytes([0xF0]) + payload + bytes([0xF7])


def analog_four_minimal_kit_payload(name: bytes = b"A4 KIT") -> bytes:
    """Build the minimal Analog Four kit payload shape used by passive reports."""

    payload = bytes([0x00, 0x20, 0x3C, 0x07]) + name[:16].ljust(16, b"\x00")
    return payload


def dual_machine_reference_bank_files(tmp_path: Path) -> tuple[Path, Path]:
    """Write tiny Rytm/A4 saved-kit banks for passive dual-machine report tests."""

    rytm_path = tmp_path / "rytm-reference-bank.syx"
    rytm_path.write_bytes(
        elektron_syx_message(rytm_real_layout_kit_payload(name=b"ARC RYTM ONE"))
        + elektron_syx_message(rytm_real_layout_kit_payload(name=b"ARC RYTM TWO"))
    )
    a4_path = tmp_path / "a4-reference-bank.syx"
    a4_path.write_bytes(
        elektron_syx_message(analog_four_minimal_kit_payload(b"ARC A4 ONE"))
        + elektron_syx_message(analog_four_minimal_kit_payload(b"ARC A4 TWO"))
    )
    return rytm_path, a4_path


@pytest.fixture
def recording_out() -> RecordingOut:
    """A fresh ``RecordingOut`` per test."""
    return RecordingOut()


@pytest.fixture
def fake_mido_session() -> Iterator[types.ModuleType]:
    """Install a fake ``mido`` module in ``sys.modules`` for the duration of one test.

    Yields the fake module so tests can inspect or mutate it (e.g. swap out
    ``fake.Message`` for a recording subclass). Restores the prior
    ``sys.modules["mido"]`` (or removes the entry entirely) on teardown so
    other tests are unaffected.
    """
    fake = types.ModuleType("mido")
    fake.Message = _FakeMessage  # type: ignore[attr-defined]
    prior = sys.modules.get("mido")
    sys.modules["mido"] = fake
    try:
        yield fake
    finally:
        if prior is None:
            sys.modules.pop("mido", None)
        else:
            sys.modules["mido"] = prior


@pytest.fixture
def no_sleep() -> Callable[[float], None]:
    """A no-op ``sleep`` substitute matching the engines' ``SleepFunc`` signature."""

    def _impl(_seconds: float) -> None:
        return None

    return _impl
