"""Coverage tests for ``rytm_randomizer.mido_provider``.

These tests exercise the concrete ``mido``-backed real-MIDI port provider via
``sys.modules`` injection of a fake ``mido`` module, so:

* No real ``mido`` is imported (the architecture safety test that forbids any
  eager ``import mido`` in the package keeps holding -- we only mutate
  ``sys.modules`` AFTER package import).
* No hardware ports are opened.
* The lazy-import branch in :func:`_import_mido` is exercised both on the
  happy path (fake module installed) AND on the missing-dependency path
  (``ImportError`` from the real interpreter).

An autouse fixture snapshots ``sys.modules`` and restores it after every
test so neither the fake ``mido`` nor a real ``mido`` (if present in the
host venv) leaks across tests. The companion module-load safety tests in
``tests/test_real_midi_import_safety.py`` and
``tests/test_real_midi_adapter_boundary.py`` therefore continue to pass.
"""

from __future__ import annotations

import builtins
import sys
import types
from pathlib import Path

import pytest

# WS-M4: mark this module as fast-suite; pytest -m fast skips the 505
# warm-worker V1.34 parity fixtures and runs in <60s.
pytestmark = pytest.mark.fast

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# ---------------------------------------------------------------------------
# Isolation
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _restore_sys_modules():
    """Snapshot ``sys.modules`` and restore it after each test.

    Prevents the fake ``mido`` injected here -- or a real ``mido`` pulled in
    by an interleaved test -- from leaking into other tests that assert
    ``"mido" not in sys.modules`` (the package-import-safety contract).
    """

    snapshot = dict(sys.modules)
    try:
        yield
    finally:
        for name in list(sys.modules):
            if name not in snapshot:
                del sys.modules[name]
        for name, module in snapshot.items():
            sys.modules[name] = module


class _FakePort:
    """Stand-in for a ``mido`` output port: records ``send`` calls."""

    def __init__(self, name: str = "FakePort") -> None:
        self.name = name
        self.sent: list[object] = []
        self.closed = False

    def send(self, message: object) -> None:
        self.sent.append(message)

    def close(self) -> None:  # parity with real mido ports, never asserted
        self.closed = True


def _install_fake_mido(
    *,
    output_names: tuple[str, ...] = ("Fake Rytm",),
    open_factory=None,
    get_output_names_raises: BaseException | None = None,
    open_output_raises: BaseException | None = None,
) -> types.ModuleType:
    """Install a minimal fake ``mido`` module into ``sys.modules``.

    The fake exposes the two attributes the provider uses --
    ``get_output_names`` and ``open_output`` -- and lets the caller configure
    the returned names, the factory used to mint ports, and optional errors
    to raise from each surface (for boundary tests).
    """

    fake = types.ModuleType("mido")

    def _get_output_names() -> list[str]:
        if get_output_names_raises is not None:
            raise get_output_names_raises
        return list(output_names)

    def _open_output(port_name: str):
        if open_output_raises is not None:
            raise open_output_raises
        if open_factory is None:
            return _FakePort(port_name)
        return open_factory(port_name)

    fake.get_output_names = _get_output_names  # type: ignore[attr-defined]
    fake.open_output = _open_output  # type: ignore[attr-defined]
    sys.modules["mido"] = fake
    return fake


# ---------------------------------------------------------------------------
# Builder + module shape
# ---------------------------------------------------------------------------


def test_build_mido_midi_port_provider_returns_provider_instance() -> None:
    from rytm_randomizer.mido_provider import MidoMidiPortProvider, build_mido_midi_port_provider

    provider = build_mido_midi_port_provider()

    assert isinstance(provider, MidoMidiPortProvider)


def test_mido_provider_module_does_not_import_mido_at_load() -> None:
    """Importing the provider module must not pull in ``mido``."""

    # Snapshot is restored by the autouse fixture, so we can safely poke here.
    for name in ("mido", "rtmidi"):
        sys.modules.pop(name, None)

    import rytm_randomizer.mido_provider  # noqa: F401

    assert "mido" not in sys.modules
    assert "rtmidi" not in sys.modules


def test_mido_provider_public_api_is_stable() -> None:
    import rytm_randomizer.mido_provider as module

    assert module.__all__ == ["MidoMidiPortProvider", "build_mido_midi_port_provider"]


# ---------------------------------------------------------------------------
# _import_mido()
# ---------------------------------------------------------------------------


def test_import_mido_returns_installed_module() -> None:
    from rytm_randomizer.mido_provider import _import_mido

    fake = _install_fake_mido()

    result = _import_mido()

    assert result is fake


def test_import_mido_raises_dependency_error_when_mido_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """When ``mido`` is not installed, the helper raises a guarded error."""

    from rytm_randomizer.mido_provider import _import_mido
    from rytm_randomizer.real_midi_adapter import RealMidiDependencyError

    # Forcibly remove any (real or fake) ``mido`` so the import fresh-fails.
    sys.modules.pop("mido", None)

    real_import = builtins.__import__

    def _block_mido(name, *args, **kwargs):
        if name == "mido":
            raise ImportError("forced-missing: mido")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", _block_mido)

    with pytest.raises(RealMidiDependencyError) as excinfo:
        _import_mido()

    assert "mido_not_installed" in str(excinfo.value)


# ---------------------------------------------------------------------------
# list_output_names()
# ---------------------------------------------------------------------------


def test_list_output_names_returns_tuple_from_fake_mido() -> None:
    from rytm_randomizer.mido_provider import MidoMidiPortProvider

    _install_fake_mido(output_names=("Fake Rytm", "Other Port"))
    provider = MidoMidiPortProvider()

    names = provider.list_output_names()

    assert names == ("Fake Rytm", "Other Port")
    assert isinstance(names, tuple)


def test_list_output_names_empty_when_backend_reports_no_ports() -> None:
    from rytm_randomizer.mido_provider import MidoMidiPortProvider

    _install_fake_mido(output_names=())
    provider = MidoMidiPortProvider()

    assert provider.list_output_names() == ()


def test_list_output_names_propagates_dependency_error_when_mido_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from rytm_randomizer.mido_provider import MidoMidiPortProvider
    from rytm_randomizer.real_midi_adapter import RealMidiDependencyError

    sys.modules.pop("mido", None)

    real_import = builtins.__import__

    def _block_mido(name, *args, **kwargs):
        if name == "mido":
            raise ImportError("forced-missing: mido")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", _block_mido)
    provider = MidoMidiPortProvider()

    with pytest.raises(RealMidiDependencyError):
        provider.list_output_names()


# ---------------------------------------------------------------------------
# open_output() defensive paths (no real backend touched)
# ---------------------------------------------------------------------------


def test_open_output_rejects_non_string_port_name() -> None:
    from rytm_randomizer.mido_provider import MidoMidiPortProvider
    from rytm_randomizer.real_midi_adapter import RealMidiPortError

    provider = MidoMidiPortProvider()

    with pytest.raises(RealMidiPortError) as excinfo:
        provider.open_output(123)  # type: ignore[arg-type]

    assert str(excinfo.value) == "midi_output_port_required"


def test_open_output_rejects_empty_port_name() -> None:
    from rytm_randomizer.mido_provider import MidoMidiPortProvider
    from rytm_randomizer.real_midi_adapter import RealMidiPortError

    provider = MidoMidiPortProvider()

    with pytest.raises(RealMidiPortError) as excinfo:
        provider.open_output("")

    assert str(excinfo.value) == "midi_output_port_required"


def test_open_output_rejects_none_port_name() -> None:
    from rytm_randomizer.mido_provider import MidoMidiPortProvider
    from rytm_randomizer.real_midi_adapter import RealMidiPortError

    provider = MidoMidiPortProvider()

    with pytest.raises(RealMidiPortError):
        provider.open_output(None)  # type: ignore[arg-type]


def test_open_output_rejects_unknown_port_name() -> None:
    from rytm_randomizer.mido_provider import MidoMidiPortProvider
    from rytm_randomizer.real_midi_adapter import RealMidiPortError

    _install_fake_mido(output_names=("Fake Rytm",))
    provider = MidoMidiPortProvider()

    with pytest.raises(RealMidiPortError) as excinfo:
        provider.open_output("Missing Port")

    assert str(excinfo.value) == "unknown_midi_output_port: Missing Port"


def test_open_output_rejects_port_without_send_method() -> None:
    """A backend that returns a non-port object trips the duck-typing guard."""

    from rytm_randomizer.mido_provider import MidoMidiPortProvider
    from rytm_randomizer.real_midi_adapter import RealMidiPortError

    _install_fake_mido(
        output_names=("Fake Rytm",),
        open_factory=lambda _name: object(),  # no .send -> guarded
    )
    provider = MidoMidiPortProvider()

    with pytest.raises(RealMidiPortError) as excinfo:
        provider.open_output("Fake Rytm")

    assert str(excinfo.value) == "invalid_midi_output_port: Fake Rytm"


def test_open_output_returns_port_with_send_method() -> None:
    """Happy path: a known port with a ``send`` method is returned as-is."""

    from rytm_randomizer.mido_provider import MidoMidiPortProvider

    fake_port = _FakePort("Fake Rytm")
    _install_fake_mido(
        output_names=("Fake Rytm",),
        open_factory=lambda _name: fake_port,
    )
    provider = MidoMidiPortProvider()

    result = provider.open_output("Fake Rytm")

    assert result is fake_port
    # Confirm the returned object honors the protocol: send() routes through.
    result.send({"message_type": "cc", "channel": 0, "control": 16, "value": 0})
    assert fake_port.sent == [{"message_type": "cc", "channel": 0, "control": 16, "value": 0}]


def test_open_output_propagates_dependency_error_when_mido_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from rytm_randomizer.mido_provider import MidoMidiPortProvider
    from rytm_randomizer.real_midi_adapter import RealMidiDependencyError

    sys.modules.pop("mido", None)

    real_import = builtins.__import__

    def _block_mido(name, *args, **kwargs):
        if name == "mido":
            raise ImportError("forced-missing: mido")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", _block_mido)
    provider = MidoMidiPortProvider()

    with pytest.raises(RealMidiDependencyError):
        provider.open_output("Fake Rytm")
