# Rytm Snapshot File Intelligence Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Expose a passive CLI command that reads an Analog Rytm MKII `.syx` file and prints the existing snapshot intelligence report for the first supported kit snapshot.

**Architecture:** Keep file ingestion passive and routed through existing boundaries. Add one generic SysEx-file helper under `rytm_randomizer/snapshot/`, grow `rytm_randomizer/reports/rytm_snapshot_intelligence.py` into a `CliCommand`, and lazy-register the command from `cli.py`. Do not touch armed runtime, MIDI senders, engines, scene/group runners, or V1.34 parity fixtures.

**Tech Stack:** Python 3.11 stdlib, `pathlib`, existing Elektron SysEx envelope helpers, existing Analog Rytm snapshot decoder strategy, existing passive report formatter, pytest.

---

## File Structure

- Create `rytm_randomizer/snapshot/sysex_file.py`: passive file/framing helper. Reads local bytes, extracts framed SysEx payloads, and accepts already-stripped payload bytes for tests/operator diagnostics.
- Modify `rytm_randomizer/reports/rytm_snapshot_intelligence.py`: add CLI argument parsing, first-supported Rytm snapshot decode, stdout/stderr handler, and `CliCommand` registration.
- Modify `rytm_randomizer/cli.py`: add the command to `lazy_commands`.
- Modify `rytm_randomizer/help_text.py`: add usage/help text and top-level command listing.
- Modify `tests/conftest.py`: add shared Rytm kit payload builders so two test files do not duplicate Elektron 7-bit packing helpers.
- Modify `tests/test_devices_strategies_snapshot_decoder.py`: consume the shared fixture helpers instead of local duplicates.
- Create `tests/test_snapshot_sysex_file.py`: unit tests for framed, multi-frame, raw, empty, and malformed file payload extraction.
- Modify `tests/test_rytm_snapshot_intelligence_report.py`: add direct CLI-command parser/handler tests where useful.
- Modify `tests/test_cli.py`: subprocess CLI tests, help fixture test, deterministic output test.
- Modify `tests/test_cli_coverage.py`: in-process coverage for lazy registration and error branches.
- Modify `tests/test_real_midi_passive_cli_safety.py`: include the new passive command.
- Modify `tests/fixtures/cli_help_expected.txt`: top-level help fixture.
- Create `tests/fixtures/cli_rytm_snapshot_intelligence_report_help_expected.txt`: subcommand help fixture.
- Modify `README.md`: add the new passive command to the CLI/report examples.
- Modify `docs/STATUS.md`: record the new file-intelligence slice.
- Modify `docs/ARCHITECTURE_DIAGRAMS.md`: update passive CLI/report diagrams to show the new command as operator-facing rather than direct-import only.

## Task 1: Shared Rytm SysEx Test Fixtures

**Files:**
- Modify: `tests/conftest.py`
- Modify: `tests/test_devices_strategies_snapshot_decoder.py`

- [ ] **Step 1: Write the shared helper additions in `tests/conftest.py`**

```python
def pack_elektron_7bit(unpacked: bytes) -> bytes:
    """Pack bytes into Elektron's 7-bit SysEx payload encoding for tests."""

    out = bytearray()
    for start in range(0, len(unpacked), 7):
        group = unpacked[start : start + 7]
        header = 0
        for index, byte in enumerate(group):
            header |= ((byte >> 7) & 0x01) << index
        out.append(header)
        out.extend(byte & 0x7F for byte in group)
    return bytes(out)


def rytm_real_layout_kit_payload(name: bytes = b"KIT 1") -> bytes:
    """Build a packed Rytm kit body matching Jose's observed dump layout."""

    from rytm_randomizer.devices.strategies.analog_rytm_snapshot_decoder import (
        RYTM_KIT_TYPE_BYTE,
    )

    unpacked = bytearray(bytes([0x52, 0x01, 0x01, 0x00, 0x00, 0x00, 0x00, 0x06]))
    unpacked.extend(name.ljust(16, b"\x00"))
    unpacked.extend(bytes([0x00] * 2600))
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
        unpacked[174 + (162 * (pad - 1))] = value
    packed = pack_elektron_7bit(bytes(unpacked))
    return bytes([0x00, 0x20, 0x3C, RYTM_KIT_TYPE_BYTE]) + packed
```

- [ ] **Step 2: Refactor `tests/test_devices_strategies_snapshot_decoder.py`**

Replace the local `_pack_elektron_7bit` and `_real_layout_kit_payload` helpers with imports:

```python
from conftest import rytm_real_layout_kit_payload
```

Then keep the local wrapper:

```python
def _real_layout_kit_payload(name: bytes = b"KIT 1") -> bytes:
    return rytm_real_layout_kit_payload(name=name)
```

- [ ] **Step 3: Run the decoder tests**

Run:

```powershell
python -m pytest tests/test_devices_strategies_snapshot_decoder.py -n 0
```

Expected: PASS.

- [ ] **Step 4: Commit**

```powershell
git add tests/conftest.py tests/test_devices_strategies_snapshot_decoder.py
git commit -m "test: share Rytm SysEx fixture helpers"
```

## Task 2: Passive SysEx File Helper

**Files:**
- Create: `rytm_randomizer/snapshot/sysex_file.py`
- Create: `tests/test_snapshot_sysex_file.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_snapshot_sysex_file.py`:

```python
"""Tests for passive SysEx file payload extraction."""

from __future__ import annotations

from pathlib import Path

import pytest

from conftest import rytm_real_layout_kit_payload

pytestmark = pytest.mark.fast


def test_extract_sysex_payloads_accepts_already_stripped_payload() -> None:
    from rytm_randomizer.snapshot.sysex_file import extract_sysex_payloads

    payload = rytm_real_layout_kit_payload(name=b"RAW")

    assert extract_sysex_payloads(payload) == (payload,)


def test_extract_sysex_payloads_strips_single_framed_sysex() -> None:
    from rytm_randomizer.snapshot.sysex_file import extract_sysex_payloads

    payload = rytm_real_layout_kit_payload(name=b"FRAMED")

    assert extract_sysex_payloads(bytes([0xF0]) + payload + bytes([0xF7])) == (payload,)


def test_extract_sysex_payloads_returns_all_frames_from_c6_dump() -> None:
    from rytm_randomizer.snapshot.sysex_file import extract_sysex_payloads

    first = bytes([0x00, 0x20, 0x3C, 0x05, 0x00])
    second = rytm_real_layout_kit_payload(name=b"BANK")
    raw = bytes([0xF0]) + first + bytes([0xF7, 0xF0]) + second + bytes([0xF7])

    assert extract_sysex_payloads(raw) == (first, second)


def test_extract_sysex_payloads_rejects_empty_input() -> None:
    from rytm_randomizer.snapshot.sysex_file import extract_sysex_payloads

    with pytest.raises(ValueError, match="empty"):
        extract_sysex_payloads(b"")


def test_extract_sysex_payloads_rejects_unclosed_frame() -> None:
    from rytm_randomizer.snapshot.sysex_file import extract_sysex_payloads

    with pytest.raises(ValueError, match="without a closing F7"):
        extract_sysex_payloads(bytes([0xF0, 0x00, 0x20, 0x3C]))


def test_read_sysex_payloads_from_path_rejects_missing_file(tmp_path: Path) -> None:
    from rytm_randomizer.snapshot.sysex_file import read_sysex_payloads_from_path

    with pytest.raises(ValueError, match="does not exist"):
        read_sysex_payloads_from_path(tmp_path / "missing.syx")


def test_read_sysex_payloads_from_path_rejects_directory(tmp_path: Path) -> None:
    from rytm_randomizer.snapshot.sysex_file import read_sysex_payloads_from_path

    with pytest.raises(ValueError, match="not a file"):
        read_sysex_payloads_from_path(tmp_path)


def test_read_sysex_payloads_from_path_reads_payloads(tmp_path: Path) -> None:
    from rytm_randomizer.snapshot.sysex_file import read_sysex_payloads_from_path

    payload = rytm_real_layout_kit_payload(name=b"FILE")
    path = tmp_path / "kit.syx"
    path.write_bytes(bytes([0xF0]) + payload + bytes([0xF7]))

    assert read_sysex_payloads_from_path(path) == (payload,)
```

- [ ] **Step 2: Run tests to verify RED**

Run:

```powershell
python -m pytest tests/test_snapshot_sysex_file.py -n 0
```

Expected: FAIL with `ModuleNotFoundError: No module named 'rytm_randomizer.snapshot.sysex_file'`.

- [ ] **Step 3: Implement the helper**

Create `rytm_randomizer/snapshot/sysex_file.py`:

```python
"""Passive SysEx file helpers."""

from __future__ import annotations

from pathlib import Path
from typing import Final

_SYSEX_START: Final[int] = 0xF0
_SYSEX_END: Final[int] = 0xF7


def extract_sysex_payloads(raw: bytes) -> tuple[bytes, ...]:
    """Return unframed SysEx payloads from ``raw`` bytes."""

    if not raw:
        raise ValueError("SysEx data is empty")

    frames: list[bytes] = []
    cursor = 0
    while cursor < len(raw):
        try:
            start = raw.index(_SYSEX_START, cursor)
        except ValueError:
            break
        try:
            end = raw.index(_SYSEX_END, start + 1)
        except ValueError as exc:
            raise ValueError(
                f"SysEx frame starting at byte {start} is without a closing F7 byte"
            ) from exc
        payload = raw[start + 1 : end]
        if not payload:
            raise ValueError(f"SysEx frame starting at byte {start} has an empty payload")
        frames.append(payload)
        cursor = end + 1

    if frames:
        return tuple(frames)
    if raw[0] == _SYSEX_START or raw[-1] == _SYSEX_END:
        raise ValueError("SysEx framing is incomplete; expected both F0 and F7 bytes")
    return (raw,)


def read_sysex_payloads_from_path(sysex_path: str | Path) -> tuple[bytes, ...]:
    """Read ``sysex_path`` and return unframed SysEx payloads."""

    path = Path(sysex_path)
    if not path.exists():
        raise ValueError(f"SysEx file does not exist: {path}")
    if not path.is_file():
        raise ValueError(f"SysEx path is not a file: {path}")
    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise ValueError(f"Could not read SysEx file {path}: {exc}") from exc
    return extract_sysex_payloads(raw)
```

- [ ] **Step 4: Run tests to verify GREEN**

Run:

```powershell
python -m pytest tests/test_snapshot_sysex_file.py -n 0
```

Expected: PASS.

- [ ] **Step 5: Commit**

```powershell
git add rytm_randomizer/snapshot/sysex_file.py tests/test_snapshot_sysex_file.py
git commit -m "feat: add passive SysEx file extraction"
```

## Task 3: Snapshot Intelligence CLI Command

**Files:**
- Modify: `rytm_randomizer/reports/rytm_snapshot_intelligence.py`
- Modify: `tests/test_rytm_snapshot_intelligence_report.py`

- [ ] **Step 1: Write failing report/handler tests**

Append tests that call the command module directly:

```python
def test_rytm_snapshot_intelligence_cli_handler_reads_first_supported_frame(
    tmp_path: Path,
    capsys,
) -> None:
    from conftest import rytm_real_layout_kit_payload
    from rytm_randomizer.reports.rytm_snapshot_intelligence import _handle_cli_report

    bad_frame = bytes([0xF0, 0x00, 0x20, 0x3C, 0x05, 0x00, 0xF7])
    good_payload = rytm_real_layout_kit_payload(name=b"LIVECLI")
    path = tmp_path / "bank.syx"
    path.write_bytes(bad_frame + bytes([0xF0]) + good_payload + bytes([0xF7]))

    rc = _handle_cli_report(sysex_path=path, slot=0)

    captured = capsys.readouterr()
    assert rc == 0
    assert "Kit: LIVECLI" in captured.out
    assert "RytmRandomizer passive Rytm snapshot intelligence" in captured.out
    assert captured.err == ""


def test_rytm_snapshot_intelligence_cli_handler_reports_expected_errors(
    tmp_path: Path,
    capsys,
) -> None:
    from rytm_randomizer.reports.rytm_snapshot_intelligence import _handle_cli_report

    rc = _handle_cli_report(sysex_path=tmp_path / "missing.syx", slot=0)

    captured = capsys.readouterr()
    assert rc == 2
    assert captured.out == ""
    assert "SysEx file does not exist" in captured.err
    assert "Traceback" not in captured.err
```

- [ ] **Step 2: Run tests to verify RED**

Run:

```powershell
python -m pytest tests/test_rytm_snapshot_intelligence_report.py -n 0
```

Expected: FAIL because `_handle_cli_report` is not defined.

- [ ] **Step 3: Implement command registration**

In `rytm_randomizer/reports/rytm_snapshot_intelligence.py`, add imports:

```python
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path

from ..cli_registry import CliCommand, register
from ..devices.strategies.analog_rytm_snapshot_decoder import (
    AnalogRytmSnapshotDecoder,
    RytmKitSnapshot,
)
from ..snapshot.sysex_file import read_sysex_payloads_from_path
```

Add parsing and handler functions near the bottom:

```python
def _parse_cli_args(argv: Sequence[str]) -> dict[str, object]:
    if not argv:
        raise ValueError("rytm-snapshot-intelligence-report requires <syx-path>")
    if len(argv) not in (1, 3):
        raise ValueError(
            "rytm-snapshot-intelligence-report usage: <syx-path> [--slot 0]"
        )
    sysex_path = Path(argv[0])
    slot = 0
    if len(argv) == 3:
        if argv[1] != "--slot":
            raise ValueError(
                "rytm-snapshot-intelligence-report usage: <syx-path> [--slot 0]"
            )
        try:
            slot = int(argv[2])
        except ValueError as exc:
            raise ValueError("--slot must be an integer") from exc
    return {"sysex_path": sysex_path, "slot": slot}


def _decode_first_supported_snapshot(sysex_path: Path, slot: int) -> RytmKitSnapshot:
    decoder = AnalogRytmSnapshotDecoder()
    errors: list[str] = []
    for index, payload in enumerate(read_sysex_payloads_from_path(sysex_path), start=1):
        try:
            return decoder.decode(payload, slot=slot)
        except (NotImplementedError, ValueError) as exc:
            errors.append(f"frame {index}: {exc}")
    detail = "; ".join(errors) if errors else "no SysEx payloads found"
    raise ValueError(f"No supported Analog Rytm kit snapshot found in {sysex_path}: {detail}")


def _handle_cli_report(*, sysex_path: Path, slot: int) -> int:
    try:
        snapshot = _decode_first_supported_snapshot(sysex_path, slot)
    except (OSError, ValueError, NotImplementedError) as exc:
        sys.stderr.write(f"Error: {exc}\n")
        return 2
    sys.stdout.write("\n".join(format_rytm_snapshot_intelligence_report(snapshot)))
    sys.stdout.write("\n")
    return 0


RYTM_SNAPSHOT_INTELLIGENCE_CLI_COMMAND: Final[CliCommand] = CliCommand(
    name="rytm-snapshot-intelligence-report",
    summary="Print passive Rytm snapshot intelligence for a SysEx file.",
    args_parser=_parse_cli_args,
    handler=_handle_cli_report,
)

register(RYTM_SNAPSHOT_INTELLIGENCE_CLI_COMMAND)
```

Add `RYTM_SNAPSHOT_INTELLIGENCE_CLI_COMMAND` to `__all__`.

- [ ] **Step 4: Run tests to verify GREEN**

Run:

```powershell
python -m pytest tests/test_rytm_snapshot_intelligence_report.py -n 0
```

Expected: PASS.

- [ ] **Step 5: Commit**

```powershell
git add rytm_randomizer/reports/rytm_snapshot_intelligence.py tests/test_rytm_snapshot_intelligence_report.py
git commit -m "feat: add Rytm snapshot intelligence CLI handler"
```

## Task 4: CLI Wiring, Help, and Safety

**Files:**
- Modify: `rytm_randomizer/cli.py`
- Modify: `rytm_randomizer/help_text.py`
- Modify: `tests/test_cli.py`
- Modify: `tests/test_cli_coverage.py`
- Modify: `tests/test_real_midi_passive_cli_safety.py`
- Modify: `tests/fixtures/cli_help_expected.txt`
- Create: `tests/fixtures/cli_rytm_snapshot_intelligence_report_help_expected.txt`

- [ ] **Step 1: Add failing CLI tests**

Add subprocess tests for:

```python
def test_rytm_snapshot_intelligence_report_help_exits_zero_and_matches_fixture():
    result = run_cli("rytm-snapshot-intelligence-report", "--help")
    assert result.returncode == 0
    assert normalize_newlines(result.stdout) == fixture_text(
        "cli_rytm_snapshot_intelligence_report_help_expected.txt"
    )
    assert result.stderr == ""
```

```python
def test_rytm_snapshot_intelligence_report_command_reads_syx_file(tmp_path):
    from conftest import rytm_real_layout_kit_payload

    payload = rytm_real_layout_kit_payload(name=b"SUBPROC")
    path = tmp_path / "kit.syx"
    path.write_bytes(bytes([0xF0]) + payload + bytes([0xF7]))

    result = run_cli("rytm-snapshot-intelligence-report", str(path))

    assert result.returncode == 0
    assert "Kit: SUBPROC" in result.stdout
    assert "Pad 10:" in result.stdout
    assert result.stderr == ""
```

```python
def test_rytm_snapshot_intelligence_report_command_rejects_missing_file(tmp_path):
    result = run_cli("rytm-snapshot-intelligence-report", str(tmp_path / "missing.syx"))
    assert result.returncode == 2
    assert "SysEx file does not exist" in result.stderr
    assert "Traceback" not in result.stderr
```

- [ ] **Step 2: Run tests to verify RED**

Run:

```powershell
python -m pytest tests/test_cli.py::test_rytm_snapshot_intelligence_report_help_exits_zero_and_matches_fixture tests/test_cli.py::test_rytm_snapshot_intelligence_report_command_reads_syx_file tests/test_cli.py::test_rytm_snapshot_intelligence_report_command_rejects_missing_file -n 0
```

Expected: FAIL because the command is not in `HELP_TEXT` / `cli.py` lazy commands.

- [ ] **Step 3: Wire the command**

Add to `cli.py` `lazy_commands`:

```python
"rytm-snapshot-intelligence-report": (
    "rytm_randomizer.reports.rytm_snapshot_intelligence",
    "RYTM_SNAPSHOT_INTELLIGENCE_CLI_COMMAND",
),
```

Add to `help_text.py` `USAGE`, top-level help, `Commands`, and `HELP_TEXT`:

```python
def _rytm_snapshot_intelligence_report_help():
    from .reports.rytm_snapshot_intelligence import SAFETY_LINES

    return f"""RytmRandomizer passive CLI: rytm-snapshot-intelligence-report

Usage:
  python -m rytm_randomizer.cli rytm-snapshot-intelligence-report <syx-path>
  python -m rytm_randomizer.cli rytm-snapshot-intelligence-report <syx-path> --slot 0
  python -m rytm_randomizer.cli rytm-snapshot-intelligence-report --help

Behavior:
  Reads a local Analog Rytm MK2 SysEx file and prints passive snapshot intelligence
  for the first supported kit snapshot.

Safety:
{_safety_block(SAFETY_LINES)}"""
```

- [ ] **Step 4: Update passive safety lists**

Add `("rytm-snapshot-intelligence-report", <fixture-path>)` style coverage by creating a temp fixture in tests that need a path. For `PASSIVE_CLI_COMMANDS`, use the help form if the tuple cannot carry a dynamic path:

```python
("rytm-snapshot-intelligence-report", "--help"),
```

- [ ] **Step 5: Run CLI-focused tests**

Run:

```powershell
python -m pytest tests/test_cli.py tests/test_cli_coverage.py tests/test_real_midi_passive_cli_safety.py -n 0
```

Expected: PASS.

- [ ] **Step 6: Commit**

```powershell
git add rytm_randomizer/cli.py rytm_randomizer/help_text.py tests/test_cli.py tests/test_cli_coverage.py tests/test_real_midi_passive_cli_safety.py tests/fixtures/cli_help_expected.txt tests/fixtures/cli_rytm_snapshot_intelligence_report_help_expected.txt
git commit -m "feat: expose Rytm snapshot intelligence file report"
```

## Task 5: Docs and Architecture Freshness

**Files:**
- Modify: `README.md`
- Modify: `docs/STATUS.md`
- Modify: `docs/ARCHITECTURE_DIAGRAMS.md`

- [ ] **Step 1: Update README**

Add the command near the passive CLI examples:

```powershell
python -m rytm_randomizer.cli rytm-snapshot-intelligence-report "G:\ANALOG RYTM\KITS\ANALOGRYTMKITS2.syx"
```

Describe it as passive/read-only and file-based.

- [ ] **Step 2: Update STATUS**

Add:

```markdown
- 2026-05-20: Rytm snapshot file intelligence slice adds a passive CLI command that reads a local `.syx` file, scans framed C6 dumps for the first supported Rytm kit snapshot, and prints the existing snapshot intelligence report without opening MIDI ports or sending hardware data.
```

- [ ] **Step 3: Update architecture diagrams**

Update the passive CLI/report diagrams that currently describe `rytm_snapshot_intelligence.py` as direct-import only. The new label should mention:

```text
rytm_snapshot_intelligence.py
decoded/routed snapshot readiness report
+ file-backed CliCommand
```

Add `rytm-snapshot-intelligence-report <syx-path>` to the CLI command diagrams.

- [ ] **Step 4: Run doc freshness checks**

Run:

```powershell
python -m pytest tests/architecture/test_readme_freshness.py -n 0
```

Expected: PASS.

- [ ] **Step 5: Commit**

```powershell
git add README.md docs/STATUS.md docs/ARCHITECTURE_DIAGRAMS.md
git commit -m "docs: document Rytm snapshot file intelligence"
```

## Task 6: Verification, Review, Push, PR

**Files:**
- No new implementation files unless verification finds a defect.

- [ ] **Step 1: Focused tests**

Run:

```powershell
python -m pytest tests/test_snapshot_sysex_file.py tests/test_rytm_snapshot_intelligence_report.py tests/test_cli.py tests/test_cli_coverage.py tests/test_real_midi_passive_cli_safety.py -n 0
```

Expected: PASS.

- [ ] **Step 2: Architecture tests**

Run:

```powershell
python -m pytest tests/architecture/ -q
```

Expected: PASS.

- [ ] **Step 3: Fast and full tests**

Run:

```powershell
python -m pytest -m fast
python -m pytest
```

Expected: PASS.

- [ ] **Step 4: Coverage**

Run:

```powershell
python -m pytest --cov=rytm_randomizer --cov-branch --cov-report=term-missing
```

Expected: PASS and coverage at or above the repo floor.

- [ ] **Step 5: Lint**

Run:

```powershell
python -m ruff check .
python -m black --check --target-version=py311 .
python -m isort --profile black --check-only .
```

Expected: PASS.

- [ ] **Step 6: Check only our intended diff**

Run:

```powershell
git diff --stat origin/modularize-v1.34...HEAD
git status --short
```

Expected: committed diff contains only the files in this plan. Ignore unstaged CRLF-only checkout noise; do not stage it.

- [ ] **Step 7: Push**

Run:

```powershell
git push -u origin codex/rytm-snapshot-file-intelligence-pr4
```

Expected: push succeeds after pre-push gates.

- [ ] **Step 8: Open PR**

Open one PR against `modularize-v1.34` with:

- summary of passive `.syx` file intelligence,
- test plan with executed commands,
- link to this plan and the design spec,
- all 18 plan gates marked,
- strict-rule confirmation block.

Expected: CI green, review requested from Eddie / `@buzzijose-hub`.

## Self-Review

- Spec coverage: every requirement in `docs/superpowers/specs/2026-05-20-rytm-snapshot-file-intelligence-design.md` maps to Tasks 1-6.
- Placeholder scan: all steps name concrete files, commands, expected results, and error behavior.
- Type consistency: helper names are `extract_sysex_payloads`, `read_sysex_payloads_from_path`, `_decode_first_supported_snapshot`, `_handle_cli_report`, and `RYTM_SNAPSHOT_INTELLIGENCE_CLI_COMMAND` throughout.
- Scope control: no hardware sends, no bank iteration across all kits, no Analog Four decode, and no mutation execution are included.
