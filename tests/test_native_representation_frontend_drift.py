"""Tie deliberately mirrored operator-only TypeScript literals to canonical facts."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from rytm_randomizer.data.analog_four_f1_contract import (
    A4_F1_DISPLAY_SCALE,
    A4_F1_NATIVE_MAX,
    A4_F1_NATIVE_SCALE,
)
from rytm_randomizer.data.analog_four_saved_kit_layout import (
    A4_FAMILY_BYTE,
    A4_KIT_OBJECT_BYTE,
    A4_KIT_PROTOCOL_VERSION,
    A4_WORKING_KIT_OBJECT_BYTE,
)
from rytm_randomizer.snapshot import ELEKTRON_MFR_ID

pytestmark = pytest.mark.fast
_FRONTEND = Path(__file__).parents[1] / "desktop/web/src/cockpit"


def test_show_candidate_forward_label_literal_witness_matches_f1_data_contract() -> None:
    source = (_FRONTEND / "showKitForge/showKitForgeModel.ts").read_text(encoding="utf-8")
    maximum = re.search(r"native > (\d+)\) return 'unavailable'", source)
    scale = re.search(r"const hundredths = Math\.floor\(native \* (\d+) / (\d+)\)", source)
    assert (
        maximum is not None and scale is not None
    ), "Review the mirrored label witness if TS structure changes"
    assert int(maximum[1]) == A4_F1_NATIVE_MAX
    assert tuple(map(int, scale.groups())) == (A4_F1_DISPLAY_SCALE, A4_F1_NATIVE_SCALE)


def test_library_kind_label_literal_witness_matches_supported_a4_header_contract() -> None:
    source = (_FRONTEND / "referenceSound/referenceSoundModel.ts").read_text(encoding="utf-8")
    header = re.search(
        r"header\.startsWith\('([0-9a-f]+)'\) && header\.slice\(12, 16\) === '([0-9a-f]+)'", source
    )
    kinds = re.findall(r"if \(header\.slice\(10, 12\) === '([0-9a-f]+)'\) kind = '([^']+)'", source)
    assert header is not None, "Review source-kind presentation if TS structure changes"
    assert header[1] == (ELEKTRON_MFR_ID + bytes((A4_FAMILY_BYTE, 0))).hex()
    assert header[2] == bytes(A4_KIT_PROTOCOL_VERSION).hex()
    assert kinds == [
        (f"{A4_KIT_OBJECT_BYTE:02x}", "indexed KIT bank"),
        (f"{A4_WORKING_KIT_OBJECT_BYTE:02x}", "working RAM; freshness unverified"),
    ]
