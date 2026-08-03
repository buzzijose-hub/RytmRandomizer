/**
 * E2E: library management with NO device (WS-C spec 5).
 *
 * The sound library never needed hardware: records are on-disk JSON, and the
 * captures importer reads real `.syx` dumps from the sidecar's boot-time
 * captures directory (`Path.cwd() / "captures"` — see
 * `rytm_randomizer/cockpit/library/store.py::default_captures_dir`).
 *
 * ## Seeding strategy
 *
 * The importer's captures dir is the sidecar's CWD, so this spec launches
 * the sidecar from an isolated working dir inside the fixture tmp root
 * (with `PYTHONPATH` pointing at the repo so `-m rytm_randomizer.cockpit`
 * still resolves) and seeds `<workdir>/captures` with two REAL hardware
 * captures from the repo's `captures/` directory. Both seeds carry the same
 * kit payload (fingerprint `4203297a5cb48b36`, kit "KIT 1") — deliberately,
 * so the import result also pins the dedupe behavior: 1 imported, 1 skipped.
 *
 * `HOME` is pointed at the tmp root too: on macOS `default_library_dir()`
 * resolves under `~/Library/Application Support`, which `XDG_CONFIG_HOME`
 * does NOT redirect — without the HOME override this spec would write into
 * the operator's real library.
 *
 * Persistence: the record JSON lives in the tmp root and must survive a
 * sidecar restart (list + tags re-served by the NEW process). The restart
 * mints a fresh WS token, which the spec re-injects live (same pattern as
 * reconnect_journey.spec.ts).
 *
 * Console-error allowlist: WS dial failures during the deliberate restart
 * window only.
 */

import { copyFileSync, mkdirSync, readdirSync, statSync } from 'node:fs';
import * as path from 'node:path';

import { trackConsoleErrors, WS_DIAL_FAILURE } from './fixtures/console_guard';
import {
  expect,
  injectTokenLive,
  primeToken,
  resolveRepoRoot,
  test,
} from './fixtures/wizard_fixture';

/** The two real captures seeded into the isolated captures dir. */
const SEED_CAPTURES = [
  '20260528-222852-analog-rytm-current-kit-reassembled.syx',
  '20260528-224956-analog-rytm-current-kit-reassembled.syx',
];

/** Decoded identity of the seeded kit payload (both seeds share it). */
const SEEDED_KIT_NAME = 'KIT 1';
const SEEDED_RECORD_ID = '4203297a5cb48b36';

/** Recursively find `library/*.json` record files under `root`. */
function findLibraryRecordFiles(root: string): string[] {
  const found: string[] = [];
  const walk = (dir: string): void => {
    for (const entry of readdirSync(dir)) {
      const full = path.join(dir, entry);
      const info = statSync(full);
      if (info.isDirectory()) {
        walk(full);
      } else if (entry.endsWith('.json') && path.basename(dir) === 'library') {
        found.push(full);
      }
    }
  };
  walk(root);
  return found;
}

test.describe('library management without a device', () => {
  test('import seeded captures, search, tag — and persist across a sidecar restart', async ({
    page,
    sidecarControl,
  }) => {
    test.setTimeout(120_000);
    const consoleGuard = trackConsoleErrors(page, [WS_DIAL_FAILURE]);

    // ---- Seed the isolated captures dir BEFORE the sidecar boots ----------
    const repoRoot = resolveRepoRoot();
    const workDir = path.join(sidecarControl.tmpRoot, 'work');
    const capturesDir = path.join(workDir, 'captures');
    mkdirSync(capturesDir, { recursive: true });
    for (const name of SEED_CAPTURES) {
      copyFileSync(path.join(repoRoot, 'captures', name), path.join(capturesDir, name));
    }
    const sidecarEnv = {
      RYTM_RAND_MIDI_BACKEND: 'off',
      // macOS: default_library_dir() lives under ~/Library/Application
      // Support and ignores XDG — point HOME at the tmp root so the library
      // (and profiles) stay isolated on every platform.
      HOME: sidecarControl.tmpRoot,
      // cwd is the isolated workdir, so the in-tree package needs a path.
      PYTHONPATH: repoRoot,
    };

    const first = await sidecarControl.start({
      env: sidecarEnv,
      cwd: workDir,
      onToken: (token) => primeToken(page, token),
    });

    await page.goto('/');
    await expect(page.getByTestId('cockpit-root')).toBeVisible({ timeout: 10_000 });
    const library = page.getByTestId('library-panel');

    // ---- Empty store first ------------------------------------------------
    await library.getByTestId('library-load').click();
    await expect(library).toContainText('library loaded');
    await expect(library.getByText('0 record(s)')).toBeVisible();

    // ---- Import the seeded captures ---------------------------------------
    // Both seed files carry the SAME payload → the importer dedupes:
    // 1 imported, 1 skipped, 0 failed.
    await library.getByTestId('library-import').click();
    await expect(library).toContainText('imported 1, skipped 1, failed 0');
    await library.getByTestId('library-load').click();
    await expect(library.getByText('1 record(s)')).toBeVisible();
    await expect(library).toContainText(SEEDED_KIT_NAME);
    await expect(library).toContainText('analog_rytm_mk2');
    await expect(library).toContainText(SEEDED_RECORD_ID);

    // ---- Search: hit, then miss -------------------------------------------
    await library.getByTestId('library-search-input').fill('kit');
    await library.getByTestId('library-search-submit').click();
    await expect(library).toContainText('search complete: kit');
    await expect(library.getByText('1 record(s)')).toBeVisible();
    await library.getByTestId('library-search-input').fill('zz-no-such-kit');
    await library.getByTestId('library-search-submit').click();
    await expect(library).toContainText('search complete: zz-no-such-kit');
    await expect(library.getByText('0 record(s)')).toBeVisible();

    // ---- Tag the record, then find it by tag ------------------------------
    await library.getByTestId('library-load').click();
    await library.getByTestId('library-tag-record').selectOption(SEEDED_RECORD_ID);
    await library.getByTestId('library-tags-input').fill('e2e, techno');
    await library.getByTestId('library-tags-save').click();
    await expect(library).toContainText(`tags saved for ${SEEDED_RECORD_ID}`);
    await library.getByTestId('library-search-input').fill('techno');
    await library.getByTestId('library-search-submit').click();
    await expect(library.getByText('1 record(s)')).toBeVisible();
    await expect(library).toContainText('e2e, techno');

    // ---- The record is on disk inside the ISOLATED tmp root ---------------
    const recordFiles = findLibraryRecordFiles(sidecarControl.tmpRoot);
    expect(recordFiles).toHaveLength(1);
    expect(path.basename(recordFiles[0]!)).toBe(`${SEEDED_RECORD_ID}.json`);

    // ---- Restart the sidecar: the library must survive --------------------
    await sidecarControl.stop();
    await sidecarControl.start({
      env: sidecarEnv,
      cwd: workDir,
      previousToken: first.token,
      onToken: (token) => injectTokenLive(page, token),
    });
    await expect(
      page.getByTestId('safety-rail').getByText('Connected', { exact: true }),
    ).toBeVisible({ timeout: 30_000 });

    await library.getByTestId('library-load').click();
    await expect(library.getByText('1 record(s)')).toBeVisible();
    await expect(library).toContainText(SEEDED_KIT_NAME);
    await expect(library).toContainText('e2e, techno');

    consoleGuard.assertClean();
  });
});
