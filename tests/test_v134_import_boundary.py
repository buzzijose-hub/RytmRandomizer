from __future__ import annotations

import importlib
import sys
from types import ModuleType


class _ForbiddenMido(ModuleType):
    def get_output_names(self):  # pragma: no cover - should never be called
        raise AssertionError("import must not query MIDI outputs")

    def open_output(self, _port_name):  # pragma: no cover - should never be called
        raise AssertionError("import must not open MIDI outputs")


def test_v134_reference_import_is_silent_and_does_not_touch_midi(capsys):
    sys.modules.pop("rytm_hybrid_randomizer_v134", None)
    sys.modules["mido"] = _ForbiddenMido("mido")

    try:
        importlib.import_module("rytm_hybrid_randomizer_v134")
    finally:
        sys.modules.pop("rytm_hybrid_randomizer_v134", None)
        sys.modules.pop("mido", None)

    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == ""


def test_v134_reference_has_no_bare_except_clauses():
    source = open("rytm_hybrid_randomizer_v134.py", encoding="utf-8").read()
    assert "except:\n" not in source
