/**
 * Unit coverage for the rovingTabindex helpers. Task 5 implements them;
 * test file lands now (Phase A) so infrastructure is in place.
 */
import { describe, it, expect } from 'vitest';

// Module path is built at runtime so Vite's static import-analysis does
// not try to resolve it at transform time (the module lands with Task 5).
// Skipped describe blocks still get their bodies *parsed* and their
// dynamic-import strings statically resolved by Vite, so the indirection
// is required even though every test below is in a `.skip` suite.
const ROVING_MODULE = ['..', '..', 'src', 'a11y', 'rovingTabindex'].join('/');

describe.skip('rovingTabindex.nextIndex (lands with Task 5)', () => {
  it('ArrowRight advances by 1', async () => {
    const { nextIndex } = await import(ROVING_MODULE);
    expect(nextIndex(0, 3, 'ArrowRight')).toBe(1);
  });

  it('ArrowRight wraps at end', async () => {
    const { nextIndex } = await import(ROVING_MODULE);
    expect(nextIndex(2, 3, 'ArrowRight')).toBe(0);
  });

  it('ArrowLeft retreats by 1', async () => {
    const { nextIndex } = await import(ROVING_MODULE);
    expect(nextIndex(1, 3, 'ArrowLeft')).toBe(0);
  });

  it('ArrowLeft wraps at start', async () => {
    const { nextIndex } = await import(ROVING_MODULE);
    expect(nextIndex(0, 3, 'ArrowLeft')).toBe(2);
  });

  it('Home jumps to 0', async () => {
    const { nextIndex } = await import(ROVING_MODULE);
    expect(nextIndex(2, 5, 'Home')).toBe(0);
  });

  it('End jumps to last index', async () => {
    const { nextIndex } = await import(ROVING_MODULE);
    expect(nextIndex(0, 5, 'End')).toBe(4);
  });

  it('Unknown key returns the current index', async () => {
    const { nextIndex } = await import(ROVING_MODULE);
    expect(nextIndex(1, 3, 'Space')).toBe(1);
  });
});
