"""Deterministic audio-dependent Analog Four patch candidate inference."""

from __future__ import annotations

import multiprocessing
import time
from abc import abstractmethod
from collections.abc import Callable, Mapping
from dataclasses import dataclass, replace
from multiprocessing.process import BaseProcess
from pathlib import Path
from typing import Final, Protocol, TypeAlias, TypedDict, TypeVar, cast

from ..data.analog_four_audio_inference import (
    A4_AUDIO_INFERENCE_BIPOLAR,
    ANALOG_FOUR_AUDIO_INFERENCE_BY_PARAMETER,
    AnalogFourAudioInferenceSpec,
    AnalogFourInferenceFeatureKey,
    AnalogFourInferenceParameter,
)
from ..data.analog_four_display import make_a4_patch_value
from ..data.analog_four_patch_templates import ANALOG_FOUR_PATCH_CANDIDATE_TEMPLATES
from ..observability.errors import BoundaryError
from ..observability.logging import get_logger
from ..observability.metrics import AnalogFourPatchInferenceErrorCode, get_metrics
from ..observability.tracing import operation as trace_operation
from .analog_four_patch_genome import (
    ANALOG_FOUR_PATCH_CANDIDATE_MAX,
    AnalogFourPatchCandidate,
    AnalogFourPatchGene,
    AnalogFourPatchGenome,
    AnalogFourPatchGenomePayload,
    analog_four_patch_genome_to_dict,
    build_analog_four_patch_genome,
)
from .extractor import (
    AudioFeatureAnalysis,
    AudioSynthesisFeatures,
    AudioSynthesisFeaturesPayload,
    StyleAnalysisDependencyError,
    analyze_audio,
    analyze_audio_snapshot,
    audio_synthesis_features_to_dict,
)
from .feature_report import (
    FeatureReport,
    FeatureReportPayload,
    compute_feature_report_hash,
    feature_report_to_dict,
)
from .runtime_types import require_runtime_type

_AUDIO_REPORT_DERIVED_AT: Final[str] = "1970-01-01T00:00:00Z"
_INFERENCE_FAILURE_FINGERPRINT: Final[str] = "a4.audio_patch.inference_failed"
_NATIVE_CLEANUP_ERROR_KIND: Final[str] = "a4_native_analysis_cleanup"
_NATIVE_CLEANUP_FINGERPRINT: Final[str] = "a4.audio_patch.native_cleanup_failed"
_NATIVE_ANALYSIS_TIMEOUT_SECONDS: Final[float] = 60.0
_NATIVE_ANALYSIS_EXIT_TIMEOUT_SECONDS: Final[float] = 2.0
_logger = get_logger(__name__)
_InferenceResult = TypeVar("_InferenceResult")


def _audio_path_name(value: object) -> str:
    return value.name if isinstance(value, Path) else "<invalid>"


class _NativeAnalysisConnection(Protocol):
    @abstractmethod
    def send(self, value: object) -> None: ...

    @abstractmethod
    def recv(self) -> object: ...

    @abstractmethod
    def poll(self, timeout: float | None = None) -> bool: ...

    @abstractmethod
    def close(self) -> None: ...


class _NativeAnalysisProcessContext(Protocol):
    @abstractmethod
    def Pipe(
        self, *, duplex: bool  # noqa: V107 - required multiprocessing keyword contract
    ) -> tuple[_NativeAnalysisConnection, _NativeAnalysisConnection]: ...

    @abstractmethod
    def Process(self, **kwargs: object) -> BaseProcess: ...  # noqa: V107 - protocol contract


_NativeAnalysisWorker: TypeAlias = Callable[[str, _NativeAnalysisConnection], None]


AnalogFourPatchAudioFeatures: TypeAlias = AudioSynthesisFeatures
AnalogFourPatchAudioFeaturesPayload: TypeAlias = AudioSynthesisFeaturesPayload
AnalogFourFeatureReportPayload: TypeAlias = FeatureReportPayload


@dataclass(frozen=True)
class AnalogFourAudioPatchGenome:
    """Measured audio evidence and its inferred Analog Four patch genome."""

    feature_report: FeatureReport
    audio_features: AnalogFourPatchAudioFeatures
    genome: AnalogFourPatchGenome


class AnalogFourAudioPatchGenomePayload(TypedDict):
    feature_report: AnalogFourFeatureReportPayload
    audio_features: AnalogFourPatchAudioFeaturesPayload
    genome: AnalogFourPatchGenomePayload


@dataclass(frozen=True)
class _NativeAnalysisFailure:
    error_code: AnalogFourPatchInferenceErrorCode
    error_type: str
    message: str
    fingerprint: str


@dataclass(frozen=True)
class _NativeAnalysisMessage:
    analysis: AudioFeatureAnalysis | None = None
    failure: _NativeAnalysisFailure | None = None

    def __post_init__(self) -> None:
        if (self.analysis is None) == (self.failure is None):
            raise ValueError("native analysis message must contain exactly one result")


def analyze_analog_four_patch_audio(path: Path) -> AnalogFourPatchAudioFeatures:
    """Measure normalized A4 synthesis evidence from ``path``."""

    return _recorded_a4_inference(
        path,
        lambda: _audio_features_from_analysis(_analyze_audio_for_a4(path)),
    )


def analyze_analog_four_patch_audio_isolated(path: Path) -> AnalogFourPatchAudioFeatures:
    """Measure A4 synthesis evidence with native decoding in a child process."""

    return _recorded_a4_inference(
        path,
        lambda: _audio_features_from_analysis(_run_native_audio_analysis_process(path)),
    )


def analyze_analog_four_patch_audio_analysis_isolated(path: Path) -> AudioFeatureAnalysis:
    """Return the complete shared analysis with native decoding isolated."""

    return _recorded_a4_inference(
        path,
        lambda: _run_native_audio_analysis_process(path),
    )


def _a4_inference_error_code(exc: BaseException) -> AnalogFourPatchInferenceErrorCode:
    if isinstance(exc, (KeyboardInterrupt, SystemExit)):
        return "interrupted"
    if isinstance(exc, BoundaryError):
        error_code = exc.context.get("error_code")
        if error_code in (
            "audio_read_failed",
            "dependency_missing",
            "inference_failed",
            "interrupted",
            "validation",
        ):
            return error_code
    if isinstance(exc, StyleAnalysisDependencyError):
        return "dependency_missing"
    if isinstance(exc, OSError):
        return "audio_read_failed"
    if isinstance(exc, (TypeError, ValueError)):
        return "validation"
    return "inference_failed"


def _record_a4_inference_failure(
    path: object,
    exc: BaseException,
    *,
    started_at: float,
) -> None:
    error_code = _a4_inference_error_code(exc)
    duration_ms = (time.perf_counter() - started_at) * 1000.0
    metrics = get_metrics()
    metrics.record_a4_patch_inference(duration_ms, error_code=error_code)
    fingerprint = getattr(exc, "fingerprint", _INFERENCE_FAILURE_FINGERPRINT)
    if isinstance(exc, BoundaryError):
        fingerprint = str(exc.context.get("fingerprint", fingerprint))
    _logger.warning(
        "Analog Four audio patch inference failed",
        extra={
            "operation": "a4_audio_patch_inference",
            "outcome": "failed",
            "error_code": error_code,
            "fingerprint": fingerprint,
            "audio_name": path.name if isinstance(path, Path) else "<invalid>",
            "duration_ms": duration_ms,
            "error_type": type(exc).__name__,
            "metrics_summary": metrics.format_summary(),
        },
    )


def _recorded_a4_inference(
    path: Path,
    action: Callable[[], _InferenceResult],
) -> _InferenceResult:
    started_at = time.perf_counter()
    metrics = get_metrics()
    with trace_operation(
        "a4_audio_patch_inference",
        logger=_logger,
        audio_name=_audio_path_name(path),
    ):
        try:
            validated_path = require_runtime_type(
                path,
                Path,
                "path must be a pathlib.Path",
            )
            result = action()
        except (KeyboardInterrupt, SystemExit) as exc:
            _record_a4_inference_failure(path, exc, started_at=started_at)
            raise
        except (BoundaryError, KeyError, OSError, RuntimeError, TypeError, ValueError) as exc:
            _record_a4_inference_failure(path, exc, started_at=started_at)
            raise

        duration_ms = (time.perf_counter() - started_at) * 1000.0
        metrics.record_a4_patch_inference(duration_ms)
        _logger.info(
            "Analog Four audio patch inference completed",
            extra={
                "operation": "a4_audio_patch_inference",
                "outcome": "completed",
                "audio_name": validated_path.name,
                "duration_ms": duration_ms,
                "metrics_summary": metrics.format_summary(),
            },
        )
        return result


def _analyze_audio_for_a4(path: Path) -> AudioFeatureAnalysis:
    return analyze_audio(path)


def _send_native_analysis_failure(
    sender: _NativeAnalysisConnection,
    exc: BaseException,
) -> None:
    failure = _NativeAnalysisFailure(
        error_code=_a4_inference_error_code(exc),
        error_type=type(exc).__name__,
        message=str(exc),
        fingerprint=getattr(exc, "fingerprint", _INFERENCE_FAILURE_FINGERPRINT),
    )
    try:
        sender.send(_NativeAnalysisMessage(failure=failure))
    except (BrokenPipeError, EOFError, OSError):
        pass


def _native_audio_analysis_worker(
    audio_path: str,
    sender: _NativeAnalysisConnection,
) -> None:
    try:
        analysis = analyze_audio_snapshot(Path(audio_path))
        sender.send(_NativeAnalysisMessage(analysis=analysis))
    except (KeyboardInterrupt, SystemExit) as exc:
        _send_native_analysis_failure(sender, exc)
    except (KeyError, OSError, RuntimeError, TypeError, ValueError) as exc:
        _send_native_analysis_failure(sender, exc)
    finally:
        _close_native_analysis_resource(sender, resource_kind="worker_sender")


def _terminate_native_analysis_process(process: BaseProcess) -> None:
    if process.is_alive():
        process.terminate()
        process.join(_NATIVE_ANALYSIS_EXIT_TIMEOUT_SECONDS)
    if process.is_alive():
        process.kill()
        process.join(_NATIVE_ANALYSIS_EXIT_TIMEOUT_SECONDS)


def _record_native_cleanup_failure(*, resource_kind: str, exc: BaseException) -> None:
    metrics = get_metrics()
    metrics.record_error(_NATIVE_CLEANUP_ERROR_KIND)
    _logger.warning(
        "Analog Four native analysis cleanup failed",
        extra={
            "operation": "a4_native_audio_analysis_cleanup",
            "outcome": "cleanup_failed",
            "error_code": "cleanup_failed",
            "fingerprint": _NATIVE_CLEANUP_FINGERPRINT,
            "resource_kind": resource_kind,
            "error_type": type(exc).__name__,
            "metrics_summary": metrics.format_summary(),
        },
    )


def _close_native_analysis_resource(
    resource: _NativeAnalysisConnection | BaseProcess,
    *,
    resource_kind: str,
) -> None:
    try:
        resource.close()
    except (OSError, RuntimeError, ValueError) as exc:
        _record_native_cleanup_failure(resource_kind=resource_kind, exc=exc)


def _terminate_native_analysis_process_safely(process: BaseProcess) -> None:
    try:
        _terminate_native_analysis_process(process)
    except (OSError, RuntimeError, ValueError) as exc:
        _record_native_cleanup_failure(resource_kind="process_termination", exc=exc)


def _cleanup_native_analysis_parent(
    receiver: _NativeAnalysisConnection,
    sender: _NativeAnalysisConnection,
    process: BaseProcess,
    *,
    started: bool,
) -> None:
    """Close every parent resource, then propagate the first operator interruption."""

    interruptions: list[KeyboardInterrupt | SystemExit] = []

    def run_cleanup(action: Callable[[], None]) -> None:
        try:
            action()
        except (KeyboardInterrupt, SystemExit) as exc:
            if not interruptions:
                interruptions.append(exc)
            else:
                _record_native_cleanup_failure(
                    resource_kind="secondary_interruption",
                    exc=exc,
                )

    run_cleanup(
        lambda: _close_native_analysis_resource(
            receiver,
            resource_kind="parent_receiver",
        )
    )
    run_cleanup(
        lambda: _close_native_analysis_resource(
            sender,
            resource_kind="parent_sender",
        )
    )
    if started:
        run_cleanup(lambda: _terminate_native_analysis_process_safely(process))
    run_cleanup(
        lambda: _close_native_analysis_resource(
            process,
            resource_kind="process",
        )
    )
    if interruptions:
        interruption = interruptions[0]
        if isinstance(interruption, KeyboardInterrupt):
            raise KeyboardInterrupt(*interruption.args) from interruption
        raise SystemExit(interruption.code) from interruption


def _raise_native_analysis_failure(
    failure: _NativeAnalysisFailure,
) -> None:
    if failure.error_code == "dependency_missing":
        raise StyleAnalysisDependencyError(failure.message)
    if failure.error_code == "audio_read_failed":
        raise BoundaryError(
            failure.message,
            context={
                "error_code": failure.error_code,
                "fingerprint": failure.fingerprint,
                "worker_error_type": failure.error_type,
            },
        )
    if failure.error_code == "validation":
        raise ValueError(failure.message)
    if failure.error_code == "interrupted":
        raise KeyboardInterrupt(failure.message or "native audio analysis interrupted")
    raise BoundaryError(
        failure.message or "native audio analysis worker failed",
        context={
            "error_code": failure.error_code,
            "exit_code": 0,
            "fingerprint": failure.fingerprint,
            "worker_error_type": failure.error_type,
        },
    )


def _start_native_analysis_process(process: BaseProcess) -> None:
    try:
        process.start()
    except OSError as exc:
        raise BoundaryError(
            "native audio analysis worker could not start",
            context={
                "error_code": "inference_failed",
                "fingerprint": "a4.audio_patch.native_analysis_failed",
            },
        ) from exc


def _join_native_analysis_process(
    process: BaseProcess,
    *,
    timeout: float = _NATIVE_ANALYSIS_EXIT_TIMEOUT_SECONDS,
) -> None:
    try:
        process.join(timeout)
    except (KeyboardInterrupt, SystemExit):
        _terminate_native_analysis_process_safely(process)
        raise
    if process.is_alive():
        _terminate_native_analysis_process_safely(process)
        raise BoundaryError(
            "native audio analysis worker did not exit after returning a result",
            context={
                "error_code": "inference_failed",
                "fingerprint": "a4.audio_patch.native_analysis_failed",
                "timeout_seconds": timeout,
            },
        )
    if process.exitcode != 0:
        raise BoundaryError(
            "native audio analysis worker exited without a result",
            context={
                "error_code": "inference_failed",
                "exit_code": process.exitcode,
                "fingerprint": "a4.audio_patch.native_analysis_failed",
            },
        )


def _wait_for_native_analysis_result(
    receiver: _NativeAnalysisConnection,
    process: BaseProcess,
    *,
    timeout: float,
) -> AudioFeatureAnalysis:
    try:
        result_ready = receiver.poll(timeout)
    except (KeyboardInterrupt, SystemExit):
        _terminate_native_analysis_process_safely(process)
        raise
    except (EOFError, OSError) as exc:
        _join_native_analysis_process(process)
        raise BoundaryError(
            "native audio analysis worker exited without a result",
            context={
                "error_code": "inference_failed",
                "exit_code": process.exitcode,
                "fingerprint": "a4.audio_patch.native_analysis_failed",
            },
        ) from exc
    if not result_ready:
        _terminate_native_analysis_process_safely(process)
        raise BoundaryError(
            "native audio analysis worker timed out",
            context={
                "error_code": "inference_failed",
                "fingerprint": "a4.audio_patch.native_analysis_failed",
                "timeout_seconds": timeout,
            },
        )
    analysis = _receive_native_analysis_message(receiver, process)
    _join_native_analysis_process(process)
    return analysis


def _receive_native_analysis_message(
    receiver: _NativeAnalysisConnection,
    process: BaseProcess,
) -> AudioFeatureAnalysis:
    try:
        message = receiver.recv()
    except (EOFError, OSError) as exc:
        _join_native_analysis_process(process)
        raise BoundaryError(
            "native audio analysis worker exited without a result",
            context={
                "error_code": "inference_failed",
                "exit_code": process.exitcode,
                "fingerprint": "a4.audio_patch.native_analysis_failed",
            },
        ) from exc
    if not isinstance(message, _NativeAnalysisMessage):
        raise BoundaryError(
            "native audio analysis worker returned an invalid result",
            context={
                "error_code": "inference_failed",
                "exit_code": process.exitcode,
                "fingerprint": "a4.audio_patch.native_analysis_failed",
                "worker_error_type": type(message).__name__,
            },
        )
    if message.failure is not None:
        _raise_native_analysis_failure(message.failure)
    if message.analysis is None:
        raise BoundaryError(
            "native audio analysis worker exited without a result",
            context={
                "error_code": "inference_failed",
                "exit_code": process.exitcode,
                "fingerprint": "a4.audio_patch.native_analysis_failed",
            },
        )
    return message.analysis


def _run_native_audio_analysis_process(
    path: Path,
    *,
    worker: _NativeAnalysisWorker = _native_audio_analysis_worker,
    process_context: _NativeAnalysisProcessContext | None = None,
    timeout: float = _NATIVE_ANALYSIS_TIMEOUT_SECONDS,
) -> AudioFeatureAnalysis:
    """Run native decoding in a spawned child and return its bounded result."""

    context = process_context or cast(
        _NativeAnalysisProcessContext,
        multiprocessing.get_context("spawn"),
    )
    receiver, sender = context.Pipe(duplex=False)
    process = context.Process(
        target=worker,
        args=(str(path), sender),
        name="a4-native-audio-analysis",
    )
    started = False
    primary_interruption: KeyboardInterrupt | SystemExit | None = None
    try:
        _start_native_analysis_process(process)
        started = True
        _close_native_analysis_resource(sender, resource_kind="parent_sender")
        return _wait_for_native_analysis_result(
            receiver,
            process,
            timeout=timeout,
        )
    except (KeyboardInterrupt, SystemExit) as exc:
        primary_interruption = exc
        raise
    finally:
        try:
            _cleanup_native_analysis_parent(
                receiver,
                sender,
                process,
                started=started,
            )
        except (KeyboardInterrupt, SystemExit) as cleanup_exc:
            if primary_interruption is None:
                raise
            primary_interruption.add_note(
                "additional operator interruption occurred during native-analysis "
                f"cleanup: {type(cleanup_exc).__name__}"
            )


def _audio_features_from_analysis(
    analysis: AudioFeatureAnalysis,
) -> AnalogFourPatchAudioFeatures:
    return analysis.synthesis_features


def build_analog_four_audio_patch_genome(
    path: Path,
    *,
    track: int = 1,
    candidate_count: int = ANALOG_FOUR_PATCH_CANDIDATE_MAX,
) -> AnalogFourAudioPatchGenome:
    """Infer deterministic audio-dependent A4 candidates from ``path``."""

    return _recorded_a4_inference(
        path,
        lambda: _build_analog_four_audio_patch_genome(
            path,
            track=track,
            candidate_count=candidate_count,
        ),
    )


def build_analog_four_audio_patch_genome_isolated(
    path: Path,
    *,
    track: int = 1,
    candidate_count: int = ANALOG_FOUR_PATCH_CANDIDATE_MAX,
) -> AnalogFourAudioPatchGenome:
    """Infer A4 candidates while containing native audio work in a child."""

    return _recorded_a4_inference(
        path,
        lambda: _build_analog_four_audio_patch_genome_from_analysis(
            _run_native_audio_analysis_process(path),
            track=track,
            candidate_count=candidate_count,
        ),
    )


def build_analog_four_audio_patch_genome_from_analysis(
    analysis: AudioFeatureAnalysis,
    *,
    track: int = 1,
    candidate_count: int = ANALOG_FOUR_PATCH_CANDIDATE_MAX,
) -> AnalogFourAudioPatchGenome:
    """Infer A4 candidates from an already-decoded shared analysis."""

    validated_analysis = require_runtime_type(
        analysis,
        AudioFeatureAnalysis,
        "analysis must be AudioFeatureAnalysis",
    )
    return _build_analog_four_audio_patch_genome_from_analysis(
        validated_analysis,
        track=track,
        candidate_count=candidate_count,
    )


def _build_analog_four_audio_patch_genome(
    path: Path,
    *,
    track: int,
    candidate_count: int,
) -> AnalogFourAudioPatchGenome:
    """Build one genome inside the complete-operation metrics boundary."""

    return _build_analog_four_audio_patch_genome_from_analysis(
        _analyze_audio_for_a4(path),
        track=track,
        candidate_count=candidate_count,
    )


def _build_analog_four_audio_patch_genome_from_analysis(
    analysis: AudioFeatureAnalysis,
    *,
    track: int,
    candidate_count: int,
) -> AnalogFourAudioPatchGenome:
    audio_features = _audio_features_from_analysis(analysis)
    feature_report = _stable_audio_feature_report(analysis.feature_report)
    static_genome = build_analog_four_patch_genome(
        feature_report,
        track=track,
        candidate_count=candidate_count,
    )
    genome = replace(
        static_genome,
        source_hash=audio_features.audio_sha256,
        candidates=tuple(
            _infer_candidate(candidate, audio_features) for candidate in static_genome.candidates
        ),
    )
    return AnalogFourAudioPatchGenome(
        feature_report=feature_report,
        audio_features=audio_features,
        genome=genome,
    )


def analog_four_patch_audio_features_to_dict(
    features: AnalogFourPatchAudioFeatures,
) -> AnalogFourPatchAudioFeaturesPayload:
    """Return a stable JSON-ready representation of audio evidence."""

    validated_features = require_runtime_type(
        features,
        AudioSynthesisFeatures,
        "features must be AnalogFourPatchAudioFeatures",
    )
    return audio_synthesis_features_to_dict(validated_features)


def analog_four_audio_patch_genome_to_dict(
    audio_genome: AnalogFourAudioPatchGenome,
) -> AnalogFourAudioPatchGenomePayload:
    """Return a stable JSON-ready representation of inferred patch DNA."""

    validated_audio_genome = require_runtime_type(
        audio_genome,
        AnalogFourAudioPatchGenome,
        "audio_genome must be an AnalogFourAudioPatchGenome",
    )
    report = validated_audio_genome.feature_report
    return {
        "feature_report": feature_report_to_dict(report),
        "audio_features": analog_four_patch_audio_features_to_dict(
            validated_audio_genome.audio_features
        ),
        "genome": analog_four_patch_genome_to_dict(validated_audio_genome.genome),
    }


def _stable_audio_feature_report(report: FeatureReport) -> FeatureReport:
    stable = replace(report, content_hash="", derived_at=_AUDIO_REPORT_DERIVED_AT)
    return replace(stable, content_hash=compute_feature_report_hash(stable))


def _infer_candidate(
    candidate: AnalogFourPatchCandidate,
    features: AnalogFourPatchAudioFeatures,
) -> AnalogFourPatchCandidate:
    return replace(
        candidate,
        genes=tuple(_infer_gene(gene, candidate.column, features) for gene in candidate.genes),
    )


def _infer_gene(
    gene: AnalogFourPatchGene,
    column: int,
    features: AnalogFourPatchAudioFeatures,
) -> AnalogFourPatchGene:
    screen_target = _inferred_screen_target(gene.value.parameter, column, features)
    if screen_target is None:
        return gene
    return replace(
        gene,
        value=make_a4_patch_value(gene.value.parameter, screen_target=screen_target),
        rationale=f"{gene.rationale}; adjusted from measured audio evidence",
    )


def _inferred_screen_target(
    parameter: str,
    column: int,
    features: AnalogFourPatchAudioFeatures,
) -> int | None:
    feature_values = build_analog_four_inference_feature_values(features, column=column)
    if parameter not in ANALOG_FOUR_AUDIO_INFERENCE_BY_PARAMETER:
        return None
    spec = ANALOG_FOUR_AUDIO_INFERENCE_BY_PARAMETER[cast(AnalogFourInferenceParameter, parameter)]
    return evaluate_analog_four_inference_spec(spec, feature_values)


def build_analog_four_inference_feature_values(
    features: AnalogFourPatchAudioFeatures,
    *,
    column: object,
) -> Mapping[AnalogFourInferenceFeatureKey, float]:
    """Return the canonical feature inputs used by one A4 candidate column."""

    validated_features = require_runtime_type(
        features,
        AudioSynthesisFeatures,
        "features must be AudioSynthesisFeatures",
    )
    if isinstance(column, bool) or not isinstance(column, int):
        raise TypeError("column must be int")
    if not 1 <= column <= len(ANALOG_FOUR_PATCH_CANDIDATE_TEMPLATES):
        raise ValueError(
            "candidate column must be in " f"1..{len(ANALOG_FOUR_PATCH_CANDIDATE_TEMPLATES)}"
        )
    brightness, noise, low_end, animation, tail = _candidate_character(validated_features, column)
    return {
        "attack": validated_features.attack,
        "decay": validated_features.decay,
        "sustain": validated_features.sustain,
        "duration": validated_features.duration,
        "brightness": brightness,
        "noise": noise,
        "low_end": low_end,
        "animation": animation,
        "tail": tail,
        "harmonicity": validated_features.harmonicity,
        "transient": validated_features.transient,
    }


def evaluate_analog_four_inference_spec(
    spec: AnalogFourAudioInferenceSpec,
    feature_values: object,
) -> int:
    """Evaluate one canonical A4 inference equation and apply its scale clamp."""

    validated_spec = require_runtime_type(
        spec,
        AnalogFourAudioInferenceSpec,
        "spec must be AnalogFourAudioInferenceSpec",
    )
    if not isinstance(feature_values, Mapping):
        raise TypeError("feature_values must be Mapping")
    validated_feature_values = cast(Mapping[AnalogFourInferenceFeatureKey, float], feature_values)
    value = validated_spec.intercept
    for term in validated_spec.terms:
        product = 1.0
        for feature_key in term.feature_keys:
            product *= validated_feature_values[feature_key]
        value += product * term.coefficient
    value *= validated_spec.output_multiplier
    if validated_spec.scale == A4_AUDIO_INFERENCE_BIPOLAR:
        return _bipolar(value)
    return _unipolar(value)


def _candidate_character(
    features: AnalogFourPatchAudioFeatures,
    column: int,
) -> tuple[float, float, float, float, float]:
    try:
        template = ANALOG_FOUR_PATCH_CANDIDATE_TEMPLATES[column - 1]
    except IndexError as exc:
        raise ValueError(
            f"candidate column must be in 1..{len(ANALOG_FOUR_PATCH_CANDIDATE_TEMPLATES)}"
        ) from exc
    if template.column != column:
        raise ValueError("candidate template columns must be contiguous and one-based")
    return (
        clamp_audio_feature_unit(features.brightness + template.brightness_offset),
        clamp_audio_feature_unit(features.noise + template.noise_offset),
        clamp_audio_feature_unit(features.low_end + template.low_end_offset),
        clamp_audio_feature_unit(features.modulation + template.animation_offset),
        clamp_audio_feature_unit(features.tail + template.tail_offset),
    )


def _unipolar(value: float) -> int:
    return max(0, min(127, int(round(value))))


def _bipolar(value: float) -> int:
    return max(-64, min(63, int(round(value))))


def clamp_audio_feature_unit(value: float) -> float:
    """Clamp one normalized audio feature to the closed unit interval."""

    return max(0.0, min(1.0, float(value)))


__all__ = [
    "AnalogFourAudioPatchGenome",
    "AnalogFourAudioPatchGenomePayload",
    "AnalogFourFeatureReportPayload",
    "AnalogFourPatchAudioFeatures",
    "AnalogFourPatchAudioFeaturesPayload",
    "analog_four_audio_patch_genome_to_dict",
    "analog_four_patch_audio_features_to_dict",
    "analyze_analog_four_patch_audio",
    "analyze_analog_four_patch_audio_analysis_isolated",
    "analyze_analog_four_patch_audio_isolated",
    "build_analog_four_audio_patch_genome",
    "build_analog_four_audio_patch_genome_from_analysis",
    "build_analog_four_audio_patch_genome_isolated",
    "build_analog_four_inference_feature_values",
    "clamp_audio_feature_unit",
    "evaluate_analog_four_inference_spec",
]
