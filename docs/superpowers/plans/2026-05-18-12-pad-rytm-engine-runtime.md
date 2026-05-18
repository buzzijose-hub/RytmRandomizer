# 12-Pad Rytm Engine Runtime Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the first passive/mock 12-pad Analog Rytm runtime contract from a style prompt.

**Architecture:** Reuse the existing style intent, machine catalog, engine-cycle, and starter-profile modules. Add one runtime-facing plan/report module that wraps the existing `RytmEngineCycleStarterPlan` into a clearer 12-pad runtime contract, then expose it through a passive CLI report. Do not add a new active hardware path in this slice; the existing guarded `--rytm-engine-cycle` path remains unchanged.

**Tech Stack:** Python 3.11+, pytest, ruff, isort, existing `MockMidiSender`, existing passive CLI patterns.

---

## File Structure

- Create `rytm_randomizer/essence/twelve_pad_rytm_runtime.py`
  - Owns `TwelvePadRytmRuntimePlan`, per-pad runtime plans, runtime events, source-starter coverage labels, mock capture, report formatting, and error formatting.
  - Builds from `build_rytm_engine_cycle_plan` and `build_rytm_engine_cycle_starter_plan`.
  - Defaults to `profile="auto"` and `include_engine_source_starters=True`.
- Create `tests/test_twelve_pad_rytm_runtime.py`
  - Covers import safety, plan counts, event ordering, mock capture, report output, and error output.
- Modify `rytm_randomizer/cli.py`
  - Adds passive `twelve-pad-rytm-runtime-report --style <text> [--discovery <0..1>] [--profile <profile>]`.
- Modify `rytm_randomizer/help_text.py`
  - Adds top-level usage/help text plus command-specific help.
- Modify `tests/test_cli.py`
  - Adds command help and usage coverage.
- Modify `tests/fixtures/cli_help_expected.txt`
  - Updates deterministic help fixture.
- Modify `docs/STATUS.md`
  - Records the passive 12-pad runtime foundation.

---

### Task 1: Passive Runtime Contract

**Files:**
- Create: `rytm_randomizer/essence/twelve_pad_rytm_runtime.py`
- Create: `tests/test_twelve_pad_rytm_runtime.py`

- [ ] **Step 1: Write the passive import test**

Create `tests/test_twelve_pad_rytm_runtime.py` with this opening content:

```python
import subprocess
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.fast

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_importing_twelve_pad_rytm_runtime_is_passive_and_silent():
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import sys; "
                "import rytm_randomizer.essence.twelve_pad_rytm_runtime; "
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
```

- [ ] **Step 2: Run the import test to verify it fails**

Run:

```powershell
python -m pytest tests/test_twelve_pad_rytm_runtime.py::test_importing_twelve_pad_rytm_runtime_is_passive_and_silent -q -n 0
```

Expected: FAIL with `ModuleNotFoundError: No module named 'rytm_randomizer.essence.twelve_pad_rytm_runtime'`.

- [ ] **Step 3: Add plan-count and event-order tests**

Append these tests to `tests/test_twelve_pad_rytm_runtime.py`:

```python
def test_build_twelve_pad_rytm_runtime_plan_uses_auto_profile_and_source_starters():
    from rytm_randomizer.essence.twelve_pad_rytm_runtime import (
        build_twelve_pad_rytm_runtime_plan,
    )

    plan = build_twelve_pad_rytm_runtime_plan(
        "Birmingham dark techno",
        discovery=0.35,
    )

    assert plan.style_prompt == "Birmingham dark techno"
    assert plan.discovery == 0.35
    assert plan.starter_profile_key == "birmingham-dark"
    assert plan.starter_profile_label == "Birmingham Dark"
    assert plan.pad_count == 12
    assert plan.event_count == 132
    assert plan.machine_select_event_count == 12
    assert plan.engine_source_event_count == 48
    assert plan.starter_parameter_event_count == 72
    assert plan.blocked_pad_count == 0
    assert plan.source_starter_covered_pad_count == 12
    assert plan.source_starter_skipped_pad_count == 0


def test_twelve_pad_rytm_runtime_plan_preserves_pad_event_order():
    from rytm_randomizer.essence.twelve_pad_rytm_runtime import (
        build_twelve_pad_rytm_runtime_plan,
    )

    plan = build_twelve_pad_rytm_runtime_plan(
        "Birmingham dark techno",
        discovery=0.35,
        profile="birmingham-dark",
    )

    pad5 = plan.pads[4]
    assert pad5.pad == 5
    assert pad5.role_label == "Closed hat pulse"
    assert pad5.machine_key == "ch_metallic"
    assert pad5.machine_label == "CH Metallic"
    assert pad5.source_starter_status == "covered"
    assert len(pad5.events) == 11
    assert [event.event_role for event in pad5.events[:6]] == [
        "machine_select",
        "engine_source_parameter",
        "engine_source_parameter",
        "engine_source_parameter",
        "engine_source_parameter",
        "starter_parameter",
    ]
    assert pad5.events[0].cc == 15
    assert pad5.events[0].value == 17
    assert pad5.events[1].parameter_name == "SRC Slot 1"
    assert pad5.events[1].cc == 16
    assert pad5.events[1].value == 100
    assert pad5.events[5].parameter_name == "FLT Frequency"
    assert pad5.events[5].cc == 74
    assert pad5.events[5].value == 108
```

- [ ] **Step 4: Run the new tests to verify they fail**

Run:

```powershell
python -m pytest tests/test_twelve_pad_rytm_runtime.py -q -n 0
```

Expected: FAIL because `build_twelve_pad_rytm_runtime_plan` is not defined yet.

- [ ] **Step 5: Add the runtime module implementation**

Create `rytm_randomizer/essence/twelve_pad_rytm_runtime.py` with this implementation:

```python
"""Passive 12-pad Analog Rytm runtime contract from style intent.

This module wraps the existing Rytm engine-cycle and starter-profile planners
into one runtime-facing mock plan. It does not import MIDI libraries, open
ports, send real MIDI, receive SysEx, write SysEx, or mutate hardware.
"""

from __future__ import annotations

from dataclasses import dataclass

from ..mock_midi import MockMidiSender, build_cc_message
from .rytm_engine_cycle_plan import build_rytm_engine_cycle_plan
from .rytm_engine_cycle_starter_profiles import (
    RytmEngineCycleStarterEvent,
    RytmEngineCycleStarterPlan,
    build_rytm_engine_cycle_starter_plan,
)


@dataclass(frozen=True)
class TwelvePadRytmRuntimeEvent:
    """One passive runtime CC event for a Rytm pad."""

    pad: int
    midi_channel: int
    wire_channel: int
    role_key: str
    role_label: str
    machine_key: str
    machine_label: str
    machine_value: int
    support_status: str
    event_role: str
    parameter_name: str
    cc: int
    value: int
    source: str
    sends_real_midi: bool = False


@dataclass(frozen=True)
class TwelvePadRytmRuntimePadPlan:
    """Runtime event plan for one Rytm pad."""

    pad: int
    midi_channel: int
    wire_channel: int
    role_key: str
    role_label: str
    machine_key: str
    machine_label: str
    machine_value: int
    support_status: str
    source_starter_status: str
    events: tuple[TwelvePadRytmRuntimeEvent, ...]


@dataclass(frozen=True)
class TwelvePadRytmRuntimePlan:
    """Passive 12-pad Rytm runtime plan from style intent."""

    style_prompt: str
    matched_profile_labels: tuple[str, ...]
    essence_tags: tuple[str, ...]
    discovery: float
    starter_profile_key: str
    starter_profile_label: str
    starter_profile_description: str
    include_engine_source_starters: bool
    pads: tuple[TwelvePadRytmRuntimePadPlan, ...]

    @property
    def pad_count(self) -> int:
        return len(self.pads)

    @property
    def blocked_pad_count(self) -> int:
        return 0

    @property
    def source_starter_covered_pad_count(self) -> int:
        return sum(1 for pad in self.pads if pad.source_starter_status == "covered")

    @property
    def source_starter_skipped_pad_count(self) -> int:
        return sum(1 for pad in self.pads if pad.source_starter_status != "covered")

    @property
    def event_count(self) -> int:
        return sum(len(pad.events) for pad in self.pads)

    @property
    def machine_select_event_count(self) -> int:
        return self._count_role("machine_select")

    @property
    def engine_source_event_count(self) -> int:
        return self._count_role("engine_source_parameter")

    @property
    def starter_parameter_event_count(self) -> int:
        return self._count_role("starter_parameter")

    def _count_role(self, event_role: str) -> int:
        return sum(
            1 for pad in self.pads for event in pad.events if event.event_role == event_role
        )


def build_twelve_pad_rytm_runtime_plan(
    style_prompt: str,
    *,
    discovery: float | None = None,
    profile: str | None = "auto",
    include_engine_source_starters: bool = True,
) -> TwelvePadRytmRuntimePlan:
    """Build a passive 12-pad Rytm runtime plan from style intent."""

    engine_plan = build_rytm_engine_cycle_plan(style_prompt, discovery=discovery)
    starter_plan = build_rytm_engine_cycle_starter_plan(
        engine_plan,
        profile=profile,
        include_engine_source_starters=include_engine_source_starters,
    )
    return _runtime_plan_from_starter_plan(
        starter_plan,
        include_engine_source_starters=include_engine_source_starters,
    )


def capture_twelve_pad_rytm_runtime_mock_messages(
    plan: TwelvePadRytmRuntimePlan,
) -> MockMidiSender:
    """Capture the runtime plan into an inert in-memory mock sender."""

    if not isinstance(plan, TwelvePadRytmRuntimePlan):
        raise TypeError("plan must be a TwelvePadRytmRuntimePlan")

    sender = MockMidiSender()
    for pad in plan.pads:
        for event in pad.events:
            sender.send(
                build_cc_message(
                    channel=event.wire_channel,
                    control=event.cc,
                    value=event.value,
                    metadata={
                        "source_kind": "twelve_pad_rytm_runtime",
                        "source": event.source,
                        "device": "Analog Rytm MKII",
                        "style_prompt": plan.style_prompt,
                        "discovery": plan.discovery,
                        "pad": event.pad,
                        "midi_channel": event.midi_channel,
                        "role_key": event.role_key,
                        "role_label": event.role_label,
                        "event_role": event.event_role,
                        "parameter": event.parameter_name,
                        "machine_key": event.machine_key,
                        "machine_label": event.machine_label,
                        "machine_value": event.machine_value,
                        "support_status": event.support_status,
                        "source_starter_status": pad.source_starter_status,
                        "starter_profile_key": plan.starter_profile_key,
                        "starter_profile_label": plan.starter_profile_label,
                        "mock_only": True,
                        "sends_real_midi": False,
                    },
                )
            )
    return sender


def format_twelve_pad_rytm_runtime_report(
    plan: TwelvePadRytmRuntimePlan,
    sender: MockMidiSender | None = None,
) -> list[str]:
    """Format a deterministic passive 12-pad Rytm runtime report."""

    if sender is None:
        sender = capture_twelve_pad_rytm_runtime_mock_messages(plan)

    lines = [
        "RytmRandomizer passive Twelve Pad Rytm Runtime Report",
        f"Style prompt: {plan.style_prompt}",
        f"Matched profiles: {_format_labels(plan.matched_profile_labels)}",
        f"Essence tags: {_format_labels(plan.essence_tags)}",
        f"Discovery: {plan.discovery:.2f}",
        f"Starter profile: {plan.starter_profile_label} / {plan.starter_profile_key}",
        f"Profile behavior: {plan.starter_profile_description}",
        f"Planned pads: {plan.pad_count}",
        f"Blocked pads: {plan.blocked_pad_count}",
        f"Machine-select messages: {plan.machine_select_event_count}",
        f"Engine-source parameter messages: {plan.engine_source_event_count}",
        f"Starter parameter messages: {plan.starter_parameter_event_count}",
        f"Runtime messages: {len(sender.sent_messages)}",
        f"Source-starter covered pads: {plan.source_starter_covered_pad_count}",
        f"Source-starter skipped pads: {plan.source_starter_skipped_pad_count}",
        "Pad runtime plans:",
    ]
    for pad in plan.pads:
        lines.append(
            f"- Pad {pad.pad} / {pad.role_label} / {pad.machine_label}: "
            f"{len(pad.events)} message(s), source starters {pad.source_starter_status}"
        )
    lines.append("Mock MIDI stream:")
    if sender.sent_messages:
        lines.extend(_format_message_preview(message) for message in sender.sent_messages)
    else:
        lines.append("- no mock messages")
    lines.extend(
        [
            "Runtime policy:",
            "- machine select first, source starters second, common starters third",
            "- engine-source starters are enabled by default for this runtime report",
            "- generic SRC Slot labels are used where official source names are pending",
            "- existing guarded and armed engine-cycle senders are unchanged",
            "Safety:",
            "- passive/read-only",
            "- mock sender only",
            "- no MIDI sending",
            "- no MIDI receive",
            "- no port opening",
            "- no command execution",
            "- no hardware mutation",
            "- no live SysEx receive",
            "- no SysEx writes",
            "- no hardware required",
        ]
    )
    return lines


def format_twelve_pad_rytm_runtime_error(message: str) -> list[str]:
    """Format deterministic passive 12-pad Rytm runtime errors."""

    return [
        "RytmRandomizer passive Twelve Pad Rytm Runtime Report",
        "Found: False",
        f"Message: {message}. No MIDI was sent. No command executed.",
        "Safety:",
        "- passive/read-only",
        "- mock sender only",
        "- no MIDI sending",
        "- no MIDI receive",
        "- no port opening",
        "- no command execution",
        "- no hardware mutation",
        "- no live SysEx receive",
        "- no SysEx writes",
        "- no hardware required",
    ]


def _runtime_plan_from_starter_plan(
    starter_plan: RytmEngineCycleStarterPlan,
    *,
    include_engine_source_starters: bool,
) -> TwelvePadRytmRuntimePlan:
    return TwelvePadRytmRuntimePlan(
        style_prompt=starter_plan.style_prompt,
        matched_profile_labels=starter_plan.matched_profile_labels,
        essence_tags=starter_plan.essence_tags,
        discovery=starter_plan.discovery,
        starter_profile_key=starter_plan.starter_profile_key,
        starter_profile_label=starter_plan.starter_profile_label,
        starter_profile_description=starter_plan.starter_profile_description,
        include_engine_source_starters=include_engine_source_starters,
        pads=tuple(
            _runtime_pad_from_starter_pad(
                pad,
                include_engine_source_starters=include_engine_source_starters,
            )
            for pad in starter_plan.pads
        ),
    )


def _runtime_pad_from_starter_pad(
    pad,
    *,
    include_engine_source_starters: bool,
) -> TwelvePadRytmRuntimePadPlan:
    return TwelvePadRytmRuntimePadPlan(
        pad=pad.pad,
        midi_channel=pad.midi_channel,
        wire_channel=pad.wire_channel,
        role_key=pad.role_key,
        role_label=pad.role_label,
        machine_key=pad.machine_key,
        machine_label=pad.machine_label,
        machine_value=pad.machine_value,
        support_status=pad.support_status,
        source_starter_status=_source_starter_status(
            pad,
            include_engine_source_starters=include_engine_source_starters,
        ),
        events=tuple(_runtime_event_from_starter_event(event) for event in pad.events),
    )


def _runtime_event_from_starter_event(
    event: RytmEngineCycleStarterEvent,
) -> TwelvePadRytmRuntimeEvent:
    return TwelvePadRytmRuntimeEvent(
        pad=event.pad,
        midi_channel=event.midi_channel,
        wire_channel=event.wire_channel,
        role_key=event.role_key,
        role_label=event.role_label,
        machine_key=event.machine_key,
        machine_label=event.machine_label,
        machine_value=event.machine_value,
        support_status=event.support_status,
        event_role=event.event_role,
        parameter_name=event.parameter_name,
        cc=event.cc,
        value=event.value,
        source=event.source,
    )


def _format_message_preview(message) -> str:
    metadata = message.metadata
    role = str(metadata["event_role"])
    if role == "machine_select":
        detail = f"CC{message.control} -> {message.value} / {metadata['machine_label']}"
    elif role in {"starter_parameter", "engine_source_parameter"}:
        detail = f"{metadata['parameter']} CC{message.control} -> {message.value}"
    else:
        detail = f"CC{message.control} -> {message.value}"
    return (
        f"- Pad {metadata['pad']} / ch {metadata['midi_channel']} "
        f"wire {message.channel} / {role} / {detail}"
    )


def _source_starter_status(
    pad,
    *,
    include_engine_source_starters: bool,
) -> str:
    if not include_engine_source_starters:
        return "disabled"
    if any(event.event_role == "engine_source_parameter" for event in pad.events):
        return "covered"
    return "not mapped"


def _format_labels(labels: tuple[str, ...]) -> str:
    return ", ".join(labels) if labels else "none"


__all__ = [
    "TwelvePadRytmRuntimeEvent",
    "TwelvePadRytmRuntimePadPlan",
    "TwelvePadRytmRuntimePlan",
    "build_twelve_pad_rytm_runtime_plan",
    "capture_twelve_pad_rytm_runtime_mock_messages",
    "format_twelve_pad_rytm_runtime_error",
    "format_twelve_pad_rytm_runtime_report",
]
```

- [ ] **Step 6: Run the runtime tests**

Run:

```powershell
python -m pytest tests/test_twelve_pad_rytm_runtime.py -q -n 0
```

Expected: PASS for the three tests added so far.

- [ ] **Step 7: Add mock capture, report, and error tests**

Append these tests to `tests/test_twelve_pad_rytm_runtime.py`:

```python
def test_twelve_pad_rytm_runtime_mock_capture_has_metadata_and_full_stream():
    from rytm_randomizer.essence.twelve_pad_rytm_runtime import (
        build_twelve_pad_rytm_runtime_plan,
        capture_twelve_pad_rytm_runtime_mock_messages,
    )

    plan = build_twelve_pad_rytm_runtime_plan("Birmingham dark techno", discovery=0.35)
    sender = capture_twelve_pad_rytm_runtime_mock_messages(plan)

    assert len(sender.sent_messages) == 132
    assert sender.sent_messages[0].control == 15
    assert sender.sent_messages[0].metadata["source_kind"] == "twelve_pad_rytm_runtime"
    assert sender.sent_messages[0].metadata["style_prompt"] == "Birmingham dark techno"
    assert sender.sent_messages[0].metadata["starter_profile_key"] == "birmingham-dark"
    assert sender.sent_messages[0].metadata["source_starter_status"] == "covered"
    assert sender.sent_messages[0].metadata["mock_only"] is True
    assert sender.sent_messages[0].metadata["sends_real_midi"] is False
    pad5_source = sender.sent_messages[45]
    assert pad5_source.metadata["pad"] == 5
    assert pad5_source.metadata["event_role"] == "engine_source_parameter"
    assert pad5_source.metadata["parameter"] == "SRC Slot 1"
    assert pad5_source.control == 16
    assert pad5_source.value == 100


def test_twelve_pad_rytm_runtime_report_explains_counts_stream_and_safety():
    from rytm_randomizer.essence.twelve_pad_rytm_runtime import (
        build_twelve_pad_rytm_runtime_plan,
        format_twelve_pad_rytm_runtime_report,
    )

    plan = build_twelve_pad_rytm_runtime_plan("Birmingham dark techno", discovery=0.35)
    report = "\n".join(format_twelve_pad_rytm_runtime_report(plan))

    assert "RytmRandomizer passive Twelve Pad Rytm Runtime Report" in report
    assert "Style prompt: Birmingham dark techno" in report
    assert "Starter profile: Birmingham Dark / birmingham-dark" in report
    assert "Planned pads: 12" in report
    assert "Blocked pads: 0" in report
    assert "Runtime messages: 132" in report
    assert "Source-starter covered pads: 12" in report
    assert "Source-starter skipped pads: 0" in report
    assert (
        "- Pad 5 / Closed hat pulse / CH Metallic: "
        "11 message(s), source starters covered"
    ) in report
    assert "- Pad 5 / ch 5 wire 4 / machine_select / CC15 -> 17 / CH Metallic" in report
    assert "- Pad 5 / ch 5 wire 4 / engine_source_parameter / SRC Slot 1 CC16 -> 100" in report
    assert "- Pad 5 / ch 5 wire 4 / starter_parameter / FLT Frequency CC74 -> 108" in report
    assert "- engine-source starters are enabled by default for this runtime report" in report
    assert "- no MIDI sending" in report
    assert "- no hardware mutation" in report


def test_twelve_pad_rytm_runtime_error_report_is_safe():
    from rytm_randomizer.essence.twelve_pad_rytm_runtime import (
        format_twelve_pad_rytm_runtime_error,
    )

    report = "\n".join(format_twelve_pad_rytm_runtime_error("bad style"))

    assert "RytmRandomizer passive Twelve Pad Rytm Runtime Report" in report
    assert "Found: False" in report
    assert "bad style. No MIDI was sent. No command executed." in report
    assert "- no MIDI sending" in report
```

- [ ] **Step 8: Run the complete runtime module tests**

Run:

```powershell
python -m pytest tests/test_twelve_pad_rytm_runtime.py -q -n 0
```

Expected: PASS.

- [ ] **Step 9: Run formatting and lint for the new module**

Run:

```powershell
python -m isort --profile black rytm_randomizer/essence/twelve_pad_rytm_runtime.py tests/test_twelve_pad_rytm_runtime.py
python -m ruff check rytm_randomizer/essence/twelve_pad_rytm_runtime.py tests/test_twelve_pad_rytm_runtime.py
```

Expected: both commands PASS.

- [ ] **Step 10: Commit the runtime contract**

Run:

```powershell
git add rytm_randomizer/essence/twelve_pad_rytm_runtime.py tests/test_twelve_pad_rytm_runtime.py
git commit -m "feat: add passive 12-pad rytm runtime plan"
```

---

### Task 2: Passive CLI Report

**Files:**
- Modify: `rytm_randomizer/cli.py`
- Modify: `rytm_randomizer/help_text.py`
- Modify: `tests/test_cli.py`
- Modify: `tests/fixtures/cli_help_expected.txt`
- Test: `tests/test_twelve_pad_rytm_runtime.py`

- [ ] **Step 1: Add CLI command tests**

Append these tests to `tests/test_twelve_pad_rytm_runtime.py`:

```python
def run_cli(*args):
    return subprocess.run(
        [sys.executable, "-m", "rytm_randomizer.cli", *args],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def test_twelve_pad_rytm_runtime_report_cli_accepts_style_discovery_and_profile():
    result = run_cli(
        "twelve-pad-rytm-runtime-report",
        "--style",
        "Birmingham dark techno",
        "--discovery",
        "0.35",
        "--profile",
        "auto",
    )

    assert result.returncode == 0
    assert "RytmRandomizer passive Twelve Pad Rytm Runtime Report" in result.stdout
    assert "Style prompt: Birmingham dark techno" in result.stdout
    assert "Starter profile: Birmingham Dark / birmingham-dark" in result.stdout
    assert "Runtime messages: 132" in result.stdout
    assert "engine_source_parameter / SRC Slot 1 CC16 -> 100" in result.stdout
    assert "- no MIDI sending" in result.stdout
    assert result.stderr == ""


def test_twelve_pad_rytm_runtime_report_cli_rejects_invalid_discovery():
    result = run_cli(
        "twelve-pad-rytm-runtime-report",
        "--style",
        "Birmingham dark techno",
        "--discovery",
        "2",
    )

    assert result.returncode == 1
    assert "RytmRandomizer passive Twelve Pad Rytm Runtime Report" in result.stderr
    assert "Discovery must be between 0.0 and 1.0" in result.stderr
    assert "No MIDI was sent" in result.stderr
    assert result.stdout == ""
```

- [ ] **Step 2: Add command help test**

Append this test to `tests/test_cli.py` near the other help tests:

```python
def test_twelve_pad_rytm_runtime_report_help_exits_zero():
    result = run_cli("twelve-pad-rytm-runtime-report", "--help")

    assert result.returncode == 0
    assert "RytmRandomizer passive CLI: twelve-pad-rytm-runtime-report" in result.stdout
    assert "Usage:" in result.stdout
    assert result.stderr == ""
```

- [ ] **Step 3: Run CLI tests to verify they fail**

Run:

```powershell
python -m pytest tests/test_twelve_pad_rytm_runtime.py tests/test_cli.py::test_twelve_pad_rytm_runtime_report_help_exits_zero -q -n 0
```

Expected: FAIL because `twelve-pad-rytm-runtime-report` is not wired into CLI/help yet.

- [ ] **Step 4: Wire the command in `cli.py`**

In `rytm_randomizer/cli.py`, insert this command block after the existing
`twelve-pad-mock-runtime-report` block and before `analog-four-reference-report`:

```python
    if args and args[0] == "twelve-pad-rytm-runtime-report":
        from .essence.plan_report import parse_discovery_value
        from .essence.twelve_pad_rytm_runtime import (
            build_twelve_pad_rytm_runtime_plan,
            format_twelve_pad_rytm_runtime_error,
            format_twelve_pad_rytm_runtime_report,
        )

        if len(args) < 3 or args[1] != "--style" or len(args[3:]) % 2 != 0:
            sys.stderr.write(f"{USAGE}\n")
            return 2

        try:
            discovery = None
            profile = "auto"
            index = 3
            while index < len(args):
                flag = args[index]
                value = args[index + 1]
                if flag == "--discovery":
                    discovery = parse_discovery_value(value)
                elif flag == "--profile":
                    profile = value
                else:
                    sys.stderr.write(f"{USAGE}\n")
                    return 2
                index += 2
            plan = build_twelve_pad_rytm_runtime_plan(
                args[2],
                discovery=discovery,
                profile=profile,
            )
        except ValueError as exc:
            lines = format_twelve_pad_rytm_runtime_error(str(exc))
            sys.stderr.write("\n".join(lines))
            sys.stderr.write("\n")
            return 1

        sys.stdout.write("\n".join(format_twelve_pad_rytm_runtime_report(plan)))
        sys.stdout.write("\n")
        return 0
```

- [ ] **Step 5: Update top-level help text**

In `rytm_randomizer/help_text.py`:

1. Add this usage alternative in `USAGE` after `twelve-pad-mock-runtime-report`:

```text
twelve-pad-rytm-runtime-report --style <text> [--discovery <0..1>] [--profile <profile>] |
```

2. Add these examples in `HELP_TEXT` near the other runtime reports:

```text
  python -m rytm_randomizer.cli twelve-pad-rytm-runtime-report --style <text>
  python -m rytm_randomizer.cli twelve-pad-rytm-runtime-report --style <text> --discovery <0..1>
  python -m rytm_randomizer.cli twelve-pad-rytm-runtime-report --style <text> --profile <profile>
```

3. Add this command label in the command list:

```text
  twelve-pad-rytm-runtime-report
                     Preview the passive style-driven 12-pad Rytm runtime stream.
```

4. Add this entry to `COMMAND_HELP`:

```python
    "twelve-pad-rytm-runtime-report": """RytmRandomizer passive CLI: twelve-pad-rytm-runtime-report

Usage:
  python -m rytm_randomizer.cli twelve-pad-rytm-runtime-report --style <text>
  python -m rytm_randomizer.cli twelve-pad-rytm-runtime-report --style <text> --discovery <0..1>
  python -m rytm_randomizer.cli twelve-pad-rytm-runtime-report --style <text> --profile <profile>
  python -m rytm_randomizer.cli twelve-pad-rytm-runtime-report --help

Behavior:
  Builds a passive/mock 12-pad Analog Rytm runtime stream from style intent.
  The stream includes machine selects, engine-source starters, and common
  filter/amp starter values. No MIDI is sent and no port is opened.
""",
```

- [ ] **Step 6: Update deterministic help fixture and usage test string**

In `tests/test_cli.py`, update the local `USAGE` string to include:

```text
twelve-pad-rytm-runtime-report --style <text> [--discovery <0..1>] [--profile <profile>] |
```

In `tests/fixtures/cli_help_expected.txt`, mirror the same examples and command list entry added to `HELP_TEXT`.

- [ ] **Step 7: Run CLI/report tests**

Run:

```powershell
python -m pytest tests/test_twelve_pad_rytm_runtime.py tests/test_cli.py::test_twelve_pad_rytm_runtime_report_help_exits_zero tests/test_cli.py::test_top_level_help_exits_zero_and_matches_fixture -q -n 0
```

Expected: PASS.

- [ ] **Step 8: Run formatting and lint for CLI/help files**

Run:

```powershell
python -m isort --profile black rytm_randomizer/cli.py rytm_randomizer/help_text.py tests/test_cli.py tests/test_twelve_pad_rytm_runtime.py
python -m ruff check rytm_randomizer/cli.py rytm_randomizer/help_text.py tests/test_cli.py tests/test_twelve_pad_rytm_runtime.py
```

Expected: both commands PASS.

- [ ] **Step 9: Commit the passive CLI report**

Run:

```powershell
git add rytm_randomizer/cli.py rytm_randomizer/help_text.py tests/test_cli.py tests/fixtures/cli_help_expected.txt tests/test_twelve_pad_rytm_runtime.py
git commit -m "feat: expose 12-pad rytm runtime report"
```

---

### Task 3: Status Documentation And Branch Verification

**Files:**
- Modify: `docs/STATUS.md`
- Test: architecture and fast test suite

- [ ] **Step 1: Update project status**

Add this bullet at the top of `docs/STATUS.md` under `## Recent Cleanup`:

```markdown
- 2026-05-18: added the passive 12-pad Rytm runtime foundation.
  `twelve-pad-rytm-runtime-report --style <text>` builds a mock-only setup
  stream with machine selects, engine-source starter values, and common
  filter/amp starter values across all 12 Analog Rytm pads. The existing
  guarded `--rytm-engine-cycle` dry-run/arm path remains unchanged. No live
  snapshot capture, audio analysis, Analog Four mutation, SysEx writes, or
  unguarded hardware sending was added.
```

- [ ] **Step 2: Run stale-reference and top-level module checks**

Run:

```powershell
rg -n "twelve_pad_rytm_runtime" rytm_randomizer tests docs
python -m pytest tests/architecture/test_no_new_top_level_modules.py tests/architecture/test_import_direction.py tests/architecture/test_no_side_effects.py -q -n 0
```

Expected:

- `rg` shows only the new module, tests, help, and docs.
- Architecture tests PASS.

- [ ] **Step 3: Run focused runtime verification**

Run:

```powershell
python -m pytest tests/test_twelve_pad_rytm_runtime.py tests/test_rytm_engine_cycle_starter_profiles.py tests/test_rytm_engine_cycle_guarded_sender.py tests/test_rytm_engine_cycle_hardware_sender.py tests/test_app_entry.py::test_app_main_dry_run_rytm_engine_cycle_source_starters -q -n 0
```

Expected: PASS.

- [ ] **Step 4: Run full maintained-code checks**

Run:

```powershell
python -m pytest tests/architecture -q -n 0
python -m pytest -m fast -q -n 0
python -m ruff check .
python -m isort --check-only --profile black rytm_randomizer tests
git diff --check
```

Expected:

- architecture suite PASS;
- fast suite PASS;
- ruff PASS;
- isort PASS;
- diff check PASS.

- [ ] **Step 5: Commit documentation**

Run:

```powershell
git add docs/STATUS.md
git commit -m "docs: record 12-pad rytm runtime foundation"
```

- [ ] **Step 6: Push the branch**

Run:

```powershell
git status --short --branch
git push origin codex/12-pad-rytm-engine-runtime-design
```

Expected: branch pushes cleanly. If PR #36 has not merged yet, keep this as a stacked branch and do not open it as ready for merge.

---

## Implementation Notes

- This slice creates a clearer passive runtime contract. It does not replace the existing guarded `--rytm-engine-cycle` dry-run/arm path.
- The default `profile="auto"` makes style prompts choose the starter profile automatically.
- The default `include_engine_source_starters=True` makes the runtime report show the complete 132-message setup stream for the validated styles covered by the current starter data.
- If future machine selections lack source starter coverage, the existing starter planner simply emits no source starter events for that machine. The runtime report counts what was emitted and labels each pad as `covered`, `disabled`, or `not mapped` rather than assuming every pad has source events.
- Hardware testing is not required for this plan. The existing engine-cycle hardware sender tests continue to prove the guarded active path.
