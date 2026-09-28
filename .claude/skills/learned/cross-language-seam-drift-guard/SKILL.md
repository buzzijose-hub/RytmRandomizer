---
name: cross-language-seam-drift-guard
description: A contract that fixes a NOUN (payload shape, event name) leaves the VERB free — two sides can agree on the data and disagree on the channel, staying green on both suites while nothing crosses. Pin the CALL FORM with a drift guard, or generate one side from the other.
user-invocable: false
origin: auto-extracted-2026-09-08
---

# Pin the call form, not just the payload

**Extracted:** 2026-09-08
**Context:** The auto-update program's worst blocker. The shell emitted
`rytm-update-state` over Tauri IPC; the webview subscribed with the DOM's
`window.addEventListener`. `@tauri-apps/api` was not even a dependency.
B-rust passed 159/159 cargo tests, B-web passed 854/854 vitest at 100%
coverage, and **no message could ever cross**. In the bundled app the update
chip would simply never appear.

## Problem

The interface contract said:

> **I2** — Shell→webview event `rytm-update-state`:
> `{state, version, notes, hardware_revalidation, error_code}`

Both agents honored it *exactly*. Both used the same event name. The contract
fixed the **noun** — the data that crosses — and left the **verb** free:

| side | code | channel |
|---|---|---|
| producer | `window.emit(UPDATE_STATE_EVENT, payload)` | Tauri IPC |
| consumer | `window.addEventListener(NAME, handle)` | DOM |

These are different channels. `emit()` reaches JS only via `listen()` from
`@tauri-apps/api`. Neither side's tests could detect it, because each side is
individually correct.

## Pattern

A cross-boundary contract row must name **the function the consumer calls**,
not only the shape that crosses:

- BAD: "an event named `rytm-update-state` carrying `{state, version, ...}`"
- GOOD: "`subscribeUpdateState(cb): () => void`, exported from
  `src/updateProtocol.ts`, implemented with `listen()` from `@tauri-apps/api`"

Then enforce it, in this order of preference:

1. **Generate one side from the other** with a `--check` gate. Repo precedent:
   `scripts/generate_live_gui_protocol_ts.py` +
   `tests/architecture/test_live_gui_protocol_is_generated.py`. In the same
   run, the ONE contract that used this mechanism (I1, `app_version`) produced
   **zero** defects; every hand-declared cross-language contract produced one.
2. **A drift guard asserting the call form.** Repo precedent:
   `tests/architecture/test_frontend_matches_handshake_contract.py`, which
   pins the two-argument `new WebSocket(url, subprotocol)` shape — written
   after PR #113 shipped the one-argument form. Same bug class, already solved.
3. Prose. Only 1 and 2 fail CI.

`tests/architecture/test_cross_language_event_seams_agree.py` is the guard for
this seam.

## Gotcha that made the first guard useless

The first version of that guard **passed on the real defect**. The `emit` call
lives in `main.rs`; the `const UPDATE_STATE_EVENT` is declared in
`update_policy.rs`. The scanner resolved constants per-file, so the cross-file
reference never bound and the check silently found nothing to assert.

Collect **all** constants across every source file before resolving emits. And
mutation-prove a guard against the real defect — a guard you have not tried to
break is a guard you do not have.

## Cross-references

- `.claude/rules/parallel-agent-composition.md` §4.
- `tests/architecture/test_cross_language_event_seams_agree.py`.
- `tests/architecture/test_frontend_matches_handshake_contract.py` — the precedent.
- `scripts/generate_live_gui_protocol_ts.py` — the generate-and-check precedent.
