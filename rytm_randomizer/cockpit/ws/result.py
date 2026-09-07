"""Transport-neutral command-handler result container."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class HandlerResult:
    """A command acknowledgement plus events emitted after that acknowledgement."""

    ack: dict[str, object]
    events: list[dict[str, object]] = field(default_factory=list[dict[str, object]])


__all__ = ["HandlerResult"]
