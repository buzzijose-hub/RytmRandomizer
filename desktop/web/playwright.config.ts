/**
 * Playwright config for the cockpit/wizard E2E suite.
 *
 * The suite drives a real Chromium browser against the Vite dev server (which
 * loads `desktop/web/src` exactly as the Tauri shell does) and the real Python
 * sidecar (`python -m rytm_randomizer.cockpit`). The sidecar is spawned per
 * worker by the shared `wizard_fixture`, NOT by `webServer` here — the sidecar
 * needs a per-test isolated profiles directory (`XDG_CONFIG_HOME` / `APPDATA`)
 * which can't be expressed at the global config level.
 *
 * `webServer` here only manages the Vite dev server. We force a single worker
 * (`workers: 1`) + `fullyParallel: false` so the one Vite instance + one
 * sidecar process don't collide on port 4317.
 */

import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './e2e',
  timeout: 30_000,
  expect: { timeout: 5_000 },
  fullyParallel: false, // single sidecar process per worker; avoid port races
  retries: process.env.CI ? 2 : 0,
  workers: 1,
  reporter: process.env.CI ? [['html', { open: 'never' }], ['github']] : 'list',
  use: {
    baseURL: 'http://127.0.0.1:5173',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
  },
  projects: [
    { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
  ],
  webServer: {
    command: 'npm run dev -- --host 127.0.0.1 --port 5173',
    url: 'http://127.0.0.1:5173',
    reuseExistingServer: !process.env.CI,
    timeout: 60_000,
  },
});
