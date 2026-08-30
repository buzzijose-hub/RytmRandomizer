"""Generic ``MutationPlanner`` Protocol (WS-S6).

A mutation planner takes a decoded snapshot (whatever shape the matching
:class:`~rytm_randomizer.snapshot.decoder.SnapshotDecoder` returned) and a
mutation depth, and produces a device-specific plan describing the changes
to render. Each Elektron device family supplies its own implementation.

Per Gate 6 (PLAN_REQUIREMENTS) the boundary is a ``@runtime_checkable``
``Protocol``. The plan return type is intentionally device-specific:
callers pass it back to the device's own ``to_mock_messages`` /
``to_cc_messages`` renderers (see
:class:`rytm_randomizer.devices.base.Device`) and never inspect it.
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from .mutation_scope import DEFAULT_MUTATION_SCOPE, MutationScope


@runtime_checkable
class MutationPlanner(Protocol):
    """Plan a depth-bounded mutation against a decoded snapshot.

    Implementations:

    * accept ``snapshot`` (the value returned by the matching
      :class:`~rytm_randomizer.snapshot.decoder.SnapshotDecoder`) and
      ``depth`` (a non-negative integer; ``0`` typically means no
      mutation, higher values widen the parameter perturbation window),
    * return a device-specific plan value (opaque to callers),
    * raise :class:`ValueError` if ``snapshot`` is of an unexpected
      shape, or ``depth`` is negative or beyond the device's documented
      range.
    """

    def plan(
        self,
        snapshot: Any,
        depth: int,
        *,
        scope: MutationScope = DEFAULT_MUTATION_SCOPE,
    ) -> Any: ...
