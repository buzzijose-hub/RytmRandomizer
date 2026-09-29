import { mkdtempSync, mkdirSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import * as path from 'node:path';
import { afterEach, beforeEach, describe, expect, it } from 'vitest';

import { nativeFailureDetails } from '../e2e/fixtures/native_update_fixture';

describe('native failure evidence', () => {
  let root: string;
  beforeEach(() => { root = mkdtempSync(path.join(tmpdir(), 'rytm-native-diagnostic-')); });
  afterEach(() => {
    const resolved = path.resolve(root);
    if (path.dirname(resolved) !== path.resolve(tmpdir()) || !path.basename(resolved).startsWith('rytm-native-diagnostic-')) {
      throw new Error('Refusing cleanup outside the owned diagnostic fixture');
    }
    rmSync(resolved, { recursive: true, force: true });
  });

  it('redacts credentials and paths before JSON escaping and omits journal details', () => {
    const token = 'token-with-"quote\\slash';
    const armSecret = 'private-arm-secret';
    writeFileSync(path.join(root, 'ws-token'), token);
    writeFileSync(path.join(root, 'arm-secret'), armSecret);
    writeFileSync(path.join(root, 'report-started.json'), '{}');
    mkdirSync(path.join(root, 'RytmRandomizer'));
    writeFileSync(path.join(root, 'RytmRandomizer', 'update-journal.jsonl'),
      JSON.stringify({ event: 'bucket_excluded', detail: { private: token } }) + '\n');

    const detail = JSON.parse(nativeFailureDetails(root,
      [`${root} ${token} ${armSecret}`], [`/control?token=${token}`]));

    expect(detail.output).toBe('<fixture-root> <fixture-credential> <fixture-credential>');
    expect(detail.requests).toEqual(['/control']);
    expect(detail.journalEvents).toEqual(['bucket_excluded']);
    expect(detail.reportStarted).toBe(true);
    expect(detail.resultPresent).toBe(false);
    expect(detail.sidecarCredentialsPresent).toBe(true);
    expect(JSON.stringify(detail)).not.toContain(armSecret);
  });

  it('bounds output and request history when startup produced no files', () => {
    const detail = JSON.parse(nativeFailureDetails(root, ['x'.repeat(9000)],
      Array.from({ length: 60 }, (_, index) => `/request-${index}`)));

    expect(detail.output).toHaveLength(8000);
    expect(detail.requests).toHaveLength(50);
    expect(detail.requests[0]).toBe('/request-10');
    expect(detail.journalEvents).toEqual([]);
    expect(detail.reportStarted).toBe(false);
    expect(detail.resultPresent).toBe(false);
    expect(detail.sidecarCredentialsPresent).toBe(false);
  });

  it('retains complete events around a partial append and tolerates unreadable files', () => {
    mkdirSync(path.join(root, 'RytmRandomizer'));
    const journal = path.join(root, 'RytmRandomizer', 'update-journal.jsonl');
    writeFileSync(journal, '{"event":"check_started"}\n{"event":');
    expect(JSON.parse(nativeFailureDetails(root, [], [])).journalEvents)
      .toEqual(['check_started', '<incomplete-row>']);

    rmSync(journal);
    mkdirSync(journal);
    mkdirSync(path.join(root, 'ws-token'));
    expect(JSON.parse(nativeFailureDetails(root, ['startup'], [])).journalEvents).toEqual([]);
  });
});
