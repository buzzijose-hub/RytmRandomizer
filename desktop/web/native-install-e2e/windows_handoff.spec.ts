import { expect, test } from '@playwright/test';

import { runNativeScenario } from '../e2e/fixtures/native_update_fixture';

for (const choice of ['quit', 'now'] as const) {
  // Playwright requires fixture destructuring even when all work is native.
  // eslint-disable-next-line no-empty-pattern
  test(`real Windows installer handoff: ${choice === 'now' ? 'install_now' : 'install_on_quit'}`, async ({}, testInfo) => {
    const evidence = await runNativeScenario(`install_handoff_${choice}`);
    expect(evidence.result.passed).toBe(true);
    expect(evidence.handoff).toBeDefined();
    expect(evidence.handoff?.parent_exit_code).toBe(0);
    expect(evidence.handoff?.sidecar_stopped_before_install).toBe(true);
    expect(evidence.handoff?.installer_runs).toBe(1);
    expect(evidence.handoff?.restart_runs).toBe(choice === 'now' ? 1 : 0);
    expect(evidence.handoff?.replacement_sha256).not.toBe(evidence.handoff?.original_shell_sha256);
    expect(evidence.terminal).toHaveLength(1);
    expect(evidence.terminal[0]?.sha256).toBe(evidence.handoff?.artifact_sha256);
    expect(evidence.terminal[0]?.choice).toBe(choice === 'now' ? 'install_now' : 'install_on_quit');
    const events = evidence.journal.map((row) => row.event);
    expect(events).toContain('download_ok');
    expect(events).toContain('consent_granted');
    expect(events).toContain('install_started');
    expect(events.indexOf('consent_granted')).toBeLessThan(events.indexOf('install_started'));
    expect(evidence.requests.filter((url) => url === '/artifact.bin')).toHaveLength(1);
    await testInfo.attach('actual-windows-handoff', { body: JSON.stringify(evidence.handoff, null, 2), contentType: 'application/json' });
  });
}
