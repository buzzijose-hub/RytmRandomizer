"""Shared per-pad runtime mixins for Pad1-4 engines + GroupRunner.

The five runtime classes (:class:`~rytm_randomizer.engines.pad1.Pad1Engine`,
:class:`~rytm_randomizer.engines.pad2.Pad2Engine`,
:class:`~rytm_randomizer.engines.pad3.Pad3Engine`,
:class:`~rytm_randomizer.engines.pad4.Pad4Engine`, and
:class:`~rytm_randomizer.group_runner.GroupRunner`) each used to independently
define ~150 LOC of byte-identical helper methods. The H1 abstraction audit
consolidated them here as two cooperative mixins so the duplication is gone
without altering any public method signature or wire-level MIDI behavior.

:class:`PadRuntimeMixin` consolidates the eight shared methods every
runtime class needs:

* ``_send_cc`` -- one-shot CC send on the current channel.
* ``_send_machine`` -- send the machine selector CC15 for the active profile.
* ``_resolved_profile`` -- return ``active_profile`` with ``safe`` narrowed
  by :class:`~rytm_randomizer.guardrails.resolver.ResolvedBounds` when set
  (byte-identical pass-through when ``resolved_bounds`` is ``None``).
* ``_send_param`` -- send a single parameter through the resolved bounds.
* ``_clamp_state`` -- narrow a state mapping through resolved bounds; drops
  ``LOCKED_DEFAULT`` / ``FORBIDDEN`` keys.
* ``_apply_state`` -- delegate to :func:`midi_io.apply_state` and bookkeep
  anchor / current / previous state.
* ``_mutate_zone`` -- delegate to :func:`randomization.mutate_zone` and
  bookkeep current / previous state.
* ``_set_group_context`` -- switch the active pad / profile and reload
  anchor / current / previous state from the group state dicts.

:class:`IsolatedPadMixin` adds the two extra helpers Pad3 and Pad4 reuse for
their single-pad "isolated anchor" flow:

* ``_require_group_for_single_pad`` -- guard requiring all 4 pads loaded.
* ``_return_isolated_pad_to_anchor`` -- V1.10 isolated-anchor restore.

Required instance attributes (the mixins are duck-typed -- they read these
off ``self`` but do not declare them, so each concrete runtime class is
responsible for initializing them in ``__init__``):

* ``out`` -- the MIDI sender.
* ``channel`` -- the integer MIDI channel for the current pad.
* ``sleep`` -- the injected ``time.sleep``-compatible callable.
* ``rng`` -- the injected ``random.Random``-compatible source.
* ``active_profile`` -- the currently loaded profile mapping (or ``None``).
* ``anchor_state`` -- the current pad's anchor parameter dict.
* ``current_state`` -- the current pad's working parameter dict.
* ``previous_state`` -- the current pad's last-applied parameter dict
  (or ``None``).
* ``target_pad`` -- the 1-based pad index (used for resolved-bounds lookup).
* ``resolved_bounds`` -- optional
  :class:`~rytm_randomizer.guardrails.resolver.ResolvedBounds` table.

:class:`IsolatedPadMixin` additionally requires:

* ``isolated_pad`` -- the 1-based pad index of the currently isolated pad.
* ``group_anchor_states`` -- the four-pad anchor dict (must contain
  ``isolated_pad``).
* ``group_current_states`` -- the four-pad current-state dict.
* ``group_previous_states`` -- the four-pad previous-state dict.
* ``_set_group_context`` -- inherited from :class:`PadRuntimeMixin`.
* ``_apply_state`` -- inherited from :class:`PadRuntimeMixin`.

The mixins do not introduce any new behavior; each method body is the
byte-identical body previously inlined in each runtime class. Parity tests
(`tests/test_engines_padN.py` / `tests/test_group_runner.py` /
`tests/test_scene_runner.py`) stay green untouched.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .. import midi_io as _midi_io
from .. import randomization as _randomization
from ..data import GROUP_LAYOUT, PROFILES

__all__ = ["PadRuntimeMixin", "IsolatedPadMixin"]


class PadRuntimeMixin:
    """Consolidated per-pad runtime helpers shared by all engines + GroupRunner.

    See the module docstring for the required instance attribute contract.
    Method bodies are byte-identical to the previously inlined versions in
    :mod:`rytm_randomizer.engines.pad1` -- :mod:`rytm_randomizer.engines.pad4`
    and :mod:`rytm_randomizer.group_runner`.
    """

    def _send_cc(self, cc: int, value: int) -> None:
        _midi_io.send_cc(self.out, cc, value, channel=self.channel, sleep=self.sleep)

    def _resolved_profile(self) -> Mapping[str, Any] | None:
        """Return ``active_profile`` with ``safe`` narrowed by resolved bounds.

        When :attr:`resolved_bounds` is ``None`` -- or no entry covers this
        pad -- returns ``self.active_profile`` unchanged so the mutation
        engines see byte-identical inputs (parity tests stay green).

        When set, returns a shallow copy with ``safe`` replaced by the
        intersection: for each parameter the new ``(low, high)`` is the
        intersection of the profile's hardware ``safe`` range and the
        resolved bound. ``LOCKED_DEFAULT`` / ``FORBIDDEN`` parameters are
        clamped to the parameter's current anchor value so the mutation
        loop's ``randint(low, high)`` collapses to a single value -- and
        :meth:`_send_param` then refuses to send them.
        """

        if self.resolved_bounds is None or self.active_profile is None:
            return self.active_profile

        base_safe: Mapping[str, tuple[int, int]] = self.active_profile["safe"]
        anchor: Mapping[str, int] = self.active_profile["anchor"]
        narrowed: dict[str, tuple[int, int]] = dict(base_safe)
        for name in list(base_safe.keys()):
            bound = self.resolved_bounds.get(self.target_pad, name)
            if bound is None:
                continue
            base_low, base_high = base_safe[name]
            new_low = max(base_low, bound.low)
            new_high = min(base_high, bound.high)
            if new_low > new_high:
                # Collapse to the anchor value so the mutation engine emits
                # a stable, identity-style choice; ``_send_param`` will
                # short-circuit on the LOCKED class.
                pinned = anchor.get(name, base_low)
                new_low = new_high = pinned
            narrowed[name] = (new_low, new_high)

        # Build a shallow-copy profile dict so downstream callers (the
        # randomization core, the V1.34 stdout banners) see the same shape
        # but a narrower ``safe`` table.
        profile_copy: dict[str, Any] = dict(self.active_profile)
        profile_copy["safe"] = narrowed
        return profile_copy

    def _send_machine(self) -> None:
        _midi_io.send_machine(self.out, self.active_profile, channel=self.channel, sleep=self.sleep)

    def _send_param(self, name: str, value: int) -> None:
        if self.resolved_bounds is not None:
            clamped = self.resolved_bounds.clamp_value(self.target_pad, name, value)
            if clamped is None:
                # The resolved entry is LOCKED_DEFAULT / FORBIDDEN -- the
                # profile says this parameter must not mutate. Skip the
                # outgoing CC entirely. ``send_param`` would otherwise
                # echo the value to stdout in V1.34-parity format.
                return
            value = clamped
        _midi_io.send_param(
            self.out,
            self.active_profile,
            name,
            value,
            channel=self.channel,
            sleep=self.sleep,
        )

    def _clamp_state(self, state: Mapping[str, int]) -> Mapping[str, int]:
        """Return ``state`` with every value clamped through resolved bounds.

        Parameters whose resolved class is ``LOCKED_DEFAULT`` / ``FORBIDDEN``
        are dropped from the returned mapping -- ``apply_state`` then has
        nothing to send for them, so no CC reaches the wire. Parameters
        outside the resolved table pass through unchanged.

        Returns ``state`` itself unchanged when ``resolved_bounds`` is
        ``None`` so the parity path is byte-identical.
        """

        if self.resolved_bounds is None:
            return state
        out: dict[str, int] = {}
        for name, value in state.items():
            clamped = self.resolved_bounds.clamp_value(self.target_pad, name, value)
            if clamped is None:
                continue
            out[name] = clamped
        return out

    def _apply_state(
        self,
        state: Mapping[str, int],
        label: str,
        *,
        set_anchor: bool = False,
        switch_machine_first: bool = False,
    ) -> None:
        # ``apply_state`` sends each parameter via :func:`midi_io.send_param`;
        # we route it through ``_resolved_profile()`` so the narrowed ``safe``
        # table determines which values reach the wire and ``_clamp_state``
        # narrows the *input* state itself (anchor values, restored states,
        # etc.). When ``resolved_bounds`` is ``None`` both helpers are
        # no-ops -- byte-identical to today.
        result = _midi_io.apply_state(
            self.out,
            self._resolved_profile() if self.active_profile else None,
            self._clamp_state(state),
            label,
            anchor_state=self.anchor_state,
            current_state=self.current_state,
            previous_state=self.previous_state,
            set_anchor=set_anchor,
            switch_machine_first=switch_machine_first,
            channel=self.channel,
            sleep=self.sleep,
        )

        if not result.applied:
            return

        self.anchor_state = dict(result.anchor_state)
        self.current_state = dict(result.current_state)
        self.previous_state = (
            dict(result.previous_state) if result.previous_state is not None else None
        )

    def _mutate_zone(self, zone_name: str, depth_name: str) -> None:
        # See ``_apply_state`` -- ``mutate_zone`` likewise reads the safe
        # ranges from the profile we hand it, so ``_resolved_profile()``
        # is the single hand-off point for guardrail-driven narrowing.
        result = _randomization.mutate_zone(
            self.out,
            zone_name,
            depth_name,
            profile=self._resolved_profile() if self.active_profile else None,
            anchor_state=self.anchor_state,
            current_state=self.current_state,
            previous_state=self.previous_state,
            channel=self.channel,
            sleep=self.sleep,
            rng=self.rng,
        )

        if not result.applied:
            return

        self.current_state = dict(result.current_state)
        self.previous_state = (
            dict(result.previous_state) if result.previous_state is not None else None
        )

    def _set_group_context(self, pad: int, profile_key: str) -> None:
        """Mirror the monolith ``set_group_context``: switch active pad/profile.

        Loads anchor / current / previous state for ``pad`` from the group
        state dicts, falling back to the profile anchor exactly as the monolith.
        """

        self.target_pad = pad
        self.channel = pad - 1

        self.active_profile = PROFILES[profile_key]

        if pad in self.group_anchor_states:
            self.anchor_state = dict(self.group_anchor_states[pad])
        else:
            self.anchor_state = dict(self.active_profile["anchor"])

        if pad in self.group_current_states:
            self.current_state = dict(self.group_current_states[pad])
        else:
            self.current_state = dict(self.anchor_state)

        previous = self.group_previous_states.get(pad)
        self.previous_state = dict(previous) if previous is not None else None


class IsolatedPadMixin:
    """Single-pad isolated-anchor helpers shared by Pad3 and Pad4.

    See the module docstring for the required instance attribute contract.
    This mixin assumes :class:`PadRuntimeMixin` is also mixed in (it calls
    :meth:`PadRuntimeMixin._set_group_context` and
    :meth:`PadRuntimeMixin._apply_state`).
    """

    def _require_group_for_single_pad(self) -> bool:
        """Mirror the monolith ``require_group_for_single_pad`` guard.

        The dedicated single-pad discovery commands require the full 4-pad
        group to have been loaded first (so safe anchors exist for every pad).
        """

        if len(self.group_current_states) < 4:
            print("\nLoad the full 4-pad group first with O.")
            print("This stores safe anchors for Pads 1-4 before isolated " "mutation.")
            return False
        return True

    def _return_isolated_pad_to_anchor(self) -> None:
        """Mirror the monolith ``return_isolated_pad_to_anchor`` (V1.10).

        Pad3 / Pad4 reuse this by temporarily pointing ``isolated_pad`` at
        themselves before delegating.
        """

        if not self._require_group_for_single_pad():
            return

        cfg = GROUP_LAYOUT[self.isolated_pad]
        profile_key = cfg["profile"]
        self._set_group_context(self.isolated_pad, profile_key)

        print("\nReturning isolated pad to anchor:")
        print(f"  Pad {self.isolated_pad}: {cfg['role']} / " f"{self.active_profile['name']}")
        print(
            "  Pads not touched: "
            + ", ".join(str(p) for p in GROUP_LAYOUT if p != self.isolated_pad)
        )

        anchor = dict(self.group_anchor_states[self.isolated_pad])

        self._apply_state(
            anchor,
            f"Pad {self.isolated_pad} isolated back to anchor",
            set_anchor=False,
            switch_machine_first=True,
        )

        self.group_current_states[self.isolated_pad] = dict(self.current_state)
        self.group_previous_states[self.isolated_pad] = None

        print(
            f"\nPad {self.isolated_pad} returned to anchor. Other group pads " "were not touched."
        )
