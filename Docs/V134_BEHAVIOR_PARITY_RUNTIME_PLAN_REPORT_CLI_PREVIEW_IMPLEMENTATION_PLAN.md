# V1.34 Behavior Parity Runtime Plan Report CLI Preview Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a passive `runtime-plan-report` CLI preview that prints the existing read-only runtime plan report without adding execution, MIDI, ports, active behavior, or hardware behavior.

**Architecture:** Reuse `format_runtime_plan_report()` from `rytm_randomizer/runtime_plan_report.py`. Wire it into `rytm_randomizer/cli.py` using the same passive report pattern as `mock-mapper-report`, with fixture-backed tests in `tests/test_cli.py`.

**Tech Stack:** Python standard library, existing passive CLI module, existing fixture-based CLI tests, existing PowerShell closeout script.

---

## 1. Purpose

Document the future implementation steps for the accepted runtime plan report
CLI preview design.

This is a documentation-only implementation plan.

It does not implement the CLI command.

It does not add tests, fixtures, closeout script changes, CLI changes, CLI
execution wiring, runtime execution, dispatch, command execution, MIDI, ports,
package metadata changes, active behavior, or hardware behavior.

## 2. Current Clean Baseline

Current branch:

- `modularize-v1.34`

Current HEAD before this implementation-plan slice:

- `e193470 Add runtime plan report CLI preview design review`

Current phase:

- Passive/Mock Foundation Phase
- behavior-parity implementation phase
- read-only runtime plan report implemented and closeout-covered
- runtime plan report CLI preview design accepted
- runtime plan report CLI preview implementation plan now being documented

Hardware status:

- Analog Rytm MKII off
- Analog Four MKII off
- hardware not required

## 3. Accepted Inputs

Accepted design review:

- `Docs/V134_BEHAVIOR_PARITY_RUNTIME_PLAN_REPORT_CLI_PREVIEW_DESIGN_REVIEW.md`

Accepted design:

- `Docs/V134_BEHAVIOR_PARITY_RUNTIME_PLAN_REPORT_CLI_PREVIEW_DESIGN.md`

Accepted design review milestone:

- `e193470 Add runtime plan report CLI preview design review`

Accepted future command:

- `python -m rytm_randomizer.cli runtime-plan-report`
- `python -m rytm_randomizer.cli runtime-plan-report --help`

## 4. Future File Scope

Future implementation files, only after this plan is separately reviewed and
accepted:

- Modify: `rytm_randomizer/cli.py`
- Modify: `tests/test_cli.py`
- Modify: `tests/fixtures/cli_help_expected.txt`
- Create: `tests/fixtures/cli_runtime_plan_report_help_expected.txt`
- Create: `tests/fixtures/cli_runtime_plan_report_expected.txt`

Files that should not be edited for the implementation:

- `rytm_hybrid_randomizer_v134.py`
- `Scripts/closeout_check.ps1`
- `rytm_randomizer/runtime_plan_report.py`
- runtime execution/dispatch logic
- active CLI command code
- package metadata files
- MIDI adapter code
- hardware-facing code

`Scripts/closeout_check.ps1` should not need changes because `tests/test_cli.py`
is already included in closeout.

## 5. Existing Runtime Report Output

The future `runtime-plan-report` command should print exactly the existing
formatted runtime plan report:

```text
RytmRandomizer Runtime Plan Report
Runtime Plan Mode:
- mock_only: True
- metadata_only: True
- blocked_by_default: True
Supported Planning Inputs:
- group_profile:2 -> Pad 1 / My BD Hard (execution_not_implemented)
- group_profile:3 -> Pad 2 / My BD Classic (execution_not_implemented)
Parked Planning Inputs:
- group_profile:4 -> Pad 1 / My BD Acoustic (profile_4_parked)
Unsupported Planning Inputs:
- group_profile:unknown -> unknown (unsupported_key)
- scene:S1A -> Rolling Light (unsupported_source_kind)
Runtime Plan Safety:
- would_execute: False
- mock_only: True
- sends_real_midi: False
- ports_allowed: False
- hardware_required: False
- runtime_execution: absent
- cli_execution_wiring: absent
- dispatch: absent
Source: rytm_randomizer.runtime_plan
In-memory only: True
```

## 6. Task 1: Add Future Fixtures

**Files:**

- Modify: `tests/fixtures/cli_help_expected.txt`
- Create: `tests/fixtures/cli_runtime_plan_report_help_expected.txt`
- Create: `tests/fixtures/cli_runtime_plan_report_expected.txt`

- [ ] **Step 1: Update top-level help fixture**

Add this usage line to `tests/fixtures/cli_help_expected.txt` near the other
report commands:

```text
  python -m rytm_randomizer.cli runtime-plan-report
```

Add this command listing near `mock-mapper-report`:

```text
  runtime-plan-report
                     Print the read-only runtime plan report.
```

- [ ] **Step 2: Create command help fixture**

Create `tests/fixtures/cli_runtime_plan_report_help_expected.txt`:

```text
RytmRandomizer passive CLI: runtime-plan-report

Usage:
  python -m rytm_randomizer.cli runtime-plan-report
  python -m rytm_randomizer.cli runtime-plan-report --help

Behavior:
  Prints the deterministic read-only runtime plan report to stdout.

Safety:
  passive/read-only
  mock-only
  no MIDI sending
  no port opening
  no runtime execution
  no command execution
  no dispatch
  no hardware mutation
  no hardware required
```

- [ ] **Step 3: Create output fixture**

Create `tests/fixtures/cli_runtime_plan_report_expected.txt`:

```text
RytmRandomizer Runtime Plan Report
Runtime Plan Mode:
- mock_only: True
- metadata_only: True
- blocked_by_default: True
Supported Planning Inputs:
- group_profile:2 -> Pad 1 / My BD Hard (execution_not_implemented)
- group_profile:3 -> Pad 2 / My BD Classic (execution_not_implemented)
Parked Planning Inputs:
- group_profile:4 -> Pad 1 / My BD Acoustic (profile_4_parked)
Unsupported Planning Inputs:
- group_profile:unknown -> unknown (unsupported_key)
- scene:S1A -> Rolling Light (unsupported_source_kind)
Runtime Plan Safety:
- would_execute: False
- mock_only: True
- sends_real_midi: False
- ports_allowed: False
- hardware_required: False
- runtime_execution: absent
- cli_execution_wiring: absent
- dispatch: absent
Source: rytm_randomizer.runtime_plan
In-memory only: True
```

## 7. Task 2: Add Failing Future CLI Tests

**Files:**

- Modify: `tests/test_cli.py`

- [ ] **Step 1: Update the local expected `USAGE` string**

```python
USAGE = (
    "Usage: python -m rytm_randomizer.cli [--help] | report | "
    "mock-mapper-report | runtime-plan-report | active-boundary-report | "
    "anchor-profile-report | behavior-parity-report | inspect-command <key> | "
    "inspect-scene <key> | inspect-group-profile <key> | list-commands | "
    "list-scenes | list-group-profiles | search-commands <query> | "
    "search-scenes <query> | search-group-profiles <query> | "
    "preview-command <key> | preview-scene <key> | preview-group-profile <key>"
)
```

- [ ] **Step 2: Add help fixture test**

```python
def test_runtime_plan_report_help_exits_zero_and_matches_fixture():
    result = run_cli("runtime-plan-report", "--help")

    assert result.returncode == 0
    assert normalize_newlines(result.stdout) == fixture_text(
        "cli_runtime_plan_report_help_expected.txt"
    )
    assert result.stderr == ""
```

- [ ] **Step 3: Add output fixture test**

```python
def test_runtime_plan_report_command_exits_zero_and_matches_fixture():
    result = run_cli("runtime-plan-report")

    assert result.returncode == 0
    assert normalize_newlines(result.stdout) == fixture_text(
        "cli_runtime_plan_report_expected.txt"
    )
    assert result.stderr == ""
```

- [ ] **Step 4: Add deterministic output test**

```python
def test_runtime_plan_report_command_is_deterministic():
    first = run_cli("runtime-plan-report")
    second = run_cli("runtime-plan-report")

    assert first.returncode == 0
    assert second.returncode == 0
    assert normalize_newlines(first.stdout) == normalize_newlines(second.stdout)
```

- [ ] **Step 5: Add no-real-MIDI import test**

```python
def test_runtime_plan_report_command_imports_no_real_midi_libraries():
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import sys\n"
                "from contextlib import redirect_stdout\n"
                "from io import StringIO\n"
                "from rytm_randomizer.cli import main\n"
                "with redirect_stdout(StringIO()):\n"
                "    code = main(['runtime-plan-report'])\n"
                "assert code == 0\n"
                "assert 'mido' not in sys.modules\n"
                "assert 'rtmidi' not in sys.modules\n"
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

- [ ] **Step 6: Add unknown argument safe-failure test**

```python
def test_unknown_runtime_plan_report_arguments_fail_safely():
    result = run_cli("runtime-plan-report", "--mutate")

    assert result.returncode == 2
    assert result.stdout == ""
    assert normalize_newlines(result.stderr) == USAGE
```

- [ ] **Step 7: Add boundary output test**

```python
def test_runtime_plan_report_exposes_no_active_behavior_or_support_expansion():
    result = run_cli("runtime-plan-report")
    output = normalize_newlines(result.stdout)

    assert result.returncode == 0
    assert "Supported Planning Inputs:" in output
    assert "- group_profile:2 -> Pad 1 / My BD Hard" in output
    assert "- group_profile:3 -> Pad 2 / My BD Classic" in output
    assert "Parked Planning Inputs:" in output
    assert "- group_profile:4 -> Pad 1 / My BD Acoustic" in output
    assert "- would_execute: False" in output
    assert "- mock_only: True" in output
    assert "- sends_real_midi: False" in output
    assert "- ports_allowed: False" in output
    assert "- hardware_required: False" in output
    assert "- runtime_execution: absent" in output
    assert "- cli_execution_wiring: absent" in output
    assert "- dispatch: absent" in output
    assert "execute-command" not in output
    assert "send-command" not in output
    assert "hardware-test" not in output
```

- [ ] **Step 8: Add manual runner calls**

Add these calls to the manual runner at the bottom of `tests/test_cli.py`:

```python
    test_runtime_plan_report_help_exits_zero_and_matches_fixture()
    test_runtime_plan_report_command_exits_zero_and_matches_fixture()
    test_runtime_plan_report_command_is_deterministic()
    test_runtime_plan_report_command_imports_no_real_midi_libraries()
    test_unknown_runtime_plan_report_arguments_fail_safely()
    test_runtime_plan_report_exposes_no_active_behavior_or_support_expansion()
```

- [ ] **Step 9: Verify tests fail before implementation**

Run:

```powershell
python .\tests\test_cli.py
```

Expected result:

- fails because `runtime-plan-report` is not implemented yet

## 8. Task 3: Add Minimal Passive CLI Wiring

**Files:**

- Modify: `rytm_randomizer/cli.py`

- [ ] **Step 1: Import existing formatter**

```python
from .runtime_plan_report import format_runtime_plan_report
```

- [ ] **Step 2: Add `runtime-plan-report` to `USAGE`**

```python
USAGE = (
    "Usage: python -m rytm_randomizer.cli [--help] | report | "
    "mock-mapper-report | runtime-plan-report | active-boundary-report | "
    "anchor-profile-report | behavior-parity-report | inspect-command <key> | "
    "inspect-scene <key> | inspect-group-profile <key> | list-commands | "
    "list-scenes | list-group-profiles | search-commands <query> | "
    "search-scenes <query> | search-group-profiles <query> | "
    "preview-command <key> | preview-scene <key> | preview-group-profile <key>"
)
```

- [ ] **Step 3: Add command to top-level help**

Add:

```text
  python -m rytm_randomizer.cli runtime-plan-report
```

and:

```text
  runtime-plan-report
                     Print the read-only runtime plan report.
```

- [ ] **Step 4: Add help constant**

```python
RUNTIME_PLAN_REPORT_HELP = """RytmRandomizer passive CLI: runtime-plan-report

Usage:
  python -m rytm_randomizer.cli runtime-plan-report
  python -m rytm_randomizer.cli runtime-plan-report --help

Behavior:
  Prints the deterministic read-only runtime plan report to stdout.

Safety:
  passive/read-only
  mock-only
  no MIDI sending
  no port opening
  no runtime execution
  no command execution
  no dispatch
  no hardware mutation
  no hardware required"""
```

- [ ] **Step 5: Add help dispatch**

```python
    if args == ["runtime-plan-report", "--help"]:
        sys.stdout.write(f"{RUNTIME_PLAN_REPORT_HELP}\n")
        return 0
```

- [ ] **Step 6: Add command dispatch**

```python
    if args == ["runtime-plan-report"]:
        sys.stdout.write("\n".join(format_runtime_plan_report()))
        sys.stdout.write("\n")
        return 0
```

Do not call runtime execution.

Do not create a sender.

Do not open ports.

Do not add active command names.

## 9. Task 4: Verify Future Implementation

**Files:**

- No additional file edits expected.

- [ ] **Step 1: Run focused CLI tests**

```powershell
python .\tests\test_cli.py
```

Expected result:

- exits `0`

- [ ] **Step 2: Run manual CLI checks**

```powershell
python -m rytm_randomizer.cli --help
python -m rytm_randomizer.cli runtime-plan-report --help
python -m rytm_randomizer.cli runtime-plan-report
```

Expected result:

- top-level help lists `runtime-plan-report`
- command help shows passive/read-only safety
- report output matches the existing runtime plan report

- [ ] **Step 3: Run full closeout**

```powershell
powershell -ExecutionPolicy Bypass -File .\Scripts\closeout_check.ps1
```

Expected result:

- closeout completes
- no Runtime Plan Report regression
- no Passive CLI regression

- [ ] **Step 4: Run protected diffs**

```powershell
git diff -- rytm_hybrid_randomizer_v134.py
git diff -- pyproject.toml requirements.txt setup.py setup.cfg
git status --short
```

Expected result:

- V1.34 reference diff is empty
- package metadata diff is empty
- git status shows only intended implementation files before commit

## 10. Future Commit Scope

Expected future implementation commit files:

- `rytm_randomizer/cli.py`
- `tests/test_cli.py`
- `tests/fixtures/cli_help_expected.txt`
- `tests/fixtures/cli_runtime_plan_report_help_expected.txt`
- `tests/fixtures/cli_runtime_plan_report_expected.txt`

Recommended future implementation commit message:

- `Add runtime plan report CLI preview`

## 11. Confirmed Non-Goals

This implementation plan does not authorize:

- implementation in this slice
- tests in this slice
- fixtures in this slice
- closeout script changes in this slice
- CLI changes in this slice
- active CLI commands
- CLI execution wiring
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
- runtime mutation
- profile `4` active-boundary support
- fourth runtime-adjacent candidate
- Analog Four support
- Pads 5-12 support
- SysEx
- GUI/capture
- package metadata changes
- hardware behavior

## 12. Safe Next Options

Safe next options:

- docs-only review/acceptance gate for this implementation plan
- pause at this clean implementation-plan checkpoint
- implement the runtime plan report CLI preview only after review

## 13. Recommendation

Recommended next task:

- docs-only review/acceptance gate for this implementation plan

Do not implement the CLI preview until that review is accepted.

Do not add real MIDI.

Do not open ports.

Do not add active CLI commands.

Do not turn on hardware.

## 14. Decision

The runtime plan report CLI preview implementation plan is documented.

The plan does not authorize implementation by itself.

Hardware remains off.

No implementation in this slice.
