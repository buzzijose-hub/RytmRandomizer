import { defineConfig } from '@playwright/test';

// This target launches the native shell itself; Playwright only owns the runner.
// Missing native prerequisites FAIL instead of turning safety checks into skips.
export default defineConfig({
  testDir: './native-e2e',
  timeout: 150_000,
  fullyParallel: false,
  workers: 1,
  retries: 0,
  reporter: process.env.CI ? [['github'], ['html', { outputFolder: 'native-playwright-report', open: 'never' }]] : 'list',
  webServer: {
    command: 'npm run dev -- --host 127.0.0.1 --port 5173 --strictPort',
    url: 'http://127.0.0.1:5173',
    reuseExistingServer: !process.env.CI,
    timeout: 60_000,
  },
});
