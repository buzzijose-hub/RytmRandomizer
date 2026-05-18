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

import sys
import types
from collections.abc import Iterator
from typing import Any, Callable

import pytest


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
    after WS-M4 dedupe. New tests should prefer the ``fake_mido_session``
    pytest fixture which handles teardown.
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
