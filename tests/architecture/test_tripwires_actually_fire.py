"""Designated tripwires must not be satisfiable by import side effects.

A "tripwire" here is a test that pins a global fact — the registered device
roster, for instance — so that changing it is a deliberate, reviewed act.
A tripwire is only worth having if it actually fails when its subject
changes.

**This is not hypothetical.** PR #240 added
``tests/test_device_family_conformance.py::test_registered_device_roster``
to pin the device roster in one place, and rewrote six ``device_count == N``
assertions to derive from ``len(all_devices())`` — delegating their
regression-detection power to that tripwire. But ``register_device()``
writes to a process-global dict at import time, so any peer test importing
``rytm_randomizer.devices.digitakt`` repopulated the registry for the whole
xdist worker. With the family's registration removed, the tripwire FAILED
when run alone and PASSED in the full suite: detection depended on worker
placement. Every mechanical gate stayed green.

What this gate does
-------------------
Asserts that each registered tripwire reads its fact from a **fresh
interpreter** rather than from in-process state a peer test can mutate. It
checks the test's source for the subprocess-isolation marker, and separately
verifies the isolation actually works by running the probe itself.

Registering a new tripwire
--------------------------
Add it to ``_TRIPWIRES`` with the module path, test name, and the probe that
reads its fact in a clean interpreter. If the fact cannot be read that way,
the tripwire is not isolable and should be rewritten until it is.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Final, NamedTuple

import pytest

pytestmark = pytest.mark.fast

PROJECT_ROOT: Final[Path] = Path(__file__).resolve().parents[2]


class Tripwire(NamedTuple):
    """One registered tripwire and the clean-interpreter probe for its fact."""

    test_module: str
    test_name: str
    probe: str
    description: str


_TRIPWIRES: Final[tuple[Tripwire, ...]] = (
    Tripwire(
        test_module="tests/test_device_family_conformance.py",
        test_name="test_registered_device_roster",
        probe=(
            "import json, sys; "
            "from rytm_randomizer.devices import all_devices; "
            "json.dump(sorted(all_devices()), sys.stdout)"
        ),
        description="the registered Elektron device roster",
    ),
)


def _run_probe(probe: str) -> list[str]:
    result = subprocess.run(
        [sys.executable, "-c", probe],
        capture_output=True,
        text=True,
        cwd=PROJECT_ROOT,
        env={**os.environ, "PYTHONPATH": str(PROJECT_ROOT)},
    )
    assert (
        result.returncode == 0
    ), f"tripwire probe failed to run:\n{result.stdout}\n{result.stderr}"
    return json.loads(result.stdout)


@pytest.mark.parametrize("tripwire", _TRIPWIRES, ids=lambda t: t.test_name)
def test_tripwire_reads_its_fact_from_a_clean_interpreter(tripwire: Tripwire) -> None:
    """The tripwire must isolate itself from in-process registration state.

    Checked structurally: the test body must spawn a subprocess. A tripwire
    that reads a module-level global directly can be satisfied by whatever a
    peer test happened to import first.
    """

    path = PROJECT_ROOT / tripwire.test_module
    assert path.is_file(), f"tripwire module missing: {tripwire.test_module}"

    source = path.read_text(encoding="utf-8")
    marker = f"def {tripwire.test_name}("
    assert marker in source, (
        f"{tripwire.test_module} no longer defines {tripwire.test_name}. "
        "If the tripwire was renamed or removed, update ``_TRIPWIRES`` in "
        "the same change set."
    )

    body = source.split(marker, 1)[1].split("\ndef ", 1)[0]
    assert "subprocess.run" in body, (
        f"{tripwire.test_name} pins {tripwire.description}, but does not read "
        "it in a subprocess. In-process reads can be satisfied by a peer "
        "test's import side effects, which makes the tripwire pass or fail "
        "depending on xdist worker placement -- see this module's docstring "
        "for the concrete incident."
    )


@pytest.mark.parametrize("tripwire", _TRIPWIRES, ids=lambda t: t.test_name)
def test_tripwire_probe_is_runnable_and_deterministic(tripwire: Tripwire) -> None:
    """The clean-interpreter probe works and returns a stable answer."""

    first = _run_probe(tripwire.probe)
    second = _run_probe(tripwire.probe)

    assert first, f"probe for {tripwire.description} returned nothing"
    assert first == second, (
        f"probe for {tripwire.description} is not deterministic:\n" f"  {first}\n  {second}"
    )
