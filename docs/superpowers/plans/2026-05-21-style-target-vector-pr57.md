# Style Target Vector PR57 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a passive style target vector schema and report so the PR #56 style profile catalog can become deterministic planner input for future snapshot mutation routing.

**Architecture:** Keep this PR passive and data/report only. `rytm_randomizer/data/style_targets.py` owns immutable numeric target vectors keyed by `STYLE_PROFILES`, while `rytm_randomizer/reports/style_targets.py` formats deterministic operator-facing output and registers passive CLI commands through the existing `cli_registry` pattern. This PR does not read snapshots, mutate parameters, choose machines, open MIDI ports, or send MIDI.

**Tech Stack:** Python 3.11, dataclasses, `MappingProxyType`, existing passive CLI registry, pytest fast tests, architecture gate, ruff, black, isort.

---

## Scope Rules

- Start only after PR #56 has merged into `origin/modularize-v1.34`.
- Create a fresh clean-base branch from `origin/modularize-v1.34`; do not build a pushed PR from this local draft branch.
- Do not open a stacked PR.
- Do not import `mido`.
- Do not touch V1.34 parity fixtures.
- Do not add a new top-level package module.
- Keep all behavior passive and deterministic.

## File Structure

- Create `rytm_randomizer/data/style_targets.py`
  - Defines `StyleTargetVector`, the axis names, and `STYLE_TARGET_VECTORS`.
  - Depends only on standard library and `data.style_profiles`.
- Modify `rytm_randomizer/data/__init__.py`
  - Re-export `STYLE_TARGET_VECTOR_AXES`, `STYLE_TARGET_VECTORS`, and `StyleTargetVector`.
- Create `rytm_randomizer/reports/style_targets.py`
  - Builds and formats passive target-vector catalog and inspection reports.
  - Registers `style-target-report` and `inspect-style-target`.
- Modify `rytm_randomizer/cli.py`
  - Adds lazy command entries for the new passive report commands.
- Modify `rytm_randomizer/help_text.py`
  - Adds top-level usage/help and command-specific help.
- Modify `tests/test_style_targets_report.py`
  - New focused fast tests for data, report formatting, parser behavior, and handler behavior.
- Modify `tests/test_cli.py`
  - Adds subprocess CLI tests for the two new commands and safe failures.
- Modify `tests/fixtures/cli_help_expected.txt`
  - Updates top-level help fixture.
- Modify `README.md`, `docs/STATUS.md`, and `docs/ARCHITECTURE_DIAGRAMS.md`
  - Documents the passive target-vector layer and keeps docs freshness gates green.

---

### Task 1: Add Failing Data-Layer Tests

**Files:**
- Create: `tests/test_style_targets_report.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_style_targets_report.py` with:

```python
import pytest

from rytm_randomizer.data.style_profiles import STYLE_PROFILES

pytestmark = pytest.mark.fast


def test_style_target_vectors_cover_every_style_profile():
    from rytm_randomizer.data.style_targets import STYLE_TARGET_VECTORS

    assert set(STYLE_TARGET_VECTORS) == set(STYLE_PROFILES)


def test_style_target_vector_axes_are_stable_and_bounded():
    from rytm_randomizer.data.style_targets import (
        STYLE_TARGET_VECTOR_AXES,
        STYLE_TARGET_VECTORS,
    )

    assert STYLE_TARGET_VECTOR_AXES == (
        "low_end_weight",
        "transient_density",
        "attack_sharpness",
        "decay_tail",
        "darkness",
        "metallicity",
        "noise_grit",
        "drive_pressure",
        "space_depth",
        "motion_amount",
        "repetition_hypnosis",
        "percussive_density",
        "tonal_center_weight",
        "industrial_edge",
        "minimal_restraint",
        "warehouse_intensity",
    )

    for key, vector in STYLE_TARGET_VECTORS.items():
        assert vector.key == key
        mapping = vector.as_mapping()
        assert tuple(mapping) == STYLE_TARGET_VECTOR_AXES
        for axis in STYLE_TARGET_VECTOR_AXES:
            assert 0 <= mapping[axis] <= 100


def test_style_target_vectors_encode_expected_musical_intent():
    from rytm_randomizer.data.style_targets import STYLE_TARGET_VECTORS

    birmingham = STYLE_TARGET_VECTORS["birmingham_pressure"]
    detroit = STYLE_TARGET_VECTORS["detroit_minimal"]
    industrial = STYLE_TARGET_VECTORS["industrial_dark"]
    hardgroove = STYLE_TARGET_VECTORS["hardgroove_percussive"]

    assert birmingham.drive_pressure >= 85
    assert industrial.noise_grit == 100
    assert hardgroove.percussive_density >= 85
    assert detroit.minimal_restraint >= 85
    assert detroit.space_depth < industrial.space_depth
```

- [ ] **Step 2: Run the failing tests**

Run:

```bash
python -m pytest tests/test_style_targets_report.py -n 0
```

Expected: fails with `ModuleNotFoundError: No module named 'rytm_randomizer.data.style_targets'`.

---

### Task 2: Implement the Style Target Data Module

**Files:**
- Create: `rytm_randomizer/data/style_targets.py`
- Modify: `rytm_randomizer/data/__init__.py`
- Test: `tests/test_style_targets_report.py`

- [ ] **Step 1: Add the data module**

Create `rytm_randomizer/data/style_targets.py`:

```python
"""Passive numeric style target vectors for snapshot-routing planners."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import Final

from .style_profiles import STYLE_PROFILES

STYLE_TARGET_VECTOR_AXES: Final[tuple[str, ...]] = (
    "low_end_weight",
    "transient_density",
    "attack_sharpness",
    "decay_tail",
    "darkness",
    "metallicity",
    "noise_grit",
    "drive_pressure",
    "space_depth",
    "motion_amount",
    "repetition_hypnosis",
    "percussive_density",
    "tonal_center_weight",
    "industrial_edge",
    "minimal_restraint",
    "warehouse_intensity",
)


@dataclass(frozen=True)
class StyleTargetVector:
    """Bounded 0-100 style target vector for passive planning."""

    key: str
    low_end_weight: int
    transient_density: int
    attack_sharpness: int
    decay_tail: int
    darkness: int
    metallicity: int
    noise_grit: int
    drive_pressure: int
    space_depth: int
    motion_amount: int
    repetition_hypnosis: int
    percussive_density: int
    tonal_center_weight: int
    industrial_edge: int
    minimal_restraint: int
    warehouse_intensity: int

    def as_mapping(self) -> Mapping[str, int]:
        """Return axis values in stable report order."""

        return MappingProxyType(
            {
                "low_end_weight": self.low_end_weight,
                "transient_density": self.transient_density,
                "attack_sharpness": self.attack_sharpness,
                "decay_tail": self.decay_tail,
                "darkness": self.darkness,
                "metallicity": self.metallicity,
                "noise_grit": self.noise_grit,
                "drive_pressure": self.drive_pressure,
                "space_depth": self.space_depth,
                "motion_amount": self.motion_amount,
                "repetition_hypnosis": self.repetition_hypnosis,
                "percussive_density": self.percussive_density,
                "tonal_center_weight": self.tonal_center_weight,
                "industrial_edge": self.industrial_edge,
                "minimal_restraint": self.minimal_restraint,
                "warehouse_intensity": self.warehouse_intensity,
            }
        )


def _target(
    key: str,
    *,
    low_end_weight: int,
    transient_density: int,
    attack_sharpness: int,
    decay_tail: int,
    darkness: int,
    metallicity: int,
    noise_grit: int,
    drive_pressure: int,
    space_depth: int,
    motion_amount: int,
    repetition_hypnosis: int,
    percussive_density: int,
    tonal_center_weight: int,
    industrial_edge: int,
    minimal_restraint: int,
    warehouse_intensity: int,
) -> StyleTargetVector:
    return StyleTargetVector(
        key=key,
        low_end_weight=low_end_weight,
        transient_density=transient_density,
        attack_sharpness=attack_sharpness,
        decay_tail=decay_tail,
        darkness=darkness,
        metallicity=metallicity,
        noise_grit=noise_grit,
        drive_pressure=drive_pressure,
        space_depth=space_depth,
        motion_amount=motion_amount,
        repetition_hypnosis=repetition_hypnosis,
        percussive_density=percussive_density,
        tonal_center_weight=tonal_center_weight,
        industrial_edge=industrial_edge,
        minimal_restraint=minimal_restraint,
        warehouse_intensity=warehouse_intensity,
    )


_STYLE_TARGET_VECTOR_ITEMS: Final[tuple[StyleTargetVector, ...]] = (
    _target(
        "detroit_minimal",
        low_end_weight=70,
        transient_density=55,
        attack_sharpness=65,
        decay_tail=30,
        darkness=40,
        metallicity=35,
        noise_grit=20,
        drive_pressure=35,
        space_depth=25,
        motion_amount=35,
        repetition_hypnosis=90,
        percussive_density=45,
        tonal_center_weight=45,
        industrial_edge=15,
        minimal_restraint=95,
        warehouse_intensity=50,
    ),
    _target(
        "mills_hypnotic",
        low_end_weight=65,
        transient_density=75,
        attack_sharpness=85,
        decay_tail=35,
        darkness=50,
        metallicity=85,
        noise_grit=45,
        drive_pressure=70,
        space_depth=60,
        motion_amount=90,
        repetition_hypnosis=100,
        percussive_density=70,
        tonal_center_weight=55,
        industrial_edge=45,
        minimal_restraint=55,
        warehouse_intensity=80,
    ),
    _target(
        "hood_stripped",
        low_end_weight=80,
        transient_density=45,
        attack_sharpness=80,
        decay_tail=25,
        darkness=50,
        metallicity=35,
        noise_grit=35,
        drive_pressure=65,
        space_depth=15,
        motion_amount=25,
        repetition_hypnosis=90,
        percussive_density=35,
        tonal_center_weight=50,
        industrial_edge=25,
        minimal_restraint=100,
        warehouse_intensity=65,
    ),
    _target(
        "ur_machine_funk",
        low_end_weight=70,
        transient_density=70,
        attack_sharpness=75,
        decay_tail=35,
        darkness=40,
        metallicity=55,
        noise_grit=45,
        drive_pressure=60,
        space_depth=35,
        motion_amount=70,
        repetition_hypnosis=75,
        percussive_density=75,
        tonal_center_weight=60,
        industrial_edge=35,
        minimal_restraint=55,
        warehouse_intensity=65,
    ),
    _target(
        "hardgroove_percussive",
        low_end_weight=75,
        transient_density=85,
        attack_sharpness=75,
        decay_tail=40,
        darkness=40,
        metallicity=45,
        noise_grit=55,
        drive_pressure=70,
        space_depth=30,
        motion_amount=70,
        repetition_hypnosis=75,
        percussive_density=95,
        tonal_center_weight=45,
        industrial_edge=35,
        minimal_restraint=40,
        warehouse_intensity=75,
    ),
    _target(
        "birmingham_pressure",
        low_end_weight=85,
        transient_density=80,
        attack_sharpness=85,
        decay_tail=25,
        darkness=85,
        metallicity=65,
        noise_grit=90,
        drive_pressure=95,
        space_depth=20,
        motion_amount=65,
        repetition_hypnosis=90,
        percussive_density=75,
        tonal_center_weight=35,
        industrial_edge=95,
        minimal_restraint=45,
        warehouse_intensity=95,
    ),
    _target(
        "industrial_dark",
        low_end_weight=80,
        transient_density=80,
        attack_sharpness=80,
        decay_tail=45,
        darkness=100,
        metallicity=90,
        noise_grit=100,
        drive_pressure=90,
        space_depth=35,
        motion_amount=70,
        repetition_hypnosis=75,
        percussive_density=80,
        tonal_center_weight=30,
        industrial_edge=100,
        minimal_restraint=30,
        warehouse_intensity=90,
    ),
    _target(
        "deep_dark_hypnosis",
        low_end_weight=85,
        transient_density=45,
        attack_sharpness=45,
        decay_tail=70,
        darkness=95,
        metallicity=35,
        noise_grit=45,
        drive_pressure=55,
        space_depth=85,
        motion_amount=65,
        repetition_hypnosis=100,
        percussive_density=45,
        tonal_center_weight=65,
        industrial_edge=35,
        minimal_restraint=65,
        warehouse_intensity=60,
    ),
    _target(
        "warehouse_peak",
        low_end_weight=90,
        transient_density=90,
        attack_sharpness=90,
        decay_tail=35,
        darkness=65,
        metallicity=65,
        noise_grit=70,
        drive_pressure=85,
        space_depth=55,
        motion_amount=85,
        repetition_hypnosis=85,
        percussive_density=85,
        tonal_center_weight=45,
        industrial_edge=65,
        minimal_restraint=35,
        warehouse_intensity=100,
    ),
)

STYLE_TARGET_VECTORS: Final[Mapping[str, StyleTargetVector]] = MappingProxyType(
    {target.key: target for target in _STYLE_TARGET_VECTOR_ITEMS}
)

if set(STYLE_TARGET_VECTORS) != set(STYLE_PROFILES):
    raise RuntimeError("style target vectors must cover every style profile")

__all__ = [
    "STYLE_TARGET_VECTOR_AXES",
    "STYLE_TARGET_VECTORS",
    "StyleTargetVector",
]
```

- [ ] **Step 2: Re-export from the data package**

Add imports in `rytm_randomizer/data/__init__.py`:

```python
from .style_targets import STYLE_TARGET_VECTOR_AXES, STYLE_TARGET_VECTORS, StyleTargetVector
```

Add these entries to `__all__` near `STYLE_PROFILES`:

```python
    "STYLE_TARGET_VECTOR_AXES",
    "STYLE_TARGET_VECTORS",
    "StyleTargetVector",
```

- [ ] **Step 3: Run data tests**

Run:

```bash
python -m pytest tests/test_style_targets_report.py -n 0
```

Expected: the first three tests pass.

- [ ] **Step 4: Commit the data slice**

Run:

```bash
git add rytm_randomizer/data/style_targets.py rytm_randomizer/data/__init__.py tests/test_style_targets_report.py
git commit -m "feat: add style target vector data"
```

---

### Task 3: Add Passive Report Formatting

**Files:**
- Modify: `tests/test_style_targets_report.py`
- Create: `rytm_randomizer/reports/style_targets.py`

- [ ] **Step 1: Add failing report tests**

Append to `tests/test_style_targets_report.py`:

```python
def test_style_target_catalog_report_is_detached_from_source_mapping():
    from rytm_randomizer.data.style_targets import STYLE_TARGET_VECTORS
    from rytm_randomizer.reports.style_targets import (
        StyleTargetCatalogReport,
        build_style_target_catalog_report,
    )

    report = build_style_target_catalog_report()

    assert isinstance(report, StyleTargetCatalogReport)
    assert report.target_count == len(STYLE_TARGET_VECTORS)
    assert report.targets_by_key == STYLE_TARGET_VECTORS

    with pytest.raises(TypeError):
        report.targets_by_key["new_target"] = STYLE_TARGET_VECTORS["detroit_minimal"]


def test_style_target_report_formatter_is_sorted_and_passive():
    from rytm_randomizer.reports.style_targets import format_style_target_report

    lines = format_style_target_report()
    item_lines = [line for line in lines if line.startswith("- ") and ": " in line]

    assert lines[0] == "RytmRandomizer passive style target vector report"
    assert "- Purpose: numeric style intent for future snapshot mutation planning" in lines
    assert item_lines == sorted(item_lines)
    assert any(line.startswith("- birmingham_pressure:") for line in item_lines)
    assert "- no MIDI sending" in lines
    assert "- no hardware mutation" in lines


def test_style_target_inspection_is_case_insensitive_and_safe():
    from rytm_randomizer.reports.style_targets import format_style_target_inspection

    lines = format_style_target_inspection("INDUSTRIAL_DARK")

    assert lines[0] == "RytmRandomizer passive style target vector inspection"
    assert "Key: industrial_dark" in lines
    assert "Found: True" in lines
    assert "darkness: 100" in lines
    assert "noise_grit: 100" in lines
    assert "- no command execution" in lines


def test_style_target_inspection_unknown_key_reports_no_send_path():
    from rytm_randomizer.reports.style_targets import format_style_target_inspection

    lines = format_style_target_inspection("ghost_style")

    assert "Key: ghost_style" in lines
    assert "Found: False" in lines
    assert "Message: Style target not found. No MIDI was sent. No command executed." in lines
    assert "- no MIDI sending" in lines
```

- [ ] **Step 2: Run failing report tests**

Run:

```bash
python -m pytest tests/test_style_targets_report.py -n 0
```

Expected: fails with `ModuleNotFoundError: No module named 'rytm_randomizer.reports.style_targets'`.

- [ ] **Step 3: Implement report module**

Create `rytm_randomizer/reports/style_targets.py`:

```python
"""Passive style target vector reports for techno design intent."""

from __future__ import annotations

import sys
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from types import MappingProxyType
from typing import Final

from ..cli_registry import CliCommand, register
from ..data.style_targets import STYLE_TARGET_VECTOR_AXES, STYLE_TARGET_VECTORS, StyleTargetVector
from .formatter import SAFETY_SECTION_HEADER, PassiveReportHeader, passive_report_lines

REPORT_TITLE: Final[str] = "RytmRandomizer passive style target vector report"
INSPECT_TITLE: Final[str] = "RytmRandomizer passive style target vector inspection"
SOURCE_MODULE: Final[str] = "reports.style_targets"
SAFETY_LINES: Final[tuple[str, ...]] = (
    "passive/read-only",
    "metadata only",
    "no MIDI sending",
    "no port opening",
    "no command execution",
    "no hardware mutation",
    "no hardware required",
)
_HEADER: Final[PassiveReportHeader] = PassiveReportHeader(
    title=REPORT_TITLE,
    source_module=SOURCE_MODULE,
)
_INSPECT_HEADER: Final[PassiveReportHeader] = PassiveReportHeader(
    title=INSPECT_TITLE,
    source_module=SOURCE_MODULE,
)


@dataclass(frozen=True)
class StyleTargetCatalogReport:
    """Passive catalog report for all style target vectors."""

    target_count: int
    targets_by_key: Mapping[str, StyleTargetVector]


def _safety_lines() -> list[str]:
    return [SAFETY_SECTION_HEADER, *[f"- {line}" for line in SAFETY_LINES]]


def _style_targets_by_key() -> Mapping[str, StyleTargetVector]:
    return MappingProxyType(dict(STYLE_TARGET_VECTORS))


def build_style_target_catalog_report() -> StyleTargetCatalogReport:
    """Return passive catalog data for all style target vectors."""

    targets_by_key = _style_targets_by_key()
    return StyleTargetCatalogReport(
        target_count=len(targets_by_key),
        targets_by_key=targets_by_key,
    )


def _axis_line(axis: str, value: int) -> str:
    return f"{axis}: {value}"


def _target_lines(target: StyleTargetVector) -> list[str]:
    mapping = target.as_mapping()
    return [
        f"Key: {target.key}",
        "Axes:",
        *[_axis_line(axis, mapping[axis]) for axis in STYLE_TARGET_VECTOR_AXES],
    ]


def format_style_target_report(
    report: StyleTargetCatalogReport | None = None,
) -> list[str]:
    """Return deterministic catalog lines for all style target vectors."""

    source_report = build_style_target_catalog_report() if report is None else report
    lines = [
        "Summary:",
        f"- Targets: {source_report.target_count}",
        "- Purpose: numeric style intent for future snapshot mutation planning",
        "Targets:",
    ]
    for key in sorted(source_report.targets_by_key):
        target = source_report.targets_by_key[key]
        mapping = target.as_mapping()
        strongest_axes = sorted(mapping.items(), key=lambda item: (-item[1], item[0]))[:3]
        strongest_text = ", ".join(f"{axis}={value}" for axis, value in strongest_axes)
        lines.append(f"- {target.key}: {strongest_text}")
    lines.extend(_safety_lines())
    return passive_report_lines(_HEADER, lines)


def format_style_target_inspection(key: str) -> list[str]:
    """Return deterministic detail lines for one style target vector."""

    normalized_key = str(key).lower()
    target = STYLE_TARGET_VECTORS.get(normalized_key)
    if target is None:
        lines = [
            f"Key: {normalized_key}",
            "Found: False",
            "Message: Style target not found. No MIDI was sent. No command executed.",
        ]
        lines.extend(_safety_lines())
        return passive_report_lines(_INSPECT_HEADER, lines)

    lines = [
        f"Key: {target.key}",
        "Found: True",
        *_target_lines(target)[1:],
    ]
    lines.extend(_safety_lines())
    return passive_report_lines(_INSPECT_HEADER, lines)


def _parse_no_args(argv: Sequence[str]) -> dict[str, object]:
    if argv:
        raise ValueError("command takes no arguments")
    return {}


def _parse_key(argv: Sequence[str]) -> dict[str, object]:
    if len(argv) != 1:
        raise ValueError("command requires exactly one key")
    return {"key": argv[0]}


def _write_lines(lines: Sequence[str]) -> int:
    sys.stdout.write("\n".join(lines))
    sys.stdout.write("\n")
    return 0


def _handle_style_target_report() -> int:
    return _write_lines(format_style_target_report())


def _handle_style_target_inspection(key: str) -> int:
    lines = format_style_target_inspection(key)
    output = "\n".join(lines)
    if "Found: True" in lines:
        sys.stdout.write(f"{output}\n")
        return 0
    sys.stderr.write(f"{output}\n")
    return 1


STYLE_TARGET_REPORT_CLI_COMMAND: Final[CliCommand] = CliCommand(
    name="style-target-report",
    summary="Print the passive style target vector report.",
    args_parser=_parse_no_args,
    handler=_handle_style_target_report,
)
INSPECT_STYLE_TARGET_CLI_COMMAND: Final[CliCommand] = CliCommand(
    name="inspect-style-target",
    summary="Inspect passive style target vector metadata by key.",
    args_parser=_parse_key,
    handler=_handle_style_target_inspection,
)

register(STYLE_TARGET_REPORT_CLI_COMMAND)
register(INSPECT_STYLE_TARGET_CLI_COMMAND)

__all__ = [
    "INSPECT_STYLE_TARGET_CLI_COMMAND",
    "REPORT_TITLE",
    "SAFETY_LINES",
    "SOURCE_MODULE",
    "STYLE_TARGET_REPORT_CLI_COMMAND",
    "StyleTargetCatalogReport",
    "build_style_target_catalog_report",
    "format_style_target_inspection",
    "format_style_target_report",
]
```

- [ ] **Step 4: Run report tests**

Run:

```bash
python -m pytest tests/test_style_targets_report.py -n 0
```

Expected: all current style target report tests pass.

- [ ] **Step 5: Commit the report slice**

Run:

```bash
git add rytm_randomizer/reports/style_targets.py tests/test_style_targets_report.py
git commit -m "feat: add passive style target report"
```

---

### Task 4: Wire Passive CLI Commands

**Files:**
- Modify: `tests/test_style_targets_report.py`
- Modify: `tests/test_cli.py`
- Modify: `rytm_randomizer/cli.py`
- Modify: `rytm_randomizer/help_text.py`
- Modify: `tests/fixtures/cli_help_expected.txt`

- [ ] **Step 1: Add failing command-handler tests**

Append to `tests/test_style_targets_report.py`:

```python
def test_style_target_cli_command_parsers_accept_expected_arguments():
    from rytm_randomizer.reports.style_targets import (
        INSPECT_STYLE_TARGET_CLI_COMMAND,
        STYLE_TARGET_REPORT_CLI_COMMAND,
    )

    assert STYLE_TARGET_REPORT_CLI_COMMAND.args_parser([]) == {}
    assert INSPECT_STYLE_TARGET_CLI_COMMAND.args_parser(["detroit_minimal"]) == {
        "key": "detroit_minimal"
    }


@pytest.mark.parametrize(
    ("command_name", "argv", "message"),
    [
        ("STYLE_TARGET_REPORT_CLI_COMMAND", ["extra"], "command takes no arguments"),
        ("INSPECT_STYLE_TARGET_CLI_COMMAND", [], "command requires exactly one key"),
        (
            "INSPECT_STYLE_TARGET_CLI_COMMAND",
            ["one", "two"],
            "command requires exactly one key",
        ),
    ],
)
def test_style_target_cli_command_parsers_reject_bad_arguments(
    command_name,
    argv,
    message,
):
    import rytm_randomizer.reports.style_targets as style_targets

    command = getattr(style_targets, command_name)
    with pytest.raises(ValueError, match=message):
        command.args_parser(argv)


def test_style_target_report_handler_writes_stdout(capsys):
    from rytm_randomizer.reports.style_targets import STYLE_TARGET_REPORT_CLI_COMMAND

    assert STYLE_TARGET_REPORT_CLI_COMMAND.handler() == 0
    captured = capsys.readouterr()

    assert "RytmRandomizer passive style target vector report" in captured.out
    assert "- no MIDI sending" in captured.out
    assert captured.err == ""


def test_style_target_inspect_handler_routes_known_key_to_stdout(capsys):
    from rytm_randomizer.reports.style_targets import INSPECT_STYLE_TARGET_CLI_COMMAND

    kwargs = INSPECT_STYLE_TARGET_CLI_COMMAND.args_parser(["detroit_minimal"])

    assert INSPECT_STYLE_TARGET_CLI_COMMAND.handler(**kwargs) == 0
    captured = capsys.readouterr()

    assert "Found: True" in captured.out
    assert "minimal_restraint:" in captured.out
    assert captured.err == ""


def test_style_target_inspect_handler_routes_unknown_key_to_stderr(capsys):
    from rytm_randomizer.reports.style_targets import INSPECT_STYLE_TARGET_CLI_COMMAND

    kwargs = INSPECT_STYLE_TARGET_CLI_COMMAND.args_parser(["ghost_style"])

    assert INSPECT_STYLE_TARGET_CLI_COMMAND.handler(**kwargs) == 1
    captured = capsys.readouterr()

    assert captured.out == ""
    assert "Found: False" in captured.err
    assert "No MIDI was sent" in captured.err
```

Append to `tests/test_cli.py`:

```python
def test_style_target_report_command_exits_zero_and_is_passive():
    result = run_cli("style-target-report")
    output = normalize_newlines(result.stdout)

    assert result.returncode == 0
    assert "RytmRandomizer passive style target vector report" in output
    assert "- Targets: 9" in output
    assert "- no MIDI sending" in output
    assert result.stderr == ""


def test_inspect_style_target_known_key_exits_zero():
    result = run_cli("inspect-style-target", "birmingham_pressure")
    output = normalize_newlines(result.stdout)

    assert result.returncode == 0
    assert "RytmRandomizer passive style target vector inspection" in output
    assert "Key: birmingham_pressure" in output
    assert "drive_pressure: 95" in output
    assert result.stderr == ""


def test_inspect_style_target_unknown_key_fails_safely():
    result = run_cli("inspect-style-target", "ghost_style")

    assert result.returncode == 1
    assert result.stdout == ""
    assert "Style target not found" in result.stderr
    assert "No MIDI was sent" in result.stderr


def test_style_target_report_rejects_unknown_argument():
    result = run_cli("style-target-report", "--mutate")

    assert result.returncode == 2
    assert result.stdout == ""
    assert result.stderr == USAGE + "\n"
```

- [ ] **Step 2: Run failing CLI tests**

Run:

```bash
python -m pytest tests/test_style_targets_report.py tests/test_cli.py -n 0 -k "style_target or style_targets"
```

Expected: subprocess CLI tests fail because `cli.py` and `help_text.py` do not expose the commands yet.

- [ ] **Step 3: Add lazy command dispatch**

In `rytm_randomizer/cli.py`, add these entries to `lazy_commands`:

```python
        "style-target-report": (
            "rytm_randomizer.reports.style_targets",
            "STYLE_TARGET_REPORT_CLI_COMMAND",
        ),
        "inspect-style-target": (
            "rytm_randomizer.reports.style_targets",
            "INSPECT_STYLE_TARGET_CLI_COMMAND",
        ),
```

- [ ] **Step 4: Add help text**

In `rytm_randomizer/help_text.py`, add the commands to `USAGE`, top-level help usage, top-level command list, and `HELP_TEXT`.

Add a helper function near `_style_profile_report_help`:

```python
def _style_target_report_help():
    from .reports.style_targets import SAFETY_LINES

    return f"""RytmRandomizer passive CLI: style-target-report

Usage:
  python -m rytm_randomizer.cli style-target-report
  python -m rytm_randomizer.cli style-target-report --help

Behavior:
  Prints passive numeric style target vectors for future snapshot planning.

Safety:
{_safety_block(SAFETY_LINES)}"""
```

Add these `HELP_TEXT` entries:

```python
    "style-target-report": _style_target_report_help,
    "inspect-style-target": """RytmRandomizer passive CLI: inspect-style-target

Usage:
  python -m rytm_randomizer.cli inspect-style-target <key>
  python -m rytm_randomizer.cli inspect-style-target --help

Behavior:
  Displays passive numeric style target vector metadata for an existing key.

Safety:
  passive/read-only
  metadata only
  no MIDI sending
  no port opening
  no command execution
  no hardware mutation
  no hardware required""",
```

Update the top-level command descriptions with:

```text
  style-target-report
                     Print the passive style target vector report.
  inspect-style-target
                     Inspect passive style target vector metadata by key.
```

- [ ] **Step 5: Refresh top-level help fixture**

Run:

```bash
python -m rytm_randomizer.cli --help > tests/fixtures/cli_help_expected.txt
```

Use PowerShell equivalent if needed:

```powershell
python -m rytm_randomizer.cli --help | Set-Content -Encoding UTF8 tests\fixtures\cli_help_expected.txt
```

- [ ] **Step 6: Run focused CLI tests**

Run:

```bash
python -m pytest tests/test_style_targets_report.py tests/test_cli.py -n 0 -k "style_target or style_targets or top_level_help"
```

Expected: focused CLI tests pass.

- [ ] **Step 7: Commit the CLI slice**

Run:

```bash
git add rytm_randomizer/cli.py rytm_randomizer/help_text.py tests/test_style_targets_report.py tests/test_cli.py tests/fixtures/cli_help_expected.txt
git commit -m "feat: expose passive style target CLI"
```

---

### Task 5: Update Docs and Status

**Files:**
- Modify: `README.md`
- Modify: `docs/STATUS.md`
- Modify: `docs/ARCHITECTURE_DIAGRAMS.md`

- [ ] **Step 1: Update README command examples**

Add these examples near the style profile CLI examples:

```markdown
python -m rytm_randomizer.cli style-target-report   # passive numeric style target vectors for future snapshot planning
python -m rytm_randomizer.cli inspect-style-target birmingham_pressure   # inspect one passive target vector
```

Add one short paragraph after the style profile paragraph:

```markdown
Style target vectors turn those style profiles into bounded 0-100 planning axes such as low-end weight, transient density, darkness, metallicity, grit, motion, hypnosis, and warehouse intensity. They are passive numeric intent only: they do not choose machines, mutate snapshots, send MIDI, or touch hardware.
```

- [ ] **Step 2: Update status**

Add one dated bullet near the top of `docs/STATUS.md`:

```markdown
- 2026-05-21: Style target vector PR57 prepared after the passive style-profile foundation. Added a passive numeric target-vector layer for future snapshot mutation planning, with CLI/report visibility and no MIDI or hardware behavior.
```

- [ ] **Step 3: Update architecture diagrams**

In `docs/ARCHITECTURE_DIAGRAMS.md`, update the data/report module summaries that list `style_profiles` so they also include `style_targets`.

Use phrasing like:

```text
data/{param_maps,plans,profiles,scenes,scene_display,modes,rytm_machine_catalog,style_profiles,style_targets}.py
```

and:

```text
reports/{formatter,rytm_machine_matrix,rytm_snapshot_pad_compatibility,rytm_snapshot_intelligence,rytm_snapshot_mutation_preview,style_profiles,style_targets}.py
```

- [ ] **Step 4: Run docs freshness gates**

Run:

```bash
python -m pytest tests/architecture/test_readme_freshness.py tests/architecture/test_plan_requirements_referenced.py -q
```

Expected: passes.

- [ ] **Step 5: Commit docs**

Run:

```bash
git add README.md docs/STATUS.md docs/ARCHITECTURE_DIAGRAMS.md
git commit -m "docs: describe style target vectors"
```

---

### Task 6: Full Verification and PR Prep

**Files:**
- Review all changed files from Tasks 1-5.

- [ ] **Step 1: Run focused tests**

Run:

```bash
python -m pytest tests/test_style_targets_report.py tests/test_cli.py tests/test_data_layer.py -n 0 -k "style_target or style_targets or style_profile or data_layer_exports_are_non_empty"
```

Expected: all selected tests pass.

- [ ] **Step 2: Run architecture tests**

Run:

```bash
python -m pytest tests/architecture/ -q
```

Expected: architecture gate passes.

- [ ] **Step 3: Run fast tests**

Run:

```bash
python -m pytest -m fast
```

Expected: fast suite passes.

- [ ] **Step 4: Run full suite**

Run:

```bash
python -m pytest
```

Expected: full suite passes.

- [ ] **Step 5: Run lint**

Run:

```bash
python -m ruff check .
python -m black --check --target-version=py311 .
python -m isort --profile black --check-only .
```

Expected: all lint commands pass.

- [ ] **Step 6: Run review gate**

Run:

```bash
python scripts/code_review_gate.py --mode cli
```

Expected: mechanical review gate passes, including V1.34 parity.

- [ ] **Step 7: Confirm clean real diff**

Run:

```bash
git diff --check
git diff --name-only --ignore-space-at-eol
git status --short
```

Expected: no whitespace errors; only intentional PR57 files appear as changed or all changes are committed.

- [ ] **Step 8: Open PR only after verification**

Use the repository PR helper if available:

```bash
just pr
```

If raw commands are needed:

```bash
git push -u origin codex/style-target-vector-pr57
gh pr create --base modularize-v1.34 --title "feat: add passive style target vectors" --body-file path/to/pr-body.md
```

Expected: ready PR against `modularize-v1.34`, not against another feature branch.

## PR Body Notes

Include these summary points:

- Adds passive numeric style target vectors keyed by every style profile.
- Adds passive report and inspection CLI commands.
- Adds no MIDI sending, no port opening, no snapshot mutation, and no hardware behavior.
- Prepares the next routing slice by making style intent machine-readable.

Include the required 18-gate checklist and strict-rules confirmation block from `.github/PULL_REQUEST_TEMPLATE.md`.

## Self-Review Notes

- Spec coverage: implements PR57 from the style routing design: style target vector schema and passive report.
- Deferred scope: snapshot routing, slider blending, Analog Four routing, analyzer DSP, and armed rendering remain separate PRs.
- Type consistency: `StyleTargetVector`, `STYLE_TARGET_VECTOR_AXES`, and `STYLE_TARGET_VECTORS` names are used consistently across data, report, tests, and CLI.
- Safety consistency: report commands are metadata-only and keep the same safety lines as style-profile reports.
