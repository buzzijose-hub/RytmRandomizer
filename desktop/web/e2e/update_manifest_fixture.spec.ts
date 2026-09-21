/**
 * E2E: the mock-manifest fixture itself and the I3 contract it serves.
 *
 * These specs pass TODAY — they exercise no client behavior, only the
 * fixture and the cross-language contract. They exist because every other
 * update spec's credibility rests on this one: a mock server that quietly
 * served a malformed manifest, or drifted from the I3 fixture the Rust
 * serde tests read, would turn six passing specs into six false greens.
 *
 * Covered:
 *  - the server binds an ephemeral port (never 4317 / 5173 — §9.5);
 *  - the served document satisfies the §4 validation rules the client
 *    applies fail-closed, including the GitHub-releases host pinning;
 *  - the fallback stand-in matches the A5 fixture once it lands (the
 *    dependency guard: this spec is what makes the fallback safe);
 *  - request accounting works, which is the substrate of the freeze
 *    spec's zero-request assertion.
 */

import { existsSync } from 'node:fs';
import { expect, test } from '@playwright/test';

import {
  FALLBACK_MANIFEST,
  I3_MANIFEST_FIXTURE_RELPATH,
  loadContractManifest,
  startMockManifestServer,
  type UpdateManifest,
} from './fixtures/update_manifest';

/** Ports already owned by this suite; the mock server must avoid both. */
const CONTENDED_PORTS = [4317, 5173];

/**
 * §4 validation rules, applied to whatever document the fixture serves.
 * Written as a reusable checker so it runs against BOTH the fallback and
 * the A5 fixture — the two are only interchangeable if both pass.
 */
function assertSpecSection4Conformant(manifest: UpdateManifest): void {
  expect(manifest.schema_version, 'schema_version gates interpretation').toBe(1);
  expect(manifest.version, 'version must be strict SemVer').toMatch(
    /^\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?$/,
  );
  expect(manifest.pub_date, 'pub_date must be an ISO-8601 instant').toMatch(
    /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$/,
  );
  expect(typeof manifest.hardware_revalidation).toBe('boolean');
  expect(Number.isInteger(manifest.rollout_percent)).toBe(true);
  expect(manifest.rollout_percent).toBeGreaterThanOrEqual(0);
  expect(manifest.rollout_percent).toBeLessThanOrEqual(100);
  // §4: advisory-banner-only in v1, but the key must exist so flipping it
  // to blocking later is not a schema migration.
  expect(manifest).toHaveProperty('minimum_version');

  // §4 provenance: present and shaped, never used for eligibility.
  expect(manifest.build.source_sha).toMatch(/^[0-9a-f]{40}$/);
  expect(manifest.build.builder_workflow_sha).toMatch(/^[0-9a-f]{40}$/);
  expect(manifest.build.workflow_run_url).toMatch(/^https:\/\/github\.com\//);

  // §4 host pinning: any non-GitHub-releases URL is refused by the client,
  // so a fixture carrying one would be testing a rejection path by accident.
  const targets = Object.keys(manifest.platforms);
  expect(targets.length, 'at least one platform target').toBeGreaterThan(0);
  for (const target of targets) {
    const platform = manifest.platforms[target];
    expect(platform, `platform entry for ${target}`).toBeTruthy();
    expect(platform!.url, `${target} url must be a GitHub release download`).toMatch(
      /^https:\/\/github\.com\/[^/]+\/[^/]+\/releases\/download\//,
    );
    expect(platform!.signature.length, `${target} signature must be non-empty`).toBeGreaterThan(0);
  }
}

test.describe('mock manifest fixture (I3 contract)', () => {
  test('binds an ephemeral port, not a contended one', async () => {
    const server = await startMockManifestServer();
    try {
      const port = Number(new URL(server.origin).port);
      expect(port).toBeGreaterThan(0);
      expect(CONTENDED_PORTS, 'must not reuse the sidecar/Vite ports').not.toContain(port);
      expect(new URL(server.origin).hostname, 'loopback only').toBe('127.0.0.1');
    } finally {
      await server.close();
    }
  });

  test('serves a spec §4-conformant manifest and counts requests', async ({ request }) => {
    const server = await startMockManifestServer();
    try {
      expect(server.manifestRequests()).toHaveLength(0);

      const response = await request.get(server.manifestUrl);
      expect(response.status()).toBe(200);
      assertSpecSection4Conformant((await response.json()) as UpdateManifest);

      // Request accounting — the freeze spec's zero-request claim is only
      // meaningful if a real request would have been counted.
      expect(server.manifestRequests()).toHaveLength(1);
      expect(server.pingRequests()).toHaveLength(0);

      // §6 ping asset is served and counted independently of the manifest.
      const ping = await request.get(`${server.origin}/beacon-1.34.0-darwin-aarch64.txt`);
      expect(ping.status()).toBe(200);
      expect(server.pingRequests()).toHaveLength(1);
      expect(server.manifestRequests()).toHaveLength(1);
    } finally {
      await server.close();
    }
  });

  test('the fallback stand-in is itself §4-conformant', () => {
    assertSpecSection4Conformant(FALLBACK_MANIFEST);
  });

  test('the A5 fixture, once present, agrees with the fallback shape', () => {
    const { manifest, usedFixture, fixturePath } = loadContractManifest();
    if (!usedFixture) {
      // Not a skip: the fallback is what the suite is running against, and
      // asserting its conformance here keeps that state honest and visible.
      expect(
        existsSync(fixturePath),
        `I3 fixture ${I3_MANIFEST_FIXTURE_RELPATH} not present yet — specs run against the fallback`,
      ).toBe(false);
      return;
    }
    // Once A5 lands, the real fixture must be conformant AND carry the same
    // key set as the fallback, so swapping sources cannot change behavior.
    assertSpecSection4Conformant(manifest);
    expect(Object.keys(manifest).sort()).toEqual(Object.keys(FALLBACK_MANIFEST).sort());
    expect(Object.keys(manifest.platforms).sort()).toEqual(
      Object.keys(FALLBACK_MANIFEST.platforms).sort(),
    );
  });

  test('overrides let a spec force the §4 fail-closed paths', async ({ request }) => {
    const server = await startMockManifestServer();
    try {
      server.setManifestOverride({ status: 500, body: '' });
      expect((await request.get(server.manifestUrl)).status()).toBe(500);

      // "Manifest not understood" (§4) — served as a parseable document with
      // an unknown schema_version, which is a DIFFERENT path from a 500 and
      // must be reachable by the fixture or the client rule is untestable.
      server.setManifestOverride({
        status: 200,
        body: JSON.stringify({ ...FALLBACK_MANIFEST, schema_version: 99 }),
      });
      const unknown = await request.get(server.manifestUrl);
      expect(unknown.status()).toBe(200);
      expect(((await unknown.json()) as UpdateManifest).schema_version).toBe(99);

      server.setManifestOverride(null);
      expect((await request.get(server.manifestUrl)).status()).toBe(200);
    } finally {
      await server.close();
    }
  });

  test('a hang override black-holes the request and close() still returns', async ({ request }) => {
    // The ping-independence spec's hardest case depends on this mechanism,
    // and it is the one override whose failure mode is silence: a `hang`
    // that quietly answered would make that spec pass while proving
    // nothing. So the hang is exercised directly here, where a regression
    // surfaces as a fixture failure rather than as a false green upstream.
    const server = await startMockManifestServer();
    let closed = false;
    try {
      server.setPingOverride({ hang: true });

      // The request must NOT settle. Racing it against a short timer is the
      // only way to assert "never answers" in finite time; the timer must
      // win.
      const pinged = request
        .get(`${server.origin}/beacon-1.34.0-darwin-aarch64.txt`, { timeout: 2_000 })
        .then(() => 'answered' as const)
        .catch(() => 'aborted' as const);
      const timer = new Promise<'still-hanging'>((resolve) =>
        setTimeout(() => resolve('still-hanging'), 750),
      );
      expect(await Promise.race([pinged, timer])).toBe('still-hanging');
      expect(server.pingRequests(), 'a hung request is still a counted request').toHaveLength(1);

      // The manifest route stays healthy while the ping hangs — that
      // independence is the whole point of the §6 claim.
      expect((await request.get(server.manifestUrl)).status()).toBe(200);

      // close() must destroy the parked socket rather than waiting on it.
      // Without that, teardown deadlocks and the failure presents as the
      // entire suite timing out, miles from the cause.
      await server.close();
      closed = true;
      await pinged; // settles (aborted) once the socket is destroyed
    } finally {
      if (!closed) await server.close();
    }
  });
});
