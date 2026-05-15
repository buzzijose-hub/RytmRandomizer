"""End-to-end (E2E) test suite for the RytmRandomizer package (WS-R).

These tests drive the **real entry point** -- :func:`rytm_randomizer.app.main`
-- through the documented operator-command flows from the V1.34 baseline.
They run entirely in-process against
:class:`rytm_randomizer.mock_midi.MockMidiSender` via the ``--dry-run`` mode,
so the suite is fully automatable in CI: no hardware, no real MIDI library,
no subprocess overhead.

Randomization is seeded deterministically by the fixture in
:mod:`tests.e2e.conftest` (seed ``12345`` -- documented there) so every run
produces identical MIDI message sequences. A committed golden file
(``tests/e2e/_golden/canonical_validation_flow.json``) captures the canonical
``SCN -> GM -> S1A -> S3A -> S3B -> S4B -> S5 -> 1 -> Z -> Q`` flow's full
ordered message sequence; the canonical-flow test asserts byte-for-byte
parity against it on every run.
"""
