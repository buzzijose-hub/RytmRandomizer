# Real MIDI Import And Port Safety Test Implementation Plan

## 1. Purpose

Define the tests-only implementation plan for real MIDI import and port safety.

This plan is the next step after accepting
`Docs/REAL_MIDI_IMPLEMENTATION_TEST_PLAN.md`.

This plan does not implement tests.

This plan does not add real MIDI code.

This plan does not add a real MIDI dependency.

This plan does not authorize opening ports, sending MIDI, adding active CLI
commands, dispatching commands, executing scenes, mutating hardware, or turning
hardware on.

## 2. Current Clean Baseline

Current branch:

- modularize-v1.34

Current HEAD before this slice:

- 17d1a0a Add real MIDI implementation test plan review

Current phase:

- Passive/Mock Foundation Phase
- project-level roadmap update accepted
- mock-first active boundary safety baseline accepted
- real MIDI boundary planning gate accepted
- real MIDI boundary plan accepted
- real MIDI implementation design/spec accepted
- real MIDI implementation test plan accepted
- tests-only implementation plan now being documented
- no real MIDI or hardware validation started

Hardware status:

- Analog Rytm MKII off
- Analog Four MKII off
- hardware not required

## 3. Implementation Scope

Future implementation must be tests-only.

The future test slice may add:

- `tests/test_real_midi_import_safety.py`
- `tests/test_real_midi_passive_cli_safety.py`
- closeout labels for those tests

The future test slice must not add:

- real MIDI modules
- mido dependency
- port provider implementation
- sender implementation
- active CLI commands
- runtime dispatch
- hardware behavior

## 4. Planned File Ownership

Future file ownership:

- `tests/test_real_midi_import_safety.py`
  - proves passive imports are quiet and do not import real MIDI libraries
  - proves passive/mock modules expose no port-opening or send-MIDI affordances
  - proves V1.34 reference remains untouched by test work
- `tests/test_real_midi_passive_cli_safety.py`
  - proves passive CLI commands do not expose active/real-MIDI command names
  - proves passive CLI source does not construct senders or evaluate active
    boundary requests
  - proves representative passive CLI commands run without importing mido
- `Scripts/closeout_check.ps1`
  - future update only after tests are added
  - must add explicit, non-duplicative labels

These files are not modified in this slice.

## 5. Future Closeout Labels

Future closeout labels should be:

- `=== Test: Real MIDI Import Safety ===`
- `=== Test: Real MIDI Passive CLI Safety ===`

Do not add duplicate entries for existing test files.

Do not remove existing closeout labels.

Do not rename existing closeout labels.

## 6. Future Test: Import Safety

Future file:

- `tests/test_real_midi_import_safety.py`

Future test helpers should follow existing subprocess patterns:

```python
from pathlib import Path
import subprocess
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def run_python(code):
    return subprocess.run(
        [sys.executable, "-c", code],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
```

Future import safety tests should include:

```python
def test_passive_imports_do_not_import_real_midi_libraries():
    code = """
import sys
import rytm_randomizer.cli
import rytm_randomizer.mock_midi
import rytm_randomizer.mock_message_mapper
import rytm_randomizer.mock_mapper_report
import rytm_randomizer.active_boundary
import rytm_randomizer.active_boundary_report
for name in ('mido', 'rtmidi', 'pythonrtmidi'):
    assert name not in sys.modules, name
"""
    result = run_python(code)

    assert result.returncode == 0
    assert result.stdout == ""
    assert result.stderr == ""
```

Future quiet-import tests should include:

```python
def test_passive_imports_print_nothing():
    code = """
import rytm_randomizer.cli
import rytm_randomizer.mock_midi
import rytm_randomizer.mock_message_mapper
import rytm_randomizer.mock_mapper_report
import rytm_randomizer.active_boundary
import rytm_randomizer.active_boundary_report
"""
    result = run_python(code)

    assert result.returncode == 0
    assert result.stdout == ""
    assert result.stderr == ""
```

## 7. Future Test: Source Has No Real MIDI Affordances

Future import-safety tests should inspect source for forbidden affordances:

```python
def test_passive_modules_expose_no_real_midi_affordances():
    module_paths = [
        PROJECT_ROOT / "rytm_randomizer" / "cli.py",
        PROJECT_ROOT / "rytm_randomizer" / "mock_midi.py",
        PROJECT_ROOT / "rytm_randomizer" / "mock_message_mapper.py",
        PROJECT_ROOT / "rytm_randomizer" / "mock_mapper_report.py",
        PROJECT_ROOT / "rytm_randomizer" / "active_boundary.py",
        PROJECT_ROOT / "rytm_randomizer" / "active_boundary_report.py",
    ]
    forbidden = (
        "import mido",
        "from mido",
        "open_output",
        "open_input",
        "open_midi_port",
        "send_midi",
        "MidiPortProvider",
        "RealMidiSender",
        "execute-command",
        "send-command",
        "hardware-test",
    )

    for path in module_paths:
        source = path.read_text(encoding="utf-8")
        for token in forbidden:
            assert token not in source, f"{token} found in {path}"
```

If a later accepted implementation introduces a real MIDI adapter, this test
must remain scoped to passive/mock modules only and must not scan the adapter
module unless the accepted plan says so.

## 8. Future Test: Passive CLI No Real MIDI Import

Future file:

- `tests/test_real_midi_passive_cli_safety.py`

Future test helpers should follow the existing `tests/test_cli.py` style:

```python
from pathlib import Path
import subprocess
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def run_cli_and_check_no_mido(*args):
    code = f"""
import runpy
import sys
sys.argv = ['-m', 'rytm_randomizer.cli', *{list(args)!r}]
runpy.run_module('rytm_randomizer.cli', run_name='__main__')
assert 'mido' not in sys.modules
assert 'rtmidi' not in sys.modules
assert 'pythonrtmidi' not in sys.modules
"""
    return subprocess.run(
        [sys.executable, "-c", code],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
```

Future passive CLI checks should include representative commands:

```python
def test_representative_passive_cli_commands_do_not_import_mido():
    commands = (
        ("--help",),
        ("report",),
        ("mock-mapper-report",),
        ("active-boundary-report",),
        ("preview-group-profile", "2"),
    )

    for command in commands:
        result = run_cli_and_check_no_mido(*command)
        assert result.returncode == 0, command
        assert "Traceback" not in result.stderr
```

These tests must not assert exact full CLI output because existing CLI fixture
tests already own output contracts.

## 9. Future Test: Passive CLI Source Separation

Future passive CLI safety tests should preserve source-level separation:

```python
def test_cli_source_does_not_construct_senders_or_evaluate_active_boundary():
    source = (PROJECT_ROOT / "rytm_randomizer" / "cli.py").read_text(
        encoding="utf-8"
    )

    forbidden = (
        "MockMidiSender(",
        "RealMidiSender(",
        "evaluate_mock_active_boundary",
        "open_output",
        "send_midi",
        "execute-command",
        "send-command",
        "hardware-test",
    )

    for token in forbidden:
        assert token not in source
```

This preserves the existing rule that passive CLI report commands may print
read-only summaries but must not evaluate or execute active boundary requests.

## 10. Future Test: Active Boundary Scope Stays Narrow

Future tests should preserve the current active boundary scope:

```python
def test_active_boundary_scope_remains_profile_2_only():
    from rytm_randomizer.active_boundary import (
        ActiveBoundaryRequest,
        evaluate_mock_active_boundary,
    )
    from rytm_randomizer.mock_midi import MockMidiSender

    accepted = evaluate_mock_active_boundary(
        ActiveBoundaryRequest(
            source_kind="group_profile",
            source_key="2",
            armed=True,
            dry_run_confirmed=True,
            target="mock",
        ),
        MockMidiSender(),
    )
    unsupported_3 = evaluate_mock_active_boundary(
        ActiveBoundaryRequest(
            source_kind="group_profile",
            source_key="3",
            armed=True,
            dry_run_confirmed=True,
            target="mock",
        ),
        MockMidiSender(),
    )
    unsupported_4 = evaluate_mock_active_boundary(
        ActiveBoundaryRequest(
            source_kind="group_profile",
            source_key="4",
            armed=True,
            dry_run_confirmed=True,
            target="mock",
        ),
        MockMidiSender(),
    )

    assert accepted.accepted is True
    assert unsupported_3.accepted is False
    assert unsupported_3.emitted_messages == ()
    assert unsupported_4.accepted is False
    assert unsupported_4.emitted_messages == ()
```

If this duplicates existing active boundary tests, the future implementation
may keep the assertion in `tests/test_active_boundary.py` instead and document
that no new duplicate test was needed.

## 11. Future Closeout Update

Future closeout update should add these sections only after tests exist:

```powershell
"" | Add-Content $summary
"=== Test: Real MIDI Import Safety ===" | Add-Content $summary
& $pythonExe @pythonArgs .\tests\test_real_midi_import_safety.py 2>&1 | Tee-Object -FilePath "$logDir\latest_test_real_midi_import_safety.log" | Add-Content $summary

"" | Add-Content $summary
"=== Test: Real MIDI Passive CLI Safety ===" | Add-Content $summary
& $pythonExe @pythonArgs .\tests\test_real_midi_passive_cli_safety.py 2>&1 | Tee-Object -FilePath "$logDir\latest_test_real_midi_passive_cli_safety.log" | Add-Content $summary
```

Do not update closeout before creating the accepted test files.

Do not add closeout labels for tests that do not exist.

## 12. Future Verification Commands

Future implementation must run:

```powershell
powershell -ExecutionPolicy Bypass -File .\Scripts\closeout_check.ps1
git diff -- rytm_hybrid_randomizer_v134.py
git status --short
```

Expected result:

- closeout complete
- V1.34 reference diff empty
- git status clean after commit

## 13. Future Commit Boundary

The future tests-only implementation commit should include only:

- `tests/test_real_midi_import_safety.py`
- `tests/test_real_midi_passive_cli_safety.py`
- `Scripts/closeout_check.ps1`

Recommended future commit message:

- `Add real MIDI import and port safety tests`

Do not include runtime modules in that commit.

Do not include documentation checkpoint updates in that commit unless the user
explicitly asks to combine them.

## 14. Safety Invariants

The future tests-only implementation must preserve:

- no real MIDI
- no mido
- no MIDI port opening
- no MIDI sending
- no hardware detection
- no hardware send
- no active CLI command
- no active execution
- no passive CLI active-boundary evaluation
- no passive CLI construction of `MockMidiSender`
- no dispatch
- no command execution
- no scene execution
- no hardware behavior
- no hardware mutation
- no SysEx
- no GUI/capture
- no Analog Four support
- no Pads 5-12 support
- no machine/profile expansion
- no profile `"4"` implementation
- no profile `"3"` active-boundary support
- no hardware validation

## 15. Stop Conditions

Stop immediately if future implementation would require:

- importing mido
- adding a real MIDI dependency
- opening a port
- sending MIDI
- adding active CLI commands
- changing runtime dispatch
- changing active-boundary candidate scope
- implementing profile `"4"`
- adding profile `"3"` active-boundary support
- editing `rytm_hybrid_randomizer_v134.py`
- turning on hardware

## 16. Next Review Gate

Before any tests are implemented, this plan should be reviewed and accepted.

Safe next options:

- review and accept this tests-only implementation plan
- pause at this clean planning checkpoint
- return to passive/project documentation

No tests or implementation are added in this slice.
