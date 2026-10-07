"""Diagnostic lifecycle tests use fake children, never scientific imports."""

from __future__ import annotations

import ast
import hashlib
import importlib.util
import io
import json
import os
import subprocess
import sys
import threading
from pathlib import Path
from types import FunctionType, ModuleType, SimpleNamespace
from typing import Final

import pytest

pytestmark = pytest.mark.fast
_SCRIPT: Final[Path] = (
    Path(__file__).resolve().parents[1] / "scripts/diagnose_native_audio_cache.py"
)
_SCI_PACKAGES: Final[tuple[str, ...]] = ("librosa", "numpy", "numba", "llvmlite", "scipy")
_SCI_IMPORTS_BEFORE: Final[frozenset[str]] = frozenset(sys.modules).intersection(_SCI_PACKAGES)
_SPEC = importlib.util.spec_from_file_location("diagnose_native_audio_cache", _SCRIPT)
assert _SPEC is not None and _SPEC.loader is not None
diagnostic = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = diagnostic
_SPEC.loader.exec_module(diagnostic)
_SCI_IMPORTS_FROM_SCRIPT: Final[frozenset[str]] = (
    frozenset(sys.modules).intersection(_SCI_PACKAGES) - _SCI_IMPORTS_BEFORE
)


class _FakeProcess:
    def __init__(self, owner: _FakeSpawn, number: int, directory: Path, cache: Path) -> None:
        self.owner = owner
        self.number = number
        self.pid = 1000 + number
        self.returncode: int | None = None
        self.stdout = io.BytesIO(
            b"[cache] index loaded from '/private/SECRET/cache.nbi'\nTOKEN=SECRET\n"
        )
        self.stderr = io.BytesIO(b"/private/SECRET/error\n")
        self.killed = False
        with (directory / "input.wav").open("xb") as handle:
            handle.write(owner.audio if number != owner.mismatch else b"x" * 88_244)
        digest = hashlib.sha256((directory / "input.wav").read_bytes()).hexdigest()
        diagnostic._publish(directory / "input.json", {"sha256": digest})
        (cache / f"child-{number}.nbi").touch(exist_ok=False)
        if number not in (owner.failure, owner.timeout):
            diagnostic._publish(
                directory / "child.json", {"status": "completed", "onset_array_count": 0}
            )

    def wait(self, timeout: float) -> int:
        if self.number == self.owner.timeout and not self.killed:
            raise subprocess.TimeoutExpired("SECRET", timeout)
        if not self.killed:
            phase = (self.number - 1) // 2
            self.owner.barriers[phase].wait(timeout=2)
        if self.returncode is None:
            self.returncode = -9 if self.killed else -11 if self.number == self.owner.failure else 0
            with self.owner.lock:
                self.owner.active -= 1
        return self.returncode

    def kill(self) -> None:
        self.killed = True


class _FakeSpawn:
    def __init__(self, *, failure: int = 0, timeout: int = 0, mismatch: int = 0) -> None:
        self.failure = failure
        self.timeout = timeout
        self.mismatch = mismatch
        self.audio = bytes(88_244)
        self.lock = threading.Lock()
        self.active = 0
        self.maximum = 0
        self.calls: list[tuple[list[str], Path, dict[str, str]]] = []
        self.barriers = [threading.Barrier(2) for _ in range(4)]

    def __call__(
        self,
        command: list[str],
        *,
        cwd: Path,
        env: dict[str, str],
        stdin: int,
        stdout: int,
        stderr: int,
    ) -> _FakeProcess:
        assert stdin == subprocess.DEVNULL
        assert stdout == stderr == subprocess.PIPE
        with self.lock:
            self.calls.append((command, cwd, env))
            number = diagnostic._PHASES.index(cwd.parent.name) * 2 + int(cwd.name[-1])
            self.active += 1
            self.maximum = max(self.maximum, self.active)
        return _FakeProcess(self, number, cwd, Path(env["NUMBA_CACHE_DIR"]))


def test_four_fixed_phases_reuse_only_owned_caches_and_publish_identical_inputs(
    tmp_path: Path,
) -> None:
    fake = _FakeSpawn()
    output = tmp_path / "new-diagnostic"
    result = diagnostic.run_diagnostic(output, spawn=fake)
    assert fake.maximum == 2 and fake.active == 0
    assert len(fake.calls) == result["observation_count"] == 8
    assert result["input_identity"] == "identical"
    assert result["diagnostic_only"] is True
    assert result["acceptance_established"] is False
    assert result["causal_conclusion"] == "not_established"
    assert result["required_pytest_result"] == "not_modified"
    assert result["retries"] == 0
    caches = [env["NUMBA_CACHE_DIR"] for _, _, env in fake.calls]
    assert len(set(caches[:4])) == 1
    assert set(caches[4:6]) == set(caches[6:8])
    assert len(set(caches[4:])) == 2
    assert set(caches[:4]).isdisjoint(caches[4:])
    for command, directory, env in fake.calls:
        assert command[-2:] == ["--child", str(directory)]
        assert directory.is_relative_to(output)
        assert Path(env["NUMBA_CACHE_DIR"]).is_relative_to(output)
        assert env["NUMBA_DEBUG_CACHE"] == "1"
        assert all(env[key] == "1" for key in diagnostic._THREAD_VARS)
        assert env["RYTM_RAND_MIDI_BACKEND"] == "off"
        assert env["TMP"] == env["TMPDIR"] == env["TEMP"] == str(directory / "tmp")
        assert (directory / "observation.json").is_file()
    assert [obs["phase"] for obs in result["observations"]] == [
        phase for phase in diagnostic._PHASES for _ in range(2)
    ]
    assert result["observations"][0]["cache_before"]["files"] == 0
    assert result["observations"][2]["cache_before"]["index_files"] == 2
    published = (output / "manifest.json").read_text()
    assert "SECRET" not in published and "/private/" not in published
    assert json.loads(published) == result
    assert result["public_report_directory"] == "public-report"
    public_manifest = output / "public-report/manifest.json"
    assert public_manifest.read_bytes() == (output / "manifest.json").read_bytes()


def test_failed_child_and_timeout_are_observations_without_retries(tmp_path: Path) -> None:
    fake = _FakeSpawn(failure=1, timeout=2)
    # The timed-out child must still meet its pair's deterministic barrier.
    fake.barriers[0] = threading.Barrier(1)
    result = diagnostic.run_diagnostic(tmp_path / "failures", timeout=0.1, spawn=fake)
    assert len(fake.calls) == 8 and fake.active == 0
    assert result["observations"][0]["status"] == "child_failed"
    assert result["observations"][0]["returncode"] == -11
    assert result["observations"][0]["signal"] == (11 if os.name != "nt" else None)
    assert result["observations"][1]["status"] == "timed_out"
    assert result["observations"][1]["timed_out"] is True
    assert result["observations"][1]["child_result"] is None
    assert result["acceptance_established"] is False


def test_manifest_whitelists_public_json_not_every_file_beneath_output(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    output = tmp_path / "private-artifacts"
    child = output / "shared_cache_cold/child-1"
    private_paths = (
        output / "unexpected.json",
        child / "unexpected.json",
        child / "onset-9.json",
        child / "analyze_audio-private.json",
        child / "observation.json.leaked.tmp",
        child / "tmp" / "private.json",
        output / "caches" / "shared" / "private.json",
    )
    export = diagnostic.export_public_report

    def inject_lookalikes(root: Path) -> Path:
        for path in private_paths:
            path.write_text('{"private":"SECRET"}')
        return export(root)

    monkeypatch.setattr(diagnostic, "export_public_report", inject_lookalikes)
    result = diagnostic.run_diagnostic(output, spawn=_FakeSpawn())
    approved = set(result["approved_artifact_paths"])
    assert approved == set(diagnostic.approved_artifact_paths())
    assert {"manifest.json", "diagnostic-marker.json"} <= approved
    assert all(Path(path).suffix == ".json" for path in approved)
    assert all(not {"tmp", "caches"}.intersection(Path(path).parts) for path in approved)
    assert all(path.relative_to(output).as_posix() not in approved for path in private_paths)
    assert (child / "input.wav").relative_to(output).as_posix() not in approved
    public = output / "public-report"
    uploaded = [path for path in public.rglob("*") if path.is_file()]
    assert {path.relative_to(public).as_posix() for path in uploaded} == {
        relative for relative in approved if (output / relative).is_file()
    }
    assert uploaded and all("SECRET" not in path.read_text() for path in uploaded)
    assert not (public / "caches").exists()
    assert not (public / "shared_cache_cold/child-1/tmp").exists()
    assert any(path.is_file() for path in (output / "caches").rglob("*.nbi"))


def test_inherited_librosa_cache_is_cleared_without_touching_external_sentinel(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    external_cache = tmp_path / "external-cache"
    external_cache.mkdir()
    sentinel = external_cache / "sentinel"
    sentinel.write_text("untouched")
    monkeypatch.setenv("LIBROSA_CACHE_DIR", str(external_cache))
    monkeypatch.setenv("NUMBA_DISABLE_JIT", "0")

    class CacheAwareSpawn(_FakeSpawn):
        def __call__(
            self,
            command: list[str],
            *,
            cwd: Path,
            env: dict[str, str],
            stdin: int,
            stdout: int,
            stderr: int,
        ) -> _FakeProcess:
            if env.get("LIBROSA_CACHE_DIR") == str(external_cache):
                sentinel.write_text("touched")
            return super().__call__(
                command, cwd=cwd, env=env, stdin=stdin, stdout=stdout, stderr=stderr
            )

    fake = CacheAwareSpawn()
    result = diagnostic.run_diagnostic(tmp_path / "owned-caches", spawn=fake)
    assert result["observation_count"] == 8
    assert all("LIBROSA_CACHE_DIR" not in env for _, _, env in fake.calls)
    assert all(env["NUMBA_DISABLE_JIT"] == "0" for _, _, env in fake.calls)
    assert os.environ["LIBROSA_CACHE_DIR"] == str(external_cache)
    assert sentinel.read_text() == "untouched"


def test_spawn_failure_is_contained_and_manifest_is_still_published(tmp_path: Path) -> None:
    calls = []

    def fail(*args: object, **kwargs: object) -> None:
        calls.append(1)
        raise OSError("SECRET")

    output = tmp_path / "spawn-errors"
    result = diagnostic.run_diagnostic(output, spawn=fail)
    assert len(calls) == 8
    assert all(obs["status"] == "process_error" for obs in result["observations"])
    assert result["input_identity"] == "incomplete"
    assert (output / "manifest.json").is_file()
    assert "SECRET" not in (output / "manifest.json").read_text()


def test_mismatched_input_is_not_reported_as_identical(tmp_path: Path) -> None:
    result = diagnostic.run_diagnostic(tmp_path / "mismatch", spawn=_FakeSpawn(mismatch=8))
    assert result["input_identity"] == "mismatch"


def test_existing_output_is_refused_without_touching_existing_content(tmp_path: Path) -> None:
    sentinel = tmp_path / "manifest.json"
    sentinel.write_text("existing")
    with pytest.raises(FileExistsError):
        diagnostic.run_diagnostic(tmp_path, spawn=_FakeSpawn())
    assert sentinel.read_text() == "existing"
    with pytest.raises(ValueError):
        diagnostic.run_diagnostic(Path("relative-output"))


def test_json_publication_reuses_atomic_writer_no_clobber_and_encoding_bound(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    atomic = diagnostic.atomic_write
    calls: list[tuple[Path, bytes, bool]] = []

    def spy(path: Path, data: bytes, *, overwrite: bool) -> object:
        calls.append((path, data, overwrite))
        return atomic(path, data, overwrite=overwrite)

    monkeypatch.setattr(diagnostic, "atomic_write", spy)
    target = tmp_path / "data.json"
    diagnostic._publish(target, {"first": True})
    with pytest.raises(FileExistsError):
        diagnostic._publish(target, {"second": True})
    assert json.loads(target.read_text()) == {"first": True}
    assert list(tmp_path.iterdir()) == [target]
    with pytest.raises(ValueError):
        diagnostic._publish(tmp_path / "huge.json", {"data": "x" * diagnostic._JSON_LIMIT})
    assert calls == [(target, b'{"first": true}\n', False), (target, b'{"second": true}\n', False)]


def test_json_publication_does_not_mask_the_shared_writer_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    original = OSError("SECRET original publication error")

    def fail(path: Path, data: bytes, *, overwrite: bool) -> None:
        raise original

    monkeypatch.setattr(diagnostic, "atomic_write", fail)
    with pytest.raises(OSError) as raised:
        diagnostic._publish(tmp_path / "report.json", {"diagnostic_only": True})
    assert raised.value is original
    assert list(tmp_path.iterdir()) == []


def test_public_report_export_command_uses_exact_allowlist_without_analysis(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path / "existing-diagnostic"
    child = root / "shared_cache_cold/child-1"
    child.mkdir(parents=True)
    diagnostic._publish(root / "diagnostic-marker.json", {"diagnostic_only": True})
    diagnostic._publish(child / "onset-1.json", {"values": [0.0, 1.0]})
    diagnostic._publish(child / "onset-9.json", {"private": "SECRET"})
    diagnostic._publish(child / "analyze_audio-private.json", {"private": "SECRET"})

    def forbid_analysis(*args: object, **kwargs: object) -> None:
        raise AssertionError("export must not run audio analysis")

    monkeypatch.setattr(diagnostic, "run_diagnostic", forbid_analysis)
    assert diagnostic.main(["--export-public-report", str(root)]) == 0
    public = root / "public-report"
    assert (public / "shared_cache_cold/child-1/onset-1.json").read_bytes() == (
        child / "onset-1.json"
    ).read_bytes()
    assert {
        path.relative_to(public).as_posix() for path in public.rglob("*") if path.is_file()
    } == {
        "diagnostic-marker.json",
        "shared_cache_cold/child-1/onset-1.json",
    }
    with pytest.raises(FileExistsError):
        diagnostic.export_public_report(root)


def test_stdout_capture_is_bounded_and_exports_only_redacted_cache_categories() -> None:
    capture = diagnostic._Capture()
    capture.drain(io.BytesIO(b"[cache] data saved to '/SECRET/path'\n" + b"x" * 200_000))
    result = capture.payload()
    assert len(capture.prefix) == diagnostic._CAPTURE_LIMIT
    assert result["truncated"] is True
    assert result["cache_debug_events"] == [
        {"kind": "data", "action": "saved", "path": "<redacted>", "function": "other"}
    ]
    assert "SECRET" not in json.dumps(result)


def test_cache_trace_event_count_is_bounded_without_losing_target_category() -> None:
    capture = diagnostic._Capture()
    capture.drain(io.BytesIO(b"[cache] data loaded from '/SECRET/utils.__peak_pick.nbc'\n" * 100))
    result = capture.payload()
    assert len(result["cache_debug_events"]) == 64
    assert result["cache_debug_event_count_in_prefix"] == 100
    assert result["events_truncated"] is True
    assert all(event["function"] == "peak_pick" for event in result["cache_debug_events"])
    assert "SECRET" not in json.dumps(result)


def test_cleanup_failure_stops_new_pairs_and_retains_handles_through_final_cleanup(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    class Unreaped:
        returncode = None
        stdout = None
        stderr = None

        def __init__(self, pid: int) -> None:
            self.pid = pid
            self.kill_calls = 0
            self.wait_timeouts: list[float] = []

        def wait(self, timeout: float) -> int:
            self.wait_timeouts.append(timeout)
            raise subprocess.TimeoutExpired("SECRET", timeout)

        def kill(self) -> None:
            self.kill_calls += 1
            raise OSError("SECRET")

    handles: list[Unreaped] = []
    spawn_lock = threading.Lock()

    def spawn(*args: object, **kwargs: object) -> Unreaped:
        with spawn_lock:
            process = Unreaped(1000 + len(handles))
            handles.append(process)
        return process

    output = tmp_path / "unreaped"
    result = diagnostic.run_diagnostic(output, spawn=spawn)
    assert len(handles) == result["observation_count"] == 2
    assert result["completion"] == "aborted_cleanup"
    assert result["input_identity"] == "incomplete"
    assert result["acceptance_established"] is False
    assert all(handle.kill_calls == 2 for handle in handles)
    assert all(handle.wait_timeouts == [60.0, diagnostic._REAP_SECONDS] for handle in handles)
    cleanup = result["final_process_cleanup"]
    assert cleanup["status"] == "incomplete"
    assert cleanup["attempted_children"] == 2
    assert set(cleanup["unreaped_pids"]) == {handle.pid for handle in handles}
    assert cleanup["kill_error_count"] == cleanup["wait_error_count"] == 2
    assert result["cleanup_complete"] is False
    assert (output / "manifest.json").is_file()
    monkeypatch.setattr(diagnostic, "run_diagnostic", lambda path, timeout: result)
    assert diagnostic.main(["--output", str(output)]) == 3
    handoff = json.loads(capsys.readouterr().err)
    assert set(handoff) == {"diagnostic_only", "error_category", "unreaped_pids"}
    assert handoff["diagnostic_only"] is True
    assert handoff["error_category"] == "diagnostic_cleanup_incomplete"
    assert set(handoff["unreaped_pids"]) == {handle.pid for handle in handles}


@pytest.mark.parametrize("failed_artifact", ["observation.json", "manifest.json", "public-report"])
def test_publication_failure_retains_survivor_evidence_and_stderr_supervisor_handoff(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    failed_artifact: str,
) -> None:
    class Survivor:
        returncode = None
        stdout = None
        stderr = None

        def __init__(self, pid: int) -> None:
            self.pid = pid
            self.kill_calls = 0
            self.wait_timeouts: list[float] = []

        def wait(self, timeout: float) -> int:
            self.wait_timeouts.append(timeout)
            raise subprocess.TimeoutExpired("SECRET /private/env", timeout)

        def kill(self) -> None:
            self.kill_calls += 1
            raise OSError("SECRET /private/env")

    handles: list[Survivor] = []
    spawn_lock = threading.Lock()

    def spawn(*args: object, **kwargs: object) -> Survivor:
        with spawn_lock:
            process = Survivor(3000 + len(handles))
            handles.append(process)
        return process

    publish = diagnostic._publish
    publications: list[str] = []
    copy_calls: list[Path] = []

    def fail_publication(path: Path, payload: object) -> None:
        publications.append(path.name)
        if path.name == failed_artifact:
            raise OSError("SECRET /private/env")
        publish(path, payload)

    monkeypatch.setattr(diagnostic, "_publish", fail_publication)
    if failed_artifact == "public-report":

        def fail_copy(source: Path, destination: Path) -> None:
            copy_calls.append(destination)
            raise OSError("SECRET /private/env")

        monkeypatch.setattr(diagnostic.shutil, "copyfile", fail_copy)
    output = tmp_path / "publication-with-survivors"
    with pytest.raises(diagnostic.DiagnosticPublicationError) as raised:
        diagnostic.run_diagnostic(output, spawn=spawn)
    assert len(handles) == 2
    assert all(handle.kill_calls == 2 for handle in handles)
    assert all(handle.wait_timeouts == [60.0, diagnostic._REAP_SECONDS] for handle in handles)
    if failed_artifact == "public-report":
        assert len(copy_calls) == 1
    else:
        assert publications.count(failed_artifact) == 1
    assert (output / "manifest.json").exists() is (failed_artifact == "public-report")
    assert not any((output / phase).exists() for phase in diagnostic._PHASES[1:])
    failure = raised.value
    assert str(failure) == "diagnostic_publication_failed"
    assert failure.__context__ is None
    assert failure.cleanup["status"] == "incomplete"
    assert failure.cleanup["attempted_children"] == 2
    assert set(failure.cleanup["unreaped_pids"]) == {handle.pid for handle in handles}
    assert failure.cleanup["kill_error_count"] == failure.cleanup["wait_error_count"] == 2

    def propagate(path: Path, *, timeout: float) -> None:
        raise failure

    monkeypatch.setattr(diagnostic, "run_diagnostic", propagate)
    assert diagnostic.main(["--output", str(output)]) == 3
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "SECRET" not in captured.err and "/private/" not in captured.err
    assert len(captured.err.encode()) < 256
    handoff = json.loads(captured.err)
    assert set(handoff) == {"diagnostic_only", "error_category", "unreaped_pids"}
    assert handoff["diagnostic_only"] is True
    assert handoff["error_category"] == "diagnostic_cleanup_incomplete"
    assert len(handoff["unreaped_pids"]) == 2
    assert all(isinstance(pid, int) for pid in handoff["unreaped_pids"])
    assert set(handoff["unreaped_pids"]) == {handle.pid for handle in handles}
    assert all(handle.kill_calls == 2 for handle in handles)


def test_publication_failure_without_survivors_keeps_publication_exit_code(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    cleanup = {
        "status": "complete",
        "attempted_children": 0,
        "unreaped_pids": [],
        "kill_error_count": 0,
        "wait_error_count": 0,
    }

    def fail(path: Path, *, timeout: float) -> None:
        raise diagnostic.DiagnosticPublicationError(cleanup)

    monkeypatch.setattr(diagnostic, "run_diagnostic", fail)
    assert diagnostic.main(["--output", str(tmp_path / "no-survivors")]) == 2
    assert json.loads(capsys.readouterr().err) == {
        "diagnostic_only": True,
        "error_category": "diagnostic_publication_failed",
    }


def test_final_cleanup_can_reap_retained_handles_without_launching_another_pair(
    tmp_path: Path,
) -> None:
    class LateKill:
        stdout = None
        stderr = None

        def __init__(self, pid: int) -> None:
            self.pid = pid
            self.returncode: int | None = None
            self.kill_calls = 0
            self.wait_timeouts: list[float] = []

        def wait(self, timeout: float) -> int:
            self.wait_timeouts.append(timeout)
            if self.kill_calls < 2:
                raise subprocess.TimeoutExpired("SECRET", timeout)
            self.returncode = -9
            return self.returncode

        def kill(self) -> None:
            self.kill_calls += 1
            if self.kill_calls == 1:
                raise OSError("SECRET")

    handles: list[LateKill] = []
    spawn_lock = threading.Lock()

    def spawn(*args: object, **kwargs: object) -> LateKill:
        with spawn_lock:
            process = LateKill(2000 + len(handles))
            handles.append(process)
        return process

    result = diagnostic.run_diagnostic(tmp_path / "final-reap", spawn=spawn)
    assert len(handles) == result["observation_count"] == 2
    assert result["completion"] == "aborted_cleanup"
    assert result["final_process_cleanup"] == {
        "status": "complete",
        "attempted_children": 2,
        "unreaped_pids": [],
        "kill_error_count": 0,
        "wait_error_count": 0,
    }
    assert result["cleanup_complete"] is True
    assert all(handle.returncode == -9 and handle.kill_calls == 2 for handle in handles)
    assert all(handle.wait_timeouts == [60.0, diagnostic._REAP_SECONDS] for handle in handles)


@pytest.mark.parametrize("timeout", [float("nan"), float("inf"), 0, 181])
def test_invalid_timeout_does_not_create_output(tmp_path: Path, timeout: float) -> None:
    output = tmp_path / "invalid-timeout"
    with pytest.raises(ValueError):
        diagnostic.run_diagnostic(output, timeout=timeout)
    assert not output.exists()


def test_cli_contract_requires_output_and_does_not_mask_publication_errors(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(
        diagnostic,
        "run_diagnostic",
        lambda path, timeout: {"diagnostic_only": True, "cleanup_complete": True},
    )
    with pytest.raises(SystemExit):
        diagnostic.main([])
    assert diagnostic.main(["--output", str(tmp_path / "new")]) == 0
    monkeypatch.setattr(
        diagnostic, "run_diagnostic", lambda path, timeout: (_ for _ in ()).throw(OSError("SECRET"))
    )
    assert diagnostic.main(["--output", str(tmp_path / "new")]) == 2
    assert "SECRET" not in capsys.readouterr().err


def test_cli_success_means_publication_only_even_when_every_child_fails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    run = diagnostic.run_diagnostic

    def fail(*args: object, **kwargs: object) -> None:
        raise OSError("SECRET")

    monkeypatch.setattr(
        diagnostic,
        "run_diagnostic",
        lambda path, timeout: run(path, timeout=timeout, spawn=fail),
    )
    output = tmp_path / "failed-children-cli"
    assert diagnostic.main(["--output", str(output)]) == 0
    result = json.loads((output / "manifest.json").read_text())
    assert all(observation["status"] == "process_error" for observation in result["observations"])
    assert result["acceptance_established"] is False
    assert result["required_pytest_result"] == "not_modified"


def test_import_and_fake_process_tests_do_not_import_audio_packages() -> None:
    assert not _SCI_IMPORTS_FROM_SCRIPT
    source = _SCRIPT.read_text()
    tree = ast.parse(source)
    top_imports = [node for node in tree.body if isinstance(node, (ast.Import, ast.ImportFrom))]
    assert all(
        "numpy" not in ast.unparse(node) and "librosa" not in ast.unparse(node)
        for node in top_imports
    )
    annotations = {
        node.name: ast.unparse(node.returns)
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.returns is not None
    }
    assert annotations["run_diagnostic"] == "DiagnosticManifest"
    assert annotations["_cache_counts"] == "CacheCounts"
    assert annotations["_input_identity"] == "InputIdentity"
    assert annotations["_run_one"] == "AudioObservation"
    assert annotations["_crash_metadata"] == "MacCrashMetadata"
    assert annotations["_versions"] == "dict[str, str]"
    assert annotations["_final_process_cleanup"] == "FinalProcessCleanup"
    capture = next(
        node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == "_Capture"
    )
    payload = next(
        node
        for node in capture.body
        if isinstance(node, ast.FunctionDef) and node.name == "payload"
    )
    assert payload.returns is not None and ast.unparse(payload.returns) == "StreamCapturePayload"
    schemas = {
        node.name
        for node in tree.body
        if isinstance(node, ast.ClassDef)
        and any(isinstance(base, ast.Name) and base.id == "TypedDict" for base in node.bases)
    }
    assert {
        "DiagnosticManifest",
        "WaveInput",
        "AudioObservation",
        "ChildResult",
        "InputIdentity",
        "CacheCounts",
        "StreamCapturePayload",
        "CacheDebugEvent",
        "MacCrashMetadata",
        "MacCrashReport",
        "FinalProcessCleanup",
        "SupervisorHandoff",
    } <= schemas


def test_child_observes_full_onset_returns_and_publishes_both_public_outputs_without_native_imports(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    directory = tmp_path / "shared_cache_cold" / "child-1"
    cache = tmp_path / "caches" / "shared"
    directory.mkdir(parents=True)
    cache.mkdir(parents=True)
    diagnostic._publish(tmp_path / "diagnostic-marker.json", {"diagnostic_only": True})
    monkeypatch.setenv("NUMBA_CACHE_DIR", str(cache))
    monkeypatch.setattr(diagnostic, "_write_test_wave", lambda directory: directory / "input.wav")

    class Array:
        def tolist(self) -> list[float]:
            return [0.0, 0.25, 0.5]

    onset = ModuleType("librosa.onset")

    def onset_strength() -> Array:
        return Array()

    def onset_detect() -> Array:
        return Array()

    onset.__dict__["onset_strength"] = FunctionType(
        onset_strength.__code__, onset.__dict__, closure=onset_strength.__closure__
    )
    onset.__dict__["onset_detect"] = FunctionType(
        onset_detect.__code__, onset.__dict__, closure=onset_detect.__closure__
    )
    calls = []

    def analyze(path: Path) -> SimpleNamespace:
        calls.append(path)
        onset.onset_strength()
        onset.onset_detect()
        return SimpleNamespace(
            feature_report={"bpm": 0.0},
            synthesis_features={"noise": 0.0},
            dna_evidence={"dominant_note": "A4"},
        )

    extractor = ModuleType("rytm_randomizer.style_analysis.extractor")
    extractor.__dict__.update(
        analyze_audio=analyze,
        analyze_audio_snapshot=analyze,
        audio_dna_evidence_to_dict=dict,
        audio_synthesis_features_to_dict=dict,
    )
    feature_report = ModuleType("rytm_randomizer.style_analysis.feature_report")
    feature_report.__dict__["feature_report_to_dict"] = dict
    monkeypatch.setitem(sys.modules, extractor.__name__, extractor)
    monkeypatch.setitem(sys.modules, feature_report.__name__, feature_report)
    assert diagnostic._child(directory) == 0
    assert calls == [directory / "input.wav"] * 2
    arrays = [
        json.loads((directory / f"onset-{number}.json").read_text()) for number in range(1, 5)
    ]
    assert all(array["values"] == [0.0, 0.25, 0.5] for array in arrays)
    assert [array["api"] for array in arrays] == ["analyze_audio_snapshot"] * 2 + [
        "analyze_audio"
    ] * 2
    for name in ("analyze_audio_snapshot", "analyze_audio"):
        assert json.loads((directory / f"{name}.json").read_text()) == {
            "feature_report": {"bpm": 0.0},
            "synthesis_features": {"noise": 0.0},
            "dna_evidence": {"dominant_note": "A4"},
        }
    assert sys.getprofile() is None


def test_child_errors_publish_fixed_categories_without_private_messages(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    directory = tmp_path / "shared_cache_cold" / "child-1"
    cache = tmp_path / "caches" / "shared"
    directory.mkdir(parents=True)
    cache.mkdir(parents=True)
    diagnostic._publish(tmp_path / "diagnostic-marker.json", {"diagnostic_only": True})
    monkeypatch.setenv("NUMBA_CACHE_DIR", str(cache))

    def fail(directory: Path) -> None:
        raise ImportError("SECRET /private/audio")

    monkeypatch.setattr(diagnostic, "_write_test_wave", fail)
    assert diagnostic._child(directory) == 1
    result = json.loads((directory / "child.json").read_text())
    assert result == {
        "status": "failed",
        "error_category": "dependency_error",
        "stage": "bootstrap",
        "onset_array_count": 0,
    }
    assert "SECRET" not in json.dumps(result)


def test_macos_crash_metadata_matches_only_child_pids_and_redacts_report_content(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    reports = tmp_path / "Library/Logs/DiagnosticReports"
    reports.mkdir(parents=True)
    (reports / "Python-1.ips").write_text(
        json.dumps({"app_name": "SECRET"})
        + "\n"
        + json.dumps(
            {"pid": 1001, "exception": {"type": "EXC_BAD_ACCESS"}, "path": "/private/SECRET"}
        )
    )
    (reports / "Python-other.ips").write_text(
        json.dumps({"pid": 9999, "exception": {"type": "EXC_BAD_ACCESS"}})
    )
    (reports / "Python-2.crash").write_text(
        "Process: Python [1002]\nException Type: EXC_BAD_ACCESS\nSECRET"
    )
    original_scandir = os.scandir
    monkeypatch.setattr(diagnostic.sys, "platform", "darwin")
    monkeypatch.setattr(diagnostic.Path, "home", lambda: tmp_path)
    monkeypatch.setattr(
        diagnostic.os,
        "scandir",
        lambda path: (
            original_scandir(reports)
            if Path(path) == reports
            else original_scandir(tmp_path / "absent")
        ),
    )
    result = diagnostic._crash_metadata({1001, 1002}, 0.0)
    assert result["status"] == "matched"
    assert {report["pid"] for report in result["reports"]} == {1001, 1002}
    assert all(report["exception"] == "bad_access" for report in result["reports"])
    assert "SECRET" not in json.dumps(result)


def test_macos_crash_report_reads_are_bounded(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    reports = tmp_path / "Library/Logs/DiagnosticReports"
    reports.mkdir(parents=True)
    for number in range(20):
        (reports / f"Python-{number}.ips").write_text(json.dumps({"pid": 1001}))
    original_scandir = os.scandir
    monkeypatch.setattr(diagnostic.sys, "platform", "darwin")
    monkeypatch.setattr(diagnostic.Path, "home", lambda: tmp_path)
    monkeypatch.setattr(
        diagnostic.os,
        "scandir",
        lambda path: (
            original_scandir(reports)
            if Path(path) == reports
            else original_scandir(tmp_path / "absent")
        ),
    )
    result = diagnostic._crash_metadata({1001}, 0.0)
    assert result["bounded"] is True
    assert result["read_count"] == len(result["reports"]) == 8
