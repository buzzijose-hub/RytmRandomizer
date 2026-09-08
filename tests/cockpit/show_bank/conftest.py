"""Shared Show Kit Forge workspace harnesses for boundary and evidence tests."""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Final

from cockpit.conftest import MutableClock, capture_fixed_frame

from conftest import (
    analog_four_saved_kit_frame,
    elektron_syx_message,
    rytm_real_layout_kit_payload,
)
from rytm_randomizer.cockpit.capture import (
    ANALOG_FOUR_DEVICE_ID,
    ANALOG_RYTM_DEVICE_ID,
    KitCaptureResult,
)
from rytm_randomizer.cockpit.data import ProfileModel
from rytm_randomizer.cockpit.data.show_bank import ShowKitCandidate
from rytm_randomizer.cockpit.profiles import ProfileRegistry
from rytm_randomizer.cockpit.show_bank.store import ShowBankStore
from rytm_randomizer.cockpit.show_bank.workspace import ShowKitForgeWorkspace

SHOW_BANK_BOUNDARY_NOW: Final[datetime] = datetime(2026, 9, 4, 16, 0, tzinfo=timezone.utc)


@dataclass
class ShowBankHarness:
    """One isolated paired source, deterministic clock, profile, and local store."""

    workspace: ShowKitForgeWorkspace
    store: ShowBankStore
    rytm: KitCaptureResult
    analog_four: KitCaptureResult
    profile: ProfileModel
    bank_id: str
    entry_id: str
    clock: MutableClock

    @property
    def captures(self) -> dict[str, KitCaptureResult]:
        return {
            ANALOG_RYTM_DEVICE_ID: self.rytm,
            ANALOG_FOUR_DEVICE_ID: self.analog_four,
        }


def build_show_bank_harness(tmp_path: Path) -> ShowBankHarness:
    """Build immutable source anchors from canonical shared Elektron fixtures."""

    rytm = replace(
        capture_fixed_frame(
            ANALOG_RYTM_DEVICE_ID,
            elektron_syx_message(rytm_real_layout_kit_payload(b"BOUNDARY RYTM")),
        ),
        captured_at=SHOW_BANK_BOUNDARY_NOW - timedelta(minutes=2),
    )
    analog_four = replace(
        capture_fixed_frame(
            ANALOG_FOUR_DEVICE_ID,
            analog_four_saved_kit_frame(name=b"BOUNDARY A4"),
        ),
        captured_at=SHOW_BANK_BOUNDARY_NOW - timedelta(minutes=2),
    )
    clock = MutableClock(SHOW_BANK_BOUNDARY_NOW)
    ids = iter(("bank-boundary", "cue-source", "cue-copy", "cue-copy-two"))
    store = ShowBankStore(tmp_path / "banks", clock=clock)
    workspace = ShowKitForgeWorkspace(
        store,
        clock=clock,
        id_factory=lambda _prefix: next(ids),
    )
    bank = workspace.create_bank(
        name="Boundary show",
        description="Mock-only boundary coverage",
        notes=("No hardware I/O.",),
    )
    entry = workspace.adopt_sources(
        bank.bank_id,
        bank.revision,
        captures={
            ANALOG_RYTM_DEVICE_ID: rytm,
            ANALOG_FOUR_DEVICE_ID: analog_four,
        },
        rytm_fingerprint=rytm.fingerprint,
        analog_four_fingerprint=analog_four.fingerprint,
        rytm_slot=20,
        analog_four_slot=21,
    )
    profile = ProfileRegistry(tmp_path / "profiles").list_profiles()[0]
    return ShowBankHarness(
        workspace=workspace,
        store=store,
        rytm=rytm,
        analog_four=analog_four,
        profile=profile,
        bank_id=bank.bank_id,
        entry_id=entry.entry_id,
        clock=clock,
    )


def generate_show_bank_candidates(
    harness: ShowBankHarness, *, count: int = 2, seed: int = 91
) -> tuple[ShowKitCandidate, ...]:
    """Generate deterministic A4 candidates while locking every Rytm pad."""

    bank = harness.workspace.bank(harness.bank_id)
    return harness.workspace.generate_candidates(
        harness.bank_id,
        harness.entry_id,
        bank.revision,
        profile=harness.profile,
        depth_preset="small",
        depth=0.25,
        seed=seed,
        candidate_count=count,
        rytm_targets=(),
        rytm_locks=tuple(range(1, 13)),
        analog_four_targets=(1,),
        analog_four_locks=(),
    )
