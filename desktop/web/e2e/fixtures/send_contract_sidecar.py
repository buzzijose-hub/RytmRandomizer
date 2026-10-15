"""Browser-to-production-handler contract with a test-only in-memory output.

This harness is outside the shipped package. It cannot discover or open MIDI.
The production sidecar has no environment flag for selecting this harness.
"""

from __future__ import annotations

import json
import os
import secrets
from pathlib import Path
from typing import Final

import uvicorn
from cockpit.conftest import make_default_snapshot

from rytm_randomizer.cockpit.device import MockDeviceAdapter
from rytm_randomizer.cockpit.history import HistoryStore
from rytm_randomizer.cockpit.profiles import ProfileRegistry
from rytm_randomizer.cockpit.ws.server import create_app
from rytm_randomizer.cockpit.ws.session import CockpitSession
from rytm_randomizer.senders.armed_apply import ArmedApplySession

OUTPUT_NAME: Final[str] = "TEST_ONLY_CC7_RECORDER"


class MemoryOutput:
    """Record the real ArmedApply seam's resolved triples, without a backend."""

    def __init__(self, receipt_path: Path) -> None:
        self.receipt_path = receipt_path
        self.packets: list[object] = []
        self.closed = 0
        self.flush()

    def flush(self) -> None:
        self.receipt_path.write_text(
            json.dumps({"simulated_packets": self.packets, "closed": self.closed}),
            encoding="utf-8",
        )

    def send(self, message: object) -> None:
        self.packets.append(message)
        self.flush()

    def close(self) -> None:
        self.closed += 1
        self.flush()


class MemoryOpener:
    def __init__(self, output: MemoryOutput) -> None:
        self.output = output

    def open_exact(self, name: str) -> MemoryOutput:
        if name != OUTPUT_NAME:
            raise ValueError("test-only output name mismatch")
        return self.output


if __name__ == "__main__":
    token_file = Path(os.environ["RYTM_RAND_WS_TOKEN_FILE"])
    token = secrets.token_urlsafe(32)
    token_file.write_text(token, encoding="utf-8")
    initial = make_default_snapshot()
    history = HistoryStore()
    history.initial(initial)
    output = MemoryOutput(token_file.parent / "send-contract-receipt.json")
    seam = ArmedApplySession(opener=MemoryOpener(output), port_name=OUTPUT_NAME, arm_token=token)
    seam.arm(token)
    session = CockpitSession(
        profile_registry=ProfileRegistry(token_file.parent / "profiles"),
        history_store=history,
        device=MockDeviceAdapter(initial),
        armed_apply=seam,
        depth=0.1,
        seed=42,
    )
    uvicorn.run(
        create_app(session, token=token),
        host="127.0.0.1",
        port=int(os.environ["RYTM_RAND_WS_PORT"]),
        log_level="warning",
    )
