import { readFileSync } from 'node:fs';
import * as path from 'node:path';
import { describe, expect, it, vi } from 'vitest';

import { bootstrap } from '../e2e/fixtures/native_update_bootstrap';
import { resolveRepoRootForManifest } from '../e2e/fixtures/update_manifest';

describe('native App-before-driver bootstrap', () => {
  it('pins the native hook and HTML to the same App module graph', () => {
    const repo = resolveRepoRootForManifest();
    const shell = readFileSync(path.join(repo, 'desktop/shell/src/native_fixture.rs'), 'utf8');
    const html = readFileSync(path.join(repo, 'desktop/web/index.html'), 'utf8');
    expect(shell).toContain("import('/e2e/fixtures/native_update_bootstrap.ts')");
    expect(shell).toContain('.then(m => m.bootstrap({scenario}, {origin}))');
    expect(html).toContain('src="/src/main.tsx"');
  });

  it('waits for the actual App module before loading or running assertions', async () => {
    let release: (() => void) | undefined;
    const app = new Promise<void>((resolve) => { release = resolve; });
    const run = vi.fn().mockResolvedValue(undefined);
    const loadDriver = vi.fn().mockResolvedValue({ run });
    const pending = bootstrap('hydrate_reload', 'http://127.0.0.1:99', () => app, loadDriver);
    await Promise.resolve();
    expect(loadDriver).not.toHaveBeenCalled();
    expect(run).not.toHaveBeenCalled();
    release?.();
    await pending;
    expect(loadDriver).toHaveBeenCalledOnce();
    expect(run).toHaveBeenCalledExactlyOnceWith('hydrate_reload', 'http://127.0.0.1:99');
  });

  it('does not run assertions when App loading fails', async () => {
    const failure = new Error('App graph did not load');
    const loadDriver = vi.fn();
    await expect(bootstrap('hydrate_reload', 'http://127.0.0.1:99',
      () => Promise.reject(failure), loadDriver)).rejects.toBe(failure);
    expect(loadDriver).not.toHaveBeenCalled();
  });

  it('preserves a failed driver import and a failed strict assertion', async () => {
    const failure = new Error('strict native assertion failed');
    const app = () => Promise.resolve();
    await expect(bootstrap('hydrate_reload', 'http://127.0.0.1:99', app,
      () => Promise.reject(failure))).rejects.toBe(failure);
    const run = vi.fn().mockRejectedValue(failure);
    await expect(bootstrap('hydrate_reload', 'http://127.0.0.1:99', app,
      () => Promise.resolve({ run }))).rejects.toBe(failure);
    expect(run).toHaveBeenCalledOnce();
  });
});
