"""Bounded post-failure observations, never a required-test replacement.

Run only after required macOS pytest has failed:
    python scripts/diagnose_native_audio_cache.py --output <new-absolute-directory>
Upload only <output>/public-report. An existing diagnostic can be copied with
--export-public-report <output> when that separate public directory is absent.

Four ordered phases each launch two children, without retries. Warm means
reuse of the cold phase's directory, not proof that compilation succeeded.
Only children import scientific/audio packages. Each generates the exact
test_style_analysis sine fixture; no user audio, MIDI, USB or audio network
source is accepted. analyze_audio's temporary copy is confined via TMPDIR.

Child env overrides are NUMBA_DEBUG_CACHE=1, NUMBA_CACHE_DIR (owned cache),
native thread counts=1, temporary directories (owned), and MIDI backend=off.
PYTHONPATH selects this checkout; bytecode writes are disabled and stdout is
unbuffered so cache events survive a crash. The return-event observer changes
timing; these samples cannot establish cause, a fix, or acceptance.
Inherited LIBROSA_CACHE_DIR is cleared to disable that optional disk cache.
No JIT-disable, CPU-target or threading-backend override is introduced.
Raw stdout/stderr, environment values and crash-report text are not published.
Only approved_artifact_paths are public; caches, temporary copies, input.wav
and unrecognized files beneath the output root are not upload-approved.
If publication fails with survivors, stderr carries a flushed categorical
supervisor handoff with at most two numeric PIDs; cleanup failure exits 3.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import io
import json
import math
import os
import re
import shutil
import stat
import subprocess
import sys
import threading
import time
import wave
from collections.abc import Callable, Mapping, Sequence
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path
from types import FrameType
from typing import IO, Final, NotRequired, Protocol, TypedDict, cast

from rytm_randomizer.cockpit.export.writer import atomic_write

_PHASES: Final[tuple[str, ...]] = (
    "shared_cache_cold",
    "shared_cache_warm",
    "isolated_per_child_cache_cold",
    "isolated_per_child_cache_warm",
)
_THREAD_VARS: Final[tuple[str, ...]] = (
    "NUMBA_NUM_THREADS",
    "OMP_NUM_THREADS",
    "OPENBLAS_NUM_THREADS",
    "MKL_NUM_THREADS",
    "VECLIB_MAXIMUM_THREADS",
    "BLIS_NUM_THREADS",
    "NUMEXPR_NUM_THREADS",
)
_PACKAGES: Final[tuple[str, ...]] = (
    "librosa",
    "numba",
    "llvmlite",
    "numpy",
    "scipy",
    "soundfile",
    "soxr",
)
_CAPTURE_LIMIT: Final[int] = 65_536
_JSON_LIMIT: Final[int] = 262_144
_REAP_SECONDS: Final[float] = 5.0
_CACHE_EVENT: Final[re.Pattern[str]] = re.compile(
    r"^\[cache\] (index|data) (loaded|saved) (?:from|to) "
)
_SAFE_VERSION: Final[re.Pattern[str]] = re.compile(r"^[0-9][0-9A-Za-z.+_-]{0,63}$")
PUBLIC_REPORT_SUBDIR: Final[str] = "public-report"
PUBLIC_ROOT_ARTIFACTS: Final[tuple[str, ...]] = ("diagnostic-marker.json", "manifest.json")
PUBLIC_CHILD_ARTIFACTS: Final[tuple[str, ...]] = (
    "bootstrap.json",
    "input.json",
    "observation.json",
    "child.json",
    "analyze_audio_snapshot-started.json",
    "analyze_audio_snapshot.json",
    "analyze_audio-started.json",
    "analyze_audio.json",
    *(f"onset-{number}.json" for number in range(1, 9)),
)


class CacheDebugEvent(TypedDict):
    kind: str
    action: str
    path: str
    function: str


class StreamCapturePayload(TypedDict):
    byte_count: int
    truncated: bool
    read_error: bool
    cache_debug_events: list[CacheDebugEvent]
    cache_debug_event_count_in_prefix: int
    events_truncated: bool
    other_text: str


class CacheCounts(TypedDict):
    files: int
    index_files: int
    data_files: int
    bounded: bool


class InputIdentity(TypedDict):
    status: str
    sha256: str | None
    byte_count: NotRequired[int]


class ChildResult(TypedDict):
    status: str
    onset_array_count: int
    error_category: NotRequired[str]
    stage: NotRequired[str]


class AudioObservation(TypedDict):
    phase: str
    child: int
    pid: int | None
    status: str
    returncode: int | None
    signal: int | None
    timed_out: bool
    cleanup: str
    elapsed_seconds: float
    cache_before: CacheCounts
    cache_after: CacheCounts
    input: InputIdentity
    stdout: StreamCapturePayload
    stderr: StreamCapturePayload
    child_result: ChildResult | None
    artifact_directory: str


class MacCrashReport(TypedDict):
    format: str
    pid: int
    exception: str
    byte_count: int


class MacCrashMetadata(TypedDict):
    status: str
    reports: list[MacCrashReport]
    scanned_count: NotRequired[int]
    read_count: NotRequired[int]
    bounded: NotRequired[bool]


class WaveInput(TypedDict):
    frequency_hz: int
    sample_rate_hz: int
    duration_seconds: int
    channels: int
    generator: str


class FinalProcessCleanup(TypedDict):
    status: str
    attempted_children: int
    unreaped_pids: list[int]
    kill_error_count: int
    wait_error_count: int


class SupervisorHandoff(TypedDict):
    diagnostic_only: bool
    error_category: str
    unreaped_pids: list[int]


class DiagnosticPublicationError(RuntimeError):
    """Publication failed after cleanup; retain only typed supervisor evidence."""

    def __init__(self, cleanup: FinalProcessCleanup) -> None:
        super().__init__("diagnostic_publication_failed")
        self.cleanup: FinalProcessCleanup = cleanup


class DiagnosticManifest(TypedDict):
    """Fixed observational result; nested records retain their field types."""

    schema_version: int
    diagnostic_only: bool
    acceptance_established: bool
    causal_conclusion: str
    required_pytest_result: str
    phases: list[str]
    observation_count: int
    completion: str
    max_concurrent_children: int
    retries: int
    onset_collection: str
    observer_changes_timing: bool
    warm_cache_semantics: str
    input_identity: str
    input: WaveInput
    versions: dict[str, str]
    observations: list[AudioObservation]
    macos_crash_metadata: MacCrashMetadata
    approved_artifact_paths: list[str]
    final_process_cleanup: FinalProcessCleanup
    cleanup_complete: bool
    public_report_directory: str


class _Process(Protocol):
    pid: int
    returncode: int | None
    stdout: IO[bytes] | None
    stderr: IO[bytes] | None

    def wait(self, timeout: float) -> int: ...

    def kill(self) -> None: ...


class _Array(Protocol):
    def tolist(self) -> object: ...


@dataclass(frozen=True)
class _Job:
    phase: str
    child: int
    directory: Path
    cache: Path
    cache_before: CacheCounts


@dataclass
class _Capture:
    prefix: bytearray = field(default_factory=bytearray)
    byte_count: int = 0
    failed: bool = False

    def drain(self, stream: IO[bytes]) -> None:
        try:
            while chunk := stream.read(4096):
                self.byte_count += len(chunk)
                self.prefix.extend(chunk[: max(0, _CAPTURE_LIMIT - len(self.prefix))])
        except (OSError, ValueError):
            self.failed = True
        finally:
            stream.close()

    def payload(self) -> StreamCapturePayload:
        events: list[CacheDebugEvent] = []
        event_count = 0
        for line in self.prefix.decode("utf-8", errors="replace").splitlines():
            match = _CACHE_EVENT.match(line)
            if match:
                event_count += 1
                if len(events) < 64:
                    events.append(
                        {
                            "kind": match[1],
                            "action": match[2],
                            "path": "<redacted>",
                            "function": "peak_pick" if "peak_pick" in line else "other",
                        }
                    )
        return {
            "byte_count": self.byte_count,
            "truncated": self.byte_count > _CAPTURE_LIMIT,
            "read_error": self.failed,
            "cache_debug_events": events,
            "cache_debug_event_count_in_prefix": event_count,
            "events_truncated": event_count > 64,
            "other_text": "<redacted>",
        }


def _publish(path: Path, payload: Mapping[str, object]) -> None:
    """Publish complete JSON atomically and refuse any preexisting destination."""
    encoded = (json.dumps(payload, sort_keys=True, allow_nan=False) + "\n").encode("utf-8")
    if len(encoded) > _JSON_LIMIT:
        raise ValueError("diagnostic JSON exceeds bound")
    atomic_write(path, encoded, overwrite=False)


def _read_json(path: Path) -> dict[str, object] | None:
    try:
        if not stat.S_ISREG(path.lstat().st_mode) or path.stat().st_size > _JSON_LIMIT:
            return None
        with path.open("rb") as handle:
            raw = handle.read(_JSON_LIMIT + 1)
        value: object = json.loads(raw)
        if isinstance(value, dict):
            return cast(dict[str, object], value)
    except (OSError, ValueError, RecursionError):
        return None
    return None


def _versions() -> dict[str, str]:
    versions: dict[str, str] = {"python": sys.version.split()[0]}
    for name in _PACKAGES:
        try:
            version = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            versions[name] = "missing"
            continue
        versions[name] = version if _SAFE_VERSION.fullmatch(version) else "unavailable"
    return versions


def _child_environment(job: _Job) -> dict[str, str]:
    environment = dict(os.environ)
    environment.pop("LIBROSA_CACHE_DIR", None)
    environment.update(dict.fromkeys(_THREAD_VARS, "1"))
    environment.update(
        NUMBA_DEBUG_CACHE="1",
        NUMBA_CACHE_DIR=str(job.cache),
        TMPDIR=str(job.directory / "tmp"),
        TMP=str(job.directory / "tmp"),
        TEMP=str(job.directory / "tmp"),
        RYTM_RAND_MIDI_BACKEND="off",
        PYTHONDONTWRITEBYTECODE="1",
        PYTHONUNBUFFERED="1",
        PYTHONPATH=os.pathsep.join(
            filter(None, (str(Path(__file__).resolve().parents[1]), environment.get("PYTHONPATH")))
        ),
    )
    return environment


def _cache_counts(cache: Path) -> CacheCounts:
    counts: CacheCounts = {"files": 0, "index_files": 0, "data_files": 0, "bounded": False}
    seen = 0
    for _root, directories, files in os.walk(cache, followlinks=False):
        seen += len(files) + len(directories)
        if seen > 512:
            counts["bounded"] = True
            break
        counts["files"] += len(files)
        counts["index_files"] += sum(name.endswith(".nbi") for name in files)
        counts["data_files"] += sum(name.endswith(".nbc") for name in files)
    return counts


def _input_identity(directory: Path) -> InputIdentity:
    path = directory / "input.wav"
    try:
        if not stat.S_ISREG(path.lstat().st_mode) or path.stat().st_size != 88_244:
            return {"status": "invalid_or_missing", "sha256": None}
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        claimed = _read_json(directory / "input.json")
        return {
            "status": "verified" if claimed and claimed.get("sha256") == digest else "unclaimed",
            "sha256": digest,
            "byte_count": 88_244,
        }
    except OSError:
        return {"status": "invalid_or_missing", "sha256": None}


def _run_one(
    job: _Job,
    timeout: float,
    spawn: Callable[..., _Process],
    owned_processes: list[_Process],
) -> AudioObservation:
    started = time.monotonic()
    process: _Process | None = None
    captures = (_Capture(), _Capture())
    readers: list[threading.Thread] = []
    status = "completed"
    cleanup = "complete"
    try:
        process = spawn(
            [sys.executable, str(Path(__file__).resolve()), "--child", str(job.directory)],
            cwd=job.directory,
            env=_child_environment(job),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        owned_processes.append(process)
        for stream, capture in zip((process.stdout, process.stderr), captures):
            if stream is not None:
                reader = threading.Thread(target=capture.drain, args=(stream,), daemon=True)
                reader.start()
                readers.append(reader)
        try:
            code = process.wait(timeout=timeout)
            if code != 0:
                status = "child_failed"
        except subprocess.TimeoutExpired:
            status = "timed_out"
    except Exception:
        status = "process_error"
    finally:
        if process is not None and process.returncode is None:
            try:
                process.kill()
                process.wait(timeout=_REAP_SECONDS)
            except Exception:
                cleanup = "reap_failed"
        for reader in readers:
            reader.join(timeout=1.0)
            if reader.is_alive():
                cleanup = "stream_cleanup_incomplete"
    code = process.returncode if process else None
    termination_signal = -code if code is not None and code < 0 and os.name != "nt" else None
    return {
        "phase": job.phase,
        "child": job.child,
        "pid": process.pid if process else None,
        "status": status,
        "returncode": code,
        "signal": termination_signal,
        "timed_out": status == "timed_out",
        "cleanup": cleanup,
        "elapsed_seconds": round(time.monotonic() - started, 3),
        "cache_before": job.cache_before.copy(),
        "cache_after": _cache_counts(job.cache),
        "input": _input_identity(job.directory),
        "stdout": captures[0].payload(),
        "stderr": captures[1].payload(),
        "child_result": cast(ChildResult | None, _read_json(job.directory / "child.json")),
        "artifact_directory": f"{job.phase}/child-{job.child}",
    }


def _final_process_cleanup(owned_processes: Sequence[_Process]) -> FinalProcessCleanup:
    """Keep failed-reap handles owned through one final bounded cleanup pass."""
    attempted = 0
    kill_errors = wait_errors = 0
    for process in owned_processes:
        if process.returncode is not None:
            continue
        attempted += 1
        try:
            process.kill()
        except Exception:
            kill_errors += 1
        try:
            process.wait(timeout=_REAP_SECONDS)
        except Exception:
            wait_errors += 1
    unreaped = [process.pid for process in owned_processes if process.returncode is None]
    return {
        "status": "incomplete" if unreaped else "complete",
        "attempted_children": attempted,
        "unreaped_pids": unreaped,
        "kill_error_count": kill_errors,
        "wait_error_count": wait_errors,
    }


def approved_artifact_paths() -> tuple[str, ...]:
    """Return fixed upload-eligible relative paths, including possibly absent JSON."""
    return PUBLIC_ROOT_ARTIFACTS + tuple(
        f"{phase}/child-{child}/{name}"
        for phase in _PHASES
        for child in (1, 2)
        for name in PUBLIC_CHILD_ARTIFACTS
    )


def export_public_report(output: Path) -> Path:
    """Copy exact approved JSON into a new directory; never copy source residue."""
    root = output.resolve(strict=True)
    marker = _read_json(root / "diagnostic-marker.json")
    if marker is None or marker.get("diagnostic_only") is not True:
        raise ValueError("diagnostic marker required for public export")
    public = root / PUBLIC_REPORT_SUBDIR
    public.mkdir(mode=0o700, exist_ok=False)
    for relative in approved_artifact_paths():
        source = root / relative
        try:
            metadata = source.lstat()
        except FileNotFoundError:
            continue
        if (
            not stat.S_ISREG(metadata.st_mode)
            or source.resolve(strict=True) != source
            or _read_json(source) is None
        ):
            raise ValueError("approved diagnostic JSON is invalid")
        destination = public / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        # Source publications are immutable; the destination tree is newly owned.
        shutil.copyfile(source, destination)
    return public


def _crash_metadata(pids: set[int], since: float) -> MacCrashMetadata:
    """Parent-only, bounded macOS report scan; export categories/counts, never text."""
    if sys.platform != "darwin":
        return {"status": "not_macos", "reports": []}
    reports: list[MacCrashReport] = []
    scanned = read_count = 0
    bounded = unavailable = False
    for directory in (
        Path.home() / "Library/Logs/DiagnosticReports",
        Path("/Library/Logs/DiagnosticReports"),
    ):
        try:
            with os.scandir(directory) as entries:
                for entry in entries:
                    scanned += 1
                    if scanned > 128 or read_count >= 8:
                        bounded = True
                        break
                    if not entry.name.lower().startswith("python") or not entry.name.endswith(
                        (".ips", ".crash")
                    ):
                        continue
                    if not entry.is_file(follow_symlinks=False):
                        continue
                    info = entry.stat(follow_symlinks=False)
                    if info.st_mtime < since or info.st_size > _JSON_LIMIT:
                        continue
                    read_count += 1
                    with open(entry.path, "rb") as handle:
                        raw = handle.read(_JSON_LIMIT + 1)
                    if len(raw) > _JSON_LIMIT:
                        continue
                    if entry.name.endswith(".ips"):
                        text = raw.decode("utf-8")
                        decoder = json.JSONDecoder()
                        first, end = decoder.raw_decode(text)
                        body: object = (
                            decoder.raw_decode(text[end:].lstrip())[0]
                            if text[end:].strip()
                            else first
                        )
                        if not isinstance(body, dict) or body.get("pid") not in pids:
                            continue
                        exception = body.get("exception")
                        is_segv = (
                            isinstance(exception, dict)
                            and exception.get("type") == "EXC_BAD_ACCESS"
                        )
                        reports.append(
                            {
                                "format": "ips",
                                "pid": cast(int, body["pid"]),
                                "exception": "bad_access" if is_segv else "other",
                                "byte_count": len(raw),
                            }
                        )
                    else:
                        text = raw.decode("utf-8", errors="replace")
                        match = re.search(r"^Process:.*\[(\d+)\]\s*$", text, re.MULTILINE)
                        if match and int(match[1]) in pids:
                            reports.append(
                                {
                                    "format": "crash",
                                    "pid": int(match[1]),
                                    "exception": (
                                        "bad_access" if "EXC_BAD_ACCESS" in text else "other"
                                    ),
                                    "byte_count": len(raw),
                                }
                            )
        except (OSError, ValueError, RecursionError):
            unavailable = True
    return {
        "status": "matched" if reports else "unavailable" if unavailable else "not_found",
        "reports": reports,
        "scanned_count": min(scanned, 128),
        "read_count": read_count,
        "bounded": bounded,
    }


def _spawn_process(
    command: list[str],
    *,
    cwd: Path,
    env: Mapping[str, str],
    stdin: int,
    stdout: int,
    stderr: int,
) -> _Process:
    return subprocess.Popen(command, cwd=cwd, env=env, stdin=stdin, stdout=stdout, stderr=stderr)


def run_diagnostic(
    output: Path,
    *,
    timeout: float = 60.0,
    spawn: Callable[..., _Process] = _spawn_process,
) -> DiagnosticManifest:
    """Publish eight observations; child failure is evidence, not acceptance."""
    if not output.is_absolute() or not math.isfinite(timeout) or not 0.1 <= timeout <= 180.0:
        raise ValueError("absolute new output and bounded timeout required")
    output.mkdir(mode=0o700, parents=False, exist_ok=False)
    output = output.resolve()
    started = time.time()
    shared = output / "caches" / "shared"
    isolated = tuple(output / "caches" / f"isolated-{child}" for child in (1, 2))
    for cache in (shared, *isolated):
        cache.mkdir(parents=True, exist_ok=False)
    _publish(
        output / "diagnostic-marker.json",
        {
            "diagnostic_only": True,
            "acceptance_established": False,
            "causal_conclusion": "not_established",
            "required_pytest_result": "not_modified",
            "planned_observations": 8,
            "max_concurrent_children": 2,
            "retries": 0,
        },
    )
    observations: list[AudioObservation] = []
    owned_processes: list[_Process] = []
    publication_failed = False
    try:
        with ThreadPoolExecutor(max_workers=2) as executor:
            for index, phase in enumerate(_PHASES):
                jobs = []
                for child in (1, 2):
                    directory = output / phase / f"child-{child}"
                    (directory / "tmp").mkdir(parents=True, exist_ok=False)
                    cache = shared if index < 2 else isolated[child - 1]
                    jobs.append(_Job(phase, child, directory, cache, _cache_counts(cache)))
                futures = [
                    executor.submit(_run_one, job, timeout, spawn, owned_processes) for job in jobs
                ]
                results = [future.result() for future in futures]
                for job, result in zip(jobs, results):
                    _publish(job.directory / "observation.json", result)
                    observations.append(result)
                if any(result["cleanup"] != "complete" for result in results):
                    # Never start another pair while a previous child may still exist.
                    break
    except Exception:
        publication_failed = True
    finally:
        final_cleanup = _final_process_cleanup(owned_processes)
    if publication_failed:
        raise DiagnosticPublicationError(final_cleanup) from None
    identities = [result["input"]["sha256"] for result in observations]
    present = [value for value in identities if value is not None]
    pids = {pid for result in observations if (pid := result["pid"]) is not None}
    manifest: DiagnosticManifest = {
        "schema_version": 1,
        "diagnostic_only": True,
        "acceptance_established": False,
        "causal_conclusion": "not_established",
        "required_pytest_result": "not_modified",
        "phases": list(_PHASES),
        "observation_count": len(observations),
        "completion": "observed" if len(observations) == 8 else "aborted_cleanup",
        "max_concurrent_children": 2,
        "retries": 0,
        "onset_collection": "python_return_event_observer",
        "observer_changes_timing": True,
        "warm_cache_semantics": "directory_reused_not_proven_compiled",
        "input_identity": (
            "identical"
            if len(present) == 8 and len(set(present)) == 1
            else "mismatch" if len(set(present)) > 1 else "incomplete"
        ),
        "input": {
            "frequency_hz": 440,
            "sample_rate_hz": 22050,
            "duration_seconds": 2,
            "channels": 1,
            "generator": "test_style_analysis_float32_sine_pcm16",
        },
        "versions": _versions(),
        "observations": observations,
        "macos_crash_metadata": _crash_metadata(pids, started),
        "approved_artifact_paths": list(approved_artifact_paths()),
        "final_process_cleanup": final_cleanup,
        "cleanup_complete": final_cleanup["status"] == "complete"
        and not any(result["cleanup"] == "stream_cleanup_incomplete" for result in observations),
        "public_report_directory": PUBLIC_REPORT_SUBDIR,
    }
    try:
        _publish(output / "manifest.json", manifest)
        export_public_report(output)
    except Exception:
        publication_failed = True
    if publication_failed:
        raise DiagnosticPublicationError(final_cleanup) from None
    return manifest


def _write_test_wave(directory: Path) -> Path:
    import numpy as np

    # These operations intentionally match tests/test_style_analysis.py exactly.
    t = np.arange(0, int(22050 * 2.0)) / float(22050)
    samples = (0.5 * np.sin(2.0 * np.pi * 440.0 * t)).astype(np.float32)
    pcm = (samples * 32767.0).astype(np.int16)
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(22050)
        handle.writeframes(pcm.tobytes())
    data = buffer.getvalue()
    path = directory / "input.wav"
    with path.open("xb") as handle:
        handle.write(data)
    _publish(
        directory / "input.json",
        {"sha256": hashlib.sha256(data).hexdigest(), "byte_count": len(data)},
    )
    return path


def _error_category(error: Exception) -> str:
    if isinstance(error, ImportError):
        return "dependency_error"
    if isinstance(error, OSError):
        return "io_error"
    if isinstance(error, (ValueError, TypeError)):
        return "data_error"
    return "analysis_error"


def _child(directory: Path) -> int:
    directory = directory.resolve(strict=True)
    cache = Path(os.environ["NUMBA_CACHE_DIR"]).resolve(strict=True)
    root = directory.parent.parent
    if not (root / "diagnostic-marker.json").is_file() or not cache.is_relative_to(root / "caches"):
        return 2
    active_api = "bootstrap"
    onset_count = 0

    def observe(frame: FrameType, event: str, value: object) -> None:
        nonlocal onset_count
        if event != "return" or frame.f_globals.get("__name__") != "librosa.onset":
            return
        name = frame.f_code.co_name
        if name not in ("onset_strength", "onset_detect") or value is None or onset_count >= 8:
            return
        onset_count += 1
        _publish(
            directory / f"onset-{onset_count}.json",
            {"api": active_api, "function": name, "values": cast(_Array, value).tolist()},
        )

    try:
        _publish(
            directory / "bootstrap.json",
            {"versions": _versions(), "thread_limit": 1, "numba_debug_cache": True},
        )
        path = _write_test_wave(directory)
        from rytm_randomizer.style_analysis.extractor import (
            analyze_audio,
            analyze_audio_snapshot,
            audio_dna_evidence_to_dict,
            audio_synthesis_features_to_dict,
        )
        from rytm_randomizer.style_analysis.feature_report import feature_report_to_dict

        # Profile observes actual public onset returns, without monkeypatching code.
        sys.setprofile(observe)
        for active_api, analyze in (
            ("analyze_audio_snapshot", analyze_audio_snapshot),
            ("analyze_audio", analyze_audio),
        ):
            _publish(directory / f"{active_api}-started.json", {"stage": active_api})
            analysis = analyze(path)
            _publish(
                directory / f"{active_api}.json",
                {
                    "feature_report": dict(feature_report_to_dict(analysis.feature_report)),
                    "synthesis_features": dict(
                        audio_synthesis_features_to_dict(analysis.synthesis_features)
                    ),
                    "dna_evidence": dict(audio_dna_evidence_to_dict(analysis.dna_evidence)),
                },
            )
        sys.setprofile(None)
        _publish(
            directory / "child.json", {"status": "completed", "onset_array_count": onset_count}
        )
        return 0
    except Exception as error:
        sys.setprofile(None)
        _publish(
            directory / "child.json",
            {
                "status": "failed",
                "error_category": _error_category(error),
                "stage": active_api,
                "onset_array_count": onset_count,
            },
        )
        return 1
    finally:
        sys.setprofile(None)


def _emit_supervisor_handoff(cleanup: FinalProcessCleanup) -> None:
    payload: SupervisorHandoff = {
        "diagnostic_only": True,
        "error_category": "diagnostic_cleanup_incomplete",
        "unreaped_pids": cleanup["unreaped_pids"][:2],
    }
    print(json.dumps(payload, sort_keys=True), file=sys.stderr, flush=True)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--output", type=Path)
    group.add_argument("--child", type=Path, help=argparse.SUPPRESS)
    group.add_argument("--export-public-report", type=Path)
    parser.add_argument("--timeout-seconds", type=float, default=60.0)
    args = parser.parse_args(argv)
    try:
        if args.child is not None:
            return _child(args.child)
        if args.export_public_report is not None:
            export_public_report(args.export_public_report)
            return 0
        manifest = run_diagnostic(args.output, timeout=args.timeout_seconds)
        if not manifest["cleanup_complete"]:
            _emit_supervisor_handoff(manifest["final_process_cleanup"])
            return 3
    except DiagnosticPublicationError as failure:
        if failure.cleanup["status"] != "complete":
            _emit_supervisor_handoff(failure.cleanup)
            return 3
        print(
            '{"diagnostic_only":true,"error_category":"diagnostic_publication_failed"}',
            file=sys.stderr,
            flush=True,
        )
        return 2
    except Exception:
        # No paths, exception messages, environment or traceback on the wire.
        print(
            '{"diagnostic_only":true,"error_category":"diagnostic_publication_failed"}',
            file=sys.stderr,
        )
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
