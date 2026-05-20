# Rytm 12-Pad Machine Matrix Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a passive Analog Rytm MK2 12-pad machine-compatibility matrix so the codebase can report every legal pad/engine pairing before live 12-pad mutation is enabled.

**Architecture:** The matrix is a pure data-layer fact table under `rytm_randomizer/data/`, rendered by a passive report under `rytm_randomizer/reports/`, and exposed through the existing read-only CLI. No real MIDI module, active runtime module, or V1.34 parity fixture is touched.

**Tech Stack:** Python 3.11, pytest, frozen dataclasses, `MappingProxyType`, existing passive report formatter, existing CLI help-text module.

---

## Preconditions

- Work from `C:\Users\Jose Buzzi\Documents\RytmRandomizer\.worktrees\rytm-12-pad-machine-matrix-lf`.
- Base branch is `origin/modularize-v1.34`.
- The worktree currently shows unrelated CRLF/LF noise from the merged base. Do not stage unrelated files. Use path-specific `git add -- <paths>`.
- Do not run `PARITY_CAPTURE_MODE=1`.
- Do not send hardware MIDI.

## File Structure

- Create `rytm_randomizer/data/rytm_machine_catalog.py`: passive OS 1.72 Rytm machine/pad compatibility catalog.
- Modify `rytm_randomizer/data/__init__.py`: re-export uppercase catalog constants only.
- Create `tests/test_data_rytm_machine_catalog.py`: fast tests for machine values, pad eligibility, and cardinality.
- Create `rytm_randomizer/reports/rytm_machine_matrix.py`: passive report builder/formatter.
- Modify `rytm_randomizer/reports/__init__.py`: re-export the new report functions.
- Create `tests/test_rytm_machine_matrix_report.py`: fast tests for report totals, safety wording, and Pad 10 behavior.
- Modify `rytm_randomizer/cli.py`: add one read-only command arm.
- Modify `rytm_randomizer/help_text.py`: add command usage/help text.
- Modify `tests/test_cli.py`, `tests/test_cli_coverage.py`, and `tests/test_real_midi_passive_cli_safety.py`: cover the command and passive safety.
- Modify `README.md` and `docs/STATUS.md`: update the user-facing status.

---

## Task 1: Add Rytm Machine Catalog Data

**Files:**
- Create: `tests/test_data_rytm_machine_catalog.py`
- Create: `rytm_randomizer/data/rytm_machine_catalog.py`
- Modify: `rytm_randomizer/data/__init__.py`

- [ ] **Step 1: Write the failing data-layer tests**

Create `tests/test_data_rytm_machine_catalog.py` with:

```python
"""Tests for the passive Analog Rytm 12-pad machine catalog."""

from __future__ import annotations

import pytest

from rytm_randomizer.data.rytm_machine_catalog import (
    RYTM_MACHINE_PROFILES,
    RYTM_MACHINE_PROFILES_BY_KEY,
    RYTM_PAD_CAPABILITIES,
    allowed_machine_profiles_for_pad,
    get_rytm_machine_profile,
    get_rytm_pad_capability,
    is_machine_allowed_on_pad,
)

pytestmark = pytest.mark.fast


def test_catalog_has_expected_cardinality() -> None:
    assert len(RYTM_MACHINE_PROFILES) == 33
    assert len(RYTM_PAD_CAPABILITIES) == 12
    assert sum(len(pad.allowed_machine_keys) for pad in RYTM_PAD_CAPABILITIES) == 116


def test_every_pad_machine_reference_resolves_to_cc15_value() -> None:
    for pad in RYTM_PAD_CAPABILITIES:
        for machine_key in pad.allowed_machine_keys:
            profile = RYTM_MACHINE_PROFILES_BY_KEY[machine_key]
            assert 0 <= profile.machine_value <= 127


@pytest.mark.parametrize(
    ("machine_key", "machine_value"),
    [
        ("bd_hard", 0),
        ("bd_classic", 1),
        ("sd_hard", 2),
        ("sd_classic", 3),
        ("rs_hard", 4),
        ("rs_classic", 5),
        ("cp_classic", 6),
        ("bt_classic", 7),
        ("xt_classic", 8),
        ("ch_classic", 9),
        ("oh_classic", 10),
        ("cy_classic", 11),
        ("cb_classic", 12),
        ("bd_fm", 13),
        ("sd_fm", 14),
        ("ut_noise", 15),
        ("ut_impulse", 16),
        ("ch_metallic", 17),
        ("oh_metallic", 18),
        ("cy_metallic", 19),
        ("cb_metallic", 20),
        ("bd_plastic", 21),
        ("bd_silky", 22),
        ("sd_natural", 23),
        ("hh_basic", 24),
        ("cy_ride", 25),
        ("bd_sharp", 26),
        ("dual_vco", 28),
        ("sy_chip", 29),
        ("bd_acoustic", 30),
        ("sd_acoustic", 31),
        ("sy_raw", 32),
        ("hh_lab", 33),
    ],
)
def test_machine_key_maps_to_expected_cc15_value(machine_key: str, machine_value: int) -> None:
    assert get_rytm_machine_profile(machine_key).machine_value == machine_value


def test_pad_10_is_open_hihat_not_xt_classic() -> None:
    pad = get_rytm_pad_capability(10)

    assert pad.track_code == "OH"
    assert pad.label == "Open Hihat"
    assert is_machine_allowed_on_pad(10, "oh_classic")
    assert is_machine_allowed_on_pad(10, "oh_metallic")
    assert is_machine_allowed_on_pad(10, "hh_basic")
    assert is_machine_allowed_on_pad(10, "ch_classic")
    assert is_machine_allowed_on_pad(10, "ut_noise")
    assert not is_machine_allowed_on_pad(10, "xt_classic")


@pytest.mark.parametrize("pad", [6, 7, 8])
def test_tom_pads_allow_xt_classic(pad: int) -> None:
    assert is_machine_allowed_on_pad(pad, "xt_classic")
    assert not is_machine_allowed_on_pad(pad, "oh_classic")


def test_allowed_machine_profiles_for_pad_preserves_manual_order() -> None:
    labels = [profile.label for profile in allowed_machine_profiles_for_pad(11)]

    assert labels == [
        "CY Classic",
        "CY Metallic",
        "CY Ride",
        "CB Classic",
        "CB Metallic",
        "UT Noise",
        "UT Impulse",
    ]


def test_unknown_pad_and_machine_raise_specific_key_errors() -> None:
    with pytest.raises(KeyError, match="Unknown Rytm pad"):
        get_rytm_pad_capability(13)

    with pytest.raises(KeyError, match="Unknown Rytm machine key"):
        get_rytm_machine_profile("not_a_machine")
```

- [ ] **Step 2: Run the data tests and verify RED**

Run:

```bash
python -m pytest tests/test_data_rytm_machine_catalog.py -n 0
```

Expected: FAIL because `rytm_randomizer.data.rytm_machine_catalog` does not exist.

- [ ] **Step 3: Implement the passive catalog**

Create `rytm_randomizer/data/rytm_machine_catalog.py` with:

```python
"""Passive Analog Rytm MK2 OS 1.72 machine compatibility catalog."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import Final, Literal

SupportStatus = Literal["mutable_v134", "machine_selectable"]


@dataclass(frozen=True)
class RytmMachineProfile:
    """Passive description of one selectable Analog Rytm machine."""

    key: str
    label: str
    family: str
    machine_value: int
    support_status: SupportStatus
    role_tags: tuple[str, ...]


@dataclass(frozen=True)
class RytmPadCapability:
    """OS 1.72 machine compatibility for one Analog Rytm pad."""

    pad: int
    track_code: str
    label: str
    allowed_machine_keys: tuple[str, ...]


def _profile(
    key: str,
    label: str,
    family: str,
    machine_value: int,
    support_status: SupportStatus = "machine_selectable",
    role_tags: tuple[str, ...] = (),
) -> RytmMachineProfile:
    return RytmMachineProfile(
        key=key,
        label=label,
        family=family,
        machine_value=machine_value,
        support_status=support_status,
        role_tags=role_tags,
    )


BD_MACHINE_KEYS: Final[tuple[str, ...]] = (
    "bd_hard",
    "bd_classic",
    "bd_fm",
    "bd_plastic",
    "bd_silky",
    "bd_sharp",
    "bd_acoustic",
)
SD_MACHINE_KEYS: Final[tuple[str, ...]] = (
    "sd_hard",
    "sd_classic",
    "sd_fm",
    "sd_natural",
    "sd_acoustic",
)
SY_MACHINE_KEYS: Final[tuple[str, ...]] = ("dual_vco", "sy_chip", "sy_raw")
RS_MACHINE_KEYS: Final[tuple[str, ...]] = ("rs_hard", "rs_classic")
CP_MACHINE_KEYS: Final[tuple[str, ...]] = ("cp_classic",)
BT_MACHINE_KEYS: Final[tuple[str, ...]] = ("bt_classic",)
XT_MACHINE_KEYS: Final[tuple[str, ...]] = ("xt_classic",)
CH_MACHINE_KEYS: Final[tuple[str, ...]] = ("ch_classic", "ch_metallic")
OH_MACHINE_KEYS: Final[tuple[str, ...]] = ("oh_classic", "oh_metallic")
HH_MACHINE_KEYS: Final[tuple[str, ...]] = ("hh_basic", "hh_lab")
CY_MACHINE_KEYS: Final[tuple[str, ...]] = ("cy_classic", "cy_metallic", "cy_ride")
CB_MACHINE_KEYS: Final[tuple[str, ...]] = ("cb_classic", "cb_metallic")
UT_MACHINE_KEYS: Final[tuple[str, ...]] = ("ut_noise", "ut_impulse")

RYTM_MACHINE_PROFILES: Final[tuple[RytmMachineProfile, ...]] = (
    _profile("bd_hard", "BD Hard", "BD", 0, "mutable_v134", ("kick", "foundation")),
    _profile("bd_classic", "BD Classic", "BD", 1, "mutable_v134", ("kick", "round")),
    _profile("bd_fm", "BD FM", "BD", 13, "mutable_v134", ("kick", "metallic")),
    _profile("bd_plastic", "BD Plastic", "BD", 21, "mutable_v134", ("kick", "rubber")),
    _profile("bd_silky", "BD Silky", "BD", 22, "mutable_v134", ("kick", "deep")),
    _profile("bd_sharp", "BD Sharp", "BD", 26, "mutable_v134", ("kick", "attack")),
    _profile("bd_acoustic", "BD Acoustic", "BD", 30, "mutable_v134", ("kick", "body")),
    _profile("sd_hard", "SD Hard", "SD", 2, "mutable_v134", ("snare", "pressure")),
    _profile("sd_classic", "SD Classic", "SD", 3, "mutable_v134", ("snare", "classic")),
    _profile("sd_fm", "SD FM", "SD", 14, "mutable_v134", ("snare", "metallic")),
    _profile("sd_natural", "SD Natural", "SD", 23, role_tags=("snare", "natural")),
    _profile("sd_acoustic", "SD Acoustic", "SD", 31, role_tags=("snare", "acoustic")),
    _profile("dual_vco", "SY Dual VCO", "SY", 28, role_tags=("synth", "tonal")),
    _profile("sy_chip", "SY Chip", "SY", 29, role_tags=("synth", "digital")),
    _profile("sy_raw", "SY Raw", "SY", 32, "mutable_v134", ("synth", "raw")),
    _profile("rs_hard", "RS Hard", "RS", 4, role_tags=("rim", "hard")),
    _profile("rs_classic", "RS Classic", "RS", 5, role_tags=("rim", "classic")),
    _profile("cp_classic", "CP Classic", "CP", 6, role_tags=("clap", "classic")),
    _profile("bt_classic", "BT Classic", "BT", 7, role_tags=("tom", "low")),
    _profile("xt_classic", "XT Classic", "XT", 8, role_tags=("tom", "classic")),
    _profile("ch_classic", "CH Classic", "CH", 9, role_tags=("hat", "closed")),
    _profile("ch_metallic", "CH Metallic", "CH", 17, role_tags=("hat", "metallic")),
    _profile("oh_classic", "OH Classic", "OH", 10, role_tags=("hat", "open")),
    _profile("oh_metallic", "OH Metallic", "OH", 18, role_tags=("hat", "open")),
    _profile("hh_basic", "HH Basic", "HH", 24, role_tags=("hat", "basic")),
    _profile("hh_lab", "HH Lab", "HH", 33, role_tags=("hat", "lab")),
    _profile("cy_classic", "CY Classic", "CY", 11, role_tags=("cymbal", "classic")),
    _profile("cy_metallic", "CY Metallic", "CY", 19, role_tags=("cymbal", "metallic")),
    _profile("cy_ride", "CY Ride", "CY", 25, role_tags=("cymbal", "ride")),
    _profile("cb_classic", "CB Classic", "CB", 12, role_tags=("cowbell", "classic")),
    _profile("cb_metallic", "CB Metallic", "CB", 20, role_tags=("cowbell", "metallic")),
    _profile("ut_noise", "UT Noise", "UT", 15, role_tags=("utility", "noise")),
    _profile("ut_impulse", "UT Impulse", "UT", 16, role_tags=("utility", "impulse")),
)

RYTM_MACHINE_PROFILES_BY_KEY: Final[Mapping[str, RytmMachineProfile]] = MappingProxyType(
    {profile.key: profile for profile in RYTM_MACHINE_PROFILES}
)


def _allowed(*groups: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(machine_key for group in groups for machine_key in group)


RYTM_PAD_CAPABILITIES: Final[tuple[RytmPadCapability, ...]] = (
    RytmPadCapability(1, "BD", "Bass Drum", _allowed(BD_MACHINE_KEYS, SY_MACHINE_KEYS, SD_MACHINE_KEYS, UT_MACHINE_KEYS)),
    RytmPadCapability(2, "SD", "Snare Drum", _allowed(SD_MACHINE_KEYS, SY_MACHINE_KEYS, BD_MACHINE_KEYS, UT_MACHINE_KEYS)),
    RytmPadCapability(3, "RS", "Rim Shot", _allowed(RS_MACHINE_KEYS, SY_MACHINE_KEYS, BD_MACHINE_KEYS, SD_MACHINE_KEYS, CP_MACHINE_KEYS, UT_MACHINE_KEYS)),
    RytmPadCapability(4, "CP", "Hand Clap", _allowed(CP_MACHINE_KEYS, SY_MACHINE_KEYS, BD_MACHINE_KEYS, SD_MACHINE_KEYS, RS_MACHINE_KEYS, UT_MACHINE_KEYS)),
    RytmPadCapability(5, "BT", "Bass Tom", _allowed(BT_MACHINE_KEYS, UT_MACHINE_KEYS)),
    RytmPadCapability(6, "LT", "Low Tom", _allowed(XT_MACHINE_KEYS, UT_MACHINE_KEYS)),
    RytmPadCapability(7, "MT", "Mid Tom", _allowed(XT_MACHINE_KEYS, UT_MACHINE_KEYS)),
    RytmPadCapability(8, "HT", "Hi Tom", _allowed(XT_MACHINE_KEYS, UT_MACHINE_KEYS)),
    RytmPadCapability(9, "CH", "Closed Hihat", _allowed(CH_MACHINE_KEYS, HH_MACHINE_KEYS, OH_MACHINE_KEYS, UT_MACHINE_KEYS)),
    RytmPadCapability(10, "OH", "Open Hihat", _allowed(OH_MACHINE_KEYS, HH_MACHINE_KEYS, CH_MACHINE_KEYS, UT_MACHINE_KEYS)),
    RytmPadCapability(11, "CY", "Cymbal", _allowed(CY_MACHINE_KEYS, CB_MACHINE_KEYS, UT_MACHINE_KEYS)),
    RytmPadCapability(12, "CB", "Cow Bell", _allowed(CB_MACHINE_KEYS, CY_MACHINE_KEYS, UT_MACHINE_KEYS)),
)

RYTM_PAD_CAPABILITIES_BY_PAD: Final[Mapping[int, RytmPadCapability]] = MappingProxyType(
    {capability.pad: capability for capability in RYTM_PAD_CAPABILITIES}
)


def get_rytm_machine_profile(key: str) -> RytmMachineProfile:
    """Return one machine profile by key."""

    try:
        return RYTM_MACHINE_PROFILES_BY_KEY[key]
    except KeyError as exc:
        raise KeyError(f"Unknown Rytm machine key: {key}") from exc


def get_rytm_pad_capability(pad: int) -> RytmPadCapability:
    """Return one pad capability by 1-based pad number."""

    try:
        return RYTM_PAD_CAPABILITIES_BY_PAD[pad]
    except KeyError as exc:
        raise KeyError(f"Unknown Rytm pad: {pad}") from exc


def allowed_machine_profiles_for_pad(pad: int) -> tuple[RytmMachineProfile, ...]:
    """Return machine profiles allowed on a pad, preserving manual order."""

    capability = get_rytm_pad_capability(pad)
    return tuple(get_rytm_machine_profile(key) for key in capability.allowed_machine_keys)


def is_machine_allowed_on_pad(pad: int, machine_key: str) -> bool:
    """Return whether a machine key is legal for the pad."""

    return machine_key in get_rytm_pad_capability(pad).allowed_machine_keys
```

- [ ] **Step 4: Re-export uppercase catalog constants from data package**

Modify `rytm_randomizer/data/__init__.py`:

```python
from .rytm_machine_catalog import (
    RYTM_MACHINE_PROFILES,
    RYTM_MACHINE_PROFILES_BY_KEY,
    RYTM_PAD_CAPABILITIES,
    RYTM_PAD_CAPABILITIES_BY_PAD,
)
```

Add these names to `__all__`:

```python
    "RYTM_MACHINE_PROFILES",
    "RYTM_MACHINE_PROFILES_BY_KEY",
    "RYTM_PAD_CAPABILITIES",
    "RYTM_PAD_CAPABILITIES_BY_PAD",
```

- [ ] **Step 5: Run the data tests and verify GREEN**

Run:

```bash
python -m pytest tests/test_data_rytm_machine_catalog.py -n 0
```

Expected: PASS.

- [ ] **Step 6: Commit Task 1**

Run:

```bash
git add -- tests/test_data_rytm_machine_catalog.py rytm_randomizer/data/rytm_machine_catalog.py rytm_randomizer/data/__init__.py
git commit -m "feat: add Rytm 12-pad machine catalog"
```

---

## Task 2: Add Passive Rytm Machine Matrix Report

**Files:**
- Create: `tests/test_rytm_machine_matrix_report.py`
- Create: `rytm_randomizer/reports/rytm_machine_matrix.py`
- Modify: `rytm_randomizer/reports/__init__.py`

- [ ] **Step 1: Write the failing report tests**

Create `tests/test_rytm_machine_matrix_report.py` with:

```python
"""Tests for the passive Rytm 12-pad machine matrix report."""

from __future__ import annotations

import pytest

from rytm_randomizer.reports.rytm_machine_matrix import (
    build_rytm_machine_matrix_report,
    format_rytm_machine_matrix_report,
)

pytestmark = pytest.mark.fast


def test_build_report_has_expected_totals() -> None:
    report = build_rytm_machine_matrix_report()

    assert report["pad_count"] == 12
    assert report["machine_profile_count"] == 33
    assert report["allowed_slot_count"] == 116
    assert report["cc15_selectable_slot_count"] == 116
    assert report["pending_machine_value_count"] == 0


def test_build_report_marks_pad_10_as_open_hihat() -> None:
    report = build_rytm_machine_matrix_report()
    pad_10 = report["pads"][10]

    assert pad_10["track_code"] == "OH"
    assert pad_10["label"] == "Open Hihat"
    assert "OH Classic (CC15 10)" in pad_10["machines"]
    assert "XT Classic (CC15 8)" not in pad_10["machines"]


def test_format_report_includes_totals_and_safety_text() -> None:
    lines = format_rytm_machine_matrix_report()
    text = "\n".join(lines)
    pad_10_start = lines.index("Pad 10 / OH / Open Hihat:")
    pad_11_start = lines.index("Pad 11 / CY / Cymbal:")
    pad_10_lines = lines[pad_10_start:pad_11_start]

    assert lines[0] == "RytmRandomizer passive Rytm 12-pad machine matrix"
    assert "- Pads: 12" in lines
    assert "- Machine profiles: 33" in lines
    assert "- Allowed pad-machine slots: 116" in lines
    assert "- CC15-selectable slots: 116" in lines
    assert "Pad 10 / OH / Open Hihat:" in text
    assert "OH Classic (CC15 10)" in text
    assert "  - XT Classic (CC15 8)" not in pad_10_lines
    assert "- passive/read-only" in lines
    assert "- no MIDI sending" in lines
    assert "- no port opening" in lines
    assert "Source: rytm_randomizer.reports.rytm_machine_matrix" in lines
    assert "In-memory only: True" in lines
```

- [ ] **Step 2: Run the report tests and verify RED**

Run:

```bash
python -m pytest tests/test_rytm_machine_matrix_report.py -n 0
```

Expected: FAIL because `rytm_randomizer.reports.rytm_machine_matrix` does not exist.

- [ ] **Step 3: Implement the report module**

Create `rytm_randomizer/reports/rytm_machine_matrix.py` with:

```python
"""Passive Analog Rytm 12-pad machine matrix report."""

from __future__ import annotations

from typing import Final

from ..data.rytm_machine_catalog import (
    RYTM_MACHINE_PROFILES,
    RYTM_PAD_CAPABILITIES,
    allowed_machine_profiles_for_pad,
)
from .formatter import passive_footer_lines

_SAFETY_LINES: Final[tuple[str, ...]] = (
    "passive/read-only",
    "no MIDI sending",
    "no port opening",
    "no command execution",
    "no hardware mutation",
    "no hardware required",
)


def _machine_label(label: str, machine_value: int) -> str:
    return f"{label} (CC15 {machine_value})"


def build_rytm_machine_matrix_report() -> dict[str, object]:
    """Return passive report data for the Rytm 12-pad machine matrix."""

    pads: dict[int, dict[str, object]] = {}
    allowed_slot_count = 0
    cc15_slot_count = 0
    for capability in RYTM_PAD_CAPABILITIES:
        machines = tuple(
            _machine_label(profile.label, profile.machine_value)
            for profile in allowed_machine_profiles_for_pad(capability.pad)
        )
        allowed_slot_count += len(machines)
        cc15_slot_count += len(machines)
        pads[capability.pad] = {
            "track_code": capability.track_code,
            "label": capability.label,
            "machines": machines,
        }

    return {
        "title": "RytmRandomizer passive Rytm 12-pad machine matrix",
        "pad_count": len(RYTM_PAD_CAPABILITIES),
        "machine_profile_count": len(RYTM_MACHINE_PROFILES),
        "allowed_slot_count": allowed_slot_count,
        "cc15_selectable_slot_count": cc15_slot_count,
        "pending_machine_value_count": 0,
        "pads": pads,
        "safety": _SAFETY_LINES,
    }


def format_rytm_machine_matrix_report() -> list[str]:
    """Return deterministic report lines for the Rytm 12-pad machine matrix."""

    report = build_rytm_machine_matrix_report()
    lines = [
        str(report["title"]),
        "Summary:",
        f"- Pads: {report['pad_count']}",
        f"- Machine profiles: {report['machine_profile_count']}",
        f"- Allowed pad-machine slots: {report['allowed_slot_count']}",
        f"- CC15-selectable slots: {report['cc15_selectable_slot_count']}",
        f"- Pending machine values: {report['pending_machine_value_count']}",
        "Pads:",
    ]

    pads = report["pads"]
    assert isinstance(pads, dict)
    for pad in sorted(pads):
        pad_report = pads[pad]
        assert isinstance(pad_report, dict)
        lines.append(f"Pad {pad} / {pad_report['track_code']} / {pad_report['label']}:")
        machines = pad_report["machines"]
        assert isinstance(machines, tuple)
        lines.extend(f"  - {machine}" for machine in machines)

    lines.append("Safety:")
    lines.extend(f"- {line}" for line in _SAFETY_LINES)
    lines.extend(passive_footer_lines("reports.rytm_machine_matrix"))
    return lines
```

- [ ] **Step 4: Re-export report functions**

Modify `rytm_randomizer/reports/__init__.py` near the imports:

```python
from .rytm_machine_matrix import (
    build_rytm_machine_matrix_report,
    format_rytm_machine_matrix_report,
)
```

If `reports/__init__.py` has no `__all__`, no `__all__` update is required.

- [ ] **Step 5: Run report tests and verify GREEN**

Run:

```bash
python -m pytest tests/test_data_rytm_machine_catalog.py tests/test_rytm_machine_matrix_report.py -n 0
```

Expected: PASS.

- [ ] **Step 6: Commit Task 2**

Run:

```bash
git add -- tests/test_rytm_machine_matrix_report.py rytm_randomizer/reports/rytm_machine_matrix.py rytm_randomizer/reports/__init__.py
git commit -m "feat: add passive Rytm machine matrix report"
```

---

## Task 3: Wire Passive CLI Command and Safety Tests

**Files:**
- Modify: `rytm_randomizer/cli.py`
- Modify: `rytm_randomizer/help_text.py`
- Modify: `tests/test_cli.py`
- Modify: `tests/test_cli_coverage.py`
- Modify: `tests/test_real_midi_passive_cli_safety.py`

- [ ] **Step 1: Write failing CLI tests**

Add to `tests/test_cli.py`:

```python
def test_rytm_machine_matrix_report_command_exits_zero_and_describes_pad_10():
    result = run_cli("rytm-12-pad-machine-matrix-report")

    output = normalize_newlines(result.stdout)
    assert result.returncode == 0
    assert "RytmRandomizer passive Rytm 12-pad machine matrix" in output
    assert "- Pads: 12" in output
    assert "- Allowed pad-machine slots: 116" in output
    assert "Pad 10 / OH / Open Hihat:" in output
    assert "OH Classic (CC15 10)" in output
    assert result.stderr == ""


def test_rytm_machine_matrix_report_help_exits_zero():
    result = run_cli("rytm-12-pad-machine-matrix-report", "--help")

    assert result.returncode == 0
    assert "RytmRandomizer passive CLI: rytm-12-pad-machine-matrix-report" in result.stdout
    assert result.stderr == ""
```

Add to `tests/test_cli_coverage.py`:

```python
def test_main_rytm_machine_matrix_report_writes_report(capsys):
    rc = cli.main(["rytm-12-pad-machine-matrix-report"])

    captured = capsys.readouterr()
    assert rc == 0
    assert captured.out.endswith("\n")
    assert "RytmRandomizer passive Rytm 12-pad machine matrix" in captured.out
    assert captured.err == ""
```

Update `PASSIVE_CLI_COMMANDS` and `PASSIVE_CLI_SWEEP_COMMANDS` in `tests/test_real_midi_passive_cli_safety.py` to include:

```python
    ("rytm-12-pad-machine-matrix-report",),
```

- [ ] **Step 2: Run CLI tests and verify RED**

Run:

```bash
python -m pytest tests/test_cli.py::test_rytm_machine_matrix_report_command_exits_zero_and_describes_pad_10 tests/test_cli.py::test_rytm_machine_matrix_report_help_exits_zero tests/test_cli_coverage.py::test_main_rytm_machine_matrix_report_writes_report tests/test_real_midi_passive_cli_safety.py::test_passive_cli_sweep_does_not_import_real_midi_or_adapter_modules -n 0
```

Expected: FAIL because the command is not wired.

- [ ] **Step 3: Wire CLI dispatch**

In `rytm_randomizer/cli.py`, add this command arm before `dual-machine-target-report`:

```python
    if args == ["rytm-12-pad-machine-matrix-report"]:
        from .reports import format_rytm_machine_matrix_report

        sys.stdout.write("\n".join(format_rytm_machine_matrix_report()))
        sys.stdout.write("\n")
        return 0
```

- [ ] **Step 4: Update help text**

In `rytm_randomizer/help_text.py`, add `rytm-12-pad-machine-matrix-report` to `USAGE`, top-level help usage, command list, and `HELP_TEXT`:

```python
    "behavior-parity-report | rytm-12-pad-machine-matrix-report | "
```

```text
  python -m rytm_randomizer.cli rytm-12-pad-machine-matrix-report
```

```text
  rytm-12-pad-machine-matrix-report
                     Print the passive Rytm 12-pad machine matrix report.
```

```python
    "rytm-12-pad-machine-matrix-report": """RytmRandomizer passive CLI: rytm-12-pad-machine-matrix-report

Usage:
  python -m rytm_randomizer.cli rytm-12-pad-machine-matrix-report
  python -m rytm_randomizer.cli rytm-12-pad-machine-matrix-report --help

Behavior:
  Prints the passive Analog Rytm MK2 12-pad machine compatibility matrix.

Safety:
  passive/read-only
  no MIDI sending
  no port opening
  no command execution
  no hardware mutation
  no hardware required""",
```

Update the duplicate `USAGE` string in `tests/test_cli.py` to include the same command.

- [ ] **Step 5: Run CLI tests and verify GREEN**

Run:

```bash
python -m pytest tests/test_cli.py tests/test_cli_coverage.py tests/test_real_midi_passive_cli_safety.py -n 0
```

Expected: PASS.

- [ ] **Step 6: Commit Task 3**

Run:

```bash
git add -- rytm_randomizer/cli.py rytm_randomizer/help_text.py tests/test_cli.py tests/test_cli_coverage.py tests/test_real_midi_passive_cli_safety.py
git commit -m "feat: expose passive Rytm machine matrix CLI"
```

---

## Task 4: Update README and Status Docs

**Files:**
- Modify: `README.md`
- Modify: `docs/STATUS.md`

- [ ] **Step 1: Write docs freshness assertion**

Add this test to `tests/test_cli.py`:

```python
def test_readme_mentions_rytm_machine_matrix_report_command():
    text = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")

    assert "rytm-12-pad-machine-matrix-report" in text
    assert "12-pad machine matrix" in text
```

- [ ] **Step 2: Run docs/readme test and verify RED**

Run:

```bash
python -m pytest tests/test_cli.py::test_readme_mentions_rytm_machine_matrix_report_command -n 0
```

Expected: FAIL before README is updated.

- [ ] **Step 3: Update README**

In `README.md`, replace:

```text
- No Pads 5-12 expansion yet.
```

with:

```text
- Pads 5-12 have a passive machine matrix report; armed 12-pad runtime mutation remains gated until the follow-up runtime slice.
```

Add this passive CLI example near the dual-machine target commands:

```bash
python -m rytm_randomizer.cli rytm-12-pad-machine-matrix-report   # passive Rytm 12-pad machine compatibility matrix
```

- [ ] **Step 4: Update docs/STATUS.md**

Add a top entry under `## Recent Cleanup`:

```markdown
- 2026-05-19: Rytm 12-pad machine matrix checkpoint started. The implementation adds a passive OS 1.72 pad-machine compatibility catalog and report so pads 1-12 can be validated before armed 12-pad mutation. Pad 10 is explicitly treated as OH / Open Hihat, while XT Classic remains limited to LT/MT/HT tom pads. This is read-only reporting only; hardware sends and runtime mutation remain gated.
```

Also replace the stale `What's Next` line:

```text
- Out of scope for now: Pads 5-12, additional machines/profiles, new CC mappings, GUI/capture, SysEx, and Analog Four support.
```

with:

```text
- Out of scope for the current runtime: armed pads 5-12 mutation, GUI/capture, audio analysis, and ungated Analog Four hardware sends.
```

- [ ] **Step 5: Run docs tests**

Run:

```bash
python -m pytest tests/architecture/test_readme_freshness.py -q
```

Expected: PASS.

- [ ] **Step 6: Commit Task 4**

Run:

```bash
git add -- README.md docs/STATUS.md tests/test_cli.py
git commit -m "docs: update Rytm 12-pad matrix status"
```

---

## Task 5: Final Verification and PR Preparation

**Files:**
- Create: `docs/superpowers/plans/2026-05-19-rytm-12-pad-machine-matrix-pr-body.md`

- [ ] **Step 1: Run focused verification**

Run:

```bash
python -m pytest tests/test_data_rytm_machine_catalog.py tests/test_rytm_machine_matrix_report.py tests/test_cli.py tests/test_cli_coverage.py tests/test_real_midi_passive_cli_safety.py -n 0
```

Expected: PASS.

- [ ] **Step 2: Run architecture gate**

Run:

```bash
python -m pytest tests/architecture/ -q
```

Expected: PASS.

- [ ] **Step 3: Run fast suite**

Run:

```bash
python -m pytest -m fast
```

Expected: PASS.

- [ ] **Step 4: Run full suite**

Run:

```bash
python -m pytest
```

Expected: PASS.

- [ ] **Step 5: Run lint trio**

Run:

```bash
python -m ruff check .
python -m black --check --target-version=py311 .
python -m isort --profile black --check-only .
git diff --check
```

Expected: all PASS.

- [ ] **Step 6: Create PR body file**

Create `docs/superpowers/plans/2026-05-19-rytm-12-pad-machine-matrix-pr-body.md` with this filled body:

````markdown
# Summary

Adds a passive Analog Rytm MK2 12-pad machine compatibility matrix. The new data/report/CLI surface validates 33 selectable machines, 12 pads, and 116 legal pad-machine slots from the OS 1.72 pad table. Pad 10 is explicitly represented as OH / Open Hihat; XT Classic remains limited to pads 6-8.

## What changed

- Added `rytm_randomizer/data/rytm_machine_catalog.py` as the passive Rytm OS 1.72 machine/pad compatibility source of truth.
- Added `rytm_randomizer/reports/rytm_machine_matrix.py` for the passive operator report.
- Added `python -m rytm_randomizer.cli rytm-12-pad-machine-matrix-report`.
- Updated README/status docs and passive CLI safety coverage.

## Why this matters

This is the safe foundation for 12-pad Rytm mutation, snapshot-mode mutation, and audio-analyzer machine selection. It gives the software an auditable legality map before any armed 12-pad runtime sends are enabled.

## Test plan

```bash
python -m pytest tests/test_data_rytm_machine_catalog.py tests/test_rytm_machine_matrix_report.py tests/test_cli.py tests/test_cli_coverage.py tests/test_real_midi_passive_cli_safety.py -n 0
python -m pytest tests/architecture/ -q
python -m pytest -m fast
python -m pytest
python -m ruff check .
python -m black --check --target-version=py311 .
python -m isort --profile black --check-only .
git diff --check
```

- [ ] Local pytest passes (full suite).
- [ ] `tests/architecture/` passes.
- [ ] Lint trio (ruff + black + isort) clean.
- [ ] Coverage stays >=95% pure-branch.
- [ ] 685/685 V1.34 parity items byte-identical.
- [ ] No new dead code.
- [ ] CI matrix green on all 3 OSes.

## Plan-requirements conformance

- [ ] **Gate 1** - 100% branch coverage on touched files; project >=95% pure-branch.
- [ ] **Gate 2** - V1.34 parity byte-identical; no fixtures regenerated.
- [ ] **Gate 3** - lint clean (ruff + black `--target-version=py311` + isort `--profile black`).
- [ ] **Gate 4** - no new dead code.
- [ ] **Gate 5** - docs updated: `README.md`, `docs/STATUS.md`, design doc, implementation plan.
- [ ] **Gate 6** - type-system hygiene: frozen dataclasses, `Final` constants, no bare `Any`.
- [ ] **Gate 7** - N/A: passive report/data path, no hot runtime path.
- [ ] **Gate 8** - test hygiene: focused fast tests with clear behavior names.
- [ ] **Gate 9** - module organization: data/report subpackages only, no new top-level package.
- [ ] **Gate 10** - N/A: no string-literal runtime dispatch refactor.
- [ ] **Gate 11** - N/A: no shared fixture additions.
- [ ] **Gate 12** - `Final` constants on module-level constants.
- [ ] **Gate 13** - N/A: no env var reads.
- [ ] **Gate 14** - maintainability: scope bounded to one passive data/report/CLI surface.
- [ ] **Gate 15** - N/A: no new reusable learned rule extracted.
- [ ] **Gate 16** - one branch/one PR against `modularize-v1.34`; no stacked PR.

## Strict rules - non-negotiables

- [ ] **No hardware in tests** - no test opens a real MIDI port; no test mutates a connected device.
- [ ] **Lazy MIDI imports** - no new eager `mido` or `python-rtmidi` imports.
- [ ] **Hardware-pinned packages** - `mido==1.3.3` and `python-rtmidi==1.5.8` not bumped.
- [ ] **Passive default** - `python -m rytm_randomizer.cli` does not open a real port.
- [ ] **No stacked PRs** - this PR's base is `modularize-v1.34`.
- [ ] **No `--no-verify`** - pre-commit hooks were not bypassed.

## Plan document

Plan doc: `docs/superpowers/plans/2026-05-19-rytm-12-pad-machine-matrix.md`

Design doc: `docs/superpowers/specs/2026-05-19-rytm-12-pad-machine-matrix-design.md`

## Reviewer notes

- Passive/read-only only.
- No hardware sends.
- No V1.34 parity fixture regeneration.
- No new top-level package.
````

- [ ] **Step 7: Commit PR body**

Run:

```bash
git add -- docs/superpowers/plans/2026-05-19-rytm-12-pad-machine-matrix-pr-body.md
git commit -m "docs: prepare Rytm machine matrix PR body"
```

- [ ] **Step 8: Push and open a draft PR**

Run:

```bash
git push -u origin codex/rytm-12-pad-machine-matrix-lf
gh pr create --base modularize-v1.34 --head codex/rytm-12-pad-machine-matrix-lf --title "[codex] Add passive Rytm 12-pad machine matrix" --body-file docs/superpowers/plans/2026-05-19-rytm-12-pad-machine-matrix-pr-body.md --draft
```

Expected: draft PR opens against `modularize-v1.34`, not another PR branch.

---

## Self-Review Checklist

- The plan implements the approved design scope only.
- The first production code change is preceded by a failing test.
- No step stages unrelated CRLF/LF files.
- No step touches parity fixtures.
- No step opens a MIDI port or sends MIDI.
- No new top-level `rytm_randomizer/<family>/` package is created.
- README/status docs are updated with the new passive state.
