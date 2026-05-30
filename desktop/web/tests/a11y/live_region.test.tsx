/**
 * LiveRegion + announcer module integration. Renders LiveRegion in
 * isolation, calls announce(...), asserts the visible textContent
 * updates after debounce.
 */
import { render, screen, act } from '@testing-library/react';
import { describe, expect, it, afterEach } from 'vitest';

import { announce, _reset } from '../../src/a11y/announcer';
import { LiveRegion } from '../../src/a11y/LiveRegion';

afterEach(() => _reset());

describe('LiveRegion', () => {
  it('renders an empty role=status region by default', () => {
    render(<LiveRegion />);
    const region = screen.getByTestId('a11y-live-region');
    expect(region).toHaveAttribute('role', 'status');
    expect(region).toHaveAttribute('aria-live', 'polite');
    expect(region.textContent).toBe('');
  });

  it('updates text content when announce() fires (after debounce)', async () => {
    render(<LiveRegion />);
    await act(async () => {
      announce('Send complete, 12 parameters sent');
      await new Promise((r) => setTimeout(r, 250));
    });
    const region = screen.getByTestId('a11y-live-region');
    expect(region.textContent).toBe('Send complete, 12 parameters sent');
  });
});
