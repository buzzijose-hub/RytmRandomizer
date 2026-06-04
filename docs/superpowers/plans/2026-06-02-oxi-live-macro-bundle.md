# OXI Live Macro Bundle Implementation Plan

> Status: proposed (branch `codex/next-oxi-live-macro-spec`)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add the next OXI-style live macro bundle after PR #149: named Rytm live macros, passive macro catalog/readiness output, A4 candidate-only runway, and Cockpit-ready handoff data.

**Architecture:** Keep active Rytm behavior inside the existing all-12-pad snapshot shell and its injected sender boundary. Move reusable macro definitions into a small `engines/` helper so the shell does not keep growing command-specific branches, then add passive reports for GUI/A4 handoff that open no ports and send no MIDI. Analog Four remains candidate-only in this bundle.

**Tech Stack:** Python 3.11+, frozen dataclasses, existing Rytm snapshot shell, existing A4 device/data surfaces, `MockMidiSender`, pytest, ruff, black, isort.

---

## Source Spec

Implement from `docs/superpowers/specs/2026-05-31-oxi-live-macro-bundle-design.md`.

## File Structure

- Create `rytm_randomizer/engines/analog_rytm_snapshot_macros.py`
  - Pure macro definition helpers for the snapshot shell.
  - Owns frozen macro spec dataclasses and the canonical macro catalog.
  - Imports only stdlib. It does not import `mido`, senders, `app.py`, `cli.py`, or the shell.
- Modify `rytm_randomizer/engines/analog_rytm_snapshot_shell.py`
  - Imports the macro catalog helper.
  - Applies named macro specs through existing guardrail mutation APIs.
  - Adds `macro NAME`, direct macro commands, `home`, and help/status text.
- Modify `tests/test_analog_rytm_snapshot_shell.py`
  - Covers named macro behavior, direct aliases, `macro NAME`, `home`, send safety, and existing `kit-core` preservation.
- Create `rytm_randomizer/reports/oxi_live_macro_catalog.py`
  - Passive report that emits macro cards and A4 candidate/deferred rows.
  - Outputs deterministic text and JSON-ready data.
- Modify `rytm_randomizer/reports/__init__.py`
  - Re-export `build_oxi_live_macro_catalog_report`,
    `format_oxi_live_macro_catalog_report`, and
    `build_oxi_live_macro_catalog_payload`.
- Modify `rytm_randomizer/cli.py`
  - Add one lazy command manifest entry for `oxi-live-macro-catalog-report`.
- Modify `rytm_randomizer/help_text.py`
  - Add concise passive-report help for the new command.
- Create `tests/test_oxi_live_macro_catalog_report.py`
  - Covers passive report output, JSON shape, Rytm macro cards, A4 candidate-only state, and blocked active actions.
- Modify `README.md`
  - Add the new macro command/report in the live snapshot shell area.
- Modify `docs/STATUS.md`
  - Record the shipped implementation after code lands.

## Macro Names

The first implementation covers these names:

- `kit-core`
- `hard-groove`
- `industrial`
- `dub-pressure`
- `transition`
- `home`

`drum-core` remains supported as the older focused four-pad macro.

## Task 1: Add Macro Catalog Unit Tests

**Files:**
- Create: `rytm_randomizer/engines/analog_rytm_snapshot_macros.py`
- Modify: `tests/test_analog_rytm_snapshot_shell.py`

- [ ] **Step 1: Write failing macro catalog tests**

Add these tests near the existing `kit-core` tests:

```python
def test_snapshot_shell_live_macro_catalog_contains_expected_names() -> None:
    from rytm_randomizer.engines.analog_rytm_snapshot_macros import (
        SNAPSHOT_LIVE_MACROS,
    )

    assert tuple(SNAPSHOT_LIVE_MACROS) == (
        "kit-core",
        "hard-groove",
        "industrial",
        "dub-pressure",
        "transition",
        "home",
    )


def test_snapshot_shell_live_macro_specs_are_passive_data() -> None:
    from rytm_randomizer.engines.analog_rytm_snapshot_macros import (
        SNAPSHOT_LIVE_MACROS,
    )

    hard_groove = SNAPSHOT_LIVE_MACROS["hard-groove"]

    assert hard_groove.name == "hard-groove"
    assert hard_groove.label == "Hard Groove"
    assert hard_groove.mode == "live"
    assert hard_groove.locked_pads == frozenset({1})
    assert hard_groove.recovery_action == "home"
    assert hard_groove.risk_label == "live-safe"
    assert hard_groove.pad_policies[5].lane_policies["filter"] == "off"
    assert hard_groove.pad_policies[5].lane_policies["lfo"] == "off"
    assert hard_groove.pad_policies[5].section_family_allowlists["AMP"] == frozenset(
        {"drive", "delay", "reverb"}
    )
```

- [ ] **Step 2: Run and verify red**

Run:

```powershell
python -m pytest tests\test_analog_rytm_snapshot_shell.py -k "live_macro_catalog" -n 0
```

Expected: fail with `ModuleNotFoundError` for `analog_rytm_snapshot_macros`.

- [ ] **Step 3: Create the macro helper module**

Create `rytm_randomizer/engines/analog_rytm_snapshot_macros.py`:

```python
from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Final, Literal, Mapping


MacroMode = Literal["live", "studio"]
MacroLane = Literal["tune", "noise", "fx", "filter", "amp", "lfo"]
MacroLanePolicy = Literal["off", "micro", "normal", "wide"]
MacroAmount = Literal["micro", "normal", "wide"]
MacroDensity = Literal["off", "low", "medium", "high", "full"]
MacroBias = Literal["neutral", "darker", "brighter", "tighter", "looser", "grittier"]
MacroRiskLabel = Literal["live-safe", "edge", "studio", "blocked"]


@dataclass(frozen=True)
class SnapshotMacroPadPolicy:
    amount: MacroAmount | None = None
    density: MacroDensity | None = None
    bias: MacroBias | None = None
    lane_policies: Mapping[MacroLane, MacroLanePolicy] = field(
        default_factory=lambda: MappingProxyType({})
    )
    section_family_allowlists: Mapping[str, frozenset[str]] = field(
        default_factory=lambda: MappingProxyType({})
    )


@dataclass(frozen=True)
class SnapshotLiveMacroSpec:
    name: str
    label: str
    mode: MacroMode
    lane_policies: Mapping[MacroLane, MacroLanePolicy]
    locked_pads: frozenset[int]
    pad_policies: Mapping[int, SnapshotMacroPadPolicy]
    recovery_action: str
    risk_label: MacroRiskLabel
    summary: str


_AMP_FX_FAMILIES: Final[frozenset[str]] = frozenset(("delay", "drive", "reverb"))


def _pad_policy(
    *,
    amount: MacroAmount | None = None,
    density: MacroDensity | None = None,
    bias: MacroBias | None = None,
    lanes: Mapping[MacroLane, MacroLanePolicy] | None = None,
    amp_fx_only: bool = False,
) -> SnapshotMacroPadPolicy:
    allowlists: Mapping[str, frozenset[str]]
    if amp_fx_only:
        allowlists = MappingProxyType({"AMP": _AMP_FX_FAMILIES})
    else:
        allowlists = MappingProxyType({})
    return SnapshotMacroPadPolicy(
        amount=amount,
        density=density,
        bias=bias,
        lane_policies=MappingProxyType(dict(lanes or {})),
        section_family_allowlists=allowlists,
    )


def _macro(
    *,
    name: str,
    label: str,
    lane_policies: Mapping[MacroLane, MacroLanePolicy],
    pad_policies: Mapping[int, SnapshotMacroPadPolicy],
    risk_label: MacroRiskLabel,
    summary: str,
) -> SnapshotLiveMacroSpec:
    return SnapshotLiveMacroSpec(
        name=name,
        label=label,
        mode="live",
        lane_policies=MappingProxyType(dict(lane_policies)),
        locked_pads=frozenset({1}),
        pad_policies=MappingProxyType(dict(pad_policies)),
        recovery_action="home",
        risk_label=risk_label,
        summary=summary,
    )


_BASE_LIVE_LANES: Final[Mapping[MacroLane, MacroLanePolicy]] = MappingProxyType(
    {"lfo": "off", "fx": "micro"}
)


SNAPSHOT_LIVE_MACROS: Final[Mapping[str, SnapshotLiveMacroSpec]] = MappingProxyType(
    {
        "kit-core": _macro(
            name="kit-core",
            label="Kit Core",
            lane_policies=_BASE_LIVE_LANES,
            risk_label="live-safe",
            summary="Full-kit live-safe discovery with Jose's pad 5-11 lane discipline.",
            pad_policies={
                2: _pad_policy(amount="wide", density="full", bias="looser"),
                3: _pad_policy(amount="wide", density="full", bias="grittier"),
                4: _pad_policy(amount="wide", density="full", bias="grittier"),
                5: _pad_policy(amount="normal", density="high", lanes={"filter": "off", "lfo": "off"}, amp_fx_only=True),
                6: _pad_policy(amount="wide", density="full", bias="tighter", lanes={"filter": "micro", "lfo": "off"}, amp_fx_only=True),
                7: _pad_policy(amount="wide", density="full", bias="tighter", lanes={"filter": "micro", "lfo": "off"}, amp_fx_only=True),
                8: _pad_policy(amount="wide", density="full", bias="tighter", lanes={"filter": "micro", "lfo": "off"}, amp_fx_only=True),
                9: _pad_policy(amount="normal", density="high", lanes={"filter": "off", "lfo": "off"}, amp_fx_only=True),
                10: _pad_policy(amount="normal", density="high", lanes={"filter": "off", "lfo": "off"}, amp_fx_only=True),
                11: _pad_policy(amount="normal", density="high", lanes={"filter": "off", "lfo": "off"}, amp_fx_only=True),
            },
        ),
        "hard-groove": _macro(
            name="hard-groove",
            label="Hard Groove",
            lane_policies=_BASE_LIVE_LANES,
            risk_label="live-safe",
            summary="Dry pressure macro for OXI patterns that already carry the groove.",
            pad_policies={
                2: _pad_policy(amount="normal", density="high", bias="tighter"),
                3: _pad_policy(amount="normal", density="high", bias="tighter"),
                4: _pad_policy(amount="normal", density="high", bias="grittier"),
                5: _pad_policy(amount="normal", density="high", bias="tighter", lanes={"filter": "off", "lfo": "off"}, amp_fx_only=True),
                6: _pad_policy(amount="wide", density="full", bias="tighter", lanes={"filter": "micro", "lfo": "off"}, amp_fx_only=True),
                7: _pad_policy(amount="wide", density="full", bias="tighter", lanes={"filter": "micro", "lfo": "off"}, amp_fx_only=True),
                8: _pad_policy(amount="wide", density="full", bias="tighter", lanes={"filter": "micro", "lfo": "off"}, amp_fx_only=True),
                9: _pad_policy(amount="normal", density="high", bias="brighter", lanes={"filter": "off", "lfo": "off"}, amp_fx_only=True),
                10: _pad_policy(amount="normal", density="high", bias="brighter", lanes={"filter": "off", "lfo": "off"}, amp_fx_only=True),
                11: _pad_policy(amount="normal", density="high", bias="brighter", lanes={"filter": "off", "lfo": "off"}, amp_fx_only=True),
                12: _pad_policy(amount="normal", density="medium", bias="neutral", amp_fx_only=True),
            },
        ),
        "industrial": _macro(
            name="industrial",
            label="Industrial",
            lane_policies=_BASE_LIVE_LANES,
            risk_label="edge",
            summary="Metallic pressure and controlled grit without releasing the kick anchor.",
            pad_policies={
                2: _pad_policy(amount="wide", density="full", bias="grittier"),
                3: _pad_policy(amount="wide", density="full", bias="grittier"),
                4: _pad_policy(amount="wide", density="full", bias="grittier"),
                5: _pad_policy(amount="normal", density="high", bias="grittier", lanes={"filter": "off", "lfo": "off"}, amp_fx_only=True),
                6: _pad_policy(amount="wide", density="full", bias="grittier", lanes={"filter": "micro", "lfo": "off"}, amp_fx_only=True),
                7: _pad_policy(amount="wide", density="full", bias="grittier", lanes={"filter": "micro", "lfo": "off"}, amp_fx_only=True),
                8: _pad_policy(amount="wide", density="full", bias="grittier", lanes={"filter": "micro", "lfo": "off"}, amp_fx_only=True),
                9: _pad_policy(amount="normal", density="high", bias="brighter", lanes={"filter": "off", "lfo": "off"}, amp_fx_only=True),
                10: _pad_policy(amount="normal", density="high", bias="brighter", lanes={"filter": "off", "lfo": "off"}, amp_fx_only=True),
                11: _pad_policy(amount="normal", density="high", bias="grittier", lanes={"filter": "off", "lfo": "off"}, amp_fx_only=True),
                12: _pad_policy(amount="wide", density="high", bias="grittier", amp_fx_only=True),
            },
        ),
        "dub-pressure": _macro(
            name="dub-pressure",
            label="Dub Pressure",
            lane_policies={"lfo": "off", "fx": "normal"},
            risk_label="live-safe",
            summary="Darker pressure with more delay/reverb influence and small filter motion.",
            pad_policies={
                2: _pad_policy(amount="normal", density="medium", bias="darker"),
                3: _pad_policy(amount="normal", density="medium", bias="looser"),
                4: _pad_policy(amount="normal", density="medium", bias="darker"),
                5: _pad_policy(amount="normal", density="medium", bias="darker", lanes={"filter": "off", "lfo": "off"}, amp_fx_only=True),
                6: _pad_policy(amount="normal", density="high", bias="looser", lanes={"filter": "micro", "lfo": "off"}, amp_fx_only=True),
                7: _pad_policy(amount="normal", density="high", bias="looser", lanes={"filter": "micro", "lfo": "off"}, amp_fx_only=True),
                8: _pad_policy(amount="normal", density="high", bias="looser", lanes={"filter": "micro", "lfo": "off"}, amp_fx_only=True),
                9: _pad_policy(amount="micro", density="medium", bias="darker", lanes={"filter": "off", "lfo": "off"}, amp_fx_only=True),
                10: _pad_policy(amount="micro", density="medium", bias="darker", lanes={"filter": "off", "lfo": "off"}, amp_fx_only=True),
                11: _pad_policy(amount="micro", density="medium", bias="darker", lanes={"filter": "off", "lfo": "off"}, amp_fx_only=True),
                12: _pad_policy(amount="normal", density="medium", bias="darker", amp_fx_only=True),
            },
        ),
        "transition": _macro(
            name="transition",
            label="Transition",
            lane_policies={"lfo": "micro", "fx": "normal"},
            risk_label="edge",
            summary="Set-section movement with obvious recovery through home.",
            pad_policies={
                2: _pad_policy(amount="wide", density="full", bias="looser"),
                3: _pad_policy(amount="wide", density="full", bias="grittier"),
                4: _pad_policy(amount="wide", density="full", bias="looser"),
                5: _pad_policy(amount="normal", density="high", bias="brighter", lanes={"filter": "off", "lfo": "off"}, amp_fx_only=True),
                6: _pad_policy(amount="wide", density="high", bias="looser", lanes={"filter": "micro", "lfo": "off"}, amp_fx_only=True),
                7: _pad_policy(amount="wide", density="high", bias="looser", lanes={"filter": "micro", "lfo": "off"}, amp_fx_only=True),
                8: _pad_policy(amount="wide", density="high", bias="looser", lanes={"filter": "micro", "lfo": "off"}, amp_fx_only=True),
                9: _pad_policy(amount="normal", density="high", bias="brighter", lanes={"filter": "off", "lfo": "off"}, amp_fx_only=True),
                10: _pad_policy(amount="normal", density="high", bias="brighter", lanes={"filter": "off", "lfo": "off"}, amp_fx_only=True),
                11: _pad_policy(amount="normal", density="high", bias="brighter", lanes={"filter": "off", "lfo": "off"}, amp_fx_only=True),
                12: _pad_policy(amount="wide", density="medium", bias="looser", amp_fx_only=True),
            },
        ),
        "home": SnapshotLiveMacroSpec(
            name="home",
            label="Home",
            mode="live",
            lane_policies=MappingProxyType({}),
            locked_pads=frozenset(),
            pad_policies=MappingProxyType({}),
            recovery_action="home",
            risk_label="live-safe",
            summary="Return the current staged plan to the captured anchor.",
        ),
    }
)
```

- [ ] **Step 4: Run and verify green**

Run:

```powershell
python -m pytest tests\test_analog_rytm_snapshot_shell.py -k "live_macro_catalog" -n 0
```

Expected: the two macro catalog tests pass.

- [ ] **Step 5: Commit**

```powershell
git add rytm_randomizer\engines\analog_rytm_snapshot_macros.py tests\test_analog_rytm_snapshot_shell.py
git commit -m "feat: add Rytm live macro catalog"
```

## Task 2: Wire Named Macro Commands Into The Snapshot Shell

**Files:**
- Modify: `rytm_randomizer/engines/analog_rytm_snapshot_shell.py`
- Modify: `tests/test_analog_rytm_snapshot_shell.py`

- [ ] **Step 1: Write failing shell dispatch tests**

Add these tests near the current `kit-core` macro tests:

```python
@pytest.mark.parametrize(
    ("command", "macro_name"),
    (
        ("macro hard-groove", "hard-groove"),
        ("macro industrial", "industrial"),
        ("macro dub-pressure", "dub-pressure"),
        ("macro transition", "transition"),
        ("hard-groove", "hard-groove"),
        ("industrial", "industrial"),
        ("dub-pressure", "dub-pressure"),
        ("transition", "transition"),
    ),
)
def test_snapshot_shell_named_live_macros_stage_without_sending(
    command: str,
    macro_name: str,
    capsys,
) -> None:
    from rytm_randomizer.engines.analog_rytm_snapshot_shell import (
        AnalogRytmSnapshotShell,
        build_snapshot_shell_anchor,
    )

    sender = MockMidiSender()
    shell = AnalogRytmSnapshotShell(build_snapshot_shell_anchor(_snapshot()), sender)

    assert shell.dispatch(command) is True

    captured = capsys.readouterr()
    assert f"macro applied: {macro_name}" in captured.out
    assert shell.state.guardrails.mode == "live"
    assert shell.state.guardrails.locked_pads == frozenset({1})
    assert shell.state.last_command_name == "randomize"
    assert _pad_values_unchanged(shell.state.anchor.events, shell.state.current_events, pad=1)
    assert len(sender.sent_messages) == 0


def test_snapshot_shell_macro_home_restores_anchor_without_sending(capsys) -> None:
    from rytm_randomizer.engines.analog_rytm_snapshot_shell import (
        AnalogRytmSnapshotShell,
        build_snapshot_shell_anchor,
    )

    anchor = build_snapshot_shell_anchor(_snapshot())
    sender = MockMidiSender()
    shell = AnalogRytmSnapshotShell(anchor, sender)

    assert shell.dispatch("kit-core") is True
    assert shell.dispatch("macro home") is True

    captured = capsys.readouterr()
    assert "macro applied: home" in captured.out
    assert shell.state.mutation_name == "home"
    assert shell.state.current_events == anchor.events
    assert shell.state.last_command_name is None
    assert len(sender.sent_messages) == 0


def test_snapshot_shell_unknown_macro_is_non_destructive(capsys) -> None:
    from rytm_randomizer.engines.analog_rytm_snapshot_shell import (
        AnalogRytmSnapshotShell,
        build_snapshot_shell_anchor,
    )

    anchor = build_snapshot_shell_anchor(_snapshot())
    shell = AnalogRytmSnapshotShell(anchor, MockMidiSender())

    assert shell.dispatch("macro alien") is True

    captured = capsys.readouterr()
    assert "unknown snapshot shell macro: alien" in captured.out
    assert shell.state.current_events == anchor.events
```

- [ ] **Step 2: Run and verify red**

Run:

```powershell
python -m pytest tests\test_analog_rytm_snapshot_shell.py -k "named_live_macros or macro_home or unknown_macro" -n 0
```

Expected: fail because `macro NAME` and direct new macro commands are not wired.

- [ ] **Step 3: Import the macro catalog**

In `rytm_randomizer/engines/analog_rytm_snapshot_shell.py`, add:

```python
from .analog_rytm_snapshot_macros import (
    SNAPSHOT_LIVE_MACROS,
    SnapshotLiveMacroSpec,
    SnapshotMacroPadPolicy,
)
```

- [ ] **Step 4: Add a generic macro applier**

Replace the hard-coded body of `_apply_kit_core_macro` with a generic helper while keeping `_apply_drum_core_macro` intact:

```python
    def _apply_live_macro(self, macro: SnapshotLiveMacroSpec) -> None:
        self._write_line(f"macro applied: {macro.name}")
        if macro.name == "home":
            self.state = replace(
                self.state,
                mutation_name="home",
                previous_events=self.state.current_events,
                current_events=self.state.anchor.events,
                last_command_name=None,
                last_depth=None,
            )
            return
        self._set_preset(("preset", macro.mode))
        for lane, policy in macro.lane_policies.items():
            self._set_lane_policy(("lane", lane, policy))
        for pad in macro.locked_pads:
            self._set_lock(("lock", str(pad)), locked=True)
        for pad, policy in macro.pad_policies.items():
            self._apply_macro_pad_policy(pad, policy)
        self._apply_command(SNAPSHOT_SHELL_COMMANDS[_CMD_RANDOMIZE])

    def _apply_macro_pad_policy(self, pad: int, policy: SnapshotMacroPadPolicy) -> None:
        raw_pad = str(pad)
        for lane, lane_policy in policy.lane_policies.items():
            self._set_pad_lane_policy(pad, lane, lane_policy)
        for section, families in policy.section_family_allowlists.items():
            self._set_pad_section_family_allowlist(pad, section, families)
        if policy.amount is not None:
            self._set_pad_randomizer_policy(("pad", raw_pad, "amount", policy.amount))
        if policy.density is not None:
            self._set_pad_randomizer_policy(("pad", raw_pad, "density", policy.density))
        if policy.bias is not None:
            self._set_pad_randomizer_policy(("pad", raw_pad, "bias", policy.bias))

    def _apply_kit_core_macro(self) -> None:
        self._apply_live_macro(SNAPSHOT_LIVE_MACROS[_CMD_KIT_CORE])
```

- [ ] **Step 5: Add macro dispatch**

In `dispatch`, add the explicit `macro` branch before unknown command handling:

```python
        if parts and parts[0] == "macro":
            if len(parts) != 2:
                self._write_line("usage: macro NAME")
                return True
            macro = SNAPSHOT_LIVE_MACROS.get(parts[1])
            if macro is None:
                self._write_line(f"unknown snapshot shell macro: {parts[1]}")
                return True
            self._apply_live_macro(macro)
            return True
        direct_macro = SNAPSHOT_LIVE_MACROS.get(normalized)
        if direct_macro is not None and normalized not in {_CMD_KIT_CORE}:
            self._apply_live_macro(direct_macro)
            return True
```

Leave the existing `kit-core`, `kitcore`, and `full-kit` branch in place so compatibility stays explicit.

- [ ] **Step 6: Update help text**

Extend `_snapshot_help_text()` macro lines so it includes:

```text
macro NAME = stage a named live macro
hard-groove / industrial / dub-pressure / transition / home = direct macro shortcuts
```

- [ ] **Step 7: Run and verify green**

Run:

```powershell
python -m pytest tests\test_analog_rytm_snapshot_shell.py -k "named_live_macros or macro_home or unknown_macro or kit_core_macro" -n 0
```

Expected: all selected tests pass.

- [ ] **Step 8: Commit**

```powershell
git add rytm_randomizer\engines\analog_rytm_snapshot_shell.py tests\test_analog_rytm_snapshot_shell.py
git commit -m "feat: wire Rytm live macro commands"
```

## Task 3: Lock Down Macro Pad Policies

**Files:**
- Modify: `tests/test_analog_rytm_snapshot_shell.py`
- Modify: `rytm_randomizer/engines/analog_rytm_snapshot_shell.py`
- Modify: `rytm_randomizer/engines/analog_rytm_snapshot_macros.py`

- [ ] **Step 1: Write policy tests for reserved pads and tom pads**

Add:

```python
@pytest.mark.parametrize("command", ("hard-groove", "industrial", "dub-pressure", "transition"))
def test_snapshot_shell_macros_keep_reserved_pads_src_first_and_no_filter_lfo(command: str) -> None:
    from rytm_randomizer.engines.analog_rytm_snapshot_shell import (
        AnalogRytmSnapshotShell,
        build_snapshot_shell_anchor,
    )

    anchor = build_snapshot_shell_anchor(_snapshot())
    shell = AnalogRytmSnapshotShell(anchor, MockMidiSender())

    assert shell.dispatch(command) is True

    for pad in (5, 9, 10, 11):
        changed = _changed_events_for_pad(anchor.events, shell.state.current_events, pad=pad)
        assert any(event.source == "machine_src" for event in changed)
        assert all(event.section not in {"FILTER", "LFO"} for event in changed)
        assert all(
            event.section != "AMP"
            or event.parameter in {"Amp Overdrive", "Amp Delay Send", "Amp Reverb Send"}
            for event in changed
        )


@pytest.mark.parametrize("command", ("hard-groove", "industrial", "dub-pressure", "transition"))
def test_snapshot_shell_macros_keep_tom_pads_source_with_light_filter_and_no_lfo(command: str) -> None:
    from rytm_randomizer.engines.analog_rytm_snapshot_shell import (
        AnalogRytmSnapshotShell,
        build_snapshot_shell_anchor,
    )

    anchor = build_snapshot_shell_anchor(_snapshot())
    shell = AnalogRytmSnapshotShell(anchor, MockMidiSender())

    assert shell.dispatch(command) is True

    for pad in (6, 7, 8):
        changed = _changed_events_for_pad(anchor.events, shell.state.current_events, pad=pad)
        assert any(event.source == "machine_src" for event in changed)
        assert all(
            old.value == new.value
            for old, new in zip(anchor.events, shell.state.current_events, strict=True)
            if new.pad == pad and new.section == "LFO"
        )
        assert all(
            abs(new.value - old.value) <= 2
            for old, new in zip(anchor.events, shell.state.current_events, strict=True)
            if new.pad == pad and new.section == "FILTER"
        )
```

- [ ] **Step 2: Run and verify red or green**

Run:

```powershell
python -m pytest tests\test_analog_rytm_snapshot_shell.py -k "reserved_pads_src_first or tom_pads_source" -n 0
```

Expected: pass if the macro catalog from Task 1 already satisfies the policy; otherwise fail on the macro whose policy needs adjustment.

- [ ] **Step 3: Adjust macro specs if needed**

If the test identifies a macro gap, update only that macro's `SnapshotMacroPadPolicy` in `analog_rytm_snapshot_macros.py`. Use these exact rules:

```python
lanes={"filter": "off", "lfo": "off"}, amp_fx_only=True
```

for pads 5, 9, 10, and 11, and:

```python
lanes={"filter": "micro", "lfo": "off"}, amp_fx_only=True
```

for pads 6, 7, and 8.

- [ ] **Step 4: Run policy tests**

Run:

```powershell
python -m pytest tests\test_analog_rytm_snapshot_shell.py -k "reserved_pads_src_first or tom_pads_source" -n 0
```

Expected: all selected tests pass.

- [ ] **Step 5: Commit**

```powershell
git add rytm_randomizer\engines\analog_rytm_snapshot_macros.py tests\test_analog_rytm_snapshot_shell.py
git commit -m "test: lock live macro pad policies"
```

## Task 4: Preserve Dual VCO Detune Safety Across Macros

**Files:**
- Modify: `tests/test_analog_rytm_snapshot_shell.py`
- Modify: `rytm_randomizer/engines/analog_rytm_snapshot_shell.py`

- [ ] **Step 1: Write macro-wide Dual VCO detune tests**

Add:

```python
@pytest.mark.parametrize("command", ("hard-groove", "industrial", "dub-pressure", "transition"))
def test_snapshot_shell_macros_keep_low_dual_vco_detune_guarded(command: str) -> None:
    from rytm_randomizer.engines.analog_rytm_snapshot_shell import (
        AnalogRytmSnapshotShell,
        build_snapshot_shell_anchor,
    )

    snapshot = AnalogRytmSnapshotDecoder().decode(
        _snapshot_payload_with_track_overrides(
            overrides_by_pad={
                2: (28, {4: 25, 5: 64}),
                3: (28, {4: 4, 5: 51}),
            },
        ),
        slot=0,
    )
    anchor = build_snapshot_shell_anchor(snapshot)
    sender = MockMidiSender()
    shell = AnalogRytmSnapshotShell(anchor, sender)

    assert shell.dispatch(command) is True
    assert shell.dispatch("send") is True

    assert (
        _event_for(shell.state.current_events, pad=2, parameter="Osc 2 Detune").value
        == _event_for(anchor.events, pad=2, parameter="Osc 2 Detune").value
    )
    assert (
        _event_for(shell.state.current_events, pad=3, parameter="Osc 2 Detune").value
        == _event_for(anchor.events, pad=3, parameter="Osc 2 Detune").value
    )
    assert all(
        not (message.channel in {1, 2} and message.control == 20)
        for message in sender.sent_messages
    )


@pytest.mark.parametrize("command", ("hard-groove", "industrial", "dub-pressure", "transition"))
def test_snapshot_shell_macros_allow_center_band_dual_vco_detune(command: str) -> None:
    from rytm_randomizer.engines.analog_rytm_snapshot_shell import (
        AnalogRytmSnapshotShell,
        build_snapshot_shell_anchor,
    )

    snapshot = AnalogRytmSnapshotDecoder().decode(
        _snapshot_payload_with_track_overrides(
            overrides_by_pad={
                2: (28, {4: 66, 5: 64}),
            },
        ),
        slot=0,
    )
    anchor = build_snapshot_shell_anchor(snapshot)
    sender = MockMidiSender()
    shell = AnalogRytmSnapshotShell(anchor, sender)

    assert shell.dispatch(command) is True
    assert shell.dispatch("send") is True

    current = _event_for(shell.state.current_events, pad=2, parameter="Osc 2 Detune")
    assert 62 <= current.value <= 70
    assert any(message.channel == 1 and message.control == 20 for message in sender.sent_messages)
```

- [ ] **Step 2: Run and verify green**

Run:

```powershell
python -m pytest tests\test_analog_rytm_snapshot_shell.py -k "dual_vco_detune" -n 0
```

Expected: all Dual VCO detune tests pass. The new macro tests should reuse the PR #149 safety functions without implementation changes.

- [ ] **Step 3: Commit**

```powershell
git add tests\test_analog_rytm_snapshot_shell.py
git commit -m "test: cover live macros dual vco detune safety"
```

## Task 5: Add Passive Macro Catalog Report

**Files:**
- Create: `rytm_randomizer/reports/oxi_live_macro_catalog.py`
- Modify: `rytm_randomizer/reports/__init__.py`
- Modify: `rytm_randomizer/cli.py`
- Modify: `rytm_randomizer/help_text.py`
- Create: `tests/test_oxi_live_macro_catalog_report.py`

- [ ] **Step 1: Write failing report tests**

Create `tests/test_oxi_live_macro_catalog_report.py`:

```python
from __future__ import annotations

import pytest

pytestmark = pytest.mark.fast


def test_oxi_live_macro_catalog_report_lists_rytm_macros_and_a4_candidate_state() -> None:
    from rytm_randomizer.reports.oxi_live_macro_catalog import (
        build_oxi_live_macro_catalog_report,
        format_oxi_live_macro_catalog_report,
    )

    report = build_oxi_live_macro_catalog_report()
    text = "\n".join(format_oxi_live_macro_catalog_report(report))

    assert report.title == "RytmRandomizer OXI live macro catalog"
    assert [card.name for card in report.rytm_macros] == [
        "kit-core",
        "hard-groove",
        "industrial",
        "dub-pressure",
        "transition",
        "home",
    ]
    assert "Rytm macros:" in text
    assert "hard-groove | live-safe | recovery=home" in text
    assert "Analog Four runway: candidate-only" in text
    assert "blocked active actions: A4 outbound macro send" in text


def test_oxi_live_macro_catalog_json_is_deterministic() -> None:
    from rytm_randomizer.reports.oxi_live_macro_catalog import (
        build_oxi_live_macro_catalog_payload,
    )

    payload = build_oxi_live_macro_catalog_payload()

    assert payload["title"] == "RytmRandomizer OXI live macro catalog"
    assert payload["rytm_macros"][0]["name"] == "kit-core"
    assert payload["rytm_macros"][1]["affected_pads"] == [2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
    assert payload["analog_four"]["status"] == "candidate-only"
    assert payload["blocked_active_actions"] == ["A4 outbound macro send"]
```

- [ ] **Step 2: Run and verify red**

Run:

```powershell
python -m pytest tests\test_oxi_live_macro_catalog_report.py -n 0
```

Expected: fail because the report module does not exist.

- [ ] **Step 3: Implement the report module**

Create `rytm_randomizer/reports/oxi_live_macro_catalog.py`:

```python
from __future__ import annotations

import sys
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Final

from ..cli_registry import CliCommand, register
from ..engines.analog_rytm_snapshot_macros import SNAPSHOT_LIVE_MACROS

REPORT_TITLE: Final[str] = "RytmRandomizer OXI live macro catalog"


@dataclass(frozen=True)
class OxiLiveMacroCard:
    name: str
    label: str
    risk_label: str
    affected_pads: tuple[int, ...]
    recovery_action: str
    summary: str


@dataclass(frozen=True)
class AnalogFourMacroRunway:
    status: str
    tracks: tuple[int, ...]
    summary: str


@dataclass(frozen=True)
class OxiLiveMacroCatalogReport:
    title: str
    rytm_macros: tuple[OxiLiveMacroCard, ...]
    analog_four: AnalogFourMacroRunway
    blocked_active_actions: tuple[str, ...]


def _affected_pads(pad_policies: Mapping[int, object]) -> tuple[int, ...]:
    pads = sorted(pad_policies)
    if 12 not in pads:
        pads.append(12)
    return tuple(pads)


def build_oxi_live_macro_catalog_report() -> OxiLiveMacroCatalogReport:
    cards = tuple(
        OxiLiveMacroCard(
            name=macro.name,
            label=macro.label,
            risk_label=macro.risk_label,
            affected_pads=_affected_pads(macro.pad_policies),
            recovery_action=macro.recovery_action,
            summary=macro.summary,
        )
        for macro in SNAPSHOT_LIVE_MACROS.values()
    )
    return OxiLiveMacroCatalogReport(
        title=REPORT_TITLE,
        rytm_macros=cards,
        analog_four=AnalogFourMacroRunway(
            status="candidate-only",
            tracks=(1, 2, 3, 4),
            summary="A4 macro planning is passive/mock-only until hardware validation.",
        ),
        blocked_active_actions=("A4 outbound macro send",),
    )


def format_oxi_live_macro_catalog_report(
    report: OxiLiveMacroCatalogReport,
) -> tuple[str, ...]:
    lines = [report.title, "", "Rytm macros:"]
    for card in report.rytm_macros:
        pads = ", ".join(str(pad) for pad in card.affected_pads)
        lines.append(
            f"- {card.name} | {card.risk_label} | recovery={card.recovery_action} | pads={pads}"
        )
        lines.append(f"  {card.summary}")
    lines.extend(
        (
            "",
            f"Analog Four runway: {report.analog_four.status}",
            f"  tracks: {', '.join(str(track) for track in report.analog_four.tracks)}",
            f"  {report.analog_four.summary}",
            "",
            "blocked active actions: " + ", ".join(report.blocked_active_actions),
        )
    )
    return tuple(lines)


def build_oxi_live_macro_catalog_payload() -> dict[str, object]:
    report = build_oxi_live_macro_catalog_report()
    return {
        "title": report.title,
        "rytm_macros": [
            {
                "name": card.name,
                "label": card.label,
                "risk_label": card.risk_label,
                "affected_pads": list(card.affected_pads),
                "recovery_action": card.recovery_action,
                "summary": card.summary,
            }
            for card in report.rytm_macros
        ],
        "analog_four": {
            "status": report.analog_four.status,
            "tracks": list(report.analog_four.tracks),
            "summary": report.analog_four.summary,
        },
        "blocked_active_actions": list(report.blocked_active_actions),
    }


def _parse_oxi_live_macro_catalog_args(args: Sequence[str]) -> dict[str, object]:
    if args:
        raise ValueError(
            "oxi-live-macro-catalog-report does not accept arguments"
        )
    return {}


def _handle_oxi_live_macro_catalog_report() -> int:
    report = build_oxi_live_macro_catalog_report()
    sys.stdout.write("\n".join(format_oxi_live_macro_catalog_report(report)))
    sys.stdout.write("\n")
    return 0


OXI_LIVE_MACRO_CATALOG_CLI_COMMAND: Final[CliCommand] = CliCommand(
    name="oxi-live-macro-catalog-report",
    summary=(
        "Print the passive OXI live macro catalog and candidate-only A4 runway."
    ),
    args_parser=_parse_oxi_live_macro_catalog_args,
    handler=_handle_oxi_live_macro_catalog_report,
)

register(OXI_LIVE_MACRO_CATALOG_CLI_COMMAND)


__all__ = (
    "AnalogFourMacroRunway",
    "OxiLiveMacroCard",
    "OxiLiveMacroCatalogReport",
    "OXI_LIVE_MACRO_CATALOG_CLI_COMMAND",
    "build_oxi_live_macro_catalog_payload",
    "build_oxi_live_macro_catalog_report",
    "format_oxi_live_macro_catalog_report",
)
```

- [ ] **Step 4: Wire report exports and CLI manifest**

In `rytm_randomizer/reports/__init__.py`, add these imports:

```python
from .oxi_live_macro_catalog import (  # noqa: F401
    build_oxi_live_macro_catalog_payload,
    build_oxi_live_macro_catalog_report,
    format_oxi_live_macro_catalog_report,
)
```

In `rytm_randomizer/cli.py`, add this entry to the `lazy_commands` mapping:

```python
"oxi-live-macro-catalog-report": (
    "rytm_randomizer.reports.oxi_live_macro_catalog",
    "OXI_LIVE_MACRO_CATALOG_CLI_COMMAND",
),
```

The report module's `_handle_oxi_live_macro_catalog_report()` prints
`format_oxi_live_macro_catalog_report(build_oxi_live_macro_catalog_report())`.
Do not add a JSON CLI flag in this bundle; the deterministic payload builder is
for tests and future GUI consumers. Do not open MIDI ports.

- [ ] **Step 5: Add help text**

In `rytm_randomizer/help_text.py`, add a command help entry that says:

```text
Prints the passive OXI live macro catalog, including Rytm macro cards,
candidate-only Analog Four runway state, recovery actions, and blocked active
actions. Opens no MIDI ports and sends no MIDI.
```

- [ ] **Step 6: Run report tests**

Run:

```powershell
python -m pytest tests\test_oxi_live_macro_catalog_report.py -n 0
```

Expected: all report tests pass.

- [ ] **Step 7: Commit**

```powershell
git add rytm_randomizer\reports\oxi_live_macro_catalog.py rytm_randomizer\reports\__init__.py rytm_randomizer\cli.py rytm_randomizer\help_text.py tests\test_oxi_live_macro_catalog_report.py
git commit -m "feat: add passive OXI live macro catalog report"
```

## Task 6: Update README And Status

**Files:**
- Modify: `README.md`
- Modify: `docs/STATUS.md`

- [ ] **Step 1: Update README live snapshot shell section**

In `README.md`, near the live snapshot shell / Rytm CC observer section, add:

```markdown
Named live macros are available inside `snapshot-12>` after a current-kit
capture:

- `kit-core` - full-kit live-safe discovery using the hardware-validated pad
  5-11 lane discipline.
- `hard-groove` - dry pressure for OXI patterns that already carry the groove.
- `industrial` - metallic pressure and controlled grit.
- `dub-pressure` - darker, more spacious pressure with bounded effects movement.
- `transition` - set-section movement with an obvious `home` recovery.
- `home` - return the staged plan to the captured anchor before sending.

Every macro stages changes first. Use `changes`, then `send`, and use `Z` plus
`send` or `home` plus `send` to recover the captured kit. The passive
`oxi-live-macro-catalog-report` command lists macro cards and the candidate-only
Analog Four runway without opening MIDI ports.
```

- [ ] **Step 2: Update docs status**

At the top of `docs/STATUS.md`, add:

```markdown
- 2026-06-02: OXI live macro bundle implemented after PR #149 merged. The live
  snapshot shell now supports `hard-groove`, `industrial`, `dub-pressure`,
  `transition`, and `home` in addition to `kit-core`; the passive macro catalog
  report exposes Rytm macro cards and a candidate-only Analog Four runway for
  Cockpit handoff. Active Rytm sends still require the armed snapshot shell and
  explicit `send` / `go`; A4 outbound macro sends remain blocked.
```

- [ ] **Step 3: Run README freshness and plan/status checks**

Run:

```powershell
python -m pytest tests\architecture\test_readme_freshness.py tests\architecture\test_plan_doc_status_truth.py tests\architecture\test_plan_requirements_referenced.py -q -n 0
```

Expected: all selected architecture checks pass.

- [ ] **Step 4: Commit**

```powershell
git add README.md docs\STATUS.md
git commit -m "docs: describe OXI live macro bundle"
```

## Task 7: Verification And PR Preparation

**Files:**
- All files touched by Tasks 1-6

- [ ] **Step 1: Run focused snapshot shell tests**

Run:

```powershell
python -m pytest tests\test_analog_rytm_snapshot_shell.py -n 0
```

Expected: all snapshot shell tests pass.

- [ ] **Step 2: Run report tests**

Run:

```powershell
python -m pytest tests\test_oxi_live_macro_catalog_report.py -n 0
```

Expected: all report tests pass.

- [ ] **Step 3: Run architecture tests**

Run:

```powershell
python -m pytest tests\architecture\ -q
```

Expected: all architecture tests pass. If local runtime is too slow, keep the focused architecture results and let CI run the full gate, but do not claim full local architecture passed.

- [ ] **Step 4: Run full pytest**

Run:

```powershell
python -m pytest
```

Expected: full test suite passes.

- [ ] **Step 5: Run lint trio**

Run:

```powershell
python -m ruff check .
python -m black --check --target-version=py311 .
python -m isort --profile black --check-only .
```

Expected: all lint/format checks pass.

- [ ] **Step 6: Run whitespace check**

Run:

```powershell
git diff --check
```

Expected: no whitespace errors.

- [ ] **Step 7: Prepare PR body**

Create a PR body that links:

```text
docs/superpowers/specs/2026-05-31-oxi-live-macro-bundle-design.md
docs/superpowers/plans/2026-06-02-oxi-live-macro-bundle.md
```

The PR body must include:

- what changed and why,
- test plan,
- 18-gate conformance checklist,
- strict-rules confirmation block,
- hardware note that Rytm hardware validation is planned after merge candidate testing with Jose present,
- explicit A4 boundary that A4 macro sends remain candidate-only/blocked.

- [ ] **Step 8: Push and open one PR**

Run:

```powershell
git push -u origin codex/next-oxi-live-macro-spec
python scripts/create_pr.py --title "feat: add OXI live macro bundle" --body-file <pr-body-file>
```

Expected: one PR against `modularize-v1.34`. Do not open stacked PRs.

## Hardware Validation Script After Implementation

Use only with Jose present and the Rytm powered on:

```powershell
Set-Location 'C:\Users\Jose Buzzi\Documents\RytmRandomizer'
& '.\.venv\Scripts\python.exe' -m rytm_randomizer.app --arm --rytm-live-snapshot-shell --confirm-rytm-snapshot-shell-send
```

Inside `snapshot-12>`:

```text
kit-core
changes
send
go
changes
Z
send
hard-groove
changes
send
Z
send
industrial
changes
send
Z
send
dub-pressure
changes
send
Z
send
transition
changes
send
home
send
```

Stop on any Rytm `ERR`, wrong-port behavior, lost kick foundation, uncontrolled
filter jump, excessive LFO movement, or restore failure.

## Plan Self-Review

- Spec coverage: the plan covers named Rytm macros, pad policy, Dual VCO safety,
  passive A4 runway, Cockpit-ready passive catalog data, safety boundaries,
  docs, tests, and hardware validation.
- Scope split: A4 outbound mutation is intentionally excluded from active code
  and represented as candidate-only report state.
- Type consistency: macro helper types are local to `analog_rytm_snapshot_macros.py`
  and consumed by the snapshot shell through explicit dataclasses.
- Red-flag scan: this plan contains no unresolved blanks or open-ended tasks.
