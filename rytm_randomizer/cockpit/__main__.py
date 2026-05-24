"""``python -m rytm_randomizer.cockpit`` — launch the WebSocket sidecar.

This entrypoint is what the Tauri shell (WS-H) spawns when the cockpit
window opens. It wires the default collaborators (a fresh
:class:`MockDeviceAdapter`, the on-disk :class:`ProfileRegistry`, a fresh
:class:`HistoryStore`) into a :class:`CockpitSession`, builds the
:class:`FastAPI` app via :func:`create_app`, and hands the result to
``uvicorn.run`` on ``127.0.0.1:4317``.

The port is overridable via the ``RYTM_RAND_WS_PORT`` environment
variable so devs running two cockpits side-by-side don't collide on the
default. The host is always loopback — the cockpit sidecar is intended
for the local Tauri shell only; exposing it on a routable interface is
a deliberate operator decision deferred to a later release (the spec
calls this out under Phase 1 scope).
"""

from __future__ import annotations

import os
from datetime import datetime, timezone

import uvicorn

from .data import PadState, Snapshot, new_ulid
from .device import MockDeviceAdapter
from .history import HistoryStore
from .profiles import ProfileRegistry, default_profiles_dir
from .ws.server import create_app
from .ws.session import CockpitSession

_DEFAULT_HOST = "127.0.0.1"
"""Loopback only — never expose the cockpit to a routable interface in Phase 1."""

_DEFAULT_PORT = 4317
"""The default port the Tauri shell knows to dial. Override via RYTM_RAND_WS_PORT."""

_PORT_ENV_VAR = "RYTM_RAND_WS_PORT"
"""Environment variable the Tauri shell may set when starting multiple cockpits."""

_DEFAULT_DEVICE = "analog_rytm_mk2"
"""Identifier the bootstrap snapshot wears — matches the production hardware."""

_DEFAULT_BPM = 124.0
"""Reasonable bpm placeholder for a fresh session; the user will set their own."""


def _default_initial_snapshot() -> Snapshot:
    """Build a clean, deterministic 4-pad starting snapshot for the mock adapter.

    The exact parameter values don't matter for protocol correctness —
    they're a benign placeholder so the cockpit has *something* to render
    when the user opens the window for the first time. A real session
    overwrites them on the first SEND.
    """

    pads = tuple(
        PadState(
            pad_id=pad_id,
            machine=machine,
            params={"tun": 64, "dec": 80, "lev": 110, "flt": 64},
        )
        for pad_id, machine in (
            (1, "BD Hard"),
            (2, "SD Acoustic"),
            (3, "SY Raw"),
            (4, "FX Metal"),
        )
    )
    return Snapshot(
        snapshot_id=new_ulid(),
        device=_DEFAULT_DEVICE,
        captured_at=datetime.now(timezone.utc),
        pads=pads,
        scene_slot=None,
        bpm=_DEFAULT_BPM,
    )


def _resolve_port() -> int:
    """Pick the port to bind to: ``RYTM_RAND_WS_PORT`` overrides the default."""

    raw = os.environ.get(_PORT_ENV_VAR)
    if raw is None:
        return _DEFAULT_PORT
    return int(raw)


def build_session() -> CockpitSession:
    """Compose the default cockpit session — mock device, on-disk profiles, empty history."""

    initial_snapshot = _default_initial_snapshot()
    device = MockDeviceAdapter(initial=initial_snapshot)
    history_store = HistoryStore()
    history_store.initial(device.capture_snapshot())
    return CockpitSession(
        profile_registry=ProfileRegistry(default_profiles_dir()),
        history_store=history_store,
        device=device,
    )


def main() -> None:
    """Construct the session, build the app, run uvicorn on the resolved port."""

    session = build_session()
    app = create_app(session)
    uvicorn.run(app, host=_DEFAULT_HOST, port=_resolve_port())


if __name__ == "__main__":  # pragma: no cover - exercised via ``python -m``
    main()
