"""A shell-emitted event must be consumed on the channel it is emitted on.

The Tauri shell and the React webview exchange events across a boundary no
compiler and no single test suite spans. The shell emits with Tauri's IPC
(``window.emit(...)`` in Rust, delivered to JS via ``listen()`` from
``@tauri-apps/api``); the DOM's ``window.addEventListener`` is a *different*
channel and never receives it. Both sides can be individually correct, fully
typed, and 100% covered while no message ever crosses.

This is not a hypothetical either. The auto-update program's first parallel
run had ``desktop/shell/src/main.rs`` emitting ``rytm-update-state`` over IPC
while ``UpdatePanel.tsx`` subscribed with ``window.addEventListener`` — and
``@tauri-apps/api`` was not even a dependency of the web package. B-rust
passed 159/159 cargo tests, B-web passed 854/854 vitest at 100% coverage, and
in the bundled app the update chip would never have appeared.

The precedent for this test is
``tests/architecture/test_frontend_matches_handshake_contract.py``, which
pins the two-argument ``new WebSocket(url, subprotocol)`` CALL FORM after
PR #113 shipped the single-argument shape. Same idea: assert the call form,
not merely that a shared string exists on both sides.

The test is deliberately conditional on the files existing — the update
surface is still landing — but it is NOT fail-open on the assertion: once a
Rust ``emit`` of a named event exists, the TS side must subscribe correctly
or this fails.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Final

PROJECT_ROOT: Final[Path] = Path(__file__).resolve().parents[2]
SHELL_SRC: Final[Path] = PROJECT_ROOT / "desktop" / "shell" / "src"
WEB_SRC: Final[Path] = PROJECT_ROOT / "desktop" / "web" / "src"
WEB_PACKAGE_JSON: Final[Path] = PROJECT_ROOT / "desktop" / "web" / "package.json"

#: ``window.emit("some-event"`` / ``app.emit(SOME_CONST`` — the Rust producer side.
_RUST_EMIT: Final[re.Pattern[str]] = re.compile(
    r"\.emit(?:_all|_to)?\(\s*(?:\"([a-z0-9-]+)\"|([A-Z_][A-Z0-9_]*))"
)

#: A Rust ``const NAME: &str = "value";`` so a constant emit can be resolved.
_RUST_CONST: Final[re.Pattern[str]] = re.compile(
    r"const\s+([A-Z_][A-Z0-9_]*)\s*:\s*&(?:'static\s+)?str\s*=\s*\"([^\"]+)\""
)


def _rust_emitted_event_names() -> set[str]:
    """Every event name the Rust shell emits over Tauri IPC."""
    if not SHELL_SRC.is_dir():
        return set()
    sources = [rs.read_text(encoding="utf-8") for rs in sorted(SHELL_SRC.rglob("*.rs"))]

    # Collect EVERY const first: the emit call and the const that names the
    # event routinely live in different modules (main.rs emits a constant
    # declared in update_policy.rs). Resolving per-file silently drops those.
    consts: dict[str, str] = {}
    for text in sources:
        for name, value in _RUST_CONST.findall(text):
            consts[name] = value

    emits: set[str] = set()
    for text in sources:
        for literal, const_name in _RUST_EMIT.findall(text):
            if literal:
                emits.add(literal)
            elif const_name in consts:
                emits.add(consts[const_name])
    return emits


def _web_source_text() -> str:
    if not WEB_SRC.is_dir():
        return ""
    return "\n".join(
        p.read_text(encoding="utf-8")
        for p in sorted(WEB_SRC.rglob("*.ts")) + sorted(WEB_SRC.rglob("*.tsx"))
    )


#: A real ``listen(...)`` subscribe call from ``@tauri-apps/api``.
#:
#: Two properties this must have, and a plain ``"listen(" in web`` substring
#: test has neither:
#:
#: 1. It must match the GENERIC form. The only call site in this repo is
#:    ``listen<unknown>(UPDATE_STATE_EVENT_NAME, ...)``; the literal substring
#:    ``listen(`` never appears, so the naive test read "no Tauri subscription
#:    here" and flagged a correct codebase.
#: 2. It must NOT match ``unlisten(``. The naive test was satisfied by the
#:    UNSUBSCRIBE call — ``unlisten()`` contains ``listen(`` — so its evidence
#:    that the webview subscribes over IPC came from the teardown path. A
#:    codebase that only ever unsubscribed, and never subscribed at all, would
#:    have passed it. Renaming that one call (to ``stopQuietly(unlisten)``)
#:    made the guard fail on code whose subscribe path was untouched, which is
#:    how this was found.
#:
#: The leading boundary is what excludes ``unlisten`` / ``removeListen``.
_TS_TAURI_LISTEN: Final[re.Pattern[str]] = re.compile(
    r"(?<![A-Za-z0-9_$.])listen\s*(?:<[^>]*>\s*)?\("
)


def _web_subscribes_over_ipc(web: str) -> bool:
    """Whether the web layer makes a real ``@tauri-apps/api`` listen call."""
    return _TS_TAURI_LISTEN.search(web) is not None


def test_ipc_emitted_events_are_not_consumed_as_dom_events() -> None:
    """A Tauri-IPC event subscribed with ``addEventListener`` never fires."""
    emitted = _rust_emitted_event_names()
    if not emitted:
        return  # no IPC producer yet; nothing to pin

    web = _web_source_text()
    mismatched = [
        name
        for name in sorted(emitted)
        if re.search(rf"addEventListener\(\s*[^)]*{re.escape(name)}", web)
        or (
            # subscribed via a TS constant holding the same string
            re.search(rf"=\s*[\"']{re.escape(name)}[\"']", web)
            and "addEventListener" in web
            and not _web_subscribes_over_ipc(web)
        )
    ]

    assert not mismatched, (
        "The Rust shell emits these events over Tauri IPC, but the web layer "
        f"subscribes with the DOM's addEventListener: {mismatched}.\n\n"
        "These are different channels. window.emit() is delivered to JS only "
        "through `listen()` from @tauri-apps/api; a DOM listener never fires, "
        "so the feature is silently inert in the bundled app while both sides' "
        "own test suites stay green.\n"
        "Fix: subscribe with `listen(EVENT, handler)` from @tauri-apps/api "
        "(and add that dependency), or have the shell re-dispatch to the DOM "
        "explicitly via eval/inject if a DOM event is genuinely wanted."
    )


def test_web_declares_tauri_api_when_it_listens_for_shell_events() -> None:
    """If the web layer calls ``listen(``, the dependency must be declared."""
    web = _web_source_text()
    if not _web_subscribes_over_ipc(web):
        return
    if not WEB_PACKAGE_JSON.is_file():
        return
    package = WEB_PACKAGE_JSON.read_text(encoding="utf-8")
    assert "@tauri-apps/api" in package, (
        "The web layer subscribes to shell events with `listen(`, but "
        "@tauri-apps/api is not declared in desktop/web/package.json. The "
        "import resolves in neither the dev loop nor the bundle."
    )


def test_the_listen_detector_matches_the_call_form_not_a_substring() -> None:
    """The detector must accept a real subscribe and reject an unsubscribe.

    This pins the two ways the previous ``"listen(" in web`` substring test was
    wrong, because both were silent:

    * It **missed the generic form**. The only call site in this repo is
      ``listen<unknown>(...)``, in which the literal ``listen(`` never appears,
      so the check concluded there was no Tauri subscription at all.
    * It **accepted the unsubscribe call**. ``unlisten()`` contains
      ``listen(``, so the guard's evidence that the webview subscribed over IPC
      came from the teardown path. Renaming that single call site to
      ``stopQuietly(unlisten)`` — a change that did not touch the subscribe
      path — made the guard fail on correct code, which is how this surfaced.

    A guard whose pass depends on an unrelated substring is not enforcing its
    invariant; it is passing by coincidence.
    """
    subscribes = [
        "listen<unknown>(UPDATE_STATE_EVENT_NAME, cb)",
        "listen(UPDATE_STATE_EVENT_NAME, cb)",
        "await listen<T>( NAME, cb )",
    ]
    not_subscribes = [
        "unlisten()",
        "stopQuietly(unlisten)",
        "this.removeListen(x)",
        "obj.listen(x)",
    ]
    for src in subscribes:
        assert _web_subscribes_over_ipc(src), f"must count as a subscribe: {src!r}"
    for src in not_subscribes:
        assert not _web_subscribes_over_ipc(src), f"must NOT count as a subscribe: {src!r}"
