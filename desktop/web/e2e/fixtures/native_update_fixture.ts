/** Native acceptance: real Wry/plugin, with an explicit isolated Windows handoff. */
import { spawn, execFileSync, type ChildProcess } from 'node:child_process';
import { createHash } from 'node:crypto';
import { existsSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import * as http from 'node:http';
import { tmpdir } from 'node:os';
import * as path from 'node:path';

import { resolveRepoRootForManifest } from './update_manifest';
import { collectHandoffEvidence, loadHandoffInputs, prepareHandoffCopy, type HandoffEvidence } from './native_install_handoff';

// Genuine prehashed test vector from minisign-verify 0.2.5, MIT license.
// The bytes are deliberately not an installer. No release secret is involved.
const KEY_LINE = 'RWQf6LRCGA9i53mlYecO4IzT51TGPpvWucNSCh1CBM0QTaLn73Y7GFO3';
const SIGNATURE = [
  'untrusted comment: signature from minisign secret key',
  'RUQf6LRCGA9i559r3g7V1qNyJDApGip8MfqcadIgT9CuhV3EMhHoN1mGTkUidF/z7SrlQgXdy8ofjb7bNJJylDOocrCo8KLzZwo=',
  'trusted comment: timestamp:1556193335\tfile:test',
  'y/rUw2y8/hOUYjZU71eHp/Wo1KZ40fGy2VJEDl34XMJM+TX48Ss/17u3IvIfbVR1FkZZSNCisQbuQY+bHwhEBg==',
].join('\n');
const TARGETS = ['darwin-aarch64', 'darwin-x86_64', 'windows-x86_64', 'linux-x86_64'];
export const SIGNED_BYTES_SHA256 = createHash('sha256').update('test').digest('hex');

export interface NativeEvidence {
  result: { passed: boolean; scenario: string; detail: string };
  requests: readonly string[];
  journal: ReadonlyArray<{ event: string; version: string | null; detail: Record<string, unknown> }>;
  terminal: ReadonlyArray<{ event: string; version: string; choice: string; sha256: string }>;
  handoff?: HandoffEvidence;
}

function publicKey(wrong: boolean): string {
  const raw = Buffer.from(KEY_LINE, 'base64');
  if (wrong) raw[2] = (raw[2] ?? 0) ^ 1; // Different key ID, still valid structure.
  return Buffer.from(`untrusted comment: fixture public key\n${raw.toString('base64')}`).toString('base64');
}

function manifest(version: string, rollout: number, hardware: boolean, malformedSignature: boolean, signature?: string): Record<string, unknown> {
  return {
    schema_version: 1, channel: 'stable', version,
    pub_date: '2026-09-08T00:00:00Z', notes: 'Native signed fixture release notes',
    hardware_revalidation: hardware, rollout_percent: rollout, minimum_version: null,
    build: {
      source_sha: '0'.repeat(40), builder_workflow_sha: '1'.repeat(40),
      workflow_run_url: 'https://github.com/buzzijose-hub/RytmRandomizer/actions/runs/1',
    },
    platforms: Object.fromEntries(TARGETS.map((target) => [target, {
      // Alphabet-valid but impossible length exercises the plugin Base64 error.
      signature: signature ?? (malformedSignature ? 'A' : Buffer.from(SIGNATURE).toString('base64')),
      url: `https://github.com/buzzijose-hub/RytmRandomizer/releases/download/v${version}/fixture.bin`,
    }])),
  };
}

function killOwnedProcess(child: ChildProcess): void {
  if (child.exitCode !== null || child.signalCode !== null || child.pid === undefined) return;
  if (process.platform === 'win32') {
    execFileSync('taskkill.exe', ['/PID', String(child.pid), '/T', '/F'], { windowsHide: true, stdio: 'ignore' });
  } else {
    process.kill(-child.pid, 'SIGKILL');
  }
}

async function reapOwnedProcess(child: ChildProcess): Promise<void> {
  try { killOwnedProcess(child); } catch (error) {
    if (child.exitCode === null && child.signalCode === null) throw error;
  }
  if (child.exitCode === null && child.signalCode === null) {
    await new Promise<void>((resolve) => {
      const deadline = setTimeout(resolve, 5000);
      child.once('exit', () => { clearTimeout(deadline); resolve(); });
    });
  }
}

/** Preserve bounded, credential-free startup/IPC clues before fixture cleanup. */
export function nativeFailureDetails(root: string, output: readonly string[], requests: readonly string[]): string {
  const readOptional = (name: string): string | null => {
    try { return readFileSync(path.join(root, name), 'utf8'); }
    catch { return null; } // Concurrent rotation/teardown must not hide the timeout.
  };
  const journal = readOptional(path.join('RytmRandomizer', 'update-journal.jsonl'));
  const journalEvents: string[] = [];
  if (journal !== null) {
    for (const line of journal.trim().split('\n').filter(Boolean).slice(-50)) {
      try {
        const row: unknown = JSON.parse(line);
        if (typeof row === 'object' && row !== null && 'event' in row && typeof row.event === 'string') {
          journalEvents.push(row.event.slice(0, 64));
        }
      } catch { journalEvents.push('<incomplete-row>'); }
    }
  }
  let diagnostic = output.join('').split(root).join('<fixture-root>');
  for (const name of ['ws-token', 'arm-secret']) {
    const secret = readOptional(name)?.trim();
    if (secret !== undefined && secret !== '') diagnostic = diagnostic.split(secret).join('<fixture-credential>');
  }
  return JSON.stringify({
    requests: requests.slice(-50).map((url) => url.split('?')[0]?.slice(0, 128)),
    resultPresent: existsSync(path.join(root, 'result.json')),
    reportStarted: existsSync(path.join(root, 'report-started.json')),
    sidecarCredentialsPresent: existsSync(path.join(root, 'ws-token')),
    journalEvents,
    output: diagnostic.slice(-8000),
  });
}

/** No browser Page and no mocked IPC: the spawned native window runs the assertions. */
export async function runNativeScenario(scenario: string): Promise<NativeEvidence> {
  const binary = process.env.RYTM_NATIVE_TEST_BINARY;
  const python = process.env.PYTHON ?? process.env.PYTHON_EXECUTABLE;
  if (binary === undefined || !path.isAbsolute(binary) || !existsSync(binary)) {
    throw new Error('Build --features native-test and set RYTM_NATIVE_TEST_BINARY to its isolated executable.');
  }
  if (python === undefined || !path.isAbsolute(python) || !existsSync(python)) {
    throw new Error('Set PYTHON to the absolute shared environment Python executable.');
  }
  const repo = resolveRepoRootForManifest();
  const handoffInputs = ['install_handoff_quit', 'install_handoff_now'].includes(scenario) ? loadHandoffInputs(repo) : null;
  const root = mkdtempSync(path.join(tmpdir(), 'rytm-native-update-'));
  const handoffCopy = handoffInputs === null ? null : prepareHandoffCopy(root, binary, handoffInputs);
  let handoffCompleted = handoffInputs === null;
  const requests: string[] = [];
  const parked = new Set<http.ServerResponse>();
  const timers = new Set<ReturnType<typeof setTimeout>>();
  let version = scenario === 'equal_version' ? readFileSync(path.join(repo, 'VERSION'), 'utf8').trim() : '1.35.1';
  let rollout = scenario.startsWith('rollout_') ? 10 : 100;
  const hardware = scenario === 'hardware_warning';
  const server = http.createServer((request, response) => {
    const url = request.url ?? '/';
    requests.push(url);
    response.setHeader('Access-Control-Allow-Origin', '*');
    response.setHeader('Access-Control-Allow-Headers', 'Content-Type');
    if (request.method === 'OPTIONS') { response.end(); return; }
    if (url.startsWith('/control')) {
      const params = new URL(url, 'http://127.0.0.1').searchParams;
      if (params.has('version')) version = params.get('version') ?? version;
      if (params.has('rollout')) rollout = Number(params.get('rollout'));
      response.end('ok'); return;
    }
    if (url === '/stable.json') {
      if (scenario === 'check_failure') { response.writeHead(503).end(); return; }
      const body = manifest(version, rollout, hardware, scenario === 'signature_malformed', handoffInputs?.signature);
      if (scenario === 'manifest_invalid') body.hardware_revalidation = 'incorrect_type';
      const send = (): void => { response.setHeader('Content-Type', 'application/json'); response.end(JSON.stringify(body)); };
      if (scenario === 'inflight_checks' || scenario === 'manifest_cancel') {
        parked.add(response);
        const timer = setTimeout(() => { timers.delete(timer); parked.delete(response); send(); }, scenario === 'manifest_cancel' ? 60_000 : 1500);
        timers.add(timer);
      } else send();
      return;
    }
    if (url === '/artifact.bin') {
      if (scenario === 'download_cancel') { parked.add(response); response.on('close', () => parked.delete(response)); return; }
      response.setHeader('Content-Type', 'application/octet-stream');
      response.end(handoffInputs?.bytes ?? (scenario === 'signature_failure' ? 'Test' : 'test')); return;
    }
    if (url === '/beacon.txt') {
      if (scenario === 'beacon_hang') { parked.add(response); response.on('close', () => parked.delete(response)); return; }
      response.writeHead(scenario === 'beacon_error' ? 500 : scenario === 'beacon_absent' ? 404 : 200);
      response.end('.'); return;
    }
    response.writeHead(404).end('unexpected fixture request');
  });
  let child: ChildProcess | null = null;
  try {
    await new Promise<void>((resolve, reject) => { server.once('error', reject); server.listen(0, '127.0.0.1', resolve); });
    const address = server.address();
    if (address === null || typeof address === 'string') throw new Error('native fixture port missing');
    const origin = `http://127.0.0.1:${address.port}`;
    const entry = path.join(root, 'sidecar_entry.py');
    execFileSync(python, ['-c',
      'from pathlib import Path; import runpy, sys; entry_source = runpy.run_path(sys.argv[2])["entry_source"]; Path(sys.argv[1]).write_text(entry_source(), encoding="utf-8")',
      entry, path.join(repo, 'scripts', 'build_sidecar_binary.py')], { cwd: repo, windowsHide: true, env: { ...process.env, PYTHONPATH: repo } });
    const config = path.join(root, 'native.json');
    writeFileSync(config, JSON.stringify({
      root, origin, scenario, public_key: handoffInputs?.publicKey ?? publicKey(scenario === 'wrong_key'),
      install_id: scenario === 'rollout_in' ? '00000000-0000-4000-8000-000000000015' : '00000000-0000-4000-8000-000000000119',
      python, sidecar_entry: entry,
      ...(handoffCopy === null ? {} : { handoff_nonce: handoffCopy.nonce }),
    }));
    const output: string[] = [];
    const launch = (): ChildProcess => spawn(handoffCopy?.executable ?? binary, [], {
      cwd: repo, windowsHide: true, detached: process.platform !== 'win32',
      stdio: ['ignore', 'pipe', 'pipe'],
      env: {
        ...process.env, PYTHONPATH: repo, PYTHONUNBUFFERED: '1',
        ...(handoffCopy === null ? {} : { TMP: path.join(root, 'plugin-temp'), TEMP: path.join(root, 'plugin-temp') }),
        XDG_CONFIG_HOME: root, APPDATA: root,
        RYTM_RAND_NATIVE_TEST_CONFIG: config,
        RYTM_RAND_MIDI_BACKEND: 'off',
        RYTM_RAND_WS_PORT: '', RYTM_RAND_WS_TOKEN_FILE: path.join(root, 'ws-token'),
        RYTM_RAND_ARM_SECRET_FILE: path.join(root, 'arm-secret'),
        RYTM_RAND_UPDATE_MANIFEST_URL: origin,
        RYTM_RAND_UPDATES: scenario.startsWith('frozen_') ? 'off' : 'on',
        RYTM_RAND_UPDATE_BEACON: scenario === 'beacon_off' ? 'off' : 'on',
        RYTM_RAND_UPDATE_CHANNEL: 'stable',
        HTTP_PROXY: '', HTTPS_PROXY: '', ALL_PROXY: '', NO_PROXY: '*',
      },
    });
    const waitForExit = (running: ChildProcess): Promise<void> => new Promise((resolve, reject) => {
      running.stdout?.on('data', (data: Buffer) => { output.push(data.toString()); if (output.length > 150) output.shift(); });
      running.stderr?.on('data', (data: Buffer) => { output.push(data.toString()); if (output.length > 150) output.shift(); });
      const deadline = setTimeout(() => reject(new Error(`Native scenario ${scenario} timed out:\n${nativeFailureDetails(root, output, requests)}`)), 65_000);
      running.once('error', (error) => { clearTimeout(deadline); reject(error); });
      running.once('exit', () => { clearTimeout(deadline); resolve(); });
    });
    child = launch();
    await waitForExit(child);
    let handoff: HandoffEvidence | undefined;
    if (handoffInputs !== null && handoffCopy !== null) {
      handoff = await collectHandoffEvidence(root, child, handoffInputs, handoffCopy.originalHash, scenario === 'install_handoff_now');
      handoffCompleted = true;
    }
    if (scenario === 'consent_crash') {
      if (child.exitCode !== 86 || !existsSync(path.join(root, 'crashed'))) throw new Error('Native consent crash fixture did not reach its crash boundary');
      const options = JSON.parse(readFileSync(config, 'utf8')) as Record<string, unknown>;
      writeFileSync(config, JSON.stringify({ ...options, scenario: 'consent_after_crash' }));
      child = launch();
      await waitForExit(child);
    }
    const resultPath = path.join(root, 'result.json');
    if (handoff === undefined && !existsSync(resultPath)) {
      throw new Error(`Native runner produced no result for ${scenario}:\n${nativeFailureDetails(root, output, requests)}`);
    }
    const result = handoff === undefined ? JSON.parse(readFileSync(resultPath, 'utf8')) as NativeEvidence['result']
      : { passed: true, scenario, detail: 'Real Windows installer handoff and native/DOM assertions' };
    if (!result.passed) throw new Error(`Native ${scenario}: ${result.detail}`);
    const journalPath = path.join(root, 'RytmRandomizer', 'update-journal.jsonl');
    const journal = existsSync(journalPath) ? readFileSync(journalPath, 'utf8').trim().split('\n').filter(Boolean).map((line) => JSON.parse(line)) as NativeEvidence['journal'] : [];
    const terminalPath = path.join(root, 'terminal.json');
    const terminal = existsSync(terminalPath) ? JSON.parse(readFileSync(terminalPath, 'utf8')) as NativeEvidence['terminal'] : [];
    return { result, requests, journal, terminal, ...(handoff === undefined ? {} : { handoff }) };
  } finally {
    if (child !== null) await reapOwnedProcess(child);
    timers.forEach(clearTimeout);
    parked.forEach((response) => response.destroy());
    server.closeAllConnections();
    await new Promise<void>((resolve) => server.close(() => resolve()));
    // A failed real handoff retains its isolated receipt directory rather than
    // deleting files that an independently launched bounded installer may own.
    if (handoffCompleted) rmSync(root, { recursive: true, force: true, maxRetries: 10, retryDelay: 100 });
  }
}
