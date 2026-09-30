"""Real ASGI token/origin/bootstrap refusal and bounded asset checks."""

from __future__ import annotations

import asyncio
import io
import json
import logging
import os
import re
from pathlib import Path
from types import SimpleNamespace
from urllib.parse import urlencode

import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from rytm_randomizer.cockpit import appliance_runtime as runtime
from rytm_randomizer.cockpit.__main__ import build_session
from rytm_randomizer.cockpit.ws.server import create_app
from rytm_randomizer.observability.metrics import MidiMetrics

pytestmark = pytest.mark.fast
AUTH = "test-ws-token"
NEXT_AUTH = "new-ws-token"
ARM_AUTH = "new-arm-secret"


@pytest.fixture
def prepared(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[TestClient, Path, Path]:
    monkeypatch.delenv(runtime.WEB_ROOT_ENV, raising=False)
    app = create_app(build_session(), token=AUTH)
    web = tmp_path / "web"
    private = tmp_path / "private"
    web.mkdir()
    (web / "index.html").write_text('<html><head></head><body><div id="root"></div></body></html>')
    (web / "bundle.js").write_text("window.production=true")
    (web / "font.unknownfiletype").write_bytes(b"bitmap")
    monkeypatch.setenv(runtime.WEB_ROOT_ENV, str(web))
    monkeypatch.setenv(runtime.RUNTIME_DIR_ENV, str(private))
    monkeypatch.setenv("RYTM_RAND_WS_PORT", "4317")
    runtime.install_appliance_routes(app, token=AUTH, arm_secret=None)
    return TestClient(app, base_url="http://127.0.0.1:4317"), web, private


def credential(private: Path) -> str:
    match = re.search(r'name="credential" value="([^"]+)"', (private / "launch.html").read_text())
    assert match is not None
    return match.group(1)


def enter(client: TestClient, private: Path) -> None:
    response = client.post(
        "/bootstrap", data={"credential": credential(private)}, headers={"Origin": "null"}
    )
    assert response.status_code == 200


def test_private_launch_post_handoff_and_authenticated_production_document(
    prepared: tuple[TestClient, Path, Path],
) -> None:
    client, _, private = prepared
    launch = (private / "launch.html").read_text()
    assert 'method="post"' in launch
    assert "test-ws-token" not in launch
    if os.name == "posix":
        assert private.stat().st_mode & 0o777 == 0o700
        assert (private / "launch.html").stat().st_mode & 0o777 == 0o600
    with client:
        assert client.get("/health").status_code == 200
        assert client.get("/appliance").status_code == 403
        response = client.post(
            "/bootstrap", data={"credential": credential(private)}, headers={"Origin": "null"}
        )
        assert response.status_code == 200
        assert "HttpOnly" in response.headers["set-cookie"]
        assert "SameSite=strict" in response.headers["set-cookie"]
        assert '__RYTM_RAND_WS_TOKEN__="test-ws-token"' in response.text
        assert "__RYTM_RAND_ARM_SECRET__" not in response.text
        assert "history.replaceState" in response.text
        assert response.headers["cache-control"] == "no-store"
        assert "frame-ancestors 'none'" in response.headers["content-security-policy"]
        assert response.headers["x-frame-options"] == "DENY"
        assert client.get("/appliance").status_code == 200
        assert client.get("/").status_code == 200
        assert client.get("/bundle.js").text == "window.production=true"
        assert (
            client.get("/font.unknownfiletype").headers["content-type"]
            == "application/octet-stream"
        )
        assert client.get("/index.html").status_code == 404
        assert client.get("/missing.js").status_code == 404


@pytest.mark.parametrize(
    "headers",
    [
        {"Host": "attacker.invalid:4317"},
        {"Origin": "https://attacker.invalid"},
        {"Origin": "null"},
        {"Cookie": "rytm-appliance-session=wrong"},
    ],
)
def test_document_refuses_rebinding_cross_origin_and_bad_cookie(
    prepared: tuple[TestClient, Path, Path], headers: dict[str, str]
) -> None:
    client, _, private = prepared
    enter(client, private)
    assert client.get("/appliance", headers=headers).status_code == 403


def test_bootstrap_rejects_wrong_unicode_oversize_and_malformed(
    prepared: tuple[TestClient, Path, Path],
) -> None:
    client, _, _ = prepared
    assert client.post("/bootstrap", data={"credential": "wrong"}).status_code == 403
    assert client.post("/bootstrap", data={"credential": "é"}).status_code == 403
    assert client.post("/bootstrap", content=b"x" * 2049).status_code == 413
    assert client.post("/bootstrap", content="a=1&b=2&c=3&d=4&e=5").status_code == 400
    assert (
        client.post("/bootstrap", headers={"Origin": "https://attacker.invalid"}).status_code == 403
    )
    assert client.post("/bootstrap", content="a=1").status_code == 403


def test_ws_requires_same_origin_cookie_and_existing_hello_token(
    prepared: tuple[TestClient, Path, Path],
) -> None:
    client, _, private = prepared
    with pytest.raises(WebSocketDisconnect) as denied:
        with client.websocket_connect(
            "ws://127.0.0.1:4317/ws",
            headers={"Origin": "http://127.0.0.1:4317"},
            subprotocols=["rytm-rand-cockpit-v1"],
        ):
            pass
    assert denied.value.code == 1008
    enter(client, private)
    for headers in ({}, {"Origin": "https://attacker.invalid"}):
        with pytest.raises(WebSocketDisconnect) as denied:
            with client.websocket_connect(
                "ws://127.0.0.1:4317/ws", headers=headers, subprotocols=["rytm-rand-cockpit-v1"]
            ):
                pass
        assert denied.value.code == 1008
    with client.websocket_connect(
        "ws://127.0.0.1:4317/ws",
        headers={"Origin": "http://127.0.0.1:4317"},
        subprotocols=["rytm-rand-cockpit-v1"],
    ) as socket:
        socket.send_text(json.dumps({"type": "hello", "token": "wrong"}))
        assert socket.receive_json()["code"] == "auth_failed"
    with client.websocket_connect(
        "ws://127.0.0.1:4317/ws",
        headers={"Origin": "http://127.0.0.1:4317"},
        subprotocols=["rytm-rand-cockpit-v1"],
    ) as socket:
        socket.send_text(json.dumps({"type": "hello", "token": "test-ws-token"}))
        assert socket.receive_json() == {"ok": True}
        assert socket.receive_json()["type"] == "session_status"


@pytest.mark.parametrize("package_propagates", [False, True])
def test_auth_refusal_categories_log_transport_and_increment_metrics_without_request_data(
    prepared: tuple[TestClient, Path, Path],
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
    capsys: pytest.CaptureFixture[str],
    package_propagates: bool,
) -> None:
    client, _, private = prepared
    metrics = MidiMetrics()
    monkeypatch.setattr(runtime, "get_metrics", lambda: metrics)
    # Reproduce inherited suite state: a stale capture stream and either
    # package-level propagation policy must not affect this semantic test.
    package_logger = logging.getLogger("rytm_randomizer")
    closed_stream = io.StringIO()
    closed_stream.close()
    monkeypatch.setattr(package_logger, "handlers", [logging.StreamHandler(closed_stream)])
    monkeypatch.setattr(package_logger, "propagate", package_propagates)
    caplog.set_level(logging.WARNING, logger=runtime.__name__)
    monkeypatch.setattr(runtime._logger, "handlers", [caplog.handler])
    monkeypatch.setattr(runtime._logger, "propagate", False)
    request_path = "/private-request-path-sentinel"
    secrets = [
        "private-header-host.invalid",
        "https://private-header-origin.invalid",
        "private-body-credential",
        credential(private),
        AUTH,
        ARM_AUTH,
        request_path,
    ]
    assert client.get(request_path, headers={"Host": secrets[0]}).status_code == 403
    assert client.get("/appliance", headers={"Origin": secrets[1]}).status_code == 403
    assert client.get("/appliance").status_code == 403
    assert client.post("/bootstrap", data={"credential": secrets[2]}).status_code == 403
    assert client.post("/bootstrap", content=b"x" * 2049).status_code == 413
    assert client.post("/bootstrap", content="a=1&b=2&c=3&d=4&e=5").status_code == 400
    with pytest.raises(WebSocketDisconnect):
        with client.websocket_connect(
            "ws://127.0.0.1:4317/ws", headers={"Origin": "http://127.0.0.1:4317"}
        ):
            pass
    records = [record for record in caplog.records if record.name == runtime.__name__]
    assert len(records) == 7
    assert all(record.getMessage() == "appliance_auth_refused" for record in records)
    assert [record.fingerprint for record in records] == [
        "appliance_auth.host",
        "appliance_auth.origin",
        "appliance_auth.session",
        "appliance_auth.bootstrap",
        "appliance_auth.bootstrap",
        "appliance_auth.bootstrap",
        "appliance_auth.session",
    ]
    assert [record.transport for record in records] == ["http"] * 6 + ["websocket"]
    assert dict(metrics.errors_by_kind) == {
        "appliance_auth.host": 1,
        "appliance_auth.origin": 1,
        "appliance_auth.session": 2,
        "appliance_auth.bootstrap": 3,
    }
    assert all(
        Path(record.pathname).resolve() == Path(runtime.__file__).resolve() for record in records
    )
    # Exercise POSIX source metadata on every host, including Windows.
    record_data = [
        {**record.__dict__, "pathname": Path(record.pathname).as_posix()} for record in records
    ]
    logged = json.dumps([record.__dict__ for record in records], default=str)
    assert all(secret not in logged for secret in secrets)
    # Only trusted standard source metadata is exempt from the broad route rule.
    # The unique actual request path above must be absent from the whole record.
    assert all(
        "/appliance" not in str({key: value for key, value in record.items() if key != "pathname"})
        for record in record_data
    )
    assert not metrics.cc_sent_by_channel
    assert "--- Logging error ---" not in capsys.readouterr().err


def test_assets_are_bounded_and_do_not_escape_web_root(
    prepared: tuple[TestClient, Path, Path], monkeypatch: pytest.MonkeyPatch
) -> None:
    client, web, private = prepared
    enter(client, private)
    monkeypatch.setattr(runtime, "MAX_ASSET_BYTES", 5)
    assert client.get("/bundle.js").status_code == 413
    assert client.get("/%2e%2e/private/launch.html").status_code == 404
    assert client.get("/directory/").status_code == 404
    (web / "directory").mkdir()
    assert client.get("/directory/").status_code == 404


def test_restart_rotates_every_authentication_capability(
    prepared: tuple[TestClient, Path, Path], monkeypatch: pytest.MonkeyPatch
) -> None:
    first, _, private = prepared
    old = credential(private)
    enter(first, private)
    old_cookie = first.cookies.get(runtime.COOKIE_NAME)
    assert old_cookie
    monkeypatch.delenv(runtime.WEB_ROOT_ENV)
    app = create_app(build_session(), token=NEXT_AUTH)
    monkeypatch.setenv(runtime.WEB_ROOT_ENV, str(prepared[1]))
    runtime.install_appliance_routes(app, token=NEXT_AUTH, arm_secret=ARM_AUTH)
    second = TestClient(app, base_url="http://127.0.0.1:4317")
    assert second.post("/bootstrap", data={"credential": old}).status_code == 403
    assert (
        second.get(
            "/appliance", headers={"Cookie": f"{runtime.COOKIE_NAME}={old_cookie}"}
        ).status_code
        == 403
    )
    response = second.post("/bootstrap", data={"credential": credential(private)})
    assert second.cookies.get(runtime.COOKIE_NAME) != old_cookie
    assert second.get("/appliance").status_code == 200
    assert "new-arm-secret" in response.text
    assert "new-ws-token" in response.text


@pytest.mark.parametrize("port", ["1", "65536"])
def test_runtime_refuses_privileged_or_invalid_port(
    prepared: tuple[TestClient, Path, Path], monkeypatch: pytest.MonkeyPatch, port: str
) -> None:
    monkeypatch.setenv("RYTM_RAND_WS_PORT", port)
    with pytest.raises(ValueError, match="unprivileged"):
        runtime.install_appliance_routes(prepared[0].app, token=AUTH, arm_secret=None)


def test_runtime_refuses_bad_or_oversized_index(
    prepared: tuple[TestClient, Path, Path], monkeypatch: pytest.MonkeyPatch
) -> None:
    client, web, _ = prepared
    (web / "index.html").write_text("not-production")
    with pytest.raises(ValueError, match="head"):
        runtime.install_appliance_routes(client.app, token=AUTH, arm_secret=None)
    monkeypatch.setattr(runtime, "MAX_ASSET_BYTES", 1)
    with pytest.raises(ValueError, match="bounded"):
        runtime.install_appliance_routes(client.app, token=AUTH, arm_secret=None)


def test_document_labels_explicit_simulation(
    prepared: tuple[TestClient, Path, Path], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("RYTM_RAND_APPLIANCE_SIMULATION", "1")
    client, _, private = prepared
    enter(client, private)
    assert '__RYTM_RAND_RUNTIME_MODE__="simulation"' in client.get("/appliance").text


def test_launch_credential_is_not_an_http_query(prepared: tuple[TestClient, Path, Path]) -> None:
    client, _, private = prepared
    assert (
        client.get("/bootstrap?" + urlencode({"credential": credential(private)})).status_code
        == 404
    )


def test_posix_permission_path_and_index_containment(
    prepared: tuple[TestClient, Path, Path], monkeypatch: pytest.MonkeyPatch
) -> None:
    client, _, private = prepared
    monkeypatch.setattr(runtime, "os", SimpleNamespace(name="posix", environ=os.environ))
    runtime.install_appliance_routes(client.app, token=AUTH, arm_secret=None)
    assert (private / "launch.html").exists()
    monkeypatch.setattr(Path, "is_relative_to", lambda *_: False)
    with pytest.raises(ValueError, match="inside web root"):
        runtime.install_appliance_routes(client.app, token=AUTH, arm_secret=None)


def test_simulation_composition_withholds_output_capability_before_any_provider(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from rytm_randomizer.cockpit.ws import handlers

    class RefusingProvider:
        def list_output_names(self) -> tuple[str, ...]:
            pytest.fail("simulation must never enumerate an output provider")

        def open_output(self, _port_name: str) -> object:
            pytest.fail("simulation must never open an output provider")

    monkeypatch.delenv(runtime.WEB_ROOT_ENV, raising=False)
    session = build_session()
    session.arm_secret = ARM_AUTH
    session.arm_port_provider = RefusingProvider()
    monkeypatch.setenv("RYTM_RAND_APPLIANCE_SIMULATION", "1")
    create_app(session, token=AUTH)
    assert session.arm_secret is None

    def refuse_spec(_name: str) -> None:
        pytest.fail("simulation must refuse before searching/importing the MIDI backend")

    monkeypatch.setattr(handlers.importlib.util, "find_spec", refuse_spec)
    # Removing the environment flag after composition cannot restore authority.
    monkeypatch.delenv("RYTM_RAND_APPLIANCE_SIMULATION")
    ack = asyncio.run(
        handlers.handle_command(
            {
                "request_id": "simulation-arm-refusal",
                "command": {
                    "type": "arm",
                    "arm_token": ARM_AUTH,
                    "confirm": True,
                    "port_name": "exact output",
                },
            },
            session,
        )
    )
    assert ack["ok"] is False
    assert "no ARM secret" in str(ack["message"])
    assert session.armed_apply is None
    assert session.hardware_intent is False


def test_ordinary_production_composition_retains_explicit_arm_capability(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv(runtime.WEB_ROOT_ENV, raising=False)
    monkeypatch.setenv("RYTM_RAND_APPLIANCE_SIMULATION", "0")
    session = build_session()
    session.arm_secret = ARM_AUTH
    create_app(session, token=AUTH)
    assert session.arm_secret == ARM_AUTH
