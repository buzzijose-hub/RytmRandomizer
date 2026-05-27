# Manual Validation Kit Implementation Plan

> Status: in-flight

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a passive `manual-validation-kit-report` that gives operators a deterministic installer/UI/profile/mock/hardware-smoke checklist without executing any active behavior.

**Architecture:** Add immutable manual-validation facts in `rytm_randomizer/data/manual_validation.py`, render them from `rytm_randomizer/reports/manual_validation_kit.py`, and register one lazy CLI command in `rytm_randomizer/cli.py`. The command prints active hardware commands only as instructions and keeps all execution passive.

**Tech Stack:** Python 3.11, frozen dataclasses, `CliCommand`, passive report formatter, pytest fast tests.

---

## File Structure

- Create `rytm_randomizer/data/manual_validation.py`: phase and step dataclasses plus canonical validation kit facts.
- Create `rytm_randomizer/reports/manual_validation_kit.py`: builder, filter validation, text formatter, JSON adapter, CLI parser/handler.
- Create `tests/test_manual_validation_kit_report.py`: TDD coverage for defaults, phase filtering, JSON, CLI text/JSON, help, and import safety.
- Modify `rytm_randomizer/cli.py`: add lazy command entry for `manual-validation-kit-report`.
- Modify `rytm_randomizer/help_text.py`: add top-level usage row and command-specific help text.
- Modify `tests/fixtures/cli_help_expected.txt`: keep byte-exact CLI help fixture current.
- Modify `docs/CLI_REFERENCE.md`: document the command.
- Modify `docs/MANUAL_HARDWARE_VALIDATION.md`: link the new passive kit near the manual testing checklist.

## Task 1: Failing Tests

**Files:**
- Create: `tests/test_manual_validation_kit_report.py`

- [x] **Step 1: Add tests for the desired passive report API**

```python
"""Tests for the passive manual validation kit report."""

from __future__ import annotations

import json
import sys

import pytest

pytestmark = pytest.mark.fast

FORBIDDEN_REAL_MIDI_AND_ADAPTER_MODULES = (
    "mido",
    "rtmidi",
    "pythonrtmidi",
    "rytm_randomizer.real_midi_adapter",
)


def test_manual_validation_kit_report_defaults_to_full_passive_itinerary() -> None:
    from rytm_randomizer.reports.manual_validation_kit import (
        build_manual_validation_kit_report,
        format_manual_validation_kit_report,
        to_manual_validation_kit_json,
    )

    report = build_manual_validation_kit_report()

    assert report.model_version == "manual-validation-kit-v1"
    assert report.phase_filter is None
    assert [phase.slug for phase in report.phases] == [
        "installer_bootstrap",
        "profile_workflow",
        "mock_rehearsal",
        "armed_smoke",
        "evidence_closeout",
    ]
    assert len(report.steps) >= 10
    assert any(step.requires_hardware for step in report.steps)
    assert all(not command.startswith("& ") for step in report.steps for command in step.passive_commands)
    assert "open MIDI ports" in report.blocked_actions
    assert "send MIDI" in report.blocked_actions
    assert report.safety["opens_midi_ports"] is False
    assert report.safety["sends_midi"] is False

    lines = format_manual_validation_kit_report(report)
    assert lines[0] == "RytmRandomizer passive manual validation kit report"
    assert "Validation phases:" in lines
    assert "- installer_bootstrap: Installer bootstrap" in lines
    assert "Manual commands (instruction text only):" in lines
    assert any("--arm --validate-one-cc" in line for line in lines)
    assert "Safety:" in lines
    assert "Source: rytm_randomizer.reports.manual_validation_kit" in lines

    payload = to_manual_validation_kit_json(report)
    assert payload["manual_validation_kit"]["phase_count"] == 5
    assert payload["manual_validation_kit"]["safety"]["executes_printed_commands"] is False
    json.dumps(payload, sort_keys=True)
```

- [x] **Step 2: Add tests for phase filtering and validation**

```python
def test_manual_validation_kit_report_filters_to_one_phase() -> None:
    from rytm_randomizer.reports.manual_validation_kit import (
        build_manual_validation_kit_report,
        format_manual_validation_kit_report,
    )

    report = build_manual_validation_kit_report(phase="profile_workflow")

    assert report.phase_filter == "profile_workflow"
    assert [phase.slug for phase in report.phases] == ["profile_workflow"]
    assert {step.phase for step in report.steps} == {"profile_workflow"}
    assert any("Create profile" in step.title for step in report.steps)
    assert all(not step.requires_hardware for step in report.steps)

    lines = format_manual_validation_kit_report(report)
    assert "Phase filter: profile_workflow" in lines
    assert "- profile_workflow: Profile workflow" in lines
    assert "- installer_bootstrap: Installer bootstrap" not in lines


def test_manual_validation_kit_report_rejects_unknown_phase() -> None:
    from rytm_randomizer.reports.manual_validation_kit import build_manual_validation_kit_report

    with pytest.raises(ValueError, match="Unknown manual validation phase"):
        build_manual_validation_kit_report(phase="missing")
```

- [x] **Step 3: Add CLI and import-safety tests**

```python
def test_manual_validation_kit_report_imports_no_real_midi_modules() -> None:
    before_modules = set(sys.modules)

    from rytm_randomizer.reports.manual_validation_kit import (
        build_manual_validation_kit_report,
        to_manual_validation_kit_json,
    )

    report = build_manual_validation_kit_report()
    json.dumps(to_manual_validation_kit_json(report), sort_keys=True)

    imported_modules = set(sys.modules) - before_modules
    assert not (set(FORBIDDEN_REAL_MIDI_AND_ADAPTER_MODULES) & imported_modules)


def test_manual_validation_kit_report_passive_cli_text_json_and_help(
    capsys: pytest.CaptureFixture[str],
) -> None:
    from rytm_randomizer import cli
    from rytm_randomizer.help_text import resolve_help_text

    rc = cli.main(["manual-validation-kit-report", "--phase", "mock_rehearsal"])

    captured = capsys.readouterr()
    assert rc == 0
    assert "RytmRandomizer passive manual validation kit report" in captured.out
    assert "Phase filter: mock_rehearsal" in captured.out
    assert "Mock rehearsal" in captured.out
    assert "no MIDI ports opened" in captured.out
    assert captured.err == ""

    rc = cli.main(["manual-validation-kit-report", "--phase", "armed_smoke", "--json"])

    captured = capsys.readouterr()
    assert rc == 0
    payload = json.loads(captured.out)
    assert payload["manual_validation_kit"]["phase_filter"] == "armed_smoke"
    assert payload["manual_validation_kit"]["phases"][0]["slug"] == "armed_smoke"
    assert payload["manual_validation_kit"]["safety"]["sends_midi"] is False
    assert captured.err == ""

    help_text = resolve_help_text("manual-validation-kit-report")
    assert help_text.startswith("RytmRandomizer passive CLI: manual-validation-kit-report")
    assert "manual-validation-kit-report [--phase <slug>] [--json]" in help_text
```

- [x] **Step 4: Run tests and confirm RED**

Run:

```bash
python -m pytest tests/test_manual_validation_kit_report.py -n 0
```

Expected: fails because `rytm_randomizer.reports.manual_validation_kit` does not exist.

## Task 2: Data Model

**Files:**
- Create: `rytm_randomizer/data/manual_validation.py`

- [x] **Step 1: Implement immutable phases and steps**

Create frozen dataclasses `ManualValidationPhase` and `ManualValidationStep`, the five phase constants, and ordered step constants covering installer bootstrap, profile workflow, mock rehearsal, armed smoke, and evidence closeout.

- [x] **Step 2: Run tests and confirm data import works**

Run:

```bash
python -m pytest tests/test_manual_validation_kit_report.py -n 0
```

Expected: still fails because the report module is not implemented.

## Task 3: Passive Report and CLI Command

**Files:**
- Create: `rytm_randomizer/reports/manual_validation_kit.py`
- Modify: `rytm_randomizer/cli.py`

- [x] **Step 1: Implement report DTOs and builder**

Add `ManualValidationKitReport`, `build_manual_validation_kit_report`, and phase validation. Unknown phases raise `ValueError("Unknown manual validation phase: <phase>")`.

- [x] **Step 2: Implement text and JSON output**

Add `format_manual_validation_kit_report` and `to_manual_validation_kit_json`. Text must include validation phases, steps, evidence prompts, stop conditions, passive commands, manual commands, blocked actions, safety, and the passive footer.

- [x] **Step 3: Implement CLI parser/handler**

Register `MANUAL_VALIDATION_KIT_CLI_COMMAND` with:

```bash
manual-validation-kit-report [--phase <slug>] [--json]
```

`--help` is handled by `help_text.py`; the parser should accept no other flags.

- [x] **Step 4: Wire lazy CLI dispatch**

Add to `lazy_commands`:

```python
"manual-validation-kit-report": (
    "rytm_randomizer.reports.manual_validation_kit",
    "MANUAL_VALIDATION_KIT_CLI_COMMAND",
),
```

- [x] **Step 5: Run focused tests and confirm GREEN**

Run:

```bash
python -m pytest tests/test_manual_validation_kit_report.py -n 0
```

Expected: all tests in the new file pass.

## Task 4: Help and Docs

**Files:**
- Modify: `rytm_randomizer/help_text.py`
- Modify: `tests/fixtures/cli_help_expected.txt`
- Modify: `docs/CLI_REFERENCE.md`
- Modify: `docs/MANUAL_HARDWARE_VALIDATION.md`

- [x] **Step 1: Add top-level and command-specific help**

Add `manual-validation-kit-report [--phase <slug>] [--json]` to top-level help and a command-specific help block that repeats the passive safety boundaries.

- [x] **Step 2: Refresh byte-exact help fixture**

Run:

```bash
python -m rytm_randomizer.cli --help > tests/fixtures/cli_help_expected.txt
```

Expected: only `tests/fixtures/cli_help_expected.txt` changes among fixtures.

- [x] **Step 3: Document CLI reference and manual validation entry point**

Add the command to `docs/CLI_REFERENCE.md` and add a short "Passive validation kit" section to `docs/MANUAL_HARDWARE_VALIDATION.md`.

- [x] **Step 4: Run focused CLI/help tests**

Run:

```bash
python -m pytest tests/test_manual_validation_kit_report.py tests/test_cli.py::test_cli_help_matches_fixture tests/test_real_midi_passive_cli_safety.py -n 0
```

Expected: all selected tests pass and the passive sweep includes the new command.

## Task 5: Verification and Publication

**Files:**
- All intended files only

- [x] **Step 1: Run focused and architecture verification**

Run:

```bash
python -m pytest tests/test_manual_validation_kit_report.py -n 0
python -m pytest tests/test_real_midi_passive_cli_safety.py -n 0
python -m pytest tests/architecture/ -q
```

Expected: all pass.

- [x] **Step 2: Run broad verification**

Run:

```bash
python -m pytest -m fast
python -m pytest
python -m pytest --cov=rytm_randomizer --cov-branch --cov-report=term-missing
python -m ruff check .
python -m black --check --target-version=py311 .
python -m isort --profile black --check-only .
git diff --check
```

Expected: all pass. The broad status may still show unrelated parity/CRLF noise; do not stage it.

- [ ] **Step 3: Exact-stage intended files only**

Stage only:

```bash
git add docs/superpowers/specs/2026-05-27-manual-validation-kit-design.md
git add docs/superpowers/plans/2026-05-27-manual-validation-kit.md
git add rytm_randomizer/data/manual_validation.py
git add rytm_randomizer/reports/manual_validation_kit.py
git add rytm_randomizer/cli.py
git add rytm_randomizer/help_text.py
git add tests/test_manual_validation_kit_report.py
git add tests/fixtures/cli_help_expected.txt
git add docs/CLI_REFERENCE.md
git add docs/MANUAL_HARDWARE_VALIDATION.md
```

- [ ] **Step 4: Commit and open one clean-base PR**

Run:

```bash
git commit -m "feat: add passive manual validation kit"
git push -u origin codex/manual-validation-kit
gh pr create --base modularize-v1.34 --head codex/manual-validation-kit --title "feat: add passive manual validation kit" --body-file <pr-body-file>
```

Expected: one coherent PR against `modularize-v1.34`, independent of PR #135 and PR #136.
