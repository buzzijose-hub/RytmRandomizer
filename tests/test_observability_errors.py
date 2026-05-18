"""Coverage tests for ``rytm_randomizer.observability.errors`` (taxonomy + re-export).

The errors module is the raises-taxonomy "umbrella" on top of the package's
existing concrete exception classes. The PEP-562 ``__getattr__`` re-exports
five legacy error classes (``RealMidiDependencyError``, ``RealMidiPortError``,
``RealMidiSendError``, ``MockMessageMappingError``, ``ActiveBoundaryError``)
under the new taxonomy bases so ``isinstance(exc, MidiError)`` works for any
real-midi-adapter exception, etc.

These tests exercise:

* ``RytmRandomizerError`` context handling (message vs. message+context).
* ``__getattr__`` for each of the five legacy re-exports.
* ``__getattr__`` for an unknown name (raises ``AttributeError``).

Test naming: ``test_<unit>_<behavior>_when_<condition>`` per Gate 8.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# WS-M4: mark this module as fast-suite; pytest -m fast skips the 505
# warm-worker V1.34 parity fixtures and runs in <60s.
pytestmark = pytest.mark.fast

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# ---------------------------------------------------------------------------
# 1. RytmRandomizerError: message-only vs. message+context rendering
# ---------------------------------------------------------------------------


def test_rytm_randomizer_error_with_no_context_renders_message_only() -> None:
    from rytm_randomizer.observability.errors import RytmRandomizerError

    err = RytmRandomizerError("boom")
    assert err.message == "boom"
    assert dict(err.context) == {}
    assert str(err) == "boom"


def test_rytm_randomizer_error_with_context_appends_context_tail() -> None:
    from rytm_randomizer.observability.errors import RytmRandomizerError

    err = RytmRandomizerError("boom", context={"pad": 1, "param": "FLT Frequency"})
    assert err.message == "boom"
    rendered = str(err)
    assert rendered.startswith("boom [context: ")
    assert "pad=1" in rendered
    assert "param='FLT Frequency'" in rendered


def test_rytm_randomizer_error_context_is_read_only_mapping() -> None:
    from rytm_randomizer.observability.errors import RytmRandomizerError

    err = RytmRandomizerError("boom", context={"key": "value"})
    # MappingProxyType raises TypeError on assignment.
    with pytest.raises(TypeError):
        err.context["key"] = "other"  # type: ignore[index]


# ---------------------------------------------------------------------------
# 2. Taxonomy bases are importable and distinct
# ---------------------------------------------------------------------------


def test_taxonomy_bases_are_exported_and_subclass_root() -> None:
    from rytm_randomizer.observability.errors import (
        BoundaryError,
        ConfigError,
        DataError,
        MidiError,
        RytmRandomizerError,
        StateError,
    )

    for cls in (MidiError, StateError, DataError, BoundaryError, ConfigError):
        assert issubclass(cls, RytmRandomizerError)


# ---------------------------------------------------------------------------
# 3. PEP-562 __getattr__: lazy re-exports
# ---------------------------------------------------------------------------


def test_module_getattr_resolves_real_midi_dependency_error() -> None:
    from rytm_randomizer.observability import errors as errors_mod
    from rytm_randomizer.observability.errors import MidiError

    cls = errors_mod.RealMidiDependencyError
    assert issubclass(cls, MidiError)


def test_module_getattr_resolves_real_midi_port_error() -> None:
    from rytm_randomizer.observability import errors as errors_mod
    from rytm_randomizer.observability.errors import MidiError

    cls = errors_mod.RealMidiPortError
    assert issubclass(cls, MidiError)


def test_module_getattr_resolves_real_midi_send_error() -> None:
    from rytm_randomizer.observability import errors as errors_mod
    from rytm_randomizer.observability.errors import MidiError

    cls = errors_mod.RealMidiSendError
    assert issubclass(cls, MidiError)


def test_module_getattr_resolves_mock_message_mapping_error() -> None:
    from rytm_randomizer.observability import errors as errors_mod
    from rytm_randomizer.observability.errors import DataError

    cls = errors_mod.MockMessageMappingError
    assert issubclass(cls, DataError)


def test_module_getattr_resolves_active_boundary_error() -> None:
    from rytm_randomizer.observability import errors as errors_mod
    from rytm_randomizer.observability.errors import BoundaryError

    cls = errors_mod.ActiveBoundaryError
    assert issubclass(cls, BoundaryError)


def test_module_getattr_raises_attribute_error_on_unknown_name() -> None:
    from rytm_randomizer.observability import errors as errors_mod

    with pytest.raises(AttributeError, match="DoesNotExistError"):
        errors_mod.DoesNotExistError  # noqa: B018 - intentional attribute access
