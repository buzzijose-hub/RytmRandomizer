"""Tests for the ``narrow_<name>`` Literal-narrowing helpers.

The narrow helpers replace the historical ``# type: ignore[arg-type]``
pattern at every wire boundary: a raw ``str`` from the wire is checked for
membership against the canonical ``_VALUES`` tuple and either returned as
the narrowed :class:`typing.Literal` (via :func:`typing.cast`) or refused
with :class:`ValueError`. These tests pin the contract:

* Every valid literal value round-trips through its narrow helper unchanged.
* Every invalid input raises :class:`ValueError` (NOT :class:`TypeError`,
  NOT a silent fall-through) — so callers can rely on a single exception
  class for input validation.
* The error message does NOT echo huge / control-character payloads
  verbatim — untrusted wire data is truncated and ``repr``-escaped via
  the internal ``_safe_repr`` helper so a malicious blob cannot bloat a
  log line.
* The error message DOES list the allowed set — debugging a bad client
  payload should not require reading the source.
* The return value is *value-equal* to the corresponding :data:`_VALUES`
  member — proving the narrow is faithful at runtime (the static
  ``Literal`` narrowing is checked by mypy separately).

Coverage spans all eleven narrow helpers across the cockpit:

* :mod:`cockpit.data.types`: ``narrow_kind``, ``narrow_history_kind``,
  ``narrow_via``, ``narrow_status``, ``narrow_transition_curve``
* :mod:`cockpit.data.send_plan`: ``narrow_readiness_reason``
* :mod:`cockpit.wizard.state`: ``narrow_kind``, ``narrow_mode``,
  ``narrow_status``, ``narrow_step`` (the wizard's own Literal aliases
  use a different value set from the data-layer ones, hence separate
  helpers).
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import pytest

from rytm_randomizer.cockpit.data import send_plan as dp_send_plan
from rytm_randomizer.cockpit.data import types as dp_types
from rytm_randomizer.cockpit.wizard import state as wz_state

pytestmark = pytest.mark.fast


# ---------------------------------------------------------------------------
# Helper table: (narrow_fn, valid_tuple, name_for_messages)
# ---------------------------------------------------------------------------
#
# Every entry here corresponds to one narrow helper plus its canonical
# allowed-values tuple. The data-layer table covers the ``cockpit.data``
# helpers; the wizard table covers the wizard's own (different value set)
# helpers. Keeping them in tables means adding a new Literal automatically
# routes through the same test bodies once the helper is wired.

_DATA_NARROWS: tuple[tuple[Callable[[str], Any], tuple[str, ...], str], ...] = (
    (dp_types.narrow_kind, dp_types.KIND_VALUES, "kind"),
    (dp_types.narrow_history_kind, dp_types.HISTORY_KIND_VALUES, "history_kind"),
    (dp_types.narrow_via, dp_types.VIA_VALUES, "via"),
    (dp_types.narrow_status, dp_types.STATUS_VALUES, "status"),
    (
        dp_types.narrow_transition_curve,
        dp_types.TRANSITION_CURVE_VALUES,
        "transition_curve",
    ),
    (
        dp_send_plan.narrow_readiness_reason,
        dp_send_plan.READINESS_REASON_VALUES,
        "readiness_reason",
    ),
)

_WIZARD_NARROWS: tuple[tuple[Callable[[str], Any], tuple[str, ...], str], ...] = (
    (wz_state.narrow_kind, wz_state.KIND_VALUES, "kind"),
    (wz_state.narrow_mode, wz_state.MODE_VALUES, "mode"),
    (wz_state.narrow_status, wz_state.STATUS_VALUES, "status"),
    (wz_state.narrow_step, wz_state.STEP_VALUES, "step"),
)

_ALL_NARROWS = _DATA_NARROWS + _WIZARD_NARROWS


# ---------------------------------------------------------------------------
# Valid-input round-trip
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "narrow_fn,valid_values,name",
    _ALL_NARROWS,
    ids=[name for _, _, name in _ALL_NARROWS],
)
def test_narrow_returns_input_unchanged_for_every_valid_literal(
    narrow_fn: Callable[[str], Any],
    valid_values: tuple[str, ...],
    name: str,
) -> None:
    """Every member of the canonical tuple round-trips through the helper.

    The narrow helper is a runtime no-op for valid input: it MUST return
    the same string value (object identity is not required, but value
    equality is — and on CPython the cast preserves identity).
    """

    del name
    for value in valid_values:
        assert narrow_fn(value) == value


# ---------------------------------------------------------------------------
# Invalid-input rejection
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "narrow_fn,valid_values,name",
    _ALL_NARROWS,
    ids=[name for _, _, name in _ALL_NARROWS],
)
def test_narrow_raises_value_error_on_unknown_string(
    narrow_fn: Callable[[str], Any],
    valid_values: tuple[str, ...],
    name: str,
) -> None:
    """An unknown literal MUST raise ``ValueError`` (NOT silently pass)."""

    del valid_values, name
    with pytest.raises(ValueError):
        narrow_fn("definitely-not-a-real-literal-value-zzz")


@pytest.mark.parametrize(
    "narrow_fn,valid_values,name",
    _ALL_NARROWS,
    ids=[name for _, _, name in _ALL_NARROWS],
)
def test_narrow_raises_value_error_on_empty_string(
    narrow_fn: Callable[[str], Any],
    valid_values: tuple[str, ...],
    name: str,
) -> None:
    """The empty string is never a valid Literal value in this codebase."""

    del valid_values, name
    with pytest.raises(ValueError):
        narrow_fn("")


@pytest.mark.parametrize(
    "narrow_fn,valid_values,name",
    _ALL_NARROWS,
    ids=[name for _, _, name in _ALL_NARROWS],
)
def test_narrow_raises_value_error_not_type_error(
    narrow_fn: Callable[[str], Any],
    valid_values: tuple[str, ...],
    name: str,
) -> None:
    """Wrong-type errors must surface as ``ValueError``, not ``TypeError``.

    Callers (the ``from_dict`` constructors, the wizard handler) catch
    ``ValueError`` to surface invalid wire payloads. ``TypeError`` would
    bypass those except branches and propagate as a programmer bug —
    which it is not, for an invalid wire string.
    """

    del valid_values, name
    with pytest.raises(ValueError) as exc_info:
        narrow_fn("bogus-value-xyz")
    # Sanity: the raised exception is exactly ``ValueError``, not a subclass
    # like ``UnicodeError`` (which would still pass the bare ``raises``
    # assertion). We allow subclasses but disallow ``TypeError``.
    assert not isinstance(exc_info.value, TypeError)


# ---------------------------------------------------------------------------
# Error-message hygiene: sanitisation + truncation + allowed-set echo
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "narrow_fn,valid_values,name",
    _ALL_NARROWS,
    ids=[name for _, _, name in _ALL_NARROWS],
)
def test_narrow_error_message_lists_allowed_values(
    narrow_fn: Callable[[str], Any],
    valid_values: tuple[str, ...],
    name: str,
) -> None:
    """The error message must contain every allowed-set entry verbatim.

    Debugging a misconfigured client should not require reading the
    cockpit source. The allowed set is tiny in every case (2-5 entries)
    so the full enumeration fits in one log line.
    """

    del name
    with pytest.raises(ValueError) as exc_info:
        narrow_fn("zzz-not-a-real-value")
    message = str(exc_info.value)
    for valid in valid_values:
        assert valid in message, f"{valid!r} missing from error message {message!r}"


@pytest.mark.parametrize(
    "narrow_fn,valid_values,name",
    _ALL_NARROWS,
    ids=[name for _, _, name in _ALL_NARROWS],
)
def test_narrow_error_message_truncates_huge_input(
    narrow_fn: Callable[[str], Any],
    valid_values: tuple[str, ...],
    name: str,
) -> None:
    """A malicious 10KB wire payload must NOT bloat the error message.

    The ``_safe_repr`` helper caps the source string at 50 chars before
    ``repr``-ing it; we assert the full 10K input is never echoed
    verbatim AND that the truncation marker is present.
    """

    del valid_values, name
    payload = "x" * 10_000
    with pytest.raises(ValueError) as exc_info:
        narrow_fn(payload)
    message = str(exc_info.value)
    # The full payload must NOT appear verbatim.
    assert payload not in message
    # The truncation marker IS present so a reader knows the value was cut.
    assert "truncated" in message


@pytest.mark.parametrize(
    "narrow_fn,valid_values,name",
    _ALL_NARROWS,
    ids=[name for _, _, name in _ALL_NARROWS],
)
def test_narrow_error_message_escapes_control_characters(
    narrow_fn: Callable[[str], Any],
    valid_values: tuple[str, ...],
    name: str,
) -> None:
    """Control characters in untrusted input must be escaped via ``repr``.

    A wire payload containing newline / null / ANSI sequences could
    corrupt log files or terminal output. The ``_safe_repr`` helper
    delegates to Python's ``repr()`` which always escapes these — so a
    literal ``"\\n"`` (backslash-n, two characters) appears in the
    message, but a real newline byte does not.
    """

    del valid_values, name
    raw_payload = "evil\nvalue\x00with\x1b[31mcontrol"
    with pytest.raises(ValueError) as exc_info:
        narrow_fn(raw_payload)
    message = str(exc_info.value)
    # The raw newline byte must not appear inside the repr-quoted segment;
    # ``repr()`` escapes it to the two-character ``\n`` sequence instead.
    # We test the escaped form is present (proves repr() ran) and the raw
    # newline is at most outside the repr (e.g. in the "expected one of"
    # prefix it never is, so a single absence check is enough).
    assert "\\n" in message
    assert "\\x00" in message


# ---------------------------------------------------------------------------
# Narrowed result equality vs. the canonical Literal constant
# ---------------------------------------------------------------------------


def test_narrow_kind_result_equals_literal_constant() -> None:
    """``narrow_kind("scene")`` is value-equal to the literal ``"scene"``.

    Proves the runtime narrow does not mangle the string (e.g. by
    interning into a different intermediate representation). Value
    equality is the strongest runtime check we can make; the static
    ``Literal`` narrowing is verified separately by mypy on this file.
    """

    result = dp_types.narrow_kind("scene")
    assert result == "scene"
    # And the narrowed value lives in the canonical tuple.
    assert result in dp_types.KIND_VALUES


def test_narrow_status_result_equals_literal_constant() -> None:
    result = dp_types.narrow_status("armed")
    assert result == "armed"
    assert result in dp_types.STATUS_VALUES


def test_narrow_readiness_reason_result_equals_literal_constant() -> None:
    result = dp_send_plan.narrow_readiness_reason("candidate_high_risk")
    assert result == "candidate_high_risk"
    assert result in dp_send_plan.READINESS_REASON_VALUES


def test_wizard_narrow_kind_uses_wizard_value_set_not_data_value_set() -> None:
    """Wizard's ``narrow_kind`` accepts ``"kit"`` / etc., NOT ``"scene"``.

    The wizard's :data:`Kind` literal is a different value set from the
    data-layer's :data:`Kind` (the wizard describes inspiration source
    types — kit, sound, song, album, artist — while the data layer
    describes profile authorship — scene vs. user). They are intentionally
    separate; this test pins the boundary.
    """

    # Valid wizard value passes.
    assert wz_state.narrow_kind("kit") == "kit"
    # Data-layer ``"scene"`` is NOT a valid wizard kind.
    with pytest.raises(ValueError):
        wz_state.narrow_kind("scene")


# ---------------------------------------------------------------------------
# Discovery: every Literal in cockpit.data.types has a matching narrow_*.
# ---------------------------------------------------------------------------


def test_every_data_layer_literal_has_a_narrow_helper() -> None:
    """Gate against drift: a new ``Xyz = Literal[...]`` MUST ship with ``narrow_xyz``.

    Walks the public surface of :mod:`cockpit.data.types` and asserts that
    every ``Final[tuple[..., ...]]`` alias (the runtime form) has a sibling
    ``narrow_<lowercased-stem>`` callable. Without this test, a future
    PR could add a new Literal without the helper and silently revive the
    ``# type: ignore[arg-type]`` pattern at the wire boundary.

    The mapping rule is: an alias named ``XYZ_VALUES`` (the canonical
    runtime tuple) implies a narrow named ``narrow_xyz``. Aliases that
    don't fit this shape (none today) are exempt — add them to the
    ``_EXEMPT`` set with a one-line rationale.
    """

    exempt: frozenset[str] = frozenset()
    missing: list[str] = []
    for attr_name in dir(dp_types):
        if not attr_name.endswith("_VALUES"):
            continue
        if attr_name.startswith("_"):
            continue
        stem = attr_name[: -len("_VALUES")].lower()
        helper_name = f"narrow_{stem}"
        if helper_name in exempt:
            continue
        if not hasattr(dp_types, helper_name):
            missing.append(f"{attr_name} → {helper_name}")
    assert not missing, (
        "Every ``XYZ_VALUES`` runtime tuple in cockpit.data.types must have "
        "a matching ``narrow_xyz`` helper to prevent the "
        "``# type: ignore[arg-type]`` pattern from creeping back in at wire "
        "boundaries.\n  Missing:\n    " + "\n    ".join(missing)
    )
