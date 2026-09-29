/** Real Windows plugin installation, confined to a copied fixture executable. */
import { createHash, randomUUID } from 'node:crypto';
import { copyFileSync, existsSync, mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import * as path from 'node:path';
import type { ChildProcess } from 'node:child_process';

export interface HandoffInputs {
  bytes: Buffer;
  publicKey: string;
  signature: string;
  installerHash: string;
  successorHash: string;
}

export interface HandoffEvidence {
  artifact_sha256: string;
  original_shell_sha256: string;
  replacement_sha256: string;
  parent_exit_code: number;
  sidecar_stopped_before_install: boolean;
  installer_runs: number;
  restart_runs: number;
  installer_arguments: string[];
}

const hash = (bytes: Buffer): string => createHash('sha256').update(bytes).digest('hex');
const requireFact = (condition: unknown, message: string): void => {
  if (!condition) throw new Error(`Native Windows handoff: ${message}`);
};

function objectFile(filename: string): Record<string, unknown> {
  const value: unknown = JSON.parse(readFileSync(filename, 'utf8'));
  if (typeof value !== 'object' || value === null || Array.isArray(value)) throw new Error('Invalid handoff receipt');
  return value as Record<string, unknown>;
}

export function loadHandoffInputs(repo: string): HandoffInputs {
  requireFact(process.platform === 'win32', 'this explicit target requires Windows');
  const filename = process.env.RYTM_NATIVE_HANDOFF_INPUTS;
  if (filename === undefined || !path.isAbsolute(filename)) throw new Error('Set RYTM_NATIVE_HANDOFF_INPUTS to the prepared absolute handoff-inputs.json path.');
  const manifest = objectFile(filename);
  requireFact(manifest.installer === 'RytmUpdaterAcceptanceInstaller.exe', 'fixture installer name mismatch');
  const sourceHashes = manifest.source_sha256 as Record<string, unknown> | undefined;
  for (const name of ['AcceptancePaths.cs', 'AcceptanceInstaller.cs', 'AcceptanceSuccessor.cs', 'as-invoker.manifest']) {
    requireFact(sourceHashes?.[name] === hash(readFileSync(path.join(repo, 'desktop/web/native-e2e/installer-fixture', name))), 'rebuild acceptance inputs from the current fixture sources');
  }
  const bytes = readFileSync(path.join(path.dirname(filename), 'RytmUpdaterAcceptanceInstaller.exe'));
  for (const field of ['public_key', 'signature', 'installer_sha256', 'successor_sha256']) requireFact(typeof manifest[field] === 'string' && manifest[field] !== '', `missing ${field}`);
  requireFact(hash(bytes) === manifest.installer_sha256, 'prepared installer hash mismatch');
  return { bytes, publicKey: manifest.public_key as string, signature: manifest.signature as string,
    installerHash: manifest.installer_sha256 as string, successorHash: manifest.successor_sha256 as string };
}

export function prepareHandoffCopy(root: string, binary: string, inputs: HandoffInputs): { executable: string; nonce: string; originalHash: string } {
  const executable = path.join(root, 'fixture-shell.exe');
  const originalHash = hash(readFileSync(binary));
  requireFact(originalHash !== inputs.successorHash, 'original shell must differ from inert successor');
  copyFileSync(binary, executable);
  requireFact(hash(readFileSync(executable)) === originalHash, 'copied fixture shell differs');
  mkdirSync(path.join(root, 'plugin-temp'));
  const nonce = randomUUID();
  writeFileSync(path.join(root, 'acceptance-marker'), nonce, { flag: 'wx' });
  writeFileSync(path.join(root, 'handoff-acceptance.json'), JSON.stringify({ nonce, shell_sha256: originalHash,
    installer_sha256: inputs.installerHash, successor_sha256: inputs.successorHash }), { flag: 'wx' });
  return { executable, nonce, originalHash };
}

function alive(pid: unknown): boolean {
  if (typeof pid !== 'number' || !Number.isSafeInteger(pid) || pid <= 0) throw new Error('Invalid fixture process ID');
  try { process.kill(pid, 0); return true; } catch (error) {
    if ((error as NodeJS.ErrnoException).code === 'ESRCH') return false;
    throw error;
  }
}

function events(root: string, filename: string): Array<Record<string, unknown>> {
  const full = path.join(root, filename);
  return existsSync(full) ? readFileSync(full, 'utf8').trim().split('\n').filter(Boolean).map((line) => JSON.parse(line) as Record<string, unknown>) : [];
}

export async function collectHandoffEvidence(root: string, child: ChildProcess, inputs: HandoffInputs, originalHash: string, restart: boolean): Promise<HandoffEvidence> {
  requireFact(child.exitCode === 0, 'real plugin must exit the native parent successfully');
  const deadline = Date.now() + 40_000;
  let exit: Record<string, unknown> | null = null;
  while (Date.now() < deadline) {
    const filename = path.join(root, 'installer-exit.json');
    if (existsSync(filename)) {
      try { exit = objectFile(filename); } catch { /* Receipt may still be flushing. */ }
      if (exit !== null && !alive(exit.pid)) break;
    }
    await new Promise((resolve) => setTimeout(resolve, 75));
  }
  requireFact(exit !== null && !alive(exit.pid), 'bounded fixture installer must finish');
  requireFact(exit?.exit_code === 0 && !existsSync(path.join(root, 'installer-error.json')), 'inert installer must complete without refusal');
  const receipt = objectFile(path.join(root, 'installer-receipt.json'));
  const start = objectFile(path.join(root, 'handoff-start.json'));
  requireFact(receipt.passed === true && receipt.parent_pid === child.pid && start.parent_pid === child.pid, 'installer must identify the actual exited shell');
  requireFact(receipt.sidecar_pid === start.sidecar_pid && !alive(receipt.sidecar_pid), 'actual passive backend must be stopped');
  requireFact(receipt.sidecar_stopped_before_install === true && receipt.parent_exited_before_replace === true, 'shutdown must precede replacement');
  requireFact(receipt.artifact_sha256 === inputs.installerHash && receipt.replacement_sha256 === inputs.successorHash, 'exact signed installer and embedded successor must be used');
  requireFact(hash(readFileSync(path.join(root, 'fixture-shell.exe'))) === inputs.successorHash, 'the copied executable must actually be replaced');
  const installerEvents = events(root, 'installer-events.jsonl');
  const restartEvents = events(root, 'restart-events.jsonl');
  requireFact(installerEvents.length === 1 && installerEvents[0]?.pid === receipt.pid, 'installer must run exactly once');
  requireFact(receipt.restart_requested === restart && restartEvents.length === (restart ? 1 : 0), 'restart choice must be honored exactly once');
  if (restart) {
    const successor = objectFile(path.join(root, 'restart-receipt.json'));
    requireFact(successor.pid === receipt.successor_pid && !alive(successor.pid) && successor.sha256 === inputs.successorHash && successor.version === '1.35.1', 'the replaced successor must really execute and exit');
  } else {
    requireFact(receipt.successor_pid === null && !existsSync(path.join(root, 'restart-receipt.json')), 'quit must not launch the successor');
  }
  const args = receipt.arguments as string[];
  requireFact(Array.isArray(args) && args.every((item) => typeof item === 'string') && args.includes('/UPDATE') && args.includes('/P') && args.includes('/R') === restart, 'real plugin Windows arguments must reach installer');
  return { artifact_sha256: inputs.installerHash, original_shell_sha256: originalHash, replacement_sha256: inputs.successorHash,
    parent_exit_code: child.exitCode ?? -1, sidecar_stopped_before_install: true, installer_runs: installerEvents.length,
    restart_runs: restartEvents.length, installer_arguments: args.map((item) => item === root ? '<fixture-root>' : item) };
}
