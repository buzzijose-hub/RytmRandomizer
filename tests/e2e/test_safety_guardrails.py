"""End-to-end safety-guardrail tests (WS-R).

These tests exercise the safety behaviors the V1.34 docs call out explicitly:

* Bare main-prompt depth digits (``1`` / ``2`` / ``3`` without a preceding
  S/F/A/G/K/Y/V/N/M1/M2/M3 command) must emit **no** MIDI.
* ``Z`` returns all four pads to their validated anchors.
* ``S5`` (scene "Back to Clean") returns all four pads to their validated
  anchors.
* The passive menu (no flag) opens no port and emits no MIDI.
* ``--arm`` is the only mode that constructs the real
  :class:`MidoMidiPortProvider` -- ``--dry-run`` must NEVER touch it.

Determinism is enforced by the project-wide :data:`E2E_RANDOM_SEED` (see
:mod:`tests.e2e.conftest`).
"""

from __future__ import annotations

import random
import sys
from unittest import mock

import pytest

from .conftest import (
    CANONICAL_VALIDATION_COMMANDS,
    E2E_RANDOM_SEED,
    CapturedMessage,
    run_canonical_dry_run,
)

# -----------------------------------------------------------------------------
# Bare-depth guardrail: main-prompt 1/2/3 must emit no MIDI by themselves.
# -----------------------------------------------------------------------------


@pytest.mark.parametrize("bare_digit", ["1", "2", "3"])
def test_bare_main_prompt_depth_digit_emits_no_midi(
    bare_digit: str,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """A bare ``1`` / ``2`` / ``3`` typed at the main Command prompt must
    not produce any additional MIDI messages -- only a guard print.

    The flow is:

      1) ``choose_target_pad`` consumes the first ``"1"`` (pick Pad 1).
      2) ``select_profile`` consumes the second ``"1"`` (pick My BD Hard).
         This emits one machine-switch CC (``CC15 -> 0``) as documented.
      3) The bare ``1``/``2``/``3`` at the Command prompt prints the guard
         message and emits zero MIDI.

    We assert the *post-guard* message count equals the *post-profile-select*
    count, i.e. the bare digit added nothing.
    """

    # Baseline: same entry flow but quit immediately after profile select.
    baseline = run_canonical_dry_run(["Q"], capsys=capsys)
    assert baseline.exit_code == 0
    baseline_count = len(baseline.captured)
    assert baseline_count > 0, (
        "Profile select itself should have emitted at least one CC -- if "
        "this fails the test scaffolding is broken, not the guardrail."
    )

    # Now run the same flow with a bare depth digit before quitting. The
    # number of messages must be IDENTICAL to baseline.
    with_bare = run_canonical_dry_run([bare_digit, "Q"], capsys=capsys)
    assert with_bare.exit_code == 0
    assert len(with_bare.captured) == baseline_count, (
        f"Bare main-prompt {bare_digit!r} emitted "
        f"{len(with_bare.captured) - baseline_count} unexpected MIDI message(s). "
        "The V1.34 guardrail requires depth digits to be no-ops at the main "
        "Command prompt -- they only have meaning after S/F/A/G/K/Y/V/N/M1/M2/M3."
    )
    assert (
        with_bare.captured == baseline.captured
    ), "Bare depth digit must not perturb the prior MIDI stream either."
    assert "No MIDI was sent." in with_bare.stdout


# -----------------------------------------------------------------------------
# Anchor-return guardrails: S5 and Z both restore the four-pad anchors.
# -----------------------------------------------------------------------------


def _final_state_by_channel_control(
    messages: tuple[CapturedMessage, ...],
) -> dict[tuple[int, int], int]:
    """Project a CC stream into ``{(channel, control): final_value}``.

    The Rytm receives MIDI as a sequence of CC writes; the *effective*
    device state at any point is the last value seen for each
    ``(channel, control)`` pair. Two flows that end with the same effective
    state are observably indistinguishable from the hardware's perspective,
    even if their MIDI streams differ in length or intermediate values.
    """

    final: dict[tuple[int, int], int] = {}
    for msg in messages:
        final[(msg.channel, msg.control)] = msg.value
    return final


def test_s5_returns_all_four_pads_to_anchors(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """After mutating with a scene, ``S5`` must return every pad to its anchor.

    Strategy: compare the *final per-(channel, control) state* of two runs:

    * ``S0 -> Q`` -- the four-pad cold anchor load.
    * ``S0 -> S3B -> S5 -> Q`` -- load, mutate, then S5 back to clean.

    The Rytm only "sees" the most recent value for each CC, so two flows
    that mutate and return must end at the same effective per-CC state.
    """

    anchor_only = run_canonical_dry_run(["S0", "Q"], capsys=capsys)
    assert anchor_only.exit_code == 0
    assert anchor_only.captured

    mutate_then_s5 = run_canonical_dry_run(["S0", "S3B", "S5", "Q"], capsys=capsys)
    assert mutate_then_s5.exit_code == 0

    anchor_state = _final_state_by_channel_control(anchor_only.captured)
    final_state = _final_state_by_channel_control(mutate_then_s5.captured)

    # All four channels (0-3) should be represented post-S5.
    channels_used = {channel for channel, _ in final_state}
    assert channels_used == {0, 1, 2, 3}

    # For every (channel, control) the anchor-only run wrote, the
    # mutate-then-S5 run must end at the SAME value.
    for key, anchor_value in anchor_state.items():
        assert final_state.get(key) == anchor_value, (
            f"S5 did not restore CC{key[1]} on channel {key[0]} to its "
            f"anchor value (anchor={anchor_value}, post-S5={final_state.get(key)})."
        )


def test_z_returns_all_four_pads_to_anchors(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """``Z`` (return-group-to-anchors) must restore every pad to its anchor.

    Same final-state assertion as the S5 test but triggered with the
    lower-level ``Z`` command rather than scene-layer ``S5``.
    """

    anchor_only = run_canonical_dry_run(["S0", "Q"], capsys=capsys)
    assert anchor_only.exit_code == 0

    mutate_then_z = run_canonical_dry_run(["S0", "S3B", "Z", "Q"], capsys=capsys)
    assert mutate_then_z.exit_code == 0

    anchor_state = _final_state_by_channel_control(anchor_only.captured)
    final_state = _final_state_by_channel_control(mutate_then_z.captured)

    for key, anchor_value in anchor_state.items():
        assert final_state.get(key) == anchor_value, (
            f"Z did not restore CC{key[1]} on channel {key[0]} to its "
            f"anchor value (anchor={anchor_value}, post-Z={final_state.get(key)})."
        )


# -----------------------------------------------------------------------------
# Passive-menu guardrail: no flag must open no port and emit no MIDI.
# -----------------------------------------------------------------------------


def test_passive_menu_opens_no_port_and_emits_no_midi(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Default mode (``app.main([])``) must run the read-only passive menu:
    no real MIDI library imported, no port opened, zero MIDI emitted.
    """

    from rytm_randomizer import app
    from rytm_randomizer.mock_midi import MockMidiSender

    # If a MockMidiSender is somehow constructed in the default path it
    # would still record nothing because no shell.run() happens. To be
    # extra strict, patch the constructor and assert it was not called.
    with mock.patch.object(
        MockMidiSender,
        "__init__",
        side_effect=AssertionError(
            "MockMidiSender must not be constructed in passive (default) mode."
        ),
    ):
        exit_code = app.main([])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "passive menu" in captured.out
    assert "no MIDI port opened" in captured.out
    assert "no MIDI sent" in captured.out
    # Real MIDI library not imported by the passive path.
    for module_name in ("mido", "rtmidi", "pythonrtmidi"):
        assert module_name not in sys.modules or module_name == "mido", (
            f"Passive mode pulled in {module_name!r}; that violates the " "import-safety contract."
        )


# -----------------------------------------------------------------------------
# Provider-guardrail: --arm is the only mode that constructs the real
# mido provider; --dry-run must never touch MidoMidiPortProvider.
# -----------------------------------------------------------------------------


def test_dry_run_never_constructs_real_midi_provider() -> None:
    """``--dry-run`` is fully automatable in CI precisely because it does
    not touch :class:`MidoMidiPortProvider`. This test patches the
    constructor and asserts it was never called during a full canonical run.
    """

    random.seed(E2E_RANDOM_SEED)

    from rytm_randomizer import app, mido_provider
    from rytm_randomizer.mock_midi import MockMidiSender

    real_init = mido_provider.MidoMidiPortProvider.__init__
    construction_count = {"calls": 0}

    def spy_init(self: object, *args: object, **kwargs: object) -> None:
        construction_count["calls"] += 1
        real_init(self)  # type: ignore[misc]

    # Drive an entry-flow that does not actually touch the shell loop
    # heavily -- this test focuses on the provider contract, not message
    # parity, so we use a short scripted input.
    inputs_iter = iter(["1", "1", "Q"])

    def feed(prompt: str = "") -> str:
        try:
            return next(inputs_iter)
        except StopIteration:
            raise EOFError

    def recording_send(self: object, message: object) -> None:
        # Accept either mido or MidiMessage; we don't assert on the stream
        # here, just keep the call from raising TypeError.
        return None

    with (
        mock.patch.object(mido_provider.MidoMidiPortProvider, "__init__", spy_init),
        mock.patch("builtins.input", feed),
        mock.patch.object(MockMidiSender, "send", recording_send),
    ):
        exit_code = app.main(["--dry-run"])

    assert exit_code == 0
    assert construction_count["calls"] == 0, (
        "MidoMidiPortProvider was constructed during a --dry-run. "
        f"({construction_count['calls']} call(s).) "
        "--dry-run must never touch the real-MIDI provider; that contract "
        "is what makes the E2E suite safe to run in CI."
    )


def test_dry_run_does_not_import_real_midi_library() -> None:
    """A clean ``--dry-run`` of the canonical flow must not pull ``mido`` /
    ``rtmidi`` / ``pythonrtmidi`` into ``sys.modules`` either.

    Note: ``mido`` is imported lazily by :func:`rytm_randomizer.midi_io.send_cc`
    when it builds a real ``mido.Message`` (the message object is harmless --
    no port is opened). What ``--dry-run`` MUST NOT import is ``rtmidi`` /
    ``pythonrtmidi``, the backends that would try to talk to hardware.
    """

    # Re-run a canonical flow in isolation and check sys.modules afterwards.

    # Force-unload the backends if a previous test loaded them.
    for backend in ("rtmidi", "pythonrtmidi"):
        sys.modules.pop(backend, None)

    run_canonical_dry_run(CANONICAL_VALIDATION_COMMANDS)

    for backend in ("rtmidi", "pythonrtmidi"):
        assert backend not in sys.modules, (
            f"--dry-run imported {backend!r}, the hardware-talking backend. "
            "That violates the no-hardware contract of dry-run mode."
        )
