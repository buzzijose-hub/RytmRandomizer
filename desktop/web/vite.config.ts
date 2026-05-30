import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'node:path';

// https://vitejs.dev/config/
// The Tauri shell (WS-H) loads the built artifact from `desktop/web/dist` and proxies dev
// requests when running `npm run dev`. The Python sidecar serves the WebSocket on
// 127.0.0.1:4317 by default (env `RYTM_RAND_WS_PORT`).
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, 'src'),
    },
  },
  server: {
    // Tauri dev uses a fixed port so the Rust shell can connect to it deterministically.
    port: 5173,
    strictPort: true,
  },
  build: {
    outDir: 'dist',
    sourcemap: true,
    target: 'es2022',
    emptyOutDir: true,
  },
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: ['./tests/setup.ts'],
    include: ['tests/**/*.test.{ts,tsx}'],
    coverage: {
      provider: 'v8',
      reporter: ['text', 'html', 'json-summary'],
      reportsDirectory: './coverage',
      include: [
        'src/ws/**',
        'src/state/**',
        'src/cockpit/**',
        'src/wizard/**',
        'src/types/wizard_protocol.ts',
      ],
      exclude: ['src/**/index.ts', 'src/cockpit/**/*.css', 'src/wizard/**/*.css'],
      thresholds: {
        // WS-I scope: 100% branch coverage on ws/** and state/**.
        // WS-J scope: 100% branch coverage on cockpit/**.
        lines: 100,
        functions: 100,
        statements: 100,
        branches: 100,
      },
    },
  },
});
