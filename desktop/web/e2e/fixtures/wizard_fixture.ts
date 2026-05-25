/**
 * Per-test sidecar fixture for wizard E2E tests.
 *
 * Spawns `python -m rytm_randomizer.cockpit` on a free port with an isolated
 * profiles directory (via `XDG_CONFIG_HOME` on Linux/macOS and `APPDATA` on
 * Windows — see `rytm_randomizer/cockpit/profiles/paths.py`). The browser
 * already connects to the default `ws://127.0.0.1:4317/ws`, so we keep the
 * port at 4317 and rely on `workers: 1` in the Playwright config to ensure
 * only one sidecar is alive at a time.
 *
 * Why per-test (not per-worker): the wizard's "save" step writes a profile
 * to disk. Two tests sharing one sidecar would see each other's state
 * (active profile, on-disk profile list). Per-test isolation keeps each
 * spec deterministic at the cost of a couple of seconds of Python startup.
 *
 * The fixture also exposes the temp dir so a test can introspect
 * `<tmpdir>/rytm-randomizer/profiles/user/*.json` to confirm a save landed.
 */

import { test as base, expect } from '@playwright/test';
import { spawn, type ChildProcessWithoutNullStreams } from 'node:child_process';
import { mkdtempSync, readFileSync, rmSync } from 'node:fs';
import * as net from 'node:net';
import { tmpdir } from 'node:os';
import * as path from 'node:path';
import { fileURLToPath } from 'node:url';

import { WS_AUTH_TOKEN_STORAGE_KEY } from '../../src/ws/client';

// ESM doesn't expose CommonJS' `__dirname`; derive it from `import.meta.url`.
// Playwright's TS runner reports `import.meta.url` even when the file is
// transpiled to CJS, so this is portable across both module modes.
const FIXTURE_DIR = path.dirname(fileURLToPath(import.meta.url));

/** The well-known sidecar port (matches `DEFAULT_WS_URL` in src/ws/client.ts). */
const SIDECAR_PORT = 4317;
const SIDECAR_HOST = '127.0.0.1';

/** Time-budget for the sidecar to accept TCP connections. */
const SIDECAR_BOOT_TIMEOUT_MS = 15_000;
/** Poll interval while waiting for the sidecar to come up. */
const SIDECAR_POLL_INTERVAL_MS = 200;
/** Grace period after sending SIGTERM before SIGKILL. */
const SIDECAR_SHUTDOWN_TIMEOUT_MS = 5_000;

/**
 * Resolve the Python executable. CI typically sets `PYTHON` to the venv
 * interpreter; locally we fall back to `python` on the PATH.
 */
function resolvePythonBinary(): string {
  return process.env.PYTHON ?? process.env.PYTHON_EXECUTABLE ?? 'python';
}

/**
 * Resolve the repo root (4 levels up from `desktop/web/e2e/fixtures`).
 * Used to set cwd for the sidecar so `python -m rytm_randomizer.cockpit`
 * picks up the in-tree package without an editable install.
 */
function resolveRepoRoot(): string {
  return path.resolve(FIXTURE_DIR, '..', '..', '..', '..');
}

/** Poll the sidecar's TCP port until it accepts a connection or we time out. */
async function waitForSidecarPort(
  host: string,
  port: number,
  timeoutMs: number,
): Promise<void> {
  const deadline = Date.now() + timeoutMs;
  let lastError: unknown = null;
  while (Date.now() < deadline) {
    try {
      await new Promise<void>((resolve, reject) => {
        const sock = net.createConnection({ host, port }, () => {
          sock.end();
          resolve();
        });
        sock.once('error', reject);
      });
      return;
    } catch (err) {
      lastError = err;
      await new Promise((r) => setTimeout(r, SIDECAR_POLL_INTERVAL_MS));
    }
  }
  throw new Error(
    `sidecar did not accept ws://${host}:${port} within ${timeoutMs}ms: ${String(
      lastError,
    )}`,
  );
}

/** Best-effort shutdown — SIGTERM, then SIGKILL after a grace period. */
async function stopSidecar(child: ChildProcessWithoutNullStreams): Promise<void> {
  if (child.exitCode !== null || child.killed) return;
  child.kill('SIGTERM');
  await new Promise<void>((resolve) => {
    const timer = setTimeout(() => {
      if (child.exitCode === null && !child.killed) {
        child.kill('SIGKILL');
      }
      resolve();
    }, SIDECAR_SHUTDOWN_TIMEOUT_MS);
    child.once('exit', () => {
      clearTimeout(timer);
      resolve();
    });
  });
}

export interface SidecarHandle {
  readonly process: ChildProcessWithoutNullStreams;
  readonly profilesRoot: string;
  readonly token: string;
  readonly host: string;
  readonly port: number;
  /** stderr accumulator for diagnostic surfacing on failure. */
  readonly stderr: { text: string };
}

interface WizardFixtures {
  sidecar: SidecarHandle;
}

/**
 * The exported `test` object. Specs `import { test, expect } from './fixtures/wizard_fixture'`
 * to automatically get a freshly-booted sidecar (and an isolated profiles
 * directory) per test.
 */
export const test = base.extend<WizardFixtures>({
  // Per-test sidecar with an isolated profiles dir. The `page` fixture is used
  // to inject the freshly-minted WS token before each spec navigates.
  sidecar: async ({ page }, use, testInfo) => {
    const tmpRoot = mkdtempSync(path.join(tmpdir(), 'rytm-wizard-e2e-'));
    const tokenFile = path.join(tmpRoot, 'cockpit-ws-token');
    const python = resolvePythonBinary();
    const cwd = resolveRepoRoot();

    // Honour both Linux/macOS (XDG) and Windows (APPDATA) so the same fixture
    // works on every CI runner without an OS-conditional in the spec file.
    const childEnv: NodeJS.ProcessEnv = {
      ...process.env,
      XDG_CONFIG_HOME: tmpRoot,
      APPDATA: tmpRoot,
      // Force the sidecar onto the well-known port the web client dials.
      RYTM_RAND_WS_PORT: String(SIDECAR_PORT),
      RYTM_RAND_WS_TOKEN_FILE: tokenFile,
      WIZARD_SOURCE_ROOTS: tmpRoot,
      // Unbuffer Python stdio so error tracebacks surface promptly in CI logs.
      PYTHONUNBUFFERED: '1',
    };

    const child = spawn(python, ['-m', 'rytm_randomizer.cockpit'], {
      cwd,
      env: childEnv,
      stdio: ['ignore', 'pipe', 'pipe'],
    });

    const stderr = { text: '' };
    child.stdout.on('data', () => {
      // Drain stdout to keep the OS buffer from blocking the child.
    });
    child.stderr.on('data', (chunk: Buffer) => {
      stderr.text += chunk.toString('utf8');
    });

    let token: string;
    try {
      await waitForSidecarPort(SIDECAR_HOST, SIDECAR_PORT, SIDECAR_BOOT_TIMEOUT_MS);
      token = readFileSync(tokenFile, 'utf8').trim();
      await page.addInitScript(
        ({ storageKey, token: injectedToken }) => {
          window.localStorage.setItem(storageKey, injectedToken);
          window.__RYTM_RAND_WS_TOKEN__ = injectedToken;
        },
        { storageKey: WS_AUTH_TOKEN_STORAGE_KEY, token },
      );
    } catch (err) {
      await stopSidecar(child);
      rmSync(tmpRoot, { recursive: true, force: true });
      throw new Error(
        `failed to boot rytm sidecar: ${String(err)}\nstderr:\n${stderr.text}`,
      );
    }

    const handle: SidecarHandle = {
      process: child,
      profilesRoot: tmpRoot,
      token,
      host: SIDECAR_HOST,
      port: SIDECAR_PORT,
      stderr,
    };

    try {
      await use(handle);
    } finally {
      await stopSidecar(child);
      // Surface child stderr on test failure so triage isn't a guessing game.
      if (testInfo.status !== testInfo.expectedStatus && stderr.text.length > 0) {
        testInfo.attach('sidecar-stderr', {
          body: stderr.text,
          contentType: 'text/plain',
        });
      }
      rmSync(tmpRoot, { recursive: true, force: true });
    }
  },
});

export { expect };
