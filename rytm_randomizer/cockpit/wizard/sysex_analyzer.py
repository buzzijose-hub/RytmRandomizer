"""Kit-SysEx file analyzer (Phase 2 byte-statistics placeholder).

The wizard's ``kind="kit"`` path expects the operator to drop an Elektron
Analog Rytm MK2 kit dump (.syx) or a folder of them. Phase 3+ will parse
the kit envelope properly (via the strategy seam in
``rytm_randomizer/devices/``) and derive per-pad parameter statistics --
that requires a real-hardware capture corpus the wizard does not yet
ship.

For Phase 2 this module ships a **deterministic byte-statistics
analyzer**: it reads the file's bytes verbatim and maps four
file-level summary statistics onto four ``_bytes_*`` placeholder
traits. CODE_REVIEW.md M5: the prior version emitted these statistics
under the canonical wizard trait names (``metallic_tension`` /
``rolling_low_end`` / ``hat_density`` / ``filter_motion``), which lied
to the operator about what was actually analyzed -- a SysEx kit dump's
byte mean has zero musical relationship to "metallic tension". The
``_bytes_*`` names are honest about being phase-2 placeholders and
intentionally do NOT appear in
:data:`~rytm_randomizer.cockpit.wizard.pad_mapping.TRAIT_TO_PAD`, so
the builder silently drops them from ``pad_mappings`` -- they still
appear on the candidate profile so the wizard's review step can show
"we measured the file and got these byte statistics" without claiming
they map to a musical pad.

============================  ===========================================
File-level statistic          :class:`StyleTrait` it produces
============================  ===========================================
Byte mean / 255               ``_bytes_mean`` (raw byte arithmetic mean)
``1 - stddev/127.5``          ``_bytes_stddev`` (inverted byte std-dev)
``min(len, 8192) / 8192``     ``_bytes_density`` (file length, saturating)
Distinct-byte count / 256     ``_bytes_distinct`` (byte-value variety)
============================  ===========================================

Every output value is clamped to ``[0.0, 1.0]`` so downstream code can
trust the range. The byte-standard-deviation -> ``_bytes_stddev`` map
is inverted (lower variance reads as higher value) so the legacy
direction of the prior mapping is preserved for any downstream
consumer that pinned numerical expectations.

If ``path`` is a folder, every ``*.syx`` file in the folder is analyzed
and the resulting per-file 4-trait tuples are weighted-averaged
(equal weight per file). Files with other extensions are skipped. An
empty folder (no ``.syx`` matches) returns the neutral 4-trait profile
under the same ``_bytes_*`` placeholder names (all at ``0.5``).

The averaging + clamping helpers live in :mod:`.trait_math`; the
canonical-trait-name builder there is intentionally NOT used here --
this analyzer emits placeholder names that intentionally do not match
:data:`~rytm_randomizer.cockpit.wizard.traits.WIZARD_TRAIT_NAMES`.
"""

from __future__ import annotations

from pathlib import Path
from typing import Final

from ..data.profile_model import StyleTrait
from .errors import WizardSourcePathError
from .trait_math import clamp_unit

#: File extension that flags a kit SysEx dump.
_KIT_EXTENSION: Final[str] = ".syx"

#: The kit-dump length we treat as "fully populated" for the density proxy.
#: A short kit (~few KB) reads as sparse; a full kit (>=8K) reads as 1.0.
_DENSITY_DENOMINATOR: Final[int] = 8192

#: Placeholder trait names emitted by the Phase 2 byte-statistics analyzer.
#: CODE_REVIEW.md M5: these names intentionally do not match
#: :data:`~rytm_randomizer.cockpit.wizard.traits.WIZARD_TRAIT_NAMES`
#: because the byte statistics carry no musical meaning. They are NOT
#: members of :data:`~rytm_randomizer.cockpit.wizard.pad_mapping.TRAIT_TO_PAD`
#: so the builder silently drops them from the candidate profile's
#: ``pad_mappings`` -- the placeholder traits still appear on the
#: profile so the wizard's review-step UI can show what was measured.
_TRAIT_BYTES_MEAN: Final[str] = "_bytes_mean"
_TRAIT_BYTES_STDDEV: Final[str] = "_bytes_stddev"
_TRAIT_BYTES_DENSITY: Final[str] = "_bytes_density"
_TRAIT_BYTES_DISTINCT: Final[str] = "_bytes_distinct"

#: The ordered tuple of placeholder trait names. Mirrors the deterministic
#: ordering convention :data:`WIZARD_TRAIT_NAMES` uses so the analyzer's
#: per-file output is stable across runs and tests can pin positional layout.
_PLACEHOLDER_TRAIT_NAMES: Final[tuple[str, ...]] = (
    _TRAIT_BYTES_STDDEV,
    _TRAIT_BYTES_MEAN,
    _TRAIT_BYTES_DENSITY,
    _TRAIT_BYTES_DISTINCT,
)


def _neutral_placeholder_traits() -> tuple[StyleTrait, ...]:
    """Return the 4-trait tuple at ``0.5`` apiece under placeholder names.

    Local analogue of :func:`trait_math.neutral_traits`. That helper
    emits the canonical :data:`WIZARD_TRAIT_NAMES`; this analyzer
    intentionally emits placeholder names instead (CODE_REVIEW.md M5),
    so the empty-input fallback uses a parallel helper that preserves
    the placeholder naming.
    """

    return tuple(StyleTrait(name, 0.5) for name in _PLACEHOLDER_TRAIT_NAMES)


def _build_placeholder_traits(
    stddev_inv: float,
    mean: float,
    density: float,
    distinct: float,
) -> tuple[StyleTrait, ...]:
    """Build the placeholder 4-trait tuple in :data:`_PLACEHOLDER_TRAIT_NAMES` order.

    Local analogue of :func:`trait_math.build_canonical_traits`. Inputs
    are clamped to ``[0.0, 1.0]`` per trait so callers do not need to
    re-clamp before constructing.
    """

    return (
        StyleTrait(_TRAIT_BYTES_STDDEV, clamp_unit(stddev_inv)),
        StyleTrait(_TRAIT_BYTES_MEAN, clamp_unit(mean)),
        StyleTrait(_TRAIT_BYTES_DENSITY, clamp_unit(density)),
        StyleTrait(_TRAIT_BYTES_DISTINCT, clamp_unit(distinct)),
    )


def extract_kit_traits(path: Path) -> tuple[StyleTrait, ...]:
    """Return the canonical 4-trait tuple derived from ``path``'s bytes.

    ``path`` may point at either a single ``.syx`` file or a folder of
    ``.syx`` files; in the folder case every matching file is analyzed
    independently and the per-file results are averaged with equal weight.

    Raises :class:`WizardSourcePathError` (a ``RytmRandomizerError`` +
    :class:`FileNotFoundError`) if ``path`` does not exist, and
    :class:`ValueError` for any other operator-supplied bad value: a
    non-:class:`pathlib.Path` argument, or a path that exists but is
    neither a file nor a directory. This matches the audio analyzer's
    convention in :mod:`.analyze` so callers can use a single
    ``(WizardSourcePathError, ValueError)`` exception arm.
    """

    # L11: use ValueError (not TypeError) for the "not a Path" guard so the
    # wizard's analyzer surface speaks a single error vocabulary --
    # WizardSourcePathError for path-policy violations (path missing on
    # disk) + ValueError for every other "operator gave us a bad value"
    # case. The audio analyzer at ``analyze.py:_analyze_audio_path``
    # follows the same convention.
    if not isinstance(path, Path):
        raise ValueError("path must be a pathlib.Path")
    if not path.exists():
        raise WizardSourcePathError(f"kit path does not exist: {path}")

    if path.is_file():
        return _analyze_single_file(path)
    if path.is_dir():
        return _analyze_folder(path)
    raise ValueError(f"kit path is neither a file nor a directory: {path}")


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _analyze_single_file(path: Path) -> tuple[StyleTrait, ...]:
    """Read one file's bytes and return its derived 4-trait tuple."""

    data = path.read_bytes()
    return _traits_from_bytes(data)


def _analyze_folder(folder: Path) -> tuple[StyleTrait, ...]:
    """Return the equal-weighted average of every ``.syx`` file's traits."""

    matches = sorted(
        p for p in folder.iterdir() if p.is_file() and p.suffix.lower() == _KIT_EXTENSION
    )
    if not matches:
        return _neutral_placeholder_traits()
    per_file = tuple(_analyze_single_file(p) for p in matches)
    # ``average_trait_tuples`` averages by trait name regardless of which
    # canonical-vs-placeholder set the inputs use; the result here carries
    # the placeholder names because every per-file tuple does. The helper
    # also re-clamps each output to ``[0.0, 1.0]``.
    return _average_placeholder_traits(per_file)


def _average_placeholder_traits(
    per_source: tuple[tuple[StyleTrait, ...], ...],
) -> tuple[StyleTrait, ...]:
    """Equal-weight per-trait mean across placeholder-named per-file tuples.

    Local analogue of :func:`trait_math.average_trait_tuples` that
    preserves the placeholder naming convention (the shared helper
    averages by canonical :data:`WIZARD_TRAIT_NAMES`). Returns trait
    instances in :data:`_PLACEHOLDER_TRAIT_NAMES` order, each clamped
    into ``[0.0, 1.0]``.
    """

    # Defer to the shared averaging helper for the arithmetic, but pull
    # placeholder names out by hand because that helper hard-codes
    # WIZARD_TRAIT_NAMES. We accumulate sums + counts here so the
    # division and re-clamp match the shared helper's semantics.
    count = len(per_source)
    sums: dict[str, float] = dict.fromkeys(_PLACEHOLDER_TRAIT_NAMES, 0.0)
    for traits in per_source:
        for trait in traits:
            sums[trait.name] = sums.get(trait.name, 0.0) + trait.value
    return tuple(
        StyleTrait(name, clamp_unit(sums[name] / count)) for name in _PLACEHOLDER_TRAIT_NAMES
    )


def _traits_from_bytes(data: bytes) -> tuple[StyleTrait, ...]:
    """Map the four byte statistics onto the 4-trait placeholder tuple.

    An empty byte string produces the neutral profile -- it carries no
    information and we refuse to invent any.
    """

    if not data:
        return _neutral_placeholder_traits()

    n = len(data)
    total = sum(data)
    mean = total / n
    # Population standard deviation (single-pass O(n)).
    sq_total = sum(b * b for b in data)
    variance = max(0.0, (sq_total / n) - (mean * mean))
    stddev = variance**0.5

    distinct = len(set(data))

    # All four ratios land inside ``[0.0, 1.0]`` by construction for any
    # valid byte payload:
    #   * ``mean / 255``       -- mean in [0, 255]
    #   * ``1 - stddev/127.5`` -- max byte-stddev is 127.5 (half-0 / half-255)
    #   * ``min(n, 8192)/8192`` -- saturates at 1.0 for long dumps
    #   * ``distinct / 256``   -- distinct count is at most 256
    mean_ratio = mean / 255.0
    stddev_inv = 1.0 - (stddev / 127.5)
    density = min(n, _DENSITY_DENOMINATOR) / _DENSITY_DENOMINATOR
    distinct_ratio = distinct / 256.0

    return _build_placeholder_traits(stddev_inv, mean_ratio, density, distinct_ratio)


__all__ = ["extract_kit_traits"]
