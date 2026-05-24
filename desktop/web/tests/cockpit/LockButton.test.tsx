/**
 * Tests for LockButton — purely presentational toggle.
 */

import { describe, expect, it, vi } from 'vitest';
import { fireEvent, render, screen } from '@testing-library/react';

import { LockButton } from '../../src/cockpit/LockButton';

describe('LockButton', () => {
  it('renders 🔓 + "Lock pad X" label when unlocked', () => {
    render(<LockButton locked={false} padId={3} onToggle={() => undefined} />);
    const btn = screen.getByRole('button', { name: 'Lock pad 3' });
    expect(btn).toHaveTextContent('🔓');
    expect(btn).toHaveAttribute('aria-pressed', 'false');
    expect(btn.className).toBe('lock-button');
  });

  it('renders 🔒 + "Unlock pad X" label + locked class when locked', () => {
    render(<LockButton locked={true} padId={2} onToggle={() => undefined} />);
    const btn = screen.getByRole('button', { name: 'Unlock pad 2' });
    expect(btn).toHaveTextContent('🔒');
    expect(btn).toHaveAttribute('aria-pressed', 'true');
    expect(btn.className).toBe('lock-button locked');
  });

  it('calls onToggle when clicked', () => {
    const spy = vi.fn();
    render(<LockButton locked={false} padId={1} onToggle={spy} />);
    fireEvent.click(screen.getByRole('button'));
    expect(spy).toHaveBeenCalledTimes(1);
  });
});
