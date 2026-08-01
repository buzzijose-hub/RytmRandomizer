/**
 * Vitest setup file. Loaded before every test file.
 *
 * - Pulls in `@testing-library/jest-dom` matchers (toBeInTheDocument, etc.).
 * - We do NOT touch the global `WebSocket`; ws-client tests inject a mock factory.
 * - Stubs `HTMLCanvasElement.getContext` to a no-op. jsdom does not implement
 *   canvas; axe-core's colour-contrast rule probes `getContext('2d')` while
 *   detecting icon-ligature fonts and otherwise floods stderr with
 *   "Not implemented" noise on every a11y scan. Returning null keeps axe on
 *   its non-canvas code path (contrast is enforced in Chromium by the E2E
 *   `a11y_axe_scan.spec` and by the CSS-token architecture test), while the
 *   structural WCAG rules still run in jsdom.
 */

import '@testing-library/jest-dom/vitest';

if (typeof HTMLCanvasElement !== 'undefined') {
  HTMLCanvasElement.prototype.getContext = (() => null) as typeof HTMLCanvasElement.prototype.getContext;
}
