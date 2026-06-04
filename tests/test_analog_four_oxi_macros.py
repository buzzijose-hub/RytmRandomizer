import subprocess
import sys
from collections.abc import Mapping
from pathlib import Path
from types import MappingProxyType

import pytest

from rytm_randomizer.data.analog_four_midi import ANALOG_FOUR_SYNTH_TRACK_CC

pytestmark = pytest.mark.fast

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_importing_analog_four_oxi_macros_prints_nothing():
    result = subprocess.run(
        [sys.executable, "-c", "import rytm_randomizer.data.analog_four_oxi_macros"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert result.stdout == ""
    assert result.stderr == ""


def test_oxi_macro_catalog_is_immutable_and_has_default():
    from rytm_randomizer.data.analog_four_oxi_macros import (
        ANALOG_FOUR_OXI_MACROS,
        DEFAULT_ANALOG_FOUR_OXI_MACRO,
    )

    assert isinstance(ANALOG_FOUR_OXI_MACROS, MappingProxyType)
    assert isinstance(ANALOG_FOUR_OXI_MACROS, Mapping)
    assert DEFAULT_ANALOG_FOUR_OXI_MACRO == "hard-groove"
    assert DEFAULT_ANALOG_FOUR_OXI_MACRO in ANALOG_FOUR_OXI_MACROS
    assert tuple(ANALOG_FOUR_OXI_MACROS) == (
        "home",
        "hard-groove",
        "dub-pressure",
        "industrial-transition",
    )


def test_oxi_macro_events_are_manual_backed_and_track_scoped():
    from rytm_randomizer.data.analog_four_oxi_macros import ANALOG_FOUR_OXI_MACROS

    for macro in ANALOG_FOUR_OXI_MACROS.values():
        assert macro.track_count == 4
        assert macro.events
        assert {event.track for event in macro.events} == {1, 2, 3, 4}
        for event in macro.events:
            assert event.parameter in ANALOG_FOUR_SYNTH_TRACK_CC
            assert 1 <= event.track <= 4
            assert event.value_min <= event.value_max
            assert 0 <= event.value_min <= 127
            assert 0 <= event.value_max <= 127
            assert event.role
            assert event.lane
            assert event.intent


def test_oxi_macro_catalog_does_not_expose_real_midi_dependencies():
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import sys; "
                "import rytm_randomizer.data.analog_four_oxi_macros; "
                "print('mido' in sys.modules); "
                "print('rtmidi' in sys.modules); "
                "print('rytm_randomizer.real_midi_adapter' in sys.modules); "
                "print('rytm_randomizer.mido_provider' in sys.modules)"
            ),
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert result.stdout.splitlines() == ["False", "False", "False", "False"]
    assert result.stderr == ""
