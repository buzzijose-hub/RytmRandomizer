/**
 * Per-component axe-core smoke tests. Each component is rendered into a
 * detached container and scanned for WCAG 2.2 AA violations. The
 * grandfathered-violations map records the AUDIT BASELINE — every entry
 * is a known finding the fix-cluster tasks will drive to zero. New
 * violations on a component without an entry fail the test loudly.
 */
import { render } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import { ProfileToggle } from '../../src/cockpit/ProfileToggle';
import { runAxe, violationSummary } from './__helpers__/axe';

// Floor map: component-name → expected violation count. Each fix-cluster
// task drops the matching entry to 0 (or removes it once fully clean).
// `as const` narrows the value type so direct property access returns
// `number` instead of `number | undefined` (which would otherwise fail
// `toBeLessThanOrEqual(number)` strict typing).
const FLOORS = {
  ProfileToggle: 0, // already clean per audit
} as const;

describe('axe-core smoke (WCAG 2.2 AA)', () => {
  it('ProfileToggle has no violations beyond the floor', async () => {
    const { container } = render(<ProfileToggle value="scene" onChange={() => {}} />);
    const results = await runAxe(container);
    expect(results.violations.length, violationSummary(results)).toBeLessThanOrEqual(
      FLOORS.ProfileToggle,
    );
  });
});
