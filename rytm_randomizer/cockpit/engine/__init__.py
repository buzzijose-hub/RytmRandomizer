"""Cockpit mutation engine — deterministic pure-function mutation pipeline.

The engine takes a ``Snapshot`` (the device's current state) + a
``ProfileModel`` (the operator's taste) + a ``depth`` slider position
+ a ``seed`` (32-bit unsigned), and returns a ``MutationCandidate``
that the UI previews and the device adapter (WS-F) eventually sends.

Two hard guarantees:

1. **Determinism.** ``mutate(s, p, d, seed)`` always returns the same
   ``MutationCandidate.to_dict()`` byte stream given the same inputs,
   independent of process, run, OS, Python version, or wall clock.
2. **C-portability.** The algorithm (PRNG, iteration order, arithmetic,
   clamping, status thresholds) is encoded in
   :doc:`spec.md <./spec>` so a C99 / Rust embedded implementation can
   reproduce ``MutationCandidate.pad_deltas`` byte-for-byte. See
   ``tests/cockpit/fixtures/engine_conformance/*.json`` for the locked
   conformance corpus.

The engine never opens MIDI, never touches the wall clock except for
``candidate_id`` generation (a ULID), and never depends on anything in
``rytm_randomizer`` outside ``cockpit.data``.
"""

from __future__ import annotations

from .mutate import mutate
from .prng import xorshift32
from .send_plan import prepare_send_plan

__all__ = ["mutate", "prepare_send_plan", "xorshift32"]
