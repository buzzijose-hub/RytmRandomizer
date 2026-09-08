/**
 * Per-test sidecar fixtures for the cockpit E2E suite.
 *
 * Spawns `python -m rytm_randomizer.cockpit` on the well-known port 4317 with
 * an isolated profiles directory (via `XDG_CONFIG_HOME` on Linux and `APPDATA`
 * on Windows — see `rytm_randomizer/cockpit/profiles/paths.py`). `workers: 1`
 * in the Playwright config guarantees only one sidecar is alive at a time.
 *
 * Why per-test (not per-worker): the wizard's "save" step writes a profile
 * to disk. Two tests sharing one sidecar would see each other's state
 * (active profile, on-disk profile list). Per-test isolation keeps each
 * spec deterministic at the cost of a couple of seconds of Python startup.
 *
 * Two fixtures are exported:
 *
 * - `sidecar` — the original auto-spawned handle. Specs that just need a
 *   running sidecar keep using it; `test.use({ sidecarEnv: {...} })` layers
 *   extra environment onto the spawn. MIDI defaults to `off`; device-list
 *   tests explicitly select the list-only `fake` backend.
 * - `sidecarControl` — a manual start/stop controller for specs that need
 *   the sidecar absent at page load (offline shell), killed mid-test
 *   (reconnect journey), or launched with a custom working directory
 *   (isolated captures dir for the library importer).
 *
 * ## Race-free token hand-off
 *
 * The sidecar mints a fresh WS handshake token on EVERY boot and writes it to
 * `RYTM_RAND_WS_TOKEN_FILE` *before* uvicorn binds the port (see
 * `cockpit/__main__.py::main` — `_provision_token()` runs first). The launch
 * helper exploits that ordering: it waits for the token file, hands the token
 * to the spec's `onToken` callback (which injects it into the page), and only
 * then waits for the TCP port. By the time any client dial can succeed, the
 * token is already in place — otherwise a token-less dial would sit in the
 * reject loop (the client withholds the `hello` frame; the server closes the
 * socket at its first-frame deadline with 1008) and burn spec time on
 * redials before the token lands.
 */

import { test as base, expect } from '@playwright/test';
import type { Page } from '@playwright/test';
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
/** Time-budget for the sidecar to mint + persist the WS token at boot. */
const TOKEN_FILE_TIMEOUT_MS = 15_000;
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
 * picks up the in-tree package without an editable install. Exported so
 * specs can locate repo assets (e.g. `captures/*.syx` seed files).
 */
export function resolveRepoRoot(): string {
  return path.resolve(FIXTURE_DIR, '..', '..', '..', '..');
}

/** Sleep helper for the boot-poll loops. */
function delay(ms: number): Promise<void> {
  return new Promise((r) => setTimeout(r, ms));
}

/** Throw (with captured stderr) when the child died before finishing boot. */
function assertChildAlive(
  child: ChildProcessWithoutNullStreams,
  stderr: { text: string },
  stage: string,
): void {
  if (child.exitCode !== null) {
    if (RTMIDI_BOOT_CRASH_SIGNATURE.test(stderr.text)) {
      throw new RetryableSidecarBootError(
        `sidecar died from the transient macOS CoreMIDI (-304) crash while ${stage}` +
          `\nstderr:\n${stderr.text}`,
      );
    }
    throw new Error(
      `sidecar exited with code ${child.exitCode} while ${stage}\nstderr:\n${stderr.text}`,
    );
  }
}

/**
 * Signature of the transient macOS CoreMIDI failure documented in
 * `cockpit/__main__.py::_build_port_enumerator`: python-rtmidi 1.5.8 can
 * abort (or wedge) the whole process from its C++ layer when the OS MIDI
 * client cannot be created — observed here under rapid sidecar churn as
 * `RtMidiError: MidiInCore::initialize ... (-304)` during app startup.
 * No Python `except` can catch it, and the very next launch typically
 * succeeds, so the launch helper treats it as retryable (see below).
 */
const RTMIDI_BOOT_CRASH_SIGNATURE = /RtMidiError|MidiInCore::initialize/;

/** Marker error for a boot failure worth one more spawn attempt. */
class RetryableSidecarBootError extends Error {}

/** Poll the sidecar's TCP port until it accepts a connection or we time out. */
async function waitForSidecarPort(
  child: ChildProcessWithoutNullStreams,
  stderr: { text: string },
  host: string,
  port: number,
  timeoutMs: number,
): Promise<void> {
  const deadline = Date.now() + timeoutMs;
  let lastError: unknown = null;
  while (Date.now() < deadline) {
    assertChildAlive(child, stderr, 'waiting for the WS port');
    // Fail FAST (and retryably) on the transient CoreMIDI churn crash —
    // the process sometimes wedges instead of exiting, which would
    // otherwise burn the whole port timeout inside the test's budget.
    if (RTMIDI_BOOT_CRASH_SIGNATURE.test(stderr.text)) {
      throw new RetryableSidecarBootError(
        `sidecar hit the transient macOS CoreMIDI (-304) crash at boot\nstderr:\n${stderr.text}`,
      );
    }
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
      await delay(SIDECAR_POLL_INTERVAL_MS);
    }
  }
  throw new Error(
    `sidecar did not accept ws://${host}:${port} within ${timeoutMs}ms: ${String(
      lastError,
    )}\nstderr:\n${stderr.text}`,
  );
}

/**
 * Poll the token file until it holds a fresh non-empty token.
 *
 * `previousToken` matters on a restart into the same tmp root: the old
 * launch's file is still on disk, and reading it before the new process
 * overwrites it would hand the spec a token the new server will reject.
 */
async function waitForTokenFile(
  child: ChildProcessWithoutNullStreams,
  stderr: { text: string },
  tokenFile: string,
  previousToken: string | undefined,
  timeoutMs: number,
): Promise<string> {
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    assertChildAlive(child, stderr, 'waiting for the WS token file');
    if (RTMIDI_BOOT_CRASH_SIGNATURE.test(stderr.text)) {
      throw new RetryableSidecarBootError(
        `sidecar hit the transient macOS CoreMIDI (-304) crash at boot\nstderr:\n${stderr.text}`,
      );
    }
    try {
      const token = readFileSync(tokenFile, 'utf8').trim();
      if (token !== '' && token !== previousToken) return token;
    } catch {
      // Not written yet — keep polling.
    }
    await delay(SIDECAR_POLL_INTERVAL_MS);
  }
  throw new Error(
    `sidecar did not write a fresh token to ${tokenFile} within ${timeoutMs}ms` +
      `\nstderr:\n${stderr.text}`,
  );
}

/** Best-effort shutdown — SIGTERM, then SIGKILL after a grace period. */
async function stopSidecar(
  child: ChildProcessWithoutNullStreams,
  signal: NodeJS.Signals = 'SIGTERM',
): Promise<void> {
  if (child.exitCode !== null || child.killed) return;
  child.kill(signal);
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
  readonly tokenFile: string;
  readonly host: string;
  readonly port: number;
  /** stderr accumulator for diagnostic surfacing on failure. */
  readonly stderr: { text: string };
}

export interface SidecarLaunchOptions {
  /** Extra environment layered over the isolation defaults. */
  env?: Record<string, string>;
  /**
   * Working directory for the sidecar process. Defaults to the repo root
   * (so `python -m rytm_randomizer.cockpit` resolves in-tree). Specs that
   * override it (e.g. to isolate the `./captures` importer directory) must
   * also provide `PYTHONPATH` pointing at the repo root via `env`.
   */
  cwd?: string;
  /**
   * Called with the freshly-minted token as soon as the token file lands —
   * i.e. BEFORE the WS port opens. This is the race-free injection point
   * for pages that are already loaded (see the module docstring).
   */
  onToken?: (token: string) => Promise<void> | void;
  /** The previous launch's token when relaunching into the same tmp root. */
  previousToken?: string;
}

/** Boot attempts per launch — retries only the transient CoreMIDI crash. */
const SIDECAR_BOOT_ATTEMPTS = 3;
/** Pause before a retry so the OS MIDI service can settle. */
const SIDECAR_BOOT_RETRY_DELAY_MS = 750;

/**
 * Spawn one sidecar into `tmpRoot` and wait for token + port.
 *
 * Retries (up to {@link SIDECAR_BOOT_ATTEMPTS} total) ONLY when the boot
 * failed with the {@link RTMIDI_BOOT_CRASH_SIGNATURE} — the documented
 * transient macOS CoreMIDI churn failure. Every other boot failure is
 * surfaced immediately: retrying a real regression would just hide it.
 */
async function launchSidecar(
  tmpRoot: string,
  options: SidecarLaunchOptions = {},
): Promise<SidecarHandle> {
  const tokenFile = path.join(tmpRoot, 'cockpit-ws-token');
  let lastCrash: RetryableSidecarBootError | null = null;
  let previousToken = options.previousToken;
  for (let attempt = 1; attempt <= SIDECAR_BOOT_ATTEMPTS; attempt += 1) {
    try {
      return await launchSidecarOnce(tmpRoot, { ...options, previousToken });
    } catch (err) {
      if (!(err instanceof RetryableSidecarBootError)) throw err;
      lastCrash = err;
      // A crashed attempt may have already minted a token; the next attempt
      // must wait for a token that differs from THAT one, or the browser
      // would present a stale token the fresh server rejects at 1008.
      try {
        const staleToken = readFileSync(tokenFile, 'utf8').trim();
        if (staleToken !== '') previousToken = staleToken;
      } catch {
        // No token file yet — the crash beat _provision_token; nothing stale.
      }
      await delay(SIDECAR_BOOT_RETRY_DELAY_MS);
    }
  }
  throw new Error(
    `failed to boot rytm sidecar after ${SIDECAR_BOOT_ATTEMPTS} attempts ` +
      `(persistent CoreMIDI -304 crash): ${String(lastCrash)}`,
  );
}

/** One spawn attempt (see {@link launchSidecar} for the retry policy). */
async function launchSidecarOnce(
  tmpRoot: string,
  options: SidecarLaunchOptions,
): Promise<SidecarHandle> {
  const tokenFile = path.join(tmpRoot, 'cockpit-ws-token');
  const python = resolvePythonBinary();
  const cwd = options.cwd ?? resolveRepoRoot();

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
    // Browser integration tests must never enumerate or open physical MIDI.
    RYTM_RAND_MIDI_BACKEND: 'off',
    // Unbuffer Python stdio so error tracebacks surface promptly in CI logs.
    PYTHONUNBUFFERED: '1',
    ...options.env,
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

  try {
    const token = await waitForTokenFile(
      child,
      stderr,
      tokenFile,
      options.previousToken,
      TOKEN_FILE_TIMEOUT_MS,
    );
    // Token first, port second — see the module docstring for why.
    await options.onToken?.(token);
    await waitForSidecarPort(child, stderr, SIDECAR_HOST, SIDECAR_PORT, SIDECAR_BOOT_TIMEOUT_MS);
    return {
      process: child,
      profilesRoot: tmpRoot,
      token,
      tokenFile,
      host: SIDECAR_HOST,
      port: SIDECAR_PORT,
      stderr,
    };
  } catch (err) {
    await stopSidecar(child);
    // Keep the retryable marker intact so the outer attempt loop can see it.
    if (err instanceof RetryableSidecarBootError) throw err;
    throw new Error(`failed to boot rytm sidecar: ${String(err)}`);
  }
}

/**
 * Register the token for pages that have NOT navigated yet: an init script
 * makes it available to every subsequent load (the pre-goto path).
 */
export async function primeToken(page: Page, token: string): Promise<void> {
  await page.addInitScript(
    ({ storageKey, token: injectedToken }) => {
      window.localStorage.setItem(storageKey, injectedToken);
      window.__RYTM_RAND_WS_TOKEN__ = injectedToken;
    },
    { storageKey: WS_AUTH_TOKEN_STORAGE_KEY, token },
  );
}

/**
 * Inject the token into an ALREADY-LOADED page without reloading it. The WS
 * client resolves the token lazily on every dial (`defaultAuthTokenResolver`
 * reads `window.__RYTM_RAND_WS_TOKEN__` / localStorage at handshake time),
 * so a live injection is picked up by the next reconnect attempt.
 */
export async function injectTokenLive(page: Page, token: string): Promise<void> {
  await page.evaluate(
    ({ storageKey, token: injectedToken }) => {
      window.localStorage.setItem(storageKey, injectedToken);
      window.__RYTM_RAND_WS_TOKEN__ = injectedToken;
    },
    { storageKey: WS_AUTH_TOKEN_STORAGE_KEY, token },
  );
}

/**
 * Manual sidecar controller for specs that need boot/kill/reboot control.
 * All launches share one isolated tmp root (so a restart sees the same
 * on-disk state — that is the point for persistence specs).
 */
export interface SidecarControl {
  readonly tmpRoot: string;
  readonly current: SidecarHandle | null;
  /** Boot a sidecar. Throws if one this controller owns is still running. */
  start(options?: SidecarLaunchOptions): Promise<SidecarHandle>;
  /** Stop the running sidecar (SIGTERM by default; pass 'SIGKILL' to crash it). */
  stop(signal?: NodeJS.Signals): Promise<void>;
}

interface WizardFixtures {
  /** Extra spawn environment for the auto `sidecar` fixture (option). */
  sidecarEnv: Record<string, string>;
  sidecar: SidecarHandle;
  sidecarControl: SidecarControl;
}

/**
 * The exported `test` object. Specs `import { test, expect } from './fixtures/wizard_fixture'`
 * to automatically get a freshly-booted sidecar (and an isolated profiles
 * directory) per test — or a `sidecarControl` for manual lifecycle specs.
 */
export const test = base.extend<WizardFixtures>({
  sidecarEnv: [{}, { option: true }],

  // Per-test sidecar with an isolated profiles dir. The `page` fixture is used
  // to inject the freshly-minted WS token before each spec navigates.
  sidecar: async ({ page, sidecarEnv }, use, testInfo) => {
    const tmpRoot = mkdtempSync(path.join(tmpdir(), 'rytm-wizard-e2e-'));
    let handle: SidecarHandle;
    try {
      handle = await launchSidecar(tmpRoot, {
        env: sidecarEnv,
        onToken: (token) => primeToken(page, token),
      });
    } catch (err) {
      rmSync(tmpRoot, { recursive: true, force: true });
      throw err;
    }

    try {
      await use(handle);
    } finally {
      await stopSidecar(handle.process);
      // Surface child stderr on test failure so triage isn't a guessing game.
      if (testInfo.status !== testInfo.expectedStatus && handle.stderr.text.length > 0) {
        testInfo.attach('sidecar-stderr', {
          body: handle.stderr.text,
          contentType: 'text/plain',
        });
      }
      rmSync(tmpRoot, { recursive: true, force: true });
    }
  },

  // Manual start/stop controller. Does NOT auto-spawn; the spec owns the
  // lifecycle (and the token hand-off, via `primeToken` / `injectTokenLive`).
  // eslint-disable-next-line no-empty-pattern -- Playwright fixtures require destructuring
  sidecarControl: async ({}, use, testInfo) => {
    const tmpRoot = mkdtempSync(path.join(tmpdir(), 'rytm-e2e-ctl-'));
    let current: SidecarHandle | null = null;
    const stderrLog: string[] = [];

    const control: SidecarControl = {
      tmpRoot,
      get current() {
        return current;
      },
      async start(options: SidecarLaunchOptions = {}) {
        if (current !== null && current.process.exitCode === null) {
          throw new Error('sidecarControl.start: a sidecar is already running — stop it first');
        }
        current = await launchSidecar(tmpRoot, options);
        return current;
      },
      async stop(signal: NodeJS.Signals = 'SIGTERM') {
        if (current === null) return;
        await stopSidecar(current.process, signal);
        stderrLog.push(current.stderr.text);
        current = null;
      },
    };

    try {
      await use(control);
    } finally {
      if (current !== null) {
        await stopSidecar(current.process);
        stderrLog.push(current.stderr.text);
      }
      const combined = stderrLog.filter((text) => text.length > 0).join('\n---\n');
      if (testInfo.status !== testInfo.expectedStatus && combined.length > 0) {
        testInfo.attach('sidecar-stderr', { body: combined, contentType: 'text/plain' });
      }
      rmSync(tmpRoot, { recursive: true, force: true });
    }
  },
});

export { expect };
