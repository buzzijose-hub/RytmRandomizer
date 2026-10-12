"""Owned QA shutdown contracts using fake processes only, never a packaged launch."""

from __future__ import annotations

import importlib.util
import subprocess
from io import BytesIO
from pathlib import Path
from types import ModuleType
from typing import cast

import pytest

pytestmark = pytest.mark.fast


@pytest.fixture
def qa() -> ModuleType:
    path = Path(__file__).parents[1] / "scripts" / "verify_reference_sound_package.py"
    spec = importlib.util.spec_from_file_location("reference_sound_qa_cleanup", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class BrokenInput(BytesIO):
    def write(self, data: bytes) -> int:
        raise BrokenPipeError("private pipe detail")


class ClosedInput(BytesIO):
    def flush(self) -> None:
        raise ValueError("private closed pipe detail")

    def close(self) -> None:
        super().close()
        raise OSError("private close detail")


class OwnedProcess:
    def __init__(self, exits_after: int | None = 1, *, stopped: bool = False) -> None:
        self.stdin: BytesIO | None = BytesIO()
        self.returncode: int | None = 0 if stopped else None
        self.exits_after = exits_after
        self.events: list[object] = []
        self.stop_failures: set[str] = set()

    def poll(self) -> int | None:
        return self.returncode

    def wait(self, timeout: float) -> int:
        self.events.append(timeout)
        if (
            self.exits_after is None
            or sum(isinstance(item, int) for item in self.events) < self.exits_after
        ):
            raise subprocess.TimeoutExpired("owned-only", timeout)
        self.returncode = 0
        return 0

    def terminate(self) -> None:
        self.events.append("terminate")
        if "terminate" in self.stop_failures:
            raise OSError("private terminate detail")

    def kill(self) -> None:
        self.events.append("kill")
        if "kill" in self.stop_failures:
            raise OSError("private kill detail")


@pytest.mark.parametrize(
    "exits_after,expected",
    [(1, [12]), (2, [12, "terminate", 5]), (3, [12, "terminate", 5, "kill", 5])],
)
def test_graceful_terminate_and_kill_are_owned_bounded_and_reaped(
    qa: ModuleType, exits_after: int, expected: list[object]
) -> None:
    process = OwnedProcess(exits_after)
    qa._stop_owned_sidecar(cast(subprocess.Popen[bytes], process))
    assert process.events == expected
    assert process.returncode == 0
    assert process.stdin is not None and process.stdin.closed


@pytest.mark.parametrize("stdin", [None, BrokenInput(), ClosedInput()])
def test_broken_or_missing_stdin_cannot_skip_shutdown(
    qa: ModuleType, stdin: BytesIO | None
) -> None:
    process = OwnedProcess(3)
    process.stdin = stdin
    qa._stop_owned_sidecar(cast(subprocess.Popen[bytes], process))
    assert process.events == [12, "terminate", 5, "kill", 5]
    assert process.returncode == 0


def test_already_exited_child_is_not_signalled(qa: ModuleType) -> None:
    process = OwnedProcess(stopped=True)
    qa._stop_owned_sidecar(cast(subprocess.Popen[bytes], process))
    assert process.events == []
    assert process.stdin is not None and process.stdin.closed


@pytest.mark.parametrize("stop_failures", [{"terminate"}, {"terminate", "kill"}])
def test_stop_errors_still_escalate_and_reap(qa: ModuleType, stop_failures: set[str]) -> None:
    process = OwnedProcess(3)
    process.stop_failures = stop_failures
    qa._stop_owned_sidecar(cast(subprocess.Popen[bytes], process))
    assert process.events == [12, "terminate", 5, "kill", 5]
    assert process.returncode == 0


def test_process_exit_race_during_terminate_is_a_success(qa: ModuleType) -> None:
    process = OwnedProcess(3)

    def stopped_while_terminating() -> None:
        process.returncode = 0
        raise ProcessLookupError("private process detail")

    process.terminate = stopped_while_terminating
    qa._stop_owned_sidecar(cast(subprocess.Popen[bytes], process))
    assert process.events == [12]


@pytest.mark.parametrize("primary_failure", [False, True])
def test_failed_shutdown_always_preserves_log_and_never_masks_the_primary_failure(
    qa: ModuleType, tmp_path: Path, primary_failure: bool
) -> None:
    process = OwnedProcess(None)
    backend_log = tmp_path / "backend.log"
    receipt = tmp_path / "receipt" / "proof.json"
    expected = "original QA failure" if primary_failure else "package proof is incomplete"
    with backend_log.open("wb") as log:
        log.write(b"private backend diagnostics\n")
        with pytest.raises(RuntimeError, match=expected) as failure:
            try:
                if primary_failure:
                    raise RuntimeError("original QA failure")
            finally:
                qa._finish_owned_sidecar(
                    cast(subprocess.Popen[bytes], process), log, backend_log, receipt
                )
    assert (receipt.parent / "backend-private.log").read_bytes() == b"private backend diagnostics\n"
    assert not receipt.exists()
    assert process.events == [12, "terminate", 5, "kill", 5]
    assert process.stdin is not None and process.stdin.closed
    if primary_failure:
        assert failure.value.__notes__ == [
            "Owned sidecar shutdown failed; package proof is incomplete."
        ]


def test_successful_shutdown_preserves_exact_private_log(qa: ModuleType, tmp_path: Path) -> None:
    process = OwnedProcess()
    backend_log = tmp_path / "backend.log"
    receipt = tmp_path / "receipt" / "proof.json"
    with backend_log.open("wb") as log:
        log.write(b"private backend diagnostics\n")
        qa._finish_owned_sidecar(cast(subprocess.Popen[bytes], process), log, backend_log, receipt)
    assert (receipt.parent / "backend-private.log").read_bytes() == b"private backend diagnostics\n"
    assert not receipt.exists()
