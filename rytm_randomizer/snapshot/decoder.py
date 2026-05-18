"""Generic ``SnapshotDecoder`` Protocol (WS-S6).

A snapshot decoder turns a raw SysEx kit/pattern dump (already stripped of
``F0``/``F7`` framing and -- if needed -- 7-bit-unpacked via
:func:`rytm_randomizer.snapshot.envelope.unpack_elektron_7bit`) into a
device-specific snapshot value. Each Elektron device family supplies its
own implementation; the Protocol is intentionally generic over the
snapshot type so the per-device decoder can return its own dataclass.

Per Gate 6 (PLAN_REQUIREMENTS) the boundary is a ``@runtime_checkable``
``Protocol``. Per the PR #21 forward-compat plan, a hand-rolled stub class
with a matching ``decode(raw, slot)`` method satisfies
``isinstance(stub, SnapshotDecoder)`` without inheritance.
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class SnapshotDecoder(Protocol):
    """Decode a raw SysEx kit/pattern dump into a device-specific snapshot.

    Implementations:

    * accept ``raw`` (the unwrapped SysEx payload bytes — caller has
      already stripped ``F0 .. F7`` framing) and ``slot`` (the 0-based
      slot/index the dump represents),
    * return a device-specific snapshot value (the concrete return type
      is up to the implementation -- callers treat it opaque and pass it
      to the matching :class:`~rytm_randomizer.snapshot.planner.MutationPlanner`),
    * raise :class:`ValueError` on malformed payloads (caller surfaces
      to the operator via a clean error message).
    """

    def decode(self, raw: bytes, slot: int) -> Any: ...
