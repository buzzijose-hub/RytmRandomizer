/* Run with node --test. All driver I/O is fake; PowerShell sees synthetic rows only. */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const { spawnSync } = require('node:child_process');
const { test } = require('node:test');

const driver = path.resolve(__dirname, '../e2e/fixtures/offline_endurance_driver.cjs');
const source = fs.readFileSync(driver, 'utf8');
const privateDetails = String.raw`C:\Users\private-operator\secret-kit.syx token=private-token-value kit=Private Stage Name`;

async function runFakeDriver({ failure, cleanupFailure, launchFailure = false, cleanupOnly = false }) {
  const writes = new Map(), operations = [];
  let powershell;
  const root = path.parse(driver).root;
  const context = vm.createContext({
    __dirname: path.dirname(driver),
    __filename: driver,
    process: {
      argv: ['node', driver, '--bundle', path.join(root, 'qa-delivery'), '--run-root', path.join(root, 'qa-isolated'), '--python', path.join(root, 'qa-python.exe'), '--smoke-seconds', '30'],
      env: { RYTM_RAND_MIDI_BACKEND: 'off' },
    },
    console: { log() {} },
    fetch: async () => ({ ok: true }),
    require(name) {
      if (name === 'node:fs') return {
        existsSync: () => false,
        mkdirSync() {},
        readFileSync(file) {
          if (path.basename(file) === 'BUILD-MANIFEST.json') return JSON.stringify({ source_commit: 'qa-source', sha256: {} });
          assert.equal(file, driver, 'Unexpected driver read');
          return source;
        },
        writeFileSync: (file, value) => writes.set(file, value),
        appendFileSync: (file, value) => writes.set(file, (writes.get(file) || '') + value),
      };
      if (name === 'node:child_process') return {
        spawnSync(command, args, options) {
          if (command === 'git') return { status: 0, stdout: '', stderr: '' };
          assert.equal(command, 'pwsh.exe', 'No other subprocess is allowed');
          assert.equal(options.windowsHide, true);
          powershell = args.at(-1);
          const { operation } = JSON.parse(options.input);
          operations.push(operation);
          if (operation === 'launch') {
            if (launchFailure) return { status: 1, stdout: privateDetails, stderr: privateDetails };
            return { status: 0, stdout: JSON.stringify({ shell_pid: 100, created_ticks: '1', ws_port: 4317, debug_port: 9222 }), stderr: '' };
          }
          assert.equal(operation, 'stop');
          if (cleanupFailure === 'stderr') return { status: 1, stdout: privateDetails, stderr: privateDetails };
          if (cleanupFailure) throw cleanupFailure;
          return { status: 0, stdout: '{"stopped":true}', stderr: '' };
        },
      };
      if (name === '@playwright/test') return {
        chromium: { async connectOverCDP() { throw failure; } },
        expect() { assert.fail('No browser assertions may run in helper QA'); },
      };
      assert(['node:path', 'node:crypto', 'node:assert/strict', 'node:perf_hooks'].includes(name));
      return require(name);
    },
  });
  // The real entry point runs to its persisted finally block inside this I/O sandbox.
  let exercised = source;
  if (cleanupOnly) {
    const main = source.indexOf('async function main()');
    const finalizer = source.lastIndexOf('  } finally {');
    assert(main > 0 && finalizer > main, 'The actual main finalizer is required');
    exercised = source.slice(0, main) + `async function main() {
      let browser;
      try {
        launch = { shell_pid: 100, created_ticks: '1' };
        summary.passed = true;
        summary.stop_reason = 'declared-endurance-duration-completed';
      ` + source.slice(finalizer);
  }
  await new vm.Script(exercised, { filename: driver }).runInContext(context);
  const report = JSON.parse(writes.get(path.join(root, 'qa-isolated', 'report', 'summary.json')));
  assert.equal(context.process.exitCode, 1);
  return { report, writes, operations, powershell };
}

function assertPrivateFree(writes) {
  for (const value of writes.values()) {
    for (const forbidden of ['private-operator', 'secret-kit.syx', 'private-token-value', 'Private Stage Name', 'C:\\Users\\']) {
      assert(!value.includes(forbidden), `Persisted private detail: ${forbidden}`);
    }
  }
}

const assertionFailure = () => new assert.AssertionError({
  message: privateDetails,
  actual: { private_path: privateDetails, token: privateDetails },
  expected: { kit: privateDetails },
});
const metadataFailure = () => {
  const error = new TypeError(privateDetails);
  error.private_metadata = { source: privateDetails, stderr: privateDetails, token: privateDetails };
  error.private_metadata.cycle = error;
  return error;
};
const privateNameFailure = () => Object.assign(new Error(privateDetails), { name: privateDetails });

for (const [label, makeFailure, errorType] of [
  ['assertion values', assertionFailure, 'AssertionError'],
  ['stderr assertion', assertionFailure, 'AssertionError'],
  ['circular private metadata', metadataFailure, 'TypeError'],
  ['private error name', privateNameFailure, 'Error'],
]) {
  test(`persisted failure and cleanup are categorical for ${label}`, async () => {
    const { report, writes, operations } = await runFakeDriver({
      failure: makeFailure(),
      cleanupFailure: label === 'stderr assertion' ? 'stderr' : makeFailure(),
    });
    assert.deepEqual(report.failure, { category: 'offline_rehearsal_operation_failed', error_type: errorType });
    assert.deepEqual(report.cleanup, { stopped: false, category: 'owned_process_cleanup_failed', error_type: errorType });
    assert.equal(report.passed, false);
    assert.equal(report.stop_reason, 'owned-process-cleanup-failed');
    assert.deepEqual(operations, ['launch', 'stop']);
    assertPrivateFree(writes);
  });
}

test('successful rehearsal verdict and exit status are revoked when actual finalizer cleanup fails', async () => {
  const { report, writes, operations } = await runFakeDriver({
    cleanupOnly: true, cleanupFailure: metadataFailure(),
  });
  assert.equal(report.failure, undefined);
  assert.equal(report.passed, false);
  assert.equal(report.stop_reason, 'owned-process-cleanup-failed');
  assert.deepEqual(report.cleanup, {
    stopped: false, category: 'owned_process_cleanup_failed', error_type: 'TypeError',
  });
  assert.deepEqual(operations, ['stop']);
  assertPrivateFree(writes);
});

test('launch stderr never enters the persisted failure or requests cleanup without ownership', async () => {
  const { report, writes, operations } = await runFakeDriver({ launchFailure: true });
  assert.deepEqual(report.failure, { category: 'offline_rehearsal_operation_failed', error_type: 'AssertionError' });
  assert.equal(report.cleanup, undefined);
  assert.deepEqual(operations, ['launch']);
  assertPrivateFree(writes);
});

test('stable cue rotation remains fair while display order changes', () => {
  const helper = source.match(/^const rehearsalCueId = .*;$/m)?.[0];
  assert(helper, 'The real cue rotation helper is required');
  assert(source.includes('rehearsalCueId(cueIds, cycle)'));
  const context = vm.createContext({});
  new vm.Script(helper + ';globalThis.choose=rehearsalCueId;').runInContext(context);
  const ids = ['A', 'B', 'C', 'D'], display = [...ids], counts = new Map(ids.map(id => [id, 2]));
  for (let cycle = 0; cycle < 240; cycle++) {
    const id = context.choose(ids, cycle);
    counts.set(id, counts.get(id) + 1);
    const last = display.pop(); display.splice(display.length - 1, 0, last);
  }
  assert.deepEqual([...counts.values()], [62, 62, 62, 62]);
});

test('scope proof requires a fresh event and exact cells, not a matching old length', () => {
  const helpers = source.match(/^const (?:orderedCells|freshExactScope) = .*;$/gm);
  assert.equal(helpers.length, 2, 'The real scope observation helpers are required');
  const context = vm.createContext({});
  new vm.Script(helpers.join('\n') + ';globalThis.observe=freshExactScope;').runInContext(context);
  const expected = [{ item_id: 1, parameter_key: 'osc1_tune' }, { item_id: 1, parameter_key: 'osc1_pwm_depth' }];
  assert.equal(context.observe(4, 4, expected, expected), false);
  assert.equal(context.observe(5, 4, [{ item_id: 2, parameter_key: 'osc1_tune' }, expected[1]], expected), false);
  assert.equal(context.observe(5, 4, [expected[1], expected[0]], expected), true);
  assert.equal(context.observe(5, 4, null, []), false);
  assert.equal(context.observe(5, 4, [], []), true);
});

const processRows = String.raw`
$epoch=[DateTime]::new(2026,1,1,0,0,0,[DateTimeKind]::Utc)
function Process-Row($id,$parent,$seconds,$executable='C:\qa\child.exe'){
  [pscustomobject]@{ProcessId=[int]$id;ParentProcessId=[int]$parent;CreationDate=$epoch.AddSeconds($seconds);ExecutablePath=$executable}
}
$r=[pscustomobject]@{shell_pid=100;bundle='C:\qa\bundle';created_ticks=[string]$epoch.AddSeconds(100).Ticks}
$all=@(
  (Process-Row 600 500 140),
  (Process-Row 700 400 150),
  (Process-Row 400 300 90),
  (Process-Row 500 300 130),
  (Process-Row 200 100 50),
  (Process-Row 800 100 125),
  (Process-Row 300 100 110 'C:\qa\bundle\binaries\rytm-sidecar.exe'),
  (Process-Row 100 1 100 'C:\qa\bundle\rytm-randomizer-shell.exe')
)
function Get-CimInstance { return $all }
`;

async function processFunctions() {
  const { powershell } = await runFakeDriver({ launchFailure: true });
  const boundary = powershell.indexOf("\nif($r.operation -eq 'launch')");
  assert(boundary > 0, 'PowerShell function boundary is required');
  assert.equal(powershell.match(/HashSet\[int\]/g).length, 1, 'Exactly one descendant walker');
  assert(powershell.includes('return @(Descendants-Of $all $shell)'));
  assert(powershell.includes('Stop-Owned @(Descendants-Of $tree $side[0])'));
  return powershell.slice(0, boundary);
}

function evaluatePowerShell(functions, body) {
  const result = spawnSync('pwsh.exe', ['-NoProfile', '-NonInteractive', '-Command', functions + processRows + body], {
    input: '{}', encoding: 'utf8', timeout: 10000, windowsHide: true,
  });
  assert.equal(result.status, 0, result.stderr);
  assert.equal(result.stderr, '');
  return JSON.parse(result.stdout.replace(/^\uFEFF/, '').trim());
}

test('both roots reject older reused-PID children and admit newer transitive descendants', async () => {
  const result = evaluatePowerShell(await processFunctions(), String.raw`
    $shell=@(Own-Tree)
    $backend=$all|Where-Object ProcessId -eq 300
    $children=@(Descendants-Of $all $backend)
    @{shell=@($shell.ProcessId|Sort-Object);backend=@($children.ProcessId|Sort-Object)}|ConvertTo-Json -Compress
  `);
  assert.deepEqual(result.shell, [100, 300, 500, 600, 800]);
  assert.deepEqual(result.backend, [300, 500, 600]);
});

test('owned shell must retain its executable and creation identity before walking', async () => {
  const result = evaluatePowerShell(await processFunctions(), String.raw`
    $valid=$all
    $errors=@()
    foreach($change in @('missing','path','creation')){
      $all=@($valid|Where-Object ProcessId -ne 100)
      if($change -eq 'path'){$all+=Process-Row 100 1 100 'C:\unrelated.exe'}
      if($change -eq 'creation'){$all+=Process-Row 100 1 104 'C:\qa\bundle\rytm-randomizer-shell.exe'}
      try{Own-Tree|Out-Null;throw 'Unexpected accepted root'}catch{$errors+=$_.Exception.Message}
    }
    ConvertTo-Json -InputObject $errors -Compress
  `);
  assert.deepEqual(result, ['Owned shell missing', 'Owned shell missing', 'Owned shell identity changed']);
});

const boundProcessFactory = String.raw`
function Bound-Process($row,$tag){
  $value=[pscustomobject]@{StartTime=$row.CreationDate;Path=$row.ExecutablePath;HasExited=$false;Tag=$tag}
  $value|Add-Member ScriptProperty SafeHandle {$script:events+="pin:$($this.Tag)";return 42}
  $value|Add-Member ScriptMethod Kill {$script:events+="kill:$($this.Tag)"}
  $value|Add-Member ScriptMethod WaitForExit {$script:events+="wait:$($this.Tag)";return $true}
  $value|Add-Member ScriptMethod Dispose {$script:events+="dispose:$($this.Tag)"}
  return $value
}
`;

test('stop pins a handle and verifies its identity before killing or disposing it', async () => {
  const result = evaluatePowerShell(await processFunctions(), String.raw`
    $owned=@((Process-Row 10 100 110),(Process-Row 11 100 110),(Process-Row 12 100 110),(Process-Row 13 100 110))
    $current=@((Process-Row 10 100 110),(Process-Row 11 100 111),(Process-Row 12 100 110 'C:\unrelated.exe'))
    $script:events=@();$script:queried=@()
    ` + boundProcessFactory + String.raw`
    function Get-Process($Id,$ErrorAction){
      $script:queried+=$Id
      $row=$current|Where-Object ProcessId -eq $Id
      if($null -eq $row){throw 'Process already gone'}
      return (Bound-Process $row $Id)
    }
    function Get-CimInstance($ClassName,$Filter){
      $current|Where-Object {"ProcessId=$($_.ProcessId)" -eq $Filter}
    }
    Stop-Owned $owned
    @{events=$script:events;queries=$script:queried}|ConvertTo-Json -Compress
  `);
  assert.deepEqual(result.events, ['pin:10', 'kill:10', 'wait:10', 'dispose:10', 'pin:11', 'dispose:11', 'pin:12', 'dispose:12']);
  assert.deepEqual(result.queries, [10, 11, 12, 13]);
});

test('a PID replacement after handle acquisition is not the object terminated', async () => {
  const result = evaluatePowerShell(await processFunctions(), String.raw`
    $owned=Process-Row 10 100 110
    $script:events=@();$script:lookups=0
    ` + boundProcessFactory + String.raw`
    function Get-Process {
      $script:lookups++
      $bound=Bound-Process $owned 'original'
      $bound|Add-Member -Force ScriptProperty SafeHandle {
        $script:replacement=Process-Row 10 1 200 'C:\unrelated.exe'
        $script:events+='pin:original'
        return 42
      }
      return $bound
    }
    function Stop-Process {throw 'PID-based termination is prohibited'}
    Stop-Owned @($owned)
    @{events=$script:events;lookups=$script:lookups;replacement=$script:replacement.ExecutablePath}|ConvertTo-Json -Compress
  `);
  assert.deepEqual(result.events, ['pin:original', 'kill:original', 'wait:original', 'dispose:original']);
  assert.equal(result.lookups, 1);
  assert.equal(result.replacement, 'C:\\unrelated.exe');
});

test('handle identity accounts only for CIM microsecond truncation, not a later process', async () => {
  const result = evaluatePowerShell(await processFunctions(), String.raw`
    $owned=Process-Row 10 100 110
    $script:events=@()
    ` + boundProcessFactory + String.raw`
    $results=@()
    foreach($extra in @(9,10)){
      function Get-Process {
        $native=Process-Row 10 100 110
        $native.CreationDate=$native.CreationDate.AddTicks($extra)
        return (Bound-Process $native $extra)
      }
      $bound=Open-OwnedProcess $owned
      $results+=@{extra=$extra;accepted=($null -ne $bound)}
      if($null -ne $bound){$bound.Dispose()}
    }
    ConvertTo-Json -InputObject $results -Compress
  `);
  assert.deepEqual(result, [{ extra: 9, accepted: true }, { extra: 10, accepted: false }]);
});

test('the actual test-owned PowerShell process binds successfully without being terminated', async () => {
  const result = evaluatePowerShell(await processFunctions(), String.raw`
    $self=Get-Process -Id $PID
    $ticks=$self.StartTime.ToUniversalTime().Ticks
    $row=[pscustomobject]@{ProcessId=$PID;CreationDate=[DateTime]::new($ticks-($ticks%10),[DateTimeKind]::Utc);ExecutablePath=$self.Path}
    $bound=Open-OwnedProcess $row
    if($null -eq $bound){throw 'Actual owned process identity did not bind'}
    @{matched=($bound.Id -eq $PID);handle_valid=(-not$bound.SafeHandle.IsInvalid);exited=$bound.HasExited}|ConvertTo-Json -Compress
    $bound.Dispose();$self.Dispose()
  `);
  assert.deepEqual(result, { matched: true, handle_valid: true, exited: false });
});

test('failed handle acquisition reports an owned survivor but ignores gone or replaced processes', async () => {
  const result = evaluatePowerShell(await processFunctions(), String.raw`
    $owned=Process-Row 10 100 110
    $results=@()
    foreach($change in @('survivor','gone','creation','path')){
      function Get-Process {throw 'Synthetic access failure'}
      function Get-CimInstance {
        if($change -eq 'survivor'){return $owned}
        if($change -eq 'creation'){return (Process-Row 10 100 111)}
        if($change -eq 'path'){return (Process-Row 10 100 110 'C:\unrelated.exe')}
      }
      $errorMessage=$null
      try{Stop-Owned @($owned)}catch{$errorMessage=$_.Exception.Message}
      $results+=@{change=$change;error=$errorMessage}
    }
    ConvertTo-Json -InputObject $results -Compress
  `);
  for (const row of result) assert.equal(row.error, row.change === 'survivor' ? 'Synthetic access failure' : null);
  assert(!source.includes('Stop-Process -Id'), 'No terminate-by-PID fallback is allowed');
  assert(source.includes('$main=Open-OwnedProcess ($owned|Where-Object ProcessId -eq $r.shell_pid'));
});
