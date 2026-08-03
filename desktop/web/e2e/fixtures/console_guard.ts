/**
 * Console-error tracking for E2E specs.
 *
 * Every no-device / reconnect spec asserts that the journey produced ZERO
 * unexpected browser console errors — a crash-detection net the DOM
 * assertions alone don't provide (React error boundaries and swallowed
 * rejections surface here first).
 *
 * Each spec passes its own allowlist and documents every allowance. The one
 * recurring legitimate entry is Chromium's WS dial-failure line
 * ("WebSocket connection to 'ws://…' failed"), which is EXPECTED noise in
 * specs that deliberately run without a sidecar or kill it mid-test — the
 * reconnect loop is the feature under test there, not a defect.
 */

import { expect, type Page } from '@playwright/test';

/** Chromium's console line for a failed WS dial (offline / kill windows). */
export const WS_DIAL_FAILURE = /WebSocket connection to 'ws:\/\/127\.0\.0\.1:4317\/ws' failed/;

export interface ConsoleErrorTracker {
  /** Unexpected console-error texts collected so far (mutating view). */
  readonly errors: readonly string[];
  /** Assert no unexpected console errors were observed. */
  assertClean(): void;
}

/**
 * Start collecting `console.error` output + uncaught page errors on `page`.
 * Messages matching any `allowlist` regex are ignored. Call `assertClean()`
 * at the end of the journey (and after any intermediate phase, if useful).
 */
export function trackConsoleErrors(
  page: Page,
  allowlist: readonly RegExp[] = [],
): ConsoleErrorTracker {
  const errors: string[] = [];
  page.on('console', (message) => {
    if (message.type() !== 'error') return;
    const text = message.text();
    if (allowlist.some((pattern) => pattern.test(text))) return;
    errors.push(text);
  });
  page.on('pageerror', (error) => {
    errors.push(`pageerror: ${error.message}`);
  });
  return {
    errors,
    assertClean(): void {
      expect(errors, 'unexpected browser console errors during the journey').toEqual([]);
    },
  };
}
