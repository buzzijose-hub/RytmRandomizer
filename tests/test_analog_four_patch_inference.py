"""Tests for deterministic Analog Four audio-to-patch inference."""

from __future__ import annotations

import dataclasses
import json
import os
import pickle
from collections.abc import Iterator
from contextlib import contextmanager
from multiprocessing.connection import Connection
from pathlib import Path

import pytest

from rytm_randomizer.guardrails.schema import Confidence, SourceType
from rytm_randomizer.style_analysis import FeatureReport

pytestmark = pytest.mark.fast


def _reference_report(*, derived_at: str = "2026-07-16T12:00:00Z") -> FeatureReport:
    return FeatureReport(
        source_type=SourceType.SINGLE_TRACK,
        confidence=Confidence.HIGH,
        bpm=128.0,
        tempo_stability=0.94,
        kick_density=0.18,
        percussion_density=0.41,
        low_end_weight=0.48,
        spectral_brightness=0.52,
        texture_noise=0.21,
        energy_arc=(0.12, 0.82, 0.64, 0.48, 0.35, 0.24, 0.16, 0.08),
        content_hash="time-dependent-placeholder",
        derived_at=derived_at,
    )


def _features(
    *,
    audio_sha256: str = "a" * 64,
    duration: float = 0.38,
    attack: float = 0.05,
    decay: float = 0.32,
    sustain: float = 0.18,
    tail: float = 0.24,
    brightness: float = 0.58,
    spectral_flatness: float = 0.12,
    noise: float = 0.16,
    low_end: float = 0.44,
    harmonicity: float = 0.76,
    transient: float = 0.82,
    modulation: float = 0.22,
):
    from rytm_randomizer.style_analysis.analog_four_patch_inference import (
        AnalogFourPatchAudioFeatures,
    )

    return AnalogFourPatchAudioFeatures(
        audio_sha256=audio_sha256,
        duration=duration,
        attack=attack,
        decay=decay,
        sustain=sustain,
        tail=tail,
        brightness=brightness,
        spectral_flatness=spectral_flatness,
        noise=noise,
        low_end=low_end,
        harmonicity=harmonicity,
        transient=transient,
        modulation=modulation,
    )


def _analysis(*, features=None, report: FeatureReport | None = None):
    from rytm_randomizer.style_analysis.extractor import AudioFeatureAnalysis

    settled = features or _features()
    return AudioFeatureAnalysis(
        feature_report=report or _reference_report(),
        synthesis_features=settled,
    )


def _successful_native_analysis_worker(_path: str, sender: Connection) -> None:
    from rytm_randomizer.style_analysis import analog_four_patch_inference as inference

    sender.send(inference._NativeAnalysisMessage(analysis=_analysis()))
    sender.close()


def _hard_exit_native_analysis_worker(_path: str, sender: Connection) -> None:
    sender.close()
    os._exit(73)


class _FakeConnection:
    def __init__(
        self,
        *,
        incoming: object | None = None,
        send_error: OSError | None = None,
        receive_error: OSError | EOFError | None = None,
        poll_result: bool = True,
        poll_error: OSError | EOFError | KeyboardInterrupt | None = None,
        close_error: BaseException | None = None,
    ) -> None:
        self.incoming = incoming
        self.send_error = send_error
        self.receive_error = receive_error
        self.poll_result = poll_result
        self.poll_error = poll_error
        self.close_error = close_error
        self.poll_timeouts: list[float | None] = []
        self.sent: list[object] = []
        self.closed = False

    def send(self, value: object) -> None:
        if self.send_error is not None:
            raise self.send_error
        self.sent.append(value)

    def recv(self) -> object:
        if self.receive_error is not None:
            raise self.receive_error
        return self.incoming

    def poll(self, timeout: float | None = None) -> bool:
        self.poll_timeouts.append(timeout)
        if self.poll_error is not None:
            raise self.poll_error
        return self.poll_result

    def close(self) -> None:
        self.closed = True
        if self.close_error is not None:
            raise self.close_error


class _FakeProcess:
    def __init__(
        self,
        *,
        alive: bool = False,
        exitcode: int | None = 0,
        start_error: OSError | None = None,
        join_error: KeyboardInterrupt | SystemExit | None = None,
        join_stays_alive: bool = False,
        terminate_stays_alive: bool = False,
    ) -> None:
        self.alive = alive
        self.exitcode = exitcode
        self.start_error = start_error
        self.join_error = join_error
        self.join_stays_alive = join_stays_alive
        self.terminate_stays_alive = terminate_stays_alive
        self.started = False
        self.joined = False
        self.terminated = False
        self.killed = False
        self.closed = False

    def start(self) -> None:
        if self.start_error is not None:
            raise self.start_error
        self.started = True

    def join(self, _timeout: float | None = None) -> None:
        if self.join_error is not None:
            error = self.join_error
            self.join_error = None
            raise error
        self.joined = True
        if not self.join_stays_alive:
            self.alive = False

    def is_alive(self) -> bool:
        return self.alive

    def terminate(self) -> None:
        self.terminated = True
        if not self.terminate_stays_alive:
            self.alive = False

    def kill(self) -> None:
        self.killed = True
        self.alive = False

    def close(self) -> None:
        self.closed = True


class _FakeProcessContext:
    def __init__(
        self,
        receiver: _FakeConnection,
        sender: _FakeConnection,
        process: _FakeProcess,
    ) -> None:
        self.receiver = receiver
        self.sender = sender
        self.process = process

    def Pipe(self, *, duplex: bool) -> tuple[_FakeConnection, _FakeConnection]:
        assert duplex is False
        return self.receiver, self.sender

    def Process(self, **_kwargs: object) -> _FakeProcess:
        return self.process


def _gene(candidate, parameter: str):
    matches = [gene for gene in candidate.genes if gene.value.parameter == parameter]
    assert matches, f"Missing parameter {parameter}"
    return matches[0]


def _candidate_dna(audio_genome) -> tuple[tuple[tuple[str, int | None], ...], ...]:
    return tuple(
        tuple((gene.value.parameter, gene.value.midi_value) for gene in candidate.genes)
        for candidate in audio_genome.genome.candidates
    )


def test_audio_feature_analysis_reuses_shared_audio_measurements(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from rytm_randomizer.observability.metrics import get_metrics, reset_metrics
    from rytm_randomizer.style_analysis import analog_four_patch_inference as inference

    measured = _features(
        audio_sha256="9" * 64,
        duration=0.5,
        attack=0.1,
        decay=0.2,
        sustain=0.3,
        tail=0.4,
        brightness=0.5,
        spectral_flatness=0.6,
        noise=0.7,
        low_end=0.8,
        harmonicity=0.9,
        transient=1.0,
        modulation=0.0,
    )
    observed: list[Path] = []
    monkeypatch.setattr(
        inference,
        "analyze_audio",
        lambda path: observed.append(path) or _analysis(features=measured),
    )

    reset_metrics()
    features = inference.analyze_analog_four_patch_audio(Path("reference.wav"))

    assert observed == [Path("reference.wav")]
    assert features.audio_sha256 == "9" * 64
    assert features.duration == 0.5
    assert inference.analog_four_patch_audio_features_to_dict(features)["noise"] == 0.7
    assert get_metrics().a4_patch_inference_count == 1


@pytest.mark.parametrize(
    ("error", "error_code"),
    [
        (OSError("read failed"), "audio_read_failed"),
        (TypeError("bad path"), "validation"),
        (KeyError("missing feature"), "inference_failed"),
        (RuntimeError("analysis failed"), "inference_failed"),
    ],
)
def test_audio_feature_analysis_records_bounded_failures(
    monkeypatch: pytest.MonkeyPatch,
    error: Exception,
    error_code: str,
) -> None:
    from rytm_randomizer.observability.metrics import get_metrics, reset_metrics
    from rytm_randomizer.style_analysis import analog_four_patch_inference as inference

    def fail(_path: Path) -> object:
        raise error

    logged: list[dict[str, object]] = []
    reset_metrics()
    monkeypatch.setattr(inference, "analyze_audio", fail)
    monkeypatch.setattr(
        inference._logger,
        "warning",
        lambda _message, *, extra: logged.append(extra),
    )
    with pytest.raises(type(error), match=str(error)):
        inference.analyze_analog_four_patch_audio(Path("reference.wav"))

    assert get_metrics().a4_patch_inference_errors_by_code[error_code] == 1
    assert logged[0]["fingerprint"] == "a4.audio_patch.inference_failed"
    assert logged[0]["error_type"] == type(error).__name__
    assert float(logged[0]["duration_ms"]) >= 0.0
    assert "a4_inference_errors" in str(logged[0]["metrics_summary"])


def test_audio_feature_analysis_records_non_path_validation_inside_trace(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from rytm_randomizer.observability.metrics import get_metrics, reset_metrics
    from rytm_randomizer.style_analysis import analog_four_patch_inference as inference

    traced: list[tuple[str, str]] = []
    logged: list[dict[str, object]] = []

    @contextmanager
    def observe_operation(name: str, **_kwargs: object) -> Iterator[None]:
        traced.append(("start", name))
        try:
            yield
        except BaseException:
            traced.append(("error", name))
            raise

    monkeypatch.setattr(inference, "trace_operation", observe_operation)
    monkeypatch.setattr(
        inference._logger,
        "warning",
        lambda _message, *, extra: logged.append(extra),
    )
    reset_metrics()

    with pytest.raises(TypeError, match="path must be"):
        inference.analyze_analog_four_patch_audio("sound.wav")  # type: ignore[arg-type]

    assert traced == [
        ("start", "a4_audio_patch_inference"),
        ("error", "a4_audio_patch_inference"),
    ]
    assert get_metrics().a4_patch_inference_errors_by_code["validation"] == 1
    assert logged[0]["audio_name"] == "<invalid>"
    assert logged[0]["outcome"] == "failed"


def test_audio_feature_analysis_classifies_missing_optional_dependency() -> None:
    from rytm_randomizer.observability.errors import BoundaryError
    from rytm_randomizer.style_analysis import analog_four_patch_inference as inference
    from rytm_randomizer.style_analysis.extractor import StyleAnalysisDependencyError

    assert (
        inference._a4_inference_error_code(StyleAnalysisDependencyError("missing"))
        == "dependency_missing"
    )
    assert (
        inference._a4_inference_error_code(
            BoundaryError(
                "native crash",
                context={"error_code": "audio_read_failed"},
            )
        )
        == "audio_read_failed"
    )
    assert (
        inference._a4_inference_error_code(
            BoundaryError(
                "unknown boundary",
                context={"error_code": "unknown"},
            )
        )
        == "inference_failed"
    )


def test_audio_inference_records_native_boundary_fingerprint(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from rytm_randomizer.observability.errors import BoundaryError
    from rytm_randomizer.observability.metrics import get_metrics, reset_metrics
    from rytm_randomizer.style_analysis import analog_four_patch_inference as inference

    failure = BoundaryError(
        "native worker crashed",
        context={
            "error_code": "inference_failed",
            "fingerprint": "a4.audio_patch.native_analysis_failed",
        },
    )
    logged: list[dict[str, object]] = []
    monkeypatch.setattr(
        inference,
        "analyze_audio",
        lambda _path: (_ for _ in ()).throw(failure),
    )
    monkeypatch.setattr(
        inference._logger,
        "warning",
        lambda _message, *, extra: logged.append(extra),
    )
    reset_metrics()

    with pytest.raises(BoundaryError, match="native worker crashed"):
        inference.analyze_analog_four_patch_audio(Path("reference.wav"))

    assert logged[0]["fingerprint"] == "a4.audio_patch.native_analysis_failed"
    assert get_metrics().a4_patch_inference_errors_by_code["inference_failed"] == 1


def test_isolated_native_analysis_is_pickle_and_json_safe() -> None:
    from rytm_randomizer.style_analysis import analog_four_patch_inference as inference

    first = inference._run_native_audio_analysis_process(
        Path("parent-owned.wav"),
        worker=_successful_native_analysis_worker,
    )
    second = inference._run_native_audio_analysis_process(
        Path("parent-owned.wav"),
        worker=_successful_native_analysis_worker,
    )

    assert first == second
    assert pickle.loads(pickle.dumps(first)) == first  # noqa: S301 - trusted local round-trip
    genome = inference._build_analog_four_audio_patch_genome_from_analysis(
        first,
        track=1,
        candidate_count=2,
    )
    json.dumps(inference.analog_four_audio_patch_genome_to_dict(genome), sort_keys=True)


def test_isolated_native_analysis_classifies_abrupt_child_exit() -> None:
    from rytm_randomizer.observability.errors import BoundaryError
    from rytm_randomizer.style_analysis import analog_four_patch_inference as inference

    with pytest.raises(
        BoundaryError,
        match="exited without a result",
    ) as exc_info:
        inference._run_native_audio_analysis_process(
            Path("parent-owned.wav"),
            worker=_hard_exit_native_analysis_worker,
        )

    assert exc_info.value.context["error_code"] == "inference_failed"
    assert exc_info.value.context["exit_code"] == 73
    assert exc_info.value.context["fingerprint"] == "a4.audio_patch.native_analysis_failed"


def test_native_analysis_message_requires_exactly_one_result() -> None:
    from rytm_randomizer.style_analysis import analog_four_patch_inference as inference

    with pytest.raises(ValueError, match="exactly one result"):
        inference._NativeAnalysisMessage()
    with pytest.raises(ValueError, match="exactly one result"):
        inference._NativeAnalysisMessage(
            analysis=_analysis(),
            failure=inference._NativeAnalysisFailure(
                error_code="inference_failed",
                error_type="RuntimeError",
                message="failed",
                fingerprint="a4.audio_patch.inference_failed",
            ),
        )


def test_native_analysis_worker_serializes_success_and_bounded_failures(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from rytm_randomizer.style_analysis import analog_four_patch_inference as inference
    from rytm_randomizer.style_analysis.extractor import StyleAnalysisDependencyError

    success_sender = _FakeConnection()
    monkeypatch.setattr(inference, "analyze_audio_snapshot", lambda _path: _analysis())
    inference._native_audio_analysis_worker(
        "parent-owned.wav",
        success_sender,  # type: ignore[arg-type]
    )
    success = success_sender.sent[0]
    assert isinstance(success, inference._NativeAnalysisMessage)
    assert success.analysis == _analysis()
    assert success_sender.closed is True

    dependency_sender = _FakeConnection()
    monkeypatch.setattr(
        inference,
        "analyze_audio_snapshot",
        lambda _path: (_ for _ in ()).throw(StyleAnalysisDependencyError("missing style")),
    )
    inference._native_audio_analysis_worker(
        "parent-owned.wav",
        dependency_sender,  # type: ignore[arg-type]
    )
    dependency = dependency_sender.sent[0]
    assert isinstance(dependency, inference._NativeAnalysisMessage)
    assert dependency.failure is not None
    assert dependency.failure.error_code == "dependency_missing"

    interrupted_sender = _FakeConnection(send_error=BrokenPipeError("parent exited"))
    monkeypatch.setattr(
        inference,
        "analyze_audio_snapshot",
        lambda _path: (_ for _ in ()).throw(KeyboardInterrupt("cancelled")),
    )
    inference._native_audio_analysis_worker(
        "parent-owned.wav",
        interrupted_sender,  # type: ignore[arg-type]
    )
    assert interrupted_sender.sent == []
    assert interrupted_sender.closed is True


@pytest.mark.parametrize(
    ("failure", "error_type", "error_code"),
    [
        ("dependency_missing", "StyleAnalysisDependencyError", None),
        ("audio_read_failed", "BoundaryError", "audio_read_failed"),
        ("validation", "ValueError", None),
        ("inference_failed", "BoundaryError", "inference_failed"),
        ("interrupted", "KeyboardInterrupt", None),
    ],
)
def test_native_analysis_failure_reconstruction_is_bounded(
    failure: str,
    error_type: str,
    error_code: str | None,
) -> None:
    from rytm_randomizer.observability.errors import BoundaryError
    from rytm_randomizer.style_analysis import analog_four_patch_inference as inference

    payload = inference._NativeAnalysisFailure(
        error_code=failure,  # type: ignore[arg-type]
        error_type="NativeFailure",
        message="" if failure == "inference_failed" else "worker failed",
        fingerprint="a4.audio_patch.worker_failed",
    )
    expected = {
        "StyleAnalysisDependencyError": inference.StyleAnalysisDependencyError,
        "BoundaryError": BoundaryError,
        "ValueError": ValueError,
        "KeyboardInterrupt": KeyboardInterrupt,
    }[error_type]
    with pytest.raises(expected) as exc_info:
        inference._raise_native_analysis_failure(payload)
    if error_code is not None:
        assert isinstance(exc_info.value, BoundaryError)
        assert exc_info.value.context["error_code"] == error_code


def test_native_analysis_process_helpers_fail_closed_and_cleanup() -> None:
    from rytm_randomizer.observability.errors import BoundaryError
    from rytm_randomizer.style_analysis import analog_four_patch_inference as inference

    start_failure = _FakeProcess(start_error=OSError("spawn denied"))
    with pytest.raises(BoundaryError, match="could not start"):
        inference._start_native_analysis_process(start_failure)  # type: ignore[arg-type]

    interrupted = _FakeProcess(alive=True, join_error=KeyboardInterrupt("cancelled"))
    with pytest.raises(KeyboardInterrupt, match="cancelled"):
        inference._join_native_analysis_process(interrupted)  # type: ignore[arg-type]
    assert interrupted.terminated is True
    assert interrupted.joined is True

    crashed = _FakeProcess(exitcode=0xC0000005)
    with pytest.raises(BoundaryError, match="exited without a result"):
        inference._join_native_analysis_process(crashed)  # type: ignore[arg-type]

    completed = _FakeProcess()
    inference._join_native_analysis_process(completed)  # type: ignore[arg-type]
    assert completed.joined is True
    inference._terminate_native_analysis_process(completed)  # type: ignore[arg-type]
    assert completed.terminated is False

    hung_after_result = _FakeProcess(alive=True, join_stays_alive=True)
    with pytest.raises(BoundaryError, match="did not exit"):
        inference._join_native_analysis_process(
            hung_after_result,  # type: ignore[arg-type]
            timeout=0.01,
        )
    assert hung_after_result.terminated is True

    stubborn = _FakeProcess(
        alive=True,
        exitcode=None,
        join_stays_alive=True,
        terminate_stays_alive=True,
    )
    inference._terminate_native_analysis_process(stubborn)  # type: ignore[arg-type]
    assert stubborn.terminated is True
    assert stubborn.killed is True
    assert stubborn.alive is False


def test_safe_native_process_cleanup_records_operation_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from rytm_randomizer.observability.metrics import get_metrics, reset_metrics
    from rytm_randomizer.style_analysis import analog_four_patch_inference as inference

    class CleanupFailureProcess(_FakeProcess):
        def terminate(self) -> None:
            raise OSError("terminate failed")

    recorded: list[tuple[str, Exception]] = []

    def record_failure(*, resource_kind: str, exc: Exception) -> None:
        recorded.append((resource_kind, exc))

    monkeypatch.setattr(inference, "_record_native_cleanup_failure", record_failure)
    process = CleanupFailureProcess(alive=True)

    inference._terminate_native_analysis_process_safely(process)  # type: ignore[arg-type]

    assert len(recorded) == 1
    assert recorded[0][0] == "process_termination"
    assert isinstance(recorded[0][1], OSError)
    assert str(recorded[0][1]) == "terminate failed"

    logged: list[dict[str, object]] = []
    monkeypatch.undo()
    monkeypatch.setattr(
        inference._logger,
        "warning",
        lambda _message, *, extra: logged.append(extra),
    )
    reset_metrics()
    inference._terminate_native_analysis_process_safely(
        CleanupFailureProcess(alive=True)  # type: ignore[arg-type]
    )

    assert get_metrics().errors_by_kind["a4_native_analysis_cleanup"] == 1
    assert logged[0]["error_code"] == "cleanup_failed"
    assert logged[0]["fingerprint"] == "a4.audio_patch.native_cleanup_failed"
    assert "a4_native_analysis_cleanup:1" in str(logged[0]["metrics_summary"])


@pytest.mark.parametrize("interruption", (KeyboardInterrupt(), SystemExit(7)))
def test_native_resource_cleanup_propagates_interrupts(
    interruption: BaseException,
) -> None:
    from rytm_randomizer.observability.metrics import get_metrics, reset_metrics
    from rytm_randomizer.style_analysis import analog_four_patch_inference as inference

    class InterruptingResource:
        def close(self) -> None:
            raise interruption

    reset_metrics()
    with pytest.raises(type(interruption)):
        inference._close_native_analysis_resource(
            InterruptingResource(),  # type: ignore[arg-type]
            resource_kind="test_resource",
        )

    assert get_metrics().errors_by_kind["a4_native_analysis_cleanup"] == 0


def test_native_process_termination_cleanup_propagates_interrupt() -> None:
    from rytm_randomizer.observability.metrics import get_metrics, reset_metrics
    from rytm_randomizer.style_analysis import analog_four_patch_inference as inference

    class InterruptingProcess(_FakeProcess):
        def terminate(self) -> None:
            raise KeyboardInterrupt("operator cancelled during cleanup")

    reset_metrics()
    with pytest.raises(KeyboardInterrupt, match="operator cancelled during cleanup"):
        inference._terminate_native_analysis_process_safely(
            InterruptingProcess(alive=True)  # type: ignore[arg-type]
        )

    assert get_metrics().errors_by_kind["a4_native_analysis_cleanup"] == 0


def test_native_parent_cleanup_finishes_then_propagates_interrupt() -> None:
    from rytm_randomizer.style_analysis import analog_four_patch_inference as inference

    receiver = _FakeConnection(close_error=KeyboardInterrupt("operator cancelled during cleanup"))
    sender = _FakeConnection()
    process = _FakeProcess(alive=True, exitcode=None)

    with pytest.raises(KeyboardInterrupt, match="operator cancelled during cleanup"):
        inference._cleanup_native_analysis_parent(
            receiver,  # type: ignore[arg-type]
            sender,  # type: ignore[arg-type]
            process,  # type: ignore[arg-type]
            started=True,
        )

    assert receiver.closed is True
    assert sender.closed is True
    assert process.terminated is True
    assert process.closed is True


def test_native_parent_cleanup_propagates_system_exit_code() -> None:
    from rytm_randomizer.style_analysis import analog_four_patch_inference as inference

    receiver = _FakeConnection(close_error=SystemExit(7))
    sender = _FakeConnection()
    process = _FakeProcess()

    with pytest.raises(SystemExit) as exc_info:
        inference._cleanup_native_analysis_parent(
            receiver,  # type: ignore[arg-type]
            sender,  # type: ignore[arg-type]
            process,  # type: ignore[arg-type]
            started=False,
        )

    assert exc_info.value.code == 7
    assert sender.closed is True
    assert process.closed is True


def test_native_parent_cleanup_records_secondary_interruption() -> None:
    from rytm_randomizer.observability.metrics import get_metrics, reset_metrics
    from rytm_randomizer.style_analysis import analog_four_patch_inference as inference

    receiver = _FakeConnection(close_error=KeyboardInterrupt("first interruption"))
    sender = _FakeConnection(close_error=SystemExit(9))
    process = _FakeProcess()
    reset_metrics()

    with pytest.raises(KeyboardInterrupt, match="first interruption"):
        inference._cleanup_native_analysis_parent(
            receiver,  # type: ignore[arg-type]
            sender,  # type: ignore[arg-type]
            process,  # type: ignore[arg-type]
            started=False,
        )

    assert process.closed is True
    assert get_metrics().errors_by_kind["a4_native_analysis_cleanup"] == 1


def test_native_process_runner_propagates_cleanup_only_interruption() -> None:
    from rytm_randomizer.style_analysis import analog_four_patch_inference as inference

    receiver = _FakeConnection(
        incoming=inference._NativeAnalysisMessage(analysis=_analysis()),
        close_error=KeyboardInterrupt("operator cancelled during cleanup"),
    )
    sender = _FakeConnection()
    process = _FakeProcess()
    context = _FakeProcessContext(receiver, sender, process)

    with pytest.raises(KeyboardInterrupt, match="operator cancelled during cleanup"):
        inference._run_native_audio_analysis_process(
            Path("parent-owned.wav"),
            process_context=context,  # type: ignore[arg-type]
        )

    assert process.joined is True
    assert sender.closed is True
    assert process.closed is True


def test_native_parent_cleanup_preserves_inflight_operator_interruption() -> None:
    from rytm_randomizer.style_analysis import analog_four_patch_inference as inference

    receiver = _FakeConnection(
        poll_error=SystemExit(7),
        close_error=KeyboardInterrupt("operator cancelled during cleanup"),
    )
    sender = _FakeConnection()
    process = _FakeProcess(alive=True, exitcode=None)
    context = _FakeProcessContext(receiver, sender, process)

    with pytest.raises(SystemExit) as exc_info:
        inference._run_native_audio_analysis_process(
            Path("parent-owned.wav"),
            process_context=context,  # type: ignore[arg-type]
        )

    assert exc_info.value.code == 7
    assert exc_info.value.__notes__ == [
        "additional operator interruption occurred during native-analysis cleanup: "
        "KeyboardInterrupt"
    ]
    assert receiver.closed is True
    assert sender.closed is True
    assert process.terminated is True
    assert process.closed is True


def test_native_analysis_wait_times_out_and_terminates_worker() -> None:
    from rytm_randomizer.observability.errors import BoundaryError
    from rytm_randomizer.style_analysis import analog_four_patch_inference as inference

    receiver = _FakeConnection(poll_result=False)
    sender = _FakeConnection()
    process = _FakeProcess(alive=True, exitcode=None)
    context = _FakeProcessContext(receiver, sender, process)

    with pytest.raises(BoundaryError, match="timed out") as exc_info:
        inference._run_native_audio_analysis_process(
            Path("parent-owned.wav"),
            process_context=context,  # type: ignore[arg-type]
            timeout=0.01,
        )

    assert receiver.poll_timeouts == [0.01]
    assert process.terminated is True
    assert process.closed is True
    assert exc_info.value.context["error_code"] == "inference_failed"
    assert exc_info.value.context["timeout_seconds"] == 0.01


def test_native_analysis_wait_interrupt_terminates_worker() -> None:
    from rytm_randomizer.style_analysis import analog_four_patch_inference as inference

    receiver = _FakeConnection(poll_error=KeyboardInterrupt("operator cancelled"))
    sender = _FakeConnection()
    process = _FakeProcess(alive=True, exitcode=None)
    context = _FakeProcessContext(receiver, sender, process)

    with pytest.raises(KeyboardInterrupt, match="operator cancelled"):
        inference._run_native_audio_analysis_process(
            Path("parent-owned.wav"),
            process_context=context,  # type: ignore[arg-type]
        )

    assert process.terminated is True
    assert process.closed is True


def test_native_analysis_poll_failure_joins_worker_and_fails_closed() -> None:
    from rytm_randomizer.observability.errors import BoundaryError
    from rytm_randomizer.style_analysis import analog_four_patch_inference as inference

    receiver = _FakeConnection(poll_error=OSError("poll failed"))
    sender = _FakeConnection()
    process = _FakeProcess(exitcode=0)
    context = _FakeProcessContext(receiver, sender, process)

    with pytest.raises(BoundaryError, match="exited without a result") as exc_info:
        inference._run_native_audio_analysis_process(
            Path("parent-owned.wav"),
            process_context=context,  # type: ignore[arg-type]
        )

    assert process.joined is True
    assert process.closed is True
    assert exc_info.value.context["exit_code"] == 0


def test_native_analysis_message_reader_rejects_missing_or_invalid_results() -> None:
    from rytm_randomizer.observability.errors import BoundaryError
    from rytm_randomizer.style_analysis import analog_four_patch_inference as inference

    process = _FakeProcess()
    with pytest.raises(BoundaryError, match="exited without a result"):
        inference._receive_native_analysis_message(
            _FakeConnection(receive_error=EOFError()),  # type: ignore[arg-type]
            process,  # type: ignore[arg-type]
        )
    with pytest.raises(BoundaryError, match="invalid result") as invalid_info:
        inference._receive_native_analysis_message(
            _FakeConnection(incoming={"unexpected": True}),  # type: ignore[arg-type]
            process,  # type: ignore[arg-type]
        )
    assert invalid_info.value.context["worker_error_type"] == "dict"

    failed_message = inference._NativeAnalysisMessage(
        failure=inference._NativeAnalysisFailure(
            error_code="inference_failed",
            error_type="RuntimeError",
            message="worker failed",
            fingerprint="a4.audio_patch.worker_failed",
        )
    )
    with pytest.raises(BoundaryError, match="worker failed"):
        inference._receive_native_analysis_message(
            _FakeConnection(incoming=failed_message),  # type: ignore[arg-type]
            process,  # type: ignore[arg-type]
        )

    corrupted = inference._NativeAnalysisMessage(analysis=_analysis())
    object.__setattr__(corrupted, "analysis", None)
    with pytest.raises(BoundaryError, match="exited without a result"):
        inference._receive_native_analysis_message(
            _FakeConnection(incoming=corrupted),  # type: ignore[arg-type]
            process,  # type: ignore[arg-type]
        )


def test_isolated_public_inference_uses_process_result_and_records_boundary(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from rytm_randomizer.style_analysis import analog_four_patch_inference as inference

    monkeypatch.setattr(
        inference,
        "_run_native_audio_analysis_process",
        lambda _path: _analysis(),
    )
    result = inference.build_analog_four_audio_patch_genome_isolated(
        Path("parent-owned.wav"),
        track=3,
        candidate_count=1,
    )
    assert result.genome.selected_track == 3
    assert result.genome.candidate_count == 1

    features = inference.analyze_analog_four_patch_audio_isolated(Path("parent-owned.wav"))
    assert features == _features()


def test_process_runner_closes_pipe_when_spawn_fails() -> None:
    from rytm_randomizer.observability.errors import BoundaryError
    from rytm_randomizer.style_analysis import analog_four_patch_inference as inference

    receiver = _FakeConnection()
    sender = _FakeConnection()
    process = _FakeProcess(start_error=OSError("spawn denied"))
    context = _FakeProcessContext(receiver, sender, process)

    with pytest.raises(BoundaryError, match="could not start"):
        inference._run_native_audio_analysis_process(
            Path("parent-owned.wav"),
            process_context=context,  # type: ignore[arg-type]
        )

    assert receiver.closed is True
    assert sender.closed is True
    assert process.closed is True


def test_process_runner_finishes_all_cleanup_when_connection_close_fails() -> None:
    from rytm_randomizer.style_analysis import analog_four_patch_inference as inference

    class FailingCloseConnection(_FakeConnection):
        def close(self) -> None:
            self.closed = True
            raise OSError("receiver close failed")

    receiver = FailingCloseConnection(
        incoming=inference._NativeAnalysisMessage(analysis=_analysis())
    )
    sender = _FakeConnection()
    process = _FakeProcess()
    context = _FakeProcessContext(receiver, sender, process)

    result = inference._run_native_audio_analysis_process(
        Path("parent-owned.wav"),
        process_context=context,  # type: ignore[arg-type]
    )

    assert result == _analysis()
    assert receiver.closed is True
    assert sender.closed is True
    assert process.closed is True


def test_inference_boundary_records_and_traces_keyboard_interrupt(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from rytm_randomizer.observability.metrics import get_metrics, reset_metrics
    from rytm_randomizer.style_analysis import analog_four_patch_inference as inference

    events: list[str] = []

    @contextmanager
    def observe_operation(name: str, **_kwargs: object) -> Iterator[None]:
        events.append(f"start:{name}")
        try:
            yield
        except BaseException:
            events.append(f"error:{name}")
            raise

    def interrupt(_path: Path) -> object:
        raise KeyboardInterrupt("operator cancelled")

    reset_metrics()
    monkeypatch.setattr(inference, "trace_operation", observe_operation)
    monkeypatch.setattr(inference, "analyze_audio", interrupt)

    with pytest.raises(KeyboardInterrupt, match="operator cancelled"):
        inference.analyze_analog_four_patch_audio(Path("reference.wav"))

    assert events == [
        "start:a4_audio_patch_inference",
        "error:a4_audio_patch_inference",
    ]
    assert get_metrics().a4_patch_inference_errors_by_code["interrupted"] == 1


def test_audio_genome_metrics_cover_post_analysis_validation_failures(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from rytm_randomizer.observability.metrics import get_metrics, reset_metrics
    from rytm_randomizer.style_analysis import analog_four_patch_inference as inference

    monkeypatch.setattr(inference, "analyze_audio", lambda _path: _analysis())
    reset_metrics()

    with pytest.raises(ValueError, match="track must be"):
        inference.build_analog_four_audio_patch_genome(
            Path("reference.wav"),
            track=0,
        )

    metrics = get_metrics()
    assert metrics.a4_patch_inference_count == 1
    assert metrics.a4_patch_inference_errors_by_code["validation"] == 1


def test_audio_features_are_frozen_normalized_and_type_checked() -> None:
    from rytm_randomizer.style_analysis.analog_four_patch_inference import (
        AnalogFourPatchAudioFeatures,
        analog_four_audio_patch_genome_to_dict,
        analog_four_patch_audio_features_to_dict,
        analyze_analog_four_patch_audio,
    )

    features = _features()
    with pytest.raises(dataclasses.FrozenInstanceError):
        features.noise = 0.5  # type: ignore[misc]
    with pytest.raises(ValueError, match="64-character hexadecimal"):
        _features(audio_sha256="not-a-digest")
    with pytest.raises(ValueError, match="64-character hexadecimal"):
        _features(audio_sha256="z" * 64)
    with pytest.raises(ValueError, match="normalized"):
        _features(modulation=1.01)
    with pytest.raises(TypeError, match="path must be"):
        analyze_analog_four_patch_audio("sound.wav")  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="features must be"):
        analog_four_patch_audio_features_to_dict(object())  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="audio_genome must be"):
        analog_four_audio_patch_genome_to_dict(object())  # type: ignore[arg-type]
    assert isinstance(features, AnalogFourPatchAudioFeatures)


def test_audio_genome_is_stable_and_preserves_enum_targets(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from rytm_randomizer.style_analysis import analog_four_patch_inference as inference

    timestamps = iter(("2026-07-16T12:00:00Z", "2026-07-16T12:00:01Z"))
    monkeypatch.setattr(
        inference,
        "analyze_audio",
        lambda _path: _analysis(
            report=_reference_report(derived_at=next(timestamps)),
        ),
    )

    first = inference.build_analog_four_audio_patch_genome(Path("reference.wav"), track=2)
    second = inference.build_analog_four_audio_patch_genome(Path("reference.wav"), track=2)
    first_payload = inference.analog_four_audio_patch_genome_to_dict(first)
    second_payload = inference.analog_four_audio_patch_genome_to_dict(second)

    assert first_payload == second_payload
    assert first.feature_report.derived_at == "1970-01-01T00:00:00Z"
    assert first.genome.source_hash == "a" * 64
    assert first.genome.selected_track == 2
    assert [candidate.label for candidate in first.genome.candidates] == [
        "Closest reference",
        "Brighter sync",
        "Noisy texture",
        "Rounder bass",
    ]
    assert _gene(first.genome.candidates[0], "Filter2 Type").value.screen_value == "HP2"
    assert _gene(first.genome.candidates[0], "EnvA Env Shape").value.screen_value == ("triangle")
    assert _gene(first.genome.candidates[1], "Filter1 Frequency").value.midi_value > (
        _gene(first.genome.candidates[0], "Filter1 Frequency").value.midi_value
    )
    assert _gene(first.genome.candidates[2], "Noise Level").value.midi_value > 40
    assert _gene(first.genome.candidates[2], "LFO1 Depth A").value.midi_value > (
        _gene(first.genome.candidates[0], "LFO1 Depth A").value.midi_value
    )
    assert _gene(first.genome.candidates[3], "Filter1 Frequency").value.midi_value < (
        _gene(first.genome.candidates[0], "Filter1 Frequency").value.midi_value
    )
    assert json.dumps(first_payload, sort_keys=True) == json.dumps(
        second_payload,
        sort_keys=True,
    )


def test_different_audio_profiles_produce_different_clamped_candidate_dna(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from rytm_randomizer.style_analysis import analog_four_patch_inference as inference

    profiles = iter(
        (
            _features(
                audio_sha256="1" * 64,
                brightness=0.08,
                noise=0.03,
                low_end=0.92,
                harmonicity=0.94,
                transient=0.12,
                modulation=0.04,
            ),
            _features(
                audio_sha256="2" * 64,
                attack=1.0,
                decay=1.0,
                sustain=1.0,
                tail=1.0,
                brightness=1.0,
                spectral_flatness=1.0,
                noise=1.0,
                low_end=0.0,
                harmonicity=0.0,
                transient=1.0,
                modulation=1.0,
            ),
        )
    )
    monkeypatch.setattr(
        inference, "analyze_audio", lambda _path: _analysis(features=next(profiles))
    )

    dark = inference.build_analog_four_audio_patch_genome(Path("dark.wav"))
    bright = inference.build_analog_four_audio_patch_genome(Path("bright.wav"))

    assert _candidate_dna(dark) != _candidate_dna(bright)
    assert dark.genome.source_hash != bright.genome.source_hash
    for candidate in bright.genome.candidates:
        for gene in candidate.genes:
            if gene.value.midi_value is not None:
                assert 0 <= gene.value.midi_value <= 127


def test_candidate_count_and_numeric_helpers_cover_bounds(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from rytm_randomizer.style_analysis import analog_four_patch_inference as inference

    monkeypatch.setattr(inference, "analyze_audio", lambda _path: _analysis())

    result = inference.build_analog_four_audio_patch_genome(
        Path("two-columns.wav"),
        candidate_count=2,
    )

    assert result.genome.candidate_count == 2
    assert inference._unipolar(-1.0) == 0
    assert inference._unipolar(200.0) == 127
    assert inference._bipolar(-100.0) == -64
    assert inference._bipolar(100.0) == 63
    assert inference._clamp_audio_feature_unit(-1.0) == 0.0
    assert inference._clamp_audio_feature_unit(2.0) == 1.0
    with pytest.raises(ValueError, match="candidate column must be"):
        inference._candidate_character(_features(), 5)

    templates = inference.ANALOG_FOUR_PATCH_CANDIDATE_TEMPLATES
    monkeypatch.setattr(
        inference,
        "ANALOG_FOUR_PATCH_CANDIDATE_TEMPLATES",
        (dataclasses.replace(templates[0], column=2), *templates[1:]),
    )
    with pytest.raises(ValueError, match="contiguous and one-based"):
        inference._candidate_character(_features(), 1)
