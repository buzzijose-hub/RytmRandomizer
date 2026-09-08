/**
 * Drive the real Tauri IPC event bridge in tests.
 *
 * The update panel subscribes with `listen()` from `@tauri-apps/api/event`.
 * Stubbing that import would recreate the exact defect this seam exists to
 * prevent: the original tests dispatched a DOM `CustomEvent` and passed while
 * the shell emitted over IPC, so the panel could never have received a real
 * message and nothing failed. A test has to exercise the transport the
 * producer actually uses.
 *
 * `mockIPC` intercepts the IPC layer *below* `listen()`, so the production
 * path — the dynamic import, the real `listen`, the real payload envelope —
 * all runs. Two things about the wire shape are not obvious:
 *
 * 1. `listen` sends `{event, target, handler}` where **`handler` is a NUMBER**,
 *    a callback id, not a function. Calling it fails with "handler is not a
 *    function".
 * 2. The real callback lives in Tauri's internal registry, not on `window`
 *    under that id. The mock exposes `window.__TAURI_INTERNALS__.runCallback`
 *    to invoke it, which is the supported way in.
 */
import { emit } from '@tauri-apps/api/event';
import { mockIPC } from '@tauri-apps/api/mocks';

type CallbackId = number;

/** Install the IPC shim. Call once per suite, before mounting. */
export function installTauriEventBridge(): void {
  const listeners = new Map<string, CallbackId[]>();

  mockIPC((cmd, args) => {
    const payload = (args ?? {}) as Record<string, unknown>;

    if (cmd === 'plugin:event|listen') {
      const event = String(payload.event);
      const id = payload.handler as CallbackId;
      listeners.set(event, [...(listeners.get(event) ?? []), id]);
      return id;
    }

    if (cmd === 'plugin:event|emit' || cmd === 'plugin:event|emit_to') {
      const event = String(payload.event);
      const internals = (window as unknown as {
        __TAURI_INTERNALS__?: { runCallback?: (id: number, value: unknown) => void };
      }).__TAURI_INTERNALS__;
      for (const id of listeners.get(event) ?? []) {
        internals?.runCallback?.(id, { event, id, payload: payload.payload });
      }
      return undefined;
    }

    if (cmd === 'plugin:event|unlisten') {
      const event = String(payload.event);
      const id = payload.eventId as CallbackId;
      listeners.set(event, (listeners.get(event) ?? []).filter((known) => known !== id));
      return undefined;
    }

    return undefined;
  });
}

/** Emit an event the way the Rust shell does. */
export async function emitTauriEvent(event: string, payload: unknown): Promise<void> {
  await emit(event, payload);
}
