"""Centerpiece WS-R E2E test: the V1.34 canonical operator validation flow.

The V1.34 docs spell out the operator-command sequence used to validate the
randomizer against a real Analog Rytm:

    SCN -> GM -> S1A -> S3A -> S3B -> S4B -> S5 -> 1 -> Z -> Q

This test drives the **real entry point** -- :func:`rytm_randomizer.app.main`
-- through that exact sequence in ``--dry-run`` mode against
:class:`MockMidiSender`, with :mod:`random` seeded by :data:`E2E_RANDOM_SEED`
(``12345``) for full determinism. The captured MIDI message stream is then
asserted byte-for-byte against the committed golden file
``_golden/canonical_validation_flow.json``.

On the very first run (when the golden does not exist yet) the test bootstraps
the golden file from the actual recorded stream and fails with a clear
message asking the operator to review and commit it. Every subsequent run
asserts equality.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from .conftest import (
    CANONICAL_VALIDATION_COMMANDS,
    E2E_RANDOM_SEED,
    GOLDEN_DIR,
    CapturedMessage,
    load_golden,
    run_canonical_dry_run,
    save_golden,
)

GOLDEN_NAME = "canonical_validation_flow"


def test_canonical_validation_flow_matches_golden(capsys: pytest.CaptureFixture[str]) -> None:
    """``SCN -> GM -> S1A -> S3A -> S3B -> S4B -> S5 -> 1 -> Z -> Q`` against
    the dry-run mock must produce the committed golden message sequence.

    The full ordered sequence of CC messages -- their channel, control number,
    and value -- is compared against ``_golden/canonical_validation_flow.json``.
    With the project-wide seed :data:`E2E_RANDOM_SEED`, the randomization core
    in :mod:`rytm_randomizer.randomization` produces identical outputs every
    run, so any drift is a real behavioral regression.
    """

    result = run_canonical_dry_run(CANONICAL_VALIDATION_COMMANDS, capsys=capsys)

    assert result.exit_code == 0, (
        f"app.main(['--dry-run']) returned non-zero exit code: {result.exit_code}\n"
        f"stderr: {result.stderr}"
    )
    assert result.captured, "Canonical flow produced zero MIDI messages -- expected hundreds"

    actual_dicts = [msg.to_dict() for msg in result.captured]
    expected = load_golden(GOLDEN_NAME)

    if expected is None:
        # First-run bootstrap: write the golden so the operator can review it
        # in the resulting diff, then fail loudly. Subsequent runs are pure
        # asserts.
        golden_path = save_golden(GOLDEN_NAME, result.captured)
        pytest.fail(
            "Bootstrapped golden file at "
            f"{golden_path} ({len(result.captured)} messages). "
            "Review the diff, commit it, and re-run pytest -- this fail-on-create "
            "is intentional so a missing golden cannot silently pass."
        )

    assert len(actual_dicts) == len(expected), (
        f"Canonical flow produced {len(actual_dicts)} messages, "
        f"golden has {len(expected)}. Either the flow drifted or the seed "
        f"({E2E_RANDOM_SEED}) needs re-baselining (do this only with intent)."
    )
    assert actual_dicts == expected, (
        "Canonical flow MIDI stream diverged from the golden. "
        "Run with -vv to see the diff. If this is a legitimate change, "
        "delete tests/e2e/_golden/canonical_validation_flow.json, re-run "
        "to regenerate it, and commit the new golden with a behavioral "
        "rationale in the commit message."
    )


def test_canonical_flow_is_deterministic_across_repeats(capsys: pytest.CaptureFixture[str]) -> None:
    """Re-running the canonical flow back-to-back must yield identical streams.

    This is a determinism contract test: if a future refactor introduces a
    non-seeded RNG (e.g. ``random.Random()`` with no seed), this test would
    catch it before the golden-comparison test surfaced as flaky.
    """

    first = run_canonical_dry_run(CANONICAL_VALIDATION_COMMANDS, capsys=capsys)
    second = run_canonical_dry_run(CANONICAL_VALIDATION_COMMANDS, capsys=capsys)

    assert first.exit_code == 0
    assert second.exit_code == 0
    assert first.captured == second.captured, (
        "Two seeded canonical runs produced different MIDI streams. "
        "Determinism contract broken -- check that all RNG usage threads "
        "through random.seed() / the injected Random instance, never a "
        "fresh, unseeded Random()."
    )


def test_canonical_flow_exits_cleanly_with_q(capsys: pytest.CaptureFixture[str]) -> None:
    """The trailing ``Q`` must drive the shell out via exit code 0, not EOFError."""

    result = run_canonical_dry_run(CANONICAL_VALIDATION_COMMANDS, capsys=capsys)

    assert result.exit_code == 0
    assert "Exiting." in result.stdout
    assert "Dry-run complete." in result.stdout


def test_canonical_flow_emits_messages_on_all_four_channels(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """A canonical run drives all 4 group pads, so all 4 MIDI channels (0-3)
    must appear in the captured stream. A regression that silently routes
    everything to one channel would be caught here.
    """

    result = run_canonical_dry_run(CANONICAL_VALIDATION_COMMANDS, capsys=capsys)

    channels_used = {msg.channel for msg in result.captured}
    assert channels_used == {0, 1, 2, 3}, (
        f"Canonical flow only used channels {sorted(channels_used)}; "
        "expected all of 0-3 (one per pad)."
    )


def test_golden_file_is_committed_and_well_formed() -> None:
    """Operational sanity: the golden file must exist on disk, be valid JSON,
    and every entry must have the expected schema.
    """

    golden_path: Path = GOLDEN_DIR / f"{GOLDEN_NAME}.json"
    assert golden_path.exists(), (
        f"Golden file missing at {golden_path}. Run the canonical-flow test "
        "once to bootstrap it, then commit the result."
    )

    with golden_path.open("r", encoding="utf-8") as fh:
        data = json.load(fh)

    assert isinstance(data, list), "Golden must be a JSON array"
    assert data, "Golden must not be empty"
    required_keys = {"message_type", "channel", "control", "value"}
    for entry in data:
        assert required_keys.issubset(entry.keys()), entry
        assert isinstance(entry["channel"], int)
        assert isinstance(entry["control"], int)
        assert isinstance(entry["value"], int)
