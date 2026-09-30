"""Authenticated local presentation of the existing production Cockpit.

The private launch document carries a process-local bootstrap credential in
a POST body. Neither the WS token nor the arm secret appears in a URL, CLI
argument, diagnostic, or persistent frontend storage. This module has no MIDI
authority; it presents the app composed by the established entry point.
"""

from __future__ import annotations

import hmac
import json
import mimetypes
import os
import secrets
from http.cookies import SimpleCookie
from pathlib import Path
from typing import Final
from urllib.parse import parse_qs

from fastapi import FastAPI, Request
from starlette.responses import HTMLResponse, Response
from starlette.types import ASGIApp, Receive, Scope, Send

from .export.writer import atomic_write

WEB_ROOT_ENV: Final[str] = "RYTM_RAND_APPLIANCE_WEB_ROOT"
RUNTIME_DIR_ENV: Final[str] = "RYTM_RAND_APPLIANCE_RUNTIME_DIR"
COOKIE_NAME: Final[str] = "rytm-appliance-session"
MAX_ASSET_BYTES: Final[int] = 20 * 1024 * 1024
MAX_BOOTSTRAP_BYTES: Final[int] = 2048


class ApplianceGuard:
    """Refuse DNS rebinding, foreign origins and unauthenticated documents."""

    def __init__(self, app: ASGIApp, *, origin: str, cookie: str) -> None:
        self.app = app
        self.origin = origin
        self.host = origin.removeprefix("http://")
        self.cookie = cookie

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] not in {"http", "websocket"}:
            await self.app(scope, receive, send)
            return
        headers = dict(scope.get("headers", []))
        host = headers.get(b"host", b"").decode("latin1")
        origin = headers.get(b"origin", b"").decode("latin1")
        path = scope.get("path", "")
        bootstrap = scope["type"] == "http" and path == "/bootstrap"
        origin_ok = origin == self.origin or (not origin and scope["type"] == "http")
        if bootstrap and origin == "null":
            origin_ok = True
        jar: SimpleCookie = SimpleCookie()
        jar.load(headers.get(b"cookie", b"").decode("latin1"))
        value = jar[COOKIE_NAME].value if COOKIE_NAME in jar else ""
        public = bootstrap or path == "/health"
        authorised = public or hmac.compare_digest(value.encode("utf-8"), self.cookie.encode())
        if host != self.host or not origin_ok or not authorised:
            if scope["type"] == "websocket":
                await send({"type": "websocket.close", "code": 1008})
            else:
                await Response("Appliance authentication required", status_code=403)(
                    scope, receive, send
                )
            return
        await self.app(scope, receive, send)


def _document(index: str, *, token: str, arm_secret: str | None, port: int) -> HTMLResponse:
    nonce = secrets.token_urlsafe(24)
    values: dict[str, str | int | bool] = {
        "__RYTM_RAND_WS_TOKEN__": token,
        "__RYTM_RAND_WS_PORT__": port,
        "__RYTM_RAND_APPLIANCE__": True,
        "__RYTM_RAND_RUNTIME_MODE__": (
            "simulation" if os.environ.get("RYTM_RAND_APPLIANCE_SIMULATION") == "1" else "passive"
        ),
    }
    if arm_secret is not None:
        values["__RYTM_RAND_ARM_SECRET__"] = arm_secret
    script = "".join(f"window.{key}={json.dumps(value)};" for key, value in values.items())
    script += "history.replaceState(null,'','/appliance');"
    injected = f'<script nonce="{nonce}">{script}</script>'
    html = index.replace("<head>", f"<head>{injected}", 1)
    return HTMLResponse(
        html,
        headers={
            "Cache-Control": "no-store",
            "Referrer-Policy": "no-referrer",
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "Content-Security-Policy": (
                f"default-src 'self'; script-src 'self' 'nonce-{nonce}'; "
                "style-src 'self' 'unsafe-inline'; img-src 'self' data:; "
                f"connect-src 'self' ws://127.0.0.1:{port}; "
                "frame-ancestors 'none'; base-uri 'none'; form-action 'self'"
            ),
        },
    )


def install_appliance_routes(app: FastAPI, *, token: str, arm_secret: str | None) -> None:
    """Opt-in composition hook; retain the existing /ws and /health handlers."""
    root = Path(os.environ[WEB_ROOT_ENV]).resolve(strict=True)
    index_path = (root / "index.html").resolve(strict=True)
    if not index_path.is_relative_to(root) or index_path.stat().st_size > MAX_ASSET_BYTES:
        raise ValueError("Appliance requires a bounded production index.html inside web root")
    index = index_path.read_text(encoding="utf-8")
    if "<head>" not in index:
        raise ValueError("Appliance requires a bounded production index.html with a head")
    port = int(os.environ.get("RYTM_RAND_WS_PORT", "4317"))
    if not 1024 <= port <= 65535:
        raise ValueError("Appliance port must be an unprivileged TCP port")
    origin = f"http://127.0.0.1:{port}"
    runtime = Path(os.environ[RUNTIME_DIR_ENV]).resolve()
    runtime.mkdir(parents=True, exist_ok=True, mode=0o700)
    if os.name == "posix":
        runtime.chmod(0o700)
    bootstrap_secret = secrets.token_urlsafe(32)
    cookie = secrets.token_urlsafe(32)
    launch = (
        '<!doctype html><meta charset="utf-8"><title>Launching appliance</title>'
        f'<form method="post" action="{origin}/bootstrap">'
        f'<input type="hidden" name="credential" value="{bootstrap_secret}">'
        "<noscript><button>Open appliance</button></noscript></form>"
        "<script>document.forms[0].submit()</script>"
    )
    atomic_write(runtime / "launch.html", launch.encode("utf-8"), overwrite=True)
    (runtime / "launch.html").chmod(0o600)
    app.add_middleware(ApplianceGuard, origin=origin, cookie=cookie)

    async def bootstrap(request: Request) -> Response:
        body = bytearray()
        async for chunk in request.stream():
            body.extend(chunk)
            if len(body) > MAX_BOOTSTRAP_BYTES:
                return Response("Bootstrap body too large", status_code=413)
        try:
            parsed = parse_qs(bytes(body).decode("utf-8", errors="replace"), max_num_fields=4)
        except ValueError:
            return Response("Malformed bootstrap body", status_code=400)
        credential = parsed.get("credential", [""])[0]
        if not hmac.compare_digest(credential.encode("utf-8"), bootstrap_secret.encode()):
            return Response("Bootstrap refused", status_code=403)
        response = _document(index, token=token, arm_secret=arm_secret, port=port)
        response.set_cookie(COOKIE_NAME, cookie, httponly=True, samesite="strict", path="/")
        return response

    async def document() -> HTMLResponse:
        return _document(index, token=token, arm_secret=arm_secret, port=port)

    async def asset(asset_path: str) -> Response:
        path = (root / asset_path).resolve()
        if not path.is_relative_to(root) or not path.is_file():
            return Response("Asset not found", status_code=404)
        if path.suffix == ".html":
            return Response("Use /appliance", status_code=404)
        if path.stat().st_size > MAX_ASSET_BYTES:
            return Response("Asset too large", status_code=413)
        return Response(
            path.read_bytes(),
            media_type=mimetypes.guess_type(path.name)[0] or "application/octet-stream",
            headers={"Cache-Control": "no-store", "X-Content-Type-Options": "nosniff"},
        )

    app.add_api_route("/bootstrap", bootstrap, methods=["POST"])
    app.add_api_route("/appliance", document, methods=["GET"])
    app.add_api_route("/", document, methods=["GET"])
    app.add_api_route("/{asset_path:path}", asset, methods=["GET"])


__all__ = ["install_appliance_routes"]
