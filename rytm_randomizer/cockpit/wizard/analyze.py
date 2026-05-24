"""Top-level analysis dispatcher for the Profile Wizard.

The wizard hands every :class:`~rytm_randomizer.cockpit.wizard.state.
InspirationSource` to :func:`analyze_source`, which routes by the source's
``(kind, mode)`` pair to one of three analyzers and returns the derived
:class:`~rytm_randomizer.cockpit.data.profile_model.StyleTrait` tuple:

================================================  =================================
``(kind, mode)``                                  Analyzer
================================================  =================================
``(*, "reference")``                              :mod:`reference_analyzer`
``("kit", "file" | "folder")``                    :mod:`sysex_analyzer`
``("sound" | "song" | "album", "file" | "folder")``  :func:`_analyze_audio_path`
================================================  =================================

The audio path wraps the existing
:func:`rytm_randomizer.style_analysis.extractor.extract_from_audio` (see
the WS-V style analysis package) and maps the produced
:class:`~rytm_randomizer.style_analysis.feature_report.FeatureReport`
onto the four canonical wizard traits via
:func:`feature_report_to_traits`. The folder variant iterates every
matching audio file, analyzes each, and returns an equal-weighted
average of the per-file results.

The dispatcher is synchronous + deterministic + side-effect free except
for the file reads the analyzers perform. The WS handler runs it on a
worker thread (:func:`asyncio.to_thread`) so the WebSocket event loop
stays responsive.
"""

from __future__ import annotations

from pathlib import Path
from typing import Final

from ...style_analysis.extractor import extract_from_audio
from ...style_analysis.feature_report import FeatureReport
from ..data.profile_model import StyleTrait
from . import reference_analyzer, sysex_analyzer
from .errors import WizardSourcePathError
from .reference_analyzer import WIZARD_TRAIT_NAMES
from .state import InspirationSource

#: Audio extensions accepted by the audio path.
_AUDIO_EXTENSIONS: Final[tuple[str, ...]] = (".wav", ".mp3", ".flac", ".aif", ".aiff")

#: SysEx extension accepted by the kit path (mirrors :mod:`sysex_analyzer`).
_KIT_EXTENSIONS: Final[tuple[str, ...]] = (".syx",)

#: Audio-leaning :data:`~rytm_randomizer.cockpit.wizard.state.Kind` values.
_AUDIO_KINDS: Final[frozenset[str]] = frozenset({"sound", "song", "album"})


def analyze_source(source: InspirationSource) -> tuple[StyleTrait, ...]:
    """Dispatch ``source`` to the correct analyzer + return its traits.

    Routes purely on ``source.kind`` + ``source.mode`` -- the analyzers
    themselves do not inspect the dispatch decision. See module docstring
    for the routing table.

    Raises ``ValueError`` for an unsupported ``(kind, mode)`` combination
    (e.g. ``kind="artist"`` with ``mode="file"``) -- the wizard's state
    layer prevents these in practice, but the dispatcher is defensive
    against a malformed source slipping through.
    """

    if source.mode == "reference":
        return reference_analyzer.lookup_traits(source.location)

    path = Path(source.location)
    if source.kind == "kit":
        return sysex_analyzer.extract_kit_traits(path)

    if source.kind in _AUDIO_KINDS:
        return _analyze_audio_path(path)

    raise ValueError(f"unsupported (kind, mode) combination: ({source.kind!r}, {source.mode!r})")


# ---------------------------------------------------------------------------
# Audio path
# ---------------------------------------------------------------------------


def _analyze_audio_path(path: Path) -> tuple[StyleTrait, ...]:
    """Audio path: single file or folder -> canonical 4-trait tuple.

    Folders are iterated for entries whose suffix is in
    :data:`_AUDIO_EXTENSIONS`. Per-file results are averaged with equal
    weight (the file count is the denominator). Folders that contain no
    matching files return the neutral profile.

    Raises ``FileNotFoundError`` if ``path`` does not exist, and
    ``ValueError`` if ``path`` is neither a file nor a directory.
    """

    if not path.exists():
        raise WizardSourcePathError(f"audio path does not exist: {path}")

    if path.is_file():
        report = extract_from_audio(path)
        return feature_report_to_traits(report)

    if path.is_dir():
        matches = sorted(
            p for p in path.iterdir() if p.is_file() and p.suffix.lower() in _AUDIO_EXTENSIONS
        )
        if not matches:
            return _neutral_traits()
        per_file = tuple(feature_report_to_traits(extract_from_audio(p)) for p in matches)
        return _average_trait_tuples(per_file)

    raise ValueError(f"audio path is neither a file nor a directory: {path}")


def feature_report_to_traits(report: FeatureReport) -> tuple[StyleTrait, ...]:
    """Project the WS-V :class:`FeatureReport` onto the canonical 4 traits.

    The :class:`FeatureReport` carries seven scalar measurements; the
    wizard expresses operator taste in four canonical traits, so this
    function is the projection layer:

    ===================  ==================================================
    Wizard trait         FeatureReport source field(s)
    ===================  ==================================================
    ``rolling_low_end``  ``low_end_weight`` + ``tempo_stability`` average
    ``metallic_tension`` ``spectral_brightness`` + ``texture_noise`` average
    ``hat_density``      ``percussion_density``
    ``filter_motion``    ``1.0 - tempo_stability`` (motion = movement)
    ===================  ==================================================

    Every output value is clamped to ``[0.0, 1.0]``.
    """

    rolling = _clamp_unit((report.low_end_weight + report.tempo_stability) / 2.0)
    metallic = _clamp_unit((report.spectral_brightness + report.texture_noise) / 2.0)
    hats = _clamp_unit(report.percussion_density)
    motion = _clamp_unit(1.0 - report.tempo_stability)
    return (
        StyleTrait("rolling_low_end", rolling),
        StyleTrait("metallic_tension", metallic),
        StyleTrait("hat_density", hats),
        StyleTrait("filter_motion", motion),
    )


# ---------------------------------------------------------------------------
# Internal helpers (mirrored from :mod:`sysex_analyzer`; intentionally local
# so the two analyzers can evolve their averaging independently if needed).
# ---------------------------------------------------------------------------


def _average_trait_tuples(
    per_file: tuple[tuple[StyleTrait, ...], ...],
) -> tuple[StyleTrait, ...]:
    """Element-wise mean across a non-empty tuple of canonical 4-trait tuples.

    The audio path filters out the empty case BEFORE invoking this
    helper, so the contract is "at least one tuple in"; this keeps the
    branch surface minimal.
    """

    count = len(per_file)
    sums: dict[str, float] = dict.fromkeys(WIZARD_TRAIT_NAMES, 0.0)
    for traits in per_file:
        for trait in traits:
            sums[trait.name] = sums.get(trait.name, 0.0) + trait.value
    return tuple(StyleTrait(name, _clamp_unit(sums[name] / count)) for name in WIZARD_TRAIT_NAMES)


def _neutral_traits() -> tuple[StyleTrait, ...]:
    """Return the canonical 4-trait tuple at ``0.5`` apiece (neutral)."""

    return tuple(StyleTrait(name, 0.5) for name in WIZARD_TRAIT_NAMES)


def _clamp_unit(value: float) -> float:
    """Clamp ``value`` into ``[0.0, 1.0]``."""

    if value < 0.0:
        return 0.0
    if value > 1.0:
        return 1.0
    return float(value)


__all__ = [
    "analyze_source",
    "feature_report_to_traits",
]
