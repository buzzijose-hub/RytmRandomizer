"""Bounded frozen-sidecar reference workflow proof; synthetic audio, MIDI off."""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import math
import os
import shutil
import socket
import struct
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
import wave
from pathlib import Path
from typing import BinaryIO, cast

from websockets.sync.client import connect

from rytm_randomizer.cockpit.capture import decode_kit_capture_frame
from rytm_randomizer.cockpit.library.store import LibraryStore


def require_package_check(condition: object, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def synthetic_reference(frequency: float) -> bytes:
    """An explicit test tone, never an instrument-render substitute."""
    from io import BytesIO

    buffer = BytesIO()
    with wave.open(buffer, "wb") as audio:
        audio.setnchannels(1)
        audio.setsampwidth(2)
        audio.setframerate(22050)
        samples = (
            struct.pack("<h", int(16000 * math.sin(2 * math.pi * frequency * index / 22050)))
            for index in range(11025)
        )
        audio.writeframes(b"".join(samples))
    return buffer.getvalue()


def _wait_owned_sidecar_exit(process: subprocess.Popen[bytes], timeout: float) -> bool:
    try:
        process.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        return False
    return True


def _stop_owned_sidecar(process: subprocess.Popen[bytes]) -> None:
    """Bound shutdown to this Popen handle, including a kill/reap fallback."""
    try:
        if process.poll() is not None:
            return
        if process.stdin is not None:
            try:
                process.stdin.write(b"RYTM_SIDECAR_SHUTDOWN\n")
                process.stdin.flush()
            except (OSError, ValueError):
                pass
        if _wait_owned_sidecar_exit(process, 12):
            return
        for stop in (process.terminate, process.kill):
            try:
                stop()
            except OSError:
                if process.poll() is not None:
                    return
            if _wait_owned_sidecar_exit(process, 5):
                return
        raise RuntimeError("Owned sidecar did not stop after bounded shutdown and kill.")
    finally:
        if process.stdin is not None:
            try:
                process.stdin.close()
            except (OSError, ValueError):
                pass


def _finish_owned_sidecar(
    process: subprocess.Popen[bytes], log: BinaryIO, backend_log: Path, receipt: Path
) -> None:
    """Preserve private diagnostics even when shutdown fails, without masking QA failure."""
    primary_error = sys.exception()
    try:
        _stop_owned_sidecar(process)
    except (OSError, RuntimeError):
        if primary_error is None:
            raise RuntimeError(
                "Owned sidecar shutdown failed; package proof is incomplete."
            ) from None
        primary_error.add_note("Owned sidecar shutdown failed; package proof is incomplete.")
    finally:
        try:
            log.flush()
        finally:
            receipt.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(backend_log, receipt.parent / "backend-private.log")


def run(binary: Path, receipt: Path) -> dict[str, object]:
    """Test only this owned executable/backend and terminate it afterward."""
    started = time.monotonic()
    root = Path(__file__).resolve().parents[1]
    with tempfile.TemporaryDirectory(prefix="reference-package-qa-") as temporary:
        owned = Path(temporary)
        home = owned / "home"
        home.mkdir()
        library = LibraryStore(home / "rytm-randomizer" / "library")
        source_ids: dict[str, str] = {}
        sources = {
            "analog_rytm_mk2": (
                "RYTM_RIO145_AR_CORE_RETURN_Kit.syx",
                2,
                ["filter_frequency", "amp_decay"],
            ),
            "analog_four_mk2": (
                "A4_RIO145_CORE_RETURN_Kit.syx",
                3,
                ["filter1_frequency", "filter2_resonance"],
            ),
        }
        for device, (name, _, _) in sources.items():
            frame = (root / "tests" / "fixtures" / "rio145" / name).read_bytes()
            source_ids[device] = library.retain_source(
                decode_kit_capture_frame(device, frame), origin="file_import"
            ).record_id
        with socket.socket() as listener:
            listener.bind(("127.0.0.1", 0))
            port = listener.getsockname()[1]
        token_file = owned / "token"
        environment = dict(os.environ)
        for name in ("PYTHONPATH", "PYTHONHOME", "VIRTUAL_ENV"):
            environment.pop(name, None)
        environment.update(
            {
                "RYTM_RAND_MIDI_BACKEND": "off",
                "RYTM_RAND_WS_PORT": str(port),
                "RYTM_RAND_WS_TOKEN_FILE": str(token_file),
                "APPDATA": str(home),
                "HOME": str(home),
                "USERPROFILE": str(home),
                "XDG_CONFIG_HOME": str(home),
            }
        )
        outcomes: list[dict[str, object]] = []
        with (owned / "backend.log").open("wb") as log:
            process = subprocess.Popen(
                [str(binary)],
                cwd=owned,
                env=environment,
                stdin=subprocess.PIPE,
                stdout=log,
                stderr=subprocess.STDOUT,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
            try:
                deadline = time.monotonic() + 30
                while True:
                    if process.poll() is not None:
                        raise RuntimeError("Frozen sidecar exited before readiness.")
                    try:
                        with urllib.request.urlopen(
                            f"http://127.0.0.1:{port}/health", timeout=1
                        ) as response:
                            health = json.load(response)
                        break
                    except (OSError, urllib.error.URLError):
                        if time.monotonic() >= deadline:
                            raise RuntimeError("Frozen sidecar did not become ready.") from None
                        time.sleep(0.05)
                require_package_check(
                    health.get("mode", "mock") == "mock", "Frozen startup must be passive."
                )
                token = token_file.read_text().strip()
                with connect(
                    f"ws://127.0.0.1:{port}/ws", subprotocols=["rytm-rand-cockpit-v1"]
                ) as ws:
                    ws.send(json.dumps({"type": "hello", "token": token}))
                    require_package_check(
                        json.loads(ws.recv(timeout=10)) == {"ok": True},
                        "Frozen authentication failed.",
                    )
                    while True:
                        event = json.loads(ws.recv(timeout=10))
                        if event.get("type") == "session_status":
                            require_package_check(
                                event["armed"] is False, "Frozen startup was armed."
                            )
                        if event.get("type") == "connection_changed":
                            break
                    sequence = 0

                    def command(action: str, **body: object) -> dict[str, object]:
                        nonlocal sequence
                        sequence += 1
                        request_id = f"qa-{sequence}"
                        before = time.monotonic()
                        ws.send(
                            json.dumps(
                                {
                                    "request_id": request_id,
                                    "command": {
                                        "type": "reference_sound",
                                        "action": action,
                                        **body,
                                    },
                                }
                            )
                        )
                        while True:
                            ack = json.loads(ws.recv(timeout=70))
                            if ack.get("request_id") == request_id:
                                break
                        require_package_check(
                            ack["ok"], f"Frozen {action} refused: {ack.get('message')}"
                        )
                        outcomes.append(
                            {"action": action, "seconds": round(time.monotonic() - before, 4)}
                        )
                        return cast(dict[str, object], ack["reference_sound"])

                    def upload(audio: bytes) -> str:
                        upload_id = str(command("upload_begin", size=len(audio))["upload_id"])
                        for offset in range(0, len(audio), 192 * 1024):
                            command(
                                "upload_chunk",
                                upload_id=upload_id,
                                offset=offset,
                                chunk=base64.b64encode(
                                    audio[offset : offset + 192 * 1024]
                                ).decode(),
                            )
                        return upload_id

                    for device, (_, target, parameters) in sources.items():
                        audio = synthetic_reference(440.0)
                        imported = command(
                            "upload_finish",
                            upload_id=upload(audio),
                            title="Synthetic package proof",
                        )
                        imported_session = cast(dict[str, object], imported["session"])
                        generated = command(
                            "generate",
                            session_id=imported_session["session_id"],
                            source_record_id=source_ids[device],
                            device_id=device,
                            target=target,
                            parameters=parameters,
                            locks=[],
                            strength=0.1,
                        )
                        session = cast(dict[str, object], generated["session"])
                        candidates = cast(list[dict[str, object]], session["candidates"])
                        require_package_check(
                            len(candidates) == 8, "Eight real candidates were not generated."
                        )
                        chosen = candidates[0]
                        require_package_check(
                            chosen["roundtrip_redecoded"] is True
                            and chosen["hardware_send_validated"] is False,
                            "Candidate codec or physical-evidence boundary changed.",
                        )
                        command(
                            "favorite",
                            session_id=session["session_id"],
                            candidate_id=chosen["candidate_id"],
                            favorite=True,
                        )
                        recording = synthetic_reference(880.0)
                        compared = command(
                            "record",
                            session_id=session["session_id"],
                            candidate_id=chosen["candidate_id"],
                            candidate_sha256=chosen["frame_sha256"],
                            upload_id=upload(recording),
                        )
                        require_package_check(
                            cast(dict[str, object], compared["session"])["recordings"],
                            "Recording comparison was not retained.",
                        )
                        command(
                            "refine",
                            session_id=session["session_id"],
                            candidate_id=chosen["candidate_id"],
                            correction_gain=0.5,
                        )
                        exported = command(
                            "export",
                            session_id=session["session_id"],
                            candidate_id=chosen["candidate_id"],
                            destination_slot=19,
                        )
                        frame = base64.b64decode(str(exported["sysex_base64"]))
                        require_package_check(
                            hashlib.sha256(frame).hexdigest() == exported["sha256"],
                            "Export byte identity changed.",
                        )
                        reopened = command("reopen", session_id=session["session_id"])
                        require_package_check(
                            chosen["candidate_id"]
                            in cast(dict[str, object], reopened["session"])["favorites"],
                            "Favorite was not retained on reopen.",
                        )
            finally:
                _finish_owned_sidecar(process, log, owned / "backend.log", receipt)
            exit_code = process.returncode
        result: dict[str, object] = {
            "binary_sha256": hashlib.sha256(binary.read_bytes()).hexdigest(),
            "seconds": round(time.monotonic() - started, 3),
            "operations": outcomes,
            "exit_code": exit_code,
            "midi_backend": "off",
            "audio_evidence": "synthetic only",
            "developer_python_cleared": True,
            "owned_process_stopped": process.poll() is not None,
        }
        receipt.parent.mkdir(parents=True, exist_ok=True)
        receipt.write_text(json.dumps(result, indent=2) + "\n")
        return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--binary", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    arguments = parser.parse_args()
    result = run(arguments.binary.resolve(), arguments.receipt.resolve())
    print(json.dumps({key: value for key, value in result.items() if key != "operations"}))


if __name__ == "__main__":
    main()
