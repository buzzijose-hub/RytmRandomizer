/** Runs INSIDE real WebView2. All update observations/actions cross real Tauri IPC. */
import { invoke } from '@tauri-apps/api/core';

import { useCockpitStore } from '../../src/state';
import {
  confirmUpdateChoiceOnShell, parseUpdateSnapshot, requestUpdateCheck,
  subscribeUpdateState, type UpdateSnapshot,
} from '../../src/updateProtocol';
import { WS_SUBPROTOCOL } from '../../src/ws/client';

interface Terminal { event: string; version: string; choice: string; sha256: string }
interface Stats { terminal: Terminal[] }
let assertions = 0;

function check(condition: unknown, label: string): asserts condition {
  assertions += 1;
  if (!condition) throw new Error(label);
}

async function until(label: string, predicate: () => boolean | Promise<boolean>): Promise<void> {
  const deadline = Date.now() + 25_000;
  while (Date.now() < deadline) {
    if (await predicate()) return;
    await new Promise((resolve) => setTimeout(resolve, 75));
  }
  throw new Error(`Timed out: ${label}`);
}

async function snapshot(): Promise<UpdateSnapshot> {
  const value = parseUpdateSnapshot(await invoke('update_snapshot'));
  check(value !== null, 'native snapshot matches production parser');
  return value;
}

const stats = (): Promise<Stats> => invoke('control', { action: 'stats' });
const nativeControl = (action: string): Promise<Stats> => invoke('control', { action });
const element = (id: string): HTMLElement | null => document.querySelector(`[data-testid="${id}"]`);

async function connected(): Promise<void> {
  await until('actual sidecar authenticated session', () =>
    useCockpitStore.getState().connectionStatus === 'connected' && useCockpitStore.getState().sessionStatus !== null);
  check(useCockpitStore.getState().sessionStatus?.armed === false, 'passive sidecar stays disarmed');
}

async function staged(): Promise<void> {
  await until('verified native stage', async () => (await snapshot()).state.state === 'staged');
  await until('native stage reflected in React chip', () => element('update-chip')?.textContent?.includes('1.35.1') === true);
}

async function clickConfirm(choice: string, waitForConsent = true): Promise<void> {
  await connected();
  const radio = document.querySelector<HTMLInputElement>(`input[name="update-consent"][value="${choice}"]`);
  check(radio !== null && !radio.disabled, 'consent radio is usable after authentication');
  radio.click();
  await until('chosen radio', () => radio.checked);
  const button = element('update-confirm');
  check(button instanceof HTMLButtonElement && !button.disabled, 'native consent button enabled');
  button.click();
  if (waitForConsent) await until('consent reached native journal', async () => (await snapshot()).journal.some((row) => row.event === 'consent_granted'));
}

async function staleHandshakeRejected(token: string): Promise<boolean> {
  const port = window.localStorage.getItem('rytm-rand-ws-port');
  return new Promise((resolve) => {
    const ws = new WebSocket(`ws://127.0.0.1:${port}/ws`, WS_SUBPROTOCOL);
    const deadline = setTimeout(() => { ws.close(); resolve(false); }, 5000);
    ws.onopen = () => ws.send(JSON.stringify({ type: 'hello', token }));
    ws.onmessage = (message) => {
      const payload = JSON.parse(String(message.data)) as { code?: string };
      if (payload.code === 'auth_failed') { clearTimeout(deadline); ws.close(); resolve(true); }
    };
    ws.onclose = (event) => { clearTimeout(deadline); resolve(event.code === 1008); };
  });
}

export async function run(scenario: string, origin: string): Promise<void> {
  let eventCount = 0;
  let hydrated: UpdateSnapshot | null = null;
  const stop = subscribeUpdateState(() => { eventCount += 1; }, (value) => { hydrated = value; });
  try {
    await until('React cockpit mounted', () => element('cockpit-root') !== null);
    await until('real invoke/listen snapshot hydration', () => hydrated !== null);
    check((await stats()).terminal.length === 0, 'mount cannot install or restart');

    if (scenario.startsWith('frozen_')) {
      check((await snapshot()).frozen, 'native process reports frozen');
      check(await requestUpdateCheck() === false, 'frozen native command refuses check');
      check(element('update-chip') === null, 'frozen has no chip');
      await connected();
      const button = element('update-check-now');
      check(button instanceof HTMLButtonElement && button.disabled, 'frozen manual control is disabled');
    } else if (scenario === 'manifest_cancel' || scenario === 'download_cancel') {
      const pending = scenario === 'manifest_cancel' ? 'checking' : 'downloading';
      await until('native operation is pending', async () => (await snapshot()).state.state === pending);
      await nativeControl('shutdown');
      check((await stats()).terminal.length === 0, 'shutdown with pending network cannot install');
      check(!(await snapshot()).journal.some((row) => row.event === 'download_ok'), 'cancelled bytes cannot stage');
    } else if (scenario === 'missing_key') {
      await until('native check-only discovery', async () => (await snapshot()).state.error_code === 'signature_key_missing');
      const state = await snapshot();
      check(state.state.version === '1.35.1' && state.state.notes.includes('Native signed fixture'), 'keyless discovery retains release and notes');
      check(!state.journal.some((row) => row.event === 'download_started' || row.event === 'signature_rejected'), 'missing key does not claim bad signature or start download');
      check(await confirmUpdateChoiceOnShell('1.35.1', 'install_now') === false, 'check-only discovery cannot obtain install consent');
      await until('keyless discovery visible in React', () => element('update-panel')?.textContent?.includes('signing key') === true);
    } else if (scenario === 'skip_reload' && window.sessionStorage.getItem('native-skip_reload') === 'reloaded') {
      await until('skip survives webview reload', async () => (await snapshot()).state.state === 'skipped');
      check(element('update-chip') === null, 'reload cannot resurrect skipped chip');
      check((await snapshot()).journal.some((row) => row.event === 'skip_recorded'), 'skip is evidenced in native journal');
    } else if (['equal_version', 'rollout_out', 'rollout_expands'].includes(scenario)) {
      await until('native up-to-date state', async () => (await snapshot()).state.state === 'up_to_date');
      check(element('update-chip') === null, 'no chip for equal/excluded release');
      if (scenario.startsWith('rollout_')) check((await snapshot()).journal.some((row) => row.event === 'bucket_excluded'), 'native rollout exclusion journalled');
      if (scenario === 'rollout_expands') {
        await fetch(`${origin}/control?rollout=100`);
        check(await requestUpdateCheck(), 'manual rollout recheck accepted');
        await staged();
      }
    } else if (['check_failure', 'manifest_invalid', 'signature_failure', 'signature_malformed', 'wrong_key'].includes(scenario)) {
      await until('native refusal', async () => (await snapshot()).state.state === 'failed');
      const state = await snapshot();
      check(element('update-chip') === null, 'failed verification cannot present staged chip');
      check(await confirmUpdateChoiceOnShell('1.35.1', 'install_now') === false, 'refused artifact cannot obtain consent');
      const expected = scenario === 'check_failure' ? 'check_failed' : scenario === 'manifest_invalid' ? 'manifest_rejected' : 'signature_rejected';
      check(state.journal.some((row) => row.event === expected), 'typed refusal reaches native journal');
      await until('journal reaches actual React activity', () => element('update-activity-list')?.textContent?.includes(expected) === true);
    } else {
      if (scenario === 'inflight_checks') {
        await Promise.all(Array.from({ length: 12 }, () => requestUpdateCheck()));
      }
      await staged();
      const original = await snapshot();
      check(original.journal.some((row) => row.event === 'download_ok'), 'stage backed by signed native download');
      if (['staged_ui', 'journal_ui', 'beacon_error', 'beacon_absent'].includes(scenario)) {
        const expectedPing = scenario.startsWith('beacon_') ? 'ping_failed' : 'ping_ok';
        await until('real beacon completion reaches local journal', async () =>
          (await snapshot()).journal.some((row) => row.event === expectedPing));
        check((await snapshot()).state.state === 'staged', 'beacon outcome cannot change staged update');
      }
      check(original.state.hardware_revalidation === (scenario === 'hardware_warning'), 'manifest hardware warning preserved');

      if (scenario === 'hydrate_reload' || scenario === 'skip_reload') {
        const key = `native-${scenario}`;
        if (window.sessionStorage.getItem(key) !== 'reloaded') {
          if (scenario === 'skip_reload') {
            check(await confirmUpdateChoiceOnShell('1.35.1', 'skip_this_version'), 'native skip accepted');
          }
          window.sessionStorage.setItem(key, 'reloaded');
          stop();
          window.location.reload();
          return;
        }
      }

      if (scenario === 'staged_ui' || scenario === 'journal_ui' || scenario === 'hardware_warning' || scenario === 'ordinary_release') {
        await connected();
        const radios = Array.from(document.querySelectorAll<HTMLInputElement>('input[name="update-consent"]'));
        check(radios.map((radio) => radio.value).join(',') === 'install_on_quit,install_now,skip_this_version', 'real radio order matches consent contract');
        check(radios[0]?.checked && radios[1] !== undefined && !radios[1].checked, 'quit is the calm default');
        radios[1]?.click();
        check((await stats()).terminal.length === 0, 'radio selection alone is inert');
        await until('actual activity contains signed download', () => element('update-activity-list')?.textContent?.includes('download_ok') === true);
        check(element('update-panel')?.textContent?.includes('Native signed fixture release notes'), 'raw release notes reach frontend');
        if (scenario === 'hardware_warning') check(element('update-panel')?.textContent?.includes('This update changes hardware send paths'), 'hardware warning is visible');
      } else if (scenario === 'install_handoff_quit' || scenario === 'install_handoff_now') {
        await connected();
        await nativeControl('prepare_handoff');
        if (scenario === 'install_handoff_quit') {
          await clickConfirm('install_on_quit');
          check((await stats()).terminal.length === 0, 'real installer awaits natural quit');
          await nativeControl('shutdown');
        } else {
          // Successful Windows Update.install exits the native process. The
          // outside runner observes exit/replacement; no fake success IPC follows.
          await clickConfirm('install_now', false);
        }
        return;
      } else if (scenario === 'consent_stale') {
        check(await confirmUpdateChoiceOnShell('1.36.0', 'install_now') === false, 'stale-version consent rejected');
        check(await invoke('update_confirm_choice', { version: '1.35.1', choice: 'unknown' }) === false, 'unknown choice rejected by real command');
        check((await stats()).terminal.length === 0, 'rejected consent has no terminal effects');
      } else if (scenario === 'consent_crash') {
        await clickConfirm('install_on_quit');
        check((await stats()).terminal.length === 0, 'consent awaits actual quit');
        await nativeControl('crash_after_consent');
        return;
      } else if (scenario === 'consent_after_crash') {
        check((await stats()).terminal.length === 0, 'new native process does not replay old consent');
        check((await snapshot()).journal.some((row) => row.event === 'consent_granted'), 'previous process consent remains audit evidence');
        check(!(await snapshot()).journal.some((row) => row.event === 'install_started'), 'journal is never a consent replay queue');
      } else if (scenario === 'consent_quit' || scenario === 'install_failure') {
        await clickConfirm('install_on_quit');
        check((await stats()).terminal.length === 0, 'quit consent does not install before quit');
        check(await confirmUpdateChoiceOnShell('1.35.1', 'install_now') === false, 'duplicate consent rejected');
        await nativeControl('shutdown');
        await nativeControl('shutdown');
        const terminal = (await stats()).terminal;
        check(terminal.filter((event) => event.event === 'install').length === 1, 'repeated teardown installs exactly once');
        check(terminal[0]?.choice === 'install_on_quit', 'quit choice reaches terminal boundary');
        if (scenario === 'install_failure') check((await snapshot()).state.error_code === 'install_failed', 'installer refusal updates native state');
      } else if (scenario === 'consent_now') {
        await clickConfirm('install_now');
        await until('native teardown then recorded restart', async () => (await stats()).terminal.some((event) => event.event === 'restart'));
        const terminal = (await stats()).terminal;
        check(terminal.map((event) => event.event).join(',') === 'install,restart', 'native clean shutdown precedes install and restart');
        check(terminal[0]?.choice === 'install_now', 'restart choice reaches terminal boundary');
      } else if (scenario === 'skip_newer') {
        check(await confirmUpdateChoiceOnShell('1.35.1', 'skip_this_version'), 'skip accepted');
        await fetch(`${origin}/control?version=1.36.0`);
        check(await requestUpdateCheck(), 'new version recheck accepted');
        await until('newer version staged', async () => (await snapshot()).state.version === '1.36.0' && (await snapshot()).state.state === 'staged');
        check(!(await snapshot()).journal.some((row) => row.event === 'consent_granted'), 'new version requires fresh consent');
      } else if (scenario === 'backend_restart') {
        await connected();
        const oldToken = window.__RYTM_RAND_WS_TOKEN__;
        const oldSecret = window.__RYTM_RAND_ARM_SECRET__;
        check(oldToken && oldSecret, 'both native credential bridges injected');
        await nativeControl('restart_backend');
        await until('native bridge rotates both credentials', () =>
          Boolean(window.__RYTM_RAND_WS_TOKEN__ && window.__RYTM_RAND_WS_TOKEN__ !== oldToken &&
            window.__RYTM_RAND_ARM_SECRET__ && window.__RYTM_RAND_ARM_SECRET__ !== oldSecret));
        check(await staleHandshakeRejected(oldToken), 'old token rejected by restarted backend');
        await connected();
        check(await requestUpdateCheck(), 'same page still invokes native after backend restart');
      }
      if (!['consent_quit', 'consent_now', 'install_failure'].includes(scenario)) {
        await requestUpdateCheck();
        await until('actual native event reaches TS listener', () => eventCount > 0);
      }
    }
    stop();
    await invoke('report', { passed: true, detail: `${assertions} native/DOM assertions` });
  } catch (error) {
    stop();
    await invoke('report', { passed: false, detail: error instanceof Error ? error.message : 'native assertion failed' });
  }
}
