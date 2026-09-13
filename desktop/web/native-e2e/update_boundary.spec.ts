import { expect, test } from '@playwright/test';

import { runNativeScenario, SIGNED_BYTES_SHA256 } from '../e2e/fixtures/native_update_fixture';

const scenarios = [
  'staged_ui', 'journal_ui', 'hydrate_reload', 'equal_version',
  'hardware_warning', 'ordinary_release', 'frozen_start', 'frozen_manual',
  'rollout_in', 'rollout_out', 'rollout_expands',
  'beacon_off', 'beacon_error', 'beacon_absent', 'beacon_hang',
  'check_failure', 'manifest_invalid', 'signature_failure', 'signature_malformed', 'wrong_key', 'missing_key',
  'consent_stale', 'consent_quit', 'consent_now', 'consent_crash', 'install_failure',
  'skip_reload', 'skip_newer', 'backend_restart', 'inflight_checks',
  'manifest_cancel', 'download_cancel',
] as const;

for (const scenario of scenarios) {
  test(`real native updater: ${scenario}`, async () => {
    const evidence = await runNativeScenario(scenario);
    expect(evidence.result.passed).toBe(true);
    expect(evidence.result.detail).toMatch(/native\/DOM assertions/);
    const artifactRequests = evidence.requests.filter((url) => url === '/artifact.bin');
    const events = evidence.journal.map((row) => row.event);

    if (scenario.startsWith('frozen_')) {
      expect(evidence.requests).toEqual([]);
    } else if (['equal_version', 'rollout_out', 'check_failure', 'manifest_invalid', 'missing_key', 'manifest_cancel'].includes(scenario)) {
      expect(artifactRequests).toEqual([]);
      expect(events).not.toContain('download_ok');
    } else {
      expect(artifactRequests.length).toBeGreaterThan(0);
    }
    if (scenario === 'beacon_off') expect(evidence.requests).not.toContain('/beacon.txt');
    if (['beacon_error', 'beacon_absent', 'beacon_hang'].includes(scenario)) {
      expect(evidence.requests).toContain('/beacon.txt');
      expect(events).toContain('download_ok');
      expect(events).not.toContain('ping_ok');
    }
    if (scenario === 'inflight_checks') {
      expect(evidence.requests.filter((url) => url === '/stable.json').length).toBeLessThanOrEqual(3);
    }
    if (scenario === 'rollout_out') {
      expect(evidence.journal.find((row) => row.event === 'bucket_excluded')?.detail).toMatchObject({ bucket: 10, rollout_percent: 10 });
    }
    if (['consent_quit', 'consent_now', 'install_failure'].includes(scenario)) {
      const installs = evidence.terminal.filter((event) => event.event === 'install');
      expect(installs).toHaveLength(1);
      expect(installs[0]?.sha256).toBe(SIGNED_BYTES_SHA256);
      expect(events).toContain('consent_granted');
      expect(events).toContain('install_started');
      expect(events).toContain(scenario === 'install_failure' ? 'install_failed' : 'install_ok');
    } else {
      expect(evidence.terminal).toEqual([]);
      expect(events).not.toContain('install_started');
    }
    // Raw journal evidence must never contain credentials, fixture paths or IDs.
    const journal = JSON.stringify(evidence.journal);
    expect(journal).not.toContain('00000000-0000-4000-8000');
    expect(journal).not.toContain('rytm-native-update-');
    expect(journal).not.toMatch(/"(?:token|arm_secret|install_id)"/);
  });
}
