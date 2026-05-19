# Analog Four Guarded Runtime Dry-Run Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build an A4-only guarded runtime dry-run path that emits the existing Track 1-4 runtime plan into `MockMidiSender` only.

**Architecture:** Add an A4-owned guarded sender module beside `analog_four/runtime_plan.py`, wire it into the passive CLI, then add an app dry-run flag that reuses the same module. Keep real MIDI blocked for this slice; the app must reject `--arm --analog-four-runtime`.

**Tech Stack:** Python dataclasses, existing `MockMidiSender`, existing `analog_four.runtime_plan`, current `cli.py` and `app.py` command patterns, pytest.

---

## File Structure

- Create `rytm_randomizer/analog_four/guarded_runtime_sender.py`
  - Owns A4-only guarded dry-run execution and report formatting.
  - Imports only passive/mock helpers.
  - Does not import `mido`, `rtmidi`, provider classes, real adapters, or app wiring.
- Modify `rytm_randomizer/cli.py`
  - Adds `analog-four-runtime-guarded-send-dry-run [--profile <profile>]`.
  - Returns 1 with an error report for unknown profiles.
- Modify `rytm_randomizer/help_text.py`
  - Adds top-level and command-specific help.
- Modify `tests/fixtures/cli_help_expected.txt` and `tests/test_cli.py`
  - Keeps static CLI help fixture green.
- Modify `rytm_randomizer/app.py`
  - Adds `--analog-four-runtime` and reuses existing `--analog-four-profile`.
  - Allows only `--dry-run --analog-four-runtime`.
  - Rejects `--arm --analog-four-runtime` in this slice.
- Add `tests/test_analog_four_guarded_runtime_sender.py`
  - Covers the module and passive CLI.
- Modify `tests/test_app_entry.py`
  - Covers app dry-run and arm rejection.
- Modify `docs/STATUS.md` and `docs/FUTURE_ANALOG_FOUR_EXPANSION.md`
  - Records the new A4-only guarded dry-run boundary.

---

### Task 1: A4 Guarded Sender Module

**Files:**
- Create: `rytm_randomizer/analog_four/guarded_runtime_sender.py`
- Test: `tests/test_analog_four_guarded_runtime_sender.py`

- [ ] **Step 1: Write failing tests for passive import, accepted send, and blocking**

Create `tests/test_analog_four_guarded_runtime_sender.py`:

```python
import subprocess
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.fast

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def run_cli(*args):
    return subprocess.run(
        [sys.executable, "-m", "rytm_randomizer.cli", *args],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def test_importing_a4_guarded_runtime_sender_is_passive_and_silent():
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import sys; "
                "import rytm_randomizer.analog_four.guarded_runtime_sender; "
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


def test_a4_guarded_runtime_dry_run_emits_balanced_mock_messages():
    from rytm_randomizer.analog_four.guarded_runtime_sender import (
        build_analog_four_runtime_guarded_send_dry_run,
    )
    from rytm_randomizer.analog_four.runtime_plan import build_analog_four_runtime_plan

    plan = build_analog_four_runtime_plan(profile="balanced")
    result = build_analog_four_runtime_guarded_send_dry_run(plan)

    assert result.device == "Elektron Analog Four MKII"
    assert result.accepted is True
    assert result.reason == "accepted_a4_guarded_mock_only"
    assert result.plan_ready is True
    assert result.eligible_message_count == 20
    assert result.blocked_event_count == 0
    assert result.emitted_message_count == 20
    assert result.track_count == 4
    assert result.starter_profile_key == "balanced"
    assert result.starter_profile_label == "Balanced"
    assert result.mock_only is True
    assert result.sends_real_midi is False

    first = result.emitted_messages[0]
    assert first.type == "cc"
    assert first.channel == 0
    assert first.control == 95
    assert first.value == 104
    assert first.metadata["guard"] == "analog_four_runtime_guarded_send_dry_run"
    assert first.metadata["device"] == "Elektron Analog Four MKII"
    assert first.metadata["track"] == 1
    assert first.metadata["midi_channel"] == 1
    assert first.metadata["wire_channel"] == 0
    assert first.metadata["role"] == "bass / low tonal anchor"
    assert first.metadata["parameter"] == "Track Level"
    assert first.metadata["starter_profile_key"] == "balanced"
    assert first.metadata["mock_only"] is True
    assert first.metadata["sends_real_midi"] is False


def test_a4_guarded_runtime_preserves_birmingham_dark_values():
    from rytm_randomizer.analog_four.guarded_runtime_sender import (
        build_analog_four_runtime_guarded_send_dry_run,
    )
    from rytm_randomizer.analog_four.runtime_plan import build_analog_four_runtime_plan

    plan = build_analog_four_runtime_plan(profile="birmingham-dark")
    result = build_analog_four_runtime_guarded_send_dry_run(plan)

    assert result.accepted is True
    first = result.emitted_messages[0]
    assert first.channel == 0
    assert first.control == 95
    assert first.value == 106
    assert first.metadata["role"] == "dark bass pressure"
    assert first.metadata["starter_profile_key"] == "birmingham-dark"


def test_a4_guarded_runtime_blocks_without_arming_or_confirmation():
    from rytm_randomizer.analog_four.guarded_runtime_sender import (
        execute_analog_four_runtime_guarded_send,
    )
    from rytm_randomizer.analog_four.runtime_plan import build_analog_four_runtime_plan
    from rytm_randomizer.mock_midi import MockMidiSender

    plan = build_analog_four_runtime_plan(profile="balanced")
    sender = MockMidiSender()

    missing_armed = execute_analog_four_runtime_guarded_send(
        plan,
        sender,
        armed=False,
        dry_run_confirmed=True,
    )
    assert missing_armed.accepted is False
    assert missing_armed.reason == "missing_arming"
    assert missing_armed.emitted_message_count == 0
    assert len(sender.sent_messages) == 0

    missing_confirmation = execute_analog_four_runtime_guarded_send(
        plan,
        sender,
        armed=True,
        dry_run_confirmed=False,
    )
    assert missing_confirmation.accepted is False
    assert missing_confirmation.reason == "missing_dry_run_confirmation"
    assert missing_confirmation.emitted_message_count == 0
    assert len(sender.sent_messages) == 0


def test_format_a4_guarded_runtime_report_shows_policy_and_stream():
    from rytm_randomizer.analog_four.guarded_runtime_sender import (
        build_analog_four_runtime_guarded_send_dry_run,
        format_analog_four_runtime_guarded_send_dry_run_report,
    )
    from rytm_randomizer.analog_four.runtime_plan import build_analog_four_runtime_plan

    result = build_analog_four_runtime_guarded_send_dry_run(
        build_analog_four_runtime_plan(profile="detroit-classic")
    )
    report = format_analog_four_runtime_guarded_send_dry_run_report(result)

    assert report[0] == "RytmRandomizer passive Analog Four Guarded Runtime Dry-Run Report"
    assert "Device: Elektron Analog Four MKII" in report
    assert "Starter profile: Detroit Classic / detroit-classic" in report
    assert "Accepted: True" in report
    assert "Reason: accepted_a4_guarded_mock_only" in report
    assert "Plan ready: True" in report
    assert "Eligible mapped CC messages: 20" in report
    assert "Emitted mock messages: 20" in report
    assert "- Track 1 / analog bass motif: 5 message(s)" in report
    assert "- Track 1 ch 1 wire 0 / Track Level CC95 -> 100" in report
    assert "- A4-only guarded dry-run" in report
    assert "- no Rytm MIDI sending" in report
    assert "- no MIDI sending" in report


def test_a4_guarded_runtime_cli_accepts_profile():
    result = run_cli("analog-four-runtime-guarded-send-dry-run", "--profile", "birmingham-dark")

    assert result.returncode == 0
    assert "RytmRandomizer passive Analog Four Guarded Runtime Dry-Run Report" in result.stdout
    assert "Starter profile: Birmingham Dark / birmingham-dark" in result.stdout
    assert "Accepted: True" in result.stdout
    assert "Track 1 ch 1 wire 0 / Track Level CC95 -> 106" in result.stdout
    assert "- no Rytm MIDI sending" in result.stdout
    assert result.stderr == ""


def test_a4_guarded_runtime_cli_rejects_unknown_profile_safely():
    result = run_cli("analog-four-runtime-guarded-send-dry-run", "--profile", "acid-swamp")

    assert result.returncode == 1
    assert result.stdout == ""
    assert "RytmRandomizer passive Analog Four Guarded Runtime Dry-Run Report" in result.stderr
    assert "Unknown Analog Four starter profile: acid-swamp" in result.stderr
    assert "No MIDI was sent" in result.stderr
```

- [ ] **Step 2: Run tests to verify RED**

Run:

```powershell
python -m pytest tests/test_analog_four_guarded_runtime_sender.py -q -n 0
```

Expected: fails because `rytm_randomizer.analog_four.guarded_runtime_sender` does not exist and the CLI command is unknown.

- [ ] **Step 3: Implement guarded sender module**

Create `rytm_randomizer/analog_four/guarded_runtime_sender.py` with:

```python
"""Mock-only guarded sender for Analog Four runtime plans.

This module proves the A4 runtime guard without opening MIDI ports or sending
hardware MIDI. It accepts only a MockMidiSender and emits only mapped CC
events from an AnalogFourRuntimePlan.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType

from ..mock_midi import MidiMessage, MockMidiSender, build_cc_message
from .runtime_plan import AnalogFourRuntimeEvent, AnalogFourRuntimePlan

GUARD_NAME = "analog_four_runtime_guarded_send_dry_run"


def _freeze_metadata(metadata: Mapping[str, object] | None) -> Mapping[str, object]:
    if metadata is None:
        return MappingProxyType({})
    return MappingProxyType(dict(metadata))


@dataclass(frozen=True)
class AnalogFourRuntimeGuardedSendResult:
    """Result from a mock-only A4 guarded runtime send attempt."""

    device: str
    accepted: bool
    reason: str
    plan_ready: bool
    eligible_message_count: int
    blocked_event_count: int
    emitted_messages: tuple[MidiMessage, ...]
    starter_profile_key: str
    starter_profile_label: str
    mock_only: bool = True
    sends_real_midi: bool = False
    metadata: Mapping[str, object] = field(default_factory=lambda: MappingProxyType({}))

    def __post_init__(self) -> None:
        object.__setattr__(self, "emitted_messages", tuple(self.emitted_messages))
        object.__setattr__(self, "metadata", _freeze_metadata(self.metadata))

    @property
    def emitted_message_count(self) -> int:
        return len(self.emitted_messages)

    @property
    def track_count(self) -> int:
        return len({message.metadata["track"] for message in self.emitted_messages})


def execute_analog_four_runtime_guarded_send(
    plan: AnalogFourRuntimePlan,
    sender: MockMidiSender,
    *,
    armed: bool,
    dry_run_confirmed: bool,
) -> AnalogFourRuntimeGuardedSendResult:
    """Execute an A4 runtime plan into an injected mock sender."""

    if not isinstance(plan, AnalogFourRuntimePlan):
        raise TypeError("plan must be an AnalogFourRuntimePlan")
    if not isinstance(sender, MockMidiSender):
        raise TypeError("sender must be a MockMidiSender")

    events = tuple(event for track in plan.tracks for event in track.events)
    if not armed:
        return _blocked_result(plan, events, "missing_arming")
    if not dry_run_confirmed:
        return _blocked_result(plan, events, "missing_dry_run_confirmation")

    messages = tuple(_message_from_event(plan, event) for event in events)
    sender.send_many(messages)
    return AnalogFourRuntimeGuardedSendResult(
        device=plan.device,
        accepted=True,
        reason="accepted_a4_guarded_mock_only",
        plan_ready=True,
        eligible_message_count=len(messages),
        blocked_event_count=0,
        emitted_messages=messages,
        starter_profile_key=plan.starter_profile_key,
        starter_profile_label=plan.starter_profile_label,
        metadata=_result_metadata(plan, "accepted_a4_guarded_mock_only", len(messages), 0),
    )


def build_analog_four_runtime_guarded_send_dry_run(
    plan: AnalogFourRuntimePlan,
) -> AnalogFourRuntimeGuardedSendResult:
    """Build and execute an A4 runtime guarded dry-run into a fresh mock sender."""

    sender = MockMidiSender()
    return execute_analog_four_runtime_guarded_send(
        plan,
        sender,
        armed=True,
        dry_run_confirmed=True,
    )


def format_analog_four_runtime_guarded_send_dry_run_report(
    result: AnalogFourRuntimeGuardedSendResult,
) -> list[str]:
    """Format a deterministic A4 guarded runtime dry-run report."""

    lines = [
        "RytmRandomizer passive Analog Four Guarded Runtime Dry-Run Report",
        f"Device: {result.device}",
        f"Starter profile: {result.starter_profile_label} / {result.starter_profile_key}",
        f"Accepted: {result.accepted}",
        f"Reason: {result.reason}",
        f"Plan ready: {result.plan_ready}",
        f"Eligible mapped CC messages: {result.eligible_message_count}",
        f"Blocked candidate events: {result.blocked_event_count}",
        f"Emitted mock messages: {result.emitted_message_count}",
        "Track coverage:",
    ]
    lines.extend(_track_coverage_lines(result))
    lines.append("Mock emission preview:")
    if result.emitted_messages:
        lines.extend(_format_message_line(message) for message in result.emitted_messages)
    else:
        lines.append("- no messages emitted")
    lines.extend(_safety_lines())
    return lines


def format_analog_four_runtime_guarded_send_error(message: str) -> list[str]:
    """Format deterministic A4 guarded dry-run errors."""

    return [
        "RytmRandomizer passive Analog Four Guarded Runtime Dry-Run Report",
        "Found: False",
        f"Message: {message}. No MIDI was sent. No command executed.",
        *_safety_lines(),
    ]


def _blocked_result(
    plan: AnalogFourRuntimePlan,
    events: tuple[AnalogFourRuntimeEvent, ...],
    reason: str,
) -> AnalogFourRuntimeGuardedSendResult:
    return AnalogFourRuntimeGuardedSendResult(
        device=plan.device,
        accepted=False,
        reason=reason,
        plan_ready=True,
        eligible_message_count=len(events),
        blocked_event_count=0,
        emitted_messages=(),
        starter_profile_key=plan.starter_profile_key,
        starter_profile_label=plan.starter_profile_label,
        metadata=_result_metadata(plan, reason, len(events), 0),
    )


def _message_from_event(plan: AnalogFourRuntimePlan, event: AnalogFourRuntimeEvent) -> MidiMessage:
    return build_cc_message(
        channel=event.wire_channel,
        control=event.cc,
        value=event.value,
        metadata={
            "guard": GUARD_NAME,
            "device": plan.device,
            "track": event.track,
            "midi_channel": event.midi_channel,
            "wire_channel": event.wire_channel,
            "role": event.role_label,
            "parameter": event.parameter_name,
            "starter_profile_key": plan.starter_profile_key,
            "starter_profile_label": plan.starter_profile_label,
            "eligible_reason": "mapped_cc_message",
            "mock_only": True,
            "sends_real_midi": False,
        },
    )


def _result_metadata(
    plan: AnalogFourRuntimePlan,
    reason: str,
    eligible_message_count: int,
    blocked_event_count: int,
) -> dict[str, object]:
    return {
        "guard": GUARD_NAME,
        "device": plan.device,
        "reason": reason,
        "starter_profile_key": plan.starter_profile_key,
        "starter_profile_label": plan.starter_profile_label,
        "eligible_message_count": eligible_message_count,
        "blocked_event_count": blocked_event_count,
        "mock_only": True,
        "sends_real_midi": False,
    }


def _track_coverage_lines(result: AnalogFourRuntimeGuardedSendResult) -> list[str]:
    if not result.emitted_messages:
        return ["- no track messages emitted"]
    counts = Counter(message.metadata["track"] for message in result.emitted_messages)
    role_by_track = {}
    for message in result.emitted_messages:
        role_by_track.setdefault(message.metadata["track"], message.metadata["role"])
    return [
        f"- Track {track} / {role_by_track[track]}: {counts[track]} message(s)"
        for track in sorted(counts)
    ]


def _format_message_line(message: MidiMessage) -> str:
    metadata = message.metadata
    return (
        f"- Track {metadata['track']} ch {metadata['midi_channel']} "
        f"wire {metadata['wire_channel']} / {metadata['parameter']} "
        f"CC{message.control} -> {message.value}"
    )


def _safety_lines() -> list[str]:
    return [
        "Guard policy:",
        "- A4-only guarded dry-run",
        "- requires arming and dry-run confirmation",
        "- emits mapped CC messages only",
        "- blocked plans emit no partial messages",
        "Safety:",
        "- passive/read-only",
        "- A4-only guarded dry-run",
        "- mock sender only",
        "- no Rytm MIDI sending",
        "- no MIDI sending",
        "- no MIDI receive",
        "- no port opening",
        "- no command execution",
        "- no hardware mutation",
        "- no live SysEx receive",
        "- no SysEx writes",
        "- no hardware required",
    ]


__all__ = [
    "AnalogFourRuntimeGuardedSendResult",
    "GUARD_NAME",
    "build_analog_four_runtime_guarded_send_dry_run",
    "execute_analog_four_runtime_guarded_send",
    "format_analog_four_runtime_guarded_send_dry_run_report",
    "format_analog_four_runtime_guarded_send_error",
]
```

- [ ] **Step 4: Run tests to verify GREEN**

Run:

```powershell
python -m pytest tests/test_analog_four_guarded_runtime_sender.py -q -n 0
```

Expected: module tests pass; CLI tests still fail until Task 2.

---

### Task 2: Passive CLI Command

**Files:**
- Modify: `rytm_randomizer/cli.py`
- Modify: `rytm_randomizer/help_text.py`
- Modify: `tests/test_cli.py`
- Modify: `tests/fixtures/cli_help_expected.txt`
- Test: `tests/test_analog_four_guarded_runtime_sender.py`

- [ ] **Step 1: Add CLI dispatch**

In `rytm_randomizer/cli.py`, after the existing `analog-four-runtime-report` branch, add:

```python
    if args and args[0] == "analog-four-runtime-guarded-send-dry-run":
        from .analog_four.guarded_runtime_sender import (
            build_analog_four_runtime_guarded_send_dry_run,
            format_analog_four_runtime_guarded_send_dry_run_report,
            format_analog_four_runtime_guarded_send_error,
        )
        from .analog_four.runtime_plan import build_analog_four_runtime_plan

        if len(args) not in (1, 3):
            sys.stderr.write(f"{USAGE}\n")
            return 2
        if len(args) == 3 and args[1] != "--profile":
            sys.stderr.write(f"{USAGE}\n")
            return 2

        profile = "balanced" if len(args) == 1 else args[2]
        try:
            plan = build_analog_four_runtime_plan(profile=profile)
            result = build_analog_four_runtime_guarded_send_dry_run(plan)
        except ValueError as exc:
            sys.stderr.write("\n".join(format_analog_four_runtime_guarded_send_error(str(exc))))
            sys.stderr.write("\n")
            return 1

        sys.stdout.write("\n".join(format_analog_four_runtime_guarded_send_dry_run_report(result)))
        sys.stdout.write("\n")
        return 0
```

- [ ] **Step 2: Add help text**

In `rytm_randomizer/help_text.py`:

- Add to `USAGE` near the A4 runtime report:

```python
"analog-four-runtime-guarded-send-dry-run [--profile <profile>] | "
```

- Add to top-level help usage:

```text
  python -m rytm_randomizer.cli analog-four-runtime-guarded-send-dry-run
  python -m rytm_randomizer.cli analog-four-runtime-guarded-send-dry-run --profile <profile>
```

- Add to top-level command list:

```text
  analog-four-runtime-guarded-send-dry-run
                     Execute A4 runtime events into a mock guarded sender only.
```

- Add `HELP_TEXT["analog-four-runtime-guarded-send-dry-run"]`:

```python
    "analog-four-runtime-guarded-send-dry-run": """RytmRandomizer passive CLI: analog-four-runtime-guarded-send-dry-run

Usage:
  python -m rytm_randomizer.cli analog-four-runtime-guarded-send-dry-run
  python -m rytm_randomizer.cli analog-four-runtime-guarded-send-dry-run --profile <profile>
  python -m rytm_randomizer.cli analog-four-runtime-guarded-send-dry-run --help

Behavior:
  Builds an Analog Four Track 1-4 runtime plan from manual-backed starter
  profiles, then executes eligible mapped CC events into an inert guarded mock
  sender. It does not open ports, send MIDI, receive SysEx, write SysEx, touch
  the Rytm, or mutate hardware.

Safety:
  passive/read-only
  A4-only guarded dry-run
  mock sender only
  no Rytm MIDI sending
  no MIDI sending
  no MIDI receive
  no port opening
  no command execution
  no hardware mutation
  no live SysEx receive
  no SysEx writes
  no hardware required""",
```

- [ ] **Step 3: Update help fixture and USAGE constant in tests**

In `tests/test_cli.py`, update the local `USAGE` string to include:

```python
"analog-four-runtime-guarded-send-dry-run [--profile <profile>] | "
```

In `tests/fixtures/cli_help_expected.txt`, add the new usage and command lines matching `help_text.py`.

- [ ] **Step 4: Run CLI tests**

Run:

```powershell
python -m pytest tests/test_analog_four_guarded_runtime_sender.py tests/test_cli.py::test_top_level_help_exits_zero_and_matches_fixture -q -n 0
```

Expected: all selected tests pass.

---

### Task 3: App Dry-Run Flag

**Files:**
- Modify: `rytm_randomizer/app.py`
- Modify: `tests/test_app_entry.py`

- [ ] **Step 1: Write failing app tests**

Add to `tests/test_app_entry.py` near existing A4 smoke dry-run tests:

```python
def test_app_main_dry_run_analog_four_runtime_uses_guarded_mock_sender(capsys):
    _seed()
    from rytm_randomizer import app

    exit_code = app.main(
        [
            "--dry-run",
            "--analog-four-runtime",
            "--analog-four-profile",
            "birmingham-dark",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "guarded Analog Four runtime send" in captured.out
    assert "Analog Four Guarded Runtime Dry-Run Report" in captured.out
    assert "Starter profile: Birmingham Dark / birmingham-dark" in captured.out
    assert "Accepted: True" in captured.out
    assert "Emitted mock messages: 20" in captured.out
    assert "Track 1 ch 1 wire 0 / Track Level CC95 -> 106" in captured.out
    assert "Dry-run complete. Mock sender captured 20 message(s)." in captured.out
    assert "Select target pad" not in captured.out
    assert captured.err == ""


def test_app_main_arm_analog_four_runtime_is_blocked_for_now(capsys):
    _seed()
    from rytm_randomizer import app

    exit_code = app.main(["--arm", "--analog-four-runtime"])
    captured = capsys.readouterr()

    assert exit_code == 2
    assert "--analog-four-runtime supports --dry-run only in this slice" in captured.err
    assert "Available MIDI outputs" not in captured.out
```

- [ ] **Step 2: Run app tests to verify RED**

Run:

```powershell
python -m pytest tests/test_app_entry.py::test_app_main_dry_run_analog_four_runtime_uses_guarded_mock_sender tests/test_app_entry.py::test_app_main_arm_analog_four_runtime_is_blocked_for_now -q -n 0
```

Expected: fails because app parser does not know `--analog-four-runtime`.

- [ ] **Step 3: Add parser flag and request helper**

In `_build_parser()` add:

```python
    parser.add_argument(
        "--analog-four-runtime",
        action="store_true",
        help=(
            "With --dry-run only, execute the Analog Four Track 1-4 runtime "
            "plan into a guarded mock sender. Real MIDI is blocked for this slice."
        ),
    )
```

Add helper after `_rytm_engine_cycle_request_from_args`:

```python
def _analog_four_runtime_request_from_args(
    args: argparse.Namespace,
) -> dict[str, object] | None:
    if not args.analog_four_runtime:
        return None
    return {
        "analog_four_profile": args.analog_four_profile or "balanced",
    }
```

- [ ] **Step 4: Add dry-run runner**

Add near `_run_dry_run_dual_machine_snapshot_send`:

```python
def _run_dry_run_analog_four_runtime(request: dict[str, object]) -> int:
    """Run the guarded A4 runtime send against the mock sender."""

    from .analog_four.guarded_runtime_sender import (
        build_analog_four_runtime_guarded_send_dry_run,
        format_analog_four_runtime_guarded_send_dry_run_report,
        format_analog_four_runtime_guarded_send_error,
    )
    from .analog_four.runtime_plan import build_analog_four_runtime_plan

    sys.stdout.write(
        "RytmRandomizer --dry-run: guarded Analog Four runtime send "
        "(mock-only, no hardware, no port opened).\n"
    )
    try:
        plan = build_analog_four_runtime_plan(
            profile=str(request.get("analog_four_profile") or "balanced")
        )
        result = build_analog_four_runtime_guarded_send_dry_run(plan)
    except ValueError as exc:
        sys.stdout.write("\n".join(format_analog_four_runtime_guarded_send_error(str(exc))))
        sys.stdout.write("\n")
        return 1

    sys.stdout.write("\n".join(format_analog_four_runtime_guarded_send_dry_run_report(result)))
    sys.stdout.write("\n")
    sys.stdout.write(
        f"Dry-run complete. Mock sender captured {result.emitted_message_count} message(s).\n"
    )
    return 0 if result.accepted else 1
```

- [ ] **Step 5: Wire request into `_run_dry_run`, validation, and mode conflicts**

In `_run_dry_run(...)` signature add:

```python
    analog_four_runtime_request: dict[str, object] | None = None,
```

Before other request checks add:

```python
    if analog_four_runtime_request is not None:
        return _run_dry_run_analog_four_runtime(analog_four_runtime_request)
```

In `main()`, after `rytm_engine_cycle_request`:

```python
    analog_four_runtime_request = _analog_four_runtime_request_from_args(args)
```

Add `bool(args.analog_four_runtime)` to `active_snapshot_modifier_count`.

Update active-mode conflict messages to include `--analog-four-runtime`.

Add validation:

```python
    if args.analog_four_runtime and not (args.arm or args.dry_run):
        sys.stderr.write("--analog-four-runtime requires --dry-run in this slice.\n")
        return 2

    if args.analog_four_runtime and args.arm:
        sys.stderr.write("--analog-four-runtime supports --dry-run only in this slice.\n")
        return 2

    if args.analog_four_profile is not None and not (
        args.dual_machine_snapshot_send or args.analog_four_runtime
    ):
        sys.stderr.write("--analog-four-profile requires --dual-machine-snapshot-send or --analog-four-runtime.\n")
        return 2
```

When calling `_run_dry_run(...)`, pass:

```python
            analog_four_runtime_request=analog_four_runtime_request,
```

Do not pass the request to `_run_arm(...)` because arm is blocked before that branch.

- [ ] **Step 6: Run app tests**

Run:

```powershell
python -m pytest tests/test_app_entry.py::test_app_main_dry_run_analog_four_runtime_uses_guarded_mock_sender tests/test_app_entry.py::test_app_main_arm_analog_four_runtime_is_blocked_for_now -q -n 0
```

Expected: both pass.

---

### Task 4: Docs, Verification, Commit

**Files:**
- Modify: `docs/STATUS.md`
- Modify: `docs/FUTURE_ANALOG_FOUR_EXPANSION.md`

- [ ] **Step 1: Update project status**

Add a 2026-05-19 bullet to `docs/STATUS.md`:

```markdown
- 2026-05-19: added the A4-only guarded runtime dry-run path.
  `analog-four-runtime-guarded-send-dry-run [--profile <profile>]` and
  `rytm-randomizer --dry-run --analog-four-runtime --analog-four-profile <profile>`
  execute the manual-backed A4 Track 1-4 runtime plan into a guarded mock
  sender only. The path emits no real MIDI, opens no ports, touches no Rytm
  state, and rejects `--arm --analog-four-runtime` until a separate hardware
  slice is approved.
```

- [ ] **Step 2: Update A4 future checkpoint**

In `docs/FUTURE_ANALOG_FOUR_EXPANSION.md`, add a short section after "Current Passive Runtime Plan":

```markdown
## Current Guarded Runtime Dry-Run

`python -m rytm_randomizer.cli analog-four-runtime-guarded-send-dry-run [--profile <profile>]`
and `rytm-randomizer --dry-run --analog-four-runtime --analog-four-profile <profile>`
now prove the A4 runtime plan through an A4-only guarded mock sender. This is
the sender-shaped gate before real hardware. It does not open an A4 port, send
MIDI, touch the Rytm, receive live SysEx, write SysEx, or mutate hardware.
```

- [ ] **Step 3: Run focused verification**

Run:

```powershell
python -m pytest tests/test_analog_four_guarded_runtime_sender.py tests/test_analog_four_runtime_plan.py tests/test_app_entry.py::test_app_main_dry_run_analog_four_runtime_uses_guarded_mock_sender tests/test_app_entry.py::test_app_main_arm_analog_four_runtime_is_blocked_for_now -q -n 0
```

Expected: all selected tests pass.

- [ ] **Step 4: Run full fast suite**

Run:

```powershell
python -m pytest -m fast -q -n 0
```

Expected: all fast tests pass with known skips only.

- [ ] **Step 5: Run full suite**

Run:

```powershell
python -m pytest -q -n 0
```

Expected: all tests pass with known skips only.

- [ ] **Step 6: Commit and push**

Run:

```powershell
git status --short
git add rytm_randomizer/analog_four/guarded_runtime_sender.py rytm_randomizer/cli.py rytm_randomizer/help_text.py rytm_randomizer/app.py tests/test_analog_four_guarded_runtime_sender.py tests/test_app_entry.py tests/test_cli.py tests/fixtures/cli_help_expected.txt docs/STATUS.md docs/FUTURE_ANALOG_FOUR_EXPANSION.md
git commit -m "feat: add a4 guarded runtime dry run"
git push origin codex/12-pad-rytm-engine-runtime-design
```

Expected: branch pushes cleanly.

---

## Self-Review

- Spec coverage: this plan covers the A4-only guarded module, passive CLI dry-run, app dry-run flag, arm rejection, safety reporting, docs, and verification.
- Placeholder scan: no TBD/TODO placeholders are present.
- Type consistency: the plan uses `AnalogFourRuntimePlan`, `AnalogFourRuntimeGuardedSendResult`, and `MockMidiSender` consistently with existing module patterns.
- Scope check: real MIDI, A4 port selection, dual-machine coupling, SysEx, GUI, and audio analysis are explicitly out of scope.
