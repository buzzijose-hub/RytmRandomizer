/**
 * Schema fixtures and an ephemeral HTTP server for manifest contract tests.
 * Native acceptance uses native_update_fixture for real shell traffic,
 * signature verification, isolated configuration and journal evidence.
 */

import { readFileSync, existsSync } from 'node:fs';
import * as http from 'node:http';
import * as path from 'node:path';
import { fileURLToPath } from 'node:url';

const FIXTURE_DIR = path.dirname(fileURLToPath(import.meta.url));

/**
 * Repo-root-relative path of the I3 contract fixture (authored by agent A5
 * on the PR-A track, per the plan's dispatch matrix). When present it is the
 * single source of truth shared by the Python validator, the Rust serde
 * tests, and these specs — R2's "one truth, three languages". When absent
 * (PR-C is developed in parallel with PR-A, and consumes I3 as a frozen
 * contract rather than as A5's output) {@link FALLBACK_MANIFEST} stands in.
 *
 * The fallback is spec-§4-conformant, and `update_manifest_fixture.spec.ts`
 * asserts the two agree once A5's file lands, so the stand-in can never
 * silently drift from the contract it is standing in for. Deleting the
 * fallback once A5 merges is NOT the follow-up: it is what keeps this suite
 * runnable in a checkout where PR-A has not landed.
 */
export const I3_MANIFEST_FIXTURE_RELPATH =
  'tests/fixtures/update_manifest/manifest.v1.json';

/** Repo root, 4 levels up from `desktop/web/e2e/fixtures`. */
export function resolveRepoRootForManifest(): string {
  return path.resolve(FIXTURE_DIR, '..', '..', '..', '..');
}

/** A single platform entry in the §4 manifest. */
export interface ManifestPlatform {
  signature: string;
  url: string;
}

/** Build provenance (§4: informational, never gates eligibility). */
export interface ManifestBuild {
  source_sha: string;
  workflow_run_url: string;
  builder_workflow_sha: string;
}

/** The §4 manifest schema (v1). */
export interface UpdateManifest {
  schema_version: number;
  channel: string;
  version: string;
  pub_date: string;
  notes: string;
  hardware_revalidation: boolean;
  rollout_percent: number;
  minimum_version: string | null;
  build: ManifestBuild;
  platforms: Record<string, ManifestPlatform>;
}

/**
 * Spec-§4-conformant stand-in used until the A5 fixture lands.
 *
 * Kept byte-shaped like the spec's example (same key order, same platform
 * set, GitHub-releases URLs so the §4 host-pinning rule passes) so that
 * swapping in the real file changes behavior nowhere.
 */
export const FALLBACK_MANIFEST: UpdateManifest = {
  schema_version: 1,
  channel: 'stable',
  version: '1.35.1',
  pub_date: '2026-09-14T00:00:00Z',
  notes: 'markdown excerpt of the generated changelog',
  hardware_revalidation: false,
  rollout_percent: 100,
  minimum_version: null,
  build: {
    source_sha: '0'.repeat(40),
    workflow_run_url: 'https://github.com/buzzijose-hub/RytmRandomizer/actions/runs/1',
    builder_workflow_sha: '1'.repeat(40),
  },
  platforms: {
    'darwin-aarch64': {
      signature: 'dW50cnVzdGVkIGNvbW1lbnQ6IGZpeHR1cmU=',
      url: 'https://github.com/buzzijose-hub/RytmRandomizer/releases/download/v1.35.1/RytmRandomizer.app.tar.gz',
    },
    'darwin-x86_64': {
      signature: 'dW50cnVzdGVkIGNvbW1lbnQ6IGZpeHR1cmU=',
      url: 'https://github.com/buzzijose-hub/RytmRandomizer/releases/download/v1.35.1/RytmRandomizer-x64.app.tar.gz',
    },
    'windows-x86_64': {
      signature: 'dW50cnVzdGVkIGNvbW1lbnQ6IGZpeHR1cmU=',
      url: 'https://github.com/buzzijose-hub/RytmRandomizer/releases/download/v1.35.1/RytmRandomizer-setup.nsis.zip',
    },
    'linux-x86_64': {
      signature: 'dW50cnVzdGVkIGNvbW1lbnQ6IGZpeHR1cmU=',
      url: 'https://github.com/buzzijose-hub/RytmRandomizer/releases/download/v1.35.1/RytmRandomizer.AppImage.tar.gz',
    },
  },
};

/**
 * Load the I3 contract manifest, falling back to {@link FALLBACK_MANIFEST}.
 * `usedFixture` tells callers which source won, so a spec can report the
 * dependency state instead of silently testing the stand-in.
 */
export function loadContractManifest(): {
  manifest: UpdateManifest;
  usedFixture: boolean;
  fixturePath: string;
} {
  const fixturePath = path.join(resolveRepoRootForManifest(), I3_MANIFEST_FIXTURE_RELPATH);
  if (existsSync(fixturePath)) {
    const parsed = JSON.parse(readFileSync(fixturePath, 'utf8')) as UpdateManifest;
    return { manifest: parsed, usedFixture: true, fixturePath };
  }
  return {
    manifest: structuredClone(FALLBACK_MANIFEST),
    usedFixture: false,
    fixturePath,
  };
}

/** One recorded inbound request against the mock server. */
export interface RecordedRequest {
  readonly method: string;
  readonly url: string;
  readonly at: number;
}

/** Per-response override so a spec can force a failure path. */
export interface ResponseOverride {
  /** HTTP status to answer with (default 200). */
  status?: number;
  /** Raw body to answer with; bypasses JSON serialization of the manifest. */
  body?: string;
  /**
   * Accept the connection and then never answer — a black-holed request.
   *
   * This has to live in the SERVER, not in `page.route(...)`. Playwright's
   * route interception only sees requests issued by the browser context,
   * and the §6 ping is issued by the Rust shell: a browser-scoped hang
   * would leave the shell's real GET answered promptly, so the test would
   * pass without ever exercising the stall it claims to catch. Hanging
   * here black-holes the request whichever process made it, which is the
   * only version of this test that can fail for the right reason.
   *
   * The socket is held open until {@link MockManifestServer.close}, which
   * destroys every parked response so the server can actually shut down.
   */
  hang?: boolean;
}

export interface MockManifestServer {
  /** Base origin, e.g. `http://127.0.0.1:53124` (ephemeral port). */
  readonly origin: string;
  /** Full URL for the stable channel manifest. */
  readonly manifestUrl: string;
  /** Every request the server saw, in arrival order. */
  readonly requests: readonly RecordedRequest[];
  /** Only the manifest-path requests (the §8 freeze-silence assertion). */
  manifestRequests(): readonly RecordedRequest[];
  /** Only the §6 ping-asset requests (ping-independence assertion). */
  pingRequests(): readonly RecordedRequest[];
  /** Replace the served manifest (rollout steps, newer version, banner flag). */
  setManifest(manifest: UpdateManifest): void;
  /** The manifest currently being served. */
  currentManifest(): UpdateManifest;
  /** Force the next manifest responses to fail / return garbage. */
  setManifestOverride(override: ResponseOverride | null): void;
  /** Force the §6 ping asset to fail (ping-independence spec). */
  setPingOverride(override: ResponseOverride | null): void;
  /** Shut the server down. */
  close(): Promise<void>;
}

/** Path the manifest is served from (channel-shaped, per spec §3). */
const MANIFEST_PATH = '/stable.json';
/** Ping assets live under this prefix (`beacon-<version>-<target>.txt`, §6). */
const PING_PREFIX = '/beacon-';

/**
 * Start the mock manifest server on an ephemeral port.
 *
 * Binds 127.0.0.1 explicitly (never 0.0.0.0) so a test fixture never
 * listens on a routable interface, and port 0 so the OS assigns a free
 * port — see the module docstring on port discipline.
 */
export async function startMockManifestServer(
  initial: UpdateManifest = loadContractManifest().manifest,
): Promise<MockManifestServer> {
  const requests: RecordedRequest[] = [];
  let manifest: UpdateManifest = structuredClone(initial);
  let manifestOverride: ResponseOverride | null = null;
  let pingOverride: ResponseOverride | null = null;
  /** Responses parked by a `hang` override; released only at close(). */
  const parked = new Set<http.ServerResponse>();

  /**
   * Apply an override, returning true when it fully handled the response.
   * Shared by both routes so a `hang` on the manifest behaves exactly like
   * a `hang` on the ping — the asymmetry would otherwise be a latent trap.
   */
  function applyOverride(
    override: ResponseOverride,
    res: http.ServerResponse,
    contentType: string,
    defaultStatus: number,
  ): void {
    if (override.hang === true) {
      // Accept and never answer. Tracked so close() can destroy the socket;
      // otherwise `server.close()` waits forever on the open connection and
      // the fixture teardown hangs the whole suite.
      parked.add(res);
      res.on('close', () => parked.delete(res));
      return;
    }
    res.writeHead(override.status ?? defaultStatus, { 'content-type': contentType });
    res.end(override.body ?? '');
  }

  const server = http.createServer((req, res) => {
    const url = req.url ?? '/';
    requests.push({ method: req.method ?? 'GET', url, at: Date.now() });

    if (url.startsWith(PING_PREFIX)) {
      if (pingOverride !== null) {
        applyOverride(pingOverride, res, 'text/plain', 500);
        return;
      }
      // §6: one-byte asset. Its download_count is the fleet counter.
      res.writeHead(200, { 'content-type': 'text/plain' });
      res.end('.');
      return;
    }

    if (url.startsWith(MANIFEST_PATH)) {
      if (manifestOverride !== null) {
        applyOverride(manifestOverride, res, 'application/json', 500);
        return;
      }
      res.writeHead(200, { 'content-type': 'application/json' });
      res.end(JSON.stringify(manifest));
      return;
    }

    res.writeHead(404, { 'content-type': 'text/plain' });
    res.end('not found');
  });

  await new Promise<void>((resolve, reject) => {
    server.once('error', reject);
    server.listen(0, '127.0.0.1', resolve);
  });

  const address = server.address();
  if (address === null || typeof address === 'string') {
    server.close();
    throw new Error('mock manifest server did not bind an ephemeral TCP port');
  }
  const origin = `http://127.0.0.1:${address.port}`;

  return {
    origin,
    manifestUrl: `${origin}${MANIFEST_PATH}`,
    requests,
    manifestRequests: () => requests.filter((r) => r.url.startsWith(MANIFEST_PATH)),
    pingRequests: () => requests.filter((r) => r.url.startsWith(PING_PREFIX)),
    setManifest(next: UpdateManifest): void {
      manifest = structuredClone(next);
    },
    currentManifest: () => structuredClone(manifest),
    setManifestOverride(override: ResponseOverride | null): void {
      manifestOverride = override;
    },
    setPingOverride(override: ResponseOverride | null): void {
      pingOverride = override;
    },
    close(): Promise<void> {
      // Release every parked (hung) response first: `server.close()` refuses
      // to finish while a connection is open, so a `hang` override without
      // this would deadlock the fixture teardown rather than fail a test.
      for (const res of parked) res.destroy();
      parked.clear();
      return new Promise<void>((resolve) => server.close(() => resolve()));
    },
  };
}
