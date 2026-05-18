"""Passive mock 12-pad snapshot fixtures for Live Snapshot planning.

Fixtures in this module are hand-authored metadata. They do not decode SysEx,
request hardware dumps, open MIDI ports, receive MIDI, send MIDI, write SysEx,
execute commands, or mutate hardware.
"""

from __future__ import annotations

from dataclasses import dataclass

from ..essence.machine_catalog import SupportStatus, get_machine_profile
from ..performance.modes import CaptureStatus, SnapshotState


@dataclass(frozen=True)
class SnapshotPadFixture:
    """One captured pad in a passive snapshot fixture."""

    pad: int
    machine_key: str
    machine_label: str
    machine_value: int | None
    support_status: SupportStatus
    baseline_parameter_count: int


@dataclass(frozen=True)
class SnapshotFixture:
    """A passive mock snapshot fixture."""

    key: str
    label: str
    source_note: str
    capture_status: CaptureStatus
    expected_pad_count: int
    pads: tuple[SnapshotPadFixture, ...]

    @property
    def mapped_pad_count(self) -> int:
        return sum(1 for pad in self.pads if pad.support_status == "mutable_v134")

    @property
    def future_only_pad_count(self) -> int:
        return sum(1 for pad in self.pads if pad.support_status == "needs_manual_mapping")


_AM9_SLOT_01_PAD_SPECS: tuple[tuple[int, str, int], ...] = (
    (1, "bd_hard", 7),
    (2, "bd_classic", 7),
    (3, "sy_raw", 8),
    (4, "bd_acoustic", 7),
    (5, "hat_family", 0),
    (6, "hat_family", 0),
    (7, "rs_family", 0),
    (8, "sd_hard", 7),
    (9, "bd_fm", 7),
    (10, "bd_classic", 7),
    (11, "sd_fm", 7),
    (12, "bd_plastic", 7),
)


def list_snapshot_fixtures() -> tuple[SnapshotFixture, ...]:
    """Return all passive snapshot fixtures."""

    return SNAPSHOT_FIXTURES


def get_snapshot_fixture(key: str) -> SnapshotFixture:
    """Return a passive snapshot fixture by key."""

    normalized = str(key).strip().lower()
    for fixture in SNAPSHOT_FIXTURES:
        if fixture.key == normalized:
            return fixture
    raise KeyError(f"unknown snapshot fixture: {key!r}")


def snapshot_state_from_fixture(fixture: SnapshotFixture) -> SnapshotState:
    """Return a SnapshotState view for a passive fixture."""

    return SnapshotState(
        mode="live_snapshot",
        capture_status=fixture.capture_status,
        expected_pad_count=fixture.expected_pad_count,
        captured_pad_count=len(fixture.pads),
    )


def format_snapshot_fixture_report(fixture: SnapshotFixture) -> list[str]:
    """Format a deterministic passive snapshot fixture report."""

    lines = [
        "RytmRandomizer passive Snapshot Fixture Report",
        f"Fixture: {fixture.label}",
        f"Key: {fixture.key}",
        f"Capture status: {fixture.capture_status}",
        (
            "Pad counts: "
            f"total {len(fixture.pads)} / "
            f"mapped {fixture.mapped_pad_count} / "
            f"future-only {fixture.future_only_pad_count}"
        ),
        "Pads:",
    ]
    lines.extend(_format_pad_line(pad) for pad in fixture.pads)
    lines.extend(
        [
            "Safety:",
            "- passive/read-only",
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


def _build_snapshot_pad(
    pad: int,
    machine_key: str,
    baseline_parameter_count: int,
) -> SnapshotPadFixture:
    machine = get_machine_profile(machine_key)
    return SnapshotPadFixture(
        pad=pad,
        machine_key=machine.key,
        machine_label=machine.label,
        machine_value=machine.machine_value,
        support_status=machine.support_status,
        baseline_parameter_count=baseline_parameter_count,
    )


SNAPSHOT_FIXTURES: tuple[SnapshotFixture, ...] = (
    SnapshotFixture(
        key="am9-slot-01",
        label="AM9 Slot 01 Mock 12-pad Snapshot",
        source_note=(
            "Hand-authored AM9-inspired fixture; not decoded from live SysEx or "
            "used for restore."
        ),
        capture_status="captured",
        expected_pad_count=12,
        pads=tuple(
            _build_snapshot_pad(pad, machine_key, baseline_count)
            for pad, machine_key, baseline_count in _AM9_SLOT_01_PAD_SPECS
        ),
    ),
)


def _format_pad_line(pad: SnapshotPadFixture) -> str:
    support_label = "mutable" if pad.support_status == "mutable_v134" else "future"
    return (
        f"- Pad {pad.pad}: {pad.machine_label} [{support_label}] / "
        f"baseline params {pad.baseline_parameter_count}"
    )


__all__ = [
    "SnapshotFixture",
    "SnapshotPadFixture",
    "format_snapshot_fixture_report",
    "get_snapshot_fixture",
    "list_snapshot_fixtures",
    "snapshot_state_from_fixture",
]
