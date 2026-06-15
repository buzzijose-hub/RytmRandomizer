# Controller Brain Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a passive E16/OXI-style controller-brain catalog and report so a 16-encoder surface can be mapped to RytmRandomizer musical intent rather than raw CCs.

**Architecture:** Static controller mapping facts live in `rytm_randomizer/data/` as frozen dataclasses and immutable catalogs. A passive report in `rytm_randomizer/reports/` projects that catalog into text/JSON and a lazy CLI command. No active controller input, MIDI send, WebSocket dispatch, or hardware behavior changes land in this slice.

**Tech Stack:** Python 3.11 stdlib, frozen dataclasses, `MappingProxyType`, existing passive CLI registry, `reports/formatter.py`, pytest.

---

## File Structure

- Create `rytm_randomizer/data/controller_mapping_profiles.py`
  - Owns the generic 16-encoder controller profile and immutable catalog.
- Modify `rytm_randomizer/data/__init__.py`
  - Re-export only uppercase constants from the new data module.
- Create `rytm_randomizer/reports/controller_mapping_profile_catalog.py`
  - Builds text/JSON passive controller-brain report.
- Modify `rytm_randomizer/cli.py`
  - Add a lazy CLI registration entry for `controller-brain-mapping-report`.
- Create `tests/test_controller_mapping_profiles.py`
  - Tests the data catalog shape and safety contract.
- Create `tests/test_controller_mapping_profile_catalog_report.py`
  - Tests report text/JSON/CLI behavior.
- Modify `README.md`
  - Mention the new passive controller-brain command in the passive CLI section.
- Modify `docs/CLI_REFERENCE.md`
  - Document the command and its safety boundary.
- Modify `docs/STATUS.md`
  - Add a current status entry.
- Modify architecture docs/diagrams if needed for the new passive report/CLI surface.

## Task 1: Data Catalog

**Files:**
- Create: `rytm_randomizer/data/controller_mapping_profiles.py`
- Modify: `rytm_randomizer/data/__init__.py`
- Test: `tests/test_controller_mapping_profiles.py`

- [ ] **Step 1: Write the failing catalog tests**

```python
def test_default_controller_profile_has_16_slot_pages() -> None:
    from rytm_randomizer.data.controller_mapping_profiles import (
        CONTROLLER_ENCODER_COUNT,
        CONTROLLER_MAPPING_PROFILES,
        DEFAULT_CONTROLLER_MAPPING_PROFILE,
    )

    profile = CONTROLLER_MAPPING_PROFILES[DEFAULT_CONTROLLER_MAPPING_PROFILE]

    assert CONTROLLER_ENCODER_COUNT == 16
    assert profile.controller_family == "generic-16-encoder"
    assert [page.key for page in profile.pages] == [
        "global-brain",
        "rytm-pads-1-4",
        "rytm-pads-5-8",
        "rytm-pads-9-12",
        "analog-four-tracks",
        "style-crates-queue",
        "snapshot-recovery-journal",
    ]
    for page in profile.pages:
        assert [control.slot for control in page.controls] == list(range(1, 17))


def test_controller_profile_is_intent_based_and_device_aware() -> None:
    from rytm_randomizer.data.controller_mapping_profiles import (
        CONTROLLER_MAPPING_PROFILES,
        DEFAULT_CONTROLLER_MAPPING_PROFILE,
    )

    profile = CONTROLLER_MAPPING_PROFILES[DEFAULT_CONTROLLER_MAPPING_PROFILE]
    controls = [control for page in profile.pages for control in page.controls]

    assert {control.target_device for control in controls} >= {
        "analog_rytm_mk2",
        "analog_four_mk2",
        "style_queue",
        "snapshot_recovery",
    }
    assert {control.target_scope for control in controls} >= {
        "rytm_pad_6",
        "rytm_pad_12",
        "a4_track_1",
        "queue",
        "journal",
    }
    assert all(control.intent_key for control in controls)
    assert all("cc" not in control.action.lower() for control in controls)


def test_controller_profile_blocks_active_hardware_actions() -> None:
    from rytm_randomizer.data.controller_mapping_profiles import (
        CONTROLLER_MAPPING_PROFILES,
        DEFAULT_CONTROLLER_MAPPING_PROFILE,
    )

    profile = CONTROLLER_MAPPING_PROFILES[DEFAULT_CONTROLLER_MAPPING_PROFILE]

    assert "open MIDI controller input" in profile.blocked_active_actions
    assert "send hardware MIDI" in profile.blocked_active_actions
    assert "dispatch Cockpit WebSocket commands" in profile.blocked_active_actions
```

- [ ] **Step 2: Run catalog tests and verify they fail**

Run: `python -m pytest tests/test_controller_mapping_profiles.py -n 0 -q`

Expected: import failure for missing `rytm_randomizer.data.controller_mapping_profiles`.

- [ ] **Step 3: Implement the data module**

Create frozen dataclasses for `ControllerMappingControlSpec`, `ControllerMappingPageSpec`, and `ControllerMappingProfileSpec`. Add immutable constants:

```python
CONTROLLER_ENCODER_COUNT: Final[int] = 16
DEFAULT_CONTROLLER_MAPPING_PROFILE: Final[str] = "generic-16-encoder-performance"
CONTROLLER_MAPPING_PROFILES: Final[Mapping[str, ControllerMappingProfileSpec]] = MappingProxyType(...)
```

Each page must contain exactly 16 controls. Keep helper functions private and data-only. Use no imports outside stdlib.

- [ ] **Step 4: Re-export uppercase constants**

Import and add these names in `rytm_randomizer/data/__init__.py`:

```python
CONTROLLER_ENCODER_COUNT
CONTROLLER_MAPPING_PROFILES
DEFAULT_CONTROLLER_MAPPING_PROFILE
```

- [ ] **Step 5: Run catalog tests and verify they pass**

Run: `python -m pytest tests/test_controller_mapping_profiles.py -n 0 -q`

Expected: all tests pass.

## Task 2: Passive Report And CLI

**Files:**
- Create: `rytm_randomizer/reports/controller_mapping_profile_catalog.py`
- Modify: `rytm_randomizer/cli.py`
- Test: `tests/test_controller_mapping_profile_catalog_report.py`

- [ ] **Step 1: Write failing report tests**

```python
def test_controller_mapping_report_text_mentions_pages_and_safety() -> None:
    from rytm_randomizer.reports.controller_mapping_profile_catalog import (
        build_controller_mapping_profile_report,
        format_controller_mapping_profile_report,
    )

    report = build_controller_mapping_profile_report()
    text = "\n".join(format_controller_mapping_profile_report(report))

    assert report.title == "RytmRandomizer passive controller brain mapping report"
    assert "Controller profile: generic-16-encoder-performance" in text
    assert "Page 1: Global Brain" in text
    assert "Page 4: Rytm Pads 9-12" in text
    assert "open MIDI controller input" in text
    assert "Source: rytm_randomizer.reports.controller_mapping_profile_catalog" in text


def test_controller_mapping_report_json_is_deterministic() -> None:
    from rytm_randomizer.reports.controller_mapping_profile_catalog import (
        build_controller_mapping_profile_payload,
    )

    payload = build_controller_mapping_profile_payload()

    assert payload["profile_key"] == "generic-16-encoder-performance"
    assert len(payload["pages"]) == 7
    assert payload["pages"][0]["controls"][0]["intent_key"] == "global.preview_depth"
    assert payload["pages"][3]["controls"][-1]["target_scope"] == "rytm_pad_12"
    assert payload["safety"]["sends_midi"] is False
    assert payload["blocked_active_actions"]


def test_controller_mapping_report_cli_supports_text_and_json(capsys) -> None:
    import json
    import pytest
    from rytm_randomizer.reports.controller_mapping_profile_catalog import (
        CONTROLLER_MAPPING_PROFILE_CATALOG_CLI_COMMAND,
    )

    assert CONTROLLER_MAPPING_PROFILE_CATALOG_CLI_COMMAND.handler() == 0
    text_output = capsys.readouterr().out
    assert "RytmRandomizer passive controller brain mapping report" in text_output

    assert CONTROLLER_MAPPING_PROFILE_CATALOG_CLI_COMMAND.handler(json_output=True) == 0
    json_output = capsys.readouterr().out
    assert json.loads(json_output)["profile_key"] == "generic-16-encoder-performance"

    with pytest.raises(ValueError, match="accepts only optional --json"):
        CONTROLLER_MAPPING_PROFILE_CATALOG_CLI_COMMAND.args_parser(["extra"])
```

- [ ] **Step 2: Run report tests and verify they fail**

Run: `python -m pytest tests/test_controller_mapping_profile_catalog_report.py -n 0 -q`

Expected: import failure for missing report module.

- [ ] **Step 3: Implement the passive report**

Use `PassiveReportHeader`, `passive_report_lines`, and
`make_passive_report_command`. The report should expose:

- `build_controller_mapping_profile_report()`
- `format_controller_mapping_profile_report(report)`
- `build_controller_mapping_profile_payload()`
- `CONTROLLER_MAPPING_PROFILE_CATALOG_CLI_COMMAND`

- [ ] **Step 4: Wire lazy CLI registration**

Add this entry to `rytm_randomizer/cli.py`:

```python
"controller-brain-mapping-report": (
    "rytm_randomizer.reports.controller_mapping_profile_catalog",
    "CONTROLLER_MAPPING_PROFILE_CATALOG_CLI_COMMAND",
),
```

- [ ] **Step 5: Run report tests and verify they pass**

Run: `python -m pytest tests/test_controller_mapping_profile_catalog_report.py -n 0 -q`

Expected: all tests pass.

## Task 3: Docs And Verification

**Files:**
- Modify: `README.md`
- Modify: `docs/CLI_REFERENCE.md`
- Modify: `docs/STATUS.md`
- Modify: `docs/ARCHITECTURE.md` and `docs/ARCHITECTURE_DIAGRAMS.md` if the architecture-review check requires them.

- [ ] **Step 1: Document the command**

Add `controller-brain-mapping-report [--json]` to the passive CLI docs and explain that it is no-port/no-send/no-controller-input.

- [ ] **Step 2: Run focused tests**

Run:

```powershell
python -m pytest tests/test_controller_mapping_profiles.py tests/test_controller_mapping_profile_catalog_report.py -n 0 -q
```

- [ ] **Step 3: Run passive CLI safety and architecture gates**

Run:

```powershell
python -m pytest tests/test_real_midi_passive_cli_safety.py -n 0 -q
python -m pytest tests/architecture/ -q
```

- [ ] **Step 4: Run lint**

Run:

```powershell
python -m ruff check .
python -m black --check --target-version=py311 .
python -m isort --profile black --check-only .
```

- [ ] **Step 5: Commit**

Stage only intended files and commit:

```powershell
git add rytm_randomizer/data/controller_mapping_profiles.py `
  rytm_randomizer/data/__init__.py `
  rytm_randomizer/reports/controller_mapping_profile_catalog.py `
  rytm_randomizer/cli.py `
  tests/test_controller_mapping_profiles.py `
  tests/test_controller_mapping_profile_catalog_report.py `
  README.md docs/CLI_REFERENCE.md docs/STATUS.md `
  docs/superpowers/specs/2026-06-15-controller-brain-design.md `
  docs/superpowers/plans/2026-06-15-controller-brain-bundle.md
git commit -m "feat: add passive controller brain mapping"
```

## Conformance Notes

- Gate 1: new/touched behavior gets focused tests; full coverage command runs before PR.
- Gate 2: no V1.34 parity fixtures touched.
- Gate 5: README, CLI reference, status, and relevant architecture docs are updated.
- Gate 9: no new top-level modules; data and reports use existing subpackages.
- Gate 12: new module constants use `Final`.
- Gate 17: reuses data-layer fact table pattern, passive report formatter, and CLI registry.
- Gate 18: new CLI/report surface is documented.
