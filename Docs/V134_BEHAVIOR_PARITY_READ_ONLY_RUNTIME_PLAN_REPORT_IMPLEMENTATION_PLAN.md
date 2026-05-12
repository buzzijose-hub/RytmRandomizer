# Read-Only Runtime Plan Report Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a read-only runtime plan report that summarizes existing mock-only runtime plan metadata without adding execution, MIDI, ports, CLI execution wiring, active behavior, or hardware behavior.

**Architecture:** Create a small passive `runtime_plan_report.py` module that builds copied in-memory report data from existing `runtime_plan.py` concepts, plus deterministic formatter and summary helpers. Add focused tests and a closeout label for the new report test file, while leaving runtime plan execution behavior blocked and unchanged.

**Tech Stack:** Python standard library, existing `runtime_plan.py` dataclasses/helpers, pytest-style script tests, existing PowerShell closeout suite. No `mido`, no `rtmidi`, no port providers, no CLI execution wiring, no package metadata changes, and no hardware dependency.

---

## 1. Purpose

Define the future implementation plan for the read-only runtime plan report
after the accepted report design review.

This is a documentation-only implementation plan.

It does not implement the report.

It does not add tests.

It does not change closeout.

It does not add CLI execution wiring, runtime execution, dispatch, command
execution, MIDI, ports, package metadata changes, active behavior, or hardware
behavior.

## 2. Current Clean Baseline

Current branch:

- `modularize-v1.34`

Current HEAD before this planning slice:

- `8063b60 Add read-only runtime plan report design review`

Current phase:

- Passive/Mock Foundation Phase
- behavior-parity implementation phase
- mock-only runtime plan scaffold implemented and accepted
- metadata-only runtime plan preview metadata implemented and accepted
- read-only runtime plan report design reviewed and accepted
- read-only runtime plan report implementation plan now being documented

Hardware status:

- Analog Rytm MKII off
- Analog Four MKII off
- hardware not required

## 3. Accepted Upstream Inputs

Accepted design review:

- `Docs/V134_BEHAVIOR_PARITY_READ_ONLY_RUNTIME_PLAN_REPORT_DESIGN_REVIEW.md`

Accepted design:

- `Docs/V134_BEHAVIOR_PARITY_READ_ONLY_RUNTIME_PLAN_REPORT_DESIGN.md`

Accepted current runtime plan baseline:

- `Docs/V134_BEHAVIOR_PARITY_METADATA_ONLY_RUNTIME_PLAN_PREVIEW_METADATA_CHECKPOINT_REVIEW.md`

Current runtime plan module:

- `rytm_randomizer/runtime_plan.py`

Current runtime plan tests:

- `tests/test_runtime_plan.py`

Current closeout coverage:

- `=== Test: Runtime Plan ===`

## 4. Future File Structure

Future implementation should create:

- `rytm_randomizer/runtime_plan_report.py`
  - builds copied report data from existing runtime plan concepts
  - formats deterministic human-readable report lines
  - summarizes report counts and safety flags
  - remains side-effect free on import
- `tests/test_runtime_plan_report.py`
  - proves report data, formatter, summary, copy safety, no MIDI imports, and
    no active behavior names

Future implementation should modify:

- `Scripts/closeout_check.ps1`
  - add one closeout label:
    - `=== Test: Runtime Plan Report ===`

Future implementation should not modify:

- `rytm_hybrid_randomizer_v134.py`
- `rytm_randomizer/cli.py`
- `rytm_randomizer/runtime_plan.py`
- `rytm_randomizer/mock_midi.py`
- `rytm_randomizer/mock_message_mapper.py`
- `rytm_randomizer/mock_mapper_report.py`
- package metadata
- runtime execution/dispatch logic
- active CLI commands

## 5. Task 1: Report Data Tests

**Files:**

- Create: `tests/test_runtime_plan_report.py`
- Modify later: `rytm_randomizer/runtime_plan_report.py`

- [ ] **Step 1: Write failing tests for import silence and report data**

Create `tests/test_runtime_plan_report.py` with:

```python
from pathlib import Path
import subprocess
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def test_importing_runtime_plan_report_prints_nothing():
    result = subprocess.run(
        [sys.executable, "-c", "import rytm_randomizer.runtime_plan_report"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert result.stdout == ""
    assert result.stderr == ""


def test_report_summarizes_runtime_plan_inputs():
    from rytm_randomizer.runtime_plan_report import build_runtime_plan_report

    report = build_runtime_plan_report()

    assert report["title"] == "RytmRandomizer Runtime Plan Report"
    assert report["mode"] == {
        "mock_only": True,
        "metadata_only": True,
        "blocked_by_default": True,
    }
    assert report["supported_planning_inputs"] == (
        {
            "source_kind": "group_profile",
            "source_key": "2",
            "target": "Pad 1 / My BD Hard",
            "source_label": "group_profile:2",
            "status": "blocked",
            "reason": "execution not implemented",
            "reason_code": "execution_not_implemented",
            "supported": True,
            "parked": False,
            "would_execute": False,
            "mock_only": True,
            "sends_real_midi": False,
            "ports_allowed": False,
            "hardware_required": False,
        },
        {
            "source_kind": "group_profile",
            "source_key": "3",
            "target": "Pad 2 / My BD Classic",
            "source_label": "group_profile:3",
            "status": "blocked",
            "reason": "execution not implemented",
            "reason_code": "execution_not_implemented",
            "supported": True,
            "parked": False,
            "would_execute": False,
            "mock_only": True,
            "sends_real_midi": False,
            "ports_allowed": False,
            "hardware_required": False,
        },
    )
    assert report["parked_planning_inputs"] == (
        {
            "source_kind": "group_profile",
            "source_key": "4",
            "target": "Pad 1 / My BD Acoustic",
            "source_label": "group_profile:4",
            "status": "blocked",
            "reason": "profile 4 parked",
            "reason_code": "profile_4_parked",
            "supported": False,
            "parked": True,
            "would_execute": False,
            "mock_only": True,
            "sends_real_midi": False,
            "ports_allowed": False,
            "hardware_required": False,
        },
    )
    assert report["unsupported_planning_inputs"] == (
        {
            "source_kind": "group_profile",
            "source_key": "unknown",
            "target": "unknown",
            "source_label": "group_profile:unknown",
            "status": "blocked",
            "reason": "unsupported key",
            "reason_code": "unsupported_key",
            "supported": False,
            "parked": False,
            "would_execute": False,
            "mock_only": True,
            "sends_real_midi": False,
            "ports_allowed": False,
            "hardware_required": False,
        },
        {
            "source_kind": "scene",
            "source_key": "S1A",
            "target": "Rolling Light",
            "source_label": "scene:S1A",
            "status": "blocked",
            "reason": "unsupported source kind",
            "reason_code": "unsupported_source_kind",
            "supported": False,
            "parked": False,
            "would_execute": False,
            "mock_only": True,
            "sends_real_midi": False,
            "ports_allowed": False,
            "hardware_required": False,
        },
    )
```

- [ ] **Step 2: Run tests and verify failure**

Run:

```powershell
python -m pytest tests/test_runtime_plan_report.py::test_importing_runtime_plan_report_prints_nothing tests/test_runtime_plan_report.py::test_report_summarizes_runtime_plan_inputs -q
```

Expected:

- FAIL because `rytm_randomizer.runtime_plan_report` does not exist yet.

## 6. Task 2: Minimal Report Module

**Files:**

- Create: `rytm_randomizer/runtime_plan_report.py`

- [ ] **Step 1: Implement the minimal report module**

Create `rytm_randomizer/runtime_plan_report.py`:

```python
"""Read-only runtime plan report summary.

This module is passive and in-memory only. It reports current mock-only
runtime plan metadata without opening ports, sending MIDI, wiring CLI
execution, or touching hardware.
"""

from __future__ import annotations

from copy import deepcopy

from .runtime_plan import RuntimeIntent, validate_runtime_intent_scope

SUPPORTED_REPORT_INPUTS = (
    {
        "category": "supported",
        "source_kind": "group_profile",
        "source_key": "2",
        "target": "Pad 1 / My BD Hard",
    },
    {
        "category": "supported",
        "source_kind": "group_profile",
        "source_key": "3",
        "target": "Pad 2 / My BD Classic",
    },
)

PARKED_REPORT_INPUTS = (
    {
        "category": "parked",
        "source_kind": "group_profile",
        "source_key": "4",
        "target": "Pad 1 / My BD Acoustic",
    },
)

UNSUPPORTED_REPORT_INPUTS = (
    {
        "category": "unsupported",
        "source_kind": "group_profile",
        "source_key": "unknown",
        "target": "unknown",
    },
    {
        "category": "unsupported",
        "source_kind": "scene",
        "source_key": "S1A",
        "target": "Rolling Light",
    },
)

RUNTIME_PLAN_REPORT_BOUNDARY = {
    "runtime_execution": "absent",
    "cli_execution_wiring": "absent",
    "dispatch": "absent",
    "command_execution": "absent",
    "scene_execution": "absent",
    "real_midi": "absent",
    "port_opening": "absent",
    "hardware_required": False,
}


def _preview_summary(report_input):
    intent = RuntimeIntent(
        source_kind=report_input["source_kind"],
        source_key=report_input["source_key"],
        target=report_input["target"],
    )
    preview = validate_runtime_intent_scope(intent)
    metadata = preview.metadata
    return {
        "source_kind": metadata["source_kind"],
        "source_key": metadata["source_key"],
        "target": metadata["target"],
        "source_label": metadata["source_label"],
        "status": preview.status,
        "reason": preview.reason,
        "reason_code": metadata["reason_code"],
        "supported": metadata["supported"],
        "parked": metadata["parked"],
        "would_execute": metadata["would_execute"],
        "mock_only": metadata["mock_only"],
        "sends_real_midi": metadata["sends_real_midi"],
        "ports_allowed": metadata["ports_allowed"],
        "hardware_required": metadata["hardware_required"],
    }


def build_runtime_plan_report():
    """Return copied, in-memory data about current runtime plan metadata."""

    report = {
        "title": "RytmRandomizer Runtime Plan Report",
        "mode": {
            "mock_only": True,
            "metadata_only": True,
            "blocked_by_default": True,
        },
        "supported_planning_inputs": tuple(
            _preview_summary(report_input)
            for report_input in SUPPORTED_REPORT_INPUTS
        ),
        "parked_planning_inputs": tuple(
            _preview_summary(report_input)
            for report_input in PARKED_REPORT_INPUTS
        ),
        "unsupported_planning_inputs": tuple(
            _preview_summary(report_input)
            for report_input in UNSUPPORTED_REPORT_INPUTS
        ),
        "reason_codes": (
            "execution_not_implemented",
            "unsupported_key",
            "unsupported_source_kind",
            "profile_4_parked",
            "missing_arming",
        ),
        "safety": {
            "would_execute": False,
            "mock_only": True,
            "sends_real_midi": False,
            "ports_allowed": False,
            "hardware_required": False,
        },
        **RUNTIME_PLAN_REPORT_BOUNDARY,
        "source": {
            "runtime_plan_module": "rytm_randomizer.runtime_plan",
            "in_memory_only": True,
        },
    }
    return deepcopy(report)
```

- [ ] **Step 2: Run report data tests and verify pass**

Run:

```powershell
python -m pytest tests/test_runtime_plan_report.py::test_importing_runtime_plan_report_prints_nothing tests/test_runtime_plan_report.py::test_report_summarizes_runtime_plan_inputs -q
```

Expected:

- PASS.

## 7. Task 3: Safety, Summary, And Formatter Tests

**Files:**

- Modify: `tests/test_runtime_plan_report.py`
- Modify later: `rytm_randomizer/runtime_plan_report.py`

- [ ] **Step 1: Add failing tests for boundaries, summary, formatter, copy safety, and active names**

Append to `tests/test_runtime_plan_report.py`:

```python
def test_report_records_read_only_runtime_boundaries():
    from rytm_randomizer.runtime_plan_report import build_runtime_plan_report

    report = build_runtime_plan_report()

    assert report["safety"] == {
        "would_execute": False,
        "mock_only": True,
        "sends_real_midi": False,
        "ports_allowed": False,
        "hardware_required": False,
    }
    assert report["runtime_execution"] == "absent"
    assert report["cli_execution_wiring"] == "absent"
    assert report["dispatch"] == "absent"
    assert report["command_execution"] == "absent"
    assert report["scene_execution"] == "absent"
    assert report["real_midi"] == "absent"
    assert report["port_opening"] == "absent"
    assert report["hardware_required"] is False


def test_report_summary_is_deterministic():
    from rytm_randomizer.runtime_plan_report import summarize_runtime_plan_report

    assert summarize_runtime_plan_report() == {
        "title": "RytmRandomizer Runtime Plan Report",
        "supported_count": 2,
        "parked_count": 1,
        "unsupported_count": 2,
        "reason_codes": (
            "execution_not_implemented",
            "unsupported_key",
            "unsupported_source_kind",
            "profile_4_parked",
            "missing_arming",
        ),
        "would_execute": False,
        "mock_only": True,
        "runtime_execution": "absent",
    }


def test_formatted_report_is_deterministic_and_human_readable():
    from rytm_randomizer.runtime_plan_report import format_runtime_plan_report

    first = format_runtime_plan_report()
    second = format_runtime_plan_report()

    assert first == second
    assert first == [
        "RytmRandomizer Runtime Plan Report",
        "Runtime Plan Mode:",
        "- mock_only: True",
        "- metadata_only: True",
        "- blocked_by_default: True",
        "Supported Planning Inputs:",
        "- group_profile:2 -> Pad 1 / My BD Hard (execution_not_implemented)",
        "- group_profile:3 -> Pad 2 / My BD Classic (execution_not_implemented)",
        "Parked Planning Inputs:",
        "- group_profile:4 -> Pad 1 / My BD Acoustic (profile_4_parked)",
        "Unsupported Planning Inputs:",
        "- group_profile:unknown -> unknown (unsupported_key)",
        "- scene:S1A -> Rolling Light (unsupported_source_kind)",
        "Runtime Plan Safety:",
        "- would_execute: False",
        "- mock_only: True",
        "- sends_real_midi: False",
        "- ports_allowed: False",
        "- hardware_required: False",
        "- runtime_execution: absent",
        "- cli_execution_wiring: absent",
        "- dispatch: absent",
        "Source: rytm_randomizer.runtime_plan",
        "In-memory only: True",
    ]


def test_returned_report_data_is_copied_and_mutation_safe():
    from rytm_randomizer.runtime_plan_report import build_runtime_plan_report

    report = build_runtime_plan_report()
    report["supported_planning_inputs"][0]["target"] = "MUTATED"
    report["source"]["runtime_plan_module"] = "MUTATED"

    fresh_report = build_runtime_plan_report()

    assert fresh_report["supported_planning_inputs"][0]["target"] == "Pad 1 / My BD Hard"
    assert fresh_report["source"]["runtime_plan_module"] == "rytm_randomizer.runtime_plan"


def test_no_real_midi_library_is_imported():
    import rytm_randomizer.runtime_plan_report  # noqa: F401

    assert "mido" not in sys.modules
    assert "rtmidi" not in sys.modules


def test_runtime_plan_report_exposes_no_active_behavior_names():
    import rytm_randomizer.runtime_plan_report as report

    exposed_names = set(dir(report))

    assert "execute_command" not in exposed_names
    assert "send_command" not in exposed_names
    assert "hardware_test" not in exposed_names
    assert "open_port" not in exposed_names
    assert "open_midi_port" not in exposed_names
    assert "send_midi" not in exposed_names
```

- [ ] **Step 2: Run tests and verify failure**

Run:

```powershell
python -m pytest tests/test_runtime_plan_report.py -q
```

Expected:

- FAIL because summary and formatter helpers do not exist yet.

## 8. Task 4: Summary And Formatter Implementation

**Files:**

- Modify: `rytm_randomizer/runtime_plan_report.py`

- [ ] **Step 1: Add summary and formatter helpers**

Append to `rytm_randomizer/runtime_plan_report.py`:

```python
def summarize_runtime_plan_report(report=None):
    """Return a compact copied summary of the runtime plan report."""

    source_report = build_runtime_plan_report() if report is None else report
    return {
        "title": source_report["title"],
        "supported_count": len(source_report["supported_planning_inputs"]),
        "parked_count": len(source_report["parked_planning_inputs"]),
        "unsupported_count": len(source_report["unsupported_planning_inputs"]),
        "reason_codes": tuple(source_report["reason_codes"]),
        "would_execute": source_report["safety"]["would_execute"],
        "mock_only": source_report["safety"]["mock_only"],
        "runtime_execution": source_report["runtime_execution"],
    }


def _input_line(summary):
    return (
        f"- {summary['source_label']} -> {summary['target']} "
        f"({summary['reason_code']})"
    )


def format_runtime_plan_report(report=None):
    """Return deterministic human-readable runtime plan report lines."""

    source_report = build_runtime_plan_report() if report is None else report
    lines = [
        source_report["title"],
        "Runtime Plan Mode:",
        f"- mock_only: {source_report['mode']['mock_only']}",
        f"- metadata_only: {source_report['mode']['metadata_only']}",
        f"- blocked_by_default: {source_report['mode']['blocked_by_default']}",
        "Supported Planning Inputs:",
    ]

    for summary in source_report["supported_planning_inputs"]:
        lines.append(_input_line(summary))

    lines.append("Parked Planning Inputs:")
    for summary in source_report["parked_planning_inputs"]:
        lines.append(_input_line(summary))

    lines.append("Unsupported Planning Inputs:")
    for summary in source_report["unsupported_planning_inputs"]:
        lines.append(_input_line(summary))

    lines.extend(
        [
            "Runtime Plan Safety:",
            f"- would_execute: {source_report['safety']['would_execute']}",
            f"- mock_only: {source_report['safety']['mock_only']}",
            f"- sends_real_midi: {source_report['safety']['sends_real_midi']}",
            f"- ports_allowed: {source_report['safety']['ports_allowed']}",
            f"- hardware_required: {source_report['safety']['hardware_required']}",
            f"- runtime_execution: {source_report['runtime_execution']}",
            f"- cli_execution_wiring: {source_report['cli_execution_wiring']}",
            f"- dispatch: {source_report['dispatch']}",
            "Source: rytm_randomizer.runtime_plan",
            "In-memory only: True",
        ]
    )
    return lines
```

- [ ] **Step 2: Run tests and verify pass**

Run:

```powershell
python -m pytest tests/test_runtime_plan_report.py -q
```

Expected:

- PASS.

## 9. Task 5: Closeout Integration

**Files:**

- Modify: `Scripts/closeout_check.ps1`

- [ ] **Step 1: Add closeout label**

Add after the existing Runtime Plan test block:

```powershell
"=== Test: Runtime Plan Report ===" | Add-Content $summary
& $pythonExe @pythonArgs .\tests\test_runtime_plan_report.py 2>&1 | Tee-Object -FilePath "$logDir\latest_test_runtime_plan_report.log" | Add-Content $summary

"" | Add-Content $summary
```

- [ ] **Step 2: Run full closeout and verify label appears**

Run:

```powershell
powershell -ExecutionPolicy Bypass -File .\Scripts\closeout_check.ps1
```

Expected:

- closeout completes
- `=== Test: Runtime Plan Report ===` appears
- V1.34 reference diff is empty

## 10. Task 6: Protected Diffs And Commit

**Files:**

- Review only.

- [ ] **Step 1: Confirm V1.34 untouched**

Run:

```powershell
git diff -- rytm_hybrid_randomizer_v134.py
```

Expected:

- no output.

- [ ] **Step 2: Confirm package metadata untouched**

Run:

```powershell
git diff -- pyproject.toml requirements.txt setup.py setup.cfg
```

Expected:

- no output.

- [ ] **Step 3: Check status**

Run:

```powershell
git status --short
```

Expected:

```text
 M Scripts/closeout_check.ps1
?? rytm_randomizer/runtime_plan_report.py
?? tests/test_runtime_plan_report.py
```

- [ ] **Step 4: Commit approved implementation files**

Run:

```powershell
git add .\rytm_randomizer\runtime_plan_report.py `
        .\tests\test_runtime_plan_report.py `
        .\Scripts\closeout_check.ps1

git commit -m "Add read-only runtime plan report"
```

- [ ] **Step 5: Final closeout**

Run:

```powershell
powershell -ExecutionPolicy Bypass -File .\Scripts\closeout_check.ps1
git status --short
```

Expected:

- closeout completes
- `git status --short` returns no output

## 11. Forbidden Scope

The future implementation must not add:

- runtime execution
- dispatch
- command execution
- scene execution
- real MIDI
- `mido`
- `rtmidi`
- port discovery
- port opening
- MIDI sending
- active CLI execution
- `execute-command`
- `send-command`
- `hardware-test`
- runtime plan report CLI command
- profile `4` mock mapper support
- fourth runtime-adjacent candidate
- selected pad switching execution
- selected pad target state mutation
- selected pad anchor return execution
- current anchor return execution
- isolated pad mutation execution
- runtime mutation
- Analog Four support
- Pads 5-12 support
- SysEx
- GUI/capture
- package metadata changes
- active behavior
- hardware behavior

## 12. Self-Review

Spec coverage:

- The plan covers the future report module, test file, deterministic formatter,
  summary helper, copied report data, closeout label, protected diffs, and
  commit command.

Placeholder scan:

- No `TBD`, `TODO`, or fill-in placeholders are included.

Type consistency:

- Function names are consistent across tests and implementation:
  - `build_runtime_plan_report`
  - `summarize_runtime_plan_report`
  - `format_runtime_plan_report`

## 13. Decision

The read-only runtime plan report implementation plan is documented.

The plan is not implementation.

Future implementation remains separately gated.

Hardware remains off.

## 14. Follow-Up Status

The implementation plan is now reviewed and accepted by:

- `Docs/V134_BEHAVIOR_PARITY_READ_ONLY_RUNTIME_PLAN_REPORT_IMPLEMENTATION_PLAN_REVIEW.md`

The next recommended task is to implement the read-only runtime plan report
using TDD.
