# Dual Snapshot Style Kit Readiness Bundle Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a passive, bank-level readiness layer that scans Rytm and Analog Four kit dumps, fingerprints decoded kit states, and ranks Rytm+A4 kit pairings for a selected style target before any hardware path is armed.

**Architecture:** Keep all behavior inside existing Strategy/report boundaries. Rytm kit readiness consumes the already-passive Rytm SysEx decoder plus style mock-preview builder; dual-machine readiness composes the Rytm and Analog Four per-kit readiness reports rather than introducing a parallel device family path.

**Tech Stack:** Python 3.11+ dataclasses, existing `CliCommand` registry, existing passive report formatter, existing Elektron SysEx decoders, pytest fast-suite tests, README/status docs.

---

## File Map

- Modify: `rytm_randomizer/devices/strategies/analog_rytm_snapshot_decoder.py`
  - Add `rytm_snapshot_payload_fingerprint(snapshot)` mirroring the Analog Four fingerprint helper.
- Modify: `rytm_randomizer/devices/strategies/__init__.py`
  - Re-export the Rytm fingerprint helper for strategy consumers.
- Create: `rytm_randomizer/reports/rytm_style_kit_readiness.py`
  - Build, format, JSON-serialize, and CLI-register the per-kit Rytm readiness sweep.
- Create: `rytm_randomizer/reports/dual_machine_style_kit_readiness.py`
  - Compose Rytm and Analog Four per-kit readiness into ranked rig pairings.
- Modify: `rytm_randomizer/cli.py`
  - Add lazy registrations for `rytm-style-kit-readiness-report` and `dual-machine-style-kit-readiness-report`.
- Modify: `rytm_randomizer/help_text.py`
  - Add usage/help blocks for both new commands.
- Modify: `tests/test_rytm_style_kit_readiness.py`
  - Cover Rytm fingerprinting, build/format/JSON/CLI parser/handler behavior.
- Modify: `tests/test_dual_machine_style_kit_readiness.py`
  - Cover dual bank pairing counts, sorting, text/JSON output, and CLI parser/handler behavior.
- Modify: `tests/test_cli.py`, `tests/test_cli_coverage.py`, `tests/test_real_midi_passive_cli_safety.py`, `tests/fixtures/cli_help_expected.txt`
  - Keep the operator CLI, in-process coverage, and passive safety gates current.
- Modify: `README.md`, `docs/STATUS.md`
  - Document the new operator commands and project checkpoint.

## Task 1: Add Rytm Payload Fingerprints

**Files:**
- Modify: `rytm_randomizer/devices/strategies/analog_rytm_snapshot_decoder.py`
- Modify: `rytm_randomizer/devices/strategies/__init__.py`
- Test: `tests/test_rytm_style_kit_readiness.py`

- [x] **Step 1: Write the failing test**

```python
def test_rytm_snapshot_payload_fingerprint_is_stable():
    from conftest import rytm_real_layout_kit_payload

    from rytm_randomizer.devices.strategies.analog_rytm_snapshot_decoder import (
        AnalogRytmSnapshotDecoder,
        rytm_snapshot_payload_fingerprint,
    )

    snapshot = AnalogRytmSnapshotDecoder().decode(
        rytm_real_layout_kit_payload(name=b"FINGERPRINT"),
        slot=3,
    )

    first = rytm_snapshot_payload_fingerprint(snapshot)
    second = rytm_snapshot_payload_fingerprint(snapshot)

    assert first == second
    assert len(first) == 16
    assert int(first, 16) >= 0
```

- [x] **Step 2: Verify red**

Run:

```bash
python -m pytest tests\test_rytm_style_kit_readiness.py -n 0
```

Expected: import failure for `rytm_snapshot_payload_fingerprint`.

- [x] **Step 3: Implement the helper**

```python
from hashlib import sha256


def rytm_snapshot_payload_fingerprint(snapshot: RytmKitSnapshot) -> str:
    """Return a stable short digest for the decoded Rytm kit payload."""

    payload = snapshot.unpacked or snapshot.raw
    return sha256(payload).hexdigest()[:16]
```

- [x] **Step 4: Re-export through strategies package**

Add `rytm_snapshot_payload_fingerprint` to `rytm_randomizer/devices/strategies/__init__.py` imports and `__all__`.

## Task 2: Build Rytm Per-Kit Style Readiness

**Files:**
- Create: `rytm_randomizer/reports/rytm_style_kit_readiness.py`
- Test: `tests/test_rytm_style_kit_readiness.py`

- [x] **Step 1: Write failing report tests**

The tests create a two-kit framed `.syx` dump with `rytm_real_layout_kit_payload`, call `build_rytm_style_kit_readiness_report(path, "jose_core_techno")`, and assert:

```python
assert report.kit_count == 2
assert report.preview_ready_count == 2
assert report.blocked_kit_count == 0
assert report.entries[0].kit_name == "RYTM ONE"
assert report.entries[0].preview_ready is True
assert len(report.entries[0].payload_fingerprint) == 16
```

- [x] **Step 2: Verify red**

Run:

```bash
python -m pytest tests\test_rytm_style_kit_readiness.py -n 0
```

Expected: `ModuleNotFoundError` for `rytm_randomizer.reports.rytm_style_kit_readiness`.

- [x] **Step 3: Implement the report module**

Create frozen dataclasses:

```python
@dataclass(frozen=True)
class RytmStyleKitReadinessEntry:
    slot: int
    kit_name: str
    discovery_band: str
    mutation_depth: str
    preview_ready: bool
    ready_pad_count: int
    blocked_pad_count: int
    render_event_count: int
    mock_message_count: int
    planned_pads: tuple[int, ...]
    payload_fingerprint: str
    readiness_reason: str
```

Build entries by decoding every supported Rytm snapshot and passing each snapshot through `build_rytm_style_mutation_mock_preview`.

- [x] **Step 4: Add text, JSON, parser, and handler**

Expose:

```python
build_rytm_style_kit_readiness_report(...)
format_rytm_style_kit_readiness_report(...)
to_rytm_style_kit_readiness_json(...)
_parse_cli_args(...)
_handle_cli_report(...)
RYTM_STYLE_KIT_READINESS_CLI_COMMAND
```

The safety block must include `passive/read-only`, `style/mock preview only`, `no MIDI sending`, and `no port opening`.

## Task 3: Build Dual-Machine Kit Pairing Readiness

**Files:**
- Create: `rytm_randomizer/reports/dual_machine_style_kit_readiness.py`
- Test: `tests/test_dual_machine_style_kit_readiness.py`

- [x] **Step 1: Write failing dual-report tests**

The tests create two Rytm kits and two A4 kits, then assert:

```python
assert report.rytm_kit_count == 2
assert report.analog_four_kit_count == 2
assert report.pairing_count == 4
assert report.ready_pair_count == 0
assert report.partial_pair_count == 4
assert report.entries[0].rig_readiness == "partial"
```

- [x] **Step 2: Verify red**

Run:

```bash
python -m pytest tests\test_dual_machine_style_kit_readiness.py -n 0
```

Expected: `ModuleNotFoundError` for `rytm_randomizer.reports.dual_machine_style_kit_readiness`.

- [x] **Step 3: Implement the pairing report**

Compose existing single-machine report builders:

```python
rytm_report = build_rytm_style_kit_readiness_report(...)
analog_four_report = build_analog_four_style_kit_readiness_report(...)
entries = tuple(
    sorted(
        (
            _entry_from_pair(rytm_entry, analog_four_entry)
            for rytm_entry in rytm_report.entries
            for analog_four_entry in analog_four_report.entries
        ),
        key=_sort_key,
    )
)
```

Classify each pair as `ready`, `partial`, or `blocked`, then score by readiness rank, ready pad/track counts, and mock row counts.

- [x] **Step 4: Add text, JSON, parser, and handler**

Expose:

```python
build_dual_machine_style_kit_readiness_report(...)
format_dual_machine_style_kit_readiness_report(...)
to_dual_machine_style_kit_readiness_json(...)
_parse_cli_args(...)
_handle_cli_report(...)
DUAL_MACHINE_STYLE_KIT_READINESS_CLI_COMMAND
```

The safety block must include `rig-level kit-bank readiness only`, `no MIDI sending`, and `no port opening`.

## Task 4: Wire CLI, Help, and Passive Safety

**Files:**
- Modify: `rytm_randomizer/cli.py`
- Modify: `rytm_randomizer/help_text.py`
- Modify: `tests/test_cli.py`
- Modify: `tests/test_cli_coverage.py`
- Modify: `tests/test_real_midi_passive_cli_safety.py`
- Modify: `tests/fixtures/cli_help_expected.txt`

- [x] **Step 1: Register lazy commands**

Add:

```python
"rytm-style-kit-readiness-report": (
    "rytm_randomizer.reports.rytm_style_kit_readiness",
    "RYTM_STYLE_KIT_READINESS_CLI_COMMAND",
),
"dual-machine-style-kit-readiness-report": (
    "rytm_randomizer.reports.dual_machine_style_kit_readiness",
    "DUAL_MACHINE_STYLE_KIT_READINESS_CLI_COMMAND",
),
```

- [x] **Step 2: Add help text**

Add command-specific help functions and top-level usage entries. The command help must import safety lines from the report source, so tests can prove help and report safety remain synchronized.

- [x] **Step 3: Add CLI subprocess and in-process tests**

Subprocess tests verify operator output and JSON output. In-process `cli.main(...)` tests cover lazy import registration under coverage.

- [x] **Step 4: Keep passive safety sweep current**

Add both `--help` commands to the passive MIDI import sweep so the new command surface proves it imports no real MIDI libraries and exposes no armed/port text.

## Task 5: Docs and Status

**Files:**
- Modify: `README.md`
- Modify: `docs/STATUS.md`
- Create: `docs/superpowers/plans/2026-05-21-dual-snapshot-style-kit-readiness-bundle-pr16.md`

- [x] **Step 1: Update README commands**

Add operator examples for:

```bash
python -m rytm_randomizer.cli rytm-style-kit-readiness-report "G:\ANALOG RYTM\KITS\ANALOGRYTMKITS2.syx" jose_core_techno --limit 16
python -m rytm_randomizer.cli dual-machine-style-kit-readiness-report "G:\ANALOG RYTM\KITS\ANALOGRYTMKITS2.syx" "G:\ANALOG FOUR\KITS\ANALOGFOURKITS1.syx" jose_core_techno --limit 16
```

- [x] **Step 2: Update README behavior notes**

Document that Rytm readiness scans every decoded kit and that dual readiness ranks Rytm+A4 kit pairs before hardware sends exist.

- [x] **Step 3: Update status**

Add a 2026-05-21 Recent Cleanup entry describing the dual-machine style kit-readiness sweep as passive and hardware-safe.

## Verification Plan

- [x] Focused red phase:

```bash
python -m pytest tests\test_rytm_style_kit_readiness.py tests\test_dual_machine_style_kit_readiness.py -n 0
```

Expected before implementation: import/module failures for the new API.

- [x] Focused green phase:

```bash
python -m pytest tests\test_rytm_style_kit_readiness.py tests\test_dual_machine_style_kit_readiness.py -n 0
```

Expected after implementation: all focused report tests pass.

- [x] CLI/safety verification:

```bash
python -m pytest tests\test_cli.py tests\test_cli_coverage.py tests\test_real_midi_passive_cli_safety.py -n 0
```

Expected: top-level help fixture, command help safety, in-process lazy imports, and passive MIDI import safety all pass.

- [x] Final closeout before commit/PR:

```bash
python -m pytest tests\test_reports_formatter.py tests\test_rytm_style_kit_readiness.py tests\test_dual_machine_style_kit_readiness.py tests\test_cli.py tests\test_cli_coverage.py tests\test_real_midi_passive_cli_safety.py -n 0
python -m pytest tests/architecture/ -q
python -m pytest -m fast
python -m pytest
python -m pytest --cov=rytm_randomizer --cov-branch --cov-report=term-missing
python -m ruff check .
python -m black --check --target-version=py311 .
python -m isort --profile black --check-only .
```

Expected: all commands exit 0 before staging, commit, push, and PR creation.

- [x] Real-file passive smoke:

```bash
python -m rytm_randomizer.cli rytm-style-kit-readiness-report "G:\ANALOG RYTM\KITS\ANALOGRYTMKITS2.syx" jose_core_techno --limit 3
python -m rytm_randomizer.cli analog-four-style-kit-readiness-report "G:\ANALOG FOUR\KITS\ANALOGFOURKITS1.syx" jose_core_techno --limit 3
python -m rytm_randomizer.cli dual-machine-style-kit-readiness-report "G:\ANALOG RYTM\KITS\ANALOGRYTMKITS2.syx" "G:\ANALOG FOUR\KITS\ANALOGFOURKITS1.syx" jose_core_techno --limit 3
```

Expected: all commands exit 0, remain passive/read-only, and open no ports.
