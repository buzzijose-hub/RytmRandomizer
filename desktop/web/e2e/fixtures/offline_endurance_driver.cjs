/* Explicit packaged-Windows QA, not a CI spec or production app entry point. */
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const assert = require('node:assert/strict');
const { spawnSync } = require('node:child_process');
const { performance } = require('node:perf_hooks');
const { chromium, expect } = require('@playwright/test');

const repo = path.resolve(__dirname, '../../../..');
const args = process.argv.slice(2);
const argument = (name, fallback) => {
  const index = args.indexOf(name);
  return index < 0 ? fallback : args[index + 1];
};
const bundle = path.resolve(argument('--bundle', ''));
const runRoot = path.resolve(argument('--run-root', ''));
const python = argument('--python', path.join(repo, '.venv/Scripts/python.exe'));
const smoke = Number(argument('--smoke-seconds', '0'));
const minutes = Number(argument('--minutes', '100'));
const intervalSeconds = Number(argument('--interval-seconds', '30'));
const a4Track = Number(argument('--a4-track', '3'));
const a4Page = argument('--a4-page', 'FILTER');
const a4Fields = argument('--a4-fields', 'Filter1 Frequency,filter2_resonance').split(',');
const a4SourceHash = argument('--a4-source-sha256', null);
const includePad2 = args.includes('--pad2');
assert(args.includes('--bundle') && args.includes('--run-root'));
assert(path.isAbsolute(python));
assert(smoke > 0 ? smoke <= 600 : minutes >= 90 && minutes <= 120);
assert(intervalSeconds >= 10 && intervalSeconds <= 180);
// Four cues remain below the existing 64-candidate entry limit for 120 minutes.
assert(smoke > 0 || intervalSeconds >= 30);
assert(Number.isInteger(a4Track) && a4Track >= 1 && a4Track <= 4);
assert(a4Fields.length > 0 && a4Fields.length <= 8);
assert(!runRoot.startsWith(bundle + path.sep), 'QA credentials must be outside delivery');
assert(!fs.existsSync(runRoot), 'Use a new isolated QA namespace');
const manifest = JSON.parse(fs.readFileSync(path.join(bundle, 'BUILD-MANIFEST.json'), 'utf8').replace(/^\uFEFF/, ''));
const digest = data => crypto.createHash('sha256').update(data).digest('hex');
for (const [name, expected] of Object.entries(manifest.sha256)) {
  assert(['rytm-randomizer-shell.exe', 'binaries/rytm-sidecar.exe'].includes(name));
  assert.equal(digest(fs.readFileSync(path.join(bundle, name))), expected);
}
const sourceDiff = spawnSync('git', ['diff', '--name-only', manifest.source_commit, '--', 'rytm_randomizer', 'desktop/web/src'], { cwd: repo, encoding: 'utf8', windowsHide: true });
assert.equal(sourceDiff.status, 0); assert.equal(sourceDiff.stdout.trim(), '', 'Verifier source must match binary production');
fs.mkdirSync(path.join(runRoot, 'report'), { recursive: true });
const reportRoot = path.join(runRoot, 'report');
const telemetry = path.join(reportRoot, 'telemetry.ndjson');
const summary = { source_commit: manifest.source_commit, binary_sha256: manifest.sha256, driver_sha256: digest(fs.readFileSync(__filename)), mode: smoke > 0 ? 'smoke' : 'endurance', minimum_minutes: smoke > 0 ? null : minutes, started_at: new Date().toISOString(), midi_backend: 'off', physical_observation: false, a4_track: a4Track, a4_fields: a4Fields, pad2_preset: includePad2, passed: false, cycles: 0, restarts: [], setup_interruptions: [], operations: {}, pending_high_water: 0, configured_bounds: { journal: 50, native_frame_cache: 128, native_frame_cache_bytes: 67108864 }, observation_limits: ['HistoryStore is append-only, not an eviction ring; source-reuse history size is observed. Native frame-cache occupancy is not exposed; its structural bounds have separate software tests.'] };
const save = () => fs.writeFileSync(path.join(reportRoot, 'summary.json'), JSON.stringify(summary, null, 2) + '\n');
const record = value => fs.appendFileSync(telemetry, JSON.stringify({ at: new Date().toISOString(), ...value }) + '\n');
const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));
const errorType = error => ['AssertionError', 'Error', 'TimeoutError', 'TypeError', 'RangeError', 'SyntaxError'].includes(error?.name) ? error.name : 'Error';
const rehearsalCueId = (ids, cycle) => ids[cycle % ids.length];
const orderedCells = cells => cells === null || cells === undefined ? null : [...cells].sort((left, right) => left.item_id - right.item_id || (left.parameter_key < right.parameter_key ? -1 : left.parameter_key > right.parameter_key ? 1 : 0));
const freshExactScope = (sequence, previous, actual, expected) => sequence > previous && JSON.stringify(orderedCells(actual)) === JSON.stringify(orderedCells(expected));

const powershell = String.raw`
$ErrorActionPreference='Stop'
$r=[Console]::In.ReadToEnd()|ConvertFrom-Json
function Descendants-Of($all,$root){
  $ids=[System.Collections.Generic.HashSet[int]]::new()
  $byId=@{};foreach($p in $all){$byId[$p.ProcessId]=$p}
  [void]$ids.Add($root.ProcessId)
  # Parent PIDs can be reused; an older child cannot belong to the current parent.
  do{$changed=$false;foreach($p in $all){if($ids.Contains($p.ParentProcessId)-and$byId.ContainsKey($p.ParentProcessId)-and$p.CreationDate -ge $byId[$p.ParentProcessId].CreationDate-and$ids.Add($p.ProcessId)){$changed=$true}}}while($changed)
  return @($all|Where-Object {$ids.Contains($_.ProcessId)})
}
function Own-Tree {
  $all=@(Get-CimInstance Win32_Process)
  $shell=$all|Where-Object ProcessId -eq $r.shell_pid|Select-Object -First 1
  if($null -eq $shell -or $shell.ExecutablePath -ne (Join-Path $r.bundle 'rytm-randomizer-shell.exe')){throw 'Owned shell missing'}
  $recorded=[long]$r.created_ticks
  if($shell.CreationDate.ToUniversalTime().Ticks -ne ($recorded-($recorded%10))){throw 'Owned shell identity changed'}
  return @(Descendants-Of $all $shell)
}
function Open-OwnedProcess($row){
  $bound=$null
  try{
    $bound=Get-Process -Id $row.ProcessId -ErrorAction Stop
    # Pin the Windows process object before identity reads or termination.
    [void]$bound.SafeHandle
    # CIM timestamps retain microseconds; native process times retain 100ns.
    $nativeTicks=$bound.StartTime.ToUniversalTime().Ticks
    if($bound.HasExited-or($nativeTicks-($nativeTicks%10)) -ne $row.CreationDate.ToUniversalTime().Ticks-or$bound.Path -ne $row.ExecutablePath){$bound.Dispose();return $null}
    return $bound
  }catch{
    if($null -ne $bound){$bound.Dispose()}
    $current=Get-CimInstance Win32_Process -Filter "ProcessId=$($row.ProcessId)"
    if($null -ne $current-and$current.CreationDate -eq $row.CreationDate-and$current.ExecutablePath -eq $row.ExecutablePath){throw}
    return $null
  }
}
function Stop-Owned($owned){
  foreach($p in $owned){
    $bound=Open-OwnedProcess $p
    if($null -eq $bound){continue}
    try{
      if(-not$bound.HasExited){$bound.Kill();if(-not$bound.WaitForExit(5000)){throw 'Owned process did not stop'}}
    }finally{
      $bound.Dispose()
    }
  }
}
if($r.operation -eq 'launch'){
  New-Item -ItemType Directory -Path $r.state -Force|Out-Null
  $listener=[System.Net.Sockets.TcpListener]::new([System.Net.IPAddress]::Loopback,0)
  $listener.Start();$ws=$listener.LocalEndpoint.Port;$listener.Stop()
  $listener.Start();$debug=$listener.LocalEndpoint.Port;$listener.Stop()
  $env:RYTM_RAND_MIDI_BACKEND='off';$env:RYTM_RAND_UPDATES='off'
  Remove-Item Env:RYTM_RAND_SIDECAR_BIN -ErrorAction SilentlyContinue
  $env:RYTM_RAND_WS_PORT="$ws"
  $env:RYTM_RAND_WS_TOKEN_FILE=Join-Path $r.state 'ws-token.txt'
  $env:RYTM_RAND_ARM_SECRET_FILE=Join-Path $r.state 'arm-secret.txt'
  $env:APPDATA=Join-Path $r.state 'roaming';$env:LOCALAPPDATA=Join-Path $r.state 'local'
  $env:HOME=$r.state;$env:USERPROFILE=$r.state;$env:XDG_CONFIG_HOME=Join-Path $r.state 'config'
  $env:WEBVIEW2_USER_DATA_FOLDER=Join-Path $r.state "webview-$debug"
  $env:WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS="--remote-debugging-port=$debug --remote-debugging-address=127.0.0.1"
  $p=Start-Process -FilePath (Join-Path $r.bundle 'rytm-randomizer-shell.exe') -WorkingDirectory $r.bundle -WindowStyle Hidden -PassThru
  @{shell_pid=$p.Id;created_at=$p.StartTime.ToUniversalTime().ToString('o');created_ticks=[string]$p.StartTime.ToUniversalTime().Ticks;ws_port=$ws;debug_port=$debug}|ConvertTo-Json -Compress
}elseif($r.operation -eq 'sample'){
  $tree=@(Own-Tree);$rows=@()
  foreach($p in $tree){$value=Get-Process -Id $p.ProcessId -ErrorAction SilentlyContinue;if($null -ne $value){$rows+=@{name=$p.Name;pid=$p.ProcessId;private_bytes=$value.PrivateMemorySize64;working_set=$value.WorkingSet64;handles=$value.HandleCount;cpu_seconds=$value.CPU}}}
  $os=Get-CimInstance Win32_OperatingSystem
  @{processes=$rows;free_ram_bytes=($os.FreePhysicalMemory*1024)}|ConvertTo-Json -Depth 4 -Compress
}elseif($r.operation -eq 'stop'){
  $owned=@(Own-Tree)
  $main=Open-OwnedProcess ($owned|Where-Object ProcessId -eq $r.shell_pid|Select-Object -First 1)
  if($null -ne $main){try{[void]$main.CloseMainWindow();[void]$main.WaitForExit(5000)}finally{$main.Dispose()}}
  Stop-Owned $owned;@{stopped=$true}|ConvertTo-Json -Compress
}elseif($r.operation -eq 'restart-backend'){
  $tree=@(Own-Tree);$sidecarPath=Join-Path $r.bundle 'binaries/rytm-sidecar.exe'
  $side=@($tree|Where-Object {$_.ParentProcessId -eq $r.shell_pid-and$_.ExecutablePath -eq $sidecarPath})
  if($side.Count -ne 1){throw 'Expected one owned backend root'}
  $token=Join-Path $r.state 'ws-token.txt';$before=(Get-FileHash -LiteralPath $token -Algorithm SHA256).Hash
  Stop-Owned @(Descendants-Of $tree $side[0])
  $deadline=[DateTime]::UtcNow.AddSeconds(30);$replacement=$null;$rotated=$false
  do{Start-Sleep -Milliseconds 250;$replacement=Get-CimInstance Win32_Process|Where-Object {$_.ParentProcessId -eq $r.shell_pid-and$_.ExecutablePath -eq $sidecarPath-and$_.ProcessId -ne $side[0].ProcessId}|Select-Object -First 1;$rotated=(Test-Path -LiteralPath $token)-and((Get-FileHash -LiteralPath $token -Algorithm SHA256).Hash -ne $before)}while(($null -eq $replacement-or-not$rotated)-and[DateTime]::UtcNow -lt $deadline)
  if($null -eq $replacement-or-not$rotated){throw 'Owned backend recovery deadline exceeded'}
  @{old_pid=$side[0].ProcessId;new_pid=$replacement.ProcessId;token_rotated=$rotated;shell_preserved=$true}|ConvertTo-Json -Compress
}else{throw 'Unknown owned-process operation'}
`;
let launch;
function processOperation(operation) {
  const result = spawnSync('pwsh.exe', ['-NoProfile', '-Command', powershell], { input: JSON.stringify({ operation, bundle, state: path.join(runRoot, 'state'), ...launch }), encoding: 'utf8', timeout: 45000, windowsHide: true });
  assert.equal(result.status, 0, `owned-process ${operation} failed: ${result.stderr}`);
  return JSON.parse(result.stdout.replace(/^\uFEFF/, '').trim());
}
function locatePackage(directoryName) {
  const queue = [path.join(runRoot, 'state')];
  while (queue.length) {
    const current = queue.shift();
    for (const entry of fs.readdirSync(current, { withFileTypes: true })) {
      if (!entry.isDirectory() || entry.isSymbolicLink()) continue;
      const target = path.join(current, entry.name);
      if (entry.name === directoryName) return target;
      if (!entry.name.startsWith('webview-')) queue.push(target);
    }
  }
  throw new Error('Expected package publication is absent');
}
function verifyPack(directoryName) {
  const result = spawnSync(python, [path.join(repo, 'scripts/verify_offline_rehearsal_pack.py'), locatePackage(directoryName)], { cwd: repo, env: { ...process.env, PYTHONPATH: repo, RYTM_RAND_MIDI_BACKEND: 'off' }, encoding: 'utf8', timeout: 30000, windowsHide: true });
  assert.equal(result.status, 0, `canonical package verification failed: ${result.stdout} ${result.stderr}`);
  const verified = JSON.parse(result.stdout.trim()); assert(verified.verified); return verified;
}

async function main() {
  let browser;
  try {
    for (let attempt = 0; attempt < 2; attempt++) {
      launch = processOperation('launch');
      fs.writeFileSync(path.join(runRoot, 'owned-launch.json'), JSON.stringify(launch, null, 2) + '\n');
      save();
      let available = false;
      for (let probe = 0; probe < 20; probe++) {
        try { const response = await fetch(`http://127.0.0.1:${launch.debug_port}/json/version`); available = response.ok; } catch { /* Cold WebView may need a separate fresh profile. */ }
        if (available) break;
        await sleep(500);
      }
      if (available) break;
      summary.setup_interruptions.push({ reason: 'debug_listener_unavailable', attempt, at: new Date().toISOString() });
      processOperation('stop'); launch = null;
    }
    assert(launch, 'Both isolated WebView startup attempts refused debugging');
    browser = await chromium.connectOverCDP(`http://127.0.0.1:${launch.debug_port}`);
    const page = browser.contexts().flatMap(context => context.pages()).find(candidate => candidate.url().includes('tauri.localhost'));
    assert(page); page.setDefaultTimeout(15000);
    const cdp = await page.context().newCDPSession(page);
    await cdp.send('Network.enable'); await cdp.send('Performance.enable');
    const latest = {}, pending = new Map();
    let exported, diagnostics, rawPageErrors = 0, observationFailure = null, parameterSequence = 0;
    page.on('pageerror', () => { rawPageErrors++; });
    cdp.on('Network.webSocketFrameSent', event => {
      let value; try { value = JSON.parse(event.response.payloadData); } catch { return; }
      if (!value.command) return;
      if (['arm', 'send', 'save', 'capture_current_kit', 'list_capture_inputs'].includes(value.command.type)) observationFailure = 'Prohibited command observed';
      pending.set(value.request_id, { command: value.command.type, started: performance.now() });
      if (pending.size > 64) observationFailure = 'Unbounded wire backlog';
      summary.pending_high_water = Math.max(summary.pending_high_water, pending.size);
    });
    cdp.on('Network.webSocketFrameReceived', event => {
      let value; try { value = JSON.parse(event.response.payloadData); } catch { return; }
      if (value.type) latest[value.type] = value;
      if (value.type === 'mutation_parameters_changed') parameterSequence++;
      if (value.library_records) latest.library_records = value.library_records;
      if (value.show_pack_export) exported = value.show_pack_export;
      if (value.diagnostics) diagnostics = value.diagnostics;
      if (!pending.has(value.request_id)) return;
      const operation = pending.get(value.request_id); pending.delete(value.request_id);
      const elapsed = performance.now() - operation.started;
      const totals = summary.operations[operation.command] ||= { count: 0, failures: 0, milliseconds: 0, maximum_ms: 0 };
      totals.count++; totals.failures += value.ok ? 0 : 1; totals.milliseconds += elapsed; totals.maximum_ms = Math.max(totals.maximum_ms, elapsed);
      record({ kind: 'command', command: operation.command, ok: value.ok, code: value.code || null, milliseconds: elapsed });
    });
    cdp.on('Network.webSocketClosed', () => { pending.clear(); });
    const forge = page.getByTestId('show-kit-forge'), scope = page.getByTestId('mutation-parameters-panel');
    const bank = () => latest.show_bank_changed?.show_bank.banks.find(value => value.bank_id === latest.show_bank_changed.show_bank.active_bank_id);
    const connected = async () => {
      await expect(page.getByTestId('safety-rail').getByText('Connected', { exact: true })).toBeVisible({ timeout: 30000 });
      await expect(page.getByTestId('safety-rail').getByText('Hardware Off')).toBeVisible();
    };
    await connected();
    await page.getByTestId('profile-chips').getByRole('button').first().click();
    await forge.getByLabel('Bank name', { exact: true }).fill('Bounded endurance rehearsal');
    await forge.getByRole('button', { name: 'Create show bank', exact: true }).click();
    await expect.poll(() => bank()?.bank_id).not.toBeUndefined();
    const workBankId = bank().bank_id;
    await forge.getByRole('button', { name: 'Import captures folder' }).click();
    await forge.getByRole('button', { name: 'Refresh source files' }).click();
    await forge.getByRole('combobox', { name: 'Rytm source file', exact: true }).selectOption({ index: 1 });
    if (a4SourceHash) {
      await expect.poll(() => latest.library_records?.some(record => record.source_frame?.sha256 === a4SourceHash)).toBe(true);
      const record = latest.library_records.find(record => record.source_frame?.sha256 === a4SourceHash);
      await forge.getByRole('combobox', { name: 'Analog Four source file', exact: true }).selectOption(record.record_id);
    } else await forge.getByRole('combobox', { name: 'Analog Four source file', exact: true }).selectOption({ index: 1 });
    const slots = forge.getByLabel('Source hardware slot (1–128)'); await slots.nth(0).fill('20'); await slots.nth(1).fill('20');
    await forge.getByRole('button', { name: 'Adopt source files', exact: true }).click();
    await expect(forge.getByRole('heading', { name: 'Forge candidate pairs' })).toBeVisible();
    if (includePad2) await scope.getByRole('button', { name: 'Pad 2 rehearsal', exact: true }).click();
    else await scope.getByRole('button', { name: 'Select none', exact: true }).click();
    await scope.getByLabel('Parameter scope device').selectOption('analog_four_mk2');
    await scope.getByRole('button', { name: 'Select none', exact: true }).click();
    await scope.getByLabel('Parameter scope item').selectOption(String(a4Track));
    await scope.getByLabel('Explicit target track').check();
    await scope.getByLabel('Lock track').uncheck();
    await scope.getByRole('tab', { name: a4Page, exact: true }).click();
    for (const field of a4Fields) await scope.getByTestId(`parameter-row-${a4Track}-${field}`).getByRole('checkbox').check();
    await forge.getByLabel('Candidate count').selectOption('1');
    let selectedEntryId = bank().active_entry_id;
    const stableEntries = value => value.entries.map(entry => ({ entry_id: entry.entry_id, name: entry.name, candidates: entry.candidates, favorite: entry.favorite, rytm_source: entry.rytm_source, analog_four_source: entry.analog_four_source, oxi: entry.oxi, transition_notes: entry.transition_notes }));
    async function generate(seed, size) {
      const count = bank().entries.find(entry => entry.entry_id === selectedEntryId).candidates.length;
      await forge.getByLabel('Starting seed').fill(String(seed));
      await forge.getByRole('button', { name: new RegExp(size) }).click();
      await forge.getByRole('button', { name: 'Forge 1 candidate pairs', exact: true }).click();
      await expect.poll(() => bank()?.entries.find(entry => entry.entry_id === selectedEntryId)?.candidates.length).toBe(count + 1);
      const entry = bank().entries.find(value => value.entry_id === selectedEntryId), candidate = entry.candidates.at(-1);
      const canonicalKeys = a4Fields.map(key => key === 'Filter1 Frequency' ? 'filter1_frequency' : key);
      assert(candidate.analog_four_candidate.values.every(value => value.track_id === a4Track && canonicalKeys.includes(value.parameter)));
      assert(candidate.rytm_candidate.pad_deltas.every(delta => delta.changed_keys.length === 0 || (includePad2 && delta.pad_id === 2 && delta.changed_keys.every(key => ['flt', 'amp_decay', 'overdrive', 'reverb'].includes(key)))));
      const card = forge.getByRole('article', { name: `Candidate ${entry.candidates.length}`, exact: true });
      await card.getByText('Compare musical changes', { exact: true }).click();
      await card.getByRole('button', { name: 'Mark favorite', exact: true }).click();
      const confirm = card.getByRole('button', { name: 'Replace favorite', exact: true });
      if (await confirm.isVisible()) await confirm.click();
      await expect.poll(() => bank()?.entries.find(value => value.entry_id === entry.entry_id)?.favorite?.candidate_id).toBe(candidate.candidate_id);
      return candidate;
    }
    await generate(3000, 'Small'); await generate(3001, 'Large');
    for (let item = 0; item < 3; item++) {
      await forge.getByRole('button', { name: 'Duplicate', exact: true }).first().click();
      await expect.poll(() => bank()?.entries.length).toBe(item + 2);
      const duplicate = bank().entries.at(-1);
      await forge.getByRole('button', { name: duplicate.name, exact: true }).last().click();
      const metadata = forge.locator('form').filter({ hasText: 'Shape the show moment' });
      await metadata.getByLabel('Name', { exact: true }).fill(`Endurance cue ${item + 2}`);
      await metadata.getByRole('button', { name: /Save cue/ }).click();
      await expect.poll(() => bank()?.entries.find(entry => entry.entry_id === duplicate.entry_id)?.name).toBe(`Endurance cue ${item + 2}`);
    }
    const sourceIdentity = bank().entries.map(entry => [entry.rytm_source.sysex.frame_sha256, entry.analog_four_source.sysex.frame_sha256]);
    const cueIds = bank().entries.map(entry => entry.entry_id);
    const expectedScope = a4Fields.map(field => ({ item_id: a4Track, parameter_key: field === 'Filter1 Frequency' ? 'filter1_frequency' : field }));
    summary.phase = 'missing-package-refusal'; save();
    const beforeMissing = structuredClone(bank());
    await forge.getByLabel('Import package ID').fill('missing-endurance-package');
    await forge.getByLabel('New bank ID (optional)').fill('missing-endurance-copy');
    await forge.getByRole('button', { name: 'Import local pack', exact: true }).click();
    await expect(forge.getByText('Import show pack failed: Local artifact is missing. Restore the complete package or retained source, then retry.', { exact: true })).toBeVisible();
    assert.deepEqual(bank(), beforeMissing);
    summary.missing_package_refusal_preserved_bank = true;
    const started = performance.now(), duration = smoke > 0 ? smoke * 1000 : minutes * 60000;
    summary.rehearsal_started_at = new Date().toISOString(); save();
    while (performance.now() - started < duration) {
      const cycleStart = performance.now(), cycle = summary.cycles;
      await forge.getByLabel('Server banks').selectOption(workBankId);
      await expect.poll(() => bank()?.bank_id).toBe(workBankId);
      const entry = bank().entries.find(value => value.entry_id === rehearsalCueId(cueIds, cycle));
      await forge.getByRole('button', { name: entry.name, exact: true }).first().click();
      selectedEntryId = entry.entry_id;
      summary.phase = 'scope-change-and-generation'; save();
      await scope.getByLabel('Parameter scope device').selectOption('analog_four_mk2');
      await scope.getByLabel('Parameter scope item').selectOption(String(a4Track));
      await scope.getByRole('tab', { name: a4Page, exact: true }).click();
      const selectedControl = scope.getByTestId(`parameter-row-${a4Track}-${a4Fields[0]}`).getByRole('checkbox');
      let previousSequence = parameterSequence;
      await selectedControl.uncheck();
      await expect.poll(() => freshExactScope(parameterSequence, previousSequence, latest.mutation_parameters_changed?.a4_parameters, expectedScope.slice(1))).toBe(true);
      previousSequence = parameterSequence;
      await selectedControl.check();
      await expect.poll(() => freshExactScope(parameterSequence, previousSequence, latest.mutation_parameters_changed?.a4_parameters, expectedScope)).toBe(true);
      assert(entry.candidates.length < 64, 'Legal cue candidate bound reached');
      await generate(3100 + cycle, cycle % 2 ? 'Large' : 'Small');
      const last = bank().entries.at(-1);
      await forge.getByRole('button', { name: `Move ${last.name} earlier`, exact: true }).click();
      await expect.poll(() => bank()?.entries.at(-1)?.entry_id).not.toBe(last.entry_id);
      const expected = structuredClone(stableEntries(bank()));
      const packageId = `endurance-${cycle}`;
      summary.phase = 'export-and-byte-verification'; save();
      await forge.getByLabel('Export package ID').fill(packageId);
      await forge.getByRole('button', { name: 'Export draft local pack', exact: true }).click();
      await expect.poll(() => exported?.package_id).toBe(packageId);
      const verification = verifyPack(exported.directory_name);
      record({ kind: 'pack-verification', cycle, ...verification });
      await forge.getByLabel('Import package ID').fill(packageId);
      await forge.getByLabel('New bank ID (optional)').fill(cycle < 8 ? `endurance-copy-${cycle}` : 'endurance-copy-0');
      const before = structuredClone(bank());
      summary.phase = 'import-or-duplicate-refusal'; save();
      await forge.getByRole('button', { name: 'Import local pack', exact: true }).click();
      if (cycle < 8) {
        await expect(forge.getByLabel('Server banks')).toHaveValue(`endurance-copy-${cycle}`);
        assert.deepEqual(stableEntries(bank()), expected);
      } else {
        await expect(forge.getByText(/Import show pack failed:/)).toBeVisible();
        assert.equal(bank().revision, before.revision);
        assert.deepEqual(bank().entries, before.entries);
      }
      await expect(page.getByTestId('action-send')).toBeDisabled();
      assert(bank().readiness.show_ready === false);
      summary.phase = 'resource-measurement'; save();
      await page.getByTestId('doctor-refresh').click();
      await expect.poll(() => diagnostics?.journal !== undefined).toBe(true);
      assert(diagnostics.journal.length <= 50);
      assert.deepEqual(diagnostics.available_inputs, []); assert.deepEqual(diagnostics.available_outputs, []);
      const resource = processOperation('sample');
      const privateBytes = resource.processes.reduce((total, process) => total + process.private_bytes, 0);
      assert(resource.free_ram_bytes > 6 * 1024 ** 3, 'Resource floor reached; stop safely');
      assert(privateBytes < 3 * 1024 ** 3, 'Owned app private-memory ceiling reached');
      const performanceMetrics = await cdp.send('Performance.getMetrics');
      const health = await (await fetch(`http://127.0.0.1:${launch.ws_port}/health`)).json();
      assert.equal(health.mode, 'mock');
      assert(health.outbound_queue, 'Source-bound package must expose queue telemetry');
      assert(health.outbound_queue.high_water_per_connection <= health.outbound_queue.capacity_per_connection);
      assert(health.outbound_queue.queued_frames <= health.outbound_queue.connection_count * health.outbound_queue.capacity_per_connection);
      record({ kind: 'resource', cycle, resource, private_bytes: privateBytes, outbound_queue: health.outbound_queue, journal_count: diagnostics.journal.length, history_count: latest.history_updated?.history?.entries.length ?? null, pending_requests: pending.size, webview_metrics: Object.fromEntries(performanceMetrics.metrics.filter(value => ['JSHeapUsedSize', 'JSHeapTotalSize', 'Documents', 'Nodes', 'JSEventListeners'].includes(value.name)).map(value => [value.name, value.value])) });
      assert.equal(rawPageErrors, 0);
      assert.equal(observationFailure, null);
      if (cycle === 2 || (!smoke && cycle === 90)) {
        summary.phase = 'owned-backend-restart-and-recall'; save();
        const restartBankId = bank().bank_id;
        const identity = digest(JSON.stringify(stableEntries(bank())));
        const recovery = processOperation('restart-backend');
        summary.restarts.push({ ...recovery, cycle, at: new Date().toISOString() });
        await connected();
        await forge.getByRole('button', { name: 'Refresh from server', exact: true }).click();
        await forge.getByLabel('Server banks').selectOption(restartBankId);
        await expect.poll(() => bank()?.entries.length).toBe(4);
        assert.equal(digest(JSON.stringify(stableEntries(bank()))), identity);
        const first = bank().entries[0];
        await forge.getByRole('button', { name: first.name, exact: true }).first().click();
        const favoriteIndex = first.candidates.findIndex(value => value.candidate_id === first.favorite.candidate_id);
        await forge.getByRole('article', { name: `Candidate ${favoriteIndex + 1}`, exact: true }).getByRole('button', { name: 'Select for audition' }).click();
        await expect.poll(() => latest.mutation_parameters_changed?.a4_parameters?.length).toBe(a4Fields.length);
        await expect(page.getByTestId('action-send')).toBeDisabled();
      }
      summary.cycles++; summary.elapsed_seconds = (performance.now() - started) / 1000;
      summary.original_source_sha256 = sourceIdentity; save();
      await sleep(Math.min(Math.max(0, intervalSeconds * 1000 - (performance.now() - cycleStart)), Math.max(0, duration - (performance.now() - started))));
    }
    summary.elapsed_seconds = (performance.now() - started) / 1000;
    assert(summary.cycles >= 3);
    assert(smoke > 0 || summary.elapsed_seconds >= minutes * 60);
    summary.passed = true; summary.stop_reason = smoke > 0 ? 'bounded-smoke-completed-not-endurance' : 'declared-endurance-duration-completed';
    summary.phase = 'completed';
    await page.screenshot({ path: path.join(reportRoot, 'final-desktop.png') });
  } catch (error) {
    summary.passed = false;
    summary.stop_reason = 'failure';
    summary.failure = { category: 'offline_rehearsal_operation_failed', error_type: errorType(error) };
    throw error;
  } finally {
    summary.ended_at = new Date().toISOString();
    if (browser) await browser.close().catch(() => {});
    if (launch) {
      try { summary.cleanup = processOperation('stop'); } catch (error) {
        summary.cleanup = { stopped: false, category: 'owned_process_cleanup_failed', error_type: errorType(error) };
        summary.passed = false;
        summary.stop_reason = 'owned-process-cleanup-failed';
        process.exitCode = 1;
      }
    }
    save(); console.log(JSON.stringify({ passed: summary.passed, mode: summary.mode, cycles: summary.cycles, stop_reason: summary.stop_reason, report: reportRoot }));
  }
}
main().catch(() => { process.exitCode = 1; });
