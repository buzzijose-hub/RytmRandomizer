/**
 * Shared axe-core runner for Vitest a11y tests. Configures WCAG 2.2 AA
 * tags so the helper rejects per WCAG 2.0/2.1/2.2 A + AA rules but does
 * NOT trip on best-practice-only rules (which are advisory).
 */
import axe, { type AxeResults, type RunOptions } from 'axe-core';

const DEFAULT_OPTIONS: RunOptions = {
  runOnly: {
    type: 'tag',
    values: ['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'wcag22aa'],
  },
};

export async function runAxe(
  container: Element,
  overrides: RunOptions = {},
): Promise<AxeResults> {
  return axe.run(container, { ...DEFAULT_OPTIONS, ...overrides });
}

export function violationSummary(results: AxeResults): string {
  if (results.violations.length === 0) return 'no violations';
  return results.violations
    .map((v) => `  - ${v.id} (${v.impact}): ${v.help}`)
    .join('\n');
}
