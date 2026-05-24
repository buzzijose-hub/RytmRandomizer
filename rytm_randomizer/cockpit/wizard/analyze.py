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

Routing is table-driven (a ``(kind, mode)`` -> callable map built once
at module load) so adding a new analyzer is a single dict insertion: no
``if/elif`` ladder to extend, no risk of forgetting to forward an error
case. The dispatcher itself becomes a ``Mapping`` lookup with a single
``KeyError → ValueError`` translation for unsupported combinations.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Final

from ...style_analysis.extractor import extract_from_audio
from ...style_analysis.feature_report import FeatureReport
from ..data.profile_model import StyleTrait
from . import reference_analyzer, sysex_analyzer
from .errors import WizardSourcePathError
from .state import InspirationSource, Kind, Mode
from .trait_math import average_trait_tuples, build_canonical_traits, neutral_traits

#: Audio extensions accepted by the audio path.
_AUDIO_EXTENSIONS: Final[tuple[str, ...]] = (".wav", ".mp3", ".flac", ".aif", ".aiff")


_AnalyzerFn = Callable[[InspirationSource], tuple[StyleTrait, ...]]


def _dispatch_reference(source: InspirationSource) -> tuple[StyleTrait, ...]:
    """Route ``mode="reference"`` to the curated lookup table."""

    return reference_analyzer.lookup_traits(source.location)


def _dispatch_kit(source: InspirationSource) -> tuple[StyleTrait, ...]:
    """Route ``kind="kit", mode in {"file", "folder"}`` to the SysEx analyzer."""

    return sysex_analyzer.extract_kit_traits(Path(source.location))


def _dispatch_audio(source: InspirationSource) -> tuple[StyleTrait, ...]:
    """Route audio kinds to :func:`_analyze_audio_path`."""

    return _analyze_audio_path(Path(source.location))


def _build_dispatch_table() -> Mapping[tuple[Kind, Mode], _AnalyzerFn]:
    """Build the ``(kind, mode)`` -> analyzer-function lookup once.

    Reference mode wins over kind because the lookup table is text-only;
    file / folder modes routed by kind because the analyzer depends on
    the underlying byte / audio interpretation. New analyzers become a
    single insertion here.
    """

    table: dict[tuple[Kind, Mode], _AnalyzerFn] = {}

    # Every kind routed through reference when the mode is "reference".
    reference_kinds: tuple[Kind, ...] = ("kit", "sound", "song", "album", "artist")
    for kind in reference_kinds:
        table[(kind, "reference")] = _dispatch_reference

    # Kit + file/folder routes through the SysEx analyzer.
    for mode in ("file", "folder"):
        table[("kit", mode)] = _dispatch_kit

    # Audio kinds + file/folder routes through the audio analyzer.
    audio_kinds: tuple[Kind, ...] = ("sound", "song", "album")
    for kind in audio_kinds:
        for mode in ("file", "folder"):
            table[(kind, mode)] = _dispatch_audio

    return table


#: ``(kind, mode)`` -> analyzer function. Built once at import time.
_DISPATCH: Final[Mapping[tuple[Kind, Mode], _AnalyzerFn]] = _build_dispatch_table()


def analyze_source(source: InspirationSource) -> tuple[StyleTrait, ...]:
    """Dispatch ``source`` to the correct analyzer + return its traits.

    Routes purely on ``source.kind`` + ``source.mode`` via :data:`_DISPATCH`
    -- the analyzers themselves do not inspect the dispatch decision. See
    module docstring for the routing table.

    Raises ``ValueError`` for an unsupported ``(kind, mode)`` combination
    (e.g. ``kind="artist"`` with ``mode="file"``) -- the wizard's state
    layer prevents these in practice, but the dispatcher is defensive
    against a malformed source slipping through.
    """

    key = (source.kind, source.mode)
    try:
        analyzer = _DISPATCH[key]
    except KeyError:
        raise ValueError(
            f"unsupported (kind, mode) combination: ({source.kind!r}, {source.mode!r})"
        ) from None
    return analyzer(source)


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
            return neutral_traits()
        per_file = tuple(feature_report_to_traits(extract_from_audio(p)) for p in matches)
        return average_trait_tuples(per_file)

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

    rolling = (report.low_end_weight + report.tempo_stability) / 2.0
    metallic = (report.spectral_brightness + report.texture_noise) / 2.0
    hats = report.percussion_density
    motion = 1.0 - report.tempo_stability
    return build_canonical_traits(rolling, metallic, hats, motion)


__all__ = [
    "analyze_source",
    "feature_report_to_traits",
]
