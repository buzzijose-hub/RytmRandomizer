# Post-158 OXI/A4 Readiness Implementation Plan

Status: in-flight

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Prepare the next clean-base bundle after PR #158 by turning the Rytm OXI live strategy and Analog Four passive macro runway into concrete readiness, validation, and cockpit handoff surfaces without adding unattended hardware behavior.

**Architecture:** Keep Rytm active sends inside `rytm_randomizer/engines/analog_rytm_snapshot_shell.py` and its injected sender boundary. Keep Analog Four promotion staged through passive reports and explicit operator-present `--arm` validation commands before any full A4 macro SEND path exists. Reuse `devices/`, `data/`, `reports/`, `cli_registry.py`, and the existing cockpit protocol models; do not create parallel top-level device packages.

**Tech Stack:** Python 3.11, frozen dataclasses, existing A4 manual-backed CC facts, existing Rytm snapshot macro facts, passive CLI reports, pytest, ruff, black, isort, GitHub PR gates.

---

## Merge Gate

This plan is local preparation only while PR #158 is blocked by review.

- Do not open this as a second PR while #158 is unresolved.
- Base implementation work on `origin/modularize-v1.34` after #158 either merges or is explicitly superseded.
- If #158 merges, fold its `oxi-live-set-strategy-report` output into this bundle as an input surface.
- If #158 receives new actionable review feedback, address #158 first and return here afterward.

## Product Target

The live rig direction stays:

- OXI handles notes, triggers, mutes, pattern motion, and human performance timing.
- RytmRandomizer rides sound design as a second performer.
- Rytm `kit/resnapshot` captures the current kit as the anchor.
- Rytm `kit-core`, `hard-groove`, `industrial`, `dub-pressure`, and `transition` stage safe variations.
- Rytm `send` and `go` remain explicit operator actions.
- Rytm `home` or `Z` plus `send` returns to the captured anchor.
- Analog Four remains passive or operator-present until readiness evidence proves each macro row.

## File Structure

- Create `rytm_randomizer/reports/analog_four_oxi_macro_readiness.py`
  - Builds readiness cards from `analog-four-oxi-macro-report` events.
  - Classifies every event as `cc-ready`, `nrpn-required`, `manual-review`, or `blocked`.
  - Emits hardware validation commands for one-row operator tests.
  - Sends no MIDI and opens no ports.
- Keep `rytm_randomizer/reports/__init__.py` unchanged for this report
  - The PR #158 factory migration brought this legacy facade below the
    comprehensibility cap; the readiness report lives in its focused module and
    is loaded lazily through `cli.py`.
- Modify `rytm_randomizer/cli.py`
  - Import the readiness command in the passive command registry list.
- Modify `rytm_randomizer/help_text.py`
  - Add help text for `analog-four-oxi-macro-readiness-report`.
- Create `tests/test_analog_four_oxi_macro_readiness.py`
  - Covers deterministic readiness, safety flags, JSON, parser behavior, and CLI output.
- Modify `tests/test_real_midi_passive_cli_safety.py`
  - Add the new passive command to the no-real-MIDI safety matrix.
- Modify `rytm_randomizer/reports/live_gui_performance_flow_model.py`
  - Add A4 readiness summary fields that the cockpit can show before active A4 promotion.
- Modify `desktop/web/src/types/live_gui_protocol.ts`
  - Mirror the new readiness fields in the TypeScript contract.
- Modify `desktop/web/src/cockpit/LiveReadinessPanel.tsx`
  - Render the A4 readiness summary as review-only state.
- Modify `tests/test_live_gui_performance_flow_model.py`
  - Pin the Python report output.
- Modify `desktop/web/tests/cockpit/LiveReadinessPanel.test.tsx`
  - Pin the cockpit rendering of the readiness state.
- Modify `README.md`
  - Document the readiness report and the next manual A4 validation path.
- Modify `docs/STATUS.md`
  - Update the hand-authored current status in place after implementation.

## Task 1: Add Passive A4 Macro Readiness Tests

**Files:**
- Create: `tests/test_analog_four_oxi_macro_readiness.py`
- Create: `rytm_randomizer/reports/analog_four_oxi_macro_readiness.py`

- [x] **Step 1: Write the failing report model test**

Add this test:

```python
def test_a4_macro_readiness_defaults_to_passive_cc_ready_rows() -> None:
    from rytm_randomizer.reports.analog_four_oxi_macro_readiness import (
        build_analog_four_oxi_macro_readiness_report,
    )

    report = build_analog_four_oxi_macro_readiness_report(
        "hard-groove",
        seed=7,
        intensity=4,
    )

    assert report.title == "RytmRandomizer passive Analog Four OXI macro readiness"
    assert report.macro_name == "hard-groove"
    assert report.readiness == "review-ready"
    assert report.opens_ports is False
    assert report.sends_midi is False
    assert report.hardware_required is False
    assert report.operator_present_required is True
    assert report.ready_count == len(report.events)
    assert report.blocked_count == 0
    assert {event.status for event in report.events} == {"cc-ready"}
    assert all(event.validation_command.startswith("python -m rytm_randomizer.app --arm --a4-send-param") for event in report.events)
```

- [x] **Step 2: Run the test to verify it fails**

Run:

```powershell
python -m pytest tests\test_analog_four_oxi_macro_readiness.py::test_a4_macro_readiness_defaults_to_passive_cc_ready_rows -n 0
```

Expected: fail with `ModuleNotFoundError` because the report module does not exist yet.

- [x] **Step 3: Add the readiness dataclasses and builder**

Create `rytm_randomizer/reports/analog_four_oxi_macro_readiness.py` with:

```python
"""Passive readiness report for promoting A4 OXI macros toward hardware tests."""

from __future__ import annotations

import json
import shlex
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Final, Literal

from ..cli_registry import CliCommand, register
from .analog_four_oxi_macro_report import (
    DEFAULT_ANALOG_FOUR_OXI_MACRO,
    AnalogFourOxiMacroEvent,
    AnalogFourOxiMacroReport,
    build_analog_four_oxi_macro_report,
)
from .formatter import SAFETY_SECTION_HEADER, PassiveReportHeader, passive_report_lines

ReadinessStatus = Literal["cc-ready", "nrpn-required", "manual-review", "blocked"]
ReportReadiness = Literal["review-ready", "needs-review", "blocked"]

REPORT_TITLE: Final[str] = "RytmRandomizer passive Analog Four OXI macro readiness"
SOURCE_MODULE: Final[str] = "reports.analog_four_oxi_macro_readiness"
SAFETY_LINES: Final[tuple[str, ...]] = (
    "passive/read-only",
    "no MIDI sending",
    "no port opening",
    "operator-present validation commands only",
    "A4 full macro SEND remains unimplemented",
)
_HEADER: Final[PassiveReportHeader] = PassiveReportHeader(
    title=REPORT_TITLE,
    source_module=SOURCE_MODULE,
)
_USAGE: Final[str] = (
    "analog-four-oxi-macro-readiness-report usage: "
    "[<macro-name>] [--seed N] [--intensity N] [--limit N] [--json]"
)


@dataclass(frozen=True)
class AnalogFourOxiMacroReadinessEvent:
    """One A4 macro event with promotion status and a one-row validation command."""

    track: int
    role: str
    lane: str
    parameter: str
    channel: int
    control: int
    value: int
    status: ReadinessStatus
    validation_command: str
    reason: str


@dataclass(frozen=True)
class AnalogFourOxiMacroReadinessReport:
    """Passive readiness report for one deterministic A4 macro preview."""

    title: str
    macro_name: str
    seed: int
    intensity: int
    readiness: ReportReadiness
    event_count: int
    ready_count: int
    review_count: int
    blocked_count: int
    events: tuple[AnalogFourOxiMacroReadinessEvent, ...]
    opens_ports: bool
    sends_midi: bool
    hardware_required: bool
    operator_present_required: bool


def _validation_command(event: AnalogFourOxiMacroEvent) -> str:
    parameter = shlex.quote(event.parameter)
    return (
        "python -m rytm_randomizer.app --arm --a4-send-param "
        f"--parameter {parameter} --channel {event.channel} --value {event.value}"
    )


def _readiness_event(event: AnalogFourOxiMacroEvent) -> AnalogFourOxiMacroReadinessEvent:
    return AnalogFourOxiMacroReadinessEvent(
        track=event.track,
        role=event.role,
        lane=event.lane,
        parameter=event.parameter,
        channel=event.channel,
        control=event.control,
        value=event.value,
        status="cc-ready",
        validation_command=_validation_command(event),
        reason="manual-backed CC MSB row is available through --a4-send-param",
    )


def _report_readiness(events: Sequence[AnalogFourOxiMacroReadinessEvent]) -> ReportReadiness:
    if any(event.status == "blocked" for event in events):
        return "blocked"
    if any(event.status != "cc-ready" for event in events):
        return "needs-review"
    return "review-ready"


def build_analog_four_oxi_macro_readiness_report(
    macro_name: str = DEFAULT_ANALOG_FOUR_OXI_MACRO,
    *,
    seed: int = 0,
    intensity: int = 4,
) -> AnalogFourOxiMacroReadinessReport:
    """Build a deterministic passive A4 macro readiness report."""

    macro_report: AnalogFourOxiMacroReport = build_analog_four_oxi_macro_report(
        macro_name,
        seed=seed,
        intensity=intensity,
    )
    events = tuple(_readiness_event(event) for event in macro_report.events)
    review_count = sum(1 for event in events if event.status == "manual-review")
    blocked_count = sum(1 for event in events if event.status == "blocked")
    ready_count = sum(1 for event in events if event.status == "cc-ready")
    return AnalogFourOxiMacroReadinessReport(
        title=REPORT_TITLE,
        macro_name=macro_report.macro_name,
        seed=macro_report.seed,
        intensity=macro_report.intensity,
        readiness=_report_readiness(events),
        event_count=len(events),
        ready_count=ready_count,
        review_count=review_count,
        blocked_count=blocked_count,
        events=events,
        opens_ports=False,
        sends_midi=False,
        hardware_required=False,
        operator_present_required=True,
    )
```

- [x] **Step 4: Run the focused test**

Run:

```powershell
python -m pytest tests\test_analog_four_oxi_macro_readiness.py::test_a4_macro_readiness_defaults_to_passive_cc_ready_rows -n 0
```

Expected: pass.

## Task 2: Format, JSON, and CLI Registration

**Files:**
- Modify: `rytm_randomizer/reports/analog_four_oxi_macro_readiness.py`
- Modify: `rytm_randomizer/cli.py`
- Modify: `rytm_randomizer/help_text.py`
- Modify: `tests/test_analog_four_oxi_macro_readiness.py`
- Modify: `tests/test_real_midi_passive_cli_safety.py`

- [x] **Step 1: Write output and parser tests**

Append:

```python
import json

import pytest


def test_a4_macro_readiness_format_and_json_are_deterministic(capsys) -> None:
    from rytm_randomizer.reports.analog_four_oxi_macro_readiness import (
        build_analog_four_oxi_macro_readiness_payload,
        build_analog_four_oxi_macro_readiness_report,
        format_analog_four_oxi_macro_readiness_report,
    )

    report = build_analog_four_oxi_macro_readiness_report("dub-pressure", seed=3, intensity=5)
    text = "\n".join(format_analog_four_oxi_macro_readiness_report(report, event_limit=2))
    payload = build_analog_four_oxi_macro_readiness_payload(report, event_limit=2)

    assert "RytmRandomizer passive Analog Four OXI macro readiness" in text
    assert "Macro: dub-pressure" in text
    assert "Readiness: review-ready" in text
    assert "A4 full macro SEND remains unimplemented" in text
    assert payload["macro_name"] == "dub-pressure"
    assert payload["shown_count"] == 2
    assert payload["truncated_count"] == report.event_count - 2
    assert json.dumps(payload, sort_keys=True) == json.dumps(
        build_analog_four_oxi_macro_readiness_payload(report, event_limit=2),
        sort_keys=True,
    )


def test_a4_macro_readiness_cli_parser_and_handler(capsys) -> None:
    from rytm_randomizer.reports.analog_four_oxi_macro_readiness import (
        ANALOG_FOUR_OXI_MACRO_READINESS_CLI_COMMAND,
    )

    parsed = ANALOG_FOUR_OXI_MACRO_READINESS_CLI_COMMAND.args_parser(
        ["industrial-transition", "--seed", "8", "--intensity", "6", "--limit", "1"]
    )

    assert parsed == {
        "macro_name": "industrial-transition",
        "seed": 8,
        "intensity": 6,
        "event_limit": 1,
        "json_output": False,
    }
    assert ANALOG_FOUR_OXI_MACRO_READINESS_CLI_COMMAND.handler(**parsed) == 0
    assert "Macro: industrial-transition" in capsys.readouterr().out


def test_a4_macro_readiness_cli_rejects_bad_args() -> None:
    from rytm_randomizer.reports.analog_four_oxi_macro_readiness import (
        _parse_a4_macro_readiness_args,
    )

    with pytest.raises(ValueError, match="--seed requires a value"):
        _parse_a4_macro_readiness_args(["--seed"])
    with pytest.raises(ValueError, match="unknown argument"):
        _parse_a4_macro_readiness_args(["--surprise"])
    with pytest.raises(ValueError, match="macro name can only be provided once"):
        _parse_a4_macro_readiness_args(["home", "hard-groove"])
```

- [x] **Step 2: Add formatter, payload, parser, and handler**

Append the implementation:

```python
def _visible_events(
    events: Sequence[AnalogFourOxiMacroReadinessEvent],
    *,
    event_limit: int,
) -> tuple[AnalogFourOxiMacroReadinessEvent, ...]:
    if event_limit < 0:
        raise ValueError("event_limit must be >= 0")
    if event_limit == 0 or event_limit >= len(events):
        return tuple(events)
    return tuple(events[:event_limit])


def _event_line(event: AnalogFourOxiMacroReadinessEvent) -> str:
    return (
        f"- Track {event.track} | {event.role} | {event.lane} | "
        f"{event.parameter} | ch {event.channel} | CC{event.control} -> {event.value} | "
        f"{event.status} | {event.reason}"
    )


def format_analog_four_oxi_macro_readiness_report(
    report: AnalogFourOxiMacroReadinessReport,
    *,
    event_limit: int = 24,
) -> tuple[str, ...]:
    """Format ``report`` as deterministic operator-readable text."""

    visible = _visible_events(report.events, event_limit=event_limit)
    lines = [
        f"Macro: {report.macro_name}",
        f"Seed: {report.seed}",
        f"Intensity: {report.intensity}",
        f"Readiness: {report.readiness}",
        f"Events: {report.event_count}",
        f"Ready: {report.ready_count}",
        f"Needs review: {report.review_count}",
        f"Blocked: {report.blocked_count}",
        f"Shown events: {len(visible)}",
        f"Truncated events: {report.event_count - len(visible)}",
        "Safety flags:",
        f"- opens_ports: {report.opens_ports}",
        f"- sends_midi: {report.sends_midi}",
        f"- hardware_required: {report.hardware_required}",
        f"- operator_present_required: {report.operator_present_required}",
        "Validation rows:",
    ]
    lines.extend(_event_line(event) for event in visible)
    lines.append("Validation commands:")
    lines.extend(f"- {event.validation_command}" for event in visible)
    lines.append(SAFETY_SECTION_HEADER)
    lines.extend(f"- {line}" for line in SAFETY_LINES)
    return tuple(passive_report_lines(_HEADER, lines))


def _event_payload(event: AnalogFourOxiMacroReadinessEvent) -> dict[str, object]:
    return {
        "track": event.track,
        "role": event.role,
        "lane": event.lane,
        "parameter": event.parameter,
        "channel": event.channel,
        "control": event.control,
        "value": event.value,
        "status": event.status,
        "validation_command": event.validation_command,
        "reason": event.reason,
    }


def build_analog_four_oxi_macro_readiness_payload(
    report: AnalogFourOxiMacroReadinessReport,
    *,
    event_limit: int = 0,
) -> dict[str, object]:
    """Return JSON-ready A4 readiness metadata."""

    visible = _visible_events(report.events, event_limit=event_limit)
    return {
        "title": report.title,
        "macro_name": report.macro_name,
        "seed": report.seed,
        "intensity": report.intensity,
        "readiness": report.readiness,
        "event_count": report.event_count,
        "ready_count": report.ready_count,
        "review_count": report.review_count,
        "blocked_count": report.blocked_count,
        "shown_count": len(visible),
        "truncated_count": report.event_count - len(visible),
        "opens_ports": report.opens_ports,
        "sends_midi": report.sends_midi,
        "hardware_required": report.hardware_required,
        "operator_present_required": report.operator_present_required,
        "events": [_event_payload(event) for event in visible],
        "safety": list(SAFETY_LINES),
    }


def _parse_int(value: str, *, option: str) -> int:
    try:
        return int(value)
    except ValueError as exc:
        raise ValueError(f"{option} must be an integer") from exc


def _parse_nonnegative_int(value: str, *, option: str) -> int:
    parsed = _parse_int(value, option=option)
    if parsed < 0:
        raise ValueError(f"{option} must be >= 0")
    return parsed


def _parse_a4_macro_readiness_args(argv: Sequence[str]) -> dict[str, object]:
    macro_name = DEFAULT_ANALOG_FOUR_OXI_MACRO
    seed = 0
    intensity = 4
    event_limit = 24
    json_output = False
    macro_seen = False
    remaining = list(argv)
    while remaining:
        argument = remaining.pop(0)
        if argument == "--json":
            json_output = True
            continue
        if argument in {"--seed", "--intensity", "--limit"}:
            if not remaining:
                raise ValueError(f"{argument} requires a value")
            value = remaining.pop(0)
            if argument == "--seed":
                seed = _parse_int(value, option=argument)
            elif argument == "--intensity":
                intensity = _parse_nonnegative_int(value, option=argument)
            else:
                event_limit = _parse_nonnegative_int(value, option=argument)
            continue
        if argument.startswith("-"):
            raise ValueError(f"unknown argument: {argument}")
        if macro_seen:
            raise ValueError("macro name can only be provided once")
        macro_name = argument
        macro_seen = True
    return {
        "macro_name": macro_name,
        "seed": seed,
        "intensity": intensity,
        "event_limit": event_limit,
        "json_output": json_output,
    }


def _handle_a4_macro_readiness(
    macro_name: str = DEFAULT_ANALOG_FOUR_OXI_MACRO,
    *,
    seed: int = 0,
    intensity: int = 4,
    event_limit: int = 24,
    json_output: bool = False,
) -> int:
    try:
        report = build_analog_four_oxi_macro_readiness_report(
            macro_name,
            seed=seed,
            intensity=intensity,
        )
        if json_output:
            sys.stdout.write(
                json.dumps(
                    build_analog_four_oxi_macro_readiness_payload(
                        report,
                        event_limit=event_limit,
                    ),
                    sort_keys=True,
                    indent=2,
                )
            )
            sys.stdout.write("\n")
        else:
            sys.stdout.write(
                "\n".join(
                    format_analog_four_oxi_macro_readiness_report(
                        report,
                        event_limit=event_limit,
                    )
                )
            )
            sys.stdout.write("\n")
    except ValueError as exc:
        sys.stderr.write(f"{exc}\n")
        return 2
    return 0


ANALOG_FOUR_OXI_MACRO_READINESS_CLI_COMMAND: Final[CliCommand] = CliCommand(
    name="analog-four-oxi-macro-readiness-report",
    summary="Print passive A4 OXI macro readiness and operator validation commands.",
    args_parser=_parse_a4_macro_readiness_args,
    handler=_handle_a4_macro_readiness,
)

register(ANALOG_FOUR_OXI_MACRO_READINESS_CLI_COMMAND)
```

- [x] **Step 3: Register the command through the lazy CLI table**

Do not re-export this focused report through `rytm_randomizer/reports/__init__.py`;
PR #158 intentionally brought that legacy facade back under the 1,500-line
comprehensibility cap. In `rytm_randomizer/cli.py`, add
`"ANALOG_FOUR_OXI_MACRO_READINESS_CLI_COMMAND"` beside the A4 passive command
imports.

In `rytm_randomizer/help_text.py`, add:

```python
"analog-four-oxi-macro-readiness-report": (
    "RytmRandomizer passive CLI: analog-four-oxi-macro-readiness-report\n"
    "Builds A4 OXI macro readiness cards and operator-present one-row validation commands. "
    "No MIDI port is opened and no MIDI is sent."
),
```

In `tests/test_real_midi_passive_cli_safety.py`, add:

```python
("analog-four-oxi-macro-readiness-report",),
("analog-four-oxi-macro-readiness-report", "--json"),
```

- [x] **Step 4: Run focused tests**

Run:

```powershell
python -m pytest tests\test_analog_four_oxi_macro_readiness.py tests\test_real_midi_passive_cli_safety.py -n 0
```

Expected: all selected tests pass.

## Task 3: Add A4 Readiness to the Cockpit Performance Flow Model

**Files:**
- Modify: `rytm_randomizer/reports/live_gui_performance_flow_model.py`
- Modify: `desktop/web/src/cockpit/live_gui_protocol.ts`
- Modify: `desktop/web/src/cockpit/LiveReadinessPanel.tsx`
- Modify: `tests/test_live_gui_performance_flow_model.py`
- Modify: `desktop/web/tests/cockpit/LiveReadinessPanel.test.tsx`

- [x] **Step 1: Write Python contract tests**

Add:

```python
def test_live_gui_performance_flow_includes_a4_readiness_summary() -> None:
    from rytm_randomizer.reports.live_gui_performance_flow_model import (
        build_live_gui_performance_flow_model,
        live_gui_performance_flow_model_payload,
    )

    payload = live_gui_performance_flow_model_payload(
        build_live_gui_performance_flow_model()
    )["live_gui_performance_flow_model"]

    assert payload["analog_four_readiness"]["status"] == "review-ready"
    assert payload["analog_four_readiness"]["command"] == (
        "analog-four-oxi-macro-readiness-report hard-groove --seed 0 --intensity 4 --limit 4"
    )
    assert payload["analog_four_readiness"]["blocked_active_actions"] == [
        "A4 full macro SEND"
    ]
```

- [x] **Step 2: Update the Python model**

Add a frozen dataclass near the existing flow dataclasses:

```python
@dataclass(frozen=True)
class AnalogFourReadinessSummaryModel:
    status: str
    command: str
    summary: str
    blocked_active_actions: tuple[str, ...]
```

Add this field to the report model:

```python
analog_four_readiness: AnalogFourReadinessSummaryModel
```

Populate it in the builder:

```python
analog_four_readiness=AnalogFourReadinessSummaryModel(
    status="review-ready",
    command="analog-four-oxi-macro-readiness-report hard-groove --seed 0 --intensity 4 --limit 4",
    summary="A4 macro rows are passive readiness cards until operator-present validation promotes them.",
    blocked_active_actions=("A4 full macro SEND",),
),
```

Add it to the JSON payload:

```python
"analog_four_readiness": {
    "status": report.analog_four_readiness.status,
    "command": report.analog_four_readiness.command,
    "summary": report.analog_four_readiness.summary,
    "blocked_active_actions": list(report.analog_four_readiness.blocked_active_actions),
},
```

- [x] **Step 3: Mirror the TypeScript protocol**

In `desktop/web/src/cockpit/live_gui_protocol.ts`, add:

```ts
export interface AnalogFourReadinessSummaryModel {
  status: string;
  command: string;
  summary: string;
  blocked_active_actions: string[];
}
```

Add `analog_four_readiness: AnalogFourReadinessSummaryModel;` to the live flow model interface.

- [x] **Step 4: Render the A4 readiness row**

In `desktop/web/src/cockpit/LiveReadinessPanel.tsx`, render the summary in the existing passive A4 area:

```tsx
<section className="live-performance-flow__a4-readiness" aria-label="Analog Four readiness">
  <h4>Analog Four Readiness</h4>
  <p>{model.analog_four_readiness.summary}</p>
  <code>{model.analog_four_readiness.command}</code>
  <ul>
    {model.analog_four_readiness.blocked_active_actions.map((action) => (
      <li key={action}>{action}</li>
    ))}
  </ul>
</section>
```

- [x] **Step 5: Run focused Python and frontend tests**

Run:

```powershell
python -m pytest tests\test_live_gui_performance_flow_model.py -n 0
pushd desktop\web
npm test -- --run LiveReadinessPanel
popd
```

Expected: both focused suites pass.

## Task 4: Document the Operator-Present A4 Validation Runway

**Files:**
- Modify: `README.md`
- Modify: `docs/STATUS.md`

- [x] **Step 1: Update README**

Near the A4 soft capture and named-send section, add:

````markdown
Analog Four OXI macro readiness is passive:

```bash
python -m rytm_randomizer.cli analog-four-oxi-macro-readiness-report hard-groove --seed 0 --intensity 4 --limit 4
```

The report lists the deterministic A4 macro rows and prints one-row validation
commands such as `python -m rytm_randomizer.app --arm --a4-send-param ...`.
Those commands are for operator-present hardware checks only. They do not create
an unattended A4 macro SEND path, and the cockpit must keep A4 full macro SEND
blocked until the validation evidence is reviewed.
````

- [x] **Step 2: Update status**

At the top of `docs/STATUS.md`, set `Last updated: 2026-06-06.` and add a single current-status bullet under Recent Cleanup:

```markdown
- 2026-06-06: Post-#158 A4 readiness runway prepared. The passive
  `analog-four-oxi-macro-readiness-report` classifies deterministic A4 OXI macro
  rows, prints operator-present one-row validation commands, and feeds the
  cockpit performance flow as review-only state. This opens no ports, sends no
  MIDI, and still blocks unattended A4 full macro SEND.
```

- [x] **Step 3: Run doc checks**

Run:

```powershell
git diff --check
python -m pytest tests\architecture\ -q
```

Expected: no whitespace errors and architecture tests pass.

## Task 5: Full Verification and PR Preparation

**Files:**
- Modify: PR body file created by the implementation worker, if opening after #158.

- [x] **Step 1: Run focused report tests**

Run:

```powershell
python -m pytest tests\test_analog_four_oxi_macro_readiness.py tests\test_analog_four_oxi_macro_report.py tests\test_live_gui_performance_flow_model.py -n 0
```

Expected: all selected tests pass.

- [x] **Step 2: Run passive CLI safety**

Run:

```powershell
python -m pytest tests\test_real_midi_passive_cli_safety.py -n 0
```

Expected: all passive command safety tests pass, proving the new CLI path does not import or open real MIDI.

- [x] **Step 3: Run full local verification**

Run:

```powershell
python -m pytest
python -m ruff check .
python -m black --check --target-version=py311 .
python -m isort --profile black --check-only .
git diff --check
```

Expected: pytest passes, lint passes, formatting checks pass, and no whitespace errors are reported.

- [ ] **Step 4: Open exactly one PR after #158 is resolved**

Only after #158 merges or is explicitly replaced, push this branch and open one PR against `modularize-v1.34`:

```powershell
git push -u origin codex/post-158-oxi-a4-readiness
python scripts\create_pr.py --title "feat: add A4 OXI macro readiness runway" --body-file .pr-body-post-158-oxi-a4-readiness.md
```

Expected: one non-stacked PR with the 18-gate checklist and reviewer request.

## Self-Review

- Spec coverage: this plan covers A4 passive readiness, operator-present one-row validation commands, cockpit handoff, docs, tests, and no-stacked-PR discipline while #158 is review-blocked.
- Safety coverage: passive commands open no ports and send no MIDI; active A4 testing remains explicit `--arm` with one row at a time; A4 full macro SEND remains blocked.
- Architecture coverage: new work lands in `reports/`, existing `data/` facts, existing CLI registry, existing cockpit protocol, and does not create new top-level packages or device-family forks.
- Rytm coverage: the plan preserves the already-shipped Rytm all-12 macro policy, including SRC-first movement for pads 5, 9, 10, and 11; tom/source movement with light filter and no LFO for pads 6-8; and product support for Pad 12.
