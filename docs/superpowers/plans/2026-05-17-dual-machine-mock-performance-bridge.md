# Dual-Machine Mock Performance Bridge Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a passive combined Rytm + Analog Four mock performance bridge report.

**Update:** The Analog Four safe-starter plan was expanded later in
`2026-05-17-analog-four-richer-safe-starter.md` from two to five mapped CCs per
track. The count examples below reflect that newer safe-starter contract.

**Architecture:** Create a focused `rytm_randomizer.dual_machine_mock_bridge` module. It will consume the existing Rytm snapshot mutation planner, build a conservative A4 safe-starter plan from validated CCs, capture both streams into `MockMidiSender`, and expose a passive CLI report.

**Tech Stack:** Python dataclasses, existing `MockMidiSender`, existing `snapshot_mutation_planner`, passive CLI dispatch, pytest.

---

## File Structure

- Create `rytm_randomizer/dual_machine_mock_bridge.py`
  - Owns combined bridge dataclasses.
  - Builds the Rytm plan from a saved kit file.
  - Builds the A4 safe-starter track plan.
  - Captures both devices into an inert mock sender.
  - Formats the passive report and error output.
- Create `tests/test_dual_machine_mock_bridge.py`
  - Synthetic saved Rytm kit fixture.
  - Passive import checks.
  - Plan and mock sender assertions.
  - CLI happy path and safe failure assertions.
- Modify `rytm_randomizer/cli.py`
  - Add `dual-machine-mock-bridge-report <path> --slot <1-128> --depth <micro|groove|strong>`.
- Modify `rytm_randomizer/help_text.py`
  - Add the new command to top-level help and command-specific help.
- Modify `tests/test_cli.py` and `tests/fixtures/cli_help_expected.txt`
  - Add help coverage.
- Modify `Docs/PASSIVE_CLI_OPERATOR_QUICKSTART.md`
  - Add operator command examples and safety boundary.

## Task 1: Dual Bridge Domain And Mock Capture

**Files:**
- Create: `tests/test_dual_machine_mock_bridge.py`
- Create: `rytm_randomizer/dual_machine_mock_bridge.py`

- [ ] **Step 1: Write failing tests**

Add `tests/test_dual_machine_mock_bridge.py` with:

```python
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def pack_7bit_payload(payload):
    packed = bytearray()
    for index in range(0, len(payload), 7):
        chunk = payload[index : index + 7]
        mask = 0
        data = bytearray()
        for bit, value in enumerate(chunk):
            if value & 0x80:
                mask |= 1 << bit
            data.append(value & 0x7F)
        packed.append(mask)
        packed.extend(data)
    return bytes(packed)


def make_rytm_kit_record(slot_index=0, kit_name="BRIDGE", machine_values=None, values=None):
    machine_values = machine_values or ((0,) + tuple(27 for _ in range(11)))
    values = values or {
        1: {
            0x1E: 59,
            0x20: 68,
            0x44: 25,
            0x46: 14,
            0x4A: 65,
            0x50: 121,
        }
    }
    decoded = bytearray(58 + (12 * 162) + 8)
    decoded[4 : 4 + len(kit_name)] = kit_name.encode("ascii")
    for pad in range(1, 13):
        sound_name = f"SOUND {pad}"
        offset = 58 + ((pad - 1) * 162)
        track_offset = 46 + ((pad - 1) * 162)
        decoded[offset : offset + len(sound_name)] = sound_name.encode("ascii")
        decoded[track_offset + 0x7C] = machine_values[pad - 1]
        for parameter_offset, value in values.get(pad, {}).items():
            decoded[track_offset + parameter_offset] = value
    return (
        bytes([0xF0, 0x00, 0x20, 0x3C, 0x07, 0x00, 0x52, 0x01, 0x01, slot_index])
        + pack_7bit_payload(decoded)
        + bytes([0xF7])
    )


def test_importing_dual_machine_bridge_is_passive_and_silent():
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import sys; "
                "import rytm_randomizer.dual_machine_mock_bridge; "
                "assert 'mido' not in sys.modules; "
                "assert 'rtmidi' not in sys.modules"
            ),
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert result.stdout == ""
    assert result.stderr == ""


def test_dual_bridge_combines_rytm_snapshot_and_a4_safe_starter(tmp_path):
    from rytm_randomizer.dual_machine_mock_bridge import build_dual_machine_mock_bridge
    from rytm_randomizer.dual_machine_mock_bridge import capture_dual_machine_mock_messages

    sysex_path = tmp_path / "kits.syx"
    sysex_path.write_bytes(make_rytm_kit_record(kit_name="BRIDGE KIT"))

    bridge = build_dual_machine_mock_bridge(str(sysex_path), slot=1, depth="micro")
    sender = capture_dual_machine_mock_messages(bridge)

    assert bridge.rytm_source == "saved-kit snapshot"
    assert bridge.analog_four_source == "safe starter CC plan"
    assert bridge.rytm_plan.kit_name == "BRIDGE KIT"
    assert bridge.rytm_message_count == 6
    assert bridge.analog_four_track_count == 4
    assert bridge.analog_four_message_count == 20
    assert bridge.combined_message_count == 26
    assert len(sender.sent_messages) == 26
    first = sender.sent_messages[0]
    assert first.channel == 0
    assert first.control == 17
    assert first.value == 60
    assert first.metadata["device"] == "Analog Rytm MKII"
    assert first.metadata["baseline_value"] == 59
    last = sender.sent_messages[-1]
    assert last.channel == 3
    assert last.metadata["device"] == "Analog Four MKII"
    assert last.metadata["track"] == 4
    assert {message.metadata["device"] for message in sender.sent_messages} == {
        "Analog Rytm MKII",
        "Analog Four MKII",
    }
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```powershell
pytest tests\test_dual_machine_mock_bridge.py -q
```

Expected: FAIL with `ModuleNotFoundError: No module named 'rytm_randomizer.dual_machine_mock_bridge'`.

- [ ] **Step 3: Implement module**

Create `rytm_randomizer/dual_machine_mock_bridge.py` with dataclasses for:

- `AnalogFourStarterChange`
- `AnalogFourTrackPlan`
- `DualMachineMockBridge`

Required functions:

- `build_dual_machine_mock_bridge(path, *, slot, depth)`
- `capture_dual_machine_mock_messages(bridge)`
- `format_dual_machine_mock_bridge_report(bridge)`
- `format_dual_machine_mock_bridge_error(path, message)`

The A4 starter plan must produce five mapped CC changes per track:

- Track 1: `Track Level` CC95 -> 104, `OSC1 Level` CC69 -> 96,
  `OSC2 Level` CC78 -> 72, `Filter 1 Frequency` CC18 -> 112,
  `Amp Pan` CC10 -> 60
- Track 2: `Track Level` CC95 -> 100, `OSC1 Waveform` CC70 -> 2,
  `Filter 1 Frequency` CC18 -> 104, `Amp Env Decay` CC105 -> 54,
  `Amp Pan` CC10 -> 68
- Track 3: `Track Level` CC95 -> 92, `OSC1 Level` CC69 -> 82,
  `OSC2 Level` CC78 -> 88, `Filter 2 Frequency` CC19 -> 74,
  `Reverb Send` CC93 -> 36
- Track 4: `Track Level` CC95 -> 88, `Noise Level` CC77 -> 72,
  `Noise Fade` CC76 -> 68, `Filter 1 Frequency` CC18 -> 88,
  `Amp Pan` CC10 -> 64

All messages must use wire channel `track - 1` for A4 and `pad - 1` for Rytm.

- [ ] **Step 4: Run tests to verify pass**

Run:

```powershell
pytest tests\test_dual_machine_mock_bridge.py -q
```

Expected: PASS.

## Task 2: CLI Report And Help

**Files:**
- Modify: `rytm_randomizer/cli.py`
- Modify: `rytm_randomizer/help_text.py`
- Modify: `tests/test_cli.py`
- Modify: `tests/fixtures/cli_help_expected.txt`
- Test: `tests/test_dual_machine_mock_bridge.py`

- [ ] **Step 1: Add failing CLI test**

Append to `tests/test_dual_machine_mock_bridge.py`:

```python
def run_cli(*args):
    return subprocess.run(
        [sys.executable, "-m", "rytm_randomizer.cli", *args],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def test_dual_machine_mock_bridge_cli_reads_saved_kit_without_hardware(tmp_path):
    sysex_path = tmp_path / "kits.syx"
    sysex_path.write_bytes(make_rytm_kit_record(kit_name="CLI BRIDGE"))

    result = run_cli(
        "dual-machine-mock-bridge-report",
        str(sysex_path),
        "--slot",
        "1",
        "--depth",
        "micro",
    )

    assert result.returncode == 0
    assert "RytmRandomizer passive Dual-Machine Mock Bridge Report" in result.stdout
    assert "Rytm source: saved-kit snapshot" in result.stdout
    assert "Analog Four source: safe starter CC plan" in result.stdout
    assert "Combined mock messages: 26" in result.stdout
    assert "- Analog Four Track 4 / FX / noise / transition: 5 message(s)" in result.stdout
    assert "- mock sender only" in result.stdout
    assert "- no MIDI sending" in result.stdout
    assert result.stderr == ""
```

Add to `tests/test_cli.py`:

```python
def test_dual_machine_mock_bridge_report_help_exits_zero():
    result = run_cli("dual-machine-mock-bridge-report", "--help")

    assert result.returncode == 0
    assert "RytmRandomizer passive CLI: dual-machine-mock-bridge-report" in result.stdout
    assert "Rytm + Analog Four" in result.stdout
    assert "mock sender only" in result.stdout
    assert "no MIDI sending" in result.stdout
    assert result.stderr == ""
```

- [ ] **Step 2: Run tests to verify fail**

Run:

```powershell
pytest tests\test_dual_machine_mock_bridge.py tests\test_cli.py::test_dual_machine_mock_bridge_report_help_exits_zero -q
```

Expected: FAIL because the CLI command and help text are not wired.

- [ ] **Step 3: Wire CLI**

In `rytm_randomizer/cli.py`, add a dispatch block matching:

```python
dual-machine-mock-bridge-report <path> --slot <slot> --depth <depth>
```

It should call:

```python
build_dual_machine_mock_bridge(args[1], slot=slot, depth=args[5])
format_dual_machine_mock_bridge_report(bridge)
```

Errors should use `format_dual_machine_mock_bridge_error`.

- [ ] **Step 4: Update help text**

In `rytm_randomizer/help_text.py` and `tests/fixtures/cli_help_expected.txt`, add:

```text
python -m rytm_randomizer.cli dual-machine-mock-bridge-report <path> --slot <1-128> --depth <micro|groove|strong>
```

Command description:

```text
dual-machine-mock-bridge-report
                     Preview a combined Rytm + Analog Four mock performance stream.
```

Add command-specific help explaining it is passive, mock sender only, no MIDI sending, no port opening.

- [ ] **Step 5: Run tests to verify pass**

Run:

```powershell
pytest tests\test_dual_machine_mock_bridge.py tests\test_cli.py::test_top_level_help_exits_zero_and_matches_fixture tests\test_cli.py::test_dual_machine_mock_bridge_report_help_exits_zero -q
```

Expected: PASS.

## Task 3: Docs And Real File Verification

**Files:**
- Create: `Docs/DUAL_MACHINE_MOCK_BRIDGE_CHECKPOINT.md`
- Modify: `Docs/PASSIVE_CLI_OPERATOR_QUICKSTART.md`

- [ ] **Step 1: Add checkpoint doc**

Create `Docs/DUAL_MACHINE_MOCK_BRIDGE_CHECKPOINT.md` documenting:

- purpose
- command
- Rytm source: saved-kit snapshot
- A4 source: safe starter CC plan
- safety boundary
- next steps: A4 snapshot decoder or dry-run operator flow

- [ ] **Step 2: Update quickstart**

Add a "Dual-Machine Mock Bridge Report" section with:

```powershell
python -m rytm_randomizer.cli dual-machine-mock-bridge-report "G:\ANALOG RYTM\KITS\ANALOGRYTMKITS2.syx" --slot 16 --depth micro
```

- [ ] **Step 3: Run focused tests and real reports**

Run:

```powershell
pytest tests\test_dual_machine_mock_bridge.py tests\test_snapshot_mutation_planner.py tests\test_sysex_snapshot_decoder.py tests\test_cli.py tests\architecture\test_no_side_effects.py -q
```

Expected: all selected tests pass.

Run:

```powershell
python -m rytm_randomizer.cli dual-machine-mock-bridge-report "G:\ANALOG RYTM\KITS\ANALOGRYTMKITS2.syx" --slot 16 --depth micro
```

Expected: report exits zero and shows combined Rytm + Analog Four mock message counts.

- [ ] **Step 4: Final safety checks**

Run:

```powershell
git diff --check
git diff -- rytm_hybrid_randomizer_v134.py
```

Expected: no whitespace errors except existing CRLF warnings; protected V1.34 diff empty.
