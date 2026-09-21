import { defineConfig } from '@playwright/test';

import nativeConfig from './playwright.native.config';

// Explicit prerequisites fail this target; the existing 32 native cases retain
// their public signature vector and need no ephemeral installer preparation.
export default defineConfig({
  ...nativeConfig,
  testDir: './native-install-e2e',
  reporter: process.env.CI
    ? [['github'], ['html', { outputFolder: 'native-install-playwright-report', open: 'never' }]]
    : 'list',
});
