/**
 * Vitest setup file. Loaded before every test file.
 *
 * - Pulls in `@testing-library/jest-dom` matchers (toBeInTheDocument, etc.).
 * - We do NOT touch the global `WebSocket`; ws-client tests inject a mock factory.
 */

import '@testing-library/jest-dom/vitest';
