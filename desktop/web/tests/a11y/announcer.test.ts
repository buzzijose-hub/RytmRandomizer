/**
 * Unit coverage for the announcer module. Task 8 implements the module;
 * this test file lands now (Phase A) so the test infrastructure is in
 * place and the failing-by-skip status is visible in CI.
 */
import { describe, it, expect, beforeEach, vi } from 'vitest';

// Module path is built at runtime so Vite's static import-analysis does
// not try to resolve it at transform time (the module lands with Task 8).
// Skipped describe blocks still get their bodies *parsed* and their
// dynamic-import strings statically resolved by Vite, so the indirection
// is required even though every test below is in a `.skip` suite.
const ANNOUNCER_MODULE = ['..', '..', 'src', 'a11y', 'announcer'].join('/');

describe.skip('announcer (lands with Task 8)', () => {
  beforeEach(() => {
    vi.resetModules();
  });

  it('calls the registered callback with the message', async () => {
    const { announce, _registerWriter } = await import(ANNOUNCER_MODULE);
    const writer = vi.fn();
    _registerWriter(writer);
    announce('hello');
    await new Promise((r) => setTimeout(r, 250));
    expect(writer).toHaveBeenCalledWith('hello');
  });

  it('debounces rapid calls', async () => {
    const { announce, _registerWriter } = await import(ANNOUNCER_MODULE);
    const writer = vi.fn();
    _registerWriter(writer);
    announce('first');
    announce('second');
    announce('third');
    await new Promise((r) => setTimeout(r, 250));
    expect(writer).toHaveBeenCalledTimes(1);
    expect(writer).toHaveBeenCalledWith('third');
  });

  it('is a no-op when no writer is registered', () => {
    return import(ANNOUNCER_MODULE).then(({ announce }) => {
      expect(() => announce('nobody home')).not.toThrow();
    });
  });
});
