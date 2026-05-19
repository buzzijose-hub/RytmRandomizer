# Analog Four Runtime Hardware Send Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add an A4-only armed runtime sender that sends the existing Track 1-4 runtime CC plan only after `--arm`, port selection, and exact `SEND` confirmation.

**Architecture:** Create `analog_four/hardware_runtime_sender.py` as the active counterpart to the mock guarded sender. Wire `app.py` so `--arm --analog-four-runtime --analog-four-profile <profile>` builds the plan, asks for an Analog Four port, asks for `SEND`, opens the port after confirmation, and sends only those A4 CC events.

**Tech Stack:** Python dataclasses, existing `midi_io.send_cc`, existing `analog_four.runtime_plan`, existing `app.py` provider/confirmation patterns, pytest fake mido ports.

---

## File Structure

- Create `rytm_randomizer/analog_four/hardware_runtime_sender.py`
  - Executes `AnalogFourRuntimePlan` through an injected output port.
  - Refuses without `armed=True` and `operator_confirmed=True`.
  - Imports no real MIDI backend at module load.
- Add `tests/test_analog_four_hardware_runtime_sender.py`
  - Covers import safety, refusals, accepted fake-port sends, report text.
- Modify `rytm_randomizer/app.py`
  - Removes the temporary arm block for `--analog-four-runtime`.
  - Adds `_run_arm_analog_four_runtime`.
  - Adds `_confirm_analog_four_runtime_send`.
- Modify `tests/test_app_entry.py`
  - Replaces arm-block test with fake-port armed send and cancellation tests.
- Modify `docs/STATUS.md` and `docs/FUTURE_ANALOG_FOUR_EXPANSION.md`
  - Records software readiness for the A4 armed runtime path.

---

### Task 1: Hardware Sender Module

**Files:**
- Create: `rytm_randomizer/analog_four/hardware_runtime_sender.py`
- Test: `tests/test_analog_four_hardware_runtime_sender.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_analog_four_hardware_runtime_sender.py`:

```python
import subprocess
import sys
from pathlib import Path

import pytest
from conftest import _FakeMessage

pytestmark = pytest.mark.fast

PROJECT_ROOT = Path(__file__).resolve().parents[1]


class RecordingOut:
    def __init__(self):
        self.sent = []

    def send(self, message):
        self.sent.append(message)


def test_importing_a4_hardware_runtime_sender_is_passive_and_silent():
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import sys; "
                "import rytm_randomizer.analog_four.hardware_runtime_sender; "
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


def test_a4_hardware_runtime_refuses_without_arming_or_confirmation(monkeypatch):
    from rytm_randomizer.analog_four.hardware_runtime_sender import (
        execute_analog_four_runtime_hardware_send,
    )
    from rytm_randomizer.analog_four.runtime_plan import build_analog_four_runtime_plan
    import rytm_randomizer.midi_io as midi_io

    monkeypatch.setattr(midi_io, "mido", type("Mido", (), {"Message": _FakeMessage}))
    plan = build_analog_four_runtime_plan(profile="balanced")
    out = RecordingOut()

    missing_arm = execute_analog_four_runtime_hardware_send(
        plan,
        out,
        port_name="Fake A4",
        armed=False,
        operator_confirmed=True,
        sleep=lambda _seconds: None,
    )
    assert missing_arm.accepted is False
    assert missing_arm.reason == "missing_arming"
    assert missing_arm.emitted_message_count == 0
    assert out.sent == []

    missing_confirmation = execute_analog_four_runtime_hardware_send(
        plan,
        out,
        port_name="Fake A4",
        armed=True,
        operator_confirmed=False,
        sleep=lambda _seconds: None,
    )
    assert missing_confirmation.accepted is False
    assert missing_confirmation.reason == "missing_operator_confirmation"
    assert missing_confirmation.emitted_message_count == 0
    assert out.sent == []


def test_a4_hardware_runtime_sends_balanced_plan_to_fake_port(monkeypatch):
    from rytm_randomizer.analog_four.hardware_runtime_sender import (
        execute_analog_four_runtime_hardware_send,
    )
    from rytm_randomizer.analog_four.runtime_plan import build_analog_four_runtime_plan
    import rytm_randomizer.midi_io as midi_io

    monkeypatch.setattr(midi_io, "mido", type("Mido", (), {"Message": _FakeMessage}))
    plan = build_analog_four_runtime_plan(profile="balanced")
    out = RecordingOut()

    result = execute_analog_four_runtime_hardware_send(
        plan,
        out,
        port_name="Fake A4",
        armed=True,
        operator_confirmed=True,
        sleep=lambda _seconds: None,
    )

    assert result.accepted is True
    assert result.reason == "accepted_hardware_send"
    assert result.device == "Elektron Analog Four MKII"
    assert result.port_name == "Fake A4"
    assert result.starter_profile_key == "balanced"
    assert result.emitted_message_count == 20
    assert result.sends_real_midi is True
    assert result.mock_only is False
    assert len(out.sent) == 20
    assert out.sent[0].type == "control_change"
    assert out.sent[0].channel == 0
    assert out.sent[0].control == 95
    assert out.sent[0].value == 104
    assert out.sent[-1].channel == 3


def test_a4_hardware_runtime_preserves_birmingham_dark_values(monkeypatch):
    from rytm_randomizer.analog_four.hardware_runtime_sender import (
        execute_analog_four_runtime_hardware_send,
    )
    from rytm_randomizer.analog_four.runtime_plan import build_analog_four_runtime_plan
    import rytm_randomizer.midi_io as midi_io

    monkeypatch.setattr(midi_io, "mido", type("Mido", (), {"Message": _FakeMessage}))
    plan = build_analog_four_runtime_plan(profile="birmingham-dark")
    out = RecordingOut()

    result = execute_analog_four_runtime_hardware_send(
        plan,
        out,
        port_name="Fake A4",
        armed=True,
        operator_confirmed=True,
        sleep=lambda _seconds: None,
    )

    assert result.emitted_messages[0].track == 1
    assert result.emitted_messages[0].control == 95
    assert result.emitted_messages[0].value == 106
    assert result.emitted_messages[0].role == "dark bass pressure"
    assert out.sent[0].control == 95
    assert out.sent[0].value == 106


def test_format_a4_hardware_runtime_report_shows_active_policy(monkeypatch):
    from rytm_randomizer.analog_four.hardware_runtime_sender import (
        execute_analog_four_runtime_hardware_send,
        format_analog_four_runtime_hardware_send_report,
    )
    from rytm_randomizer.analog_four.runtime_plan import build_analog_four_runtime_plan
    import rytm_randomizer.midi_io as midi_io

    monkeypatch.setattr(midi_io, "mido", type("Mido", (), {"Message": _FakeMessage}))
    result = execute_analog_four_runtime_hardware_send(
        build_analog_four_runtime_plan(profile="detroit-classic"),
        RecordingOut(),
        port_name="Fake A4",
        armed=True,
        operator_confirmed=True,
        sleep=lambda _seconds: None,
    )
    report = format_analog_four_runtime_hardware_send_report(result)

    assert report[0] == "RytmRandomizer armed Analog Four Runtime Hardware Send Report"
    assert "Device: Elektron Analog Four MKII" in report
    assert "Starter profile: Detroit Classic / detroit-classic" in report
    assert "Accepted: True" in report
    assert "Reason: accepted_hardware_send" in report
    assert "Port: Fake A4" in report
    assert "Emitted real MIDI messages: 20" in report
    assert "- Track 1 ch 1 wire 0 / Track Level CC95 -> 100" in report
    assert "- A4-only runtime hardware send" in report
    assert "- requires exact SEND confirmation" in report
    assert "- no Rytm MIDI sending" in report
    assert "- no SysEx writes" in report
```

- [ ] **Step 2: Run tests to verify RED**

Run:

```powershell
python -m pytest tests/test_analog_four_hardware_runtime_sender.py -q -n 0
```

Expected: fails because `rytm_randomizer.analog_four.hardware_runtime_sender` does not exist.

- [ ] **Step 3: Implement hardware sender module**

Create `rytm_randomizer/analog_four/hardware_runtime_sender.py` with:

```python
"""Guarded real-MIDI sender for Analog Four runtime plans."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any

from ..midi_io import send_cc
from .runtime_plan import AnalogFourRuntimeEvent, AnalogFourRuntimePlan

HARDWARE_SEND_NAME = "analog_four_runtime_hardware_send"


def _freeze_metadata(metadata: Mapping[str, object] | None) -> Mapping[str, object]:
    if metadata is None:
        return MappingProxyType({})
    return MappingProxyType(dict(metadata))


@dataclass(frozen=True)
class AnalogFourRuntimeHardwareEmission:
    track: int
    midi_channel: int
    channel: int
    control: int
    value: int
    parameter_name: str
    role: str


@dataclass(frozen=True)
class AnalogFourRuntimeHardwareSendResult:
    device: str
    accepted: bool
    reason: str
    plan_ready: bool
    port_name: str
    starter_profile_key: str
    starter_profile_label: str
    eligible_message_count: int
    blocked_event_count: int
    emitted_messages: tuple[AnalogFourRuntimeHardwareEmission, ...]
    mock_only: bool = False
    sends_real_midi: bool = True
    metadata: Mapping[str, object] = field(default_factory=lambda: MappingProxyType({}))

    def __post_init__(self) -> None:
        object.__setattr__(self, "emitted_messages", tuple(self.emitted_messages))
        object.__setattr__(self, "metadata", _freeze_metadata(self.metadata))

    @property
    def emitted_message_count(self) -> int:
        return len(self.emitted_messages)


def execute_analog_four_runtime_hardware_send(
    plan: AnalogFourRuntimePlan,
    out: Any,
    *,
    port_name: str,
    armed: bool,
    operator_confirmed: bool,
    sleep: Callable[[float], Any],
) -> AnalogFourRuntimeHardwareSendResult:
    if not isinstance(plan, AnalogFourRuntimePlan):
        raise TypeError("plan must be an AnalogFourRuntimePlan")
    if not hasattr(out, "send"):
        raise TypeError("out must expose a send(message) method")

    events = tuple(event for track in plan.tracks for event in track.events)
    if not armed:
        return build_analog_four_runtime_hardware_send_refusal(
            plan,
            "missing_arming",
            port_name=port_name,
        )
    if not operator_confirmed:
        return build_analog_four_runtime_hardware_send_refusal(
            plan,
            "missing_operator_confirmation",
            port_name=port_name,
        )

    emitted = tuple(_send_event(event, out, sleep=sleep) for event in events)
    return AnalogFourRuntimeHardwareSendResult(
        device=plan.device,
        accepted=True,
        reason="accepted_hardware_send",
        plan_ready=True,
        port_name=port_name,
        starter_profile_key=plan.starter_profile_key,
        starter_profile_label=plan.starter_profile_label,
        eligible_message_count=len(events),
        blocked_event_count=0,
        emitted_messages=emitted,
        metadata=_result_metadata(plan, "accepted_hardware_send", port_name, len(events), 0),
    )


def build_analog_four_runtime_hardware_send_refusal(
    plan: AnalogFourRuntimePlan,
    reason: str,
    *,
    port_name: str = "<not-opened>",
) -> AnalogFourRuntimeHardwareSendResult:
    if not isinstance(plan, AnalogFourRuntimePlan):
        raise TypeError("plan must be an AnalogFourRuntimePlan")
    eligible_message_count = sum(len(track.events) for track in plan.tracks)
    return AnalogFourRuntimeHardwareSendResult(
        device=plan.device,
        accepted=False,
        reason=reason,
        plan_ready=True,
        port_name=port_name,
        starter_profile_key=plan.starter_profile_key,
        starter_profile_label=plan.starter_profile_label,
        eligible_message_count=eligible_message_count,
        blocked_event_count=0,
        emitted_messages=(),
        metadata=_result_metadata(plan, reason, port_name, eligible_message_count, 0),
    )


def format_analog_four_runtime_hardware_send_report(
    result: AnalogFourRuntimeHardwareSendResult,
) -> list[str]:
    lines = [
        "RytmRandomizer armed Analog Four Runtime Hardware Send Report",
        f"Device: {result.device}",
        f"Starter profile: {result.starter_profile_label} / {result.starter_profile_key}",
        f"Accepted: {result.accepted}",
        f"Reason: {result.reason}",
        f"Plan ready: {result.plan_ready}",
        f"Port: {result.port_name}",
        f"Eligible mapped CC messages: {result.eligible_message_count}",
        f"Blocked candidate events: {result.blocked_event_count}",
        f"Emitted real MIDI messages: {result.emitted_message_count}",
        "Hardware emission preview:",
    ]
    if result.emitted_messages:
        lines.extend(_format_emission_line(message) for message in result.emitted_messages)
    else:
        lines.append("- no messages emitted")
    lines.extend(
        [
            "Guard policy:",
            "- A4-only runtime hardware send",
            "- requires --arm",
            "- requires exact SEND confirmation",
            "- opens one selected Analog Four output only",
            "- real MIDI sending happened only after --arm and SEND confirmation",
            "- blocked plans emit no partial messages",
            "Safety:",
            "- active guarded sender",
            "- no Rytm MIDI sending",
            "- no SysEx writes",
            "- no live SysEx receive",
            "- no NRPN sending",
            "- no CV track mutation",
            "- no command execution",
        ]
    )
    return lines


def format_analog_four_runtime_hardware_send_error(message: str) -> list[str]:
    return [
        "RytmRandomizer armed Analog Four Runtime Hardware Send Report",
        "Found: False",
        f"Message: {message}. No MIDI was sent. No command executed.",
        "Safety:",
        "- active guarded sender",
        "- no MIDI sending",
        "- no MIDI receive",
        "- no port opening",
        "- no command execution",
        "- no hardware mutation",
        "- no live SysEx receive",
        "- no SysEx writes",
    ]


def _send_event(
    event: AnalogFourRuntimeEvent,
    out: Any,
    *,
    sleep: Callable[[float], Any],
) -> AnalogFourRuntimeHardwareEmission:
    send_cc(out, event.cc, event.value, channel=event.wire_channel, sleep=sleep)
    return AnalogFourRuntimeHardwareEmission(
        track=event.track,
        midi_channel=event.midi_channel,
        channel=event.wire_channel,
        control=event.cc,
        value=event.value,
        parameter_name=event.parameter_name,
        role=event.role_label,
    )


def _result_metadata(
    plan: AnalogFourRuntimePlan,
    reason: str,
    port_name: str,
    eligible_message_count: int,
    blocked_event_count: int,
) -> dict[str, object]:
    return {
        "guard": HARDWARE_SEND_NAME,
        "device": plan.device,
        "reason": reason,
        "port_name": port_name,
        "starter_profile_key": plan.starter_profile_key,
        "starter_profile_label": plan.starter_profile_label,
        "eligible_message_count": eligible_message_count,
        "blocked_event_count": blocked_event_count,
        "mock_only": False,
        "sends_real_midi": True,
    }


def _format_emission_line(message: AnalogFourRuntimeHardwareEmission) -> str:
    return (
        f"- Track {message.track} ch {message.midi_channel} wire {message.channel} / "
        f"{message.parameter_name} CC{message.control} -> {message.value}"
    )


__all__ = [
    "AnalogFourRuntimeHardwareEmission",
    "AnalogFourRuntimeHardwareSendResult",
    "HARDWARE_SEND_NAME",
    "build_analog_four_runtime_hardware_send_refusal",
    "execute_analog_four_runtime_hardware_send",
    "format_analog_four_runtime_hardware_send_error",
    "format_analog_four_runtime_hardware_send_report",
]
```

- [ ] **Step 4: Run tests to verify GREEN**

Run:

```powershell
python -m pytest tests/test_analog_four_hardware_runtime_sender.py -q -n 0
```

Expected: all module tests pass.

---

### Task 2: App Armed Runtime Wiring

**Files:**
- Modify: `rytm_randomizer/app.py`
- Modify: `tests/test_app_entry.py`

- [ ] **Step 1: Replace the arm-block test with armed fake-port tests**

In `tests/test_app_entry.py`, replace `test_app_main_arm_analog_four_runtime_is_blocked_for_now` with:

```python
def test_app_main_arm_analog_four_runtime_sends_to_selected_fake_port(monkeypatch, capsys):
    _seed()
    from rytm_randomizer import app, mido_provider

    fake_mido = types.ModuleType("mido")
    fake_mido.Message = _FakeMessage
    original_mido = sys.modules.get("mido")
    sys.modules["mido"] = fake_mido

    port = _RecordingPort()
    calls = {"list": 0, "open": []}
    real_list = mido_provider.MidoMidiPortProvider.list_output_names
    real_open = mido_provider.MidoMidiPortProvider.open_output

    def fake_list(self):
        calls["list"] += 1
        return ("Fake Rytm", "Fake A4")

    def fake_open(self, port_name):
        calls["open"].append(port_name)
        return port

    scripted_inputs = iter(["1", "SEND"])
    monkeypatch.setattr(app, "_smoke_sleep", lambda _seconds: None, raising=False)
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(scripted_inputs))
    mido_provider.MidoMidiPortProvider.list_output_names = fake_list
    mido_provider.MidoMidiPortProvider.open_output = fake_open
    try:
        exit_code = app.main(
            [
                "--arm",
                "--analog-four-runtime",
                "--analog-four-profile",
                "birmingham-dark",
            ]
        )
    finally:
        mido_provider.MidoMidiPortProvider.list_output_names = real_list
        mido_provider.MidoMidiPortProvider.open_output = real_open
        if original_mido is not None:
            sys.modules["mido"] = original_mido
        else:
            sys.modules.pop("mido", None)

    captured = capsys.readouterr()
    assert exit_code == 0
    assert calls["list"] == 1
    assert calls["open"] == ["Fake A4"]
    assert len(port.sent) == 20
    assert port.sent[0].type == "control_change"
    assert port.sent[0].channel == 0
    assert port.sent[0].control == 95
    assert port.sent[0].value == 106
    assert port.closed is True
    assert "Analog Four Runtime Hardware Send Report" in captured.out
    assert "Starter profile: Birmingham Dark / birmingham-dark" in captured.out
    assert "Accepted: True" in captured.out
    assert "Emitted real MIDI messages: 20" in captured.out
    assert "Type SEND to transmit 20 Analog Four runtime CC message(s)" in captured.out


def test_app_main_arm_analog_four_runtime_cancel_before_send_does_not_open_port(
    monkeypatch,
    capsys,
):
    _seed()
    from rytm_randomizer import app, mido_provider

    calls = {"list": 0, "open": []}
    real_list = mido_provider.MidoMidiPortProvider.list_output_names
    real_open = mido_provider.MidoMidiPortProvider.open_output

    def fake_list(self):
        calls["list"] += 1
        return ("Fake A4",)

    def fake_open(self, port_name):
        calls["open"].append(port_name)
        return _RecordingPort()

    scripted_inputs = iter(["0", "NOPE"])
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(scripted_inputs))
    mido_provider.MidoMidiPortProvider.list_output_names = fake_list
    mido_provider.MidoMidiPortProvider.open_output = fake_open
    try:
        exit_code = app.main(["--arm", "--analog-four-runtime"])
    finally:
        mido_provider.MidoMidiPortProvider.list_output_names = real_list
        mido_provider.MidoMidiPortProvider.open_output = real_open

    captured = capsys.readouterr()
    assert exit_code == 1
    assert calls["list"] == 1
    assert calls["open"] == []
    assert "--arm cancelled: exact SEND confirmation was not provided." in captured.err
```

- [ ] **Step 2: Run app tests to verify RED**

Run:

```powershell
python -m pytest tests/test_app_entry.py::test_app_main_arm_analog_four_runtime_sends_to_selected_fake_port tests/test_app_entry.py::test_app_main_arm_analog_four_runtime_cancel_before_send_does_not_open_port -q -n 0
```

Expected: fails because app still blocks `--arm --analog-four-runtime`.

- [ ] **Step 3: Implement app arm runner and confirmation**

In `rytm_randomizer/app.py`:

- Add `_run_arm_analog_four_runtime(request)` that:
  - builds the A4 runtime plan
  - lists output ports
  - prompts with `device_label="Analog Four"`
  - confirms via `_confirm_analog_four_runtime_send`
  - opens the selected port after confirmation
  - calls `execute_analog_four_runtime_hardware_send`
  - closes the port best-effort

- Add `_confirm_analog_four_runtime_send(plan, port_name)`:

```python
def _confirm_analog_four_runtime_send(plan, port_name: str) -> bool:
    sys.stdout.write(
        "\nType SEND to transmit "
        f"{plan.event_count} Analog Four runtime CC message(s) "
        f"({plan.starter_profile_label} / {plan.starter_profile_key}) "
        f"to Analog Four on {port_name}: "
    )
    try:
        raw = input().strip()
    except (EOFError, KeyboardInterrupt, OSError):
        sys.stderr.write("--arm cancelled: SEND confirmation was not provided.\n")
        return False
    if raw != "SEND":
        sys.stderr.write("--arm cancelled: exact SEND confirmation was not provided.\n")
        return False
    return True
```

- In `_run_arm(...)`, add `analog_four_runtime_request` parameter and dispatch it before generic provider/shell handling.
- In `main()`, remove the arm rejection for `args.analog_four_runtime`; keep requiring `--arm` or `--dry-run`.
- Pass `analog_four_runtime_request` into `_run_arm(...)`.

- [ ] **Step 4: Run app tests to verify GREEN**

Run:

```powershell
python -m pytest tests/test_app_entry.py::test_app_main_arm_analog_four_runtime_sends_to_selected_fake_port tests/test_app_entry.py::test_app_main_arm_analog_four_runtime_cancel_before_send_does_not_open_port -q -n 0
```

Expected: both tests pass.

---

### Task 3: Docs and Verification

**Files:**
- Modify: `docs/STATUS.md`
- Modify: `docs/FUTURE_ANALOG_FOUR_EXPANSION.md`

- [ ] **Step 1: Update docs**

Add a 2026-05-19 status bullet:

```markdown
- 2026-05-19: added the software-ready A4-only runtime hardware sender.
  `rytm-randomizer --arm --analog-four-runtime --analog-four-profile <profile>`
  now builds the A4 Track 1-4 runtime plan, asks for an Analog Four MIDI output,
  requires exact `SEND`, and then sends the same 20 mapped CC events validated
  by the guarded dry-run. Tests use fake ports; real hardware validation remains
  a separate operator step.
```

Update `docs/FUTURE_ANALOG_FOUR_EXPANSION.md` to say the armed path is
software-ready and hardware validation is next.

- [ ] **Step 2: Focused verification**

Run:

```powershell
python -m pytest tests/test_analog_four_hardware_runtime_sender.py tests/test_analog_four_guarded_runtime_sender.py tests/test_app_entry.py::test_app_main_arm_analog_four_runtime_sends_to_selected_fake_port tests/test_app_entry.py::test_app_main_arm_analog_four_runtime_cancel_before_send_does_not_open_port tests/test_app_entry.py::test_app_main_dry_run_analog_four_runtime_uses_guarded_mock_sender -q -n 0
```

Expected: all selected tests pass.

- [ ] **Step 3: Full verification**

Run:

```powershell
python -m pytest -m fast -q -n 0
python -m pytest -q -n 0
```

Expected: both suites pass with known skips only.

- [ ] **Step 4: Commit and push**

Run:

```powershell
git add rytm_randomizer/analog_four/hardware_runtime_sender.py rytm_randomizer/app.py tests/test_analog_four_hardware_runtime_sender.py tests/test_app_entry.py docs/STATUS.md docs/FUTURE_ANALOG_FOUR_EXPANSION.md
git commit -m "feat: add a4 runtime hardware sender"
git push origin codex/12-pad-rytm-engine-runtime-design
```

Expected: branch pushes cleanly.

---

## Self-Review

- Spec coverage: covers hardware sender module, app armed path, confirmation gate, fake-port tests, docs, and verification.
- Placeholder scan: no TBD/TODO placeholders.
- Type consistency: uses existing `AnalogFourRuntimePlan.event_count`, `starter_profile_key`, `starter_profile_label`, and `midi_io.send_cc`.
- Scope check: excludes dual-machine integration, Rytm sends, SysEx, NRPN, CV, GUI, audio analysis, and continuous tracking.
