# Analog Four Soft Live Capture Implementation Plan

> Status: in-flight (branch codex/rytm-snapshot-pad-compatibility-pr1)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a passive Analog Four MKII soft live capture path that observes incoming CC messages for all four A4 tracks and reports the captured known state without opening output ports or sending MIDI.

**Architecture:** Add an immutable `state/a4_soft_capture.py` reducer that maps A4 track-channel CC observations through the manual-backed data table. Add a passive report formatter, extend the existing mido provider with input-port discovery/opening, and wire one explicit `--arm --a4-soft-capture` app path that opens only an input port.

**Tech Stack:** Python 3.11+ dataclasses, `MappingProxyType`, existing `mido_provider` lazy import boundary, existing passive report formatter, pytest with fake ports.

---

## File Structure

- Create `rytm_randomizer/state/a4_soft_capture.py`
  - Owns immutable observed-state dataclasses and pure reducer functions.
  - Depends on `rytm_randomizer.data.ANALOG_FOUR_SYNTH_TRACK_CC_BY_MSB`.
  - Performs no I/O.
- Modify `rytm_randomizer/data/analog_four_midi.py`
  - Add a CC-number lookup for manual-backed A4 synth-track mappings.
- Modify `rytm_randomizer/data/__init__.py`
  - Re-export `ANALOG_FOUR_SYNTH_TRACK_CC_BY_MSB`.
- Create `rytm_randomizer/reports/a4_soft_capture.py`
  - Formats deterministic capture reports.
  - Performs no I/O.
- Modify `rytm_randomizer/reports/__init__.py`
  - Re-export the report builder/formatter if this package exports other report helpers.
- Modify `rytm_randomizer/mido_provider.py`
  - Add lazy `list_input_names()` and `open_input()` methods.
  - Keep import-time behavior side-effect free.
- Modify `rytm_randomizer/app.py`
  - Add `--a4-soft-capture`.
  - Require `--arm`.
  - Open an input port only, wait for the operator to press Enter, drain pending input messages, print report, close input port.
- Create `tests/test_a4_soft_capture.py`
  - Covers reducer and report behavior.
- Modify `tests/test_data_layer.py`
  - Pins the CC lookup shape.
- Modify `tests/test_mido_provider.py`
  - Covers input discovery/opening with fake mido.
- Modify `tests/test_app_entry.py`
  - Covers the app command with fake input port and no output port.
- Modify `tests/test_real_midi_passive_cli_safety.py`
  - No passive CLI command changes expected; only update if a safety assertion needs to name the new app-only path.

---

### Task 1: Manual-Backed CC Lookup

**Files:**
- Modify: `rytm_randomizer/data/analog_four_midi.py`
- Modify: `rytm_randomizer/data/__init__.py`
- Modify: `tests/test_data_layer.py`

- [ ] **Step 1: Write the failing lookup test**

Add this test in `tests/test_data_layer.py` below the existing A4 manual mapping test:

```python
def test_analog_four_cc_lookup_maps_msb_to_manual_entry():
    pulsewidth = data.ANALOG_FOUR_SYNTH_TRACK_CC_BY_MSB[72]
    pwm_speed = data.ANALOG_FOUR_SYNTH_TRACK_CC_BY_MSB[73]
    pwm_depth = data.ANALOG_FOUR_SYNTH_TRACK_CC_BY_MSB[74]

    assert pulsewidth.parameter == "OSC1 Pulsewidth"
    assert pwm_speed.parameter == "OSC1 PWM Speed"
    assert pwm_depth.parameter == "OSC1 PWM Depth"
```

- [ ] **Step 2: Run the test and verify it fails**

Run:

```powershell
python -m pytest tests/test_data_layer.py::test_analog_four_cc_lookup_maps_msb_to_manual_entry -n 0
```

Expected: fails with `AttributeError: module 'rytm_randomizer.data' has no attribute 'ANALOG_FOUR_SYNTH_TRACK_CC_BY_MSB'`.

- [ ] **Step 3: Add the CC lookup**

In `rytm_randomizer/data/analog_four_midi.py`, add the lookup after `ANALOG_FOUR_SYNTH_TRACK_CC`:

```python
ANALOG_FOUR_SYNTH_TRACK_CC_BY_MSB: Final[Mapping[int, AnalogFourCcMapping]] = (
    MappingProxyType({mapping.cc_msb: mapping for mapping in ANALOG_FOUR_SYNTH_TRACK_CC.values()})
)
```

Update the module export:

```python
__all__ = ["ANALOG_FOUR_SYNTH_TRACK_CC", "ANALOG_FOUR_SYNTH_TRACK_CC_BY_MSB"]
```

In `rytm_randomizer/data/__init__.py`, import and export the new name:

```python
from .analog_four_midi import ANALOG_FOUR_SYNTH_TRACK_CC, ANALOG_FOUR_SYNTH_TRACK_CC_BY_MSB
```

Add `"ANALOG_FOUR_SYNTH_TRACK_CC_BY_MSB"` to `__all__` next to `"ANALOG_FOUR_SYNTH_TRACK_CC"`.

- [ ] **Step 4: Run the data-layer tests**

Run:

```powershell
python -m pytest tests/test_data_layer.py::test_analog_four_manual_cc_mapping_matches_pwm_depth_and_filter_frequency tests/test_data_layer.py::test_analog_four_cc_lookup_maps_msb_to_manual_entry -n 0
```

Expected: both tests pass.

- [ ] **Step 5: Commit**

```powershell
git add rytm_randomizer/data/analog_four_midi.py rytm_randomizer/data/__init__.py tests/test_data_layer.py
git commit -m "feat: add Analog Four CC lookup"
```

---

### Task 2: Soft Capture State Reducer

**Files:**
- Create: `rytm_randomizer/state/a4_soft_capture.py`
- Modify: `rytm_randomizer/state/__init__.py`
- Create: `tests/test_a4_soft_capture.py`

- [ ] **Step 1: Write failing reducer tests**

Create `tests/test_a4_soft_capture.py` with:

```python
from __future__ import annotations

from types import MappingProxyType

import pytest

pytestmark = pytest.mark.fast


class FakeCcMessage:
    def __init__(self, *, channel: int, control: int, value: int) -> None:
        self.type = "control_change"
        self.channel = channel
        self.control = control
        self.value = value


class FakeNoteMessage:
    type = "note_on"
    channel = 0
    note = 60
    velocity = 100


def test_observe_known_cc_updates_track_parameter() -> None:
    from rytm_randomizer.state.a4_soft_capture import (
        empty_a4_soft_capture_snapshot,
        observe_a4_message,
    )

    snapshot = empty_a4_soft_capture_snapshot()
    updated = observe_a4_message(
        snapshot,
        FakeCcMessage(channel=0, control=72, value=96),
        observed_at=12.5,
    )

    track_1 = updated.tracks[0]
    observed = track_1.parameters["OSC1 Pulsewidth"]
    assert observed.track == 1
    assert observed.parameter == "OSC1 Pulsewidth"
    assert observed.section == "OSC 1"
    assert observed.cc == 72
    assert observed.value == 96
    assert observed.observed_at == 12.5
    assert updated.known_parameter_count == 1


def test_observe_maps_channels_to_all_four_tracks() -> None:
    from rytm_randomizer.state.a4_soft_capture import (
        empty_a4_soft_capture_snapshot,
        observe_a4_message,
    )

    snapshot = empty_a4_soft_capture_snapshot()
    snapshot = observe_a4_message(snapshot, FakeCcMessage(channel=1, control=72, value=64), observed_at=1.0)
    snapshot = observe_a4_message(snapshot, FakeCcMessage(channel=3, control=74, value=32), observed_at=2.0)

    assert snapshot.tracks[1].parameters["OSC1 Pulsewidth"].track == 2
    assert snapshot.tracks[3].parameters["OSC1 PWM Depth"].track == 4
    assert snapshot.known_parameter_count == 2


def test_unknown_cc_is_counted_but_not_mislabeled() -> None:
    from rytm_randomizer.state.a4_soft_capture import (
        empty_a4_soft_capture_snapshot,
        observe_a4_message,
    )

    snapshot = observe_a4_message(
        empty_a4_soft_capture_snapshot(),
        FakeCcMessage(channel=0, control=99, value=88),
        observed_at=3.0,
    )

    assert snapshot.known_parameter_count == 0
    assert len(snapshot.unknown_controls) == 1
    unknown = snapshot.unknown_controls[0]
    assert unknown.channel == 0
    assert unknown.control == 99
    assert unknown.value == 88
    assert unknown.reason == "unknown_cc"
    assert snapshot.tracks[0].parameters == MappingProxyType({})


def test_out_of_scope_channel_is_counted() -> None:
    from rytm_randomizer.state.a4_soft_capture import (
        empty_a4_soft_capture_snapshot,
        observe_a4_message,
    )

    snapshot = observe_a4_message(
        empty_a4_soft_capture_snapshot(),
        FakeCcMessage(channel=4, control=72, value=64),
        observed_at=4.0,
    )

    assert snapshot.out_of_scope_message_count == 1
    assert snapshot.known_parameter_count == 0


def test_non_cc_message_is_ignored_without_crashing() -> None:
    from rytm_randomizer.state.a4_soft_capture import (
        empty_a4_soft_capture_snapshot,
        observe_a4_message,
    )

    snapshot = observe_a4_message(empty_a4_soft_capture_snapshot(), FakeNoteMessage(), observed_at=5.0)

    assert snapshot.ignored_message_count == 1
    assert snapshot.known_parameter_count == 0


def test_capture_all_always_has_four_tracks() -> None:
    from rytm_randomizer.state.a4_soft_capture import empty_a4_soft_capture_snapshot

    snapshot = empty_a4_soft_capture_snapshot()

    assert tuple(track.track for track in snapshot.tracks) == (1, 2, 3, 4)
    assert snapshot.source == "passive_cc_observation"
    assert snapshot.unknown_policy == "unknown_parameters_untouched"
```

- [ ] **Step 2: Run tests and verify they fail**

Run:

```powershell
python -m pytest tests/test_a4_soft_capture.py -n 0
```

Expected: fails with `ModuleNotFoundError: No module named 'rytm_randomizer.state.a4_soft_capture'`.

- [ ] **Step 3: Implement the reducer**

Create `rytm_randomizer/state/a4_soft_capture.py`:

```python
"""Passive Analog Four soft live capture state."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Final

from ..data import ANALOG_FOUR_SYNTH_TRACK_CC_BY_MSB

SOURCE: Final[str] = "passive_cc_observation"
UNKNOWN_POLICY: Final[str] = "unknown_parameters_untouched"
TRACK_COUNT: Final[int] = 4


@dataclass(frozen=True)
class ObservedA4Parameter:
    track: int
    parameter: str
    section: str
    cc: int
    value: int
    observed_at: float


@dataclass(frozen=True)
class UnknownA4Control:
    channel: int
    control: int
    value: int
    observed_at: float
    reason: str


def _freeze_parameters(
    parameters: Mapping[str, ObservedA4Parameter] | None,
) -> Mapping[str, ObservedA4Parameter]:
    return MappingProxyType(dict(parameters or {}))


@dataclass(frozen=True)
class A4ObservedTrackState:
    track: int
    parameters: Mapping[str, ObservedA4Parameter] = field(default_factory=lambda: MappingProxyType({}))

    def __post_init__(self) -> None:
        if self.track < 1 or self.track > TRACK_COUNT:
            raise ValueError(f"A4ObservedTrackState.track must be in [1, 4], got {self.track}")
        object.__setattr__(self, "parameters", _freeze_parameters(self.parameters))


@dataclass(frozen=True)
class A4SoftCaptureSnapshot:
    tracks: tuple[A4ObservedTrackState, ...]
    source: str = SOURCE
    unknown_policy: str = UNKNOWN_POLICY
    unknown_controls: tuple[UnknownA4Control, ...] = ()
    ignored_message_count: int = 0
    out_of_scope_message_count: int = 0

    def __post_init__(self) -> None:
        if len(self.tracks) != TRACK_COUNT:
            raise ValueError("A4SoftCaptureSnapshot requires exactly four tracks")

    @property
    def known_parameter_count(self) -> int:
        return sum(len(track.parameters) for track in self.tracks)


def empty_a4_soft_capture_snapshot() -> A4SoftCaptureSnapshot:
    return A4SoftCaptureSnapshot(
        tracks=tuple(A4ObservedTrackState(track=track) for track in range(1, TRACK_COUNT + 1))
    )


def observe_a4_message(
    snapshot: A4SoftCaptureSnapshot,
    message: object,
    *,
    observed_at: float,
) -> A4SoftCaptureSnapshot:
    if getattr(message, "type", None) != "control_change":
        return A4SoftCaptureSnapshot(
            tracks=snapshot.tracks,
            unknown_controls=snapshot.unknown_controls,
            ignored_message_count=snapshot.ignored_message_count + 1,
            out_of_scope_message_count=snapshot.out_of_scope_message_count,
        )

    channel = int(getattr(message, "channel"))
    control = int(getattr(message, "control"))
    value = int(getattr(message, "value"))

    if channel < 0 or channel >= TRACK_COUNT:
        return A4SoftCaptureSnapshot(
            tracks=snapshot.tracks,
            unknown_controls=snapshot.unknown_controls,
            ignored_message_count=snapshot.ignored_message_count,
            out_of_scope_message_count=snapshot.out_of_scope_message_count + 1,
        )

    mapping = ANALOG_FOUR_SYNTH_TRACK_CC_BY_MSB.get(control)
    if mapping is None:
        return A4SoftCaptureSnapshot(
            tracks=snapshot.tracks,
            unknown_controls=snapshot.unknown_controls
            + (
                UnknownA4Control(
                    channel=channel,
                    control=control,
                    value=value,
                    observed_at=observed_at,
                    reason="unknown_cc",
                ),
            ),
            ignored_message_count=snapshot.ignored_message_count,
            out_of_scope_message_count=snapshot.out_of_scope_message_count,
        )

    track_index = channel
    track = snapshot.tracks[track_index]
    parameters = dict(track.parameters)
    parameters[mapping.parameter] = ObservedA4Parameter(
        track=channel + 1,
        parameter=mapping.parameter,
        section=mapping.section,
        cc=control,
        value=value,
        observed_at=observed_at,
    )
    tracks = list(snapshot.tracks)
    tracks[track_index] = A4ObservedTrackState(track=channel + 1, parameters=parameters)
    return A4SoftCaptureSnapshot(
        tracks=tuple(tracks),
        unknown_controls=snapshot.unknown_controls,
        ignored_message_count=snapshot.ignored_message_count,
        out_of_scope_message_count=snapshot.out_of_scope_message_count,
    )
```

Update `rytm_randomizer/state/__init__.py`:

```python
from . import (
    a4_soft_capture,
    anchor,
    anchor_validation,
    group,
    pad_mode,
    scene,
    selected_isolated_pad_validation,
    selected_target_validation,
    selection,
)

__all__ = [
    "a4_soft_capture",
    "anchor",
    "anchor_validation",
    "group",
    "pad_mode",
    "scene",
    "selected_isolated_pad_validation",
    "selected_target_validation",
    "selection",
]
```

- [ ] **Step 4: Run reducer tests**

Run:

```powershell
python -m pytest tests/test_a4_soft_capture.py -n 0
```

Expected: all tests pass.

- [ ] **Step 5: Commit**

```powershell
git add rytm_randomizer/state/a4_soft_capture.py rytm_randomizer/state/__init__.py tests/test_a4_soft_capture.py
git commit -m "feat: add Analog Four soft capture state"
```

---

### Task 3: Soft Capture Report

**Files:**
- Create: `rytm_randomizer/reports/a4_soft_capture.py`
- Modify: `rytm_randomizer/reports/__init__.py`
- Modify: `tests/test_a4_soft_capture.py`

- [ ] **Step 1: Add failing report tests**

Append to `tests/test_a4_soft_capture.py`:

```python
def test_format_report_lists_known_params_and_empty_tracks() -> None:
    from rytm_randomizer.reports.a4_soft_capture import format_a4_soft_capture_report
    from rytm_randomizer.state.a4_soft_capture import (
        empty_a4_soft_capture_snapshot,
        observe_a4_message,
    )

    snapshot = observe_a4_message(
        empty_a4_soft_capture_snapshot(),
        FakeCcMessage(channel=0, control=72, value=96),
        observed_at=10.0,
    )

    lines = format_a4_soft_capture_report(snapshot, input_name="Fake A4 In")

    assert lines[0] == "A4 soft live capture"
    assert "Input: Fake A4 In" in lines
    assert "Opened output: False" in lines
    assert "Sent MIDI: False" in lines
    assert "Track 1: 1 observed params" in lines
    assert "- OSC1 Pulsewidth: 96" in lines
    assert "Track 2: 0 observed params" in lines
    assert "Track 3: 0 observed params" in lines
    assert "Track 4: 0 observed params" in lines
    assert "Unknown parameters: left untouched" in lines


def test_format_report_counts_unknown_and_ignored_messages() -> None:
    from rytm_randomizer.reports.a4_soft_capture import format_a4_soft_capture_report
    from rytm_randomizer.state.a4_soft_capture import (
        empty_a4_soft_capture_snapshot,
        observe_a4_message,
    )

    snapshot = empty_a4_soft_capture_snapshot()
    snapshot = observe_a4_message(snapshot, FakeCcMessage(channel=0, control=99, value=10), observed_at=1.0)
    snapshot = observe_a4_message(snapshot, FakeNoteMessage(), observed_at=2.0)
    snapshot = observe_a4_message(snapshot, FakeCcMessage(channel=6, control=72, value=64), observed_at=3.0)

    lines = format_a4_soft_capture_report(snapshot, input_name="Fake A4 In")

    assert "Unknown raw CC observations: 1" in lines
    assert "Ignored non-CC messages: 1" in lines
    assert "Out-of-scope channel messages: 1" in lines
```

- [ ] **Step 2: Run report tests and verify they fail**

Run:

```powershell
python -m pytest tests/test_a4_soft_capture.py::test_format_report_lists_known_params_and_empty_tracks tests/test_a4_soft_capture.py::test_format_report_counts_unknown_and_ignored_messages -n 0
```

Expected: fails with `ModuleNotFoundError: No module named 'rytm_randomizer.reports.a4_soft_capture'`.

- [ ] **Step 3: Implement report formatter**

Create `rytm_randomizer/reports/a4_soft_capture.py`:

```python
"""Analog Four soft live capture report formatting."""

from __future__ import annotations

from typing import Final

from ..state.a4_soft_capture import A4SoftCaptureSnapshot

REPORT_TITLE: Final[str] = "A4 soft live capture"


def format_a4_soft_capture_report(
    snapshot: A4SoftCaptureSnapshot,
    *,
    input_name: str,
) -> list[str]:
    lines = [
        REPORT_TITLE,
        f"Input: {input_name}",
        "Opened output: False",
        "Sent MIDI: False",
        "",
    ]
    for track in snapshot.tracks:
        lines.append(f"Track {track.track}: {len(track.parameters)} observed params")
        for parameter in sorted(track.parameters.values(), key=lambda item: item.cc):
            lines.append(f"- {parameter.parameter}: {parameter.value}")
        lines.append("")

    lines.extend(
        [
            "Unknown parameters: left untouched",
            f"Unknown raw CC observations: {len(snapshot.unknown_controls)}",
            f"Ignored non-CC messages: {snapshot.ignored_message_count}",
            f"Out-of-scope channel messages: {snapshot.out_of_scope_message_count}",
        ]
    )
    return lines
```

If `rytm_randomizer/reports/__init__.py` exports report symbols, add:

```python
from .a4_soft_capture import REPORT_TITLE as A4_SOFT_CAPTURE_REPORT_TITLE
from .a4_soft_capture import format_a4_soft_capture_report
```

and include both names in its export surface only if that file has a maintained `__all__`.

- [ ] **Step 4: Run report and reducer tests**

Run:

```powershell
python -m pytest tests/test_a4_soft_capture.py -n 0
```

Expected: all tests pass.

- [ ] **Step 5: Commit**

```powershell
git add rytm_randomizer/reports/a4_soft_capture.py rytm_randomizer/reports/__init__.py tests/test_a4_soft_capture.py
git commit -m "feat: report Analog Four soft capture state"
```

---

### Task 4: Lazy Mido Input Boundary

**Files:**
- Modify: `rytm_randomizer/mido_provider.py`
- Modify: `tests/test_mido_provider.py`

- [ ] **Step 1: Add failing input provider tests**

Modify `_install_fake_mido` in `tests/test_mido_provider.py` to accept input surfaces:

```python
def _install_fake_mido(
    *,
    output_names: tuple[str, ...] = ("Fake Rytm",),
    input_names: tuple[str, ...] = ("Fake A4 In",),
    open_factory=None,
    open_input_factory=None,
    get_output_names_raises: BaseException | None = None,
    get_input_names_raises: BaseException | None = None,
    open_output_raises: BaseException | None = None,
    open_input_raises: BaseException | None = None,
) -> types.ModuleType:
```

Inside it, add:

```python
def _get_input_names() -> list[str]:
    if get_input_names_raises is not None:
        raise get_input_names_raises
    return list(input_names)

def _open_input(port_name: str):
    if open_input_raises is not None:
        raise open_input_raises
    if open_input_factory is None:
        return _FakeInputPort(port_name)
    return open_input_factory(port_name)

fake.get_input_names = _get_input_names  # type: ignore[attr-defined]
fake.open_input = _open_input  # type: ignore[attr-defined]
```

Add this fake input port near `_FakePort`:

```python
class _FakeInputPort:
    def __init__(self, name: str = "FakeInput") -> None:
        self.name = name
        self.closed = False

    def iter_pending(self):
        return iter(())

    def close(self) -> None:
        self.closed = True
```

Add tests:

```python
def test_list_input_names_returns_tuple_from_fake_mido() -> None:
    from rytm_randomizer.mido_provider import MidoMidiPortProvider

    _install_fake_mido(input_names=("Fake A4 In", "Other In"))
    provider = MidoMidiPortProvider()

    assert provider.list_input_names() == ("Fake A4 In", "Other In")


def test_open_input_returns_port_with_iter_pending_method() -> None:
    from rytm_randomizer.mido_provider import MidoMidiPortProvider

    fake_port = _FakeInputPort("Fake A4 In")
    _install_fake_mido(
        input_names=("Fake A4 In",),
        open_input_factory=lambda _name: fake_port,
    )
    provider = MidoMidiPortProvider()

    result = provider.open_input("Fake A4 In")

    assert result is fake_port
    assert list(result.iter_pending()) == []


def test_open_input_rejects_unknown_port_name() -> None:
    from rytm_randomizer.mido_provider import MidoMidiPortProvider
    from rytm_randomizer.real_midi_adapter import RealMidiPortError

    _install_fake_mido(input_names=("Fake A4 In",))
    provider = MidoMidiPortProvider()

    with pytest.raises(RealMidiPortError) as excinfo:
        provider.open_input("Missing In")

    assert str(excinfo.value) == "unknown_midi_input_port: Missing In"
```

- [ ] **Step 2: Run input provider tests and verify they fail**

Run:

```powershell
python -m pytest tests/test_mido_provider.py::test_list_input_names_returns_tuple_from_fake_mido tests/test_mido_provider.py::test_open_input_returns_port_with_iter_pending_method tests/test_mido_provider.py::test_open_input_rejects_unknown_port_name -n 0
```

Expected: fails because `MidoMidiPortProvider` has no `list_input_names` / `open_input`.

- [ ] **Step 3: Implement input provider methods**

In `rytm_randomizer/mido_provider.py`, add methods to `MidoMidiPortProvider`:

```python
def list_input_names(self) -> tuple[str, ...]:
    """Return available hardware MIDI input port names (lazy ``mido``)."""

    mido = _import_mido()
    try:
        names = mido.get_input_names()
    except (
        OSError,
        RuntimeError,
        ImportError,
        AttributeError,
    ) as exc:
        raise RealMidiPortError(
            "midi_input_discovery_failed",
            context={"underlying": repr(exc)},
        ) from exc
    return tuple(names)

def open_input(self, port_name: str):
    """Open a hardware MIDI input port by name (lazy ``mido``)."""

    if not isinstance(port_name, str) or not port_name:
        raise RealMidiPortError("midi_input_port_required")

    with operation("open_input", port_name=port_name):
        mido = _import_mido()
        available = self.list_input_names()
        if port_name not in available:
            raise RealMidiPortError(f"unknown_midi_input_port: {port_name}")
        try:
            port = mido.open_input(port_name)
        except (
            OSError,
            RuntimeError,
            ImportError,
            AttributeError,
        ) as exc:
            raise RealMidiPortError(
                f"unavailable_midi_input_port: {port_name}",
                context={"underlying": repr(exc)},
            ) from exc
        if not callable(getattr(port, "iter_pending", None)):
            raise RealMidiPortError(f"invalid_midi_input_port: {port_name}")
        return port
```

- [ ] **Step 4: Run provider tests**

Run:

```powershell
python -m pytest tests/test_mido_provider.py -n 0
```

Expected: all tests pass.

- [ ] **Step 5: Commit**

```powershell
git add rytm_randomizer/mido_provider.py tests/test_mido_provider.py
git commit -m "feat: add lazy MIDI input provider"
```

---

### Task 5: App Command for A4 Soft Capture

**Files:**
- Modify: `rytm_randomizer/app.py`
- Modify: `tests/test_app_entry.py`

- [ ] **Step 1: Add failing app command tests**

Append to `tests/test_app_entry.py`:

```python
def test_app_main_a4_soft_capture_requires_arm(capsys):
    from rytm_randomizer import app

    exit_code = app.main(["--a4-soft-capture"])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "--a4-soft-capture requires --arm" in captured.err


def test_app_main_arm_a4_soft_capture_opens_only_input_and_reports(
    monkeypatch,
    capsys,
):
    from rytm_randomizer import app, mido_provider

    class FakeMessage:
        type = "control_change"
        channel = 0
        control = 72
        value = 96

    class FakeInputPort:
        def __init__(self) -> None:
            self.closed = False

        def iter_pending(self):
            return iter((FakeMessage(),))

        def close(self) -> None:
            self.closed = True

    fake_input = FakeInputPort()

    monkeypatch.setattr(
        mido_provider.MidoMidiPortProvider,
        "list_input_names",
        lambda self: ("Fake A4 In",),
    )
    monkeypatch.setattr(
        mido_provider.MidoMidiPortProvider,
        "open_input",
        lambda self, port_name: fake_input,
    )

    def fail_output(self, *_args, **_kwargs):
        raise AssertionError("A4 soft capture must not open output ports")

    monkeypatch.setattr(mido_provider.MidoMidiPortProvider, "list_output_names", fail_output)
    monkeypatch.setattr(mido_provider.MidoMidiPortProvider, "open_output", fail_output)
    scripted_inputs = iter(["0", ""])
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(scripted_inputs))

    exit_code = app.main(["--arm", "--a4-soft-capture"])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert fake_input.closed is True
    assert "A4 soft live capture" in captured.out
    assert "Input: Fake A4 In" in captured.out
    assert "Opened output: False" in captured.out
    assert "Sent MIDI: False" in captured.out
    assert "Track 1: 1 observed params" in captured.out
    assert "- OSC1 Pulsewidth: 96" in captured.out
    assert captured.err == ""
```

- [ ] **Step 2: Run app tests and verify they fail**

Run:

```powershell
python -m pytest tests/test_app_entry.py::test_app_main_a4_soft_capture_requires_arm tests/test_app_entry.py::test_app_main_arm_a4_soft_capture_opens_only_input_and_reports -n 0
```

Expected: fails because argparse does not know `--a4-soft-capture`.

- [ ] **Step 3: Implement parser flag and command routing**

In `_build_parser()` in `rytm_randomizer/app.py`, add:

```python
parser.add_argument(
    "--a4-soft-capture",
    action="store_true",
    help=(
        "Open only an Analog Four MIDI input port, observe pending CC messages, "
        "and print a soft live capture report. Requires --arm."
    ),
)
```

In `main()`, route before `if args.arm:`:

```python
if args.a4_soft_capture:
    return _run_a4_soft_capture(args)
```

Add helper functions:

```python
def _choose_input_port_name(input_names: Sequence[str]) -> str | None:
    sys.stdout.write("\nAvailable MIDI inputs:\n\n")
    for index, name in enumerate(input_names):
        sys.stdout.write(f"{index}: {name}\n")

    try:
        raw = input("\nChoose the Analog Four MIDI input number: ").strip()
    except (EOFError, KeyboardInterrupt, OSError):
        sys.stderr.write("--arm --a4-soft-capture failed: no MIDI input choice provided.\n")
        return None

    try:
        chosen_index = int(raw)
        return input_names[chosen_index]
    except (ValueError, IndexError):
        sys.stderr.write("--arm --a4-soft-capture failed: invalid MIDI input choice.\n")
        return None


def _run_a4_soft_capture(args: argparse.Namespace) -> int:
    if not args.arm:
        sys.stderr.write("--a4-soft-capture requires --arm.\n")
        return 1

    from time import monotonic

    from .mido_provider import build_mido_midi_port_provider
    from .real_midi_adapter import RealMidiDependencyError, RealMidiPortError
    from .reports.a4_soft_capture import format_a4_soft_capture_report
    from .state.a4_soft_capture import empty_a4_soft_capture_snapshot, observe_a4_message

    provider = build_mido_midi_port_provider()
    try:
        input_names = provider.list_input_names()
    except (RealMidiDependencyError, RealMidiPortError) as exc:
        sys.stderr.write(f"--arm --a4-soft-capture failed: {exc}\n")
        return 1

    if not input_names:
        sys.stderr.write(
            "--arm --a4-soft-capture failed: no real MIDI input ports available. "
            "Connect the Analog Four and retry.\n"
        )
        return 1

    input_name = _choose_input_port_name(input_names)
    if input_name is None:
        return 1

    sys.stdout.write(f"\nOpening MIDI input: {input_name}\n")
    try:
        port = provider.open_input(input_name)
    except (RealMidiDependencyError, RealMidiPortError) as exc:
        sys.stderr.write(f"--arm --a4-soft-capture failed: {exc}\n")
        return 1

    snapshot = empty_a4_soft_capture_snapshot()
    try:
        sys.stdout.write("Move A4 controls, then press Enter to capture observed CCs.\n")
        try:
            input("")
        except (EOFError, KeyboardInterrupt, OSError):
            pass
        for message in port.iter_pending():
            snapshot = observe_a4_message(snapshot, message, observed_at=monotonic())
    finally:
        close = getattr(port, "close", None)
        if callable(close):
            try:
                close()
            except (OSError, RuntimeError, AttributeError):
                _shutdown_logger = _observability_get_logger(__name__)
                _shutdown_logger.debug("a4_soft_capture_input_close_failed_best_effort")

    sys.stdout.write("\n".join(format_a4_soft_capture_report(snapshot, input_name=input_name)))
    sys.stdout.write("\n")
    return 0
```

- [ ] **Step 4: Run app command tests**

Run:

```powershell
python -m pytest tests/test_app_entry.py::test_app_main_a4_soft_capture_requires_arm tests/test_app_entry.py::test_app_main_arm_a4_soft_capture_opens_only_input_and_reports -n 0
```

Expected: both tests pass.

- [ ] **Step 5: Commit**

```powershell
git add rytm_randomizer/app.py tests/test_app_entry.py
git commit -m "feat: add Analog Four soft capture app command"
```

---

### Task 6: Safety, Docs, and Verification

**Files:**
- Modify: `README.md`
- Modify: `docs/MANUAL_HARDWARE_VALIDATION.md`
- Modify: `docs/STATUS.md`
- Modify: tests only if safety output needs fixture updates.

- [ ] **Step 1: Update README passive/active wording**

Add a short note near the Analog Four / dual-machine section:

```markdown
Analog Four soft live capture is input-only: `python -m rytm_randomizer.app --arm --a4-soft-capture` opens an A4 MIDI input port, observes pending CC messages, prints a known/unknown state report, and sends no MIDI.
```

- [ ] **Step 2: Update manual hardware validation docs**

Add an Analog Four soft live capture subsection to `docs/MANUAL_HARDWARE_VALIDATION.md`:

````markdown
## Analog Four Soft Live Capture Validation

This validation is input-only. It opens the Analog Four MIDI input port, sends no MIDI, requests no SysEx, and writes no kit/project data.

Command:

```powershell
python -m rytm_randomizer.app --arm --a4-soft-capture
```

Expected:

- Select the Analog Four input port.
- Move one or more A4 controls on tracks 1-4.
- Press Enter to capture observed CCs.
- Confirm the report lists known manual-backed parameters and marks unknown parameters as untouched.
````

- [ ] **Step 3: Update status**

Add one concise line to `docs/STATUS.md` under the current section:

```markdown
- Added the Analog Four soft live capture plan: input-only CC observation, all-four-track reporting, and no hardware output.
```

- [ ] **Step 4: Run focused tests**

Run:

```powershell
python -m pytest tests/test_a4_soft_capture.py tests/test_mido_provider.py tests/test_app_entry.py -n 0
```

Expected: all selected tests pass.

- [ ] **Step 5: Run safety and architecture tests**

Run:

```powershell
python -m pytest tests/test_real_midi_passive_cli_safety.py -n 0
python -m pytest tests/architecture/test_no_side_effects.py tests/architecture/test_data_not_code.py -q
```

Expected: all selected tests pass.

- [ ] **Step 6: Run full fast suite and lint trio**

Run:

```powershell
python -m pytest -m fast
python -m ruff check .
python -m black --check --target-version=py311 .
python -m isort --profile black --check-only .
```

Expected: all commands pass.

- [ ] **Step 7: Commit docs and verification fixes**

```powershell
git add README.md docs/MANUAL_HARDWARE_VALIDATION.md docs/STATUS.md tests/test_real_midi_passive_cli_safety.py
git commit -m "docs: document Analog Four soft live capture"
```
