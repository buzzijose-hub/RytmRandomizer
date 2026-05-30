/**
 * Announcer — debounced writer into the live-region <div>.
 *
 * Architecture:
 * - LiveRegion.tsx mounts the visually-hidden <div role="status"> and
 *   registers its `setText` callback via `_registerWriter(...)`.
 * - Anywhere in the app, call `announce(message)`; the message is
 *   debounced (default 200ms) then written into the live region.
 * - SRs announce the change automatically via aria-live="polite".
 *
 * Debounce coalesces bursty calls (e.g. ten store updates fired during
 * one mutation) into a single announcement of the last message — the
 * intermediate states are not useful to a SR user.
 *
 * Reference: WAI-ARIA 1.2 §"Live regions" and
 * https://www.w3.org/WAI/ARIA/apg/practices/live-regions/
 */

type Writer = (message: string) => void;

let writer: Writer | null = null;
let pendingMessage: string | null = null;
let timer: ReturnType<typeof setTimeout> | null = null;
const DEBOUNCE_MS = 200;

export function _registerWriter(next: Writer | null): void {
  writer = next;
}

export function announce(message: string): void {
  pendingMessage = message;
  if (timer !== null) clearTimeout(timer);
  timer = setTimeout(() => {
    if (writer !== null && pendingMessage !== null) {
      writer(pendingMessage);
    }
    pendingMessage = null;
    timer = null;
  }, DEBOUNCE_MS);
}

/** Clear pending announcements + the writer. Test-only escape hatch. */
export function _reset(): void {
  if (timer !== null) clearTimeout(timer);
  timer = null;
  pendingMessage = null;
  writer = null;
}
