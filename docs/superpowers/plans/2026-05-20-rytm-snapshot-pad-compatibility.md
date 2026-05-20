# Rytm Snapshot Pad Compatibility Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a passive Rytm snapshot-pad compatibility report that explains which of the 12 Analog Rytm pads are ready for snapshot-based mutation and which are legally selectable but not mutation-ready yet.

**Architecture:** Build on the merged Rytm 12-pad machine matrix. Add a focused passive report module under `rytm_randomizer/reports/`, register one passive CLI command via `CliCommand`, and update help/docs without touching armed runtime, MIDI senders, or Device Strategy implementations.

**Tech Stack:** Python 3.11-compatible stdlib, pytest, existing `CliCommand` registry, existing passive report formatter, existing Rytm machine catalog.

---

## File Structure

- Create: `rytm_randomizer/reports/rytm_snapshot_pad_compatibility.py`
  - Owns immutable report dataclasses, readiness calculation, formatting, and CLI command registration.
- Create: `tests/test_rytm_snapshot_pad_compatibility_report.py`
  - Focused data/report tests for the new passive report.
- Modify: `rytm_randomizer/cli.py`
  - Lazy-register the new CLI command beside `rytm-12-pad-machine-matrix-report`.
- Modify: `rytm_randomizer/help_text.py`
  - Add top-level help, usage, and command-specific help text.
- Modify: `tests/test_cli.py`
  - Add help and command coverage for the passive CLI command.
- Modify: `tests/test_real_midi_passive_cli_safety.py`
  - Include the new command in passive no-real-MIDI sweeps.
- Modify: `README.md`
  - Mention the new passive snapshot-pad compatibility report.
- Modify: `docs/STATUS.md`
  - Add one current checkpoint line.
- Create: `tests/fixtures/cli_rytm_snapshot_pad_compatibility_report_help_expected.txt`
  - Golden help fixture for the new CLI help entry.

---

### Task 1: Add Failing Report Tests

**Files:**
- Create: `tests/test_rytm_snapshot_pad_compatibility_report.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_rytm_snapshot_pad_compatibility_report.py`:

```python
"""Tests for the passive Rytm snapshot-pad compatibility report."""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.fast

from rytm_randomizer.reports.rytm_snapshot_pad_compatibility import (
    build_rytm_snapshot_pad_compatibility_report,
    format_rytm_snapshot_pad_compatibility_report,
)


def test_build_report_summarizes_snapshot_readiness() -> None:
    report = build_rytm_snapshot_pad_compatibility_report()

    assert report.pad_count == 12
    assert report.snapshot_ready_pad_count == 4
    assert report.blocked_pad_count == 8
    assert report.allowed_slot_count == 116


def test_build_report_marks_v134_backed_pads_ready() -> None:
    report = build_rytm_snapshot_pad_compatibility_report()

    for pad in (1, 2, 3, 4):
        pad_report = report.pads_by_pad[pad]
        assert pad_report.snapshot_ready is True
        assert pad_report.mutable_machine_count > 0
        assert "V1.34-backed" in pad_report.readiness_reason


def test_build_report_blocks_pad_10_without_tom_engine_leakage() -> None:
    report = build_rytm_snapshot_pad_compatibility_report()
    pad_10 = report.pads_by_pad[10]

    assert pad_10.track_code == "OH"
    assert pad_10.label == "Open Hihat"
    assert pad_10.snapshot_ready is False
    assert pad_10.mutable_machine_count == 0
    assert pad_10.machine_selectable_count == 8
    assert "XT Classic" not in pad_10.machine_labels
    assert "not snapshot-mutable yet" in pad_10.readiness_reason


def test_format_report_is_passive_and_operator_facing() -> None:
    lines = format_rytm_snapshot_pad_compatibility_report()
    text = "\n".join(lines)

    assert lines[0] == "RytmRandomizer passive Rytm snapshot pad compatibility"
    assert "- Pads: 12" in lines
    assert "- Snapshot-ready pads: 4" in lines
    assert "- Blocked pads: 8" in lines
    assert "Pad 10 / OH / Open Hihat:" in text
    assert "Snapshot ready: False" in text
    assert "XT Classic" not in text.split("Pad 10 / OH / Open Hihat:", 1)[1].split(
        "Pad 11 / CY / Cymbal:", 1
    )[0]
    assert "- passive/read-only" in lines
    assert "- no MIDI sending" in lines
    assert "- no port opening" in lines
    assert "Source: rytm_randomizer.reports.rytm_snapshot_pad_compatibility" in lines
    assert "In-memory only: True" in lines
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```powershell
python -m pytest tests/test_rytm_snapshot_pad_compatibility_report.py -n 0
```

Expected: FAIL with `ModuleNotFoundError: No module named 'rytm_randomizer.reports.rytm_snapshot_pad_compatibility'`.

---

### Task 2: Implement the Passive Compatibility Report

**Files:**
- Create: `rytm_randomizer/reports/rytm_snapshot_pad_compatibility.py`
- Modify: `rytm_randomizer/reports/__init__.py`

- [ ] **Step 1: Add the report module**

Create `rytm_randomizer/reports/rytm_snapshot_pad_compatibility.py`:

```python
"""Passive Analog Rytm snapshot-pad compatibility report."""

from __future__ import annotations

import sys
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from types import MappingProxyType
from typing import Final

from ..cli_registry import CliCommand, register
from ..data.rytm_machine_catalog import (
    RYTM_PAD_CAPABILITIES,
    RytmMachineProfile,
    allowed_machine_profiles_for_pad,
)
from .formatter import SAFETY_SECTION_HEADER, PassiveReportHeader, passive_report_lines

REPORT_TITLE: Final[str] = "RytmRandomizer passive Rytm snapshot pad compatibility"
SOURCE_MODULE: Final[str] = "reports.rytm_snapshot_pad_compatibility"
SAFETY_LINES: Final[tuple[str, ...]] = (
    "passive/read-only",
    "no MIDI sending",
    "no port opening",
)
_HEADER: Final[PassiveReportHeader] = PassiveReportHeader(
    title=REPORT_TITLE,
    source_module=SOURCE_MODULE,
)


@dataclass(frozen=True)
class RytmSnapshotPadCompatibilityPadReport:
    """Snapshot-readiness summary for one 1-based Rytm pad."""

    pad: int
    track_code: str
    label: str
    allowed_machine_count: int
    mutable_machine_count: int
    machine_selectable_count: int
    snapshot_ready: bool
    readiness_reason: str
    machine_labels: tuple[str, ...]


@dataclass(frozen=True)
class RytmSnapshotPadCompatibilityReport:
    """Passive snapshot-pad compatibility report for the 12-pad Rytm surface."""

    pad_count: int
    snapshot_ready_pad_count: int
    blocked_pad_count: int
    allowed_slot_count: int
    pads_by_pad: Mapping[int, RytmSnapshotPadCompatibilityPadReport]


def _machine_label(profile: RytmMachineProfile) -> str:
    return f"{profile.label} (CC15 {profile.machine_value}, {profile.support_status})"


def _readiness_reason(mutable_count: int, selectable_count: int) -> str:
    if mutable_count:
        return (
            f"Snapshot-ready: {mutable_count} V1.34-backed legal machine(s); "
            f"{selectable_count} legal machine(s) are selectable only."
        )
    return (
        "Blocked: legal machines are selectable on this pad, but none are "
        "snapshot-mutable yet."
    )


def _pad_report(pad: int, track_code: str, label: str) -> RytmSnapshotPadCompatibilityPadReport:
    profiles = allowed_machine_profiles_for_pad(pad)
    mutable_count = sum(1 for profile in profiles if profile.support_status == "mutable_v134")
    selectable_count = sum(
        1 for profile in profiles if profile.support_status == "machine_selectable"
    )
    return RytmSnapshotPadCompatibilityPadReport(
        pad=pad,
        track_code=track_code,
        label=label,
        allowed_machine_count=len(profiles),
        mutable_machine_count=mutable_count,
        machine_selectable_count=selectable_count,
        snapshot_ready=mutable_count > 0,
        readiness_reason=_readiness_reason(mutable_count, selectable_count),
        machine_labels=tuple(_machine_label(profile) for profile in profiles),
    )


def build_rytm_snapshot_pad_compatibility_report() -> RytmSnapshotPadCompatibilityReport:
    """Return passive snapshot-readiness data for all 12 Rytm pads."""

    pads_by_pad: dict[int, RytmSnapshotPadCompatibilityPadReport] = {}
    allowed_slot_count = 0
    ready_count = 0

    for capability in RYTM_PAD_CAPABILITIES:
        pad_report = _pad_report(capability.pad, capability.track_code, capability.label)
        pads_by_pad[capability.pad] = pad_report
        allowed_slot_count += pad_report.allowed_machine_count
        if pad_report.snapshot_ready:
            ready_count += 1

    return RytmSnapshotPadCompatibilityReport(
        pad_count=len(RYTM_PAD_CAPABILITIES),
        snapshot_ready_pad_count=ready_count,
        blocked_pad_count=len(RYTM_PAD_CAPABILITIES) - ready_count,
        allowed_slot_count=allowed_slot_count,
        pads_by_pad=MappingProxyType(pads_by_pad),
    )


def _body_lines(report: RytmSnapshotPadCompatibilityReport) -> list[str]:
    lines = [
        "Summary:",
        f"- Pads: {report.pad_count}",
        f"- Snapshot-ready pads: {report.snapshot_ready_pad_count}",
        f"- Blocked pads: {report.blocked_pad_count}",
        f"- Allowed pad-machine slots: {report.allowed_slot_count}",
        "Pads:",
    ]

    for pad in sorted(report.pads_by_pad):
        pad_report = report.pads_by_pad[pad]
        lines.extend(
            [
                f"Pad {pad} / {pad_report.track_code} / {pad_report.label}:",
                f"  Snapshot ready: {pad_report.snapshot_ready}",
                f"  Allowed machines: {pad_report.allowed_machine_count}",
                f"  Snapshot-mutable machines: {pad_report.mutable_machine_count}",
                f"  Selectable-only machines: {pad_report.machine_selectable_count}",
                f"  Reason: {pad_report.readiness_reason}",
                "  Machines:",
            ]
        )
        lines.extend(f"    - {machine}" for machine in pad_report.machine_labels)

    lines.append(SAFETY_SECTION_HEADER)
    lines.extend(f"- {line}" for line in SAFETY_LINES)
    return lines


def format_rytm_snapshot_pad_compatibility_report(
    report: RytmSnapshotPadCompatibilityReport | None = None,
) -> list[str]:
    """Return deterministic report lines for Rytm snapshot-pad compatibility."""

    source_report = build_rytm_snapshot_pad_compatibility_report() if report is None else report
    return passive_report_lines(_HEADER, _body_lines(source_report))


def _parse_cli_args(argv: Sequence[str]) -> dict[str, object]:
    if argv:
        raise ValueError("rytm-snapshot-pad-compatibility-report takes no arguments")
    return {}


def _handle_cli_report() -> int:
    sys.stdout.write("\n".join(format_rytm_snapshot_pad_compatibility_report()))
    sys.stdout.write("\n")
    return 0


RYTM_SNAPSHOT_PAD_COMPATIBILITY_CLI_COMMAND: Final[CliCommand] = CliCommand(
    name="rytm-snapshot-pad-compatibility-report",
    summary="Print the passive Rytm snapshot-pad compatibility report.",
    args_parser=_parse_cli_args,
    handler=_handle_cli_report,
)

register(RYTM_SNAPSHOT_PAD_COMPATIBILITY_CLI_COMMAND)


__all__ = [
    "REPORT_TITLE",
    "RYTM_SNAPSHOT_PAD_COMPATIBILITY_CLI_COMMAND",
    "RytmSnapshotPadCompatibilityPadReport",
    "RytmSnapshotPadCompatibilityReport",
    "SAFETY_LINES",
    "SOURCE_MODULE",
    "build_rytm_snapshot_pad_compatibility_report",
    "format_rytm_snapshot_pad_compatibility_report",
]
```

- [ ] **Step 2: Re-export the formatter**

In `rytm_randomizer/reports/__init__.py`, add:

```python
from .rytm_snapshot_pad_compatibility import (  # noqa: F401
    build_rytm_snapshot_pad_compatibility_report,
    format_rytm_snapshot_pad_compatibility_report,
)
```

Place it next to the existing `rytm_machine_matrix` import.

- [ ] **Step 3: Run focused tests**

Run:

```powershell
python -m pytest tests/test_rytm_snapshot_pad_compatibility_report.py -n 0
```

Expected: PASS.

- [ ] **Step 4: Commit the report slice**

Run:

```powershell
git add rytm_randomizer/reports/rytm_snapshot_pad_compatibility.py rytm_randomizer/reports/__init__.py tests/test_rytm_snapshot_pad_compatibility_report.py
git commit -m "feat: add Rytm snapshot pad compatibility report"
```

---

### Task 3: Wire the Passive CLI Command

**Files:**
- Modify: `rytm_randomizer/cli.py`
- Modify: `rytm_randomizer/help_text.py`
- Modify: `tests/test_cli.py`
- Create: `tests/fixtures/cli_rytm_snapshot_pad_compatibility_report_help_expected.txt`

- [ ] **Step 1: Add failing CLI tests**

In `tests/test_cli.py`, extend the `USAGE` string to include:

```python
"behavior-parity-report | rytm-12-pad-machine-matrix-report | "
"rytm-snapshot-pad-compatibility-report | "
```

Add a help test after the matrix help test:

```python
def test_rytm_snapshot_pad_compatibility_report_help_exits_zero_and_matches_fixture():
    result = run_cli("rytm-snapshot-pad-compatibility-report", "--help")

    assert result.returncode == 0
    assert normalize_newlines(result.stdout) == fixture_text(
        "cli_rytm_snapshot_pad_compatibility_report_help_expected.txt"
    )
    assert result.stderr == ""
```

Add a command test after the matrix command test:

```python
def test_rytm_snapshot_pad_compatibility_report_command_exits_zero_and_describes_pad_10():
    result = run_cli("rytm-snapshot-pad-compatibility-report")

    output = normalize_newlines(result.stdout)
    assert result.returncode == 0
    assert "RytmRandomizer passive Rytm snapshot pad compatibility" in output
    assert "- Snapshot-ready pads: 4" in output
    assert "- Blocked pads: 8" in output
    assert "Pad 10 / OH / Open Hihat:" in output
    assert "Snapshot ready: False" in output
    assert result.stderr == ""
```

Add a README command assertion near the existing matrix README test:

```python
def test_readme_mentions_rytm_snapshot_pad_compatibility_report_command():
    text = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")

    assert "rytm-snapshot-pad-compatibility-report" in text
    assert "snapshot-pad compatibility" in text
```

Add a deterministic command test near the other deterministic tests:

```python
def test_rytm_snapshot_pad_compatibility_report_command_is_deterministic():
    first = run_cli("rytm-snapshot-pad-compatibility-report")
    second = run_cli("rytm-snapshot-pad-compatibility-report")

    assert first.returncode == 0
    assert second.returncode == 0
    assert normalize_newlines(first.stdout) == normalize_newlines(second.stdout)
    assert first.stderr == ""
    assert second.stderr == ""
```

- [ ] **Step 2: Create the failing help fixture**

Create `tests/fixtures/cli_rytm_snapshot_pad_compatibility_report_help_expected.txt`:

```text
RytmRandomizer passive CLI: rytm-snapshot-pad-compatibility-report

Usage:
  python -m rytm_randomizer.cli rytm-snapshot-pad-compatibility-report
  python -m rytm_randomizer.cli rytm-snapshot-pad-compatibility-report --help

Behavior:
  Prints the passive Analog Rytm MK2 snapshot-pad compatibility report.

Safety:
  passive/read-only
  no MIDI sending
  no port opening
  no command execution
  no hardware mutation
  no hardware required
```

- [ ] **Step 3: Verify CLI tests fail before wiring**

Run:

```powershell
python -m pytest tests/test_cli.py::test_rytm_snapshot_pad_compatibility_report_help_exits_zero_and_matches_fixture tests/test_cli.py::test_rytm_snapshot_pad_compatibility_report_command_exits_zero_and_describes_pad_10 -n 0
```

Expected: FAIL because the new help key and lazy registry dispatch are not wired yet.

- [ ] **Step 4: Wire lazy command registration in `cli.py`**

In `_registered_command_exit_code`, extend the special lazy command registration:

```python
    lazy_command_modules = {
        "rytm-12-pad-machine-matrix-report": "rytm_randomizer.reports.rytm_machine_matrix",
        "rytm-snapshot-pad-compatibility-report": (
            "rytm_randomizer.reports.rytm_snapshot_pad_compatibility"
        ),
    }
    command = cli_registry.get(args[0])
    module_name = lazy_command_modules.get(args[0])
    if command is None and module_name is not None:
        from importlib import import_module

        import_module(module_name)
        command = cli_registry.get(args[0])
```

Replace the existing one-off `rytm-12-pad-machine-matrix-report` block with this table.

- [ ] **Step 5: Wire help text**

In `rytm_randomizer/help_text.py`:

1. Add `rytm-snapshot-pad-compatibility-report` to `USAGE`.
2. Add the command to top-level `Usage:`.
3. Add the command summary to `Commands:`.
4. Add a `HELP_TEXT["rytm-snapshot-pad-compatibility-report"]` entry matching the fixture.

- [ ] **Step 6: Run CLI focused tests**

Run:

```powershell
python -m pytest tests/test_cli.py -n 0
```

Expected: PASS, except README test may still fail until Task 4.

---

### Task 4: Update Passive Safety Sweep and Docs

**Files:**
- Modify: `tests/test_real_midi_passive_cli_safety.py`
- Modify: `README.md`
- Modify: `docs/STATUS.md`

- [ ] **Step 1: Add the command to passive safety sweeps**

In `tests/test_real_midi_passive_cli_safety.py`, add this tuple to both `PASSIVE_CLI_COMMANDS` and `PASSIVE_CLI_SWEEP_COMMANDS`:

```python
("rytm-snapshot-pad-compatibility-report",),
```

- [ ] **Step 2: Update README**

In `README.md`, update the dual-machine target command block to include:

```bash
python -m rytm_randomizer.cli rytm-snapshot-pad-compatibility-report   # passive snapshot readiness per Rytm pad
```

Also add one sentence after the block:

```markdown
The snapshot-pad compatibility report explains which legal Rytm pad/machine combinations are snapshot-mutable today and which remain selectable-only until the follow-up runtime slice.
```

- [ ] **Step 3: Update status**

At the top of `docs/STATUS.md` under `## Recent Cleanup`, add:

```markdown
- 2026-05-20: Rytm snapshot-pad compatibility checkpoint started from the clean post-PR #48 base. This PR adds a passive report that separates legal pad-machine selection from snapshot-mutation readiness across all 12 Rytm pads. Pads with V1.34-backed mutable profiles report ready; selectable-only pads report a clear blocked reason. No hardware sends or runtime mutation are introduced.
```

- [ ] **Step 4: Run focused passive CLI safety tests**

Run:

```powershell
python -m pytest tests/test_real_midi_passive_cli_safety.py -n 0
```

Expected: PASS.

- [ ] **Step 5: Commit the CLI/docs slice**

Run:

```powershell
git add rytm_randomizer/cli.py rytm_randomizer/help_text.py tests/test_cli.py tests/test_real_midi_passive_cli_safety.py tests/fixtures/cli_rytm_snapshot_pad_compatibility_report_help_expected.txt README.md docs/STATUS.md
git commit -m "feat: expose Rytm snapshot pad compatibility report"
```

---

### Task 5: Verification and PR Readiness

**Files:**
- No new files.
- Verify all touched files.

- [ ] **Step 1: Run focused tests**

Run:

```powershell
python -m pytest tests/test_rytm_snapshot_pad_compatibility_report.py -n 0
python -m pytest tests/test_cli.py -n 0
python -m pytest tests/test_real_midi_passive_cli_safety.py -n 0
```

Expected: PASS.

- [ ] **Step 2: Run architecture gate**

Run:

```powershell
python -m pytest tests/architecture/ -q
```

Expected: PASS.

- [ ] **Step 3: Run fast suite**

Run:

```powershell
python -m pytest -m fast
```

Expected: PASS.

- [ ] **Step 4: Run full suite**

Run:

```powershell
python -m pytest
```

Expected: PASS.

- [ ] **Step 5: Run lint checks**

Run:

```powershell
python -m ruff check .
python -m black --check --target-version=py311 .
python -m isort --profile black --check-only .
git diff --check
```

Expected: all commands PASS. If `git diff --check` reports only pre-existing CRLF/LF churn in unstaged files, do not stage those files; investigate before touching them.

- [ ] **Step 6: Prepare PR body**

Use the PR body from `docs/superpowers/plans/2026-05-20-rytm-snapshot-pad-compatibility-pr-body.md` if added, or create a concise PR body with:

```markdown
## Summary

- Adds a passive Rytm snapshot-pad compatibility report.
- Explains which pads have V1.34-backed snapshot-mutable legal machines.
- Exposes `rytm-snapshot-pad-compatibility-report` through the passive CLI.

## Safety

- No hardware sends.
- No MIDI port opening.
- No runtime mutation.
- No Analog Four behavior change.

## Verification

- `python -m pytest tests/test_rytm_snapshot_pad_compatibility_report.py -n 0`
- `python -m pytest tests/test_cli.py -n 0`
- `python -m pytest tests/test_real_midi_passive_cli_safety.py -n 0`
- `python -m pytest tests/architecture/ -q`
- `python -m pytest -m fast`
- `python -m pytest`
- `python -m ruff check .`
- `python -m black --check --target-version=py311 .`
- `python -m isort --profile black --check-only .`
```

---

## Self-Review Checklist

- Spec coverage: Tasks 1-4 cover report model, readiness rule, CLI, passive safety, README, and status docs.
- No scope creep: No armed send path, no Analog Four runtime behavior, no GUI, no analyzer.
- Type consistency: Report dataclass and function names match between tests, implementation, re-export, and CLI.
- Architecture: New code lives in `reports/`, uses existing `data/` and `cli_registry`, and adds no top-level package.
- TDD: Each implementation task starts with failing tests before code.
