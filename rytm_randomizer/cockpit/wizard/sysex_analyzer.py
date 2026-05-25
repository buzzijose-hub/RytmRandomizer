"""Kit-SysEx file analyzer (Phase 2 byte-statistics).

The wizard's ``kind="kit"`` path expects the operator to drop an Elektron
Analog Rytm MK2 kit dump (.syx) or a folder of them. Phase 3+ will parse
the kit envelope properly (via the strategy seam in
``rytm_randomizer/devices/``) and derive per-pad parameter statistics --
that requires a real-hardware capture corpus the wizard does not yet
ship.

For Phase 2 this module ships a **deterministic byte-statistics
analyzer**: it reads the file's bytes verbatim and maps four
file-level summary statistics onto the four canonical wizard traits:

============================  ===========================================
File-level statistic          :class:`StyleTrait` it produces
============================  ===========================================
Byte mean / 255               ``metallic_tension`` (harsher = higher)
Byte standard deviation       ``rolling_low_end`` (steadier = higher)
``min(len, 8192) / 8192``     ``hat_density`` (longer dumps = more dense)
Distinct-byte count / 256     ``filter_motion`` (more variety = more motion)
============================  ===========================================

Every output value is clamped to ``[0.0, 1.0]`` so downstream code can
trust the range. The byte-standard-deviation -> ``rolling_low_end`` map
is inverted (lower variance = more rolling) so a steady, repetitive dump
reads as more "rolling".

If ``path`` is a folder, every ``*.syx`` file in the folder is analyzed
and the resulting per-file 4-trait tuples are weighted-averaged
(equal weight per file). Files with other extensions are skipped. An
empty folder (no ``.syx`` matches) returns the neutral 4-trait profile.

The averaging + clamping + neutral-fallback helpers all live in
:mod:`.trait_math` so the audio analyzer and this analyzer share a single
implementation.
"""

from __future__ import annotations

from pathlib import Path
from typing import Final

from ..data.profile_model import StyleTrait
from .errors import WizardSourcePathError
from .trait_math import average_trait_tuples, build_canonical_traits, neutral_traits

#: File extension that flags a kit SysEx dump.
_KIT_EXTENSION: Final[str] = ".syx"

#: The kit-dump length we treat as "fully populated" for the density proxy.
#: A short kit (~few KB) reads as sparse; a full kit (>=8K) reads as 1.0.
_DENSITY_DENOMINATOR: Final[int] = 8192


def extract_kit_traits(path: Path) -> tuple[StyleTrait, ...]:
    """Return the canonical 4-trait tuple derived from ``path``'s bytes.

    ``path`` may point at either a single ``.syx`` file or a folder of
    ``.syx`` files; in the folder case every matching file is analyzed
    independently and the per-file results are averaged with equal weight.

    Raises ``TypeError`` if ``path`` is not a :class:`pathlib.Path`
    (Python convention: wrong argument *type* is a TypeError, distinct
    from a value-out-of-range :class:`ValueError`),
    ``FileNotFoundError`` if it does not exist, and ``ValueError`` if it
    is neither a file nor a directory.
    """

    # L11: keep TypeError (not ValueError) because the violation here is a
    # wrong argument *type* -- the Python convention is that ValueError
    # signals "right type, wrong value" while TypeError signals "wrong
    # type entirely". The surrounding raises in this function use
    # WizardSourcePathError / ValueError for value-level checks, which is
    # the correct contrast.
    if not isinstance(path, Path):
        raise TypeError("path must be a pathlib.Path")
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
        return neutral_traits()
    per_file = tuple(_analyze_single_file(p) for p in matches)
    return average_trait_tuples(per_file)


def _traits_from_bytes(data: bytes) -> tuple[StyleTrait, ...]:
    """Map the four byte statistics onto the canonical 4-trait tuple.

    An empty byte string produces the neutral profile -- it carries no
    information and we refuse to invent any.
    """

    if not data:
        return neutral_traits()

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
    metallic = mean / 255.0
    rolling = 1.0 - (stddev / 127.5)
    hats = min(n, _DENSITY_DENOMINATOR) / _DENSITY_DENOMINATOR
    motion = distinct / 256.0

    return build_canonical_traits(rolling, metallic, hats, motion)


__all__ = ["extract_kit_traits"]
